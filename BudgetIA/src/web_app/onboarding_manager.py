# src/web_app/onboarding_manager.py
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

# Importa do núcleo do sistema
import config
from core.agent_runner_interface import AgentRunner
from finance.planilha_manager import PlanilhaManager

# Constantes de configuração
CONFIG_FILE_PATH = Path(config.DATA_DIR) / "user_config.json"
PLANILHA_KEY = "planilha_path"


class OnboardingManager:
    """
    Gerencia o estado e a lógica do processo de onboarding do usuário,
    de forma independente da interface (Streamlit).
    """

    def __init__(self) -> None:
        self.config_data: dict = self._load_persistent_config()
        self.planilha_path: str | None = self.get_saved_planilha_path()
        print("--- DEBUG OnboardingManager: Instanciado. ---")

    # --- Métodos de Config/Utils (Movidos de utils.py) ---

    def _load_persistent_config(self) -> dict[str, str]:
        """Carrega a configuração do arquivo JSON."""
        if CONFIG_FILE_PATH.exists():
            try:
                with open(CONFIG_FILE_PATH, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Erro ao ler config: {e}")
                return {}
        return {}

    def _save_persistent_config(self) -> None:
        """Salva a configuração no arquivo JSON."""
        try:
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
        except OSError as e:
            print(f"Erro ao salvar config: {e}")

    def get_saved_planilha_path(self) -> str | None:
        """Retorna o caminho da planilha salvo na configuração, se existir e for válido."""
        path_str = self.config_data.get(PLANILHA_KEY)
        if path_str:
            planilha_path = Path(path_str)
            if planilha_path.is_file():
                print(f"--- DEBUG OB_MGR: Planilha válida em config: {path_str} ---")
                return path_str
            else:
                print(f"--- DEBUG OB_MGR WARN: Caminho '{path_str}' inválido. ---")
                self.config_data.pop(PLANILHA_KEY, None)
                self._save_persistent_config()
                return None
        return None

    def _save_planilha_path(self, path_str: str) -> None:
        """Salva o caminho da planilha na configuração persistente."""
        print(f"--- DEBUG OB_MGR: Salvando planilha '{path_str}' no config... ---")
        self.config_data[PLANILHA_KEY] = path_str
        self._save_persistent_config()
        self.planilha_path = path_str

    def reset_config(self) -> None:
        """Limpa a configuração da planilha."""
        print("--- DEBUG OB_MGR: Resetando configuração. ---")
        self.config_data.pop(PLANILHA_KEY, None)
        self._save_persistent_config()
        self.planilha_path = None

    # --- Fase 1: Lógica de Setup da Planilha ---

    def is_planilha_setup_complete(self) -> bool:
        """Verifica se a Fase 1 (seleção da planilha) está completa."""
        return self.planilha_path is not None

    def create_new_planilha(
        self, path_str: str, validation_callback: Any
    ) -> tuple[bool, str]:
        """
        Lógica de negócios para criar uma nova planilha.
        Recebe um 'validation_callback' para testar a inicialização.
        """
        novo_path = Path(path_str)
        if not novo_path.name.endswith(".xlsx"):
            return False, "O nome do arquivo deve terminar com .xlsx"
        if novo_path.exists():
            return (
                False,
                f"O arquivo '{novo_path}' já existe. Use a opção 'Usar Existente'.",
            )

        try:
            novo_path.parent.mkdir(parents=True, exist_ok=True)
            # Chama o callback de validação (ex: initialize_financial_system)
            temp_pm, _, _, _ = validation_callback(str(novo_path))
            if not temp_pm:
                return False, "Falha ao inicializar o sistema com a nova planilha."

            self._save_planilha_path(str(novo_path))
            return True, f"Planilha criada: '{novo_path}'!"
        except Exception as e:
            return False, f"Erro ao criar ou inicializar planilha: {e}"

    def set_planilha_from_path(
        self, path_str: str, validation_callback: Any
    ) -> tuple[bool, str]:
        """Lógica para usar uma planilha por caminho existente."""
        path_obj = Path(path_str)
        if not path_obj.is_file():
            return False, f"Arquivo não encontrado: {path_str}"
        if not path_obj.name.endswith(".xlsx"):
            return False, "O arquivo deve ser .xlsx"

        try:
            temp_pm, _, _, _ = validation_callback(str(path_obj))
            if not temp_pm:
                return False, "Não foi possível carregar o sistema com esta planilha."

            self._save_planilha_path(str(path_obj))
            return True, f"Usando: {path_obj}"
        except Exception as e:
            return False, f"Erro ao carregar do caminho '{path_obj}': {e}"

    def handle_uploaded_planilha(
        self, uploaded_file: Any, save_dir: str, validation_callback: Any
    ) -> tuple[bool, str]:
        """Lógica para salvar e validar um arquivo carregado."""
        save_path = Path(save_dir) / uploaded_file.name
        try:
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            temp_pm, _, _, _ = validation_callback(str(save_path))
            if not temp_pm:
                if save_path.exists():
                    os.remove(save_path)
                return False, "Planilha inválida. Não foi possível carregar o sistema."

            self._save_planilha_path(str(save_path))
            return True, f"Planilha '{uploaded_file.name}' carregada!"
        except Exception as e:
            if save_path.exists():
                try:
                    os.remove(save_path)
                except OSError:
                    pass
            return False, f"Erro ao processar planilha: {e}"

    # --- Fase 2: Lógica de Setup do Perfil ---

    def verificar_perfil_preenchido(self, plan_manager: PlanilhaManager) -> bool:
        """Verifica se os campos essenciais do perfil estão preenchidos."""
        try:
            df_perfil = plan_manager.visualizar_dados(
                config.NomesAbas.PERFIL_FINANCEIRO
            )
            if df_perfil.empty or "Campo" not in df_perfil.columns:
                return False

            valores_perfil = df_perfil.set_index("Campo")["Valor"]
            campos_essenciais = ["Renda Mensal Média", "Principal Objetivo"]

            for campo in campos_essenciais:
                if (
                    campo not in valores_perfil
                    or pd.isna(valores_perfil[campo])
                    or str(valores_perfil[campo]).strip() == ""
                ):
                    return False
            return True
        except Exception:
            return False

    def process_profile_input(self, user_input: str, agent_runner: AgentRunner) -> str:
        """Processa a entrada do usuário durante o onboarding do perfil."""
        prompt_guiado = (
            f"O usuário respondeu: '{user_input}'.\n"
            "Seu ÚNICO objetivo é extrair DADOS DE PERFIL (especificamente 'Renda Mensal Média' ou 'Principal Objetivo') desta resposta. "
            "Se você extrair um dado, use a ferramenta 'coletar_perfil_usuario' IMEDIATAMENTE para salvar o par 'campo' e 'valor' (ex: campo='Renda Mensal Média', valor=5000). "
            "Após salvar, confirme o que salvou e faça a próxima pergunta (se a Renda foi dada, pergunte o Objetivo; se o Objetivo foi dado, pergunte a Renda). "
            "Se você não conseguir extrair um dado válido, peça educadamente pela informação novamente (Renda ou Objetivo)."
            "NÃO use outras ferramentas. NÃO responda a perguntas aleatórias. Foque 100% em preencher o perfil."
        )

        try:
            output = agent_runner.interagir(prompt_guiado)
            return output
        except Exception as e:
            print(f"--- DEBUG ONBOARDING ERROR: {e} ---")
            return f"Ocorreu um erro ao processar sua resposta: {e}"
