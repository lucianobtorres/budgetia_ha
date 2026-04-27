# src/core/intelligence/fact_checker.py
import re

from core.logger import get_logger

logger = get_logger("FactChecker")

class FactChecker:
    """
    Auditor de veracidade para respostas de IA.
    Compara o output final com as observações das ferramentas (Intermediate Steps).
    """

    @staticmethod
    def verify_financial_data(output: str, observations: str) -> dict:
        """
        Verifica se os valores financeiros citados no output existem nas observações.
        Retorna um dicionário com o status e detalhes.
        """
        # Regex para capturar valores monetários comuns em PT-BR
        # Pega "R$ 1.234,56", "1234,56", etc.
        pattern = r"R\$\s?[\d.,]+|[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})"
        found_in_output = re.findall(pattern, output)

        if not found_in_output:
            return {"status": "ok", "message": "Nenhum valor financeiro detectado para auditoria."}

        suspicious_values = []

        # Normalização simples para busca: remove R$ e espaços
        normalized_obs = observations.replace("R$", "").replace(" ", "")

        for val in found_in_output:
            clean_val = val.replace("R$", "").replace(" ", "").strip()

            # Se o valor tem menos de 2 caracteres, ignoramos (evita falsos positivos com '0,')
            if len(clean_val) < 3:
                continue

            # Se o valor não está contido na observação, é suspeito
            if clean_val not in normalized_obs:
                suspicious_values.append(val)

        if suspicious_values:
            logger.warning(f"FactChecker: Detectados valores suspeitos: {suspicious_values}")
            return {
                "status": "warning",
                "message": f"Valores citados não encontrados nos dados brutos: {suspicious_values}",
                "suspicious_values": suspicious_values
            }

        return {"status": "ok", "message": "Todos os valores auditados com sucesso."}

    @staticmethod
    def audit_and_fix(output: str, steps: list[dict], llm_orchestrator: any) -> str:
        """
        Versão avançada: Se detectar erro, usa o LLM para corrigir a resposta
        baseando-se estritamente nos dados reais.
        """
        all_obs = "\n".join([f"Tool {s['tool']}: {s['observation']}" for s in steps])
        check_result = FactChecker.verify_financial_data(output, all_obs)

        if check_result["status"] == "ok":
            return output

        # Se houver aviso, vamos tentar uma correção rápida via LLM (opcionalmente)
        logger.info("CoV: Iniciando processo de autocorreção via LLM...")

        try:
            llm = llm_orchestrator.get_current_llm()

            audit_prompt = (
                f"Você é um Auditor Financeiro Estrito. Sua tarefa é corrigir a resposta de um assistente.\n"
                f"DADOS REAIS (VERDADE): {all_obs}\n"
                f"RESPOSTA SUSPEITA: {output}\n\n"
                f"INSTRUÇÃO: Corrija apenas os valores numéricos da RESPOSTA SUSPEITA para que correspondam EXATAMENTE aos DADOS REAIS.\n"
                f"Mantenha o tom e o estilo original. Se o assistente inventou um dado que não existe na VERDADE, remova-o.\n"
                f"CORREÇÃO FINAL:"
            )

            # Chamada síncrona/direta ao LLM para correção (Stream off)
            corrected_output = llm.predict(audit_prompt)
            return corrected_output

        except Exception as e:
            logger.error(f"Erro ao realizar autocorreção CoV: {e}")
            return output # Fallback para a original se a correção falhar
