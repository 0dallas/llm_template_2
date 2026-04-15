# ► CACHE ◄

## 1. `@lru_cache` (built-in de Python)

```python
from functools import lru_cache
```
✅ Características
- En memoria (RAM del proceso)
- Súper rápido ⚡
- Sin dependencias externas
- LRU automático  

❌ Limitaciones
- No compartido entre procesos
- No persistente
- Sin TTL (expiración por tiempo)

🧩 Cuándo usarlo
- Configuración (Settings)
- Modelos ML (.pkl)
- Clientes (S3, DB, APIs)

👉 Básicamente: cosas estáticas o casi estáticas

## 2. `cachetools` (más control en memoria)

Es como una versión más poderosa de `lru_cache`.  
  
⏱ TTL (expiración por tiempo)  
```python
from cachetools import TTLCache, cached

cache = TTLCache(maxsize=100, ttl=60)  # 60 segundos

@cached(cache)
def get_data(x):
    print("Fetching...")
    return x * 2
```
👉 Después de 60s → se invalida automáticamente  

🧠 Tipos de cache
- LRU (igual que lru_cache)
- LFU (least frequently used)
- FIFO

❌ Limitaciones
- Sigue siendo en memoria local
- No funciona bien en múltiples instancias (microservices, Kubernetes)

🧩 Cuándo usarlo
- Cuando necesitas TTL
- Cuando quieres control fino del cache
- APIs con datos semi-dinámicos

## 3. Redis (cache distribuido real)

Esto ya es producción seria / sistemas distribuidos.  

🚀 Características
- Cache en memoria externo
- Compartido entre servicios
- Persistente (opcional)
- TTL nativo
- Ultra rápido

```python
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def get_data(key):
    if r.exists(key):
        return r.get(key)

    # Simula cálculo costoso
    value = expensive_function()
    r.setex(key, 60, value)  # TTL 60s
    return value
```

💡 Ventajas clave
- Funciona con múltiples instancias
- Ideal para microservicios
- Reduce carga en DB
- Escalable

❌ Desventajas
- Necesitas infraestructura
- Más complejidad
- Latencia ligeramente mayor que memoria local

## ⚔️ Comparación clara

| Feature       | `lru_cache` | cachetools | Redis |
| ------------- | ----------- | ---------- | ----- |
| Velocidad     | ⚡⚡⚡         | ⚡⚡⚡        | ⚡⚡    |
| TTL           | ❌           | ✅          | ✅     |
| Multi-proceso | ❌           | ❌          | ✅     |
| Distribuido   | ❌           | ❌          | ✅     |
| Persistencia  | ❌           | ❌          | ✅     |
| Complejidad   | ✅ baja      | media      | alta  |

---
# ► VARIABLES ENTORNO ◄

🚀 **Solución: pydantic-settings**

👉 Automáticamente:
- Lee variables de entorno
- Convierte tipos (string → bool, int, etc.)
- Valida datos

⚙️ Ejemplo con .env
```text
DB_URL=postgresql://user:pass@localhost/db
DEBUG=true
```
``` python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    db_url: str
    debug: bool
    workers: int = 2
    api_key: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env"
    )
    # Para varaiables definidas por Docker/Kubernetes no es necesario usar SettingsConfigDict

@lru_cache()
def get_settings():
    return Settings()
```

Esto se inyecta en FastAPI

```python
# main.py
from fastapi import FastAPI, Depends
from config import Settings, get_settings

app = FastAPI()

@app.get("/")
def read_root(settings: Settings = Depends(get_settings)):
    return {"debug": settings.debug}
```

## Override en test
```python
from fastapi.testclient import TestClient
from main import app
from config import Settings, get_settings

# 👇 override
def get_test_settings():
    return Settings(
        db_url="sqlite:///test.db",
        debug=True
    )

# 🔥 aquí ocurre la magia
app.dependency_overrides[get_settings] = get_test_settings

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.json()["db"] == "sqlite:///test.db"
```

---
# ► REINTENTOS ◄

**Tenacity** es una librería de Python que sirve para reintentar automáticamente operaciones que pueden fallar, especialmente cuando trabajas con:
- APIs externas 🌐
- Bases de datos
- servicios inestables
- redes

```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(
    stop=stop_after_attempt(2),   # máximo 2 intentos
    wait=wait_fixed(1)            # 1 segundo
)
async def call_llm():
    ...
```

```python
async def safe_call():
    try:
        return await call_llm()
    except RetryError:
        return {"error": "Servicio temporalmente inestable"}
    except Exception:
        return {"error": "Error inesperado"}
```

## Tener en cuenta:

### Timeout SIEMPRE para llamados de APIs
```python
requests.get(url, timeout=5)
```
👉 Nunca dejes llamadas abiertas  

### Diferenciar errores
```python
from tenacity import retry_if_exception_type

@retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(2)
)
```
👉 Solo reintentas errores transitorios  
❌ No errores lógicos o de input  

### UX moderna (MUY importante)
👉 No haces esperar al usuario  

🔹 **A. Respuesta rápida + async**  
- "Estamos procesando tu solicitud..."  
- Background job (Celery, queue)  

🔹 **B. Streaming (mejor UX)**  
Con FastAPI + LLM:   
- Devuelves tokens en tiempo real
- Si falla → usuario ya vio algo

🔹 **C. Fallback**  
```python
try:
    return call_llm()
except:
    return "Lo siento, intenta nuevamente"
```

## Circuit Braker
👉 Es un patrón para evitar seguir llamando a un servicio que está fallando.

### 📦 Setup
```python
import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
```

### 🔴 Circuit Breaker
```python
breaker = pybreaker.CircuitBreaker(
    fail_max=3,        # abre tras 3 fallos
    reset_timeout=10   # intenta recuperación en 10s
)
```

### 🔁 Retry async
```python
@breaker
@retry(
    stop=stop_after_attempt(2),  # máximo 2 intentos
    wait=wait_exponential(min=1, max=3),
    retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
)
async def call_external_api():
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get("https://api.externa.com/data")
        response.raise_for_status()
        return response.json()
```
### ⚡ Wrapper con fallback (MUY importante)
```python
async def safe_call():
    try:
        return await call_external_api()
    except pybreaker.CircuitBreakerError:
        return {"error": "Servicio temporalmente no disponible"}
    except Exception:
        return {"error": "Fallo en la llamada externa"}
```

### 🚀 Integración con FastAPI
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/data")
async def get_data():
    result = await safe_call()
    return result
```
### Explicación
**Request 1**:  
retry intenta 2 veces → falla  
→ breaker registra 1 fallo  

**Request 2**:  
retry intenta 2 veces → falla  
→ breaker registra 2 fallos  

**Request 3**:  
retry intenta 2 veces → falla  
→ breaker registra 3 fallos  
→ 🔴 breaker OPEN  

---
# ► LOGGING ◄
`structlog` es una librería de Python para hacer logging estructurado, es decir, logs en formato clave–valor (JSON u otros) en lugar de texto plano.