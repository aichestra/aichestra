#!/usr/bin/env python3
"""
Test client for Agent Management API endpoints
"""
import asyncio
import json
import httpx
from typing import Dict, Any


class AgentManagementClient:
    """Client for testing agent management API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/management/api/v1/agents"
    
    async def list_agents(self) -> Dict[str, Any]:
        """List all registered agents"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/list")
            return response.json()
    
    async def register_agent(self, endpoint: str) -> Dict[str, Any]:
        """Register a new agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/register",
                json={"endpoint": endpoint}
            )
            return response.json()
    
    async def unregister_agent(self, agent_identifier: str) -> Dict[str, Any]:
        """Unregister an agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/unregister",
                json={"agent_identifier": agent_identifier}
            )
            return response.json()
    
    # Alternative GET endpoints for simpler testing
    async def register_agent_get(self, endpoint: str) -> Dict[str, Any]:
        """Register agent using GET endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/register_agent",
                params={"endpoint": endpoint}
            )
            return response.json()
    
    async def unregister_agent_get(self, agent_identifier: str) -> Dict[str, Any]:
        """Unregister agent using GET endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/unregister_agent",
                params={"agent_identifier": agent_identifier}
            )
            return response.json()
    
    async def list_agents_get(self) -> Dict[str, Any]:
        """List agents using GET endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/list_agents")
            return response.json()


async def run_tests():
    """Run test scenarios for the agent management API"""
    client = AgentManagementClient()
    
    print("🧪 Testing Agent Management API")
    print("=" * 50)
    
    try:
        # Test 1: List initial agents
        print("\n1. 📋 Listing initial agents...")
        result = await client.list_agents()
        print(f"   Status: {'✅' if result.get('success') else '❌'}")
        print(f"   Total agents: {result.get('total_count', 0)}")
        if result.get('agents'):
            for agent in result['agents']:
                print(f"   - {agent['name']} ({agent['endpoint']})")
        
        # Test 2: Register a new agent (example)
        print("\n2. ➕ Registering a new agent...")
        new_agent_endpoint = "http://localhost:8004"
        result = await client.register_agent(new_agent_endpoint)
        print(f"   Status: {'✅' if result.get('success') else '❌'}")
        print(f"   Message: {result.get('message', result.get('error'))}")
        
        # Test 3: List agents after registration
        print("\n3. 📋 Listing agents after registration...")
        result = await client.list_agents()
        print(f"   Status: {'✅' if result.get('success') else '❌'}")
        print(f"   Total agents: {result.get('total_count', 0)}")
        
        # Test 4: Unregister an agent (if any exist)
        if result.get('agents') and len(result['agents']) > 0:
            print("\n4. ➖ Unregistering an agent...")
            agent_to_remove = result['agents'][0]['agent_id']
            result = await client.unregister_agent(agent_to_remove)
            print(f"   Status: {'✅' if result.get('success') else '❌'}")
            print(f"   Message: {result.get('message', result.get('error'))}")
            
            # Test 5: List agents after unregistration
            print("\n5. 📋 Listing agents after unregistration...")
            result = await client.list_agents()
            print(f"   Status: {'✅' if result.get('success') else '❌'}")
            print(f"   Total agents: {result.get('total_count', 0)}")
        
        # Test GET endpoints
        print("\n6. 🔄 Testing GET endpoints...")
        print("   6a. List agents (GET)...")
        result = await client.list_agents_get()
        print(f"       Status: {'✅' if result.get('success') else '❌'}")
        print(f"       Total agents: {result.get('total_count', 0)}")
        
        print("   6b. Register agent (GET)...")
        result = await client.register_agent_get("http://localhost:8005")
        print(f"       Status: {'✅' if result.get('success') else '❌'}")
        print(f"       Message: {result.get('message', result.get('error'))}")
        
        print("\n✅ Tests completed!")
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("   Make sure the orchestrator server is running on localhost:8000")


def print_usage():
    """Print usage instructions"""
    print("🚀 Agent Management API Usage Examples")
    print("=" * 50)
    print()
    print("1. Start the orchestrator server:")
    print("   cd orchestrator")
    print("   python -m app")
    print()
    print("2. Access the API documentation:")
    print("   http://localhost:8000/management/docs")
    print()
    print("3. Use curl commands to test:")
    print()
    print("   # List agents")
    print("   curl http://localhost:8000/management/api/v1/agents/list")
    print()
    print("   # Register agent (POST)")
    print("   curl -X POST http://localhost:8000/management/api/v1/agents/register \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"endpoint\": \"http://localhost:8001\"}'")
    print()
    print("   # Register agent (GET)")
    print("   curl 'http://localhost:8000/management/api/v1/agents/register_agent?endpoint=http://localhost:8001'")
    print()
    print("   # Unregister agent (POST)")
    print("   curl -X POST http://localhost:8000/management/api/v1/agents/unregister \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"agent_identifier\": \"MathAgent\"}'")
    print()
    print("   # Unregister agent (GET)")
    print("   curl 'http://localhost:8000/management/api/v1/agents/unregister_agent?agent_identifier=MathAgent'")
    print()
    print("4. Python usage:")
    print("   python test_agent_management_api.py")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage()
    else:
        print_usage()
        print("\n" + "="*50)
        asyncio.run(run_tests()) 