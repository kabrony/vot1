#!/usr/bin/env python3
"""
Tests for the VOT1 Development Feedback Bridge module.

This module contains tests for the development feedback bridge functionality,
ensuring it correctly analyzes code and provides helpful feedback.
"""

import os
import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.development_feedback_bridge import DevelopmentFeedbackBridge
from src.vot1.code_analyzer import CodeAnalyzer

# Reuse the sample code from the code analyzer tests
from test_code_analyzer import GOOD_PYTHON_CODE, BAD_PYTHON_CODE


@pytest.fixture
def temp_good_code_file(tmp_path):
    """Create a temporary file with good Python code."""
    file_path = tmp_path / "good_code.py"
    with open(file_path, "w") as f:
        f.write(GOOD_PYTHON_CODE)
    return file_path


@pytest.fixture
def temp_bad_code_file(tmp_path):
    """Create a temporary file with bad Python code."""
    file_path = tmp_path / "bad_code.py"
    with open(file_path, "w") as f:
        f.write(BAD_PYTHON_CODE)
    return file_path


@pytest.fixture
def mock_code_analyzer():
    """Create a mock code analyzer."""
    mock = MagicMock()
    # Mock analyze_code to return different results for good and bad code
    mock.analyze_code = AsyncMock()
    mock.calculate_quality_score = MagicMock()
    
    # Set up the mock to return different quality scores for good vs bad code
    def mock_analyze(file_path):
        if "good" in str(file_path):
            return {
                "file_path": file_path,
                "static_analysis": {"issues": []},
                "performance": {"issues": []},
                "security": {"issues": []},
                "documentation": {"issues": []},
                "complexity": {"issues": []},
                "memory_management": {"issues": []}
            }
        else:
            return {
                "file_path": file_path,
                "static_analysis": {"issues": [
                    {"severity": "high", "message": "Test issue", "suggestion": "Fix it"}
                ]},
                "performance": {"issues": []},
                "security": {"issues": [
                    {"severity": "critical", "message": "Security issue", "suggestion": "Fix it urgently"}
                ]},
                "documentation": {"issues": []},
                "complexity": {"issues": []},
                "memory_management": {"issues": []}
            }
    
    def mock_quality_score(analysis):
        if "issues" in analysis.get("static_analysis", {}) and len(analysis["static_analysis"]["issues"]) > 0:
            return 0.6  # Bad code
        return 0.9  # Good code
    
    mock.analyze_code.side_effect = mock_analyze
    mock.calculate_quality_score.side_effect = mock_quality_score
    
    return mock


@pytest.fixture
def mock_mcp():
    """Create a mock MCP."""
    mock = MagicMock()
    mock.process_request_async = AsyncMock()
    mock.process_request_async.return_value = {"content": "Mock feedback content"}
    mock.process_github_request = AsyncMock()
    mock.process_github_request.return_value = {"content": "[]"}
    return mock


@pytest.fixture
def mock_memory_manager():
    """Create a mock memory manager."""
    mock = MagicMock()
    mock.add_semantic_memory = MagicMock()
    return mock


@pytest.fixture
def mock_owl_engine():
    """Create a mock OWL reasoning engine."""
    mock = MagicMock()
    mock.reason = MagicMock()
    mock.reason.return_value = {"reasoning": "Test reasoning"}
    return mock


