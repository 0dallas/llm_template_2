"""
Fixtures globales para todos los tests.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from my_genai_app.api.main import create_app
from my_genai_app.config.settings import get_settings
from my_genai_app.domain.enums import Sentiment
from my_genai_app.domain.models import AgentRequest, AgentResponse
from my_genai_app.graph.state import GraphState


# ── Configuración de pytest-asyncio ──────────────────────────────────────────
pytest_plugins = ["pytest_asyncio"]


# ── Fixtures de configuración ────────────────────────────────────────────────
@pytest.fixture(scope="session")
def settings():
    """Settings de test (cargadas desde variables de entorno de pytest)."""
    return get_settings()


# ── Fixtures de la aplicación ─────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    """Instancia de la aplicación FastAPI para tests."""
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """Cliente de test de FastAPI (síncrono)."""
    with TestClient(app) as c:
        yield c


# ── Fixtures de datos ─────────────────────────────────────────────────────────
@pytest.fixture
def sample_positive_message() -> str:
    return "Estoy muy feliz en Madrid"


@pytest.fixture
def sample_negative_message() -> str:
    return "Estoy muy triste en Lima"


@pytest.fixture
def sample_agent_request_positive(sample_positive_message) -> AgentRequest:
    return AgentRequest(message=sample_positive_message)


@pytest.fixture
def sample_agent_request_negative(sample_negative_message) -> AgentRequest:
    return AgentRequest(message=sample_negative_message)


@pytest.fixture
def mock_weather_result() -> str:
    return "Soleado, 28°C (sensación térmica 30°C), humedad 40%, viento 3.5 m/s"


@pytest.fixture
def mock_time_result() -> str:
    return "04:56 PM (15/01/2025, America/Lima)"


@pytest.fixture
def positive_graph_state(sample_positive_message, mock_weather_result) -> GraphState:
    return GraphState(
        user_message=sample_positive_message,
        sentiment=Sentiment.POSITIVE,
        city="Madrid",
        tool_used="weather",
        tool_result=mock_weather_result,
        final_message="¡Qué bueno que estés feliz en Madrid! Actualmente tiene un clima soleado de 28°C.",
    )


@pytest.fixture
def negative_graph_state(sample_negative_message, mock_time_result) -> GraphState:
    return GraphState(
        user_message=sample_negative_message,
        sentiment=Sentiment.NEGATIVE,
        city="Lima",
        tool_used="time",
        tool_result=mock_time_result,
        final_message="Entiendo que estés triste en Lima, donde actualmente son las 04:56 PM. ¡Ánimo!",
    )


@pytest.fixture
def mock_agent_response_positive(positive_graph_state) -> AgentResponse:
    return AgentResponse(
        message=positive_graph_state.final_message,  # type: ignore[arg-type]
        sentiment="positive",
        city="Madrid",
        tool_used="weather",
        tool_result=positive_graph_state.tool_result,  # type: ignore[arg-type]
    )


@pytest.fixture
def mock_agent_response_negative(negative_graph_state) -> AgentResponse:
    return AgentResponse(
        message=negative_graph_state.final_message,  # type: ignore[arg-type]
        sentiment="negative",
        city="Lima",
        tool_used="time",
        tool_result=negative_graph_state.tool_result,  # type: ignore[arg-type]
    )