#!/usr/bin/env python3
"""
Tests for the VOT1 Code Analyzer module.

This module contains tests for the code analyzer functionality,
ensuring it correctly identifies code quality issues.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.code_analyzer import CodeAnalyzer, create_analyzer

# Sample code for testing
GOOD_PYTHON_CODE = """#!/usr/bin/env python3
\"\"\"
Sample module with good code quality.
\"\"\"

def calculate_sum(a, b):
    \"\"\"
    Calculate the sum of two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    \"\"\"
    return a + b

class Calculator:
    \"\"\"A simple calculator class.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the calculator.\"\"\"
        self.history = []
    
    def add(self, a, b):
        \"\"\"Add two numbers and store in history.\"\"\"
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
"""

BAD_PYTHON_CODE = """
# No module docstring

def calculate_sum(a, b):
    return a + b  # No docstring

def complex_function(data):
    # Deeply nested code
    result = []
    for item in data:
        if item > 0:
            for subitem in item:
                if subitem < 10:
                    if isinstance(subitem, int):
                        if subitem % 2 == 0:
                            result.append(subitem)
    return result

password = "hardcoded_secret"  # Security issue

file = open("test.txt", "r")  # Resource leak
data = file.read()

# Large data structure literal
large_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
              21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]

# Repeated function calls
result1 = calculate_sum(1, 2)
result2 = calculate_sum(3, 4)
result3 = calculate_sum(5, 6)
result4 = calculate_sum(7, 8)
result5 = calculate_sum(9, 10)
result6 = calculate_sum(11, 12)
"""

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
def mock_mcp():
    """Create a mock MCP for testing."""
    mock = MagicMock()
    mock.process_request_async = MagicMock()
    mock.process_request_async.return_value = {"content": '{"issues": []}'}
    return mock

@pytest.fixture
def mock_owl_engine():
    """Create a mock OWL reasoning engine for testing."""
    mock = MagicMock()
    mock.reason = MagicMock()
    mock.reason.return_value = {"reasoning": "Test reasoning"}
    return mock

class TestCodeAnalyzer:
    """Tests for the CodeAnalyzer class."""
    
    @pytest.mark.asyncio
    async def test_create_analyzer(self, mock_mcp, mock_owl_engine, tmp_path):
        """Test the create_analyzer factory function."""
        analyzer = create_analyzer(
            mcp=mock_mcp, 
            owl_engine=mock_owl_engine, 
            workspace_dir=str(tmp_path)
        )
        
        assert isinstance(analyzer, CodeAnalyzer)
        assert analyzer.mcp == mock_mcp
        assert analyzer.owl_engine == mock_owl_engine
        assert analyzer.workspace_dir == tmp_path
    
    @pytest.mark.asyncio
    async def test_static_analysis_good_code(self, temp_good_code_file, mock_mcp, mock_owl_engine):
        """Test static analysis on good quality code."""
        # Create analyzer with the temp file's directory as workspace
        workspace_dir = temp_good_code_file.parent
        analyzer = CodeAnalyzer(
            mcp=mock_mcp,
            owl_engine=mock_owl_engine,
            workspace_dir=str(workspace_dir)
        )
        
        # Get relative path for the file
        relative_path = temp_good_code_file.name
        
        # Run static analysis
        analysis = analyzer._perform_static_analysis(GOOD_PYTHON_CODE, relative_path)
        
        # Check results
        assert "issues" in analysis
        assert "stats" in analysis
        assert analysis["stats"]["lines_of_code"] > 0
        assert analysis["stats"]["comment_lines"] > 0
        
        # Good code should have few or no issues
        assert len(analysis["issues"]) <= 1  # Might find print statements or TODOs
    
    @pytest.mark.asyncio
    async def test_static_analysis_bad_code(self, temp_bad_code_file, mock_mcp, mock_owl_engine):
        """Test static analysis on poor quality code."""
        # Create analyzer with the temp file's directory as workspace
        workspace_dir = temp_bad_code_file.parent
        analyzer = CodeAnalyzer(
            mcp=mock_mcp,
            owl_engine=mock_owl_engine,
            workspace_dir=str(workspace_dir)
        )
        
        # Get relative path for the file
        relative_path = temp_bad_code_file.name
        
        # Run static analysis
        analysis = analyzer._perform_static_analysis(BAD_PYTHON_CODE, relative_path)
        
        # Check results
        assert "issues" in analysis
        assert "stats" in analysis
        
        # Bad code should have multiple issues
        assert len(analysis["issues"]) > 0
    
    @pytest.mark.asyncio
    async def test_documentation_gaps(self, temp_good_code_file, temp_bad_code_file, mock_mcp, mock_owl_engine):
        """Test documentation gap detection."""
        # Create analyzer with the temp files' directory as workspace
        workspace_dir = temp_good_code_file.parent
        analyzer = CodeAnalyzer(
            mcp=mock_mcp,
            owl_engine=mock_owl_engine,
            workspace_dir=str(workspace_dir)
        )
        
        # Check good code
        good_issues = analyzer._check_documentation_gaps(GOOD_PYTHON_CODE, "good_code.py")
        
        # Check bad code
        bad_issues = analyzer._check_documentation_gaps(BAD_PYTHON_CODE, "bad_code.py")
        
        # Good code should have fewer documentation issues than bad code
        assert len(good_issues["issues"]) < len(bad_issues["issues"])
        
        # Bad code should have a missing module docstring issue
        assert any(issue["type"] == "missing_module_docstring" for issue in bad_issues["issues"])
    
    @pytest.mark.asyncio
    async def test_calculate_quality_score(self, mock_mcp, mock_owl_engine, tmp_path):
        """Test quality score calculation."""
        analyzer = CodeAnalyzer(
            mcp=mock_mcp,
            owl_engine=mock_owl_engine,
            workspace_dir=str(tmp_path)
        )
        
        # Create a mock analysis result with various issues
        analysis_result = {
            "static_analysis": {
                "issues": [
                    {"severity": "critical"},
                    {"severity": "high"},
                    {"severity": "medium"},
                    {"severity": "low"},
                ]
            },
            "performance": {"issues": []},
            "security": {"issues": []},
            "documentation": {"issues": []},
            "complexity": {"issues": []},
            "memory_management": {"issues": []}
        }
        
        # Calculate score
        score = analyzer.calculate_quality_score(analysis_result)
        
        # Score should be less than 1.0 due to issues
        assert score < 1.0
        
        # Create a mock analysis result with no issues
        perfect_analysis = {
            "static_analysis": {"issues": []},
            "performance": {"issues": []},
            "security": {"issues": []},
            "documentation": {"issues": []},
            "complexity": {"issues": []},
            "memory_management": {"issues": []}
        }
        
        # Calculate score
        perfect_score = analyzer.calculate_quality_score(perfect_analysis)
        
        # Score should be 1.0 for perfect code
        assert perfect_score == 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_code_integration(self, temp_good_code_file, mock_mcp, mock_owl_engine):
        """Test the full analyze_code method."""
        # Setup mock responses
        mock_mcp.process_request_async.return_value = {
            "content": '{"overall_quality": "high", "strengths": ["Good documentation"], "issues": [], "recommendations": []}'
        }
        
        # Create analyzer
        workspace_dir = temp_good_code_file.parent
        analyzer = CodeAnalyzer(
            mcp=mock_mcp,
            owl_engine=mock_owl_engine,
            workspace_dir=str(workspace_dir)
        )
        
        # Get relative path for the file
        relative_path = temp_good_code_file.name
        
        # Run analysis
        with patch.object(analyzer, '_check_performance', return_value={"issues": []}), \
             patch.object(analyzer, '_check_security_vulnerabilities', return_value={"issues": []}), \
             patch.object(analyzer, '_check_memory_management', return_value={"issues": []}):
            result = await analyzer.analyze_code(relative_path)
        
        # Check results
        assert "file_path" in result
        assert "static_analysis" in result
        assert "performance" in result
        assert "security" in result
        assert "documentation" in result
        assert "complexity" in result
        assert "memory_management" in result
        assert "total_issues" in result
        
        # Quality score should be calculated
        score = analyzer.calculate_quality_score(result)
        assert 0 <= score <= 1.0


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 