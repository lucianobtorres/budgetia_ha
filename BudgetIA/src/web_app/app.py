# src/web_app/app.py

import os
import time
from pathlib import Path
from typing import Any

import streamlit as st

# Imports do seu projeto
from config import (  # Importar NomesAbas para verificar_perfil_preenchido
    DATA_DIR,
)
from finance.planilha_manager import PlanilhaManager
from initialization.system_initializer import initialize_financial_system

# Importar TODAS as funções de utils
from web_app.utils import (
    PLANILHA_KEY,  # Importar a chave usada no JSON
    get_saved_planilha_path,
    # Adicione load_persistent_config e save_persistent_config se precisar do botão de reset
    load_persistent_config,
    save_persistent_config,
    save_planilha_path,
    verificar_perfil_preenchido,
)

# --- Constantes e Funções Helper ---
PLANILHA_PATH_STATE_KEY = "planilha_path"  # Chave para o session_state

# --- DEBUG INICIAL DO SCRIPT ---
print("\n--- SCRIPT START ---")
print(f"Session State Keys AT START: {list(st.session_state.keys())}")
# --- FIM DEBUG INICIAL ---


# Função load_financial_system (com @st.cache_resource e prints de debug)
# @st.cache_resource
def load_financial_system(
    planilha_path: str,
) -> tuple[PlanilhaManager | None, Any | None, Any | None, bool]:
    print(f"\n--- DEBUG: Entrando em load_financial_system para '{planilha_path}' ---")
    try:
        print("--- DEBUG: Chamando initialize_financial_system... ---")
        plan_manager, agent_runner, llm_orchestrator, dados_adicionados = (
            initialize_financial_system(planilha_path)
        )
        print("--- DEBUG: initialize_financial_system RETORNOU: ---")
        print(f"   plan_manager: {type(plan_manager)}")
        print(f"   agent_runner: {type(agent_runner)}")
        print(f"   llm_orchestrator: {type(llm_orchestrator)}")
        print(f"   dados_adicionados: {dados_adicionados}")

        if plan_manager and agent_runner and llm_orchestrator:
            print("--- DEBUG: load_financial_system retornando objetos válidos. ---")
            return plan_manager, agent_runner, llm_orchestrator, dados_adicionados
        else:
            print("--- DEBUG ERROR: initialize_financial_system retornou None! ---")
            st.error("Falha interna ao inicializar componentes.")
            st.stop()
            return None, None, None, False
    except FileNotFoundError:
        print(f"--- DEBUG ERROR: FileNotFoundError para '{planilha_path}' ---")
        st.error(
            f"Erro Crítico: Planilha não encontrada em '{planilha_path}'. Limpando configuração."
        )
        if PLANILHA_PATH_STATE_KEY in st.session_state:
            del st.session_state[PLANILHA_PATH_STATE_KEY]
        # Limpar config persistente também
        config_data = load_persistent_config()
        config_data.pop(PLANILHA_KEY, None)
        save_persistent_config(config_data)
        st.rerun()
        return None, None, None, False
    except Exception as e:
        print(f"--- DEBUG ERROR: Exception em load_financial_system: {e} ---")
        st.error(f"Erro inesperado ao carregar sistema: {e}")
        st.exception(e)
        st.stop()
        return None, None, None, False


# --- Configuração da Página Streamlit ---
st.set_page_config(
    page_title="BudgetIA",
    page_icon="💰",
    layout="wide",
)

# --- Inicialização das variáveis (apenas para este script) ---
onboarding_necessario = False  # Assume que não precisa até verificar

# --- LÓGICA DE INICIALIZAÇÃO REFINADA ---

