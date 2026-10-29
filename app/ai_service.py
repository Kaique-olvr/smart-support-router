import logging
import os
import time

from google import genai
from google.genai import types

from app.schemas import TicketRequest, TicketAnalysisResult

logger = logging.getLogger("smart_support_router")


class TicketAIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY ou GOOGLE_API_KEY não está configurada.")

        configured_model = os.getenv("GEMINI_MODEL", "").strip()
        fallback_models_raw = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-3.8-flash,gemini-2.5-flash,gemini-2.0-flash",
        )
        fallback_models = [
            model.strip() for model in fallback_models_raw.split(",") if model.strip()
        ]

        self.model_names = []
        if configured_model:
            self.model_names.append(configured_model)
        for model in fallback_models:
            if model not in self.model_names:
                self.model_names.append(model)
        if not self.model_names:
            self.model_names = ["gemini-3.8-flash"]

        self.model_name = self.model_names[0]
        self.max_retries = max(1, int(os.getenv("GEMINI_MAX_RETRIES", "2")))
        self.retry_delay_seconds = max(0.5, float(os.getenv("GEMINI_RETRY_DELAY_SECONDS", "1.0")))
        self.client = genai.Client(api_key=api_key)

    def _parse_response(self, response):
        if hasattr(response, "parsed") and response.parsed is not None:
            return TicketAnalysisResult.model_validate(response.parsed)

        if hasattr(response, "text") and response.text:
            return TicketAnalysisResult.model_validate_json(response.text)

        raise ValueError("A resposta da IA não retornou um payload JSON válido.")

    def _request_model(self, model_name: str, prompt: str):
        response = self.client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TicketAnalysisResult,
                temperature=0.1,
            ),
        )
        return self._parse_response(response)

    def analyze_ticket(self, ticket: TicketRequest) -> TicketAnalysisResult:
        prompt = f"""
        Você é um sistema especialista em triagem e roteamento de chamados do ecossistema de delivery.
        Análise o seguinte ticket do cliente e faça a classificação estruturada:

        ID do Ticket: {ticket.ticket_id}
        Mensagem do Cliente: "{ticket.customer_message.strip()}"
        """

        last_error = None

        for attempt in range(self.max_retries + 1):
            for model_name in self.model_names:
                try:
                    return self._request_model(model_name, prompt)
                except Exception as exc:  # pragma: no cover - depends on external API
                    last_error = exc
                    logger.warning(
                        "Falha ao chamar o modelo %s na tentativa %s/%s: %s",
                        model_name,
                        attempt + 1,
                        self.max_retries + 1,
                        exc,
                    )

            if attempt < self.max_retries:
                time.sleep(self.retry_delay_seconds)

        if last_error is not None:
            raise last_error

        raise ValueError("A resposta da IA não retornou um payload JSON válido.")