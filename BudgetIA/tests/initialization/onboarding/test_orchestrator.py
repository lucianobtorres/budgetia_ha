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
    service.get_pending_planilha_path.side_effect = lambda: config_data.get("pending_planilha_path")
    
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
    generator.generate_and_validate_strategy.return_value = (True, "Strategy Validated", "Schema Mock")
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
        
        orch = OnboardingOrchestrator(mock_config_service, mock_llm_orchestrator)
        return orch


def test_initial_state(orchestrator):
    assert orchestrator.get_current_state() == OnboardingState.WELCOME


def test_welcome_conversation(orchestrator, mock_agent):
    response = orchestrator.process_user_input("Olá, tudo bem?")
    assert response == "Resposta do Agente"
    # Now we pass clean_text (lowercase) to the agent
    mock_agent.chat.assert_called_with("olá, tudo bem?", OnboardingState.WELCOME)


def test_welcome_transition_command(orchestrator):
    response = orchestrator.process_user_input("Começar agora")
    assert orchestrator.get_current_state() == OnboardingState.SPREADSHEET_ACQUISITION


def test_acquisition_conversation(orchestrator, mock_agent):
    orchestrator.process_user_input("Começar agora")
    response = orchestrator.process_user_input("Estou com dúvida sobre qual escolher")
    assert response == "Resposta do Agente"


def test_default_spreadsheet_flow(orchestrator):
    orchestrator.process_user_input("Começar agora")
    response = orchestrator.process_user_input(
        "Quero criar uma nova planilha",
        extra_context={"target_path": "test_sheet.xlsx"},
    )
    # Now goes to TRANSLATION_REVIEW first
    assert orchestrator.get_current_state() == OnboardingState.TRANSLATION_REVIEW
    
    # Confirm to go to OPTIONAL_PROFILE
    orchestrator.process_user_input("Tudo Certo! ✅")
    assert orchestrator.get_current_state() == OnboardingState.OPTIONAL_PROFILE


def test_strategy_generation(
    orchestrator, mock_profile_analyzer, mock_strategy_suggester
):
    # Setup: Chegar em OPTIONAL_PROFILE
    orchestrator.process_user_input("Começar agora")
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    # Pass through TRANSLATION_REVIEW
    orchestrator.process_user_input("Tudo Certo! ✅")

    # Ação: Simular que o agente ofereceu uma estratégia e o usuário aceitou
    # Primeiro, o agente oferece a estratégia (simulado via _last_agent_response)
    orchestrator._last_agent_response = "Aqui está uma sugestão de estratégia para você."
    
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
    orchestrator.process_user_input("Começar agora")
    options = orchestrator.get_ui_options()
    # Note: After "Começar agora", state is SPREADSHEET_ACQUISITION
    assert "Criar do Zero 🚀" in options

    # Avança para Profile
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    # Pass through TRANSLATION_REVIEW
    orchestrator.process_user_input("Tudo Certo! ✅")
    
    options = orchestrator.get_ui_options()
    assert "Responder Perguntas 📝" in options

    # Start interview
    orchestrator.process_user_input("Responder Perguntas 📝")
    options = orchestrator.get_ui_options()
    assert "Responder Perguntas 📝" not in options
    assert "Pular Perfil ⏭️" in options

    # Simulate agent offering strategy
    orchestrator._last_agent_response = "Aqui está uma sugestão de estratégia..."
    options = orchestrator.get_ui_options()
    assert "Aceitar Sugestão ✅" in options
    assert "Pular / Finalizar 🚀" in options

def test_strategy_skip_flow(orchestrator, mock_config_service):
    # Setup: Chegar em OPTIONAL_STRATEGY
    orchestrator.process_user_input("Começar agora")
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    orchestrator.process_user_input("Tudo Certo! ✅")
    
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
