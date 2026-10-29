import asyncio
import logging

from fastapi import FastAPI, HTTPException, status
from dotenv import load_dotenv

from app.schemas import TicketRequest, TicketAnalysisResult
from app.ai_service import TicketAIService

load_dotenv()

logger = logging.getLogger("smart_support_router")

app = FastAPI(
    title="Smart Support Router API",
    description="Microsserviço inteligente em Python/FastAPI para classificação, priorização e roteamento automático de tickets de suporte utilizando Gemini LLM e Pydantic.",
    version="1.0.0"
)

try:
    ai_service = TicketAIService()
except RuntimeError as exc:
    logger.warning("AI service initialization failed: %s", exc)
    ai_service = None


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy", "service": "Smart Support Router"}


@app.post("/api/v1/tickets/analyze", response_model=TicketAnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_ticket(ticket: TicketRequest):
    if ai_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao processar o ticket via IA: serviço de IA não configurado.",
        )

    try:
        result = await asyncio.to_thread(ai_service.analyze_ticket, ticket)
        return result
    except Exception as exc:
        logger.exception("Erro ao analisar ticket %s", ticket.ticket_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao processar o ticket via IA. Tente novamente em instantes.",
        ) from exc