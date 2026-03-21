"""
Agente que usa la herramienta extraer_hora para obtener la hora
de una ciudad y genera una respuesta empática para sentimientos negativos.
"""
from langchain_core.prompts import ChatPromptTemplate

from my_genai_app.tools import extraer_hora

from .base import BaseAgent, _invoke_with_retry


class TimeAgent(BaseAgent):
    """
    Agente de hora para sentimientos negativos.
    Invoca la herramienta extraer_hora y genera una respuesta comprensiva.
    """

    _SYSTEM_PROMPT = """
Eres un asistente empático y comprensivo.
El usuario está sintiendo algo negativo en una ciudad.
Usa los datos de hora para contextualizar tu respuesta.
El mensaje debe:
- Mostrar empatía y comprensión hacia el estado emocional del usuario
- Mencionar la ciudad y la hora local de forma natural
- Ofrecer un pequeño mensaje de aliento
- Ser en español
- Ser conciso (máximo 2 oraciones)
"""

    def __init__(self) -> None:
        super().__init__()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._SYSTEM_PROMPT),
                (
                    "human",
                    (
                        "El usuario dice: '{original_message}'. "
                        "Ciudad: {city}. "
                        "Hora local actual: {tool_result}. "
                        "Genera el mensaje final."
                    ),
                ),
            ]
        )

    async def run(  # type: ignore[override]
        self,
        original_message: str,
        city: str,
    ) -> dict:
        """
        Ejecuta el agente de hora.

        Returns:
            dict con keys: final_message (str), tool_result (str)
        """
        self._logger.info("Ejecutando TimeAgent", city=city)

        # 1. Obtener hora con la herramienta
        tool_result = extraer_hora.invoke({"city": city})  # type: ignore[attr-defined]
        self._logger.debug("Hora obtenida", result=tool_result)

        # 2. Generar respuesta final con el LLM
        chain = self._prompt | self._llm
        final_response = await _invoke_with_retry(
            chain,
            {
                "original_message": original_message,
                "city": city,
                "tool_result": tool_result,
            },
        )

        final_message = final_response.content  # type: ignore[attr-defined]
        self._logger.info("TimeAgent completado", final_message=final_message)

        return {
            "final_message": final_message,
            "tool_result": tool_result,
        }