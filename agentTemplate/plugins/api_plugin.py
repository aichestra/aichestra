"""
API Plugin Implementation
Integrates with external REST APIs.
"""

import asyncio
import json
from typing import List, Any, Dict, Optional
import httpx
from langchain_core.tools import tool

from .base_plugin import BasePlugin, PluginInitializationError, PluginConnectionError

class APIPlugin(BasePlugin):
    """Plugin for integrating with external REST APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        self.base_url = ""
        self.headers = {}
        self.timeout = 10
        self.rate_limit = 100
        self._request_count = 0
        
    async def initialize(self) -> None:
        """Initialize API plugin"""
        try:
            self.log_info("Initializing API plugin")
            
            # Get configuration
            self.base_url = self.get_config_value("base_url")
            if not self.base_url:
                raise PluginInitializationError("API base URL not configured")
            
            # Set up headers
            self.headers = self.get_config_value("headers", {})
            api_key = self.get_config_value("api_key")
            if api_key:
                self.headers["Authorization"] = f"Bearer {api_key}"
            
            # Set up other configuration
            self.timeout = self.get_config_value("timeout", 10)
            self.rate_limit = self.get_config_value("rate_limit", 100)
            
            # Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=self.timeout,
                verify=True
            )
            
            # Test connection
            await self._test_api_connection()
            
            self.is_initialized = True
            self.log_info("API plugin initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize API plugin: {e}")
            raise PluginInitializationError(f"API plugin initialization failed: {e}")
    
    async def load_tools(self) -> List[Any]:
        """Load tools for API integration"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            self.log_info("Loading API tools")
            
            # Create API tools
            tools = [
                self._create_get_tool(),
                self._create_post_tool(),
                self._create_put_tool(),
                self._create_delete_tool(),
                self._create_custom_request_tool()
            ]
            
            self.tools = tools
            self.log_info(f"Loaded {len(tools)} API tools")
            
            return tools
            
        except Exception as e:
            self.log_error(f"Failed to load API tools: {e}")
            raise PluginConnectionError(f"Failed to load API tools: {e}")
    
    def _create_get_tool(self):
        """Create GET request tool"""
        @tool
        def api_get(endpoint: str, params: Optional[Dict] = None) -> str:
            """
            Make a GET request to the API
            
            Args:
                endpoint: API endpoint path
                params: Optional query parameters
            
            Returns:
                API response as string
            """
            return asyncio.run(self._make_request("GET", endpoint, params=params))
        
        return api_get
    
    def _create_post_tool(self):
        """Create POST request tool"""
        @tool
        def api_post(endpoint: str, data: Optional[Dict] = None) -> str:
            """
            Make a POST request to the API
            
            Args:
                endpoint: API endpoint path
                data: Optional request body data
            
            Returns:
                API response as string
            """
            return asyncio.run(self._make_request("POST", endpoint, data=data))
        
        return api_post
    
    def _create_put_tool(self):
        """Create PUT request tool"""
        @tool
        def api_put(endpoint: str, data: Optional[Dict] = None) -> str:
            """
            Make a PUT request to the API
            
            Args:
                endpoint: API endpoint path
                data: Optional request body data
            
            Returns:
                API response as string
            """
            return asyncio.run(self._make_request("PUT", endpoint, data=data))
        
        return api_put
    
    def _create_delete_tool(self):
        """Create DELETE request tool"""
        @tool
        def api_delete(endpoint: str) -> str:
            """
            Make a DELETE request to the API
            
            Args:
                endpoint: API endpoint path
            
            Returns:
                API response as string
            """
            return asyncio.run(self._make_request("DELETE", endpoint))
        
        return api_delete
    
    def _create_custom_request_tool(self):
        """Create custom request tool"""
        @tool
        def api_custom_request(method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> str:
            """
            Make a custom HTTP request to the API
            
            Args:
                method: HTTP method (GET, POST, PUT, DELETE, etc.)
                endpoint: API endpoint path
                data: Optional request body data
                params: Optional query parameters
            
            Returns:
                API response as string
            """
            return asyncio.run(self._make_request(method, endpoint, data=data, params=params))
        
        return api_custom_request
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> str:
        """Make HTTP request to API"""
        if not self.client:
            raise PluginConnectionError("API client not initialized")
        
        # Check rate limit
        if self._request_count >= self.rate_limit:
            self.log_warning(f"Rate limit exceeded: {self._request_count}/{self.rate_limit}")
            await asyncio.sleep(1)  # Simple rate limiting
            self._request_count = 0
        
        try:
            self.log_info(f"Making {method} request to {endpoint}")
            
            # Prepare request
            request_kwargs = {
                "method": method,
                "url": endpoint,
                "timeout": self.timeout
            }
            
            if params:
                request_kwargs["params"] = params
            
            if data:
                request_kwargs["json"] = data
            
            # Make request
            response = await self.client.request(**request_kwargs)
            self._request_count += 1
            
            # Handle response
            if response.status_code >= 400:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                self.log_error(error_msg)
                return f"Error: {error_msg}"
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                return json.dumps(response_data, indent=2)
            except:
                return response.text
            
        except httpx.TimeoutException:
            error_msg = f"API request timeout after {self.timeout} seconds"
            self.log_error(error_msg)
            return f"Error: {error_msg}"
        
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            self.log_error(error_msg)
            return f"Error: {error_msg}"
    
    async def _test_api_connection(self) -> None:
        """Test API connection"""
        if not self.client:
            raise PluginConnectionError("API client not initialized")
        
        try:
            self.log_info("Testing API connection")
            
            # Try a simple request to test connectivity
            # Most APIs have a health or status endpoint
            test_endpoints = ["/health", "/status", "/", "/api/v1/health"]
            
            for endpoint in test_endpoints:
                try:
                    response = await self.client.get(endpoint, timeout=5)
                    if response.status_code < 500:  # Accept any non-server-error response
                        self.log_info(f"API connection successful via {endpoint}")
                        return
                except:
                    continue
            
            # If no test endpoint works, assume connection is okay
            self.log_info("API connection test completed (no test endpoint found)")
            
        except Exception as e:
            self.log_error(f"API connection test failed: {e}")
            raise PluginConnectionError(f"API connection test failed: {e}")
    
    async def cleanup(self) -> None:
        """Clean up API plugin resources"""
        try:
            self.log_info("Cleaning up API plugin")
            
            if self.client:
                await self.client.aclose()
                self.client = None
            
            self.tools = []
            self.is_initialized = False
            self._request_count = 0
            
            self.log_info("API plugin cleanup completed")
        
        except Exception as e:
            self.log_error(f"Error during API plugin cleanup: {e}")
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get API plugin information"""
        return {
            "name": self.name,
            "type": "api",
            "version": "1.0.0",
            "description": "External REST API integration plugin",
            "base_url": self.base_url,
            "request_count": self._request_count,
            "rate_limit": self.rate_limit,
            "tools_loaded": len(self.tools),
            "supported_features": [
                "http_methods",
                "json_handling",
                "rate_limiting",
                "error_handling"
            ]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on API plugin"""
        base_health = await super().health_check()
        
        # Add API-specific health information
        api_health = {
            "base_url": self.base_url,
            "request_count": self._request_count,
            "rate_limit": self.rate_limit,
            "client_active": self.client is not None,
            "api_accessible": False
        }
        
        # Test API accessibility
        try:
            await self._test_api_connection()
            api_health["api_accessible"] = True
        except Exception as e:
            api_health["api_error"] = str(e)
        
        base_health.update(api_health)
        return base_health
    
    def validate_config(self) -> bool:
        """Validate API plugin configuration"""
        if not super().validate_config():
            return False
        
        # Check required configuration
        base_url = self.get_config_value("base_url")
        if not base_url or not isinstance(base_url, str):
            self.log_error("API base URL is required and must be a string")
            return False
        
        # Validate URL format
        if not base_url.startswith(("http://", "https://")):
            self.log_error("API base URL must start with http:// or https://")
            return False
        
        # Validate timeout
        timeout = self.get_config_value("timeout", 10)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            self.log_error("API timeout must be a positive number")
            return False
        
        # Validate rate limit
        rate_limit = self.get_config_value("rate_limit", 100)
        if not isinstance(rate_limit, int) or rate_limit <= 0:
            self.log_error("API rate limit must be a positive integer")
            return False
        
        return True
    
    def get_base_url(self) -> str:
        """Get API base URL"""
        return self.base_url
    
    def get_request_count(self) -> int:
        """Get current request count"""
        return self._request_count
    
    def reset_request_count(self) -> None:
        """Reset request count"""
        self._request_count = 0
        self.log_info("Request count reset")
    
    def get_rate_limit(self) -> int:
        """Get rate limit"""
        return self.rate_limit 