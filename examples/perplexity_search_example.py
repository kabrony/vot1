#!/usr/bin/env python3
"""
VOT1 Client with Perplexity Integration - Example Usage

This example demonstrates how to use the VOT1 client with Perplexity integration
to perform web searches and generate responses that incorporate the latest information.
"""

import os
import sys
import logging
from datetime import datetime
import json
import uuid

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.enhanced_client import VOT1Client
from src.vot1.memory import MemoryManager, VectorStore

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Check for API keys
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
    
    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    if not perplexity_api_key:
        logger.warning("PERPLEXITY_API_KEY environment variable not set. Web search will be disabled.")
    
    # Initialize memory manager with a vector store
    vector_store = VectorStore(storage_path="memory/vector_store.db")
    memory_manager = MemoryManager(vector_store=vector_store)
    
    # Initialize the VOT1 client
    vot1_client = VOT1Client(
        anthropic_api_key=anthropic_api_key,
        perplexity_api_key=perplexity_api_key,
        memory_manager=memory_manager
    )
    
    # Create a conversation ID for this session
    conversation_id = str(uuid.uuid4())
    
    print("\n" + "="*80)
    print("VOT1 Client with Perplexity Integration - Example Usage")
    print("="*80 + "\n")
    
    # Example 1: Direct web search
    print("\n--- Example 1: Direct Web Search ---\n")
    search_query = "What are the latest developments in AI language models?"
    print(f"Search Query: {search_query}")
    
    search_result = vot1_client.search_web(search_query)
    if "error" in search_result:
        print(f"Error: {search_result['error']}")
    else:
        print(f"\nSearch Results:\n{search_result.get('answer', 'No answer found')}")
        
        # Print sources if available
        if "links" in search_result and search_result["links"]:
            print("\nSources:")
            for link in search_result["links"]:
                print(f"- {link.get('title', 'Unnamed Source')}: {link.get('url', '')}")
    
    # Example 2: Generate response with auto web search
    print("\n\n--- Example 2: Generate Response with Auto Web Search ---\n")
    prompt = "What are the most recent developments in quantum computing and when did they happen?"
    print(f"User Prompt: {prompt}")
    
    response = vot1_client.generate_response(
        prompt=prompt,
        conversation_id=conversation_id,
        use_web_search=True
    )
    
    print(f"\nResponse:\n{response['content']}")
    print(f"\nWeb Search Used: {response.get('web_search_used', False)}")
    
    # Example 3: Generate response with memory and web search
    print("\n\n--- Example 3: Generate Response with Memory and Web Search ---\n")
    
    # First, add some knowledge to memory
    vot1_client.add_knowledge(
        content="The user is interested in space exploration and new technologies.",
        metadata={"source": "user_profile", "importance": "high"}
    )
    
    prompt = "What are the most exciting recent developments in space exploration?"
    print(f"User Prompt: {prompt}")
    
    response = vot1_client.generate_response(
        prompt=prompt,
        conversation_id=conversation_id,
        use_memory=True,
        use_web_search=True
    )
    
    print(f"\nResponse:\n{response['content']}")
    print(f"\nWeb Search Used: {response.get('web_search_used', False)}")
    
    # Example 4: Follow-up question (testing memory)
    print("\n\n--- Example 4: Follow-up Question (Testing Memory) ---\n")
    prompt = "Can you tell me more about the technical challenges involved in these developments?"
    print(f"User Prompt: {prompt}")
    
    response = vot1_client.generate_response(
        prompt=prompt,
        conversation_id=conversation_id,
        use_memory=True,
        use_web_search=True
    )
    
    print(f"\nResponse:\n{response['content']}")
    print(f"\nWeb Search Used: {response.get('web_search_used', False)}")
    
    print("\n" + "="*80)
    print("Example completed successfully!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main() 