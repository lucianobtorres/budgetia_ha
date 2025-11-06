import importlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

import config

# (Removido import da base para evitar confusão)

# Define um local seguro para as estratégias geradas
STRATEGY_PATH = Path("src/finance/strategies")
# Define um nome de arquivo temporário para o sandbox
TEMP_STRATEGY_MODULE = "temp_strategy_module"
TEMP_STRATEGY_FILE = STRATEGY_PATH / f"{TEMP_STRATEGY_MODULE}.py"
# Nome padrão da classe que a IA deve gerar
GENERATED_CLASS_NAME = "CustomStrategy"
# Nome da classe base que a IA deve importar
BASE_CLASS_NAME = "BaseMappingStrategy"


class StrategyGenerator:
    """
    Usa um LLM para analisar uma planilha desconhecida e gerar
    dinamicamente um módulo de estratégia em Python para lê-la e escrevê-la.
    """

    def __init__(self, llm_orchestrator: Any, max_retries: int = 3):
        self.llm = llm_orchestrator.get_configured_llm(temperature=0.0)
        self.max_retries = max_retries

    def _get_planilha_schema(self, file_path: str) -> str:
        """Lê os metadados de uma planilha Excel para a IA analisar."""
        try:
            xls = pd.ExcelFile(file_path)
            abas = xls.sheet_names
            schema_str = "Esquema da Planilha do Usuário:\n"
            abas_para_analisar = abas[:5]

            for aba in abas_para_analisar:
                try:
                    df = pd.read_excel(xls, sheet_name=aba, nrows=5)
                    schema_str += f"\n--- Aba: '{aba}' ---\n"
                    schema_str += f"Colunas: {df.columns.to_list()}\n"
                    schema_str += "Exemplos de Dados (primeiras 5 linhas):\n"
                    schema_str += df.to_string(index=False) + "\n"
                except Exception as e:
                    schema_str += (
                        f"\n--- Aba: '{aba}' (Não foi possível ler: {e}) ---\n"
                    )

            if len(abas) > 5:
                schema_str += f"\n... (e mais {len(abas) - 5} abas)"

            return schema_str
        except Exception as e:
            print(f"Erro ao ler schema da planilha: {e}")
            raise OSError(f"Não foi possível ler os metadados do arquivo: {e}")

    def _get_base_templates(self) -> str:
        """Carrega os arquivos de estratégia base como texto para dar de exemplo ao LLM."""
        try:
            base_strategy_path = STRATEGY_PATH / "base_strategy.py"
            padrao_strategy_path = STRATEGY_PATH / "default_strategy.py"

            with open(base_strategy_path, encoding="utf-8") as f:
                base_code = f.read()
            with open(padrao_strategy_path, encoding="utf-8") as f:
                padrao_code = f.read()

            return (
                f"Você DEVE implementar esta interface (de base_strategy.py):\n"
                f"--- INÍCIO: Interface Base ({BASE_CLASS_NAME}) ---\n"
                f"{base_code}\n"
                f"--- FIM: Interface Base ---\n\n"
                f"Use este código (de default_strategy.py) como exemplo de implementação:\n"
                f"--- INÍCIO: Exemplo (DefaultStrategy) ---\n"
                f"{padrao_code}\n"
                f"--- FIM: Exemplo ---\n"
            )
        except FileNotFoundError as e:
            print(f"ERRO: Não encontrou os arquivos de template de estratégia: {e}")
            raise e

    def _get_system_prompt(self) -> str:
        """Cria o prompt de sistema focado em GERAÇÃO DE CÓDIGO."""
        layout_str = json.dumps(config.LAYOUT_PLANILHA, indent=2)

        return (
            "Você é um engenheiro de software Python sênior, especialista em Pandas e ETL.\n"
            "Sua única tarefa é escrever um arquivo de estratégia em Python para traduzir"
            "a planilha de um usuário (com formato desconhecido) para um formato de sistema interno.\n"
            "\n"
            "O FORMATO INTERNO (Seu objetivo) é este dicionário de DataFrames:\n"
            f"{layout_str}\n"
            "\n"
            "REGRAS CRÍTICAS PARA O CÓDIGO GERADO:\n"
            "1. IMPORTS: Use APENAS imports relativos para módulos locais."
            f"   - CORRETO: `from .base_strategy import {BASE_CLASS_NAME}`\n"
            "   - ERRADO: `from src.finance.strategies...` ou `from src.strategies...`\n"
            "   - IMPORTE `config` diretamente: `import config`\n"
            f"2. CLASSE: O nome da classe DEVE ser `{GENERATED_CLASS_NAME}`.\n"
            f"3. HERANÇA: A classe DEVE herdar de `{BASE_CLASS_NAME}`.\n"
            "4. __INIT__: O `__init__` DEVE seguir a assinatura da classe base. Você pode definir `self.mapeamento` dentro dele, se precisar (ex: para `get_sheet_name_to_save`).\n"
            "5. MÉTODOS: Implemente `map_transactions` e `unmap_transactions`."
            "\n"
            "Responda APENAS com o código Python completo. Não inclua markdown (```python) ou qualquer outra explicação."
        )

    def _sandbox_test_strategy(
        self, file_path_usuario: str, layout_config: dict
    ) -> tuple[bool, str]:
        """
        Tenta carregar e executar o `temp_strategy_module.py` em um sandbox.
        Retorna (Sucesso, MensagemDeErro)
        """
        print(f"--- DEBUG SANDBOX: Testando estratégia em {TEMP_STRATEGY_FILE}...")
        falhou = False
        try:
            if str(STRATEGY_PATH.resolve()) not in sys.path:
                sys.path.insert(0, str(STRATEGY_PATH.resolve()))

            module_to_load = f"finance.strategies.{TEMP_STRATEGY_MODULE}"

            if module_to_load in sys.modules:
                module = importlib.reload(sys.modules[module_to_load])
            else:
                module = importlib.import_module(module_to_load)

            strategy_class = getattr(module, GENERATED_CLASS_NAME)

            # --- CORREÇÃO DO SANDBOX ---
            # 1. Instancia a estratégia (como o PlanilhaManager faria)
            strategy_instance = strategy_class(
                layout_config, None
            )  # Passa None para mapeamento

            # 2. Lê os dados brutos (como o ExcelHandler faria)
            try:
                xls = pd.ExcelFile(file_path_usuario)
                # Tenta adivinhar a aba de transações (ou usa a primeira)
                aba_transacoes_bruta = xls.sheet_names[0]
                if config.NomesAbas.TRANSACOES in xls.sheet_names:
                    aba_transacoes_bruta = config.NomesAbas.TRANSACOES
                df_bruto = pd.read_excel(xls, sheet_name=aba_transacoes_bruta)
            except Exception as e:
                raise OSError(f"Sandbox falhou ao ler o arquivo Excel: {e}")

            print("--- DEBUG SANDBOX: Executando .map_transactions()... ---")
            # 3. Testa o map_transactions
            df_mapeado = strategy_instance.map_transactions(df_bruto)

            print("--- DEBUG SANDBOX: Validando schema... ---")
            colunas_requeridas = layout_config[config.NomesAbas.TRANSACOES]
            for col in colunas_requeridas:
                if col not in df_mapeado.columns:
                    raise ValueError(
                        f"Estratégia falhou em traduzir. Coluna interna '{col}' está faltando."
                    )

            if not df_mapeado.empty and not pd.api.types.is_numeric_dtype(
                df_mapeado["Valor"]
            ):
                raise TypeError(
                    "Estratégia falhou. A coluna 'Valor' traduzida não é numérica."
                )

            print("--- DEBUG SANDBOX: Sucesso! ---")
            return True, "Validado com sucesso"

        except Exception as e:
            print(f"--- DEBUG SANDBOX: FALHA! Erro: {e} ---")
            falhou = True
            return False, str(e)
        finally:
            if module_to_load in sys.modules:
                del sys.modules[module_to_load]
            if os.path.exists(TEMP_STRATEGY_FILE):
                try:
                    if falhou:
                        os.remove(TEMP_STRATEGY_FILE)
                except Exception:
                    pass

    def generate_and_validate_strategy(
        self, file_path_usuario: str
    ) -> tuple[bool, str]:
        """
        Orquestra o processo de geração e validação da estratégia.
        Retorna (Sucesso, NomeDoModuloJson) ou (Falha, MensagemDeErro)
        """
        try:
            schema_usuario = self._get_planilha_schema(file_path_usuario)
            base_templates = self._get_base_templates()
            layout_config = config.LAYOUT_PLANILHA  # Passado para o sandbox
            system_prompt = self._get_system_prompt()

            human_prompt = (
                f"{base_templates}\n\n"
                f"Aqui está o schema da planilha do usuário:\n{schema_usuario}\n\n"
                f"Gere o código Python completo para a classe `{GENERATED_CLASS_NAME}` "
                "conforme as instruções no prompt de sistema. "
                "Lembre-se das regras de import relativo e do __init__!"
            )

            erro_log = ""
            for i in range(self.max_retries):
                print(f"--- DEBUG GENERATOR: Tentativa {i + 1}/{self.max_retries} ---")

                if erro_log:
                    prompt_com_erro = (
                        f"A tentativa anterior falhou. Erro: {erro_log}\n"
                        "Analise o erro e o schema do usuário e gere um novo código Python corrigido.\n"
                        f"Schema do Usuário:\n{schema_usuario}\n"
                        "Lembre-se das REGRAS CRÍTICAS (imports relativos, nome da classe, __init__)!"
                        "Gere apenas o código."
                    )
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=prompt_com_erro),
                    ]
                else:
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=human_prompt),
                    ]

                print(
                    f"--- DEBUG GENERATOR [PROMPT (Tentativa {i + 1})]:\n{messages[1].content[:500]}...\n"
                )

                resposta_ia = self.llm.invoke(messages).content
                codigo_gerado = (
                    str(resposta_ia)
                    .strip()
                    .replace("```python", "")
                    .replace("```", "")
                    .strip()
                )
                print(
                    f"--- DEBUG GENERATOR [RESPOSTA IA (Código)]:\n{codigo_gerado[:500]}...\n"
                )

                try:
                    with open(TEMP_STRATEGY_FILE, "w", encoding="utf-8") as f:
                        f.write(codigo_gerado)
                except Exception as e:
                    erro_log = f"Falha ao salvar arquivo temporário: {e}"
                    continue

                success, result = self._sandbox_test_strategy(
                    file_path_usuario, layout_config
                )

                if success:
                    novo_nome_modulo = f"strategy_user_{int(time.time())}"
                    novo_arquivo = STRATEGY_PATH / f"{novo_nome_modulo}.py"
                    shutil.move(TEMP_STRATEGY_FILE, novo_arquivo)

                    print(
                        f"--- DEBUG GENERATOR: Estratégia validada e salva como '{novo_nome_modulo}' ---"
                    )

                    # A IA deve ter definido o mapeamento internamente
                    # Vamos apenas salvar o nome do módulo.
                    mapa_para_salvar = {"strategy_module": novo_nome_modulo}

                    return True, json.dumps(mapa_para_salvar)  # Retorna o JSON
                else:
                    erro_log = str(result)

            return (
                False,
                f"IA falhou em gerar uma estratégia válida após {self.max_retries} tentativas. Último erro: {erro_log}",
            )

        except Exception as e:
            print(f"--- DEBUG GENERATOR [ERRO FATAL]: {e} ---")
            import traceback

            traceback.print_exc()
            return False, f"Erro crítico no StrategyGenerator: {e}"
