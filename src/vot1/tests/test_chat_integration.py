#!/usr/bin/env python3
"""
Test script for the VOT1 Dashboard AI Chat Integration.
This script tests the chat API endpoints and functionality.
"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock
import asyncio

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.vot1.dashboard.api import (
    process_chat_message,
    get_chat_history,
    update_system_prompt,
    memory_search,
    visualization_command,
    process_with_mcp,
    get_system_prompt,
    get_memory_context,
    format_memory_references,
    extract_visualization_commands
)

class MockRequest:
    """Mock Flask request for testing API endpoints."""
    
    def __init__(self, json_data=None, args=None):
        self.json = json_data
        self.args = args if args else {}

class MockResponse:
    """Mock Flask response for testing API endpoints."""
    
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        
    def get_json(self):
        return self.data

class TestChatIntegration(unittest.TestCase):
    """Test cases for the VOT1 Dashboard AI Chat Integration."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Mock MCP and memory manager
        self.mcp_patcher = patch('src.vot1.dashboard.api.mcp')
        self.memory_manager_patcher = patch('src.vot1.dashboard.api.memory_manager')
        
        self.mock_mcp = self.mcp_patcher.start()
        self.mock_memory_manager = self.memory_manager_patcher.start()
        
        # Set up mock conversation store for testing
        from src.vot1.dashboard.api import conversation_store
        conversation_store.clear()
        conversation_store['test-conv'] = [
            {
                'role': 'user',
                'content': 'Hello',
                'timestamp': '2023-01-01T12:00:00'
            },
            {
                'role': 'assistant',
                'content': 'Hi there! How can I help you?',
                'timestamp': '2023-01-01T12:00:01',
                'memory_references': []
            }
        ]
    
    def tearDown(self):
        """Clean up after each test."""
        self.mcp_patcher.stop()
        self.memory_manager_patcher.stop()
    
    @patch('src.vot1.dashboard.api.jsonify')
    @patch('src.vot1.dashboard.api.request')
    def test_process_chat_message(self, mock_request, mock_jsonify):
        """Test the process_chat_message API endpoint."""
        # Setup mock request
        mock_request.json = {
            'message': 'What memories do I have about Python?',
            'conversation_id': 'test-conv',
            'include_memory_context': True
        }
        
        # Setup mock MCP response
        async def mock_process_async(**kwargs):
            return {
                'content': 'I found some memories about Python programming.',
                'memory_references': []
            }
        
        # Setup mock memory search
        self.mock_memory_manager.search_semantic_memory.return_value = [
            MagicMock(
                id='mem-123',
                content='Python is a programming language',
                metadata={'title': 'Python Language', 'type': 'concept'},
                score=0.92
            )
        ]
        
        # Setup mock MCP
        self.mock_mcp.process_request_async = mock_process_async
        
        # Call the function
        with patch('src.vot1.dashboard.api.asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = lambda x: asyncio.get_event_loop().run_until_complete(x)
            process_chat_message()
        
        # Check that jsonify was called with the expected response
        actual_args = mock_jsonify.call_args[0][0]
        
        # Verify response keys
        self.assertIn('response', actual_args)
        self.assertIn('conversation_id', actual_args)
        self.assertIn('message_id', actual_args)
        self.assertIn('memory_references', actual_args)
        
        # Verify response content
        self.assertEqual(actual_args['response'], 'I found some memories about Python programming.')
        self.assertEqual(actual_args['conversation_id'], 'test-conv')
    
    @patch('src.vot1.dashboard.api.jsonify')
    @patch('src.vot1.dashboard.api.request')
    def test_get_chat_history(self, mock_request, mock_jsonify):
        """Test the get_chat_history API endpoint."""
        # Setup mock request
        mock_request.args = {
            'conversation_id': 'test-conv',
            'limit': '10'
        }
        
        # Call the function
        get_chat_history()
        
        # Check that jsonify was called with the expected response
        actual_args = mock_jsonify.call_args[0][0]
        
        # Verify response keys
        self.assertIn('conversation_id', actual_args)
        self.assertIn('messages', actual_args)
        
        # Verify response content
        self.assertEqual(actual_args['conversation_id'], 'test-conv')
        self.assertEqual(len(actual_args['messages']), 2)
        self.assertEqual(actual_args['messages'][0]['content'], 'Hello')
        self.assertEqual(actual_args['messages'][1]['content'], 'Hi there! How can I help you?')
    
    @patch('src.vot1.dashboard.api.jsonify')
    @patch('src.vot1.dashboard.api.request')
    def test_update_system_prompt(self, mock_request, mock_jsonify):
        """Test the update_system_prompt API endpoint."""
        # Setup mock request
        mock_request.json = {
            'conversation_id': 'test-conv',
            'system_prompt': 'You are a helpful assistant that helps manage memories.'
        }
        
        # Call the function
        update_system_prompt()
        
        # Check that the system prompt was updated
        from src.vot1.dashboard.api import conversation_store
        self.assertEqual(
            conversation_store['test-conv_system_prompt'],
            'You are a helpful assistant that helps manage memories.'
        )
        
        # Check that jsonify was called with the expected response
        actual_args = mock_jsonify.call_args[0][0]
        
        # Verify response keys and content
        self.assertTrue(actual_args['success'])
        self.assertEqual(actual_args['conversation_id'], 'test-conv')
        self.assertEqual(
            actual_args['system_prompt'],
            'You are a helpful assistant that helps manage memories.'
        )
    
    @patch('src.vot1.dashboard.api.jsonify')
    @patch('src.vot1.dashboard.api.request')
    def test_memory_search(self, mock_request, mock_jsonify):
        """Test the memory_search API endpoint."""
        # Setup mock request
        mock_request.args = {
            'q': 'Python',
            'limit': '5'
        }
        
        # Setup mock memory search
        self.mock_memory_manager.search_semantic_memory.return_value = [
            MagicMock(
                id='mem-123',
                content='Python is a programming language',
                metadata={'title': 'Python Language', 'type': 'concept'},
                score=0.92
            ),
            MagicMock(
                id='mem-456',
                content='Python can be used for data science',
                metadata={'title': 'Python Data Science', 'type': 'fact'},
                score=0.85
            )
        ]
        
        # Call the function
        memory_search()
        
        # Check that jsonify was called with the expected response
        actual_args = mock_jsonify.call_args[0][0]
        
        # Verify response keys
        self.assertIn('query', actual_args)
        self.assertIn('results', actual_args)
        
        # Verify response content
        self.assertEqual(actual_args['query'], 'Python')
        self.assertEqual(len(actual_args['results']), 2)
        self.assertEqual(actual_args['results'][0]['id'], 'mem-123')
        self.assertEqual(actual_args['results'][1]['id'], 'mem-456')
    
    @patch('src.vot1.dashboard.api.jsonify')
    @patch('src.vot1.dashboard.api.request')
    def test_visualization_command(self, mock_request, mock_jsonify):
        """Test the visualization_command API endpoint."""
        # Setup mock request
        mock_request.json = {
            'command': 'focus',
            'params': {
                'query': 'Python'
            }
        }
        
        # Call the function
        visualization_command()
        
        # Check that jsonify was called with the expected response
        actual_args = mock_jsonify.call_args[0][0]
        
        # Verify response keys and content
        self.assertTrue(actual_args['success'])
        self.assertEqual(actual_args['command'], 'focus')
        self.assertEqual(actual_args['params'], {'query': 'Python'})
    
    def test_get_system_prompt(self):
        """Test the get_system_prompt helper function."""
        # Test without memory context
        prompt = get_system_prompt()
        
        # Verify it contains the expected sections
        self.assertIn('You are VOT1 Assistant', prompt)
        self.assertIn('Your capabilities include', prompt)
        self.assertIn('Guidelines', prompt)
        self.assertIn('Available visualization commands', prompt)
        
        # Test with memory context
        memory_context = {
            'items': [
                {
                    'id': 'mem-123',
                    'content': 'Python is a programming language',
                    'metadata': {'title': 'Python Language', 'type': 'concept'},
                    'score': 0.92
                }
            ]
        }
        
        prompt_with_context = get_system_prompt(memory_context)
        
        # Verify it contains the base prompt plus memory information
        self.assertIn('You are VOT1 Assistant', prompt_with_context)
        self.assertIn('I\'m providing you with relevant memories', prompt_with_context)
        self.assertIn('mem-123', prompt_with_context)
        self.assertIn('Python Language', prompt_with_context)
    
    def test_extract_visualization_commands(self):
        """Test the extract_visualization_commands helper function."""
        # Test with a command in the content
        content = "Here's what I found about Python. [VISUALIZATION:{\"command\":\"focus\",\"params\":{\"query\":\"Python\"}}]"
        
        command = extract_visualization_commands(content)
        
        # Verify the command was extracted
        self.assertEqual(command['command'], 'focus')
        self.assertEqual(command['params']['query'], 'Python')
        
        # Test with no command
        content = "Here's what I found about Python."
        
        command = extract_visualization_commands(content)
        
        # Verify no command was extracted
        self.assertIsNone(command)
        
        # Test with invalid JSON
        content = "Here's what I found about Python. [VISUALIZATION:invalid json]"
        
        command = extract_visualization_commands(content)
        
        # Verify no command was extracted due to invalid JSON
        self.assertIsNone(command)
    
    def test_format_memory_references(self):
        """Test the format_memory_references helper function."""
        # Test with memory context
        memory_context = {
            'items': [
                {
                    'id': 'mem-123',
                    'content': 'Python is a programming language',
                    'metadata': {'title': 'Python Language', 'type': 'concept'},
                    'score': 0.92
                },
                {
                    'id': 'mem-456',
                    'content': 'Python can be used for data science',
                    'metadata': {'title': 'Python Data Science', 'type': 'fact'},
                    'score': 0.85
                }
            ]
        }
        
        references = format_memory_references(memory_context)
        
        # Verify the references were formatted correctly
        self.assertEqual(len(references), 2)
        self.assertEqual(references[0]['id'], 'mem-123')
        self.assertEqual(references[0]['relevance'], 0.92)
        self.assertEqual(references[0]['summary'], 'Python Language')
        
        self.assertEqual(references[1]['id'], 'mem-456')
        self.assertEqual(references[1]['relevance'], 0.85)
        self.assertEqual(references[1]['summary'], 'Python Data Science')
        
        # Test with empty memory context
        references = format_memory_references(None)
        
        # Verify empty list is returned
        self.assertEqual(references, [])

if __name__ == '__main__':
    unittest.main() 