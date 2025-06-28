#!/usr/bin/env python3
"""
Test script for FastAPI integration with orchestrator client
"""
import asyncio
import sys
from fastapi_client import OrchestratorFastAPIClient, HybridOrchestratorClient


async def test_fastapi_client():
    """Test the FastAPI client functionality"""
    print("🧪 Testing FastAPI Client Integration")
    print("=" * 60)
    
    # Initialize client
    client = OrchestratorFastAPIClient("http://localhost:8000")
    
    try:
        # Test 1: Check API availability
        print("\n1. 🔍 Checking FastAPI availability...")
        api_available = await client.check_api_availability()
        print(f"   FastAPI Available: {'✅ Yes' if api_available else '❌ No'}")
        
        if not api_available:
            print("   ⚠️  Make sure the orchestrator is running with FastAPI endpoints enabled")
            print("   💡 Start with: cd orchestrator && uv run -m app")
            return
        
        # Test 2: List agents
        print("\n2. 📋 Listing agents via FastAPI...")
        result = await client.list_agents()
        if result.get("success"):
            agents = result.get("agents", [])
            print(f"   Found {len(agents)} agents:")
            for agent in agents:
                print(f"   - {agent['name']} ({agent['endpoint']})")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        
        # Test 3: Show API documentation URLs
        print("\n3. 📖 API Documentation URLs:")
        print(f"   Interactive Docs: {client.get_docs_url()}")
        print(f"   Alternative Docs: {client.get_redoc_url()}")
        
        # Test 4: Register agent (example)
        print("\n4. ➕ Testing agent registration...")
        test_endpoint = "http://localhost:8004"
        reg_result = await client.register_agent(test_endpoint)
        if reg_result.get("success"):
            print(f"   ✅ Registration successful: {reg_result.get('message')}")
            
            # Test 5: Unregister the same agent
            print("\n5. ➖ Testing agent unregistration...")
            agent_id = reg_result.get("agent_id")
            if agent_id:
                unreg_result = await client.unregister_agent(agent_id)
                if unreg_result.get("success"):
                    print(f"   ✅ Unregistration successful: {unreg_result.get('message')}")
                else:
                    print(f"   ❌ Unregistration failed: {unreg_result.get('error')}")
        else:
            print(f"   ⚠️  Registration failed (expected if agent not running): {reg_result.get('error')}")
        
        print("\n✅ FastAPI client tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


async def test_hybrid_client():
    """Test the hybrid client functionality"""
    print("\n" + "=" * 60)
    print("🔄 Testing Hybrid Client (FastAPI + A2A fallback)")
    print("=" * 60)
    
    # Initialize hybrid client
    client = HybridOrchestratorClient("http://localhost:8000")
    
    try:
        # Test 1: List agents with hybrid approach
        print("\n1. 📋 Listing agents via hybrid client...")
        result = await client.list_agents(prefer_fastapi=True)
        if result.get("success"):
            agents = result.get("agents", [])
            print(f"   Found {len(agents)} agents:")
            for agent in agents:
                print(f"   - {agent['name']} ({agent['endpoint']})")
        else:
            print(f"   ❌ Failed: {result.get('error')}")
        
        # Test 2: Test fallback behavior
        print("\n2. 🔄 Testing A2A fallback...")
        result_a2a = await client.list_agents(prefer_fastapi=False)
        if result_a2a.get("success"):
            print(f"   ✅ A2A fallback works: Found {result_a2a.get('total_count')} agents")
        else:
            print(f"   ⚠️  A2A fallback failed: {result_a2a.get('error')}")
        
        print("\n✅ Hybrid client tests completed!")
        
    except Exception as e:
        print(f"\n❌ Hybrid test failed: {e}")


async def interactive_demo():
    """Interactive demo of the FastAPI client"""
    print("\n" + "=" * 60)
    print("🎮 Interactive FastAPI Demo")
    print("=" * 60)
    print("Commands:")
    print("  list    - List all agents")
    print("  reg     - Register an agent")
    print("  unreg   - Unregister an agent")
    print("  docs    - Show API documentation URLs")
    print("  quit    - Exit demo")
    print("=" * 60)
    
    client = OrchestratorFastAPIClient("http://localhost:8000")
    
    while True:
        try:
            command = input("\n🎮 Enter command: ").strip().lower()
            
            if command in ["quit", "q", "exit"]:
                print("👋 Goodbye!")
                break
            elif command == "list":
                result = await client.list_agents()
                if result.get("success"):
                    agents = result.get("agents", [])
                    print(f"\n📋 Found {len(agents)} agents:")
                    for i, agent in enumerate(agents, 1):
                        print(f"{i}. {agent['name']} - {agent['endpoint']}")
                else:
                    print(f"❌ Error: {result.get('error')}")
            elif command == "reg":
                endpoint = input("Enter agent endpoint (e.g., http://localhost:8001): ")
                if endpoint:
                    result = await client.register_agent(endpoint)
                    if result.get("success"):
                        print(f"✅ Registered: {result.get('agent_name')}")
                    else:
                        print(f"❌ Error: {result.get('error')}")
            elif command == "unreg":
                identifier = input("Enter agent identifier (name, ID, or endpoint): ")
                if identifier:
                    result = await client.unregister_agent(identifier)
                    if result.get("success"):
                        print(f"✅ Unregistered: {result.get('agent_name')}")
                    else:
                        print(f"❌ Error: {result.get('error')}")
            elif command == "docs":
                print(f"\n📖 API Documentation:")
                print(f"Interactive Docs: {client.get_docs_url()}")
                print(f"Alternative Docs: {client.get_redoc_url()}")
            else:
                print("❓ Unknown command. Try: list, reg, unreg, docs, quit")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def print_usage():
    """Print usage instructions"""
    print("🚀 FastAPI Integration Usage")
    print("=" * 50)
    print()
    print("1. Start the orchestrator with FastAPI endpoints:")
    print("   cd orchestrator")
    print("   uv run -m app")
    print()
    print("2. Run this test script:")
    print("   python test_fastapi_integration.py")
    print()
    print("3. Use the updated orchestrator client:")
    print("   # List agents via FastAPI")
    print("   python -m orchestrator_client --list_agent --use_fastapi")
    print()
    print("   # Register agent via FastAPI") 
    print("   python -m orchestrator_client --register_agent http://localhost:8001 --use_fastapi")
    print()
    print("   # Show API documentation URLs")
    print("   python -m orchestrator_client --show_api_docs")
    print()
    print("4. Access API documentation:")
    print("   http://localhost:8000/management/docs")


async def main():
    """Main test function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print_usage()
            return
        elif sys.argv[1] == "--interactive":
            await interactive_demo()
            return
    
    print_usage()
    print("\n" + "=" * 50)
    
    # Run automated tests
    await test_fastapi_client()
    await test_hybrid_client()
    
    # Ask if user wants interactive demo
    try:
        if input("\n🎮 Run interactive demo? (y/n): ").lower().startswith('y'):
            await interactive_demo()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main()) 