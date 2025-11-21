# tests/initialization/onboarding/test_orchestrator.py
from unittest.mock import MagicMock, patch

import pytest

from initialization.onboarding.orchestrator import (
    OnboardingOrchestrator,
    OnboardingState,
)


@pytest.fixture
def mock_config_service():
    return MagicMock()


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
def orchestrator(
    mock_config_service,
    mock_llm_orchestrator,
    mock_agent,
    mock_profile_analyzer,
    mock_strategy_suggester,
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
    ):
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
    assert orchestrator.get_current_state() == OnboardingState.OPTIONAL_PROFILE


def test_strategy_generation(
    orchestrator, mock_profile_analyzer, mock_strategy_suggester
):
    # Setup: Chegar em OPTIONAL_PROFILE
    orchestrator.process_user_input("Começar agora")
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )

    # Ação: Gerar estratégia
    response = orchestrator.process_user_input("Gerar estratégia")

    # Verificações
    assert orchestrator.get_current_state() == OnboardingState.OPTIONAL_STRATEGY
    assert "Analisei seu perfil" in response
    mock_profile_analyzer.analyze.assert_called()
    mock_strategy_suggester.suggest.assert_called()
    assert orchestrator.get_suggested_strategy().name == "Estratégia Teste"


def test_ui_options(orchestrator):
    orchestrator.process_user_input("Começar agora")
    options = orchestrator.get_ui_options()
    assert "Criar do Zero 🚀" in options

    # Avança para Profile
    orchestrator.process_user_input(
        "Quero criar uma nova planilha", extra_context={"target_path": "test.xlsx"}
    )
    options = orchestrator.get_ui_options()
    assert "Gerar Estratégia 🧠" in options
