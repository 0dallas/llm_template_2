"""
Configuración de structlog para logging estructurado en JSON (producción)
o en formato legible para humanos (desarrollo).
"""
import logging
import sys

import structlog

from my_genai_app.config.settings import get_settings


def configure_logging() -> None:
    """
    Configura structlog según el entorno:
    - Producción/Staging: JSON estructurado (compatible con ELK, Datadog, etc.)
    - Desarrollo/Test: formato legible con colores
    """
    settings = get_settings()

    # Nivel de log según configuración
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Shared processors para todos los entornos
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.environment in ("production", "staging"):
        # JSON estructurado para producción
        renderer = structlog.processors.JSONRenderer()
    else:
        # Salida legible con colores para desarrollo
        renderer = structlog.dev.ConsoleRenderer(colors=True)  # type: ignore[assignment]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configurar el logging estándar de Python para capturar logs de librerías
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silenciar logs verbosos de librerías externas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)