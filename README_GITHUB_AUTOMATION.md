# GitHub Automation with VOT1

This document provides a comprehensive guide to using the GitHub Automation features in VOT1, including repository analysis, automated improvements, webhooks, and workflow management.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
  - [Repository Analysis](#repository-analysis)
  - [Automated Improvements](#automated-improvements)
  - [Webhook Integration](#webhook-integration)
  - [Workflow Management](#workflow-management)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

The GitHub Automation feature in VOT1 leverages Claude 3.7 to analyze GitHub repositories and generate targeted improvements. It can:

- Analyze repository structure and codebase
- Generate comprehensive improvement plans
- Create pull requests with suggested improvements
- Set up webhooks for automated triggers
- Create and manage GitHub Actions workflows
- Provide 3D visualization of repository updates
- Offer insights into AI reasoning

The system uses a dual-model approach for efficient analysis and the VOT1 Model Control Protocol (MCP) for integrating with GitHub's API.

## Installation

1. Clone the VOT1 repository:
   ```bash
   git clone https://github.com/kabrony/vot1.git
   cd vot1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your GitHub token:
   ```bash
   export GITHUB_TOKEN="your_github_token"
   ```

## Configuration

The GitHub Automation feature requires a GitHub Personal Access Token with the following permissions:
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)
- `admin:repo_hook` (Full control of repository hooks)

You can configure the feature through environment variables or command-line arguments:

```bash
# Environment variables
export GITHUB_TOKEN="your_github_token"
export COMPOSIO_API_KEY="your_composio_api_key"  # Optional, for enhanced MCP integration

# Command-line arguments
python -m scripts.run_github_automation --github-token YOUR_TOKEN --owner OWNER --repo REPO
```

## Basic Usage

### Command Line

```bash
# Basic analysis and update
python -m scripts.run_github_automation --owner OWNER --repo REPO

# Full command with all options
python -m scripts.run_github_automation \
  --owner OWNER \
  --repo REPO \
  --github-token YOUR_TOKEN \
  --deep-analysis \
  --max-thinking-tokens 10000 \
  --update-areas documentation workflows dependencies code_quality \
  --auto-approve \
  --use-composio \
  --create-visualization
```

### Python API

```python
from scripts.github_update_automation import GitHubUpdateAutomation

# Initialize the automation
automation = GitHubUpdateAutomation(
    primary_model="anthropic/claude-3-7-sonnet-20240620",
    secondary_model="anthropic/claude-3-5-sonnet-20240620",
    use_extended_thinking=True,
    max_thinking_tokens=16000,
    memory_path="./memory",
    github_token="your_github_token",
    use_composio=True
)

# Analyze and update a repository
result = await automation.analyze_and_update(
    owner="owner",
    repo="repo",
    deep_analysis=True,
    update_areas=["documentation", "workflows", "dependencies", "code_quality"],
    max_updates=5
)
```

## Advanced Features

### Repository Analysis

The GitHub Automation feature can perform deep analysis of repositories to identify areas for improvement:

```python
# Analyze a repository
analysis = await automation.analyzer.analyze_repository(
    owner="owner",
    repo="repo",
    deep_analysis=True
)

# Generate an improvement plan
plan = await automation.analyzer.generate_improvement_plan(
    owner="owner",
    repo="repo"
)
```

### Automated Improvements

The system can automatically create improvements in several areas:

1. **Documentation Updates**
   - README improvements
   - Code documentation
   - User guides
   - API references

2. **Workflow Updates**
   - GitHub Actions workflow creation and optimization
   - CI/CD pipeline improvements
   - Automation of repetitive tasks

3. **Dependency Updates**
   - Identifying outdated dependencies
   - Recommending version upgrades
   - Security vulnerability fixes

4. **Code Quality Updates**
   - Code structure improvements
   - Performance optimizations
   - Best practices implementation

### Webhook Integration

You can create and manage webhooks to trigger automated processes when repository events occur:

```python
# Create a webhook
webhook_result = await automation.create_webhook(
    owner="owner",
    repo="repo",
    webhook_url="https://your-service.com/webhook",
    events=["push", "pull_request"],
    secret="optional-secret-for-verification"
)
```

Webhooks can be used to:
- Trigger CI/CD pipelines
- Notify external services of repository changes
- Automate deployment processes
- Integrate with monitoring systems

### Workflow Management

You can create, list, and trigger GitHub Actions workflows:

```python
# List workflows
workflows = await automation.list_workflows(
    owner="owner",
    repo="repo"
)

# Create or update a workflow
workflow_result = await automation.create_or_update_workflow(
    owner="owner",
    repo="repo",
    workflow_path=".github/workflows/ci.yml",
    workflow_content=workflow_yaml_content,
    commit_message="Add CI workflow"
)

# Trigger a workflow
trigger_result = await automation.trigger_workflow(
    owner="owner",
    repo="repo",
    workflow_id="workflow-id",
    ref="main",
    inputs={"parameter": "value"}
)
```

## API Reference

### GitHubUpdateAutomation

```python
class GitHubUpdateAutomation:
    """
    Automated GitHub repository updates based on ecosystem analysis.
    """
    
    def __init__(
        self,
        analyzer=None,
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="anthropic/claude-3-5-sonnet-20240620",
        use_extended_thinking=True,
        max_thinking_tokens=16000,
        memory_path=None,
        github_token=None,
        composio_api_key=None,
        default_owner=None,
        default_repo=None,
        auto_approve=False,
        use_composio=True,
        use_perplexity=True
    ):
        """Initialize GitHub Update Automation."""
        
    async def analyze_and_update(
        self,
        owner,
        repo,
        deep_analysis=True,
        update_areas=None,
        max_updates=3
    ):
        """Analyze a repository and create updates."""
        
    async def create_webhook(
        self,
        owner,
        repo,
        webhook_url,
        events=None,
        secret=None
    ):
        """Create a webhook for a repository."""
        
    async def list_workflows(
        self,
        owner,
        repo
    ):
        """List GitHub Actions workflows in a repository."""
        
    async def create_or_update_workflow(
        self,
        owner,
        repo,
        workflow_path,
        workflow_content,
        commit_message="Update workflow"
    ):
        """Create or update a GitHub Actions workflow file."""
        
    async def trigger_workflow(
        self,
        owner,
        repo,
        workflow_id,
        ref="main",
        inputs=None
    ):
        """Trigger a GitHub Actions workflow."""
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure your GitHub token has the required permissions
   - Check that the token is correctly set in the environment variable

2. **MCP Configuration Issues**
   - Verify that the MCP configuration file exists at `src/vot1/config/mcp.json`
   - Check that the configuration contains valid URLs for GitHub and Perplexity

3. **Memory Manager Errors**
   - Ensure the memory directory exists and is writable
   - Check that the `memory_path` parameter is correctly set

4. **Webhook/Workflow Errors**
   - Verify your token has appropriate permissions
   - Check network access to GitHub API

### Logs

For detailed troubleshooting, check the logs at:
- `logs/github_update_automation.log`
- `logs/webhook_workflow_example.log`

## Examples

### Example Scripts

- [Webhook and Workflow Example](scripts/webhook_workflow_example.py)
- [Test GitHub Webhook](scripts/test_github_webhook.py)

### Example Workflow YAML

```yaml
name: CI

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
``` 