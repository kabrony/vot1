#!/usr/bin/env python3
"""
Composio CLI Runner

This script provides a convenient way to run the Composio CLI.
"""

import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the Composio CLI
from vot1.integrations.composio.cli import main

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the CLI
    sys.exit(main()) 