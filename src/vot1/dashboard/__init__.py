"""
VOT1 Dashboard

A web-based dashboard for VOT1 with Three.js visualization and Flask backend.
"""

import os
import logging
from typing import Optional, Union
from pathlib import Path

# Import the server implementation
try:
    from .server import DashboardServer, create_dashboard
except ImportError as e:
    logging.warning(f"Dashboard server not fully available: {e}")
    
    # Provide minimal placeholder implementations
    class DashboardServer:
        def __init__(self, *args, **kwargs):
            logging.error("DashboardServer not available, missing dependencies")
            
        def start(self, *args, **kwargs):
            logging.error("DashboardServer not available, missing dependencies")
    
    def create_dashboard(*args, **kwargs):
        logging.error("Dashboard creation failed, missing dependencies")
        return None

# Package version
__version__ = "0.1.0"

# Determine the path to the static folder
DASHBOARD_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(DASHBOARD_PATH, "static")

def ensure_static_files():
    """
    Ensure all required static files exist.
    Returns True if all files are present, False otherwise.
    """
    required_files = [
        "index.html",
        "css/style.css",
        "js/api.js",
        "js/app.js",
        "js/init.js",
        "js/memory-chart.js",
        "js/three-visualization.js"
    ]
    
    for file in required_files:
        if not os.path.exists(os.path.join(STATIC_FOLDER, file)):
            logging.warning(f"Missing dashboard file: {file}")
            return False
    
    return True

# Ensure dashboard files are available
if not os.path.exists(STATIC_FOLDER):
    logging.warning(f"Dashboard static folder not found at {STATIC_FOLDER}")
else:
    if not ensure_static_files():
        logging.warning("Dashboard is missing some required files")
    else:
        logging.info("Dashboard files verified successfully")

# Export the public interface
__all__ = ["create_dashboard", "DashboardServer"] 