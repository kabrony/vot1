"""
Composio Integration for VOT1

This module provides integration with Composio's API.
"""

from .client import ComposioClient
from .auth import ComposioAuthManager

# Define custom exceptions
class ComposioAPIError(Exception):
    """Base exception for Composio API errors"""
    pass

class ComposioRateLimitError(ComposioAPIError):
    """Exception raised when rate limits are exceeded"""
    pass

class ComposioAuthError(ComposioAPIError):
    """Exception raised when authentication fails"""
    pass

# Placeholders for other classes referenced in imports
class ComposioConnector:
    """Connector for Composio API"""
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

class ComposioToolRegistry:
    """Registry for Composio tools"""
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager

__all__ = [
    'ComposioClient', 
    'ComposioAuthManager',
    'ComposioConnector',
    'ComposioToolRegistry',
    'ComposioAPIError',
    'ComposioRateLimitError',
    'ComposioAuthError'
] 