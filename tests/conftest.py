"""
Pytest configuration file with fixtures for VOT1 testing.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables for testing."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "sk-ant-api03-mock-key-for-testing",
        "GITHUB_TOKEN": "github_mock_token",
        "GITHUB_REPO": "mock_repo",
        "GITHUB_OWNER": "mock_owner",
        "PERPLEXITY_API_KEY": "mock_perplexity_key"
    }):
        yield

@pytest.fixture
def mock_anthropic():
    """Fixture to mock the Anthropic client."""
    with patch('anthropic.Anthropic') as mock:
        mock_client = MagicMock()
        mock_messages = MagicMock()
        
        # Set up mock response
        mock_content = MagicMock()
        mock_content.text = "This is a mock response from Claude"
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.model = "claude-3.7-sonnet-20240620"
        mock_usage = MagicMock()
        mock_usage.input_tokens = 15
        mock_usage.output_tokens = 25
        mock_response.usage = mock_usage
        
        mock_messages.create.return_value = mock_response
        mock_client.messages = mock_messages
        
        mock.return_value = mock_client
        yield mock

@pytest.fixture
def mock_requests():
    """Fixture to mock HTTP requests."""
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        # Configure mock response for Perplexity
        mock_perplexity_response = MagicMock()
        mock_perplexity_response.status_code = 200
        mock_perplexity_response.json.return_value = {
            "answer": "This is a mock web search result",
            "query": "mock query"
        }
        mock_post.return_value = mock_perplexity_response
        
        # Configure mock response for GitHub
        mock_github_response = MagicMock()
        mock_github_response.status_code = 201
        mock_github_response.json.return_value = {
            "html_url": "https://github.com/mock_owner/mock_repo/issues/1",
            "number": 1,
            "title": "Mock Issue"
        }
        mock_get.return_value = mock_github_response
        
        yield {
            "post": mock_post,
            "get": mock_get
        }

@pytest.fixture
def mock_aiohttp():
    """Fixture to mock aiohttp for async HTTP requests."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_json = MagicMock()
        mock_json.return_value = {
            "answer": "This is a mock async web search result",
            "query": "mock async query"
        }
        mock_response.json = mock_json
        mock_response.status = 200
        
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = mock_response
        
        mock_post = MagicMock()
        mock_post.return_value = mock_context
        
        mock_session_instance = MagicMock()
        mock_session_instance.post = mock_post
        
        mock_session_context = MagicMock()
        mock_session_context.__aenter__.return_value = mock_session_instance
        mock_session.return_value = mock_session_context
        
        yield mock_session 