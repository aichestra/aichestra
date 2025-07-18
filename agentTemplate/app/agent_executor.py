"""
Agent Executor
A2A protocol executor for the template agent.
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

from app.agent import TemplateAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateAgentExecutor(AgentExecutor):
    """Template Agent Executor for A2A SDK integration"""

    def __init__(self):
        self.agent = TemplateAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute agent request using A2A protocol"""
        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        task = context.current_task
        if not task:
            if context.message:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            else:
                raise ServerError(error=InvalidParamsError())
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Stream the agent's response
            async for item in self.agent.stream(query, task.contextId):
                is_task_complete = item['is_task_complete']
                require_user_input = item['require_user_input']

                if not is_task_complete and not require_user_input:
                    # Agent is working - update status
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            item['content'],
                            task.contextId,
                            task.id,
                        ),
                    )
                elif require_user_input:
                    # Agent requires user input - set as input_required
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_text_message(
                            item['content'],
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                else:
                    # Task is complete - add result and complete
                    await updater.add_artifact(
                        [Part(root=TextPart(text=item['content']))],
                        name='agent_result',
                    )
                    await updater.complete()
                    break

        except Exception as e:
            logger.error(f'An error occurred while processing request: {e}')
            raise ServerError(error=InternalError()) from e

    def _validate_request(self, context: RequestContext) -> bool:
        """Validate incoming request"""
        # Basic validation - can be extended as needed
        return False

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution"""
        # Template agents don't support cancellation yet
        raise ServerError(error=UnsupportedOperationError())

    async def cleanup(self):
        """Clean up agent resources"""
        try:
            await self.agent.cleanup()
        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")

    def __del__(self):
        """Destructor"""
        # Note: async cleanup should be called explicitly
        pass 