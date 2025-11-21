# src/web_app/onboarding_manager.py
import json
import os
from collections.abc import Callable
from enum import Enum, auto
from pathlib import Path
from typing import Any

import pandas as pd

# Importa do núcleo do sistema
import config
from core.agent_runner_interface import AgentRunner
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from finance.planilha_manager import PlanilhaManager
from initialization.file_preparer import FileAnalysisPreparer

# --- Importa o novo Gerador ---
from initialization.strategy_generator import StrategyGenerator

# --- 1. IMPORTAR AS FUNÇÕES DE UTILS ---
# (Vamos usar as funções centralizadas em vez de duplicá-las)


class OnboardingState(Enum):
    """Define os estados da máquina de onboarding."""

    INIT = auto()
    AWAITING_FILE_SELECTION = auto()
    AWAITING_BACKEND_CONSENT = auto()
    GENERATING_STRATEGY = auto()
    STRATEGY_FAILED_FALLBACK = auto()
    GUIDED_IMPORT_MAPPING = auto()
    SETUP_COMPLETE = auto()


class OnboardingManager:
    """
    Gerencia o estado e a lógica do processo de onboarding do usuário,
    de forma independente da interface (Streamlit).
    """

    def __init__(
        self, llm_orchestrator: LLMOrchestrator, config_service: UserConfigService
    ):
        self.config_service = config_service
        self.llm_orchestrator = llm_orchestrator
        self.max_retries: int = 3

        self.planilha_path: str | None = self.config_service.get_planilha_path()

        # --- 2. TIPO DE ESTADO ATUALIZADO ---
        self.current_state: OnboardingState = OnboardingState.INIT

        self._determine_initial_state()
        print("--- DEBUG OnboardingManager: Instanciado com LLMOrchestrator. ---")

    def _determine_initial_state(self) -> None:
        # Lê a string salva no config
        saved_state_str = self.config_service.get_onboarding_state()

        if saved_state_str == OnboardingState.STRATEGY_FAILED_FALLBACK.name:
            self.current_state = OnboardingState.STRATEGY_FAILED_FALLBACK
        elif self.planilha_path is not None:
            self.current_state = OnboardingState.SETUP_COMPLETE
        else:
            self.current_state = OnboardingState.AWAITING_FILE_SELECTION

        print(f"--- DEBUG OB_MGR: Estado inicial: {self.current_state.name} ---")

    def get_current_state(self) -> OnboardingState:
        """Retorna o objeto Enum do estado atual."""
        return self.current_state

    def set_state(self, new_state: OnboardingState) -> None:
        """Define o estado usando o Enum e salva seu nome (string)."""
        if not isinstance(new_state, OnboardingState):
            raise TypeError("set_state deve ser chamado com um membro OnboardingState.")

        print(
            f"--- DEBUG OB_MGR: Mudando estado de {self.current_state.name} -> {new_state.name} ---"
        )
        self.current_state = new_state

        # Salva o NOME (string) do enum no config
        if new_state == OnboardingState.STRATEGY_FAILED_FALLBACK:
            self.config_service.save_onboarding_state(new_state.name)

    def get_saved_planilha_path(self) -> str | None:
        # Delega ao serviço
        return self.config_service.get_planilha_path()

    def _save_planilha_path(self, path_str: str) -> None:
        """Salva o caminho da planilha usando o serviço."""
        print(
            f"--- DEBUG OB_MGR: Salvando planilha '{path_str}' via config service... ---"
        )
        self.config_service.save_planilha_path(path_str)
        self.planilha_path = path_str

    def reset_config(self) -> None:
        """Limpa a configuração da planilha e o estado."""
        print("--- DEBUG OB_MGR: Resetando configuração. ---")
        self.config_service.clear_config()
        self.planilha_path = None
        self.set_state(OnboardingState.AWAITING_FILE_SELECTION)

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
            self.set_state(OnboardingState.SETUP_COMPLETE)
            return True, f"Planilha criada: '{novo_path}'!"
        except Exception as e:
            return False, f"Erro ao criar ou inicializar planilha: {e}"

    def _processar_planilha_customizada(self) -> tuple[bool, str]:
        """Tenta o Plano A (IA) e muda o estado para Fallback (B/C) se falhar."""
        path_str = self.config_service.get_pending_planilha_path()
        if not path_str:
            return False, "Erro: Caminho da planilha pendente não encontrado."

        # 1. Delega a preparação do arquivo (download/conversão)
        preparer = FileAnalysisPreparer(path_str)
        generator = StrategyGenerator(self.llm_orchestrator, self.max_retries)

        path_para_analise = ""
        strategy_path = self.config_service.strategy_file_path
        try:
            path_para_analise = preparer.get_local_path()

            # --- 1. SEU INSIGHT DE REUTILIZAÇÃO ---
            if strategy_path.exists():
                print(
                    f"--- DEBUG OB_MGR: Testando estratégia existente em {strategy_path}... ---"
                )

                # Chama o novo método público do generator
                success, msg = generator.validate_existing_strategy(
                    strategy_path, path_para_analise
                )
                if success:
                    print(
                        "--- DEBUG OB_MGR: Estratégia existente é válida! Reutilizando. ---"
                    )

                    # O mapeamento já deve existir, mas salvamos o path
                    # para garantir que o 'mapeamento' no config está correto
                    mapa_config = {"strategy_module": strategy_path.stem}
                    self.config_service.save_mapeamento(mapa_config)

                    self._save_planilha_path(path_str)  # Salva o link da planilha
                    self.set_state(OnboardingState.SETUP_COMPLETE)
                    return True, "Sucesso! A IA reutilizou sua estratégia existente."
                else:
                    print(
                        f"--- DEBUG OB_MGR: Estratégia existente falhou ({msg}). Gerando uma nova... ---"
                    )
            # --- FIM DA REUTILIZAÇÃO ---

            # --- 2. FLUXO NORMAL DE GERAÇÃO ---
            print(
                f"--- DEBUG OB_MGR: Enviando '{path_para_analise}' para o StrategyGenerator (Salvar em: {strategy_path})... ---"
            )

            success, result_message_json = generator.generate_and_validate_strategy(
                path_para_analise,
                strategy_path,  # Passa o caminho de salvamento do usuário
            )

            if success:
                # O result_message_json é o JSON: {"strategy_module": "user_strategy"}
                mapa_config = json.loads(result_message_json)

                # Salva o mapeamento (que contém o nome do módulo)
                self.config_service.save_mapeamento(mapa_config)

                self._save_planilha_path(path_str)
                self.set_state(OnboardingState.SETUP_COMPLETE)
                return (
                    True,
                    f"Sucesso! A IA criou a estratégia '{mapa_config.get('strategy_module')}'.",
                )
            else:
                self.set_state(OnboardingState.STRATEGY_FAILED_FALLBACK)
                return False, result_message_json  # Retorna o erro da IA

        except Exception as e:
            print(
                f"--- DEBUG OB_MGR: Erro crítico no _processar_planilha_customizada: {e}"
            )
            self.set_state(OnboardingState.STRATEGY_FAILED_FALLBACK)
            return False, f"Um erro inesperado ocorreu: {e}"

        finally:
            preparer.cleanup()

    # --- 4. CORRIGIR A LÓGICA DE 'set_planilha_from_path' ---
    # (Para aceitar URLs do Google Sheets)
    def set_planilha_from_path(self, path_str: str) -> tuple[bool, str]:
        """
        Lógica para usar uma planilha por caminho existente.
        Valida o caminho (arquivo local OU URL GSheets) e define o estado de GERAÇÃO.
        """
        path_str = path_str.strip().strip('"')
        if not path_str:
            return False, "O caminho/link não pode ser vazio."

        # Salva o caminho que a IA precisa processar
        self.config_service.save_pending_planilha_path(path_str)

        # O estado é SEMPRE 'GENERATING_STRATEGY' (que agora também testa re-uso)
        self.set_state(OnboardingState.GENERATING_STRATEGY)
        return True, "Caminho salvo. Iniciando análise e geração de estratégia..."

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
            self.config_service.save_pending_planilha_path(str(save_path))

            # Apenas define o estado. NÃO chama _processar_planilha_customizada.
            self.set_state(OnboardingState.GENERATING_STRATEGY)
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
        self.set_state(OnboardingState.GUIDED_IMPORT_MAPPING)
        # TODO: Implementar a lógica onde a IA gera o JSON
        # Por enquanto, apenas mudamos o estado
        return (
            True,
            "Vamos iniciar a importação guiada. Por favor, me ajude a mapear suas colunas.",
        )

    def set_google_file_selection(self, file_url: str) -> None:
        """
        Chamado quando o usuário seleciona um arquivo do Google Drive.
        Salva o arquivo e transiciona para a tela de consentimento.

        Args:
            file_url (str): A URL (webViewLink) do arquivo selecionado.
        """
        print(
            f"--- DEBUG OB_MGR: Usuário selecionou o arquivo Google URL: {file_url} ---"
        )

        # 1. Salva a URL para o FileAnalysisPreparer usar depois
        self.config_service.save_pending_planilha_path(file_url)

        # 2. Muda o estado (NÃO chama st.rerun() aqui)
        self.set_state(OnboardingState.AWAITING_BACKEND_CONSENT)
