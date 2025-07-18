"""
Plugin Configuration
Define plugin settings and configurations here.
"""

import os
from typing import Dict, Any

def get_plugin_type():
    """Get the configured plugin type"""
    return os.getenv("TOOL_TYPE", "mcp").lower()

def get_mcp_config():
    """Get MCP plugin configuration"""
    return {
        "command": os.getenv("MCP_COMMAND", "python example_mcp_server.py"),
        "timeout": int(os.getenv("MCP_TIMEOUT", "30")),
        "retry_count": int(os.getenv("MCP_RETRY_COUNT", "3")),
        "env_vars": {
            # Pass through any environment variables that MCP server might need
            key: value for key, value in os.environ.items()
            if key.startswith("MCP_") or key in ["GOOGLE_API_KEY", "OPENAI_API_KEY"]
        }
    }

def get_api_config():
    """Get API plugin configuration"""
    return {
        "base_url": os.getenv("API_BASE_URL", "https://api.example.com"),
        "api_key": os.getenv("API_KEY", ""),
        "timeout": int(os.getenv("API_TIMEOUT", "10")),
        "rate_limit": int(os.getenv("API_RATE_LIMIT", "100")),
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": "A2A-Agent-Template/1.0"
        },
        "retry_config": {
            "enabled": os.getenv("ENABLE_RETRY", "true").lower() == "true",
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "delay": float(os.getenv("RETRY_DELAY", "1"))
        }
    }

def get_custom_config():
    """Get custom plugin configuration"""
    return {
        "module": os.getenv("CUSTOM_PLUGIN_MODULE", "plugins.custom_plugin"),
        "class": os.getenv("CUSTOM_PLUGIN_CLASS", "CustomPlugin"),
        "config": {
            # Add custom configuration parameters here
            "custom_param": os.getenv("CUSTOM_PARAM", "default_value")
        }
    }

def get_plugin_config(plugin_type: str | None = None) -> Dict[str, Any]:
    """Get configuration for a specific plugin type"""
    if plugin_type is None:
        plugin_type = get_plugin_type()
    
    config_map = {
        "mcp": get_mcp_config,
        "api": get_api_config,
        "custom": get_custom_config
    }
    
    if plugin_type not in config_map:
        raise ValueError(f"Unknown plugin type: {plugin_type}")
    
    return config_map[plugin_type]()

def get_all_plugin_configs():
    """Get all plugin configurations"""
    return {
        "mcp": get_mcp_config(),
        "api": get_api_config(),
        "custom": get_custom_config()
    }

# Plugin-specific settings
PLUGIN_SETTINGS = {
    "mcp": {
        "supports_streaming": True,
        "supports_async": True,
        "connection_pooling": False,
        "auto_reconnect": True
    },
    "api": {
        "supports_streaming": False,
        "supports_async": True,
        "connection_pooling": True,
        "auto_reconnect": False
    },
    "custom": {
        "supports_streaming": True,
        "supports_async": True,
        "connection_pooling": False,
        "auto_reconnect": False
    }
}

def get_plugin_settings(plugin_type: str | None = None):
    """Get plugin-specific settings"""
    if plugin_type is None:
        plugin_type = get_plugin_type()
    
    return PLUGIN_SETTINGS.get(plugin_type, {})

def validate_plugin_config(plugin_type: str | None = None):
    """Validate plugin configuration"""
    if plugin_type is None:
        plugin_type = get_plugin_type()
    
    if plugin_type == "mcp":
        config = get_mcp_config()
        if not config["command"]:
            raise ValueError("MCP_COMMAND is required for MCP plugin")
    
    elif plugin_type == "api":
        config = get_api_config()
        if not config["base_url"]:
            raise ValueError("API_BASE_URL is required for API plugin")
        if not config["api_key"]:
            print("Warning: API_KEY is not set for API plugin")
    
    elif plugin_type == "custom":
        config = get_custom_config()
        if not config["module"] or not config["class"]:
            raise ValueError("CUSTOM_PLUGIN_MODULE and CUSTOM_PLUGIN_CLASS are required for custom plugin")
    
    else:
        raise ValueError(f"Unknown plugin type: {plugin_type}")

# Tool-specific configurations
TOOL_CONFIGURATIONS = {
    "example_tool": {
        "name": "example_tool",
        "description": "An example tool for demonstration",
        "enabled": True,
        "config": {}
    }
}

def get_tool_config(tool_name: str):
    """Get configuration for a specific tool"""
    return TOOL_CONFIGURATIONS.get(tool_name, {}) 