#!/usr/bin/env python3
"""
Example usage of the VOT1Client with Claude 3.7 Sonnet.

This script demonstrates how to use the VOT1Client to interact with
Claude 3.7 Sonnet, including both synchronous and asynchronous calls, GitHub integration,
and Perplexity search enhancement.
"""

import os
import sys
import asyncio
from pathlib import Path
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the VOT1Client
from src.vot1 import VOT1Client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

async def main():
    """Main function demonstrating the capabilities of VOT1Client."""
    try:
        # Initialize the client
        client = VOT1Client(
            # API key will be loaded from ANTHROPIC_API_KEY environment variable
            # Perplexity API key will be loaded from PERPLEXITY_API_KEY environment variable if available
        )
        
        logger.info(f"Initialized client with model: {client.model}")
        
        # Example 1: Simple synchronous call
        prompt = "What are the latest advancements in AI in 2024?"
        logger.info(f"Sending synchronous prompt: {prompt}")
        response = client.send_message(prompt)
        if isinstance(response, dict):
            logger.info(f"Response: {response['content'][:100]}...")
            logger.info(f"Token usage: {response['usage']}")
        else:
            logger.info(f"Response: {response[:100]}...")
        
        # Example 2: Synchronous call with system prompt
        system_prompt = "You are a technical expert who specializes in explaining complex concepts clearly and concisely."
        prompt = "Explain how large language models work in 3-5 sentences."
        logger.info(f"Sending synchronous prompt with system prompt: {prompt}")
        response = client.send_message(
            prompt=prompt,
            system_prompt=system_prompt,
        )
        if isinstance(response, dict):
            logger.info(f"Response: {response['content'][:100]}...")
        else:
            logger.info(f"Response: {response[:100]}...")
        
        # Example 3: Asynchronous call
        prompt = "What are the major benefits of asynchronous programming in Python?"
        logger.info(f"Sending asynchronous prompt: {prompt}")
        response = await client.send_message_async(prompt)
        logger.info(f"Async response: {response['content'][:100]}...")
        logger.info(f"Token usage: {response['usage']}")
        
        # Example 4: Using Perplexity for web search (if enabled)
        if client.perplexity_enabled:
            prompt = "What were the major breakthroughs in quantum computing this year?"
            logger.info(f"Sending prompt with Perplexity enhancement: {prompt}")
            response = client.send_message(prompt, use_perplexity=True)
            if isinstance(response, dict):
                logger.info(f"Response with Perplexity: {response['content'][:100]}...")
            else:
                logger.info(f"Response with Perplexity: {response[:100]}...")
        else:
            logger.info("Perplexity integration not enabled, skipping example 4")
        
        # Example 5: Set up GitHub integration (if credentials available)
        github_token = os.environ.get("GITHUB_TOKEN")
        github_owner = os.environ.get("GITHUB_OWNER")
        github_repo = os.environ.get("GITHUB_REPOSITORY")
        
        if github_token and github_owner and github_repo:
            try:
                client.setup_github_integration(
                    github_token=github_token,
                    github_owner=github_owner,
                    github_repo=github_repo
                )
                
                logger.info("GitHub integration enabled, creating test issue")
                issue_response = client.create_github_issue(
                    title="Test Issue from VOT1Client",
                    body="This is a test issue created by the VOT1Client example script.",
                    labels=["test", "documentation"]
                )
                logger.info(f"Created issue: {issue_response['url']}")
            except Exception as e:
                logger.error(f"Error setting up GitHub integration: {e}")
        else:
            logger.info("GitHub credentials not found, skipping example 5")
        
        # Show conversation history
        logger.info("Conversation history:")
        for i, message in enumerate(client.get_conversation_history()):
            logger.info(f"  [{i}] {message['role']}: {message['content'][:50]}...")
    
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main()) 