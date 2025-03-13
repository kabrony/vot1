"""
GitHub UI Module

This module provides UI components and visualizations for GitHub automation
operations, including progress tracking, operation status display, and
performance metrics visualization.
"""

import logging
import time
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class GitHubOperationTracker:
    """
    Tracks GitHub automation operations and provides progress reporting.
    
    This class manages operation status tracking, storing historical operations,
    and provides callbacks for UI updates when operations change state.
    """
    
    def __init__(self, storage_path: str = "logs/github_operations"):
        """
        Initialize the operation tracker.
        
        Args:
            storage_path: Path to store operation history
        """
        self.operations = {}  # Active operations
        self.storage_path = storage_path
        self.callbacks = {}
        self.history_limit = 100  # Maximum number of historical operations to keep
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Load any saved operations
        self._load_history()
        
        logger.info(f"Initialized GitHubOperationTracker with storage at {storage_path}")
    
    def register_callback(self, callback_id: str, callback_fn: Callable) -> None:
        """
        Register a callback for operation updates.
        
        Args:
            callback_id: Unique identifier for the callback
            callback_fn: Function to call with operation updates
        """
        self.callbacks[callback_id] = callback_fn
        logger.debug(f"Registered operation callback: {callback_id}")
    
    def unregister_callback(self, callback_id: str) -> None:
        """
        Remove a callback.
        
        Args:
            callback_id: ID of the callback to remove
        """
        if callback_id in self.callbacks:
            del self.callbacks[callback_id]
            logger.debug(f"Unregistered operation callback: {callback_id}")
    
    def start_operation(self, operation_id: str, operation_type: str, details: Dict[str, Any]) -> None:
        """
        Start tracking a new operation.
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (e.g., "create_webhook")
            details: Operation details
        """
        self.operations[operation_id] = {
            "id": operation_id,
            "type": operation_type,
            "details": details,
            "start_time": time.time(),
            "progress": 0,
            "status": "started",
            "success": None,
            "error": None,
            "result": None
        }
        
        # Notify callbacks
        self._notify_callbacks(operation_id)
        
        # Store operation to history
        self._save_to_history(operation_id)
    
    def update_operation(
        self, 
        operation_id: str, 
        progress: Optional[int] = None, 
        status: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update an operation's status.
        
        Args:
            operation_id: Unique identifier for the operation
            progress: Progress percentage (0-100)
            status: Status message
            details: Updated operation details
        """
        if operation_id not in self.operations:
            logger.warning(f"Attempted to update unknown operation: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        
        if progress is not None:
            operation["progress"] = progress
        
        if status is not None:
            operation["status"] = status
        
        if details is not None:
            operation["details"].update(details)
        
        # Notify callbacks
        self._notify_callbacks(operation_id)
        
        # Store operation to history
        self._save_to_history(operation_id)
    
    def complete_operation(
        self, 
        operation_id: str, 
        success: bool, 
        error: Optional[str] = None, 
        result: Optional[Any] = None
    ) -> None:
        """
        Mark an operation as complete.
        
        Args:
            operation_id: Unique identifier for the operation
            success: Whether the operation succeeded
            error: Error message if failed
            result: Operation result data
        """
        if operation_id not in self.operations:
            logger.warning(f"Attempted to complete unknown operation: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        operation["progress"] = 100
        operation["status"] = "completed" if success else "failed"
        operation["success"] = success
        operation["end_time"] = time.time()
        operation["duration"] = operation["end_time"] - operation["start_time"]
        
        if error:
            operation["error"] = error
        
        if result:
            operation["result"] = result
        
        # Notify callbacks
        self._notify_callbacks(operation_id)
        
        # Store operation to history
        self._save_to_history(operation_id)
        
        # Schedule cleanup
        asyncio.create_task(self._cleanup_operation(operation_id))
    
    async def _cleanup_operation(self, operation_id: str) -> None:
        """
        Remove completed operation after delay.
        
        Args:
            operation_id: ID of the operation to clean up
        """
        await asyncio.sleep(300)  # 5 minutes
        if operation_id in self.operations:
            del self.operations[operation_id]
    
    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get operation details by ID.
        
        Args:
            operation_id: ID of the operation to retrieve
            
        Returns:
            Operation details or None if not found
        """
        return self.operations.get(operation_id)
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get all active operations.
        
        Returns:
            List of active operations
        """
        return list(self.operations.values())
    
    def get_operation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get historical operations.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of historical operations, newest first
        """
        history_files = sorted(
            Path(self.storage_path).glob("*.json"), 
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]
        
        history = []
        for history_file in history_files:
            try:
                with open(history_file, 'r') as f:
                    operation = json.load(f)
                    history.append(operation)
            except Exception as e:
                logger.error(f"Error loading operation history file {history_file}: {e}")
        
        return history
    
    def _notify_callbacks(self, operation_id: str) -> None:
        """
        Notify all callbacks of an operation update.
        
        Args:
            operation_id: ID of the updated operation
        """
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        
        for callback_id, callback_fn in self.callbacks.items():
            try:
                callback_fn(operation)
            except Exception as e:
                logger.error(f"Error in operation callback {callback_id}: {e}")
    
    def _save_to_history(self, operation_id: str) -> None:
        """
        Save operation to history file.
        
        Args:
            operation_id: ID of the operation to save
        """
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        
        # Create filename with timestamp and operation ID
        timestamp = int(operation["start_time"])
        filename = f"{timestamp}_{operation_id}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        try:
            with open(filepath, 'w') as f:
                # Convert any non-serializable objects to strings
                clean_operation = self._clean_for_serialization(operation)
                json.dump(clean_operation, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving operation to history: {e}")
    
    def _clean_for_serialization(self, obj: Any) -> Any:
        """
        Convert non-serializable objects to strings.
        
        Args:
            obj: Object to clean
            
        Returns:
            Cleaned object
        """
        if isinstance(obj, dict):
            return {k: self._clean_for_serialization(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_serialization(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def _load_history(self) -> None:
        """Load recent operation history into memory."""
        # This is optional - load recent operations into memory for quick access
        self.recent_history = self.get_operation_history(10)
        
        # Clean up old history files if we exceed the limit
        history_files = sorted(
            Path(self.storage_path).glob("*.json"), 
            key=lambda p: p.stat().st_mtime
        )
        
        if len(history_files) > self.history_limit:
            # Remove oldest files
            for file_to_remove in history_files[:len(history_files) - self.history_limit]:
                try:
                    os.remove(file_to_remove)
                    logger.debug(f"Removed old operation history file: {file_to_remove}")
                except Exception as e:
                    logger.error(f"Error removing old history file {file_to_remove}: {e}")


class GitHubDashboard:
    """
    Dashboard for GitHub automation operations visualization.
    
    This class provides methods to generate HTML reports and visualizations
    for GitHub operations, performance metrics, and system status.
    """
    
    def __init__(
        self,
        operation_tracker: GitHubOperationTracker,
        output_dir: str = "reports/github",
        refresh_interval: int = 30
    ):
        """
        Initialize the GitHub dashboard.
        
        Args:
            operation_tracker: Operation tracker instance
            output_dir: Directory for dashboard output files
            refresh_interval: Auto-refresh interval in seconds
        """
        self.operation_tracker = operation_tracker
        self.output_dir = output_dir
        self.refresh_interval = refresh_interval
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Template paths
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(self.template_dir, exist_ok=True)
        
        # Register callback for operation updates
        self.operation_tracker.register_callback("dashboard", self._operation_updated)
        
        logger.info(f"Initialized GitHubDashboard with output to {output_dir}")
    
    def generate_dashboard(self) -> str:
        """
        Generate the main dashboard HTML.
        
        Returns:
            Path to the generated dashboard HTML file
        """
        output_file = os.path.join(self.output_dir, "dashboard.html")
        
        # Get active operations and history
        active_operations = self.operation_tracker.get_active_operations()
        history = self.operation_tracker.get_operation_history(20)
        
        # Create dashboard data
        dashboard_data = {
            "title": "GitHub Automation Dashboard",
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "refresh_interval": self.refresh_interval,
            "active_operations": active_operations,
            "operation_history": history,
            "stats": self._calculate_stats(active_operations, history)
        }
        
        # Generate HTML
        html = self._render_dashboard_html(dashboard_data)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated GitHub dashboard at {output_file}")
        return output_file
    
    def generate_operation_report(self, operation_id: str) -> Optional[str]:
        """
        Generate a detailed report for a specific operation.
        
        Args:
            operation_id: ID of the operation to report on
            
        Returns:
            Path to the generated report HTML file, or None if operation not found
        """
        operation = self.operation_tracker.get_operation(operation_id)
        if not operation:
            logger.warning(f"Cannot generate report for unknown operation: {operation_id}")
            return None
        
        output_file = os.path.join(self.output_dir, f"operation_{operation_id}.html")
        
        # Generate HTML
        html = self._render_operation_html(operation)
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"Generated operation report at {output_file}")
        return output_file
    
    def _operation_updated(self, operation: Dict[str, Any]) -> None:
        """
        Handle operation updates.
        
        Args:
            operation: Updated operation data
        """
        # Regenerate dashboard when operations are updated
        # This could be optimized to only regenerate on significant changes
        asyncio.create_task(self._async_regenerate_dashboard())
        
        # Generate operation-specific report
        asyncio.create_task(self._async_regenerate_operation_report(operation["id"]))
    
    async def _async_regenerate_dashboard(self) -> None:
        """Async wrapper for dashboard regeneration."""
        self.generate_dashboard()
    
    async def _async_regenerate_operation_report(self, operation_id: str) -> None:
        """Async wrapper for operation report regeneration."""
        self.generate_operation_report(operation_id)
    
    def _calculate_stats(
        self,
        active_operations: List[Dict[str, Any]],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from operations.
        
        Args:
            active_operations: List of active operations
            history: List of historical operations
            
        Returns:
            Dictionary of calculated statistics
        """
        stats = {
            "total_operations": len(active_operations) + len(history),
            "active_operations": len(active_operations),
            "completed_operations": 0,
            "failed_operations": 0,
            "success_rate": 0,
            "avg_duration": 0,
            "operations_by_type": {}
        }
        
        # Count completed and failed operations
        durations = []
        for op in history:
            if op.get("success") is True:
                stats["completed_operations"] += 1
            elif op.get("success") is False:
                stats["failed_operations"] += 1
            
            # Track by operation type
            op_type = op.get("type", "unknown")
            if op_type not in stats["operations_by_type"]:
                stats["operations_by_type"][op_type] = 0
            stats["operations_by_type"][op_type] += 1
            
            # Track duration for completed operations
            if "duration" in op:
                durations.append(op["duration"])
        
        # Calculate success rate
        total_completed = stats["completed_operations"] + stats["failed_operations"]
        if total_completed > 0:
            stats["success_rate"] = (stats["completed_operations"] / total_completed) * 100
        
        # Calculate average duration
        if durations:
            stats["avg_duration"] = sum(durations) / len(durations)
        
        return stats
    
    def _render_dashboard_html(self, data: Dict[str, Any]) -> str:
        """
        Render dashboard HTML.
        
        Args:
            data: Dashboard data
            
        Returns:
            HTML string
        """
        # This is a simple HTML template - in a real app you'd use a template engine
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{data['title']}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{data['refresh_interval']}">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #0366d6; }}
        .card {{ background: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 15px; margin-bottom: 20px; }}
        .progress {{ background: #f1f1f1; border-radius: 4px; height: 20px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: #2cbe4e; }}
        .progress-bar.failed {{ background: #cb2431; }}
        .operation {{ margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; }}
        .status {{ padding: 3px 6px; border-radius: 3px; font-size: 12px; }}
        .status.completed {{ background: #dcffe4; color: #1a7f37; }}
        .status.failed {{ background: #ffebe9; color: #cf222e; }}
        .status.started {{ background: #fff8c5; color: #9a6700; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #eee; }}
        th {{ font-weight: bold; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .stat-card {{ background: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 15px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #0366d6; }}
        .stat-label {{ font-size: 14px; color: #586069; }}
    </style>
</head>
<body>
    <h1>{data['title']}</h1>
    <p>Generated at: {data['generation_time']} (auto-refresh every {data['refresh_interval']} seconds)</p>
    
    <div class="card">
        <h2>Statistics</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{data['stats']['total_operations']}</div>
                <div class="stat-label">Total Operations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['stats']['active_operations']}</div>
                <div class="stat-label">Active Operations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data['stats']['completed_operations']}</div>
                <div class="stat-label">Completed Operations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{round(data['stats']['success_rate'], 1)}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{round(data['stats']['avg_duration'], 2)}s</div>
                <div class="stat-label">Avg Duration</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>Active Operations</h2>
        {self._render_operations_html(data['active_operations'])}
    </div>
    
    <div class="card">
        <h2>Recent Operations</h2>
        {self._render_operations_html(data['operation_history'])}
    </div>
</body>
</html>"""
        return html
    
    def _render_operations_html(self, operations: List[Dict[str, Any]]) -> str:
        """
        Render HTML for a list of operations.
        
        Args:
            operations: List of operations to render
            
        Returns:
            HTML string
        """
        if not operations:
            return "<p>No operations to display.</p>"
        
        html = ""
        for op in operations:
            op_id = op.get("id", "unknown")
            op_type = op.get("type", "unknown")
            status = op.get("status", "unknown")
            progress = op.get("progress", 0)
            start_time = datetime.fromtimestamp(op.get("start_time", 0)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Format details
            details = op.get("details", {})
            details_str = "<br>".join([f"{k}: {v}" for k, v in details.items()]) if details else "No details"
            
            # Format duration
            duration = "In progress"
            if "duration" in op:
                duration = f"{op['duration']:.2f}s"
            
            # Format result/error
            result = ""
            if op.get("success") is True:
                result = f"<div>Result: {str(op.get('result', 'Success'))}</div>"
            elif op.get("success") is False:
                result = f"<div>Error: {op.get('error', 'Unknown error')}</div>"
            
            # CSS class for status
            status_class = status
            
            html += f"""
            <div class="operation">
                <h3>{op_type}: {op_id}</h3>
                <div>Started: {start_time}</div>
                <div>Status: <span class="status {status_class}">{status}</span></div>
                <div>Progress:</div>
                <div class="progress">
                    <div class="progress-bar{' failed' if op.get('success') is False else ''}" style="width: {progress}%"></div>
                </div>
                <div>Duration: {duration}</div>
                <div>Details:<br>{details_str}</div>
                {result}
                <div><a href="operation_{op_id}.html">View detailed report</a></div>
            </div>"""
        
        return html
    
    def _render_operation_html(self, operation: Dict[str, Any]) -> str:
        """
        Render HTML for a single operation.
        
        Args:
            operation: Operation data
            
        Returns:
            HTML string
        """
        op_id = operation.get("id", "unknown")
        op_type = operation.get("type", "unknown")
        status = operation.get("status", "unknown")
        progress = operation.get("progress", 0)
        start_time = datetime.fromtimestamp(operation.get("start_time", 0)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Format details
        details = operation.get("details", {})
        details_html = "<table><tr><th>Property</th><th>Value</th></tr>"
        for k, v in details.items():
            details_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
        details_html += "</table>"
        
        # Format duration
        duration = "In progress"
        if "duration" in operation:
            duration = f"{operation['duration']:.2f}s"
        
        # Format result/error
        result_html = ""
        if operation.get("success") is True:
            result = operation.get("result", {})
            if isinstance(result, dict):
                result_html = "<h3>Result</h3><table><tr><th>Property</th><th>Value</th></tr>"
                for k, v in result.items():
                    result_html += f"<tr><td>{k}</td><td>{v}</td></tr>"
                result_html += "</table>"
            else:
                result_html = f"<h3>Result</h3><pre>{str(result)}</pre>"
        elif operation.get("success") is False:
            error = operation.get("error", "Unknown error")
            result_html = f"<h3>Error</h3><div class='error'>{error}</div>"
        
        # CSS class for status
        status_class = status
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Operation: {op_id}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="{self.refresh_interval}">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #0366d6; }}
        .card {{ background: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 15px; margin-bottom: 20px; }}
        .progress {{ background: #f1f1f1; border-radius: 4px; height: 20px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: #2cbe4e; }}
        .progress-bar.failed {{ background: #cb2431; }}
        .status {{ padding: 3px 6px; border-radius: 3px; font-size: 12px; }}
        .status.completed {{ background: #dcffe4; color: #1a7f37; }}
        .status.failed {{ background: #ffebe9; color: #cf222e; }}
        .status.started {{ background: #fff8c5; color: #9a6700; }}
        .error {{ color: #cf222e; background: #ffebe9; padding: 10px; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #eee; }}
        th {{ font-weight: bold; }}
        pre {{ background: #f6f8fa; padding: 10px; border-radius: 3px; overflow: auto; }}
    </style>
</head>
<body>
    <h1>Operation: {op_id}</h1>
    <p><a href="dashboard.html">Back to Dashboard</a></p>
    
    <div class="card">
        <h2>Operation Summary</h2>
        <table>
            <tr>
                <th>ID</th>
                <td>{op_id}</td>
            </tr>
            <tr>
                <th>Type</th>
                <td>{op_type}</td>
            </tr>
            <tr>
                <th>Status</th>
                <td><span class="status {status_class}">{status}</span></td>
            </tr>
            <tr>
                <th>Start Time</th>
                <td>{start_time}</td>
            </tr>
            <tr>
                <th>Duration</th>
                <td>{duration}</td>
            </tr>
            <tr>
                <th>Progress</th>
                <td>
                    <div class="progress">
                        <div class="progress-bar{' failed' if operation.get('success') is False else ''}" style="width: {progress}%"></div>
                    </div>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="card">
        <h2>Operation Details</h2>
        {details_html}
    </div>
    
    <div class="card">
        {result_html}
    </div>
</body>
</html>"""
        return html


def create_dashboard(storage_path: str = "logs/github_operations") -> GitHubDashboard:
    """
    Create and initialize a GitHub dashboard.
    
    Args:
        storage_path: Path to store operation history
        
    Returns:
        Initialized GitHubDashboard instance
    """
    tracker = GitHubOperationTracker(storage_path=storage_path)
    dashboard = GitHubDashboard(tracker)
    dashboard.generate_dashboard()  # Generate initial dashboard
    return dashboard 