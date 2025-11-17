# src/web_app/utils.py
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from core.user_config_service import UserConfigService
from finance.strategies.base_strategy import BaseMappingStrategy

# Adiciona o diretório 'src' ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from config import DATA_DIR, DEFAULT_GEMINI_MODEL, PLANILHA_KEY
from core.llm_manager import LLMOrchestrator
from core.llm_providers.gemini_provider import GeminiProvider

# Importa a Fachada
from finance.planilha_manager import PlanilhaManager

# Importa o tipo
from initialization.strategy_generator import StrategyGenerator

CONFIG_FILE_PATH = Path(DATA_DIR) / "user_config.json"


@st.cache_resource
def get_llm_orchestrator() -> LLMOrchestrator:
    """Cria e cacheia o LLMOrchestrator."""
    print("--- DEBUG APP: Criando LLMOrchestrator (cache_resource)... ---")
    primary_provider = GeminiProvider(default_model=DEFAULT_GEMINI_MODEL)
    orchestrator = LLMOrchestrator(primary_provider=primary_provider)
    orchestrator.get_configured_llm()
    return orchestrator


@st.cache_data(show_spinner=False)
def get_user_config_service(username: str) -> UserConfigService:
    print(f"--- DEBUG APP: Criando UserConfigService para '{username}' ---")
    return UserConfigService(username)


@st.cache_data
def load_auth_config() -> dict[str, Any]:
    """Carrega o arquivo de configuração YAML."""
    try:
        with open("data/users.yaml") as file:
            config = yaml.load(file, Loader=SafeLoader)
            return config
    except FileNotFoundError:
        st.error("Arquivo 'data/users.yaml' não encontrado.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao ler 'data/users.yaml': {e}")
        st.stop()


def load_persistent_config() -> dict[str, Any]:
    """Carrega a configuração do arquivo JSON."""
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Erro ao ler arquivo de configuração '{CONFIG_FILE_PATH}': {e}")
            return {}  # Retorna dict vazio em caso de erro
    return {}


def save_persistent_config(config_data: dict) -> None:
    """Salva a configuração no arquivo JSON."""
    try:
        # Garante que o diretório data exista
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except OSError as e:
        print(f"Erro ao salvar arquivo de configuração '{CONFIG_FILE_PATH}': {e}")


def get_saved_planilha_path() -> str | None:
    """Retorna o caminho da planilha salvo na configuração, se existir e for válido."""
    config_data = load_persistent_config()
    path_str = config_data.get(PLANILHA_KEY)

    print(
        f"--- DEBUG CONFIG: get_saved_planilha_path | {path_str} | {config_data}. ---"
    )
    if not path_str:
        print("--- DEBUG CONFIG: Nenhuma planilha válida encontrada no config. ---")
        return None

    # 1. Primeiro, checa se é uma URL válida do Google Sheets
    if "docs.google.com/" in path_str:
        print(
            f"--- DEBUG CONFIG: Planilha Google Sheets encontrada em config: {path_str} ---"
        )
        return str(path_str)

    # 2. Se não for URL, checa se é um arquivo local
    planilha_path = Path(path_str)
    if planilha_path.is_file():
        print(f"--- DEBUG CONFIG: Planilha local encontrada em config: {path_str} ---")
        return str(path_str)
    else:
        print(
            f"--- DEBUG CONFIG WARN: Caminho '{path_str}' no config não é um arquivo válido. Ignorando. ---"
        )
        config_data.pop(PLANILHA_KEY, None)
        save_persistent_config(config_data)
        return None


def save_planilha_path(path_str: str) -> None:
    """Salva o caminho da planilha na configuração persistente."""
    print(f"--- DEBUG CONFIG: Salvando planilha '{path_str}' no config... ---")
    config_data = load_persistent_config()
    config_data[PLANILHA_KEY] = path_str
    save_persistent_config(config_data)


