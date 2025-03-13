"""
Perplexity AI Search Integration for VOT1

This module provides integration with Perplexity AI's search capabilities
through the Composio MCP interface.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

class PerplexitySearch:
    """
    Client for interacting with Perplexity AI search through Composio MCP.
    """
    
    def __init__(self, mcp_url: Optional[str] = None):
        """
        Initialize the Perplexity Search client.
        
        Args:
            mcp_url: Optional URL for the Perplexity MCP endpoint.
                     If not provided, will use environment variable or config file.
        """
        self.mcp_url = mcp_url or self._get_mcp_url()
        self.api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        
        # Validate configuration
        if not self.mcp_url:
            logger.warning("Perplexity MCP URL not configured. Search functionality will be limited.")
    
    def _get_mcp_url(self) -> str:
        """
        Get the Perplexity MCP URL from environment variables or config file.
        
        Returns:
            The MCP URL as a string.
        """
        # First check environment variable
        mcp_url = os.environ.get("PERPLEXITY_MCP_URL")
        if mcp_url:
            return mcp_url
            
        # Then check config file
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../../config/mcp.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("mcpServers", {}).get("PERPLEXITY", {}).get("url", "")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return ""
    
    def search(self, query: str, focus: Optional[str] = None, 
               max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a search query using Perplexity AI.
        
        Args:
            query: The search query string
            focus: Optional focus area for the search (e.g., "academic", "news", "general")
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot perform search: Perplexity MCP URL not configured")
            return {"error": "Perplexity MCP URL not configured", "results": []}
            
        try:
            # Prepare the request payload
            payload = {
                "query": query,
                "max_results": max_results
            }
            
            if focus:
                payload["focus"] = focus
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/search",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error performing Perplexity search: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": []
            }
    
    def answer_question(self, question: str, include_sources: bool = True) -> Dict[str, Any]:
        """
        Get a comprehensive answer to a question using Perplexity AI.
        
        Args:
            question: The question to answer
            include_sources: Whether to include sources in the response
            
        Returns:
            Dictionary containing the answer and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot answer question: Perplexity MCP URL not configured")
            return {"error": "Perplexity MCP URL not configured", "answer": ""}
            
        try:
            # Prepare the request payload
            payload = {
                "question": question,
                "include_sources": include_sources
            }
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/answer",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting answer from Perplexity: {e}")
            return {
                "error": str(e),
                "question": question,
                "answer": ""
            }
    
    def search_and_summarize(self, topic: str, depth: str = "medium") -> Dict[str, Any]:
        """
        Search for information on a topic and provide a summarized report.
        
        Args:
            topic: The topic to research
            depth: Depth of research - "brief", "medium", or "comprehensive"
            
        Returns:
            Dictionary containing the summary and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot perform search and summarize: Perplexity MCP URL not configured")
            return {"error": "Perplexity MCP URL not configured", "summary": ""}
            
        try:
            # Prepare the request payload
            payload = {
                "topic": topic,
                "depth": depth
            }
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/summarize",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in search and summarize: {e}")
            return {
                "error": str(e),
                "topic": topic,
                "summary": ""
            }

    def _load_mcp_config(self):
        """Load MCP configuration from file."""
        try:
            # Try multiple possible locations for the config file
            possible_paths = [
                os.path.join(os.getcwd(), "src", "vot1", "config", "mcp.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "mcp.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "config", "mcp.json"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "config", "mcp.json")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logger.info(f"Loading MCP config from {path}")
                    with open(path, "r") as f:
                        return json.load(f)
            
            # If no config file found, create a default one
            config_dir = os.path.join(os.getcwd(), "src", "vot1", "config")
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, "mcp.json")
            default_config = {
                "providers": {
                    "github": {
                        "url": "https://mcp.composio.dev/github/victorious-damaged-branch-0ojHhf"
                    },
                    "perplexity": {
                        "url": "https://mcp.composio.dev/perplexity/victorious-damaged-branch-0ojHhf"
                    }
                }
            }
            
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default MCP config at {config_path}")
            return default_config
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    perplexity = PerplexitySearch()
    
    # Example search
    results = perplexity.search("latest advancements in quantum computing")
    print(json.dumps(results, indent=2))
    
    # Example question answering
    answer = perplexity.answer_question("What are the environmental impacts of electric vehicles?")
    print(json.dumps(answer, indent=2)) 