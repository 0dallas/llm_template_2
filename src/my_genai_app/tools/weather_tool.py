"""
Herramienta para obtener el clima de una ciudad.
Usa la API de OpenWeatherMap.
"""
import structlog
from langchain_core.tools import tool
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from my_genai_app.config import get_settings
from my_genai_app.domain.exceptions import WeatherToolError

import requests

logger = structlog.get_logger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException),
    reraise=False,
)
def _fetch_weather(city: str) -> dict:
    """Llamada HTTP a OpenWeatherMap con reintentos automáticos."""
    settings = get_settings()
    params = {
        "q": city,
        "appid": settings.openweather_api_key.get_secret_value(),
        "units": settings.openweather_units,
        "lang": settings.openweather_lang,
    }
    response = requests.get(
        f"{settings.openweather_base_url}/weather",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


@tool
def extraer_clima(city: str) -> str:
    """
    Extrae el clima actual de una ciudad.

    Args:
        city: Nombre de la ciudad (ejemplo: 'Madrid', 'Lima', 'Buenos Aires').

    Returns:
        Descripción del clima en formato legible.
    """
    log = logger.bind(tool="extraer_clima", city=city)
    log.info("Llamando a herramienta extraer_clima")

    try:
        data = _fetch_weather(city)

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        description = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (
            f"{description}, {temp}°C "
            f"(sensación térmica {feels_like}°C), "
            f"humedad {humidity}%, "
            f"viento {wind_speed} m/s"
        )

        log.info("Clima obtenido exitosamente", result=result)
        return result

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            error_msg = f"Ciudad '{city}' no encontrada en OpenWeatherMap"
        else:
            error_msg = f"Error HTTP al obtener clima de '{city}': {e}"
        log.error("Error al obtener clima", error=error_msg)
        raise WeatherToolError(error_msg) from e

    except RetryError as e:
        error_msg = f"Reintentos agotados al obtener clima de '{city}'"
        log.error(error_msg)
        raise WeatherToolError(error_msg) from e

    except (KeyError, ValueError) as e:
        error_msg = f"Error al parsear respuesta del clima para '{city}': {e}"
        log.error(error_msg)
        raise WeatherToolError(error_msg) from e