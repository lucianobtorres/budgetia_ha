# src/config.py
import os

from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. Configurações de Caminhos (Paths) ---
# Define o diretório raiz do projeto de forma robusta
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "src", "prompts")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)

# Nomes dos arquivos centralizados aqui
PLANILHA_FILENAME = "planilha_mestra.xlsx"
DADOS_EXEMPLO_FILENAME = "dados_exemplo.json"
SYSTEM_PROMPT_FILENAME = "system_prompt.txt"
PLANILHA_KEY = "planilha_path"

# Caminhos completos para serem usados em toda a aplicação
PLANILHA_PATH = os.path.join(DATA_DIR, PLANILHA_FILENAME)
DADOS_EXEMPLO_PATH = os.path.join(DATA_DIR, DADOS_EXEMPLO_FILENAME)
SYSTEM_PROMPT_PATH = os.path.join(PROMPTS_DIR, SYSTEM_PROMPT_FILENAME)

# --- 2. Configurações de Modelos de IA ---
# O os.getenv busca a variável de ambiente, se não encontrar, usa o valor padrão.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Adicione outros modelos padrão aqui se necessário
DEFAULT_GEMINI_MODEL2 = "gemini-1.5-flash"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# --- 3. Constantes da Aplicação (Nossas "Strings Centralizadas") ---


class SummaryKeys:
    """Chaves usadas no dicionário de resumo financeiro."""

    RECEITAS = "total_receitas"
    DESPESAS = "total_despesas"
    SALDO = "saldo"


class ValoresTipo:
    """Valores usados na coluna 'Tipo (Receita/Despesa)'."""

    RECEITA = "Receita"
    DESPESA = "Despesa"


class ColunasTransacoes:
    """Nomes das colunas internas da aba 'Transações'."""

    ID = "ID Transacao"
    DATA = "Data"
    TIPO = "Tipo (Receita/Despesa)"
    CATEGORIA = "Categoria"
    DESCRICAO = "Descricao"
    VALOR = "Valor"
    STATUS = "Status"


class ColunasOrcamentos:
    """Nomes das colunas internas da aba 'Orçamentos'."""

    ID = "ID Orcamento"
    CATEGORIA = "Categoria"
    LIMITE = "Valor Limite Mensal"
    GASTO = "Valor Gasto Atual"
    PERCENTUAL = "Porcentagem Gasta (%)"
    PERIODO = "Período Orçamento"
    STATUS = "Status Orçamento"
    OBS = "Observações"


class ColunasDividas:
    """Nomes das colunas internas da aba 'Dívidas'."""

    ID = "ID Divida"
    NOME = "Nome da Dívida"
    VALOR_ORIGINAL = "Valor Original"
    SALDO_DEVEDOR = "Saldo Devedor Atual"
    TAXA_JUROS = "Taxa Juros Mensal (%)"
    PARCELAS_TOTAIS = "Parcelas Totais"
    PARCELAS_PAGAS = "Parcelas Pagas"
    VALOR_PARCELA = "Valor Parcela"
    DATA_PGTO = "Data Próximo Pgto"
    OBS = "Observações"


class ColunasPerfil:
    """Nomes das colunas internas da aba 'Perfil Financeiro'."""

    CAMPO = "Campo"
    VALOR = "Valor"
    OBS = "Observações"


class ColunasMetas:
    """Nomes das colunas internas da aba 'Metas Financeiras'."""

    ID = "ID Meta"
    NOME = "Nome da Meta"
    VALOR_ALVO = "Valor Alvo"
    VALOR_ATUAL = "Valor Atual"
    DATA_ALVO = "Data Alvo"
    STATUS = "Status"
    OBS = "Observações"


