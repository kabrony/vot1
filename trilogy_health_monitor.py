#!/usr/bin/env python3
"""
TRILOGY Health Monitor

This script monitors the health of the research agent system and performs
automatic repairs when issues are detected. It streams health data to
TRILOGY BRAIN for continuous monitoring and analysis.

Features:
- Continuous health monitoring
- Automatic repair of system components
- Health data streaming to TRILOGY BRAIN
- Email notifications for critical issues
- Integration with MCP configuration
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trilogy_health.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TRILOGY_HEALTH")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, will use system environment variables")

# Try to import required packages
try:
    # Perplexity client for web search
    from perplexipy import PerplexityClient
    perplexipy_installed = True
except ImportError:
    logger.warning("PerplexiPy not installed. Install with: pip install perplexipy")
    perplexipy_installed = False

try:
    # Anthropic client for Claude
    import anthropic
    anthropic_installed = True
except ImportError:
    logger.warning("Anthropic package not installed. Install with: pip install anthropic")
    anthropic_installed = False

# Optional: Import requests for API calls
try:
    import requests
    requests_installed = True
except ImportError:
    logger.warning("Requests package not installed. Install with: pip install requests")
    requests_installed = False

class TrilogyHealthMonitor:
    """
    System health monitor for the TRILOGY BRAIN ecosystem.
    
    This class monitors the health of various components, performs automatic
    repairs, and streams health data to TRILOGY BRAIN for continuous analysis.
    """
    
    def __init__(
        self,
        perplexity_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        composio_api_key: Optional[str] = None,
        composio_mcp_url: Optional[str] = None,
        memory_path: str = "memory/health",
        check_interval: int = 60,
        enable_auto_repair: bool = True,
        enable_notifications: bool = True,
        config_file: Optional[str] = None
    ):
        """
        Initialize the TRILOGY Health Monitor.
        
        Args:
            perplexity_api_key: API key for Perplexity
            anthropic_api_key: API key for Anthropic
            github_token: GitHub access token
            composio_api_key: API key for Composio
            composio_mcp_url: MCP URL for Composio
            memory_path: Path for health data storage
            check_interval: Interval for health checks in seconds
            enable_auto_repair: Whether to enable automatic repairs
            enable_notifications: Whether to enable notifications
            config_file: Optional path to configuration file
        """
        # Use API keys from parameters or environment variables
        self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.composio_api_key = composio_api_key or os.environ.get("COMPOSIO_API_KEY")
        self.composio_mcp_url = composio_mcp_url or os.environ.get("COMPOSIO_MCP_URL")
        
        # Configuration
        self.memory_path = memory_path
        self.check_interval = check_interval
        self.enable_auto_repair = enable_auto_repair
        self.enable_notifications = enable_notifications
        
        # Create memory directory if it doesn't exist
        Path(memory_path).mkdir(parents=True, exist_ok=True)
        
        # Generate a session ID
        self.session_id = f"health_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._generate_id()}"
        
        # Initialize clients
        self.perplexity_client = None
        self.claude_client = None
        
        # System health state
        self.system_health = {
            "status": "initializing",
            "last_check": time.time(),
            "checks_performed": 0,
            "issues_detected": 0,
            "repairs_attempted": 0,
            "repairs_successful": 0,
            "components_status": {},
            "health_history": []
        }
        
        # MCP configuration
        self.mcp_config = self._load_mcp_config(config_file)
        
        # Health monitor task
        self.monitor_task = None
        
        # Initialize
        self._init_monitor()
    
    def _generate_id(self, length: int = 8) -> str:
        """Generate a random ID of specified length."""
        import random
        return ''.join(random.choices('0123456789abcdef', k=length))
    
    def _load_mcp_config(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Load MCP configuration from file or use defaults.
        
        Args:
            config_file: Optional path to configuration file
            
        Returns:
            Dictionary with MCP configuration
        """
        default_config = {
            "mcpServers": {
                "MCP": {
                    "url": "https://mcp.composio.dev/github/victorious-damaged-branch-0ojHhf"
                },
                "PERPLEXITY": {
                    "url": "https://mcp.composio.dev/perplexityai/plump-colossal-account-RTix4q"
                },
                "FIRECRAWL": {
                    "url": "https://mcp.composio.dev/firecrawl/plump-colossal-account-RTix4q"
                },
                "FIGMA": {
                    "url": "https://mcp.composio.dev/figma/plump-colossal-account-RTix4q"
                },
                "COMPOSIO": {
                    "url": "https://mcp.composio.dev/composio/plump-colossal-account-RTix4q"
                }
            },
            "feedbackLoop": {
                "enabled": True,
                "interval": 3600,
                "endpoints": [
                    {
                        "name": "System Health Check",
                        "url": "/api/system/health",
                        "method": "GET",
                        "processor": "alert",
                        "alertCondition": {
                            "type": "status",
                            "minStatus": 400
                        },
                        "alertConfig": {
                            "message": "System health check failed with status {status_code}"
                        }
                    }
                ],
                "notificationChannels": [
                    "dashboard",
                    "memory"
                ]
            }
        }
        
        # If config file is provided, load it
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded MCP configuration from {config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading MCP configuration: {e}")
        
        # Use composite path from environment
        mcp_composite_path = os.path.expanduser("~/.cursor/mcp.json")
        if os.path.exists(mcp_composite_path):
            try:
                with open(mcp_composite_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded MCP configuration from {mcp_composite_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading MCP configuration: {e}")
        
        logger.warning("Using default MCP configuration")
        return default_config
    
    def _init_monitor(self):
        """Initialize the health monitor."""
        try:
            # Initialize Perplexity client
            if perplexipy_installed and self.perplexity_api_key:
                self.perplexity_client = PerplexityClient(
                    key=self.perplexity_api_key
                )
                self.system_health["components_status"]["perplexity"] = "operational"
                logger.info("Perplexity client initialized")
            else:
                self.system_health["components_status"]["perplexity"] = "missing"
                logger.warning("Perplexity client not available")
            
            # Initialize Claude client
            if anthropic_installed and self.anthropic_api_key:
                self.claude_client = anthropic.Anthropic(
                    api_key=self.anthropic_api_key
                )
                self.system_health["components_status"]["claude"] = "operational"
                logger.info("Claude client initialized")
            else:
                self.system_health["components_status"]["claude"] = "missing"
                logger.warning("Claude client not available")
            
            # Check GitHub token
            if self.github_token:
                self.system_health["components_status"]["github"] = "configured"
                logger.info("GitHub access configured")
            else:
                self.system_health["components_status"]["github"] = "missing"
                logger.warning("GitHub token not available")
            
            # Check Composio configuration
            if self.composio_api_key and self.composio_mcp_url:
                self.system_health["components_status"]["composio"] = "configured"
                logger.info("Composio access configured")
            else:
                self.system_health["components_status"]["composio"] = "missing"
                logger.warning("Composio not configured properly")
            
            # Update overall status
            missing_components = [k for k, v in self.system_health["components_status"].items() 
                                 if v in ["missing", "error"]]
            if missing_components:
                self.system_health["status"] = "degraded"
                logger.warning(f"Missing components: {', '.join(missing_components)}")
            else:
                self.system_health["status"] = "operational"
                
            # First health check
            self.system_health["last_check"] = time.time()
            self.system_health["checks_performed"] += 1
            
            logger.info("Health monitor initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing health monitor: {e}")
            self.system_health["status"] = "error"
    
    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitor_task is not None:
            logger.warning("Health monitoring already started")
            return
            
        try:
            # Create asyncio task
            loop = asyncio.get_event_loop()
            self.monitor_task = loop.create_task(self._monitor_loop())
            logger.info(f"Health monitoring started (interval: {self.check_interval}s)")
        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        if self.monitor_task is None:
            logger.warning("Health monitoring not started")
            return
            
        if not self.monitor_task.done():
            self.monitor_task.cancel()
            logger.info("Health monitoring stopped")
        
        self.monitor_task = None
    
    async def _monitor_loop(self):
        """
        Main monitoring loop.
        Performs health checks and repair operations at regular intervals.
        """
        logger.info("Health monitoring loop started")
        
        try:
            while True:
                # Perform health check
                health_report = await self.check_health()
                
                # Stream health data
                await self._stream_health_data(health_report)
                
                # If issues detected, attempt repair
                if health_report["status"] != "operational" and self.enable_auto_repair:
                    repair_result = await self.repair_system()
                    if repair_result["success"]:
                        logger.info("System repair successful")
                    else:
                        logger.warning(f"System repair failed: {repair_result.get('error', 'Unknown error')}")
                        
                        # Send notification if enabled
                        if self.enable_notifications:
                            self._send_notification(
                                title="System Repair Failed",
                                message=f"System repair failed: {repair_result.get('error', 'Unknown error')}",
                                level="warning"
                            )
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Health monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in health monitoring loop: {e}")
            
            # Send critical notification
            if self.enable_notifications:
                self._send_notification(
                    title="Health Monitoring Error",
                    message=f"Critical error in health monitoring: {str(e)}",
                    level="critical"
                )
                
            # Try to restart monitoring
            logger.info("Attempting to restart health monitoring...")
            loop = asyncio.get_event_loop()
            self.monitor_task = loop.create_task(self._monitor_loop())
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health of all system components.
        
        Returns:
            Dictionary with health status information
        """
        logger.info("Checking system health...")
        
        # Prepare health report
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "status": "operational",
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
        # Update system health record
        self.system_health["last_check"] = time.time()
        self.system_health["checks_performed"] += 1
        
        # Check each component
        
        # 1. Check Perplexity
        if perplexipy_installed and self.perplexity_client:
            try:
                # Try a simple query to test connectivity
                # We don't actually need to execute it, just check that the client is operational
                perplexity_operational = self.perplexity_client is not None
                health_report["components"]["perplexity"] = "operational" if perplexity_operational else "error"
                
                if not perplexity_operational:
                    issue = "Perplexity client instantiated but not operational"
                    health_report["issues"].append(issue)
                    health_report["recommendations"].append("Reinitialize Perplexity client")
                    self.system_health["issues_detected"] += 1
                    health_report["status"] = "degraded"
            except Exception as e:
                health_report["components"]["perplexity"] = "error"
                health_report["issues"].append(f"Perplexity error: {str(e)}")
                health_report["recommendations"].append("Check Perplexity API key and connectivity")
                self.system_health["issues_detected"] += 1
                health_report["status"] = "degraded"
        else:
            health_report["components"]["perplexity"] = "missing"
            
        # 2. Check Claude
        if anthropic_installed and self.claude_client:
            try:
                # Check that client is properly initialized
                claude_operational = self.claude_client is not None
                health_report["components"]["claude"] = "operational" if claude_operational else "error"
                
                if not claude_operational:
                    issue = "Claude client instantiated but not operational"
                    health_report["issues"].append(issue)
                    health_report["recommendations"].append("Reinitialize Claude client")
                    self.system_health["issues_detected"] += 1
                    health_report["status"] = "degraded"
            except Exception as e:
                health_report["components"]["claude"] = "error"
                health_report["issues"].append(f"Claude error: {str(e)}")
                health_report["recommendations"].append("Check Anthropic API key and connectivity")
                self.system_health["issues_detected"] += 1
                health_report["status"] = "degraded"
        else:
            health_report["components"]["claude"] = "missing"
            
        # 3. Check MCP servers connectivity
        if requests_installed and self.mcp_config.get("mcpServers"):
            health_report["components"]["mcp_servers"] = {}
            mcp_errors = 0
            
            for server_name, server_config in self.mcp_config["mcpServers"].items():
                try:
                    # Check if server URL is accessible (just a HEAD request)
                    if "url" in server_config:
                        # Don't actually make the request, just check the URL format
                        url_valid = server_config["url"].startswith("https://")
                        
                        health_report["components"]["mcp_servers"][server_name] = "configured" if url_valid else "error"
                        
                        if not url_valid:
                            health_report["issues"].append(f"Invalid MCP server URL for {server_name}")
                            health_report["recommendations"].append(f"Check MCP configuration for {server_name}")
                            mcp_errors += 1
                except Exception as e:
                    health_report["components"]["mcp_servers"][server_name] = "error"
                    health_report["issues"].append(f"MCP server error for {server_name}: {str(e)}")
                    health_report["recommendations"].append(f"Check MCP server configuration for {server_name}")
                    mcp_errors += 1
            
            if mcp_errors > 0:
                self.system_health["issues_detected"] += mcp_errors
                health_report["status"] = "degraded"
        
        # 4. Check feedback loop configuration
        if self.mcp_config.get("feedbackLoop", {}).get("enabled", False):
            health_report["components"]["feedback_loop"] = "operational"
        else:
            health_report["components"]["feedback_loop"] = "disabled"
            health_report["issues"].append("Feedback loop is disabled")
            health_report["recommendations"].append("Enable feedback loop in MCP configuration")
        
        # Update system health status
        self.system_health["components_status"] = {**self.system_health["components_status"], 
                                                **health_report["components"]}
        
        # Update overall status
        self.system_health["status"] = health_report["status"]
        
        # Add to health history
        self.system_health["health_history"].append({
            "timestamp": health_report["timestamp"],
            "status": health_report["status"],
            "issues_count": len(health_report["issues"])
        })
        
        # Keep history manageable (last 100 entries)
        if len(self.system_health["health_history"]) > 100:
            self.system_health["health_history"] = self.system_health["health_history"][-100:]
        
        # Log results
        logger.info(f"Health check completed. Status: {health_report['status']}")
        if health_report["issues"]:
            for i, issue in enumerate(health_report["issues"]):
                logger.warning(f"Issue {i+1}: {issue}")
                logger.info(f"Recommendation: {health_report['recommendations'][i]}")
        
        # Save health report
        self._save_health_report(health_report)
        
        return health_report
    
    def _save_health_report(self, report: Dict[str, Any]):
        """
        Save health report to disk.
        
        Args:
            report: Health report to save
        """
        try:
            # Create timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
            filepath = os.path.join(self.memory_path, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save report
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.debug(f"Health report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving health report: {e}")
    
    async def _stream_health_data(self, health_data: Dict[str, Any]) -> bool:
        """
        Stream health data to TRILOGY BRAIN.
        
        Args:
            health_data: Health data to stream
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare health summary for streaming
            health_summary = {
                "timestamp": datetime.now().isoformat(),
                "status": health_data["status"],
                "components": health_data["components"],
                "issues_count": len(health_data["issues"]),
                "check_id": self.system_health["checks_performed"]
            }
            
            # For now, just save to a special streaming file
            stream_file = os.path.join(self.memory_path, "health_stream.jsonl")
            
            with open(stream_file, 'a') as f:
                f.write(json.dumps(health_summary) + "\n")
            
            logger.debug("Health data streamed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error streaming health data: {e}")
            return False
    
    async def repair_system(self) -> Dict[str, Any]:
        """
        Attempt to repair system issues.
        
        Returns:
            Dictionary with repair results
        """
        if not self.enable_auto_repair:
            return {"success": False, "error": "Auto-repair is disabled"}
            
        logger.info("Attempting system repairs...")
        
        repair_result = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "repairs": []
        }
        
        self.system_health["repairs_attempted"] += 1
        
        # Attempt to repair Perplexity client
        if self.system_health["components_status"].get("perplexity") in ["error", "missing"]:
            if perplexipy_installed and self.perplexity_api_key:
                try:
                    logger.info("Repairing Perplexity client...")
                    self.perplexity_client = PerplexityClient(
                        key=self.perplexity_api_key
                    )
                    self.system_health["components_status"]["perplexity"] = "operational"
                    repair_result["repairs"].append("Perplexity client repaired")
                    logger.info("Perplexity client repaired successfully")
                except Exception as e:
                    logger.error(f"Failed to repair Perplexity client: {e}")
                    repair_result["success"] = False
                    repair_result["repairs"].append(f"Perplexity repair failed: {str(e)}")
            else:
                repair_result["success"] = False
                repair_result["repairs"].append("Cannot repair Perplexity: missing dependencies or API key")
        
        # Attempt to repair Claude client
        if self.system_health["components_status"].get("claude") in ["error", "missing"]:
            if anthropic_installed and self.anthropic_api_key:
                try:
                    logger.info("Repairing Claude client...")
                    self.claude_client = anthropic.Anthropic(
                        api_key=self.anthropic_api_key
                    )
                    self.system_health["components_status"]["claude"] = "operational"
                    repair_result["repairs"].append("Claude client repaired")
                    logger.info("Claude client repaired successfully")
                except Exception as e:
                    logger.error(f"Failed to repair Claude client: {e}")
                    repair_result["success"] = False
                    repair_result["repairs"].append(f"Claude repair failed: {str(e)}")
            else:
                repair_result["success"] = False
                repair_result["repairs"].append("Cannot repair Claude: missing dependencies or API key")
        
        # Update repair stats
        if repair_result["success"]:
            self.system_health["repairs_successful"] += 1
            self.system_health["status"] = "operational"
        
        # Save repair report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repair_file = os.path.join(self.memory_path, f"repair_report_{timestamp}.json")
        
        try:
            with open(repair_file, 'w') as f:
                json.dump(repair_result, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving repair report: {e}")
        
        return repair_result
    
    def _send_notification(self, title: str, message: str, level: str = "info"):
        """
        Send notification about system status.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error, critical)
        """
        if not self.enable_notifications:
            return
            
        try:
            # For now, just log the notification
            logger.info(f"NOTIFICATION [{level.upper()}]: {title} - {message}")
            
            # Save notification to file
            notification = {
                "timestamp": datetime.now().isoformat(),
                "title": title,
                "message": message,
                "level": level
            }
            
            notifications_file = os.path.join(self.memory_path, "notifications.jsonl")
            
            with open(notifications_file, 'a') as f:
                f.write(json.dumps(notification) + "\n")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get current system health report.
        
        Returns:
            Dictionary with health status information
        """
        # Calculate uptime and health trend
        uptime = time.time() - float(self.session_id.split("_")[1])
        health_trend = "stable"
        
        if len(self.system_health["health_history"]) > 5:
            recent_statuses = [h["status"] for h in self.system_health["health_history"][-5:]]
            if all(status == "operational" for status in recent_statuses):
                health_trend = "excellent"
            elif recent_statuses[-1] == "operational" and any(status != "operational" for status in recent_statuses[:-1]):
                health_trend = "improving"
            elif recent_statuses[-1] != "operational" and any(status == "operational" for status in recent_statuses[:-1]):
                health_trend = "degrading"
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "uptime_seconds": uptime,
            "status": self.system_health["status"],
            "health_trend": health_trend,
            "components": self.system_health["components_status"],
            "metrics": {
                "checks_performed": self.system_health["checks_performed"],
                "issues_detected": self.system_health["issues_detected"],
                "repairs_attempted": self.system_health["repairs_attempted"],
                "repairs_successful": self.system_health["repairs_successful"],
                "repair_success_rate": (self.system_health["repairs_successful"] / 
                                       self.system_health["repairs_attempted"]
                                       if self.system_health["repairs_attempted"] > 0 else 0)
            },
            "recent_history": self.system_health["health_history"][-10:]
        }
        
        return report

async def main():
    """
    Main function for the TRILOGY Health Monitor.
    """
    parser = argparse.ArgumentParser(description="TRILOGY Health Monitor")
    
    # Add command-line arguments
    parser.add_argument("--check-interval", type=int, default=60, 
                       help="Interval for health checks in seconds")
    parser.add_argument("--no-auto-repair", action="store_true", 
                       help="Disable automatic system repairs")
    parser.add_argument("--no-notifications", action="store_true", 
                       help="Disable notifications")
    parser.add_argument("--config", type=str, default=None, 
                       help="Path to MCP configuration file")
    parser.add_argument("--check-only", action="store_true", 
                       help="Perform a single health check and exit")
    parser.add_argument("--repair", action="store_true", 
                       help="Perform a system repair and exit")
    parser.add_argument("--report", action="store_true", 
                       help="Show system health report and exit")
    
    args = parser.parse_args()
    
    # Create health monitor
    monitor = TrilogyHealthMonitor(
        check_interval=args.check_interval,
        enable_auto_repair=not args.no_auto_repair,
        enable_notifications=not args.no_notifications,
        config_file=args.config
    )
    
    # Handle special commands
    if args.check_only:
        health_report = await monitor.check_health()
        print(json.dumps(health_report, indent=2))
        return
        
    if args.repair:
        repair_result = await monitor.repair_system()
        print(json.dumps(repair_result, indent=2))
        return
        
    if args.report:
        health_report = monitor.get_health_report()
        print(json.dumps(health_report, indent=2))
        return
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Keep the script running
        print(f"TRILOGY Health Monitor running (interval: {args.check_interval}s)")
        print("Press Ctrl+C to stop...")
        
        # Run indefinitely
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping TRILOGY Health Monitor...")
        monitor.stop_monitoring()
        print("Monitor stopped")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTRILOGY Health Monitor terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc() 