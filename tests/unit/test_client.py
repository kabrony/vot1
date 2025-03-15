"""
Unit tests for the EnhancedClaudeClient class.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import pytest
import asyncio

from src.vot1 import EnhancedClaudeClient

class TestEnhancedClaudeClient(unittest.TestCase):
    """Test cases for the EnhancedClaudeClient class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock API key for testing
        self.api_key = "sk-ant-api03-mock-key"
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": self.api_key,
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    @patch('anthropic.Anthropic')
    def test_init(self, mock_anthropic):
        """Test client initialization."""
        # Arrange
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Act
        client = EnhancedClaudeClient()
        
        # Assert
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.model, "claude-3.7-sonnet-20240620")
        self.assertEqual(client.max_tokens, 1024)
        self.assertFalse(client.github_enabled)
        self.assertEqual(client.conversation_history, [])
        mock_anthropic.assert_called_once_with(api_key=self.api_key)
    
    @patch('anthropic.Anthropic')
    def test_init_custom_params(self, mock_anthropic):
        """Test client initialization with custom parameters."""
        # Arrange
        custom_api_key = "sk-ant-api03-custom-key"
        custom_model = "claude-3.7-opus-20240620"
        custom_max_tokens = 2048
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Act
        client = EnhancedClaudeClient(
            api_key=custom_api_key,
            model=custom_model,
            max_tokens=custom_max_tokens
        )
        
        # Assert
        self.assertEqual(client.api_key, custom_api_key)
        self.assertEqual(client.model, custom_model)
        self.assertEqual(client.max_tokens, custom_max_tokens)
        mock_anthropic.assert_called_once_with(api_key=custom_api_key)
    
    @patch('anthropic.Anthropic')
    def test_init_no_api_key(self, mock_anthropic):
        """Test client initialization with no API key."""
        # Arrange
        self.env_patcher.stop()  # Remove environment variable
        
        # Act & Assert
        with self.assertRaises(ValueError):
            EnhancedClaudeClient()
    
    @patch('anthropic.Anthropic')
    def test_send_message(self, mock_anthropic):
        """Test sending a message."""
        # Arrange
        mock_anthropic_instance = MagicMock()
        mock_messages = MagicMock()
        mock_anthropic_instance.messages = mock_messages
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Create a mock response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "This is a test response"
        mock_response.content = [mock_content]
        mock_response.model = "claude-3.7-sonnet-20240620"
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 5
        mock_response.usage = mock_usage
        
        mock_messages.create.return_value = mock_response
        
        # Act
        client = EnhancedClaudeClient()
        prompt = "Test prompt"
        response = client.send_message(prompt)
        
        # Assert
        mock_messages.create.assert_called_once()
        call_args = mock_messages.create.call_args[1]
        self.assertEqual(call_args["model"], "claude-3.7-sonnet-20240620")
        self.assertEqual(call_args["max_tokens"], 1024)
        self.assertAlmostEqual(call_args["temperature"], 0.7)
        self.assertIsNone(call_args["system"])
        self.assertEqual(call_args["messages"], [{"role": "user", "content": prompt}])
        
        self.assertEqual(response["content"], "This is a test response")
        self.assertEqual(response["model"], "claude-3.7-sonnet-20240620")
        self.assertEqual(response["usage"]["input_tokens"], 10)
        self.assertEqual(response["usage"]["output_tokens"], 5)
        
        # Check conversation history
        self.assertEqual(len(client.conversation_history), 2)
        self.assertEqual(client.conversation_history[0]["role"], "user")
        self.assertEqual(client.conversation_history[0]["content"], prompt)
        self.assertEqual(client.conversation_history[1]["role"], "assistant")
        self.assertEqual(client.conversation_history[1]["content"], "This is a test response")
    
    @patch('anthropic.Anthropic')
    def test_setup_github_integration(self, mock_anthropic):
        """Test setting up GitHub integration."""
        # Arrange
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        github_token = "github_token"
        github_repo = "test_repo"
        github_owner = "test_owner"
        
        # Act
        client = EnhancedClaudeClient()
        client.setup_github_integration(
            github_token=github_token,
            github_repo=github_repo,
            github_owner=github_owner
        )
        
        # Assert
        self.assertTrue(client.github_enabled)
        self.assertEqual(client.github_token, github_token)
        self.assertEqual(client.github_repo, github_repo)
        self.assertEqual(client.github_owner, github_owner)
    
    @patch('anthropic.Anthropic')
    def test_clear_conversation_history(self, mock_anthropic):
        """Test clearing conversation history."""
        # Arrange
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        # Act
        client = EnhancedClaudeClient()
        client.conversation_history = [
            {"role": "user", "content": "Test prompt"},
            {"role": "assistant", "content": "Test response"}
        ]
        client.clear_conversation_history()
        
        # Assert
        self.assertEqual(client.conversation_history, [])
    
    @patch('anthropic.Anthropic')
    def test_get_conversation_history(self, mock_anthropic):
        """Test getting conversation history."""
        # Arrange
        mock_anthropic_instance = MagicMock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        history = [
            {"role": "user", "content": "Test prompt"},
            {"role": "assistant", "content": "Test response"}
        ]
        
        # Act
        client = EnhancedClaudeClient()
        client.conversation_history = history.copy()
        result = client.get_conversation_history()
        
        # Assert
        # Check that the result is a copy, not the original
        self.assertEqual(result, history)
        self.assertIsNot(result, history)

# Async tests using pytest
@pytest.mark.asyncio
@patch('anthropic.Anthropic')
async def test_send_message_async(mock_anthropic):
    """Test sending a message asynchronously."""
    # Arrange
    mock_anthropic_instance = MagicMock()
    mock_messages = MagicMock()
    mock_anthropic_instance.messages = mock_messages
    mock_anthropic.return_value = mock_anthropic_instance
    
    # Create a mock response
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a test async response"
    mock_response.content = [mock_content]
    mock_response.model = "claude-3.7-sonnet-20240620"
    mock_usage = MagicMock()
    mock_usage.input_tokens = 10
    mock_usage.output_tokens = 5
    mock_response.usage = mock_usage
    
    mock_messages.create.return_value = mock_response
    
    # Act
    client = EnhancedClaudeClient()
    prompt = "Test async prompt"
    response = await client.send_message_async(prompt)
    
    # Assert
    mock_messages.create.assert_called_once()
    call_args = mock_messages.create.call_args[1]
    assert call_args["model"] == "claude-3.7-sonnet-20240620"
    assert call_args["messages"] == [{"role": "user", "content": prompt}]
    
    assert response["content"] == "This is a test async response"
    assert "timestamp" in response
    
    # Check conversation history
    assert len(client.conversation_history) == 2
    assert client.conversation_history[0]["role"] == "user"
    assert client.conversation_history[0]["content"] == prompt
    assert client.conversation_history[1]["role"] == "assistant"
    assert client.conversation_history[1]["content"] == "This is a test async response"

if __name__ == "__main__":
    unittest.main() 