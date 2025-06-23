#!/usr/bin/env python3
"""
ArgoCD Agent with A2A SDK integration
"""
import asyncio
import os
from typing import Optional

import click
import httpx
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

from app.agent import ArgoCDAgent


def create_agent_card() -> AgentCard:
    """Create the ArgoCD agent card with proper A2A SDK types"""
    skills = [
        AgentSkill(
            id="kubernetes_management",
            name="Kubernetes Management",
            description="Kubernetes cluster management and operations",
            tags=["kubernetes", "k8s"]
        ),
        AgentSkill(
            id="gitops",
            name="GitOps",
            description="GitOps workflow management and automation",
            tags=["gitops", "git"]
        ),
        AgentSkill(
            id="application_deployment",
            name="Application Deployment",
            description="Application deployment and lifecycle management",
            tags=["deployment", "applications"]
        ),
        AgentSkill(
            id="argocd_operations",
            name="ArgoCD Operations",
            description="ArgoCD specific operations and management",
            tags=["argocd", "operations"]
        ),
        AgentSkill(
            id="sync_operations",
            name="Sync Operations",
            description="Application synchronization operations",
            tags=["sync", "operations"]
        ),
        AgentSkill(
            id="resource_monitoring",
            name="Resource Monitoring",
            description="Kubernetes resource monitoring and status tracking",
            tags=["monitoring", "resources"]
        )
    ]
    
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=True,
        stateTransitionHistory=False
    )
    
    return AgentCard(
        name="ArgoCD Agent",
        description="Handles ArgoCD and Kubernetes operations via MCP protocol",
        url="http://localhost:8001",
        version="1.0.0",
        capabilities=capabilities,
        skills=skills,
        defaultInputModes=["text"],
        defaultOutputModes=["text"]
    )


# Import the agent executor
from app.agent_executor import ArgoCDAgentExecutor


@click.command()
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--port", default=8001, help="Port to bind to")
@click.option("--log-level", default="INFO", help="Logging level")
def main(host: str, port: int, log_level: str):
    """Run the ArgoCD Agent server using A2A SDK"""
    
    # Create agent card
    agent_card = create_agent_card()
    
    print(f"🚀 Starting ArgoCD Agent on {host}:{port}")
    print(f"📋 Agent Name: {agent_card.name}")
    print(f"📝 Description: {agent_card.description}")
    print(f"🎯 Skills: {', '.join([skill.name for skill in agent_card.skills])}")
    
    try:
        # Create the server components following currencyAgent pattern
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=ArgoCDAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )

        import uvicorn
        uvicorn.run(server.build(), host=host, port=port)
        
    except Exception as e:
        print(f"❌ Error starting ArgoCD Agent server: {e}")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main() 