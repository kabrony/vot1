"""
MCP Tools Utility Module

This module provides utility functions for interacting with Machine Capability Providers (MCPs),
such as Perplexity AI and Firecrawl.
"""

import logging
import os
import importlib
import inspect
import json
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Exception raised for MCP-related errors."""
    pass

@lru_cache(maxsize=128)
def get_mcp_function(function_name):
    """
    Dynamically import and return an MCP function by name.
    
    Args:
        function_name (str): The fully qualified name of the MCP function.
        
    Returns:
        callable: The imported MCP function.
        
    Raises:
        MCPError: If the function cannot be imported or is not callable.
    """
    try:
        # Parse function name
        if function_name.startswith('mcp_'):
            # Extract module and function name
            parts = function_name.split('_')
            if len(parts) < 3:
                raise MCPError(f"Invalid MCP function name format: {function_name}")
            
            # Assuming format is mcp_PROVIDER_FUNCTION
            provider = parts[1].lower()
            
            # Try to import the module
            module_name = f"mcp_{provider}"
            module = importlib.import_module(module_name)
            
            # Get the function
            func = getattr(module, function_name)
            if not callable(func):
                raise MCPError(f"Imported object {function_name} is not callable")
            
            return func
        else:
            raise MCPError(f"Function name does not start with 'mcp_': {function_name}")
    except ImportError as e:
        logger.error(f"Failed to import MCP function {function_name}: {str(e)}")
        raise MCPError(f"Failed to import MCP function {function_name}: {str(e)}")
    except AttributeError as e:
        logger.error(f"MCP function {function_name} not found: {str(e)}")
        raise MCPError(f"MCP function {function_name} not found: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error importing MCP function {function_name}: {str(e)}")
        raise MCPError(f"Unexpected error importing MCP function {function_name}: {str(e)}")

def call_mcp_function(function_name, args):
    """
    Call an MCP function by name with the provided arguments.
    
    Args:
        function_name (str): The fully qualified name of the MCP function.
        args (dict): The arguments to pass to the function.
        
    Returns:
        dict: The response from the MCP function.
        
    Raises:
        MCPError: If there's an error calling the function.
    """
    try:
        # During development/testing, we can mock API responses
        if os.environ.get("VOT1_MCP_MOCK", "false").lower() == "true":
            return mock_mcp_response(function_name, args)
        
        # In production, get and call the actual function
        func = get_mcp_function(function_name)
        response = func(args)
        
        # Ensure the response is a dict with a standard format
        if not isinstance(response, dict):
            response = {"data": response, "error": None}
        
        return response
    except Exception as e:
        logger.error(f"Error calling MCP function {function_name}: {str(e)}")
        return {"data": None, "error": str(e), "successful": False}

def mock_mcp_response(function_name, args):
    """
    Generate a mock response for MCP function calls during development.
    
    Args:
        function_name (str): The MCP function name.
        args (dict): The arguments passed to the function.
        
    Returns:
        dict: A mock response mimicking the structure of real MCP responses.
    """
    logger.info(f"Generating mock response for MCP function: {function_name}")
    
    # Simple mapping of function names to mock responses
    mock_responses = {
        "mcp_PERPLEXITY_PERPLEXITYAI_CHECK_ACTIVE_CONNECTION": {
            "data": {
                "active_connection": True,
                "connection_details": {
                    "connection_id": "mock-perplexity-connection-id",
                    "tool_name": "perplexityai",
                    "status": "ACTIVE"
                }
            },
            "error": None,
            "successful": True
        },
        "mcp_FIRECRAWL_FIRECRAWL_CHECK_ACTIVE_CONNECTION": {
            "data": {
                "active_connection": False,
                "connection_details": None
            },
            "error": None,
            "successful": True
        },
        "mcp_PERPLEXITY_PERPLEXITYAI_GET_REQUIRED_PARAMETERS": {
            "data": {
                "required_parameters": [],
                "has_default_credentials": True
            },
            "error": None,
            "successful": True
        },
        "mcp_FIRECRAWL_FIRECRAWL_GET_REQUIRED_PARAMETERS": {
            "data": {
                "required_parameters": [
                    {
                        "name": "api_key",
                        "display_name": "API Key",
                        "description": "Your Firecrawl API key",
                        "type": "string",
                        "required": True
                    }
                ],
                "has_default_credentials": False
            },
            "error": None,
            "successful": True
        },
        "mcp_PERPLEXITY_PERPLEXITYAI_INITIATE_CONNECTION": {
            "data": {
                "connection_id": "mock-perplexity-connection-id",
                "status": "ACTIVE"
            },
            "error": None,
            "successful": True
        },
        "mcp_FIRECRAWL_FIRECRAWL_INITIATE_CONNECTION": {
            "data": {
                "connection_id": "mock-firecrawl-connection-id",
                "status": "ACTIVE"
            },
            "error": None,
            "successful": True
        },
        "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "completion": f"Mock research results for query: {args.get('params', {}).get('userContent', 'unknown query')}.\n\nThis is simulated content that would normally come from Perplexity AI.",
                        "citations": [
                            {"title": "Mock Source 1", "url": "https://example.com/source1"},
                            {"title": "Mock Source 2", "url": "https://example.com/source2"}
                        ]
                    })
                }
            ],
            "error": None,
            "successful": True
        },
        "mcp_FIRECRAWL_FIRECRAWL_CRAWL_URLS": {
            "data": {
                "id": "mock-crawl-job-id",
                "status": "processing"
            },
            "error": None,
            "successful": True
        },
        "mcp_FIRECRAWL_FIRECRAWL_CRAWL_JOB_STATUS": {
            "data": {
                "id": "mock-crawl-job-id",
                "status": "completed",
                "url": args.get('params', {}).get('url', 'https://example.com'),
                "pages": [
                    {
                        "url": "https://example.com/page1",
                        "title": "Mock Page 1",
                        "content": "Mock content for page 1"
                    },
                    {
                        "url": "https://example.com/page2",
                        "title": "Mock Page 2",
                        "content": "Mock content for page 2"
                    }
                ]
            },
            "error": None,
            "successful": True
        }
    }
    
    # Return the appropriate mock response, or a default one if not found
    return mock_responses.get(function_name, {
        "data": {"message": f"Mock response for {function_name} (not specifically defined)"},
        "error": None,
        "successful": True
    }) 