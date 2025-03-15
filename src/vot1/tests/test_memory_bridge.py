#!/usr/bin/env python3
"""
Test script for ComposioMemoryBridge

This script demonstrates how to use the ComposioMemoryBridge to integrate
the VOT1 memory system with Composio MCP using Claude 3.7.
"""

import os
import sys
import asyncio
import logging
import argparse
from dotenv import load_dotenv

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.composio.enhanced_memory import EnhancedMemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_memory_bridge(api_key, mcp_url, memory_path="memory", use_enhanced=True):
    """
    Test the ComposioMemoryBridge functionality
    
    Args:
        api_key: Composio API key
        mcp_url: Composio MCP URL
        memory_path: Path to memory storage
        use_enhanced: Whether to use the enhanced memory manager
    """
    logger.info("Initializing Composio client and memory bridge")
    
    # Initialize Composio client
    client = ComposioClient(
        api_key=api_key,
        mcp_url=mcp_url,
        default_model="claude-3-7-sonnet"
    )
    
    # Test connection
    await client.test_connection()
    
    # Initialize memory manager and bridge
    if use_enhanced:
        memory_manager = EnhancedMemoryManager(memory_path=memory_path)
        logger.info("Using enhanced memory manager")
    else:
        from vot1.memory import MemoryManager
        memory_manager = MemoryManager(memory_path=memory_path)
        logger.info("Using standard memory manager")
    
    # Initialize memory bridge
    memory_bridge = ComposioMemoryBridge(
        memory_manager=memory_manager,
        composio_client=client,
        use_enhanced_memory=use_enhanced,
        memory_path=memory_path
    )
    
    # Test 1: Simple request with memory storage
    logger.info("Running Test 1: Basic memory storage")
    response = await memory_bridge.process_with_memory(
        prompt="What are the key advantages of graph-based memory for AI systems?",
        system="You are an expert on AI memory systems. Provide clear, concise information.",
        store_response=True,
        thinking=True
    )
    logger.info(f"Test 1 Response ID: {response.get('id', 'unknown')}")
    
    # Test 2: Request with memory retrieval from previous response
    logger.info("Running Test 2: Memory retrieval and context integration")
    response2 = await memory_bridge.process_with_memory(
        prompt="Expand on how these memory advantages could help in AGI development.",
        query="graph-based memory AGI advantages",
        memory_limit=3,
        store_response=True,
        thinking=True
    )
    logger.info(f"Test 2 Response ID: {response2.get('id', 'unknown')}")
    
    # Test 3: Memory consolidation
    logger.info("Running Test 3: Memory consolidation")
    consolidated = await memory_bridge.consolidate_memories(
        topic="graph-based memory and AGI",
        max_memories=5
    )
    
    if "error" in consolidated:
        logger.error(f"Consolidation error: {consolidated['error']}")
    else:
        logger.info("Memory consolidation successful")
        logger.info(f"Themes identified: {', '.join(consolidated.get('themes', []))}")
        logger.info(f"Key insights: {consolidated.get('key_insights', [])}")
        
    # Test 4: Create a plan with memory context
    logger.info("Running Test 4: Planning with memory")
    plan_response = await memory_bridge.plan_with_memory(
        goal="Design an AI system with advanced episodic and semantic memory",
        context="The system should be able to learn from past experiences and improve over time."
    )
    
    logger.info("Memory bridge testing completed successfully")
    
    return {
        "basic_response": response,
        "context_response": response2,
        "consolidated": consolidated,
        "plan": plan_response
    }

def main():
    parser = argparse.ArgumentParser(description="Test the Composio Memory Bridge")
    parser.add_argument("--api-key", help="Composio API key (or set COMPOSIO_API_KEY env var)")
    parser.add_argument("--mcp-url", help="Composio MCP URL (or set COMPOSIO_MCP_URL env var)")
    parser.add_argument("--memory-path", default="memory", help="Path to memory storage")
    parser.add_argument("--standard-memory", action="store_true", help="Use standard memory manager instead of enhanced")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    api_key = args.api_key or os.getenv("COMPOSIO_API_KEY")
    mcp_url = args.mcp_url or os.getenv("COMPOSIO_MCP_URL")
    
    if not api_key:
        logger.error("No Composio API key provided. Set --api-key or COMPOSIO_API_KEY env var.")
        sys.exit(1)
        
    if not mcp_url:
        logger.error("No Composio MCP URL provided. Set --mcp-url or COMPOSIO_MCP_URL env var.")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_memory_bridge(
        api_key=api_key,
        mcp_url=mcp_url,
        memory_path=args.memory_path,
        use_enhanced=not args.standard_memory
    ))

if __name__ == "__main__":
    main() 