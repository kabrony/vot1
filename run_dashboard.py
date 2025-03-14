#!/usr/bin/env python3
"""
VOTai Dashboard Runner

A simple script to run the VOTai dashboard from the project root.
"""

import os
import sys
import logging
from pathlib import Path

# Set up correct path for imports
sys.path.append(str(Path(__file__).parent))

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the VOTai Dashboard."""
    try:
        from src.vot1.dashboard.app import main as run_dashboard
        
        # Run the dashboard
        logger.info("Starting VOTai Dashboard...")
        run_dashboard()
    except ImportError as e:
        logger.error(f"Failed to import dashboard components: {e}")
        logger.error("Make sure you have installed all required dependencies")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 