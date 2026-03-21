"""Tests unitarios para las herramientas (tools)."""
import pytest
from unittest.mock import MagicMock, patch

from my_genai_app.domain.exceptions import TimeToolError, WeatherToolError


class TestWeatherTool:
    """Tests de la herramienta extraer_clima."""

    @patch("my_genai_app.tools.weather_tool.requests.get")
    def test_extraer_clima_success(self, mock_get):
        """Debe retornar el clima formateado correctamente."""
        from my_genai_app.tools.weather_tool import extraer_clima

        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "main": {
                "temp": 28.5,
                "feels_like": 30.0,
                "humidity": 45,
            },
            "weather": [{"description": "cielo despejado"}],
            "wind": {"speed": 3.2},
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Act
        result = extraer_clima.invoke({"city": "Madrid"})  # type: ignore[attr-defined]

        # Assert
        assert "28.5°C" in result
        assert "Cielo despejado" in result
        assert "humedad 45%" in result

    @patch("my_genai_app.tools.weather_tool.requests.get")
    def test_extraer_clima_city_not_found(self, mock_get):
        """Ciudad no encontrada debe lanzar WeatherToolError."""
        import requests
        from my_genai_app.tools.weather_tool import extraer_clima

        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = requests.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        # Act & Assert
        with pytest.raises(WeatherToolError, match="no encontrada"):
            extraer_clima.invoke({"city": "CiudadInexistente123"})  # type: ignore[attr-defined]

    @patch("my_genai_app.tools.weather_tool.requests.get")
    def test_extraer_clima_invalid_response_structure(self, mock_get):
        """Respuesta con estructura incorrecta debe lanzar WeatherToolError."""
        from my_genai_app.tools.weather_tool import extraer_clima

        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "structure"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(WeatherToolError):
            extraer_clima.invoke({"city": "Madrid"})  # type: ignore[attr-defined]


class TestTimeTool:
    """Tests de la herramienta extraer_hora."""

    @patch("my_genai_app.tools.time_tool._geolocate")
    @patch("my_genai_app.tools.time_tool._timezone_finder")
    def test_extraer_hora_success(self, mock_tf, mock_geolocate):
        """Debe retornar la hora formateada correctamente."""
        from my_genai_app.tools.time_tool import extraer_hora

        # Arrange
        mock_location = MagicMock()
        mock_location.latitude = -12.0464
        mock_location.longitude = -77.0428
        mock_geolocate.return_value = mock_location
        mock_tf.timezone_at.return_value = "America/Lima"

        # Act
        result = extraer_hora.invoke({"city": "Lima"})  # type: ignore[attr-defined]

        # Assert
        assert "America/Lima" in result
        assert "PM" in result or "AM" in result

    @patch("my_genai_app.tools.time_tool._geolocate")
    def test_extraer_hora_city_not_found(self, mock_geolocate):
        """Ciudad no encontrada debe lanzar TimeToolError."""
        from my_genai_app.tools.time_tool import extraer_hora

        mock_geolocate.return_value = None

        with pytest.raises(TimeToolError, match="no encontrada"):
            extraer_hora.invoke({"city": "CiudadInexistente123"})  # type: ignore[attr-defined]

    @patch("my_genai_app.tools.time_tool._geolocate")
    @patch("my_genai_app.tools.time_tool._timezone_finder")
    def test_extraer_hora_no_timezone(self, mock_tf, mock_geolocate):
        """Sin timezone disponible debe lanzar TimeToolError."""
        from my_genai_app.tools.time_tool import extraer_hora

        mock_location = MagicMock()
        mock_location.latitude = 0.0
        mock_location.longitude = 0.0
        mock_geolocate.return_value = mock_location
        mock_tf.timezone_at.return_value = None

        with pytest.raises(TimeToolError, match="timezone"):
            extraer_hora.invoke({"city": "PuntoMedio"})  # type: ignore[attr-defined]