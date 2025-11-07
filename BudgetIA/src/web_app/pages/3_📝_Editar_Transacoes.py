# pages/3_📝_Editar_Transacoes.py
import pandas as pd
import streamlit as st

from config import NomesAbas

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page

plan_manager, agent_runner = setup_page(
    title="Editar Transações",
    icon="📝",
)

aba_transacoes = NomesAbas.TRANSACOES

try:
    df_transacoes = plan_manager.visualizar_dados(aba_nome=aba_transacoes)
    st.info("Gerencie diretamente as transações")
    if "Data" in df_transacoes.columns:
        df_transacoes["Data"] = pd.to_datetime(df_transacoes["Data"], errors="coerce")

    # Usar uma chave única para o data_editor
    editor_key = "editor_transacoes"

    # Verifica se há dados editados no estado da sessão (preservar entre reruns)
    if f"{editor_key}_edited_rows" in st.session_state:
        edited_rows = st.session_state[f"{editor_key}_edited_rows"]
        # Potencialmente aplicar edições aqui se necessário antes de renderizar,
        # mas o data_editor geralmente lida bem com isso.
        pass

    edited_df = st.data_editor(
        df_transacoes,
        num_rows="dynamic",  # Permite adicionar/deletar linhas
        use_container_width=True,
        # Configurar colunas para melhor edição e validação
        column_config={
            "ID Transacao": st.column_config.NumberColumn(
                disabled=True
            ),  # ID não deve ser editável
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
        key=editor_key,  # Atribui a chave
    )

    # Comparar o DataFrame editado com o original
    if not df_transacoes.equals(edited_df):
        if st.button("Salvar Alterações nas Transações"):
            st.info("Salvando alterações e recalculando...")
            try:
                # Validar dados antes de salvar (ex: valores negativos onde não devem)
                if (edited_df["Valor"] < 0).any():
                    st.warning(
                        "Valores negativos detectados na coluna 'Valor'. Verifique as transações."
                    )
                    # Poderia parar aqui ou tentar corrigir/alertar mais

                plan_manager.update_dataframe(aba_transacoes, edited_df)
                plan_manager.recalculate_budgets()  # Recalcula orçamentos
                plan_manager.save()
                st.success("Planilha atualizada com sucesso!")
                # Limpar o estado de edição após salvar
                # st.session_state[f"{editor_key}_edited_rows"] = {} # Limpa edições pendentes (opcional)
                st.rerun()  # Recarrega para mostrar dados salvos
            except Exception as e:
                st.error(f"Erro ao salvar alterações nas transações: {e}")
                st.exception(e)  # Mostra traceback para debug
        else:
            st.warning("Você tem alterações não salvas.")

except Exception as e:
    st.error(f"Erro ao carregar ou editar transações: {e}")
    st.exception(e)
