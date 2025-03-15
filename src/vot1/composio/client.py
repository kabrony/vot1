"""
VOTai Composio Client

This module provides integration with the Composio tool ecosystem,
enabling VOTai to discover, manage, and execute external tools.
"""

import os
import json
import time
import asyncio
import logging
import httpx
from typing import Dict, List, Any, Optional, Union, Tuple

try:
    # Absolute imports (for installed package)
    from vot1.utils.branding import format_status
    from vot1.utils.logging import get_logger
except ImportError:
    # Relative imports (for development)
    from src.vot1.utils.branding import format_status
    from src.vot1.utils.logging import get_logger

logger = get_logger(__name__)

class ComposioClient:
    """
    Client for interacting with the Composio API to discover and execute tools.
    
    This client provides:
    - Tool discovery and management
    - Tool execution with parameter validation
    - Tool monitoring and statistics
    - Integration with VOTai memory system
    """
    
    # API endpoints
    BASE_URL = "https://api.composio.dev/v1"
    TOOLS_PATH = "/tools"
    EXECUTE_PATH = "/execute"
    INTEGRATIONS_PATH = "/integrations"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        integration_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        max_concurrent_executions: int = 5,
        cache_ttl: int = 300,
        memory_bridge: Optional[Any] = None
    ):
        """
        Initialize the Composio client.
        
        Args:
            api_key: Composio API key (defaults to COMPOSIO_API_KEY env var)
            integration_id: Integration ID (defaults to COMPOSIO_INTEGRATION_ID env var)
            endpoint: Custom API endpoint (defaults to BASE_URL)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            max_concurrent_executions: Maximum concurrent tool executions
            cache_ttl: Time-to-live for tool cache in seconds
            memory_bridge: Memory bridge instance for tool execution records
        """
        self.api_key = api_key or os.environ.get("COMPOSIO_API_KEY")
        self.integration_id = integration_id or os.environ.get("COMPOSIO_INTEGRATION_ID")
        self.endpoint = endpoint or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_concurrent_executions = max_concurrent_executions
        self.cache_ttl = cache_ttl
        self.memory_bridge = memory_bridge
        
        # Tool cache
        self._tool_cache = {}
        self._tool_cache_timestamp = 0
        
        # Semaphore for concurrent executions
        self._execution_semaphore = asyncio.Semaphore(max_concurrent_executions)
        
        # Statistics
        self.stats = {
            "tool_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "cached_tool_lookups": 0,
            "api_requests": 0,
            "start_time": time.time()
        }
        
        # Validate configuration
        if not self.api_key:
            logger.warning(format_status("warning", "No Composio API key provided, some features will be limited"))
        
        if not self.integration_id:
            logger.warning(format_status("warning", "No Composio integration ID provided, some features will be limited"))
        
        logger.info(format_status("info", "Composio client initialized"))
    
    async def list_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of available tools from Composio.
        
        Args:
            force_refresh: Whether to bypass the cache and fetch fresh data
            
        Returns:
            List of available tools
        """
        # Check if we can use cached tools
        current_time = time.time()
        if (
            not force_refresh and 
            self._tool_cache and 
            (current_time - self._tool_cache_timestamp) < self.cache_ttl
        ):
            self.stats["cached_tool_lookups"] += 1
            return list(self._tool_cache.values())
        
        # Need to fetch tools
        if not self.api_key:
            return []
        
        self.stats["api_requests"] += 1
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.endpoint}{self.TOOLS_PATH}"
        if self.integration_id:
            url += f"?integration_id={self.integration_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                tools = response.json()
                
                # Update cache
                self._tool_cache = {tool["id"]: tool for tool in tools}
                self._tool_cache_timestamp = current_time
                
                logger.info(format_status("success", f"Retrieved {len(tools)} tools from Composio"))
                
                return tools
                
        except Exception as e:
            logger.error(f"Error retrieving tools from Composio: {str(e)}")
            return []
    
    async def get_tool(self, tool_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific tool.
        
        Args:
            tool_id: The ID of the tool to retrieve
            force_refresh: Whether to bypass the cache and fetch fresh data
            
        Returns:
            Tool details or None if not found
        """
        # Check cache first
        if not force_refresh and tool_id in self._tool_cache:
            return self._tool_cache[tool_id]
        
        # Fetch individual tool
        if not self.api_key:
            return None
        
        self.stats["api_requests"] += 1
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.endpoint}{self.TOOLS_PATH}/{tool_id}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                tool = response.json()
                
                # Update cache
                self._tool_cache[tool_id] = tool
                
                return tool
                
        except Exception as e:
            logger.error(f"Error retrieving tool {tool_id} from Composio: {str(e)}")
            return None
    
    async def get_tool_definition(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tool definition in Claude-compatible format.
        
        Args:
            tool_id: The ID of the tool
            
        Returns:
            Tool definition for Claude or None if tool not found
        """
        tool = await self.get_tool(tool_id)
        if not tool:
            return None
        
        # Create Claude-compatible tool definition
        params = {}
        required = []
        
        for param in tool.get("parameters", []):
            param_id = param.get("id", "")
            param_info = {
                "type": self._map_param_type(param.get("type", "string")),
                "description": param.get("description", "")
            }
            
            # Add enum values for select type
            if param.get("type") == "select" and "options" in param:
                param_info["enum"] = [opt.get("value") for opt in param["options"]]
            
            # Add required parameters
            if param.get("required", False):
                required.append(param_id)
            
            params[param_id] = param_info
        
        # Define Claude-compatible tool
        tool_def = {
            "name": tool.get("id", "unknown-tool"),
            "description": tool.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": params,
                "required": required
            }
        }
        
        return tool_def
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        timeout: Optional[int] = None,
        store_in_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a Composio tool with the given parameters.
        
        Args:
            tool_id: The ID of the tool to execute
            parameters: The parameters for the tool
            timeout: Custom timeout for this execution
            store_in_memory: Whether to store execution in memory
            
        Returns:
            Tool execution result
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "No API key provided"
            }
        
        self.stats["tool_executions"] += 1
        execution_start = time.time()
        
        # Get tool definition for validation
        tool = await self.get_tool(tool_id)
        if not tool:
            self.stats["failed_executions"] += 1
            return {
                "success": False,
                "error": f"Tool '{tool_id}' not found"
            }
        
        # Validate parameters
        validation_result = self._validate_parameters(tool, parameters)
        if not validation_result["valid"]:
            self.stats["failed_executions"] += 1
            return {
                "success": False,
                "error": f"Parameter validation failed: {validation_result['error']}"
            }
        
        # Prepare request
        self.stats["api_requests"] += 1
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "tool_id": tool_id,
            "parameters": parameters
        }
        
        if self.integration_id:
            payload["integration_id"] = self.integration_id
        
        url = f"{self.endpoint}{self.EXECUTE_PATH}"
        execution_timeout = timeout or self.timeout
        
        try:
            # Limit concurrent executions
            async with self._execution_semaphore:
                async with httpx.AsyncClient(timeout=execution_timeout) as client:
                    # Execute with retry logic
                    for attempt in range(self.max_retries):
                        try:
                            response = await client.post(url, json=payload, headers=headers)
                            response.raise_for_status()
                            
                            result_data = response.json()
                            
                            # Process successful result
                            execution_time = time.time() - execution_start
                            
                            result = {
                                "success": True,
                                "data": result_data.get("result"),
                                "tool_id": tool_id,
                                "execution_time": execution_time,
                                "timestamp": time.time()
                            }
                            
                            self.stats["successful_executions"] += 1
                            
                            # Store in memory if requested
                            if store_in_memory and self.memory_bridge:
                                await self._store_execution_in_memory(tool_id, parameters, result)
                            
                            logger.info(format_status("success", f"Tool '{tool_id}' executed successfully in {execution_time:.2f}s"))
                            
                            return result
                            
                        except httpx.HTTPError as e:
                            # Handle rate limiting or temporary errors
                            if e.response and e.response.status_code in (429, 500, 503, 504):
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                    continue
                            
                            # Re-raise for other errors or after max retries
                            raise
                    
                    # Should never reach here due to exception, but just in case
                    raise Exception("Maximum retries exceeded")
                    
        except Exception as e:
            self.stats["failed_executions"] += 1
            
            error_result = {
                "success": False,
                "error": str(e),
                "tool_id": tool_id,
                "execution_time": time.time() - execution_start,
                "timestamp": time.time()
            }
            
            logger.error(f"Error executing tool '{tool_id}': {str(e)}")
            
            # Store error in memory
            if store_in_memory and self.memory_bridge:
                await self._store_execution_error(tool_id, parameters, error_result)
            
            return error_result
    
    async def search_tools(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tools based on a query.
        
        Args:
            query: Search query for tools
            limit: Maximum number of results
            
        Returns:
            List of matching tools
        """
        # First, ensure we have tools loaded
        tools = await self.list_tools()
        if not tools:
            return []
        
        # Simple search implementation
        matches = []
        query = query.lower()
        
        for tool in tools:
            score = 0
            
            # Match name (higher weight)
            if query in tool.get("name", "").lower():
                score += 3
            
            # Match description
            if query in tool.get("description", "").lower():
                score += 2
            
            # Match category
            if query in tool.get("category", "").lower():
                score += 1
            
            # Match tags
            for tag in tool.get("tags", []):
                if query in tag.lower():
                    score += 1
            
            if score > 0:
                matches.append((score, tool))
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x[0], reverse=True)
        return [match[1] for match in matches[:limit]]
    
    async def _store_execution_in_memory(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Store tool execution in memory bridge"""
        if not self.memory_bridge:
            return
        
        try:
            # Create tool execution memory
            execution_data = {
                "tool_id": tool_id,
                "parameters": parameters,
                "result": result.get("data"),
                "success": True,
                "execution_time": result.get("execution_time", 0),
                "timestamp": result.get("timestamp", time.time())
            }
            
            # Store in memory
            await self.memory_bridge.store_memory(
                content=json.dumps(execution_data),
                memory_type="tool_execution",
                metadata={
                    "tool_id": tool_id,
                    "success": True,
                    "execution_time": result.get("execution_time", 0)
                }
            )
        except Exception as e:
            logger.error(f"Error storing tool execution in memory: {str(e)}")
    
    async def _store_execution_error(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        error_result: Dict[str, Any]
    ) -> None:
        """Store tool execution error in memory bridge"""
        if not self.memory_bridge:
            return
        
        try:
            # Create tool execution error memory
            execution_data = {
                "tool_id": tool_id,
                "parameters": parameters,
                "error": error_result.get("error", "Unknown error"),
                "success": False,
                "execution_time": error_result.get("execution_time", 0),
                "timestamp": error_result.get("timestamp", time.time())
            }
            
            # Store in memory
            await self.memory_bridge.store_memory(
                content=json.dumps(execution_data),
                memory_type="tool_execution_error",
                metadata={
                    "tool_id": tool_id,
                    "success": False,
                    "error": error_result.get("error", "Unknown error")
                }
            )
        except Exception as e:
            logger.error(f"Error storing tool execution error in memory: {str(e)}")
    
    def _validate_parameters(self, tool: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against tool definition.
        
        Args:
            tool: Tool definition
            parameters: Parameters to validate
            
        Returns:
            Validation result with valid status and error message
        """
        tool_parameters = tool.get("parameters", [])
        
        # Check required parameters
        for param in tool_parameters:
            param_id = param.get("id", "")
            if param.get("required", False) and param_id not in parameters:
                return {
                    "valid": False,
                    "error": f"Missing required parameter: {param_id}"
                }
        
        # Validate parameter types
        for param_id, param_value in parameters.items():
            # Find parameter definition
            param_def = next((p for p in tool_parameters if p.get("id") == param_id), None)
            if not param_def:
                continue  # Skip validation for unknown parameters
            
            param_type = param_def.get("type", "string")
            
            # Validate by type
            if param_type == "number" and not isinstance(param_value, (int, float)):
                return {
                    "valid": False,
                    "error": f"Parameter '{param_id}' must be a number"
                }
            elif param_type == "boolean" and not isinstance(param_value, bool):
                return {
                    "valid": False,
                    "error": f"Parameter '{param_id}' must be a boolean"
                }
            elif param_type == "select":
                options = [opt.get("value") for opt in param_def.get("options", [])]
                if param_value not in options:
                    return {
                        "valid": False,
                        "error": f"Parameter '{param_id}' must be one of: {', '.join(options)}"
                    }
        
        return {
            "valid": True
        }
    
    def _map_param_type(self, composio_type: str) -> str:
        """Map Composio parameter type to JSON Schema type"""
        type_mapping = {
            "string": "string",
            "textarea": "string",
            "number": "number",
            "boolean": "boolean",
            "select": "string"
        }
        
        return type_mapping.get(composio_type, "string")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        current_time = time.time()
        uptime = current_time - self.stats["start_time"]
        
        return {
            **self.stats,
            "uptime": uptime,
            "executions_per_minute": (self.stats["tool_executions"] / (uptime / 60)) if uptime > 0 else 0,
            "success_rate": (self.stats["successful_executions"] / self.stats["tool_executions"]) if self.stats["tool_executions"] > 0 else 0,
            "cache_size": len(self._tool_cache),
            "cache_age": current_time - self._tool_cache_timestamp
        } 