"""
Servicio principal que orquesta la ejecución del grafo.
Es la única entrada desde la capa API hacia la lógica de negocio.
Implementa el patrón Facade.
"""
import structlog

from my_genai_app.domain.exceptions import GraphExecutionError
from my_genai_app.domain.models import AgentRequest, AgentResponse
from my_genai_app.graph import GraphState, build_graph

logger = structlog.get_logger(__name__)


class AgentService:
    """
    Orquesta la ejecución del grafo LangGraph.
    La API llama a este servicio; este servicio conoce el grafo.
    """

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Procesa el mensaje del usuario a través del grafo LangGraph.

        Args:
            request: AgentRequest con el mensaje del usuario.

        Returns:
            AgentResponse con el resultado final.

        Raises:
            GraphExecutionError: Si la ejecución del grafo falla.
        """
        log = logger.bind(service="AgentService", message=request.message)
        log.info("Iniciando procesamiento del mensaje")

        try:
            # 1. Construir estado inicial
            initial_state = GraphState(user_message=request.message)

            # 2. Obtener grafo compilado (singleton)
            graph = build_graph()

            # 3. Ejecutar el grafo de forma asíncrona
            final_state: GraphState = await graph.ainvoke(initial_state)  # type: ignore[arg-type]

            log.info(
                "Grafo ejecutado exitosamente",
                sentiment=final_state.sentiment,
                city=final_state.city,
                tool_used=final_state.tool_used,
            )

            # 4. Verificar si hubo errores durante la ejecución
            if final_state.error:
                raise GraphExecutionError(final_state.error)

            # 5. Construir respuesta
            return AgentResponse(
                message=final_state.final_message or "No se pudo generar una respuesta.",
                sentiment=final_state.sentiment.value if final_state.sentiment else "unknown",
                city=final_state.city or "unknown",
                tool_used=final_state.tool_used or "unknown",
                tool_result=final_state.tool_result or "unknown",
            )

        except GraphExecutionError:
            raise

        except Exception as e:
            log.exception("Error inesperado en AgentService", error=str(e))
            raise GraphExecutionError(
                f"Error inesperado durante la ejecución del grafo: {e}"
            ) from e