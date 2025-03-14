#!/usr/bin/env python3
"""
VOTai Local MCP Bridge Server

This module provides a Flask server that exposes the VOTai LocalMCPBridge functionality
through HTTP endpoints, allowing local applications to interact with MCP services.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import json
import logging
import argparse
import time
import sys
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

from .bridge import LocalMCPBridge
from .port_finder import is_port_in_use, find_available_port
from .ascii_art import get_votai_ascii
from .github_integration import GitHubIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'local_mcp_server.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class LocalMCPServer:
    """
    Flask server that exposes the VOTai LocalMCPBridge functionality through HTTP endpoints.
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        host: str = "localhost",
        port: int = 5678,
        debug: bool = False,
        api_keys: Optional[Dict[str, str]] = None,
        cache_enabled: bool = True,
        enable_agents: bool = False,
        find_port: bool = False
    ):
        """
        Initialize the VOTai Local MCP Server.
        
        Args:
            config_path: Path to the MCP configuration file
            host: Host to bind the server to
            port: Port to bind the server to
            debug: Whether to run in debug mode
            api_keys: Dictionary of API keys for MCP services
            cache_enabled: Whether to enable caching
            enable_agents: Whether to enable agent ecosystem support
            find_port: Whether to find an available port if the specified port is in use
        """
        # Display VOTai signature
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai Local MCP Server initializing...")
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Initialize the bridge
        self.bridge = LocalMCPBridge(
            config_path=config_path,
            api_keys=api_keys,
            cache_enabled=cache_enabled
        )
        
        # Initialize GitHub integration
        self.github = GitHubIntegration(self.bridge)
        
        # Initialize Flask app
        self.app = Flask(__name__, static_folder='static')
        CORS(self.app)
        
        # Set server parameters
        self.host = host
        self.port = port
        self.debug = debug
        
        # Find available port if requested
        if find_port and is_port_in_use(self.port):
            self.port = find_available_port(start_port=self.port)
            logger.info(f"Port {port} is in use, using port {self.port} instead")
        
        # Initialize routes
        self._init_routes()
        
        # Initialize agent ecosystem if requested
        if enable_agents:
            self._init_agent_ecosystem()
        
        logger.info("VOTai Local MCP Server initialized successfully")
    
    def _init_routes(self):
        """Register routes with the Flask app."""
        # Service connection routes
        self.app.route('/api/check-connection/<service>')(self.check_connection)
        self.app.route('/api/get-required-parameters/<service>')(self.get_required_parameters)
        self.app.route('/api/initiate-connection/<service>', methods=['POST'])(self.initiate_connection)
        
        # Function calling routes
        self.app.route('/api/call-function', methods=['POST'])(self.call_function)
        
        # Utility routes
        self.app.route('/api/status')(self.get_status)
        self.app.route('/api/metrics')(self.get_metrics)
        self.app.route('/api/clear-cache', methods=['POST'])(self.clear_cache)
        self.app.route('/api/routes')(self.list_routes)
        
        # Root route for health check
        self.app.route('/')(self.health_check)

        # New routes
        self.app.route('/api/github/status', methods=['GET'])(self.get_github_status)
        self.app.route('/github')(self.github_status_page)
        self.app.route('/api/caches/clear', methods=['POST'])(self.clear_caches)
    
    def _init_agent_ecosystem(self):
        """Initialize the agent ecosystem."""
        try:
            from .server_agents import create_agent_blueprint, start_agent_ecosystem
            
            # Register the agent blueprint
            agent_bp = create_agent_blueprint(self.bridge)
            self.app.register_blueprint(agent_bp, url_prefix='/api')
            
            # Start the agent ecosystem
            self.orchestrator = start_agent_ecosystem(self.bridge)
            
            logger.info("Agent ecosystem initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing agent ecosystem: {e}")
            self.enable_agents = False
    
    def check_connection(self, service):
        """API endpoint to check connection to a service."""
        connection_id = request.args.get('connection_id')
        result = self.bridge.check_connection(service, connection_id)
        return jsonify(result)
    
    def get_required_parameters(self, service):
        """API endpoint to get required parameters for a service."""
        result = self.bridge.get_required_parameters(service)
        return jsonify(result)
    
    def initiate_connection(self, service):
        """API endpoint to initiate a connection to a service."""
        parameters = request.json or {}
        result = self.bridge.initiate_connection(service, parameters)
        return jsonify(result)
    
    def call_function(self):
        """API endpoint to call an MCP function."""
        data = request.json or {}
        function_name = data.get('function_name')
        params = data.get('params', {})
        
        if not function_name:
            return jsonify({
                "successful": False,
                "error": "Function name is required"
            }), 400
        
        result = self.bridge.call_function(function_name, params)
        return jsonify(result)
    
    def get_status(self):
        """API endpoint to get server status."""
        available_services = []
        connected_services = []
        
        # Check which services are available and connected
        for service in [
            LocalMCPBridge.SERVICE_GITHUB,
            LocalMCPBridge.SERVICE_PERPLEXITY,
            LocalMCPBridge.SERVICE_FIRECRAWL,
            LocalMCPBridge.SERVICE_FIGMA,
            LocalMCPBridge.SERVICE_COMPOSIO
        ]:
            service_url = self.bridge.get_service_url(service)
            if service_url:
                available_services.append(service)
                
                # Check if we're connected
                connection = self.bridge.connections.get(service)
                if connection:
                    connected_services.append(service)
        
        status_data = {
            "successful": True,
            "status": "running",
            "uptime": time.time() - self.bridge.performance_metrics["start_time"],
            "available_services": available_services,
            "connected_services": connected_services
        }
        
        # Add agent ecosystem status if enabled
        if self.enable_agents and hasattr(self, 'orchestrator'):
            status_data["agent_ecosystem"] = {
                "enabled": True,
                "agent_count": len(self.orchestrator.list_agents())
            }
        else:
            status_data["agent_ecosystem"] = {
                "enabled": False
            }
        
        return jsonify(status_data)
    
    def get_metrics(self):
        """API endpoint to get server metrics."""
        metrics = self.bridge.get_performance_metrics()
        return jsonify({
            "successful": True,
            "metrics": metrics
        })
    
    def clear_cache(self):
        """API endpoint to clear the cache."""
        result = self.bridge.clear_cache()
        return jsonify(result)
    
    def health_check(self):
        """Root endpoint for health check."""
        return jsonify({
            "status": "healthy",
            "service": "Local MCP Bridge",
            "timestamp": time.time()
        })
    
    def get_github_status(self):
        """Get GitHub service status."""
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai GitHub Status API called")
        
        # Use the GitHub integration module instead of the bridge directly
        status = self.github.get_status()
        
        # Check if we have a GitHub PAT in environment
        github_pat = os.environ.get("GITHUB_PAT")
        if github_pat and not status.get("status", {}).get("connection_active", False):
            logger.info("Found GitHub PAT in environment, attempting to initialize connection")
            try:
                # Initialize connection with PAT
                connection_result = self.bridge.call_function("mcp_MCP_GITHUB_INITIATE_CONNECTION", {
                    "params": {
                        "tool": "GitHub",
                        "parameters": {
                            "api_key": github_pat
                        }
                    }
                })
                
                if connection_result.get("successful", False):
                    logger.info("GitHub connection initialized successfully")
                    # Get updated status
                    status = self.github.get_status()
                else:
                    logger.error(f"Failed to initialize GitHub connection: {connection_result.get('error')}")
            except Exception as e:
                logger.error(f"Error initializing GitHub connection: {e}")
        
        return jsonify(status)
    
    def github_status_page(self):
        """Serve the GitHub status page."""
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai GitHub Status Page requested")
        
        return send_from_directory('static', 'github_status.html')
    
    def clear_caches(self):
        """API endpoint to clear the caches."""
        result = self.bridge.clear_caches()
        return jsonify(result)
    
    def list_routes(self):
        """API endpoint to list all available routes."""
        routes = []
        for rule in self.app.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "path": str(rule)
            })
        
        return jsonify({
            "successful": True,
            "routes": routes
        })
    
    def run(self):
        """Run the server."""
        try:
            logger.info(f"Starting Local MCP Server on {self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=self.debug)
        except OSError as e:
            if "Address already in use" in str(e) and self.find_port:
                logger.error(f"Port {self.port} is already in use.")
                logger.info("Use the --find-port option to automatically find an available port.")
                raise RuntimeError(f"Port {self.port} is in use by another program. Either identify and stop that program, or start the server with a different port.")
            else:
                raise


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Run the Local MCP Bridge Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5678, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--config", help="Path to MCP configuration file")
    parser.add_argument("--enable-agents", action="store_true", help="Enable agent ecosystem")
    parser.add_argument("--find-port", action="store_true", help="Find an available port if the specified port is in use")
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Initialize and run server
        server = LocalMCPServer(
            config_path=args.config,
            host=args.host,
            port=args.port,
            debug=args.debug,
            enable_agents=args.enable_agents,
            find_port=args.find_port
        )
        server.run()
    except RuntimeError as e:
        logger.error(str(e))
        return 1
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    
    return 0


if __name__ == "__main__":
    exit(main()) 