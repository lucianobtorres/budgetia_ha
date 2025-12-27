
import streamlit as st
import pandas as pd
from typing import Any
import sys
import os

# Adiciona o 'src' ao path (para acesso a config/enums se necessário, 
# embora devêssemos mover constantes para um lugar comum)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import ColunasTransacoes, ValoresTipo
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

st.set_page_config(page_title="Editar Transações", page_icon="📝", layout="wide")

st.title("📝 Editar Transações")
st.info("Gerencie suas transações diretamente aqui. As alterações são salvas na planilha via API.")

# --- Busca Dados ---
# Por enquanto trazemos um limite alto para edição, mas idealmente seria paginado
# Se for muito grande, o GET transactions pode demorar.
transactions_data = api_client.get_transactions(limit=1000)

if not transactions_data:
    st.warning("Nenhuma transação encontrada ou falha ao carregar.")
else:
    df_transacoes = pd.DataFrame(transactions_data)
    
    # Normalização de Datas
    if ColunasTransacoes.DATA in df_transacoes.columns:
        df_transacoes[ColunasTransacoes.DATA] = pd.to_datetime(
            df_transacoes[ColunasTransacoes.DATA], errors="coerce"
        ).dt.date
    
    # Reordenar colunas se possível (ID primeiro)
    cols = [c for c in df_transacoes.columns if c != ColunasTransacoes.ID]
    if ColunasTransacoes.ID in df_transacoes.columns:
        cols = [ColunasTransacoes.ID] + cols
    df_transacoes = df_transacoes[cols]

    editor_key = "editor_transacoes_api"

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
            st.info("Enviando alterações para a API...")
            
            try:
                # Validação Básica
                if ColunasTransacoes.VALOR in edited_df.columns:
                    if (edited_df[ColunasTransacoes.VALOR] < 0).any():
                        st.warning("Atenção: Valores negativos detectados.")

                # Converte para lista de dicts para JSON
                # Converte datas para string ISO
                edited_df_to_send = edited_df.copy()
                if ColunasTransacoes.DATA in edited_df_to_send.columns:
                     edited_df_to_send[ColunasTransacoes.DATA] = edited_df_to_send[ColunasTransacoes.DATA].astype(str)
                
                records = edited_df_to_send.to_dict(orient="records")
                
                success = api_client.update_transactions_bulk(records)
                
                if success:
                    st.success("Transações atualizadas com sucesso!")
                    st.rerun()
                else:
                    st.error("Falha ao salvar via API. Verifique se o servidor está rodando.")
            
            except Exception as e:
                st.error(f"Erro no processamento: {e}")
