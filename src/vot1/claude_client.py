"""
VOTai Claude 3.7 Sonnet Client

This module provides a client for interacting with the Claude 3.7 Sonnet API,
with support for streaming, hybrid thinking, and tool execution.
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, AsyncGenerator

import anthropic
from anthropic.types import (
    MessageParam,
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    MessageStartEvent,
    MessageStopEvent,
    MessageDeltaEvent
)

try:
    # Absolute imports (for installed package)
    from vot1.utils.branding import format_status
    from vot1.utils.logging import get_logger
except ImportError:
    # Relative imports (for development)
    from src.vot1.utils.branding import format_status
    from src.vot1.utils.logging import get_logger

logger = get_logger(__name__)

class ClaudeClient:
    """
    Client for interacting with Claude 3.7 Sonnet API.
    
    Features:
    - Streaming and non-streaming modes
    - Hybrid thinking with maximum token utilization
    - Tool usage and validation
    - Embedding generation for semantic search
    - Memory-efficient processing
    """
    
    # Claude 3.7 Sonnet configuration
    CLAUDE_DEFAULT_MODEL = "claude-3-7-sonnet-20240708"
    CLAUDE_MAX_TOKENS = 15000
    CLAUDE_MAX_TOKENS_IN_PROMPT = 170000  # Approximate maximum tokens for prompt
    
    # Supported Claude models with capabilities
    CLAUDE_MODELS = {
        "claude-3-7-sonnet-20240708": {
            "max_tokens": 15000,
            "context_window": 180000,
            "supports_tools": True,
            "supports_thinking": True,
            "supports_vision": True,
            "description": "Latest Claude 3.7 Sonnet (July 2024)"
        },
        "claude-3-5-sonnet-20240620": {
            "max_tokens": 15000,
            "context_window": 170000,
            "supports_tools": True,
            "supports_thinking": True,
            "supports_vision": True,
            "description": "Claude 3.5 Sonnet (June 2024)"
        },
        "claude-3-haiku-20240307": {
            "max_tokens": 4096,
            "context_window": 48000,
            "supports_tools": True,
            "supports_thinking": False,
            "supports_vision": True,
            "description": "Claude 3 Haiku (March 2024)"
        }
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        timeout: int = 120,
        max_retries: int = 3,
        default_system_prompt: Optional[str] = None,
        memory_bridge: Optional[Any] = None
    ):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries on failure
            default_system_prompt: Default system prompt to use
            memory_bridge: Optional memory bridge instance
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning(format_status("warning", "No Anthropic API key provided; some features will be limited"))
            
        self.model = model or self.CLAUDE_DEFAULT_MODEL
        self.max_tokens = max_tokens or self.CLAUDE_MODELS.get(self.model, {}).get("max_tokens", self.CLAUDE_MAX_TOKENS)
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_system_prompt = default_system_prompt
        self.memory_bridge = memory_bridge
        
        # Validate model
        if self.model not in self.CLAUDE_MODELS:
            logger.warning(format_status("warning", f"Unrecognized Claude model: {self.model}, defaulting to {self.CLAUDE_DEFAULT_MODEL}"))
            self.model = self.CLAUDE_DEFAULT_MODEL
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        
        # Statistics
        self.stats = {
            "requests": 0,
            "tokens_generated": 0,
            "tokens_processed": 0,
            "streaming_requests": 0,
            "tool_executions": 0,
            "errors": 0,
            "start_time": time.time()
        }
        
        # Tool state
        self.registered_tools = {}
        
        logger.info(format_status("info", f"Claude client initialized with model: {self.model}"))
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        tools: Optional[List[Dict[str, Any]]] = None,
        with_thinking: bool = False
    ) -> str:
        """
        Generate a response from Claude.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p for sampling
            tools: Tools to provide to Claude
            with_thinking: Whether to include thinking in the response
            
        Returns:
            Generated text
        """
        if not self.client:
            raise ValueError("Claude client not initialized. Please provide a valid API key.")
        
        self.stats["requests"] += 1
        
        # Create message
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Set up the request parameters
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p
        }
        
        # Add system prompt if provided
        if system_prompt or self.default_system_prompt:
            request_params["system"] = system_prompt or self.default_system_prompt
        
        # Add tools if provided
        if tools and self._model_supports_tools():
            request_params["tools"] = tools
        
        # Add thinking if requested and supported
        if with_thinking and self._model_supports_thinking():
            request_params["thinking"] = True
        
        # Make the request with retry logic
        response = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.messages.create(**request_params)
                break
            except anthropic.APIError as e:
                if attempt < self.max_retries - 1 and e.status_code in (429, 500, 502, 503, 504):
                    # Exponential backoff
                    delay = 2 ** attempt
                    logger.warning(format_status("warning", f"API error ({e.status_code}), retrying in {delay}s..."))
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed or non-retryable error
                    self.stats["errors"] += 1
                    logger.error(format_status("error", f"Claude API error: {str(e)}"))
                    raise
        
        if not response:
            self.stats["errors"] += 1
            raise Exception("Failed to get response from Claude API")
        
        # Extract the text from the response
        content = response.content[0].text if response.content else ""
        
        # Update stats
        self.stats["tokens_generated"] += len(content.split()) // 4  # Rough estimation
        
        return content
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        tools: Optional[List[Dict[str, Any]]] = None,
        with_thinking: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from Claude.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p for sampling
            tools: Tools to provide to Claude
            with_thinking: Whether to include thinking in the response
            
        Yields:
            Text chunks as they are generated
        """
        if not self.client:
            raise ValueError("Claude client not initialized. Please provide a valid API key.")
        
        self.stats["requests"] += 1
        self.stats["streaming_requests"] += 1
        
        # Create message
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Set up the request parameters
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }
        
        # Add system prompt if provided
        if system_prompt or self.default_system_prompt:
            request_params["system"] = system_prompt or self.default_system_prompt
        
        # Add tools if provided
        if tools and self._model_supports_tools():
            request_params["tools"] = tools
        
        # Add thinking if requested and supported
        if with_thinking and self._model_supports_thinking():
            request_params["thinking"] = True
        
        try:
            # Make the streaming request
            stream = await self.client.messages.create(**request_params)
            
            # Process the stream
            current_thinking = []
            async for chunk in stream:
                # Handle message start
                if isinstance(chunk, MessageStartEvent):
                    continue
                
                # Handle content block start
                elif isinstance(chunk, ContentBlockStartEvent):
                    continue
                
                # Handle content delta (actual text)
                elif isinstance(chunk, ContentBlockDeltaEvent):
                    self.stats["tokens_generated"] += len(chunk.delta.text.split()) // 10  # Rough estimation
                    yield chunk.delta.text
                
                # Handle thinking (if enabled)
                elif hasattr(chunk, "thinking") and chunk.thinking:
                    current_thinking.append(chunk.thinking)
                    # We don't yield thinking - it's collected for later use
                
                # Handle message delta (unused)
                elif isinstance(chunk, MessageDeltaEvent):
                    continue
                
                # Handle message stop
                elif isinstance(chunk, MessageStopEvent):
                    # Store thinking in memory if available
                    if current_thinking and self.memory_bridge:
                        thinking_text = "\n".join(current_thinking)
                        await self._store_thinking_in_memory(thinking_text, prompt)
        
        except anthropic.APIError as e:
            self.stats["errors"] += 1
            logger.error(format_status("error", f"Claude API streaming error: {str(e)}"))
            yield f"Error: {str(e)}"
            return
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(format_status("error", f"Unexpected error during streaming: {str(e)}"))
            yield f"Error: {str(e)}"
            return
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding for the given text.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            Embedding vector
        """
        if not self.client:
            raise ValueError("Claude client not initialized. Please provide a valid API key.")
        
        # Truncate text if needed
        if len(text) > 8000:
            text = text[:8000]
        
        try:
            embedding = await self.client.embeddings.create(
                input=text,
                model="claude-3-sonnet-20240229"  # Use default embedding model
            )
            
            return embedding.embedding
        except Exception as e:
            logger.error(format_status("error", f"Error creating embedding: {str(e)}"))
            # Return empty embedding vector as fallback
            return [0.0] * 1024
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        store_result: bool = True
    ) -> Any:
        """
        Execute a registered tool.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            store_result: Whether to store the result in memory
            
        Returns:
            Tool execution result
        """
        self.stats["tool_executions"] += 1
        
        # Check if tool is registered
        if tool_name not in self.registered_tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")
        
        tool = self.registered_tools[tool_name]
        
        # Execute the tool
        try:
            result = await tool["function"](parameters)
            
            # Store the result in memory if requested
            if store_result and self.memory_bridge:
                await self._store_tool_execution(tool_name, parameters, result, success=True)
            
            return result
        except Exception as e:
            logger.error(format_status("error", f"Error executing tool '{tool_name}': {str(e)}"))
            
            # Store the error in memory if requested
            if store_result and self.memory_bridge:
                await self._store_tool_execution(tool_name, parameters, str(e), success=False)
            
            raise
    
    def register_tool(
        self,
        name: str,
        description: str,
        function: callable,
        parameters_schema: Dict[str, Any]
    ) -> None:
        """
        Register a tool for use with Claude.
        
        Args:
            name: Tool name
            description: Tool description
            function: Async function to execute the tool
            parameters_schema: JSON Schema for the tool parameters
        """
        # Create tool definition
        tool_def = {
            "name": name,
            "description": description,
            "input_schema": parameters_schema
        }
        
        # Store the tool
        self.registered_tools[name] = {
            "definition": tool_def,
            "function": function
        }
        
        logger.info(format_status("info", f"Registered tool: {name}"))
    
    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a registered tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool schema or None if not found
        """
        if name in self.registered_tools:
            return self.registered_tools[name]["definition"]
        return None
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all registered tools.
        
        Returns:
            List of tool schemas
        """
        return [tool["definition"] for tool in self.registered_tools.values()]
    
    async def _store_thinking_in_memory(self, thinking: str, prompt: str) -> None:
        """Store thinking in memory bridge"""
        if not self.memory_bridge:
            return
        
        try:
            await self.memory_bridge.store_memory(
                content=thinking,
                memory_type="thought",
                metadata={
                    "prompt": prompt,
                    "model": self.model
                }
            )
        except Exception as e:
            logger.error(format_status("error", f"Error storing thinking in memory: {str(e)}"))
    
    async def _store_tool_execution(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        success: bool
    ) -> None:
        """Store tool execution in memory bridge"""
        if not self.memory_bridge:
            return
        
        try:
            # Convert result to string if needed
            if not isinstance(result, str):
                if isinstance(result, dict):
                    result_str = json.dumps(result)
                else:
                    result_str = str(result)
            else:
                result_str = result
            
            # Create content
            if success:
                content = f"Tool execution: {tool_name}\nParameters: {json.dumps(parameters)}\nResult: {result_str}"
            else:
                content = f"Tool execution error: {tool_name}\nParameters: {json.dumps(parameters)}\nError: {result_str}"
            
            # Store in memory
            await self.memory_bridge.store_memory(
                content=content,
                memory_type="tool_execution",
                metadata={
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "success": success
                }
            )
        except Exception as e:
            logger.error(format_status("error", f"Error storing tool execution in memory: {str(e)}"))
    
    def _model_supports_tools(self) -> bool:
        """Check if the current model supports tools"""
        return self.CLAUDE_MODELS.get(self.model, {}).get("supports_tools", False)
    
    def _model_supports_thinking(self) -> bool:
        """Check if the current model supports thinking"""
        return self.CLAUDE_MODELS.get(self.model, {}).get("supports_thinking", False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        current_time = time.time()
        uptime = current_time - self.stats["start_time"]
        
        return {
            **self.stats,
            "uptime": uptime,
            "requests_per_minute": (self.stats["requests"] / (uptime / 60)) if uptime > 0 else 0,
            "tokens_per_second": (self.stats["tokens_generated"] / uptime) if uptime > 0 else 0,
            "current_model": self.model,
            "registered_tools": len(self.registered_tools)
        } 