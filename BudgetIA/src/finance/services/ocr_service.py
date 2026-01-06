from typing import BinaryIO
import base64
import json
from langchain_core.messages import SystemMessage, HumanMessage
from core.llm_manager import LLMOrchestrator
from core.logger import get_logger

logger = get_logger("OCRService")

class OCRService:
    def __init__(self, llm_orchestrator: LLMOrchestrator):
        self.llm_orchestrator = llm_orchestrator

    def analyze_receipt(self, file_content: bytes, content_type: str) -> dict:
        """
        Analisa uma imagem de cupom fiscal usando LLM (Vision).
        Retorna um dicionário com os dados extraídos.
        """
        try:
            # 1. Encode image to Base64
            encoded_image = base64.b64encode(file_content).decode("utf-8")
            image_data_url = f"data:{content_type};base64,{encoded_image}"

            # 2. Construct Prompt
            # Vision models often take text + image blocks
            prompt_text = """
            Você é uma IA especializada em extração de dados de Cupons Fiscais (OCR).
            Analise a imagem deste cupom fiscal e extraia os seguintes dados em formato JSON estrito:
            
            - "data": Data da compra no formato YYYY-MM-DD (Se não achar, tente estimar ou null).
            - "total": Valor total da compra (float).
            - "estabelecimento": Nome da loja/estabelecimento.
            - "itens": Lista de strings com os nomes dos itens (resumo).
            - "categoria_sugerida": Uma categoria sugerida para esta compra (ex: Alimentação, Mercado, Farmácia, Restaurante, Combustível).

            Retorne APENAS o JSON. Sem markdown, sem explicações.
            """

            logger.info("Enviando imagem para análise Vision LLM...")
            
            # 3. Call LLM
            # Solicita explicitamente um LLM com capacidade de visão
            llm = self.llm_orchestrator.get_vision_capable_llm(temperature=0.20)
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": image_data_url}
                ]
            )

            response = llm.invoke([message])
            content = response.content
            
            logger.debug(f"Vision Response: {content}")

            # 4. Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            return data

        except Exception as e:
            logger.error(f"Erro no OCR Service: {e}", exc_info=True)
            raise ValueError(f"Falha ao processar imagem: {str(e)}")
