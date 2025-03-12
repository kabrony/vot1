"""
EnhancedClaudeClient module for interacting with Anthropic's Claude models.

This module provides an enhanced client for Claude with additional features
such as GitHub integration, feedback collection, and more.
"""

from typing import Dict, List, Optional, Union, Any, Literal
import os
import json
import asyncio
import logging
from datetime import datetime
import requests
import anthropic
from anthropic import Anthropic

from .memory import MemoryManager

# Setup logging
logger = logging.getLogger("vot1")

class EnhancedClaudeClient:
    """Enhanced client for interacting with Anthropic's Claude API.
    
    This client extends the basic functionality of Claude with additional
    features like GitHub integration, feedback collection, and more.
    
    Attributes:
        api_key (str): Anthropic API key
        model (str): Claude model to use (default: 'claude-3.7-sonnet-20240620')
        max_tokens (int): Maximum number of tokens to generate
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3.7-sonnet-20240620",
        max_tokens: int = 1024,
        perplexity_api_key: Optional[str] = None,
        memory_storage_dir: str = ".vot1/memory",
    ) -> None:
        """Initialize the EnhancedClaudeClient.
        
        Args:
            api_key: API key for Anthropic. If not provided, will try to get from
                environment variable ANTHROPIC_API_KEY
            model: Claude model to use
            max_tokens: Maximum number of tokens to generate
            perplexity_api_key: API key for Perplexity. If not provided, will try to get from
                environment variable PERPLEXITY_API_KEY
            memory_storage_dir: Directory to store memory data
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as an argument or "
                "as the ANTHROPIC_API_KEY environment variable"
            )
        
        self.model = model
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, str]] = []
        self.github_enabled = False
        self.github_token = None
        self.github_repo = None
        self.github_owner = None
        
        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)
        
        # Initialize Perplexity integration
        self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.perplexity_enabled = self.perplexity_api_key is not None
        if self.perplexity_enabled:
            logger.info("Perplexity integration enabled")
        
        # Initialize Memory Manager
        self.memory = MemoryManager(storage_dir=memory_storage_dir)
        
        logger.info(f"Initialized EnhancedClaudeClient with model {model}")
    
    def send_message(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        stream: bool = False,
        use_perplexity: bool = False,
        temperature: float = 0.7,
        use_memory: bool = True,
        memory_search_query: Optional[str] = None,
    ) -> Union[str, Dict[str, Any]]:
        """Send a message to Claude.
        
        Args:
            prompt: The user's input message
            system_prompt: Optional system prompt to guide Claude's behavior
            stream: Whether to stream the response
            use_perplexity: Whether to use Perplexity for web search augmentation
            temperature: Controls randomness of the output (0.0 to 1.0)
            use_memory: Whether to use memory for context augmentation
            memory_search_query: Query to search memory (if None, uses prompt)
            
        Returns:
            Response from Claude API as a string or dictionary
        """
        # Log the request
        logger.debug(f"Sending message to Claude: {prompt[:50]}...")
        
        # Add to conversation history and memory
        message_id = self.memory.add_conversation_item("user", prompt)
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add previous messages from conversation history for context
        # Limited to the last 10 messages to avoid exceeding context limits
        if len(self.conversation_history) > 1:
            prev_messages = self.conversation_history[:-1][-10:]
            messages = prev_messages + messages
        
        # Enhance with memory context if enabled
        memory_context = ""
        if use_memory and (memory_search_query or prompt):
            search_query = memory_search_query or prompt
            memory_results = self.memory.search_all(search_query, limit=3)
            
            if memory_results["conversation"] or memory_results["semantic"]:
                memory_context = "Relevant information from memory:\n"
                
                for i, item in enumerate(memory_results["conversation"]):
                    memory_context += f"[Conversation {i+1}] {item.get('role', 'unknown')}: {item.get('content', '')}\n"
                
                for i, item in enumerate(memory_results["semantic"]):
                    memory_context += f"[Knowledge {i+1}] {item.get('content', '')}\n"
        
        # Combine memory context with system prompt if available
        if memory_context:
            if system_prompt:
                system_prompt = f"{system_prompt}\n\n{memory_context}"
            else:
                system_prompt = memory_context
        
        if use_perplexity and self.perplexity_enabled:
            # Enhance the prompt with Perplexity search results
            search_results = self._query_perplexity(prompt)
            # Add search results as a system message
            if system_prompt:
                system_prompt += f"\n\nAdditional context from web search: {search_results}"
            else:
                system_prompt = f"Additional context from web search: {search_results}"
            logger.debug("Enhanced prompt with Perplexity search results")
        
        try:
            # Call Anthropic API
            if stream:
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                ) as stream:
                    response_content = ""
                    for text in stream.text_stream:
                        response_content += text
                        # Could yield text here if needed
                    
                    # Get the final message once stream completes
                    response = stream.get_final_message()
                    response_content = response.content[0].text
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                )
                response_content = response.content[0].text
            
            # Add to conversation history and memory
            self.conversation_history.append({"role": "assistant", "content": response_content})
            self.memory.add_conversation_item("assistant", response_content, {
                "model": self.model,
                "system_prompt_used": bool(system_prompt),
                "memory_used": bool(memory_context),
                "web_search_used": use_perplexity and self.perplexity_enabled,
                "in_response_to": message_id
            })
            
            if stream:
                return response_content
            else:
                return {
                    "content": response_content,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                }
                
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise
    
    async def send_message_async(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        use_perplexity: bool = False,
        temperature: float = 0.7,
        use_memory: bool = True,
        memory_search_query: Optional[str] = None,
    ) -> Dict[str, Union[str, float]]:
        """Send a message to Claude asynchronously.
        
        Args:
            prompt: The user's input message
            system_prompt: Optional system prompt to guide Claude's behavior
            use_perplexity: Whether to use Perplexity for web search augmentation
            temperature: Controls randomness of the output (0.0 to 1.0)
            use_memory: Whether to use memory for context augmentation
            memory_search_query: Query to search memory (if None, uses prompt)
            
        Returns:
            Response from Claude API as a dictionary
        """
        # Log the request
        logger.debug(f"Sending async message to Claude: {prompt[:50]}...")
        
        # Add to conversation history and memory
        message_id = self.memory.add_conversation_item("user", prompt)
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add previous messages from conversation history for context
        # Limited to the last 10 messages to avoid exceeding context limits
        if len(self.conversation_history) > 1:
            prev_messages = self.conversation_history[:-1][-10:]
            messages = prev_messages + messages
        
        # Enhance with memory context if enabled
        memory_context = ""
        if use_memory and (memory_search_query or prompt):
            search_query = memory_search_query or prompt
            memory_results = self.memory.search_all(search_query, limit=3)
            
            if memory_results["conversation"] or memory_results["semantic"]:
                memory_context = "Relevant information from memory:\n"
                
                for i, item in enumerate(memory_results["conversation"]):
                    memory_context += f"[Conversation {i+1}] {item.get('role', 'unknown')}: {item.get('content', '')}\n"
                
                for i, item in enumerate(memory_results["semantic"]):
                    memory_context += f"[Knowledge {i+1}] {item.get('content', '')}\n"
        
        # Combine memory context with system prompt if available
        if memory_context:
            if system_prompt:
                system_prompt = f"{system_prompt}\n\n{memory_context}"
            else:
                system_prompt = memory_context
        
        if use_perplexity and self.perplexity_enabled:
            # Enhance the prompt with Perplexity search results
            search_results = await self._query_perplexity_async(prompt)
            # Add search results as a system message
            if system_prompt:
                system_prompt += f"\n\nAdditional context from web search: {search_results}"
            else:
                system_prompt = f"Additional context from web search: {search_results}"
            logger.debug("Enhanced prompt with Perplexity search results")
        
        # We need to run the synchronous API call in a thread pool since
        # the anthropic Python client doesn't have async support yet
        loop = asyncio.get_running_loop()
        
        try:
            # Run the synchronous API call in a thread pool
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                )
            )
            
            response_content = response.content[0].text
            
            # Add to conversation history and memory
            self.conversation_history.append({"role": "assistant", "content": response_content})
            self.memory.add_conversation_item("assistant", response_content, {
                "model": self.model,
                "system_prompt_used": bool(system_prompt),
                "memory_used": bool(memory_context),
                "web_search_used": use_perplexity and self.perplexity_enabled,
                "in_response_to": message_id,
                "async": True
            })
            
            return {
                "content": response_content,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Error calling Claude API asynchronously: {e}")
            raise
    
    def _query_perplexity(self, query: str) -> str:
        """Query Perplexity API for search results.
        
        Args:
            query: Search query to send to Perplexity
            
        Returns:
            Search results as a string
        """
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not available")
            return ""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "query": query,
                "max_tokens": 250  # Limit response length
            }
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Store the search result in semantic memory
                self.memory.add_semantic_item(
                    content=result.get("answer", ""),
                    metadata={"source": "perplexity", "query": query}
                )
                return result.get("answer", "")
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Error querying Perplexity API: {e}")
            return ""
    
    async def _query_perplexity_async(self, query: str) -> str:
        """Query Perplexity API for search results asynchronously.
        
        Args:
            query: Search query to send to Perplexity
            
        Returns:
            Search results as a string
        """
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not available")
            return ""
        
        try:
            import aiohttp
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "query": query,
                "max_tokens": 250  # Limit response length
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Store the search result in semantic memory
                        self.memory.add_semantic_item(
                            content=result.get("answer", ""),
                            metadata={"source": "perplexity", "query": query, "async": True}
                        )
                        return result.get("answer", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Perplexity API error: {response.status} - {error_text}")
                        return ""
        except Exception as e:
            logger.error(f"Error querying Perplexity API asynchronously: {e}")
            return ""
    
    def setup_github_integration(
        self,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_owner: Optional[str] = None
    ) -> None:
        """Set up GitHub integration.
        
        Args:
            github_token: GitHub personal access token. If not provided, will try to get from
                environment variable GITHUB_TOKEN
            github_repo: GitHub repository name. If not provided, will try to get from
                environment variable GITHUB_REPO
            github_owner: GitHub repository owner. If not provided, will try to get from
                environment variable GITHUB_OWNER
        """
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.github_repo = github_repo or os.environ.get("GITHUB_REPO")
        self.github_owner = github_owner or os.environ.get("GITHUB_OWNER")
        
        if not all([self.github_token, self.github_repo, self.github_owner]):
            logger.warning(
                "GitHub integration not fully configured. "
                "Need token, repo, and owner."
            )
            self.github_enabled = False
            return
        
        self.github_enabled = True
        logger.info(f"GitHub integration enabled for {self.github_owner}/{self.github_repo}")
    
    def create_github_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a GitHub issue.
        
        Args:
            title: Issue title
            body: Issue body
            labels: List of labels to apply to the issue
            
        Returns:
            Response from GitHub API as a dictionary
        """
        if not self.github_enabled:
            raise ValueError("GitHub integration not enabled")
        
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "title": title,
                "body": body
            }
            
            if labels:
                data["labels"] = labels
            
            response = requests.post(
                f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/issues",
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"Created GitHub issue: {result['html_url']}")
                
                # Store in semantic memory
                self.memory.add_semantic_item(
                    content=f"Created GitHub issue: {title}\n\n{body}",
                    metadata={
                        "source": "github", 
                        "type": "issue", 
                        "url": result['html_url'],
                        "issue_number": result['number']
                    }
                )
                
                return result
            else:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise ValueError(f"Failed to create GitHub issue: {response.text}")
        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}")
            raise
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def save_memory(self) -> None:
        """Save all memory."""
        self.memory.save_all()
    
    def add_knowledge(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add knowledge to semantic memory.
        
        Args:
            content: The knowledge content
            metadata: Optional metadata about the knowledge
            
        Returns:
            ID of the added knowledge item
        """
        return self.memory.add_semantic_item(content, metadata)
    
    def search_memory(self, query: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Search all memory types.
        
        Args:
            query: Search query
            limit: Maximum number of results per memory type
            
        Returns:
            Dictionary with search results grouped by memory type
        """
        return self.memory.search_all(query, limit)
    
    def __repr__(self) -> str:
        """Return string representation of the client."""
        return (
            f"EnhancedClaudeClient(model={self.model}, "
            f"github_enabled={self.github_enabled}, "
            f"perplexity_enabled={self.perplexity_enabled})"
        ) 