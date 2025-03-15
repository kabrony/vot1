#!/usr/bin/env python3
"""
VOT1 Dashboard Example

This script demonstrates how to launch the VOT1 dashboard with various configurations.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the vot1 package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vot1_dashboard')

# Load environment variables from .env file if it exists
load_dotenv()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the VOT1 dashboard')
    
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host to run the dashboard server on (default: 127.0.0.1)')
    
    parser.add_argument('--port', type=int, default=5000,
                        help='Port to run the dashboard server on (default: 5000)')
    
    parser.add_argument('--debug', action='store_true',
                        help='Run the dashboard in debug mode')
    
    parser.add_argument('--memory-path', type=str, default=None,
                        help='Path to store memory files (default: .vot1/memory)')
    
    parser.add_argument('--no-memory', action='store_true',
                        help='Disable memory management')
    
    parser.add_argument('--api-key', type=str,
                        help='Anthropic API key (if not provided, will use ANTHROPIC_API_KEY environment variable)')
    
    parser.add_argument('--model', type=str, default='claude-3.7-sonnet-20240620',
                        help='Claude model to use (default: claude-3.7-sonnet-20240620)')
    
    parser.add_argument('--github-token', type=str,
                        help='GitHub token for integration (if not provided, will use GITHUB_TOKEN environment variable)')
    
    parser.add_argument('--github-repo', type=str,
                        help='GitHub repository for integration in format "owner/repo"')
    
    parser.add_argument('--perplexity-api-key', type=str,
                        help='Perplexity API key for web search enhancement (if not provided, will use PERPLEXITY_API_KEY)')
    
    return parser.parse_args()

def main():
    """Main function to run the dashboard"""
    # Parse command line arguments
    args = parse_args()
    
    try:
        # Import required components
        from vot1.client import EnhancedClaudeClient
        from vot1.dashboard import create_dashboard
        
        # Initialize the memory manager if enabled
        memory_manager = None
        if not args.no_memory:
            try:
                from vot1.memory import MemoryManager
                memory_manager = MemoryManager(storage_dir=args.memory_path)
                logger.info(f"Memory manager initialized at {memory_manager.storage_dir}")
            except ImportError as e:
                logger.warning(f"Could not import MemoryManager: {e}")
                logger.warning("Running without memory management")
        
        # Set up API key
        api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            logger.warning("No Anthropic API key provided. Some features may not work.")
        
        # Initialize the client
        client = EnhancedClaudeClient(
            api_key=api_key,
            model=args.model
        )
        
        # Set up GitHub integration if credentials provided
        github_token = args.github_token or os.environ.get('GITHUB_TOKEN')
        github_repo = args.github_repo
        
        if github_token and github_repo:
            try:
                client.setup_github(github_token, github_repo)
                logger.info(f"GitHub integration set up for repository: {github_repo}")
            except Exception as e:
                logger.error(f"Failed to set up GitHub integration: {e}")
        
        # Set up Perplexity API if key provided
        perplexity_api_key = args.perplexity_api_key or os.environ.get('PERPLEXITY_API_KEY')
        if perplexity_api_key:
            client.perplexity_api_key = perplexity_api_key
            logger.info("Perplexity API integration enabled")
        
        # Create and start the dashboard
        dashboard = create_dashboard(
            client=client,
            memory_manager=memory_manager,
            host=args.host,
            port=args.port,
            start_server=True,
            debug=args.debug
        )
        
        logger.info(f"Dashboard server running at http://{args.host}:{args.port}")
        logger.info("Press Ctrl+C to stop the server")
        
        # The dashboard.start() method will block until the server is stopped
        # If we get here, it means the server was stopped
        logger.info("Dashboard server stopped")
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Please make sure you have installed the requirements")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Dashboard server stopped by user")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 