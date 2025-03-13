# VOT1 GitHub Integration Guide

This guide explains how to use the VOT1 GitHub integration which leverages the MCP (Model Control Protocol) GitHub functionality for autonomous repository management and improvement.

## Overview

VOT1 integrates directly with GitHub using MCP's built-in capabilities, allowing you to:

1. Analyze repositories for code quality issues
2. Create and manage issues programmatically 
3. Create and analyze pull requests
4. Add comments and review comments to pull requests
5. Run autonomous improvement cycles

This integration does not require setting up a separate GitHub App - it works directly with MCP's GitHub tools.

## Setup Instructions

### 1. Initialize the GitHub Connection

Before using the GitHub integration, you need to establish a connection:

```bash
# Initialize GitHub connection
python -m scripts.init_github

# To only check if a connection exists without trying to create one
python -m scripts.init_github --check
```

The script will:
1. Check if an active GitHub connection exists
2. If not, initiate the OAuth flow to create a connection
3. Save the connection details for future use

### 2. Environment Configuration

Set these environment variables for easier use:

```bash
export GITHUB_OWNER="your-username-or-org"
export GITHUB_REPO="your-repository-name"
```

You can also set these in a `.env` file in your project root:

```
GITHUB_OWNER=your-username-or-org
GITHUB_REPO=your-repository-name
```

## Usage Examples

### Analyzing a Repository

```bash
# Using default repository from environment variables
python -m scripts.run_github_bridge analyze-repo

# Specifying repository
python -m scripts.run_github_bridge analyze-repo --owner username --repo repository
```

This command:
- Retrieves repository information
- Identifies code quality issues (TODOs, FIXMEs, etc.)
- Gets recent pull requests and their status
- Gets recent commits
- Stores the analysis in memory

### Analyzing a Pull Request

```bash
# Analyze PR #123
python -m scripts.run_github_bridge analyze-pr 123

# With specific repository
python -m scripts.run_github_bridge analyze-pr 123 --owner username --repo repository
```

This command:
- Gets pull request details
- Lists commits in the pull request
- Gets detailed information about the latest commit
- Optionally provides code quality feedback
- Offers to post the analysis as a PR comment

### Creating an Issue

```bash
# Create a simple issue
python -m scripts.run_github_bridge create-issue "Bug: Login not working" "The login button doesn't respond when clicked on Firefox."

# With labels
python -m scripts.run_github_bridge create-issue "Feature Request: Dark Mode" "Add dark mode to improve accessibility." --labels enhancement accessibility
```

### Repository Health Check

```bash
# Check repository health
python -m scripts.run_github_bridge check-repo-health

# Create an issue with the health report
python -m scripts.run_github_bridge check-repo-health --create-issue
```

This command:
- Analyzes the repository
- Generates a comprehensive health report
- Optionally creates an issue with the findings

### Creating Improvement Issues

```bash
# Create an improvement issue for a specific file
python -m scripts.run_github_bridge create-improvement-issue src/vot1/memory.py

# Only creates an issue if the quality score is below 0.85
```

### Running an Autonomous Improvement Cycle

```bash
# Run an autonomous improvement cycle with auto-discovery
python -m scripts.run_github_bridge run-autonomous-cycle

# Target specific components
python -m scripts.run_github_bridge run-autonomous-cycle --components src/vot1/memory.py src/vot1/owl_reasoning.py
```

This cycle:
1. Analyzes the repository
2. Identifies components to improve
3. Analyzes each component
4. Creates improvement issues for components with quality below threshold

## GitHub Actions Workflow

You can use the autonomous improvement workflow to automatically run these processes:

```yaml
# .github/workflows/autonomous-improvement.yml
name: VOT1 Autonomous Improvement

on:
  schedule:
    - cron: '0 1 * * 1'  # Weekly on Monday at 1:00 AM UTC
  workflow_dispatch:
    inputs:
      components:
        description: 'Comma-separated list of components to improve'
        required: false

# ... rest of the workflow configuration
```

To run manually:
1. Go to "Actions" in your GitHub repository
2. Select "VOT1 Autonomous Improvement"
3. Click "Run workflow"
4. Optionally specify target components

## GitHub Bridge API

The `GitHubAppBridge` class provides these key methods:

