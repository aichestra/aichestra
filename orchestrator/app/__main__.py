#!/usr/bin/env python3
"""
Orchestrator Agent main application with A2A SDK integration and FastAPI endpoints
"""
import logging
import os
import sys

import click
import httpx
import uvicorn
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.client import A2ACardResolver

from app.orchestrator import SmartOrchestrator
from app.agent_management_api import router as agent_management_router, set_orchestrator

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
        ),
        AgentSkill(
            id="dynamic_agent_discovery",
            name="Dynamic Agent Discovery",
            description="Discover and integrate new agents dynamically",
            tags=["discovery", "integration", "dynamic"]
        ),
        AgentSkill(
            id="semantic_routing",
            name="Semantic Routing",
            description="Route requests based on semantic understanding",
            tags=["semantic", "understanding", "context"]
        ),
        AgentSkill(
            id="agent_management",
            name="Agent Management",
            description="Register, unregister, and list agents via API endpoints",
            tags=["management", "api", "registration"]
        )
    ]
    
    capabilities = AgentCapabilities(
        streaming=False,
        pushNotifications=True,
        stateTransitionHistory=False
    )
    
    return AgentCard(
        name="Smart Orchestrator Agent",
        description="Intelligent agent that routes requests to specialized agents using LangGraph and A2A protocol with FastAPI management endpoints",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=skills,
        defaultInputModes=["text"],
        defaultOutputModes=["text"]
    )


def create_fastapi_app(orchestrator: SmartOrchestrator) -> FastAPI:
    """Create FastAPI application with agent management endpoints"""
    # Set the orchestrator instance for the API endpoints
    set_orchestrator(orchestrator)
    
    # Create FastAPI app
    fastapi_app = FastAPI(
        title="Orchestrator Agent Management API",
        description="API endpoints for managing agents in the orchestrator",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include the agent management router
    fastapi_app.include_router(agent_management_router)
    
    # Add a root endpoint
    @fastapi_app.get("/")
    async def root():
        return {
            "message": "Orchestrator Agent Management API",
            "version": "1.0.0",
            "endpoints": {
                "docs": "/docs",
                "register_agent": "/api/v1/agents/register",
                "unregister_agent": "/api/v1/agents/unregister", 
                "list_agents": "/api/v1/agents/list"
            }
        }
    
    return fastapi_app


def create_combined_app(host: str, port: int, orchestrator: SmartOrchestrator) -> Starlette:
    """Create a combined Starlette app that includes both A2A and FastAPI"""
    from app.agent_executor import OrchestratorAgentExecutor
    
    # Create the agent card
    agent_card = create_orchestrator_agent_card(host, port)
    
    # Create the A2A server
    httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorAgentExecutor(),
        task_store=InMemoryTaskStore(),
        push_notifier=InMemoryPushNotifier(httpx_client),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card, 
        http_handler=request_handler
    )
    
    # Create FastAPI app
    fastapi_app = create_fastapi_app(orchestrator)
    
    # Create the combined Starlette application
    middleware = [
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]
    
    combined_app = Starlette(
        middleware=middleware,
        routes=[
            Mount("/management", fastapi_app),  # Mount FastAPI under /management
            Mount("/", a2a_app.build()),       # Mount A2A app at root
        ]
    )
    
    return combined_app


@click.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
def main(host: str, port: int):
    """Starts the Orchestrator Agent server with FastAPI management endpoints."""
    try:
        # Create orchestrator instance
        orchestrator = SmartOrchestrator()
        
        # Create the combined application
        app = create_combined_app(host, port, orchestrator)
        
        agent_card = create_orchestrator_agent_card(host, port)

        print(f"🚀 Starting Smart Orchestrator Agent on {host}:{port}")
        print(f"📋 Agent Name: {agent_card.name}")
        print(f"📝 Description: {agent_card.description}")
        print(f"🎯 Skills: {', '.join([skill.name for skill in agent_card.skills])}")
        print(f"⚙️  Capabilities: Intelligent routing, Dynamic agent discovery, Semantic understanding")
        print(f"🔌 Pluggable: New agents can be registered at runtime")
        print()
        print("🔧 FastAPI Management Endpoints:")
        print(f"   📖 API Documentation: http://{host}:{port}/management/docs")
        print(f"   📋 List Agents: http://{host}:{port}/management/api/v1/agents/list") 
        print(f"   ➕ Register Agent: POST http://{host}:{port}/management/api/v1/agents/register")
        print(f"   ➖ Unregister Agent: POST http://{host}:{port}/management/api/v1/agents/unregister")
        print()
        print("🌐 A2A Protocol Endpoints:")
        print(f"   🏠 A2A Root: http://{host}:{port}/")
        print(f"   📄 Agent Card: http://{host}:{port}/agent-card")

        uvicorn.run(app, host=host, port=port)

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        sys.exit(1)


if __name__ == "__main__":
    main()
