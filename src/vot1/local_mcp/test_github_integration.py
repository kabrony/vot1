#!/usr/bin/env python3
"""
VOTai GitHub Integration Test Script

This script tests the functionality of the VOTai GitHub Integration module.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import json
import logging
import time
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('github_integration_test.log', mode='w')
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
    logger.info(f"\n{votai_ascii}\nVOTai GitHub Integration Test")
    
    # Initialize the bridge
    bridge = LocalMCPBridge()
    
    # Initialize the GitHub integration
    github = GitHubIntegration(bridge)
    
    # Test GitHub status
    logger.info("Testing GitHub status...")
    status = github.get_status()
    logger.info(f"GitHub status: {json.dumps(status, indent=2)}")
    
    if not status.get("successful", False):
        logger.error("GitHub integration is not available. Exiting.")
        return
    
    # Test repository analysis
    logger.info("Testing repository analysis...")
    repo_analysis = github.analyze_repository(
        owner="anthropics",
        repo="anthropic-sdk-python",
        depth="summary",
        focus=["structure", "dependencies", "quality"]
    )
    
    if repo_analysis.get("successful", False):
        logger.info("Repository analysis successful!")
        analysis_text = repo_analysis.get("analysis", "")
        logger.info(f"Analysis preview: {analysis_text[:200]}...")
    else:
        logger.error(f"Repository analysis failed: {repo_analysis.get('error', 'Unknown error')}")
    
    # Test pull request analysis if there are open PRs
    logger.info("Testing pull request analysis...")
    
    # First, get a list of open PRs
    try:
        # This is a simplified approach - in a real scenario, you'd use the GitHub API to list PRs
        pr_number = 1  # Use a known PR number for testing
        
        pr_analysis = github.analyze_pull_request(
            owner="anthropics",
            repo="anthropic-sdk-python",
            pr_number=pr_number,
            focus=["code quality", "performance", "security"]
        )
        
        if pr_analysis.get("successful", False):
            logger.info("Pull request analysis successful!")
            analysis_text = pr_analysis.get("analysis", "")
            logger.info(f"Analysis preview: {analysis_text[:200]}...")
        else:
            logger.error(f"Pull request analysis failed: {pr_analysis.get('error', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error during pull request analysis test: {e}")
    
    logger.info("GitHub integration test completed!")

if __name__ == "__main__":
    main() 