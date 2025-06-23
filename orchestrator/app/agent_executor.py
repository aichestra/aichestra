"""
Orchestrator Agent Executor
"""
import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from app.orchestrator import SmartOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrchestratorAgentExecutor(AgentExecutor):
    """Orchestrator Agent Executor for intelligent request routing"""

    def __init__(self):
        logger.info("Initializing OrchestratorAgentExecutor...")
        self.orchestrator = SmartOrchestrator()
        logger.info(f"Orchestrator initialized with agents: {list(self.orchestrator.agents.keys())}")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        logger.info(f"Processing query: {query}")
        logger.info(f"Available agents: {list(self.orchestrator.agents.keys())}")
        
        task = context.current_task
        if not task:
            if context.message:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            else:
                raise ServerError(error=InvalidParamsError())
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Check if this is a list agents request
            if query.strip() == "LIST_AGENTS":
                logger.info("Listing available agents")
                
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        "Retrieving available agents...",
                        task.contextId,
                        task.id,
                    ),
                )
                
                # Get available agents
                agents = self.orchestrator.get_available_agents()
                logger.info(f"Available agents: {len(agents)}")
                
                # Format as JSON for the client
                import json
                response_text = json.dumps({
                    "type": "agent_list",
                    "agents": agents,
                    "total_count": len(agents)
                }, indent=2)
                
            else:
                # Process the request through the orchestrator
                result = await self.orchestrator.process_request(query)
                logger.info(f"Orchestrator result: {result}")
                
                # Update task status
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        "Processing request through orchestrator...",
                        task.contextId,
                        task.id,
                    ),
                )
                
                # Format the response
                if result.get("success", False):
                    response_text = f"✅ Routed to {result.get('selected_agent_name', 'Unknown Agent')}\n"
                    response_text += f"Confidence: {result.get('confidence', 0):.2f}\n"
                    response_text += f"Reasoning: {result.get('reasoning', 'No reasoning provided')}\n"
                    response_text += f"Response: {result.get('response', 'No response')}"
                else:
                    response_text = f"❌ Error: {result.get('error', 'Unknown error')}"
                    logger.error(f"Orchestrator error: {result.get('error', 'Unknown error')}")
            
            # Complete the task
            await updater.add_artifact(
                [Part(root=TextPart(text=response_text))],
                name='orchestrator_result',
            )
            await updater.complete()

        except Exception as e:
            logger.error(f'An error occurred while processing orchestrator request: {e}')
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError()) 