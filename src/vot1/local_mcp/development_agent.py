#!/usr/bin/env python3
"""
Development Agent for the VOTai MCP Agent Ecosystem.

This module provides a specialized agent for development tasks,
including code generation, repository analysis, and code snippets generation.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import traceback

from .agent import FeedbackAgent
from .ascii_art import get_votai_ascii
from .github_integration import GitHubIntegration
from .agent_memory_manager import AgentMemoryManager

logger = logging.getLogger(__name__)

class AgentMetrics:
    """
    Collect and report agent performance metrics.
    
    This class tracks various metrics related to task execution, success rates,
    response times, and more to help monitor agent performance.
    """
    
    def __init__(self):
        """Initialize the metrics tracker."""
        self.metrics = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "fallbacks_used": 0,
            "average_response_time": 0,
            "response_times": [],
            "task_types": {}
        }
        self.start_time = time.time()
    
    def record_task_start(self, task_id: str, task_type: str):
        """
        Record the start of a task.
        
        Args:
            task_id: ID of the task
            task_type: Type of the task
        """
        self.metrics["tasks_processed"] += 1
        
        # Track by task type
        if task_type not in self.metrics["task_types"]:
            self.metrics["task_types"][task_type] = {
                "count": 0,
                "succeeded": 0,
                "failed": 0,
                "fallbacks": 0,
                "average_time": 0,
                "response_times": []
            }
        self.metrics["task_types"][task_type]["count"] += 1
    
    def record_task_completion(self, task_id: str, task_type: str, success: bool, 
                              duration: float, used_fallback: bool = False):
        """
        Record the completion of a task.
        
        Args:
            task_id: ID of the task
            task_type: Type of the task
            success: Whether the task was successful
            duration: Time taken to complete the task (seconds)
            used_fallback: Whether a fallback mechanism was used
        """
        if success:
            self.metrics["tasks_succeeded"] += 1
            self.metrics["task_types"][task_type]["succeeded"] += 1
        else:
            self.metrics["tasks_failed"] += 1
            self.metrics["task_types"][task_type]["failed"] += 1
            
        if used_fallback:
            self.metrics["fallbacks_used"] += 1
            self.metrics["task_types"][task_type]["fallbacks"] += 1
            
        # Update response time metrics
        self.metrics["response_times"].append(duration)
        self.metrics["average_response_time"] = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        
        # Update task type metrics
        type_metrics = self.metrics["task_types"][task_type]
        type_metrics["response_times"].append(duration)
        type_metrics["average_time"] = sum(type_metrics["response_times"]) / len(type_metrics["response_times"])
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Returns:
            Dict containing summary metrics
        """
        total_tasks = self.metrics["tasks_processed"]
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_duration(uptime),
            "tasks_processed": total_tasks,
            "tasks_per_minute": (total_tasks / (uptime / 60)) if uptime > 0 else 0,
            "success_rate": (self.metrics["tasks_succeeded"] / max(1, total_tasks)) * 100,
            "fallback_rate": (self.metrics["fallbacks_used"] / max(1, total_tasks)) * 100,
            "average_response_time": self.metrics["average_response_time"],
            "task_types": {
                task_type: {
                    "count": metrics["count"],
                    "success_rate": (metrics["succeeded"] / max(1, metrics["count"])) * 100,
                    "fallback_rate": (metrics["fallbacks"] / max(1, metrics["count"])) * 100,
                    "average_time": metrics["average_time"]
                }
                for task_type, metrics in self.metrics["task_types"].items()
            }
        }
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format a duration in seconds to a human-readable string.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)

