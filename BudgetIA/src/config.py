# src/config.py
import json
import os

from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- 1. Configurações de Caminhos (Paths) ---
# Define o diretório raiz do projeto de forma robusta
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

DEFAULT_CRED_FILENAME = "gen-lang-client-0988185244-c9e312f68267.json"
GSPREAD_CREDENTIALS_PATH = os.getenv("GSPREAD_CREDENTIALS_PATH")

# --- NOVAS CHAVES PARA O LOGIN DE USUÁRIO (OAUTH 2.0) ---
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

# O URI de redirecionamento que você configurou no Google Console
GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8501"

# --- CONFIGURAÇÃO DE SEGURANÇA (JWT) ---
# Usar um segredo forte em produção!
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_dev_key_change_in_prod_12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Dias para dev (PWA persistência)

# Os "escopos" (permissões) que pediremos ao usuário.
# Precisamos de acesso total ao Drive para listar, compartilhar e ler.
GOOGLE_OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive"]

PROMPTS_DIR = os.path.join(PROJECT_ROOT, "src", "core", "prompts")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PROMPTS_DIR, exist_ok=True)
except Exception as e:
    print(f"AVISO CONFIG: Erro ao criar diretórios: {e}")

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
class LLMModels:
    """Centraliza as definições dos modelos de LLM suportados."""
    
    # GROQ Options
    GROQ_LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    GROQ_LLAMA_3_1_8B = "llama-3.1-8b-instant"
    GROQ_GPT_OSS_120B = "openai/gpt-oss-120b"
    
    # GEMINI Options
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    
    # OPENAI Options
    OPENAI_GPT_3_5_TURBO = "gpt-3.5-turbo"
    # OPENAI_GPT_4 = "gpt-4" # Exemplo futuro

    # Defaults do Sistema
    DEFAULT_GROQ = GROQ_GPT_OSS_120B
    DEFAULT_GEMINI = GEMINI_2_0_FLASH_LITE 
    # DEFAULT_GEMINI = GEMINI_2_5_FLASH # Alternativa
    
# Mantendo compatibilidade com código antigo que importava essas variáveis, 
# mas agora apontando para a classe central.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", LLMModels.DEFAULT_GROQ)
DEFAULT_GEMINI_MODEL = LLMModels.DEFAULT_GEMINI

SERVICE_ACCOUNT_EMAIL = None
try:
    if GSPREAD_CREDENTIALS_PATH is not None:
        with open(GSPREAD_CREDENTIALS_PATH) as f:
            creds_json = json.load(f)
            SERVICE_ACCOUNT_EMAIL = creds_json.get("client_email")
            if not SERVICE_ACCOUNT_EMAIL:
                print(
                    f"AVISO CRÍTICO: 'client_email' não encontrado em {GSPREAD_CREDENTIALS_PATH}"
                )
except FileNotFoundError:
    print(
        f"AVISO CRÍTICO: Arquivo de credenciais GSpread não encontrado em {GSPREAD_CREDENTIALS_PATH}"
    )
except Exception as e:
    print(f"AVISO CRÍTICO: Falha ao ler 'client_email' do JSON de credenciais: {e}")

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")

# Você pode adicionar uma verificação se quiser
if not UPSTASH_REDIS_URL:
    print("Aviso: UPSTASH_REDIS_URL não encontrada. O cache não funcionará.")

# PRESENÇA / SMART ROUTING
# Tempo sem heartbeat para considerar offline (Default: 300s = 5 min)
# Reduzido para 30s para testes a pedido do usuário
PRESENCE_OFFLINE_THRESHOLD_SECONDS = 30


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
    LIMITE = "Valor Limite"
    GASTO = "Valor Gasto Atual"
    PERCENTUAL = "Porcentagem Gasta (%)"
    PERIODO = "Período Orçamento"
    STATUS = "Status Orçamento"
    OBS = "Observações"
    ATUALIZACAO = "Última Atualização Orçamento"


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
    DATA_INICIO = "Data Início"
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


# --- CONSTANTES DE PERFIL ---
PROFILE_ESSENTIAL_FIELDS = ["Renda Mensal Média", "Principal Objetivo"]
PROFILE_DESIRED_FIELDS = PROFILE_ESSENTIAL_FIELDS + ["Tolerância a Risco"]


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
        ColunasDividas.DATA_INICIO,
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
    ColunasDividas.DATA_INICIO: "datetime64[ns]",
    # Metas
    ColunasMetas.ID: "Int64",
    ColunasMetas.VALOR_ALVO: "float64",
    ColunasMetas.VALOR_ATUAL: "float64",
    ColunasMetas.DATA_ALVO: "datetime64[ns]",
    # Insights
    ColunasInsights.ID: "Int64",
    ColunasInsights.DATA: "datetime64[ns]",
}

SERVICE_ACCOUNT_CREDENTIALS_PATH = os.path.join(
    PROJECT_ROOT, "data", "gen-lang-client-0988185244-c9e312f68267.json"
)
