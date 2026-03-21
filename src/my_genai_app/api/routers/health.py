"""
Router de Health Check.
Endpoint estándar de producción para verificar el estado de la aplicación.
Compatible con Kubernetes liveness/readiness probes.
"""
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from my_genai_app.config import get_settings
from my_genai_app.domain.models import HealthResponse

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Verifica el estado de la aplicación. "
        "Usado por load balancers, Kubernetes probes y monitoreo."
    ),
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check.

    Returns:
        HealthResponse con status, environment y version.
    """
    settings = get_settings()
    logger.debug("Health check ejecutado")
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=settings.api_version,
    )


@router.get(
    "/health/ready",
    summary="Readiness Check",
    description="Verifica si la aplicación está lista para recibir tráfico.",
)
async def readiness_check() -> JSONResponse:
    """
    Readiness probe para Kubernetes.
    Verifica que el grafo LangGraph esté compilado y listo.
    """
    from my_genai_app.graph import build_graph

    try:
        graph = build_graph()
        if graph is None:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Graph not compiled"},
            )
        return JSONResponse(
            status_code=200,
            content={"status": "ready"},
        )
    except Exception as e:
        logger.error("Readiness check fallido", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": str(e)},
        )


@router.get(
    "/health/live",
    summary="Liveness Check",
    description="Verifica que el proceso de la aplicación esté vivo.",
)
async def liveness_check() -> JSONResponse:
    """Liveness probe para Kubernetes."""
    return JSONResponse(status_code=200, content={"status": "alive"})