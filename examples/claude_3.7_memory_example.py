#!/usr/bin/env python3
"""
Example demonstrating Claude 3.7 memory integration in VOT1

This script demonstrates how to use the enhanced ComposioMemoryBridge
with Claude 3.7's capabilities for advanced memory operations.
"""

import os
import json
import asyncio
import time
from dotenv import load_dotenv

from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge

# Load environment variables
load_dotenv()

async def main():
    # Initialize the Composio client with Claude 3.7
    client = ComposioClient(
        model="claude-3-7-sonnet-20240620",  # Claude 3.7 Sonnet
        hybrid_mode=True,
        max_thinking_tokens=120000,
        max_tokens=40000
    )
    
    # Test the connection
    connection_status, message = await client.test_connection()
    if not connection_status:
        print(f"Failed to connect to Composio MCP: {message}")
        return
        
    print(f"Connected to Composio MCP: {message}")
    
    # Initialize the memory bridge
    memory_bridge = ComposioMemoryBridge(
        composio_client=client,
        use_enhanced_memory=True,
        memory_path="memory"
    )
    
    # Example 1: Simple memory integration
    print("\n=== Example 1: Basic Memory Integration ===")
    response1 = await memory_bridge.process_with_memory(
        prompt="What are the key capabilities of Claude 3.7?",
        memory_limit=5,
        memory_retrieval_strategy="semantic",
        thinking=True
    )
    
    # Display the response
    print_response(response1)
    print(f"Memory Context: {json.dumps(response1['memory_context'], indent=2)}")
    print(f"Performance: {json.dumps(response1['memory_context'], indent=2)}")
    
    # Wait a moment between operations
    await asyncio.sleep(2)
    
    # Example 2: Hybrid processing mode
    print("\n=== Example 2: Hybrid Processing Mode ===")
    response2 = await memory_bridge.process_with_hybrid_memory(
        prompt="How does the VOT1 memory system leverage Claude 3.7's capabilities?",
        memory_limit=10,
        memory_retrieval_strategy="hybrid"
    )
    
    # Display the response
    print_response(response2)
    print(f"Performance: {json.dumps(response2['performance'], indent=2)}")
    
    # Wait a moment between operations
    await asyncio.sleep(2)
    
    # Example 3: Advanced memory reflection
    print("\n=== Example 3: Advanced Memory Reflection ===")
    reflection = await memory_bridge.advanced_memory_reflection(
        query="memory systems",
        reflection_depth="deep",
        max_memories=15,
        include_thinking=True
    )
    
    # Display the reflection
    if reflection.get("success", False):
        print(f"Reflection Memory ID: {reflection.get('memory_id')}")
        print(f"Memory Count: {reflection.get('memory_count')}")
        print(f"Memory Types: {json.dumps(reflection.get('memory_types', {}), indent=2)}")
        print(f"Reflection:\n{reflection.get('reflection')}")
    else:
        print(f"Reflection failed: {reflection.get('error')}")
    
    # Close the client session
    await client.close()
    
def print_response(response):
    """Print a nicely formatted response from the memory bridge"""
    if "choices" in response and len(response["choices"]) > 0:
        print("\nResponse:")
        print("-" * 80)
        print(response["choices"][0]["message"]["content"])
        print("-" * 80)
        
        # Print thinking if available
        if "thinking" in response["choices"][0]:
            thinking = response["choices"][0]["thinking"]
            print("\nThinking (excerpt):")
            print("-" * 80)
            if len(thinking) > 1000:
                print(thinking[:1000] + "...[truncated]")
            else:
                print(thinking)
            print("-" * 80)
    else:
        print("No response content available")

if __name__ == "__main__":
    asyncio.run(main()) 