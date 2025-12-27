
import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import ColunasOrcamentos
from interfaces.web_app.api_client import BudgetAPIClient
from interfaces.web_app.session_manager import initialize_session_auth

# --- Autenticação ---
is_logged_in, username, _, _ = initialize_session_auth()
if not is_logged_in:
    st.warning("Por favor, faça o login na página inicial.")
    st.stop()

if "api_client" not in st.session_state:
    st.warning("Conexão com API não estabelecida. Volte para a Home.")
    st.stop()

api_client: BudgetAPIClient = st.session_state.api_client

st.set_page_config(page_title="Meus Orçamentos", page_icon="🎯", layout="wide")

st.title("🎯 Meus Orçamentos")
st.info("O sistema irá monitorar seus gastos automaticamente. Edite seus limites aqui.")

# --- Busca Dados ---
budgets_data = api_client.get_all_budgets()

if not budgets_data:
    st.warning("Nenhum orçamento encontrado ou falha ao carregar.")
else:
    df_orcamentos = pd.DataFrame(budgets_data)
    
    # Tratamentos básicos de tipos (similar à original)
    if ColunasOrcamentos.ATUALIZACAO in df_orcamentos.columns:
        df_orcamentos[ColunasOrcamentos.ATUALIZACAO] = pd.to_datetime(
            df_orcamentos[ColunasOrcamentos.ATUALIZACAO], errors="coerce"
        )
    if ColunasOrcamentos.LIMITE in df_orcamentos.columns:
        df_orcamentos[ColunasOrcamentos.LIMITE] = pd.to_numeric(
             df_orcamentos[ColunasOrcamentos.LIMITE], errors="coerce"
        ).fillna(0.0)
    
    # Reordenar colunas
    cols = [c for c in df_orcamentos.columns if c != ColunasOrcamentos.ID]
    if ColunasOrcamentos.ID in df_orcamentos.columns:
        cols = [ColunasOrcamentos.ID] + cols
    df_orcamentos = df_orcamentos[cols]

    editor_key_orc = "editor_orcamentos_api"

    edited_df_orc = st.data_editor(
        df_orcamentos,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            ColunasOrcamentos.ID: st.column_config.NumberColumn(disabled=True),
            ColunasOrcamentos.CATEGORIA: st.column_config.TextColumn(
                required=True, help="Nome da categoria (Ex: Alimentação)"
            ),
            ColunasOrcamentos.LIMITE: st.column_config.NumberColumn(
                format="R$ %.2f",
                required=True,
                min_value=0.0,
                step=0.01,
                help="O valor máximo que você planeja gastar nesta categoria por mês.",
            ),
            ColunasOrcamentos.PERIODO: st.column_config.SelectboxColumn(
                options=["Mensal", "Anual", "Único"],
                default="Mensal",
                required=True,
                help="Frequência do orçamento.",
            ),
            ColunasOrcamentos.OBS: st.column_config.TextColumn(),
            ColunasOrcamentos.GASTO: st.column_config.NumberColumn(
                format="R$ %.2f", disabled=True
            ),
            # O progresso é visual apenas
            ColunasOrcamentos.PERCENTUAL: st.column_config.ProgressColumn(
                format="%.1f%%", min_value=0, max_value=100
            ),
            ColunasOrcamentos.STATUS: st.column_config.TextColumn(disabled=True),
            ColunasOrcamentos.ATUALIZACAO: st.column_config.DatetimeColumn(
                disabled=True, format="YYYY-MM-DD HH:mm:ss"
            ),
        },
        hide_index=True,
        key=editor_key_orc,
    )

    if not df_orcamentos.equals(edited_df_orc):
        if st.button("Salvar Alterações nos Orçamentos"):
            st.info("Enviando alterações para a API...")
            try:
                # Conversão de Datas para String
                edited_df_to_send = edited_df_orc.copy()
                if ColunasOrcamentos.ATUALIZACAO in edited_df_to_send.columns:
                     edited_df_to_send[ColunasOrcamentos.ATUALIZACAO] = edited_df_to_send[ColunasOrcamentos.ATUALIZACAO].astype(str)

                records = edited_df_to_send.to_dict(orient="records")
                success = api_client.update_budgets_bulk(records)
                
                if success:
                    st.success("Orçamentos atualizados com sucesso!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar via API.")
            except Exception as e:
                st.error(f"Erro: {e}")
