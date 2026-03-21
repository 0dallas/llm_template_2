"""
Middleware personalizado para logging estructurado de requests/responses.
"""
import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
    - Genera un request_id único por cada petición (trazabilidad)
    - Registra inicio y fin de cada request con tiempo de respuesta
    - Añade el header X-Request-ID a la respuesta
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Bind del request_id al contexto de structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info(
            "Request recibido",
            query_params=str(request.query_params),
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception("Error no controlado en middleware", error=str(exc))
            raise

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.info(
            "Request completado",
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )

        # Añadir header de trazabilidad a la respuesta
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)

        return response