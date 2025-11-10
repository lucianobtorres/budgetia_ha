# pages/1_📊_Dashboard.py

import pandas as pd
import streamlit as st

from config import ColunasOrcamentos, NomesAbas, SummaryKeys

try:
    from ..ui_components.common_ui import setup_page
except ImportError:
    from web_app.ui_components.common_ui import setup_page

plan_manager, agent_runner = setup_page(
    title="Dashboard Financeiro",
    icon="📊",
)

try:
    summary = plan_manager.get_summary()

    # --- DEBUG PRINT 1 ---
    # Vamos ver o que o summary realmente contém QUANDO A PÁGINA RODA
    print(f"--- DEBUG (Dashboard): Sumário carregado: {summary} ---")
    # --- FIM DO DEBUG ---

    st.info("Aqui você verá um resumo visual dos seus dados financeiros.")
    if summary and (
        summary.get(SummaryKeys.RECEITAS, 0) > 0
        or summary.get(SummaryKeys.DESPESAS, 0) > 0
    ):
        col1, col2, col3 = st.columns(3)

        # Formatação BRL (ponto e vírgula)
        saldo_str_br = (
            f"{summary.get(SummaryKeys.SALDO, 0):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        receitas_str_br = (
            f"{summary.get(SummaryKeys.RECEITAS, 0):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        despesas_str_br = (
            f"{summary.get(SummaryKeys.DESPESAS, 0):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        col1.metric(label="Total de Receitas", value=f"R$ {receitas_str_br}")
        col2.metric(label="Total de Despesas", value=f"R$ {despesas_str_br}")
        col3.metric(label="Saldo Atual", value=f"R$ {saldo_str_br}")

        st.subheader("Top 5 Despesas por Categoria")
        despesas_por_categoria = plan_manager.get_expenses_by_category(top_n=5)
        if not despesas_por_categoria.empty:
            # Opcional: Formatar valores do gráfico para BRL se possível/necessário
            st.bar_chart(despesas_por_categoria)
        else:
            st.info("Ainda não há despesas registradas este mês para gerar o gráfico.")

        st.subheader("Resumo dos Orçamentos Mensais Ativos")
        df_orcamentos = plan_manager.visualizar_dados(aba_nome=NomesAbas.ORCAMENTOS)
        if not df_orcamentos.empty:
            orcamentos_mensais_ativos = df_orcamentos[
                (
                    df_orcamentos[ColunasOrcamentos.PERIODO].astype(str).str.lower()
                    == "mensal"
                )
                & (df_orcamentos[ColunasOrcamentos.STATUS] != "Inativo")  # Exemplo
            ].copy()  # Usar .copy() para evitar SettingWithCopyWarning

            if not orcamentos_mensais_ativos.empty:
                # Aplicar formatação BRL às colunas relevantes ANTES do loop
                for col in [ColunasOrcamentos.LIMITE, ColunasOrcamentos.GASTO]:
                    if col in orcamentos_mensais_ativos.columns:
                        # Tratar possíveis valores não numéricos antes de formatar
                        orcamentos_mensais_ativos[f"{col}_BRL"] = (
                            orcamentos_mensais_ativos[col].apply(
                                lambda x: f"{float(x):,.2f}".replace(",", "X")
                                .replace(".", ",")
                                .replace("X", ".")
                                if pd.notna(x) and isinstance(x, (int, float))
                                else "0,00"
                            )
                        )

                for index, row in orcamentos_mensais_ativos.iterrows():
                    # Usar as colunas formatadas _BRL que criamos
                    limite_brl = row.get("Valor Limite Mensal_BRL", "0,00")
                    gasto_brl = row.get("Valor Gasto Atual_BRL", "0,00")
                    porcentagem = row.get(ColunasOrcamentos.PERCENTUAL, 0.0)
                    status = row.get(ColunasOrcamentos.STATUS, "N/A")
                    categoria = row.get(ColunasOrcamentos.CATEGORIA, "N/A")

                    st.markdown(
                        f"**{categoria}**: Orçado R$ {limite_brl}, "
                        f"Gasto R$ {gasto_brl} "
                        f"({porcentagem:.1f}%) - Status: **{status}**"
                    )
            else:
                st.info("Nenhum orçamento mensal ativo configurado.")
        else:
            st.info("Nenhum orçamento configurado. Defina na aba 'Meus Orçamentos'.")
    else:
        # --- DEBUG PRINT 2 ---
        # Se chegarmos aqui, o PRINT 1 nos dirá o porquê.
        print(
            "--- DEBUG (Dashboard): 'summary' considerado vazio. Mostrando aviso. ---"
        )
        # --- FIM DO DEBUG ---
        st.info(
            "Sua planilha de transações parece estar vazia. "
            "Adicione receitas/despesas usando o 'Chat com a IA' ou editando as 'Transações'."
        )
except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o dashboard: {e}")
    st.exception(e)  # Mostra o traceback completo para debug
