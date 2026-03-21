# My GenAI App 🤖

API de producción con **LangChain**, **LangGraph** y **FastAPI** que analiza sentimientos y responde con información contextual (clima u hora) según el estado emocional del usuario.

## 🏗️ Arquitectura

```
Usuario → FastAPI → AgentService → LangGraph
                                      │
                              SentimentNode (detecta sentimiento + ciudad)
                                      │
                              [Router Condicional]
                                 /           \
                          POSITIVO        NEGATIVO/NEUTRAL
                              │                 │
                         WeatherNode        TimeNode
                    (extraer_clima)    (extraer_hora)
                              │                 │
                          Respuesta final con empatía
```

## ✨ Características

- ✅ Detección de sentimiento (positivo/negativo/neutral) con LLM
- ✅ Router condicional con LangGraph (State Machine)
- ✅ Herramienta de clima: OpenWeatherMap API
- ✅ Herramienta de hora: geopy + timezonefinder + pytz
- ✅ Reintentos automáticos con Tenacity
- ✅ Logging estructurado con structlog
- ✅ Health checks (liveness + readiness)
- ✅ Request tracing con X-Request-ID
- ✅ Multi-stage Docker build
- ✅ CI/CD con GitHub Actions
- ✅ Cobertura de tests ≥ 80%

## 🚀 Inicio Rápido

### 1. Clonar y configurar

```bash
git clone <repo-url>
cd my_genai_app
cp .env.example .env
# Editar .env con tus claves API reales
```

### 2. Con Docker (recomendado)

```bash
# Desarrollo con hot-reload
docker compose up --build

# Producción local
docker compose -f docker-compose.yml up --build
```

### 3. Sin Docker (desarrollo local)

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Ejecutar la aplicación
uvicorn my_genai_app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📋 Variables de Entorno

| Variable | Descripción | Requerida | Default |
|---|---|---|---|
| `OPENAI_API_KEY` | Clave API de OpenAI | ✅ Sí | — |
| `OPENWEATHER_API_KEY` | Clave API de OpenWeatherMap | ✅ Sí | — |
| `OPENAI_MODEL` | Modelo de OpenAI a usar | No | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | Temperatura del LLM (0.0-2.0) | No | `0.0` |
| `ENVIRONMENT` | Entorno de ejecución | No | `development` |
| `PORT` | Puerto del servidor | No | `8000` |
| `LOG_LEVEL` | Nivel de logging | No | `INFO` |
| `OPENWEATHER_UNITS` | Unidades de temperatura | No | `metric` |
| `LANGGRAPH_RECURSION_LIMIT` | Límite de recursión del grafo | No | `10` |

## 🌐 Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/v1/agent` | Procesar mensaje del usuario |
| `GET` | `/health` | Health check general |
| `GET` | `/health/ready` | Readiness probe (Kubernetes) |
| `GET` | `/health/live` | Liveness probe (Kubernetes) |
| `GET` | `/api/v1/docs` | Swagger UI (solo dev) |
| `GET` | `/api/v1/redoc` | ReDoc (solo dev) |

## 📨 Ejemplos de Uso

### Sentimiento positivo → Clima

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy muy feliz en Madrid"}'
```

**Respuesta:**
```json
{
  "message": "¡Qué bueno que estés feliz en Madrid! Actualmente tiene un clima soleado de 28°C con sensación térmica de 30°C.",
  "sentiment": "positive",
  "city": "Madrid",
  "tool_used": "weather",
  "tool_result": "Cielo despejado, 28°C (sensación térmica 30°C), humedad 40%, viento 3.5 m/s"
}
```

### Sentimiento negativo → Hora

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy muy triste en Lima"}'
```

**Respuesta:**
```json
{
  "message": "Entiendo que estés triste en Lima. Aquí son las 04:56 PM, espero que el resto de tu día mejore. ¡Ánimo!",
  "sentiment": "negative",
  "city": "Lima",
  "tool_used": "time",
  "tool_result": "04:56 PM (15/01/2025, America/Lima)"
}
```

## 🧪 Tests

```bash
# Todos los tests con cobertura
pytest

# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración
pytest tests/integration/ -v

# Con reporte HTML de cobertura
pytest --cov=my_genai_app --cov-report=html
open htmlcov/index.html

# Con Docker
docker compose -f docker-compose.test.yml up --build
```

## 🐳 Docker — Stages Disponibles

