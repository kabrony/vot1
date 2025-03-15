#!/usr/bin/env python3
"""
VOT1 Dashboard Application Runner

This module provides a simple entry point for running the VOT1 dashboard server.
It imports and runs the dashboard server from the server module.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to Python path if running this file directly
current_file = os.path.abspath(__file__)
project_root = os.path.abspath(os.path.join(os.path.dirname(current_file), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

# Import the dashboard server
try:
    from src.vot1.dashboard.server import main as run_dashboard
except ImportError:
    try:
        from vot1.dashboard.server import main as run_dashboard
    except ImportError as e:
        logger.error(f"Failed to import dashboard server: {e}")
        logger.error("Please ensure VOT1 is properly installed or run from project root")
        sys.exit(1)

def main():
    """
    Main entry point for running the dashboard.
    Creates required directories if they don't exist.
    """
    # Ensure memory directory exists
    memory_dir = os.environ.get('VOT1_MEMORY_PATH', os.path.join(project_root, 'memory'))
    Path(memory_dir).mkdir(parents=True, exist_ok=True)
    
    # Ensure logs directory exists
    logs_dir = os.path.join(project_root, 'logs')
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    # Run the dashboard
    logger.info("Starting VOT1 dashboard...")
    run_dashboard()

if __name__ == '__main__':
    main() 