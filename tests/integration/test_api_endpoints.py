"""
Tests de integración para los endpoints de la API.
Mockean los servicios externos (LLM, APIs) pero prueban el flujo completo HTTP.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from my_genai_app.api.dependencies import get_agent_service
from my_genai_app.api.main import create_app
from my_genai_app.domain.models import AgentResponse


# ── Fixtures específicos de integración ──────────────────────────────────────
@pytest.fixture(scope="module")
def integration_app():
    """App de FastAPI para tests de integración."""
    return create_app()


@pytest.fixture(scope="module")
def integration_client(integration_app):
    with TestClient(integration_app) as c:
        yield c


# ── Tests de Health ───────────────────────────────────────────────────────────
class TestHealthEndpoints:
    """Tests de los endpoints de health."""

    def test_health_check_returns_200(self, integration_client):
        response = integration_client.get("/health")
        assert response.status_code == 200

    def test_health_check_response_structure(self, integration_client):
        response = integration_client.get("/health")
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "version" in data
        assert data["status"] == "ok"

    def test_health_check_environment_is_test(self, integration_client):
        response = integration_client.get("/health")
        data = response.json()
        assert data["environment"] == "test"

    def test_readiness_check_returns_200(self, integration_client):
        response = integration_client.get("/health/ready")
        assert response.status_code == 200

    def test_liveness_check_returns_200(self, integration_client):
        response = integration_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


# ── Tests del endpoint /agent ─────────────────────────────────────────────────
class TestAgentEndpoint:
    """Tests del endpoint POST /api/v1/agent."""

    def _mock_service(self, app, mock_response: AgentResponse):
        """Helper para inyectar un servicio mockeado."""
        mock_service = AsyncMock()
        mock_service.process.return_value = mock_response
        app.dependency_overrides[get_agent_service] = lambda: mock_service
        return mock_service

    def test_agent_endpoint_positive_sentiment(
        self,
        integration_app,
        integration_client,
        mock_agent_response_positive,
    ):
        """Request positivo debe retornar respuesta de clima."""
        self._mock_service(integration_app, mock_agent_response_positive)

        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "Estoy muy feliz en Madrid"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "positive"
        assert data["city"] == "Madrid"
        assert data["tool_used"] == "weather"
        assert "message" in data

        # Limpiar override
        integration_app.dependency_overrides.clear()

    def test_agent_endpoint_negative_sentiment(
        self,
        integration_app,
        integration_client,
        mock_agent_response_negative,
    ):
        """Request negativo debe retornar respuesta de hora."""
        self._mock_service(integration_app, mock_agent_response_negative)

        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "Estoy muy triste en Lima"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sentiment"] == "negative"
        assert data["city"] == "Lima"
        assert data["tool_used"] == "time"

        integration_app.dependency_overrides.clear()

    def test_agent_endpoint_empty_message_returns_422(self, integration_client):
        """Mensaje vacío debe retornar 422 Unprocessable Entity."""
        response = integration_client.post(
            "/api/v1/agent",
            json={"message": ""},
        )
        assert response.status_code == 422

    def test_agent_endpoint_missing_message_returns_422(self, integration_client):
        """Request sin campo 'message' debe retornar 422."""
        response = integration_client.post(
            "/api/v1/agent",
            json={},
        )
        assert response.status_code == 422

    def test_agent_endpoint_message_too_long_returns_422(self, integration_client):
        """Mensaje mayor a 500 chars debe retornar 422."""
        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "a" * 501},
        )
        assert response.status_code == 422

    def test_agent_endpoint_graph_error_returns_500(
        self,
        integration_app,
        integration_client,
    ):
        """Error en el grafo debe retornar 500."""
        from my_genai_app.domain.exceptions import GraphExecutionError

        mock_service = AsyncMock()
        mock_service.process.side_effect = GraphExecutionError("Error del grafo")
        integration_app.dependency_overrides[get_agent_service] = lambda: mock_service

        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "Estoy feliz en Madrid"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

        integration_app.dependency_overrides.clear()

    def test_response_has_request_id_header(
        self,
        integration_app,
        integration_client,
        mock_agent_response_positive,
    ):
        """La respuesta debe tener el header X-Request-ID."""
        self._mock_service(integration_app, mock_agent_response_positive)

        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "Estoy feliz en Madrid"},
        )

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) == 36  # UUID format

        integration_app.dependency_overrides.clear()

    def test_response_has_process_time_header(
        self,
        integration_app,
        integration_client,
        mock_agent_response_positive,
    ):
        """La respuesta debe tener el header X-Process-Time-Ms."""
        self._mock_service(integration_app, mock_agent_response_positive)

        response = integration_client.post(
            "/api/v1/agent",
            json={"message": "Estoy feliz en Madrid"},
        )

        assert "x-process-time-ms" in response.headers

        integration_app.dependency_overrides.clear()