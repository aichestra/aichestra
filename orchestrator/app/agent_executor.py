"""
Orchestrator Agent Executor
"""
import logging
import re

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

# Support three major features:
# 1. List available agents: LIST_AGENTS
# 2. Register an agent: REGISTER_AGENT:<agent_url>
# 3. Process a request through the orchestrator: <request>

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
                # Auto-detect if this might be a multi-agent request
                logger.info("Analyzing request for multi-agent requirements...")
                
                # Try multi-agent workflow first if we detect potential complexity
                needs_multi_agent = self._detect_multi_agent_need(query)
                
                if needs_multi_agent:
                    logger.info("Request detected as potentially requiring multi-agent collaboration")
                    
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            "Analyzing request for multi-agent collaboration...",
                            task.contextId,
                            task.id,
                        ),
                    )
                    
                    # Try multi-agent workflow
                    result = await self.orchestrator.process_multi_agent_request(query)
                    logger.info(f"Multi-agent analysis result: {result}")
                    
                    # If multi-agent workflow succeeded and found multiple steps, use it
                    if (result.get("success", False) and 
                        result.get("execution_type") == "multi" and 
                        len(result.get("execution_plan", [])) > 1):
                        
                        logger.info("Using multi-agent workflow")
                        response_text = f"🤝 Multi-Agent Collaboration (Auto-detected)\n"
                        response_text += f"Confidence: {result.get('confidence', 0):.2f}\n"
                        response_text += f"Reasoning: {result.get('reasoning', 'No reasoning provided')}\n"
                        response_text += f"Response: {result.get('response', 'No response')}"
                    else:
                        # Fall back to single-agent routing
                        logger.info("Falling back to single-agent routing")
                        result = await self.orchestrator.process_request(query)
                        logger.info(f"Single-agent fallback result: {result}")
                        
                        if result.get("success", False):
                            response_text = f"✅ Routed to {result.get('selected_agent_name', 'Unknown Agent')}\n"
                            response_text += f"Confidence: {result.get('confidence', 0):.2f}\n"
                            response_text += f"Reasoning: {result.get('reasoning', 'No reasoning provided')}\n"
                            response_text += f"Response: {result.get('response', 'No response')}"
                        else:
                            response_text = f"❌ Error: {result.get('error', 'Unknown error')}"
                            logger.error(f"Orchestrator error: {result.get('error', 'Unknown error')}")
                else:
                    # Process through standard single-agent orchestrator
                    logger.info("Using single-agent routing")
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

    def _detect_multi_agent_need(self, query: str) -> bool:
        """Detect if a query might need multi-agent collaboration using dynamic agent capabilities"""
        query_lower = query.lower()
        
        # Get all available capabilities from the orchestrator
        capability_registry = self.orchestrator.capability_registry
        
        if not capability_registry or len(self.orchestrator.agents) < 2:
            # Need at least 2 agents for multi-agent collaboration
            return False
        
        # Group capabilities by agent to identify distinct agent domains
        agent_capabilities = {}
        for capability, agent_ids in capability_registry.items():
            for agent_id in agent_ids:
                if agent_id not in agent_capabilities:
                    agent_capabilities[agent_id] = set()
                agent_capabilities[agent_id].add(capability)
        
        # Score each agent based on how well their capabilities match the query
        agent_scores = {}
        matching_agents = []
        
        for agent_id, capabilities in agent_capabilities.items():
            score = 0
            matches = []
            
            for capability in capabilities:
                if capability in query_lower:
                    score += 2.0  # Direct match
                    matches.append(capability)
                else:
                    # Check for partial matches
                    capability_words = capability.split()
                    for word in capability_words:
                        if len(word) > 2 and word in query_lower:
                            score += 1.0
                            matches.append(word)
            
            if score > 0:
                agent_scores[agent_id] = score
                matching_agents.append((agent_id, score, matches))
        
        # Sort agents by relevance score
        matching_agents.sort(key=lambda x: x[1], reverse=True)
        
        # Check if multiple agents have significant relevance to the query
        # Use a more discriminating approach - need substantial score difference
        if len(matching_agents) >= 2:
            top_score = matching_agents[0][1]
            second_score = matching_agents[1][1]
            
            # Only consider multi-agent if:
            # 1. Multiple agents have substantial scores (>= 2.0)
            # 2. AND the scores are relatively close (within 2x of each other)
            # This prevents weak matches from triggering multi-agent mode
            substantial_agents = [agent for agent, score, matches in matching_agents if score >= 2.0]
            
            if len(substantial_agents) > 1 and second_score >= (top_score * 0.5):
                logger.info(f"Multiple agents with substantial relevance detected: {[agent for agent in substantial_agents]}")
                logger.info(f"Agent scores: {[(agent, score) for agent, score, _ in matching_agents[:3]]}")
                return True
            else:
                logger.info(f"Single dominant agent detected. Top score: {top_score}, Second: {second_score}")
                return False
        
        # Look for generic connecting words that suggest multi-step operations
        multi_step_indicators = [
            'and then', 'then', 'after', 'followed by', 'next',
            'and also', 'plus', 'combined with', 'together with', 'and'
        ]
        has_connectors = any(indicator in query_lower for indicator in multi_step_indicators)
        
        # If we have connectors and at least one matching agent, might be multi-step
        if has_connectors and len(matching_agents) > 0:
            logger.info(f"Multi-step indicators found with {len(matching_agents)} relevant agents")
            return True
        
        # Check for mathematical operators combined with other capabilities
        # This is the only non-generic check, but it's for a very common pattern
        math_operators = ['+', '-', '*', '/', '=']
        has_math_ops = any(op in query_lower for op in math_operators)
        
        if has_math_ops and len(matching_agents) > 1:
            logger.info(f"Mathematical operators found with multiple relevant agents")
            return True
        
        # Check if the query has multiple distinct concepts that might map to different agents
        query_words = set(query_lower.split())
        agent_specific_words = {}
        
        for agent_id, capabilities in agent_capabilities.items():
            agent_words = set()
            for capability in capabilities:
                agent_words.update(capability.split())
            
            # Count how many query words match this agent's capability words
            common_words = query_words.intersection(agent_words)
            if common_words:
                agent_specific_words[agent_id] = common_words
        
        # If multiple agents have unique word matches, likely multi-agent
        agents_with_matches = len(agent_specific_words)
        if agents_with_matches > 1:
            logger.info(f"Query words match {agents_with_matches} different agent domains")
            logger.info(f"Agent word matches: {agent_specific_words}")
            return True
        
        logger.info(f"Single-agent request detected. Best match: {matching_agents[0] if matching_agents else 'none'}")
        return False

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError()) 