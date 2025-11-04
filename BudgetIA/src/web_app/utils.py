# Em: src/web_app/utils.py (ou config_manager.py)
import json
from pathlib import Path

import pandas as pd

import config

# Importar DATA_DIR do config
from config import DATA_DIR
from finance.planilha_manager import PlanilhaManager

CONFIG_FILE_PATH = Path(DATA_DIR) / "user_config.json"
PLANILHA_KEY = "planilha_path"  # Chave dentro do JSON


def load_persistent_config() -> dict[str, str]:
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
    if path_str:
        planilha_path = Path(path_str)
        if planilha_path.is_file():
            print(f"--- DEBUG CONFIG: Planilha encontrada em config: {path_str} ---")
            return path_str
        else:
            print(
                f"--- DEBUG CONFIG WARN: Caminho '{path_str}' no config não é um arquivo válido. Ignorando. ---"
            )
            # Opcional: Limpar a chave inválida do config
            # config_data.pop(PLANILHA_KEY, None)
            # save_persistent_config(config_data)
            return None
    print("--- DEBUG CONFIG: Nenhuma planilha válida encontrada no config. ---")
    return None


def save_planilha_path(path_str: str) -> None:
    """Salva o caminho da planilha na configuração persistente."""
    print(f"--- DEBUG CONFIG: Salvando planilha '{path_str}' no config... ---")
    config_data = load_persistent_config()
    config_data[PLANILHA_KEY] = path_str
    save_persistent_config(config_data)


def verificar_perfil_preenchido(plan_manager: PlanilhaManager) -> bool:
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
