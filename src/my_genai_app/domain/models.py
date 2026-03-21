"""Modelos de entrada/salida de la API (DTOs)."""
from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """Cuerpo de la petición al endpoint del agente."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Mensaje del usuario. Ejemplo: 'Estoy feliz en Madrid'",
        examples=["Estoy muy feliz en Madrid", "Estoy triste en Lima"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Estoy muy feliz en Madrid"
            }
        }


class AgentResponse(BaseModel):
    """Respuesta del agente al usuario."""

    message: str = Field(..., description="Respuesta final del agente")
    sentiment: str = Field(..., description="Sentimiento detectado: positive | negative | neutral")
    city: str = Field(..., description="Ciudad detectada en el mensaje")
    tool_used: str = Field(..., description="Herramienta utilizada: weather | time")
    tool_result: str = Field(..., description="Resultado bruto de la herramienta")


class HealthResponse(BaseModel):
    """Respuesta del endpoint /health."""

    status: str = Field(default="ok")
    environment: str
    version: str