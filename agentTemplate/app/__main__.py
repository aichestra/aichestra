#!/usr/bin/env python3
"""
Agent Template - Main Entry Point
A2A + LangGraph pluggable agent template
"""

import logging
import os
import sys

import click
import httpx
import uvicorn
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCard

from config.agent_config import (
    get_agent_name,
    get_agent_description,
    get_agent_port,
    get_agent_host,
    get_agent_version,
    get_agent_skills,
    get_agent_capabilities,
    get_supported_content_types
)
from config.plugin_config import get_plugin_type, validate_plugin_config
from app.agent import TemplateAgent
from app.agent_executor import TemplateAgentExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MissingConfigError(Exception):
    """Exception for missing configuration."""

def create_agent_card(host: str, port: int) -> AgentCard:
    """Create agent card for A2A registration"""
    return AgentCard(
        name=get_agent_name(),
        description=get_agent_description(),
        url=f'http://{host}:{port}/',
        version=get_agent_version(),
        defaultInputModes=get_supported_content_types(),
        defaultOutputModes=get_supported_content_types(),
        capabilities=get_agent_capabilities(),
        skills=get_agent_skills(),
    )

def validate_configuration():
    """Validate agent configuration"""
    # Check for required API keys
    if not os.getenv('GOOGLE_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        raise MissingConfigError(
            'Either GOOGLE_API_KEY or OPENAI_API_KEY environment variable must be set.'
        )
    
    # Validate plugin configuration
    try:
        validate_plugin_config()
    except Exception as e:
        raise MissingConfigError(f"Plugin configuration error: {e}")

def print_startup_info(host: str, port: int):
    """Print startup information"""
    plugin_type = get_plugin_type()
    
    print(f"🚀 Starting {get_agent_name()} on {host}:{port}")
    print(f"📝 Description: {get_agent_description()}")
    print(f"🔌 Plugin Type: {plugin_type}")
    print(f"🎯 Skills: {', '.join([skill.name for skill in get_agent_skills()])}")
    print()
    
    if plugin_type == "mcp":
        mcp_command = os.getenv("MCP_COMMAND", "Not configured")
        print(f"🔧 MCP Command: {mcp_command}")
    elif plugin_type == "api":
        api_url = os.getenv("API_BASE_URL", "Not configured")
        print(f"🌐 API Base URL: {api_url}")
    elif plugin_type == "custom":
        custom_module = os.getenv("CUSTOM_PLUGIN_MODULE", "Not configured")
        print(f"⚙️ Custom Plugin: {custom_module}")
    
    print()
    print("📚 Available endpoints:")
    print(f"  • Agent Card: http://{host}:{port}/.well-known/agent.json")
    print(f"  • Health Check: http://{host}:{port}/health")
    print(f"  • Plugin Status: http://{host}:{port}/plugin/status")
    print()

@click.command()
@click.option('--host', default=None, help='Host to bind to')
@click.option('--port', default=None, type=int, help='Port to bind to')
@click.option('--log-level', default='INFO', help='Logging level')
def main(host: str, port: int, log_level: str):
    """Start the Template Agent server"""
    
    # Set up logging
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))
    
    # Get configuration
    if host is None:
        host = get_agent_host()
    if port is None:
        port = get_agent_port()
    
    try:
        # Validate configuration
        validate_configuration()
        
        # Print startup information
        print_startup_info(host, port)
        
        # Create agent card
        agent_card = create_agent_card(host, port)
        
        # Create server components
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=TemplateAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )
        
        # Create A2A application
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        # Add custom routes for plugin management
        app = server.build()
        
        @app.get("/plugin/status")
        async def plugin_status():
            """Get plugin status"""
            from plugins.plugin_manager import get_plugin_status
            return get_plugin_status()
        
        @app.get("/plugin/health")
        async def plugin_health():
            """Get plugin health"""
            from plugins.plugin_manager import plugin_health_check
            return await plugin_health_check()
        
        @app.get("/capabilities")
        async def agent_capabilities():
            """Get agent capabilities"""
            agent = TemplateAgent()
            return await agent.get_capabilities()
        
        @app.get("/health")
        async def health():
            """Health check endpoint"""
            return {"status": "healthy", "agent": get_agent_name()}
        
        print("✅ Agent server starting...")
        print(f"🎯 Access your agent at: http://{host}:{port}")
        print()
        
        # Run server
        uvicorn.run(app, host=host, port=port, log_level=log_level.lower())
        
    except MissingConfigError as e:
        logger.error(f'Configuration Error: {e}')
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Quick Setup:")
        print("1. Copy .env.example to .env")
        print("2. Set GOOGLE_API_KEY or OPENAI_API_KEY")
        print("3. Configure TOOL_TYPE (mcp, api, or custom)")
        print("4. Set plugin-specific configuration")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f'Startup Error: {e}')
        print(f"\n❌ Startup Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 