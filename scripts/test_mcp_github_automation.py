#!/usr/bin/env python3
"""
Test MCP GitHub Automation with Claude 3.7 Maximum Thinking

This script demonstrates how to use the GitHub Update Automation with MCP Composio integration
and Claude 3.7 with maximum thinking capability (16,000 tokens). It also integrates
Perplexity for web search to enhance analysis.
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.github_update_automation import GitHubUpdateAutomation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_mcp_github_automation.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_mcp_config():
    """Load MCP configuration from file or create a default one."""
    config_dir = os.path.join('src', 'vot1', 'config')
    config_file = os.path.join(config_dir, 'mcp.json')
    
    os.makedirs(config_dir, exist_ok=True)
    
    default_config = {
        "providers": {
            "github": {
                "url": "https://mcp.composio.dev/github/victorious-damaged-branch-0ojHhf"
            },
            "perplexity": {
                "url": "https://mcp.composio.dev/perplexity/victorious-damaged-branch-0ojHhf"
            }
        }
    }
    
    if not os.path.exists(config_file):
        logger.info(f"Creating default MCP config at {config_file}")
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
    else:
        logger.info(f"Found existing MCP config at {config_file}")
    
    return config_file

async def main():
    """Test MCP GitHub Automation with Claude 3.7 Maximum Thinking"""
    
    # Set your repository details
    owner = "kabrony"
    repo = "vot1"
    
    # Ensure GitHub token is available
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token is required. Set it with GITHUB_TOKEN environment variable.")
        return 1
    
    # Ensure MCP config is available
    mcp_config_file = load_mcp_config()
    logger.info(f"Using MCP config from {mcp_config_file}")
    
    # Ensure memory directory exists
    memory_path = "./memory"
    os.makedirs(memory_path, exist_ok=True)
    logger.info(f"Ensuring memory directory exists at {memory_path}")
    
    # Initialize GitHubUpdateAutomation with MCP integration and Claude 3.7 maximum thinking
    logger.info("Initializing GitHubUpdateAutomation...")
    automation = GitHubUpdateAutomation(
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="anthropic/claude-3-5-sonnet-20240620",
        use_extended_thinking=True,
        max_thinking_tokens=16000,  # Maximum thinking power
        memory_path=memory_path,    # Using memory_path parameter, not storage_path
        github_token=github_token,
        auto_approve=False,  # Set to True to auto-approve pull requests
        use_composio=True,   # Use MCP Composio integration
        use_perplexity=True  # Use Perplexity for web search
    )
    
    logger.info("Starting GitHub Update Automation with Claude 3.7 Maximum Thinking")
    logger.info(f"Repository: {owner}/{repo}")
    logger.info(f"Max thinking tokens: 16,000")
    logger.info(f"Using MCP integrations: GitHub and Perplexity")
    
    # Perform a test web search to enhance analysis
    try:
        logger.info("Testing Perplexity web search integration...")
        search_result = await automation.web_search(f"GitHub repository {owner}/{repo} latest updates")
        if search_result.get("success"):
            logger.info("Web search completed successfully")
        else:
            logger.warning(f"Web search error: {search_result.get('error')}")
    except Exception as e:
        logger.warning(f"Web search error: {str(e)}")
    
    # Start repository analysis and update
    logger.info("Starting repository analysis and update...")
    try:
        # Analyze repository and generate improvement plan
        analysis_result = await automation.analyze_and_update(
            owner=owner,
            repo=repo,
            deep_analysis=True,  # Perform deep analysis for better results
            update_areas=["documentation", "workflows", "code_quality"],  # Select update areas
            max_updates=3  # Limit number of updates (3 per area)
        )
        
        if analysis_result.get("success"):
            logger.info(f"Analysis and update completed successfully")
            logger.info(f"Generated {len(analysis_result.get('updates', []))} updates")
            
            for i, update in enumerate(analysis_result.get("updates", [])):
                logger.info(f"Update {i+1}: {update.get('title')} - {update.get('type')}")
                
            logger.info("GitHub Update Automation with Claude 3.7 Maximum Thinking completed successfully")
            return 0
        else:
            logger.error(f"Analysis and update failed: {analysis_result.get('error')}")
            return 1
    except Exception as e:
        logger.error(f"Error in analysis and update: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 