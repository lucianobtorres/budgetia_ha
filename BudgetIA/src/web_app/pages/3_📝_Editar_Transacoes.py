# pages/3_📝_Editar_Transacoes.py
import os

# Adiciona o 'src' ao path
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import NomesAbas
from finance.planilha_manager import PlanilhaManager

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page


# --- Configuração da Página ---
plan_manager, agent_runner = setup_page(title="Editar Transações", icon="📝")

# --- Verificação de Inicialização ---
if "plan_manager" not in st.session_state:
    st.error("Erro: O sistema financeiro não foi carregado. Volte à página principal.")
    if st.button("Voltar à Página Principal"):
        st.switch_page("💰_BudgetIA.py")
    st.stop()

# --- Obtém o PlanilhaManager (Fachada) ---
plan_manager: PlanilhaManager = st.session_state.plan_manager
aba_transacoes = NomesAbas.TRANSACOES

# --- Renderização da Página de Edição de Transações ---
st.header(f"📝 Visualizar/Editar: {aba_transacoes}")
st.write(f"Gerencie diretamente as transações da sua aba '{aba_transacoes}'.")

try:
    # Lê os dados usando a fachada
    df_transacoes = plan_manager.visualizar_dados(aba_transacoes)

    # Garante que o ID da Transação seja o primeiro
    cols = ["ID Transacao"] + [col for col in df_transacoes if col != "ID Transacao"]
    df_transacoes = df_transacoes[cols]

    editor_key = f"editor_{aba_transacoes}"

    edited_df = st.data_editor(
        df_transacoes,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "ID Transacao": st.column_config.NumberColumn(disabled=True),
            "Data": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
            "Tipo (Receita/Despesa)": st.column_config.SelectboxColumn(
                options=["Receita", "Despesa"], required=True
            ),
            "Categoria": st.column_config.TextColumn(required=True),
            "Descricao": st.column_config.TextColumn(),
            "Valor": st.column_config.NumberColumn(
                format="R$ %.2f", required=True, step=0.01
            ),
            "Status": st.column_config.SelectboxColumn(
                options=["Concluído", "Pendente"], default="Concluído"
            ),
        },
        key=editor_key,
    )

    if not df_transacoes.equals(edited_df):
        if st.button("Salvar Alterações nas Transações"):
            st.info("Salvando alterações e recalculando...")
            try:
                if (edited_df["Valor"] < 0).any():
                    st.warning(
                        "Valores negativos detectados na coluna 'Valor'. Verifique as transações."
                    )

                # --- USA A FACHADA (ESTADO ORIGINAL) ---
                plan_manager.update_dataframe(aba_transacoes, edited_df)
                plan_manager.recalculate_budgets()  # Orquestração
                plan_manager.save()
                # --- FIM ---

                st.success("Planilha atualizada com sucesso!")
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

except Exception as e:
    st.error(f"Erro ao carregar dados da aba '{aba_transacoes}': {e}")
