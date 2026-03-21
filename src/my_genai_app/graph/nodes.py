"""
Nodos del grafo LangGraph.
Cada función representa un nodo que transforma el estado.
"""
import structlog

from my_genai_app.agents import SentimentAgent, TimeAgent, WeatherAgent
from my_genai_app.domain.enums import Sentiment
from my_genai_app.domain.exceptions import GenAIAppException

from .state import GraphState

logger = structlog.get_logger(__name__)


async def sentiment_node(state: GraphState) -> dict:
    """
    Nodo 1: Detecta el sentimiento y extrae la ciudad del mensaje.
    Actualiza: sentiment, city (o error).
    """
    log = logger.bind(node="sentiment_node", message=state.user_message)
    log.info("Ejecutando nodo de sentimiento")

    try:
        agent = SentimentAgent()
        result = await agent.run(state.user_message)
        log.info(
            "Sentimiento detectado",
            sentiment=result["sentiment"].value,
            city=result["city"],
        )
        return {
            "sentiment": result["sentiment"],
            "city": result["city"],
        }
    except GenAIAppException as e:
        log.error("Error en sentiment_node", error=str(e))
        return {"error": str(e), "sentiment": Sentiment.NEUTRAL}


async def weather_node(state: GraphState) -> dict:
    """
    Nodo 2a: Para sentimientos positivos.
    Obtiene el clima de la ciudad y genera respuesta.
    Actualiza: tool_used, tool_result, final_message (o error).
    """
    log = logger.bind(node="weather_node", city=state.city)
    log.info("Ejecutando nodo de clima")

    try:
        agent = WeatherAgent()
        result = await agent.run(
            original_message=state.user_message,
            city=state.city or "desconocida",
        )
        return {
            "tool_used": "weather",
            "tool_result": result["tool_result"],
            "final_message": result["final_message"],
        }
    except GenAIAppException as e:
        log.error("Error en weather_node", error=str(e))
        return {"error": str(e)}


async def time_node(state: GraphState) -> dict:
    """
    Nodo 2b: Para sentimientos negativos.
    Obtiene la hora de la ciudad y genera respuesta.
    Actualiza: tool_used, tool_result, final_message (o error).
    """
    log = logger.bind(node="time_node", city=state.city)
    log.info("Ejecutando nodo de hora")

    try:
        agent = TimeAgent()
        result = await agent.run(
            original_message=state.user_message,
            city=state.city or "desconocida",
        )
        return {
            "tool_used": "time",
            "tool_result": result["tool_result"],
            "final_message": result["final_message"],
        }
    except GenAIAppException as e:
        log.error("Error en time_node", error=str(e))
        return {"error": str(e)}