#!/usr/bin/env python3
"""
VOT1 Self-Improvement Agent

This module implements an advanced self-improvement agent for the VOT1 system,
enabling autonomous enhancement of code and visualization. The agent uses
Claude 3.7 Sonnet with maximum thinking tokens, hybrid reasoning with Perplexity,
and OWL-based code understanding to continuously improve itself.

Key features:
1. Recursive self-improvement capabilities
2. Code analysis and enhancement
3. Automated testing and evaluation
4. Safety guardrails and oversight
5. Learning from improvement attempts
6. Memory-enhanced reasoning
"""

import os
import json
import logging
import time
import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable

from vot1.vot_mcp import VotModelControlProtocol
from vot1.memory import MemoryManager
from vot1.owl_reasoning import OWLReasoningEngine
from vot1.self_improvement_workflow import SelfImprovementWorkflow
from vot1.code_analyzer import CodeAnalyzer, create_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SelfImprovementAgent:
    """
    Autonomous agent capable of improving its own code and the VOT1 system.
    
    This agent builds on the self-improvement workflow to provide a more
    autonomous system for continuous enhancement, with built-in safety
    measures and learning capabilities.
    """
    
    def __init__(
        self,
        workflow: Optional[SelfImprovementWorkflow] = None,
        max_thinking_tokens: int = 4096,
        max_iterations: int = 5,
        improvement_threshold: float = 0.2,  # 20% improvement required
        safety_checks: bool = True,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize the self-improvement agent.
        
        Args:
            workflow: Self-improvement workflow for baseline functionality
            max_thinking_tokens: Maximum tokens for Claude thinking steps
            max_iterations: Maximum number of improvement iterations
            improvement_threshold: Minimum score for improvements to be accepted
            safety_checks: Whether to perform safety checks on code changes
            workspace_dir: Root directory of the workspace
        """
        self.workflow = workflow or SelfImprovementWorkflow(
            workspace_dir=workspace_dir
        )
        
        self.max_thinking_tokens = max_thinking_tokens
        self.max_iterations = max_iterations
        self.improvement_threshold = improvement_threshold
        self.safety_checks = safety_checks
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        
        # Initialize statistics tracking
        self.improvement_stats = {
            "attempts": 0,
            "successful": 0,
            "failed": 0,
            "safety_rejected": 0,
            "quality_rejected": 0,
        }
        
        # Initialize code analyzer
        self.code_analyzer = create_analyzer(
            mcp=self.workflow.mcp,
            owl_engine=self.workflow.owl_engine,
            workspace_dir=self.workspace_dir
        )
        
        # Initialize safety verifier
        if safety_checks:
            self._init_safety_verifier()
        
        logger.info(f"Initialized SelfImprovementAgent with max_iterations={max_iterations}, improvement_threshold={improvement_threshold}")
    
    def _init_safety_verifier(self):
        """Initialize the safety verification system."""
        # System message for safety verification
        self.safety_system_message = """
        You are a cybersecurity and software safety expert responsible for verifying code changes.
        Your task is to carefully analyze proposed code changes and identify any potential issues:
        
        1. Security vulnerabilities (injection, XSS, CSRF, etc.)
        2. Memory leaks or performance degradation
        3. Breaking changes to existing APIs
        4. Unsafe file operations or system calls
        5. Introduction of external dependencies without proper validation
        
        Be very conservative in your assessment. If you detect any significant issues, 
        reject the change and explain why. Only approve changes that are clearly safe.
        """
    
    async def improve_component(self, 
                         component_path: str, 
                         improvement_type: str,
                         custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempt to improve a specific component of the system.
        
        Args:
            component_path: Path to the component to improve
            improvement_type: Type of improvement to attempt
            custom_instructions: Optional specific instructions
        
        Returns:
            Dictionary with improvement results
        """
        logger.info(f"Starting improvement attempt for {component_path}, type={improvement_type}")
        
        # Increment attempt counter
        self.improvement_stats["attempts"] += 1
        
        # Create a unique ID for this improvement
        improvement_id = str(uuid.uuid4())
        
        try:
            # Step 1: Analyze current code
            analysis = await self._analyze_component(component_path)
            
            # Check if analysis failed
            if "error" in analysis and not analysis.get("success", True):
                logger.error(f"Analysis failed for {component_path}: {analysis['error']}")
                self.improvement_stats["failed"] += 1
                return {
                    "success": False,
                    "improvement_id": improvement_id,
                    "component": component_path,
                    "improvement_type": improvement_type,
                    "error": f"Analysis failed: {analysis.get('error', 'Unknown error')}",
                    "timestamp": time.time()
                }
            
            # Step 2: Generate improvement plan
            improvement_plan = await self._create_improvement_plan(
                component_path, 
                improvement_type, 
                analysis,
                custom_instructions
            )
            
            # Step 3: Generate code changes
            code_changes = await self._generate_code_changes(
                component_path,
                improvement_plan
            )
            
            # Step 4: Safety verification if enabled
            if self.safety_checks:
                safety_result = await self._verify_safety(component_path, code_changes)
                if not safety_result["safe"]:
                    logger.warning(f"Safety check failed: {safety_result['reason']}")
                    self.improvement_stats["safety_rejected"] += 1
                    
                    return {
                        "success": False,
                        "improvement_id": improvement_id,
                        "component": component_path,
                        "improvement_type": improvement_type,
                        "error": f"Safety check failed: {safety_result['reason']}",
                        "improvement_plan": improvement_plan,
                        "code_changes": code_changes,
                        "timestamp": time.time()
                    }
            
            # Step 5: Apply code changes
            application_result = await self._apply_code_changes(component_path, code_changes)
            
            if not application_result["success"]:
                logger.error(f"Failed to apply code changes: {application_result.get('error', 'Unknown error')}")
                self.improvement_stats["failed"] += 1
                
                return {
                    "success": False,
                    "improvement_id": improvement_id,
                    "component": component_path,
                    "improvement_type": improvement_type,
                    "error": f"Failed to apply code changes: {application_result.get('error', 'Unknown error')}",
                    "improvement_plan": improvement_plan,
                    "code_changes": code_changes,
                    "timestamp": time.time()
                }
            
            # Step 6: Test the changes
            test_result = await self._test_changes(component_path)
            
            if not test_result["success"]:
                logger.warning(f"Tests failed after changes: {test_result.get('error', 'Unknown error')}")
                
                # Revert changes if tests fail
                await self._revert_changes(component_path)
                
                self.improvement_stats["failed"] += 1
                
                return {
                    "success": False,
                    "improvement_id": improvement_id,
                    "component": component_path,
                    "improvement_type": improvement_type,
                    "error": f"Tests failed after changes: {test_result.get('error', 'Unknown error')}",
                    "improvement_plan": improvement_plan,
                    "code_changes": code_changes,
                    "timestamp": time.time()
                }
            
            # Step 7: Evaluate the improvement
            evaluation = await self._evaluate_improvement(
                component_path, 
                improvement_type,
                test_result
            )
            
            # Check if improvement meets threshold
            if evaluation["score"] < self.improvement_threshold:
                logger.warning(f"Improvement score {evaluation['score']:.2f} below threshold {self.improvement_threshold}")
                
                # Revert changes if score is below threshold
                await self._revert_changes(component_path)
                
                self.improvement_stats["quality_rejected"] += 1
                
                return {
                    "success": False,
                    "improvement_id": improvement_id,
                    "component": component_path,
                    "improvement_type": improvement_type,
                    "score": evaluation["score"],
                    "threshold": self.improvement_threshold,
                    "error": f"Improvement score {evaluation['score']:.2f} below threshold {self.improvement_threshold}",
                    "evaluation": evaluation,
                    "improvement_plan": improvement_plan,
                    "code_changes": code_changes,
                    "timestamp": time.time()
                }
            
            # Step 8: Document the improvement
            documentation = await self._document_improvement(
                component_path,
                improvement_type,
                improvement_plan,
                evaluation
            )
            
            # Store improvement in memory
            self._store_improvement_in_memory(
                improvement_id,
                component_path,
                improvement_type,
                code_changes,
                evaluation,
                documentation
            )
            
            # Increment success counter
            self.improvement_stats["successful"] += 1
            
            logger.info(f"Successfully improved {component_path}, score: {evaluation['score']:.2f}")
            
            return {
                "success": True,
                "improvement_id": improvement_id,
                "component": component_path,
                "improvement_type": improvement_type,
                "score": evaluation["score"],
                "evaluation": evaluation,
                "documentation": documentation,
                "improvement_plan": improvement_plan,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error during improvement of {component_path}: {e}", exc_info=True)
            self.improvement_stats["failed"] += 1
            
            return {
                "success": False,
                "improvement_id": improvement_id,
                "component": component_path,
                "improvement_type": improvement_type,
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _analyze_component(self, component_path: str) -> Dict[str, Any]:
        """Analyze a component to understand its structure and functionality."""
        full_path = self.workspace_dir / component_path
        
        # Check if file exists
        if not full_path.exists():
            raise FileNotFoundError(f"Component not found: {component_path}")
        
        try:
            # Use code analyzer for comprehensive analysis
            code_analysis = await self.code_analyzer.analyze_code(component_path)
            
            # Read the file for backward compatibility
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Use OWL reasoning to analyze the component (from existing code)
            reasoning_result = self.workflow.owl_engine.reason(
                query=f"Analyze this code file to understand its structure, purpose, and functionality",
                context=[content]
            )
            
            # Use MCP to get a more detailed analysis (from existing code)
            analysis_prompt = f"""
            Analyze the following code component in detail:
            
            File path: {component_path}
            
            Please provide:
            1. A summary of the component's purpose and functionality
            2. Key classes, functions, and their relationships
            3. Main design patterns and architectural approaches used
            4. Potential areas for improvement
            5. Dependencies and integration points with other components
            """
            
            analysis_response = await self.workflow.mcp.process_request_async(
                prompt=analysis_prompt,
                system="You are an expert code analyzer with deep understanding of software architecture, design patterns, and best practices.",
                context={
                    "code": content,
                    "reasoning": reasoning_result,
                    "code_analysis": code_analysis  # Add the code analysis results
                },
                max_tokens=2048
            )
            
            # Calculate quality score
            quality_score = self.code_analyzer.calculate_quality_score(code_analysis)
            
            return {
                "path": component_path,
                "reasoning": reasoning_result,
                "analysis": analysis_response.get("content", ""),
                "code_analysis": code_analysis,
                "quality_score": quality_score,
                "lines_of_code": len(content.splitlines()),
                "total_issues": code_analysis.get("total_issues", 0)
            }
        except Exception as e:
            logger.error(f"Error analyzing component {component_path}: {e}")
            return {
                "path": component_path,
                "error": str(e),
                "success": False
            }
    
    async def _create_improvement_plan(self, 
                                component_path: str, 
                                improvement_type: str, 
                                analysis: Dict[str, Any],
                                custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Create a plan for improving the component."""
        # Build prompt based on improvement type
        type_instructions = ""
        if improvement_type == "performance":
            type_instructions = """
            Focus on performance optimization:
            1. Identify bottlenecks and inefficient algorithms
            2. Improve time complexity and reduce memory usage
            3. Optimize expensive operations
            4. Implement caching where appropriate
            5. Reduce unnecessary computation
            """
        elif improvement_type == "security":
            type_instructions = """
            Focus on security improvements:
            1. Identify and fix potential vulnerabilities
            2. Implement proper input validation and sanitization
            3. Use secure API endpoints and authentication
            4. Follow least privilege principle
            5. Add appropriate error handling
            """
        elif improvement_type == "architecture":
            type_instructions = """
            Focus on architectural improvements:
            1. Improve modularity and separation of concerns
            2. Enhance extensibility and maintainability
            3. Apply appropriate design patterns
            4. Reduce technical debt
            5. Improve API design
            """
        elif improvement_type == "features":
            type_instructions = """
            Focus on feature enhancements:
            1. Identify missing capabilities that would add value
            2. Extend existing functionality in meaningful ways
            3. Add better error handling and edge case management
            4. Improve user experience and interfaces
            5. Enhance integration with other components
            """
        elif improvement_type == "visualization":
            type_instructions = """
            Focus on visualization improvements:
            1. Enhance graphical representation and aesthetics
            2. Improve interactivity and user controls
            3. Optimize rendering performance
            4. Add new visualization modes or perspectives
            5. Create a more intuitive and engaging experience with cyberpunk aesthetics
            """
        
        # Include custom instructions if provided
        if custom_instructions:
            type_instructions += f"\nCustom requirements:\n{custom_instructions}"
        
        # Generate improvement plan
        plan_prompt = f"""
        Create a detailed improvement plan for the following component:
        
        File path: {component_path}
        Improvement type: {improvement_type}
        
        {type_instructions}
        
        Based on the analysis, develop a step-by-step plan to improve this component.
        Include specific changes to make, approaches to use, and the expected benefits.
        
        Your plan should be concrete, implementable, and maintain compatibility with existing code.
        """
        
        plan_response = await self.workflow.mcp.process_request_async(
            prompt=plan_prompt,
            system="You are an expert software architect specialized in creating detailed improvement plans. Your plans are specific, implementable, and maintain compatibility with existing systems.",
            context={
                "analysis": analysis,
                "improvement_type": improvement_type
            },
            max_tokens=2048
        )
        
        return {
            "plan": plan_response.get("content", ""),
            "improvement_type": improvement_type,
            "component_path": component_path
        }
    
    async def _generate_code_changes(self, 
                              component_path: str, 
                              improvement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific code changes based on the improvement plan."""
        full_path = self.workspace_dir / component_path
        
        # Read the original file
        with open(full_path, 'r') as f:
            original_code = f.read()
        
        # Generate code changes
        changes_prompt = f"""
        Based on the improvement plan, generate specific code changes for the component.
        
        File path: {component_path}
        Improvement plan: {improvement_plan['plan']}
        
        You will modify the existing code to implement the improvements.
        Your changes should:
        
        1. Be minimal and focused on the specific improvements
        2. Maintain the overall structure and compatibility
        3. Include helpful comments explaining significant changes
        4. Follow the coding style of the original file
        5. Be thoroughly tested and without introducing bugs
        
        Provide the complete modified code, not just the changes.
        """
        
        changes_response = await self.workflow.mcp.process_request_async(
            prompt=changes_prompt,
            system="You are an expert software developer with deep knowledge of best practices, security, and performance optimization. You generate clean, well-tested code that implements improvements while maintaining compatibility.",
            context={
                "original_code": original_code,
                "improvement_plan": improvement_plan
            },
            max_tokens=4096
        )
        
        # Extract code from response
        changes_content = changes_response.get("content", "")
        
        # Extract code block if present
        import re
        code_block_pattern = r"```[\w]*\n(.*?)```"
        code_blocks = re.findall(code_block_pattern, changes_content, re.DOTALL)
        
        if code_blocks:
            modified_code = code_blocks[0]
        else:
            modified_code = changes_content
        
        return {
            "original_code": original_code,
            "modified_code": modified_code,
            "component_path": component_path,
            "explanation": changes_response.get("content", "")
        }
    
    async def _verify_safety(self, 
                      component_path: str, 
                      code_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the proposed changes are safe to apply."""
        # Extract original and modified code
        original_code = code_changes["original_code"]
        modified_code = code_changes["modified_code"]
        
        # Calculate diff
        import difflib
        differ = difflib.Differ()
        diff = list(differ.compare(original_code.splitlines(), modified_code.splitlines()))
        diff_text = "\n".join(diff)
        
        # Use MCP to verify safety
        safety_prompt = f"""
        Verify the safety of the following code changes for component: {component_path}
        
        Diff:
        ```
        {diff_text}
        ```
        
        Perform a thorough security and safety analysis of these changes.
        Specifically check for:
        
        1. Security vulnerabilities (injection, XSS, unauthorized access, etc.)
        2. Potential bugs or regressions
        3. Breaking API changes
        4. Performance issues
        5. Resource leaks
        6. Unsafe operations or system calls
        
        Rate the safety of these changes on a scale of 0.0 to 1.0, where:
        - 0.0: Clearly unsafe changes with high risk
        - 0.5: Some concerns but potentially acceptable with modifications
        - 1.0: Completely safe changes with no concerns
        
        Provide your rating and detailed explanation of any issues found.
        If any critical issues exist, they must be addressed before these changes can be applied.
        """
        
        safety_response = await self.workflow.mcp.process_request_async(
            prompt=safety_prompt,
            system=self.safety_system_message,
            context={
                "component_path": component_path,
                "original_code": original_code,
                "modified_code": modified_code
            },
            max_tokens=2048
        )
        
        # Extract safety score using regex
        import re
        score_pattern = r"(\d+\.\d+|\d+)"
        safety_content = safety_response.get("content", "")
        score_matches = re.findall(score_pattern, safety_content)
        
        safety_score = 0.0
        if score_matches:
            try:
                safety_score = float(score_matches[0])
                # Ensure score is between 0 and 1
                safety_score = max(0.0, min(1.0, safety_score))
            except ValueError:
                safety_score = 0.0
        
        # Determine if changes are safe (score >= 0.8)
        is_safe = safety_score >= 0.8
        
        return {
            "safe": is_safe,
            "score": safety_score,
            "analysis": safety_content,
            "reason": "Safety score below threshold" if not is_safe else None
        }
    
    async def _apply_code_changes(self, 
                           component_path: str, 
                           code_changes: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the code changes to the component."""
        full_path = self.workspace_dir / component_path
        
        try:
            # Create backup
            backup_path = f"{full_path}.bak"
            with open(full_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            
            # Write modified code
            with open(full_path, 'w') as f:
                f.write(code_changes["modified_code"])
            
            logger.info(f"Applied changes to {component_path}, backup at {backup_path}")
            
            return {
                "success": True,
                "component_path": component_path,
                "backup_path": backup_path
            }
        except Exception as e:
            logger.error(f"Error applying changes to {component_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _test_changes(self, component_path: str) -> Dict[str, Any]:
        """Test the changes to ensure they work as expected."""
        # This is a simplified version - in a real implementation, 
        # you would run actual tests for the component
        
        # For the demonstration, we'll simulate testing by checking if:
        # 1. The file is valid Python/JavaScript
        # 2. Basic imports work
        
        full_path = self.workspace_dir / component_path
        file_ext = full_path.suffix.lower()
        
        try:
            if file_ext == '.py':
                # For Python files, try to compile the code
                with open(full_path, 'r') as f:
                    content = f.read()
                compile(content, full_path, 'exec')
                
                # Try importing if it's a module
                if '__init__.py' in str(full_path) or component_path.startswith('src/'):
                    # Convert path to module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("module.name", full_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            
            elif file_ext == '.js':
                # For JavaScript, we could use nodejs to check syntax
                # This is a simplified check that just ensures the file exists
                if not full_path.exists():
                    raise Exception("JavaScript file does not exist")
            
            return {
                "success": True,
                "component_path": component_path
            }
        except Exception as e:
            logger.error(f"Test failed for {component_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "component_path": component_path
            }
    
    async def _evaluate_improvement(self, 
                             component_path: str, 
                             improvement_type: str,
                             test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the quality and impact of the improvement."""
        full_path = self.workspace_dir / component_path
        
        try:
            # Read the modified code
            with open(full_path, 'r') as f:
                modified_code = f.read()
            
            # Read the backup (original) code
            backup_path = f"{full_path}.bak"
            with open(backup_path, 'r') as f:
                original_code = f.read()
            
            # Use code analyzer to evaluate the improvement
            original_analysis = None
            modified_analysis = None
            
            try:
                # Create a temporary backup of the current modified code
                temp_backup_path = f"{full_path}.temp"
                with open(temp_backup_path, 'w') as f:
                    f.write(modified_code)
                
                # Restore original code to analyze it
                with open(full_path, 'w') as f:
                    f.write(original_code)
                
                # Analyze original code
                original_analysis = await self.code_analyzer.analyze_code(component_path)
                original_score = self.code_analyzer.calculate_quality_score(original_analysis)
                
                # Restore modified code
                with open(full_path, 'w') as f:
                    f.write(modified_code)
                
                # Analyze modified code
                modified_analysis = await self.code_analyzer.analyze_code(component_path)
                modified_score = self.code_analyzer.calculate_quality_score(modified_analysis)
                
                # Remove temporary backup
                if os.path.exists(temp_backup_path):
                    os.remove(temp_backup_path)
                
            except Exception as e:
                logger.warning(f"Failed to perform comparative code analysis: {e}")
                # Ensure we restore the modified code if anything fails
                with open(full_path, 'w') as f:
                    f.write(modified_code)
            
            # Use MCP to evaluate improvement
            eval_prompt = f"""
            Evaluate the improvement made to component: {component_path}
            Improvement type: {improvement_type}
            
            Compare the original and modified code to assess the quality and impact of the improvements.
            
            Rate the improvement on a scale of 0.0 to 1.0, where:
            - 0.0: No improvement or regression
            - 0.5: Moderate improvement
            - 1.0: Exceptional improvement that transforms the component
            
            Provide your rating and a detailed analysis of:
            1. How well the changes address the improvement type ({improvement_type})
            2. Code quality improvements
            3. Potential impact on the overall system
            4. Any concerns or limitations
            """
            
            # Add code analysis results to context if available
            context = {
                "original_code": original_code,
                "modified_code": modified_code,
                "improvement_type": improvement_type,
                "component_path": component_path,
                "test_result": test_result
            }
            
            if original_analysis and modified_analysis:
                context["original_analysis"] = original_analysis
                context["modified_analysis"] = modified_analysis
                context["original_score"] = original_score
                context["modified_score"] = modified_score
            
            eval_response = await self.workflow.mcp.process_request_async(
                prompt=eval_prompt,
                system="You are an expert code reviewer with deep experience evaluating software improvements. You provide balanced, objective assessments of code changes based on best practices, performance, security, and maintainability.",
                context=context,
                max_tokens=2048
            )
            
            # Extract evaluation score using regex
            import re
            score_pattern = r"(\d+\.\d+|\d+)"
            eval_content = eval_response.get("content", "")
            
            matches = re.findall(score_pattern, eval_content)
            score = 0.0
            
            if matches:
                # Look for scores between 0 and 1
                for match in matches:
                    try:
                        value = float(match)
                        if 0.0 <= value <= 1.0:
                            score = value
                            break
                    except ValueError:
                        continue
            
            # If we have both analyses, use the score difference as a factor
            analysis_score_diff = 0.0
            if original_analysis and modified_analysis:
                analysis_score_diff = modified_score - original_score
                
                # Factor in the analysis score difference (give it 40% weight)
                combined_score = (score * 0.6) + (max(0, analysis_score_diff) * 0.4)
                
                # Cap at 1.0
                score = min(1.0, max(0.0, combined_score))
            
            return {
                "score": score,
                "analysis": eval_content,
                "original_analysis": original_analysis,
                "modified_analysis": modified_analysis,
                "original_score": original_score if original_analysis else None,
                "modified_score": modified_score if modified_analysis else None,
                "score_improvement": analysis_score_diff if original_analysis and modified_analysis else None
            }
        except Exception as e:
            logger.error(f"Error evaluating improvement: {e}")
            return {
                "score": 0.0,
                "error": str(e),
                "analysis": f"Failed to evaluate improvement: {str(e)}"
            }
    
    async def _revert_changes(self, component_path: str) -> Dict[str, Any]:
        """Revert changes if they don't pass tests or evaluation."""
        full_path = self.workspace_dir / component_path
        backup_path = f"{full_path}.bak"
        
        try:
            # Check if backup exists
            if not Path(backup_path).exists():
                return {
                    "success": False,
                    "error": f"Backup file not found: {backup_path}"
                }
            
            # Restore from backup
            with open(backup_path, 'r') as src, open(full_path, 'w') as dst:
                dst.write(src.read())
            
            logger.info(f"Reverted changes to {component_path} from backup")
            
            return {
                "success": True,
                "component_path": component_path
            }
        except Exception as e:
            logger.error(f"Error reverting changes to {component_path}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _document_improvement(self, 
                             component_path: str, 
                             improvement_type: str,
                             improvement_plan: Dict[str, Any],
                             evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """Document the improvement for future reference."""
        # Generate documentation
        doc_prompt = f"""
        Create documentation for the improvement made to component: {component_path}
        Improvement type: {improvement_type}
        
        Provide:
        1. A concise summary of the changes (2-3 sentences)
        2. Key improvements made
        3. Technical details of the implementation
        4. Benefits to the system
        
        Keep the documentation clear, accurate, and focused on the most important aspects.
        """
        
        doc_response = await self.workflow.mcp.process_request_async(
            prompt=doc_prompt,
            system="You are an expert technical writer who creates clear, concise documentation of code changes. Your documentation is accurate, informative, and accessible to other developers.",
            context={
                "improvement_plan": improvement_plan,
                "evaluation": evaluation,
                "component_path": component_path,
                "improvement_type": improvement_type
            },
            max_tokens=1024
        )
        
        documentation = {
            "summary": doc_response.get("content", ""),
            "component_path": component_path,
            "improvement_type": improvement_type,
            "evaluation_score": evaluation["score"],
            "timestamp": time.time()
        }
        
        # Save documentation to file
        docs_dir = self.workspace_dir / "docs" / "improvements"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        doc_file_name = f"{Path(component_path).stem}_{improvement_type}_{int(time.time())}.md"
        doc_path = docs_dir / doc_file_name
        
        with open(doc_path, 'w') as f:
            f.write(f"# Improvement Documentation: {component_path}\n\n")
            f.write(f"**Improvement Type**: {improvement_type}\n")
            f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Evaluation Score**: {evaluation['score']:.2f}\n\n")
            f.write(documentation["summary"])
        
        return documentation
    
    def _store_improvement_in_memory(self, 
                              improvement_id: str,
                              component_path: str, 
                              improvement_type: str,
                              code_changes: Dict[str, Any],
                              evaluation: Dict[str, Any],
                              documentation: Dict[str, Any]):
        """Store the improvement details in memory for future reference."""
        # Create metadata
        metadata = {
            "type": "improvement",
            "improvement_id": improvement_id,
            "component_path": component_path,
            "improvement_type": improvement_type,
            "evaluation_score": evaluation["score"],
            "timestamp": time.time()
        }
        
        # Store in memory
        self.workflow.memory_manager.add_semantic_memory(
            content=documentation["summary"],
            metadata=metadata
        )
        
        logger.info(f"Stored improvement {improvement_id} in memory system")
    
    async def run_improvement_cycle(self, 
                             targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run a complete improvement cycle on multiple targets.
        
        Args:
            targets: List of improvement targets with component_path and improvement_type
        
        Returns:
            Dictionary with cycle results
        """
        results = []
        
        for target in targets:
            component_path = target["component_path"]
            improvement_type = target["improvement_type"]
            custom_instructions = target.get("custom_instructions")
            
            logger.info(f"Improving component {component_path} ({improvement_type})")
            
            # Skip if max iterations reached
            if self.improvement_stats["attempts"] >= self.max_iterations:
                logger.warning(f"Maximum iterations reached ({self.max_iterations}), skipping remaining targets")
                break
            
            # Attempt improvement
            result = await self.improve_component(
                component_path=component_path,
                improvement_type=improvement_type,
                custom_instructions=custom_instructions
            )
            
            results.append(result)
            
            # Add a small delay between improvements
            await asyncio.sleep(1)
        
        # Generate cycle summary
        successful_count = sum(1 for r in results if r.get("success", False))
        failed_count = len(results) - successful_count
        
        summary = {
            "total_targets": len(targets),
            "completed": len(results),
            "successful": successful_count,
            "failed": failed_count,
            "stats": self.improvement_stats,
            "results": results,
            "success": successful_count > 0 and failed_count == 0  # Only true if all succeeded
        }
        
        if successful_count > 0:
            logger.info(f"Improvement cycle completed: {successful_count}/{len(results)} successful")
        else:
            logger.warning(f"Improvement cycle completed with no successful improvements")
        
        return summary
    
    async def run_three_js_improvement(self) -> Dict[str, Any]:
        """Run a targeted improvement cycle for THREE.js visualization."""
        targets = [
            {
                "component_path": "src/vot1/dashboard/static/js/three-visualization.js",
                "improvement_type": "visualization",
                "custom_instructions": """
                Focus on creating a cyberpunk aesthetic with:
                1. Neon color scheme with bright blues, pinks, and purples
                2. Glow effects around nodes and links
                3. Grid-like background elements
                4. Futuristic particle effects
                5. Improved performance for larger memory graphs
                """
            },
            {
                "component_path": "src/vot1/dashboard/static/js/dashboard.js",
                "improvement_type": "features",
                "custom_instructions": """
                Enhance the dashboard interface to:
                1. Better display node details and relationships
                2. Provide more intuitive navigation controls
                3. Add filtering and search capabilities
                4. Integrate with memory system improvements
                5. Maintain a consistent cyberpunk theme
                """
            }
        ]
        
        return await self.run_improvement_cycle(targets)
    
    async def run_memory_improvement(self) -> Dict[str, Any]:
        """Run a targeted improvement cycle for memory system."""
        targets = [
            {
                "component_path": "src/vot1/memory.py",
                "improvement_type": "performance",
                "custom_instructions": """
                Enhance the memory system with:
                1. More efficient vector storage and retrieval
                2. Better handling of large memory collections
                3. Optimized search algorithms
                4. Improved caching mechanisms
                5. Enhanced integration with OWL reasoning
                """
            }
        ]
        
        return await self.run_improvement_cycle(targets)
    
    async def run_owl_improvement(self) -> Dict[str, Any]:
        """Run a targeted improvement cycle for OWL reasoning."""
        targets = [
            {
                "component_path": "src/vot1/owl_reasoning.py",
                "improvement_type": "features",
                "custom_instructions": """
                Enhance the OWL reasoning capabilities with:
                1. Deeper integration with memory system
                2. More sophisticated reasoning patterns
                3. Better handling of uncertainty
                4. Improved performance on large knowledge graphs
                5. Enhanced ability to reason about code
                """
            }
        ]
        
        return await self.run_improvement_cycle(targets)
    
    async def run_self_improvement(self) -> Dict[str, Any]:
        """Run a self-improvement cycle on the agent's own code."""
        targets = [
            {
                "component_path": "src/vot1/self_improvement_agent.py",
                "improvement_type": "architecture",
                "custom_instructions": """
                Enhance the self-improvement agent with:
                1. More sophisticated evaluation metrics
                2. Better safety mechanisms
                3. Enhanced learning from past improvements
                4. More efficient code generation capabilities
                5. Deeper integration with memory and reasoning systems
                """
            }
        ]
        
        return await self.run_improvement_cycle(targets)
    
    async def run_full_improvement_cycle(self) -> Dict[str, Any]:
        """Run a complete improvement cycle across all major components."""
        logger.info("Starting full improvement cycle")
        
        results = {}
        
        # Step 1: Improve OWL reasoning
        logger.info("Step 1: Improving OWL reasoning")
        results["owl"] = await self.run_owl_improvement()
        
        # Step 2: Improve memory system
        logger.info("Step 2: Improving memory system")
        results["memory"] = await self.run_memory_improvement()
        
        # Step 3: Improve THREE.js visualization
        logger.info("Step 3: Improving THREE.js visualization")
        results["three_js"] = await self.run_three_js_improvement()
        
        # Step 4: Self-improvement
        logger.info("Step 4: Self-improvement")
        results["self"] = await self.run_self_improvement()
        
        # Commit changes to GitHub if enabled
        if self.workflow.github_enabled:
            improved_files = []
            
            # Collect all successfully improved files
            for category, result in results.items():
                for item in result.get("results", []):
                    if item.get("success", False):
                        improved_files.append(item["component"])
            
            if improved_files:
                logger.info(f"Committing {len(improved_files)} improved files to GitHub")
                
                commit_result = self.workflow._handle_commit_changes(
                    commit_message="VOT1 Self-Improvement Agent: Automated code enhancements",
                    files=improved_files
                )
                
                results["github_commit"] = commit_result
        
        return {
            "success": True,
            "cycles": results,
            "stats": self.improvement_stats,
            "improved_components": len(self.improvement_history)
        }


async def main():
    """Main function to run the self-improvement agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run VOT1 self-improvement agent")
    
    parser.add_argument("--iterations", type=int, default=5,
                      help="Maximum number of improvement iterations")
    parser.add_argument("--thinking-tokens", type=int, default=4096,
                      help="Maximum tokens to use for thinking stream")
    parser.add_argument("--threshold", type=float, default=0.2,
                      help="Minimum improvement threshold (0.0-1.0)")
    parser.add_argument("--no-safety", action="store_true",
                      help="Disable safety checks")
    parser.add_argument("--target", type=str, 
                      choices=["all", "owl", "memory", "three-js", "self"],
                      default="all", help="Which component to improve")
    
    args = parser.parse_args()
    
    # Create the self-improvement agent
    agent = SelfImprovementAgent(
        max_thinking_tokens=args.thinking_tokens,
        max_iterations=args.iterations,
        improvement_threshold=args.threshold,
        safety_checks=not args.no_safety
    )
    
    # Run the selected improvement workflow
    if args.target == "all":
        results = await agent.run_full_improvement_cycle()
    elif args.target == "owl":
        results = await agent.run_owl_improvement()
    elif args.target == "memory":
        results = await agent.run_memory_improvement()
    elif args.target == "three-js":
        results = await agent.run_three_js_improvement()
    elif args.target == "self":
        results = await agent.run_self_improvement()
    
    # Print results summary
    import json
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 