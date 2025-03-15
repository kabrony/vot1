#!/usr/bin/env python3
"""
TRILOGY BRAIN Autonomous System Starter

This script automatically sets up and launches the TRILOGY BRAIN ecosystem with:
1. System health monitoring that runs continuously
2. Memory system initialization
3. Agent processes management
4. Automatic recovery mechanisms

Usage:
    python autorun.py [--help] [--config CONFIG] [--daemon]
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import subprocess
import signal
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/autorun.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TrilogyAutostarter")

class AutoStarter:
    """
    Autonomous system starter for TRILOGY BRAIN ecosystem.
    """
    
    def __init__(self, config_file: str = "config/autorun.json"):
        """Initialize with configuration file."""
        self.config_file = config_file
        self.config = self._load_config()
        self.processes = {}
        self.running = False
        self.threads = []
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        # Default configuration
        return {
            "health_monitor": {
                "enabled": True,
                "script": "system_health_monitor.py",
                "args": ["start", "--interval", "60"],
                "priority": 1
            },
            "memory_system": {
                "enabled": True,
                "init_script": "memory_init.py",
                "priority": 2
            },
            "agents": [
                {
                    "name": "Research Agent",
                    "script": "enhanced_research_agent.py",
                    "args": ["--self-analyze"],
                    "enabled": True,
                    "auto_restart": True,
                    "priority": 3
                },
                {
                    "name": "Hybrid Thinking Tester",
                    "script": "test_claude_hybrid.py",
                    "enabled": False,
                    "auto_restart": False,
                    "priority": 4
                }
            ],
            "directory_structure": [
                "logs",
                "memory",
                "memory/health",
                "memory/agent",
                "output",
                "config",
                "backups",
                "backups/memory"
            ]
        }
    
    def _setup_directory_structure(self):
        """Create required directories."""
        for directory in self.config.get("directory_structure", []):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def start(self):
        """Start all system components."""
        if self.running:
            logger.warning("System is already running")
            return
        
        logger.info("Starting TRILOGY BRAIN ecosystem...")
        
        # Setup directory structure
        self._setup_directory_structure()
        
        # Create configuration if missing
        if not os.path.exists("config/health_monitor.json"):
            self._create_default_health_config()
        
        # Start health monitor first
        health_config = self.config.get("health_monitor", {})
        if health_config.get("enabled", True):
            self._start_component("health_monitor", health_config)
        
        # Initialize memory system
        memory_config = self.config.get("memory_system", {})
        if memory_config.get("enabled", True):
            self._start_component("memory_system", memory_config)
        
        # Start agents
        agents = sorted(self.config.get("agents", []), key=lambda x: x.get("priority", 999))
        for agent in agents:
            if agent.get("enabled", True):
                self._start_component(agent["name"], agent)
        
        # Set up monitoring thread
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        self.threads.append(monitor_thread)
        
        logger.info("TRILOGY BRAIN ecosystem started")
    
    def _start_component(self, name: str, config: Dict[str, Any]):
        """Start a system component."""
        script = config.get("script", "")
        if not script or not os.path.exists(script):
            logger.error(f"Script not found for component {name}: {script}")
            return
        
        args = config.get("args", [])
        cmd = ["python3", script] + args
        
        try:
            logger.info(f"Starting component {name}: {' '.join(cmd)}")
            
            # Start the process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Store process information
            self.processes[name] = {
                "process": process,
                "config": config,
                "start_time": time.time(),
                "restart_count": 0
            }
            
            # Set up output monitoring threads
            self._setup_output_monitors(name, process)
        except Exception as e:
            logger.error(f"Error starting component {name}: {e}")
    
    def _setup_output_monitors(self, name: str, process: subprocess.Popen):
        """Set up threads to monitor process output."""
        def monitor_output(stream, is_error=False):
            prefix = f"[{name}] "
            try:
                for line in stream:
                    if is_error:
                        logger.error(f"{prefix}{line.strip()}")
                    else:
                        logger.info(f"{prefix}{line.strip()}")
            except Exception as e:
                logger.error(f"Error monitoring output for {name}: {e}")
        
        # Start stdout monitor
        stdout_thread = threading.Thread(
            target=monitor_output,
            args=(process.stdout, False)
        )
        stdout_thread.daemon = True
        stdout_thread.start()
        self.threads.append(stdout_thread)
        
        # Start stderr monitor
        stderr_thread = threading.Thread(
            target=monitor_output,
            args=(process.stderr, True)
        )
        stderr_thread.daemon = True
        stderr_thread.start()
        self.threads.append(stderr_thread)
    
    def _monitor_processes(self):
        """Monitor running processes and restart if needed."""
        while self.running:
            for name, info in list(self.processes.items()):
                process = info["process"]
                config = info["config"]
                
                # Check if process is still running
                if process.poll() is not None:
                    exit_code = process.returncode
                    logger.warning(f"Process {name} exited with code {exit_code}")
                    
                    # Check if auto-restart is enabled
                    if config.get("auto_restart", False):
                        # Check if we've hit the restart limit
                        restart_limit = config.get("max_restarts", 5)
                        if info["restart_count"] < restart_limit:
                            logger.info(f"Restarting process {name} (attempt {info['restart_count'] + 1}/{restart_limit})")
                            self._start_component(name, config)
                            self.processes[name]["restart_count"] += 1
                        else:
                            logger.error(f"Process {name} exceeded restart limit ({restart_limit})")
                    else:
                        logger.info(f"Auto-restart disabled for {name}, not restarting")
                    
                    # Remove from processes list
                    del self.processes[name]
            
            # Sleep for a short interval
            time.sleep(5)
    
    def stop(self):
        """Stop all running processes."""
        if not self.running:
            logger.warning("System is not running")
            return
        
        logger.info("Stopping TRILOGY BRAIN ecosystem...")
        
        # Stop all processes
        for name, info in self.processes.items():
            try:
                process = info["process"]
                logger.info(f"Terminating process: {name}")
                process.terminate()
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {name} did not terminate, killing")
                    process.kill()
            except Exception as e:
                logger.error(f"Error stopping process {name}: {e}")
        
        # Clear processes list
        self.processes.clear()
        self.running = False
        
        logger.info("TRILOGY BRAIN ecosystem stopped")
    
    def _create_default_health_config(self):
        """Create default health monitor configuration."""
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        
        health_config = {
            "check_interval": 60,
            "self_healing_enabled": True,
            "alert_threshold": 3,
            "max_memory_entries": 1000,
            "memory_path": "memory/health",
            "expected_agents": [
                "enhanced_research_agent.py",
                "test_claude_hybrid.py"
            ],
            "agent_commands": {
                "enhanced_research_agent.py": "python3 enhanced_research_agent.py --self-analyze",
                "test_claude_hybrid.py": "python3 test_claude_hybrid.py"
            },
            "log_dir": "logs",
            "alert_log_file": "logs/alerts.log"
        }
        
        # Write configuration
        try:
            with open(os.path.join(config_dir, "health_monitor.json"), "w") as f:
                json.dump(health_config, f, indent=4)
            logger.info("Created default health monitor configuration")
        except Exception as e:
            logger.error(f"Error creating health monitor configuration: {e}")

def handle_signal(signum, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    global auto_starter
    if auto_starter:
        auto_starter.stop()
    sys.exit(0)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TRILOGY BRAIN Autonomous System Starter")
    parser.add_argument("--config", "-c", default="config/autorun.json", help="Configuration file")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    
    # Create and start the auto starter
    global auto_starter
    auto_starter = AutoStarter(config_file=args.config)
    auto_starter.start()
    
    if args.daemon:
        # Detach from terminal
        try:
            pid = os.fork()
            if pid > 0:
                # Exit parent process
                sys.exit(0)
        except OSError as e:
            logger.error(f"Fork failed: {e}")
            sys.exit(1)
        
        # Detach from terminal
        os.setsid()
        
        # Fork again
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError as e:
            logger.error(f"Second fork failed: {e}")
            sys.exit(1)
        
        # Write PID file
        pid_file = "/tmp/trilogy_autorun.pid"
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        
        # Close all file descriptors
        for fd in range(0, 3):
            try:
                os.close(fd)
            except OSError:
                pass
        
        # Redirect standard file descriptors
        sys.stdout = open("logs/autorun_stdout.log", "a")
        sys.stderr = open("logs/autorun_stderr.log", "a")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        auto_starter.stop()

if __name__ == "__main__":
    auto_starter = None
    main() 