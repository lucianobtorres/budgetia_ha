# src/core/user_config_service.py
# (Note: 'core', não 'web_app'. Esta classe não pode importar streamlit)
import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

import config

try:
    ENCRYPTION_KEY = os.getenv("USER_DATA_ENCRYPTION_KEY").encode("utf-8")
    FERNET = Fernet(ENCRYPTION_KEY)
except Exception as e:
    print(
        f"ERRO CRÍTICO: USER_DATA_ENCRYPTION_KEY inválida ou não definida no .env. {e}"
    )
    FERNET = None


class UserConfigService:
    """
    Responsabilidade Única: Gerenciar a leitura e escrita do
    arquivo config.json de um *único* usuário.
    É a chave para a LGPD e o Multi-Tenancy.
    """

    def __init__(self, username: str):
        if not FERNET:
            raise ValueError(
                "Serviço de Configuração não pode operar. Chave de Criptografia está ausente."
            )

        if not username:
            raise ValueError("Username não pode ser nulo.")
        self.username = username
        self.config_dir = Path(config.DATA_DIR) / "users" / self.username
        self.config_file_path = self.config_dir / "user_config.json"
        self.strategy_file_path = self.config_dir / "user_strategy.py"
        self.strategy_module_name = self.strategy_file_path.stem
        self._ensure_dir_exists()

    def _ensure_dir_exists(self) -> None:
        """Garante que o diretório do usuário exista."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _encrypt_data(self, data: str) -> bytes:
        """Criptografa uma string de dados."""
        return FERNET.encrypt(data.encode("utf-8"))

    def _decrypt_data(self, encrypted_data: bytes) -> str | None:
        """Descriptografa bytes de volta para uma string."""
        try:
            return FERNET.decrypt(encrypted_data).decode("utf-8")
        except InvalidToken:
            print(
                f"ERRO: Token inválido ao descriptografar config para {self.username}. O arquivo pode estar corrompido ou a chave mudou."
            )
            return None
        except Exception as e:
            print(f"ERRO ao descriptografar: {e}")
            return None

    def load_config(self) -> dict[str, Any]:
        """Carrega a configuração do arquivo JSON deste usuário."""
        print(f"[DEBUG load_config] Tentando ler de: {self.config_file_path}")
        print(f"[DEBUG load_config] Arquivo existe? {self.config_file_path.exists()}")
        if self.config_file_path.exists():
            try:
                with open(self.config_file_path, "rb") as f:
                    encrypted_data = f.read()  # type: ignore

                if not encrypted_data:
                    print("[DEBUG load_config] Arquivo vazio!")
                    return {}

                json_string = self._decrypt_data(encrypted_data)

                if json_string:
                    data = json.loads(json_string)
                    print(f"[DEBUG load_config] Dados carregados: {list(data.keys())}")
                    return data
                else:
                    print("[DEBUG load_config] Falha na descriptografia")
                    return {}
            except (json.JSONDecodeError, OSError) as e:
                print(f"Erro ao ler config do usuário {self.username}: {e}")
                return {}
        print("[DEBUG load_config] Arquivo não existe, retornando {}")
        return {}  # Retorna dict vazio se não existir

    def save_config(self, config_data: dict[str, Any]) -> None:
        """Salva a configuração no arquivo JSON deste usuário."""
        print(f"[DEBUG save_config] Salvando em: {self.config_file_path}")
        self._ensure_dir_exists()
        try:
            json_string = json.dumps(config_data, indent=4)
            encrypted_data = self._encrypt_data(json_string)

            with open(self.config_file_path, "wb") as f:
                f.write(encrypted_data)
            print(f"[DEBUG save_config] Arquivo salvo com sucesso: {self.config_file_path.exists()}")
        except OSError as e:
            print(f"Erro ao salvar config do usuário {self.username}: {e}")

    # --- Métodos de Negócio (extraídos do utils/manager) ---

    def get_planilha_path(self) -> str | None:
        """Retorna o caminho da planilha salvo na configuração."""
        config_data = self.load_config()
        path_str = config_data.get(config.PLANILHA_KEY)

        print(f"[DEBUG get_planilha_path] PLANILHA_KEY='{config.PLANILHA_KEY}', path_str='{path_str}'")

        if not path_str:
            print("[DEBUG get_planilha_path] Nenhum caminho encontrado no config")
            return None

        # Validação (a mesma que corrigimos antes)
        if "docs.google.com/" in path_str:
            print(f"[DEBUG get_planilha_path] Google Sheets URL detectada: {path_str}")
            return str(path_str)

        file_exists = Path(path_str).is_file()
        print(f"[DEBUG get_planilha_path] Arquivo local: '{path_str}' | Existe: {file_exists}")
        
        if file_exists:
            return str(path_str)

        # O caminho salvo é inválido, vamos limpar
        print(f"[DEBUG get_planilha_path] Arquivo não existe! Removendo do config.")
        config_data.pop(config.PLANILHA_KEY, None)
        self.save_config(config_data)
        return None

    def save_planilha_path(self, path_str: str) -> None:
        """Salva o caminho da planilha na configuração."""
        print(f"[DEBUG save_planilha_path] CHAMADO com path_str='{path_str}'")
        config_data = self.load_config()
        print(f"[DEBUG save_planilha_path] Config antes: {config_data.keys()}")
        config_data[config.PLANILHA_KEY] = path_str
        # Limpa estados de onboarding pendentes ao salvar um novo caminho
        config_data.pop("onboarding_state", None)
        config_data.pop("pending_planilha_path", None)
        print(f"[DEBUG save_planilha_path] Config depois: PLANILHA_KEY='{config.PLANILHA_KEY}' -> '{config_data.get(config.PLANILHA_KEY)}'")
        self.save_config(config_data)
        print(f"[DEBUG save_planilha_path] save_config() concluído")

    def get_mapeamento(self) -> dict[str, Any] | None:
        config_data = self.load_config()
        return config_data.get("mapeamento")

    def save_mapeamento(self, mapeamento: dict[str, Any]) -> None:
        """Salva o mapeamento E o nome do módulo da estratégia."""
        config_data = self.load_config()
        if "strategy_module" not in mapeamento:
            print("AVISO: save_mapeamento chamado sem 'strategy_module' no dict.")
            # Adiciona o nome do módulo padrão por segurança
            mapeamento["strategy_module"] = self.strategy_module_name

        config_data["mapeamento"] = mapeamento
        self.save_config(config_data)

    def get_pending_planilha_path(self) -> str | None:
        config_data = self.load_config()
        return config_data.get("pending_planilha_path")

    def save_pending_planilha_path(self, path_str: str) -> None:
        config_data = self.load_config()
        config_data["pending_planilha_path"] = path_str
        self.save_config(config_data)


    def get_onboarding_state(self) -> str | None:
        config_data = self.load_config()
        return config_data.get("onboarding_state")

    def get_onboarding_status(self) -> str | None:
        """Retorna o status do onboarding salvo (ex: 'COMPLETE', 'WELCOME').
        Lê a chave 'onboarding_status' que é salva pelo OnboardingOrchestrator."""
        config_data = self.load_config()
        return config_data.get("onboarding_status")

    def save_onboarding_state(self, state: str) -> None:
        config_data = self.load_config()
        config_data["onboarding_state"] = state
        self.save_config(config_data)


    def save_google_oauth_tokens(self, token_json_str: str) -> None:
        """Salva os tokens OAuth 2.0 do usuário (como JSON string) no config."""
        config_data = self.load_config()
        config_data["google_oauth_tokens"] = token_json_str
        self.save_config(config_data)

    def get_google_oauth_tokens(self) -> str | None:
        """Carrega os tokens OAuth 2.0 do usuário (como JSON string)."""
        config_data = self.load_config()
        return config_data.get("google_oauth_tokens")

    def save_backend_consent(self, has_consent: bool) -> None:
        """Salva a decisão do usuário de compartilhar com o backend."""
        config_data = self.load_config()
        config_data["backend_consent"] = has_consent
        self.save_config(config_data)

    def get_backend_consent(self) -> bool:
        """Verifica se o usuário deu consentimento ao backend."""
        config_data = self.load_config()
        # Retorna False por padrão se a chave não existir
        return config_data.get("backend_consent", False)

    def clear_config(self) -> None:
        """
        Reseta o *onboarding da planilha*, mas MANTÉM as
        configurações de identidade do usuário (ex: tokens do Google).
        """
        print(
            f"--- DEBUG ConfigService: Resetando (clear) config da planilha para {self.username} ---"
        )

        # 1. Carrega a configuração atual
        config_data = self.load_config()

        # 2. Lista de chaves a *manter* (identidade)
        keys_to_keep = [
            "google_oauth_tokens"
            # (No futuro, 'openfinance_tokens', etc. entrariam aqui)
        ]

        # 3. Cria um novo dict SÓ com as chaves de identidade
        new_config_data = {
            key: config_data[key] for key in keys_to_keep if key in config_data
        }

        # 4. Salva o config "limpo" (só com a identidade)
        self.save_config(new_config_data)

        # 5. Apaga a estratégia .py customizada (CICLO DE VIDA LGPD)
        if self.strategy_file_path.exists():
            try:
                os.remove(self.strategy_file_path)
            except OSError as e:
                print(f"AVISO: Falha ao limpar {self.strategy_file_path}: {e}")

    def save_comunicacao_field(self, field_name: str, value: Any) -> None:
        """
        Salva um campo (ex: 'telegram_chat_id') na chave 'comunicacao'
        dentro do user_config.json.
        """
        config_data = self.load_config()

        # Garante que a chave 'comunicacao' exista
        if "comunicacao" not in config_data:
            config_data["comunicacao"] = {}

        # Só salva se o valor for novo, para evitar escritas desnecessárias
        if config_data["comunicacao"].get(field_name) != value:
            config_data["comunicacao"][field_name] = value
            print(
                f"--- DEBUG ConfigService: Salvando '{field_name}' ({value}) para {self.username} ---"
            )
            self.save_config(config_data)
