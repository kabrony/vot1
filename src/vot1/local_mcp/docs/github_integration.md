# VOTai GitHub Integration

```
█████████████████████████████████
█▄─▄▄─█─▄▄─█─▄─▄─██▀▄─██▄─▄█
██─▄█▀█─██─███─████─▀─███─██
▀▄▄▄▄▄▀▄▄▄▄▀▀▄▄▄▀▀▄▄▀▄▄▀▄▄▄▀
```

A New Dawn of a Holistic Paradigm

## Overview

The VOTai GitHub Integration provides a seamless interface for interacting with GitHub repositories, issues, pull requests, and other GitHub APIs. This integration is a key component of the VOTai ecosystem, offering enhanced functionality for developers using GitHub as their source code repository.

## Features

- **Centralized API Access:** Unified interface for all GitHub-related operations
- **Intelligent Caching:** Automatic caching of responses to improve performance
- **Enhanced Error Handling:** Robust error handling and recovery mechanisms
- **Repository Analysis:** AI-powered analysis of repository structure and quality
- **Pull Request Analysis:** Detailed analysis of pull requests with improvement suggestions
- **VOTai Branding:** Consistent VOTai branding throughout the integration

## Usage

### Repository Analysis

The GitHub integration can analyze repositories to provide insights into their structure, dependencies, and code quality:

```python
result = github_integration.analyze_repository(
    owner="owner",
    repo="repo_name",
    depth="summary",  # Options: summary, detailed, comprehensive
    focus=["structure", "dependencies", "quality"]
)

if result.get("successful", False):
    analysis = result.get("analysis")
    print(analysis)
else:
    print(f"Error: {result.get('error')}")
```

### Pull Request Analysis

Analyze pull requests to get insights into code changes, quality, and potential issues:

```python
result = github_integration.analyze_pull_request(
    owner="owner",
    repo="repo_name",
    pr_number=123,
    focus=["code quality", "performance", "security"]
)

if result.get("successful", False):
    analysis = result.get("analysis")
    print(analysis)
else:
    print(f"Error: {result.get('error')}")
```

### Creating Issues

Create issues in GitHub repositories:

```python
result = github_integration.create_issue(
    owner="owner",
    repo="repo_name",
    title="Issue Title",
    body="Issue description here",
    labels=["bug", "high-priority"],
    assignees=["username"]
)

if result.get("successful", False):
    issue_data = result.get("data")
    print(f"Issue created: #{issue_data.get('number')}")
else:
    print(f"Error: {result.get('error')}")
```

### Creating Pull Requests

Create pull requests between branches:

```python
result = github_integration.create_pull_request(
    owner="owner",
    repo="repo_name",
    title="Pull Request Title",
    body="Description of changes",
    head="feature-branch",
    base="main",
    draft=False
)

if result.get("successful", False):
    pr_data = result.get("data")
    print(f"Pull request created: #{pr_data.get('number')}")
else:
    print(f"Error: {result.get('error')}")
```

## Status Page

The GitHub Integration includes a status page that provides real-time information about the GitHub service connection, configuration, and cache statistics. To access the status page, navigate to:

```
http://localhost:5678/github
```

The status page displays:
- Connection status
- API availability
- Configuration details
- Raw status response data

## API Endpoints

### GitHub Status API

Get detailed status information about the GitHub integration:

```
GET /api/github/status
```

Response:
```json
{
  "successful": true,
  "status": {
    "configured": true,
    "url": "https://mcp.github.anthropic.com/v1",
    "connection_active": true,
    "api_available": true,
    "timestamp": 1625097600
  }
}
```

### Cache Management

Clear the cache to refresh data:

```
POST /api/caches/clear
```

Response:
```json
{
  "successful": true,
  "message": "Cache cleared successfully",
  "stats": {
    "entries_before": 42,
    "hits": 156,
    "misses": 23
  },
  "entries_after": 0
}
```

## Configuration

The GitHub integration is configured through the main MCP configuration file `mcp.json`. Example configuration:

```json
{
  "mcp_servers": {
    "GITHUB": {
      "url": "https://mcp.github.anthropic.com/v1"
    }
  }
}
```

## VOTai Integration

The GitHub integration is fully integrated with the VOTai ecosystem, providing a consistent user experience and enhanced functionality. It utilizes the VOTai branding and follows the principles of the VOTai paradigm.

---

© VOTai - A New Dawn of a Holistic Paradigm 