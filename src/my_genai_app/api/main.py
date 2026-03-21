"""
Punto de entrada principal de la aplicación FastAPI.
Registra routers, middleware, handlers de excepciones y eventos de lifecycle.
"""
# ─── IMPORTANTE: configurar logging PRIMERO antes de cualquier otro import ───
# Esto garantiza que todos los módulos que se importen después
# ya tengan el logging configurado correctamente.
from my_genai_app.config.logging import configure_logging
configure_logging()

# ─── Imports estándar ─────────────────────────────────────────────────────────
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── Imports internos ─────────────────────────────────────────────────────────
from my_genai_app.config import get_settings
from my_genai_app.domain.exceptions import GenAIAppException
from my_genai_app.graph import build_graph

from .middleware import LoggingMiddleware
from .routers import agent, health

# ─── Logger y settings (DESPUÉS de configure_logging) ────────────────────────
logger = structlog.get_logger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """
    Factory de la aplicación FastAPI.
    Patrón Application Factory: facilita testing y reutilización.
    """
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=(
            "API de producción con LangChain, LangGraph y FastAPI. "
            "Analiza sentimientos y responde con clima u hora según el estado emocional."
        ),
        docs_url=f"{settings.api_prefix}/docs" if not settings.is_production else None,
        redoc_url=f"{settings.api_prefix}/redoc" if not settings.is_production else None,
        openapi_url=f"{settings.api_prefix}/openapi.json" if not settings.is_production else None,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)                          # /health
    app.include_router(agent.router, prefix=settings.api_prefix)  # /api/v1/...

    # ── Exception Handlers ────────────────────────────────────────────────────
    @app.exception_handler(GenAIAppException)
    async def genai_exception_handler(
        request: Request, exc: GenAIAppException
    ) -> JSONResponse:
        logger.warning(
            "Error de dominio capturado",
            path=request.url.path,
            error=exc.message,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Error inesperado no controlado",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Error interno del servidor.",
                "type": "InternalServerError",
            },
        )

    # ── Lifecycle Events ──────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup() -> None:
        """
        Acciones al arrancar la aplicación:
        - Pre-compilar el grafo LangGraph (singleton via lru_cache)
        - Verificar configuración
        """
        logger.info(
            "🚀 Iniciando aplicación",
            environment=settings.environment,
            version=settings.api_version,
        )
        # Pre-compilar el grafo para que el primer request no tenga latencia extra
        build_graph()
        logger.info("✅ Grafo LangGraph pre-compilado y listo")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        logger.info("🛑 Aplicación detenida correctamente")

    return app


# Instancia global de la aplicación
app = create_app()