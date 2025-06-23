#!/usr/bin/env python3
"""
Debug orchestrator routing in detail
"""
import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
orchestrator_path = Path(__file__).parent.parent.parent / "orchestrator"
sys.path.insert(0, str(orchestrator_path))

from app.orchestrator import SmartOrchestrator

async def debug_routing():
    """Debug routing for specific query"""
    
    orchestrator = SmartOrchestrator()
    
    query = "what is 2+3"
    print(f"🔍 Debugging query: '{query}'")
    print("=" * 50)
    
    # Check each agent's score
    for agent_id, agent_card in orchestrator.agents.items():
        print(f"\n🤖 Agent: {agent_card.name} ({agent_id})")
        
        score, matched_skills = orchestrator._calculate_agent_score(query, agent_card)
        print(f"   📊 Score: {score}")
        print(f"   🎯 Matched Skills: {matched_skills}")
        
        # Check skill keywords
        print(f"   🏷️  Skills:")
        for skill in agent_card.skills:
            skill_match = orchestrator._skill_matches_request(skill.name, query)
            print(f"      - {skill.name}: {'✅' if skill_match else '❌'}")
        
        # Check skill tags
        print(f"   🔖 Tags:")
        keywords = [tag for skill in agent_card.skills for tag in (skill.tags or [])]
        for keyword in keywords:
            if keyword.lower() in query.lower():
                print(f"      - {keyword}: ✅ MATCH")
            else:
                print(f"      - {keyword}: ❌")
    
    # Test specific skill matching
    print(f"\n🔧 Testing skill matching for 'arithmetic_calculation':")
    skill_keywords = {
        "arithmetic_calculation": ["math", "calculation", "arithmetic", "compute", "calculate", "add", "subtract", "multiply", "divide", "power", "sqrt", "sin", "cos", "tan", "log", "exp", "what is", "plus", "minus", "times", "+", "-", "*", "/", "^", "sum", "product", "number", "numbers"]
    }
    
    keywords = skill_keywords.get("arithmetic_calculation", [])
    query_lower = query.lower()
    
    for keyword in keywords:
        if keyword in query_lower:
            print(f"   ✅ '{keyword}' found in '{query}'")
        else:
            print(f"   ❌ '{keyword}' not in '{query}'")

if __name__ == "__main__":
    asyncio.run(debug_routing()) 