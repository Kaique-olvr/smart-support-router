from fastapi.testclient import TestClient
from app.ai_service import TicketAIService
from app.main import app, ai_service

client = TestClient(app)


def test_default_model_is_current_supported_model(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    service = TicketAIService()

    assert service.model_name == "gemini-3.8-flash"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Smart Support Router"}


def test_analyze_ticket_rejects_short_customer_message():
    response = client.post(
        "/api/v1/tickets/analyze",
        json={
            "ticket_id": "TCK-123",
            "customer_message": "abc",
        },
    )

    assert response.status_code == 422


def test_analyze_ticket_handles_ai_errors(monkeypatch):
    def raise_runtime_error(_):
        raise RuntimeError("gemini unavailable")

    monkeypatch.setattr(ai_service, "analyze_ticket", raise_runtime_error)

    response = client.post(
        "/api/v1/tickets/analyze",
        json={
            "ticket_id": "TCK-123",
            "customer_message": "Meu pedido chegou atrasado e veio em estado ruim.",
        },
    )

    assert response.status_code == 500
    assert "Falha ao processar o ticket via IA" in response.json()["detail"]
    assert "gemini unavailable" not in response.json()["detail"]