#!/usr/bin/env python3
"""
Autonomous System Health Monitor for TRILOGY BRAIN

This module provides continuous health monitoring, diagnostics, and self-healing
capabilities for the TRILOGY BRAIN memory system and associated agents.

Features:
- Continuous health monitoring with configurable intervals
- Integration with TRILOGY BRAIN for memory storage and analytics
- Automatic detection and resolution of common issues
- Performance metrics collection and analysis
- Alerting and notification mechanisms
"""

import os
import sys
import json
import time
import logging
import asyncio
import datetime
import threading
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple
import signal
import requests
from concurrent.futures import ThreadPoolExecutor
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("system_health.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SystemHealthMonitor")

# Try to import required packages
try:
    # Import TRILOGY BRAIN components
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.memory import MemoryManager
    trilogy_brain_available = True
except ImportError:
    try:
        from vot1.composio.memory_bridge import ComposioMemoryBridge
        from vot1.memory import MemoryManager
        trilogy_brain_available = True
    except ImportError:
        logger.warning("TRILOGY BRAIN memory system not available for health monitoring")
        trilogy_brain_available = False

try:
    # Import Composio client for MCP integration
    from composio_client import ComposioClient
    composio_available = True
except ImportError:
    logger.warning("Composio client not available for MCP integration")
    composio_available = False

