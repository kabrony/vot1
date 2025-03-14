import argparse
import logging
import os
import sys
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run the Local MCP Bridge with Agent Ecosystem")
    
    # Server configuration
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5678, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    # MCP configuration
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--no-cache", action="store_true", help="Disable response caching")
    
    # API keys
    parser.add_argument("--github-token", help="GitHub API token")
    parser.add_argument("--perplexity-key", help="Perplexity API key")
    parser.add_argument("--firecrawl-key", help="Firecrawl API key")
    parser.add_argument("--figma-token", help="Figma API token")
    parser.add_argument("--composio-key", help="Composio API key")
    
    # Agent ecosystem
    parser.add_argument("--agents", action="store_true", help="Enable agent ecosystem")
    parser.add_argument("--agent-config", help="Path to agent configuration file")
    
    return parser.parse_args()

def load_api_keys(args):
    """Load API keys from arguments and environment variables."""
    api_keys = {}
    
    # Load from arguments
    if args.github_token:
        api_keys["GITHUB"] = args.github_token
    if args.perplexity_key:
        api_keys["PERPLEXITY"] = args.perplexity_key
    if args.firecrawl_key:
        api_keys["FIRECRAWL"] = args.firecrawl_key
    if args.figma_token:
        api_keys["FIGMA"] = args.figma_token
    if args.composio_key:
        api_keys["COMPOSIO"] = args.composio_key
    
    # Load from environment variables
    if os.environ.get("VOT1_MCP_GITHUB_KEY"):
        api_keys["GITHUB"] = os.environ.get("VOT1_MCP_GITHUB_KEY")
    if os.environ.get("VOT1_MCP_PERPLEXITY_KEY"):
        api_keys["PERPLEXITY"] = os.environ.get("VOT1_MCP_PERPLEXITY_KEY")
    if os.environ.get("VOT1_MCP_FIRECRAWL_KEY"):
        api_keys["FIRECRAWL"] = os.environ.get("VOT1_MCP_FIRECRAWL_KEY")
    if os.environ.get("VOT1_MCP_FIGMA_KEY"):
        api_keys["FIGMA"] = os.environ.get("VOT1_MCP_FIGMA_KEY")
    if os.environ.get("VOT1_MCP_COMPOSIO_KEY"):
        api_keys["COMPOSIO"] = os.environ.get("VOT1_MCP_COMPOSIO_KEY")
    
    # Try to load from config file
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                if "api_keys" in config:
                    # Only override keys that weren't set from command line or env vars
                    for service, key in config["api_keys"].items():
                        if service not in api_keys:
                            api_keys[service] = key
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    return api_keys

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update MCP configuration with internal tools
    logger.info("Updating MCP configuration...")
    from src.vot1.local_mcp.update_config import update_mcp_config
    update_mcp_config()
    
    # Create the MCP bridge
    from src.vot1.local_mcp.bridge import LocalMCPBridge
    logger.info("Creating Local MCP Bridge...")
    bridge = LocalMCPBridge(
        config_path="src/vot1/local_mcp/config/mcp.json",
        cache_enabled=not args.no_cache
    )
    
    # Initialize connections with API keys
    api_keys = load_api_keys(args)
    for service, key in api_keys.items():
        try:
            if service == "GITHUB":
                bridge.initiate_connection("GITHUB", {"token": key})
                logger.info("Connected to GitHub")
            elif service == "PERPLEXITY":
                bridge.initiate_connection("PERPLEXITY", {"api_key": key})
                logger.info("Connected to Perplexity")
            elif service == "FIRECRAWL":
                bridge.initiate_connection("FIRECRAWL", {"api_key": key})
                logger.info("Connected to Firecrawl")
            elif service == "FIGMA":
                bridge.initiate_connection("FIGMA", {"token": key})
                logger.info("Connected to Figma")
            elif service == "COMPOSIO":
                bridge.initiate_connection("COMPOSIO", {"api_key": key})
                logger.info("Connected to Composio")
        except Exception as e:
            logger.error(f"Error connecting to {service}: {e}")
    
    # Create and run the server
    logger.info("Starting Local MCP Server with Agent support...")
    if args.agents:
        # Run server with agent ecosystem
        from src.vot1.local_mcp.server_integration import LocalMCPServerWithAgents
        server = LocalMCPServerWithAgents(bridge, host=args.host, port=args.port)
    else:
        # Run regular server
        from src.vot1.local_mcp.server import LocalMCPServer
        server = LocalMCPServer(bridge, host=args.host, port=args.port)
    
    try:
        server.run(debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        if hasattr(server, 'shutdown'):
            server.shutdown()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 