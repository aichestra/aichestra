#!/usr/bin/env python3
"""
Orchestrator Agent main application with A2A SDK integration
"""
import logging
import os
import sys

import click
import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

from app.orchestrator import SmartOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_orchestrator_agent_card(host: str, port: int) -> AgentCard:
    """Create the orchestrator agent card"""
    skills = [
        AgentSkill(
            id="request_routing",
            name="Request Routing",
            description="Intelligent request routing to specialized agents",
            tags=["routing", "orchestration"]
        ),
        AgentSkill(
            id="agent_coordination",
            name="Agent Coordination",
            description="Multi-agent system coordination and management",
            tags=["coordination", "management"]
        ),
        AgentSkill(
            id="skill_matching",
            name="Skill Matching",
            description="Skill-based agent selection and matching",
            tags=["matching", "selection"]
        ),
        AgentSkill(
            id="confidence_scoring",
            name="Confidence Scoring",
            description="Confidence scoring for routing decisions",
            tags=["scoring", "confidence"]
        )
    ]
    
    capabilities = AgentCapabilities(
        streaming=False,
        pushNotifications=True,
        stateTransitionHistory=False
    )
    
    return AgentCard(
        name="Smart Orchestrator Agent",
        description="Intelligent agent that routes requests to specialized agents using LangGraph and A2A protocol",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=skills,
        defaultInputModes=["text"],
        defaultOutputModes=["text"]
    )


# Simplified approach - we'll use the orchestrator logic directly in the command-line mode


@click.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
def main(host: str, port: int):
    """Starts the Orchestrator Agent server."""
    try:
        from app.agent_executor import OrchestratorAgentExecutor
        
        agent_card = create_orchestrator_agent_card(host, port)

        # Create the A2A server
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=OrchestratorAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )

        uvicorn.run(server.build(), host=host, port=port)

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == "__main__":
    main() 