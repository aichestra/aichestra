#!/usr/bin/env python3
"""
FastAPI client for orchestrator agent management endpoints
"""
import asyncio
import httpx
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin


class OrchestratorFastAPIClient:
    """Client for interacting with orchestrator's FastAPI agent management endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the FastAPI client
        
        Args:
            base_url: Base URL of the orchestrator server (e.g., "http://localhost:8000")
        """
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/management/api/v1/agents"
        self.timeout = 30.0
    
    async def list_agents(self) -> Dict[str, Any]:
        """
        List all registered agents using FastAPI endpoint
        
        Returns:
            Dict containing success status, agents list, and metadata
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base}/list")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "agents": [],
                "total_count": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "agents": [],
                "total_count": 0
            }
    
    async def register_agent(self, endpoint: str) -> Dict[str, Any]:
        """
        Register a new agent using FastAPI endpoint
        
        Args:
            endpoint: The endpoint URL of the agent to register
            
        Returns:
            Dict containing success status and registration details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/register",
                    json={"endpoint": endpoint}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
                return {
                    "success": False,
                    "error": error_detail.get("error", f"HTTP {e.response.status_code}"),
                    "message": error_detail.get("message", "Registration failed")
                }
            except:
                return {
                    "success": False,
                    "error": f"HTTP {e.response.status_code}: {e.response.text}",
                    "message": "Registration failed"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "message": "Registration failed"
            }
    
    async def unregister_agent(self, agent_identifier: str) -> Dict[str, Any]:
        """
        Unregister an agent using FastAPI endpoint
        
        Args:
            agent_identifier: Agent ID, name, or endpoint to unregister
            
        Returns:
            Dict containing success status and unregistration details
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/unregister",
                    json={"agent_identifier": agent_identifier}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            try:
                error_detail = e.response.json()
                return {
                    "success": False,
                    "error": error_detail.get("error", f"HTTP {e.response.status_code}"),
                    "message": error_detail.get("message", "Unregistration failed")
                }
            except:
                return {
                    "success": False,
                    "error": f"HTTP {e.response.status_code}: {e.response.text}",
                    "message": "Unregistration failed"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "message": "Unregistration failed"
            }
    
    # Alternative GET endpoint methods for simpler usage
    async def register_agent_get(self, endpoint: str) -> Dict[str, Any]:
        """Register agent using GET endpoint (alternative method)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/register_agent",
                    params={"endpoint": endpoint}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "message": "Registration failed"
            }
    
    async def unregister_agent_get(self, agent_identifier: str) -> Dict[str, Any]:
        """Unregister agent using GET endpoint (alternative method)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/unregister_agent",
                    params={"agent_identifier": agent_identifier}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "message": "Unregistration failed"
            }
    
    async def list_agents_get(self) -> Dict[str, Any]:
        """List agents using GET endpoint (alternative method)"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.api_base}/list_agents")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "agents": [],
                "total_count": 0
            }
    
    async def get_api_info(self) -> Dict[str, Any]:
        """Get API information from the FastAPI root endpoint"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/management/")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": f"Could not get API info: {str(e)}",
                "available": False
            }
    
    async def check_api_availability(self) -> bool:
        """Check if the FastAPI endpoints are available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/management/")
                return response.status_code == 200
        except:
            return False
    
    def get_docs_url(self) -> str:
        """Get the URL for the interactive API documentation"""
        return f"{self.base_url}/management/docs"
    
    def get_redoc_url(self) -> str:
        """Get the URL for the alternative API documentation"""
        return f"{self.base_url}/management/redoc"


