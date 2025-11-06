# Em: src/web_app/pages/5_👤_Perfil_Financeiro.py

import pandas as pd
import streamlit as st

import config
from config import NomesAbas
from finance.planilha_manager import PlanilhaManager
from web_app.utils import verificar_perfil_preenchido

# --- Verificação de Inicialização ---
if "plan_manager" not in st.session_state:
    st.error("Erro: O sistema financeiro não foi carregado. Volte à página principal.")
    st.stop()

plan_manager: PlanilhaManager = st.session_state.plan_manager
aba_perfil = NomesAbas.PERFIL_FINANCEIRO

# --- Renderização da Página ---
st.header(f"👤 Editar: {aba_perfil}")  # Corrigido: sem .value

try:
    df_perfil = plan_manager.visualizar_dados(aba_nome=aba_perfil)

    # Adiciona linhas padrão se estiver vazio ou faltando
    campos_essenciais = ["Renda Mensal Média", "Principal Objetivo"]
    campos_desejados = campos_essenciais + [
        "Tolerância a Risco"
    ]  # Adiciona outros que queremos

    dados_para_adicionar = []
    # Garante que a coluna 'Campo' exista antes de tentar acessá-la
    campos_existentes = (
        set(df_perfil["Campo"])
        if not df_perfil.empty and "Campo" in df_perfil.columns
        else set()
    )

    for campo in campos_desejados:
        if campo not in campos_existentes:
            dados_para_adicionar.append(
                {"Campo": campo, "Valor": None, "Observações": ""}
            )

    # Concatena os campos faltantes (se houver)
    if dados_para_adicionar:
        # Garante que o df_perfil tenha as colunas corretas antes de concatenar
        if df_perfil.empty:
            df_perfil = pd.DataFrame(columns=config.LAYOUT_PLANILHA[aba_perfil])

        df_perfil = pd.concat(
            [
                df_perfil,
                pd.DataFrame(
                    dados_para_adicionar, columns=config.LAYOUT_PLANILHA[aba_perfil]
                ),
            ],
            ignore_index=True,
        )
    if "Campo" in df_perfil.columns:
        df_perfil["Campo"] = df_perfil["Campo"].astype(str).fillna("")

    if "Valor" in df_perfil.columns:
        # A coluna 'Valor' também é TextColumn, pois armazena números (Renda)
        # e texto (Objetivo). Deve ser string.
        df_perfil["Valor"] = df_perfil["Valor"].astype(str).fillna("")

    if "Observações" in df_perfil.columns:
        df_perfil["Observações"] = df_perfil["Observações"].astype(str).fillna("")
    editor_key_perfil = "editor_perfil"

    edited_df_perfil = st.data_editor(
        df_perfil,
        num_rows="dynamic",  # Permite adicionar novos campos
        use_container_width=True,
        column_config={
            "Campo": st.column_config.TextColumn(
                required=True, help="Nome do dado (Ex: Renda Mensal Média)."
            ),
            "Valor": st.column_config.TextColumn(
                required=True, help="O valor correspondente ao campo."
            ),
            "Observações": st.column_config.TextColumn(help="Notas opcionais."),
        },
        hide_index=True,
        key=editor_key_perfil,
    )

    # Lógica de salvamento
    if not df_perfil.equals(edited_df_perfil):
        if st.button("Salvar Alterações no Perfil"):
            st.info("Salvando perfil...")
            try:
                # Remover linhas onde o Campo é vazio/nulo
                edited_df_perfil_cleaned = edited_df_perfil.dropna(subset=["Campo"])

                plan_manager.update_dataframe(aba_perfil, edited_df_perfil_cleaned)
                plan_manager.save()
                st.success("Perfil Financeiro atualizado com sucesso!")

                # Re-verifica o perfil para dar feedback imediato
                if verificar_perfil_preenchido(plan_manager):
                    st.info("Status: Perfil parece completo.")
                else:
                    st.warning(
                        "Status: Perfil ainda parece incompleto (campos essenciais podem estar vazios ou faltando)."
                    )

                st.rerun()  # Recarrega a página
            except Exception as e:
                st.error(f"Erro ao salvar alterações no Perfil: {e}")
                st.exception(e)
        else:
            st.warning("Você tem alterações não salvas.")

except Exception as e:
    st.error(f"Erro ao carregar o Perfil Financeiro: {e}")
    st.exception(e)
