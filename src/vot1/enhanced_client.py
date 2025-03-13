#!/usr/bin/env python3
"""
VOT1 Enhanced Claude Client with Perplexity Integration

An enhanced Claude client that integrates Perplexity's sonar-reasoning-pro model
for real-time web search capabilities, creating a powerful AI assistant with
access to the latest information.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Callable
import anthropic
from anthropic.types import Message
from datetime import datetime

from vot1.perplexity_client import PerplexityMcpClient, create_mcp_tool_spec
from vot1.memory import MemoryManager

logger = logging.getLogger(__name__)

class VOT1Client:
    """
    Enhanced Claude client with Perplexity MCP integration for web search.
    
    This client combines the power of Anthropic's Claude with Perplexity's 
    sonar-reasoning-pro model to create an AI assistant with real-time
    web search capabilities and enhanced memory management.
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        perplexity_api_key: Optional[str] = None,
        claude_model: str = "claude-3-5-sonnet-20240620",
        perplexity_model: str = "sonar-reasoning-pro",
        memory_manager: Optional[MemoryManager] = None,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the VOT1 client with both Claude and Perplexity capabilities.
        
        Args:
            anthropic_api_key: Anthropic API key. If None, will look for ANTHROPIC_API_KEY env var.
            perplexity_api_key: Perplexity API key. If None, will look for PERPLEXITY_API_KEY env var.
            claude_model: Claude model to use. Default is claude-3-5-sonnet.
            perplexity_model: Perplexity model to use. Default is sonar-reasoning-pro.
            memory_manager: Optional MemoryManager instance for memory capabilities.
            max_tokens: Maximum tokens for Claude responses.
            system_prompt: Custom system prompt for Claude.
        """
        # Initialize the Anthropic client
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError(
                "Anthropic API key is required. Either pass it directly or "
                "set the ANTHROPIC_API_KEY environment variable."
            )
        
        self.client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        self.claude_model = claude_model
        self.max_tokens = max_tokens
        
        # Initialize the default system prompt if none provided
        default_system_prompt = (
            "You are VOT1, a powerful AI assistant enhanced with real-time web search "
            "capabilities through Perplexity AI. You have access to the latest information "
            "and can search the web to answer questions. When information might be outdated "
            "or you're unsure, use your web search capability to find accurate and current "
            "information. Always provide helpful, accurate, and ethical responses."
        )
        self.system_prompt = system_prompt or default_system_prompt
        
        # Initialize the Perplexity client
        try:
            self.perplexity_client = PerplexityMcpClient(
                api_key=perplexity_api_key,
                model=perplexity_model
            )
            self.has_perplexity = True
            logger.info("Perplexity MCP client initialized successfully")
        except (ValueError, Exception) as e:
            logger.warning(f"Perplexity client initialization failed: {e}")
            logger.warning("Web search capabilities will be disabled")
            self.has_perplexity = False
            self.perplexity_client = None
        
        # Set up memory management
        self.memory_manager = memory_manager
        
        # Set up tools for Claude
        self.tools = []
        if self.has_perplexity:
            self.tools.append(create_mcp_tool_spec())
        
        logger.info(f"VOT1 client initialized with Claude model: {claude_model}")
        if self.has_perplexity:
            logger.info(f"Web search enabled with Perplexity model: {perplexity_model}")

    def generate_response(
        self,
        prompt: str,
        conversation_id: Optional[str] = None,
        use_memory: bool = True,
        use_web_search: bool = True,
        custom_system_prompt: Optional[str] = None,
        tool_choice: Optional[str] = None,
        save_to_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a response using Claude with optional web search via Perplexity.
        
        Args:
            prompt: The user prompt to respond to
            conversation_id: Optional conversation ID for memory retrieval
            use_memory: Whether to use memory for context
            use_web_search: Whether to allow web search for this request
            custom_system_prompt: Optional custom system prompt to override the default
            tool_choice: Optional tool choice mode ('auto', 'required', or None)
            save_to_memory: Whether to save the interaction to memory
        
        Returns:
            Dict containing the response and metadata
        """
        # Prepare system prompt
        system_prompt = custom_system_prompt or self.system_prompt
        
        # Retrieve relevant memory if memory manager is available and use_memory is True
        memory_context = ""
        if self.memory_manager and use_memory and conversation_id:
            memories = self.memory_manager.retrieve_relevant_memories(prompt, limit=5)
            if memories:
                memory_context = "Relevant information from memory:\n"
                for i, memory in enumerate(memories, 1):
                    memory_context += f"{i}. {memory['content']}\n"
                memory_context += "\n"
        
        # Set up the messages
        messages = []
        if memory_context:
            # Add memory context to the system prompt
            system_prompt = f"{system_prompt}\n\n{memory_context}"
        
        # Build available tools
        tools = []
        if use_web_search and self.has_perplexity:
            tools = self.tools
        
        # Make the request to Claude
        try:
            response = self.client.messages.create(
                model=self.claude_model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                tools=tools if tools else None,
                tool_choice=tool_choice
            )
            
            # Process tool calls if any
            processed_response = self._process_tool_calls(response, prompt)
            
            # Save to memory if requested
            if save_to_memory and self.memory_manager and conversation_id:
                self.memory_manager.add_conversation_memory(
                    conversation_id=conversation_id,
                    role="user",
                    content=prompt,
                    timestamp=datetime.now().isoformat()
                )
                self.memory_manager.add_conversation_memory(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=processed_response["content"],
                    timestamp=datetime.now().isoformat(),
                    metadata={"web_search_used": processed_response.get("web_search_used", False)}
                )
            
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "content": f"I encountered an error while processing your request: {str(e)}",
                "error": str(e)
            }
    
    def _process_tool_calls(self, response: Message, original_prompt: str) -> Dict[str, Any]:
        """Process any tool calls in the Claude response."""
        result = {
            "content": response.content[0].text,
            "model": self.claude_model,
            "web_search_used": False
        }
        
        # Check if there are tool calls
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            return result
        
        # Process each tool call
        for tool_call in response.tool_calls:
            if tool_call.name == "search_web" and self.has_perplexity:
                # Execute web search
                query = tool_call.input.get("query")
                include_links = tool_call.input.get("include_links", True)
                detailed_responses = tool_call.input.get("detailed_responses", True)
                
                if query:
                    try:
                        search_result = self.perplexity_client.search(
                            query=query,
                            include_links=include_links,
                            detailed_responses=detailed_responses
                        )
                        
                        # Format the search result for Claude
                        if "answer" in search_result:
                            web_info = f"Web search results for '{query}':\n{search_result['answer']}\n\n"
                            if include_links and "links" in search_result and search_result["links"]:
                                web_info += "Sources:\n"
                                for link in search_result["links"]:
                                    web_info += f"- {link.get('title', 'Unnamed Source')}: {link.get('url', '')}\n"
                            
                            # Generate a new response with the web search results
                            new_response = self.client.messages.create(
                                model=self.claude_model,
                                max_tokens=self.max_tokens,
                                system=f"{self.system_prompt}\n\nWEB SEARCH RESULTS:\n{web_info}",
                                messages=[{"role": "user", "content": original_prompt}]
                            )
                            
                            result["content"] = new_response.content[0].text
                            result["web_search_used"] = True
                            
                            # Save search result to memory if memory manager is available
                            if self.memory_manager:
                                self.memory_manager.add_semantic_memory(
                                    content=web_info,
                                    metadata={
                                        "type": "web_search",
                                        "query": query,
                                        "source": "perplexity",
                                        "timestamp": datetime.now().isoformat()
                                    }
                                )
                    except Exception as e:
                        logger.error(f"Error during web search: {e}")
                        result["web_search_error"] = str(e)
        
        return result
    
    def search_web(self, query: str) -> Dict[str, Any]:
        """
        Direct method to search the web using Perplexity.
        
        Args:
            query: The search query
            
        Returns:
            Dict containing the search results and metadata
        """
        if not self.has_perplexity or not self.perplexity_client:
            return {
                "error": "Web search capability is not available. Check Perplexity API key."
            }
        
        try:
            return self.perplexity_client.search(query=query)
        except Exception as e:
            logger.error(f"Error during direct web search: {e}")
            return {"error": str(e)}
    
    def add_knowledge(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add knowledge to the semantic memory.
        
        Args:
            content: The knowledge content to add
            metadata: Optional metadata about the knowledge
            
        Returns:
            Boolean indicating success
        """
        if not self.memory_manager:
            logger.warning("Cannot add knowledge: Memory manager not initialized")
            return False
        
        try:
            self.memory_manager.add_semantic_memory(content=content, metadata=metadata)
            return True
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return False 