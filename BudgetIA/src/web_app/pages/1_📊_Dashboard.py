# pages/1_📊_Dashboard.py

import pandas as pd  # Necessário para a verificação e formatação
import streamlit as st

# Importar NomesAbas e PlanilhaManager (ajuste o caminho se necessário)
from config import NomesAbas
from finance.planilha_manager import PlanilhaManager

# --- Verificação de Inicialização ---
# Garante que o PlanilhaManager foi carregado pelo app.py principal
if "plan_manager" not in st.session_state:
    st.error(
        "Erro: O sistema financeiro não foi carregado corretamente. Por favor, volte à página principal (app.py)."
    )
    st.stop()  # Interrompe a execução desta página

# Recupera o PlanilhaManager do estado da sessão
plan_manager: PlanilhaManager = st.session_state.plan_manager

# --- Renderização da Página do Dashboard ---
st.header("📊 Dashboard Financeiro")
st.write("Aqui você verá um resumo visual dos seus dados financeiros.")

try:
    summary = plan_manager.get_summary()

    if summary and (summary.get("receitas", 0) > 0 or summary.get("despesas", 0) > 0):
        col1, col2, col3 = st.columns(3)

        # Formatação BRL (ponto e vírgula)
        saldo_str_br = (
            f"{summary.get('saldo', 0):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        receitas_str_br = (
            f"{summary.get('receitas', 0):,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        despesas_str_br = (
            f"{summary.get('despesas', 0):,.2f}".replace(",", "X")
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
                (df_orcamentos["Período Orçamento"].astype(str).str.lower() == "mensal")
                & (df_orcamentos["Status Orçamento"] != "Inativo")  # Exemplo
            ].copy()  # Usar .copy() para evitar SettingWithCopyWarning

            if not orcamentos_mensais_ativos.empty:
                # Aplicar formatação BRL às colunas relevantes ANTES do loop
                for col in ["Valor Limite Mensal", "Valor Gasto Atual"]:
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
                    porcentagem = row.get("Porcentagem Gasta (%)", 0.0)
                    status = row.get("Status Orçamento", "N/A")
                    categoria = row.get("Categoria", "N/A")

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
        st.info(
            "Sua planilha de transações parece estar vazia. "
            "Adicione receitas/despesas usando o 'Chat com a IA' ou editando as 'Transações'."
        )
except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o dashboard: {e}")
    st.exception(e)  # Mostra o traceback completo para debug
