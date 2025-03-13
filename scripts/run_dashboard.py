#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script launches the VOT1 dashboard.
"""

import argparse
import logging
import os
import sys

# Add the src directory to the module search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the VOT1 Dashboard")
    
    parser.add_argument("--host", 
                        default="0.0.0.0", 
                        help="Host to run the dashboard on (default: 0.0.0.0)")
    
    parser.add_argument("--port", 
                        type=int, 
                        default=5000, 
                        help="Port to run the dashboard on (default: 5000)")
    
    parser.add_argument("--debug", 
                        action="store_true", 
                        help="Run in debug mode")
    
    parser.add_argument("--memory-path", 
                        default=None, 
                        help="Path to memory storage directory")
    
    parser.add_argument("--no-memory", 
                        action="store_true", 
                        help="Disable memory management")
    
    parser.add_argument("--api-key", 
                        default=None, 
                        help="API key for Claude API")
    
    parser.add_argument("--enable-mcp-hybrid", 
                        action="store_true", 
                        help="Enable MCP hybrid automation for model selection")
    
    parser.add_argument("--primary-model", 
                        default="claude-3-7-sonnet-20240620", 
                        help="Primary model for MCP hybrid automation (default: claude-3-7-sonnet-20240620)")
    
    parser.add_argument("--secondary-model", 
                        default="claude-3-5-sonnet-20240620", 
                        help="Secondary model for MCP hybrid automation (default: claude-3-5-sonnet-20240620)")
    
    parser.add_argument("--extended-thinking", 
                        action="store_true", 
                        help="Enable extended thinking mode for MCP hybrid automation")
    
    parser.add_argument("--max-thinking-tokens", 
                        type=int, 
                        default=8000, 
                        help="Maximum tokens for extended thinking in MCP hybrid automation (default: 8000)")
    
    parser.add_argument("--enable-streaming", 
                        action="store_true", 
                        help="Enable streaming responses for MCP hybrid automation")
    
    return parser.parse_args()

def main():
    """Main entry point for running the dashboard."""
    args = parse_args()
    
    try:
        from vot1.dashboard import create_app
        from vot1.client import EnhancedClaudeClient
        
        # Set up API key from environment variable or command-line argument
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("No API key provided. Please set the ANTHROPIC_API_KEY environment variable or use --api-key")
            sys.exit(1)
        
        # Initialize the client
        client = EnhancedClaudeClient(api_key=api_key)
        
        # Initialize MCP hybrid automation options
        mcp_hybrid_options = {
            "enabled": args.enable_mcp_hybrid,
            "primary_model": args.primary_model,
            "secondary_model": args.secondary_model,
            "use_extended_thinking": args.extended_thinking,
            "max_thinking_tokens": args.max_thinking_tokens,
            "enable_streaming": args.enable_streaming
        }
        
        # Create and run the app
        app = create_app(
            client=client,
            memory_path=args.memory_path,
            no_memory=args.no_memory,
            mcp_hybrid_options=mcp_hybrid_options
        )
        
        app.run(host=args.host, port=args.port, debug=args.debug)
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 