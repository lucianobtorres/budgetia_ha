import os
import sys

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

try:
    print("Tentando importar OnboardingOrchestrator...")

    print("Importação SUCESSO!")
except Exception as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    import traceback

    traceback.print_exc()
