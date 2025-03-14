#!/usr/bin/env python3
"""
VOTai Local MCP Bridge

This module provides a bridge between local applications and MCP services,
enabling seamless integration with services like GitHub, Perplexity, Firecrawl,
Figma, and Composio.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import json
import logging
import uuid
import time
import requests
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from .ascii_art import get_votai_ascii

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'local_mcp_bridge.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class LocalMCPBridge:
    """
    Bridge between local applications and MCP services.
    
    The VOTai LocalMCPBridge provides a unified interface for interacting with
    various MCP services, handling authentication, request formatting, and response
    processing.
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    # Service constants
    SERVICE_GITHUB = "GITHUB"
    SERVICE_PERPLEXITY = "PERPLEXITY"
    SERVICE_FIRECRAWL = "FIRECRAWL"
    SERVICE_FIGMA = "FIGMA"
    SERVICE_COMPOSIO = "COMPOSIO"
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        api_keys: Optional[Dict[str, str]] = None,
        cache_enabled: bool = True,
        timeout: int = 30
    ):
        """
        Initialize the VOTai Local MCP Bridge.
        
        Args:
            config_path: Path to the MCP configuration file
            api_keys: Dictionary of API keys for MCP services
            cache_enabled: Whether to enable caching
            timeout: Timeout for API requests in seconds
        """
        # Display VOTai signature
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai Local MCP Bridge initializing...")
        
        # Initialize instance variables
        self.config = self._load_config(config_path)
        self.api_keys = api_keys or {}
        self.cache_enabled = cache_enabled
        self.timeout = timeout
        self.connections = {}
        self.cache = {}
        self.tool_handlers = {}
        
        # Initialize performance metrics
        self.start_time = time.time()
        self.requests_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_request_time = 0
        
        logger.info("Local MCP Bridge initialized")
        logger.info(f"Available MCP services: {', '.join(self.config.get('mcpServers', {}).keys())}")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load the MCP configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing the MCP configuration
        """
        # Default configuration
        config = {
            "mcp_url": "https://mcp.cursor.sh",
            "services": {}
        }
        
        # Try to load from config_path if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    config.update(loaded_config)
                logger.info(f"Loaded MCP configuration from {config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading MCP configuration from {config_path}: {e}")
        
        # Check for config in standard locations
        config_paths = [
            Path("src/vot1/config/mcp.json"),
            Path("src/vot1/local_mcp/config/mcp.json"),
            Path.home() / ".cursor" / "mcp.json",
            Path.home() / ".vot1" / "config" / "mcp.json",
            Path(os.getcwd()) / "mcp.json"
        ]
        
        config_file = None
        for path in config_paths:
            if path.exists():
                config_file = path
                break
        
        if not config_file or not config_file.exists():
            logger.warning("MCP configuration file not found")
            return {}
        
        logger.info(f"Loading MCP configuration from {config_file}")
        with open(config_file, "r") as f:
            config = json.load(f)
        
        return config
    
    def get_service_url(self, service: str) -> Optional[str]:
        """
        Get the URL for a specific MCP service.
        
        Args:
            service: Service identifier (e.g., "GITHUB", "PERPLEXITY")
            
        Returns:
            URL for the service or None if not found
        """
        service = service.upper()
        return self.config.get("mcpServers", {}).get(service, {}).get("url")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get the API key for a specific service.
        
        Args:
            service: Service identifier
            
        Returns:
            API key for the service or None if not found
        """
        service = service.upper()
        # Check instance-provided keys first
        if service in self.api_keys:
            return self.api_keys[service]
            
        # Then check environment variables
        env_var = f"{service}_API_KEY"
        return os.environ.get(env_var)
    
    def check_connection(self, service: str, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a connection to a service is active.
        
        Args:
            service: Service identifier
            connection_id: Optional specific connection ID to check
            
        Returns:
            Dictionary with connection status
        """
        service = service.upper()
        
        try:
            # Check if we have a connection for this service
            if service in self.connections:
                connection = self.connections[service]
                return {
                    "successful": True,
                    "active_connection": True,
                    "connection_id": connection.get("id"),
                    "connected_at": connection.get("connected_at")
                }
            
            # Check if the service is configured
            service_url = self.get_service_url(service)
            if not service_url:
                return {
                    "successful": False,
                    "active_connection": False,
                    "error": f"Service '{service}' not configured"
                }
            
            # If a specific connection ID is provided, check that
            if connection_id:
                # This would actually call the service's check_connection endpoint
                # For now, we'll simulate the check
                is_valid = connection_id.startswith(service.lower())
                return {
                    "successful": True,
                    "active_connection": is_valid,
                    "connection_id": connection_id if is_valid else None
                }
            
            # Default to not connected
            return {
                "successful": True,
                "active_connection": False
            }
            
        except Exception as e:
            logger.error(f"Error checking connection for {service}: {e}")
            return {
                "successful": False,
                "error": str(e)
            }
    
    def get_required_parameters(self, service: str) -> Dict[str, Any]:
        """
        Get the parameters required to connect to a service.
        
        Args:
            service: Service identifier
            
        Returns:
            Dictionary with required parameters
        """
        service = service.upper()
        
        # Define required parameters for each service
        service_params = {
            self.SERVICE_GITHUB: [],  # GitHub uses OAuth, no parameters needed
            self.SERVICE_PERPLEXITY: ["api_key"],
            self.SERVICE_FIRECRAWL: ["api_key"],
            self.SERVICE_FIGMA: ["access_token"],
            self.SERVICE_COMPOSIO: ["api_key"]
        }
        
        if service not in service_params:
            return {
                "successful": False,
                "error": f"Unknown service: {service}"
            }
        
        return {
            "successful": True,
            "parameters": service_params[service]
        }
    
    def initiate_connection(self, service: str, parameters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Initiate a connection to a service.
        
        Args:
            service: Service identifier
            parameters: Optional parameters for the connection
            
        Returns:
            Dictionary with connection result
        """
        service = service.upper()
        parameters = parameters or {}
        
        try:
            # Check if the service is configured
            service_url = self.get_service_url(service)
            if not service_url:
                return {
                    "successful": False,
                    "error": f"Service '{service}' not configured"
                }
            
            # Validate parameters
            required_params = self.get_required_parameters(service)
            if not required_params.get("successful", False):
                return required_params
            
            required_param_list = required_params.get("parameters", [])
            missing_params = [param for param in required_param_list if param not in parameters]
            
            # If parameters are required but not provided, check if we have API keys
            if missing_params and service in [self.SERVICE_PERPLEXITY, self.SERVICE_FIRECRAWL, self.SERVICE_COMPOSIO]:
                api_key = self.get_api_key(service)
                if api_key:
                    parameters["api_key"] = api_key
                    missing_params = [param for param in missing_params if param != "api_key"]
            
            if missing_params:
                return {
                    "successful": False,
                    "error": f"Missing required parameters: {', '.join(missing_params)}"
                }
            
            # In a real implementation, this would call the service's connection endpoint
            # For now, we'll simulate the connection
            connection_id = f"{service.lower()}-{str(uuid.uuid4())[:8]}"
            
            # Store connection information
            self.connections[service] = {
                "id": connection_id,
                "connected_at": time.time(),
                "parameters": parameters
            }
            
            logger.info(f"Connected to {service} with connection ID {connection_id}")
            
            return {
                "successful": True,
                "connection_id": connection_id,
                "message": f"Successfully connected to {service}"
            }
            
        except Exception as e:
            logger.error(f"Error initiating connection to {service}: {e}")
            return {
                "successful": False,
                "error": str(e)
            }
    
    def call_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP function.
        
        Args:
            function_name: Name of the function to call
            params: Parameters to pass to the function
            
        Returns:
            Result of the function call
        """
        # Check if this is an internal function call
        if "_" in function_name:
            parts = function_name.split("_", 1)
            if len(parts) == 2:
                tool_name, internal_function_name = parts
                if tool_name in self.tool_handlers and internal_function_name in self.tool_handlers[tool_name]:
                    logger.debug(f"Calling internal function {tool_name}.{internal_function_name}")
                    return self.call_internal_function(tool_name, internal_function_name, params)
        
        # Check cache if enabled
        if self.cache_enabled:
            cache_key = self._get_cache_key(function_name, params)
            if cache_key in self.cache:
                logger.debug(f"Cache hit for {function_name}")
                self.cache_hits += 1
                return self.cache[cache_key]
            else:
                self.cache_misses += 1
        
        try:
            # Parse function name to determine service and endpoint
            service, endpoint = self._parse_function_name(function_name)
            
            # Get service URL
            service_url = self.get_service_url(service)
            if not service_url:
                return {
                    "successful": False,
                    "error": f"Service '{service}' not configured"
                }
            
            # Prepare request
            url = f"{service_url}/{endpoint}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add API key if available
            api_key = self.get_api_key(service)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Track performance metrics
            start_time = time.time()
            self.requests_processed += 1
            
            # Simulate network call
            # In a real implementation, this would be an actual HTTP request
            # For now, we'll just return a mock response
            logger.info(f"Calling {function_name} with params: {params}")
            
            # Make the actual request
            response = requests.post(
                url,
                json={"params": params},
                headers=headers,
                timeout=self.timeout
            )
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                
                # Cache result if enabled
                if self.cache_enabled:
                    self.cache[cache_key] = result
                
                self.cache_hits += 1
            else:
                result = {
                    "successful": False,
                    "error": f"API call failed with status code {response.status_code}",
                    "status_code": response.status_code
                }
                self.cache_misses += 1
            
            # Track response time
            response_time = time.time() - start_time
            self.total_request_time += response_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling function {function_name}: {e}")
            self.cache_misses += 1
            return {
                "successful": False,
                "error": str(e)
            }
    
    async def call_function_async(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP function asynchronously.
        
        Args:
            function_name: Full function name
            params: Function parameters
            
        Returns:
            Function result
        """
        # This is just a wrapper around the synchronous method for now
        # In a real implementation, this would use aiohttp or similar
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.call_function, function_name, params)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the bridge."""
        end_time = time.time()
        uptime = end_time - self.start_time
        
        metrics = {
            "uptime": self._format_duration(uptime),
            "uptime_seconds": round(uptime, 2),
            "requests_processed": self.requests_processed,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_ratio": round(self.cache_hits / max(1, self.cache_hits + self.cache_misses), 2),
            "average_request_time": round(self.total_request_time / max(1, self.requests_processed), 2),
            "services": {
                service: {"url": self.get_service_url(service), "active": self.check_connection(service).get("active_connection", False)}
                for service in [self.SERVICE_GITHUB, self.SERVICE_PERPLEXITY, self.SERVICE_FIRECRAWL, self.SERVICE_FIGMA, self.SERVICE_COMPOSIO]
            },
            "cache_size": len(self.cache),
            "timestamp": time.time()
        }
        
        return {
            "successful": True,
            "metrics": metrics
        }
    
    def get_github_status(self) -> Dict[str, Any]:
        """
        Get detailed status information for the GitHub service.
        
        Returns:
            A dictionary with GitHub service status information
        """
        votai_ascii = get_votai_ascii("small")
        logging.info(f"\n{votai_ascii}\nGetting VOTai GitHub service status")
        
        # Check if GitHub service is configured
        github_url = self.get_service_url(self.SERVICE_GITHUB)
        if not github_url:
            return {
                "successful": False,
                "error": "GitHub service not configured",
                "status": {
                    "configured": False
                }
            }
        
        # Check connection to GitHub
        connection_result = self.check_connection(self.SERVICE_GITHUB)
        active_connection = connection_result.get("active_connection", False)
        
        # Build status object
        status = {
            "configured": True,
            "url": github_url,
            "connection_active": active_connection,
            "timestamp": time.time()
        }
        
        if active_connection:
            # Try a simple API call to verify functionality
            try:
                test_result = self.call_function("mcp_MCP_GITHUB_GITHUB_API_ROOT", {
                    "params": {}
                })
                
                status["api_available"] = test_result.get("successful", False)
                
                if not status["api_available"]:
                    status["error"] = test_result.get("error", "Unknown error")
            except Exception as e:
                status["api_available"] = False
                status["error"] = str(e)
        
        return {
            "successful": active_connection,
            "status": status
        }
    
    def clear_caches(self) -> Dict[str, Any]:
        """
        Clear the cache.
        
        Returns:
            Statistics about the cleared cache
        """
        # Get stats before clearing
        stats = {
            "entries_before": len(self.cache),
            "hits": self.cache_hits,
            "misses": self.cache_misses
        }
        
        # Clear cache
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        return {
            "successful": True,
            "message": "Cache cleared successfully",
            "stats": stats,
            "entries_after": len(self.cache)
        }
    
    def register_tool_handler(self, tool_name: str, function_name: str, handler: callable) -> None:
        """
        Register a handler function for a specific tool and function.
        
        Args:
            tool_name: Name of the tool (e.g., "memory", "agent")
            function_name: Name of the function within the tool
            handler: Handler function to call when this tool function is invoked
        """
        if tool_name not in self.tool_handlers:
            self.tool_handlers[tool_name] = {}
            
        self.tool_handlers[tool_name][function_name] = handler
        logger.debug(f"Registered handler for {tool_name}.{function_name}")
    
    def call_internal_function(self, tool_name: str, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an internal function registered with register_tool_handler.
        
        Args:
            tool_name: Name of the tool
            function_name: Name of the function
            params: Parameters to pass to the function
            
        Returns:
            Result of the function call
        """
        if tool_name not in self.tool_handlers or function_name not in self.tool_handlers[tool_name]:
            return {
                "successful": False,
                "error": f"No handler registered for {tool_name}.{function_name}"
            }
            
        try:
            handler = self.tool_handlers[tool_name][function_name]
            result = handler(params)
            
            # If the result is not a dict, wrap it
            if not isinstance(result, dict):
                result = {
                    "successful": True,
                    "result": result
                }
            elif "successful" not in result:
                result["successful"] = True
                
            return result
        except Exception as e:
            logger.error(f"Error calling internal function {tool_name}.{function_name}: {e}")
            return {
                "successful": False,
                "error": str(e)
            }
    
    def _parse_function_name(self, function_name: str) -> Tuple[str, str]:
        """
        Parse a function name into service and endpoint.
        
        Args:
            function_name: Function name (e.g., mcp_GITHUB_CREATE_AN_ISSUE)
            
        Returns:
            Tuple of (service, endpoint)
            
        Raises:
            ValueError: If the function name is invalid
        """
        parts = function_name.split('_')
        if len(parts) < 3 or parts[0] != "mcp":
            raise ValueError(f"Invalid function name format: {function_name}")
            
        service = parts[1].upper()
        endpoint = '_'.join(parts[2:]).lower()
        
        return service, endpoint
    
    def _get_cache_key(self, function_name: str, params: Dict[str, Any]) -> str:
        """
        Generate a cache key for a function call.
        
        Args:
            function_name: Function name
            params: Function parameters
            
        Returns:
            Cache key string
        """
        # Sort the params to ensure consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{function_name}:{sorted_params}"
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format a duration in a human-readable format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds" 