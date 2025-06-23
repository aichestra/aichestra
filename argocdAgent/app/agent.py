import os
import asyncio
from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Response format for the ArgoCD agent."""
    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class ArgoCDAgent:
    """
    ArgoCDAgent - a specialized assistant for ArgoCD management via MCP stdio.
    
    This agent connects to ArgoCD via the MCP stdio protocol and provides
    natural language interface to ArgoCD operations.
    """
    SYSTEM_INSTRUCTION = (
        'You are a specialized assistant for ArgoCD management. '
        'Your sole purpose is to use the ArgoCD MCP tools to help users manage their ArgoCD deployments. '
        'You can list applications, get application details, sync applications, and more. '
        'If the user asks about anything other than ArgoCD management, '
        'politely state that you cannot help with that topic and can only assist with ArgoCD-related queries. '
        'Do not attempt to answer unrelated questions or use tools for other purposes. '
        'Set response status to input_required if the user needs to provide more information. '
        'Set response status to error if there is an error while processing the request. '
        'Set response status to completed if the request is complete. '
        'Always provide clear, concise responses about the ArgoCD operations you perform.'
    )

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        os.environ["ARGOCD_BASE_URL"] = os.getenv("ARGOCD_BASE_URL", "https://9.30.147.51:8080/")
        os.environ["ARGOCD_API_TOKEN"] = os.getenv("ARGOCD_API_TOKEN", "")
        self.tools = []
        self.mcp_session = None
        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=ResponseFormat,
        )

    async def _init_mcp_tools(self):
        """Initialize MCP tools using stdio transport, with direct API fallback."""
        if self.tools:
            return self.tools
            
        # Set environment variables before creating the server parameters
        os.environ["ARGOCD_BASE_URL"] = os.getenv("ARGOCD_BASE_URL", "https://9.30.147.51:8080/")
        os.environ["ARGOCD_API_TOKEN"] = os.getenv("ARGOCD_API_TOKEN", "")
        os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
        
        # First try MCP stdio transport
        mcp_command_str = os.getenv('ARGOCD_MCP_COMMAND', 'npx argocd-mcp@latest stdio')
        cmd_parts = mcp_command_str.split()
        command = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []
        
        server_params = StdioServerParameters(command=command, args=args)
        
        try:
            # Use a shorter timeout to fail faster if there are issues
            async with asyncio.timeout(10):
                async with stdio_client(server_params) as (read_stream, write_stream):
                    self.mcp_session = ClientSession(read_stream, write_stream)
                    tools = await load_mcp_tools(self.mcp_session)
                    print("Successfully initialized MCP stdio transport")
                    return tools
                    
        except Exception as e:
            print(f"MCP stdio transport failed: {str(e)}")
            print("Falling back to direct ArgoCD API client...")
            
            # Fallback to direct ArgoCD API
            try:
                from .argocd_direct import create_direct_tools
                tools, self.direct_client = create_direct_tools()
                
                # Convert direct tools to langchain-compatible tools
                from langchain_core.tools import StructuredTool
                langchain_tools = []
                
                for tool_def in tools:
                    def create_tool_func(handler, tool_name):
                        async def tool_func(**kwargs):
                            try:
                                result = await handler(**kwargs)
                                return f"Success: {result}"
                            except Exception as e:
                                return f"Error: {str(e)}"
                        tool_func.__name__ = tool_name
                        return tool_func
                    
                    langchain_tool = StructuredTool.from_function(
                        func=create_tool_func(tool_def["handler"], tool_def["name"]),
                        name=tool_def["name"],
                        description=tool_def["description"],
                        args_schema=None  # We'll handle this manually
                    )
                    langchain_tools.append(langchain_tool)
                
                print(f"Successfully initialized direct ArgoCD client with {len(langchain_tools)} tools")
                return langchain_tools
                
            except Exception as fallback_error:
                self.mcp_session = None
                raise RuntimeError(f"Both MCP stdio and direct API failed. MCP error: {str(e)}, Direct API error: {str(fallback_error)}")

    def invoke(self, query, context_id) -> dict:
        """
        Invoke the agent with a query.
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Returns:
            The agent's response as a dictionary
        """
        # For non-async usage, return a simulated response
        return {
            'is_task_complete': True,
            'require_user_input': False,
            'content': (
                "I'm the ArgoCD agent. To use my full capabilities with MCP, "
                "please use the async methods or run me in an async context. "
                f"Your query was: '{query}'"
            ),
        }

    async def ainvoke(self, query, context_id) -> dict:
        """
        Asynchronously invoke the agent with a query.
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Returns:
            The agent's response as a dictionary
        """
        if not self.tools:
            try:
                self.tools = await self._init_mcp_tools()
                self.graph = create_react_agent(
                    self.model,
                    tools=self.tools,
                    checkpointer=memory,
                    prompt=self.SYSTEM_INSTRUCTION,
                    response_format=ResponseFormat,
                )
            except Exception as e:
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': f"Error initializing MCP tools: {str(e)}",
                }
        config = {'configurable': {'thread_id': context_id}}
        self.graph.invoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(config)

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        """
        Stream the agent's response.
        
        Args:
            query: The user's query string
            context_id: A unique identifier for the conversation context
            
        Yields:
            Dictionaries containing the streaming response state
        """
        if not self.tools:
            yield {'is_task_complete': False, 'require_user_input': False, 'content': 'Initializing ArgoCD tools...'}
            try:
                self.tools = await self._init_mcp_tools()
                self.graph = create_react_agent(
                    self.model,
                    tools=self.tools,
                    checkpointer=memory,
                    prompt=self.SYSTEM_INSTRUCTION,
                    response_format=ResponseFormat,
                )
            except Exception as e:
                yield {'is_task_complete': False, 'require_user_input': True, 'content': f"Error initializing MCP tools: {str(e)}"}
                return
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id}}
        for item in self.graph.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if isinstance(message, AIMessage) and message.tool_calls:
                yield {'is_task_complete': False, 'require_user_input': False, 'content': 'Looking up ArgoCD information...'}
            elif isinstance(message, ToolMessage):
                yield {'is_task_complete': False, 'require_user_input': False, 'content': 'Processing ArgoCD tool response...'}
        yield self.get_agent_response(config)
    
    async def __del__(self):
        """Clean up resources when the agent is destroyed."""
        await self.cleanup()
        
    async def cleanup(self):
        """Explicitly clean up resources when done with the agent."""
        # Reset the session and process references
        self.mcp_session = None
        self.tools = []
        if hasattr(self, '_tools_loaded'):
            delattr(self, '_tools_loaded')
            
    async def check_argocd_server(self) -> tuple[bool, str]:
        """
        Check if the ArgoCD server is accessible.
        
        Returns:
            A tuple of (is_accessible, message)
        """
        import httpx
        
        base_url = os.getenv("ARGOCD_BASE_URL", "https://9.30.147.51:8080/")
        api_token = os.getenv("ARGOCD_API_TOKEN", "")
        
        if not api_token:
            return False, "ArgoCD API token is not configured"
            
        # Remove trailing slash if present
        if base_url.endswith('/'):
            base_url = base_url[:-1]
            
        # Try to access the ArgoCD API version endpoint
        try:
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            # Create a client that ignores SSL verification
            async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
                # Try the version endpoint first
                response = await client.get(f"{base_url}/api/version", headers=headers)
                if response.status_code == 200:
                    version_data = response.json()
                    version = version_data.get('Version', 'unknown')
                    return True, f"ArgoCD server is accessible (version: {version})"
                else:
                    return False, f"ArgoCD server returned status {response.status_code}"
                        
        except httpx.TimeoutException:
            return False, "Timeout connecting to ArgoCD server"
        except httpx.RequestError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        
    def get_agent_response(self, config):
        """
        Get the formatted agent response from the current state.
        
        Args:
            config: The configuration dictionary with thread_id
            
        Returns:
            A dictionary containing the response state and content
        """
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']