# 1. Verifica se já temos o caminho no session_state
if PLANILHA_PATH_STATE_KEY not in st.session_state:
    print(
        "\n--- DEBUG APP: Chave da planilha NÃO está no session_state. Verificando config persistente... ---"
    )
    # 2. Tenta carregar da configuração persistente
    saved_path = get_saved_planilha_path()
    if saved_path:
        print(
            f"--- DEBUG APP: Caminho encontrado no config persistente: {saved_path}. Salvando no session_state. ---"
        )
        # 3. Se encontrou, salva no session_state (a execução continua para o 'else' abaixo)
        st.session_state[PLANILHA_PATH_STATE_KEY] = saved_path
        # >>> IMPORTANTE: Forçar rerun AQUI para garantir que o else seja executado corretamente <<<
        st.rerun()
    else:
        # 4. Se não encontrou no config, MOSTRA A UI DE SELEÇÃO
        print(
            "--- DEBUG APP: Nenhum caminho válido no config. Mostrando UI de seleção/criação. ---"
        )
        st.title("💰 Bem-vindo ao BudgetIA!")
        st.info("Para começar, precisamos de uma planilha.")

        col1, col2 = st.columns(2)
        with col1:  # Criar Nova
            st.subheader("🚀 Criar Nova Planilha Mestra")
            st.markdown(
                f"Recomendado. Criaremos uma planilha organizada na pasta `{DATA_DIR}`."
            )
            default_path = str(Path(DATA_DIR) / "planilha_mestra.xlsx")
            novo_path_input = st.text_input(
                "Nome e local:", default_path, key="novo_path"
            )

            if st.button("Criar e Usar", key="criar_nova"):
                novo_path = Path(novo_path_input)
                if not novo_path.name.endswith(".xlsx"):
                    st.error("O nome do arquivo deve terminar com .xlsx")
                elif novo_path.exists():
                    st.warning(f"O arquivo '{novo_path}' já existe.")
                    st.info(
                        "Se deseja usar este arquivo, use a opção 'Usar Minha Planilha Existente'."
                    )
                else:
                    try:
                        novo_path.parent.mkdir(parents=True, exist_ok=True)
                        # Validar chamando initialize_financial_system
                        temp_pm, _, _, _ = initialize_financial_system(str(novo_path))
                        if temp_pm:
                            print(
                                f"--- DEBUG IF (Criar): TENTANDO SETAR session_state['{PLANILHA_PATH_STATE_KEY}'] = {str(novo_path)} ---"
                            )
                            save_planilha_path(str(novo_path))  # Salva persistente
                            st.session_state[PLANILHA_PATH_STATE_KEY] = str(novo_path)
                            print(
                                f"--- DEBUG IF (Criar): session_state['{PLANILHA_PATH_STATE_KEY}'] AGORA É: {st.session_state.get(PLANILHA_PATH_STATE_KEY)} ---"
                            )
                            st.success(f"Planilha criada: '{novo_path}'!")
                            time.sleep(1)
                            print("--- DEBUG IF (Criar): Chamando st.rerun()... ---")
                            st.rerun()
                        else:
                            st.error(
                                "Falha ao inicializar o sistema com a nova planilha."
                            )
                    except Exception as e:
                        st.error(f"Erro ao criar ou inicializar planilha: {e}")
                        st.exception(e)  # Mostra traceback

        with col2:  # Usar Existente
            st.subheader("📂 Usar Minha Planilha Existente")
            st.markdown("Selecione sua planilha (`.xlsx`).")
            uploaded_file = st.file_uploader(
                "Carregar (.xlsx)", type=["xlsx"], key="uploader"
            )
            if uploaded_file is not None:
                save_path = Path(DATA_DIR) / uploaded_file.name
                try:
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    # Validar
                    temp_pm, _, _, _ = initialize_financial_system(str(save_path))
                    if temp_pm:
                        print(
                            f"--- DEBUG IF (Upload): TENTANDO SETAR session_state['{PLANILHA_PATH_STATE_KEY}'] = {str(save_path)} ---"
                        )
                        save_planilha_path(str(save_path))  # Salva persistente
                        st.session_state[PLANILHA_PATH_STATE_KEY] = str(save_path)
                        print(
                            f"--- DEBUG IF (Upload): session_state['{PLANILHA_PATH_STATE_KEY}'] AGORA É: {st.session_state.get(PLANILHA_PATH_STATE_KEY)} ---"
                        )
                        st.success(f"Planilha '{uploaded_file.name}' carregada!")
                        time.sleep(1)
                        print("--- DEBUG IF (Upload): Chamando st.rerun()... ---")
                        st.rerun()
                    else:
                        st.error(
                            "Não foi possível carregar o sistema com a planilha fornecida."
                        )
                        if save_path.exists():
                            os.remove(save_path)
                except Exception as e:
                    st.error(f"Erro ao processar planilha: {e}")
                    if save_path.exists():
                        try:
                            os.remove(save_path)
                        except OSError:
                            pass

            st.markdown("--- OU ---")
            path_input = st.text_input("Insira o caminho completo:", key="path_input")
            if st.button("Usar por Caminho", key="usar_path"):
                path_obj = Path(path_input)
                if not path_obj.is_file():
                    st.error(f"Arquivo não encontrado: {path_input}")
                elif not path_obj.name.endswith(".xlsx"):
                    st.error("O arquivo deve ser .xlsx")
                else:
                    try:
                        # Validar
                        temp_pm, _, _, _ = initialize_financial_system(str(path_obj))
                        if temp_pm:
                            print(
                                f"--- DEBUG IF (Path): TENTANDO SETAR session_state['{PLANILHA_PATH_STATE_KEY}'] = {str(path_obj)} ---"
                            )
                            save_planilha_path(str(path_obj))  # Salva persistente
                            st.session_state[PLANILHA_PATH_STATE_KEY] = str(path_obj)
                            print(
                                f"--- DEBUG IF (Path): session_state['{PLANILHA_PATH_STATE_KEY}'] AGORA É: {st.session_state.get(PLANILHA_PATH_STATE_KEY)} ---"
                            )
                            st.success(f"Usando: {path_obj}")
                            time.sleep(1)
                            print("--- DEBUG IF (Path): Chamando st.rerun()... ---")
                            st.rerun()
                        else:
                            st.error(
                                "Não foi possível carregar o sistema com a planilha no caminho fornecido."
                            )
                    except Exception as e:
                        st.error(f"Erro ao carregar do caminho '{path_obj}': {e}")
                        st.exception(e)

        # Interrompe aqui se nenhuma seleção foi feita ainda
        st.stop()

