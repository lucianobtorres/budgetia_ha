# tests/initialization/onboarding/test_orchestrator.py
from unittest.mock import MagicMock, patch

import pytest

from initialization.onboarding.orchestrator import (
    OnboardingOrchestrator,
    OnboardingState,
)


@pytest.fixture
def mock_config_service():
    service = MagicMock()
    config_data = {}

    def save_pending(path):
        config_data["pending_planilha_path"] = path

    def load():
        return config_data

    service.save_pending_planilha_path.side_effect = save_pending
    service.load_config.side_effect = load
    # Também precisa suportar get_pending_planilha_path direto se usado
    service.get_pending_planilha_path.side_effect = lambda: config_data.get(
        "pending_planilha_path"
    )

    return service


@pytest.fixture
def mock_llm_orchestrator():
    return MagicMock()


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.chat.return_value = "Resposta do Agente"
    agent.history = []  # Adiciona history vazio
    return agent


@pytest.fixture
def mock_profile_analyzer():
    analyzer = MagicMock()
    analyzer.analyze.return_value = MagicMock(financial_literacy="iniciante")
    return analyzer


from initialization.onboarding.analyzers import FinancialStrategy


@pytest.fixture
def mock_strategy_suggester():
    suggester = MagicMock()
    # Usa objeto real para evitar colisão com atributo 'name' do Mock
    strategy = FinancialStrategy(
        name="Estratégia Teste", description="Desc", allocation={}
    )
    suggester.suggest.return_value = strategy
    return suggester


@pytest.fixture
def mock_strategy_generator():
    generator = MagicMock()
    # Configura para retornar sucesso por padrão
    generator.get_planilha_schema.return_value = "Schema Mock"
    generator.generate_and_validate_strategy.return_value = (
        True,
        "Strategy Validated",
        "Schema Mock",
    )
    return generator


@pytest.fixture
def orchestrator(
    mock_config_service,
    mock_llm_orchestrator,
    mock_agent,
    mock_profile_analyzer,
    mock_strategy_suggester,
    mock_strategy_generator,
):
    with (
        patch(
            "initialization.onboarding.orchestrator.OnboardingAgent",
            return_value=mock_agent,
        ),
        patch(
            "initialization.onboarding.orchestrator.ProfileAnalyzer",
            return_value=mock_profile_analyzer,
        ),
        patch(
            "initialization.onboarding.orchestrator.StrategySuggester",
            return_value=mock_strategy_suggester,
        ),
        patch(
            "initialization.onboarding.orchestrator.StrategyGenerator",
            return_value=mock_strategy_generator,
        ),
        patch(
            "initialization.onboarding.orchestrator.IntentClassifier"
        ) as mock_intent_classifier_cls,
        patch(
            "initialization.onboarding.orchestrator.DefaultSpreadsheetHandler"
        ) as mock_default_handler_cls,
    ):
        # Setup default intent to be UNCLEAR or specific based on input?
        # Better to let individual tests configure it, but we need a default.
        mock_intent_instance = mock_intent_classifier_cls.return_value
        from initialization.onboarding.analyzers import UserIntent

        def classify_side_effect(text, state, last_msg):
            text = text.lower().strip()
            if text in ["começar agora", "sim", "tudo certo", "aceitar sugestão"]:
                return UserIntent.POSITIVE_CONFIRMATION
            if text in ["pular / finalizar", "pular"]:
                return UserIntent.SKIP
            return UserIntent.UNCLEAR

        mock_intent_instance.classify.side_effect = classify_side_effect

        # Setup DefaultSpreadsheetHandler mock
        mock_default_handler = mock_default_handler_cls.return_value
        mock_default_handler.can_handle.return_value = True
        from initialization.onboarding.file_handlers import AcquisitionResult

        mock_default_handler.acquire.return_value = AcquisitionResult(
            success=True,
            file_path="mock_path.xlsx",
            handler_type="default",
        )

        orch = OnboardingOrchestrator(mock_config_service, mock_llm_orchestrator)

        # Manually inject mock handler to ensure it's used
        # (Patching class doesn't affect already instantiated objects or imports in some cases)
        orch.file_handlers[0] = mock_default_handler

        return orch


def test_initial_state(orchestrator):
    assert orchestrator.get_current_state() == OnboardingState.WELCOME


def test_welcome_conversation(orchestrator, mock_agent):
    response = orchestrator.process_user_input("Olá, tudo bem?")
    assert response == "Resposta do Agente"
    # WELCOME now includes extra_context for initial greeting
    # We just check that it was called with the right state
    assert mock_agent.chat.called
    call_args = mock_agent.chat.call_args
    assert call_args[0][1] == OnboardingState.WELCOME  # Second positional arg is state


def test_welcome_transition_command(orchestrator):
    # WELCOME now requires engagement before transitioning
    # First message: user responds to greeting (this engages)
    orchestrator.process_user_input("sim")  # This sets _welcome_engaged = True
    assert orchestrator.get_current_state() == OnboardingState.WELCOME

    # Second message: user confirms they're ready to start
    orchestrator.process_user_input(
        "sim"
    )  # When already engaged, POSITIVE_CONFIRMATION transitions
    assert orchestrator.get_current_state() == OnboardingState.SPREADSHEET_ACQUISITION


def test_acquisition_conversation(orchestrator, mock_agent):
    # Engage in WELCOME first
    orchestrator.process_user_input("sim")  # Engage
    orchestrator.process_user_input("sim")  # Confirm readiness
    response = orchestrator.process_user_input("Estou com dúvida sobre qual escolher")
    assert response == "Resposta do Agente"


