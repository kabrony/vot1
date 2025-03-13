#!/usr/bin/env python3
"""
Unit tests for GitHub webhook and workflow functionality.
"""

import os
import sys
import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.github_update_automation import GitHubUpdateAutomation
from src.vot1.github_composio_bridge import GitHubComposioBridge


@pytest.fixture
def github_automation():
    """Create a GitHubUpdateAutomation instance with mocked dependencies."""
    with patch('scripts.github_update_automation.VotModelControlProtocol') as mock_vot_mcp, \
         patch('scripts.github_update_automation.GitHubComposioBridge') as mock_bridge, \
         patch('scripts.github_update_automation.MemoryManager') as mock_memory_manager:
         
        mock_bridge_instance = AsyncMock()
        mock_vot_mcp.return_value.github_bridge = mock_bridge_instance
        mock_bridge.return_value = mock_bridge_instance
        
        # Create automation instance with test configuration
        automation = GitHubUpdateAutomation(
            primary_model="anthropic/claude-3-7-sonnet-20240620",
            secondary_model="anthropic/claude-3-5-sonnet-20240620",
            max_thinking_tokens=1000,
            memory_path="./test_memory",
            github_token="mock_gh_token",
            use_composio=True,
            use_perplexity=False
        )
        
        # Replace github_bridge with mock
        automation.github_bridge = mock_bridge_instance
        
        yield automation


@pytest.mark.asyncio
async def test_create_webhook(github_automation):
    """Test creating a webhook."""
    # Setup mock return value
    webhook_response = {
        "id": 12345678,
        "url": "https://api.github.com/repos/owner/repo/hooks/12345678",
        "test_url": "https://api.github.com/repos/owner/repo/hooks/12345678/test",
        "ping_url": "https://api.github.com/repos/owner/repo/hooks/12345678/pings",
        "name": "web",
        "events": ["push", "pull_request"],
        "active": True,
        "config": {
            "url": "https://example.com/webhook",
            "content_type": "json",
            "insecure_ssl": "0",
            "secret": "********"
        },
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }
    
    github_automation.github_bridge.create_webhook.return_value = {
        "success": True,
        "webhook": webhook_response
    }
    
    # Call the method
    result = await github_automation.create_webhook(
        owner="owner",
        repo="repo",
        webhook_url="https://example.com/webhook",
        events=["push", "pull_request"],
        secret="webhook_secret"
    )
    
    # Assert
    assert result["success"] is True
    assert result["webhook"]["id"] == 12345678
    assert result["webhook"]["events"] == ["push", "pull_request"]
    
    # Check the correct payload was sent
    github_automation.github_bridge.create_webhook.assert_called_once()
    args, kwargs = github_automation.github_bridge.create_webhook.call_args
    assert kwargs["owner"] == "owner"
    assert kwargs["repo"] == "repo"
    
    # Verify webhook payload
    payload = kwargs["webhook_payload"]
    assert payload["name"] == "web"
    assert payload["config"]["url"] == "https://example.com/webhook"
    assert payload["config"]["content_type"] == "json"
    assert payload["config"]["secret"] == "webhook_secret"
    assert payload["events"] == ["push", "pull_request"]
    assert payload["active"] is True


@pytest.mark.asyncio
async def test_list_workflows(github_automation):
    """Test listing workflows."""
    # Setup mock return value
    workflows_response = {
        "total_count": 2,
        "workflows": [
            {
                "id": 12345,
                "node_id": "MDg6V29ya2Zsb3cxMjM0NQ==",
                "name": "CI",
                "path": ".github/workflows/ci.yml",
                "state": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "url": "https://api.github.com/repos/owner/repo/actions/workflows/12345",
                "html_url": "https://github.com/owner/repo/actions/workflows/ci.yml",
                "badge_url": "https://github.com/owner/repo/workflows/CI/badge.svg"
            },
            {
                "id": 67890,
                "node_id": "MDg6V29ya2Zsb3c2Nzg5MA==",
                "name": "Release",
                "path": ".github/workflows/release.yml",
                "state": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "url": "https://api.github.com/repos/owner/repo/actions/workflows/67890",
                "html_url": "https://github.com/owner/repo/actions/workflows/release.yml",
                "badge_url": "https://github.com/owner/repo/workflows/Release/badge.svg"
            }
        ]
    }
    
    github_automation.github_bridge.list_workflows.return_value = {
        "success": True,
        "workflows": workflows_response["workflows"]
    }
    
    # Call the method
    result = await github_automation.list_workflows("owner", "repo")
    
    # Assert
    assert result["success"] is True
    assert len(result["workflows"]) == 2
    assert result["workflows"][0]["name"] == "CI"
    assert result["workflows"][1]["name"] == "Release"
    
    # Check the correct parameters were sent
    github_automation.github_bridge.list_workflows.assert_called_once_with(
        owner="owner", repo="repo"
    )


