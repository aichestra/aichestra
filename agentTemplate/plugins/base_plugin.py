"""
Base Plugin Interface
All plugins must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PluginError(Exception):
    """Base plugin exception"""
    pass

class PluginInitializationError(PluginError):
    """Plugin initialization error"""
    pass

class PluginExecutionError(PluginError):
    """Plugin execution error"""
    pass

class PluginConnectionError(PluginError):
    """Plugin connection error"""
    pass

class BasePlugin(ABC):
    """Base plugin interface that all plugins must implement"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the plugin with configuration
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__
        self.tools = []
        self.is_initialized = False
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the plugin
        Must be called before using the plugin
        """
        pass
    
    @abstractmethod
    async def load_tools(self) -> List[Any]:
        """
        Load tools for this plugin
        
        Returns:
            List of tool objects that can be used with LangGraph
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources when plugin is no longer needed
        """
        pass
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """
        Get plugin information
        
        Returns:
            Dictionary containing plugin metadata
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the plugin
        
        Returns:
            Dictionary with health status information
        """
        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "plugin_name": self.name,
            "tool_count": len(self.tools),
            "config_valid": self.validate_config()
        }
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration
        
        Returns:
            True if configuration is valid, False otherwise
        """
        return self.config is not None and isinstance(self.config, dict)
    
    def get_tool_names(self) -> List[str]:
        """
        Get list of tool names provided by this plugin
        
        Returns:
            List of tool names
        """
        return [tool.name for tool in self.tools if hasattr(tool, 'name')]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """
        Get tool descriptions
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        descriptions = {}
        for tool in self.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                descriptions[tool.name] = tool.description
        return descriptions
    
    async def test_connection(self) -> bool:
        """
        Test plugin connection/functionality
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update plugin configuration
        
        Args:
            updates: Configuration updates
        """
        self.config.update(updates)
        self.logger.info(f"Updated configuration: {updates}")
    
    def log_info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(f"[{self.name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(f"[{self.name}] {message}")
    
    def __str__(self) -> str:
        return f"{self.name}(initialized={self.is_initialized}, tools={len(self.tools)})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})" 