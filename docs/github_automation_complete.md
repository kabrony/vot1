# GitHub Update Automation - Complete Guide

This comprehensive documentation covers all features of the VOT1 GitHub Update Automation system, including repository analysis, automated improvements, webhooks, and workflow integration.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Authentication](#authentication)
- [Using the VOT1 Dashboard](#using-the-vot1-dashboard)
- [Command Line Usage](#command-line-usage)
- [Update Areas](#update-areas)
- [Webhook Integration](#webhook-integration)
- [Workflow Management](#workflow-management)
- [3D Visualization](#3d-visualization)
- [AI Reasoning Insights](#ai-reasoning-insights)
- [Memory Integration](#memory-integration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

## Overview

The GitHub Update Automation feature uses advanced AI (Claude 3.7) to analyze your GitHub repositories and generate targeted improvements. It can:

- Analyze your repository structure and codebase
- Generate a comprehensive improvement plan
- Create pull requests with suggested improvements
- Set up webhooks for automated triggers
- Create and manage GitHub Actions workflows
- Provide 3D visualization of repository updates
- Offer insights into AI reasoning

The system leverages a dual-model approach for efficient analysis and uses the VOT1 Model Control Protocol (MCP) for integrating with GitHub's API.

## Getting Started

### Prerequisites

To use GitHub Update Automation, you need:

1. A GitHub account with repositories you want to improve
2. The VOT1 system installed and configured
3. A GitHub Personal Access Token with the following permissions:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
   - `admin:repo_hook` (Full control of repository hooks)

### Authentication

Set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN="your_github_token"
```

Or provide it directly when running the command:

```bash
python -m scripts.run_github_automation --github-token YOUR_TOKEN --owner OWNER --repo REPO
```

## Using the VOT1 Dashboard

The easiest way to use GitHub Update Automation is through the VOT1 Dashboard:

1. Navigate to the GitHub tab in the VOT1 Dashboard
2. Enter your repository details (owner and name)
3. Select the update areas you want to improve
4. Configure advanced options if needed
5. Click "Create Updates" to start the process

The dashboard provides real-time progress updates and visualization of the changes.

## Command Line Usage

For advanced users, the GitHub Update Automation can be run from the command line:

### Basic Command

```bash
python -m scripts.run_github_automation --owner OWNER --repo REPO
```

### Full Command with All Options

```bash
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

### Parameters

- `--owner`: GitHub username of the repository owner
- `--repo`: Name of the repository
- `--github-token`: GitHub Personal Access Token (optional if set as environment variable)
- `--deep-analysis`: Perform a more thorough analysis (takes longer but produces better results)
- `--max-thinking-tokens`: Maximum number of tokens for AI thinking (default: 2000)
- `--update-areas`: Areas to focus updates on (multiple can be specified)
- `--auto-approve`: Automatically approve and create PRs for updates
- `--use-composio`: Use Composio MCP for GitHub API integration
- `--create-visualization`: Generate 3D visualization of updates

## Update Areas

The GitHub Update Automation can focus on several areas:

### Documentation Updates

- README improvements
- Code documentation
- User guides
- API references
- Example documentation

### Workflow Updates

- GitHub Actions workflow creation and optimization
- CI/CD pipeline improvements
- Automation of repetitive tasks
- Testing workflows

### Dependency Updates

- Identifying outdated dependencies
- Recommending version upgrades
- Security vulnerability fixes
- Dependency clean-up

### Code Quality Updates

- Code structure improvements
- Performance optimizations
- Bug fixes
- Best practices implementation

## Webhook Integration

Webhooks allow your repository to notify external services when certain events occur, triggering automated processes.

### Creating Webhooks

```python
await automation.create_webhook(
    owner="repo-owner",
    repo="repo-name",
    webhook_url="https://your-service.com/webhook",
    events=["push", "pull_request"],
    secret="optional-secret-for-signature-verification"
)
```

### Managing Webhooks

- **List webhooks**: View all webhooks configured for a repository
- **Delete webhooks**: Remove webhooks that are no longer needed

See the [Webhook Documentation](github_automation_webhooks_workflows.md#webhooks) for detailed information.

## Workflow Management

GitHub Actions workflows automate your software development lifecycle directly in your GitHub repository.

### Creating Workflows

```python
await automation.create_or_update_workflow(
    owner="repo-owner",
    repo="repo-name",
    workflow_path=".github/workflows/ci.yml",
    workflow_content=workflow_yaml_content,
    commit_message="Add CI workflow"
)
```

### Triggering Workflows

```python
await automation.trigger_workflow(
    owner="repo-owner",
    repo="repo-name",
    workflow_id="workflow-id",
    ref="main",
    inputs={"parameter": "value"}
)
```

See the [Workflow Documentation](github_automation_webhooks_workflows.md#workflows) for detailed information.

## 3D Visualization

The GitHub Update Automation includes a powerful 3D visualization tool that shows:

- Repository file structure as a 3D tree
- Updates color-coded by type (documentation, workflow, dependency, code quality)
- Interactive controls for exploring the repository
- Before/after comparisons of changes

To generate a visualization:

```bash
python -m scripts.run_github_automation --owner OWNER --repo REPO --create-visualization
```

The visualization will be available in the `visualizations` directory after the analysis completes.

## AI Reasoning Insights

The GitHub Update Automation provides insights into the AI's reasoning process:

- Analysis approaches considered
- Decision factors for improvements
- Confidence levels for suggested changes
- Alternative strategies evaluated

These insights help you understand why certain improvements were suggested and how they fit into the broader context of your repository.

## Memory Integration

The system learns from previous analyses to improve future recommendations:

- Remembers repository structure across runs
- Adapts to your feedback on previous suggestions
- Builds knowledge of your project's specific patterns
- Increases efficiency and accuracy over time

Memory is stored in the `./memory` directory and can be cleared if needed:

```bash
rm -rf ./memory/vector_store.db
```

## Security Considerations

The GitHub Update Automation is designed with security in mind:

- Your GitHub token is handled securely and never logged
- All data is processed locally on your machine
- No repository data is sent to external services without your consent
- Webhook secrets are used for payload verification

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure your GitHub token has the required permissions
   - Check that the token is correctly set

2. **Analysis Errors**
   - Increase max thinking tokens for complex repositories
   - Try running with `--deep-analysis` for more thorough results

3. **Webhook/Workflow Errors**
   - Verify your token has appropriate permissions
   - Check network access to GitHub API

### Logs

For detailed troubleshooting, check the logs at:
- `logs/github_update_automation.log`
- `logs/webhook_workflow_example.log`

## Support

For questions, issues, or feature requests:

- Open an issue on the VOT1 repository
- Join our community Discord for real-time help
- Check the [examples directory](../examples/github_workflows/) for sample workflows

## Example Scripts

- [Webhook and Workflow Example](../scripts/webhook_workflow_example.py)
- [Automated Documentation Workflow](../examples/github_workflows/automated_documentation.yml) 