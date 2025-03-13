#!/usr/bin/env python3
"""
OpenAPI Import Script for VOT1

This script imports OpenAPI specifications into Composio.
"""

import os
import sys
import argparse
import logging
from typing import Optional, List

# Add the parent directory to the path so we can import the VOT1 modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vot1.integrations.composio import ComposioClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Import OpenAPI specifications into Composio')
    
    parser.add_argument('--spec', '-s', required=True,
                        help='Path to the OpenAPI specification file')
    
    parser.add_argument('--auth', '-a',
                        help='Path to the authentication configuration file')
    
    parser.add_argument('--name', '-n',
                        help='Custom name for the tool')
    
    parser.add_argument('--description', '-d',
                        help='Custom description for the tool')
    
    parser.add_argument('--tags', '-t', nargs='+',
                        help='List of tags for the tool')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Validate input files
    if not os.path.isfile(args.spec):
        logger.error(f"Specification file not found: {args.spec}")
        sys.exit(1)
    
    if args.auth and not os.path.isfile(args.auth):
        logger.error(f"Authentication file not found: {args.auth}")
        sys.exit(1)
    
    # Initialize Composio client
    try:
        client = ComposioClient()
    except Exception as e:
        logger.error(f"Failed to initialize Composio client: {e}")
        sys.exit(1)
    
    # Check connection
    status = client.check_connection()
    if not status.get('connected', False):
        logger.error(f"Not connected to Composio: {status.get('error', 'Unknown error')}")
        sys.exit(1)
    
    logger.info(f"Connected to Composio (version: {status.get('version', 'unknown')})")
    
    # Import OpenAPI specification
    logger.info(f"Importing OpenAPI specification from {args.spec}...")
    
    result = client.import_openapi_spec(
        spec_file_path=args.spec,
        auth_file_path=args.auth,
        tool_name=args.name,
        description=args.description,
        tags=args.tags
    )
    
    if 'error' in result:
        logger.error(f"Failed to import OpenAPI specification: {result['error']}")
        sys.exit(1)
    
    tool = result.get('tool', {})
    
    logger.info(f"Successfully imported OpenAPI specification!")
    logger.info(f"Tool ID: {tool.get('id', 'unknown')}")
    logger.info(f"Tool Name: {tool.get('name', 'unknown')}")
    logger.info(f"Tool Version: {tool.get('version', 'unknown')}")
    
    if 'actions' in tool:
        logger.info(f"Available Actions:")
        for action in tool['actions']:
            action_name = action.get('name', action) if isinstance(action, dict) else action
            logger.info(f"  - {action_name}")
    
    logger.info("Import completed successfully!")

if __name__ == '__main__':
    main() 