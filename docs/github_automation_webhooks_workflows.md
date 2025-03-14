# GitHub Automation: Webhooks and Workflows

This document provides detailed information on how to use the webhook and workflow management features of the VOT1 GitHub Automation system.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Webhooks](#webhooks)
  - [Creating Webhooks](#creating-webhooks)
  - [Listing Webhooks](#listing-webhooks)
  - [Deleting Webhooks](#deleting-webhooks)
- [Workflows](#workflows)
  - [Creating Workflows](#creating-workflows)
  - [Listing Workflows](#listing-workflows)
  - [Triggering Workflows](#triggering-workflows)
- [Example Script](#example-script)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Overview

The VOT1 GitHub Automation system allows you to create and manage GitHub webhooks and workflows programmatically. This enables you to:

- Set up automated responses to repository events (using webhooks)
- Create and update GitHub Actions workflows
- List existing workflows in a repository
- Trigger workflows manually with custom inputs

These features are powered by the VOT1 MCP (Model Control Protocol) GitHub integration, which leverages Claude 3.7 for advanced automation.

## Requirements

To use these features, you'll need:

1. A GitHub Personal Access Token (PAT) with the following permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `admin:repo_hook` (Full control of repository hooks)

2. The VOT1 system installed and configured with MCP enabled

3. Set your GitHub token as an environment variable:
   ```bash
   export GITHUB_TOKEN="your_github_token"
   ```

## Webhooks

Webhooks allow you to set up integrations that subscribe to specific events on GitHub. When one of those events is triggered, GitHub sends a POST request to the webhook's configured URL.

### Creating Webhooks

You can create a webhook that will notify an external service when events occur in your repository.

```python
await automation.create_webhook(
    owner="repo-owner",
    repo="repo-name",
    webhook_url="https://your-service.com/webhook",
    events=["push", "pull_request"],
    secret="optional-secret-for-signature-verification"
)
```

#### Parameters:

- **owner** (str): Repository owner username
- **repo** (str): Repository name
- **webhook_url** (str): The URL that will receive the webhook payload
- **events** (list): List of events to trigger the webhook (default: ["push", "pull_request"])
- **secret** (str, optional): Secret for signature verification

#### Supported Events:

- `push`: Any git push to the repository
- `pull_request`: Activity on pull requests
- `issues`: Activity on issues
- `release`: Activity on releases
- `workflow_run`: When a GitHub Actions workflow run is triggered
- `discussion`: Activity on discussions
- `commit_comment`: A commit comment is created
- And [many more](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads)

### Listing Webhooks

To view all webhooks configured for a repository:

```python
webhooks = await automation.github_bridge.list_webhooks(
    owner="repo-owner",
    repo="repo-name"
)
```

### Deleting Webhooks

To remove a webhook:

```python
await automation.github_bridge.delete_webhook(
    owner="repo-owner",
    repo="repo-name",
    webhook_id="webhook-id"
)
```

## Workflows

GitHub Actions workflows automate your software development workflows right in your repository.

### Creating Workflows

You can create or update a GitHub Actions workflow file in your repository:

```python
await automation.create_or_update_workflow(
    owner="repo-owner",
    repo="repo-name",
    workflow_path=".github/workflows/ci.yml",
    workflow_content=your_workflow_yaml,
    commit_message="Add CI workflow"
)
```

#### Parameters:

- **owner** (str): Repository owner username
- **repo** (str): Repository name
- **workflow_path** (str): Path to the workflow file in the repository
- **workflow_content** (str): YAML content of the workflow
- **commit_message** (str): Commit message for creating/updating the workflow

### Listing Workflows

To list all workflows in a repository:

```python
workflows = await automation.list_workflows(
    owner="repo-owner",
    repo="repo-name"
)
```

### Triggering Workflows

You can trigger a workflow that's configured with the `workflow_dispatch` event:

```python
await automation.trigger_workflow(
    owner="repo-owner",
    repo="repo-name",
    workflow_id="workflow-id",
    ref="main",
    inputs={"parameter1": "value1", "parameter2": "value2"}
)
```

#### Parameters:

- **owner** (str): Repository owner username
- **repo** (str): Repository name
- **workflow_id** (str): The ID or filename of the workflow
- **ref** (str): The git reference (branch/tag/commit) on which to trigger the workflow
- **inputs** (dict, optional): Input parameters defined in the workflow

## Example Script

The VOT1 GitHub Automation includes an example script that demonstrates these features:

```bash
python -m scripts.webhook_workflow_example OWNER REPO [--create-webhook] [--create-workflow] [--list-workflows] [--trigger-workflow WORKFLOW_ID]
```

See the full example in [scripts/webhook_workflow_example.py](../scripts/webhook_workflow_example.py).

## API Reference

### GitHubUpdateAutomation

```python
class GitHubUpdateAutomation:
    async def create_webhook(self, owner, repo, webhook_url, events=None, secret=None):
        """Create a webhook for a repository."""
        
    async def list_workflows(self, owner, repo):
        """List GitHub Actions workflows in a repository."""
        
    async def create_or_update_workflow(self, owner, repo, workflow_path, workflow_content, commit_message):
        """Create or update a GitHub Actions workflow file."""
        
    async def trigger_workflow(self, owner, repo, workflow_id, ref, inputs=None):
        """Trigger a GitHub Actions workflow."""
```

### GitHubComposioBridge

```python
class GitHubComposioBridge:
    async def create_webhook(self, owner, repo, webhook_payload):
        """Create a webhook using MCP GitHub integration."""
        
    async def list_webhooks(self, owner, repo):
        """List webhooks using MCP GitHub integration."""
        
    async def delete_webhook(self, owner, repo, webhook_id):
        """Delete a webhook using MCP GitHub integration."""
        
    async def dispatch_workflow(self, owner, repo, workflow_id, payload):
        """Dispatch a workflow using MCP GitHub integration."""
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure your GitHub token has the required permissions
   - Check that the token is correctly set in the environment variable

2. **Webhook Creation Failed**
   - Verify webhook URL is accessible from GitHub's servers
   - Ensure you have admin permissions on the repository

3. **Workflow Trigger Failed**
   - Confirm the workflow has a `workflow_dispatch` trigger event
   - Check that the provided inputs match what's defined in the workflow

4. **Directory Creation Failed**
   - Ensure your token has push access to the repository

### Logs

For detailed troubleshooting, check the logs at:
- `logs/github_update_automation.log`
- `logs/webhook_workflow_example.log`

For MCP-specific issues:
- `logs/vot_mcp.log` 