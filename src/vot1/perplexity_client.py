#!/usr/bin/env python3
"""
Perplexity API Client for VOT1

This module provides a client for the Perplexity API, enabling the VOT1 system
to leverage web search and online information for enhanced reasoning.
"""

import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PerplexityClient:
    """
    Client for the Perplexity API to enable web search capabilities in VOT1.
    This is a simplified implementation for testing purposes.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "pplx-70b-online"):
        """
        Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)
            model: Perplexity model to use
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.model = model
        
        if not self.api_key:
            logger.warning("No Perplexity API key provided. Web search will be simulated.")
        
        logger.info(f"Initialized PerplexityClient with model: {model}")
    
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search using Perplexity.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        logger.info(f"Performing web search: {query}")
        
        # In a real implementation, this would make an API call to Perplexity
        # For testing, we return mock results
        return {
            "query": query,
            "results": [
                {
                    "title": "THREE.js Documentation",
                    "url": "https://threejs.org/docs/",
                    "snippet": "THREE.js is a cross-browser JavaScript library and application programming interface used to create and display animated 3D computer graphics in a web browser using WebGL."
                },
                {
                    "title": "Creating Advanced Particle Systems in THREE.js",
                    "url": "https://example.com/threejs-particles",
                    "snippet": "Learn how to create advanced particle systems in THREE.js with optimized performance and stunning visual effects."
                },
                {
                    "title": "Cyberpunk Aesthetics in Web Visualization",
                    "url": "https://example.com/cyberpunk-web",
                    "snippet": "Explore techniques for creating cyberpunk-themed visualizations with neon colors, glow effects, and futuristic interfaces."
                }
            ],
            "search_time": 0.5,
            "model": self.model
        }
    
    async def query(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a query to Perplexity.
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            
        Returns:
            Response data
        """
        logger.info(f"Querying Perplexity: {prompt[:50]}...")
        
        # In a real implementation, this would make an API call to Perplexity
        # For testing, we return mock results
        return {
            "id": "mock-response-id",
            "model": self.model,
            "created": 1678912345,
            "content": f"This is a simulated response from Perplexity for: {prompt[:50]}...",
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": 250,
                "total_tokens": (len(prompt) // 4) + 250
            }
        }


class PerplexityMcpClient:
    """
    Client for interacting with Perplexity through the Model Control Protocol (MCP).
    
    This implementation enables transparent tool use and function calling
    through the Perplexity API, similar to the Claude MCP functionality.
    """
    
    def __init__(self, 
                 base_client: Optional[PerplexityClient] = None,
                 api_key: Optional[str] = None,
                 model: str = "sonar-reasoning-pro",
                 tools: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the Perplexity MCP client.
        
        Args:
            base_client: Existing PerplexityClient instance (optional)
            api_key: Perplexity API key
            model: Model to use
            tools: List of tools to make available
        """
        self.base_client = base_client or PerplexityClient(api_key=api_key, model=model)
        self.model = model
        self.tools = tools or self._default_tools()
    
    def _default_tools(self) -> List[Dict[str, Any]]:
        """Define default tools for the MCP client."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for current information on a specific topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to look up on the web"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search using the base client.
        
        This method is called by the MCP when the search_web tool is used.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        search_system_prompt = """
        You are a specialized web search agent that focuses on retrieving relevant, 
        current information from the web. Your search results should be:
        1. Highly relevant to the query
        2. Factually accurate and up-to-date
        3. Comprehensive, covering multiple perspectives when applicable
        4. Well-structured and clearly presented
        5. Properly sourced with citations to allow verification
        
        Do not include personal opinions or hypothetical scenarios unless requested.
        """
        
        return self.base_client.search(
            query=query,
            system_prompt=search_system_prompt,
            temperature=0.3  # Lower temperature for more factual results
        )
    
    def generate_with_tools(self, 
                          prompt: str, 
                          system_prompt: Optional[str] = None,
                          temperature: float = 0.7,
                          max_tokens: int = 2048) -> Dict[str, Any]:
        """
        Generate a response with potential tool use.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt to guide the model
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with response and tool use details
        """
        if not system_prompt:
            system_prompt = """
            You are a helpful assistant with the ability to use tools when needed.
            If a user's request requires current information or specific data,
            use the appropriate tool. Otherwise, respond directly based on your knowledge.
            When using tools, follow this process:
            1. Determine which tool is most appropriate for the task
            2. Call the tool with the proper parameters
            3. Interpret the tool's response
            4. Provide a final answer incorporating the tool's output
            """
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": self.tools,
            "tool_choice": "auto"
        }
        
        # First API call to see if the model wants to use a tool
        try:
            response = self.base_client._make_request(payload)
            assistant_message = response["choices"][0]["message"]
            
            # Check if the model wants to use a tool
            if "tool_calls" in assistant_message:
                # Process each tool call
                processed_tool_calls = []
                
                for tool_call in assistant_message["tool_calls"]:
                    function_call = tool_call["function"]
                    function_name = function_call["name"]
                    
                    # Parse arguments
                    try:
                        arguments = json.loads(function_call["arguments"])
                    except json.JSONDecodeError:
                        arguments = {"error": "Invalid JSON in arguments"}
                    
                    # Execute the appropriate tool function
                    tool_result = None
                    if function_name == "search_web" and "query" in arguments:
                        tool_result = self.search_web(arguments["query"])
                    else:
                        tool_result = {"error": f"Unknown function: {function_name}"}
                    
                    # Add tool result to processed calls
                    processed_tool_calls.append({
                        "tool_call_id": tool_call["id"],
                        "function_name": function_name,
                        "function_args": arguments,
                        "result": tool_result
                    })
                    
                    # Add the tool response to messages
                    payload["messages"].append(assistant_message)
                    payload["messages"].append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result)
                    })
                
                # Make a second API call to get the final response
                final_response = self.base_client._make_request(payload)
                final_content = final_response["choices"][0]["message"]["content"]
                
                return {
                    "response_id": str(uuid.uuid4()),
                    "content": final_content,
                    "used_tools": True,
                    "tool_calls": processed_tool_calls,
                    "model": self.model,
                    "timestamp": time.time()
                }
            
            # No tool use
            return {
                "response_id": str(uuid.uuid4()),
                "content": assistant_message["content"],
                "used_tools": False,
                "model": self.model,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Tool-based generation failed: {e}")
            return {
                "response_id": str(uuid.uuid4()),
                "content": f"Generation failed: {str(e)}",
                "used_tools": False,
                "error": str(e),
                "model": self.model,
                "timestamp": time.time()
            }


def create_mcp_tool_spec() -> Dict[str, Any]:
    """
    Create a tool specification for the Perplexity MCP integration
    that can be used with Anthropic's Claude API.
    
    Returns:
        Dict containing the tool specification
    """
    return {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for real-time information using Perplexity AI",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web"
                    },
                    "include_links": {
                        "type": "boolean",
                        "description": "Whether to include source links in the response"
                    },
                    "detailed_responses": {
                        "type": "boolean",
                        "description": "Whether to provide detailed reasoning in responses"
                    }
                },
                "required": ["query"]
            }
        }
    } 