def verificar_perfil_preenchido(plan_manager: PlanilhaManager) -> bool:
    """Verifica se os campos essenciais do perfil foram preenchidos."""
    try:
        # 1. Lê os dados da memória do PlanilhaManager (que leu do disco)
        df_perfil = plan_manager.visualizar_dados(config.NomesAbas.PERFIL_FINANCEIRO)

        # 2. Verifica se a aba está literalmente vazia
        if df_perfil.empty:
            return False

        # 3. Verifica se a coluna "Campo" existe
        if "Campo" not in df_perfil.columns:
            return False

        try:
            # 4. Converte a tabela em um dicionário-like (Campo -> Valor)
            valores_perfil = df_perfil.set_index("Campo")["Valor"]

            # 5. Define os campos que DEVEM existir
            campos_essenciais = ["Renda Mensal Média", "Principal Objetivo"]

            # 6. Faz o loop e verifica
            for campo in campos_essenciais:
                if (
                    campo not in valores_perfil  # A chave existe?
                    or pd.isna(valores_perfil[campo])  # O valor é nulo (NaN)?
                    or str(valores_perfil[campo]).strip()
                    == ""  # O valor é uma string vazia?
                ):
                    return False  # Se qualquer campo essencial falhar, retorna Falso

            # 7. Se passou por todos os campos essenciais, está completo!
            return True
        except KeyError:
            return False  # Falha se .set_index() der erro
    except Exception:
        return False  # Falha genérica


@st.cache_resource
def get_llm_orchestrator() -> LLMOrchestrator:
    """Retorna uma instância cacheada do LLMOrchestrator."""
    print("\n--- DEBUG APP: Criando LLMOrchestrator (cache_resource)... ---")
    primary_provider = GeminiProvider(default_model=config.DEFAULT_GEMINI_MODEL)
    return LLMOrchestrator(primary_provider=primary_provider)


def check_onboarding_status() -> bool:
    """Verifica se o onboarding foi concluído."""
    return st.session_state.get("onboarding_complete", False)


def render_onboarding_ui() -> Any:
    """Renderiza a UI de upload de arquivo."""
    st.title("Para começar, importe sua Planilha Mestra")
    st.write(
        "Por favor, faça o upload do seu arquivo Excel (.xlsx) ou CSV (.csv) para iniciarmos a análise."
    )

    uploaded_file = st.file_uploader(
        "Selecione seu arquivo", type=["xlsx", "csv"], label_visibility="collapsed"
    )

    # Armazena o arquivo na sessão para ser pego pelo handle_onboarding_process
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    return uploaded_file


def handle_onboarding_process(llm_orchestrator: LLMOrchestrator) -> None:
    """Processa o arquivo enviado e completa o onboarding."""
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_file = st.session_state.uploaded_file

    if uploaded_file:
        try:
            # Salva o arquivo temporariamente
            temp_dir = Path(DATA_DIR) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file_path = temp_dir / uploaded_file.name

            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            print(f"--- DEBUG ONBOARDING: Arquivo salvo em '{temp_file_path}' ---")

            with st.spinner("Analisando o layout da sua planilha... 🤖"):
                llm = llm_orchestrator.get_configured_llm()
                strategy_generator = StrategyGenerator(llm)

                # 1. Analisa a planilha
                analysis = strategy_generator.analyze_spreadsheet(str(temp_file_path))
                print(f"--- DEBUG ONBOARDING: Análise da IA: {analysis} ---")

                # 2. Gera o código da estratégia
                strategy_code, strategy_name = (
                    strategy_generator.generate_strategy_code(analysis)
                )
                print(f"--- DEBUG ONBOARDING: Estratégia gerada: {strategy_name} ---")

                # 3. Salva a estratégia
                strategy_path = Path(config.STRATEGIES_DIR) / f"{strategy_name}.py"
                with open(strategy_path, "w", encoding="utf-8") as f:
                    f.write(strategy_code)
                print(
                    f"--- DEBUG ONBOARDING: Estratégia salva em '{strategy_path}' ---"
                )

                # 4. Salva a configuração persistente
                config_data = {
                    PLANILHA_KEY: str(temp_file_path),
                    "mapeamento": analysis,  # Salva a análise
                    "strategy_module": strategy_name,
                }
                save_persistent_config(config_data)

                # 5. Define o estado da sessão
                st.session_state[PLANILHA_KEY] = str(temp_file_path)
                st.session_state.onboarding_complete = True
                st.session_state.system_loaded = (
                    False  # Força o reload na próxima página
                )
                st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro durante a análise: {e}")
            st.exception(e)

        finally:
            # Limpa o arquivo da sessão
            st.session_state.uploaded_file = None


