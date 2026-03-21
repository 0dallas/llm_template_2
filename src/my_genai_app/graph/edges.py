"""
Edges (aristas condicionales) del grafo LangGraph.
Implementan el Router que decide hacia qué nodo ir.
"""
import structlog

from my_genai_app.domain.enums import NodeName, Sentiment

from .state import GraphState

logger = structlog.get_logger(__name__)


def sentiment_router(state: GraphState) -> str:
    """
    Router condicional que decide el siguiente nodo
    basándose en el sentimiento detectado.

    - POSITIVE  → weather_node
    - NEGATIVE  → time_node
    - NEUTRAL   → time_node  (decisión de diseño: tratar neutral como negativo)
    - error     → __end__

    Returns:
        Nombre del siguiente nodo como string.
    """
    log = logger.bind(
        router="sentiment_router",
        sentiment=state.sentiment,
        error=state.error,
    )

    # Si hay error en el nodo anterior, terminar
    if state.error:
        log.warning("Error detectado, terminando grafo")
        return NodeName.END.value

    sentiment = state.sentiment

    if sentiment == Sentiment.POSITIVE:
        log.info("Enrutando a weather_node (sentimiento positivo)")
        return NodeName.WEATHER.value

    # NEGATIVE o NEUTRAL → time_node
    log.info(
        "Enrutando a time_node",
        reason="sentimiento negativo o neutral",
    )
    return NodeName.TIME.value