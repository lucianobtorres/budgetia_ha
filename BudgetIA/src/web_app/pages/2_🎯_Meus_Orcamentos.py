# pages/4_🎯_Meus_Orcamentos.py
import pandas as pd
import streamlit as st

# Importar NomesAbas e PlanilhaManager
from config import ColunasOrcamentos, NomesAbas

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
plan_manager, agent_runner = setup_page(
    title="Meus Orçamentos",
    icon="🎯",
)

aba_orcamentos = NomesAbas.ORCAMENTOS

try:
    df_orcamentos = plan_manager.visualizar_dados(aba_nome=aba_orcamentos)
    st.info("O sistema irá monitorar seus gastos automaticamente.")
    editor_key_orc = "editor_orcamentos"

    # --- Conversão de Tipo Preventiva ---
    if "Última Atualização Orçamento" in df_orcamentos.columns:
        df_orcamentos["Última Atualização Orçamento"] = pd.to_datetime(
            df_orcamentos["Última Atualização Orçamento"], errors="coerce"
        )

    # Verifica se há dados editados no estado da sessão (preservar entre reruns)
    if f"{editor_key_orc}_edited_rows" in st.session_state:
        edited_rows = st.session_state[f"{editor_key_orc}_edited_rows"]
        # Potencialmente aplicar edições aqui se necessário antes de renderizar,
        # mas o data_editor geralmente lida bem com isso.
        pass

    edited_df_orc = st.data_editor(
        df_orcamentos,
        num_rows="dynamic",
        use_container_width=True,
        column_config={  # Configurações para melhor edição
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
                help="Frequência do orçamento (geralmente Mensal).",
            ),
            ColunasOrcamentos.OBS: st.column_config.TextColumn(
                help="Notas opcionais sobre este orçamento."
            ),
            # Colunas calculadas não devem ser editáveis diretamente
            ColunasOrcamentos.GASTO: st.column_config.NumberColumn(
                format="R$ %.2f", disabled=True
            ),
            ColunasOrcamentos.PERCENTUAL: st.column_config.ProgressColumn(  # Usar barra de progresso!
                format="%.1f%%",
                min_value=0,
                max_value=100,  # A barra vai até 100%, mesmo se exceder
            ),
            ColunasOrcamentos.STATUS: st.column_config.TextColumn(disabled=True),
            "Última Atualização Orçamento": st.column_config.DatetimeColumn(
                disabled=True, format="YYYY-MM-DD HH:mm:ss"
            ),
        },
        # Esconder colunas calculadas que não são tão úteis na edição direta
        hide_index=True,
        # column_order = [...] # Opcional: Definir ordem das colunas
        key=editor_key_orc,
    )

    if not df_orcamentos.equals(edited_df_orc):
        if st.button("Salvar Alterações nos Orçamentos"):
            st.info("Salvando e recalculando...")
            try:
                # Validações antes de salvar
                if (edited_df_orc[ColunasOrcamentos.LIMITE] <= 0).any():
                    st.warning(
                        "Orçamentos devem ter um 'Valor Limite Mensal' positivo."
                    )
                    # Poderia impedir o salvamento ou apenas alertar
                else:
                    plan_manager.update_dataframe(aba_orcamentos, edited_df_orc)
                    plan_manager.recalculate_budgets()  # Recalcula após editar
                    plan_manager.save()
                    st.success("Orçamentos atualizados com sucesso!")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar alterações nos orçamentos: {e}")
                st.exception(e)
        else:
            st.warning("Você tem alterações não salvas.")

    st.caption(
        "Preencha 'Categoria', 'Valor Limite Mensal' e 'Período'. As outras colunas são calculadas pelo sistema."
    )

except Exception as e:
    st.error(f"Erro ao carregar ou editar orçamentos: {e}")
    st.exception(e)
