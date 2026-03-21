"""
Agente que usa la herramienta extraer_clima para obtener el tiempo
de una ciudad y genera una respuesta empática y positiva.
"""
from langchain_core.prompts import ChatPromptTemplate

from my_genai_app.tools import extraer_clima

from .base import BaseAgent, _invoke_with_retry


class WeatherAgent(BaseAgent):
    """
    Agente de clima para sentimientos positivos.
    Invoca la herramienta extraer_clima y genera una respuesta amigable.
    """

    _SYSTEM_PROMPT = """
Eres un asistente amigable y empático.
El usuario está sintiendo algo positivo en una ciudad.
Usa la herramienta 'extraer_clima' para obtener el clima actual de la ciudad.
Luego genera un mensaje cálido que incluya el clima de la ciudad.
El mensaje debe:
- Reflejar el estado positivo del usuario
- Mencionar la ciudad
- Incluir los datos del clima de forma natural
- Ser en español
- Ser conciso (máximo 2 oraciones)
"""

    def __init__(self) -> None:
        super().__init__()
        # Bind de la herramienta al LLM
        self._llm_with_tools = self._llm.bind_tools([extraer_clima])

        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._SYSTEM_PROMPT),
                ("human", "El usuario dice: '{original_message}'. La ciudad es: {city}"),
            ]
        )

    async def run(  # type: ignore[override]
        self,
        original_message: str,
        city: str,
    ) -> dict:
        """
        Ejecuta el agente de clima.

        Returns:
            dict con keys: final_message (str), tool_result (str)
        """
        self._logger.info("Ejecutando WeatherAgent", city=city)

        # 1. Obtener clima directamente con la herramienta
        tool_result = extraer_clima.invoke({"city": city})  # type: ignore[attr-defined]
        self._logger.debug("Clima obtenido", result=tool_result)

        # 2. Generar respuesta final con el LLM
        chain = self._prompt | self._llm
        final_msg = await _invoke_with_retry(
            chain,
            {
                "original_message": original_message,
                "city": city,
                "tool_result": tool_result,
            },
        )

        # Ajustar el prompt del sistema para incluir el resultado de la herramienta
        # Construimos el mensaje final directamente
        refined_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self._SYSTEM_PROMPT),
                (
                    "human",
                    (
                        "El usuario dice: '{original_message}'. "
                        "Ciudad: {city}. "
                        "Clima actual: {tool_result}. "
                        "Genera el mensaje final."
                    ),
                ),
            ]
        )
        refined_chain = refined_prompt | self._llm
        final_response = await _invoke_with_retry(
            refined_chain,
            {
                "original_message": original_message,
                "city": city,
                "tool_result": tool_result,
            },
        )

        final_message = final_response.content  # type: ignore[attr-defined]
        self._logger.info("WeatherAgent completado", final_message=final_message)

        return {
            "final_message": final_message,
            "tool_result": tool_result,
        }