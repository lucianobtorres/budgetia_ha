# src/config.py
import os

from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. Configurações de Caminhos (Paths) ---
# Define o diretório raiz do projeto de forma robusta
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Nomes dos arquivos centralizados aqui
PLANILHA_FILENAME = "planilha_mestra.xlsx"
DADOS_EXEMPLO_FILENAME = "dados_exemplo.json"

# Caminhos completos para serem usados em toda a aplicação
PLANILHA_PATH = os.path.join(DATA_DIR, PLANILHA_FILENAME)
DADOS_EXEMPLO_PATH = os.path.join(DATA_DIR, DADOS_EXEMPLO_FILENAME)


# --- 2. Configurações de Modelos de IA ---
# O os.getenv busca a variável de ambiente, se não encontrar, usa o valor padrão.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Adicione outros modelos padrão aqui se necessário
DEFAULT_GEMINI_MODEL2 = "gemini-1.5-flash"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT_PATH = "system_prompt.txt"
# --- 3. Constantes da Aplicação (Nossas "Strings Centralizadas") ---


class NomesAbas:
    """Define os nomes exatos das abas da planilha como constantes."""

    TRANSACOES = "Visão Geral e Transações"
    ORCAMENTOS = "Meus Orçamentos"
    DIVIDAS = "Minhas Dívidas"
    METAS = "Metas Financeiras"
    CONSULTORIA_IA = "Consultoria da IA"
    PERFIL_FINANCEIRO = "Perfil Financeiro"


class NomesPaginas:
    """Define os nomes exatos das páginas da interface como constantes."""

    VISAO_GERAL = "Visão Geral"
    CHAT_IA = "Chat com a IA"
    PLANILHA_MESTRA = "Planilha Mestra"
    MEUS_ORCAMENTOS = "Meus Orçamentos"


# --- 4. Layout da Planilha ---
# MUDANÇA: Agora o layout usa as constantes que acabamos de criar!
LAYOUT_PLANILHA = {
    NomesAbas.TRANSACOES: [
        "ID Transacao",
        "Data",
        "Tipo (Receita/Despesa)",
        "Categoria",
        "Descricao",
        "Valor",
        "Status",
    ],
    NomesAbas.ORCAMENTOS: [
        "ID Orcamento",
        "Categoria",
        "Valor Limite Mensal",
        "Valor Gasto Atual",
        "Porcentagem Gasta (%)",
        "Status Orçamento",
        "Período Orçamento",
        "Observações",
        "Última Atualização Orçamento",
    ],
    NomesAbas.DIVIDAS: [
        "ID Divida",
        "Nome da Dívida",
        "Valor Original",
        "Saldo Devedor Atual",
        "Taxa Juros Mensal (%)",
        "Parcelas Totais",
        "Parcelas Pagas",
        "Valor Parcela",
        "Data Próximo Pgto",
        "Observações",
    ],
    NomesAbas.METAS: [
        "ID Meta",
        "Nome da Meta",
        "Valor Alvo",
        "Valor Atual",
        "Data Limite",
        "Progresso (%)",
        "Observações",
    ],
    NomesAbas.CONSULTORIA_IA: [
        "Data do Insight",
        "Tipo de Insight",
        "Título do Insight",
        "Detalhes/Recomendação da IA",
        "Status (Novo/Lido/Concluído)",
    ],
    NomesAbas.PERFIL_FINANCEIRO: [
        "Campo",
        "Valor",
        "Observações",
    ],
}

# --- 5. Tipos de Dados (d-types) para as Colunas ---
LAYOUT_DTYPES = {
    NomesAbas.TRANSACOES: {
        "ID Transacao": "Int64",  # Usamos "Int64" (com 'I' maiúsculo) para permitir valores nulos
        "Data": "str",
        "Tipo (Receita/Despesa)": "str",
        "Categoria": "str",
        "Descricao": "str",
        "Valor": "float64",
        "Status": "str",
    },
    NomesAbas.ORCAMENTOS: {
        "ID Orcamento": "Int64",
        "Categoria": "str",
        "Valor Limite Mensal": "float64",
        "Valor Gasto Atual": "float64",
        "Porcentagem Gasta (%)": "float64",
        "Status Orçamento": "str",
        "Período Orçamento": "str",
        "Observações": "str",
        "Última Atualização Orçamento": "str",
    },
    # Adicione os dtypes para as outras abas (Dívidas, Metas, etc.) aqui
}
