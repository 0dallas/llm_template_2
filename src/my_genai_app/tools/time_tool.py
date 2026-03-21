"""
Herramienta para obtener la hora actual de una ciudad.
Usa geopy para geolocalizar la ciudad y timezonefinder + pytz para la hora.
"""
from datetime import datetime

import pytz
import structlog
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from langchain_core.tools import tool
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from timezonefinder import TimezoneFinder

from my_genai_app.domain.exceptions import TimeToolError

logger = structlog.get_logger(__name__)

# Instancias reutilizables (Nominatim requiere un user_agent)
_geocoder = Nominatim(user_agent="my_genai_app_v1")
_timezone_finder = TimezoneFinder()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((GeocoderTimedOut, GeocoderUnavailable)),
    reraise=True,
)
def _geolocate(city: str):  # type: ignore[return]
    """Geolocaliza una ciudad con reintentos automáticos."""
    return _geocoder.geocode(city, language="es", timeout=10)


@tool
def extraer_hora(city: str) -> str:
    """
    Extrae la hora actual de una ciudad.

    Args:
        city: Nombre de la ciudad (ejemplo: 'Lima', 'Madrid', 'Tokio').

    Returns:
        Hora actual de la ciudad en formato legible.
    """
    log = logger.bind(tool="extraer_hora", city=city)
    log.info("Llamando a herramienta extraer_hora")

    try:
        # 1. Geolocalizar la ciudad
        location = _geolocate(city)
        if location is None:
            raise TimeToolError(f"Ciudad '{city}' no encontrada")

        lat, lon = location.latitude, location.longitude
        log.debug("Coordenadas obtenidas", lat=lat, lon=lon)

        # 2. Obtener timezone
        tz_name = _timezone_finder.timezone_at(lat=lat, lng=lon)
        if tz_name is None:
            raise TimeToolError(f"No se encontró timezone para '{city}'")

        # 3. Calcular hora actual
        tz = pytz.timezone(tz_name)
        current_time = datetime.now(tz)
        formatted_time = current_time.strftime("%I:%M %p")  # 04:56 PM
        formatted_date = current_time.strftime("%d/%m/%Y")

        result = f"{formatted_time} ({formatted_date}, {tz_name})"

        log.info("Hora obtenida exitosamente", result=result)
        return result

    except TimeToolError:
        raise

    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        error_msg = f"Reintentos agotados al geolocalizar '{city}'"
        log.error(error_msg, error=str(e))
        raise TimeToolError(error_msg) from e

    except Exception as e:
        error_msg = f"Error inesperado al obtener hora de '{city}': {e}"
        log.error(error_msg)
        raise TimeToolError(error_msg) from e