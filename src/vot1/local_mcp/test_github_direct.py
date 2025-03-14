#!/usr/bin/env python3
"""
VOTai GitHub Integration Direct Test

This script tests the GitHub integration directly without going through the server.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from vot1.local_mcp.bridge import LocalMCPBridge
from vot1.local_mcp.github_integration import GitHubIntegration
from vot1.local_mcp.ascii_art import get_votai_ascii

def main():
    """Main test function."""
    # Display VOTai signature
    votai_ascii = get_votai_ascii("medium")
    logger.info(f"\n{votai_ascii}\nVOTai GitHub Integration Direct Test\n")
    
    # Initialize the bridge
    logger.info("Initializing LocalMCPBridge...")
    bridge = LocalMCPBridge()
    
    # Initialize GitHub integration
    logger.info("Initializing GitHubIntegration...")
    github = GitHubIntegration(bridge)
    
    # Check GitHub status
    logger.info("Checking GitHub status...")
    status = github.get_status()
    logger.info(f"GitHub status: {json.dumps(status, indent=2)}")
    
    # Check if GitHub is configured
    if not status.get("status", {}).get("configured", False):
        logger.error("GitHub service is not configured. Please check your MCP configuration.")
        return
    
    # Check if GitHub PAT is set
    github_pat = os.environ.get("GITHUB_PAT")
    if not github_pat:
        logger.error("GITHUB_PAT environment variable is not set.")
        return
    
    # Initialize GitHub connection
    logger.info("Initializing GitHub connection...")
    try:
        connection_result = bridge.call_function("mcp_MCP_GITHUB_INITIATE_CONNECTION", {
            "params": {
                "tool": "GitHub",
                "parameters": {
                    "api_key": github_pat
                }
            }
        })
        
        logger.info(f"Connection result: {json.dumps(connection_result, indent=2)}")
        
        if not connection_result.get("successful", False):
            logger.error(f"Failed to initialize GitHub connection: {connection_result.get('error')}")
            return
    except Exception as e:
        logger.error(f"Error initializing GitHub connection: {e}")
        return
    
    # Check GitHub status again
    logger.info("Checking GitHub status after connection...")
    status = github.get_status()
    logger.info(f"GitHub status: {json.dumps(status, indent=2)}")
    
    # Test repository analysis
    logger.info("Testing repository analysis...")
    try:
        repo_result = github.analyze_repository(
            owner="microsoft",
            repo="vscode",
            depth="summary",
            focus=["structure", "dependencies", "quality"]
        )
        
        logger.info(f"Repository analysis result: {json.dumps(repo_result, indent=2)}")
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
    
    logger.info("VOTai GitHub Integration Direct Test completed!")

if __name__ == "__main__":
    main() 