"""
VOTai Composio Tools Example

This example demonstrates how to register and use Composio tools with the VOTai system,
integrating them with Claude 3.7 Sonnet and the memory system.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try to import from installed package
    from vot1.initialize import initialize_system
    from vot1.utils.branding import format_status, format_tool_result
    from vot1.utils.logging import get_logger
except ImportError:
    # Fall back to relative imports
    from src.vot1.initialize import initialize_system
    from src.vot1.utils.branding import format_status, format_tool_result
    from src.vot1.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class ComposioToolsExample:
    """
    Example class demonstrating Composio tools integration with VOTai.
    
    This demonstrates how to:
    1. Register custom tools with Claude
    2. List available Composio tools
    3. Execute tools and store results in memory
    4. Use tools in hybrid thinking processes
    """
    
    def __init__(self):
        """Initialize the example (system will be initialized lazily)"""
        self.system = None
        self.memory_bridge = None
        self.claude_client = None
        self.composio_client = None
    
    async def initialize(self):
        """Initialize the VOTai system and required components"""
        # Initialize the system (this will set up logging)
        self.system = await initialize_system()
        
        # Get required components
        self.memory_bridge = await self.system.get_memory_bridge()
        self.claude_client = await self.system.get_claude_client()
        self.composio_client = await self.system.get_composio_client()
        
        # Register some example tools with Claude
        await self._register_example_tools()
        
        logger.info(format_status("success", "Composio Tools Example initialized"))
    
    async def _register_example_tools(self):
        """Register example tools with Claude"""
        # Weather tool
        self.claude_client.register_tool(
            name="get_weather",
            description="Get the current weather for a location",
            function=self._weather_tool,
            parameters_schema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location (city, zip code, etc.)"
                    },
                    "units": {
                        "type": "string",
                        "description": "Temperature units (celsius, fahrenheit)",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        )
        
        # Calculator tool
        self.claude_client.register_tool(
            name="calculator",
            description="Perform mathematical calculations",
            function=self._calculator_tool,
            parameters_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
        
        logger.info(format_status("success", "Example tools registered with Claude"))
    
    async def _weather_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Example implementation of a weather tool"""
        location = parameters.get("location", "")
        units = parameters.get("units", "celsius")
        
        # In a real implementation, this would call a weather API
        # This is just a mock example
        mock_responses = {
            "new york": {"temperature": 72, "conditions": "Partly Cloudy", "humidity": 65},
            "london": {"temperature": 18, "conditions": "Rainy", "humidity": 80},
            "tokyo": {"temperature": 26, "conditions": "Sunny", "humidity": 70},
            "sydney": {"temperature": 22, "conditions": "Clear", "humidity": 60}
        }
        
        # Convert location to lowercase for matching
        location_key = location.lower()
        
        # Find closest match (simple implementation)
        for key in mock_responses:
            if key in location_key or location_key in key:
                location_key = key
                break
        
        # Get weather data or default
        weather = mock_responses.get(location_key, {
            "temperature": 20, 
            "conditions": "Unknown",
            "humidity": 50
        })
        
        # Convert temperature if needed
        if units == "fahrenheit" and "temperature" in weather:
            weather["temperature"] = round((weather["temperature"] * 9/5) + 32)
        
        result = {
            "location": location,
            "temperature": f"{weather['temperature']}°{'F' if units == 'fahrenheit' else 'C'}",
            "conditions": weather["conditions"],
            "humidity": f"{weather['humidity']}%",
            "units": units
        }
        
        return result
    
    async def _calculator_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Example implementation of a calculator tool"""
        expression = parameters.get("expression", "")
        
        try:
            # Use safe eval for basic calculations
            # In real implementation, you'd want more robust parsing
            import ast
            import operator
            
            # Define allowed operators
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.BitXor: operator.xor,
                ast.USub: operator.neg
            }
            
            def safe_eval(expr):
                return eval_node(ast.parse(expr, mode='eval').body)
                
            def eval_node(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.BinOp):
                    return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
                elif isinstance(node, ast.UnaryOp):
                    return operators[type(node.op)](eval_node(node.operand))
                else:
                    raise TypeError(f"Unsupported operation: {node}")
            
            result = safe_eval(expression)
            
            return {
                "expression": expression,
                "result": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "expression": expression,
                "result": None,
                "error": str(e)
            }
    
    async def list_composio_tools(self):
        """List all available Composio tools"""
        if not self.system:
            await self.initialize()
        
        print(format_status("info", "Listing available Composio tools..."))
        
        try:
            tools = await self.composio_client.list_tools()
            
            print(f"\nFound {len(tools)} Composio tools:\n")
            
            for i, tool in enumerate(tools, 1):
                tool_id = tool.get("id", "unknown")
                tool_name = tool.get("name", tool_id)
                tool_description = tool.get("description", "No description")
                
                print(f"{i}. {tool_name} ({tool_id})")
                print(f"   Description: {tool_description}")
                
                # Show parameters if available
                params = tool.get("parameters", [])
                if params:
                    print(f"   Parameters:")
                    for param in params:
                        required = "Required" if param.get("required", False) else "Optional"
                        print(f"   - {param.get('id', 'unknown')}: {param.get('description', '')} ({required})")
                
                print()
            
            return tools
            
        except Exception as e:
            logger.error(f"Error listing Composio tools: {str(e)}")
            print(format_status("error", f"Error listing tools: {str(e)}"))
            return []
    
    async def execute_claude_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Execute a tool registered with Claude"""
        if not self.system:
            await self.initialize()
        
        print(format_status("info", f"Executing Claude tool: {tool_name}"))
        print(f"Parameters: {json.dumps(parameters, indent=2)}")
        
        try:
            # Execute the tool
            result = await self.claude_client.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                store_result=True
            )
            
            print("\n" + format_tool_result(tool_name, result, success=True))
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing Claude tool {tool_name}: {str(e)}")
            print(format_status("error", f"Tool execution error: {str(e)}"))
            return {"error": str(e)}
    
    async def execute_composio_tool(self, tool_id: str, parameters: Dict[str, Any]):
        """Execute a Composio tool"""
        if not self.system:
            await self.initialize()
        
        print(format_status("info", f"Executing Composio tool: {tool_id}"))
        print(f"Parameters: {json.dumps(parameters, indent=2)}")
        
        try:
            # Execute the tool
            result = await self.composio_client.execute_tool(
                tool_id=tool_id,
                parameters=parameters,
                store_in_memory=True
            )
            
            if result.get("success", False):
                print("\n" + format_tool_result(tool_id, {"data": result.get("data")}, success=True))
            else:
                print("\n" + format_tool_result(tool_id, {"error": result.get("error")}, success=False))
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing Composio tool {tool_id}: {str(e)}")
            print(format_status("error", f"Tool execution error: {str(e)}"))
            return {"success": False, "error": str(e)}
    
    async def use_tools_with_claude(self, prompt: str):
        """Use Claude with tools to process a prompt"""
        if not self.system:
            await self.initialize()
        
        print(format_status("info", f"Processing prompt with Claude using tools"))
        print(f"Prompt: {prompt}")
        
        try:
            # Get all tool schemas
            tool_schemas = self.claude_client.get_all_tool_schemas()
            
            # Let Claude decide when to use tools with a modified system prompt
            system_prompt = """You are Claude, an AI assistant with access to tools.
If the user's request requires using a tool, use the most appropriate tool to help respond.
If tool execution fails, explain the failure and try to provide help without the tool if possible.
Always respond to the user in a helpful and informative way."""
            
            # Generate response with Claude, providing tools
            response = await self.claude_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                tools=tool_schemas,
                with_thinking=True
            )
            
            print("\nClaude's response:")
            print("-" * 80)
            print(response)
            print("-" * 80)
            
            return response
            
        except Exception as e:
            logger.error(f"Error using tools with Claude: {str(e)}")
            print(format_status("error", f"Error: {str(e)}"))
            return f"Error: {str(e)}"