class DevelopmentAgent(FeedbackAgent):
    """
    A specialized agent for software development tasks.
    
    The VOTai DevelopmentAgent extends the base FeedbackAgent with capabilities
    specifically designed for software development, including:
    
    - Code generation and improvement
    - Repository analysis and exploration
    - Code review and quality assessment
    - Documentation generation
    - Testing and debugging assistance
    - Dependency management
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(self, orchestrator, name: str = "DevelopmentAgent"):
        """
        Initialize a new development agent.
        
        Args:
            orchestrator: The MCPOrchestrator instance
            name: Name of the agent (default: "DevelopmentAgent")
        """
        super().__init__(orchestrator, name)
        
        self.capabilities = [
            "code_generation",
            "code_review",
            "repository_analysis",
            "ecosystem_analysis",
            "performance_analysis",
            "recommendations",
            "task_management"
        ]
        
        self.metrics = AgentMetrics()
        
        # Initialize memory manager for tracking agent activities
        try:
            self.memory_manager = AgentMemoryManager()
            logger.info(f"Initialized AgentMemoryManager for {name}")
            
            # Record agent initialization
            self.memory_manager.record_agent_activity(
                agent_id=self.id,
                activity_type="initialization",
                details={
                    "name": name,
                    "capabilities": self.capabilities,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to initialize AgentMemoryManager: {e}")
            logger.info("Continuing without advanced memory tracking...")
            self.memory_manager = None
        
        # Initialize development-specific attributes
        self.current_repository = None
        self.language_preferences = {}
        self.code_style_guides = {}
        
        # Default settings
        self.max_task_queue_size = 50
        self.max_response_size = 10000
        
        logger.info(f"Development Agent '{name}' (ID: {self.id}) initialized with capabilities: {self.capabilities}")
        
        # Display a medium-sized VOTai signature for the Development Agent
        self.display_signature(size="medium")
        
        # Initialize GitHub integration
        self.github_integration = GitHubIntegration(self)
    
    def set_language_preference(self, language: str, settings: Dict[str, Any]):
        """
        Set preferences for a specific programming language.
        
        Args:
            language: Programming language (e.g., "python", "javascript")
            settings: Dictionary of language-specific settings
        """
        self.language_preferences[language.lower()] = settings
        self.logger.info(f"Set language preferences for {language}")
    
    def set_code_style_guide(self, language: str, style_guide: Dict[str, Any]):
        """
        Set code style guide for a specific programming language.
        
        Args:
            language: Programming language (e.g., "python", "javascript")
            style_guide: Dictionary of style guide rules
        """
        self.code_style_guides[language.lower()] = style_guide
        self.logger.info(f"Set code style guide for {language}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        metrics_summary = self.metrics.get_summary()
        
        # Record metrics in memory manager
        if self.memory_manager:
            self.memory_manager.record_agent_metrics(self.id, metrics_summary)
            
            # If available, add memory statistics to the metrics
            try:
                memory_info = self.memory_manager.get_memory_info()
                metrics_summary["memory_statistics"] = {
                    "categories": memory_info.get("categories", {}),
                    "total_memory_size": memory_info.get("total_size", 0),
                    "activity_count": len(self.memory_manager.list_keys(self.memory_manager.AGENT_ACTIVITY_CATEGORY)),
                    "task_count": len(self.memory_manager.list_keys(self.memory_manager.AGENT_TASKS_CATEGORY)),
                    "knowledge_count": len(self.memory_manager.list_keys(self.memory_manager.AGENT_KNOWLEDGE_CATEGORY))
                }
            except Exception as e:
                logger.warning(f"Error adding memory statistics to metrics: {e}")
        
        return metrics_summary
    
    def _handle_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a task.
        
        Args:
            task_id: ID of the task
            task_data: Task data including type and parameters
        """
        task_type = task_data.get("type", "")
        
        # Record task start in memory
        if self.memory_manager:
            self.memory_manager.record_task(
                agent_id=self.id,
                task_id=task_id,
                task_type=task_type,
                task_data=task_data
            )
        
        start_time = time.time()
        self.metrics.record_task_start(task_id, task_type)
        
        try:
            # Record task activity
            if self.memory_manager:
                self.memory_manager.record_agent_activity(
                    agent_id=self.id,
                    activity_type="task_start",
                    details={
                        "task_id": task_id,
                        "task_type": task_type,
                        "start_time": datetime.now().isoformat()
                    }
                )
            
            # Map task type to handler
            handler_map = {
                "generate_code": self._handle_generate_code_task,
                "review_code": self._handle_review_code_task,
                "analyze_repository": self._handle_analyze_repository_task,
                "analyze_ecosystem": self._handle_analyze_ecosystem_task,
                "analyze_performance": self._handle_analyze_performance_task,
                "generate_recommendations": self._handle_generate_recommendations_task,
                "analyze_pull_request": self._handle_analyze_pull_request_task,
                "get_metrics": self._handle_get_metrics_task
            }
            
            handler = handler_map.get(task_type)
            if handler:
                # Update task status to in_progress
                if self.memory_manager:
                    self.memory_manager.update_task_status(task_id, "in_progress")
                
                # Call the handler
                handler(task_id, task_data)
                
                # Record task completion time
                end_time = time.time()
                duration = end_time - start_time
                self.metrics.record_task_completion(task_id, task_type, True, duration)
                
                # Update task status to completed
                if self.memory_manager:
                    self.memory_manager.update_task_status(
                        task_id, 
                        "completed",
                        result=self.task_results.get(task_id)
                    )
                    
                    # Record task completion activity
                    self.memory_manager.record_agent_activity(
                        agent_id=self.id,
                        activity_type="task_complete",
                        details={
                            "task_id": task_id,
                            "task_type": task_type,
                            "duration": duration,
                            "success": True
                        }
                    )
            else:
                # Handle unsupported task type
                error_message = f"Unsupported task type: {task_type}"
                self.set_task_result(task_id, {"error": error_message})
                logger.error(error_message)
                
                # Record task error
                if self.memory_manager:
                    self.memory_manager.update_task_status(
                        task_id, 
                        "failed",
                        result={"error": error_message}
                    )
                
                # Record metrics
                end_time = time.time()
                duration = end_time - start_time
                self.metrics.record_task_completion(task_id, task_type, False, duration)
                
                # Record task failure activity
                if self.memory_manager:
                    self.memory_manager.record_agent_activity(
                        agent_id=self.id,
                        activity_type="task_error",
                        details={
                            "task_id": task_id,
                            "task_type": task_type,
                            "error": error_message,
                            "duration": duration
                        }
                    )
        except Exception as e:
            # Handle unexpected errors
            error_message = f"Error handling task {task_id} ({task_type}): {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            
            # Set task result
            self.set_task_result(task_id, {"error": error_message})
            
            # Record metrics
            end_time = time.time()
            duration = end_time - start_time
            self.metrics.record_task_completion(task_id, task_type, False, duration)
            
            # Update task status in memory
            if self.memory_manager:
                self.memory_manager.update_task_status(
                    task_id, 
                    "failed",
                    result={"error": error_message}
                )
                
                # Record error activity
                self.memory_manager.record_agent_activity(
                    agent_id=self.id,
                    activity_type="task_error",
                    details={
                        "task_id": task_id,
                        "task_type": task_type,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "duration": duration
                    }
                )
    
    def _handle_get_metrics_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a request for agent metrics.
        
        Args:
            task_id: ID of the task
            task_data: Task data
        """
        try:
            # Regular metrics from the built-in tracker
            metrics = self.metrics.get_summary()
            
            # Add additional data if using the advanced memory manager
            if self.memory_manager:
                # Generate a report from the memory manager
                agent_report = self.memory_manager.generate_agent_report(self.id)
                metrics["detailed_report"] = agent_report
                
                # Add agent activity summary
                activity_keys = self.memory_manager.list_keys(self.memory_manager.AGENT_ACTIVITY_CATEGORY)
                recent_activities = []
                
                for key in activity_keys[:10]:  # Get 10 most recent activities
                    if key.startswith(f"{self.id}_"):
                        activity = self.memory_manager.load(self.memory_manager.AGENT_ACTIVITY_CATEGORY, key)
                        if activity:
                            recent_activities.append(activity)
                
                # Sort by timestamp (newest first)
                recent_activities.sort(key=lambda a: a["timestamp"], reverse=True)
                metrics["recent_activities"] = recent_activities
            
            # Set task result
            self.set_task_result(task_id, metrics)
            
            # Log summary
            logger.info(f"Metrics retrieved for agent {self.id}: {len(metrics)} data points")
        except Exception as e:
            error_message = f"Error getting metrics: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            self.set_task_result(task_id, {"error": error_message})
    
    def _handle_generate_code_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a code generation task.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing language, description, and requirements
        """
        logger.info(f"Handling generate_code task {task_id}")
        
        language = task_data.get("language", "python")
        description = task_data.get("description", "")
        requirements = task_data.get("requirements", [])
        
        # Check if we should force a fallback (for testing purposes)
        force_fallback = task_data.get("_force_fallback", False)
        
        try:
            if force_fallback:
                logger.info(f"Forcing fallback for task {task_id} (testing mode)")
                fallback_code = self._generate_fallback_code(language, description, requirements)
                
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "code",
                    "code": fallback_code,
                    "language": language,
                    "is_fallback": True,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent fallback code for task {task_id}")
                return
            
            # Prepare prompt for generating code
            prompt = f"Generate {language} code for the following task: {description}\n\n"
            if requirements:
                prompt += "Requirements:\n"
                for req in requirements:
                    prompt += f"- {req}\n"
            
            # Call the external service
            # Use a try-except block to handle service failures
            try:
                response = self.mcp_functions["mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"]({
                    "params": {
                        "systemContent": f"You are a senior {language} developer. Generate high-quality, well-documented code.",
                        "userContent": prompt,
                        "temperature": 0.2
                    }
                })
                
                logger.debug(f"Service response: {response}")
                
                # Check if the service call was successful
                if not response or "response" not in response:
                    logger.warning(f"Service call failed for task {task_id}")
                    fallback_code = self._generate_fallback_code(language, description, requirements)
                    
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "code",
                        "code": fallback_code,
                        "language": language,
                        "is_fallback": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Sent fallback code for task {task_id}")
                    return
                
                code_text = self._extract_code_blocks(response["response"])
                
                # If no code blocks found, use fallback
                if not code_text:
                    logger.warning(f"No code blocks found in service response for task {task_id}")
                    fallback_code = self._generate_fallback_code(language, description, requirements)
                    
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "code",
                        "code": fallback_code,
                        "language": language,
                        "is_fallback": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Sent fallback code for task {task_id}")
                    return
                
                # Send response
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "code",
                    "code": code_text,
                    "language": language,
                    "is_fallback": False,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent code for task {task_id}")
                
            except Exception as e:
                logger.error(f"Error calling external service for task {task_id}: {e}")
                fallback_code = self._generate_fallback_code(language, description, requirements)
                
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "code",
                    "code": fallback_code,
                    "language": language,
                    "is_fallback": True,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent fallback code for task {task_id}")
                
        except Exception as e:
            error_message = f"Error handling generate_code task {task_id}: {str(e)}"
            logger.error(error_message)
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_fallback_code(self, language: str, description: str, requirements: List[str]) -> str:
        """
        Generate fallback code when external services fail.
        
        Args:
            language: Programming language
            description: Description of the code to generate
            requirements: Specific requirements for the code
            
        Returns:
            Template code as a string
        """
        # Extract function name from description
        func_name = self._extract_function_name(description)
        
        # Generate docstring from description and requirements
        docstring = f'"""\n{description}\n\n'
        if requirements:
            docstring += "Requirements:\n"
            for req in requirements:
                docstring += f"- {req}\n"
        docstring += '"""'
        
        # Generate language-specific templates
        if language.lower() == "python":
            return f"""def {func_name}(parameters):
    {docstring}
    # TODO: Implement {description}
    
    # This is a fallback implementation
    # Please replace with actual implementation
    
    # Basic error handling
    try:
        result = None
        # Implementation goes here
        return result
    except Exception as e:
        print(f"Error: {{e}}")
        return None
"""
        elif language.lower() == "javascript":
            return f"""/**
 * {description}
 * 
 * Requirements:
{chr(10).join([f' * - {req}' for req in requirements])}
 */
function {func_name}(parameters) {{
    // TODO: Implement {description}
    
    // This is a fallback implementation
    // Please replace with actual implementation
    
    // Basic error handling
    try {{
        let result = null;
        // Implementation goes here
        return result;
    }} catch (error) {{
        console.error(`Error: ${{error}}`);
        return null;
    }}
}}
"""
        else:
            # Generic template for other languages
            return f"""// Function: {func_name}
// Description: {description}
// Requirements: {', '.join(requirements)}
//
// This is a fallback implementation
// Please replace with actual implementation
"""
    
    def _extract_function_name(self, description: str) -> str:
        """
        Extract a function name from a description.
        
        Args:
            description: Description of the function
            
        Returns:
            Suitable function name
        """
        # Remove special characters and convert to lowercase
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', description.lower())
        
        # Extract key words
        words = cleaned.split()
        
        # Filter out common words
        common_words = {'a', 'an', 'the', 'to', 'for', 'that', 'which', 'with', 'and', 'or', 'function', 'method'}
        words = [word for word in words if word not in common_words]
        
        # If no words left, use a generic name
        if not words:
            return "function_implementation"
            
        # Use first 3 words (or fewer if not enough)
        words = words[:min(3, len(words))]
        
        # Join with underscores
        return '_'.join(words)
    
    def _handle_review_code_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a code review task.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing code to review, language, and criteria
        """
        logger.info(f"Handling review_code task {task_id}")
        
        code = task_data.get("code", "")
        language = task_data.get("language", "python")
        criteria = task_data.get("criteria", ["readability", "efficiency", "maintainability", "security"])
        
        # Check if we should force a fallback (for testing purposes)
        force_fallback = task_data.get("_force_fallback", False)
        
        if not code:
            error_message = "No code provided for review"
            logger.error(error_message)
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
            return
        
        try:
            if force_fallback:
                logger.info(f"Forcing fallback for task {task_id} (testing mode)")
                fallback_review = self._generate_fallback_review(code, language, criteria)
                
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "review",
                    "review": fallback_review,
                    "language": language,
                    "is_fallback": True,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent fallback review for task {task_id}")
                return
                
            # Prepare the prompt for code review
            criteria_str = ", ".join(criteria)
            prompt = f"""Please review the following {language} code based on these criteria: {criteria_str}.

