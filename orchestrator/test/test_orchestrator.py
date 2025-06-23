"""
Test client for the Orchestrator Agent using AgentCard
"""
import asyncio
from .orchestrator import SmartOrchestrator

# Import AgentCard and Skill from the same place as orchestrator
try:
    from a2a_sdk import AgentCard, Skill
except ImportError:
    from .orchestrator import AgentCard, Skill

async def test_orchestrator():
    """Test the orchestrator with various requests"""
    orchestrator = SmartOrchestrator()
    
    # Test cases
    test_cases = [
        "List all ArgoCD applications",
        "What is the current exchange rate for USD to EUR?",
        "Sync the guestbook application in ArgoCD",
        "Convert 100 USD to Japanese Yen",
        "Show me the status of my Kubernetes deployments",
        "Get historical currency rates for the last month",
        "Deploy a new application using GitOps",
        "What's the price of Bitcoin in USD?",
        "Help me troubleshoot a failing pod",
        "Calculate the exchange rate between GBP and CAD",
        "Hello world",  # Test default routing
        "kubernetes cluster management",  # Test skill matching
        "financial market analysis"  # Test skill matching
    ]
    
    print("=== Smart Orchestrator Test (AgentCard) ===\n")
    
    # Show available agents
    agents = orchestrator.get_available_agents()
    print("Available Agents:")
    for agent in agents:
        print(f"  - {agent['agent_id']}: {agent['name']}")
        print(f"    Endpoint: {agent['endpoint']}")
        print(f"    Description: {agent['description']}")
        print(f"    Skills: {', '.join([skill['name'] for skill in agent['skills']])}")
        print(f"    Keywords: {', '.join(agent['keywords'])}")
        print(f"    Capabilities: {', '.join(agent['capabilities'])}")
        print()
    
    print("=== Test Cases ===\n")
    
    for i, test_request in enumerate(test_cases, 1):
        print(f"Test {i}: {test_request}")
        
        try:
            result = await orchestrator.process_request(test_request)
            
            if result["success"]:
                print(f"  ✅ Success")
                print(f"  Selected Agent: {result['selected_agent_id']} ({result['selected_agent_name']})")
                print(f"  Agent Skills: {', '.join(result['agent_skills'])}")
                print(f"  Confidence: {result['confidence']:.2f}")
                print(f"  Reasoning: {result['reasoning']}")
                print(f"  Response: {result['response']}")
                
                # Show detailed scoring if available
                metadata = result["metadata"]
                if "agent_scores" in metadata:
                    print(f"  Agent Scores: {metadata['agent_scores']}")
                if "skill_matches" in metadata:
                    print(f"  Skill Matches: {metadata['skill_matches']}")
                    
            else:
                print(f"  ❌ Error: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        print("-" * 80)

async def test_add_agent():
    """Test adding a new agent dynamically using AgentCard"""
    print("\n=== Testing Dynamic Agent Addition with AgentCard ===\n")
    
    orchestrator = SmartOrchestrator()
    
    # Create skills for the weather agent
    weather_skills = [
        Skill("weather_forecasting", "Weather prediction and forecasting", 0.9),
        Skill("climate_analysis", "Climate data analysis", 0.8),
        Skill("meteorology", "Meteorological data processing", 0.85)
    ]
    
    # Create a new weather agent using AgentCard
    weather_agent = AgentCard(
        agent_id="weather",
        name="Weather Agent",
        description="Handles weather-related queries and forecasting",
        skills=weather_skills,
        endpoint="http://localhost:8003",
        metadata={
            "keywords": ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "climate"],
            "capabilities": ["get_forecast", "analyze_climate", "weather_alerts"]
        }
    )
    
    # Add the agent to the orchestrator
    orchestrator.add_agent(weather_agent)
    
    print("Added Weather Agent using AgentCard. Available agents:")
    for agent in orchestrator.get_available_agents():
        print(f"  - {agent['agent_id']}: {agent['name']}")
        print(f"    Skills: {', '.join([skill['name'] for skill in agent['skills']])}")
    
    # Test routing to the new agent
    weather_requests = [
        "What's the weather like today?",
        "Will it rain tomorrow?",
        "Show me the temperature forecast",
        "Climate analysis for this region",
        "Weather forecasting data"
    ]
    
    print("\n=== Testing Weather Agent Routing ===")
    for request in weather_requests:
        print(f"\nTesting: {request}")
        result = await orchestrator.process_request(request)
        if result["success"]:
            print(f"  Routed to: {result['selected_agent_id']} ({result['selected_agent_name']})")
            print(f"  Skills: {', '.join(result['agent_skills'])}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Reasoning: {result['reasoning']}")
            
            # Show skill matches
            metadata = result["metadata"]
            if "skill_matches" in metadata and metadata["skill_matches"].get(result['selected_agent_id']):
                matched_skills = metadata["skill_matches"][result['selected_agent_id']]
                print(f"  Matched Skills: {', '.join(matched_skills)}")

async def test_agent_card_features():
    """Test AgentCard specific features"""
    print("\n=== Testing AgentCard Features ===\n")
    
    orchestrator = SmartOrchestrator()
    
    # Test getting agent by ID
    argocd_agent = orchestrator.get_agent_by_id("argocd")
    if argocd_agent:
        print(f"Retrieved agent: {argocd_agent.name}")
        print(f"Skills: {[skill.name for skill in argocd_agent.skills]}")
        print(f"Confidence levels: {[skill.confidence for skill in argocd_agent.skills]}")
    
    # Test listing all agents
    all_agents = orchestrator.list_agents()
    print(f"\nTotal agents registered: {len(all_agents)}")
    for agent in all_agents:
        print(f"  - {agent.agent_id}: {len(agent.skills)} skills")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
    asyncio.run(test_add_agent())
    asyncio.run(test_agent_card_features()) 