"""
Agent Template Core
Main agent implementation with pluggable tool support.
"""

import os
from collections.abc import AsyncIterable
from typing import Any, Literal, List, Dict, Optional, Union

from langchain_core.messages import AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, SecretStr

from config.agent_config import (
    AGENT_SYSTEM_INSTRUCTION,
    get_supported_content_types
)
from plugins.plugin_manager import plugin_manager

# Memory for conversation state
memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Response format for the agent"""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class TemplateAgent:
    """
    Template Agent - A pluggable agent built with A2A SDK and LangGraph
    
    This agent can work with different tool plugins:
    - MCP Plugin: For Model Context Protocol servers
    - API Plugin: For external REST APIs
    - Custom Plugin: For custom tool implementations
    """
    
    SUPPORTED_CONTENT_TYPES = get_supported_content_types()
    
    def __init__(self):
        self.model: Optional[Union[ChatGoogleGenerativeAI, ChatOpenAI]] = None
        self.tools: List[Any] = []
        self.graph = None
        self.plugin = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model"""
        # Try Google AI first
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            self.model = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=google_api_key,
                temperature=0
            )
        else:
            # Fall back to OpenAI
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.model = ChatOpenAI(
                    model=os.getenv("OPENAI_MODEL", "gpt-4"),
                    api_key=SecretStr(openai_api_key),
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    temperature=0
                )
            else:
                # Default to Google AI without explicit key
                self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0
                )
    
    async def _initialize_tools(self):
        """Initialize tools from the active plugin"""
        if not self.model:
            return False
            
        try:
            # Load plugin and tools
            self.plugin = await plugin_manager.get_active_plugin()
            if self.plugin:
                self.tools = await self.plugin.load_tools()
                
                # Create or update agent graph
                self.graph = create_react_agent(
                    self.model,
                    tools=self.tools,
                    checkpointer=memory,
                    prompt=AGENT_SYSTEM_INSTRUCTION,
                    response_format=ResponseFormat,
                )
                
                return True
            else:
                # No plugin available - create agent without tools
                self.tools = []
                self.graph = create_react_agent(
                    self.model,
                    tools=self.tools,
                    checkpointer=memory,
                    prompt=AGENT_SYSTEM_INSTRUCTION,
                    response_format=ResponseFormat,
                )
                return False
                
        except Exception as e:
            print(f"Error initializing tools: {e}")
            # Create agent without tools as fallback
            self.tools = []
            self.graph = create_react_agent(
                self.model,
                tools=self.tools,
                checkpointer=memory,
                prompt=AGENT_SYSTEM_INSTRUCTION,
                response_format=ResponseFormat,
            )
            return False
    
    async def invoke(self, query: str, context_id: str) -> Dict[str, Any]:
        """
        Invoke the agent with a query (sync interface)
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Returns:
            The agent's response as a dictionary
        """
        # For sync usage, return a basic response
        return {
            'is_task_complete': True,
            'require_user_input': False,
            'content': (
                "I'm the Template Agent. To use my full capabilities with plugins, "
                "please use the async methods or run me in an async context. "
                f"Your query was: '{query}'"
            ),
        }
    
    async def ainvoke(self, query: str, context_id: str) -> Dict[str, Any]:
        """
        Asynchronously invoke the agent with a query
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Returns:
            The agent's response as a dictionary
        """
        # Initialize tools if not already done
        if not self.graph:
            await self._initialize_tools()
        
        if not self.graph:
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': "Agent not properly initialized",
            }
        
        try:
            config = {'configurable': {'thread_id': context_id}}
            self.graph.invoke({'messages': [('user', query)]}, config)
            return self.get_agent_response(config)
            
        except Exception as e:
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f"Error processing request: {str(e)}",
            }
    
    async def stream(self, query: str, context_id: str) -> AsyncIterable[Dict[str, Any]]:
        """
        Stream the agent's response
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Yields:
            Dictionaries containing the streaming response state
        """
        # Initialize tools if not already done
        if not self.graph:
            yield {'is_task_complete': False, 'require_user_input': False, 'content': 'Initializing agent tools...'}
            tools_loaded = await self._initialize_tools()
            if not tools_loaded:
                yield {'is_task_complete': False, 'require_user_input': False, 'content': 'No plugin tools available - using basic capabilities...'}
        
        if not self.graph:
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': "Agent not properly initialized"
            }
            return
        
        try:
            inputs = {'messages': [('user', query)]}
            config = {'configurable': {'thread_id': context_id}}
            
            for item in self.graph.stream(inputs, config, stream_mode='values'):
                message = item['messages'][-1]
                
                if isinstance(message, AIMessage) and message.tool_calls:
                    plugin_type = self.plugin.name if self.plugin else "default"
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': f'Using {plugin_type} plugin tools...'
                    }
                elif isinstance(message, ToolMessage):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Processing tool response...'
                    }
            
            yield self.get_agent_response(config)
            
        except Exception as e:
            yield {
                'is_task_complete': False,
                'require_user_input': True,
                'content': f"Error during streaming: {str(e)}"
            }
    
    def get_agent_response(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the formatted agent response from the current state
        
        Args:
            config: The configuration dictionary with thread_id
            
        Returns:
            A dictionary containing the response state and content
        """
        if not self.graph:
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': 'Agent not properly initialized',
            }
        
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            elif structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            elif structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }
        
        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'Unable to process your request at the moment. '
                'Please try again.'
            ),
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        plugin_info = {}
        if self.plugin:
            plugin_info = self.plugin.get_plugin_info()
        
        return {
            "agent_type": "template",
            "model": self.model.model_name if hasattr(self.model, 'model_name') else "unknown",
            "plugin_info": plugin_info,
            "tools_available": len(self.tools),
            "supported_content_types": self.SUPPORTED_CONTENT_TYPES,
            "features": [
                "pluggable_tools",
                "streaming_responses",
                "multi_turn_conversation",
                "error_handling",
                "tool_switching"
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health = {
            "agent_status": "healthy",
            "model_initialized": self.model is not None,
            "tools_loaded": len(self.tools),
            "graph_initialized": self.graph is not None,
            "plugin_status": {}
        }
        
        if self.plugin:
            try:
                plugin_health = await self.plugin.health_check()
                health["plugin_status"] = plugin_health
            except Exception as e:
                health["plugin_status"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health
    
    async def reload_plugin(self) -> bool:
        """Reload the current plugin"""
        try:
            await plugin_manager.reload_plugin()
            await self._initialize_tools()
            return True
        except Exception as e:
            print(f"Error reloading plugin: {e}")
            return False
    
    async def switch_plugin(self, plugin_type: str) -> bool:
        """Switch to a different plugin"""
        try:
            await plugin_manager.switch_plugin(plugin_type)
            await self._initialize_tools()
            return True
        except Exception as e:
            print(f"Error switching plugin: {e}")
            return False
    
    async def get_plugin_info(self) -> Dict[str, Any]:
        """Get information about the current plugin"""
        if self.plugin:
            return self.plugin.get_plugin_info()
        return {"message": "No plugin loaded"}
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            await plugin_manager.cleanup_all()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor"""
        # Note: async cleanup should be called explicitly
        pass 