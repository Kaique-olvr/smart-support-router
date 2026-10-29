from pydantic import BaseModel, Field
from enum import Enum

class DepartmentEnum(str, Enum):
    FINANCIAL = "Financeiro e Reembolsos"
    LOGISTICS = "Logística e Entregas"
    ACCOUNT = "Conta e Cadastro"
    RESTAURANT = "Suporte ao Restaurante"
    TECHNICAL = "Suporte Técnico / App"

class PriorityEnum(str, Enum):
    LOW = "Baixa"
    MEDIUM = "Média"
    HIGH = "Alta"
    URGENT = "Urgente"

class TicketAnalysisResult(BaseModel):
    department: DepartmentEnum = Field(description="Departamento responsável pelo encaminhamento do ticket")
    priority: PriorityEnum = Field(description="Nível de prioridade do ticket com base na urgência")
    summary: str = Field(description="Resumo executivo do problema para o atendente humano (1 a 2 frases)")
    suggested_action: str = Field(description="Ação imediata recomendada para a equipe de atendimento")
    confidence_score: float = Field(description="Grau de confiança da classificação (de 0.0 a 1.0)")

class TicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=3, json_schema_extra={"example": "TCK-98421"})
    customer_message: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        json_schema_extra={"example": "Meu pedido atrasou mais de 1 hora, veio tudo frio e cobrou 2 vezes no meu cartão de crédito!"},
    )

    @classmethod
    def model_validate(cls, obj):
        if isinstance(obj, dict):
            obj = obj.copy()
            if "customer_message" in obj and isinstance(obj["customer_message"], str):
                obj["customer_message"] = obj["customer_message"].strip()
        return super().model_validate(obj)