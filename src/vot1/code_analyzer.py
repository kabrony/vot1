#!/usr/bin/env python3
"""
VOT1 Code Analyzer

This module provides advanced code analysis capabilities for the VOT1 system,
enabling AI-powered static analysis, performance optimization suggestions,
security vulnerability detection, and code quality assessment.

Key features:
1. Multi-dimensional code quality analysis
2. Security vulnerability scanning
3. Performance optimization suggestions
4. Documentation completeness checking
5. Complexity analysis
6. Memory leak detection
"""

import os
import re
import logging
import ast
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Comprehensive code analysis tool with AI-powered capabilities.
    
    This class analyzes code for quality issues, security vulnerabilities,
    performance problems, and other potential improvements.
    """
    
    def __init__(
        self,
        mcp=None,
        owl_engine=None,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize the code analyzer.
        
        Args:
            mcp: VOT Model Control Protocol instance for AI analysis
            owl_engine: OWL reasoning engine for semantic analysis
            workspace_dir: Root directory of the workspace
        """
        self.mcp = mcp
        self.owl_engine = owl_engine
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        logger.info(f"Initialized CodeAnalyzer with workspace at {self.workspace_dir}")
    
    async def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze code file comprehensively.
        
        Args:
            file_path: Path to the code file to analyze
        
        Returns:
            Dictionary with analysis results
        """
        full_path = self.workspace_dir / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read the file
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Perform static analysis
        static_analysis = self._perform_static_analysis(content, file_path)
        
        # Performance analysis
        performance_issues = await self._check_performance(content, file_path)
        
        # Security analysis
        security_issues = await self._check_security_vulnerabilities(content, file_path)
        
        # Documentation analysis
        doc_issues = self._check_documentation_gaps(content, file_path)
        
        # Complexity analysis
        complexity_issues = self._analyze_complexity(content, file_path)
        
        # Memory management analysis (Python-specific)
        memory_issues = await self._check_memory_management(content, file_path)
        
        # AI-powered semantic analysis if MCP is available
        semantic_analysis = {}
        if self.mcp:
            semantic_analysis = await self._perform_ai_analysis(content, file_path)
        
        # OWL-based reasoning if available
        owl_analysis = {}
        if self.owl_engine:
            owl_analysis = self._perform_owl_reasoning(content, file_path)
        
        return {
            "file_path": file_path,
            "static_analysis": static_analysis,
            "performance": performance_issues,
            "security": security_issues,
            "documentation": doc_issues,
            "complexity": complexity_issues,
            "memory_management": memory_issues,
            "semantic_analysis": semantic_analysis,
            "owl_analysis": owl_analysis,
            "total_issues": (
                len(static_analysis.get("issues", [])) +
                len(performance_issues.get("issues", [])) +
                len(security_issues.get("issues", [])) +
                len(doc_issues.get("issues", [])) +
                len(complexity_issues.get("issues", [])) +
                len(memory_issues.get("issues", []))
            ),
            "analysis_timestamp": time.time()
        }
    
    def _perform_static_analysis(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform static code analysis."""
        issues = []
        stats = {"lines_of_code": 0, "comment_lines": 0, "blank_lines": 0}
        
        # Count lines
        lines = content.splitlines()
        stats["lines_of_code"] = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                stats["blank_lines"] += 1
            elif stripped.startswith('#'):
                stats["comment_lines"] += 1
        
        # Try to parse Python code with AST to find syntax errors
        if file_path.endswith('.py'):
            try:
                ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    "type": "syntax_error",
                    "line": e.lineno,
                    "message": str(e),
                    "severity": "critical"
                })
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            # Check for print statements in Python files (might be debug code)
            if file_path.endswith('.py') and 'print(' in line and not line.strip().startswith('#'):
                issues.append({
                    "type": "potential_debug_code",
                    "line": i,
                    "message": "Print statement might be leftover debug code",
                    "severity": "low"
                })
            
            # Check for TODO comments
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    "type": "todo_comment",
                    "line": i,
                    "message": f"Unresolved TODO/FIXME: {line.strip()}",
                    "severity": "low"
                })
        
        return {
            "issues": issues,
            "stats": stats
        }
    
    async def _check_performance(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for performance issues in the code."""
        issues = []
        
        # Basic regex-based checks
        if file_path.endswith('.py'):
            # Check for inefficient list comprehensions that should be generator expressions
            list_comps = re.findall(r'\[.*for.*in.*\]', content)
            for comp in list_comps:
                if 'if' in comp and comp.count('for') == 1 and not re.search(r'\[.*for.*in.*if.*\].*\[', content):
                    issues.append({
                        "type": "inefficient_list_comprehension",
                        "message": "Consider using generator expression instead of list comprehension for filtering",
                        "severity": "medium",
                        "suggestion": "Change list comprehension to generator expression when only filtering is needed"
                    })
            
            # Check for repeated calls that could be cached
            function_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\(', content)
            call_counts = {}
            for call in function_calls:
                call_counts[call] = call_counts.get(call, 0) + 1
            
            for call, count in call_counts.items():
                if count > 5 and call not in ['print', 'str', 'int', 'len', 'list', 'dict', 'set']:
                    issues.append({
                        "type": "repeated_function_call",
                        "message": f"Function '{call}' is called {count} times and might benefit from caching or refactoring",
                        "severity": "medium",
                        "suggestion": f"Consider caching the results of '{call}' or refactoring the code"
                    })
        
        # AI-powered performance analysis if MCP is available
        if self.mcp:
            try:
                analysis_prompt = f"""
                Analyze the following code for performance issues:
                
                ```
                {content[:3000]}  # Limit code size for prompt
                ```
                
                Focus on:
                1. Inefficient algorithms or data structures
                2. Redundant calculations
                3. Performance bottlenecks
                4. Optimization opportunities
                
                Return a JSON object with the following structure:
                {{
                    "issues": [
                        {{
                            "type": "issue_type",
                            "message": "Detailed description",
                            "severity": "low|medium|high|critical",
                            "suggestion": "How to fix it"
                        }}
                    ]
                }}
                """
                
                response = await self.mcp.process_request_async(
                    prompt=analysis_prompt,
                    system="You are an expert performance engineer specializing in optimizing code. Analyze the provided code for performance issues and return detailed recommendations in JSON format.",
                    context={"file_path": file_path},
                    max_tokens=1024
                )
                
                try:
                    # Extract JSON from response
                    import json
                    content = response.get("content", "{}")
                    
                    # Find JSON block in the content (might be wrapped in ```json...```)
                    json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                    
                    # Clean up the JSON string
                    json_str = re.sub(r'(?m)^\s*//.*$', '', json_str)  # Remove JavaScript comments
                    
                    ai_issues = json.loads(json_str).get("issues", [])
                    issues.extend(ai_issues)
                except Exception as e:
                    logger.warning(f"Failed to parse AI performance analysis response: {e}")
            except Exception as e:
                logger.warning(f"Failed to perform AI performance analysis: {e}")
        
        return {
            "issues": issues
        }
    
    async def _check_security_vulnerabilities(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for security vulnerabilities in the code."""
        issues = []
        
        # Basic security checks
        if file_path.endswith('.py'):
            # Check for potential SQL injection
            if re.search(r'cursor\.execute\([^,]*\+', content) or re.search(r'execute\([^,]*\+', content):
                issues.append({
                    "type": "sql_injection",
                    "message": "Potential SQL injection vulnerability detected",
                    "severity": "critical",
                    "suggestion": "Use parameterized queries instead of string concatenation"
                })
            
            # Check for hardcoded secrets
            secret_patterns = [
                (r'(?:password|passwd|pwd)\s*=\s*[\'"][^\'"]+[\'"]', "hardcoded_password"),
                (r'(?:api_?key|apikey|token)\s*=\s*[\'"][^\'"]+[\'"]', "hardcoded_api_key"),
                (r'(?:secret)\s*=\s*[\'"][^\'"]+[\'"]', "hardcoded_secret")
            ]
            
            for pattern, issue_type in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append({
                        "type": issue_type,
                        "message": f"Potential hardcoded secret ({issue_type}) detected",
                        "severity": "high",
                        "suggestion": "Use environment variables or a secure secret management system"
                    })
            
            # Check for unsafe deserialization
            if "pickle.loads" in content or "yaml.load(" in content:
                issues.append({
                    "type": "unsafe_deserialization",
                    "message": "Potentially unsafe deserialization detected",
                    "severity": "high",
                    "suggestion": "Use yaml.safe_load() instead of yaml.load() or ensure pickle data is from trusted sources"
                })
        
        # AI-powered security analysis if MCP is available
        if self.mcp:
            try:
                analysis_prompt = f"""
                Analyze the following code for security vulnerabilities:
                
                ```
                {content[:3000]}  # Limit code size for prompt
                ```
                
                Focus on:
                1. Injection vulnerabilities
                2. Authentication and authorization issues
                3. Data exposure risks
                4. Security misconfigurations
                
                Return a JSON object with the following structure:
                {{
                    "issues": [
                        {{
                            "type": "issue_type",
                            "message": "Detailed description",
                            "severity": "low|medium|high|critical",
                            "suggestion": "How to fix it"
                        }}
                    ]
                }}
                """
                
                response = await self.mcp.process_request_async(
                    prompt=analysis_prompt,
                    system="You are an expert security engineer specializing in code security. Analyze the provided code for security vulnerabilities and return detailed recommendations in JSON format.",
                    context={"file_path": file_path},
                    max_tokens=1024
                )
                
                try:
                    # Extract JSON from response
                    import json
                    content = response.get("content", "{}")
                    
                    # Find JSON block in the content
                    json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                    
                    # Clean up the JSON string
                    json_str = re.sub(r'(?m)^\s*//.*$', '', json_str)
                    
                    ai_issues = json.loads(json_str).get("issues", [])
                    issues.extend(ai_issues)
                except Exception as e:
                    logger.warning(f"Failed to parse AI security analysis response: {e}")
            except Exception as e:
                logger.warning(f"Failed to perform AI security analysis: {e}")
        
        return {
            "issues": issues
        }
    
    def _check_documentation_gaps(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for documentation gaps in the code."""
        issues = []
        
        if file_path.endswith('.py'):
            # Check for module docstring
            if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
                issues.append({
                    "type": "missing_module_docstring",
                    "message": "Module lacks a docstring",
                    "severity": "medium",
                    "suggestion": "Add a module-level docstring to explain the purpose and usage of this module"
                })
            
            # Parse the AST to check for class/function docstrings
            try:
                parsed = ast.parse(content)
                
                for node in ast.walk(parsed):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Check for docstring
                        docstring = ast.get_docstring(node)
                        if not docstring:
                            issues.append({
                                "type": f"missing_{'class' if isinstance(node, ast.ClassDef) else 'function'}_docstring",
                                "message": f"{node.name} lacks a docstring",
                                "severity": "medium",
                                "suggestion": f"Add a docstring to {node.name} to explain its purpose, parameters, and return value"
                            })
                        
                        # For functions, check if parameters are documented
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and docstring:
                            # Check if there are parameters not mentioned in docstring
                            params = [a.arg for a in node.args.args if a.arg != 'self']
                            for param in params:
                                if param not in docstring:
                                    issues.append({
                                        "type": "undocumented_parameter",
                                        "message": f"Parameter '{param}' in function '{node.name}' is not documented",
                                        "severity": "low",
                                        "suggestion": f"Document the '{param}' parameter in the docstring for '{node.name}'"
                                    })
            except Exception as e:
                logger.warning(f"Failed to parse AST for documentation analysis: {e}")
        
        return {
            "issues": issues
        }
    
    def _analyze_complexity(self, content: str, file_path: str) -> Dict[str, Any]:
        """Analyze code complexity."""
        issues = []
        
        if file_path.endswith('.py'):
            try:
                parsed = ast.parse(content)
                
                for node in ast.walk(parsed):
                    # Check for deeply nested control structures
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        max_nesting = 0
                        current_nesting = 0
                        
                        for subnode in ast.walk(node):
                            if isinstance(subnode, (ast.For, ast.While, ast.If)):
                                current_nesting += 1
                                max_nesting = max(max_nesting, current_nesting)
                            elif isinstance(subnode, ast.FunctionDef):
                                current_nesting = 0  # Reset for nested functions
                        
                        if max_nesting > 3:
                            issues.append({
                                "type": "high_nesting_complexity",
                                "message": f"Function '{node.name}' has deeply nested control structures (depth: {max_nesting})",
                                "severity": "medium",
                                "suggestion": f"Consider refactoring '{node.name}' to reduce nesting depth"
                            })
                        
                        # Check for function length
                        func_lines = len(ast.unparse(node).split('\n'))
                        if func_lines > 50:
                            issues.append({
                                "type": "function_too_long",
                                "message": f"Function '{node.name}' is too long ({func_lines} lines)",
                                "severity": "medium",
                                "suggestion": f"Consider breaking '{node.name}' into smaller functions"
                            })
                        
                        # Count number of branches
                        branch_count = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While)))
                        if branch_count > 10:
                            issues.append({
                                "type": "high_cyclomatic_complexity",
                                "message": f"Function '{node.name}' has high cyclomatic complexity ({branch_count} branches)",
                                "severity": "medium",
                                "suggestion": f"Consider refactoring '{node.name}' to reduce complexity"
                            })
            except Exception as e:
                logger.warning(f"Failed to analyze code complexity: {e}")
        
        return {
            "issues": issues
        }
    
    async def _check_memory_management(self, content: str, file_path: str) -> Dict[str, Any]:
        """Check for memory management issues."""
        issues = []
        
        if file_path.endswith('.py'):
            # Check for open files or resources not properly closed
            if 'open(' in content:
                # Count open() calls not in with statement
                open_calls = re.findall(r'([^w]open\()', content)
                with_open = re.findall(r'with\s+open\(', content)
                
                if len(open_calls) > len(with_open):
                    issues.append({
                        "type": "resource_leak",
                        "message": "Possible file resource leak: file opened without 'with' statement",
                        "severity": "medium",
                        "suggestion": "Use 'with open(...) as f:' pattern to ensure files are properly closed"
                    })
            
            # Check for large data structures in memory
            if re.search(r'= \[.{1000,}\]', content) or re.search(r'= \{.{1000,}\}', content):
                issues.append({
                    "type": "large_literal",
                    "message": "Large literal data structure may cause memory issues",
                    "severity": "medium",
                    "suggestion": "Consider loading large data from external files or generating it dynamically"
                })
        
        # AI-powered memory analysis if MCP is available
        if self.mcp:
            try:
                analysis_prompt = f"""
                Analyze the following code for memory management issues:
                
                ```
                {content[:3000]}  # Limit code size for prompt
                ```
                
                Focus on:
                1. Memory leaks
                2. Inefficient memory usage
                3. Resource leaks
                4. Memory-intensive operations
                
                Return a JSON object with the following structure:
                {{
                    "issues": [
                        {{
                            "type": "issue_type",
                            "message": "Detailed description",
                            "severity": "low|medium|high|critical",
                            "suggestion": "How to fix it"
                        }}
                    ]
                }}
                """
                
                response = await self.mcp.process_request_async(
                    prompt=analysis_prompt,
                    system="You are an expert in memory management and optimization. Analyze the provided code for memory-related issues and return detailed recommendations in JSON format.",
                    context={"file_path": file_path},
                    max_tokens=1024
                )
                
                try:
                    # Extract JSON from response
                    import json
                    content = response.get("content", "{}")
                    
                    # Find JSON block in the content
                    json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                    
                    # Clean up the JSON string
                    json_str = re.sub(r'(?m)^\s*//.*$', '', json_str)
                    
                    ai_issues = json.loads(json_str).get("issues", [])
                    issues.extend(ai_issues)
                except Exception as e:
                    logger.warning(f"Failed to parse AI memory analysis response: {e}")
            except Exception as e:
                logger.warning(f"Failed to perform AI memory analysis: {e}")
        
        return {
            "issues": issues
        }
    
    async def _perform_ai_analysis(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform AI-powered code analysis."""
        try:
            analysis_prompt = f"""
            Perform a comprehensive code review of the following code:
            
            ```
            {content[:4000]}  # Limit code size for prompt
            ```
            
            Analyze the code for:
            1. Overall code quality and maintainability
            2. Adherence to best practices
            3. Potential bugs or edge cases
            4. Architectural concerns
            5. Any other issues that should be addressed
            
            Return a JSON object with the following structure:
            {{
                "overall_quality": "low|medium|high",
                "strengths": ["strength1", "strength2", ...],
                "issues": [
                    {{
                        "type": "issue_type",
                        "message": "Detailed description",
                        "severity": "low|medium|high|critical",
                        "suggestion": "How to fix it"
                    }}
                ],
                "recommendations": ["recommendation1", "recommendation2", ...]
            }}
            """
            
            response = await self.mcp.process_request_async(
                prompt=analysis_prompt,
                system="You are an expert code reviewer with deep understanding of software development best practices. Analyze the provided code and provide actionable feedback in JSON format.",
                context={"file_path": file_path},
                max_tokens=2048
            )
            
            try:
                # Extract JSON from response
                import json
                content = response.get("content", "{}")
                
                # Find JSON block in the content
                json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', content)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
                
                # Clean up the JSON string
                json_str = re.sub(r'(?m)^\s*//.*$', '', json_str)
                
                return json.loads(json_str)
            except Exception as e:
                logger.warning(f"Failed to parse AI analysis response: {e}")
                return {"error": str(e), "raw_response": response.get("content", "")}
        except Exception as e:
            logger.warning(f"Failed to perform AI analysis: {e}")
            return {"error": str(e)}
    
    def _perform_owl_reasoning(self, content: str, file_path: str) -> Dict[str, Any]:
        """Perform OWL-based reasoning on the code."""
        if not self.owl_engine:
            return {}
        
        try:
            reasoning_result = self.owl_engine.reason(
                query=f"Analyze this code file to understand its quality, potential issues, and improvement opportunities",
                context=[content]
            )
            
            return reasoning_result
        except Exception as e:
            logger.warning(f"Failed to perform OWL reasoning: {e}")
            return {"error": str(e)}
    
    def calculate_quality_score(self, analysis_result: Dict[str, Any]) -> float:
        """
        Calculate a quality score based on analysis results.
        
        The score ranges from 0.0 (worst) to 1.0 (best).
        """
        # Count issues by severity
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        
        # Process all issue types
        for category in ["static_analysis", "performance", "security", "documentation", "complexity", "memory_management"]:
            issues = analysis_result.get(category, {}).get("issues", [])
            for issue in issues:
                severity = issue.get("severity", "").lower()
                if severity == "critical":
                    critical_issues += 1
                elif severity == "high":
                    high_issues += 1
                elif severity == "medium":
                    medium_issues += 1
                elif severity == "low":
                    low_issues += 1
        
        # Calculate base score (1.0 is perfect)
        base_score = 1.0
        
        # Deduct points based on issue severity
        base_score -= critical_issues * 0.2  # Critical issues have major impact
        base_score -= high_issues * 0.1      # High issues have significant impact
        base_score -= medium_issues * 0.03   # Medium issues have moderate impact
        base_score -= low_issues * 0.01      # Low issues have minor impact
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))


# Simple factory function
def create_analyzer(mcp=None, owl_engine=None, workspace_dir=None):
    """Create a CodeAnalyzer instance with the given components."""
    return CodeAnalyzer(mcp=mcp, owl_engine=owl_engine, workspace_dir=workspace_dir) 