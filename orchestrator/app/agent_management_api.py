#!/usr/bin/env python3
"""
FastAPI endpoints for agent management operations
"""
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.orchestrator import SmartOrchestrator

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class RegisterAgentRequest(BaseModel):
    endpoint: str = Field(..., description="The endpoint URL of the agent to register")

class RegisterAgentResponse(BaseModel):
    success: bool
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    endpoint: Optional[str] = None
    message: str
    error: Optional[str] = None

class UnregisterAgentRequest(BaseModel):
    agent_identifier: str = Field(..., description="Agent ID, name, or endpoint to unregister")

class UnregisterAgentResponse(BaseModel):
    success: bool
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    endpoint: Optional[str] = None
    message: str
    error: Optional[str] = None

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint: str
    skills: List[Dict]
    keywords: List[str]
    capabilities: List[str]

class ListAgentsResponse(BaseModel):
    success: bool = True
    agents: List[AgentInfo]
    total_count: int
    message: str

# Global orchestrator instance (will be injected)
_orchestrator_instance: Optional[SmartOrchestrator] = None

def get_orchestrator() -> SmartOrchestrator:
    """Dependency to get the orchestrator instance"""
    if _orchestrator_instance is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator_instance

def set_orchestrator(orchestrator: SmartOrchestrator):
    """Set the orchestrator instance"""
    global _orchestrator_instance
    _orchestrator_instance = orchestrator

# Create FastAPI router
router = APIRouter(prefix="/api/v1/agents", tags=["Agent Management"])

@router.post("/register", response_model=RegisterAgentResponse)
async def register_agent(
    request: RegisterAgentRequest,
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    Register a new agent by providing its endpoint URL.
    The orchestrator will fetch the agent's card and add it to the registry.
    """
    try:
        logger.info(f"Registering agent from endpoint: {request.endpoint}")
        
        result = await orchestrator.register_agent(request.endpoint)
        
        if result["success"]:
            logger.info(f"Successfully registered agent: {result.get('agent_name', 'Unknown')}")
            return RegisterAgentResponse(
                success=True,
                agent_id=result.get("agent_id"),
                agent_name=result.get("agent_name"),
                endpoint=result.get("endpoint"),
                message=result.get("message", "Agent registered successfully")
            )
        else:
            logger.warning(f"Failed to register agent from {request.endpoint}: {result.get('error')}")
            return RegisterAgentResponse(
                success=False,
                message="Failed to register agent",
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error registering agent from {request.endpoint}: {e}")
        return RegisterAgentResponse(
            success=False,
            message="Internal server error during agent registration",
            error=str(e)
        )

@router.post("/unregister", response_model=UnregisterAgentResponse)
async def unregister_agent(
    request: UnregisterAgentRequest,
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    Unregister an agent by providing its identifier (agent ID, name, or endpoint).
    The agent will be removed from the registry.
    """
    try:
        logger.info(f"Unregistering agent: {request.agent_identifier}")
        
        result = await orchestrator.unregister_agent(request.agent_identifier)
        
        if result["success"]:
            logger.info(f"Successfully unregistered agent: {result.get('agent_name', 'Unknown')}")
            return UnregisterAgentResponse(
                success=True,
                agent_id=result.get("agent_id"),
                agent_name=result.get("agent_name"),
                endpoint=result.get("endpoint"),
                message=result.get("message", "Agent unregistered successfully")
            )
        else:
            logger.warning(f"Failed to unregister agent {request.agent_identifier}: {result.get('error')}")
            return UnregisterAgentResponse(
                success=False,
                message="Failed to unregister agent",
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error unregistering agent {request.agent_identifier}: {e}")
        return UnregisterAgentResponse(
            success=False,
            message="Internal server error during agent unregistration",
            error=str(e)
        )

@router.get("/list", response_model=ListAgentsResponse)
async def list_agents(
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    List all registered agents with their details including skills and capabilities.
    """
    try:
        logger.info("Listing all registered agents")
        
        agents_data = orchestrator.get_available_agents()
        
        agents = [
            AgentInfo(
                agent_id=agent["agent_id"],
                name=agent["name"],
                description=agent["description"],
                endpoint=agent["endpoint"],
                skills=agent["skills"],
                keywords=agent["keywords"],
                capabilities=agent["capabilities"]
            )
            for agent in agents_data
        ]
        
        logger.info(f"Found {len(agents)} registered agents")
        
        return ListAgentsResponse(
            success=True,
            agents=agents,
            total_count=len(agents),
            message=f"Found {len(agents)} registered agents"
        )
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during agent listing: {str(e)}"
        )

# Alternative simpler endpoints if you prefer GET requests for register/unregister
@router.get("/register_agent")
async def register_agent_get(
    endpoint: str,
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    Alternative GET endpoint for registering an agent.
    Usage: GET /api/v1/agents/register_agent?endpoint=http://localhost:8001
    """
    request = RegisterAgentRequest(endpoint=endpoint)
    return await register_agent(request, orchestrator)

@router.get("/unregister_agent")
async def unregister_agent_get(
    agent_identifier: str,
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    Alternative GET endpoint for unregistering an agent.
    Usage: GET /api/v1/agents/unregister_agent?agent_identifier=MathAgent
    """
    request = UnregisterAgentRequest(agent_identifier=agent_identifier)
    return await unregister_agent(request, orchestrator)

@router.get("/list_agents")
async def list_agents_get(
    orchestrator: SmartOrchestrator = Depends(get_orchestrator)
):
    """
    Alternative GET endpoint for listing agents.
    Usage: GET /api/v1/agents/list_agents
    """
    return await list_agents(orchestrator) 