@pytest.mark.asyncio
async def test_create_or_update_workflow(github_automation):
    """Test creating a workflow."""
    # Setup mock for directory check and creation
    github_automation._directory_exists = AsyncMock(return_value=False)
    github_automation._create_directory_if_needed = AsyncMock(return_value={"success": True})
    
    # Setup mock return value for file creation
    github_automation.github_bridge._make_github_api_request = AsyncMock(return_value={
        "content": {
            "name": "ci.yml",
            "path": ".github/workflows/ci.yml",
            "sha": "abc123",
            "size": 1234,
            "url": "https://api.github.com/repos/owner/repo/contents/.github/workflows/ci.yml",
            "html_url": "https://github.com/owner/repo/blob/main/.github/workflows/ci.yml",
            "git_url": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
            "download_url": "https://raw.githubusercontent.com/owner/repo/main/.github/workflows/ci.yml",
            "type": "file",
            "content": "encoded-content==",
            "encoding": "base64",
            "_links": {
                "self": "https://api.github.com/repos/owner/repo/contents/.github/workflows/ci.yml",
                "git": "https://api.github.com/repos/owner/repo/git/blobs/abc123",
                "html": "https://github.com/owner/repo/blob/main/.github/workflows/ci.yml"
            }
        }
    })
    
    workflow_content = """name: CI
on:
  push:
    branches: [ main ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: echo "Running tests"
"""
    
    # Call the method
    result = await github_automation.create_or_update_workflow(
        owner="owner",
        repo="repo",
        workflow_path=".github/workflows/ci.yml",
        workflow_content=workflow_content,
        commit_message="Add CI workflow"
    )
    
    # Assert
    assert result["success"] is True
    
    # Check the correct path was checked and created
    github_automation._directory_exists.assert_called_once_with(
        owner="owner", repo="repo", path=".github/workflows"
    )
    github_automation._create_directory_if_needed.assert_called_once_with(
        owner="owner", repo="repo", path=".github/workflows"
    )


@pytest.mark.asyncio
async def test_trigger_workflow(github_automation):
    """Test triggering a workflow."""
    # Setup mock return value
    trigger_response = {
        "id": 4242424242,
        "repository": {
            "id": 1234567,
            "name": "repo",
            "full_name": "owner/repo"
        },
        "status": "queued"
    }
    
    github_automation.github_bridge.dispatch_workflow.return_value = {
        "success": True,
        "workflow_run": trigger_response
    }
    
    # Call the method
    result = await github_automation.trigger_workflow(
        owner="owner",
        repo="repo",
        workflow_id="12345",
        ref="main",
        inputs={"param1": "value1"}
    )
    
    # Assert
    assert result["success"] is True
    assert result["workflow_run"]["status"] == "queued"
    
    # Check the correct payload was sent
    github_automation.github_bridge.dispatch_workflow.assert_called_once()
    args, kwargs = github_automation.github_bridge.dispatch_workflow.call_args
    assert kwargs["owner"] == "owner"
    assert kwargs["repo"] == "repo"
    assert kwargs["workflow_id"] == "12345"
    
    # Verify dispatch payload
    payload = kwargs["payload"]
    assert payload["ref"] == "main"
    assert payload["inputs"] == {"param1": "value1"}


@pytest.mark.asyncio
async def test_github_bridge_create_webhook():
    """Test GitHubComposioBridge create_webhook method."""
    with patch('src.vot1.github_composio_bridge.VotModelControlProtocol') as mock_vot_mcp:
        mock_process = AsyncMock()
        mock_process.return_value = {
            "id": 12345678,
            "active": True,
            "events": ["push", "pull_request"]
        }
        mock_vot_mcp.return_value.process = mock_process
        
        bridge = GitHubComposioBridge(
            mcp=mock_vot_mcp.return_value,
            github_token="mock_token"
        )
        
        result = await bridge.create_webhook(
            owner="owner",
            repo="repo",
            webhook_payload={
                "name": "web",
                "config": {
                    "url": "https://example.com/webhook",
                    "content_type": "json"
                },
                "events": ["push", "pull_request"]
            }
        )
        
        assert result["success"] is True
        assert result["webhook"]["id"] == 12345678
        
        # Verify the API call
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert kwargs["method"] == "POST"
        assert kwargs["url"] == "repos/owner/repo/hooks"
        assert "data" in kwargs


@pytest.mark.asyncio
async def test_github_bridge_list_workflows():
    """Test GitHubComposioBridge list_workflows method."""
    with patch('src.vot1.github_composio_bridge.VotModelControlProtocol') as mock_vot_mcp:
        mock_process = AsyncMock()
        mock_process.return_value = {
            "total_count": 1,
            "workflows": [{
                "id": 12345,
                "name": "CI",
                "path": ".github/workflows/ci.yml"
            }]
        }
        mock_vot_mcp.return_value.process = mock_process
        
        bridge = GitHubComposioBridge(
            mcp=mock_vot_mcp.return_value,
            github_token="mock_token"
        )
        
        result = await bridge.list_workflows(
            owner="owner",
            repo="repo"
        )
        
        assert result["success"] is True
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["name"] == "CI"
        
        # Verify the API call
        mock_process.assert_called_once()
        args, kwargs = mock_process.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "repos/owner/repo/actions/workflows"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 