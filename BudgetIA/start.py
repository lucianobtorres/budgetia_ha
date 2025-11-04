import os
import subprocess
import sys


def main() -> None:
    # Caminho para seu app Streamlit
    app_path = os.path.join("src", "web_app", "app.py")

    # Executa o streamlit via subprocesso
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])


if __name__ == "__main__":
    main()