# --- SE CHEGOU AQUI, PLANILHA_PATH_STATE_KEY JÁ EXISTE NO session_state ---
print(
    f"\n--- DEBUG APP: Chave '{PLANILHA_PATH_STATE_KEY}' JÁ ESTÁ no session_state. Prosseguindo... ---"
)
current_planilha_path = st.session_state[PLANILHA_PATH_STATE_KEY]

# 5. Carrega o sistema (usando cache se já carregado para este path)
print(
    f"--- DEBUG APP: Chamando load_financial_system para: {current_planilha_path} ---"
)
plan_manager, agent_runner, llm_orchestrator, dados_adicionados = load_financial_system(
    current_planilha_path
)

# 6. Salva objetos no session_state (necessário para as páginas)
if plan_manager and agent_runner and llm_orchestrator:
    print("--- DEBUG APP: Armazenando objetos no session_state (pós-load)... ---")
    st.session_state.plan_manager = plan_manager
    st.session_state.agent_runner = agent_runner
    st.session_state.llm_orchestrator = llm_orchestrator
    st.session_state.current_planilha_path = current_planilha_path
    print(
        f"--- DEBUG APP: st.session_state.plan_manager agora é {type(st.session_state.get('plan_manager'))} ---"
    )
else:
    print(
        "--- DEBUG APP ERROR: Falha ao obter objetos válidos de load_financial_system. Interrompendo. ---"
    )
    st.error("Falha crítica ao carregar componentes do sistema.")
    if st.button("Tentar Novamente (Limpar Configuração)"):
        config_data = load_persistent_config()
        config_data.pop(PLANILHA_KEY, None)
        save_persistent_config(config_data)
        if PLANILHA_PATH_STATE_KEY in st.session_state:
            del st.session_state[PLANILHA_PATH_STATE_KEY]
        st.rerun()
    st.stop()  # Interrompe se o carregamento falhou

# 7. Verifica perfil e decide se mostra onboarding de perfil
# Só verifica o perfil se o plan_manager foi carregado com sucesso
onboarding_necessario = (
    not verificar_perfil_preenchido(plan_manager) if plan_manager else False
)
print(
    f"--- DEBUG APP: Verificação de perfil: onboarding_necessario = {onboarding_necessario} ---"
)

# Mensagem de dados de exemplo
if dados_adicionados and "dados_exemplo_msg_mostrada" not in st.session_state:
    st.success("Dados de exemplo foram carregados na sua planilha!")
    st.session_state.dados_exemplo_msg_mostrada = True

