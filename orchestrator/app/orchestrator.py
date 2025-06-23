#!/usr/bin/env python3
"""
Smart Orchestrator Agent with A2A SDK integration
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict

import httpx
from langgraph.graph import StateGraph
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.client import A2AClient, A2ACardResolver

class RouterState(TypedDict):
    request: str
    selected_agent: str
    confidence: float
    reasoning: str
    response: str
    error: str
    metadata: dict


class SmartOrchestrator:
    """Intelligent orchestrator using A2A SDK types and LangGraph workflow"""
    
    def __init__(self):
        self.agents: Dict[str, AgentCard] = {}
        self.skill_keywords: Dict[str, List[str]] = {}
        self.workflow = self._create_workflow()
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """Initialize default agents by fetching their agent cards using A2A client"""
        
        # Default agent endpoints
        default_agents = [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8003"
        ]
        
        # Fetch agent cards using A2A client - run async initialization
        asyncio.run(self._fetch_all_agent_cards(default_agents))
    
    async def _fetch_all_agent_cards(self, default_agents: List[str]):
        """Async method to fetch all agent cards"""
        async with httpx.AsyncClient(timeout=5.0) as httpx_client:
            for endpoint in default_agents:
                try:
                    agent_card = await self._fetch_agent_card_with_a2a(httpx_client, endpoint)
                    if agent_card:
                        self.agents[agent_card.name] = agent_card
                        print(f"✅ Loaded {agent_card.name} from {endpoint}")
                    else:
                        print(f"⚠️  Failed to load agent card from {endpoint}")
                except Exception as e:
                    print(f"❌ Error loading agent from {endpoint}: {e}")
        
        # Update skill keywords after loading all default agents
        self._update_skill_keywords()
    
    async def _fetch_agent_card_with_a2a(self, httpx_client: httpx.AsyncClient, endpoint: str) -> Optional[AgentCard]:
        """Fetch agent card using A2A client"""
        try:
            # Create A2A card resolver
            resolver = A2ACardResolver(
                httpx_client=httpx_client,
                base_url=endpoint
            )
            
            # Fetch agent card using the resolver
            agent_card = await resolver.get_agent_card()
            return agent_card
                
        except Exception as e:
            print(f"Error fetching agent card from {endpoint} using A2A client: {e}")
            return None
    
    def add_agent(self, agent_id: str, agent_card: AgentCard):
        """Add a new agent using A2A SDK AgentCard"""
        self.agents[agent_id] = agent_card
        self._update_skill_keywords()
    
    def _update_skill_keywords(self):
        """Update skill keywords based on currently available agents"""
        self.skill_keywords = {}
        
        for agent_id, agent_card in self.agents.items():
            for skill in agent_card.skills:
                skill_name = skill.name
                
                # Initialize skill keywords list if not exists
                if skill_name not in self.skill_keywords:
                    self.skill_keywords[skill_name] = []
                
                # Add tags from this skill as keywords
                if skill.tags:
                    for tag in skill.tags:
                        if tag.lower() not in [kw.lower() for kw in self.skill_keywords[skill_name]]:
                            self.skill_keywords[skill_name].append(tag.lower())
                
                # Add skill name itself as a keyword
                skill_name_lower = skill_name.lower().replace("_", " ")
                if skill_name_lower not in [kw.lower() for kw in self.skill_keywords[skill_name]]:
                    self.skill_keywords[skill_name].append(skill_name_lower)
                
                # Add description words as keywords (first 3 words)
                if skill.description:
                    desc_words = skill.description.lower().split()[:3]
                    for word in desc_words:
                        # Only add meaningful words (length > 2)
                        if len(word) > 2 and word not in [kw.lower() for kw in self.skill_keywords[skill_name]]:
                            self.skill_keywords[skill_name].append(word)
        
        print(f"Updated skill keywords for {len(self.skill_keywords)} skills from {len(self.agents)} agents")
    
    async def register_agent(self, endpoint: str) -> Dict:
        """Register a new agent by fetching its agent card from the endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as httpx_client:
                agent_card = await self._fetch_agent_card_with_a2a(httpx_client, endpoint)
                if agent_card:
                    # Generate agent_id from the endpoint
                    agent_id = agent_card.name
                    
                    # Add the agent to our registry
                    self.agents[agent_id] = agent_card
                    self._update_skill_keywords()
                    
                    return {
                        "success": True,
                        "agent_id": agent_id,
                        "agent_name": agent_card.name,
                        "endpoint": endpoint,
                        "message": f"Successfully registered {agent_card.name} from {endpoint}"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to fetch agent card from {endpoint}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error registering agent from {endpoint}: {str(e)}"
            }
    
    async def unregister_agent(self, agent_identifier: str) -> Dict:
        """Unregister an agent by agent_id, endpoint, or name"""
        try:
            agent_to_remove = None
            agent_id_to_remove = None
            
            # Try to find the agent by different identifiers
            for agent_id, agent_card in self.agents.items():
                # Match by agent_id
                if agent_id == agent_identifier:
                    agent_to_remove = agent_card
                    agent_id_to_remove = agent_id
                    break
                # Match by endpoint/URL
                elif agent_card.url == agent_identifier:
                    agent_to_remove = agent_card
                    agent_id_to_remove = agent_id
                    break
                # Match by name
                elif agent_card.name.lower() == agent_identifier.lower():
                    agent_to_remove = agent_card
                    agent_id_to_remove = agent_id
                    break
                # Match by partial endpoint (e.g., localhost:8080)
                elif agent_identifier in agent_card.url:
                    agent_to_remove = agent_card
                    agent_id_to_remove = agent_id
                    break
            
            if agent_to_remove and agent_id_to_remove:
                # Remove the agent from registry
                del self.agents[agent_id_to_remove]
                self._update_skill_keywords()
                
                return {
                    "success": True,
                    "agent_id": agent_id_to_remove,
                    "agent_name": agent_to_remove.name,
                    "endpoint": agent_to_remove.url,
                    "message": f"Successfully unregistered {agent_to_remove.name} (ID: {agent_id_to_remove})"
                }
            else:
                return {
                    "success": False,
                    "error": f"Agent not found: {agent_identifier}. Available agents: {list(self.agents.keys())}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error unregistering agent {agent_identifier}: {str(e)}"
            }
    
    def get_available_agents(self) -> List[Dict]:
        """Get available agents in a format compatible with existing code"""
        agents = []
        for agent_id, agent_card in self.agents.items():
            agents.append({
                "agent_id": agent_id,
                "name": agent_card.name,
                "description": agent_card.description,
                "endpoint": agent_card.url,
                "skills": [{"name": skill.name, "description": skill.description} for skill in agent_card.skills],
                "keywords": [tag for skill in agent_card.skills for tag in (skill.tags or [])],
                "capabilities": [cap for cap, enabled in [
                    ("streaming", agent_card.capabilities.streaming),
                    ("pushNotifications", agent_card.capabilities.pushNotifications),
                    ("stateTransitionHistory", agent_card.capabilities.stateTransitionHistory)
                ] if enabled]
            })
        return agents
    
    def _create_workflow(self):
        """Create LangGraph workflow for request routing"""
        workflow = StateGraph(RouterState)
        
        workflow.add_node("analyze", self._analyze_request)
        workflow.add_node("route", self._route_to_agent)
        
        workflow.add_edge("analyze", "route")
        workflow.set_entry_point("analyze")
        workflow.set_finish_point("route")
        
        return workflow.compile()
    
    async def _analyze_request(self, state: RouterState) -> RouterState:
        """Analyze the request and select the best agent"""
        request = state["request"]
        
        best_agent = None
        best_score = 0.0
        agent_scores = {}
        skill_matches = {}
        
        for agent_id, agent_card in self.agents.items():
            score, matched_skills = self._calculate_agent_score(request, agent_card)
            agent_scores[agent_id] = score
            skill_matches[agent_id] = matched_skills
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        # Default to argocd if no clear winner
        if best_agent is None:
            best_agent = "argocd"
            best_score = 0.3
        
        # Calculate confidence (0.0 to 1.0)
        confidence = min(best_score / 5.0, 1.0)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(request, best_agent, agent_scores, skill_matches)
        
        state.update({
            "selected_agent": best_agent,
            "confidence": confidence,
            "reasoning": reasoning,
            "metadata": {
                "request_id": str(uuid.uuid4()),
                "start_timestamp": datetime.now().isoformat(),
                "agent_scores": agent_scores,
                "skill_matches": skill_matches,
                "analysis_timestamp": datetime.now().isoformat()
            }
        })
        
        return state
    
    def _calculate_agent_score(self, request: str, agent_card: AgentCard) -> tuple[float, List[str]]:
        """
        Calculate score for an agent based on keywords and skills matching.
        
        Scoring mechanism:
        - Keyword matching from skill tags: +1.0 points per match
        - Skill matching via _skill_matches_request: +1.5 points per match
        
        Examples:
        
        1. Math calculation request: "what is 2+3"
            - Math Agent: 
              * Keywords: "what is", "+" → +2.0 points (from skill tags)
              * Skills: "arithmetic_calculation" (matches "what is", "+") → +1.5 points
              * Total: 3.5 points
            - Currency Agent: 0.0 points (no matches)
            - ArgoCD Agent: 0.0 points (no matches)
            → Math Agent selected (highest score)

        2. Currency conversion request: "how much is 10 USD in INR?"
            - Currency Agent:
              * Keywords: "usd", "inr" → +2.0 points (from skill tags)
              * Skills: "currency_exchange" (matches "usd", "inr") → +1.5 points
              * Total: 3.5 points
            - Math Agent: 0.0 points (no currency-specific matches)
            - ArgoCD Agent: 0.0 points (no matches)
            → Currency Agent selected (highest score)
        
        3. ArgoCD management request: "sync my kubernetes application"
            - ArgoCD Agent:
             * Keywords: "kubernetes", "sync" → +2.0 points
             * Skills: "sync_operations" (matches "sync"), "kubernetes_management" (matches "kubernetes") → +3.0 points
             * Total: 5.0 points
            - Math Agent: 0.0 points (no matches)
            - Currency Agent: 0.0 points (no matches) 
            → ArgoCD Agent selected (highest score)
        
        Returns:
            tuple[float, List[str]]: (total_score, list_of_matched_skill_names)
        """
        score = 0.0
        matched_skills = []
        
        request_lower = request.lower()
        
                # Keyword matching from skill tags (weight: 1.0)
        keywords = [tag for skill in agent_card.skills for tag in (skill.tags or [])]
        for keyword in keywords:
            if keyword.lower() in request_lower:
                score += 1.0

        # Skill matching (weight: 1.5 - no confidence field available)
        for skill in agent_card.skills:
            if self._skill_matches_request(skill.name, request):
                score += 1.5
                matched_skills.append(skill.name)
        
        return score, matched_skills
    
    def _skill_matches_request(self, skill_name: str, request: str) -> bool:
        """Check if a skill matches the request content using dynamic keywords from available agents"""
        # Get keywords for this skill from the dynamically built skill_keywords
        keywords = self.skill_keywords.get(skill_name, [])
        request_lower = request.lower()
        
        return any(keyword in request_lower for keyword in keywords)
    
    def _generate_reasoning(self, request: str, selected_agent: str, agent_scores: Dict, skill_matches: Dict) -> str:
        """Generate human-readable reasoning for the routing decision"""
        agent_card = self.agents[selected_agent]
        
                # Find matched keywords from skill tags
        matched_keywords = []
        request_lower = request.lower()
        keywords = [tag for skill in agent_card.skills for tag in (skill.tags or [])]

        for keyword in keywords:
            if keyword.lower() in request_lower:
                matched_keywords.append(keyword)
        
        # Get matched skills
        matched_skills = skill_matches.get(selected_agent, [])
        
        reasoning_parts = [f"Selected {agent_card.name}"]
        
        if matched_keywords:
            reasoning_parts.append(f"based on keywords: {', '.join(matched_keywords)}")
        
        if matched_skills:
            if matched_keywords:
                reasoning_parts.append(f"and skills: {', '.join(matched_skills)}")
            else:
                reasoning_parts.append(f"based on skills: {', '.join(matched_skills)}")
        
        if not matched_keywords and not matched_skills:
            reasoning_parts.append("using default ArgoCD agent")
        
        return " ".join(reasoning_parts)
    
    async def _route_to_agent(self, state: RouterState) -> RouterState:
        """Route the request to the selected agent"""
        selected_agent = state["selected_agent"]
        request = state["request"]
        
        agent_card = self.agents[selected_agent]
        endpoint = agent_card.url
        
        state["metadata"]["agent_endpoint"] = endpoint
        
        try:
            # Forward the request to the selected agent and get the actual response
            actual_response = await self._forward_request_to_agent(endpoint, request)
            state["response"] = f"🎯 Routed to {agent_card.name} → {actual_response}"
            state["metadata"]["status"] = "completed"
        except Exception as e:
            # Fallback to routing information if forwarding fails
            state["response"] = f"🎯 Smart Routing Decision\n\n"
            state["response"] += f"✅ Selected Agent: {agent_card.name}\n"
            state["response"] += f"🔗 Endpoint: {endpoint}\n"
            state["response"] += f"📊 Confidence: {state.get('confidence', 0):.2f}\n"
            state["response"] += f"🧠 Reasoning: {state.get('reasoning', 'No reasoning provided')}\n\n"
            state["response"] += f"⚠️ Could not forward request: {str(e)}\n"
            state["response"] += f"💡 Connect directly to {agent_card.name} at {endpoint}"
            state["metadata"]["status"] = "routing_only"
        
        state["metadata"]["response_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _forward_request_to_agent(self, endpoint: str, request: str) -> str:
        """Forward request to agent using A2A protocol"""
        import json
        from uuid import uuid4
        
        # Create A2A JSON-RPC request payload using message/send method
        task_id = str(uuid4())
        message_id = str(uuid4())
        context_id = str(uuid4())
        
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": "message/send",
            "params": {
                "id": task_id,
                "message": {
                    "role": "user",
                    "messageId": message_id,
                    "contextId": context_id,
                    "parts": [
                        {
                            "type": "text",
                            "text": request
                        }
                    ]
                },
                "configuration": {
                    "acceptedOutputModes": ["text"]
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Send task to agent
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Check for JSON-RPC error
                if "error" in result:
                    raise Exception(f"Agent returned error: {result['error']}")
                
                # Get the response from message/send
                if "result" not in result:
                    raise Exception("No result in agent response")
                
                message_result = result["result"]
                
                # For message/send, the response might be a Task or Message
                if isinstance(message_result, dict):
                    # If it's a Task, we need to poll for completion
                    if "id" in message_result and "status" in message_result:
                        task_id = message_result["id"]
                        
                        # Poll for task completion
                        for attempt in range(30):  # Poll for up to 30 seconds
                            await asyncio.sleep(1)
                            
                            get_payload = {
                                "jsonrpc": "2.0",
                                "id": str(uuid4()),
                                "method": "tasks/get",
                                "params": {
                                    "id": task_id
                                }
                            }
                            
                            get_response = await client.post(
                                endpoint,
                                json=get_payload,
                                headers={"Content-Type": "application/json"}
                            )
                            get_response.raise_for_status()
                            
                            get_result = get_response.json()
                            
                            if "result" in get_result and get_result["result"]:
                                task_data = get_result["result"]
                                
                                # Check task state
                                task_state = task_data.get("status", {}).get("state")
                                
                                if task_state == "completed":
                                    # Extract response from artifacts
                                    artifacts = task_data.get("artifacts", [])
                                    if artifacts:
                                        for artifact in artifacts:
                                            parts = artifact.get("parts", [])
                                            for part in parts:
                                                if part.get("kind") == "text":
                                                    return part.get("text", "No text in response")
                                    
                                    return "Task completed but no response text found"
                                elif task_state == "failed":
                                    return "Agent task failed"
                                elif task_state == "input-required":
                                    # Extract response from status message for input-required state
                                    status_message = task_data.get("status", {}).get("message", {})
                                    if status_message:
                                        parts = status_message.get("parts", [])
                                        for part in parts:
                                            if part.get("kind") == "text":
                                                return part.get("text", "No text in input-required response")
                                    return "Agent requires input but no message provided"
                        
                        return "Task did not complete within timeout"
                    
                    # If it's a direct Message response
                    elif "parts" in message_result:
                        for part in message_result.get("parts", []):
                            if part.get("type") == "text":
                                return part.get("text", "No text in message")
                        return "Message received but no text content"
                
                return "Unexpected response format from agent"
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Request forwarding failed: {str(e)}")

    async def process_request(self, request: str) -> Dict:
        """Process a request through the LangGraph workflow"""
        initial_state = RouterState(
            request=request,
            selected_agent="",
            confidence=0.0,
            reasoning="",
            response="",
            error="",
            metadata={}
        )
        
        try:
            final_state = await self.workflow.ainvoke(initial_state)
            
            agent_card = self.agents[final_state["selected_agent"]]
            
            return {
                "success": True,
                "request": request,
                "selected_agent_id": final_state["selected_agent"],
                "selected_agent_name": agent_card.name,
                "agent_skills": [skill.name for skill in agent_card.skills],
                "confidence": final_state["confidence"],
                "reasoning": final_state["reasoning"],
                "response": final_state["response"],
                "metadata": final_state["metadata"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "request": request,
                "error": str(e),
                "metadata": {
                    "request_id": str(uuid.uuid4()),
                    "error_timestamp": datetime.now().isoformat()
                }
            } 