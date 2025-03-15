#!/usr/bin/env python3
"""
Test script for Composio MCP integration with VOT1

This script tests the integration with Composio's Model Control Protocol (MCP)
to ensure proper communication and workflow for the advanced memory system.
"""

import os
import json
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComposioClient:
    """
    Client for interacting with Composio's Model Control Protocol (MCP)
    """
    
    def __init__(self, api_key=None, mcp_url=None):
        # Load API key and URL from environment if not provided
        self.api_key = api_key or os.getenv('COMPOSIO_API_KEY')
        self.mcp_url = mcp_url or os.getenv('COMPOSIO_MCP_URL')
        
        if not self.api_key:
            raise ValueError("Composio API key is required. Set COMPOSIO_API_KEY in .env or pass as argument.")
        
        if not self.mcp_url:
            raise ValueError("Composio MCP URL is required. Set COMPOSIO_MCP_URL in .env or pass as argument.")
        
        logger.info(f"Composio client initialized with URL: {self.mcp_url}")
    
    def test_connection(self):
        """Test the connection to Composio MCP"""
        import requests
        
        try:
            # Simplified test - in production would use actual API endpoints
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Just checking if the endpoint is reachable
            response = requests.get(
                self.mcp_url,
                headers=headers
            )
            
            # Log response status
            logger.info(f"Connection test status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Successfully connected to Composio MCP")
                return True
            else:
                logger.error(f"Failed to connect to Composio MCP: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Composio MCP: {str(e)}")
            return False

    def process_request(self, prompt, system=None, tools=None, temperature=0.7, max_tokens=1024):
        """
        Process a request through Composio MCP
        
        Args:
            prompt: The user message or prompt
            system: Optional system message
            tools: Optional list of tools
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response from the model
        """
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload based on Composio MCP API
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add system message if provided
        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})
            
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            
        try:
            response = requests.post(
                f"{self.mcp_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error from Composio MCP: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Exception calling Composio MCP: {str(e)}")
            return {"error": str(e)}

def main():
    """Main function to test Composio MCP integration"""
    parser = argparse.ArgumentParser(description="Test Composio MCP Integration")
    parser.add_argument("--api-key", type=str, help="Composio API Key (overrides env variable)")
    parser.add_argument("--mcp-url", type=str, help="Composio MCP URL (overrides env variable)")
    parser.add_argument("--prompt", type=str, default="How can the VOT1 advanced memory system be integrated with Composio MCP?", 
                       help="Test prompt to send to Composio MCP")
    
    args = parser.parse_args()
    
    try:
        # Initialize Composio client
        client = ComposioClient(api_key=args.api_key, mcp_url=args.mcp_url)
        
        # Test connection
        if client.test_connection():
            logger.info("Connection test successful")
            
            # Process a test request
            logger.info(f"Sending test prompt: {args.prompt}")
            response = client.process_request(
                prompt=args.prompt,
                system="You are a helpful AI assistant with expertise in advanced memory systems for AGI."
            )
            
            # Print response
            logger.info("Response received:")
            print(json.dumps(response, indent=2))
        else:
            logger.error("Connection test failed")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
