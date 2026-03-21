"""
Estado del grafo LangGraph.
Actúa como la 'memoria' que se pasa entre nodos.
"""
from typing import Optional

from pydantic import BaseModel, Field

from my_genai_app.domain.enums import Sentiment


class GraphState(BaseModel):
    """
    Estado compartido entre todos los nodos del grafo.
    Cada nodo puede leer y actualizar este estado.

    Implementa el patrón State Machine de LangGraph.
    """

    # Input
    user_message: str = Field(..., description="Mensaje original del usuario")

    # Resultado del nodo de sentimiento
    sentiment: Optional[Sentiment] = Field(
        default=None,
        description="Sentimiento detectado: positive | negative | neutral",
    )
    city: Optional[str] = Field(
        default=None,
        description="Ciudad extraída del mensaje",
    )

    # Resultado del nodo de herramienta (weather o time)
    tool_used: Optional[str] = Field(
        default=None,
        description="Nombre de la herramienta usada: weather | time",
    )
    tool_result: Optional[str] = Field(
        default=None,
        description="Resultado de la herramienta",
    )

    # Respuesta final
    final_message: Optional[str] = Field(
        default=None,
        description="Mensaje final para el usuario",
    )

    # Control de errores
    error: Optional[str] = Field(
        default=None,
        description="Mensaje de error si algo falló",
    )