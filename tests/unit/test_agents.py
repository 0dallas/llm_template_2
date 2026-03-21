"""Tests unitarios para los agentes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from my_genai_app.domain.enums import Sentiment
from my_genai_app.domain.exceptions import (
    CityExtractionError,
    SentimentDetectionError,
)


class TestSentimentAgent:
    """Tests del agente de sentimiento."""

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.sentiment_agent._invoke_with_retry")
    async def test_positive_sentiment_detection(self, mock_invoke):
        """Debe detectar sentimiento positivo y extraer ciudad."""
        from my_genai_app.agents.sentiment_agent import SentimentAgent

        # Arrange
        mock_invoke.return_value = {"sentiment": "positive", "city": "Madrid"}
        agent = SentimentAgent()

        # Act
        result = await agent.run("Estoy muy feliz en Madrid")

        # Assert
        assert result["sentiment"] == Sentiment.POSITIVE
        assert result["city"] == "Madrid"

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.sentiment_agent._invoke_with_retry")
    async def test_negative_sentiment_detection(self, mock_invoke):
        """Debe detectar sentimiento negativo y extraer ciudad."""
        from my_genai_app.agents.sentiment_agent import SentimentAgent

        mock_invoke.return_value = {"sentiment": "negative", "city": "Lima"}
        agent = SentimentAgent()

        result = await agent.run("Estoy muy triste en Lima")

        assert result["sentiment"] == Sentiment.NEGATIVE
        assert result["city"] == "Lima"

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.sentiment_agent._invoke_with_retry")
    async def test_unknown_city_raises_error(self, mock_invoke):
        """Sin ciudad en el mensaje debe lanzar CityExtractionError."""
        from my_genai_app.agents.sentiment_agent import SentimentAgent

        mock_invoke.return_value = {"sentiment": "positive", "city": "unknown"}
        agent = SentimentAgent()

        with pytest.raises(CityExtractionError):
            await agent.run("Estoy muy feliz hoy")

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.sentiment_agent._invoke_with_retry")
    async def test_invalid_llm_response_raises_error(self, mock_invoke):
        """Respuesta inválida del LLM debe lanzar SentimentDetectionError."""
        from my_genai_app.agents.sentiment_agent import SentimentAgent

        mock_invoke.return_value = "esto no es un dict"
        agent = SentimentAgent()

        with pytest.raises(SentimentDetectionError):
            await agent.run("Mensaje cualquiera")

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.sentiment_agent._invoke_with_retry")
    async def test_unrecognized_sentiment_defaults_to_neutral(self, mock_invoke):
        """Sentimiento no reconocido debe defaultear a NEUTRAL."""
        from my_genai_app.agents.sentiment_agent import SentimentAgent

        mock_invoke.return_value = {"sentiment": "confused", "city": "Paris"}
        agent = SentimentAgent()

        result = await agent.run("Me siento raro en Paris")

        assert result["sentiment"] == Sentiment.NEUTRAL
        assert result["city"] == "Paris"


class TestWeatherAgent:
    """Tests del agente de clima."""

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.weather_agent._invoke_with_retry")
    @patch("my_genai_app.tools.weather_tool.extraer_clima")
    async def test_weather_agent_success(self, mock_tool, mock_invoke):
        """Debe retornar mensaje final con datos del clima."""
        from my_genai_app.agents.weather_agent import WeatherAgent

        # Arrange
        mock_tool.invoke.return_value = "Soleado, 30°C"
        mock_response = MagicMock()
        mock_response.content = "¡Qué bueno que estés feliz en Madrid! Tiene un clima soleado de 30°C."
        mock_invoke.return_value = mock_response

        agent = WeatherAgent()

        # Act
        result = await agent.run(
            original_message="Estoy feliz en Madrid",
            city="Madrid",
        )

        # Assert
        assert "final_message" in result
        assert "tool_result" in result


class TestTimeAgent:
    """Tests del agente de hora."""

    @pytest.mark.asyncio
    @patch("my_genai_app.agents.time_agent._invoke_with_retry")
    @patch("my_genai_app.tools.time_tool.extraer_hora")
    async def test_time_agent_success(self, mock_tool, mock_invoke):
        """Debe retornar mensaje final con la hora local."""
        from my_genai_app.agents.time_agent import TimeAgent

        # Arrange
        mock_tool.invoke.return_value = "04:56 PM (15/01/2025, America/Lima)"
        mock_response = MagicMock()
        mock_response.content = "Entiendo que estés triste en Lima, donde son las 04:56 PM. ¡Ánimo!"
        mock_invoke.return_value = mock_response

        agent = TimeAgent()

        # Act
        result = await agent.run(
            original_message="Estoy triste en Lima",
            city="Lima",
        )

        # Assert
        assert "final_message" in result
        assert "tool_result" in result