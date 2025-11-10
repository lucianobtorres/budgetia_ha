import os
import subprocess
import sys

print("--- START.PY: Forçando Encoding UTF-8 ---")
os.environ["PYTHONUTF8"] = "1"


def main() -> None:
    # Caminho para seu app Streamlit
    app_path = os.path.join("src", "web_app", "💰_BudgetIA.py")

    try:
        # Executa o streamlit via subprocesso
        process = subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
        process.wait()
    except KeyboardInterrupt:
        print("Encerrando o servidor Streamlit...")
        process.terminate()
        process.wait()


if __name__ == "__main__":
    main()
