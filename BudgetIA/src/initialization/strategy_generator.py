import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

import config

TEMPLATE_STRATEGY_PATH = Path("src/finance/strategies")
GENERATED_CLASS_NAME = "CustomStrategy"
BASE_CLASS_NAME = "BaseMappingStrategy"

try:
    with open(
        os.path.join(config.PROMPTS_DIR, "strategy_system_prompt.txt"), encoding="utf-8"
    ) as f:
        SYSTEM_PROMPT_TEMPLATE = f.read()
    with open(
        os.path.join(config.PROMPTS_DIR, "strategy_human_prompt.txt"), encoding="utf-8"
    ) as f:
        HUMAN_PROMPT_TEMPLATE = f.read()
    with open(
        os.path.join(config.PROMPTS_DIR, "strategy_retry_prompt.txt"), encoding="utf-8"
    ) as f:
        RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    print(
        "ERRO CRÍTICO: Arquivos de prompt de estratégia não encontrados na pasta 'src/prompts/'."
    )
    raise


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
            with pd.ExcelFile(file_path) as xls:
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
            base_strategy_path = TEMPLATE_STRATEGY_PATH / "base_strategy.py"
            padrao_strategy_path = TEMPLATE_STRATEGY_PATH / "default_strategy.py"

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
        """Cria o prompt de sistema lendo o template."""
        layout_str = json.dumps(config.LAYOUT_PLANILHA, indent=2)
        return SYSTEM_PROMPT_TEMPLATE.format(layout_sistema=layout_str)

    def _sandbox_test_strategy(
        self, strategy_file_path: Path, file_path_usuario: str, layout_config: dict
    ) -> tuple[bool, str]:
        """
        Tenta carregar e executar o `temp_strategy_module.py` em um sandbox.
        Retorna (Sucesso, MensagemDeErro)
        """
        print(f"--- DEBUG SANDBOX: Testando estratégia em {strategy_file_path}...")
        falhou = False

        # O 'strategy_file_path' é o caminho completo (ex: data/users/jsmith/user_strategy.py)
        module_name = strategy_file_path.stem  # (ex: "user_strategy")

        try:
            codigo_gerado = strategy_file_path.read_text(encoding="utf-8")

            # --- Verificação de imports/funções proibidas ---
            imports_proibidos = [
                r"\bimport\s+os\b",
                r"\bimport\s+sys\b",
                r"\bimport\s+subprocess\b",
                r"\bimport\s+shutil\b",
                r"__import__\s*\(",
                r"\beval\s*\(",
                r"\bexec\s*\(",
            ]

            for proibido in imports_proibidos:
                if re.search(proibido, codigo_gerado):
                    erro = f"Import/Função perigosa detectada: '{proibido}'"
                    print(f"--- DEBUG SANDBOX: FALHA! {erro} ---")
                    falhou = True  # Garante a limpeza do arquivo
                    return False, erro

            # --- Lógica de importlib (para carregar de qualquer lugar) ---
            spec = importlib.util.spec_from_file_location(
                module_name, strategy_file_path
            )
            if spec is None:
                raise ImportError(
                    f"Não foi possível criar spec para {strategy_file_path}"
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            strategy_class = getattr(module, GENERATED_CLASS_NAME)

            # --- CORREÇÃO DO SANDBOX ---
            # 1. Instancia a estratégia (como o PlanilhaManager faria)
            strategy_instance = strategy_class(
                layout_config, None
            )  # Passa None para mapeamento

            # 2. Lê os dados brutos (como o ExcelHandler faria)
            try:
                # Usar 'with' garante que o 'xls' será fechado
                with pd.ExcelFile(file_path_usuario) as xls:
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
            # Limpa o módulo do cache
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Se falhou, apaga o .py quebrado (CICLO DE VIDA)
            if falhou and strategy_file_path.exists():
                try:
                    os.remove(strategy_file_path)
                except Exception:
                    pass

    def validate_existing_strategy(
        self, strategy_file_path: Path, file_path_usuario: str
    ) -> tuple[bool, str]:
        """
        Interface pública para testar uma estratégia .py existente.
        """
        if not strategy_file_path.exists():
            return False, "Arquivo de estratégia não encontrado."

        print(
            f"--- DEBUG GENERATOR: Validando estratégia existente em {strategy_file_path}... ---"
        )
        layout_config = config.LAYOUT_PLANILHA

        # Reutiliza o seu sandbox!
        return self._sandbox_test_strategy(
            strategy_file_path, file_path_usuario, layout_config
        )

    def generate_and_validate_strategy(
        self, file_path_usuario: str, strategy_save_path: Path
    ) -> tuple[bool, str]:
        """
        Orquestra o processo de geração e validação da estratégia.
        Salva o .py final no 'strategy_save_path' fornecido.
        """
        try:
            schema_usuario = self._get_planilha_schema(file_path_usuario)
            base_templates = self._get_base_templates()
            layout_config = config.LAYOUT_PLANILHA  # Passado para o sandbox
            system_prompt = self._get_system_prompt()

            erro_log = ""
            for i in range(self.max_retries):
                print(f"--- DEBUG GENERATOR: Tentativa {i + 1}/{self.max_retries} ---")

                if erro_log:
                    prompt_com_erro = RETRY_PROMPT_TEMPLATE.format(
                        erro_log=erro_log, schema_usuario=schema_usuario
                    )
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=prompt_com_erro),
                    ]
                else:
                    human_prompt = HUMAN_PROMPT_TEMPLATE.format(
                        base_templates=base_templates, schema_usuario=schema_usuario
                    )
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
                    with open(strategy_save_path, "w", encoding="utf-8") as f:
                        f.write(codigo_gerado)
                except Exception as e:
                    erro_log = f"Falha ao salvar arquivo temporário: {e}"
                    continue

                success, result = self._sandbox_test_strategy(
                    strategy_save_path,  # Testa o arquivo final
                    file_path_usuario,
                    layout_config,
                )
                if success:
                    module_name = strategy_save_path.stem
                    print(
                        f"--- DEBUG GENERATOR: Estratégia validada e salva como '{module_name}' ---"
                    )
                    mapa_para_salvar = {"strategy_module": module_name}
                    return True, json.dumps(mapa_para_salvar)
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
