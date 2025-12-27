import os
import sys
from pathlib import Path

import uvicorn

# Configuração de caminhos (igual ao start.py)
# Configuração de caminhos (igual ao start.py)
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


import threading
import time
import webbrowser


def open_browser():
    """Abre o navegador após aguardar o servidor iniciar."""
    print("--- Aguardando servidor iniciar... ---")
    time.sleep(2)  # Dá um tempinho para o Uvicorn subir
    url = "http://127.0.0.1:8000/docs"
    print(f"--- Abrindo documentação da API em: {url} ---")
    webbrowser.open(url)


def main() -> None:
    """Função principal para iniciar a API."""
    if os.name == "nt":
        # Forçar UTF-8 no Windows
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    print("--- INICIANDO API BUDGETIA ---")
    print("--- Roteando para: src.api.main:app ---")

    # Inicia a thread que abrirá o navegador
    threading.Thread(target=open_browser, daemon=True).start()

    # Executa o Uvicorn
    # A string de import deve ser relativa ao PYTHONPATH (que incluímos 'src')
    # Então 'api.main:app' funciona porque 'src' está no path.
    # Alternativamente, podemos passar o app object importado,
    # mas passar string habilita o 'reload' funcionar melhor.
    uvicorn.run(
        "interfaces.api.main:app", 
        host="0.0.0.0", # Allow external access if needed (for mobile/PWA testing)
        port=8000, 
        reload=True, 
        reload_dirs=["src"],
        reload_excludes=["data", "data/*", "*.pyc", "__pycache__", "*temp_user_strategy.py"],
        log_level="info"
    )


if __name__ == "__main__":
    main()
