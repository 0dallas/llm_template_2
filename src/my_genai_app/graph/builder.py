"""
Constructor del grafo LangGraph.
Patrón Singleton: el grafo se compila una sola vez.
"""
from functools import lru_cache

import structlog
from langgraph.graph import END, StateGraph

from my_genai_app.config import get_settings
from my_genai_app.domain.enums import NodeName

from .edges import sentiment_router
from .nodes import sentiment_node, time_node, weather_node
from .state import GraphState

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def build_graph():
    """
    Construye y compila el grafo LangGraph.
    Singleton via @lru_cache — se compila una sola vez en el ciclo de vida.

    Flujo del grafo (State Machine):
    ┌─────────────┐
    │    START    │
    └──────┬──────┘
           │
    ┌──────▼──────────┐
    │ sentiment_node  │ ← Detecta sentimiento + ciudad
    └──────┬──────────┘
           │
     [sentiment_router]
     ┌─────┴──────┐
     │            │
    POSITIVE    NEGATIVE/NEUTRAL
     │            │
    ┌▼──────┐  ┌──▼──────┐
    │weather│  │  time   │
    │ node  │  │  node   │
    └───┬───┘  └───┬─────┘
        │          │
        └────┬─────┘
             │
           [END]
    """
    settings = get_settings()

    log = logger.bind(component="GraphBuilder")
    log.info("Construyendo grafo LangGraph")

    # 1. Crear el grafo con el tipo de estado
    graph = StateGraph(GraphState)

    # 2. Agregar nodos
    graph.add_node(NodeName.SENTIMENT.value, sentiment_node)
    graph.add_node(NodeName.WEATHER.value, weather_node)
    graph.add_node(NodeName.TIME.value, time_node)

    # 3. Definir el punto de entrada
    graph.set_entry_point(NodeName.SENTIMENT.value)

    # 4. Agregar edge condicional (el router)
    graph.add_conditional_edges(
        source=NodeName.SENTIMENT.value,
        path=sentiment_router,
        path_map={
            NodeName.WEATHER.value: NodeName.WEATHER.value,
            NodeName.TIME.value: NodeName.TIME.value,
            NodeName.END.value: END,
        },
    )

    # 5. Los nodos finales terminan en END
    graph.add_edge(NodeName.WEATHER.value, END)
    graph.add_edge(NodeName.TIME.value, END)

    # 6. Compilar el grafo
    compiled = graph.compile()
    compiled.recursion_limit = settings.langgraph_recursion_limit  # type: ignore[attr-defined]

    log.info("Grafo LangGraph compilado exitosamente")
    return compiled