#!/usr/bin/env python3
"""
Local MCP Bridge Launcher

This script provides an easy way to start the Local MCP Bridge with proper configuration,
environment variable handling, and monitoring capabilities.
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import signal
import webbrowser
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'launcher.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class LocalMCPLauncher:
    """
    Launcher for the Local MCP Bridge.
    
    This class provides methods to:
    - Check prerequisites
    - Load environment variables
    - Start the bridge
    - Monitor the bridge
    - Open a dashboard or status page
    """
    
    def __init__(self, args):
        """Initialize the launcher with command-line arguments."""
        self.args = args
        self.process = None
        self.start_time = None
        self.config = self._load_config()
        
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or environment variables.
        
        Returns:
            Dictionary with configuration values
        """
        config = {}
        
        # Check for config file
        if self.args.config and os.path.exists(self.args.config):
            with open(self.args.config, 'r') as f:
                config = json.load(f)
        
        # Load environment variables
        # Format: VOT1_MCP_GITHUB_KEY, VOT1_MCP_PORT, etc.
        for key, value in os.environ.items():
            if key.startswith('VOT1_MCP_'):
                parts = key[9:].lower().split('_')
                
                if len(parts) == 2 and parts[0] in ['host', 'port', 'debug']:
                    # Server config
                    if 'server' not in config:
                        config['server'] = {}
                    config['server'][parts[0]] = value if parts[0] != 'port' else int(value)
                elif len(parts) >= 2 and parts[1] == 'key':
                    # API keys
                    if 'api_keys' not in config:
                        config['api_keys'] = {}
                    service = parts[0].upper()
                    config['api_keys'][service] = value
        
        return config
    
    def check_prerequisites(self) -> bool:
        """
        Check prerequisites for running the bridge.
        
        Returns:
            True if all prerequisites are met, False otherwise
        """
        # Check Python version
        if sys.version_info < (3, 7):
            logger.error("Python 3.7 or higher is required")
            return False
        
        # Check for required modules
        try:
            import flask
            import requests
        except ImportError as e:
            logger.error(f"Required module not found: {e}")
            logger.info("Please install required modules: pip install -r requirements.txt")
            return False
        
        # Check for configuration file
        mcp_config_path = "src/vot1/local_mcp/config/mcp.json"
        if not os.path.exists(mcp_config_path):
            logger.error(f"MCP configuration file not found: {mcp_config_path}")
            return False
        
        # Check for bridge script
        bridge_script = "run_local_mcp_bridge.py"
        if not os.path.exists(bridge_script):
            logger.error(f"Bridge script not found: {bridge_script}")
            return False
        
        return True
    
    def build_command(self) -> List[str]:
        """
        Build the command to run the bridge.
        
        Returns:
            List of command parts
        """
        cmd = ["python", "run_local_mcp_bridge.py"]
        
        # Add server configuration
        if 'server' in self.config:
            if 'host' in self.config['server']:
                cmd.extend(["--host", str(self.config['server']['host'])])
            if 'port' in self.config['server']:
                cmd.extend(["--port", str(self.config['server']['port'])])
            if self.config['server'].get('debug', False):
                cmd.append("--debug")
        
        # Add API keys
        if 'api_keys' in self.config:
            for service, key in self.config['api_keys'].items():
                if service == "GITHUB":
                    cmd.extend(["--github-token", key])
                elif service == "PERPLEXITY":
                    cmd.extend(["--perplexity-key", key])
                elif service == "FIRECRAWL":
                    cmd.extend(["--firecrawl-key", key])
                elif service == "FIGMA":
                    cmd.extend(["--figma-token", key])
                elif service == "COMPOSIO":
                    cmd.extend(["--composio-key", key])
        
        # Add command-line arguments
        if self.args.host:
            cmd.extend(["--host", self.args.host])
        if self.args.port:
            cmd.extend(["--port", str(self.args.port)])
        if self.args.debug:
            cmd.append("--debug")
        if self.args.no_cache:
            cmd.append("--no-cache")
        if self.args.config:
            cmd.extend(["--config", self.args.config])
        
        return cmd
    
    def start_bridge(self) -> bool:
        """
        Start the Local MCP Bridge.
        
        Returns:
            True if started successfully, False otherwise
        """
        cmd = self.build_command()
        logger.info(f"Starting Local MCP Bridge: {' '.join(cmd)}")
        
        try:
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.start_time = time.time()
            
            # Wait for server to start
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self._check_server_running():
                    logger.info("Local MCP Bridge started successfully")
                    return True
            
            logger.error("Timed out waiting for server to start")
            return False
            
        except Exception as e:
            logger.error(f"Error starting Local MCP Bridge: {e}")
            return False
    
    def _check_server_running(self) -> bool:
        """
        Check if the server is running.
        
        Returns:
            True if the server is running, False otherwise
        """
        import requests
        
        try:
            host = self.args.host or self.config.get('server', {}).get('host', 'localhost')
            port = self.args.port or self.config.get('server', {}).get('port', 5678)
            
            response = requests.get(f"http://{host}:{port}/api/status", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def monitor_bridge(self):
        """Monitor the bridge and display logs."""
        if not self.process:
            logger.error("Bridge not started")
            return
        
        try:
            # Read and print output
            for line in iter(self.process.stdout.readline, ''):
                print(line, end='')
                
                # Check if the process has exited
                if self.process.poll() is not None:
                    break
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        finally:
            # Check if the process is still running
            if self.process.poll() is None:
                # Process is still running, don't stop it
                pass
    
    def open_dashboard(self):
        """Open a dashboard or status page in the web browser."""
        if not self._check_server_running():
            logger.error("Server not running, cannot open dashboard")
            return
        
        host = self.args.host or self.config.get('server', {}).get('host', 'localhost')
        port = self.args.port or self.config.get('server', {}).get('port', 5678)
        
        # Create a simple HTML dashboard
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False) as f:
            dashboard_path = f.name
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Local MCP Bridge Dashboard</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .panel {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                    .endpoints {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; }}
                    .endpoint {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                    .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
                    .metric {{ background-color: #f0f8ff; padding: 10px; border-radius: 5px; }}
                    button {{ padding: 8px 16px; background-color: #4CAF50; color: white; border: none; cursor: pointer; border-radius: 4px; }}
                    button:hover {{ background-color: #45a049; }}
                </style>
                <script>
                    function fetchStatus() {{
                        fetch('http://{host}:{port}/api/status')
                            .then(response => response.json())
                            .then(data => {{
                                document.getElementById('status').textContent = data.status;
                                document.getElementById('uptime').textContent = formatTime(data.uptime);
                                
                                const servicesList = document.getElementById('available-services');
                                servicesList.innerHTML = '';
                                data.available_services.forEach(service => {{
                                    const li = document.createElement('li');
                                    li.textContent = service;
                                    servicesList.appendChild(li);
                                }});
                                
                                const connectedList = document.getElementById('connected-services');
                                connectedList.innerHTML = '';
                                data.connected_services.forEach(service => {{
                                    const li = document.createElement('li');
                                    li.textContent = service;
                                    connectedList.appendChild(li);
                                }});
                            }})
                            .catch(error => console.error('Error fetching status:', error));
                    }}
                    
                    function fetchMetrics() {{
                        fetch('http://{host}:{port}/api/metrics')
                            .then(response => response.json())
                            .then(data => {{
                                const metrics = data.metrics;
                                document.getElementById('api-calls').textContent = metrics.api_calls;
                                document.getElementById('api-errors').textContent = metrics.api_errors;
                                document.getElementById('error-rate').textContent = 
                                    (metrics.error_rate * 100).toFixed(2) + '%';
                                document.getElementById('avg-response-time').textContent = 
                                    metrics.avg_response_time.toFixed(3) + ' seconds';
                                
                                if (metrics.cache_stats) {{
                                    document.getElementById('cache-hits').textContent = metrics.cache_stats.hits;
                                    document.getElementById('cache-misses').textContent = metrics.cache_stats.misses;
                                    document.getElementById('cache-last-cleared').textContent = 
                                        new Date(metrics.cache_stats.last_cleared * 1000).toLocaleString();
                                }}
                            }})
                            .catch(error => console.error('Error fetching metrics:', error));
                    }}
                    
                    function clearCache() {{
                        fetch('http://{host}:{port}/api/clear-cache', {{ method: 'POST' }})
                            .then(response => response.json())
                            .then(data => {{
                                alert('Cache cleared successfully');
                                fetchMetrics();
                            }})
                            .catch(error => console.error('Error clearing cache:', error));
                    }}
                    
                    function formatTime(seconds) {{
                        const days = Math.floor(seconds / 86400);
                        seconds %= 86400;
                        const hours = Math.floor(seconds / 3600);
                        seconds %= 3600;
                        const minutes = Math.floor(seconds / 60);
                        seconds = Math.floor(seconds % 60);
                        
                        return `${{days}}d ${{hours}}h ${{minutes}}m ${{seconds}}s`;
                    }}
                    
                    // Refresh data every 5 seconds
                    setInterval(() => {{
                        fetchStatus();
                        fetchMetrics();
                    }}, 5000);
                    
                    // Initial fetch
                    document.addEventListener('DOMContentLoaded', () => {{
                        fetchStatus();
                        fetchMetrics();
                    }});
                </script>
            </head>
            <body>
                <h1>Local MCP Bridge Dashboard</h1>
                
                <div class="panel">
                    <h2>Server Status</h2>
                    <p><strong>Status:</strong> <span id="status">Loading...</span></p>
                    <p><strong>Uptime:</strong> <span id="uptime">Loading...</span></p>
                    <p><strong>Server URL:</strong> <a href="http://{host}:{port}">http://{host}:{port}</a></p>
                    
                    <div style="display: flex; gap: 30px;">
                        <div>
                            <h3>Available Services</h3>
                            <ul id="available-services">
                                <li>Loading...</li>
                            </ul>
                        </div>
                        <div>
                            <h3>Connected Services</h3>
                            <ul id="connected-services">
                                <li>Loading...</li>
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="panel">
                    <h2>Performance Metrics</h2>
                    <div class="metrics">
                        <div class="metric">
                            <h3>API Calls</h3>
                            <p id="api-calls">Loading...</p>
                        </div>
                        <div class="metric">
                            <h3>API Errors</h3>
                            <p id="api-errors">Loading...</p>
                        </div>
                        <div class="metric">
                            <h3>Error Rate</h3>
                            <p id="error-rate">Loading...</p>
                        </div>
                        <div class="metric">
                            <h3>Avg Response Time</h3>
                            <p id="avg-response-time">Loading...</p>
                        </div>
                        <div class="metric">
                            <h3>Cache Hits</h3>
                            <p id="cache-hits">Loading...</p>
                        </div>
                        <div class="metric">
                            <h3>Cache Misses</h3>
                            <p id="cache-misses">Loading...</p>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button onclick="clearCache()">Clear Cache</button>
                    </div>
                </div>
                
                <div class="panel">
                    <h2>API Endpoints</h2>
                    <div class="endpoints">
                        <div class="endpoint">
                            <h3>Check Connection</h3>
                            <p><code>GET /api/check-connection/&lt;service&gt;</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Get Required Parameters</h3>
                            <p><code>GET /api/get-required-parameters/&lt;service&gt;</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Initiate Connection</h3>
                            <p><code>POST /api/initiate-connection/&lt;service&gt;</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Call Function</h3>
                            <p><code>POST /api/call-function</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Status</h3>
                            <p><code>GET /api/status</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Metrics</h3>
                            <p><code>GET /api/metrics</code></p>
                        </div>
                        <div class="endpoint">
                            <h3>Clear Cache</h3>
                            <p><code>POST /api/clear-cache</code></p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Open the dashboard in the browser
        webbrowser.open(f"file://{dashboard_path}")
        logger.info(f"Dashboard opened in browser: {dashboard_path}")
        
        # Return the URL
        return f"http://{host}:{port}"
    
    def run(self):
        """Run the launcher."""
        # Check prerequisites
        if not self.check_prerequisites():
            return 1
        
        # Start the bridge
        if not self.start_bridge():
            return 1
        
        # Open dashboard if requested
        if self.args.dashboard:
            self.open_dashboard()
        
        # Monitor the bridge
        if not self.args.detach:
            self.monitor_bridge()
        
        return 0
    
    def handle_signals(self):
        """Set up signal handlers."""
        def signal_handler(sig, frame):
            logger.info("Received signal to terminate")
            if self.process and self.process.poll() is None:
                logger.info("Stopping Local MCP Bridge")
                self.process.terminate()
                self.process.wait(timeout=5)
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Launch the Local MCP Bridge")
    
    # Server configuration
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    # MCP configuration
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--no-cache", action="store_true", help="Disable response caching")
    
    # Launcher options
    parser.add_argument("--dashboard", action="store_true", help="Open a dashboard in the browser")
    parser.add_argument("--detach", action="store_true", help="Start the bridge and exit")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Create and run the launcher
    launcher = LocalMCPLauncher(args)
    launcher.handle_signals()
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main()) 