async def main():
    """Run the example"""
    # Create example
    example = ComposioToolsExample()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="VOTai Composio Tools Example")
    parser.add_argument("--action", choices=["list", "execute-claude", "execute-composio", "use"],
                      default="use", help="Action to perform")
    parser.add_argument("--tool", help="Tool ID or name to execute")
    parser.add_argument("--parameters", help="JSON string of parameters for tool execution")
    parser.add_argument("--prompt", default="What's the weather in New York? Also, calculate 25 * 4.", 
                      help="Prompt for Claude when using tools")
    args = parser.parse_args()
    
    # Initialize the example
    await example.initialize()
    
    if args.action == "list":
        # List available Composio tools
        await example.list_composio_tools()
        
    elif args.action == "execute-claude":
        # Execute a Claude tool
        if not args.tool:
            print(format_status("error", "Tool name is required for execute-claude action"))
            return
        
        # Parse parameters
        parameters = {}
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(format_status("error", "Invalid JSON parameters"))
                return
        
        await example.execute_claude_tool(args.tool, parameters)
        
    elif args.action == "execute-composio":
        # Execute a Composio tool
        if not args.tool:
            print(format_status("error", "Tool ID is required for execute-composio action"))
            return
        
        # Parse parameters
        parameters = {}
        if args.parameters:
            try:
                parameters = json.loads(args.parameters)
            except json.JSONDecodeError:
                print(format_status("error", "Invalid JSON parameters"))
                return
        
        await example.execute_composio_tool(args.tool, parameters)
        
    else:  # use
        # Use tools with Claude
        await example.use_tools_with_claude(args.prompt)

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 