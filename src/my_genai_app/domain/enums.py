"""Enumeraciones del dominio."""
from enum import Enum


class Sentiment(str, Enum):
    """Sentimientos que el agente puede detectar."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"  # Por defecto si no se puede determinar


class NodeName(str, Enum):
    """Nombres de los nodos del grafo LangGraph."""
    SENTIMENT = "sentiment_node"
    WEATHER = "weather_node"
    TIME = "time_node"
    FINAL_RESPONSE = "final_response_node"
    END = "__end__"