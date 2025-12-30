# src/initialization/onboarding/state_machine.py
from typing import Any
from enum import Enum, auto
from core.logger import get_logger

logger = get_logger("OnboardingState")


class OnboardingState(Enum):
    """
    Define os estados do fluxo de onboarding conversacional.

    Fluxo Típico:
    WELCOME -> SPREADSHEET_ACQUISITION -> TRANSLATION_REVIEW -> OPTIONAL_PROFILE -> OPTIONAL_STRATEGY -> COMPLETE
    """

    # 1. Boas-vindas e Engajamento
    # Onde o agente se apresenta e cria rapport.
    WELCOME = auto()

    # 2. Aquisição da Planilha
    # Onde o usuário escolhe: Default, Upload ou Google.
    SPREADSHEET_ACQUISITION = auto()

    # 3. Revisão da Translação (Strategy)
    # Onde a IA analisa a planilha e confirma o entendimento.
    # Pode incluir Guided Import (fallback) se necessário.
    TRANSLATION_REVIEW = auto()

    # 4. Perfil Financeiro (Opcional)
    # Perguntas sobre hábitos e objetivos.
    OPTIONAL_PROFILE = auto()

    # 5. Sugestão de Estratégia (Opcional)
    # Sugestão de regras (50/30/20) baseada no perfil.
    OPTIONAL_STRATEGY = auto()

    # 6. Conclusão
    # Onboarding finalizado, libera acesso ao chat principal.
    COMPLETE = auto()


class OnboardingStateMachine:
    """
    Gerencia as transições de estado do onboarding.
    Garante que o fluxo siga uma ordem lógica e válida.
    """

    def __init__(self, initial_state: OnboardingState = OnboardingState.WELCOME, on_transition: Any = None):
        self._current_state = initial_state
        self._on_transition = on_transition # Callback(new_state)

        # Define transições válidas para cada estado
        self._valid_transitions: dict[OnboardingState, set[OnboardingState]] = {
            # ... (mantém igual, apenas injetando o callback no init)
            OnboardingState.WELCOME: {
                OnboardingState.SPREADSHEET_ACQUISITION,
                OnboardingState.COMPLETE,
            },
            OnboardingState.SPREADSHEET_ACQUISITION: {
                OnboardingState.TRANSLATION_REVIEW,
                OnboardingState.OPTIONAL_PROFILE,
                OnboardingState.WELCOME,
            },
            OnboardingState.TRANSLATION_REVIEW: {
                OnboardingState.OPTIONAL_PROFILE,
                OnboardingState.SPREADSHEET_ACQUISITION,
            },
            OnboardingState.OPTIONAL_PROFILE: {
                OnboardingState.OPTIONAL_STRATEGY,
                OnboardingState.COMPLETE,
            },
            OnboardingState.OPTIONAL_STRATEGY: {
                OnboardingState.COMPLETE,
                OnboardingState.OPTIONAL_PROFILE,
            },
            OnboardingState.COMPLETE: {
                OnboardingState.WELCOME
            },
        }


    @property
    def current_state(self) -> OnboardingState:
        """Retorna o estado atual."""
        return self._current_state

    def can_transition_to(self, new_state: OnboardingState) -> bool:
        """Verifica se a transição para o novo estado é válida."""
        if self._current_state == new_state:
            return True  # Permanecer no mesmo estado é sempre válido

        allowed = self._valid_transitions.get(self._current_state, set())
        return new_state in allowed

    def transition_to(self, new_state: OnboardingState) -> bool:
        """
        Executa a transição para o novo estado se for válida.

        Returns:
            bool: True se a transição ocorreu, False se foi rejeitada.
        """
        # Permanecer no mesmo estado é sempre válido
        if self._current_state == new_state:
            logger.debug(
                f"Permanecendo no estado {self._current_state.name}"
            )
            return True

        allowed = self._valid_transitions.get(self._current_state, set())
        if new_state in allowed:
            logger.info(
                f"Transição de {self._current_state.name} para {new_state.name}"
            )
            self._current_state = new_state
            
            # Aciona callback de persistência
            if self._on_transition:
                self._on_transition(new_state)
                
            return True

        logger.warning(
            f"Transição INVÁLIDA de {self._current_state.name} para {new_state.name}"
        )
        return False

    def get_progress(self) -> float:
        """Retorna uma estimativa de progresso (0.0 a 1.0) para UI."""
        # Mapeamento simples de progresso
        progress_map = {
            OnboardingState.WELCOME: 0.1,
            OnboardingState.SPREADSHEET_ACQUISITION: 0.3,
            OnboardingState.TRANSLATION_REVIEW: 0.5,
            OnboardingState.OPTIONAL_PROFILE: 0.7,
            OnboardingState.OPTIONAL_STRATEGY: 0.9,
            OnboardingState.COMPLETE: 1.0,
        }
        return progress_map.get(self._current_state, 0.0)
