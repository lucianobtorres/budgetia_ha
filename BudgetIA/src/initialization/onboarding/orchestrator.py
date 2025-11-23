# src/initialization/onboarding/orchestrator.py
"""Orchestrator for the conversational onboarding flow.

Manages state transitions, persistence via UserConfigService, and delegates to
handlers and the LLM agent. The orchestrator is deliberately lightweight – most
business logic lives in the agent and the analyzers.
"""

import logging
import os
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from core.google_auth_service import GoogleAuthService
from core.llm_manager import LLMOrchestrator
from core.user_config_service import UserConfigService
from initialization.onboarding.agent import OnboardingAgent
from initialization.onboarding.analyzers import (
    FinancialStrategy,
    IntentClassifier,
    ProfileAnalyzer,
    StrategySuggester,
    TranslationResult,
    UserIntent,
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
from initialization.strategy_generator import StrategyGenerator

logger = logging.getLogger(__name__)


class OnboardingOrchestrator:
    """Central coordinator for the onboarding process.

    It keeps track of the current :class:`OnboardingState`, persists progress via
    :class:`UserConfigService` and interacts with the LLM through
    :class:`OnboardingAgent`.
    """

    def __init__(
        self, config_service: UserConfigService, llm_orchestrator: LLMOrchestrator
    ) -> None:
        self.config_service = config_service
        self.llm_orchestrator = llm_orchestrator

        # Load any previously saved onboarding status.
        saved_status = config_service.get_onboarding_status()
        initial_state = OnboardingState.WELCOME
        if saved_status and saved_status != OnboardingState.COMPLETE.name:
            try:
                initial_state = OnboardingState[saved_status]
                print(f"[ONBOARDING] Restoring interrupted state: {initial_state.name}")
            except KeyError:
                print(
                    f"[ONBOARDING] Invalid saved status '{saved_status}'. Starting fresh."
                )
        else:
            print(
                f"[ONBOARDING] Starting new onboarding with state: {initial_state.name}"
            )

        self.state_machine = OnboardingStateMachine(initial_state=initial_state)
        self.google_auth_service = GoogleAuthService(config_service)

        # Handlers for spreadsheet acquisition.
        self.file_handlers: list[IFileHandler] = [
            DefaultSpreadsheetHandler(),
            UploadHandler(),
            GoogleSheetsHandler(self.google_auth_service),
        ]

        # LLM agent and analysis utilities.
        self.agent = OnboardingAgent(llm_orchestrator)
        self.profile_analyzer = ProfileAnalyzer(llm_orchestrator)
        self.strategy_suggester = StrategySuggester()
        self.strategy_generator = StrategyGenerator(llm_orchestrator)
        self.intent_classifier = IntentClassifier(llm_orchestrator)

        # Runtime state.
        self._translation_result: TranslationResult | None = None
        self._context: dict[str, Any] = {}
        self._user_profile: UserProfile | None = None
        self._suggested_strategy: FinancialStrategy | None = None
        self._profile_interview_started: bool = False
        self._last_agent_response: str = ""

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def get_current_state(self) -> OnboardingState:
        return self.state_machine.current_state

    def get_progress(self) -> float:
        return self.state_machine.get_progress()

    # ---------------------------------------------------------------------
    # Core processing
    # ---------------------------------------------------------------------
    def process_user_input(self, text: str, extra_context: dict | None = None) -> str:
        """Process a user message (or UI action) and return the agent's reply."""
        if extra_context:
            self._context.update(extra_context)

        current_state = self.state_machine.current_state

        # Normalise text for simple keyword matching (still useful for legacy commands)
        clean_text = (
            text.lower()
            .replace("🚀", "")
            .replace("📤", "")
            .replace("☁️", "")
            .replace("🧠", "")
            .replace("✅", "")
            .replace("⚡", "")
            .replace("👋", "")
            .replace("🆘", "")
            .replace("⏭️", "")
            .replace("📝", "")
            .replace("!", "")
            .strip()
        )

        # Safe logging – avoid UnicodeEncodeError on Windows consoles.
        try:
            print(
                f"\n[ONBOARDING] State={current_state.name} | User Input: '{text}' | Clean: '{clean_text}'"
            )
        except UnicodeEncodeError:
            print(
                f"\n[ONBOARDING] State={current_state.name} | User Input: (unicode) | Clean: '{clean_text}'"
            )
        logger.info(f"[ONBOARDING] State={current_state.name} | User Input: '{text}'")

        # Classify Intent
        intent = self.intent_classifier.classify(
            clean_text, current_state.name, self._last_agent_response
        )
        print(f"[ONBOARDING] Intent Detected: {intent.name}")

        # -----------------------------------------------------------------
        # Auto‑transition after the agent offers a strategy suggestion.
        # -----------------------------------------------------------------
        if (
            current_state == OnboardingState.OPTIONAL_PROFILE
            and "sugestão de estratégia" in self._last_agent_response.lower()
        ):
            # The next user answer decides whether to accept or skip.
            if intent in [UserIntent.NEGATIVE_REFUSAL, UserIntent.SKIP]:
                print(
                    "[ONBOARDING] User declined strategy after profile interview (Intent). Finalising onboarding."
                )
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()
                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context="User declined strategy after profile interview. Finalise onboarding.",
                )
                self._last_agent_response = response
                return response
            
            if intent == UserIntent.POSITIVE_CONFIRMATION:
                print(
                    "[ONBOARDING] User accepted strategy after profile interview (Intent). Finalising onboarding."
                )
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()
                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context="User accepted strategy after profile interview. Finalise onboarding.",
                )
                self._last_agent_response = response
                return response

        # -----------------------------------------------------------------
        # State‑specific handling
        # -----------------------------------------------------------------
        if current_state == OnboardingState.WELCOME:
            response = self._handle_welcome(clean_text, intent)
            self._last_agent_response = response
            return response

        if current_state == OnboardingState.SPREADSHEET_ACQUISITION:
            response = self._handle_acquisition(text)
            self._last_agent_response = response
            return response

        if current_state == OnboardingState.TRANSLATION_REVIEW:
            response = self._handle_translation_review(text, clean_text, intent)
            self._last_agent_response = response
            return response

        if current_state == OnboardingState.OPTIONAL_PROFILE:
            # Start interview
            if clean_text in ["responder perguntas", "responder"] or (
                intent == UserIntent.POSITIVE_CONFIRMATION
                and not self._profile_interview_started
            ):
                self._profile_interview_started = True
                response = self.agent.chat(
                    text,
                    OnboardingState.OPTIONAL_PROFILE,
                    extra_context="User wants to answer profile questions. Start interview.",
                )
                self._last_agent_response = response
                return response



            # Skip everything and finish onboarding.
            if intent == UserIntent.SKIP or (
                intent == UserIntent.NEGATIVE_REFUSAL
                and not self._profile_interview_started
            ):
                print(
                    "[ONBOARDING] User chose to skip profile and finish onboarding (Intent)."
                )
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()
                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context="User skipped profile. Finalise onboarding.",
                )
                self._last_agent_response = response
                return response

            # Detect interview completion via intent
            if self._profile_interview_started and intent == UserIntent.INTERVIEW_COMPLETE:
                print("[ONBOARDING] User signaled interview completion (Intent). Generating strategy...")
                self._generate_strategy_and_advance()
                
                # Offer the strategy
                strategy_summary = f"Estratégia: {self._suggested_strategy.name}" if self._suggested_strategy else "Estratégia gerada"
                response = self.agent.chat(
                    text,
                    OnboardingState.OPTIONAL_STRATEGY,
                    extra_context=f"User completed profile interview. Generated strategy: {strategy_summary}. Offer it to user.",
                )
                # Mark response so UI shows accept/skip buttons
                self._last_agent_response = f"{response}\n\nSugestão de estratégia: {strategy_summary}"
                return self._last_agent_response

            # Default: let the agent respond freely.
            response = self.agent.chat(text, current_state)
            self._last_agent_response = response
            return response

        if current_state == OnboardingState.OPTIONAL_STRATEGY:
            # Accept suggestion
            if intent == UserIntent.POSITIVE_CONFIRMATION or clean_text in [
                "aceitar sugestão",
                "aceitar sugestao",
                "aceitar",
                "usar esta",
            ]:
                print("[ONBOARDING] User accepted suggested strategy (Intent).")
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()
                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context="User accepted strategy. Finalise onboarding.",
                )
                self._last_agent_response = response
                return response

            # Personalisation placeholder.
            if clean_text in ["personalizar", "customizar"]:
                response = (
                    "Customização ainda não implementada. Usarei a sugestão padrão."
                )
                self._last_agent_response = response
                return response

            # Skip / finalize.
            if intent in [UserIntent.SKIP, UserIntent.NEGATIVE_REFUSAL]:
                print("[ONBOARDING] User skipped strategy (Intent).")
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()
                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context="User skipped strategy. Finalise onboarding.",
                )
                self._last_agent_response = response
                return response

            # Fallback to agent.
            response = self.agent.chat(text, current_state)
            self._last_agent_response = response
            return response

        if current_state == OnboardingState.COMPLETE:
            response = self.agent.chat(text, current_state)
            self._last_agent_response = response
            return response

        print(f"[ONBOARDING] Unhandled state: {current_state.name}")
        logger.warning(f"[ONBOARDING] Unhandled state: {current_state.name}")
        return "Estado não reconhecido."

    # ---------------------------------------------------------------------
    # Handlers for each state
    # ---------------------------------------------------------------------
    def _handle_welcome(self, clean_text: str, intent: UserIntent) -> str:
        if intent == UserIntent.POSITIVE_CONFIRMATION:
            self.state_machine.transition_to(OnboardingState.SPREADSHEET_ACQUISITION)
            return self.agent.chat(
                clean_text,
                OnboardingState.SPREADSHEET_ACQUISITION,
                extra_context="User wants to start. Explain spreadsheet acquisition options.",
            )
        return self.agent.chat(clean_text, OnboardingState.WELCOME)

    def _handle_acquisition(self, text: str) -> str:
        print(
            f"[ONBOARDING] Processing acquisition with {len(self.file_handlers)} handlers"
        )
        logger.info(
            f"[ONBOARDING] Processing acquisition with {len(self.file_handlers)} handlers"
        )
        for handler in self.file_handlers:
            if handler.can_handle(text):
                if "username" not in self._context:
                    self._context["username"] = self.config_service.username
                if "save_dir" not in self._context:
                    self._context["save_dir"] = str(Path.cwd() / "data")
                print(f"[ONBOARDING] Invoking handler {handler.__class__.__name__}")
                result = handler.acquire(self._context)
                if result.success:
                    self._finalize_acquisition(result)
                    return self.agent.chat(
                        text,
                        OnboardingState.TRANSLATION_REVIEW,
                        extra_context=f"Acquisition SUCCESS. File path: {result.file_path}. Handler: {result.handler_type}. Proceed to analysis.",
                    )
                elif result.requires_ui_action:
                    error_msg = result.error_message or "Ação de UI necessária"
                    return f"[UI_ACTION:{result.requires_ui_action}] {error_msg}"
                else:
                    error_msg = result.error_message or "Erro ao processar solicitação"
                    return self.agent.chat(
                        text,
                        OnboardingState.SPREADSHEET_ACQUISITION,
                        extra_context=f"Handler FAILED. Error: {error_msg}. Prompt retry.",
                    )
        print("[ONBOARDING] No handler matched; delegating to agent.")
        return self.agent.chat(text, OnboardingState.SPREADSHEET_ACQUISITION)

    def _handle_translation_review(
        self, raw_text: str, clean_text: str, intent: UserIntent
    ) -> str:
        """Handle the TRANSLATION_REVIEW state.

        The first call performs the spreadsheet analysis; subsequent calls keep the
        conversation flowing.
        """
        if self._translation_result is None:
            file_path = self.config_service.load_config().get("pending_planilha_path")
            strategy_save_path = Path("data/temp_user_strategy.py")
            schema_summary = "Não foi possível ler o esquema da planilha."
            success = False
            message = ""
            local_file_path = file_path
            if not file_path:
                self.state_machine.transition_to(
                    OnboardingState.SPREADSHEET_ACQUISITION
                )
                return "Erro: Planilha não encontrada. Voltando para aquisição."
            if file_path.startswith("http"):
                print(
                    "[ONBOARDING] Detectado Google Sheets URL. Iniciando download temporário."
                )
                try:
                    file_id = self.google_auth_service._extract_file_id_from_url(
                        file_path
                    )
                    if not file_id:
                        raise ValueError("Não foi possível extrair o File ID da URL.")
                    local_file_path = (
                        self.google_auth_service.download_sheets_as_excel_for_analysis(
                            file_id
                        )
                    )
                    if not local_file_path or not Path(local_file_path).exists():
                        raise Exception(
                            "Falha ao baixar arquivo temporário do Google Sheets."
                        )
                    print(
                        f"[ONBOARDING] Download temporário concluído em: {local_file_path}"
                    )
                except Exception as e:
                    print(f"[ONBOARDING] ERRO DOWNLOAD GOOGLE: {e}")
                    message = (
                        f"Erro ao baixar a planilha do Google Sheets. Detalhe: {e}"
                    )
                    self.state_machine.transition_to(
                        OnboardingState.SPREADSHEET_ACQUISITION
                    )
                    return message
            file_to_analyze = local_file_path
            if "MinhasFinancas.xlsx" in file_to_analyze:
                schema_summary = self.strategy_generator.get_planilha_schema(
                    file_to_analyze
                )
                success = True
                message = "Planilha padrão lida e validada com sucesso."
            else:
                print("[ONBOARDING] Iniciando geração/validação da estratégia...")
                success, message, schema_summary = (
                    self.strategy_generator.generate_and_validate_strategy(
                        file_to_analyze, strategy_save_path
                    )
                )
            if (
                local_file_path
                and "docs.google.com" in file_path
                and Path(local_file_path).exists()
            ):
                try:
                    os.remove(local_file_path)
                    print(
                        f"[ONBOARDING] Cleanup: Arquivo temporário removido: {local_file_path}"
                    )
                except Exception as e:
                    print(
                        f"[ONBOARDING] AVISO: Falha ao remover arquivo temporário {local_file_path}: {e}"
                    )
            self._translation_result = TranslationResult(
                success=success,
                message=message,
                schema_summary=schema_summary,
                strategy_path=str(strategy_save_path) if success else None,
            )
            if success and (
                intent == UserIntent.POSITIVE_CONFIRMATION
                or clean_text
                in [
                    "continuar",
                    "avançar",
                    "próximo",
                    "ok",
                    "tudo certo",
                    "confirmar",
                    "começar a usar",
                    "comecar a usar",
                ]
            ):
                self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
                self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
                return self.agent.chat(
                    clean_text,
                    OnboardingState.OPTIONAL_PROFILE,
                    extra_context="Analysis SUCCESS. User confirmed. Transitioning to profile interview.",
                )
            context_for_agent = f"\n[CONTEXTO DE ANÁLISE DE PLANILHA]\nSUCESSO: {success}\nMENSAGEM: {message}\nESQUEMA LIDO:\n{schema_summary[:2000]}"
            return self.agent.chat(
                f"Analisar o seguinte resultado da planilha: {message}",
                OnboardingState.TRANSLATION_REVIEW,
                extra_context=context_for_agent,
            )
        # Subsequent calls – keep conversation.
        context_for_agent = f"\n[CONTEXTO DE PLANILHA SALVO]\nSUCESSO: {self._translation_result.success}\nMENSAGEM: {self._translation_result.message}\nESQUEMA LIDO:\n{self._translation_result.schema_summary[:2000]}"
        if intent == UserIntent.POSITIVE_CONFIRMATION or clean_text in [
            "continuar",
            "avançar",
            "próximo",
            "ok",
            "tudo certo",
            "confirmar",
            "começar a usar",
        ]:
            if not self._translation_result.success:
                return self.agent.chat(
                    clean_text,
                    OnboardingState.TRANSLATION_REVIEW,
                    extra_context="User wants to continue but analysis failed. Explain next steps.",
                )
            self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
            return self.agent.chat(
                clean_text,
                OnboardingState.OPTIONAL_PROFILE,
                extra_context="User confirmed analysis. Transitioning to profile interview.",
            )
        if not self._translation_result.success:
            return self.agent.chat(
                raw_text,
                OnboardingState.TRANSLATION_REVIEW,
                extra_context=context_for_agent,
            )
        return self.agent.chat(
            raw_text,
            OnboardingState.TRANSLATION_REVIEW,
            extra_context=context_for_agent,
        )

    def _finalize_acquisition(self, result: AcquisitionResult) -> None:
        print(
            f"[ONBOARDING] Finalizing acquisition: file_path={result.file_path}, handler_type={result.handler_type}"
        )
        logger.info(
            f"[ONBOARDING] Finalizing acquisition: file_path={result.file_path}, handler_type={result.handler_type}"
        )
        if result.file_path:
            self.config_service.save_pending_planilha_path(result.file_path)
        self.state_machine.transition_to(OnboardingState.TRANSLATION_REVIEW)

    def _generate_strategy_and_advance(self) -> None:
        """Generate user profile and suggested strategy, then move to OPTIONAL_STRATEGY."""
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
            return ["Começar agora! 👋"]
        if state == OnboardingState.SPREADSHEET_ACQUISITION:
            return ["Criar do Zero 🚀", "Fazer Upload 📤", "Google Sheets ☁️"]
        if state == OnboardingState.TRANSLATION_REVIEW:
            return ["Tudo Certo! ✅", "Preciso de Ajuda 🆘"]
        if state == OnboardingState.OPTIONAL_PROFILE:
            # Check if agent has already offered a strategy (conversational transition)
            if "sugestão de estratégia" in self._last_agent_response.lower():
                return ["Aceitar Sugestão ✅", "Pular / Finalizar 🚀"]
            
            if self._profile_interview_started:
                return ["Pular Perfil ⏭️"]
            return ["Responder Perguntas 📝", "Pular Perfil ⏭️"]
        if state == OnboardingState.OPTIONAL_STRATEGY:
            return ["Aceitar Sugestão ✅", "Pular / Finalizar 🚀"]
        return []

    def _finalize_onboarding(self) -> None:
        """Persist onboarding completion and clean up temporary config entries."""
        print("[ONBOARDING] Finalizando onboarding...")
        logger.info("[ONBOARDING] Finalizando onboarding...")
        config_data = self.config_service.load_config()
        pending_path = config_data.get("pending_planilha_path")
        if pending_path:
            self.config_service.save_planilha_path(pending_path)
        else:
            print("[ONBOARDING] AVISO: Nenhum pending_planilha_path encontrado!")
            logger.warning(
                "[ONBOARDING] Nenhum pending_planilha_path encontrado durante finalização"
            )
        # Persist complete status.
        config_data = self.config_service.load_config()
        config_data["onboarding_status"] = OnboardingState.COMPLETE.name
        self.config_service.save_config(config_data)
        print(
            f"[ONBOARDING] Estado persistido: onboarding_status={OnboardingState.COMPLETE.name}"
        )

    def reset_config(self) -> None:
        """Reset configuration and internal state to start onboarding anew."""
        self.config_service.clear_config()
        self.state_machine = OnboardingStateMachine()
        self.agent = OnboardingAgent(self.llm_orchestrator)
        self._context = {}
        self._user_profile = None
        self._suggested_strategy = None
        self._profile_interview_started = False
        self._last_agent_response = ""

    def get_google_auth_service(self) -> GoogleAuthService:
        return self.google_auth_service
