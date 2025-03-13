"""
VOT1 Feedback Loop Module

This module implements the feedback loop workflow for continuous system improvement.
It periodically executes configured endpoints and processes the results.
"""

import os
import json
import time
import logging
import threading
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class FeedbackLoop:
    """
    Implements a feedback loop for continuous system improvement.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the feedback loop.
        
        Args:
            config_path: Optional path to the configuration file.
                         If not provided, will use the default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "../../config/mcp.json"
        )
        self.config = self._load_config()
        self.running = False
        self.thread = None
        self.last_run_time = None
        self.results_history = []
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the feedback loop configuration from the config file.
        
        Returns:
            Dictionary containing the configuration.
        """
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                return config.get("feedbackLoop", {})
        except Exception as e:
            logger.error(f"Error loading feedback loop config: {e}")
            return {}
            
    def is_enabled(self) -> bool:
        """
        Check if the feedback loop is enabled.
        
        Returns:
            True if enabled, False otherwise.
        """
        # Check environment variable first
        env_enabled = os.environ.get("FEEDBACK_LOOP_ENABLED", "").lower()
        if env_enabled in ["true", "1", "yes"]:
            return True
        if env_enabled in ["false", "0", "no"]:
            return False
            
        # Then check config
        return self.config.get("enabled", False)
        
    def get_interval(self) -> int:
        """
        Get the feedback loop interval in seconds.
        
        Returns:
            Interval in seconds.
        """
        # Check environment variable first
        env_interval = os.environ.get("FEEDBACK_LOOP_INTERVAL")
        if env_interval and env_interval.isdigit():
            return int(env_interval)
            
        # Then check config
        return self.config.get("interval", 3600)  # Default: 1 hour
        
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get the list of endpoints to execute.
        
        Returns:
            List of endpoint configurations.
        """
        return self.config.get("endpoints", [])
        
    def get_notification_channels(self) -> List[str]:
        """
        Get the list of notification channels.
        
        Returns:
            List of notification channel names.
        """
        return self.config.get("notificationChannels", ["dashboard"])
        
    def start(self):
        """
        Start the feedback loop in a background thread.
        """
        if self.running:
            logger.warning("Feedback loop is already running")
            return
            
        if not self.is_enabled():
            logger.info("Feedback loop is disabled, not starting")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Feedback loop started with interval {self.get_interval()} seconds")
        
    def stop(self):
        """
        Stop the feedback loop.
        """
        if not self.running:
            logger.warning("Feedback loop is not running")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            logger.info("Feedback loop stopped")
            
    def _run_loop(self):
        """
        Run the feedback loop continuously.
        """
        while self.running:
            try:
                self._execute_cycle()
                self.last_run_time = datetime.now()
            except Exception as e:
                logger.error(f"Error in feedback loop cycle: {e}")
                
            # Sleep until next cycle
            interval = self.get_interval()
            logger.info(f"Feedback loop sleeping for {interval} seconds")
            
            # Sleep in smaller increments to allow for clean shutdown
            sleep_increment = min(interval, 10)
            for _ in range(interval // sleep_increment):
                if not self.running:
                    break
                time.sleep(sleep_increment)
                
            # Sleep any remaining time
            remaining = interval % sleep_increment
            if remaining > 0 and self.running:
                time.sleep(remaining)
                
    def _execute_cycle(self):
        """
        Execute a single feedback loop cycle.
        """
        logger.info("Starting feedback loop cycle")
        
        endpoints = self.get_endpoints()
        if not endpoints:
            logger.warning("No endpoints configured for feedback loop")
            return
            
        cycle_results = {
            "timestamp": datetime.now().isoformat(),
            "endpoints": []
        }
        
        for endpoint in endpoints:
            try:
                result = self._execute_endpoint(endpoint)
                cycle_results["endpoints"].append(result)
                
                # Process the result
                self._process_result(endpoint, result)
                
            except Exception as e:
                logger.error(f"Error executing endpoint {endpoint.get('name', 'unknown')}: {e}")
                cycle_results["endpoints"].append({
                    "name": endpoint.get("name", "unknown"),
                    "success": False,
                    "error": str(e)
                })
                
        # Store results in history
        self.results_history.append(cycle_results)
        
        # Limit history size
        max_history = 10
        if len(self.results_history) > max_history:
            self.results_history = self.results_history[-max_history:]
            
        # Send notifications
        self._send_notifications(cycle_results)
        
        logger.info("Feedback loop cycle completed")
        
    def _execute_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single endpoint.
        
        Args:
            endpoint: Endpoint configuration.
            
        Returns:
            Dictionary containing the execution result.
        """
        name = endpoint.get("name", "unknown")
        url = endpoint.get("url")
        method = endpoint.get("method", "GET").upper()
        params = endpoint.get("params", {})
        
        if not url:
            raise ValueError(f"No URL specified for endpoint {name}")
            
        logger.info(f"Executing endpoint {name} ({method} {url})")
        
        # Prepare request
        request_kwargs = {}
        if method in ["POST", "PUT", "PATCH"]:
            request_kwargs["json"] = params
        else:
            request_kwargs["params"] = params
            
        # Execute request
        start_time = time.time()
        response = requests.request(method, url, **request_kwargs)
        duration = time.time() - start_time
        
        # Process response
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"text": response.text}
            
        result = {
            "name": name,
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "duration": duration,
            "success": 200 <= response.status_code < 300,
            "timestamp": datetime.now().isoformat(),
            "response": response_data
        }
        
        logger.info(f"Endpoint {name} executed with status {response.status_code}")
        return result
        
    def _process_result(self, endpoint: Dict[str, Any], result: Dict[str, Any]):
        """
        Process the result of an endpoint execution.
        
        Args:
            endpoint: Endpoint configuration.
            result: Execution result.
        """
        # Check if the endpoint has a processor
        processor = endpoint.get("processor")
        if not processor:
            return
            
        # Process based on processor type
        if processor == "memory":
            self._process_memory(endpoint, result)
        elif processor == "alert":
            self._process_alert(endpoint, result)
            
    def _process_memory(self, endpoint: Dict[str, Any], result: Dict[str, Any]):
        """
        Process the result by storing it in memory.
        
        Args:
            endpoint: Endpoint configuration.
            result: Execution result.
        """
        if not result.get("success"):
            logger.warning(f"Not storing failed result for {endpoint.get('name', 'unknown')} in memory")
            return
            
        try:
            # Create memory entry
            memory_data = {
                "content": json.dumps(result.get("response", {})),
                "type": "feedback_loop",
                "metadata": {
                    "endpoint": endpoint.get("name", "unknown"),
                    "url": endpoint.get("url", ""),
                    "timestamp": result.get("timestamp"),
                    "source": "feedback_loop"
                }
            }
            
            # Send to memory API
            response = requests.post(
                "http://localhost:5000/api/memory/create",
                json=memory_data
            )
            
            if response.status_code >= 300:
                logger.error(f"Error storing result in memory: {response.text}")
            else:
                logger.info(f"Result for {endpoint.get('name', 'unknown')} stored in memory")
                
        except Exception as e:
            logger.error(f"Error processing memory: {e}")
            
    def _process_alert(self, endpoint: Dict[str, Any], result: Dict[str, Any]):
        """
        Process the result by generating alerts if needed.
        
        Args:
            endpoint: Endpoint configuration.
            result: Execution result.
        """
        # Check if alert conditions are met
        alert_condition = endpoint.get("alertCondition", {})
        should_alert = False
        
        if alert_condition.get("type") == "status":
            # Alert based on status code
            status_code = result.get("status_code", 0)
            min_status = alert_condition.get("minStatus", 400)
            max_status = alert_condition.get("maxStatus", 599)
            should_alert = min_status <= status_code <= max_status
            
        elif alert_condition.get("type") == "content":
            # Alert based on content
            response = result.get("response", {})
            field = alert_condition.get("field", "")
            value = alert_condition.get("value")
            
            # Navigate to the field
            current = response
            for part in field.split('.'):
                if part and isinstance(current, dict):
                    current = current.get(part, {})
                    
            # Check value
            should_alert = current == value
            
        if should_alert:
            logger.warning(f"Alert condition met for {endpoint.get('name', 'unknown')}")
            self._send_alert(endpoint, result)
            
    def _send_alert(self, endpoint: Dict[str, Any], result: Dict[str, Any]):
        """
        Send an alert for the endpoint result.
        
        Args:
            endpoint: Endpoint configuration.
            result: Execution result.
        """
        alert_config = endpoint.get("alertConfig", {})
        message = alert_config.get("message", f"Alert for {endpoint.get('name', 'unknown')}")
        
        # Format message with result data
        message = message.format(
            name=endpoint.get("name", "unknown"),
            status_code=result.get("status_code", 0),
            duration=result.get("duration", 0),
            timestamp=result.get("timestamp", ""),
            response=result.get("response", {})
        )
        
        # Send to notification channels
        for channel in self.get_notification_channels():
            if channel == "dashboard":
                self._send_dashboard_notification(message, "alert")
            elif channel == "memory":
                self._send_memory_notification(message, "alert")
                
    def _send_notifications(self, cycle_results: Dict[str, Any]):
        """
        Send notifications about the cycle results.
        
        Args:
            cycle_results: Results of the feedback loop cycle.
        """
        # Count successes and failures
        endpoints = cycle_results.get("endpoints", [])
        success_count = sum(1 for e in endpoints if e.get("success", False))
        failure_count = len(endpoints) - success_count
        
        # Create summary message
        message = (
            f"Feedback loop cycle completed at {cycle_results.get('timestamp', '')}\n"
            f"Executed {len(endpoints)} endpoints: {success_count} succeeded, {failure_count} failed."
        )
        
        # Add details for failures
        if failure_count > 0:
            message += "\n\nFailed endpoints:"
            for endpoint in endpoints:
                if not endpoint.get("success", False):
                    message += f"\n- {endpoint.get('name', 'unknown')}: {endpoint.get('error', 'Unknown error')}"
        
        # Send to notification channels
        notification_type = "info" if failure_count == 0 else "warning"
        for channel in self.get_notification_channels():
            if channel == "dashboard":
                self._send_dashboard_notification(message, notification_type)
            elif channel == "memory":
                self._send_memory_notification(message, notification_type)
                
    def _send_dashboard_notification(self, message: str, notification_type: str):
        """
        Send a notification to the dashboard.
        
        Args:
            message: Notification message.
            notification_type: Type of notification (info, warning, error).
        """
        try:
            response = requests.post(
                "http://localhost:5000/api/notifications/create",
                json={
                    "message": message,
                    "type": notification_type,
                    "source": "feedback_loop"
                }
            )
            
            if response.status_code >= 300:
                logger.error(f"Error sending dashboard notification: {response.text}")
            else:
                logger.info("Dashboard notification sent")
                
        except Exception as e:
            logger.error(f"Error sending dashboard notification: {e}")
            
    def _send_memory_notification(self, message: str, notification_type: str):
        """
        Send a notification to memory.
        
        Args:
            message: Notification message.
            notification_type: Type of notification (info, warning, error).
        """
        try:
            # Create memory entry
            memory_data = {
                "content": message,
                "type": "notification",
                "metadata": {
                    "notification_type": notification_type,
                    "source": "feedback_loop",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Send to memory API
            response = requests.post(
                "http://localhost:5000/api/memory/create",
                json=memory_data
            )
            
            if response.status_code >= 300:
                logger.error(f"Error sending memory notification: {response.text}")
            else:
                logger.info("Memory notification sent")
                
        except Exception as e:
            logger.error(f"Error sending memory notification: {e}")
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the feedback loop.
        
        Returns:
            Dictionary containing status information.
        """
        return {
            "enabled": self.is_enabled(),
            "running": self.running,
            "interval": self.get_interval(),
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "endpoints_count": len(self.get_endpoints()),
            "notification_channels": self.get_notification_channels(),
            "results_history_count": len(self.results_history)
        }
        
    def get_results_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of feedback loop results.
        
        Returns:
            List of cycle results.
        """
        return self.results_history
        
    def run_now(self) -> Dict[str, Any]:
        """
        Run the feedback loop immediately and return the results.
        
        Returns:
            Dictionary containing the cycle results.
        """
        try:
            self._execute_cycle()
            self.last_run_time = datetime.now()
            return self.results_history[-1] if self.results_history else {}
        except Exception as e:
            logger.error(f"Error running feedback loop: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "endpoints": []
            }

# Singleton instance
_feedback_loop_instance = None

def get_feedback_loop() -> FeedbackLoop:
    """
    Get the singleton feedback loop instance.
    
    Returns:
        FeedbackLoop instance.
    """
    global _feedback_loop_instance
    if _feedback_loop_instance is None:
        _feedback_loop_instance = FeedbackLoop()
    return _feedback_loop_instance 