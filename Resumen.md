## ✅ Respuesta sobre el Entrypoint

```bash
# ❌ EVITAR — No expande variables de entorno del shell:
CMD ["uvicorn", "my_genai_app.api.main:app", "--port", "${PORT}"]

# ✅ CORRECTO — Expande variables pero pierde señales POSIX (SIGTERM):
CMD ["sh", "-c", "uvicorn my_genai_app.api.main:app --host 0.0.0.0 --port ${PORT}"]

# ✅✅ RECOMENDADO (lo que implementamos) — Script entrypoint:
ENTRYPOINT ["./scripts/entrypoint.sh"]
# Ventajas:
# - Expande variables de entorno ✅
# - Permite validaciones previas al arranque ✅
# - Maneja señales POSIX correctamente con exec ✅
# - Fácil de leer y mantener ✅
# - Permite agregar lógica (migraciones, healthchecks pre-arranque) ✅
```

## ✅ Respuesta sobre pydantic-settings + @lru_cache + tenacity

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISIONES DE DISEÑO                          │
├─────────────────────────┬───────────────────────────────────────┤
│ pydantic-settings        │ ✅ USAR                               │
│                          │ Validación automática de env vars     │
│                          │ Type safety completo                  │
│                          │ SecretStr para keys sensibles         │
│                          │ Soporte .env nativo                   │
├─────────────────────────┼───────────────────────────────────────┤
│ @lru_cache en            │ ✅ USAR (Singleton pattern)           │
│ get_settings()           │ Una sola lectura del entorno          │
│ build_graph()            │ Compilación del grafo solo 1 vez      │
│ get_agent_service()      │ Reutilización de instancias           │
├─────────────────────────┼───────────────────────────────────────┤
│ tenacity                 │ ✅ USAR con configuración precisa     │
│                          │ retry_if_exception_type → solo        │
│                          │ reintenta errores recuperables        │
│                          │ wait_exponential → evita sobrecargar  │
│                          │ stop_after_attempt(3) → límite claro  │
├─────────────────────────┼───────────────────────────────────────┤
│ structlog                │ ✅ USAR                               │
│                          │ JSON en producción (ELK/Datadog)      │
│                          │ Context vars para request tracing     │
│                          │ Formato legible en desarrollo         │
└─────────────────────────┴───────────────────────────────────────┘
```

## 📋 Checklist de instalación desde cero

```bash
# 1. Clonar el repo y entrar
git clone <tu-repo>
cd my_genai_app

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Instalar el paquete en modo editable con dependencias de dev
pip install -e ".[dev]"

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar OPENAI_API_KEY y OPENWEATHER_API_KEY reales

# 5. Verificar que los tests pasan
pytest

# 6. Verificar linting
ruff check src/ tests/
ruff format src/ tests/

# 7. Verificar tipos
mypy src/

# 8. Arrancar la aplicación
uvicorn my_genai_app.api.main:app --host 0.0.0.0 --port 8000 --reload

# 9. Probar el endpoint
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy muy feliz en Madrid"}'