```{language}
{code}
```

Provide a detailed code review including:
1. Summary of the code's purpose
2. Analysis of each criterion
3. Specific improvement suggestions with examples
4. Overall assessment
"""
            
            # Call the external service for code review
            try:
                response = self.mcp_functions["mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"]({
                    "params": {
                        "systemContent": f"You are an expert code reviewer specialized in {language}. Provide detailed, constructive feedback.",
                        "userContent": prompt,
                        "temperature": 0.3
                    }
                })
                
                logger.debug(f"Service response: {response}")
                
                # Check if the service call was successful
                if not response or "response" not in response:
                    logger.warning(f"Service call failed for task {task_id}")
                    fallback_review = self._generate_fallback_review(code, language, criteria)
                    
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "review",
                        "review": fallback_review,
                        "language": language,
                        "is_fallback": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Sent fallback review for task {task_id}")
                    return
                
                review_text = response["response"]
                
                # If review is empty, use fallback
                if not review_text.strip():
                    logger.warning(f"Empty review from service for task {task_id}")
                    fallback_review = self._generate_fallback_review(code, language, criteria)
                    
                    self.response_queue.put({
                        "task_id": task_id,
                        "type": "review",
                        "review": fallback_review,
                        "language": language,
                        "is_fallback": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Sent fallback review for task {task_id}")
                    return
                
                # Send response
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "review",
                    "review": review_text,
                    "language": language,
                    "is_fallback": False,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent review for task {task_id}")
                
            except Exception as e:
                logger.error(f"Error calling external service for task {task_id}: {e}")
                fallback_review = self._generate_fallback_review(code, language, criteria)
                
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "review",
                    "review": fallback_review,
                    "language": language,
                    "is_fallback": True,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Sent fallback review for task {task_id}")
                
        except Exception as e:
            error_message = f"Error handling review_code task {task_id}: {str(e)}"
            logger.error(error_message)
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _generate_fallback_review(self, code: str, language: str, criteria: List[str]) -> str:
        """
        Generate fallback code review when external services fail.
        
        Args:
            code: Code to review
            language: Programming language
            criteria: Review criteria
            
        Returns:
            Basic code review as a string
        """
        # Basic static analysis
        code_lines = code.strip().split('\n')
        line_count = len(code_lines)
        
        # Extract function/class names - basic regex approach
        if language.lower() == "python":
            functions = re.findall(r'def\s+(\w+)\s*\(', code)
            classes = re.findall(r'class\s+(\w+)\s*[:\(]', code)
        elif language.lower() in ["javascript", "typescript"]:
            functions = re.findall(r'function\s+(\w+)\s*\(', code)
            functions.extend(re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', code))
            classes = re.findall(r'class\s+(\w+)\s*[{\(]', code)
        else:
            functions = []
            classes = []
        
        # Basic check for comments
        comment_lines = 0
        if language.lower() == "python":
            comment_lines = sum(1 for line in code_lines if line.strip().startswith('#') or line.strip().startswith('"""'))
        elif language.lower() in ["javascript", "typescript", "java", "c++", "c#"]:
            comment_lines = sum(1 for line in code_lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*'))
        
        # Generate review
        review = f"""# Code Review (Fallback)

This is an automated fallback review generated for {line_count} lines of {language} code.

## Code Structure
- Code length: {line_count} lines
- Number of functions identified: {len(functions)}
- Number of classes identified: {len(classes)}
- Comment lines: {comment_lines} ({comment_lines/max(1, line_count)*100:.1f}% of code)

## Analysis by Criteria
"""

        for criterion in criteria:
            review += f"\n### {criterion.capitalize()}\n"
            
            if criterion.lower() == "readability":
                ratio = comment_lines / max(1, line_count)
                if ratio < 0.1:
                    review += "- Low comment ratio - consider adding more documentation\n"
                else:
                    review += "- Acceptable comment ratio\n"
                
                # Check for very long lines
                long_lines = sum(1 for line in code_lines if len(line) > 80)
                if long_lines > 0:
                    review += f"- Found {long_lines} lines exceeding 80 characters - consider breaking into shorter lines\n"
                
            elif criterion.lower() == "efficiency":
                review += "- Automated static analysis cannot determine efficiency - please review algorithms and data structures manually\n"
                
            elif criterion.lower() == "security":
                review += "- Automated static analysis cannot perform security review - please manually check for common vulnerabilities\n"
                
            elif criterion.lower() == "error handling":
                # Basic check for try/except or try/catch
                if language.lower() == "python":
                    has_error_handling = any("try:" in line for line in code_lines)
                elif language.lower() in ["javascript", "typescript", "java", "c++", "c#"]:
                    has_error_handling = any("try {" in line or "try{" in line for line in code_lines)
                else:
                    has_error_handling = False
                    
                if has_error_handling:
                    review += "- Contains error handling constructs\n"
                else:
                    review += "- No error handling detected - consider adding appropriate error handling\n"
        
        review += """
## Note
This is a fallback review generated due to service unavailability. 
For a more comprehensive review, please try again later.
"""
        return review
    
    def _handle_analyze_repository_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a repository analysis task.
        
        Args:
            task_id: ID of the task
            task_data: Task data including repository information
        """
        try:
            repo = task_data.get("repo", "")
            depth = task_data.get("depth", "summary")
            focus = task_data.get("focus", ["structure", "dependencies", "quality"])
            
            if not repo:
                raise ValueError("Repository parameter is required")
            
            logger.info(f"Analyzing repository: {repo} (depth: {depth}, focus: {focus})")
            
            # Parse owner and repo
            parts = repo.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid repository format: {repo} (expected format: owner/repo)")
            
            owner, repo_name = parts
            
            # Get GitHub integration
            github = GitHubIntegration(self.orchestrator.bridge)
            
            # Get repository info
            repo_info = github.get_repository(owner, repo_name)
            if not repo_info.get("successful", False):
                raise ValueError(f"Error getting repository info: {repo_info.get('error', 'Unknown error')}")
            
            # Record knowledge about this repository if using advanced memory
            if self.memory_manager:
                self.memory_manager.store_agent_knowledge(
                    agent_id=self.id,
                    knowledge_type="repository_info",
                    content=repo_info.get("data", {}),
                    tags=[owner, repo_name, "github", "repository"]
                )
            
            # Analyze the repository (simplified for this example)
            # In a real implementation, this would do more advanced analysis
            analysis_result = {
                "repository": repo,
                "analysis_depth": depth,
                "focus_areas": focus,
                "timestamp": datetime.now().isoformat(),
                "basic_info": repo_info.get("data", {}),
                "analysis": {
                    "structure": {
                        "languages": repo_info.get("data", {}).get("language", "Unknown"),
                        "default_branch": repo_info.get("data", {}).get("default_branch", "main"),
                        "size": repo_info.get("data", {}).get("size", 0),
                        "has_issues": repo_info.get("data", {}).get("has_issues", False),
                        "has_wiki": repo_info.get("data", {}).get("has_wiki", False)
                    },
                    "activity": {
                        "stars": repo_info.get("data", {}).get("stargazers_count", 0),
                        "forks": repo_info.get("data", {}).get("forks_count", 0),
                        "open_issues": repo_info.get("data", {}).get("open_issues_count", 0),
                        "created_at": repo_info.get("data", {}).get("created_at", ""),
                        "updated_at": repo_info.get("data", {}).get("updated_at", ""),
                        "pushed_at": repo_info.get("data", {}).get("pushed_at", "")
                    }
                }
            }
            
            # Store the analysis result in the agent's memory
            if self.memory_manager:
                knowledge_id = self.memory_manager.store_agent_knowledge(
                    agent_id=self.id,
                    knowledge_type="repository_analysis",
                    content=analysis_result,
                    tags=[owner, repo_name, "github", "analysis"] + focus
                )
                logger.info(f"Stored repository analysis in memory with ID: {knowledge_id}")
                analysis_result["knowledge_id"] = knowledge_id
            
            # Set task result
            self.set_task_result(task_id, analysis_result)
            
            logger.info(f"Repository analysis completed for {repo}")
        except Exception as e:
            error_message = f"Error analyzing repository: {str(e)}"
            logger.error(error_message)
            traceback.print_exc()
            self.set_task_result(task_id, {"error": error_message})
    
    def _handle_analyze_ecosystem_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a request to analyze the ecosystem architecture.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing system_info, analysis_depth, focus_areas, and AI model parameters
        """
        logger.info(f"Handling analyze_ecosystem task {task_id}")
        
        system_info = task_data.get("system_info", {})
        analysis_depth = task_data.get("analysis_depth", "comprehensive")
        focus_areas = task_data.get("focus_areas", [])
        ai_model = task_data.get("ai_model", "claude-3-7-sonnet")
        mode = task_data.get("mode", "stream_hybrid")
        max_tokens = task_data.get("max_tokens", 120000)
        thinking_tokens = task_data.get("thinking_tokens", 60000)
        
        try:
            # Construct a detailed prompt for the analysis
            prompt = f"""
# MCP Agent Ecosystem Analysis Request

## System Information
```json
{json.dumps(system_info, indent=2)}
```

## Analysis Requirements
- Depth: {analysis_depth}
- Focus Areas: {', '.join(focus_areas)}

## Analysis Task
Please provide a comprehensive analysis of the MCP Agent Ecosystem architecture based on the system information provided.
Your analysis should cover:

1. **Architectural Overview**
   - System components and their relationships
   - Communication patterns
   - Data flow

2. **Component Analysis**
   - Agent types and their capabilities
   - Services and their responsibilities
   - Integration points

3. **Design Pattern Evaluation**
   - Identification of design patterns
   - Evaluation of pattern appropriateness
   - Suggestions for alternative patterns where applicable

4. **Scalability Assessment**
   - Bottlenecks and constraints
   - Horizontal and vertical scaling considerations
   - Resource utilization

5. **Reliability Analysis**
   - Failure points
   - Recovery mechanisms
   - Redundancy and fallback systems

6. **Integration Assessment**
   - External service integration
   - API design and usage
   - Data synchronization

Please structure your analysis in a clear, organized manner with headings, bullet points, and markdown formatting.
"""
            
            # Call Perplexity for the analysis
            logger.info("Calling Perplexity AI for ecosystem architecture analysis")
            response = self.mcp_functions["mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"]({
                "params": {
                    "systemContent": "You are an expert software architect specializing in distributed systems, multi-agent architectures, and AI ecosystems. Provide detailed, insightful analysis with practical recommendations.",
                    "userContent": prompt,
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
            })
            
            logger.debug(f"AI service response received for task {task_id}")
            
            # Extract the analysis
            if not response or "response" not in response:
                error_message = f"Failed to get analysis from AI service for task {task_id}"
                logger.error(error_message)
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "error",
                    "error": error_message,
                    "timestamp": datetime.now().isoformat()
                })
                return
                
            analysis = response["response"]
            
            # Send the analysis as a response
            self.response_queue.put({
                "task_id": task_id,
                "type": "ecosystem_analysis",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Sent ecosystem architecture analysis for task {task_id}")
            
        except Exception as e:
            error_message = f"Error analyzing ecosystem architecture: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _handle_analyze_performance_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a request to analyze the ecosystem performance.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing performance_data, analysis_depth, optimization_focus, and AI model parameters
        """
        logger.info(f"Handling analyze_performance task {task_id}")
        
        performance_data = task_data.get("performance_data", {})
        analysis_depth = task_data.get("analysis_depth", "comprehensive")
        optimization_focus = task_data.get("optimization_focus", [])
        ai_model = task_data.get("ai_model", "claude-3-7-sonnet")
        mode = task_data.get("mode", "stream_hybrid")
        max_tokens = task_data.get("max_tokens", 120000)
        thinking_tokens = task_data.get("thinking_tokens", 60000)
        
        try:
            # Construct a detailed prompt for the performance analysis
            prompt = f"""
# MCP Agent Ecosystem Performance Analysis Request

## Performance Data
```json
{json.dumps(performance_data, indent=2)}
```

## Analysis Requirements
- Depth: {analysis_depth}
- Optimization Focus: {', '.join(optimization_focus)}

## Analysis Task
Please provide a comprehensive analysis of the MCP Agent Ecosystem performance based on the metrics provided.
Your analysis should cover:

1. **Performance Overview**
   - Current performance metrics
   - Comparison to industry benchmarks (where applicable)
   - Overall assessment

2. **Response Time Analysis**
   - Task processing times
   - Bottlenecks identification
   - Optimization opportunities

3. **Throughput Assessment**
   - Task processing capacity
   - Concurrency levels
   - Scaling implications

4. **Resource Utilization**
   - CPU usage patterns
   - Memory usage patterns
   - Network utilization
   - Storage requirements

5. **Scalability Analysis**
   - Vertical scaling considerations
   - Horizontal scaling opportunities
   - Load balancing recommendations

6. **Optimization Recommendations**
   - Short-term quick wins
   - Medium-term improvements
   - Long-term architectural changes

Please provide specific, actionable recommendations for performance improvements with expected impact levels (high, medium, low).
Structure your analysis in a clear, organized manner with headings, bullet points, and markdown formatting.
"""
            
            # Call Perplexity for the performance analysis
            logger.info("Calling Perplexity AI for ecosystem performance analysis")
            response = self.mcp_functions["mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"]({
                "params": {
                    "systemContent": "You are an expert performance engineer specializing in distributed systems, AI applications, and high-performance computing. Provide detailed, data-driven analysis with practical optimization recommendations.",
                    "userContent": prompt,
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
            })
            
            logger.debug(f"AI service response received for task {task_id}")
            
            # Extract the analysis
            if not response or "response" not in response:
                error_message = f"Failed to get performance analysis from AI service for task {task_id}"
                logger.error(error_message)
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "error",
                    "error": error_message,
                    "timestamp": datetime.now().isoformat()
                })
                return
                
            analysis = response["response"]
            
            # Send the analysis as a response
            self.response_queue.put({
                "task_id": task_id,
                "type": "performance_analysis",
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Sent performance analysis for task {task_id}")
            
        except Exception as e:
            error_message = f"Error analyzing ecosystem performance: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _handle_generate_recommendations_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a request to generate improvement recommendations.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing analysis_data, recommendation_areas, and AI model parameters
        """
        logger.info(f"Handling generate_recommendations task {task_id}")
        
        analysis_data = task_data.get("analysis_data", {})
        recommendation_areas = task_data.get("recommendation_areas", [])
        ai_model = task_data.get("ai_model", "claude-3-7-sonnet")
        mode = task_data.get("mode", "stream_hybrid")
        max_tokens = task_data.get("max_tokens", 120000)
        thinking_tokens = task_data.get("thinking_tokens", 60000)
        
        try:
            # Construct a detailed prompt for generating recommendations
            prompt = f"""
# MCP Agent Ecosystem Improvement Recommendations Request

## Analysis Data
The following analyses have been performed on the ecosystem:

### Architecture Analysis
{analysis_data.get("architecture", "Architecture analysis not available.")}

### Performance Analysis
{analysis_data.get("performance", "Performance analysis not available.")}

### Agent Metrics
```json
{json.dumps(analysis_data.get("agent_metrics", {}), indent=2)}
```

## Recommendation Requirements
- Recommendation Areas: {', '.join(recommendation_areas)}

## Task
Based on the analyses provided, please generate comprehensive recommendations for improving the MCP Agent Ecosystem.
Your recommendations should cover:

1. **Architectural Improvements**
   - Component structure
   - Communication patterns
   - Design patterns

2. **Performance Optimizations**
   - Response time improvements
   - Throughput enhancements
   - Resource efficiency

3. **Reliability Enhancements**
   - Error handling
   - Fallback mechanisms
   - Self-healing capabilities

4. **Scalability Improvements**
   - Horizontal scaling strategies
   - Vertical scaling opportunities
   - Load distribution

5. **Integration Enhancements**
   - API improvements
   - Service integration patterns
   - Data synchronization

6. **Security Reinforcements**
   - Authentication mechanisms
   - Authorization policies
   - Data protection

For each recommendation, please provide:
- Clear problem statement
- Detailed solution description
- Implementation complexity (Low, Medium, High)
- Expected impact (Low, Medium, High)
- Implementation timeline (Short-term, Medium-term, Long-term)

Please structure your recommendations in a clear, organized manner with headings, bullet points, and markdown formatting.
Prioritize recommendations that will have the highest impact with the lowest implementation complexity.
"""
            
            # Call Perplexity for generating recommendations
            logger.info("Calling Perplexity AI for ecosystem improvement recommendations")
            response = self.mcp_functions["mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"]({
                "params": {
                    "systemContent": "You are an expert systems architect and performance engineer with deep expertise in AI agent ecosystems. Provide detailed, practical, and actionable recommendations based on the analyses provided.",
                    "userContent": prompt,
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
            })
            
            logger.debug(f"AI service response received for task {task_id}")
            
            # Extract the recommendations
            if not response or "response" not in response:
                error_message = f"Failed to get recommendations from AI service for task {task_id}"
                logger.error(error_message)
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "error",
                    "error": error_message,
                    "timestamp": datetime.now().isoformat()
                })
                return
                
            recommendations = response["response"]
            
            # Send the recommendations as a response
            self.response_queue.put({
                "task_id": task_id,
                "type": "recommendations",
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Sent improvement recommendations for task {task_id}")
            
        except Exception as e:
            error_message = f"Error generating ecosystem recommendations: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    def _extract_code_blocks(self, text: str, language: str = None) -> str:
        """
        Extract code blocks from markdown text.
        
        Args:
            text: Text containing markdown code blocks
            language: Optional language to filter for
            
        Returns:
            Extracted code as a string
        """
        if not text:
            return ""
            
        # Pattern to match code blocks
        pattern = r'```(?:\w+)?\s*\n([\s\S]*?)\n```'
        
        # Find all code blocks
        code_blocks = re.findall(pattern, text)
        
        if not code_blocks:
            return ""
            
        # Join all code blocks with newlines
        return "\n\n".join(code_blocks)
    
    def _analyze_pr_data(self, pr_info: Dict[str, Any], pr_commits: Dict[str, Any], 
                        focus: List[str]) -> str:
        """
        Analyze PR data and generate insights.
        
        This is a placeholder implementation. In a real system, you would
        perform more sophisticated analysis of the PR data.
        
        Args:
            pr_info: PR information from GitHub API
            pr_commits: PR commit data from GitHub API
            focus: Analysis focus areas
            
        Returns:
            Analysis as a string
        """
        # Build prompt for Perplexity AI to analyze the PR data
        prompt = f"""Analyze the following GitHub Pull Request information:

PR Info: 
{json.dumps(pr_info, indent=2)[:2000]}

PR Commits:
{json.dumps(pr_commits, indent=2)[:2000]}

Focus Areas: {', '.join(focus)}

Please provide:
1. A summary of the PR purpose and changes
2. Assessment of code quality and test coverage
3. Potential issues or concerns
4. Recommendations for improvement
"""
        
        # Call Perplexity for PR analysis
        result = self.call_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
            "params": {
                "systemContent": "You are an expert code reviewer specializing in GitHub Pull Request analysis and improvement recommendations.",
                "userContent": prompt,
                "temperature": 0.3
            }
        })
        
        return result.get("response", {}).get("text", "PR analysis not available")
    
    def _handle_analyze_pull_request_task(self, task_id: str, task_data: Dict[str, Any]):
        """
        Handle a pull request analysis task.
        
        Args:
            task_id: ID of the task
            task_data: Task data containing:
                - repo: Repository name (owner/repo)
                - pr_number: Pull request number
                - focus: Aspects to focus on for the PR analysis
        """
        repo = task_data.get("repo", "")
        pr_number = task_data.get("pr_number")
        focus = task_data.get("focus", ["code quality", "performance", "security"])
        
        self.logger.info(f"Analyzing pull request #{pr_number} in repository: {repo}")
        
        # Store the current repository
        self.current_repository = repo
        
        # Split repository into owner and name
        parts = repo.split("/")
        if len(parts) != 2:
            self.logger.error(f"Invalid repository format: {repo}")
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": f"Invalid repository format: {repo}. Expected format: owner/repo",
                "timestamp": time.time()
            })
            return
        
        if not pr_number:
            self.logger.error("No pull request number provided")
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": "No pull request number provided",
                "timestamp": time.time()
            })
            return
        
        owner, repo_name = parts
        
        # Use the GitHub integration to analyze the pull request
        try:
            # Start metrics tracking for the task
            self.metrics.record_task_start(task_id, "analyze_pull_request")
            
            # Display VOTai signature in logs
            votai_ascii = get_votai_ascii("small")
            self.logger.info(f"\n{votai_ascii}\nVOTai Pull Request Analysis: {repo}#{pr_number}")
            
            # Use our GitHubIntegration to analyze the pull request
            result = self.github_integration.analyze_pull_request(
                owner=owner,
                repo=repo_name,
                pr_number=pr_number,
                focus=focus
            )
            
            if result.get("successful", False):
                analysis = result.get("analysis", "Pull request analysis not available")
                
                # Send the response
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "pull_request_analysis",
                    "repo": repo,
                    "pr_number": pr_number,
                    "focus": focus,
                    "analysis": analysis,
                    "timestamp": time.time()
                })
                
                # Record task completion
                self.metrics.record_task_completion(
                    task_id, 
                    success=True,
                    fallback_used=False
                )
            else:
                error_msg = result.get("error", "Unknown error during pull request analysis")
                self.logger.error(f"Failed to analyze pull request: {error_msg}")
                
                self.response_queue.put({
                    "task_id": task_id,
                    "type": "error",
                    "error": f"Failed to analyze pull request: {error_msg}",
                    "timestamp": time.time()
                })
                
                # Record task failure
                self.metrics.record_task_completion(
                    task_id, 
                    success=False,
                    fallback_used=False
                )
        except Exception as e:
            self.logger.error(f"Error analyzing pull request: {e}")
            
            self.response_queue.put({
                "task_id": task_id,
                "type": "error",
                "error": f"Error analyzing pull request: {e}",
                "timestamp": time.time()
            })
            
            # Record task failure
            self.metrics.record_task_completion(
                task_id, 
                success=False,
                fallback_used=False
            ) 