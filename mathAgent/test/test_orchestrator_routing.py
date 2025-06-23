#!/usr/bin/env python3
"""
Test orchestrator routing for math queries
"""
import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent.parent / "orchestrator"
sys.path.insert(0, str(orchestrator_path))

from app.orchestrator import SmartOrchestrator

async def test_math_routing():
    """Test if orchestrator routes math queries correctly"""
    
    print("🔀 Testing Orchestrator Routing for Math Queries")
    print("=" * 50)
    
    orchestrator = SmartOrchestrator()
    
    # Test queries that should go to math agent
    test_queries = [
        "what is 2+3",
        "calculate 5 * 6",
        "solve equation x + 2 = 5",
        "find derivative of x^2",
        "what is the mean of [1,2,3,4,5]"
    ]
    
    for query in test_queries:
        print(f"\n🔢 Query: {query}")
        
        try:
            result = await orchestrator.process_request(query)
            
            print(f"   🎯 Selected Agent: {result.get('selected_agent_name', 'Unknown')}")
            print(f"   📊 Confidence: {result.get('confidence', 0):.2f}")
            print(f"   🧠 Reasoning: {result.get('reasoning', 'No reasoning')}")
            
            if result.get('success'):
                print(f"   ✅ Status: Success")
            else:
                print(f"   ❌ Status: Failed - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print(f"\n📋 Available Agents:")
    for agent_id, agent_card in orchestrator.agents.items():
        print(f"   - {agent_id}: {agent_card.name} ({agent_card.url})")

if __name__ == "__main__":
    asyncio.run(test_math_routing()) 