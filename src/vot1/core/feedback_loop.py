"""
VOT1 Advanced Feedback Loop System

This module implements a comprehensive feedback loop system for VOT1,
enabling continuous learning, self-improvement, and adaptation through
real-time performance monitoring and response optimization.
"""

import os
import json
import logging
import time
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackLoop:
    """
    Advanced feedback loop for VOT1 system
    
    This class enables:
    1. Self-evaluation of system performance
    2. Continuous improvement through memory analysis
    3. Dynamic adaptation to changing conditions
    4. Integration with core principles
    5. Metrics-driven optimization
    """
    
    def __init__(
        self,
        memory_manager=None,
        principles_engine=None,
        composio_bridge=None,
        feedback_path: Optional[str] = None,
        evaluation_interval: int = 60  # seconds
    ):
        """
        Initialize the feedback loop system
        
        Args:
            memory_manager: VOT1 memory manager
            principles_engine: Core principles engine
            composio_bridge: Composio memory bridge
            feedback_path: Path for feedback data storage
            evaluation_interval: How often to run evaluations (seconds)
        """
        self.memory_manager = memory_manager
        self.principles_engine = principles_engine
        self.composio_bridge = composio_bridge
        self.evaluation_interval = evaluation_interval
        self.is_running = False
        self._feedback_task = None
        
        # Set up feedback storage path
        if feedback_path:
            self.feedback_path = Path(feedback_path)
        else:
            self.feedback_path = Path(os.path.join(
                os.getenv("VOT1_MEMORY_PATH", "memory"),
                "feedback"
            ))
        os.makedirs(self.feedback_path, exist_ok=True)
        
        # Initialize performance metrics
        self.metrics = {
            "interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "average_response_time": 0,
            "total_response_time": 0,
            "principle_violations": 0,
            "memory_operations": 0,
            "last_evaluation": 0,
            "model_calls": 0
        }
        
        # Improvement suggestions storage
        self.improvement_suggestions = []
        
        logger.info("Feedback loop initialized")
    
    async def start(self):
        """Start the feedback loop"""
        if self.is_running:
            logger.warning("Feedback loop is already running")
            return
        
        self.is_running = True
        self._feedback_task = asyncio.create_task(self._feedback_loop())
        logger.info("Feedback loop started")
    
    async def stop(self):
        """Stop the feedback loop"""
        if not self.is_running:
            logger.warning("Feedback loop is not running")
            return
        
        self.is_running = False
        if self._feedback_task:
            self._feedback_task.cancel()
            try:
                await self._feedback_task
            except asyncio.CancelledError:
                pass
            self._feedback_task = None
        
        logger.info("Feedback loop stopped")
    
    async def _feedback_loop(self):
        """Main feedback loop"""
        try:
            while self.is_running:
                # Only evaluate if enough time has passed
                current_time = time.time()
                time_since_last = current_time - self.metrics["last_evaluation"]
                
                if time_since_last >= self.evaluation_interval:
                    await self.evaluate_performance()
                    self.metrics["last_evaluation"] = current_time
                
                # Sleep for a short time
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info("Feedback loop task cancelled")
        except Exception as e:
            logger.error(f"Error in feedback loop: {str(e)}")
            self.is_running = False
    
    async def evaluate_performance(self) -> Dict[str, Any]:
        """
        Evaluate system performance and generate improvement suggestions
        
        Returns:
            Dict with evaluation results
        """
        logger.info("Evaluating system performance...")
        
        evaluation_results = {
            "timestamp": int(time.time()),
            "metrics": self.metrics.copy(),
            "improvement_needed": False,
            "improvements": []
        }
        
        # Calculate success rate
        if self.metrics["interactions"] > 0:
            success_rate = self.metrics["successful_interactions"] / self.metrics["interactions"]
            evaluation_results["success_rate"] = success_rate
            
            # Flag for improvement if success rate is below threshold
            if success_rate < 0.9:
                evaluation_results["improvement_needed"] = True
                evaluation_results["improvements"].append({
                    "area": "success_rate",
                    "current": success_rate,
                    "target": 0.9,
                    "priority": "high"
                })
        
        # Check average response time
        if self.metrics["successful_interactions"] > 0:
            avg_response_time = self.metrics["total_response_time"] / self.metrics["successful_interactions"]
            evaluation_results["avg_response_time"] = avg_response_time
            
            # Flag for improvement if response time is above threshold
            if avg_response_time > 2.0:  # seconds
                evaluation_results["improvement_needed"] = True
                evaluation_results["improvements"].append({
                    "area": "response_time",
                    "current": avg_response_time,
                    "target": 2.0,
                    "priority": "medium"
                })
        
        # Check principle violations
        if self.metrics["principle_violations"] > 0:
            evaluation_results["improvement_needed"] = True
            evaluation_results["improvements"].append({
                "area": "principles_adherence",
                "current": self.metrics["principle_violations"],
                "target": 0,
                "priority": "high"
            })
        
        # If improvement is needed and we have a composio bridge, generate suggestions
        if evaluation_results["improvement_needed"] and self.composio_bridge:
            await self._generate_improvement_suggestions(evaluation_results)
            
            # Store the suggestions
            self.improvement_suggestions.extend(evaluation_results.get("suggestions", []))
            
            # Implement top priority suggestions if enabled
            if self.get_improvement_config().get("auto_implement", False):
                await self._implement_suggestions(evaluation_results.get("suggestions", []))
        
        # Save evaluation results
        self._save_evaluation(evaluation_results)
        
        # Store in memory if available
        if self.memory_manager:
            memory_content = f"System performance evaluation: {json.dumps(evaluation_results, indent=2)}"
            self.memory_manager.add_semantic_memory(
                content=memory_content,
                metadata={
                    "type": "system_evaluation",
                    "timestamp": evaluation_results["timestamp"],
                    "improvement_needed": evaluation_results["improvement_needed"]
                }
            )
        
        logger.info(f"Performance evaluation complete. Improvement needed: {evaluation_results['improvement_needed']}")
        return evaluation_results
    
    def _save_evaluation(self, evaluation: Dict[str, Any]):
        """Save evaluation results to disk"""
        eval_file = self.feedback_path / f"eval_{evaluation['timestamp']}.json"
        
        try:
            with open(eval_file, 'w') as f:
                json.dump(evaluation, f, indent=2)
            logger.info(f"Evaluation saved to {eval_file}")
        except Exception as e:
            logger.error(f"Error saving evaluation: {str(e)}")
    
    async def _generate_improvement_suggestions(self, evaluation: Dict[str, Any]):
        """
        Generate improvement suggestions using LLM
        
        Args:
            evaluation: Evaluation results
        """
        if not self.composio_bridge:
            logger.warning("Cannot generate improvement suggestions: composio_bridge not available")
            return
        
        # Create a prompt for the LLM
        system_prompt = """
        You are an expert system optimization agent for the VOT1 AGI system.
        Analyze the performance metrics and suggest concrete, specific improvements.
        Focus on actionable solutions that can be implemented programmatically.
        Format your response as JSON with the following structure:
        {
            "analysis": "Brief analysis of the performance issues",
            "suggestions": [
                {
                    "id": "unique_suggestion_id",
                    "area": "The area to improve",
                    "description": "Detailed description of the suggestion",
                    "implementation": "Specific implementation steps",
                    "expected_impact": "Expected impact on metrics",
                    "priority": "high|medium|low"
                }
            ]
        }
        """
        
        user_prompt = f"""
        Please analyze the following performance evaluation and suggest improvements:
        
        {json.dumps(evaluation, indent=2)}
        
        Based on these metrics, what specific optimizations would you recommend?
        """
        
        try:
            # Process with memory
            response = await self.composio_bridge.process_with_memory(
                prompt=user_prompt,
                system=system_prompt,
                store_response=True
            )
            
            # Extract the JSON content from the response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                improvements_json = json_match.group(1)
            else:
                # Try to find any JSON object in the response
                json_match = re.search(r'\{\s*".*"\s*:.*\}', content, re.DOTALL)
                if json_match:
                    improvements_json = json_match.group(0)
                else:
                    improvements_json = content
            
            # Parse the suggestions
            try:
                improvements = json.loads(improvements_json)
                evaluation["suggestions"] = improvements.get("suggestions", [])
                evaluation["analysis"] = improvements.get("analysis", "")
                
                logger.info(f"Generated {len(evaluation['suggestions'])} improvement suggestions")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing improvement suggestions: {e}")
                logger.debug(f"Raw content: {content}")
                
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}")
    
    async def _implement_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Implement high-priority improvement suggestions
        
        Args:
            suggestions: List of improvement suggestions
        """
        # Filter for high priority suggestions
        high_priority = [s for s in suggestions if s.get("priority") == "high"]
        
        for suggestion in high_priority:
            suggestion_id = suggestion.get("id")
            logger.info(f"Implementing suggestion: {suggestion_id}")
            
            # Record the implementation attempt
            if self.memory_manager:
                self.memory_manager.add_semantic_memory(
                    content=f"Implementing improvement suggestion: {suggestion.get('description')}",
                    metadata={
                        "type": "system_improvement",
                        "suggestion_id": suggestion_id,
                        "area": suggestion.get("area"),
                        "timestamp": int(time.time())
                    }
                )
            
            # Implementation would typically involve more complex logic
            # For now, we just log the suggestion
            logger.info(f"Suggestion {suggestion_id} implementation would involve: {suggestion.get('implementation')}")
    
    def log_interaction(
        self,
        success: bool,
        response_time: float,
        principle_violations: int = 0,
        memory_ops: int = 0,
        model_calls: int = 1
    ):
        """
        Log a system interaction for performance tracking
        
        Args:
            success: Whether the interaction succeeded
            response_time: Response time in seconds
            principle_violations: Number of principle violations
            memory_ops: Number of memory operations
            model_calls: Number of model calls
        """
        self.metrics["interactions"] += 1
        
        if success:
            self.metrics["successful_interactions"] += 1
            self.metrics["total_response_time"] += response_time
            self.metrics["average_response_time"] = (
                self.metrics["total_response_time"] / self.metrics["successful_interactions"]
            )
        else:
            self.metrics["failed_interactions"] += 1
        
        self.metrics["principle_violations"] += principle_violations
        self.metrics["memory_operations"] += memory_ops
        self.metrics["model_calls"] += model_calls
        
        logger.debug(f"Logged interaction: success={success}, response_time={response_time:.2f}s")
    
    def get_improvement_config(self) -> Dict[str, Any]:
        """Get improvement configuration"""
        config_file = self.feedback_path / "improvement_config.json"
        
        default_config = {
            "auto_implement": False,
            "improvement_threshold": 0.9,
            "response_time_target": 2.0,
            "max_auto_improvements_per_day": 5,
            "priority_areas": ["principles_adherence", "success_rate", "response_time"]
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading improvement config: {str(e)}")
        
        return default_config
    
    def save_improvement_config(self, config: Dict[str, Any]):
        """Save improvement configuration"""
        config_file = self.feedback_path / "improvement_config.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Improvement config saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving improvement config: {str(e)}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get a comprehensive performance report"""
        # Run a fresh evaluation
        evaluation = await self.evaluate_performance()
        
        # Gather historical data
        historical_data = self._get_historical_data()
        
        # Prepare the report
        report = {
            "current_metrics": self.metrics,
            "latest_evaluation": evaluation,
            "historical_trends": historical_data,
            "improvement_suggestions": self.improvement_suggestions,
            "system_health": self._calculate_system_health(),
            "timestamp": int(time.time())
        }
        
        return report
    
    def _get_historical_data(self) -> Dict[str, Any]:
        """Get historical performance data"""
        # Load the most recent evaluations
        evals = []
        for eval_file in sorted(self.feedback_path.glob("eval_*.json"), reverse=True)[:10]:
            try:
                with open(eval_file, 'r') as f:
                    evals.append(json.load(f))
            except Exception as e:
                logger.error(f"Error loading evaluation file {eval_file}: {str(e)}")
        
        # Extract trends
        success_rates = []
        response_times = []
        principle_violations = []
        
        for eval_data in evals:
            metrics = eval_data.get("metrics", {})
            if "success_rate" in eval_data:
                success_rates.append(eval_data["success_rate"])
            elif metrics.get("interactions", 0) > 0:
                success_rate = metrics.get("successful_interactions", 0) / metrics.get("interactions", 1)
                success_rates.append(success_rate)
                
            if "avg_response_time" in eval_data:
                response_times.append(eval_data["avg_response_time"])
            elif metrics.get("successful_interactions", 0) > 0:
                avg_time = metrics.get("total_response_time", 0) / metrics.get("successful_interactions", 1)
                response_times.append(avg_time)
                
            principle_violations.append(metrics.get("principle_violations", 0))
        
        # Calculate trends
        return {
            "success_rates": success_rates,
            "response_times": response_times,
            "principle_violations": principle_violations,
            "improvement_needed_trend": [e.get("improvement_needed", False) for e in evals],
            "evaluation_timestamps": [e.get("timestamp", 0) for e in evals]
        }
    
    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health"""
        health_metrics = {
            "overall_health": "good",
            "areas_of_concern": [],
            "strengths": []
        }
        
        # Check success rate
        if self.metrics["interactions"] > 0:
            success_rate = self.metrics["successful_interactions"] / self.metrics["interactions"]
            if success_rate < 0.8:
                health_metrics["overall_health"] = "poor"
                health_metrics["areas_of_concern"].append("success_rate")
            elif success_rate < 0.9:
                health_metrics["overall_health"] = "fair"
                health_metrics["areas_of_concern"].append("success_rate")
            else:
                health_metrics["strengths"].append("success_rate")
        
        # Check response time
        if self.metrics["successful_interactions"] > 0:
            avg_time = self.metrics["total_response_time"] / self.metrics["successful_interactions"]
            if avg_time > 3.0:
                health_metrics["overall_health"] = "poor"
                health_metrics["areas_of_concern"].append("response_time")
            elif avg_time > 2.0:
                if health_metrics["overall_health"] == "good":
                    health_metrics["overall_health"] = "fair"
                health_metrics["areas_of_concern"].append("response_time")
            else:
                health_metrics["strengths"].append("response_time")
        
        # Check principle violations
        if self.metrics["principle_violations"] > 10:
            health_metrics["overall_health"] = "poor"
            health_metrics["areas_of_concern"].append("principles_adherence")
        elif self.metrics["principle_violations"] > 0:
            if health_metrics["overall_health"] == "good":
                health_metrics["overall_health"] = "fair"
            health_metrics["areas_of_concern"].append("principles_adherence")
        else:
            health_metrics["strengths"].append("principles_adherence")
        
        return health_metrics
    
    def track_memory_operation(self, operation_type: str, success: bool, duration: float):
        """
        Track a memory operation for performance monitoring
        
        Args:
            operation_type: Type of operation (add, search, etc.)
            success: Whether the operation succeeded
            duration: Duration of the operation in seconds
        """
        self.metrics["memory_operations"] += 1
        
        # Additional tracking logic would be implemented here
        # This could involve maintaining separate metrics for different operation types
        
        logger.debug(f"Tracked memory operation: {operation_type}, success={success}, duration={duration:.4f}s")
    
    def track_model_call(self, model: str, success: bool, duration: float, tokens_in: int, tokens_out: int):
        """
        Track a model call for performance monitoring
        
        Args:
            model: Model name/identifier
            success: Whether the call succeeded
            duration: Duration of the call in seconds
            tokens_in: Input tokens
            tokens_out: Output tokens
        """
        self.metrics["model_calls"] += 1
        
        # Additional tracking logic would be implemented here
        # This could involve maintaining per-model metrics
        
        logger.debug(f"Tracked model call: {model}, success={success}, duration={duration:.2f}s, tokens: {tokens_in}/{tokens_out}")
    
    def track_principle_violation(self, principle_id: str, severity: str):
        """
        Track a principle violation
        
        Args:
            principle_id: ID of the violated principle
            severity: Severity of the violation (high, medium, low)
        """
        self.metrics["principle_violations"] += 1
        
        # Additional tracking logic would be implemented here
        # This could involve maintaining per-principle violation counts
        
        logger.warning(f"Tracked principle violation: {principle_id}, severity={severity}")

    def reset_metrics(self):
        """Reset all performance metrics"""
        self.metrics = {
            "interactions": 0,
            "successful_interactions": 0,
            "failed_interactions": 0,
            "average_response_time": 0,
            "total_response_time": 0,
            "principle_violations": 0,
            "memory_operations": 0,
            "last_evaluation": int(time.time()),
            "model_calls": 0
        }
        logger.info("Performance metrics reset")
    
    async def analyze_memory_health(self) -> Dict[str, Any]:
        """
        Analyze the health of the memory system
        
        Returns:
            Dict with memory health analysis
        """
        if not self.memory_manager:
            return {"error": "Memory manager not available"}
        
        try:
            # Get memory stats
            memory_stats = {
                "semantic_memory_count": 0,
                "conversation_memory_count": 0,
                "memory_age_distribution": {},
                "memory_types": {},
                "total_size_bytes": 0
            }
            
            # Count semantic memories
            semantic_path = Path(self.memory_manager.semantic_memory_path)
            if semantic_path.exists():
                semantic_files = list(semantic_path.glob("*.json"))
                memory_stats["semantic_memory_count"] = len(semantic_files)
                
                # Calculate size
                total_size = sum(f.stat().st_size for f in semantic_files)
                memory_stats["total_size_bytes"] += total_size
                
                # Analyze age distribution
                now = time.time()
                age_buckets = {
                    "recent": 0,      # < 1 day
                    "mid": 0,         # 1-7 days
                    "old": 0          # > 7 days
                }
                
                # Analyze types
                memory_types = {}
                
                for mem_file in semantic_files:
                    try:
                        mtime = mem_file.stat().st_mtime
                        age_days = (now - mtime) / (24 * 3600)
                        
                        if age_days < 1:
                            age_buckets["recent"] += 1
                        elif age_days < 7:
                            age_buckets["mid"] += 1
                        else:
                            age_buckets["old"] += 1
                        
                        # Check memory type
                        with open(mem_file, 'r') as f:
                            mem_data = json.load(f)
                            mem_type = mem_data.get("metadata", {}).get("type", "unknown")
                            
                            if mem_type not in memory_types:
                                memory_types[mem_type] = 0
                            memory_types[mem_type] += 1
                            
                    except Exception:
                        continue
                
                memory_stats["memory_age_distribution"] = age_buckets
                memory_stats["memory_types"] = memory_types
            
            # Count conversation memories
            conv_path = Path(self.memory_manager.conversation_memory_path)
            if conv_path.exists():
                conv_files = list(conv_path.glob("*.json"))
                memory_stats["conversation_memory_count"] = len(conv_files)
                
                # Calculate size
                total_conv_size = sum(f.stat().st_size for f in conv_files)
                memory_stats["total_size_bytes"] += total_conv_size
            
            # Generate health assessment
            memory_health = {
                "overall_health": "good",
                "issues": [],
                "recommendations": []
            }
            
            # Check for potential issues
            if memory_stats["semantic_memory_count"] > 10000:
                memory_health["overall_health"] = "fair"
                memory_health["issues"].append("High memory count may impact performance")
                memory_health["recommendations"].append({
                    "action": "consolidate_memories",
                    "description": "Consolidate older memories to reduce count"
                })
            
            if memory_stats["total_size_bytes"] > 100 * 1024 * 1024:  # 100 MB
                memory_health["overall_health"] = "poor"
                memory_health["issues"].append("Memory size exceeds recommended limits")
                memory_health["recommendations"].append({
                    "action": "prune_memories",
                    "description": "Prune less important memories to reduce size"
                })
            
            # Age distribution check
            age_dist = memory_stats["memory_age_distribution"]
            if age_dist.get("old", 0) > 0.7 * memory_stats["semantic_memory_count"]:
                memory_health["issues"].append("High proportion of old memories")
                memory_health["recommendations"].append({
                    "action": "archive_old_memories",
                    "description": "Archive old memories to secondary storage"
                })
            
            # Return the combined analysis
            return {
                "memory_stats": memory_stats,
                "memory_health": memory_health,
                "timestamp": int(time.time())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing memory health: {str(e)}")
            return {"error": f"Memory health analysis failed: {str(e)}"}
    
    async def apply_to_vot1_system(self, vot1_system) -> Dict[str, Any]:
        """
        Apply the feedback loop to a VOT1 system
        
        Args:
            vot1_system: VOT1 system instance
            
        Returns:
            Dict with application status
        """
        if not hasattr(vot1_system, 'memory_manager'):
            return {"status": "failed", "reason": "VOT1 system has no memory_manager attribute"}
        
        try:
            # Use the VOT1 system components
            self.memory_manager = vot1_system.memory_manager
            self.principles_engine = getattr(vot1_system, 'principles_engine', None)
            self.composio_bridge = getattr(vot1_system, 'memory_bridge', None)
            
            # Patch components to track performance
            self._patch_components()
            
            # Start the feedback loop
            await self.start()
            
            return {
                "status": "applied",
                "components_patched": [
                    "memory_manager" if self.memory_manager else None,
                    "principles_engine" if self.principles_engine else None,
                    "composio_bridge" if self.composio_bridge else None
                ]
            }
            
        except Exception as e:
            logger.error(f"Error applying feedback loop to VOT1 system: {str(e)}")
            return {"status": "failed", "reason": str(e)}
    
    def _patch_components(self):
        """Patch system components to track performance"""
        # Patch memory manager if available
        if self.memory_manager and hasattr(self.memory_manager, 'add_semantic_memory'):
            original_add_memory = self.memory_manager.add_semantic_memory
            
            def patched_add_memory(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = original_add_memory(*args, **kwargs)
                except Exception:
                    success = False
                    raise
                finally:
                    duration = time.time() - start_time
                    self.track_memory_operation("add_semantic", success, duration)
                return result
            
            self.memory_manager.add_semantic_memory = patched_add_memory
            logger.info("Patched memory_manager.add_semantic_memory for performance tracking")
        
        # Patch composio bridge if available
        if self.composio_bridge and hasattr(self.composio_bridge, 'process_with_memory'):
            original_process = self.composio_bridge.process_with_memory
            
            async def patched_process_with_memory(*args, **kwargs):
                start_time = time.time()
                success = True
                try:
                    result = await original_process(*args, **kwargs)
                    
                    # Track model call
                    model = kwargs.get('model', 'default')
                    tokens_in = len(args[0]) if args else 0  # Approximate input tokens
                    tokens_out = len(result.get("choices", [{}])[0].get("message", {}).get("content", ""))
                    
                    self.track_model_call(model, True, time.time() - start_time, tokens_in, tokens_out)
                    
                    # Track interaction
                    self.log_interaction(
                        success=True,
                        response_time=time.time() - start_time,
                        principle_violations=0,
                        memory_ops=1,
                        model_calls=1
                    )
                    
                    return result
                except Exception:
                    success = False
                    self.log_interaction(
                        success=False,
                        response_time=time.time() - start_time,
                        principle_violations=0,
                        memory_ops=0,
                        model_calls=1
                    )
                    raise
            
            self.composio_bridge.process_with_memory = patched_process_with_memory
            logger.info("Patched composio_bridge.process_with_memory for performance tracking")
        
        # Patch principles engine if available
        if self.principles_engine and hasattr(self.principles_engine, 'verify_action'):
            original_verify = self.principles_engine.verify_action
            
            def patched_verify_action(*args, **kwargs):
                result = original_verify(*args, **kwargs)
                
                # Track violations
                if not result.get("verified", True):
                    for violation in result.get("results", []):
                        if not violation.get("verified", True):
                            principle_id = violation.get("principle_id", "unknown")
                            severity = "high"  # Default to high severity
                            self.track_principle_violation(principle_id, severity)
                
                return result
            
            self.principles_engine.verify_action = patched_verify_action
            logger.info("Patched principles_engine.verify_action for violation tracking") 