# src/web_app/ui_components/ui_fallback.py
import streamlit as st

from initialization.onboarding_manager import OnboardingManager


def render(manager: OnboardingManager) -> None:
    """Renderiza a tela de fallback (Plano B e C)."""
    st.title("😕 Desculpe, não consegui ler sua planilha")
    st.error(
        f"A IA tentou {manager.max_retries} vezes criar um código de tradução, mas falhou."
    )
    st.subheader("Você tem estas opções para continuar:")

    st.write("**Opção 1 (Recomendado): Importação Guiada (Plano B)**")
    st.write(
        "Nós criaremos uma `planilha_mestra.xlsx` nova para você e faremos uma importação guiada dos seus dados antigos."
    )
    if st.button("Iniciar Importação Guiada"):
        st.info("Funcionalidade 'Importação Guiada' ainda em construção.")
        # TODO: Implementar manager.start_guided_import()
        # manager.set_state("GUIDED_IMPORT_MAPPING")
        # st.rerun()

    st.write("**Opção 2 (Avançado): Estratégia Manual (Plano C)**")
    with st.expander("Instruções para desenvolvedores"):
        st.write(
            "Você pode escrever seu próprio script de estratégia em Python."
            "1. Abra a pasta `src/finance/strategies/`."
            "2. Copie `default_strategy.py` para `minha_estrategia.py`."
            "3. Edite `minha_estrategia.py` (classe `CustomStrategy`) para ler/escrever sua planilha."
            "4. Edite `data/user_config.json` e adicione a seção:\n"
            "```json\n"
            "{\n"
            '  "planilha_path": "C:\\\\caminho\\\\para\\\\sua\\\\planilha.xlsx",\n'
            '  "mapeamento": {\n'
            '    "strategy_module": "minha_estrategia"\n'
            "  }\n"
            "}\n"
            "```"
        )
    if st.button("Já fiz isso, recarregar sistema."):
        manager.set_state(
            "AWAITING_FILE_SELECTION"
        )  # Volta ao início para reler o config
        st.rerun()

    st.stop()
