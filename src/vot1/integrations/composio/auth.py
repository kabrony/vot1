"""
Composio Authentication Manager for VOT1

This module provides authentication management for Composio API integration,
handling API keys, token refresh, and session management.
"""

import os
import time
import logging
from typing import Dict, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

class ComposioAuthManager:
    """
    Authentication manager for Composio API integration
    
    This class handles API key management, token refresh, and authentication
    session management for Composio API integrations.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the authentication manager
        
        Args:
            api_key: Composio API key (defaults to COMPOSIO_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get('COMPOSIO_API_KEY')
        if not self.api_key:
            logger.warning("No Composio API key provided and COMPOSIO_API_KEY environment variable not set")
        
        self.base_url = os.environ.get('COMPOSIO_API_URL', 'https://api.composio.dev')
        
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        # Session token information
        self._session_token = None
        self._token_expiry = 0
        
    def get_api_key(self) -> Optional[str]:
        """
        Get the current API key
        
        Returns:
            The current API key or None if not set
        """
        return self.api_key
    
    def set_api_key(self, api_key: str) -> None:
        """
        Set a new API key
        
        Args:
            api_key: New Composio API key to use
        """
        self.api_key = api_key
        # Reset session token when API key changes
        self._session_token = None
        self._token_expiry = 0
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests
        
        Returns:
            Dictionary of authentication headers
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add API key if available
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        # Add session token if available
        if self._session_token and time.time() < self._token_expiry:
            headers['X-Session-Token'] = self._session_token
        
        return headers
    
    def set_session_token(self, token: str, expiry_seconds: int = 3600) -> None:
        """
        Set a session token
        
        Args:
            token: Session token
            expiry_seconds: Token expiry in seconds (default: 1 hour)
        """
        self._session_token = token
        self._token_expiry = time.time() + expiry_seconds
    
    def is_authenticated(self) -> bool:
        """
        Check if the manager has valid authentication credentials
        
        Returns:
            True if the manager has a valid API key, False otherwise
        """
        return bool(self.api_key)
    
    def get_base_url(self) -> str:
        """
        Get the base URL for API requests
        
        Returns:
            The base URL for Composio API
        """
        return self.base_url 