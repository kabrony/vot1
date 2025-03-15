"""
Example of using Model Control Protocol (MCP) with Composio in the VOTai system

This script demonstrates how to:
1. Initialize the VOT-MCP
2. Register Composio tools with the MCP
3. Execute tools through the MCP
4. Process results with memory integration
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try to import from the VOTai system
    from src.vot1.vot_mcp import VotModelControlProtocol
    from src.vot1.composio.client import ComposioClient
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.memory import MemoryManager
except ImportError:
    print("VOTai system not found. Please ensure you're in the correct directory.")
    sys.exit(1)

class MCPComposioExample:
    """
    Example class demonstrating MCP with Composio integration
    """
    
    def __init__(self):
        """Initialize the example with MCP and Composio components"""
        # Initialize memory manager
        self.memory_manager = MemoryManager(memory_path="memory/mcp_example")
        
        # Initialize MCP
        self.mcp = VotModelControlProtocol(
            primary_provider=VotModelControlProtocol.PROVIDER_ANTHROPIC,
            primary_model="claude-3-7-sonnet-20240620",
            memory_manager=self.memory_manager,
            config={
                "max_thinking_tokens": 8000,
                "streaming": True
            }
        )
        
        # Initialize Composio client
        self.composio_client = ComposioClient(
            api_key=os.environ.get("COMPOSIO_API_KEY"),
            mcp_url=os.environ.get("COMPOSIO_MCP_URL")
        )
        
        # Initialize memory bridge
        self.memory_bridge = ComposioMemoryBridge(
            composio_client=self.composio_client,
            memory_manager=self.memory_manager
        )
        
        print("MCP Composio Example initialized successfully")
    
    async def register_example_tools(self):
        """Register example tools with the MCP"""
        print("\nRegistering example tools with MCP...")
        
        # Weather tool
        weather_tool = {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit of temperature to use"
                    }
                },
                "required": ["location"]
            }
        }
        
        # Calculator tool
        calculator_tool = {
            "name": "calculator",
            "description": "Perform a calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
        
        # Register tools with MCP
        self.mcp.register_tool("get_weather", self._weather_tool_handler)
        self.mcp.register_tool("calculator", self._calculator_tool_handler)
        
        # Add tools to MCP
        self.mcp.tools = [weather_tool, calculator_tool]
        
        print("Example tools registered successfully")
    
    def _weather_tool_handler(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather tool requests"""
        location = params.get("location", "Unknown")
        unit = params.get("unit", "celsius")
        
        # In a real implementation, this would call a weather API
        # This is just a mock response
        if unit == "celsius":
            temperature = 22
            unit_symbol = "°C"
        else:
            temperature = 72
            unit_symbol = "°F"
        
        return {
            "location": location,
            "temperature": f"{temperature}{unit_symbol}",
            "conditions": "Partly cloudy",
            "humidity": "65%",
            "wind": "10 km/h"
        }
    
    def _calculator_tool_handler(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calculator tool requests"""
        expression = params.get("expression", "")
        
        try:
            # Safe evaluation of mathematical expressions
            # In a real implementation, you would use a proper math library
            # This is just a simple example
            allowed_chars = set("0123456789+-*/() .")
            if not all(c in allowed_chars for c in expression):
                raise ValueError("Invalid characters in expression")
            
            result = eval(expression)
            return {
                "expression": expression,
                "result": result
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e)
            }
    
    async def process_with_tools(self, prompt: str) -> Dict[str, Any]:
        """Process a prompt with MCP and tools"""
        print(f"\nProcessing prompt: {prompt}")
        
        # Process with MCP
        response = await self.mcp.process_request_async(
            prompt=prompt,
            system="You are a helpful assistant with access to tools. Use them when appropriate.",
            context={
                "memory_context": await self.memory_manager.get_recent_memories(limit=5)
            }
        )
        
        # Store the response in memory
        memory_id = await self.memory_manager.store_memory(
            content=response["content"],
            memory_type="mcp_response",
            metadata={
                "prompt": prompt,
                "model": response["model"],
                "provider": response["provider"]
            }
        )
        
        print(f"\nResponse: {response['content']}")
        print(f"Memory ID: {memory_id}")
        
        return response
    
    async def run_example(self):
        """Run the complete example"""
        try:
            # Register tools
            await self.register_example_tools()
            
            # Process prompts with tools
            prompts = [
                "What's the weather like in New York?",
                "Calculate 125 * 37",
                "Can you help me understand how MCP works with Composio tools?"
            ]
            
            for prompt in prompts:
                await self.process_with_tools(prompt)
                # Add a small delay between requests
                await asyncio.sleep(1)
            
            # Demonstrate memory integration
            print("\nRetrieving memories related to MCP...")
            memories = await self.memory_manager.search_memories(
                query="MCP Composio tools",
                limit=5
            )
            
            print(f"Found {len(memories)} related memories:")
            for i, memory in enumerate(memories, 1):
                print(f"\n{i}. Memory ID: {memory['id']}")
                print(f"   Content: {memory['content'][:100]}...")
            
            print("\nExample completed successfully")
            
        except Exception as e:
            print(f"\nError in example: {str(e)}")
            import traceback
            traceback.print_exc()

async def main():
    """Run the MCP Composio example"""
    example = MCPComposioExample()
    await example.run_example()

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 