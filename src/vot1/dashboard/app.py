#!/usr/bin/env python3
"""
VOTai Dashboard App

Main entry point for the VOTai dashboard application.
Initializes and runs the VOTai Dashboard web interface.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Set up logging
log_dir = os.path.expanduser('~/.vot1/logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'dashboard.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

try:
    from .dashboard import VOTaiDashboard
except ImportError:
    # When running directly as a script
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from vot1.dashboard.dashboard import VOTaiDashboard


def create_app(host="localhost", port=5000, debug=False, refresh_interval=60):
    """Create and configure the VOTai Dashboard app.
    
    Args:
        host: Hostname to bind the server to
        port: Port to bind the server to
        debug: Whether to enable Flask debug mode
        refresh_interval: Dashboard data refresh interval in seconds
        
    Returns:
        Flask application instance
    """
    logger.info(f"Creating VOTai Dashboard application (host={host}, port={port}, debug={debug})")
    
    # Initialize the dashboard
    dashboard = VOTaiDashboard(
        host=host,
        port=port,
        debug=debug,
        enable_memory=True,
        enable_github=True,
        enable_bridge=True,
        auto_refresh=True,
        refresh_interval=refresh_interval
    )
    
    # Get the Flask app instance (routes are already set up in VOTaiDashboard)
    app = dashboard.app
    
    # Store dashboard instance on app for access in views if needed
    app.dashboard = dashboard
    
    # Additional setup if needed
    app.config['dashboard'] = dashboard
    
    logger.info("VOTai Dashboard application created successfully")
    return app


def main():
    """Run the VOTai Dashboard application."""
    parser = argparse.ArgumentParser(description="VOTai Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--refresh", type=int, default=60, help="Dashboard refresh interval in seconds")
    
    args = parser.parse_args()
    
    logger.info(f"Starting VOTai Dashboard on {args.host}:{args.port} (debug={args.debug})")
    
    # Create the app
    dashboard_app = create_app(
        host=args.host,
        port=args.port,
        debug=args.debug,
        refresh_interval=args.refresh
    )
    
    # Run the app - use werkzeug's run_simple for more control
    from werkzeug.serving import run_simple
    run_simple(
        hostname=args.host,
        port=args.port,
        application=dashboard_app,
        use_reloader=args.debug,
        use_debugger=args.debug
    )


if __name__ == "__main__":
    main() 