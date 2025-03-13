#!/usr/bin/env python3
"""
VOT1 Advanced AGI Agent Example

This example demonstrates how to create an advanced agent using VOT1 with 
multiple capabilities including OWL reasoning, web search, memory management,
and the Model Control Protocol (MCP).

Copyright 2025 VillageOfThousands.io
"""

import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

# Ensure the parent directory is in the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import VOT1 components
from vot1.client import EnhancedClaudeClient
from vot1.memory import MemoryManager
from vot1.vot_mcp import VotModelControlProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("vot1_agent.log")
    ]
)
logger = logging.getLogger("vot1_agent")

def setup_environment() -> Dict[str, str]:
    """Set up the environment by loading environment variables"""
    # Load from .env file if it exists
    load_dotenv()
    
    # Required environment variables
    required_vars = ["ANTHROPIC_API_KEY"]
    
    env_vars = {}
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            logger.error(f"Missing required environment variable: {var}")
            sys.exit(1)
        env_vars[var] = value
    
    # Optional environment variables with defaults
    env_vars["PERPLEXITY_API_KEY"] = os.environ.get("PERPLEXITY_API_KEY", "")
    env_vars["VOT1_MEMORY_PATH"] = os.environ.get("VOT1_MEMORY_PATH", "memory")
    env_vars["VOT1_LOGGING_LEVEL"] = os.environ.get("VOT1_LOGGING_LEVEL", "INFO")
    
    # Set logging level from environment
    if env_vars["VOT1_LOGGING_LEVEL"]:
        numeric_level = getattr(logging, env_vars["VOT1_LOGGING_LEVEL"].upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)
    
    return env_vars

def setup_memory_manager(memory_path: str) -> MemoryManager:
    """Set up the memory manager"""
    logger.info(f"Setting up memory manager with path: {memory_path}")
    
    # Create memory directory if it doesn't exist
    memory_dir = Path(memory_path)
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize memory manager
    memory_manager = MemoryManager(
        memory_path=memory_path,
        use_vector_search=True
    )
    
    logger.info(f"Memory manager initialized with {memory_manager.count_all_memories()} memories")
    return memory_manager

def setup_claude_client(
    api_key: str, 
    memory_manager: MemoryManager, 
    perplexity_api_key: Optional[str] = None,
    model: str = "claude-3-opus-20240229"
) -> EnhancedClaudeClient:
    """Set up the Enhanced Claude Client with all capabilities"""
    logger.info(f"Setting up Enhanced Claude Client with model: {model}")
    
    # Initialize the MCP handler
    mcp_handler = VotModelControlProtocol(
        version="2.4.0",
        supported_providers=["anthropic", "perplexity"],
        execution_mode="hybrid"
    )
    
    # Initialize the client with all capabilities
    client = EnhancedClaudeClient(
        api_key=api_key,
        memory_manager=memory_manager,
        model=model,
        max_tokens=4000,
        temperature=0.7,
        mcp_handler=mcp_handler
    )
    
    # Add web search capability if Perplexity API key is provided
    if perplexity_api_key:
        logger.info("Adding web search capability")
        client.add_web_search(api_key=perplexity_api_key)
    
    # Add OWL reasoning capability
    logger.info("Adding OWL reasoning capability")
    client.add_owl_reasoning()
    
    # Register tools provided by the client
    for tool_name, tool_spec in client.get_registered_tools().items():
        logger.info(f"Registered tool: {tool_name}")
    
    return client

def print_system_info(client: EnhancedClaudeClient, memory_manager: MemoryManager):
    """Print system information"""
    print("\n" + "=" * 50)
    print(" VOT1 Advanced AGI Agent ".center(50, "="))
    print("=" * 50 + "\n")
    
    print(f"Model: {client.model}")
    print(f"Memory count: {memory_manager.count_all_memories()} items")
    print(f"Web search: {'Enabled' if client.has_web_search else 'Disabled'}")
    print(f"OWL reasoning: {'Enabled' if client.has_owl_reasoning else 'Disabled'}")
    print(f"MCP version: {client.mcp_handler.version if client.mcp_handler else 'Not available'}")
    
    tools = client.get_registered_tools()
    print(f"Available tools: {len(tools)}")
    
    print("\n" + "=" * 50 + "\n")

