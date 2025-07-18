"""
MCP Plugin Implementation
Integrates with Model Context Protocol servers.
"""

import asyncio
import os
from typing import List, Any, Dict
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools

from .base_plugin import BasePlugin, PluginInitializationError, PluginConnectionError

class MCPPlugin(BasePlugin):
    """Plugin for integrating with MCP servers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = None
        self.server_process = None
        self.command_parts = []
        self.server_params = None
        self._connection_active = False
    
    async def initialize(self) -> None:
        """Initialize MCP plugin"""
        try:
            self.log_info("Initializing MCP plugin")
            
            # Parse MCP command
            mcp_command = self.get_config_value("command")
            if not mcp_command:
                raise PluginInitializationError("MCP command not configured")
            
            self.command_parts = mcp_command.split()
            if not self.command_parts:
                raise PluginInitializationError("Invalid MCP command")
            
            # Create server parameters
            self.server_params = StdioServerParameters(
                command=self.command_parts[0],
                args=self.command_parts[1:] if len(self.command_parts) > 1 else [],
                env=self.get_config_value("env_vars", {})
            )
            
            # Test connection
            await self._test_mcp_connection()
            
            self.is_initialized = True
            self.log_info("MCP plugin initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize MCP plugin: {e}")
            raise PluginInitializationError(f"MCP plugin initialization failed: {e}")
    
    async def load_tools(self) -> List[Any]:
        """Load tools from MCP server"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            self.log_info("Loading tools from MCP server")
            
            # Create new connection for tool loading
            timeout = self.get_config_value("timeout", 30)
            
            if self.server_params is None:
                raise PluginConnectionError("Server parameters not initialized")
            
            async with asyncio.timeout(timeout):
                async with stdio_client(self.server_params) as (read_stream, write_stream):
                    session = ClientSession(read_stream, write_stream)
                    await session.initialize()
                    
                    # Load MCP tools
                    tools = await load_mcp_tools(session)
                    
                    if not tools:
                        self.log_warning("No tools loaded from MCP server")
                        return []
                    
                    self.tools = tools
                    self.log_info(f"Loaded {len(tools)} tools from MCP server")
                    
                    # Log tool information
                    for tool in tools:
                        if hasattr(tool, 'name'):
                            self.log_info(f"  - {tool.name}: {getattr(tool, 'description', 'No description')}")
                    
                    return tools
        
        except asyncio.TimeoutError:
            error_msg = f"MCP server connection timeout after {timeout} seconds"
            self.log_error(error_msg)
            raise PluginConnectionError(error_msg)
        
        except Exception as e:
            self.log_error(f"Failed to load tools from MCP server: {e}")
            raise PluginConnectionError(f"Failed to load MCP tools: {e}")
    
    async def _test_mcp_connection(self) -> None:
        """Test MCP server connection"""
        try:
            self.log_info("Testing MCP server connection")
            
            timeout = self.get_config_value("timeout", 30)
            
            if self.server_params is None:
                raise PluginConnectionError("Server parameters not initialized")
            
            async with asyncio.timeout(timeout):
                async with stdio_client(self.server_params) as (read_stream, write_stream):
                    session = ClientSession(read_stream, write_stream)
                    await session.initialize()
                    
                    # Test basic connection
                    self._connection_active = True
                    self.log_info("MCP server connection successful")
        
        except asyncio.TimeoutError:
            error_msg = f"MCP server connection timeout after {timeout} seconds"
            self.log_error(error_msg)
            raise PluginConnectionError(error_msg)
        
        except Exception as e:
            self.log_error(f"MCP server connection failed: {e}")
            raise PluginConnectionError(f"MCP server connection failed: {e}")
    
    async def cleanup(self) -> None:
        """Clean up MCP plugin resources"""
        try:
            self.log_info("Cleaning up MCP plugin")
            
            if self.session:
                # Close session if it exists
                self.session = None
            
            self._connection_active = False
            self.tools = []
            self.is_initialized = False
            
            self.log_info("MCP plugin cleanup completed")
        
        except Exception as e:
            self.log_error(f"Error during MCP plugin cleanup: {e}")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get MCP plugin information"""
        return {
            "name": self.name,
            "type": "mcp",
            "version": "1.0.0",
            "description": "Model Context Protocol integration plugin",
            "command": self.get_config_value("command"),
            "connection_active": self._connection_active,
            "tools_loaded": len(self.tools),
            "supported_features": [
                "stdio_transport",
                "async_tools",
                "tool_discovery",
                "session_management"
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP plugin"""
        base_health = await super().health_check()
        
        # Add MCP-specific health information
        mcp_health = {
            "mcp_command": self.get_config_value("command"),
            "connection_active": self._connection_active,
            "server_accessible": False
        }
        
        # Test server accessibility
        try:
            await self._test_mcp_connection()
            mcp_health["server_accessible"] = True
        except Exception as e:
            mcp_health["server_error"] = str(e)
        
        base_health.update(mcp_health)
        return base_health
    
    def validate_config(self) -> bool:
        """Validate MCP plugin configuration"""
        if not super().validate_config():
            return False
        
        # Check required configuration
        command = self.get_config_value("command")
        if not command or not isinstance(command, str):
            self.log_error("MCP command is required and must be a string")
            return False
        
        # Check if command is executable
        command_parts = command.split()
        if not command_parts:
            self.log_error("MCP command cannot be empty")
            return False
        
        # Validate timeout
        timeout = self.get_config_value("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            self.log_error("MCP timeout must be a positive integer")
            return False
        
        return True
    
    async def reconnect(self) -> bool:
        """Reconnect to MCP server"""
        try:
            self.log_info("Attempting to reconnect to MCP server")
            
            # Cleanup existing connection
            await self.cleanup()
            
            # Reinitialize
            await self.initialize()
            
            # Reload tools
            await self.load_tools()
            
            self.log_info("Successfully reconnected to MCP server")
            return True
        
        except Exception as e:
            self.log_error(f"Failed to reconnect to MCP server: {e}")
            return False
    
    def get_mcp_command(self) -> str:
        """Get the MCP command being used"""
        return self.get_config_value("command", "")
    
    def get_timeout(self) -> int:
        """Get connection timeout"""
        return self.get_config_value("timeout", 30)
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self._connection_active and self.is_initialized 