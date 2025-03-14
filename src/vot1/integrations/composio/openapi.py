"""
VOT1 OpenAPI Integration via Composio

This module provides specialized OpenAPI integration utilizing Composio's
ability to import and work with any API defined via OpenAPI specs.
It enables dynamic API integration, automated documentation, and testing.

Copyright 2025 Village of Thousands
"""

import os
import yaml
import json
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO

from vot1.integrations.composio import (
    ComposioAuthManager,
    ComposioConnector,
    ComposioToolRegistry,
    ComposioAPIError,
    ComposioRateLimitError
)

# Setup logging
logger = logging.getLogger(__name__)

class OpenAPIComposioIntegration:
    """OpenAPI integration using Composio's API capabilities"""
    
    def __init__(self, auth_manager: ComposioAuthManager = None, api_key: str = None):
        """
        Initialize the OpenAPI integration with Composio
        
        Args:
            auth_manager: An existing ComposioAuthManager instance
            api_key: Composio API key (if auth_manager not provided)
        """
        if not auth_manager and not api_key:
            api_key = os.environ.get("COMPOSIO_API_KEY")
            if not api_key:
                raise ValueError("Either auth_manager or api_key must be provided")
        
        self.auth_manager = auth_manager or ComposioAuthManager(api_key)
        self.connector = ComposioConnector(self.auth_manager)
        self.tool_registry = ComposioToolRegistry(self.auth_manager)
        self._initialized = False
        self.imported_tools = {}
        
    async def initialize(self):
        """Initialize the integration and verify OpenAPI tool availability"""
        if not self.auth_manager.session:
            await self.auth_manager.initialize()
            
        try:
            # Verify connection
            status = await self.connector.get_status()
            if status and status.get("status") == "active":
                self._initialized = True
                logger.info(f"OpenAPI integration initialized. Composio version: {status.get('version')}")
                return status
            else:
                raise RuntimeError(f"Failed to initialize OpenAPI integration: Composio status is {status.get('status')}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAPI integration: {e}")
            raise RuntimeError(f"OpenAPI integration initialization failed: {e}")
    
    async def _ensure_initialized(self):
        """Ensure the integration is initialized before use"""
        if not self._initialized:
            await self.initialize()
    
    async def import_openapi_spec(
        self,
        spec_content: Union[str, dict, BinaryIO],
        auth_config: Optional[Union[str, dict, BinaryIO]] = None,
        tool_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Import an OpenAPI specification into Composio
        
        Args:
            spec_content: OpenAPI spec content (YAML/JSON string, dict, or file-like object)
            auth_config: Authentication configuration (YAML/JSON string, dict, or file-like object)
            tool_name: Custom name for the tool (defaults to the one in the spec)
            description: Custom description (defaults to the one in the spec)
            tags: List of tags to categorize the tool
            
        Returns:
            Details of the imported tool
        """
        await self._ensure_initialized()
        
        # Process spec content
        if hasattr(spec_content, 'read'):
            # It's a file-like object
            spec_data = spec_content.read()
            if isinstance(spec_data, bytes):
                spec_data = spec_data.decode('utf-8')
        elif isinstance(spec_content, dict):
            # It's already a dictionary
            spec_data = json.dumps(spec_content)
        else:
            # Assume it's a string
            spec_data = spec_content
            
        # Check if it's YAML and convert to JSON if needed
        if not spec_data.strip().startswith('{'):
            # Likely YAML, convert to JSON
            try:
                spec_dict = yaml.safe_load(spec_data)
                spec_data = json.dumps(spec_dict)
            except Exception as e:
                logger.error(f"Failed to parse OpenAPI spec: {e}")
                raise ValueError(f"Invalid OpenAPI specification format: {e}")
        
        # Process auth config
        auth_data = None
        if auth_config:
            if hasattr(auth_config, 'read'):
                auth_data = auth_config.read()
                if isinstance(auth_data, bytes):
                    auth_data = auth_data.decode('utf-8')
            elif isinstance(auth_config, dict):
                auth_data = json.dumps(auth_config)
            else:
                auth_data = auth_config
                
            # Check if it's YAML and convert to JSON if needed
            if auth_data and not auth_data.strip().startswith('{'):
                try:
                    auth_dict = yaml.safe_load(auth_data)
                    auth_data = json.dumps(auth_dict)
                except Exception as e:
                    logger.error(f"Failed to parse auth config: {e}")
                    raise ValueError(f"Invalid auth configuration format: {e}")
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as spec_file:
            spec_path = spec_file.name
            spec_file.write(spec_data.encode('utf-8'))
            
        auth_path = None
        if auth_data:
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as auth_file:
                auth_path = auth_file.name
                auth_file.write(auth_data.encode('utf-8'))
        
        try:
            # Prepare import parameters
            import_params = {
                "spec_file": spec_path,
                "version": "2025.5"  # Latest Composio version as of 2025
            }
            
            if auth_path:
                import_params["auth_file"] = auth_path
            if tool_name:
                import_params["name"] = tool_name
            if description:
                import_params["description"] = description
            if tags:
                import_params["tags"] = tags
                
            # Import the OpenAPI spec
            result = await self.connector.import_openapi(**import_params)
            
            # Store the imported tool information
            if result and "tool_id" in result:
                tool_id = result["tool_id"]
                tool_name = result.get("name", tool_id)
                self.imported_tools[tool_name] = result
                logger.info(f"Successfully imported OpenAPI spec as tool: {tool_name}")
                
            return result
        
        except ComposioAPIError as e:
            logger.error(f"Error importing OpenAPI spec: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error importing OpenAPI spec: {e}")
            raise RuntimeError(f"OpenAPI spec import failed: {e}")
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(spec_path):
                    os.unlink(spec_path)
                if auth_path and os.path.exists(auth_path):
                    os.unlink(auth_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary files: {e}")
    
    async def import_openapi_spec_from_file(
        self,
        spec_file_path: str,
        auth_file_path: Optional[str] = None,
        tool_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Import an OpenAPI specification from files
        
        Args:
            spec_file_path: Path to the OpenAPI spec file (YAML or JSON)
            auth_file_path: Path to the auth config file (YAML or JSON)
            tool_name: Custom name for the tool (defaults to the one in the spec)
            description: Custom description (defaults to the one in the spec)
            tags: List of tags to categorize the tool
            
        Returns:
            Details of the imported tool
        """
        spec_path = Path(spec_file_path)
        if not spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {spec_file_path}")
        
        with open(spec_path, 'r', encoding='utf-8') as spec_file:
            spec_content = spec_file
            
            auth_content = None
            if auth_file_path:
                auth_path = Path(auth_file_path)
                if not auth_path.exists():
                    raise FileNotFoundError(f"Auth config file not found: {auth_file_path}")
                
                with open(auth_path, 'r', encoding='utf-8') as auth_file:
                    auth_content = auth_file
                    
                    return await self.import_openapi_spec(
                        spec_content=spec_file,
                        auth_config=auth_file,
                        tool_name=tool_name,
                        description=description,
                        tags=tags
                    )
            
            return await self.import_openapi_spec(
                spec_content=spec_file,
                auth_config=None,
                tool_name=tool_name,
                description=description,
                tags=tags
            )
    
    async def list_imported_tools(self) -> List[Dict[str, Any]]:
        """
        List all imported OpenAPI tools
        
        Returns:
            List of imported tools with their details
        """
        await self._ensure_initialized()
        
        try:
            tools = await self.tool_registry.list_tools(tags=["openapi"])
            return tools
        except Exception as e:
            logger.error(f"Error listing imported tools: {e}")
            raise
    
    async def get_tool_details(self, tool_name_or_id: str) -> Dict[str, Any]:
        """
        Get details of a specific imported tool
        
        Args:
            tool_name_or_id: Name or ID of the tool
            
        Returns:
            Tool details
        """
        await self._ensure_initialized()
        
        try:
            tool_details = await self.tool_registry.get_tool_details(tool_name_or_id)
            return tool_details
        except Exception as e:
            logger.error(f"Error getting tool details: {e}")
            raise
    
    async def execute_tool_action(
        self,
        tool_name_or_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an action on an imported OpenAPI tool
        
        Args:
            tool_name_or_id: Name or ID of the tool
            action: Name of the action to execute
            parameters: Parameters for the action
            
        Returns:
            Result of the action
        """
        await self._ensure_initialized()
        
        try:
            result = await self.connector.execute_tool(
                tool_name=tool_name_or_id,
                action=action,
                parameters=parameters
            )
            
            logger.info(f"Executed {action} on {tool_name_or_id}")
            return result
        except ComposioRateLimitError as e:
            logger.warning(f"Rate limited: {e}. Retry after {e.retry_after} seconds.")
            raise
        except ComposioAPIError as e:
            logger.error(f"Error executing tool action: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing tool action: {e}")
            raise RuntimeError(f"Tool action execution failed: {e}")
    
    async def delete_imported_tool(self, tool_name_or_id: str) -> bool:
        """
        Delete an imported OpenAPI tool
        
        Args:
            tool_name_or_id: Name or ID of the tool
            
        Returns:
            True if deleted successfully
        """
        await self._ensure_initialized()
        
        try:
            result = await self.connector.delete_tool(tool_name_or_id)
            
            # Remove from local cache if present
            if tool_name_or_id in self.imported_tools:
                del self.imported_tools[tool_name_or_id]
                
            logger.info(f"Deleted tool: {tool_name_or_id}")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Error deleting tool: {e}")
            raise
    
    async def check_daily_repository_usage(self, repository: str) -> Dict[str, Any]:
        """
        Check daily usage statistics for a repository
        
        Args:
            repository: Repository name or ID
            
        Returns:
            Usage statistics
        """
        await self._ensure_initialized()
        
        try:
            result = await self.connector.get_repository_usage(repository, timeframe="daily")
            
            logger.info(f"Retrieved daily usage stats for repository: {repository}")
            return result
        except Exception as e:
            logger.error(f"Error checking repository usage: {e}")
            raise
    
    async def close(self):
        """Close connections and clean up resources"""
        if self.auth_manager and self.auth_manager.session:
            await self.auth_manager.close()
            logger.info("OpenAPI Composio integration closed")
            self._initialized = False


# Convenience function to create an OpenAPI integration instance
async def create_openapi_integration(api_key: Optional[str] = None) -> OpenAPIComposioIntegration:
    """
    Create and initialize an OpenAPI integration instance
    
    Args:
        api_key: Composio API key (optional, can use environment variable)
        
    Returns:
        Initialized OpenAPIComposioIntegration instance
    """
    integration = OpenAPIComposioIntegration(api_key=api_key)
    await integration.initialize()
    return integration


# Examples of using the integration
async def example_usage():
    """Example of using the OpenAPI Composio integration"""
    # Create and initialize the integration
    openapi = await create_openapi_integration()
    
    try:
        # Example: Import an OpenAPI spec from a file
        imported_tool = await openapi.import_openapi_spec_from_file(
            spec_file_path="/path/to/openapi_spec.yaml",
            auth_file_path="/path/to/auth_config.yaml",
            tool_name="weather-api",
            description="Weather forecast API integration",
            tags=["weather", "forecast"]
        )
        
        print(f"Imported tool: {imported_tool.get('name')}")
        
        # List all imported tools
        tools = await openapi.list_imported_tools()
        print(f"Total imported tools: {len(tools)}")
        
        # Execute an action
        result = await openapi.execute_tool_action(
            tool_name_or_id="weather-api",
            action="get_forecast",
            parameters={
                "location": "New York",
                "days": 7
            }
        )
        
        print(f"Forecast result: {result}")
        
        # Check repository usage
        usage = await openapi.check_daily_repository_usage("vot1")
        print(f"API calls today: {usage.get('api_calls', 0)}")
        
    finally:
        # Close the integration
        await openapi.close()


if __name__ == "__main__":
    # Run the example if script is executed directly
    asyncio.run(example_usage()) 