```python
# Initialize the bridge
github_bridge = GitHubAppBridge(
    mcp=mcp,
    memory_manager=memory_manager,
    code_analyzer=code_analyzer,
    feedback_bridge=feedback_bridge,
    default_owner="username",
    default_repo="repository"
)

# Check connection
is_connected = await github_bridge.check_connection()

# Initiate connection
connection = await github_bridge.initiate_connection()

# Repository analysis
analysis = await github_bridge.analyze_repository(owner, repo)

# Create an issue
issue = await github_bridge.create_issue(title, body, owner, repo, labels, assignees)

# Create a pull request
pr = await github_bridge.create_pull_request(title, body, head, base, owner, repo, draft)

# Add PR comment
comment = await github_bridge.add_pr_comment(pr_number, body, owner, repo)

# Add PR review comment (on a specific line)
review = await github_bridge.add_pr_review_comment(pr_number, body, commit_id, path, line, owner, repo)

# Analyze a pull request
pr_analysis = await github_bridge.analyze_pull_request(pr_number, owner, repo, with_feedback=True)

# Star a repository
result = await github_bridge.star_repository(owner, repo)

# Create an improvement issue
improvement = await github_bridge.create_improvement_issue(component_path, analysis_result, owner, repo)
```

## Advanced Usage: Custom GitHub Workflows

You can extend the GitHub integration by creating custom workflows:

```python
import asyncio
from src.vot1.vot_mcp import VotModelControlProtocol
from src.vot1.github_app_bridge import GitHubAppBridge

async def custom_workflow():
    # Initialize MCP and GitHub bridge
    mcp = VotModelControlProtocol()
    github_bridge = GitHubAppBridge(mcp=mcp)
    
    # Check connection
    is_connected = await github_bridge.check_connection()
    if not is_connected:
        await github_bridge.initiate_connection()
    
    # Use MCP to generate improvement suggestions
    prompt = "Review this code and suggest improvements: ..."
    response = await mcp.process_request_async(prompt=prompt)
    
    # Create an issue with the suggestions
    await github_bridge.create_issue(
        title="Code Improvement Suggestions",
        body=response.get("content", ""),
        labels=["improvement"]
    )

if __name__ == "__main__":
    asyncio.run(custom_workflow())
```

## Troubleshooting

### Connection Issues

If you encounter connection problems:

1. Check if the connection is active:
   ```bash
   python -m scripts.init_github --check
   ```

2. Reinitialize the connection:
   ```bash
   python -m scripts.init_github
   ```

3. Verify environment variables:
   ```bash
   echo $GITHUB_OWNER
   echo $GITHUB_REPO
   ```

### API Rate Limits

GitHub enforces API rate limits. If you hit limits:

1. Wait for rate limit to reset (usually 1 hour)
2. Use authenticated requests (which have higher limits)
3. Consider implementing caching for frequently accessed data

### Insufficient Permissions

If you get permission errors:

1. Ensure your OAuth scope includes the required permissions
2. Check if your user has appropriate access to the repository
3. Reinitialize the connection with proper scopes

## Reference

### Command-Line Arguments

```
Available commands:
  analyze-repo            Analyze a GitHub repository
  analyze-pr              Analyze a GitHub pull request
  check-repo-health       Check repository health and generate report
  create-improvement-issue Create an issue with improvement suggestions
  run-autonomous-cycle    Run a complete autonomous improvement cycle

Global options:
  --owner                 Repository owner or organization
  --repo                  Repository name
  --no-prompt             Run without interactive prompts
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_OWNER` | Default repository owner/organization | None |
| `GITHUB_REPO` | Default repository name | None |
| `GITHUB_CONNECTION_ID` | GitHub connection ID | None |
| `VOT1_WORKSPACE_DIR` | Workspace directory for VOT1 | Current directory |

### API Response Structure

Most API methods return a dictionary with these common fields:

```json
{
  "success": true,          // Whether the operation was successful
  "error": "Error message", // Only present if success is false
  "url": "https://..."      // URL to the created resource (if applicable)
}
```

## Conclusion

This GitHub integration provides a powerful way to automate repository management and code improvement tasks directly using MCP's capabilities. By leveraging these tools, you can create autonomous improvement workflows that continuously enhance your codebase quality. 