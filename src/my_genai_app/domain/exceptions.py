"""Excepciones personalizadas del dominio."""


class GenAIAppException(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SentimentDetectionError(GenAIAppException):
    """Error al detectar el sentimiento."""

    def __init__(self, message: str = "No se pudo detectar el sentimiento") -> None:
        super().__init__(message, status_code=422)


class CityExtractionError(GenAIAppException):
    """Error al extraer la ciudad del mensaje."""

    def __init__(self, message: str = "No se pudo extraer la ciudad del mensaje") -> None:
        super().__init__(message, status_code=422)


class WeatherToolError(GenAIAppException):
    """Error al obtener el clima."""

    def __init__(self, message: str = "Error al obtener datos del clima") -> None:
        super().__init__(message, status_code=502)


class TimeToolError(GenAIAppException):
    """Error al obtener la hora."""

    def __init__(self, message: str = "Error al obtener la hora de la ciudad") -> None:
        super().__init__(message, status_code=502)


class LLMCallError(GenAIAppException):
    """Error al llamar al LLM."""

    def __init__(self, message: str = "Error al comunicarse con el LLM") -> None:
        super().__init__(message, status_code=502)


class GraphExecutionError(GenAIAppException):
    """Error durante la ejecución del grafo LangGraph."""

    def __init__(self, message: str = "Error en la ejecución del grafo") -> None:
        super().__init__(message, status_code=500)