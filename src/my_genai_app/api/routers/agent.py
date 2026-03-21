"""
Router del agente principal.
Expone el endpoint POST /agent que procesa mensajes del usuario.
"""
import structlog
from fastapi import APIRouter, Depends

from my_genai_app.api.dependencies import get_agent_service
from my_genai_app.domain.models import AgentRequest, AgentResponse
from my_genai_app.services import AgentService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Agent"])


@router.post(
    "/agent",
    response_model=AgentResponse,
    summary="Procesar mensaje del usuario",
    description=(
        "Recibe un mensaje del usuario, detecta el sentimiento y la ciudad, "
        "y responde con información del clima (sentimiento positivo) "
        "o la hora local (sentimiento negativo)."
    ),
    responses={
        200: {"description": "Respuesta exitosa del agente"},
        422: {"description": "No se pudo detectar sentimiento o ciudad"},
        502: {"description": "Error al llamar a herramienta externa (clima/hora)"},
        500: {"description": "Error interno del servidor"},
    },
)
async def process_message(
    request: AgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """
    Endpoint principal del agente.

    **Ejemplos de uso:**
    - `"Estoy muy feliz en Madrid"` → Responde con el clima de Madrid
    - `"Estoy triste en Lima"` → Responde con la hora actual de Lima

    El flujo interno es:
    1. Detectar sentimiento (positivo/negativo/neutral) y ciudad
    2. Router LangGraph decide el siguiente nodo
    3. Nodo de clima o nodo de hora ejecuta la herramienta correspondiente
    4. Se genera una respuesta empática con los datos obtenidos
    """
    log = logger.bind(endpoint="/agent", message=request.message)
    log.info("Procesando mensaje en endpoint /agent")

    response = await service.process(request)

    log.info(
        "Mensaje procesado exitosamente",
        sentiment=response.sentiment,
        city=response.city,
        tool_used=response.tool_used,
    )
    return response