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

# Support four major features:
# 1. List available agents: LIST_AGENTS
# 2. Register an agent: REGISTER_AGENT:<agent_url>
# 3. Unregister an agent: UNREGISTER_AGENT:<agent_id>
# 4. Process a request through the orchestrator: <request>

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
            
            # Check if this is a registration request
            elif query.startswith("REGISTER_AGENT:"):
                endpoint = query.replace("REGISTER_AGENT:", "").strip()
                logger.info(f"Registering agent from endpoint: {endpoint}")
                
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        f"Registering agent from {endpoint}...",
                        task.contextId,
                        task.id,
                    ),
                )
                
                # Register the agent
                result = await self.orchestrator.register_agent(endpoint)
                logger.info(f"Registration result: {result}")
                
                if result.get("success", False):
                    # Log all registered agent details after successful registration
                    logger.info("=" * 80)
                    logger.info("🎉 AGENT REGISTRATION SUCCESSFUL - ALL REGISTERED AGENTS:")
                    logger.info("=" * 80)
                    
                    for agent_id, agent_card in self.orchestrator.agents.items():
                        logger.info(f"Agent ID: {agent_id}")
                        logger.info(f"  Name: {agent_card.name}")
                        logger.info(f"  Endpoint: {agent_card.url}")
                        logger.info(f"  Description: {agent_card.description}")
                        
                        # Log skills if available
                        if agent_card.skills:
                            logger.info(f"  Skills ({len(agent_card.skills)}):")
                            for skill in agent_card.skills:
                                logger.info(f"    • {skill.name}: {skill.description}")
                                if skill.tags:
                                    logger.info(f"      Tags: {', '.join(skill.tags)}")
                        else:
                            logger.info("  Skills: None")
                        
                        # Log capabilities if available
                        capabilities = agent_card.capabilities
                        logger.info(f"  Capabilities:")
                        logger.info(f"    • Streaming: {capabilities.streaming}")
                        logger.info(f"    • Push Notifications: {capabilities.pushNotifications}")
                        logger.info(f"    • State Transition History: {capabilities.stateTransitionHistory}")
                        
                        logger.info("-" * 40)
                    
                    logger.info(f"Total registered agents: {len(self.orchestrator.agents)}")
                    logger.info("=" * 80)
                    
                    response_text = f"✅ {result.get('message')}\n"
                    response_text += f"Agent ID: {result.get('agent_id')}\n"
                    response_text += f"Agent Name: {result.get('agent_name')}\n"
                    response_text += f"Total agents: {len(self.orchestrator.agents)}"
                else:
                    response_text = f"❌ Registration failed: {result.get('error')}"
            
            # Check if this is an unregistration request
            elif query.startswith("UNREGISTER_AGENT:"):
                agent_identifier = query.replace("UNREGISTER_AGENT:", "").strip()
                logger.info(f"Unregistering agent: {agent_identifier}")
                
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(
                        f"Unregistering agent {agent_identifier}...",
                        task.contextId,
                        task.id,
                    ),
                )
                
                # Unregister the agent
                result = await self.orchestrator.unregister_agent(agent_identifier)
                logger.info(f"Unregistration result: {result}")
                
                if result.get("success", False):
                    # Log all registered agent details after successful unregistration
                    logger.info("=" * 80)
                    logger.info("🗑️  AGENT UNREGISTRATION SUCCESSFUL - REMAINING REGISTERED AGENTS:")
                    logger.info("=" * 80)
                    
                    if self.orchestrator.agents:
                        for agent_id, agent_card in self.orchestrator.agents.items():
                            logger.info(f"Agent ID: {agent_id}")
                            logger.info(f"  Name: {agent_card.name}")
                            logger.info(f"  Endpoint: {agent_card.url}")
                            logger.info(f"  Description: {agent_card.description}")
                            logger.info("-" * 40)
                    else:
                        logger.info("No agents remaining in registry")
                    
                    logger.info(f"Total remaining agents: {len(self.orchestrator.agents)}")
                    logger.info("=" * 80)
                    
                    response_text = f"✅ {result.get('message')}\n"
                    response_text += f"Agent ID: {result.get('agent_id')}\n"
                    response_text += f"Remaining agents: {len(self.orchestrator.agents)}"
                else:
                    response_text = f"❌ Unregistration failed: {result.get('error')}"
                
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