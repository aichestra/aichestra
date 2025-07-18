"""
Agent Configuration
Define agent skills, capabilities, and properties here.
"""

import os
from a2a.types import AgentSkill, AgentCapabilities

def get_agent_skills():
    """Get agent skills - customize these for your specific agent"""
    return [
        AgentSkill(
            id="template_skill",
            name="Template Skill",
            description="A template skill for demonstration purposes",
            tags=["template", "example", "demo"],
            examples=[
                "This is a template example",
                "Show me template functionality",
                "Help me with template operations"
            ]
        ),
        AgentSkill(
            id="tool_integration",
            name="Tool Integration",
            description="Integrate with various tools and APIs",
            tags=["tools", "integration", "api", "mcp"],
            examples=[
                "Use the integrated tools",
                "Call external API",
                "Access MCP server functions"
            ]
        ),
        AgentSkill(
            id="data_processing",
            name="Data Processing",
            description="Process and analyze data from various sources",
            tags=["data", "processing", "analysis"],
            examples=[
                "Process this data",
                "Analyze the information",
                "Transform the input"
            ]
        )
    ]

def get_agent_capabilities():
    """Get agent capabilities"""
    return AgentCapabilities(
        streaming=True,
        pushNotifications=True,
        stateTransitionHistory=False
    )

def get_agent_name():
    """Get agent name from environment or default"""
    return os.getenv("AGENT_NAME", "TemplateAgent")

def get_agent_description():
    """Get agent description from environment or default"""
    return os.getenv(
        "AGENT_DESCRIPTION",
        "A pluggable agent template built with A2A SDK and LangGraph"
    )

def get_agent_port():
    """Get agent port from environment or default"""
    return int(os.getenv("AGENT_PORT", "8004"))

def get_agent_host():
    """Get agent host from environment or default"""
    return os.getenv("AGENT_HOST", "localhost")

def get_supported_content_types():
    """Get supported content types"""
    return ["text", "text/plain"]

def get_agent_version():
    """Get agent version"""
    return os.getenv("AGENT_VERSION", "1.0.0")

def get_agent_keywords():
    """Get agent keywords for orchestrator routing"""
    return [
        "template",
        "plugin",
        "tool",
        "integration",
        "mcp",
        "api",
        "custom"
    ]

# System instruction for the agent
AGENT_SYSTEM_INSTRUCTION = """
You are a pluggable agent built with A2A SDK and LangGraph. Your purpose is to:

1. Demonstrate the pluggable architecture capabilities
2. Use the configured tools (MCP, API, or custom) to help users
3. Provide clear, helpful responses using the available tools
4. Handle errors gracefully and provide meaningful error messages

Available tool types:
- MCP: Model Context Protocol servers
- API: External REST APIs
- Custom: Custom tool implementations

If you don't have the appropriate tools loaded for a request, explain what tools 
would be needed and how they could be configured.

Always provide helpful, accurate responses and use the tools available to you.
Set response status to 'input_required' if you need more information.
Set response status to 'error' if there's an error processing the request.
Set response status to 'completed' when the task is successfully completed.
""" 