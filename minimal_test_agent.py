#!/usr/bin/env python3
"""
Minimal test version of the Enhanced Research Agent.
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MinimalTestAgent")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("dotenv module not found, using existing environment variables")
    # Manually load .env file
    try:
        with open(".env", "r") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        logger.info("Environment variables manually loaded from .env file")
    except Exception as e:
        logger.warning(f"Failed to manually load .env file: {e}")

try:
    import anthropic
    anthropic_installed = True
except ImportError:
    logger.error("Anthropic not installed. Install with: pip install anthropic")
    anthropic_installed = False

class MinimalTestAgent:
    """
    Minimal test version of the Enhanced Research Agent.
    """
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        output_dir: str = "output/test_minimal"
    ):
        """Initialize the Minimal Test Agent."""
        # Store configuration
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.output_dir = output_dir
        
        logger.info(f"API key available: {bool(self.anthropic_api_key)}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a session ID
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Initialize clients
        self.claude_client = None
        
        # Initialize state
        self.initialized = False
        
        # Model configuration
        self.claude_model = "claude-3-sonnet-20240229"
        
        # Initialize agent
        self._init_agent()
    
    def _init_agent(self):
        """Initialize agent components."""
        try:
            # Initialize Claude client
            if anthropic_installed and self.anthropic_api_key:
                self.claude_client = anthropic.Anthropic(
                    api_key=self.anthropic_api_key
                )
                logger.info("Claude client initialized")
                self.initialized = True
            else:
                logger.error("Claude client initialization failed")
                if not anthropic_installed:
                    logger.error("Anthropic module not installed")
                if not self.anthropic_api_key:
                    logger.error("ANTHROPIC_API_KEY not found in environment variables")
                self.initialized = False
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error("Agent initialization failed")
            self.initialized = False
            raise
    
    async def test_claude_connection(self) -> Dict[str, Any]:
        """Test connection to Claude API."""
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Hello, please respond with 'Connection successful!'"}
                ]
            )
            
            return {
                "success": True,
                "response": response.content[0].text,
                "model": self.claude_model
            }
            
        except Exception as e:
            logger.error(f"Error testing Claude connection: {e}")
            return {"error": str(e)}
    
    async def run_test(self) -> Dict[str, Any]:
        """Run a simple test of the agent."""
        logger.info("Running minimal test...")
        
        if not self.initialized:
            return {"error": "Agent not initialized"}
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        # Test Claude connection
        claude_test = await self.test_claude_connection()
        results["claude_test"] = claude_test
        
        # Save results
        output_file = os.path.join(self.output_dir, f"minimal_test_{self.session_id}.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Test results saved to {output_file}")
        return results

async def main():
    """Run the minimal test agent."""
    # Get the API key directly from .env content
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("No ANTHROPIC_API_KEY found in environment variables")
        # Try to get it directly from the .env file
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip("'\"")
                        break
            if api_key:
                logger.info("API key extracted directly from .env file")
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
    
    agent = MinimalTestAgent(anthropic_api_key=api_key)
    result = await agent.run_test()
    
    if "error" in result:
        logger.error(f"Test failed: {result['error']}")
        return False
    
    logger.info("Test completed successfully")
    return True

if __name__ == "__main__":
    asyncio.run(main()) 