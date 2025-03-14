#!/usr/bin/env python3
"""
Local MCP Bridge CLI

This module provides a command-line interface for running the Local MCP Bridge.
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .bridge import LocalMCPBridge
from .server import LocalMCPServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the Local MCP Bridge")
    
    # Server configuration
    server_group = parser.add_argument_group('Server Configuration')
    server_group.add_argument("--host", default="localhost", help="Host to bind to")
    server_group.add_argument("--port", type=int, default=5678, help="Port to bind to")
    server_group.add_argument("--debug", action="store_true", help="Run in debug mode")
    server_group.add_argument("--find-port", action="store_true", help="Find an available port if the specified port is in use")
    
    # MCP configuration
    mcp_group = parser.add_argument_group('MCP Configuration')
    mcp_group.add_argument("--config", help="Path to MCP configuration file")
    mcp_group.add_argument("--no-cache", action="store_true", help="Disable response caching")
    
    # Service-specific configurations
    service_group = parser.add_argument_group('Service API Keys')
    service_group.add_argument("--github-token", help="GitHub API token")
    service_group.add_argument("--perplexity-key", help="Perplexity API key")
    service_group.add_argument("--firecrawl-key", help="Firecrawl API key")
    service_group.add_argument("--figma-token", help="Figma access token")
    service_group.add_argument("--composio-key", help="Composio API key")
    
    # Configuration files
    config_group = parser.add_argument_group('Configuration Files')
    config_group.add_argument("--api-keys-file", help="JSON file containing API keys for services")
    config_group.add_argument("--save-config", help="Save current configuration to file")
    
    return parser.parse_args()

def load_api_keys(api_keys_file: Optional[str]) -> Dict[str, str]:
    """
    Load API keys from a JSON file.
    
    Args:
        api_keys_file: Path to the JSON file containing API keys
        
    Returns:
        Dictionary of API keys
    """
    if not api_keys_file:
        return {}
        
    try:
        with open(api_keys_file, 'r') as f:
            keys = json.load(f)
            
        # Validate keys
        if not isinstance(keys, dict):
            logger.error("API keys file must contain a JSON object")
            return {}
            
        return keys
    except Exception as e:
        logger.error(f"Error loading API keys file: {e}")
        return {}

def save_config(config: Dict[str, Any], filename: str) -> bool:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        filename: Output filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Configuration saved to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def run_bridge(args):
    """
    Run the Local MCP Bridge with the specified arguments.
    
    Args:
        args: Command-line arguments
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Load API keys
    api_keys = load_api_keys(args.api_keys_file)
    
    # Add any keys from command line
    if args.github_token:
        api_keys[LocalMCPBridge.SERVICE_GITHUB] = args.github_token
    if args.perplexity_key:
        api_keys[LocalMCPBridge.SERVICE_PERPLEXITY] = args.perplexity_key
    if args.firecrawl_key:
        api_keys[LocalMCPBridge.SERVICE_FIRECRAWL] = args.firecrawl_key
    if args.figma_token:
        api_keys[LocalMCPBridge.SERVICE_FIGMA] = args.figma_token
    if args.composio_key:
        api_keys[LocalMCPBridge.SERVICE_COMPOSIO] = args.composio_key
    
    # Save config if requested
    if args.save_config:
        config = {
            "server": {
                "host": args.host,
                "port": args.port,
                "debug": args.debug,
                "find_port": args.find_port
            },
            "cache_enabled": not args.no_cache,
            "api_keys": api_keys
        }
        save_config(config, args.save_config)
    
    # Initialize server
    server = LocalMCPServer(
        config_path=args.config,
        host=args.host,
        port=args.port,
        debug=args.debug,
        api_keys=api_keys,
        cache_enabled=not args.no_cache,
        find_port=args.find_port
    )
    
    try:
        logger.info("Starting Local MCP Bridge...")
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1
    
    return 0

def main():
    """Command-line entry point."""
    args = parse_args()
    return run_bridge(args)

if __name__ == "__main__":
    sys.exit(main()) 