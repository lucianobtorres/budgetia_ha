# pages/3_📝_Editar_Transacoes.py
import os

# Adiciona o 'src' ao path
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import ColunasTransacoes, NomesAbas, ValoresTipo

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page

from web_app.utils import initialize_session_auth

is_logged_in, username, config_service, llm_orchestrator = initialize_session_auth()

if not is_logged_in or not config_service or "plan_manager" not in st.session_state:
    st.warning(
        "Você precisa estar logado e ter uma planilha configurada para acessar esta página."
    )
    st.stop()

# --- Configuração da Página ---
plan_manager, agent_runner = setup_page(title="Editar Transações", icon="📝")
aba_transacoes = NomesAbas.TRANSACOES

try:
    # Lê os dados usando a fachada
    st.info(f"Gerencie diretamente as transações da sua aba '{aba_transacoes}'.")
    df_transacoes = plan_manager.visualizar_dados(aba_transacoes)

    # Garante que o ID da Transação seja o primeiro
    cols = [ColunasTransacoes.ID] + [
        col for col in df_transacoes if col != ColunasTransacoes.ID
    ]
    df_transacoes = df_transacoes[cols]

    editor_key = f"editor_{aba_transacoes}"

    edited_df = st.data_editor(
        df_transacoes,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            ColunasTransacoes.ID: st.column_config.NumberColumn(disabled=True),
            ColunasTransacoes.DATA: st.column_config.DateColumn(
                format="YYYY-MM-DD", required=True
            ),
            ColunasTransacoes.TIPO: st.column_config.SelectboxColumn(
                options=[ValoresTipo.RECEITA, ValoresTipo.DESPESA], required=True
            ),
            ColunasTransacoes.CATEGORIA: st.column_config.TextColumn(required=True),
            ColunasTransacoes.DESCRICAO: st.column_config.TextColumn(),
            ColunasTransacoes.VALOR: st.column_config.NumberColumn(
                format="R$ %.2f", required=True, step=0.01
            ),
            ColunasTransacoes.STATUS: st.column_config.SelectboxColumn(
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
