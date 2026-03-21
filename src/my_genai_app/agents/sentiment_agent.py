"""
Agente de análisis de sentimiento.
Detecta si el mensaje del usuario es positivo, negativo o neutral,
y extrae la ciudad mencionada.
"""
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from my_genai_app.domain.enums import Sentiment
from my_genai_app.domain.exceptions import CityExtractionError, SentimentDetectionError

from .base import BaseAgent, _invoke_with_retry


class SentimentAgent(BaseAgent):
    """
    Analiza el sentimiento del mensaje y extrae la ciudad.
    Devuelve un JSON con { sentiment, city }.
    """

    _SYSTEM_PROMPT = """
Eres un analizador de sentimientos y extractor de entidades.
Tu tarea es analizar el mensaje del usuario y devolver un JSON con:
- "sentiment": puede ser "positive", "negative" o "neutral"
- "city": la ciudad mencionada en el mensaje (solo el nombre, sin país)

Reglas:
1. Si el mensaje expresa alegría, felicidad, entusiasmo → "positive"
2. Si el mensaje expresa tristeza, enojo, frustración, miedo → "negative"
3. Si no queda claro → "neutral"
4. Si no hay ciudad, devuelve "city": "unknown"
5. Devuelve ÚNICAMENTE el JSON válido, sin texto adicional, sin markdown.

Ejemplo de respuesta:
{{"sentiment": "positive", "city": "Madrid"}}
"""

    def __init__(self) -> None:
        super().__init__()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._SYSTEM_PROMPT),
                ("human", "{message}"),
            ]
        )
        self._parser = JsonOutputParser()
        self._chain = self._prompt | self._llm | self._parser

    async def run(self, message: str) -> dict:  # type: ignore[override]
        """
        Analiza el mensaje y devuelve sentiment y city.

        Returns:
            dict con keys: sentiment (Sentiment), city (str)
        """
        self._logger.info("Analizando sentimiento", message=message)

        raw = await _invoke_with_retry(self._chain, {"message": message})

        # Validar estructura de respuesta
        if not isinstance(raw, dict):
            raise SentimentDetectionError(
                f"Respuesta inesperada del LLM: {raw}"
            )

        sentiment_raw = raw.get("sentiment", "neutral").lower()
        city = raw.get("city", "unknown")

        # Validar sentimiento
        try:
            sentiment = Sentiment(sentiment_raw)
        except ValueError:
            self._logger.warning(
                "Sentimiento no reconocido, usando neutral",
                raw_sentiment=sentiment_raw,
            )
            sentiment = Sentiment.NEUTRAL

        # Validar ciudad
        if not city or city == "unknown":
            raise CityExtractionError(
                "No se pudo identificar una ciudad en el mensaje."
            )

        self._logger.info(
            "Sentimiento detectado",
            sentiment=sentiment.value,
            city=city,
        )
        return {"sentiment": sentiment, "city": city}