"""
Dependencias de FastAPI (inyección de dependencias).
Centraliza la creación de servicios para facilitar mocking en tests.
"""
from functools import lru_cache

from my_genai_app.services import AgentService


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    """
    Singleton del AgentService.
    Al ser @lru_cache, FastAPI reutilizará la misma instancia
    en toda la vida de la aplicación.
    """
    return AgentService()