def create_excel_export_bytes(plan_manager: PlanilhaManager) -> bytes:
    """
    Pega o estado atual do PlanilhaManager e o converte em um
    arquivo Excel (.xlsx) em memória, retornando os bytes.
    """
    try:
        # Pega os componentes de dentro do PlanilhaManager
        strategy: BaseMappingStrategy = plan_manager._context.strategy
        dataframes_internos: dict[str, pd.DataFrame] = plan_manager._context.data

        output_buffer = io.BytesIO()

        with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
            # Reutiliza a mesma lógica de "unmap" que usamos nos handlers
            for internal_sheet_name, df_interno in dataframes_internos.items():
                sheet_name_to_save = strategy.get_sheet_name_to_save(
                    internal_sheet_name
                )

                df_para_salvar: pd.DataFrame

                if internal_sheet_name == config.NomesAbas.TRANSACOES:
                    df_para_salvar = strategy.unmap_transactions(df_interno)
                else:
                    df_para_salvar = strategy.map_other_sheet(
                        df_interno, internal_sheet_name
                    )

                df_para_salvar.to_excel(
                    writer, sheet_name=sheet_name_to_save, index=False
                )

        # Retorna o conteúdo do buffer em memória
        return output_buffer.getvalue()

    except Exception as e:
        st.error(f"Erro ao gerar o arquivo Excel: {e}")
        return b""  # Retorna bytes vazios em caso de falha


def initialize_session_auth() -> tuple[
    bool, str | None, UserConfigService | None, LLMOrchestrator | None
]:
    """
    Função MESTRE. Deve ser chamada no topo de CADA página.
    Renderiza o login, gerencia o estado e inicializa os serviços.
    Retorna (is_logged_in, username, config_service, llm_orchestrator)
    """

    auth_config = load_auth_config()
    llm_orchestrator = get_llm_orchestrator()

    authenticator = stauth.Authenticate(
        auth_config["credentials"],
        auth_config["cookie"]["name"],
        auth_config["cookie"]["key"],
        auth_config["cookie"]["expiry_days"],
    )

    # Renderiza o widget de login na *sidebar* para não travar a página
    # ou use st.empty() se preferir no centro
    with st.container():
        authenticator.login()

    if st.session_state["authentication_status"] is True:
        # --- USUÁRIO LOGADO ---
        username = st.session_state["username"]
        authenticator.logout("Sair", "sidebar")
        st.sidebar.title(f"Bem-vindo, {st.session_state['name']}!")

        # Inicializa os serviços
        config_service = get_user_config_service(username)
        return True, username, config_service, llm_orchestrator

    elif st.session_state["authentication_status"] is False:
        st.error("Usuário ou senha incorretos.")
        return False, None, None, None
    else:
        # (authentication_status is None)
        # --- NOVO FLUXO DE REGISTRO ---
        # (Movido do ui_login.py para cá)
        try:
            if authenticator.register_user(preauthorization=False):
                with open("data/users.yaml", "w") as file:
                    yaml.dump(auth_config, file, default_flow_style=False)
                st.success("Usuário registrado com sucesso! Por favor, faça o login.")
        except Exception as e:
            st.error(e)
        # --- FIM DO FLUXO DE REGISTRO ---

        st.warning("Por favor, faça o login ou crie uma conta para acessar o BudgetIA.")
        return False, None, None, None
