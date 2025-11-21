# src/initialization/onboarding/orchestrator.py
import logging
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from initialization.onboarding.agent import OnboardingAgent
from initialization.onboarding.analyzers import (
    FinancialStrategy,
    ProfileAnalyzer,
    StrategySuggester,
    UserProfile,
)
from initialization.onboarding.file_handlers import (
    AcquisitionResult,
    DefaultSpreadsheetHandler,
    GoogleSheetsHandler,
    IFileHandler,
    UploadHandler,
)
from initialization.onboarding.state_machine import (
    OnboardingState,
    OnboardingStateMachine,
)

logger = logging.getLogger(__name__)


class OnboardingOrchestrator:
    """
    Coordenador central do processo de onboarding.
    Gerencia estado, persistência e lógica de negócios.
    """

    def __init__(
        self, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator
    ):
        self.config_service = config_service
        self.llm_orchestrator = llm_orchestrator

        # Inicializa máquina de estados
        self.state_machine = OnboardingStateMachine()

        # Inicializa handlers
        self.file_handlers: list[IFileHandler] = [
            DefaultSpreadsheetHandler(),
            UploadHandler(),
            GoogleSheetsHandler(),
        ]

        # Inicializa Agente e Analyzers
        self.agent = OnboardingAgent(llm_orchestrator)
        self.profile_analyzer = ProfileAnalyzer(llm_orchestrator)
        self.strategy_suggester = StrategySuggester()

        # Contexto temporário
        self._context: dict[str, Any] = {}
        self._user_profile: UserProfile | None = None
        self._suggested_strategy: FinancialStrategy | None = None

    def get_current_state(self) -> OnboardingState:
        return self.state_machine.current_state

    def get_progress(self) -> float:
        return self.state_machine.get_progress()

    def process_user_input(self, text: str, extra_context: dict | None = None) -> str:
        """
        Processa entrada do usuário (texto ou ação de UI).
        Retorna a resposta do sistema (texto para o chat).
        """
        if extra_context:
            self._context.update(extra_context)

        current_state = self.state_machine.current_state

        # Limpa emojis e normaliza texto para comparação
        clean_text = (
            text.lower()
            .replace("🚀", "")
            .replace("📤", "")
            .replace("☁️", "")
            .replace("🧠", "")
            .replace("✅", "")
            .replace("⚡", "")
            .strip()
        )

        # LOG: Entrada do usuário
        print(
            f"\n[ONBOARDING] Estado={current_state.name} | User Input: '{text}' | Clean: '{clean_text}'"
        )
        logger.info(f"[ONBOARDING] Estado={current_state.name} | User Input: '{text}'")

        # Lógica específica por estado
        if current_state == OnboardingState.WELCOME:
            response = self._handle_welcome(clean_text)
            print(f"[ONBOARDING] Response: '{response}'")
            logger.info(f"[ONBOARDING] Response: '{response}'")
            return response

        elif current_state == OnboardingState.SPREADSHEET_ACQUISITION:
            response = self._handle_acquisition(text)  # Mantém original para handlers
            print(f"[ONBOARDING] Response: '{response}'")
            logger.info(f"[ONBOARDING] Response: '{response}'")
            return response

        elif current_state == OnboardingState.TRANSLATION_REVIEW:
            # Permite avançar para próximo estado
            if clean_text in [
                "continuar",
                "avançar",
                "próximo",
                "ok",
                "tudo certo",
                "confirmar",
                "começar a usar",
            ]:
                self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
                response = "Ótimo! Agora vamos configurar seu perfil financeiro. Posso gerar uma estratégia personalizada para você ou podemos pular direto para o sistema."
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            response = self.agent.chat(text, current_state)
            print(f"[ONBOARDING] Agent Response: '{response}'")
            logger.info(f"[ONBOARDING] Agent Response: '{response}'")
            return response

        elif current_state == OnboardingState.OPTIONAL_PROFILE:
            # Se o usuário pedir para gerar estratégia
            if clean_text in [
                "gerar estratégia",
                "gerar estrategia",
                "ver estratégia",
                "ver estrategia",
            ]:
                print("[ONBOARDING] Comando reconhecido: Gerar Estratégia")
                self._generate_strategy_and_advance()
                response = "Analisei seu perfil! Aqui está uma sugestão de estratégia para você."
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            # Se pulou, finaliza o onboarding
            elif clean_text in [
                "pular",
                "pular para o final",
                "finalizar",
                "começar a usar",
                "comecar a usar",
            ]:
                print("[ONBOARDING] Comando reconhecido: Finalizar")
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()  # Finaliza e salva configurações
                response = "Perfeito! Você está pronto para começar. Vou carregar o sistema agora! 🚀"
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            response = self.agent.chat(text, current_state)
            print(f"[ONBOARDING] Agent Response: '{response}'")
            logger.info(f"[ONBOARDING] Agent Response: '{response}'")
            return response

        elif current_state == OnboardingState.OPTIONAL_STRATEGY:
            # Aceita ou personaliza estratégia
            if clean_text in [
                "aceitar sugestão",
                "aceitar sugestao",
                "aceitar",
                "usar esta",
            ]:
                print("[ONBOARDING] Comando reconhecido: Aceitar Sugestão")
                # TODO: Salvar estratégia escolhida no config
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()  # Finaliza e salva configurações
                response = "Estratégia salva! Você está pronto para começar. Vou carregar o sistema agora! 🚀"
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            elif clean_text in ["personalizar", "customizar"]:
                # TODO: Implementar customização
                response = "Customização manual ainda não implementada. Vou usar a sugestão padrão."
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            elif clean_text in [
                "pular",
                "finalizar",
                "começar a usar",
                "comecar a usar",
            ]:
                print("[ONBOARDING] Comando reconhecido: Finalizar")
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()  # Finaliza e salva configurações
                response = "Entendido! Você está pronto para começar. Vou carregar o sistema agora! 🚀"
                print(f"[ONBOARDING] Response: '{response}'")
                logger.info(f"[ONBOARDING] Response: '{response}'")
                return response
            response = self.agent.chat(text, current_state)
            print(f"[ONBOARDING] Agent Response: '{response}'")
            logger.info(f"[ONBOARDING] Agent Response: '{response}'")
            return response

        elif current_state == OnboardingState.COMPLETE:
            response = self.agent.chat(text, current_state)
            print(f"[ONBOARDING] Agent Response: '{response}'")
            logger.info(f"[ONBOARDING] Agent Response: '{response}'")
            return response

        response = "Estado não reconhecido ou não implementado."
        print(f"[ONBOARDING] Estado não tratado: {current_state.name}")
        logger.warning(f"[ONBOARDING] Estado não tratado: {current_state.name}")
        return response

    def _handle_welcome(self, text: str) -> str:
        if text.lower() in ["começar", "começar agora", "iniciar"]:
            self.state_machine.transition_to(OnboardingState.SPREADSHEET_ACQUISITION)
            return "Ótimo! Vamos configurar sua planilha. Você prefere criar uma nova, fazer upload ou conectar o Google Sheets?"
        return self.agent.chat(text, OnboardingState.WELCOME)

    def _handle_acquisition(self, text: str) -> str:
        print(
            f"[ONBOARDING] Processing acquisition, checking {len(self.file_handlers)} handlers"
        )
        logger.info(
            f"[ONBOARDING] Processing acquisition, checking {len(self.file_handlers)} handlers"
        )
        for idx, handler in enumerate(self.file_handlers):
            can_handle = handler.can_handle(text)
            print(
                f"[ONBOARDING] Handler {idx} ({handler.__class__.__name__}): can_handle={can_handle}"
            )
            logger.info(
                f"[ONBOARDING] Handler {idx} ({handler.__class__.__name__}): can_handle={can_handle}"
            )
            if can_handle:
                # Inject username into context for handlers that need it
                if "username" not in self._context:
                    self._context["username"] = self.config_service.username

                if "save_dir" not in self._context:
                    self._context["save_dir"] = str(Path.cwd() / "data")

                print(
                    f"[ONBOARDING] Calling handler.acquire() with context keys: {list(self._context.keys())}"
                )
                logger.info(
                    f"[ONBOARDING] Calling handler.acquire() with context: {self._context}"
                )
                result = handler.acquire(self._context)
                print(
                    f"[ONBOARDING] Handler result: success={result.success}, handler_type={result.handler_type}, requires_ui={result.requires_ui_action}"
                )
                logger.info(
                    f"[ONBOARDING] Handler result: success={result.success}, handler_type={result.handler_type}, requires_ui={result.requires_ui_action}"
                )

                if result.success:
                    self._finalize_acquisition(result)
                    success_msg = f"Planilha definida em: {result.file_path}"
                    print(f"[ONBOARDING] Acquisition SUCCESS: {success_msg}")
                    logger.info(f"[ONBOARDING] Acquisition SUCCESS: {success_msg}")
                    return success_msg
                elif result.requires_ui_action:
                    error_msg = result.error_message or "Ação de UI necessária"
                    response = f"[UI_ACTION:{result.requires_ui_action}] {error_msg}"
                    print(
                        f"[ONBOARDING] UI Action requested: {result.requires_ui_action}"
                    )
                    logger.info(
                        f"[ONBOARDING] UI Action requested: {result.requires_ui_action}"
                    )
                    return response
                else:
                    error_msg = result.error_message or "Erro ao processar solicitação"
                    print(f"[ONBOARDING] Handler FAILED: {error_msg}")
                    logger.warning(f"[ONBOARDING] Handler FAILED: {error_msg}")
                    return error_msg

        print("[ONBOARDING] No handler matched, delegating to agent")
        logger.info("[ONBOARDING] No handler matched, delegating to agent")
        return self.agent.chat(text, OnboardingState.SPREADSHEET_ACQUISITION)

    def _finalize_acquisition(self, result: AcquisitionResult):
        print(
            f"[ONBOARDING] Finalizing acquisition: file_path={result.file_path}, handler_type={result.handler_type}"
        )
        logger.info(
            f"[ONBOARDING] Finalizing acquisition: file_path={result.file_path}, handler_type={result.handler_type}"
        )
        if result.file_path:
            self.config_service.save_pending_planilha_path(result.file_path)

        if result.handler_type == "default":
            self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
        else:
            self.state_machine.transition_to(OnboardingState.TRANSLATION_REVIEW)

    def _generate_strategy_and_advance(self):
        """Gera perfil e estratégia baseados no histórico do agente."""
        # Extrai histórico de texto do agente
        chat_history = [
            msg.content for msg in self.agent.history if isinstance(msg, HumanMessage)
        ]

        self._user_profile = self.profile_analyzer.analyze(chat_history)
        self._suggested_strategy = self.strategy_suggester.suggest(self._user_profile)

        self.state_machine.transition_to(OnboardingState.OPTIONAL_STRATEGY)

    def get_suggested_strategy(self) -> FinancialStrategy | None:
        return self._suggested_strategy

    def get_ui_options(self) -> list[str]:
        state = self.state_machine.current_state
        if state == OnboardingState.WELCOME:
            return ["Começar Agora"]
        elif state == OnboardingState.SPREADSHEET_ACQUISITION:
            return ["Criar do Zero 🚀", "Fazer Upload 📤", "Google Sheets ☁️"]
        elif state == OnboardingState.TRANSLATION_REVIEW:
            return ["Começar a Usar ⚡"]
        elif state == OnboardingState.OPTIONAL_PROFILE:
            return ["Gerar Estratégia 🧠", "Começar a Usar ⚡"]
        elif state == OnboardingState.OPTIONAL_STRATEGY:
            return ["Aceitar Sugestão ✅", "Começar a Usar ⚡"]
        return []

    def _finalize_onboarding(self):
        """Finaliza o onboarding, convertendo pending planilha path para definitivo."""
        print("[ONBOARDING] Finalizando onboarding...")
        logger.info("[ONBOARDING] Finalizando onboarding...")

        # Converte pending planilha path para definitivo
        config_data = self.config_service.load_config()
        pending_path = config_data.get("pending_planilha_path")

        if pending_path:
            print(f"[ONBOARDING] Salvando planilha definitiva: {pending_path}")
            logger.info(f"[ONBOARDING] Salvando planilha definitiva: {pending_path}")
            # save_planilha_path() já remove pending_planilha_path e salva o config
            # NÃO precisamos salvar de novo aqui!
            self.config_service.save_planilha_path(pending_path)
        else:
            print("[ONBOARDING] AVISO: Nenhum pending_planilha_path encontrado!")
            logger.warning(
                "[ONBOARDING] Nenhum pending_planilha_path encontrado durante finalização"
            )

    def reset_config(self):
        """Reseta a configuração e o estado do onboarding."""
        self.config_service.clear_config()
        self.state_machine = OnboardingStateMachine()
        self.agent = OnboardingAgent(self.llm_orchestrator)
        self._context = {}
        self._user_profile = None
        self._suggested_strategy = None