```bash
# Desarrollo (con hot-reload)
docker build --target development -t my_genai_app:dev .

# Test (ejecuta pytest)
docker build --target test -t my_genai_app:test .
docker run --env-file .env my_genai_app:test

# Producción (imagen mínima y segura)
docker build --target production -t my_genai_app:prod .
docker run --env-file .env -p 8000:8000 my_genai_app:prod
```

## 📁 Estructura del Proyecto

```
my_genai_app/
├── src/my_genai_app/
│   ├── api/              # Capa de presentación (FastAPI)
│   │   ├── routers/      # Endpoints HTTP
│   │   ├── middleware.py # Logging, request tracking
│   │   ├── dependencies.py # Inyección de dependencias
│   │   └── main.py       # App factory
│   ├── config/           # Configuración centralizada
│   │   ├── settings.py   # Pydantic Settings (Singleton)
│   │   └── logging.py    # structlog configuración
│   ├── domain/           # Reglas de negocio
│   │   ├── enums.py      # Sentiment, NodeName
│   │   ├── models.py     # DTOs (Request/Response)
│   │   └── exceptions.py # Excepciones del dominio
│   ├── graph/            # LangGraph (State Machine)
│   │   ├── state.py      # GraphState (memoria del grafo)
│   │   ├── nodes.py      # Nodos del grafo
│   │   ├── edges.py      # Router condicional
│   │   └── builder.py    # Compilación del grafo (Singleton)
│   ├── agents/           # Agentes LLM
│   │   ├── base.py       # BaseAgent abstracto
│   │   ├── sentiment_agent.py
│   │   ├── weather_agent.py
│   │   └── time_agent.py
│   ├── tools/            # Herramientas LangChain
│   │   ├── weather_tool.py  # OpenWeatherMap
│   │   └── time_tool.py     # geopy + pytz
│   └── services/         # Capa de aplicación (Facade)
│       └── agent_service.py
├── tests/
│   ├── unit/             # Tests de unidades individuales
│   └── integration/      # Tests de flujo HTTP completo
├── .github/workflows/    # CI/CD pipelines
├── scripts/
│   └── entrypoint.sh     # Script de inicio del contenedor
├── Dockerfile            # Multi-stage build
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## 🏛️ Patrones de Diseño Implementados

| Patrón | Dónde | Por qué |
|---|---|---|
| **Singleton** | `get_settings()`, `build_graph()`, `get_agent_service()` | Una sola instancia en todo el ciclo de vida |
| **Factory** | `create_app()` en `main.py` | Facilita testing y múltiples configuraciones |
| **Facade** | `AgentService` | Simplifica el acceso al grafo LangGraph |
| **State Machine** | LangGraph `GraphState` | Estado compartido y transiciones controladas |
| **Template Method** | `BaseAgent.run()` | Interfaz común para todos los agentes |
| **Strategy** | Router condicional en `edges.py` | Selección dinámica de nodo según sentimiento |
| **Dependency Injection** | `Depends()` de FastAPI | Desacopla servicios y facilita mocking |
| **Clean Architecture** | Capas `api → services → graph → agents → tools` | Separación de responsabilidades |

## 🔄 Flujo de CI/CD

```
Push/PR → Lint (ruff + mypy) → Unit Tests → Integration Tests → Docker Build Check
                                                                        │
main branch ─────────────────────────────────────────────── Build & Push → Deploy Staging
git tag v*.*.* ──────────────────────────────────────────── Build & Push → Deploy Production
```

## 🔧 Obtener API Keys

### OpenAI
1. Ve a [platform.openai.com](https://platform.openai.com)
2. API Keys → Create new secret key
3. Cópiala en `OPENAI_API_KEY`

### OpenWeatherMap
1. Ve a [openweathermap.org](https://openweathermap.org/api)
2. Sign Up → API Keys → Copy Default key
3. Cópiala en `OPENWEATHER_API_KEY`
> ⚠️ Las claves nuevas de OpenWeatherMap tardan ~10 minutos en activarse.

## 📦 Extender la Plantilla

Para agregar un nuevo agente/herramienta al grafo:

1. **Crear la herramienta** en `src/my_genai_app/tools/nueva_tool.py`
2. **Crear el agente** en `src/my_genai_app/agents/nuevo_agent.py` (extender `BaseAgent`)
3. **Agregar el nodo** en `src/my_genai_app/graph/nodes.py`
4. **Actualizar el router** en `src/my_genai_app/graph/edges.py`
5. **Registrar el nodo** en `src/my_genai_app/graph/builder.py`
6. **Actualizar `NodeName`** en `src/my_genai_app/domain/enums.py`
7. **Escribir tests** en `tests/unit/` e `tests/integration/`