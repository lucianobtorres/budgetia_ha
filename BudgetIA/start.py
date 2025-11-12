# start.py
# --- INÍCIO DAS CORREÇÕES ---
import os
import subprocess
import sys
from pathlib import Path

# 1. Encontre o caminho para a pasta 'src'
# Este script (start.py) está na raiz. 'src' está no mesmo nível.
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

# 2. Adicione 'src' ao sys.path
# Isso garante que 'import app' ou 'import finance' funcione
# em qualquer lugar, resolvendo o 'ModuleNotFoundError'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
    print(f"--- START.PY: Adicionado '{SRC_DIR}' ao sys.path ---")
# --- FIM DAS CORREÇÕES ---


def main() -> None:
    # (Seu código original de UTF-8)
    if os.name == "nt":
        print("--- START.PY: Forçando Encoding UTF-8 ---")
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

    app_path = str(SRC_DIR / "web_app" / "💰_BudgetIA.py")

    # --- CORREÇÃO DO UNBOUNDLOCALERROR ---
    process = None  # 3. Inicializa process como None
    # --- FIM DA CORREÇÃO ---

    try:
        # (Seu código original de subprocess.run)
        process = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", app_path], check=True
        )
    except KeyboardInterrupt:
        print("\nEncerrando o servidor Streamlit...")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o Streamlit: {e}")
    finally:
        # --- CORREÇÃO DO UNBOUNDLOCALERROR ---
        if process:  # 4. Só tenta terminar se 'process' existir
            process.terminate()
        # --- FIM DA CORREÇÃO ---


if __name__ == "__main__":
    main()