class ColunasInsights:
    """Nomes das colunas internas da aba 'Consultoria da IA'."""

    ID = "ID Insight"
    DATA = "Data do Insight"
    TIPO = "Tipo de Insight"
    TITULO = "Título do Insight"
    DETALHES = "Detalhes/Recomendação da IA"
    STATUS = "Status (Novo/Lido/Concluído)"


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
LAYOUT_PLANILHA: dict[str, list[str]] = {
    NomesAbas.TRANSACOES: [
        ColunasTransacoes.ID,
        ColunasTransacoes.DATA,
        ColunasTransacoes.TIPO,
        ColunasTransacoes.CATEGORIA,
        ColunasTransacoes.DESCRICAO,
        ColunasTransacoes.VALOR,
        ColunasTransacoes.STATUS,
    ],
    NomesAbas.ORCAMENTOS: [
        ColunasOrcamentos.ID,
        ColunasOrcamentos.CATEGORIA,
        ColunasOrcamentos.LIMITE,
        ColunasOrcamentos.GASTO,
        ColunasOrcamentos.PERCENTUAL,
        ColunasOrcamentos.PERIODO,
        ColunasOrcamentos.STATUS,
        ColunasOrcamentos.OBS,
    ],
    NomesAbas.DIVIDAS: [
        ColunasDividas.ID,
        ColunasDividas.NOME,
        ColunasDividas.VALOR_ORIGINAL,
        ColunasDividas.SALDO_DEVEDOR,
        ColunasDividas.TAXA_JUROS,
        ColunasDividas.PARCELAS_TOTAIS,
        ColunasDividas.PARCELAS_PAGAS,
        ColunasDividas.VALOR_PARCELA,
        ColunasDividas.DATA_PGTO,
        ColunasDividas.OBS,
    ],
    NomesAbas.METAS: [
        ColunasMetas.ID,
        ColunasMetas.NOME,
        ColunasMetas.VALOR_ALVO,
        ColunasMetas.VALOR_ATUAL,
        ColunasMetas.DATA_ALVO,
        ColunasMetas.STATUS,
        ColunasMetas.OBS,
    ],
    NomesAbas.CONSULTORIA_IA: [
        ColunasInsights.ID,
        ColunasInsights.DATA,
        ColunasInsights.TIPO,
        ColunasInsights.TITULO,
        ColunasInsights.DETALHES,
        ColunasInsights.STATUS,
    ],
    NomesAbas.PERFIL_FINANCEIRO: [
        ColunasPerfil.CAMPO,
        ColunasPerfil.VALOR,
        ColunasPerfil.OBS,
    ],
}

# --- 5. Tipos de Dados (d-types) para as Colunas ---
LAYOUT_DTYPES: dict[str, str] = {
    # Transações
    ColunasTransacoes.DATA: "datetime64[ns]",
    ColunasTransacoes.VALOR: "float64",
    ColunasTransacoes.ID: "Int64",  # Usa Int64 do pandas para aceitar nulos (NA)
    # Orçamentos
    ColunasOrcamentos.ID: "Int64",
    ColunasOrcamentos.LIMITE: "float64",
    ColunasOrcamentos.GASTO: "float64",
    ColunasOrcamentos.PERCENTUAL: "float64",
    # Dívidas
    ColunasDividas.ID: "Int64",
    ColunasDividas.VALOR_ORIGINAL: "float64",
    ColunasDividas.SALDO_DEVEDOR: "float64",
    ColunasDividas.TAXA_JUROS: "float64",
    ColunasDividas.PARCELAS_TOTAIS: "Int64",
    ColunasDividas.PARCELAS_PAGAS: "Int64",
    ColunasDividas.VALOR_PARCELA: "float64",
    ColunasDividas.DATA_PGTO: "datetime64[ns]",
    # Metas
    ColunasMetas.ID: "Int64",
    ColunasMetas.VALOR_ALVO: "float64",
    ColunasMetas.VALOR_ATUAL: "float64",
    ColunasMetas.DATA_ALVO: "datetime64[ns]",
    # Insights
    ColunasInsights.ID: "Int64",
    ColunasInsights.DATA: "datetime64[ns]",
}
