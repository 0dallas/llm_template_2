"""Tests unitarios para el grafo LangGraph."""
import pytest
from unittest.mock import AsyncMock, patch

from my_genai_app.domain.enums import NodeName, Sentiment
from my_genai_app.graph.edges import sentiment_router
from my_genai_app.graph.state import GraphState


class TestSentimentRouter:
    """Tests del router condicional de sentimiento."""

    def test_routes_positive_to_weather(self):
        """Sentimiento positivo debe enrutar a weather_node."""
        state = GraphState(
            user_message="test",
            sentiment=Sentiment.POSITIVE,
            city="Madrid",
        )
        result = sentiment_router(state)
        assert result == NodeName.WEATHER.value

    def test_routes_negative_to_time(self):
        """Sentimiento negativo debe enrutar a time_node."""
        state = GraphState(
            user_message="test",
            sentiment=Sentiment.NEGATIVE,
            city="Lima",
        )
        result = sentiment_router(state)
        assert result == NodeName.TIME.value

    def test_routes_neutral_to_time(self):
        """Sentimiento neutral debe enrutar a time_node."""
        state = GraphState(
            user_message="test",
            sentiment=Sentiment.NEUTRAL,
            city="Paris",
        )
        result = sentiment_router(state)
        assert result == NodeName.TIME.value

    def test_routes_error_to_end(self):
        """Si hay error, debe enrutar a __end__."""
        state = GraphState(
            user_message="test",
            error="Error en nodo previo",
        )
        result = sentiment_router(state)
        assert result == NodeName.END.value


class TestGraphState:
    """Tests del estado del grafo."""

    def test_initial_state_has_none_fields(self):
        """Estado inicial solo tiene user_message."""
        state = GraphState(user_message="Hola desde Lima")
        assert state.sentiment is None
        assert state.city is None
        assert state.tool_used is None
        assert state.tool_result is None
        assert state.final_message is None
        assert state.error is None

    def test_state_update_sentiment(self):
        """El estado debe actualizarse con el sentimiento."""
        state = GraphState(user_message="test")
        updated = state.model_copy(
            update={"sentiment": Sentiment.POSITIVE, "city": "Madrid"}
        )
        assert updated.sentiment == Sentiment.POSITIVE
        assert updated.city == "Madrid"


class TestGraphBuilder:
    """Tests del builder del grafo."""

    def test_build_graph_returns_compiled_graph(self):
        """build_graph() debe retornar un grafo compilado."""
        from my_genai_app.graph.builder import build_graph

        graph = build_graph()
        assert graph is not None

    def test_build_graph_is_singleton(self):
        """build_graph() debe retornar la misma instancia (singleton)."""
        from my_genai_app.graph.builder import build_graph

        g1 = build_graph()
        g2 = build_graph()
        assert g1 is g2


class TestGraphNodes:
    """Tests de los nodos del grafo."""

    @pytest.mark.asyncio
    @patch("my_genai_app.graph.nodes.SentimentAgent")
    async def test_sentiment_node_success(self, MockSentimentAgent):
        """Nodo de sentimiento debe actualizar estado con sentiment y city."""
        from my_genai_app.graph.nodes import sentiment_node

        # Arrange
        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = {
            "sentiment": Sentiment.POSITIVE,
            "city": "Madrid",
        }
        MockSentimentAgent.return_value = mock_agent_instance

        state = GraphState(user_message="Estoy feliz en Madrid")

        # Act
        result = await sentiment_node(state)

        # Assert
        assert result["sentiment"] == Sentiment.POSITIVE
        assert result["city"] == "Madrid"
        assert "error" not in result or result.get("error") is None

    @pytest.mark.asyncio
    @patch("my_genai_app.graph.nodes.SentimentAgent")
    async def test_sentiment_node_error_captured(self, MockSentimentAgent):
        """Errores en el nodo de sentimiento deben capturarse en el estado."""
        from my_genai_app.graph.nodes import sentiment_node
        from my_genai_app.domain.exceptions import SentimentDetectionError

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.side_effect = SentimentDetectionError("Error de prueba")
        MockSentimentAgent.return_value = mock_agent_instance

        state = GraphState(user_message="Mensaje inválido")

        result = await sentiment_node(state)

        assert result["error"] == "Error de prueba"

    @pytest.mark.asyncio
    @patch("my_genai_app.graph.nodes.WeatherAgent")
    async def test_weather_node_success(self, MockWeatherAgent):
        """Nodo de clima debe actualizar estado con tool_used y final_message."""
        from my_genai_app.graph.nodes import weather_node

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = {
            "final_message": "Madrid tiene 28°C soleado",
            "tool_result": "Soleado, 28°C",
        }
        MockWeatherAgent.return_value = mock_agent_instance

        state = GraphState(
            user_message="Feliz en Madrid",
            sentiment=Sentiment.POSITIVE,
            city="Madrid",
        )

        result = await weather_node(state)

        assert result["tool_used"] == "weather"
        assert result["final_message"] == "Madrid tiene 28°C soleado"

    @pytest.mark.asyncio
    @patch("my_genai_app.graph.nodes.TimeAgent")
    async def test_time_node_success(self, MockTimeAgent):
        """Nodo de hora debe actualizar estado con tool_used y final_message."""
        from my_genai_app.graph.nodes import time_node

        mock_agent_instance = AsyncMock()
        mock_agent_instance.run.return_value = {
            "final_message": "En Lima son las 04:56 PM. ¡Ánimo!",
            "tool_result": "04:56 PM (America/Lima)",
        }
        MockTimeAgent.return_value = mock_agent_instance

        state = GraphState(
            user_message="Triste en Lima",
            sentiment=Sentiment.NEGATIVE,
            city="Lima",
        )

        result = await time_node(state)

        assert result["tool_used"] == "time"
        assert "Lima" in result["final_message"]