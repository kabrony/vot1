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
    ) -> None:
        """Initialize the EnhancedClaudeClient.
        
        Args:
            api_key: API key for Anthropic. If not provided, will try to get from
                environment variable ANTHROPIC_API_KEY
            model: Claude model to use
            max_tokens: Maximum number of tokens to generate
            perplexity_api_key: API key for Perplexity. If not provided, will try to get from
                environment variable PERPLEXITY_API_KEY
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
        
        logger.info(f"Initialized EnhancedClaudeClient with model {model}")
    
    def send_message(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        stream: bool = False,
        use_perplexity: bool = False,
        temperature: float = 0.7,
    ) -> Union[str, Dict[str, Any]]:
        """Send a message to Claude.
        
        Args:
            prompt: The user's input message
            system_prompt: Optional system prompt to guide Claude's behavior
            stream: Whether to stream the response
            use_perplexity: Whether to use Perplexity for web search augmentation
            temperature: Controls randomness of the output (0.0 to 1.0)
            
        Returns:
            Response from Claude API as a string or dictionary
        """
        # Log the request
        logger.debug(f"Sending message to Claude: {prompt[:50]}...")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add previous messages from conversation history for context
        # Limited to the last 10 messages to avoid exceeding context limits
        if len(self.conversation_history) > 1:
            prev_messages = self.conversation_history[:-1][-10:]
            messages = prev_messages + messages
        
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
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_content})
            
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
    ) -> Dict[str, Union[str, float]]:
        """Send a message to Claude asynchronously.
        
        Args:
            prompt: The user's input message
            system_prompt: Optional system prompt to guide Claude's behavior
            use_perplexity: Whether to use Perplexity for web search augmentation
            temperature: Controls randomness of the output (0.0 to 1.0)
            
        Returns:
            Response from Claude API as a dictionary
        """
        # Log the request
        logger.debug(f"Sending async message to Claude: {prompt[:50]}...")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        
        # Prepare messages
        messages = [{"role": "user", "content": prompt}]
        
        # Add previous messages from conversation history for context
        # Limited to the last 10 messages to avoid exceeding context limits
        if len(self.conversation_history) > 1:
            prev_messages = self.conversation_history[:-1][-10:]
            messages = prev_messages + messages
        
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
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": response_content})
            
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
            query: The search query
            
        Returns:
            Search results as a string
        """
        if not self.perplexity_enabled:
            raise ValueError("Perplexity integration is not enabled. Provide a Perplexity API key.")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "query": query,
                "max_results": 5,
                "include_answer": True,
                "include_sources": True
            }
            
            response = requests.post(
                "https://api.perplexity.ai/search",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract answer and sources
                answer = result.get("answer", "No answer found")
                sources = result.get("sources", [])
                
                # Format sources
                sources_text = ""
                for i, source in enumerate(sources, 1):
                    sources_text += f"{i}. {source.get('title')}: {source.get('url')}\n"
                
                return f"{answer}\n\nSources:\n{sources_text}"
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return "Error querying Perplexity API"
        
        except Exception as e:
            logger.error(f"Error in Perplexity search: {e}")
            return f"Error querying Perplexity: {str(e)}"
    
    async def _query_perplexity_async(self, query: str) -> str:
        """Query Perplexity API for search results asynchronously.
        
        Args:
            query: The search query
            
        Returns:
            Search results as a string
        """
        if not self.perplexity_enabled:
            raise ValueError("Perplexity integration is not enabled. Provide a Perplexity API key.")
        
        # Run synchronous method in executor since we don't have async HTTP client set up
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._query_perplexity, query)
    
    def setup_github_integration(
        self,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_owner: Optional[str] = None
    ) -> None:
        """Set up GitHub integration.
        
        Args:
            github_token: GitHub token for authentication. If not provided, will try to 
                get from environment variable GITHUB_TOKEN
            github_repo: GitHub repository name
            github_owner: GitHub repository owner
        """
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError(
                "GitHub token must be provided either as an argument or "
                "as the GITHUB_TOKEN environment variable"
            )
        
        self.github_repo = github_repo
        self.github_owner = github_owner
        self.github_enabled = True
        
        logger.info(f"GitHub integration enabled for {github_owner}/{github_repo}")
    
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
            Dictionary with issue details
        """
        if not self.github_enabled:
            raise ValueError("GitHub integration is not enabled. Call setup_github_integration first.")
        
        if not self.github_repo or not self.github_owner:
            raise ValueError("GitHub repository and owner must be set")
        
        # TODO: Implement actual GitHub API call
        # For now, just return a placeholder
        logger.info(f"Creating GitHub issue: {title}")
        
        return {
            "title": title,
            "body": body,
            "url": f"https://github.com/{self.github_owner}/{self.github_repo}/issues/1",
            "number": 1,
            "created_at": datetime.now().isoformat(),
            "labels": labels or []
        }
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.debug("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history.copy()
    
    def __repr__(self) -> str:
        """Return string representation of the client."""
        return f"EnhancedClaudeClient(model={self.model}, max_tokens={self.max_tokens})" 