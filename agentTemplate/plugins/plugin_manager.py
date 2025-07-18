"""
Plugin Manager
Manages loading and lifecycle of plugins.
"""

import importlib
import logging
from typing import Dict, Any, List, Optional, Type

from .base_plugin import BasePlugin, PluginError, PluginInitializationError
from .mcp_plugin import MCPPlugin
from .api_plugin import APIPlugin
from config.plugin_config import get_plugin_type, get_plugin_config

logger = logging.getLogger(__name__)

class PluginManager:
    """Manages plugin loading and lifecycle"""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.active_plugin: Optional[BasePlugin] = None
        self.plugin_registry: Dict[str, Type[BasePlugin]] = {
            "mcp": MCPPlugin,
            "api": APIPlugin
        }
        
    def register_plugin(self, plugin_type: str, plugin_class: Type[BasePlugin]) -> None:
        """Register a new plugin type"""
        if not issubclass(plugin_class, BasePlugin):
            raise ValueError(f"Plugin class must inherit from BasePlugin")
        
        self.plugin_registry[plugin_type] = plugin_class
        logger.info(f"Registered plugin type: {plugin_type}")
    
    async def load_plugin(self, plugin_type: str = None) -> BasePlugin:
        """Load a plugin of the specified type"""
        if plugin_type is None:
            plugin_type = get_plugin_type()
        
        if plugin_type in self.plugins:
            logger.info(f"Plugin {plugin_type} already loaded")
            return self.plugins[plugin_type]
        
        try:
            logger.info(f"Loading plugin: {plugin_type}")
            
            # Get plugin class
            plugin_class = await self._get_plugin_class(plugin_type)
            
            # Get plugin configuration
            config = get_plugin_config(plugin_type)
            
            # Create plugin instance
            plugin = plugin_class(config)
            
            # Validate configuration
            if not plugin.validate_config():
                raise PluginInitializationError(f"Invalid configuration for plugin: {plugin_type}")
            
            # Initialize plugin
            await plugin.initialize()
            
            # Store plugin
            self.plugins[plugin_type] = plugin
            self.active_plugin = plugin
            
            logger.info(f"Successfully loaded plugin: {plugin_type}")
            return plugin
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_type}: {e}")
            raise PluginError(f"Failed to load plugin {plugin_type}: {e}")
    
    async def _get_plugin_class(self, plugin_type: str) -> Type[BasePlugin]:
        """Get plugin class for the specified type"""
        if plugin_type in self.plugin_registry:
            return self.plugin_registry[plugin_type]
        
        # Try to load custom plugin
        if plugin_type == "custom":
            return await self._load_custom_plugin()
        
        raise PluginError(f"Unknown plugin type: {plugin_type}")
    
    async def _load_custom_plugin(self) -> Type[BasePlugin]:
        """Load custom plugin dynamically"""
        try:
            config = get_plugin_config("custom")
            module_name = config.get("module")
            class_name = config.get("class")
            
            if not module_name or not class_name:
                raise PluginError("Custom plugin module and class must be specified")
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Get class
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, BasePlugin):
                raise PluginError(f"Custom plugin class {class_name} must inherit from BasePlugin")
            
            return plugin_class
            
        except Exception as e:
            raise PluginError(f"Failed to load custom plugin: {e}")
    
    async def get_active_plugin(self) -> Optional[BasePlugin]:
        """Get the currently active plugin"""
        if self.active_plugin is None:
            # Try to load default plugin
            try:
                return await self.load_plugin()
            except Exception as e:
                logger.error(f"Failed to load default plugin: {e}")
                return None
        
        return self.active_plugin
    
    async def get_plugin_tools(self, plugin_type: str = None) -> List[Any]:
        """Get tools from a plugin"""
        plugin = await self.load_plugin(plugin_type)
        return await plugin.load_tools()
    
    async def reload_plugin(self, plugin_type: str = None) -> BasePlugin:
        """Reload a plugin"""
        if plugin_type is None:
            plugin_type = get_plugin_type()
        
        # Cleanup existing plugin
        await self.unload_plugin(plugin_type)
        
        # Load fresh plugin
        return await self.load_plugin(plugin_type)
    
    async def unload_plugin(self, plugin_type: str) -> None:
        """Unload a plugin"""
        if plugin_type in self.plugins:
            plugin = self.plugins[plugin_type]
            await plugin.cleanup()
            del self.plugins[plugin_type]
            
            if self.active_plugin == plugin:
                self.active_plugin = None
            
            logger.info(f"Unloaded plugin: {plugin_type}")
    
    async def cleanup_all(self) -> None:
        """Clean up all plugins"""
        for plugin_type in list(self.plugins.keys()):
            await self.unload_plugin(plugin_type)
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin types"""
        return list(self.plugins.keys())
    
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugin types"""
        return list(self.plugin_registry.keys()) + ["custom"]
    
    async def get_plugin_info(self, plugin_type: str = None) -> Dict[str, Any]:
        """Get plugin information"""
        if plugin_type is None:
            plugin_type = get_plugin_type()
        
        plugin = await self.load_plugin(plugin_type)
        return plugin.get_plugin_info()
    
    async def health_check(self, plugin_type: str = None) -> Dict[str, Any]:
        """Perform health check on a plugin"""
        try:
            if plugin_type is None:
                plugin_type = get_plugin_type()
            
            plugin = await self.load_plugin(plugin_type)
            return await plugin.health_check()
            
        except Exception as e:
            return {
                "status": "error",
                "plugin_type": plugin_type,
                "error": str(e)
            }
    
    async def test_plugin_connection(self, plugin_type: str = None) -> bool:
        """Test plugin connection"""
        try:
            if plugin_type is None:
                plugin_type = get_plugin_type()
            
            plugin = await self.load_plugin(plugin_type)
            return await plugin.test_connection()
            
        except Exception as e:
            logger.error(f"Plugin connection test failed: {e}")
            return False
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """Get overall plugin status"""
        return {
            "active_plugin": self.active_plugin.name if self.active_plugin else None,
            "loaded_plugins": self.get_loaded_plugins(),
            "available_plugins": self.get_available_plugins(),
            "plugin_count": len(self.plugins)
        }
    
    async def switch_plugin(self, new_plugin_type: str) -> BasePlugin:
        """Switch to a different plugin type"""
        logger.info(f"Switching to plugin: {new_plugin_type}")
        
        # Load new plugin
        new_plugin = await self.load_plugin(new_plugin_type)
        
        # Set as active
        self.active_plugin = new_plugin
        
        logger.info(f"Switched to plugin: {new_plugin_type}")
        return new_plugin
    
    async def get_plugin_tools_info(self, plugin_type: str = None) -> Dict[str, Any]:
        """Get information about plugin tools"""
        plugin = await self.load_plugin(plugin_type)
        
        return {
            "plugin_type": plugin_type or get_plugin_type(),
            "tool_count": len(plugin.tools),
            "tool_names": plugin.get_tool_names(),
            "tool_descriptions": plugin.get_tool_descriptions()
        }

# Global plugin manager instance
plugin_manager = PluginManager()

# Convenience functions
async def get_plugin_tools() -> List[Any]:
    """Get tools from the active plugin"""
    return await plugin_manager.get_plugin_tools()

async def get_active_plugin() -> Optional[BasePlugin]:
    """Get the active plugin"""
    return await plugin_manager.get_active_plugin()

async def reload_plugins() -> None:
    """Reload all plugins"""
    await plugin_manager.cleanup_all()
    await plugin_manager.load_plugin()

async def plugin_health_check() -> Dict[str, Any]:
    """Perform health check on active plugin"""
    return await plugin_manager.health_check()

def get_plugin_status() -> Dict[str, Any]:
    """Get plugin status"""
    return plugin_manager.get_plugin_status() 