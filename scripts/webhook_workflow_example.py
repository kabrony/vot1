#!/usr/bin/env python3
"""
GitHub Webhook and Workflow Example

This script demonstrates how to use the webhook and workflow features
of the GitHub Update Automation with MCP GitHub integration.
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
        logging.FileHandler(os.path.join('logs', 'webhook_workflow_example.log'), mode='a')
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
        # Optionally merge with defaults if needed
    
    return config_file

async def create_webhook_example(automation, owner, repo):
    """Create a webhook example."""
    logger.info("Creating webhook example")
    
    # Example webhook URL (replace with your actual webhook endpoint)
    webhook_url = "https://example.com/webhook"
    
    # Create webhook with push and pull_request events
    webhook_result = await automation.create_webhook(
        owner=owner,
        repo=repo,
        webhook_url=webhook_url,
        events=["push", "pull_request", "workflow_run"]
    )
    
    logger.info(f"Webhook creation result: {webhook_result}")
    return webhook_result

async def create_workflow_example(automation, owner, repo):
    """Create a workflow example."""
    logger.info("Creating workflow example")
    
    # Create CI workflow
    workflow_result = await automation.create_or_update_workflow(
        owner=owner,
        repo=repo,
        workflow_path=".github/workflows/ci.yml",
        workflow_content=CI_WORKFLOW_YAML,
        commit_message="Add CI workflow"
    )
    
    logger.info(f"Workflow creation result: {workflow_result}")
    return workflow_result

async def list_workflows_example(automation, owner, repo):
    """List workflows example."""
    logger.info("Listing workflows")
    
    workflows_result = await automation.list_workflows(owner, repo)
    
    if workflows_result.get("success") == False:
        logger.error(f"Error listing workflows: {workflows_result.get('error')}")
        return workflows_result
    
    for workflow in workflows_result.get("workflows", []):
        logger.info(f"Workflow: {workflow.get('name')} (ID: {workflow.get('id')})")
    
    return workflows_result

async def trigger_workflow_example(automation, owner, repo, workflow_id):
    """Trigger workflow example."""
    logger.info(f"Triggering workflow {workflow_id}")
    
    # Trigger workflow with custom inputs
    trigger_result = await automation.trigger_workflow(
        owner=owner,
        repo=repo,
        workflow_id=workflow_id,
        ref="main",
        inputs={"reason": "Triggered by webhook_workflow_example.py"}
    )
    
    logger.info(f"Workflow trigger result: {trigger_result}")
    return trigger_result

async def main():
    """Run the GitHub webhook and workflow examples."""
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python webhook_workflow_example.py OWNER REPO [--create-webhook] [--create-workflow] [--list-workflows] [--trigger-workflow WORKFLOW_ID]")
        return 1
    
    owner = sys.argv[1]
    repo = sys.argv[2]
    
    create_webhook = "--create-webhook" in sys.argv
    create_workflow = "--create-workflow" in sys.argv
    list_workflows = "--list-workflows" in sys.argv
    trigger_workflow = "--trigger-workflow" in sys.argv
    
    workflow_id = None
    if trigger_workflow:
        try:
            idx = sys.argv.index("--trigger-workflow")
            if idx + 1 < len(sys.argv):
                workflow_id = sys.argv[idx + 1]
        except ValueError:
            pass
    
    if not any([create_webhook, create_workflow, list_workflows, trigger_workflow]):
        # Default to listing workflows if no action specified
        list_workflows = True
    
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
    
    # Initialize GitHubUpdateAutomation
    logger.info("Initializing GitHubUpdateAutomation...")
    automation = GitHubUpdateAutomation(
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="anthropic/claude-3-5-sonnet-20240620",
        use_extended_thinking=True,
        max_thinking_tokens=16000,
        memory_path=memory_path,  # This parameter must match what MemoryManager expects
        github_token=github_token,
        default_owner=owner,
        default_repo=repo,
        use_composio=True,
        use_perplexity=True
    )
    
    logger.info(f"Starting webhook and workflow operations for {owner}/{repo}")
    
    try:
        if create_webhook:
            await create_webhook_example(automation, owner, repo)
        
        if create_workflow:
            await create_workflow_example(automation, owner, repo)
        
        if list_workflows:
            await list_workflows_example(automation, owner, repo)
        
        if trigger_workflow and workflow_id:
            await trigger_workflow_example(automation, owner, repo, workflow_id)
        elif trigger_workflow:
            logger.error("Workflow ID is required for --trigger-workflow")
            return 1
        
        logger.info("Webhook and workflow operations completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Error in webhook and workflow operations: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 