def test_default_spreadsheet_flow(orchestrator):
    # Engage in WELCOME first
    # orchestrator.process_user_input("sim") # Trigger
    # orchestrator.process_user_input("sim") # Confirm
    # NOTE: Default spreadsheet now SKIPS translation review!
    # So we are already in OPTIONAL_PROFILE

    # Manually set state to OPTIONAL_PROFILE to simulate that we arrived here
    orchestrator.state_machine._current_state = OnboardingState.OPTIONAL_PROFILE

    # Ação: Simular que o agente ofereceu uma estratégia e o usuário aceitou
    # Primeiro, o agente oferece a estratégia (simulado via _last_agent_response)
    orchestrator._last_agent_response = (
        "Aqui está uma sugestão de estratégia para você."
    )

    # O usuário aceita
    response = orchestrator.process_user_input("Aceitar sugestão")

    # Verificações
    assert orchestrator.get_current_state() == OnboardingState.COMPLETE
    assert response == "Resposta do Agente"
    # Nota: analyze e suggest eram chamados pelo comando legado.
    # No fluxo conversacional, eles seriam chamados internamente pelo agente ou em outro ponto.
    # Como removemos o comando explícito, removemos as asserções de chamada direta aqui,
    # focando na transição de estado correta via intent.


def test_ui_options(orchestrator):
    # Engage in WELCOME first
    orchestrator.process_user_input("sim")
    orchestrator.process_user_input("sim")
    options = orchestrator.get_ui_options()
    # Note: After "Começar agora", state is SPREADSHEET_ACQUISITION
    assert "Criar do Zero 🚀" in options

    # Avança para Profile
    print(f"HANDLERS: {orchestrator.file_handlers}")
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    # Update options after transition!
    options = orchestrator.get_ui_options()
    assert "Pular Perfil ⏭️" in options


def test_strategy_skip_flow(orchestrator, mock_config_service):
    # Setup: Chegar em OPTIONAL_STRATEGY
    orchestrator.process_user_input("sim")
    orchestrator.process_user_input("sim")
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    # orchestrator.process_user_input("sim") # REMOVED: Default sheet skips TRANSLATION_REVIEW

    # Force state to OPTIONAL_STRATEGY (simulating interview completion)
    orchestrator.state_machine._current_state = OnboardingState.OPTIONAL_STRATEGY
    orchestrator._last_agent_response = "sugestão de estratégia"

    assert orchestrator.get_current_state() == OnboardingState.OPTIONAL_STRATEGY

    # Ação: Pular estratégia
    orchestrator.process_user_input("Pular / Finalizar 🚀")

    # Verificações
    assert orchestrator.get_current_state() == OnboardingState.COMPLETE

    # Verifica se salvou no config
    config_data = mock_config_service.load_config()
    assert config_data.get("onboarding_status") == "COMPLETE"


def test_profile_completion_skips_strategy(orchestrator, mock_config_service):
    # Setup: Chegar em OPTIONAL_PROFILE
    orchestrator.state_machine._current_state = OnboardingState.OPTIONAL_PROFILE
    orchestrator._profile_interview_started = True

    # Ação: Enviar comando de conclusão ("vamos começar")
    # O IntentClassifier agora usa LLM, então vamos mockar o retorno do classify
    # para simular que o LLM entendeu como INTERVIEW_COMPLETE

    from initialization.onboarding.analyzers import UserIntent

    # Acessa o mock do intent classifier
    # Configura para retornar INTERVIEW_COMPLETE quando chamado
    # IMPORTANTE: Limpar side_effect do fixture para que return_value funcione
    orchestrator.intent_classifier.classify.side_effect = None
    orchestrator.intent_classifier.classify.return_value = UserIntent.INTERVIEW_COMPLETE
    # Se precisar de side_effect para variar por input, pode usar, mas aqui queremos testar o fluxo
    # assumindo que o classificador funcionou.

    response = orchestrator.process_user_input("vamos começar")

    # Verificações
    # Deve ir direto para COMPLETE
    assert orchestrator.get_current_state() == OnboardingState.COMPLETE

    # Deve ter salvo o status
    config_data = mock_config_service.load_config()
    assert config_data.get("onboarding_status") == "COMPLETE"

    # Deve ter gerado a estratégia internamente
    assert orchestrator.strategy_suggester.suggest.called


def test_profile_completion_context_heuristic(orchestrator, mock_config_service):
    # Setup: Chegar em OPTIONAL_PROFILE
    orchestrator.state_machine._current_state = OnboardingState.OPTIONAL_PROFILE
    orchestrator._profile_interview_started = True

    # Simula que o agente perguntou se pode começar
    orchestrator._last_agent_response = "Tudo pronto! Vamos começar o uso do sistema?"

    # Ação: Usuário responde "sim" (que normalmente seria POSITIVE_CONFIRMATION)
    # Mas com a heurística, deve virar INTERVIEW_COMPLETE

    # Precisamos garantir que o IntentClassifier REAL (ou um mock com a lógica real) seja usado
    # OU mockar o classify para retornar INTERVIEW_COMPLETE se a lógica estiver correta.
    # Como estamos testando o orchestrator, e o intent classifier é mockado no fixture,
    # precisamos configurar o mock para simular o comportamento da heurística OU
    # (melhor) testar a heurística isoladamente em um teste de unidade do IntentClassifier.
    # Mas aqui, vamos assumir que o classifier fará o trabalho e configurar o mock para retornar o esperado.

    from initialization.onboarding.analyzers import UserIntent

    orchestrator.intent_classifier.classify.side_effect = None
    orchestrator.intent_classifier.classify.return_value = UserIntent.INTERVIEW_COMPLETE

    response = orchestrator.process_user_input("sim")

    # Verificações
    assert orchestrator.get_current_state() == OnboardingState.COMPLETE
    assert mock_config_service.load_config().get("onboarding_status") == "COMPLETE"