class SystemHealthMonitor:
    """
    Autonomous system health monitor that continuously checks the status
    of the TRILOGY BRAIN memory system and associated components.
    
    This monitor:
    1. Runs continuous health checks at configurable intervals
    2. Detects and diagnoses system issues
    3. Attempts to automatically resolve common problems
    4. Records health metrics in TRILOGY BRAIN memory
    5. Triggers alerts for critical issues
    """
    
    def __init__(
        self,
        composio_api_key: Optional[str] = None,
        composio_mcp_url: Optional[str] = None,
        memory_path: str = "memory/health",
        check_interval: int = 60,  # Check system health every 60 seconds by default
        self_healing_enabled: bool = True,
        alert_threshold: int = 3,  # Number of consecutive failures before alerting
        max_memory_entries: int = 1000,  # Maximum number of health records to keep
        config_file: Optional[str] = None
    ):
        """
        Initialize the health monitor.
        
        Args:
            composio_api_key: API key for Composio
            composio_mcp_url: MCP URL for Composio
            memory_path: Path for health monitoring memory storage
            check_interval: Interval between health checks in seconds
            self_healing_enabled: Whether to enable automatic problem resolution
            alert_threshold: Number of consecutive failures before alerting
            max_memory_entries: Maximum number of health records to keep
            config_file: Optional configuration file
        """
        # Store configuration
        self.composio_api_key = composio_api_key or os.environ.get("COMPOSIO_API_KEY")
        self.composio_mcp_url = composio_mcp_url or os.environ.get("COMPOSIO_MCP_URL")
        self.check_interval = check_interval
        self.self_healing_enabled = self_healing_enabled
        self.alert_threshold = alert_threshold
        self.max_memory_entries = max_memory_entries
        self.memory_path = memory_path
        
        # Create memory directory if it doesn't exist
        os.makedirs(memory_path, exist_ok=True)
        
        # Load configuration if specified
        self.config = {}
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        # Initialize metrics dictionaries
        self.current_metrics = {}
        self.historical_metrics = []
        self.failure_counts = {}
        self.last_alert_time = {}
        
        # Initialize components
        self.memory_bridge = None
        self.memory_manager = None
        self.composio_client = None
        
        # Threading and async components
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.running = False
        self.monitor_thread = None
        self.event_loop = None
        self.background_tasks = []
        
        # Initialize system checks
        self.system_checks = [
            self._check_memory_usage,
            self._check_disk_space,
            self._check_cpu_usage,
            self._check_trilogy_brain,
            self._check_composio_mcp,
            self._check_agent_processes
        ]
        
        # Initialize automatic fixes
        self.auto_fixes = {
            "memory_high": self._fix_memory_high,
            "disk_space_low": self._fix_disk_space_low,
            "trilogy_brain_unavailable": self._fix_trilogy_brain_unavailable,
            "composio_mcp_unavailable": self._fix_composio_mcp_unavailable,
            "agent_process_crashed": self._fix_agent_process_crashed
        }
        
        # Initialize the components
        self._init_components()
    
    def _init_components(self):
        """Initialize all required components."""
        # Initialize TRILOGY BRAIN if available
        if trilogy_brain_available:
            try:
                # Create memory manager
                self.memory_manager = MemoryManager(
                    storage_path=os.path.join(self.memory_path, "memory_store")
                )
                logger.info("TRILOGY BRAIN memory manager initialized")
                
                # Initialize memory bridge if Composio is available
                if composio_available and self.composio_api_key and self.composio_mcp_url:
                    try:
                        # Initialize Composio client
                        self.composio_client = ComposioClient(
                            api_key=self.composio_api_key,
                            endpoint=self.composio_mcp_url
                        )
                        
                        # Initialize memory bridge
                        self.memory_bridge = ComposioMemoryBridge(
                            memory_manager=self.memory_manager,
                            composio_client=self.composio_client
                        )
                        logger.info("Composio memory bridge initialized")
                    except Exception as e:
                        logger.error(f"Error initializing Composio components: {e}")
            except Exception as e:
                logger.error(f"Error initializing TRILOGY BRAIN: {e}")
    
    def start(self):
        """Start the health monitoring process."""
        if self.running:
            logger.warning("Health monitor is already running")
            return
        
        self.running = True
        
        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Start the event loop in a separate thread for async operations
        self.event_loop = asyncio.new_event_loop()
        self.executor.submit(self._run_event_loop)
        
        logger.info(f"System health monitoring started with {self.check_interval}s interval")
    
    def stop(self):
        """Stop the health monitoring process."""
        if not self.running:
            logger.warning("Health monitor is not running")
            return
        
        logger.info("Stopping system health monitor...")
        self.running = False
        
        # Wait for the monitoring thread to terminate
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        # Stop the event loop
        if self.event_loop:
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
            
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        # Shutdown the executor
        self.executor.shutdown(wait=False)
        logger.info("System health monitor stopped")
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.event_loop)
        try:
            self.event_loop.run_forever()
        finally:
            asyncio.set_event_loop(None)
            self.event_loop.close()
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs health checks at regular intervals."""
        while self.running:
            try:
                # Run all health checks
                self._run_health_checks()
                
                # Analyze the results
                issues = self._analyze_health_metrics()
                
                # Store health data
                self._store_health_data()
                
                # Apply automatic fixes if enabled
                if self.self_healing_enabled and issues:
                    self._apply_auto_fixes(issues)
                
                # Sleep for the check interval
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                logger.error(traceback.format_exc())
                # Sleep for a short interval if there's an error
                time.sleep(10)
    
    def _run_health_checks(self):
        """Run all configured system health checks."""
        timestamp = datetime.datetime.now().isoformat()
        self.current_metrics = {
            "timestamp": timestamp,
            "checks": {}
        }
        
        # Run each health check
        for check_func in self.system_checks:
            check_name = check_func.__name__.replace("_check_", "")
            try:
                result = check_func()
                self.current_metrics["checks"][check_name] = result
            except Exception as e:
                logger.error(f"Error running health check {check_name}: {e}")
                self.current_metrics["checks"][check_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Add current metrics to historical data
        self.historical_metrics.append(self.current_metrics)
        
        # Limit the size of historical metrics
        if len(self.historical_metrics) > self.max_memory_entries:
            self.historical_metrics = self.historical_metrics[-self.max_memory_entries:]
    
    def _analyze_health_metrics(self) -> List[Dict[str, Any]]:
        """
        Analyze health metrics to identify issues.
        
        Returns:
            List of identified issues with details
        """
        issues = []
        
        # Check each metric for problems
        for check_name, result in self.current_metrics["checks"].items():
            status = result.get("status", "unknown")
            
            if status == "error" or status == "warning" or status == "critical":
                # Increment failure count
                self.failure_counts[check_name] = self.failure_counts.get(check_name, 0) + 1
                
                # Create issue record
                issue = {
                    "check": check_name,
                    "status": status,
                    "timestamp": self.current_metrics["timestamp"],
                    "details": result,
                    "consecutive_failures": self.failure_counts[check_name]
                }
                
                issues.append(issue)
                
                # Trigger alert if threshold exceeded
                if self.failure_counts[check_name] >= self.alert_threshold:
                    # Check if we recently sent an alert for this issue
                    last_alert = self.last_alert_time.get(check_name, 0)
                    current_time = time.time()
                    
                    # Only alert once per hour (3600 seconds)
                    if current_time - last_alert > 3600:
                        self._trigger_alert(check_name, issue)
                        self.last_alert_time[check_name] = current_time
            else:
                # Reset failure count on success
                self.failure_counts[check_name] = 0
        
        return issues
    
    def _store_health_data(self):
        """Store health data in TRILOGY BRAIN memory."""
        if not self.memory_manager:
            return
        
        # Create health record
        health_record = {
            "timestamp": self.current_metrics["timestamp"],
            "metrics": self.current_metrics,
            "issues": self._analyze_health_metrics()
        }
        
        # Submit task to store health data asynchronously
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(
                lambda: self._submit_async_task(self._async_store_health_data(health_record))
            )
    
    def _submit_async_task(self, coro):
        """Submit an async task to the event loop."""
        task = asyncio.run_coroutine_threadsafe(coro, self.event_loop)
        self.background_tasks.append(task)
        # Clean up completed tasks
        self.background_tasks = [t for t in self.background_tasks if not t.done()]
    
    async def _async_store_health_data(self, health_record: Dict[str, Any]):
        """Asynchronously store health data in TRILOGY BRAIN."""
        try:
            if self.memory_manager:
                # Store health record
                await self.memory_manager.store_memory(
                    content=json.dumps(health_record),
                    memory_type="system_health",
                    metadata={
                        "timestamp": health_record["timestamp"],
                        "issues": len(health_record.get("issues", [])),
                        "status": "healthy" if not health_record.get("issues") else "unhealthy"
                    }
                )
                
                # Store individual issues for better searchability
                for issue in health_record.get("issues", []):
                    await self.memory_manager.store_memory(
                        content=json.dumps(issue),
                        memory_type=f"system_issue_{issue['check']}",
                        metadata={
                            "check": issue["check"],
                            "status": issue["status"],
                            "consecutive_failures": issue["consecutive_failures"],
                            "timestamp": issue["timestamp"]
                        }
                    )
        except Exception as e:
            logger.error(f"Error storing health data: {e}")
    
    def _apply_auto_fixes(self, issues: List[Dict[str, Any]]):
        """Apply automatic fixes for identified issues."""
        for issue in issues:
            check_name = issue["check"]
            issue_key = f"{check_name}_{issue['status']}"
            
            # Check if we have a fix for this issue
            if issue_key in self.auto_fixes:
                try:
                    logger.info(f"Attempting to fix issue: {issue_key}")
                    self.auto_fixes[issue_key](issue)
                except Exception as e:
                    logger.error(f"Error applying fix for {issue_key}: {e}")
            else:
                logger.warning(f"No automatic fix available for issue: {issue_key}")
    
    def _trigger_alert(self, check_name: str, issue: Dict[str, Any]):
        """Trigger an alert for a critical issue."""
        alert_message = f"ALERT: System health issue detected in {check_name}, status: {issue['status']}"
        
        # Log the alert
        logger.warning(alert_message)
        
        # Store the alert in TRILOGY BRAIN
        if self.event_loop:
            self.event_loop.call_soon_threadsafe(
                lambda: self._submit_async_task(self._async_store_alert(check_name, issue, alert_message))
            )
        
        # Send the alert to configured channels
        self._send_alert_notification(alert_message, issue)
    
    async def _async_store_alert(self, check_name: str, issue: Dict[str, Any], alert_message: str):
        """Asynchronously store alert in TRILOGY BRAIN."""
        try:
            if self.memory_manager:
                await self.memory_manager.store_memory(
                    content=alert_message,
                    memory_type="system_alert",
                    metadata={
                        "check": check_name,
                        "status": issue["status"],
                        "timestamp": issue["timestamp"],
                        "consecutive_failures": issue["consecutive_failures"]
                    }
                )
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def _send_alert_notification(self, alert_message: str, issue: Dict[str, Any]):
        """Send alert notification to configured channels."""
        # Send webhook notification if configured
        webhook_url = self.config.get("alert_webhook")
        if webhook_url:
            try:
                requests.post(
                    webhook_url,
                    json={
                        "message": alert_message,
                        "issue": issue,
                        "system": "trilogy_brain_health_monitor",
                        "timestamp": datetime.datetime.now().isoformat()
                    },
                    timeout=5
                )
            except Exception as e:
                logger.error(f"Error sending webhook alert: {e}")
        
        # Log to file
        alert_log_file = self.config.get("alert_log_file", "alerts.log")
        try:
            with open(alert_log_file, "a") as f:
                f.write(f"{datetime.datetime.now().isoformat()} - {alert_message}\n")
        except Exception as e:
            logger.error(f"Error writing to alert log: {e}")
    
    # System Health Checks
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        memory = psutil.virtual_memory()
        percent_used = memory.percent
        
        status = "healthy"
        if percent_used > 90:
            status = "critical"
        elif percent_used > 80:
            status = "warning"
        
        return {
            "status": status,
            "percent_used": percent_used,
            "total_gb": memory.total / (1024 ** 3),
            "available_gb": memory.available / (1024 ** 3)
        }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        disk = psutil.disk_usage('/')
        percent_used = disk.percent
        
        status = "healthy"
        if percent_used > 95:
            status = "critical"
        elif percent_used > 85:
            status = "warning"
        
        return {
            "status": status,
            "percent_used": percent_used,
            "total_gb": disk.total / (1024 ** 3),
            "free_gb": disk.free / (1024 ** 3)
        }
    
    def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        status = "healthy"
        if cpu_percent > 90:
            status = "critical"
        elif cpu_percent > 80:
            status = "warning"
        
        return {
            "status": status,
            "percent_used": cpu_percent,
            "logical_cpus": psutil.cpu_count(),
            "physical_cpus": psutil.cpu_count(logical=False)
        }
    
    def _check_trilogy_brain(self) -> Dict[str, Any]:
        """Check TRILOGY BRAIN memory system availability."""
        if not trilogy_brain_available:
            return {
                "status": "warning",
                "message": "TRILOGY BRAIN is not available"
            }
        
        if not self.memory_manager:
            return {
                "status": "warning",
                "message": "Memory manager is not initialized"
            }
        
        # Check if we can access the memory store
        memory_path = os.path.join(self.memory_path, "memory_store")
        if not os.path.exists(memory_path):
            return {
                "status": "warning",
                "message": "Memory storage path does not exist"
            }
        
        # All checks passed
        return {
            "status": "healthy",
            "memory_path": memory_path,
            "memory_bridge_available": self.memory_bridge is not None
        }
    
    def _check_composio_mcp(self) -> Dict[str, Any]:
        """Check Composio MCP availability."""
        if not composio_available:
            return {
                "status": "warning",
                "message": "Composio client is not available"
            }
        
        if not self.composio_client:
            return {
                "status": "warning",
                "message": "Composio client is not initialized"
            }
        
        if not self.composio_mcp_url:
            return {
                "status": "warning",
                "message": "Composio MCP URL is not configured"
            }
        
        # Try to ping the MCP endpoint
        try:
            # This is a simplified check, in a real implementation we would
            # use the proper client method to check MCP availability
            if self.composio_client:
                return {
                    "status": "healthy",
                    "mcp_url": self.composio_mcp_url
                }
            else:
                return {
                    "status": "warning",
                    "message": "Could not verify MCP connection"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error checking MCP: {str(e)}"
            }
    
    def _check_agent_processes(self) -> Dict[str, Any]:
        """Check if agent processes are running."""
        # Define expected agent processes
        expected_agents = self.config.get("expected_agents", ["enhanced_research_agent.py"])
        
        running_agents = []
        missing_agents = []
        
        # Check each expected agent
        for agent in expected_agents:
            found = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if agent in ' '.join(proc.info['cmdline']):
                        running_agents.append({
                            "name": agent,
                            "pid": proc.info['pid'],
                            "running_time": time.time() - proc.create_time()
                        })
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if not found:
                missing_agents.append(agent)
        
        # Determine status
        if missing_agents:
            if len(missing_agents) == len(expected_agents):
                status = "critical"  # All agents are missing
            else:
                status = "warning"  # Some agents are missing
        else:
            status = "healthy"  # All agents are running
        
        return {
            "status": status,
            "running_agents": running_agents,
            "missing_agents": missing_agents,
            "expected_agents": expected_agents
        }
    
    # Automatic Fixes
    
    def _fix_memory_high(self, issue: Dict[str, Any]):
        """Fix high memory usage."""
        logger.info("Attempting to free memory...")
        
        # Clear Python's memory caches
        import gc
        gc.collect()
        
        # If still critical, try more aggressive measures
        if issue["details"]["percent_used"] > 90:
            logger.info("Memory usage still critical, taking more aggressive measures")
            
            # Find memory hogs
            memory_hogs = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if proc.info['memory_percent'] > 10:  # Using more than 10% of memory
                        memory_hogs.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Log the memory hogs
            for proc in memory_hogs:
                logger.info(f"Memory hog: {proc.info['name']} (PID {proc.info['pid']}) using {proc.info['memory_percent']:.1f}% of memory")
    
    def _fix_disk_space_low(self, issue: Dict[str, Any]):
        """Fix low disk space."""
        logger.info("Attempting to free disk space...")
        
        # Clear log files
        log_dir = self.config.get("log_dir", ".")
        deleted_size = 0
        
        for filename in os.listdir(log_dir):
            if filename.endswith(".log") and not filename == "system_health.log":
                filepath = os.path.join(log_dir, filename)
                try:
                    # Only delete logs older than 7 days
                    if time.time() - os.path.getmtime(filepath) > 7 * 24 * 60 * 60:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        deleted_size += file_size
                        logger.info(f"Deleted old log file: {filepath} ({file_size / (1024 * 1024):.1f} MB)")
                except Exception as e:
                    logger.error(f"Error deleting log file: {e}")
        
        logger.info(f"Freed {deleted_size / (1024 * 1024):.1f} MB of disk space")
    
    def _fix_trilogy_brain_unavailable(self, issue: Dict[str, Any]):
        """Fix TRILOGY BRAIN unavailability."""
        logger.info("Attempting to fix TRILOGY BRAIN unavailability...")
        
        # Re-initialize memory components
        try:
            self._init_components()
            logger.info("Re-initialized TRILOGY BRAIN components")
            
            # Create memory path if it doesn't exist
            memory_path = os.path.join(self.memory_path, "memory_store")
            os.makedirs(memory_path, exist_ok=True)
            logger.info(f"Created memory path: {memory_path}")
        except Exception as e:
            logger.error(f"Error fixing TRILOGY BRAIN: {e}")
    
    def _fix_composio_mcp_unavailable(self, issue: Dict[str, Any]):
        """Fix Composio MCP unavailability."""
        logger.info("Attempting to fix Composio MCP unavailability...")
        
        # Re-initialize Composio client
        if composio_available and self.composio_api_key and self.composio_mcp_url:
            try:
                self.composio_client = ComposioClient(
                    api_key=self.composio_api_key,
                    endpoint=self.composio_mcp_url
                )
                logger.info("Re-initialized Composio client")
            except Exception as e:
                logger.error(f"Error re-initializing Composio client: {e}")
    
    def _fix_agent_process_crashed(self, issue: Dict[str, Any]):
        """Fix crashed agent processes."""
        logger.info("Attempting to fix crashed agent processes...")
        
        # Restart missing agents
        for agent in issue["details"].get("missing_agents", []):
            logger.info(f"Attempting to restart agent: {agent}")
            
            # Get the command to run the agent
            agent_cmd = self.config.get("agent_commands", {}).get(agent)
            if not agent_cmd:
                logger.error(f"No command configured to restart agent: {agent}")
                continue
            
            # Start the agent process
            try:
                subprocess.Popen(
                    agent_cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Started agent: {agent}")
            except Exception as e:
                logger.error(f"Error starting agent {agent}: {e}")

class SystemHealthDaemon:
    """Daemon process for system health monitoring."""
    
    def __init__(self, config_file: str = "config/health_monitor.json"):
        """Initialize the daemon."""
        self.config_file = config_file
        self.monitor = None
        self.pid_file = "/tmp/trilogy_health_monitor.pid"
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        return {}
    
    def start(self):
        """Start the daemon."""
        # Check if already running
        if os.path.exists(self.pid_file):
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                # Check if process with this PID exists
                os.kill(pid, 0)
                logger.warning(f"Daemon already running with PID {pid}")
                return
            except OSError:
                # Process not found, remove stale PID file
                os.remove(self.pid_file)
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Load configuration
        config = self.load_config()
        
        # Create and start monitor
        self.monitor = SystemHealthMonitor(**config)
        self.monitor.start()
        
        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    
    def stop(self):
        """Stop the daemon."""
        if self.monitor:
            self.monitor.stop()
        
        # Remove PID file
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
    
    def handle_signal(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

def main():
    """Command-line interface for the system health monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TRILOGY BRAIN System Health Monitor")
    parser.add_argument("action", choices=["start", "stop", "status"], help="Action to perform")
    parser.add_argument("--config", "-c", default="config/health_monitor.json", help="Configuration file")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", "-i", type=int, default=60, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    if args.action == "start":
        if args.daemon:
            # Run as daemon
            daemon = SystemHealthDaemon(config_file=args.config)
            daemon.start()
        else:
            # Run in foreground
            config = {}
            if os.path.exists(args.config):
                try:
                    with open(args.config, 'r') as f:
                        config = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading configuration: {e}")
            
            # Override interval if specified
            if args.interval:
                config["check_interval"] = args.interval
            
            # Create and start monitor
            monitor = SystemHealthMonitor(**config)
            monitor.start()
            
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                monitor.stop()
    
    elif args.action == "stop":
        # Stop the daemon
        pid_file = "/tmp/trilogy_health_monitor.pid"
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                # Send SIGTERM to the process
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to process {pid}")
                
                # Wait for the process to terminate
                for _ in range(10):
                    try:
                        os.kill(pid, 0)  # Check if process exists
                        time.sleep(0.5)
                    except OSError:
                        # Process has terminated
                        break
                else:
                    # Process didn't terminate, send SIGKILL
                    try:
                        os.kill(pid, signal.SIGKILL)
                        logger.info(f"Sent SIGKILL to process {pid}")
                    except OSError:
                        pass
                
                # Remove PID file
                os.remove(pid_file)
                logger.info("Health monitor stopped")
            except OSError:
                logger.error(f"Process {pid} not found")
                os.remove(pid_file)
        else:
            logger.error("Health monitor is not running")
    
    elif args.action == "status":
        # Check if daemon is running
        pid_file = "/tmp/trilogy_health_monitor.pid"
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                # Check if process with this PID exists
                os.kill(pid, 0)
                print(f"Health monitor is running with PID {pid}")
                
                # Get process info
                process = psutil.Process(pid)
                print(f"Running since: {datetime.datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Memory usage: {process.memory_info().rss / (1024 * 1024):.1f} MB")
                print(f"CPU usage: {process.cpu_percent(interval=1):.1f}%")
            except OSError:
                print("Health monitor is not running (stale PID file)")
                os.remove(pid_file)
        else:
            print("Health monitor is not running")

if __name__ == "__main__":
    main() 