# --- RENDERIZAÇÃO CONDICIONAL FINAL ---
if onboarding_necessario:
    print(
        "--- DEBUG APP: Onboarding do perfil é necessário. Mostrando UI de coleta... ---"
    )
    # --- UI DE COLETA DE PERFIL (AINDA NO app.py) ---
    st.header("✨ Configurando seu Perfil Financeiro")
    st.warning("Seu perfil financeiro parece incompleto...")
    st.markdown(
        "Converse com a IA abaixo para configurar sua **Renda Mensal Média** e **Principal Objetivo Financeiro**:"
    )

    # Interface de Chat para Onboarding (Lógica SIMULADA - PRECISA IMPLEMENTAR COM A FERRAMENTA REAL)
    if "onboarding_messages" not in st.session_state:
        st.session_state.onboarding_messages = [
            {
                "role": "assistant",
                "content": "Olá! Para começar, qual sua Renda Mensal Média?",
            }
        ]

    for message in st.session_state.onboarding_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Responda à IA...", key="onboarding_input"):
        st.session_state.onboarding_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analisando e salvando..."):
                # --- INÍCIO DA LÓGICA REAL DA IA ---
                if "agent_runner" in st.session_state:
                    agent_runner = st.session_state.agent_runner

                    prompt_guiado = (
                        f"O usuário respondeu: '{prompt}'.\n"
                        "Seu ÚNICO objetivo é extrair DADOS DE PERFIL (especificamente 'Renda Mensal Média' ou 'Principal Objetivo') desta resposta. "
                        "Se você extrair um dado, use a ferramenta 'coletar_perfil_usuario' IMEDIATAMENTE para salvar o par 'campo' e 'valor' (ex: campo='Renda Mensal Média', valor=5000). "
                        "Após salvar, confirme o que salvou e faça a próxima pergunta (se a Renda foi dada, pergunte o Objetivo; se o Objetivo foi dado, pergunte a Renda). "
                        "Se você não conseguir extrair um dado válido, peça educadamente pela informação novamente (Renda ou Objetivo)."
                        "NÃO use outras ferramentas. NÃO responda a perguntas aleatórias. Foque 100% em preencher o perfil."
                    )

                    try:
                        # --- CORREÇÃO: Usar .interagir() ---
                        output = agent_runner.interagir(prompt_guiado)

                        st.markdown(output)
                        st.session_state.onboarding_messages.append(
                            {"role": "assistant", "content": output}
                        )

                    except Exception as e:
                        output = f"Ocorreu um erro ao processar sua resposta: {e}"
                        print(f"--- DEBUG ONBOARDING ERROR: {e} ---")
                        st.error(output)
                        st.session_state.onboarding_messages.append(
                            {"role": "assistant", "content": output}
                        )

                else:
                    output = "Erro: Agente de IA não está disponível (não encontrado no session_state)."
                    st.error(output)
                    st.session_state.onboarding_messages.append(
                        {"role": "assistant", "content": output}
                    )

                # --- FIM DA LÓGICA REAL ---

                # --- CORREÇÃO: Mover a verificação para DEPOIS da execução da IA ---
                print(
                    "--- DEBUG ONBOARDING: Verificando perfil após chamada da IA... ---"
                )
                if verificar_perfil_preenchido(st.session_state.plan_manager):
                    print(
                        "--- DEBUG ONBOARDING: Perfil COMPLETO! Agendando rerun... ---"
                    )
                    st.session_state.onboarding_completo_flag = True  # Flag para rerun
                else:
                    print(
                        "--- DEBUG ONBOARDING: Perfil ainda incompleto após chamada da IA. ---"
                    )
                    if "onboarding_completo_flag" in st.session_state:
                        del st.session_state.onboarding_completo_flag

        # Rerun SÓ SE o perfil foi completado
        if st.session_state.get("onboarding_completo_flag", False):
            print("--- DEBUG ONBOARDING: Executando rerun agendado... ---")
            del st.session_state.onboarding_completo_flag
            st.success("Perfil configurado! Redirecionando para o Dashboard...")
            time.sleep(2)
            st.rerun()

    st.stop()

else:
    # --- ONBOARDING CONCLUÍDO - DEIXA STREAMLIT ASSUMIR ---
    print(
        "--- DEBUG APP: Onboardings concluídos. Permitindo navegação multi-página... ---"
    )
    # O Streamlit renderiza as páginas da pasta /pages automaticamente

    # Rodapé opcional
    if "current_planilha_path" in st.session_state:
        st.caption(f"Arquivo da planilha: `{st.session_state.current_planilha_path}`")