def run_interactive_session(client: EnhancedClaudeClient):
    """Run an interactive session with the agent"""
    print("\nVOT1 Advanced AGI Agent Interactive Session")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'clear' to clear the conversation context\n")
    
    conversation_id = f"session_{int(time.time())}"
    turn_count = 0
    conversation_history = []
    
    # Example system message to define agent behavior
    system_message = """
    You are VOT1, an advanced AGI assistant with multiple capabilities including web search,
    memory management, and reasoning. You have access to the following tools:
    
    1. Web search - You can search the web for current information
    2. Memory - You can store and retrieve information from your memory
    3. OWL reasoning - You can use formal reasoning to analyze problems
    
    You should provide helpful, accurate, and ethical responses. When information is not
    available in your training data, use web search to find up-to-date information.
    Use memory to maintain context and recall important details from earlier in the conversation.
    Use OWL reasoning for complex logical problems that require formal analysis.
    
    You should be concise but comprehensive in your responses, focusing on providing
    accurate information while maintaining a conversational tone.
    """
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit commands
        if user_input.lower() in ["exit", "quit"]:
            print("\nEnding session. Goodbye!")
            break
        
        # Check for clear command
        if user_input.lower() == "clear":
            conversation_history = []
            turn_count = 0
            print("\nConversation context cleared.")
            continue
        
        # Start timing response
        start_time = time.time()
        
        # Increment turn counter
        turn_count += 1
        
        try:
            # Add user message to conversation history
            conversation_history.append({"role": "user", "content": user_input})
            
            # Add to memory
            client.memory_manager.add_conversation_memory(
                content=user_input,
                metadata={
                    "conversation_id": conversation_id,
                    "turn": turn_count,
                    "role": "user"
                }
            )
            
            # Get response from model
            response = client.generate_with_context(
                system=system_message,
                conversation_history=conversation_history
            )
            
            # Add assistant response to conversation history
            conversation_history.append({"role": "assistant", "content": response})
            
            # Add to memory
            client.memory_manager.add_conversation_memory(
                content=response,
                metadata={
                    "conversation_id": conversation_id,
                    "turn": turn_count,
                    "role": "assistant"
                }
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Print response
            print(f"\nVOT1 ({response_time:.2f}s): {response}")
            
        except Exception as e:
            logger.exception(f"Error in conversation: {e}")
            print(f"\nError: {str(e)}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="VOT1 Advanced AGI Agent Example")
    parser.add_argument(
        "--model", 
        type=str, 
        default="claude-3-opus-20240229",
        help="Claude model to use"
    )
    parser.add_argument(
        "--memory-path", 
        type=str, 
        default="memory",
        help="Path to memory directory"
    )
    parser.add_argument(
        "--demo-mode", 
        action="store_true",
        help="Run in demo mode with predefined examples"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug logging"
    )
    return parser.parse_args()

def run_demo_mode(client: EnhancedClaudeClient):
    """Run a demo with predefined examples"""
    print("\nRunning VOT1 AGI Agent in demo mode")
    
    demo_queries = [
        "What are the latest developments in artificial intelligence?",
        "Can you explain the concept of a Model Control Protocol?",
        "Who is the current CEO of OpenAI and what have they been working on recently?",
        "Using OWL reasoning, can you analyze whether all mammals have hearts?",
        "What is the relationship between climate change and biodiversity loss?",
        "Compare and contrast the concepts of AGI, superintelligence, and consciousness."
    ]
    
    system_message = """
    You are VOT1, an advanced AGI assistant with multiple capabilities including web search,
    memory management, and reasoning. Provide concise, accurate and well-structured answers.
    """
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n\nDemo Query {i}/{len(demo_queries)}:")
        print(f"Query: {query}")
        
        start_time = time.time()
        
        try:
            response = client.generate_with_context(
                system=system_message,
                conversation_history=[{"role": "user", "content": query}]
            )
            
            response_time = time.time() - start_time
            
            print(f"\nResponse ({response_time:.2f}s):")
            print(response)
            print("\n" + "-" * 80)
            
        except Exception as e:
            logger.exception(f"Error in demo: {e}")
            print(f"Error: {str(e)}")
        
        # Small delay between queries
        time.sleep(2)

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Setup environment
    env_vars = setup_environment()
    
    # Setup memory manager
    memory_manager = setup_memory_manager(args.memory_path)
    
    # Setup Claude client
    client = setup_claude_client(
        api_key=env_vars["ANTHROPIC_API_KEY"],
        memory_manager=memory_manager,
        perplexity_api_key=env_vars.get("PERPLEXITY_API_KEY"),
        model=args.model
    )
    
    # Print system info
    print_system_info(client, memory_manager)
    
    try:
        # Run in demo or interactive mode
        if args.demo_mode:
            run_demo_mode(client)
        else:
            run_interactive_session(client)
    except KeyboardInterrupt:
        print("\nSession terminated by user.")
    except Exception as e:
        logger.exception(f"Error in main: {e}")
        print(f"Error: {str(e)}")
    
    print("\nShutting down VOT1 AGI Agent...")

if __name__ == "__main__":
    main() 