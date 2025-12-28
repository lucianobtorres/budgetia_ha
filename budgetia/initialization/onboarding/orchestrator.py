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
        if saved_status:
            try:
                initial_state = OnboardingState[saved_status]
                print(f"[ONBOARDING] Restoring state: {initial_state.name}")
            except KeyError:
                print(
                    f"[ONBOARDING] Invalid saved status '{saved_status}'. Starting fresh."
                )
        else:
            print(
                f"[ONBOARDING] Starting new onboarding with state: {initial_state.name}"
            )

        self.state_machine = OnboardingStateMachine(
            initial_state=initial_state,
            on_transition=self._persist_state  # Hook de persistência
        )
    
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
        self._welcome_engaged: bool = (
            False  # Track if user has engaged in welcome conversation
        )
        self._last_agent_response: str = ""

    def _persist_state(self, new_state: OnboardingState) -> None:
        """Callback: Salva o estado atual no config a cada transição."""
        try:
             # Só salvamos o state name.
             # Se for COMPLETE, _finalize_onboarding cuida dos detalhes extras (limpar flags).
             # Mas salvar o status 'COMPLETE' aqui também não faz mal.
             print(f"[ONBOARDING] Persistindo estado intermediário: {new_state.name}")
             config_data = self.config_service.load_config()
             config_data["onboarding_status"] = new_state.name
             self.config_service.save_config(config_data)
        except Exception as e:
             print(f"[ONBOARDING] ERRO AO PERSISTIR ESTADO: {e}")

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def get_current_state(self) -> OnboardingState:
        return self.state_machine.current_state

    def get_progress(self) -> float:
        return self.state_machine.get_progress()

    def is_translation_analysis_complete(self) -> bool:
        """Check if spreadsheet analysis has been completed."""
        return self._translation_result is not None

    def get_initial_message(self) -> str | None:
        """Get initial message to display when entering a state (if applicable).

        Returns the agent's greeting for states that should auto-start conversation.
        Returns None for states that wait for user action.
        """
        current_state = self.state_machine.current_state

        # WELCOME: Auto-greet when not yet engaged
        if current_state == OnboardingState.WELCOME and not self._welcome_engaged:
            print("[ONBOARDING] Generating initial WELCOME greeting...")
            message = self.agent.chat(
                "[INÍCIO]",  # Placeholder - agent will initiate based on system prompt
                OnboardingState.WELCOME,
                extra_context="""PRIMEIRA INTERAÇÃO - Mensagem de boas-vindas completa:

1. Cumprimente calorosamente com 👋
2. EXPLIQUE O QUE É O BUDGETIA: "Sou seu assistente de finanças pessoais que te ajuda a organizar gastos de forma simples, conversando naturalmente."
3. EXPLIQUE O MOMENTO: "Estamos na configuração inicial (onboarding) - vou te guiar em alguns passos rápidos para conectar sua planilha."
4. SEGURANÇA (integrado naturalmente): "Uma coisa importante: seus dados ficam SEMPRE com você (no seu computador ou Google Drive 🔒). Eu apenas leio e organizo, nada é enviado para fora."
5. PERGUNTA CONTEXTUAL: "Antes de começar, me conta: você já controla seus gastos de alguma forma hoje?"

Seja amigável, leve e use 2-3 parágrafos curtos. Não seja robótico.""",
            )
            print(f"[ONBOARDING] Initial greeting: {message[:100]}...")
            return message

        # OPTIONAL_PROFILE: Auto-prompt if arriving here directly (e.g. reload or default sheet skip)
        if current_state == OnboardingState.OPTIONAL_PROFILE and not self._profile_interview_started:
             print("[ONBOARDING] Generating initial PROFILE prompt...")
             return self.agent.chat(
                 "[INÍCIO_PERFIL]",
                 OnboardingState.OPTIONAL_PROFILE,
                 extra_context="We arrived at profile step (likely skipped translation review). Invite user to answer a few quick questions to build their financial profile for better strategy suggestions. Ask if they want to start.",
             )

        # SPREADSHEET_ACQUISITION: Remind user of options
        if current_state == OnboardingState.SPREADSHEET_ACQUISITION:
            return "Como você gostaria de conectar sua planilha?\n\n1. 🚀 Criar do Zero (Recomendado)\n2. 📤 Fazer Upload (Excel/CSV)\n3. ☁️ Conectar Google Sheets"

        # TRANSLATION_REVIEW: Remind user to review
        if current_state == OnboardingState.TRANSLATION_REVIEW:
            return "Analisei sua planilha. O que você acha do resultado? Se estiver tudo certo, podemos prosseguir."
        
        # OPTIONAL_STRATEGY: Check strategy
        if current_state == OnboardingState.OPTIONAL_STRATEGY:
            strategy_name = self._suggested_strategy.name if self._suggested_strategy else "Padrão"
            return f"Com base no seu perfil, sugeri a estratégia: **{strategy_name}**. Você gostaria de segui-la ou personalizar?"

        # Other states wait for user input
        return None

    # ---------------------------------------------------------------------
    # Core processing
    # ---------------------------------------------------------------------
    def process_user_input(self, text: str, extra_context: dict | None = None) -> str:
        """Process a user message (or UI action) and return the agent's reply."""
        if extra_context:
            self._context.update(extra_context)
        
        self._context["user_input_text"] = text
        
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
        try:
            intent = self.intent_classifier.classify(
                clean_text, current_state.name, self._last_agent_response
            )
        except Exception as e:
            print(f"[ONBOARDING] AVISO: Falha na classificação de intenção (Rate Limit?): {e}")
            logger.warning(f"[ONBOARDING] Intent classification failed: {e}")
            intent = UserIntent.NEUTRAL_INFO
        
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
            # Check if we just arrived here (e.g. from default spreadsheet skip)
            # and haven't started the interview yet.
            if (
                not self._profile_interview_started
                and intent == UserIntent.UNCLEAR
                and clean_text == ""
            ):
                # This happens when we transition directly without user input (e.g. default sheet)
                # We need to prompt the user to start the interview.
                return self.agent.chat(
                    "[INÍCIO_PERFIL]",
                    OnboardingState.OPTIONAL_PROFILE,
                    extra_context="We just created a standard spreadsheet (or finished review). Now invite the user to answer a few quick questions to build their financial profile. Explain why it's useful (better strategy). Ask if they want to start.",
                )

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
            if (
                self._profile_interview_started
                and intent == UserIntent.INTERVIEW_COMPLETE
            ):
                print(
                    "[ONBOARDING] User signaled interview completion (Intent). Generating strategy and FINALIZING..."
                )
                
                # Generate strategy but DON'T transition to OPTIONAL_STRATEGY
                # Just save it internally
                chat_history = [
                    msg.content for msg in self.agent.history if isinstance(msg, HumanMessage)
                ]
                self._user_profile = self.profile_analyzer.analyze(chat_history)
                self._suggested_strategy = self.strategy_suggester.suggest(self._user_profile)
                
                # Finalize immediately
                self.state_machine.transition_to(OnboardingState.COMPLETE)
                self._finalize_onboarding()

                response = self.agent.chat(
                    text,
                    OnboardingState.COMPLETE,
                    extra_context=f"User completed profile and wants to start. Strategy generated: {self._suggested_strategy.name}. Finalise onboarding and welcome them to the dashboard.",
                )
                self._last_agent_response = response
                return response

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
        """Handle WELCOME state with conversational sub-stages.

        Agent auto-greets and guides through 3 stages:
        1. Asks about financial control (detect literacy)
        2. Engages based on response
        3. Explains security → transitions to acquisition
        """

        # If already engaged, check if ready to proceed
        if self._welcome_engaged:
            # User confirms readiness
            if intent == UserIntent.POSITIVE_CONFIRMATION:
                print("[ONBOARDING] User ready to proceed from WELCOME")
                self.state_machine.transition_to(
                    OnboardingState.SPREADSHEET_ACQUISITION
                )
                return self.agent.chat(
                    clean_text,
                    OnboardingState.SPREADSHEET_ACQUISITION,
                    extra_context="User is ready. Present the 3 spreadsheet acquisition options clearly with emojis.",
                )

            # Continue conversation
            return self.agent.chat(
                clean_text,
                OnboardingState.WELCOME,
                extra_context="User is engaged. Answer naturally. After addressing their input, explain security (dados ficam com você 🔒) and ask if ready to choose spreadsheet setup method.",
            )

        # First meaningful interaction after greeting
        engaging_intents = [
            UserIntent.POSITIVE_CONFIRMATION,
            UserIntent.NEGATIVE_REFUSAL,
            UserIntent.NEUTRAL_INFO,
            UserIntent.QUESTION,
        ]

        if intent in engaging_intents:
            self._welcome_engaged = True
            print(f"[ONBOARDING] User engaged in WELCOME (intent: {intent.name})")

            # Context-aware based on user's answer
            if intent == UserIntent.POSITIVE_CONFIRMATION:
                context = "User said YES - they track finances. Great! Ask where they keep data (Excel? Sheets?). Then SECURITY: 'Seus dados ficam SEUS! 🔒 BudgetIA só lê e organiza.' Ask if ready to connect."
            elif intent == UserIntent.NEGATIVE_REFUSAL:
                context = "User said NO - doesn't track yet. Be empathetic: 'Sem problemas! 😊 Muitos não sabem por onde começar. Controlar é mais simples do que parece!' SECURITY: 'Dados seguros com você 🔒' Offer to create together."
            elif intent == UserIntent.QUESTION:
                context = "User asked something. Answer helpfully. Then mention: 'Dados privados e seguros 🔒' Ask if ready when appropriate."
            else:
                context = "User provided info. Acknowledge naturally. SECURITY: 'Dados ficam com você 🔒' Ask if want to set up spreadsheet."

            return self.agent.chat(
                clean_text, OnboardingState.WELCOME, extra_context=context
            )

        # Initial auto-greeting (agent should start conversation)
        return self.agent.chat(
            clean_text,
            OnboardingState.WELCOME,
            extra_context="PRIMEIRA INTERAÇÃO: Inicie a conversa automaticamente! Apresente-se calorosamente e pergunte: 'Você já controla seus gastos de alguma forma hoje?' Seja amigável e leve.",
        )

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
                    # Use o estado ATUAL da máquina, pois _finalize_acquisition pode ter pulado etapas (ex: Default -> Profile)
                    current_state = self.state_machine.current_state
                    
                    context_msg = f"Acquisition SUCCESS. File path: {result.file_path}. Handler: {result.handler_type}."
                    if current_state == OnboardingState.OPTIONAL_PROFILE:
                        context_msg += " We skipped Translation Review (Default Sheet). Now invite user to Profile Interview."
                    else:
                        context_msg += " Proceed to analysis."

                    return self.agent.chat(
                        text,
                        current_state,
                        extra_context=context_msg,
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
                try:
                    success, message, schema_summary = (
                        self.strategy_generator.generate_and_validate_strategy(
                            file_to_analyze, strategy_save_path
                        )
                    )
                except Exception as e:
                    print(f"[ONBOARDING] AVISO: Falha na geração da estratégia (Rate Limit?): {e}")
                    success = True # Assume sucesso para não travar o user
                    message = "Devido à alta demanda do servidor, ignoramos a análise detalhada e usaremos a Estratégia Padrão."
                    schema_summary = "Análise ignorada (Fallback)."
                    # strategy_save_path não será escrito, o que força fallback para DefaultStrategy depois.
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

            # ALWAYS show analysis result on first call (don't transition immediately)
            print(f"[ONBOARDING] Translation analysis complete: success={success}")
            context_for_agent = f"\n[CONTEXTO DE ANÁLISE DE PLANILHA]\nSUCESSO: {success}\nMENSAGEM: {message}\nESQUEMA LIDO:\n{schema_summary[:2000]}"
            return self.agent.chat(
                f"Analisar o seguinte resultado da planilha: {message}",
                OnboardingState.TRANSLATION_REVIEW,
                extra_context=context_for_agent,
            )
        # Subsequent calls – Intent-based conversation flow
        context_for_agent = f"\n[CONTEXTO DE PLANILHA SALVO]\nSUCESSO: {self._translation_result.success}\nMENSAGEM: {self._translation_result.message}\nESQUEMA LIDO:\n{self._translation_result.schema_summary[:2000]}"

        # CASO 1: User confirmed → Proceed to profile
        if intent == UserIntent.POSITIVE_CONFIRMATION:
            if not self._translation_result.success:
                # Analysis failed but user wants to continue → Offer alternatives
                return self.agent.chat(
                    clean_text,
                    OnboardingState.TRANSLATION_REVIEW,
                    extra_context="User wants to continue despite failed analysis. Offer to: 1) Try guided import (manual column mapping), 2) Create default spreadsheet. Ask which they prefer.",
                )

            # Analysis succeeded → Transition
            print(
                "[ONBOARDING] User confirmed translation review, proceeding to profile"
            )
            self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
            return self.agent.chat(
                clean_text,
                OnboardingState.OPTIONAL_PROFILE,
                extra_context="User confirmed analysis. Transitioning to profile interview.",
            )

        # CASO 2: User has questions → Discussion mode
        if intent == UserIntent.QUESTION:
            print("[ONBOARDING] User has questions about translation")
            return self.agent.chat(
                clean_text,
                OnboardingState.TRANSLATION_REVIEW,
                extra_context=f"User asked a question about the spreadsheet analysis. Answer naturally and helpfully using the context below. After answering, ask if they're ready to proceed or have more questions.\n{context_for_agent}",
            )

        # CASO 3: User refused/rejected → Offer alternatives
        if intent == UserIntent.NEGATIVE_REFUSAL:
            print("[ONBOARDING] User refused translation result")
            if self._translation_result.success:
                # Succeeded but user doesn't like it
                return self.agent.chat(
                    clean_text,
                    OnboardingState.TRANSLATION_REVIEW,
                    extra_context="Analysis was successful but user rejected it. Ask what specifically they'd like to adjust. Offer guided import if they want manual control over column mapping.",
                )
            else:
                # Failed AND user refused → Create default
                return self.agent.chat(
                    clean_text,
                    OnboardingState.TRANSLATION_REVIEW,
                    extra_context="Analysis failed AND user refused/rejected. Offer to create a default template spreadsheet and continue with that instead. Reassure them it's quick and easy.",
                )

        # CASO 4: Skip → Create default spreadsheet
        if intent == UserIntent.SKIP:
            print("[ONBOARDING] User wants to skip translation review")
            return self.agent.chat(
                clean_text,
                OnboardingState.TRANSLATION_REVIEW,
                extra_context="User wants to skip this step. Confirm that we'll create a default spreadsheet template for them and proceed. Be positive and reassuring.",
            )

        # DEFAULT: Continue natural conversation
        # Analysis failed → Keep discussion about problem
        if not self._translation_result.success:
            return self.agent.chat(
                raw_text,
                OnboardingState.TRANSLATION_REVIEW,
                extra_context=f"Analysis failed. Continue discussing the issue and  offer help.\n{context_for_agent}",
            )

        # Analysis succeeded → Keep discussion about result
        return self.agent.chat(
            raw_text,
            OnboardingState.TRANSLATION_REVIEW,
            extra_context=f"Analysis succeeded. Continue natural conversation. When appropriate, ask if user is ready to proceed.\n{context_for_agent}",
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

        # If default spreadsheet, skip translation review (schema is known)
        if result.handler_type == "default":
            print(
                "[ONBOARDING] Default spreadsheet created. Skipping TRANSLATION_REVIEW."
            )
            self.state_machine.transition_to(OnboardingState.OPTIONAL_PROFILE)
        else:
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
            # No initial button - agent greets automatically
            return []
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
        self._welcome_engaged = False
        self._last_agent_response = ""

    def get_google_auth_service(self) -> GoogleAuthService:
        return self.google_auth_service
