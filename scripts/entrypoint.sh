#!/bin/sh
set -e

# ─── Validaciones de variables de entorno obligatorias ────────────────────────
: "${OPENAI_API_KEY:?ERROR: La variable OPENAI_API_KEY no está definida}"
: "${OPENWEATHER_API_KEY:?ERROR: La variable OPENWEATHER_API_KEY no está definida}"

# ─── Puerto con valor por defecto ─────────────────────────────────────────────
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "🚀 Iniciando My GenAI App en el puerto ${PORT}..."
echo "📋 Entorno: ${ENVIRONMENT:-production}"

# ─── Iniciar la aplicación ────────────────────────────────────────────────────
# Para producción real, considera gunicorn + uvicorn workers:
# exec gunicorn my_genai_app.api.main:app \
#     --worker-class uvicorn.workers.UvicornWorker \
#     --workers "${WORKERS}" \
#     --bind "0.0.0.0:${PORT}" \
#     --log-level "${LOG_LEVEL}"

exec uvicorn my_genai_app.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level "${LOG_LEVEL}"