# 10. Ver los docs
open http://localhost:8000/api/v1/docs
```

## 📦 Árbol final de todos los archivos
```text
my_genai_app/
├── src/
│   └── my_genai_app/
│       ├── __init__.py                         ← versión del paquete
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py                         ← App Factory + lifecycle
│       │   ├── middleware.py                   ← LoggingMiddleware + request_id
│       │   ├── dependencies.py                 ← Singleton AgentService
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── agent.py                    ← POST /api/v1/agent
│       │       └── health.py                   ← GET /health, /ready, /live
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py                     ← pydantic-settings + lru_cache
│       │   └── logging.py                      ← structlog JSON/dev
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── enums.py                        ← Sentiment, NodeName
│       │   ├── models.py                       ← AgentRequest, AgentResponse
│       │   └── exceptions.py                   ← Excepciones tipadas del dominio
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── state.py                        ← GraphState (State Machine)
│       │   ├── nodes.py                        ← sentiment_node, weather_node, time_node
│       │   ├── edges.py                        ← sentiment_router (condicional)
│       │   └── builder.py                      ← build_graph() Singleton
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py                         ← BaseAgent + _invoke_with_retry
│       │   ├── sentiment_agent.py              ← SentimentAgent
│       │   ├── weather_agent.py                ← WeatherAgent
│       │   └── time_agent.py                   ← TimeAgent
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── weather_tool.py                 ← @tool extraer_clima
│       │   └── time_tool.py                    ← @tool extraer_hora
│       └── services/
│           ├── __init__.py
│           └── agent_service.py                ← Facade → LangGraph
├── tests/
│   ├── __init__.py
│   ├── conftest.py                             ← Fixtures globales
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_settings.py                    ← Tests de configuración
│   │   ├── test_tools.py                       ← Tests de herramientas
│   │   ├── test_agents.py                      ← Tests de agentes
│   │   └── test_graph.py                       ← Tests de nodos, router, builder
│   └── integration/
│       ├── __init__.py
│       └── test_api_endpoints.py               ← Tests HTTP completos
├── .github/
│   └── workflows/
│       ├── ci.yml                              ← Lint + Tests + Docker Build
│       └── cd.yml                              ← Build & Push + Deploy
├── scripts/
│   └── entrypoint.sh                           ← Script de inicio del contenedor
├── Dockerfile                                  ← 5 stages: base/builder/dev/test/prod
├── docker-compose.yml                          ← Desarrollo local
├── docker-compose.test.yml                     ← Tests en Docker
├── pyproject.toml                              ← hatchling + ruff + mypy + pytest
├── .env.example                                ← Plantilla de variables de entorno
├── .gitignore
└── README.md
```

## ♣ QA

### 1. ¿Por qué CI y CD están separados?

#### **Concepto**
CI = Continuous Integration  → "¿Mi código está bien?"  
CD = Continuous Deployment   → "¿Puedo enviarlo a producción?"  

#### **Lo que hace cada uno**  
```
┌─────────────────────────────────────────────────────────────────┐
│                         ci.yml                                  │
│                                                                 │
│  CUÁNDO se ejecuta:                                             │
│  - Cualquier push a main, develop, feature/**                   │
│  - Cualquier Pull Request hacia main o develop                  │
│                                                                 │
│  QUÉ hace (en orden):                                           │
│                                                                 │
│  1. lint ────────────────────────────────────────────────────── │
│     • ruff check   → detecta errores de código                  │
│     • ruff format  → verifica que el formato sea correcto       │
│     • mypy         → verifica tipos estáticos                   │
│                                                                 │
│  2. unit-tests (depende de lint) ────────────────────────────── │
│     • pytest tests/unit/                                        │
│     • genera coverage-unit.xml                                  │
│                                                                 │
│  3. integration-tests (depende de unit-tests) ───────────────── │
│     • pytest tests/integration/                                 │
│     • genera coverage-integration.xml                           │
│                                                                 │
│  4. docker-build (depende de unit + integration) ────────────── │
│     • Construye imagen production (sin hacer push)              │
│     • Construye imagen test (sin hacer push)                    │
│     • Solo verifica que el Dockerfile no tiene errores          │
│                                                                 │
│  5. coverage-report (solo en PRs) ───────────────────────────── │
│     • Combina coverage-unit + coverage-integration              │
│     • Comenta el % de cobertura en el PR de GitHub              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         cd.yml                                  │
│                                                                 │
│  CUÁNDO se ejecuta:                                             │
│  - Push a main → deploy a STAGING                               │
│  - Push de un tag v*.*.* (ej: v1.2.0) → deploy a PRODUCTION     │
│  - Manualmente desde GitHub Actions UI                          │
│                                                                 │
│  QUÉ hace (en orden):                                           │
│                                                                 │
│  1. setup ───────────────────────────────────────────────────── │
│     • Determina el entorno (staging o production)               │
│     • Determina el tag de imagen Docker                         │
│     • Ej: tag = "sha-a1b2c3d" o "v1.2.0"                        │
│                                                                 │
│  2. build-and-push ──────────────────────────────────────────── │
│     • Construye imagen production del Dockerfile                │
│     • La sube a GitHub Container Registry (ghcr.io)             │
│     • Guarda el digest SHA de la imagen                         │
│                                                                 │
│  3a. deploy-staging (si entorno = staging) ──────────────────── │
│      • Despliega la imagen en el entorno de staging             │
│      • URL: https://staging.my-genai-app.example.com            │
│                                                                 │
│  3b. deploy-production (si entorno = production) ────────────── │
│      • Despliega la imagen en producción                        │
│      • URL: https://my-genai-app.example.com                    │
│                                                                 │
│  4. notify ──────────────────────────────────────────────────── │
│     • Notifica si el deploy fue exitoso o fallido               │
└─────────────────────────────────────────────────────────────────┘
```
#### **¿Por qué separarlos y no tener un solo archivo?**
```
RAZÓN 1 — Velocidad y frecuencia:
   CI corre en CADA push (puede ser 20 veces al día)
   CD corre solo cuando el código llega a main/tag (1-2 veces al día)
   → Separados son más rápidos de leer y mantener

RAZÓN 2 — Responsabilidades distintas:
   CI  → "¿El código es correcto?" (tarea de desarrolladores)
   CD  → "¿Dónde y cómo se despliega?" (tarea de DevOps/infra)
   → Distintos equipos pueden tocar distintos archivos

RAZÓN 3 — Seguridad:
   CI no necesita secretos de AWS/GCP/Kubernetes
   CD sí necesita credenciales de producción
   → Principio de mínimo privilegio

RAZÓN 4 — Claridad en fallos:
   Si CD falla sabes que es un problema de despliegue
   Si CI falla sabes que es un problema de código
```

#### **Flujo completo visualizado**
```
Developer hace push a feature/nueva-feature
           │
           ▼
      ci.yml se dispara
      ┌─────────────────────────────────┐
      │ lint → unit → integration →     │
      │ docker-build-check              │
      └──────────────┬──────────────────┘
                     │
          ✅ Todo OK  │  ❌ Falla → notifica al dev
                     │
           PR hacia main aprobado
                     │
           ▼
      merge a main
           │
           ├── ci.yml se dispara (valida main)
           └── cd.yml se dispara
               ┌────────────────────────────────┐
               │ build-push → deploy-staging    │
               └────────────────────────────────┘
                             │
              QA aprueba staging
                             │
           git tag v1.2.0 && git push --tags
                             │
                        cd.yml se dispara
               ┌────────────────────────────────┐
               │ build-push → deploy-production │
               └────────────────────────────────┘
```

### 2. ¿Cómo funcionan los tests? ¿Qué hacen unit e integration?

#### **La diferencia conceptual**
```
┌─────────────────────────────────────────────────────────────┐
│                    TESTS UNITARIOS                          │
│                    tests/unit/                              │
│                                                             │
│  Prueban UNA sola pieza de código en completo aislamiento.  │
│  Todo lo externo (LLM, APIs, BD) se MOCKEA (simula).        │
│                                                             │
│  Características:                                           │
│  ✅ Muy rápidos (milisegundos)                              │
│  ✅ No necesitan internet                                   │
│  ✅ No gastan créditos de OpenAI                            │
│  ✅ Resultados deterministas (siempre igual)                │
│  ✅ Fácil de identificar qué falló exactamente              │
│                                                             │
│  Qué prueban en nuestro proyecto:                           │
│  • test_settings.py  → ¿Settings carga bien las env vars?   │
│  • test_tools.py     → ¿extraer_clima/hora formatean bien?  │
│  • test_agents.py    → ¿Los agentes procesan bien el JSON?  │
│  • test_graph.py     → ¿El router elige el nodo correcto?   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  TESTS DE INTEGRACIÓN                       │
│                  tests/integration/                         │
│                                                             │
│  Prueban que VARIAS piezas funcionan JUNTAS.                │
│  En nuestro caso: HTTP Request → FastAPI → Service → Graph  │
│  Los servicios externos (LLM, clima) siguen mockeados,      │
│  pero el flujo HTTP completo es REAL.                       │
│                                                             │
│  Características:                                           │
│  ✅ Prueban el flujo completo de extremo a extremo          │
│  ✅ Verifican que el routing HTTP funciona                  │
│  ✅ Verifican headers, status codes, formato de respuesta   │
│  ✅ Verifican la inyección de dependencias de FastAPI       │
│  ⚠️  Más lentos que unitarios (pero aún sin internet)       │
│                                                             │
│  Qué prueban en nuestro proyecto:                           │
│  • ¿POST /api/v1/agent devuelve 200 con JSON correcto?      │
│  • ¿GET /health devuelve 200 con estructura correcta?       │
│  • ¿Un mensaje vacío devuelve 422?                          │
│  • ¿Los headers X-Request-ID están presentes?               │
│  • ¿Un error del grafo devuelve 500?                        │
└─────────────────────────────────────────────────────────────┘
```

#### **Cómo funciona el mock en la práctica**
```python
# ─── TEST UNITARIO: test_tools.py ────────────────────────────────────────────
# Probamos extraer_clima sin hacer llamadas HTTP reales

@patch("my_genai_app.tools.weather_tool.requests.get")  # ← intercepta la llamada HTTP
def test_extraer_clima_success(self, mock_get):
    # Simulamos la respuesta de OpenWeatherMap
    mock_get.return_value.json.return_value = {
        "main": {"temp": 28.5, "feels_like": 30.0, "humidity": 45},
        "weather": [{"description": "cielo despejado"}],
        "wind": {"speed": 3.2},
    }
    mock_get.return_value.raise_for_status = MagicMock()

    # Ejecutamos la herramienta real
    result = extraer_clima.invoke({"city": "Madrid"})

    # Verificamos que el resultado es correcto
    assert "28.5°C" in result       # ← prueba real del código
    assert "Cielo despejado" in result
    # NO se hizo ninguna llamada HTTP real ✅


# ─── TEST INTEGRACIÓN: test_api_endpoints.py ─────────────────────────────────
# Probamos el flujo HTTP completo pero mockeando el AgentService

def test_agent_endpoint_positive_sentiment(self, integration_app, integration_client):
    # En vez de llamar al LLM real, inyectamos una respuesta simulada
    mock_service = AsyncMock()
    mock_service.process.return_value = AgentResponse(
        message="¡Qué bueno que estés feliz en Madrid!",
        sentiment="positive",
        city="Madrid",
        tool_used="weather",
        tool_result="Soleado, 28°C",
    )
    # Sobreescribimos la dependencia de FastAPI
    integration_app.dependency_overrides[get_agent_service] = lambda: mock_service

    # Hacemos una request HTTP REAL al servidor de test
    response = integration_client.post(
        "/api/v1/agent",                    # ← URL real
        json={"message": "Estoy feliz en Madrid"},  # ← JSON real
    )

    # Verificamos el response HTTP completo
    assert response.status_code == 200     # ← status code real
    assert response.json()["city"] == "Madrid"  # ← body real
    assert "x-request-id" in response.headers   # ← header del middleware
```

#### **Pirámide de tests**
```text
                    /\
                   /  \
                  / E2E \          ← End-to-End (contra API real con LLM real)
                 /  (0)  \          No los tenemos — gastarían dinero en CI
                /─────────\
               /           \
              / Integración \     ← tests/integration/ (lo que tenemos)
             /    (pocos)    \      Flujo HTTP completo, servicios mockeados
            /─────────────────\
           /                   \
          /     Unitarios       \   ← tests/unit/ (la mayoría)
         /       (muchos)        \   Rápidos, aislados, baratos
        /─────────────────────────\
```

### 3. ¿Cuál es la diferencia entre `docker-compose.yml` y `docker-compose.test.yml`?
```text
┌────────────────────────────────┬─────────────────────────────────────────┐
│     docker-compose.yml         │      docker-compose.test.yml            │
├────────────────────────────────┼─────────────────────────────────────────┤
│ ¿Para qué?                     │ ¿Para qué?                              │
│ Desarrollo local del día a día │ Ejecutar la suite de tests              │
│                                │                                         │
│ ¿Qué stage del Dockerfile usa? │ ¿Qué stage del Dockerfile usa?          │
│ target: development            │ target: test                            │
│                                │                                         │
│ ¿Qué hace al ejecutar?         │ ¿Qué hace al ejecutar?                  │
│ Levanta el servidor uvicorn    │ Ejecuta pytest y termina                │
│ con --reload (hot-reload)      │                                         │
│                                │                                         │
│ ¿Monta volúmenes?              │ ¿Monta volúmenes?                       │
│ Sí: ./src:/app/src             │ Solo coverage.xml para leer el reporte  │
│ (cambios en código = reload)   │                                         │
│                                │                                         │
│ ¿Qué variables usa?            │ ¿Qué variables usa?                     │
│ Tu .env real con claves reales │ Variables falsas para tests             │
│                                │ OPENAI_API_KEY=sk-test-fake-key         │
│                                │                                         │
│ ¿Cuándo lo usas?               │ ¿Cuándo lo usas?                        │
│ docker compose up              │ docker compose -f                       │
│                                │   docker-compose.test.yml up --build    │
│                                │                                         │
│ ¿El contenedor termina?        │ ¿El contenedor termina?                 │
│ No, queda escuchando           │ Sí, termina al acabar pytest            │
└────────────────────────────────┴─────────────────────────────────────────┘
```

#### **Comandos concretos**
```bash
# ─── docker-compose.yml (DESARROLLO) ──────────────────────────────────────────
docker compose up --build
# → Levanta el servidor en localhost:8000
# → Cambias código en src/ → el servidor se recarga automáticamente
# → Ctrl+C para detener

# ─── docker-compose.test.yml (TESTS) ──────────────────────────────────────────
docker compose -f docker-compose.test.yml up --build
# → Ejecuta pytest
# → Muestra el reporte de cobertura en consola
# → El contenedor termina con exit code 0 (éxito) o 1 (tests fallidos)
# → En CI/CD se usa el exit code para saber si el build pasa o no
```

### 4. ¿Al ejecutar el Dockerfile siempre pasa por los 5 stages?
**No.** Docker solo ejecuta el stage que le indicas con --target. Los stages anteriores se usan solo si el stage destino los necesita (COPY --from=...).

```text
# Dockerfile tiene estos stages:
# base → builder → development
#                → test
#                → production

# ─── Si construyes "production": ─────────────────────────────────────────────
docker build --target production .

# Docker ejecuta:
# ✅ base       (lo necesita production directamente)
# ✅ builder    (production hace COPY --from=builder)
# ❌ development (no se necesita)
# ❌ test        (no se necesita)
# ✅ production  (el target pedido)

# ─── Si construyes "development": ────────────────────────────────────────────
docker build --target development .

# Docker ejecuta:
# ✅ base        (lo necesita development)
# ✅ builder     (development hace COPY --from=builder)
# ✅ development (el target pedido)
# ❌ test        (no se necesita)
# ❌ production  (no se necesita)

# ─── Si construyes "test": ───────────────────────────────────────────────────
docker build --target test .

# Docker ejecuta:
# ✅ base        (base de development, base de test)
# ✅ builder     (development lo necesita, test extiende development)
# ✅ development (test extiende FROM development)
# ✅ test        (el target pedido)
# ❌ production  (no se necesita)

# ─── Si NO especificas --target: ─────────────────────────────────────────────
docker build .

# Docker ejecuta TODOS los stages hasta el ÚLTIMO definido en el Dockerfile
# En nuestro caso ejecutaría: base → builder → development → test → production
# Por eso SIEMPRE debes usar --target en proyectos multi-stage
```

#### **Cómo está estructurada la dependencia entre stages**

```text
┌──────────┐
│   base   │ ← imagen python:3.11-slim + apt packages
└────┬─────┘
     │ FROM base AS builder
┌────▼─────┐
│  builder │ ← instala dependencias pip en /install
└────┬─────┘
     │
     ├──── FROM base AS development ────────────────────────┐
     │     COPY --from=builder /install /usr/local          │
     │     instala deps de dev                              │
     │     CMD: uvicorn --reload                            │
     │                                                      │
     │     FROM development AS test ──────────────────────┐ │
     │     (hereda todo de development)                   │ │
     │     CMD: pytest                                    │ │
     │                                                    │ │
     └──── FROM base AS production ───────────────────────┘ │
           COPY --from=builder /install /usr/local          │
           usuario no-root                                  │
           ENTRYPOINT: entrypoint.sh                        │
           (imagen más pequeña y segura)                    │
```

### 5. ¿Cuándo pasar a v2 y cómo manejarlo en el backend?

#### **¿Cuándo crear una v2?**
```text
┌──────────────────────────────────────────────────────────────┐
│          CAMBIOS QUE REQUIEREN v2 (Breaking Changes)         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ❌ Eliminas un campo del response:                          │
│     v1: { message, sentiment, city, tool_used, tool_result } │
│     v2: { message, sentiment, city }                         │
│     → Los clientes que leían tool_used se rompen             │
│                                                              │
│  ❌ Cambias el nombre de un campo:                           │
│     v1: { "city": "Madrid" }                                 │
│     v2: { "ciudad": "Madrid" }                               │
│                                                              │
│  ❌ Cambias el tipo de un campo:                             │
│     v1: { "sentiment": "positive" }  ← string                │
│     v2: { "sentiment": 1 }           ← int                   │
│                                                              │
│  ❌ Cambias la estructura de la request:                     │
│     v1: POST body: { "message": "..." }                      │
│     v2: POST body: { "input": { "text": "..." } }            │
│                                                              │
│  ❌ Cambias la autenticación:                                │
│     v1: sin auth                                             │
│     v2: requiere Bearer token                                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│          CAMBIOS QUE NO REQUIEREN v2                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Agregas un campo OPCIONAL al response:                   │
│     v1: { message, sentiment, city }                         │
│     v1 (actualizada): { message, sentiment, city, metadata } │
│     → Los clientes anteriores simplemente ignoran metadata   │
│                                                              │
│  ✅ Mejoras internas (cambias el LLM, la lógica, etc.)       │
│  ✅ Corriges un bug sin cambiar el contrato                  │
│  ✅ Mejoras el performance                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### **Cómo implementarlo en el backend**
```text
# ─── ESTRUCTURA DE CARPETAS ───────────────────────────────────────────────────
src/my_genai_app/api/
├── routers/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── agent.py      ← POST /api/v1/agent (versión original)
│   │   └── health.py
│   ├── v2/
│   │   ├── __init__.py
│   │   └── agent.py      ← POST /api/v2/agent (nueva versión)
│   └── __init__.py
```

```python
# ─── src/my_genai_app/api/routers/v1/agent.py ────────────────────────────────
from fastapi import APIRouter, Depends
from my_genai_app.domain.models import AgentRequest, AgentResponse
from my_genai_app.services.v1.agent_service import AgentServiceV1

router = APIRouter(tags=["Agent v1"])

@router.post("/agent", response_model=AgentResponse)
async def process_message_v1(
    request: AgentRequest,
    service: AgentServiceV1 = Depends(get_agent_service_v1),
) -> AgentResponse:
    return await service.process(request)
```
```python
# ─── src/my_genai_app/api/routers/v2/agent.py ────────────────────────────────
from fastapi import APIRouter, Depends
from my_genai_app.domain.models_v2 import AgentRequestV2, AgentResponseV2
from my_genai_app.services.v2.agent_service import AgentServiceV2

router = APIRouter(tags=["Agent v2"])

@router.post("/agent", response_model=AgentResponseV2)
async def process_message_v2(
    request: AgentRequestV2,
    service: AgentServiceV2 = Depends(get_agent_service_v2),
) -> AgentResponseV2:
    return await service.process(request)
```
```python
# ─── src/my_genai_app/api/main.py ────────────────────────────────────────────
from .routers.v1 import agent as agent_v1
from .routers.v2 import agent as agent_v2

def create_app() -> FastAPI:
    app = FastAPI(...)

    # v1 sigue funcionando (no romper clientes existentes)
    app.include_router(
        agent_v1.router,
        prefix="/api/v1",
    )

    # v2 disponible para nuevos clientes
    app.include_router(
        agent_v2.router,
        prefix="/api/v2",
    )

    return app
```
```python
# ─── settings.py: controlar deprecación ──────────────────────────────────────
class Settings(BaseSettings):
    api_v1_deprecated: bool = False   # Cuando sea True, v1 muestra warning
    api_v1_sunset_date: str = ""      # "2025-12-31" → fecha de baja definitiva
```
```python
# ─── middleware de deprecación en v1 ─────────────────────────────────────────
# src/my_genai_app/api/routers/v1/agent.py

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Agent v1 (Deprecated)"])

@router.post("/agent", response_model=AgentResponse)
async def process_message_v1(request: AgentRequest, ...) -> AgentResponse:
    response = await service.process(request)

    # Añadir headers de deprecación (estándar de la industria)
    # Los clientes pueden leer estos headers para saber que deben migrar
    headers = {
        "Deprecation": "true",
        "Sunset": "Sat, 31 Dec 2025 23:59:59 GMT",
        "Link": '</api/v2/agent>; rel="successor-version"',
    }

    return JSONResponse(
        content=response.model_dump(),
        headers=headers,
    )
```
#### **Resumen de la estrategia de versionado**

```text
┌─────────────────────────────────────────────────────────────┐
│                 CICLO DE VIDA DE UNA VERSIÓN                │
│                                                             │
│  Lanzamiento v1 ────────────────────────────────────────►   │
│  Lanzamiento v2 ──────────────────────────────────────────► │
│                   │                                         │
│                   └── v1 pasa a "Deprecated"                │
│                       (headers Deprecation + Sunset)        │
│                       Sigue funcionando pero avisa          │
│                                                             │
│  6-12 meses después ──────────────────────────────────────► │
│                   v1 se da de baja (devuelve 410 Gone)      │
│                   Solo queda v2                             │
└─────────────────────────────────────────────────────────────┘

REGLA DE ORO:
"No elimines una versión hasta que el 100% del tráfico use la siguiente"
Monitorea con logs: ¿cuántos requests siguen llegando a /v1?
```
