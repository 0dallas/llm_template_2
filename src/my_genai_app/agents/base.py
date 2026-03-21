"""Clase base abstracta para todos los agentes."""
from abc import ABC, abstractmethod
from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from my_genai_app.config import get_settings
from my_genai_app.domain.exceptions import LLMCallError

logger = structlog.get_logger(__name__)


def _build_llm() -> ChatOpenAI:
    """Construye la instancia del LLM con la configuración centralizada."""
    settings = get_settings()
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
        api_key=settings.openai_api_key.get_secret_value(),
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _invoke_with_retry(chain: Any, input_data: Any) -> Any:
    """
    Invoca un chain LangChain con reintentos automáticos (tenacity).
    Centraliza la lógica de retries para todos los agentes.
    """
    try:
        return await chain.ainvoke(input_data)
    except Exception as e:
        logger.warning("Fallo en llamada al LLM, reintentando...", error=str(e))
        raise LLMCallError(f"Error al invocar LLM: {e}") from e


class BaseAgent(ABC):
    """
    Clase base para todos los agentes.
    Define la interfaz común y provee el LLM compartido.
    """

    def __init__(self) -> None:
        self._llm: BaseChatModel = _build_llm()
        self._logger = structlog.get_logger(self.__class__.__name__)

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Ejecuta la lógica principal del agente."""
        raise NotImplementedError