# =============================================================================
# Stage 1: base — imagen común con Python y dependencias del sistema
# =============================================================================
FROM python:3.11-slim AS base

# Evitar archivos .pyc y habilitar salida sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema necesarias para geopy/timezonefinder
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 2: builder — instala dependencias de Python
# =============================================================================
FROM base AS builder

# Instalar hatch para el build
RUN pip install hatchling

# Copiar solo los archivos de definición del paquete primero (cache layer)
COPY pyproject.toml ./
COPY src/ ./src/

# Instalar solo dependencias de producción en un directorio específico
RUN pip install --prefix=/install .

# =============================================================================
# Stage 3: development — incluye dependencias de dev (para docker-compose dev)
# =============================================================================
FROM base AS development

COPY --from=builder /install /usr/local

WORKDIR /app
COPY . .

# Instalar dependencias de desarrollo
RUN pip install -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "my_genai_app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# =============================================================================
# Stage 4: test — ejecuta la suite de pruebas
# =============================================================================
FROM development AS test

ENV ENVIRONMENT=test

CMD ["pytest", "tests/", "-v", "--cov=my_genai_app", "--cov-report=term-missing"]

# =============================================================================
# Stage 5: production — imagen final mínima y segura
# =============================================================================
FROM base AS production

# Crear usuario no-root para seguridad
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home appuser

# Copiar las dependencias instaladas desde builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copiar el código fuente y el entrypoint
COPY src/ ./src/
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh

RUN chmod +x ./scripts/entrypoint.sh

# Cambiar a usuario no-root
USER appuser

# PORT con valor por defecto
ENV PORT=8000

EXPOSE ${PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ⚠️  RESPUESTA A TU PREGUNTA SOBRE EL ENTRYPOINT:
# Usar CMD ["sh", "-c", "uvicorn ... --port ${PORT}"] es CORRECTO y profesional
# cuando necesitas expansión de variables de entorno en tiempo de ejecución.
# La forma exec ["uvicorn", ...] NO expande variables de entorno del shell,
# por eso necesitas la forma shell con "sh", "-c".
# RECOMENDACIÓN: usar un script entrypoint.sh es aún más limpio y permite
# lógica adicional (validaciones, migraciones, etc.) antes de arrancar.
ENTRYPOINT ["./scripts/entrypoint.sh"]