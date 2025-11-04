# Visão Geral do Projeto

**BudgetIA** é um assistente de finanças pessoais que combina uma interface web interativa (Streamlit) com o poder de modelos de linguagem grandes (LLMs) para ajudar os usuários a gerenciar suas finanças através de uma planilha do Excel.

O sistema permite que o usuário converse com uma IA para adicionar transações, fazer perguntas sobre seus gastos, definir orçamentos e obter insights financeiros. A aplicação é projetada para ser resiliente, com um sistema de fallback que alterna entre diferentes provedores de LLM (Groq, OpenAI, Google Gemini) caso um deles falhe.

## Como Executar

O projeto possui duas interfaces principais:

1.  **Aplicação Web (Recomendado):**
    *   Inicia uma interface gráfica no navegador.
    *   Comando para executar: `poetry run streamlit run src/app.py`

2.  **Interface de Linha de Comando (CLI):**
    *   Permite interagir com a IA diretamente no terminal.
    *   Comando para executar: `poetry run python src/main.py`

## Estrutura do Projeto e Arquivos

*   `src/app.py`:
    *   **Propósito**: Ponto de entrada da aplicação web com Streamlit.
    *   **Funcionalidades**:
        *   Cria a interface do usuário com abas para "Visão Geral", "Chat com a IA", "Planilha Mestra" e "Meus Orçamentos".
        *   Gerencia o estado da sessão de chat.
        *   Inicializa e coordena os outros módulos (`PlanilhaManager`, `IADeFinancas`, `LLMOrchestrator`).
        *   Apresenta um dashboard com métricas e gráficos financeiros.
        *   Permite a edição direta das transações e orçamentos na interface.

*   `src/ia_financeira.py`:
    *   **Propósito**: Orquestra a lógica da inteligência artificial.
    *   **Funcionalidades**:
        *   Define o `System Prompt` que instrui o LLM sobre como se comportar como um assistente financeiro.
        *   Cria e gerencia o `AgentExecutor` do LangChain, que combina o LLM com as ferramentas disponíveis.
        *   Processa a entrada do usuário, gerencia o histórico do chat e invoca o agente para obter uma resposta.

*   `src/llm_manager.py`:
    *   **Propósito**: Gerencia a seleção e configuração dos modelos de linguagem (LLMs).
    *   **Funcionalidades**:
        *   Define uma arquitetura com um provedor primário e provedores de *fallback*.
        *   Implementa classes para diferentes provedores de LLM (Google Gemini, Groq, OpenAI).
        *   Tenta carregar o LLM primário e, em caso de falha (ex: chave de API ausente), tenta os provedores de *fallback* em sequência.

*   `src/planilha_manager.py`:
    *   **Propósito**: Respons��vel por toda a interação com o arquivo Excel (`planilha_mestra.xlsx`).
    *   **Funcionalidades**:
        *   Cria, lê e atualiza a planilha com múltiplas abas ("Visão Geral e Transações", "Meus Orçamentos", etc.).
        *   Adiciona e gerencia registros de transações e orçamentos.
        *   Calcula automaticamente os gastos atuais com base nas transações e atualiza o status dos orçamentos.

*   `src/planilha_tools.py`:
    *   **Propósito**: Define as "ferramentas" que o agente de IA (LangChain) pode usar para interagir com a planilha.
    *   **Funcionalidades**:
        *   Expõe funções como `adicionar_transacao`, `visualizar_dados_planilha`, `calcular_saldo_total`, `definir_orcamento`, etc., como ferramentas estruturadas para o LangChain.
        *   Cada ferramenta possui uma descrição clara e um esquema de entrada (Pydantic) para que o LLM saiba como e quando usá-la.

*   `src/main.py`:
    *   **Propósito**: Ponto de entrada para a versão de linha de comando (CLI) da aplicação.
    *   **Funcionalidades**:
        *   Inicializa os componentes principais e entra em um loop de chat no terminal.
