#!/usr/bin/env python3
"""
Composio Tools Integration

This module provides integration with the Composio platform,
allowing access to various connected tools and services.
"""

import os
import logging
from typing import Optional, Dict, Any, List

# Import Composio components
from composio import ComposioToolSet, App

# Configure logging
logger = logging.getLogger("composio_tools")

class ComposioTools:
    """
    Wrapper for Composio integration providing simplified access
    to connected accounts and tools.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        connection_id: Optional[str] = None,
        load_from_env: bool = True
    ):
        """
        Initialize the Composio tools integration.
        
        Args:
            api_key: Composio API key (optional if load_from_env is True)
            connection_id: Default connection ID to use
            load_from_env: Whether to load API key from environment variables
        """
        self.api_key = api_key
        self.connection_id = connection_id
        
        # Load from environment if requested
        if load_from_env:
            self._load_from_env()
        
        # Initialize toolset
        if not self.api_key:
            logger.warning("No Composio API key provided. Toolset will not be initialized.")
            self.toolset = None
        else:
            try:
                self.toolset = ComposioToolSet(api_key=self.api_key)
                logger.info("Composio ToolSet initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Composio ToolSet: {e}")
                self.toolset = None
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        if not self.api_key:
            self.api_key = os.environ.get("COMPOSIO_API_KEY")
        
        if not self.connection_id:
            self.connection_id = os.environ.get("COMPOSIO_CONNECTION_ID")
    
    def get_connected_account(self, connection_id: Optional[str] = None) -> Any:
        """
        Get a connected account by ID.
        
        Args:
            connection_id: The connection ID (defaults to self.connection_id if not provided)
            
        Returns:
            The connected account object
            
        Raises:
            ValueError: If no connection ID is provided and no default is set
            RuntimeError: If the toolset is not initialized
        """
        if not self.toolset:
            raise RuntimeError("Composio ToolSet not initialized. Check API key.")
        
        # Use provided connection ID or default
        connection_id = connection_id or self.connection_id
        
        if not connection_id:
            raise ValueError("No connection ID provided and no default set.")
        
        try:
            connection = self.toolset.get_connected_account(connection_id)
            logger.info(f"Successfully retrieved connection: {connection_id}")
            return connection
        except Exception as e:
            logger.error(f"Error retrieving connection {connection_id}: {e}")
            raise
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """
        List all available connections.
        
        Returns:
            List of connection information dictionaries
            
        Raises:
            RuntimeError: If the toolset is not initialized
        """
        if not self.toolset:
            raise RuntimeError("Composio ToolSet not initialized. Check API key.")
        
        try:
            connections = self.toolset.list_connections()
            return connections
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
            return []
    
    def create_app(self, name: str) -> App:
        """
        Create a new app with the given name.
        
        Args:
            name: Name of the app to create
            
        Returns:
            The created App object
            
        Raises:
            RuntimeError: If the toolset is not initialized
        """
        if not self.toolset:
            raise RuntimeError("Composio ToolSet not initialized. Check API key.")
        
        try:
            app = self.toolset.create_app(name)
            logger.info(f"Created app: {name}")
            return app
        except Exception as e:
            logger.error(f"Error creating app {name}: {e}")
            raise

# Example usage
if __name__ == "__main__":
    # Load API key from environment or provide directly
    tools = ComposioTools()
    
    try:
        # Get a specific connection
        connection = tools.get_connected_account("8de7390e-4673-4feb-8ab4-7787e3bfbc12")
        print(connection)
        
        # List all connections
        connections = tools.list_connections()
        print(f"Found {len(connections)} connections")
        
    except Exception as e:
        print(f"Error: {e}") 