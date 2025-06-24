#!/usr/bin/env python3
"""
Smart Orchestrator Agent with A2A SDK integration and Generic Multi-Agent Collaboration
"""
import asyncio
import uuid
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Any, Union
from dataclasses import dataclass

import httpx
from langgraph.graph import StateGraph
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.client import A2AClient, A2ACardResolver

@dataclass
class TaskRequirement:
    """Represents a required capability for completing a task"""
    capability_type: str
    description: str
    input_format: str = "user request"
    output_format: str = "processed response"
    priority: float = 1.0

@dataclass
class ExecutionStep:
    """Represents a single execution step in multi-agent workflow"""
    step_id: str
    agent_id: str
    task_description: str
    input_dependencies: List[str]
    output_key: str
    required_capabilities: List[str]

class RouterState(TypedDict):
    request: str
    selected_agent: str
    confidence: float
    reasoning: str
    response: str
    error: str
    metadata: dict

class MultiAgentRouterState(TypedDict):
    request: str
    execution_type: str
    task_requirements: List[Dict]
    execution_plan: List[Dict]
    current_step: int
    intermediate_results: Dict[str, str]
    final_response: str
    confidence: float
    reasoning: str
    error: str
    metadata: dict


class SmartOrchestrator:
    """Intelligent orchestrator using A2A SDK types and LangGraph workflow with generic multi-agent collaboration"""
    
    def __init__(self, initialize_default_agents: bool = True):
        self.agents: Dict[str, AgentCard] = {}
        self.skill_keywords: Dict[str, List[str]] = {}
        self.capability_registry: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self.workflow = self._create_workflow()
        self.multi_agent_workflow = self._create_multi_agent_workflow()
        if initialize_default_agents:
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
        
        # Update skill keywords and capability registry after loading all default agents
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
        """Update skill keywords and capability registry based on currently available agents"""
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
        
        # Build capability registry
        self._update_capability_registry()
        
        print(f"Updated skill keywords for {len(self.skill_keywords)} skills from {len(self.agents)} agents")
    
    def _update_capability_registry(self):
        """Build capability registry from available agents - completely dynamic"""
        self.capability_registry = {}
        
        for agent_id, agent_card in self.agents.items():
            # Extract capabilities from agent card
            agent_capabilities = set()
            
            # From skills
            for skill in agent_card.skills:
                # Add skill name as capability
                skill_capability = skill.name.lower().replace('_', ' ').replace('-', ' ')
                agent_capabilities.add(skill_capability)
                
                # Add individual words from skill name
                for word in skill_capability.split():
                    if len(word) > 2:  # Avoid very short words
                        agent_capabilities.add(word)
                
                # Add from tags
                if skill.tags:
                    for tag in skill.tags:
                        if len(tag) > 2:
                            agent_capabilities.add(tag.lower())
                
                # Add from description keywords
                if skill.description:
                    # Extract meaningful words from description
                    desc_words = re.findall(r'\b\w{3,}\b', skill.description.lower())
                    for word in desc_words[:10]:  # Limit to avoid noise
                        if word not in {'the', 'and', 'for', 'with', 'this', 'that', 'can', 'will'}:
                            agent_capabilities.add(word)
            
            # From agent name and description
            if agent_card.name:
                name_words = re.findall(r'\b\w{3,}\b', agent_card.name.lower())
                agent_capabilities.update(name_words)
            
            if agent_card.description:
                desc_words = re.findall(r'\b\w{3,}\b', agent_card.description.lower())
                agent_capabilities.update(desc_words[:5])  # Limit to key words
            
            # Register all capabilities for this agent
            for capability in agent_capabilities:
                if capability not in self.capability_registry:
                    self.capability_registry[capability] = []
                
                if agent_id not in self.capability_registry[capability]:
                    self.capability_registry[capability].append(agent_id)
        
        # Remove overly common capabilities that don't discriminate well
        common_words = {'agent', 'service', 'system', 'manage', 'handle', 'process', 'operation', 'data'}
        for word in common_words:
            if word in self.capability_registry and len(self.capability_registry[word]) >= len(self.agents):
                del self.capability_registry[word]
        
        print("--------------agent capabilities registry------------------")
        print(self.capability_registry)
        print("--------------agent capabilities registry------------------")
        print(f"Built capability registry with {len(self.capability_registry)} capabilities from {len(self.agents)} agents")
        print(f"Available capabilities: {list(self.capability_registry.keys())}")
    
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
    
    def _create_multi_agent_workflow(self):
        """Create generic multi-agent workflow"""
        workflow = StateGraph(MultiAgentRouterState)
        
        workflow.add_node("analyze", self._analyze_request_requirements)
        workflow.add_node("plan", self._create_execution_plan)
        workflow.add_node("execute", self._execute_current_step)
        workflow.add_node("aggregate", self._aggregate_results)
        
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "execute")
        
        # Conditional edges for step execution
        workflow.add_conditional_edges(
            "execute",
            self._should_continue_execution,
            {
                "continue": "execute",
                "finish": "aggregate"
            }
        )
        
        workflow.set_entry_point("analyze")
        workflow.set_finish_point("aggregate")
        
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
        
        # Default to first available agent if no clear winner
        if best_agent is None:
            if self.agents:
                best_agent = list(self.agents.keys())[0]
                best_score = 0.3
            else:
                # No agents available - this is an error condition
                state.update({
                    "error": "No agents available for routing",
                    "metadata": {
                        "request_id": str(uuid.uuid4()),
                        "error_timestamp": datetime.now().isoformat()
                    }
                })
                return state
        
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
        
        The agent with the highest total score will be selected for routing.
        
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
            reasoning_parts.append("using default agent (no specific matches found)")
        
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
    
    # Generic Multi-Agent Workflow Methods
    
    async def _analyze_request_requirements(self, state: MultiAgentRouterState) -> MultiAgentRouterState:
        """Use generic analysis to identify required capabilities"""
        request = state["request"]
        
        # Use generic capability-based decomposition
        try:
            requirements_prompt = f"""
            Analyze this request and identify what capabilities are needed to complete it:
            Request: "{request}"
            
            Available capability types from registered agents:
            {json.dumps(list(self.capability_registry.keys()), indent=2)}
            
            Return a JSON list of required capabilities in this format:
            [
                {{
                    "capability_type": "capability_name",
                    "description": "what needs to be done",
                    "input_format": "what input is needed",
                    "output_format": "what output should be produced",
                    "priority": 1.0
                }}
            ]
            
            If multiple capabilities are needed, list them in execution order.
            If only one capability is needed, return a single-item list.
            """
            
            task_requirements = await self._call_llm_for_decomposition(requirements_prompt)
            
            if len(task_requirements) > 1:
                state["execution_type"] = "multi"
                state["reasoning"] = f"Multi-capability request requiring: {', '.join([req['capability_type'] for req in task_requirements])}"
            else:
                state["execution_type"] = "single"
                state["reasoning"] = f"Single-capability request: {task_requirements[0]['capability_type']}"
            
            state["task_requirements"] = task_requirements
            state["confidence"] = 0.8  # Base confidence for generic decomposition
            
        except Exception as e:
            # Fallback to single-agent routing
            state["execution_type"] = "single"
            state["task_requirements"] = [{"capability_type": "general", "description": request}]
            state["reasoning"] = f"Fallback to single-agent routing: {str(e)}"
            state["confidence"] = 0.3
        
        return state
    
    async def _call_llm_for_decomposition(self, prompt: str) -> List[Dict]:
        """Call LLM to decompose request - truly generic implementation"""
        
        # Extract the original request from the prompt
        request_match = re.search(r'Request: "(.*?)"', prompt)
        if not request_match:
            return [{"capability_type": "general", "description": "General request processing"}]
        
        original_request = request_match.group(1)
        
        # Build decomposition using ONLY available capabilities
        available_capabilities = list(self.capability_registry.keys())
        
        if not available_capabilities:
            # No agents registered yet, fallback to general processing
            return [{"capability_type": "general", "description": original_request}]
        
        try:
            # This would be replaced with actual LLM call
            # For now, use generic pattern matching based on available capabilities
            return await self._generic_pattern_matching(original_request, available_capabilities)
            
        except Exception as e:
            # Ultimate fallback - use any available capability or general
            fallback_capability = available_capabilities[0] if available_capabilities else "general"
            return [{
                "capability_type": fallback_capability,
                "description": original_request,
                "input_format": "user request",
                "output_format": "processed response",
                "priority": 1.0
            }]

    async def _generic_pattern_matching(self, request: str, available_capabilities: List[str]) -> List[Dict]:
        """Generic pattern matching using only available capabilities"""
        
        request_lower = request.lower()
        
        # Score each available capability against the request
        capability_scores = {}
        for capability in available_capabilities:
            score = self._score_capability_match(request_lower, capability)
            if score > 0:
                capability_scores[capability] = score
        
        # Sort capabilities by relevance score
        sorted_capabilities = sorted(capability_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_capabilities:
            # No capabilities match, use first available or general
            fallback = available_capabilities[0] if available_capabilities else "general"
            return [{
                "capability_type": fallback,
                "description": request,
                "input_format": "user request",
                "output_format": "processed response",
                "priority": 1.0
            }]
        

        
        # Check if this looks like a multi-step request
        if self._is_multi_step_request(request_lower, sorted_capabilities):
            # Since multi-step detection already confirmed cross-domain operation,
            # proceed with multi-agent decomposition
            
            # True multi-agent case: select capabilities from different agents
            selected_capabilities = []
            used_agents = set()
            
            # First, add the highest scoring capability
            if sorted_capabilities:
                first_cap, first_score = sorted_capabilities[0]
                if first_score > 1.0:
                    selected_capabilities.append(first_cap)
                    if first_cap in self.capability_registry:
                        used_agents.update(self.capability_registry[first_cap])
            
            # Then, find capabilities from different agents
            for capability, score in sorted_capabilities[1:]:
                if score > 0.5:  # Lower threshold for secondary capabilities
                    # Check which agents can handle this capability
                    if capability in self.capability_registry:
                        cap_agents = set(self.capability_registry[capability])
                        # Only add if it brings in a new agent domain
                        if not cap_agents.intersection(used_agents):
                            selected_capabilities.append(capability)
                            used_agents.update(cap_agents)
                            break  # Stop after finding one cross-domain capability
            
            # If we ended up with only one capability, treat as single-agent
            if len(selected_capabilities) <= 1:
                best_capability = sorted_capabilities[0][0]
                return [{
                    "capability_type": best_capability,
                    "description": request,
                    "input_format": "user request", 
                    "output_format": "processed response",
                    "priority": 1.0
                }]
            
            # Create execution steps for true multi-agent case
            steps = []
            for i, capability in enumerate(selected_capabilities):
                # Create more descriptive task descriptions based on step position
                if i == 0:
                    task_desc = f"Process the {capability} components from this request: {request}"
                else:
                    task_desc = f"Use the previous results to handle the {capability} aspects and complete the request"
                
                steps.append({
                    "capability_type": capability,
                    "description": task_desc,
                    "input_format": "previous step output" if i > 0 else "user request",
                    "output_format": f"{capability} result",
                    "priority": 1.0 - (i * 0.1)  # Decreasing priority
                })
            
            return steps
        else:
            # Single capability request
            best_capability = sorted_capabilities[0][0]
            return [{
                "capability_type": best_capability,
                "description": request,
                "input_format": "user request", 
                "output_format": "processed response",
                "priority": 1.0
            }]

    def _score_capability_match(self, request_lower: str, capability: str) -> float:
        """Score how well a capability matches a request"""
        score = 0.0
        capability_lower = capability.lower()
        
        # Skip very generic capabilities that don't discriminate well
        generic_terms = {'what', 'is', 'the', 'and', 'for', 'with', 'can', 'will', 'get', 'set', 'do', 'make', 'use'}
        if capability_lower in generic_terms:
            return 0.1  # Very low score for generic terms
        
        # Special handling for single-character symbols (like operators)
        if len(capability_lower) == 1 and capability_lower in request_lower:
            score += 3.0  # High score for direct symbol match
        
        # Direct word match (higher weight for longer, more specific terms)
        if capability_lower in request_lower:
            # Give higher score for longer, more specific capabilities
            specificity_bonus = min(len(capability_lower) / 10.0, 1.0)
            score += 2.0 + specificity_bonus
        
        # Partial word match
        capability_words = capability_lower.split()
        for word in capability_words:
            if len(word) > 2 and word not in generic_terms and word in request_lower:
                # Higher score for domain-specific words
                word_bonus = 1.5 if len(word) > 4 else 1.0
                score += word_bonus
        
        # Check if any words from the request appear in capability (but with lower weight)
        request_words = request_lower.split()
        for word in request_words:
            if len(word) > 3 and word not in generic_terms and word in capability_lower:
                score += 0.3  # Lower weight for reverse matching
        
        # Boost capabilities that contain terms related to operations when symbols are present
        if any(symbol in request_lower for symbol in ['+', '-', '*', '/', '=', '<', '>']):
            if any(op_term in capability_lower for op_term in ['operation', 'calculation', 'compute', 'process']):
                score += 1.0  # Generic boost for operation-related capabilities
        
        return score

    def _is_multi_step_request(self, request_lower: str, sorted_capabilities: List[tuple]) -> bool:
        """Determine if request requires multiple capabilities - conservative approach"""
        
        # Check for explicit multi-step indicators
        multi_step_indicators = [
            'and then', 'then', 'after', 'followed by', 'next',
            'and also', 'combined with', 'together with'
        ]
        
        has_explicit_connectors = any(indicator in request_lower for indicator in multi_step_indicators)
        
        # Check for operations that might involve different domains - completely generic
        cross_domain_operation = False
        if len(sorted_capabilities) >= 2:
            # Look for capabilities that come from different agents
            # Consider more capabilities and lower the threshold for secondary capabilities
            for i in range(min(5, len(sorted_capabilities))):
                for j in range(i + 1, min(5, len(sorted_capabilities))):
                    cap1, score1 = sorted_capabilities[i]
                    cap2, score2 = sorted_capabilities[j]
                    
                    # Primary capability needs good score, secondary needs decent score
                    if score1 > 1.0 and score2 > 0.5:
                        # Check if they're handled by different agents
                        agents1 = set(self.capability_registry.get(cap1, []))
                        agents2 = set(self.capability_registry.get(cap2, []))
                        
                        # If no overlap in agents, this is cross-domain
                        if not agents1.intersection(agents2):
                            cross_domain_operation = True
                            break
                
                if cross_domain_operation:
                    break
        

        
        # Decision: multi-step if we have explicit indicators OR cross-domain operations
        if has_explicit_connectors or cross_domain_operation:
            return True
        
        return False

    async def _create_execution_plan(self, state: MultiAgentRouterState) -> MultiAgentRouterState:
        """Create execution plan by matching requirements to available agents"""
        task_requirements = state["task_requirements"]
        execution_plan = []
        
        for i, requirement in enumerate(task_requirements):
            capability_type = requirement["capability_type"]
            
            # Find best agent for this capability
            best_agent = self._find_best_agent_for_capability(capability_type, requirement)
            
            if not best_agent:
                state["error"] = f"No agent found for capability: {capability_type}"
                return state
            
            # Create execution step
            step = ExecutionStep(
                step_id=f"step_{i}",
                agent_id=best_agent,
                task_description=requirement["description"],
                input_dependencies=[f"step_{j}_output" for j in range(i)],
                output_key=f"step_{i}_output",
                required_capabilities=[capability_type]
            )
            
            execution_plan.append({
                "step_id": step.step_id,
                "agent_id": step.agent_id,
                "task_description": step.task_description,
                "input_dependencies": step.input_dependencies,
                "output_key": step.output_key
            })
        
        state["execution_plan"] = execution_plan
        state["current_step"] = 0
        state["intermediate_results"] = {}
        
        return state
    
    def _find_best_agent_for_capability(self, capability_type: str, requirement: Dict) -> Optional[str]:
        """Find the best agent for a specific capability - completely generic"""
        
        # Direct capability match
        if capability_type in self.capability_registry:
            candidate_agents = self.capability_registry[capability_type]
            
            # Score candidates based on relevance
            best_agent = None
            best_score = 0.0
            
            for agent_id in candidate_agents:
                agent_card = self.agents[agent_id]
                score = self._score_agent_for_capability(agent_card, capability_type, requirement)
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
            
            return best_agent
        
        # Fuzzy matching if no direct match
        for registered_capability, agent_ids in self.capability_registry.items():
            if capability_type in registered_capability or registered_capability in capability_type:
                return agent_ids[0]  # Return first matching agent
        
        # Fallback to any agent if no specific match
        if self.agents:
            return list(self.agents.keys())[0]
        
        return None
    
    def _score_agent_for_capability(self, agent_card: AgentCard, capability_type: str, requirement: Dict) -> float:
        """Score an agent's suitability for a specific capability"""
        score = 0.0
        
        for skill in agent_card.skills:
            # Skill name matching
            if capability_type.lower() in skill.name.lower():
                score += 2.0
            
            # Tag matching
            if skill.tags:
                for tag in skill.tags:
                    if capability_type.lower() in tag.lower() or tag.lower() in capability_type.lower():
                        score += 1.5
            
            # Description matching
            if skill.description and capability_type in skill.description.lower():
                score += 1.0
        
        return score
    
    async def _execute_current_step(self, state: MultiAgentRouterState) -> MultiAgentRouterState:
        """Execute the current step in the execution plan"""
        current_step_idx = state["current_step"]
        execution_plan = state["execution_plan"]
        
        if current_step_idx >= len(execution_plan):
            return state
        
        step = execution_plan[current_step_idx]
        agent_id = step["agent_id"]
        task_description = step["task_description"]
        
        # Build task with dependencies
        full_task = self._build_task_with_dependencies(
            task_description, 
            step["input_dependencies"], 
            state["intermediate_results"],
            state["request"]
        )
        
        try:
            # Execute with selected agent
            agent_card = self.agents[agent_id]
            result = await self._forward_request_to_agent(agent_card.url, full_task)
            
            # Store result
            output_key = step["output_key"]
            state["intermediate_results"][output_key] = result
            
            # Update progress
            state["current_step"] += 1
            
            # Update metadata
            state["metadata"][f"step_{current_step_idx}"] = {
                "agent": agent_card.name,
                "task": task_description,
                "result": result
            }
            
        except Exception as e:
            state["error"] = f"Step {current_step_idx} failed: {str(e)}"
        
        return state
    
    def _build_task_with_dependencies(self, task_description: str, dependencies: List[str], 
                                    intermediate_results: Dict[str, str], original_request: str) -> str:
        """Build task description with dependency results - completely generic"""
        if not dependencies or not intermediate_results:
            return f"Original request: {original_request}\nTask: {task_description}"
        
        dependency_context = []
        for dep in dependencies:
            if dep in intermediate_results:
                dependency_context.append(f"{dep}: {intermediate_results[dep]}")
        
        if dependency_context:
            context_str = "\n".join(dependency_context)
            return f"Original request: {original_request}\nPrevious results:\n{context_str}\n\nYour task: {task_description}"
        else:
            return f"Original request: {original_request}\nTask: {task_description}"
    
    def _should_continue_execution(self, state: MultiAgentRouterState) -> str:
        """Determine if execution should continue"""
        if state.get("error"):
            return "finish"
        
        if state["current_step"] >= len(state["execution_plan"]):
            return "finish"
        
        return "continue"
    
    async def _aggregate_results(self, state: MultiAgentRouterState) -> MultiAgentRouterState:
        """Aggregate results from all execution steps"""
        if state.get("error"):
            state["final_response"] = f"❌ Multi-agent execution failed: {state['error']}"
        else:
            execution_plan = state["execution_plan"]
            intermediate_results = state["intermediate_results"]
            
            if state["execution_type"] == "multi":
                # Multi-agent collaboration result
                response_parts = ["🤝 Multi-Agent Collaboration Result:\n"]
                
                for i, step in enumerate(execution_plan):
                    agent_card = self.agents[step["agent_id"]]
                    result_key = step["output_key"]
                    result = intermediate_results.get(result_key, "No result")
                    
                    response_parts.append(f"Step {i+1} ({agent_card.name}): {result}")
                
                # Final answer is the last result
                final_keys = list(intermediate_results.keys())
                if final_keys:
                    final_result = intermediate_results[final_keys[-1]]
                    response_parts.append(f"\n🎯 Final Answer: {final_result}")
                
                state["final_response"] = "\n".join(response_parts)
            else:
                # Single agent result
                if intermediate_results:
                    result_key = list(intermediate_results.keys())[0]
                    result = intermediate_results[result_key]
                    agent_name = self.agents[execution_plan[0]["agent_id"]].name
                    state["final_response"] = f"🎯 Routed to {agent_name} → {result}"
                else:
                    state["final_response"] = "No results generated"
        
        return state
    
    async def process_multi_agent_request(self, request: str) -> Dict:
        """Process request through multi-agent workflow"""
        initial_state = MultiAgentRouterState(
            request=request,
            execution_type="",
            task_requirements=[],
            execution_plan=[],
            current_step=0,
            intermediate_results={},
            final_response="",
            confidence=0.0,
            reasoning="",
            error="",
            metadata={"request_id": str(uuid.uuid4())}
        )
        
        try:
            final_state = await self.multi_agent_workflow.ainvoke(initial_state)
            
            return {
                "success": True,
                "request": request,
                "execution_type": final_state["execution_type"],
                "task_requirements": final_state["task_requirements"],
                "execution_plan": final_state["execution_plan"],
                "confidence": final_state["confidence"],
                "reasoning": final_state["reasoning"],
                "response": final_state["final_response"],
                "metadata": final_state["metadata"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "request": request,
                "error": str(e),
                "metadata": {"request_id": str(uuid.uuid4())}
            }