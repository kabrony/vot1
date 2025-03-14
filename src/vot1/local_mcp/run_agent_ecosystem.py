#!/usr/bin/env python3
"""
Run VOTai Agent Ecosystem

This script starts the VOTai Local MCP Bridge with agent ecosystem support.
Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'agent_ecosystem.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import local_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.vot1.local_mcp.server import LocalMCPServer
from src.vot1.local_mcp.update_config import update_mcp_config
from src.vot1.local_mcp.port_finder import find_available_port
from src.vot1.local_mcp.ascii_art import get_votai_ascii

def load_api_keys():
    """Load API keys from environment variables and .env file."""
    api_keys = {}
    
    # Try to load from .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    # Load from environment variables
    for service in [
        'GITHUB', 'PERPLEXITY', 'FIRECRAWL', 'FIGMA', 'COMPOSIO'
    ]:
        env_var = f"{service}_API_KEY"
        if env_var in os.environ:
            api_keys[service] = os.environ[env_var]
            logger.info(f"Loaded API key for {service}")
    
    return api_keys

def main():
    """Main function to start the agent ecosystem server."""
    parser = argparse.ArgumentParser(description="Start the VOTai Agent Ecosystem server")
    parser.add_argument("--host", default="localhost", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=5678, help="Port to run the server on")
    parser.add_argument("--find-port", action="store_true", help="Find an available port automatically")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Display VOTai banner
    votai_banner = get_votai_ascii("large")
    print(f"\n{votai_banner}")
    print("VOTai Agent Ecosystem - A New Dawn of a Holistic Paradigm\n")
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Update the MCP configuration file
        logger.info("Updating MCP configuration...")
        update_mcp_config()
        
        # Load API keys
        api_keys = load_api_keys()
        
        # Check if port is available or find an alternative
        port = args.port
        if args.find_port:
            available_port = find_available_port(start_port=port)
            if available_port and available_port != port:
                logger.warning(f"Port {port} is in use, using port {available_port} instead")
                port = available_port
        
        # Update the config with the correct port if it changed
        if port != args.port:
            # Update the LOCAL server URL in the config
            config_path = os.path.join("src", "vot1", "local_mcp", "config", "mcp.json")
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if "mcpServers" in config and "LOCAL" in config["mcpServers"]:
                    config["mcpServers"]["LOCAL"]["url"] = f"http://localhost:{port}/api"
                    
                    with open(config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    logger.info(f"Updated LOCAL server URL in config to port {port}")
            except Exception as e:
                logger.error(f"Error updating config with new port: {e}")
        
        # Start the server with agent ecosystem enabled
        logger.info(f"Starting Local MCP Bridge with Agent Ecosystem on port {port}...")
        server = LocalMCPServer(
            host=args.host,
            port=port,
            debug=args.debug,
            api_keys=api_keys,
            enable_agents=True,
            find_port=True  # Always enable find_port for agent ecosystem
        )
        
        # Run the server
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running agent ecosystem: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 