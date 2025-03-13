"""
EnhancedClaudeClient: VOT1 Model Control Protocol Implementation

This module implements an enhanced client for Anthropic's Claude models with:
1. Advanced Model Control Protocol (VOT-MCP) implementation
2. Hybrid model approach using Claude 3.7 Sonnet and Thin for cost/performance optimization
3. Integrated memory management
4. Tool use capabilities with automatic function execution
5. Feedback collection and system improvement
"""

import os
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Callable

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedClaudeClient:
    """
    Enhanced Claude client with VOT1 Model Control Protocol implementation.
    
    This client extends the basic Claude client with:
    - Hybrid model approach (Claude 3.7 Sonnet/Thin)
    - Memory integration
    - Tool use with automated execution
    - Cost optimization
    - Adaptive context management
    """
    
    SONNET_MODEL = "claude-3-7-sonnet-20240620"
    THIN_MODEL = "claude-3-5-sonnet-20240620"
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: Optional[str] = None,
                 hybrid_mode: bool = True,
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024,
                 memory_manager=None,
                 tools: Optional[List[Dict[str, Any]]] = None,
                 auto_tool_execution: bool = True,
                 cost_optimization: bool = True):
        """
        Initialize the enhanced Claude client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Primary model to use (defaults to SONNET_MODEL)
            hybrid_mode: Whether to use hybrid model approach
            system: System prompt to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            memory_manager: Optional memory manager instance
            tools: List of available tools
            auto_tool_execution: Whether to automatically execute tools
            cost_optimization: Whether to use cost optimization strategies
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set the ANTHROPIC_API_KEY environment variable.")
        
        self.primary_model = model or self.SONNET_MODEL
        self.secondary_model = self.THIN_MODEL if self.primary_model != self.THIN_MODEL else self.SONNET_MODEL
        self.hybrid_mode = hybrid_mode
        self.system = system or self._default_system_prompt()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory_manager = memory_manager
        self.tools = tools
        self.auto_tool_execution = auto_tool_execution
        self.cost_optimization = cost_optimization
        
        # Initialize clients
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Track usage for cost optimization
        self.usage_stats = {
            "total_tokens": 0,
            "sonnet_calls": 0,
            "thin_calls": 0,
            "tool_calls": 0,
            "start_time": time.time()
        }
        
        logger.info(f"Initialized EnhancedClaudeClient with primary model: {self.primary_model}")
        if self.hybrid_mode:
            logger.info(f"Hybrid mode enabled with secondary model: {self.secondary_model}")
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for the VOT1 system."""
        return """
        You are Claude, an AI assistant enhanced by VOT1 (Village of Thousands) system. 
        Your capabilities include access to current information, advanced memory management,
        and specialized tools when needed.
        
        When generating responses:
        1. Be helpful, harmless, and honest
        2. Provide comprehensive, accurate information
        3. When uncertain, acknowledge limitations
        4. Use available tools when appropriate
        5. Respect user preferences and specifications
        
        You have the ability to use tools to enhance your responses, including web search
        and other specialized capabilities when requested or needed.
        """
    
    def _select_model(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Select the appropriate model based on the task complexity and cost optimization.
        
        In hybrid mode, this intelligently chooses between Sonnet and Thin models:
        - Uses Thin for simpler queries, shorter responses, or when performance isn't critical
        - Uses Sonnet for complex reasoning, creative tasks, or when high quality is essential
        
        Args:
            prompt: The user prompt
            context: Additional context
            
        Returns:
            The model name to use
        """
        if not self.hybrid_mode:
            return self.primary_model
        
        # Simple heuristics for model selection
        
        # Get task type hint from context
        task_type = context.get("task_type", "") if context else ""
        
        # Default to the primary model (usually Sonnet)
        selected_model = self.primary_model
        
        # Use Thin for simple, short queries
        if len(prompt) < 100 and not any(complex_indicator in prompt.lower() for complex_indicator in 
                                        ["explain", "analyze", "compare", "evaluate", "reason"]):
            selected_model = self.THIN_MODEL
        
        # Use Thin for basic information retrieval
        elif any(simple_task in task_type.lower() for simple_task in 
                ["lookup", "simple", "information", "basic", "quick"]):
            selected_model = self.THIN_MODEL
        
        # Use Sonnet for complex reasoning
        elif any(complex_task in task_type.lower() for complex_task in 
                ["complex", "reasoning", "creative", "important", "nuanced"]):
            selected_model = self.SONNET_MODEL
            
        logger.info(f"Selected model {selected_model} for prompt: {prompt[:50]}...")
        return selected_model
    
    def generate(self, 
                prompt: str, 
                system: Optional[str] = None,
                model: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None,
                context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a response to the given prompt.
        
        Args:
            prompt: The prompt to generate a response for
            system: Optional system prompt override
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            context: Additional context for the generation
            
        Returns:
            The generated response
        """
        context = context or {}
        
        # Determine which model to use
        model_to_use = model or self._select_model(prompt, context)
        
        # Retrieve relevant memories if memory manager is available
        memories = []
        if self.memory_manager:
            memories = self.memory_manager.retrieve_relevant_memories(prompt, limit=5)
            
            # Add memories to context
            if memories:
                memories_text = "\n\n".join([f"Memory {i+1}: {memory['content']}" for i, memory in enumerate(memories)])
                context["relevant_memories"] = memories_text
        
        # Construct the message
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Add context as assistant message if needed
        if context and any(k for k in context.keys() if k != "task_type"):
            context_message = "Here is some relevant context:\n\n"
            
            for key, value in context.items():
                if key != "task_type":  # Skip task_type as it's internal
                    context_message += f"--- {key} ---\n{value}\n\n"
            
            messages.insert(0, {
                "role": "assistant",
                "content": context_message
            })
        
        # Make the API call
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=model_to_use,
                messages=messages,
                system=system or self.system,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                tools=self.tools
            )
            
            content = response.content[0].text
            
            # Update usage statistics
            self.usage_stats["total_tokens"] += response.usage.input_tokens + response.usage.output_tokens
            if model_to_use == self.SONNET_MODEL:
                self.usage_stats["sonnet_calls"] += 1
            else:
                self.usage_stats["thin_calls"] += 1
            
            # Store in memory if available
            if self.memory_manager:
                self.memory_manager.add_memory(
                    content=content,
                    memory_type="conversation",
                    metadata={
                        "prompt": prompt,
                        "model": model_to_use,
                        "timestamp": time.time(),
                        "response_time": time.time() - start_time
                    }
                )
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_tools(self,
                           prompt: str,
                           system: Optional[str] = None,
                           model: Optional[str] = None,
                           temperature: Optional[float] = None,
                           max_tokens: Optional[int] = None,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a response with potential tool use.
        
        Args:
            prompt: The prompt to generate a response for
            system: Optional system prompt override
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            context: Additional context
            
        Returns:
            Dictionary with response and tool use details
        """
        if not self.tools:
            logger.warning("No tools available for generate_with_tools call")
            return {
                "content": self.generate(prompt, system, model, temperature, max_tokens, context),
                "used_tools": False
            }
        
        context = context or {}
        
        # Always use the primary model (usually Sonnet) for tool use
        model_to_use = model or self.primary_model
        
        # Retrieve relevant memories if memory manager is available
        memories = []
        if self.memory_manager:
            memories = self.memory_manager.retrieve_relevant_memories(prompt, limit=5)
            
            # Add memories to context
            if memories:
                memories_text = "\n\n".join([f"Memory {i+1}: {memory['content']}" for i, memory in enumerate(memories)])
                context["relevant_memories"] = memories_text
        
        # Construct the message
        messages = []
        
        # Add context as assistant message if needed
        if context and any(k for k in context.keys() if k != "task_type"):
            context_message = "Here is some relevant context:\n\n"
            
            for key, value in context.items():
                if key != "task_type":  # Skip task_type as it's internal
                    context_message += f"--- {key} ---\n{value}\n\n"
            
            messages.append({
                "role": "assistant",
                "content": context_message
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Make the API call
        try:
            response = self.client.messages.create(
                model=model_to_use,
                messages=messages,
                system=system or self.system,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                tools=self.tools
            )
            
            # Update usage statistics
            self.usage_stats["total_tokens"] += response.usage.input_tokens + response.usage.output_tokens
            self.usage_stats["sonnet_calls"] += 1
            
            # Check if the model wants to use a tool
            if response.content[0].type == "tool_use":
                tool_use = response.content[0].tool_use
                
                if self.auto_tool_execution:
                    # Execute the tool
                    tool_result = self._execute_tool(tool_use)
                    self.usage_stats["tool_calls"] += 1
                    
                    # Continue the conversation with the tool result
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_use": {
                            "name": tool_use.name,
                            "input": tool_use.input
                        }
                    })
                    
                    messages.append({
                        "role": "user",
                        "content": None,
                        "tool_result": {
                            "content": json.dumps(tool_result)
                        }
                    })
                    
                    # Get the final response
                    final_response = self.client.messages.create(
                        model=model_to_use,
                        messages=messages,
                        system=system or self.system,
                        temperature=temperature or self.temperature,
                        max_tokens=max_tokens or self.max_tokens
                    )
                    
                    # Update usage statistics again
                    self.usage_stats["total_tokens"] += final_response.usage.input_tokens + final_response.usage.output_tokens
                    
                    content = final_response.content[0].text
                    
                    result = {
                        "content": content,
                        "used_tools": True,
                        "tool_use": {
                            "name": tool_use.name,
                            "input": tool_use.input,
                            "result": tool_result
                        }
                    }
                else:
                    # Return without executing
                    result = {
                        "content": None,
                        "used_tools": True,
                        "tool_use": {
                            "name": tool_use.name,
                            "input": tool_use.input,
                            "result": None
                        },
                        "message": "Tool use requested but auto_tool_execution is disabled"
                    }
            else:
                # No tool use
                content = response.content[0].text
                result = {
                    "content": content,
                    "used_tools": False
                }
            
            # Store in memory if available
            if self.memory_manager:
                self.memory_manager.add_memory(
                    content=result["content"] if result["content"] else str(result),
                    memory_type="conversation",
                    metadata={
                        "prompt": prompt,
                        "model": model_to_use,
                        "used_tools": result["used_tools"],
                        "timestamp": time.time()
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response with tools: {e}")
            return {
                "content": f"Error generating response: {str(e)}",
                "used_tools": False,
                "error": str(e)
            }
    
    def _execute_tool(self, tool_use: Any) -> Dict[str, Any]:
        """
        Execute a tool based on the tool use request.
        
        Args:
            tool_use: Tool use request from Claude
            
        Returns:
            Tool execution result
        """
        tool_name = tool_use.name
        tool_input = json.loads(tool_use.input) if isinstance(tool_use.input, str) else tool_use.input
        
        logger.info(f"Executing tool: {tool_name}")
        
        try:
            # Here we would dispatch to the appropriate tool handler
            # This is a simplified implementation
            if tool_name == "web_search" and hasattr(self, "_web_search"):
                return self._web_search(tool_input.get("query", ""))
            elif tool_name == "calculator" and hasattr(self, "_calculator"):
                return self._calculator(tool_input.get("expression", ""))
            else:
                logger.warning(f"Unknown tool or no handler available: {tool_name}")
                return {"error": f"Unknown tool or no handler available: {tool_name}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": f"Error executing tool {tool_name}: {str(e)}"}
    
    def register_tool_handler(self, tool_name: str, handler: Callable) -> None:
        """
        Register a handler for a specific tool.
        
        Args:
            tool_name: Name of the tool
            handler: Function to handle tool execution
        """
        setattr(self, f"_{tool_name}", handler)
        logger.info(f"Registered handler for tool: {tool_name}")
    
    def add_web_search_capability(self, perplexity_client=None) -> None:
        """
        Add web search capability using Perplexity.
        
        Args:
            perplexity_client: Optional pre-configured Perplexity client
        """
        try:
            from vot1.perplexity_client import PerplexityClient
            
            # Initialize Perplexity client if not provided
            self.perplexity_client = perplexity_client or PerplexityClient()
            
            # Define web search tool
            web_search_tool = {
                "type": "function",
                "function": {
                    "name": "web_search",
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
            
            # Add tool to available tools
            self.tools = self.tools or []
            self.tools.append(web_search_tool)
            
            # Register handler
            self.register_tool_handler("web_search", self._web_search_handler)
            
            logger.info("Web search capability added successfully")
            
        except ImportError as e:
            logger.error(f"Failed to add web search capability: {e}")
            raise
    
    def _web_search_handler(self, query: str) -> Dict[str, Any]:
        """
        Handle web search requests.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        if not hasattr(self, "perplexity_client"):
            return {"error": "Perplexity client not initialized"}
        
        try:
            result = self.perplexity_client.search(query)
            
            # Store in memory if available
            if self.memory_manager:
                self.memory_manager.add_memory(
                    content=result["content"],
                    memory_type="semantic",
                    metadata={
                        "source": "web_search",
                        "query": query,
                        "timestamp": time.time()
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"error": f"Web search failed: {str(e)}"}
    
    def add_reasoning_capability(self, reasoning_engine=None) -> None:
        """
        Add enhanced reasoning capabilities using OWL integration.
        
        Args:
            reasoning_engine: Optional pre-configured reasoning engine
        """
        try:
            from vot1.owl_integration import OwlEnhancedReasoning
            
            # Initialize reasoning engine if not provided
            self.reasoning_engine = reasoning_engine or OwlEnhancedReasoning(model_name=self.primary_model)
            
            # Define reasoning tool
            reasoning_tool = {
                "type": "function",
                "function": {
                    "name": "enhanced_reasoning",
                    "description": "Apply advanced reasoning techniques to solve complex problems",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The problem or question to reason about"
                            },
                            "strategy": {
                                "type": "string",
                                "description": "The reasoning strategy to use (react, cot, reflexion, tot)",
                                "enum": ["react", "cot", "reflexion", "tot"]
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
            
            # Add tool to available tools
            self.tools = self.tools or []
            self.tools.append(reasoning_tool)
            
            # Register handler
            self.register_tool_handler("enhanced_reasoning", self._reasoning_handler)
            
            logger.info("Enhanced reasoning capability added successfully")
            
        except ImportError as e:
            logger.error(f"Failed to add reasoning capability: {e}")
            raise
    
    def _reasoning_handler(self, query: str, strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle enhanced reasoning requests.
        
        Args:
            query: The problem to reason about
            strategy: Optional reasoning strategy
            
        Returns:
            Reasoning results
        """
        if not hasattr(self, "reasoning_engine"):
            return {"error": "Reasoning engine not initialized"}
        
        try:
            result = self.reasoning_engine.reason(query, strategy=strategy)
            
            # Store in memory if available
            if self.memory_manager:
                self.memory_manager.add_memory(
                    content=f"Reasoning: {result.get('answer', '')}",
                    memory_type="semantic",
                    metadata={
                        "source": "enhanced_reasoning",
                        "query": query,
                        "strategy": strategy,
                        "reasoning": result.get("reasoning", ""),
                        "timestamp": time.time()
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced reasoning failed: {e}")
            return {"error": f"Enhanced reasoning failed: {str(e)}"}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the client.
        
        Returns:
            Dictionary with usage statistics
        """
        stats = self.usage_stats.copy()
        stats["runtime"] = time.time() - stats["start_time"]
        
        # Calculate approximate costs
        stats["estimated_cost"] = self._calculate_estimated_cost()
        
        return stats
    
    def _calculate_estimated_cost(self) -> float:
        """
        Calculate estimated API cost based on usage.
        
        Returns:
            Estimated cost in USD
        """
        # These rates are approximations and should be updated as pricing changes
        sonnet_input_cost_per_1k = 0.009
        sonnet_output_cost_per_1k = 0.027
        thin_input_cost_per_1k = 0.003
        thin_output_cost_per_1k = 0.015
        
        # Estimate token split between models and between input/output
        # This is a simplified calculation
        total_tokens = self.usage_stats["total_tokens"]
        sonnet_ratio = self.usage_stats["sonnet_calls"] / (self.usage_stats["sonnet_calls"] + self.usage_stats["thin_calls"]) if (self.usage_stats["sonnet_calls"] + self.usage_stats["thin_calls"]) > 0 else 0
        
        sonnet_tokens = total_tokens * sonnet_ratio
        thin_tokens = total_tokens * (1 - sonnet_ratio)
        
        # Assume 30% input, 70% output split on average
        sonnet_input_tokens = sonnet_tokens * 0.3
        sonnet_output_tokens = sonnet_tokens * 0.7
        thin_input_tokens = thin_tokens * 0.3
        thin_output_tokens = thin_tokens * 0.7
        
        # Calculate costs
        sonnet_cost = (sonnet_input_tokens / 1000 * sonnet_input_cost_per_1k) + (sonnet_output_tokens / 1000 * sonnet_output_cost_per_1k)
        thin_cost = (thin_input_tokens / 1000 * thin_input_cost_per_1k) + (thin_output_tokens / 1000 * thin_output_cost_per_1k)
        
        return sonnet_cost + thin_cost 