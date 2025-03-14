#!/usr/bin/env python3
"""
Run Local MCP Bridge

This script starts the Local MCP Bridge server, which provides a bridge to MCP services.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Import the CLI module
from src.vot1.local_mcp.cli import main

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the bridge
    sys.exit(main()) 