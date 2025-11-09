# src/web_app/onboarding_manager.py
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

# Importa do núcleo do sistema
import config
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from finance.planilha_manager import PlanilhaManager

# --- Importa o novo Gerador ---
from initialization.strategy_generator import StrategyGenerator

# Constantes de configuração
CONFIG_FILE_PATH = Path(config.DATA_DIR) / "user_config.json"


class OnboardingManager:
    """
    Gerencia o estado e a lógica do processo de onboarding do usuário,
    de forma independente da interface (Streamlit).
    """

    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.config_data: dict = self._load_persistent_config()
        self.planilha_path: str | None = self.get_saved_planilha_path()
        self.llm_orchestrator = llm_orchestrator
        self.max_retries: int = 3
        self.current_state: str = "INIT"
        self._determine_initial_state()
        print("--- DEBUG OnboardingManager: Instanciado com LLMOrchestrator. ---")

    def _determine_initial_state(self) -> None:
        # (Estado salvo de fallback)
        if self.config_data.get("onboarding_state") == "STRATEGY_FAILED_FALLBACK":
            self.current_state = "STRATEGY_FAILED_FALLBACK"
        elif self.is_planilha_setup_complete():
            self.current_state = "SETUP_COMPLETE"
        else:
            self.current_state = "AWAITING_FILE_SELECTION"
        print(f"--- DEBUG OB_MGR: Estado inicial: {self.current_state} ---")

    # --- Métodos de Config/Utils (permanecem os mesmos) ---

    def _load_persistent_config(self) -> dict:  # Modificado para dict
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
        # (Lógica permanece a mesma)
        path_str = self.config_data.get(config.PLANILHA_KEY)
        if path_str:
            if Path(path_str).is_file():
                return path_str
            self.config_data.pop(config.PLANILHA_KEY, None)
            self._save_persistent_config()
        return None

    def _save_planilha_path(self, path_str: str) -> None:
        """Salva o caminho da planilha na configuração persistente."""
        print(f"--- DEBUG OB_MGR: Salvando planilha '{path_str}' no config... ---")
        self.config_data[config.PLANILHA_KEY] = path_str
        # Limpa o estado de fallback se salvarmos com sucesso
        self.config_data.pop("onboarding_state", None)
        self.config_data.pop("pending_planilha_path", None)
        self._save_persistent_config()
        self.planilha_path = path_str

    def reset_config(self) -> None:
        """Limpa a configuração da planilha e o estado."""
        print("--- DEBUG OB_MGR: Resetando configuração. ---")
        self.config_data = {}  # Limpa tudo
        self._save_persistent_config()
        self.planilha_path = None
        self.set_state("AWAITING_FILE_SELECTION")

    # --- Métodos de Lógica de Estado ---

    def get_current_state(self) -> str:
        return self.current_state

    def set_state(self, new_state: str):
        print(
            f"--- DEBUG OB_MGR: Mudando estado de {self.current_state} -> {new_state} ---"
        )
        self.current_state = new_state
        # Salva o estado de fallback no config
        if new_state == "STRATEGY_FAILED_FALLBACK":
            self.config_data["onboarding_state"] = "STRATEGY_FAILED_FALLBACK"
            self._save_persistent_config()

    # --- Fase 1: Lógica de Setup da Planilha ---

    def is_planilha_setup_complete(self) -> bool:
        """Verifica se a Fase 1 (seleção da planilha) está completa."""
        return self.planilha_path is not None

    def create_new_planilha(
        self, path_str: str, validation_callback: Callable[[str], tuple[Any, ...]]
    ) -> tuple[bool, str]:
        """Lógica para criar uma nova planilha (Estratégia Padrão)."""
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
            temp_pm, _, _, _ = validation_callback(str(novo_path))
            if not temp_pm:
                return False, "Falha ao inicializar o sistema com a nova planilha."

            self._save_planilha_path(
                str(novo_path)
            )  # Salva só o caminho (usará EstrategiaPadrao)
            self.set_state("SETUP_COMPLETE")
            return True, f"Planilha criada: '{novo_path}'!"
        except Exception as e:
            return False, f"Erro ao criar ou inicializar planilha: {e}"

    def _processar_planilha_customizada(self) -> tuple[bool, str]:
        """Tenta o Plano A (IA) e muda o estado para Fallback (B/C) se falhar."""
        path_str = self.config_data.get("pending_planilha_path")
        if not path_str:
            return False, "Erro: Caminho da planilha pendente não encontrado."

        try:
            generator = StrategyGenerator(self.llm_orchestrator, self.max_retries)

            # 1. GERAR E VALIDAR A ESTRATÉGIA
            success, result_message = generator.generate_and_validate_strategy(path_str)

            if success:
                # --- ESTA É A CORREÇÃO CRÍTICA ---
                mapa_config = json.loads(result_message)

                self.config_data["mapeamento"] = mapa_config  # Salva o dict
                self._save_planilha_path(path_str)  # Salva o caminho E o mapa

                self.set_state("SETUP_COMPLETE")
                return (
                    True,
                    f"Sucesso! A IA criou a estratégia '{mapa_config.get('strategy_module')}'.",
                )

            else:  # 3. FALHA (PLANO A falhou)
                print(
                    f"--- DEBUG OB_MGR: Geração de estratégia falhou. Erro: {result_message} ---"
                )
                # Ativa o fallback
                self.set_state("STRATEGY_FAILED_FALLBACK")
                return (
                    False,
                    f"A IA não conseguiu criar um código para sua planilha. Erro: {result_message}",
                )

        except Exception as e:
            print(
                f"--- DEBUG OB_MGR: Erro crítico no _processar_planilha_customizada: {e}"
            )
            self.set_state("STRATEGY_FAILED_FALLBACK")
            return False, f"Um erro inesperado ocorreu: {e}"

    def set_planilha_from_path(self, path_str: str) -> tuple[bool, str]:
        """
        Lógica para usar uma planilha por caminho existente.
        APENAS valida o caminho e define o estado de GERAÇÃO.
        """
        path_obj = Path(path_str)
        if not path_obj.is_file():
            return False, f"Arquivo não encontrado: {path_str}"
        if not path_obj.name.endswith(".xlsx"):
            return False, "O arquivo deve ser .xlsx"

        # Salva o caminho que a IA precisa processar
        self.config_data["pending_planilha_path"] = path_str
        self._save_persistent_config()

        # Apenas define o estado. NÃO chama _processar_planilha_customizada.
        self.set_state("GENERATING_STRATEGY")
        return True, "Caminho válido. Iniciando geração de estratégia..."

    def handle_uploaded_planilha(
        self,
        uploaded_file: Any,
        save_dir: str,
    ) -> tuple[bool, str]:
        """
        Lógica para salvar um arquivo carregado.
        APENAS salva o arquivo e define o estado de GERAÇÃO.
        """
        save_path = Path(save_dir) / uploaded_file.name
        try:
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Salva o caminho que a IA precisa processar
            self.config_data["pending_planilha_path"] = str(save_path)
            self._save_persistent_config()

            # Apenas define o estado. NÃO chama _processar_planilha_customizada.
            self.set_state("GENERATING_STRATEGY")
            return True, "Upload concluído. Iniciando geração de estratégia..."

        except Exception as e:
            # (Limpeza em caso de falha no salvamento)
            if save_path.exists():
                try:
                    os.remove(save_path)
                except OSError:
                    pass
            return False, f"Erro ao salvar planilha: {e}"

    # --- Fase 2: Lógica de Setup do Perfil (permanece a mesma) ---

    def verificar_perfil_preenchido(self, plan_manager: PlanilhaManager) -> bool:
        # ... (código idêntico ao anterior) ...
        try:
            df_perfil = plan_manager.visualizar_dados(
                config.NomesAbas.PERFIL_FINANCEIRO
            )
            if df_perfil.empty or "Campo" not in df_perfil.columns:
                return False
            try:
                valores_perfil = df_perfil.set_index("Campo")["Valor"]
            except KeyError:
                valores_perfil = pd.Series(
                    dict(zip(df_perfil["Campo"], df_perfil["Valor"]))
                )
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
        # ... (código idêntico ao anterior) ...
        prompt_guiado = (
            f"O usuário respondeu: '{user_input}'.\n"
            "Seu ÚNICO objetivo é extrair DADOS DE PERFIL (especificamente 'Renda Mensal Média' ou 'Principal Objetivo') desta resposta. "
            "Use a ferramenta 'coletar_perfil_usuario' IMEDIATAMENTE para salvar o par 'campo' e 'valor'. "
            "Após salvar, confirme e faça a próxima pergunta (Renda ou Objetivo). "
            "Se não conseguir extrair, peça novamente."
        )
        try:
            return agent_runner.interagir(prompt_guiado)
        except Exception as e:
            print(f"--- DEBUG ONBOARDING ERROR: {e} ---")
            return f"Ocorreu um erro ao processar sua resposta: {e}"

    # --- Lógica do Plano B (Importação Guiada) ---

    def start_guided_import(self, file_path_usuario: str) -> tuple[bool, str]:
        """
        Plano B: A IA gera um MAPEAMENTO JSON (não um código)
        para importar os dados para a NOSSA planilha padrão.
        """
        self.set_state("GUIDED_IMPORT_MAPPING")
        # TODO: Implementar a lógica onde a IA gera o JSON
        # Por enquanto, apenas mudamos o estado
        return (
            True,
            "Vamos iniciar a importação guiada. Por favor, me ajude a mapear suas colunas.",
        )