class HybridOrchestratorClient:
    """
    Hybrid client that uses both A2A protocol and FastAPI endpoints
    Automatically falls back between methods for better reliability
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the hybrid client
        
        Args:
            base_url: Base URL of the orchestrator server
        """
        self.base_url = base_url
        self.fastapi_client = OrchestratorFastAPIClient(base_url)
        self._fastapi_available = None
    
    async def _check_fastapi_availability(self) -> bool:
        """Check if FastAPI endpoints are available (cached)"""
        if self._fastapi_available is None:
            self._fastapi_available = await self.fastapi_client.check_api_availability()
        return self._fastapi_available
    
    async def list_agents(self, prefer_fastapi: bool = True) -> Dict[str, Any]:
        """
        List agents using the best available method
        
        Args:
            prefer_fastapi: Whether to prefer FastAPI over A2A protocol
            
        Returns:
            Dict containing agents list and metadata
        """
        if prefer_fastapi and await self._check_fastapi_availability():
            # Try FastAPI first
            result = await self.fastapi_client.list_agents()
            if result.get("success", False):
                return result
            
            # Fall back to A2A if FastAPI fails
            print("⚠️  FastAPI failed, falling back to A2A protocol...")
        
        # Use A2A protocol fallback
        try:
            from __main__ import get_agents_from_orchestrator
            async with httpx.AsyncClient(timeout=30) as httpx_client:
                agents = await get_agents_from_orchestrator(httpx_client, self.base_url)
                return {
                    "success": True,
                    "agents": agents,
                    "total_count": len(agents),
                    "message": f"Found {len(agents)} agents via A2A protocol"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Both FastAPI and A2A failed: {str(e)}",
                "agents": [],
                "total_count": 0
            }
    
    async def register_agent(self, endpoint: str, prefer_fastapi: bool = True) -> Dict[str, Any]:
        """
        Register agent using the best available method
        
        Args:
            endpoint: Agent endpoint to register
            prefer_fastapi: Whether to prefer FastAPI over A2A protocol
            
        Returns:
            Dict containing registration result
        """
        if prefer_fastapi and await self._check_fastapi_availability():
            # Try FastAPI first
            result = await self.fastapi_client.register_agent(endpoint)
            if result.get("success", False):
                return result
            
            # Fall back to A2A if FastAPI fails
            print("⚠️  FastAPI failed, falling back to A2A protocol...")
        
        # Use A2A protocol fallback
        try:
            from __main__ import register_agent_with_orchestrator
            async with httpx.AsyncClient(timeout=30) as httpx_client:
                await register_agent_with_orchestrator(httpx_client, self.base_url, endpoint)
                return {
                    "success": True,
                    "message": f"Agent registered via A2A protocol",
                    "endpoint": endpoint
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Both FastAPI and A2A failed: {str(e)}",
                "message": "Registration failed"
            }
    
    async def unregister_agent(self, agent_identifier: str, prefer_fastapi: bool = True) -> Dict[str, Any]:
        """
        Unregister agent using the best available method
        
        Args:
            agent_identifier: Agent ID, name, or endpoint to unregister
            prefer_fastapi: Whether to prefer FastAPI over A2A protocol
            
        Returns:
            Dict containing unregistration result
        """
        if prefer_fastapi and await self._check_fastapi_availability():
            # Try FastAPI first
            result = await self.fastapi_client.unregister_agent(agent_identifier)
            if result.get("success", False):
                return result
            
            # Fall back to A2A if FastAPI fails
            print("⚠️  FastAPI failed, falling back to A2A protocol...")
        
        # Use A2A protocol fallback
        try:
            from __main__ import unregister_agent_with_orchestrator
            async with httpx.AsyncClient(timeout=30) as httpx_client:
                await unregister_agent_with_orchestrator(httpx_client, self.base_url, agent_identifier)
                return {
                    "success": True,
                    "message": f"Agent unregistered via A2A protocol",
                    "agent_identifier": agent_identifier
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Both FastAPI and A2A failed: {str(e)}",
                "message": "Unregistration failed"
            }
    
    def get_docs_url(self) -> str:
        """Get the URL for the interactive API documentation"""
        return self.fastapi_client.get_docs_url()
    
    def get_redoc_url(self) -> str:
        """Get the URL for the alternative API documentation"""
        return self.fastapi_client.get_redoc_url()


# Convenience functions for backward compatibility
async def create_fastapi_client(base_url: str = "http://localhost:8000") -> OrchestratorFastAPIClient:
    """Create a FastAPI client instance"""
    return OrchestratorFastAPIClient(base_url)


async def create_hybrid_client(base_url: str = "http://localhost:8000") -> HybridOrchestratorClient:
    """Create a hybrid client instance"""
    return HybridOrchestratorClient(base_url) 