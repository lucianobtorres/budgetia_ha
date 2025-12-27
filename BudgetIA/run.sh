#!/bin/bash
set -e

echo "🟢 Iniciando BudgetIA Add-on (Monorepo Mode)..."

# 1. Carregar Opções do Home Assistant
OPTIONS_PATH="/data/options.json"
if [ -f "$OPTIONS_PATH" ]; then
    echo "⚙️  Carregando opções..."
    export LOG_LEVEL=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('log_level', 'info'))")
    export OPENAI_API_KEY=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('openai_api_key', ''))")
    export GROQ_API_KEY=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('groq_api_key', ''))")
    export GEMINI_API_KEY=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('gemini_api_key', ''))")
    export GOOGLE_OAUTH_CLIENT_ID=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('google_oauth_client_id', ''))")
    export GOOGLE_OAUTH_CLIENT_SECRET=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('google_oauth_client_secret', ''))")
    export GOOGLE_OAUTH_REDIRECT_URI=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('google_oauth_redirect_uri', ''))")
    export SECRET_KEY=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('secret_key', ''))")
    export UPSTASH_REDIS_URL=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('upstash_redis_url', ''))")
    export PLANILHA_PATH=$(python3 -c "import json; print(json.load(open('$OPTIONS_PATH')).get('planilha_path', ''))")
    
    # Derivar chave de criptografia Fernet (32 bytes base64) a partir da SECRET_KEY para persistência de dados do usuário
    export USER_DATA_ENCRYPTION_KEY=$(python3 -c "import base64, hashlib, os; secret = os.environ.get('SECRET_KEY', 'default-fallback-secret'); print(base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest()).decode())")
else
    echo "⚠️  options.json não encontrado. Usando variáveis de ambiente."
fi

# 2. Configurar Persistência
if [ ! -d "/data/budgetia_files" ]; then
    echo "📁 Criando diretório de dados persistentes..."
    mkdir -p /data/budgetia_files
fi

# Copiar planilha inicial se não existir na persistência
if [ ! -f "/data/budgetia_files/planilha_mestra.xlsx" ]; then
    if [ -f "/app/planilha_mestra.xlsx" ]; then
        echo "📄 Inicializando planilha mestra..."
        cp /app/planilha_mestra.xlsx /data/budgetia_files/
    fi
fi

# Linkar persistência
ln -sf /data/budgetia_files/planilha_mestra.xlsx /app/planilha_mestra.xlsx

# 3. Iniciar Servidor
echo "🚀 Iniciando Servidor API + Frontend..."
export PYTHONPATH=$PYTHONPATH:/app/src
export STATIC_DIR="/app/static"

exec python3 -m uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000 --log-level ${LOG_LEVEL:-info}
