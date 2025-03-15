#!/usr/bin/env python3
"""
Composio Integration Example

This script demonstrates how to use the ComposioTools class
to interact with the Composio platform.
"""

import os
import logging
import argparse
from typing import Optional

from composio_tools import ComposioTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("composio_example")

def main(api_key: Optional[str] = None, connection_id: Optional[str] = None):
    """
    Run the Composio integration example.
    
    Args:
        api_key: Composio API key (optional, will use env var if not provided)
        connection_id: Connection ID to use (optional)
    """
    logger.info("Initializing Composio tools...")
    
    # Initialize ComposioTools
    # If api_key is None, it will use the COMPOSIO_API_KEY environment variable
    tools = ComposioTools(api_key=api_key, connection_id=connection_id)
    
    if not tools.api_key:
        logger.error("No Composio API key found. Set COMPOSIO_API_KEY environment variable or provide with --api-key")
        return
    
    try:
        # If connection_id is provided, get that specific connection
        if connection_id:
            logger.info(f"Getting connection with ID: {connection_id}")
            connection = tools.get_connected_account(connection_id)
            print(f"\nConnection: {connection}")
        
        # List all available connections
        logger.info("Listing all available connections...")
        connections = tools.list_connections()
        
        if connections:
            print(f"\nFound {len(connections)} connections:")
            for i, conn in enumerate(connections):
                print(f"{i+1}. {conn}")
        else:
            print("\nNo connections available.")
            
        # Create a new app example
        logger.info("Creating a new app example...")
        app_name = "Example App"
        try:
            app = tools.create_app(app_name)
            print(f"\nCreated app: {app}")
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            
    except Exception as e:
        logger.error(f"Error in Composio example: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Composio Integration Example")
    parser.add_argument("--api-key", type=str, help="Composio API key (overrides environment variable)")
    parser.add_argument("--connection-id", type=str, help="Specific connection ID to use")
    
    args = parser.parse_args()
    
    main(api_key=args.api_key, connection_id=args.connection_id) 