class TestDevelopmentFeedbackBridge:
    """Tests for the DevelopmentFeedbackBridge class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_code_analyzer, mock_mcp, mock_memory_manager, mock_owl_engine, tmp_path):
        """Test the initialization of the bridge."""
        bridge = DevelopmentFeedbackBridge(
            mcp=mock_mcp,
            code_analyzer=mock_code_analyzer,
            memory_manager=mock_memory_manager,
            owl_engine=mock_owl_engine,
            workspace_dir=str(tmp_path),
            feedback_threshold=0.7,
            auto_suggestions=True,
            store_feedback_history=True
        )
        
        assert bridge.mcp == mock_mcp
        assert bridge.code_analyzer == mock_code_analyzer
        assert bridge.memory_manager == mock_memory_manager
        assert bridge.owl_engine == mock_owl_engine
        assert bridge.workspace_dir == tmp_path
        assert bridge.feedback_threshold == 0.7
        assert bridge.auto_suggestions is True
        assert bridge.store_feedback_history is True
        assert isinstance(bridge.feedback_history, dict)
        assert len(bridge.monitored_components) == 0
        assert "on_quality_issue" in bridge.callbacks
    
    @pytest.mark.asyncio
    async def test_analyze_file_good_code(self, mock_code_analyzer, mock_mcp, tmp_path, temp_good_code_file):
        """Test analyzing a file with good code."""
        bridge = DevelopmentFeedbackBridge(
            mcp=mock_mcp,
            code_analyzer=mock_code_analyzer,
            workspace_dir=str(tmp_path),
            feedback_threshold=0.7  # Set threshold to generate feedback only for code below this score
        )
        
        result = await bridge.analyze_file_on_save(str(temp_good_code_file))
        
        # Assert that the code analyzer was called
        mock_code_analyzer.analyze_code.assert_called_once()
        mock_code_analyzer.calculate_quality_score.assert_called_once()
        
        # Good code should be above threshold (0.9 > 0.7)
        assert result["quality_score"] == 0.9
        assert result["feedback"] is None
        assert result["improvement_suggestions"] is None
        
        # The result should be stored in feedback history
        assert temp_good_code_file.name in bridge.feedback_history
    
    @pytest.mark.asyncio
    async def test_analyze_file_bad_code(self, mock_code_analyzer, mock_mcp, tmp_path, temp_bad_code_file):
        """Test analyzing a file with bad code."""
        # Mock the _generate_feedback and _generate_improvement_suggestions methods
        with patch.object(DevelopmentFeedbackBridge, '_generate_feedback', new_callable=AsyncMock) as mock_generate_feedback, \
             patch.object(DevelopmentFeedbackBridge, '_generate_improvement_suggestions', new_callable=AsyncMock) as mock_generate_suggestions, \
             patch.object(DevelopmentFeedbackBridge, '_store_feedback_in_memory') as mock_store_feedback:
            
            # Set the return values for the mocked methods
            mock_generate_feedback.return_value = "Sample feedback for bad code"
            mock_generate_suggestions.return_value = [{"issue": "Sample issue", "suggestion": "Sample suggestion"}]
            
            bridge = DevelopmentFeedbackBridge(
                mcp=mock_mcp,
                code_analyzer=mock_code_analyzer,
                workspace_dir=str(tmp_path),
                feedback_threshold=0.7  # Set threshold so bad code (0.6) triggers feedback
            )
            
            # Register a callback for testing
            callback_called = False
            file_with_issue = None
            
            async def quality_issue_callback(file_path, analysis, score):
                nonlocal callback_called, file_with_issue
                callback_called = True
                file_with_issue = file_path
            
            await bridge.register_callback("on_quality_issue", quality_issue_callback)
            
            # Analyze the bad code file
            result = await bridge.analyze_file_on_save(str(temp_bad_code_file))
            
            # Assert the code analyzer was called
            mock_code_analyzer.analyze_code.assert_called_once()
            mock_code_analyzer.calculate_quality_score.assert_called_once()
            
            # Bad code should be below threshold (0.6 < 0.7)
            assert result["quality_score"] == 0.6
            assert result["feedback"] == "Sample feedback for bad code"
            assert len(result["improvement_suggestions"]) == 1
            
            # The feedback generators should have been called
            mock_generate_feedback.assert_called_once()
            mock_generate_suggestions.assert_called_once()
            
            # The callback should have been triggered
            assert callback_called is True
            assert file_with_issue == temp_bad_code_file.name
            
            # The result should be stored in feedback history
            assert temp_bad_code_file.name in bridge.feedback_history
            
            # The feedback should be stored in memory
            mock_store_feedback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_feedback_no_mcp(self, mock_code_analyzer, tmp_path):
        """Test generating feedback without MCP."""
        bridge = DevelopmentFeedbackBridge(
            code_analyzer=mock_code_analyzer,
            workspace_dir=str(tmp_path),
            mcp=None  # No MCP, should use simple feedback generation
        )
        
        analysis = {
            "static_analysis": {
                "issues": [
                    {"severity": "high", "message": "Issue 1", "suggestion": "Fix 1"}
                ]
            },
            "security": {
                "issues": [
                    {"severity": "critical", "message": "Security issue", "suggestion": "Fix urgently"}
                ]
            },
            "performance": {"issues": []},
            "documentation": {"issues": []},
            "complexity": {"issues": []},
            "memory_management": {"issues": []}
        }
        
        feedback = await bridge._generate_feedback(analysis, "test_file.py")
        
        # Simple feedback should contain the issues
        assert "Code quality issues found:" in feedback
        assert "HIGH: Issue 1 - Fix 1" in feedback
        assert "CRITICAL: Security issue - Fix urgently" in feedback
    
    @pytest.mark.asyncio
    async def test_generate_feedback_with_mcp(self, mock_code_analyzer, mock_mcp, tmp_path):
        """Test generating feedback with MCP."""
        # Set up specific MCP response
        mock_mcp.process_request_async.return_value = {
            "content": "# Code Quality Feedback\n\nYour code has some issues that should be addressed."
        }
        
        bridge = DevelopmentFeedbackBridge(
            code_analyzer=mock_code_analyzer,
            mcp=mock_mcp,
            workspace_dir=str(tmp_path)
        )
        
        analysis = {
            "static_analysis": {"issues": [{"severity": "high", "message": "Test issue"}]},
            "performance": {"issues": []},
            "security": {"issues": []},
            "documentation": {"issues": []},
            "complexity": {"issues": []},
            "memory_management": {"issues": []}
        }
        
        feedback = await bridge._generate_feedback(analysis, "test_file.py")
        
        # MCP should have been called with the right parameters
        mock_mcp.process_request_async.assert_called_once()
        call_args = mock_mcp.process_request_async.call_args[1]
        
        assert "prompt" in call_args
        assert "system" in call_args
        assert "context" in call_args
        assert "test_file.py" in call_args["prompt"]
        
        # The feedback should match the MCP response
        assert feedback == "# Code Quality Feedback\n\nYour code has some issues that should be addressed."
    
    @pytest.mark.asyncio
    async def test_register_callback(self, mock_code_analyzer, tmp_path):
        """Test registering callbacks for events."""
        bridge = DevelopmentFeedbackBridge(
            code_analyzer=mock_code_analyzer,
            workspace_dir=str(tmp_path)
        )
        
        # Test registering a valid callback
        mock_callback = AsyncMock()
        result = await bridge.register_callback("on_quality_issue", mock_callback)
        assert result is True
        assert mock_callback in bridge.callbacks["on_quality_issue"]
        
        # Test registering an invalid callback type
        result = await bridge.register_callback("invalid_event_type", mock_callback)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_relative_path_conversion(self, mock_code_analyzer, tmp_path):
        """Test converting between absolute and relative paths."""
        bridge = DevelopmentFeedbackBridge(
            code_analyzer=mock_code_analyzer,
            workspace_dir=str(tmp_path)
        )
        
        # Create a file in the workspace
        test_file = tmp_path / "test_dir" / "test_file.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.touch()
        
        # Convert absolute path to relative
        relative_path = bridge._get_relative_path(str(test_file))
        assert relative_path == os.path.join("test_dir", "test_file.py")
        
        # Test with a path outside the workspace
        outside_path = "/tmp/outside_workspace.py"
        result_path = bridge._get_relative_path(outside_path)
        assert result_path == outside_path  # Should return the original path
    
    @pytest.mark.asyncio
    async def test_store_feedback_in_memory(self, mock_code_analyzer, mock_memory_manager, tmp_path):
        """Test storing feedback in memory."""
        bridge = DevelopmentFeedbackBridge(
            code_analyzer=mock_code_analyzer,
            memory_manager=mock_memory_manager,
            workspace_dir=str(tmp_path)
        )
        
        file_path = "test_file.py"
        quality_score = 0.65
        feedback = "Sample feedback for the test file"
        suggestions = [
            {"issue": "Test issue", "suggestion": "Test suggestion"}
        ]
        
        bridge._store_feedback_in_memory(file_path, quality_score, feedback, suggestions)
        
        # The memory manager should have been called with appropriate content
        mock_memory_manager.add_semantic_memory.assert_called_once()
        
        # Check that the metadata is correct
        call_args = mock_memory_manager.add_semantic_memory.call_args[1]
        assert "metadata" in call_args
        assert call_args["metadata"]["type"] == "code_feedback"
        assert call_args["metadata"]["file_path"] == file_path
        assert call_args["metadata"]["quality_score"] == quality_score
        
        # Check that the content includes the feedback and suggestions
        assert "content" in call_args
        assert feedback in call_args["content"]
        assert json.dumps(suggestions) in call_args["content"]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 