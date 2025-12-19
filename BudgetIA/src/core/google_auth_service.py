# src/core/google_auth_service.py
import io
import json
import re
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

import config

from .user_config_service import UserConfigService


class GoogleAuthService:
    """
    Responsabilidade Única: Gerenciar o fluxo de autenticação
    OAuth 2.0 do *usuário* (não da Conta de Serviço).
    """

    def __init__(self, config_service: UserConfigService):
        self.config_service = config_service
        self.flow: Flow = self._create_flow()

    def _create_flow(self) -> Flow:
        """Cria a instância do fluxo OAuth."""

        # Cria a configuração do 'client' a partir do config.py
        client_config = {
            "web": {
                "client_id": config.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": config.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.GOOGLE_OAUTH_REDIRECT_URI],
            }
        }

        return Flow.from_client_config(
            client_config=client_config,
            scopes=config.GOOGLE_OAUTH_SCOPES,
            redirect_uri=config.GOOGLE_OAUTH_REDIRECT_URI,
        )

    def generate_authorization_url(self, current_onboarding_state: str | None = None) -> str:
        """
        Gera a URL OAuth com estado do onboarding (opcional) para restauração após redirect.
        
        Args:
            current_onboarding_state: Nome do estado atual (ex: 'SPREADSHEET_ACQUISITION')
        
        Returns:
            URL de autorização do Google OAuth
        """
        # Cria um state customizado que inclui o estado do onboarding
        custom_state = None
        if current_onboarding_state:
            from datetime import datetime
            custom_state = json.dumps({
                "onboarding_state": current_onboarding_state,
                "timestamp": datetime.now().isoformat()
            })
        
        # 'access_type='offline'' garante que recebamos um 'refresh_token'
        # 'prompt='consent'' garante que o usuário veja a tela de permissões
        authorization_url, _ = self.flow.authorization_url(
            access_type="offline", 
            prompt="consent",
            state=custom_state  # ← NOVO: Passa estado customizado para preservar contexto
        )
        return str(authorization_url)

    def exchange_code_for_tokens(self, code: str) -> None:
        """Troca o código de autorização pelos tokens de acesso."""
        try:
            self.flow.fetch_token(code=code)
            # Salva os tokens criptografados no config do usuário
            credentials = self.flow.credentials
            self.config_service.save_google_oauth_tokens(
                credentials.to_json()  # Salva como JSON
            )
        except Exception as e:
            raise Exception(f"Erro ao trocar o código por tokens: {e}") from e

    def download_sheets_as_excel_for_analysis(self, file_id: str) -> str:
        """
        Baixa um Google Sheet (nativo ou não-nativo) como .xlsx para análise local.
        Implementa a lógica de alternar entre 'export' (Sheets nativo) e 'get_media' (XLSX não-nativo).
        """
        try:
            # --- 1. Autenticar a Service Account (o robô) ---
            sa_path = Path(config.SERVICE_ACCOUNT_CREDENTIALS_PATH)

            if not sa_path.exists():
                raise FileNotFoundError(
                    f"O arquivo de credenciais da Service Account não foi encontrado no caminho: {sa_path}."
                )

            creds_sa = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=config.GOOGLE_OAUTH_SCOPES,
            )
            drive_service = build("drive", "v3", credentials=creds_sa)

        except Exception as e:
            raise Exception(
                f"Erro ao carregar credenciais da Service Account para download: {e}"
            )

        # --- 2. Obter MIME Type do arquivo ---
        file_metadata = (
            drive_service.files().get(fileId=file_id, fields="mimeType").execute()
        )
        mime_type = file_metadata.get("mimeType")

        # --- 3. Determinar o método de download ---

        # MIME Type para XLSX (o formato que o Pandas precisa)
        xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Se o arquivo for um Google Sheets nativo (requer export/conversão)
        if mime_type == "application/vnd.google-apps.spreadsheet":
            print(
                "--- DEBUG GoogleAuth: Arquivo é um Google Sheet nativo. Usando EXPORT. ---"
            )
            request = drive_service.files().export(
                fileId=file_id,
                mimeType=xlsx_mime,  # Exporta como XLSX
            )

        # Se o arquivo for um XLSX não-nativo (upload original do usuário)
        elif mime_type == xlsx_mime:
            print(
                "--- DEBUG GoogleAuth: Arquivo é um XLSX não-nativo. Usando GET media. ---"
            )
            request = drive_service.files().get_media(fileId=file_id)

        else:
            # Qualquer outro tipo de arquivo (Docs, PDF, etc.)
            raise Exception(
                f"Tipo de arquivo não suportado ({mime_type}). Apenas Google Sheets e XLSX."
            )

        # --- 4. Salvar o arquivo localmente ---
        file_name = f"{file_id}_temp_analysis.xlsx"

        # Cria um diretório temporário específico para o usuário
        temp_dir = Path(config.DATA_DIR) / "temp" / self.config_service.username
        temp_dir.mkdir(parents=True, exist_ok=True)
        local_file_path = temp_dir / file_name

        # Executa o download usando MediaIoBaseDownload
        fh = io.FileIO(local_file_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Após o download, o arquivo .xlsx está pronto para o Pandas
        print(
            f"--- DEBUG GoogleAuth: Download temporário concluído em: {local_file_path} ---"
        )
        return str(local_file_path)

    def get_user_credentials(self) -> Credentials | None:
        """Carrega as credenciais salvas do usuário."""
        token_json = self.config_service.get_google_oauth_tokens()
        if not token_json:
            return None

        creds = Credentials.from_authorized_user_info(
            json.loads(token_json), config.GOOGLE_OAUTH_SCOPES
        )

        # Se o token de acesso expirou, atualiza-o
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Salva o token atualizado
            self.config_service.save_google_oauth_tokens(creds.to_json())

        return creds

    def list_google_drive_files(self) -> list[dict[str, Any]]:
        """
        Usa as credenciais OAuth 2.0 do USUÁRIO para listar seus
        arquivos Google Sheets e Excel no Google Drive.
        """
        creds = self.get_user_credentials()
        if not creds:
            raise ValueError("Não foi possível carregar as credenciais do Google.")

        try:
            # Constrói o serviço autenticado COMO o usuário
            drive_service = build("drive", "v3", credentials=creds)

            # Query para buscar apenas planilhas e arquivos excel
            query = (
                "mimeType='application/vnd.google-apps.spreadsheet' or "
                "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'"
            )

            results = (
                drive_service.files()
                .list(
                    q=query,
                    pageSize=50,  # Limite de 50 arquivos
                    fields="files(id, name, webViewLink, iconLink)",  # Pede o ID, Nome, Link e Ícone
                )
                .execute()
            )

            files = results.get("files", [])
            print(
                f"--- DEBUG GoogleAuth: Encontrados {len(files)} arquivos no Drive do usuário. ---"
            )
            return files

        except Exception as e:
            raise Exception(f"Erro ao listar arquivos do Google Drive: {e}") from e

    def share_file_with_service_account(self, file_id: str) -> tuple[bool, str]:
        """
        Usa as credenciais OAuth do *usuário* para dar permissão de 'leitor'
        ao e-mail da *Conta de Serviço* (o "robô").
        """
        creds = self.get_user_credentials()
        if not creds:
            return False, "Credenciais do usuário não encontradas."

        if not config.SERVICE_ACCOUNT_EMAIL:
            return False, "E-mail da Conta de Serviço não configurado no servidor."

        try:
            drive_service = build("drive", "v3", credentials=creds)

            # Define a permissão: O robô (type=user) será leitor (role=reader)
            permission = {
                "type": "user",
                "role": "writer",
                "emailAddress": config.SERVICE_ACCOUNT_EMAIL,
            }

            print(
                f"--- DEBUG GoogleAuth: Compartilhando arquivo {file_id} com {config.SERVICE_ACCOUNT_EMAIL}... ---"
            )

            drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                fields="id",  # Só precisamos saber que funcionou
            ).execute()

            print("--- DEBUG GoogleAuth: Compartilhamento bem-sucedido. ---")
            return True, "Arquivo compartilhado com o back-end."

        except Exception as e:
            print(f"ERRO GoogleAuth: Falha ao compartilhar arquivo: {e}")
            return False, f"Falha ao compartilhar arquivo: {e}"

    # --- 2. ADICIONAR MÉTODO HELPER ---
    def _extract_file_id_from_url(self, url: str) -> str | None:
        """
        Extrai o ID do arquivo de uma URL do Google Drive
        (formato /file/ ou /spreadsheets/).
        """
        # Padrão: /file/d/ID ou /spreadsheets/d/ID
        match = re.search(r"/(?:file|spreadsheets)/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        print(
            f"--- DEBUG GoogleAuth: Não foi possível extrair File ID da URL: {url} ---"
        )
        return None

    # --- 3. MÉTODO DE REVOGAÇÃO NÍVEL 1 -
    def revoke_file_sharing_from_service_account(
        self, file_id: str
    ) -> tuple[bool, str]:
        """
        Usa as credenciais OAuth do *usuário* para REMOVER as permissões
        da *Conta de Serviço* (o "robô").
        """
        creds = self.get_user_credentials()
        if not creds or not config.SERVICE_ACCOUNT_EMAIL:
            return False, "Credenciais do usuário ou e-mail de serviço não encontrados."

        try:
            drive_service = build("drive", "v3", credentials=creds)

            # 1. Encontrar o ID da permissão do nosso "robô"
            print(
                f"--- DEBUG GoogleAuth: Procurando permissão para {config.SERVICE_ACCOUNT_EMAIL} no arquivo {file_id}... ---"
            )
            permission_id_to_delete = None
            permissions = (
                drive_service.permissions()
                .list(fileId=file_id, fields="permissions(id, emailAddress)")
                .execute()
            )

            for p in permissions.get("permissions", []):
                if p.get("emailAddress") == config.SERVICE_ACCOUNT_EMAIL:
                    permission_id_to_delete = p.get("id")
                    break

            if not permission_id_to_delete:
                print(
                    "--- DEBUG GoogleAuth: Permissão não encontrada (já foi revogada). ---"
                )
                return True, "O acesso do back-end já estava revogado."

            # 2. Deletar a permissão
            print(
                f"--- DEBUG GoogleAuth: Revogando permissão ID: {permission_id_to_delete}... ---"
            )
            drive_service.permissions().delete(
                fileId=file_id, permissionId=permission_id_to_delete
            ).execute()

            print("--- DEBUG GoogleAuth: Acesso revogado com sucesso. ---")
            return True, "Acesso do back-end revogado com sucesso."

        except Exception as e:
            print(f"ERRO GoogleAuth: Falha ao revogar acesso: {e}")
            return False, f"Falha ao revogar acesso: {e}"

    # --- 4. MÉTODO DE REVOGAÇÃO NÍVEL 2 (Frontend) ---
    def revoke_google_oauth_token(self) -> bool:
        """
        Revoga o refresh_token do usuário no Google.
        Isso força o usuário a fazer login novamente.
        """
        creds = self.get_user_credentials()
        if not creds or not creds.refresh_token:
            print(
                "--- DEBUG GoogleAuth: Nenhum token para revogar. Limpando localmente. ---"
            )
            self.config_service.save_google_oauth_tokens(None)  # Limpa o token local
            return True

        try:
            # Tenta revogar o token no servidor do Google
            creds.revoke(Request())
            print(
                f"--- DEBUG GoogleAuth: Token OAuth revogado com sucesso para {self.config_service.username}. ---"
            )
        except Exception as e:
            print(
                f"AVISO GoogleAuth: Falha ao revogar token no Google (pode já estar expirado): {e}"
            )
            # Continua mesmo se a revogação falhar...

        # O mais importante: apaga o token local
        self.config_service.save_google_oauth_tokens(None)
        return True
