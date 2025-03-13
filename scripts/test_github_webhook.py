#!/usr/bin/env python3
"""
Test GitHub Webhook and Workflow Functionality

This script tests the webhook and workflow functionality of the GitHub Update Automation.
"""

import os
import sys
import asyncio
import logging
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
        logging.FileHandler(os.path.join('logs', 'test_github_webhook.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Example CI workflow YAML
CI_WORKFLOW_YAML = """name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      reason:
        description: 'Reason for manual trigger'
        required: false
        default: 'Manual test'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run tests
        run: |
          pytest
          
      - name: Notify on success
        if: success()
        run: echo "Tests passed successfully!"
"""

async def test_list_workflows(automation, owner, repo):
    """Test listing workflows."""
    logger.info(f"Testing list_workflows for {owner}/{repo}")
    result = await automation.list_workflows(owner, repo)
    logger.info(f"List workflows result: {result}")
    return result

async def test_create_workflow(automation, owner, repo):
    """Test creating a workflow."""
    logger.info(f"Testing create_or_update_workflow for {owner}/{repo}")
    result = await automation.create_or_update_workflow(
        owner=owner,
        repo=repo,
        workflow_path=".github/workflows/ci.yml",
        workflow_content=CI_WORKFLOW_YAML,
        commit_message="Add CI workflow"
    )
    logger.info(f"Create workflow result: {result}")
    return result

async def test_create_webhook(automation, owner, repo):
    """Test creating a webhook."""
    logger.info(f"Testing create_webhook for {owner}/{repo}")
    result = await automation.create_webhook(
        owner=owner,
        repo=repo,
        webhook_url="https://example.com/webhook",
        events=["push", "pull_request"]
    )
    logger.info(f"Create webhook result: {result}")
    return result

async def main():
    """Run the GitHub webhook and workflow tests."""
    # Set your repository details
    owner = "kabrony"
    repo = "vot1"
    
    # Ensure GitHub token is available
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token is required. Set it with GITHUB_TOKEN environment variable.")
        return 1
    
    # Ensure memory directory exists
    memory_path = "./memory"
    os.makedirs(memory_path, exist_ok=True)
    
    # Initialize GitHubUpdateAutomation
    logger.info("Initializing GitHubUpdateAutomation...")
    automation = GitHubUpdateAutomation(
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="anthropic/claude-3-5-sonnet-20240620",
        use_extended_thinking=True,
        max_thinking_tokens=16000,
        memory_path=memory_path,
        github_token=github_token,
        default_owner=owner,
        default_repo=repo,
        use_composio=True,
        use_perplexity=True
    )
    
    logger.info(f"Starting webhook and workflow tests for {owner}/{repo}")
    
    try:
        # Test listing workflows
        await test_list_workflows(automation, owner, repo)
        
        # Test creating a workflow
        await test_create_workflow(automation, owner, repo)
        
        # Test creating a webhook
        await test_create_webhook(automation, owner, repo)
        
        logger.info("All tests completed")
        return 0
    
    except Exception as e:
        logger.error(f"Error in tests: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 