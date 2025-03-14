"""
VOT1 Dashboard API Package

This package provides the API functionality for the VOT1 dashboard,
using a modular Blueprint-based approach for better organization and maintainability.
"""

import logging
import time
from flask import Blueprint

# Set up logging
logger = logging.getLogger(__name__)

# Import from endpoint modules
try:
    from .endpoints import api_bp, register_endpoints
except ImportError as e:
    logger.error(f"Error importing API endpoints: {e}")
    
    # Create a fallback API blueprint
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    def register_endpoints(app):
        """Fallback endpoint registration"""
        app.register_blueprint(api_bp)
        logger.warning("Using fallback API endpoints")

def init_api(socketio, client, memory_manager):
    """
    Initialize the API with the required components.
    
    Args:
        socketio: SocketIO instance for real-time communication
        client: Client instance for AI interactions
        memory_manager: MemoryManager instance for memory operations
    
    Returns:
        The API blueprint
    """
    logger.info("Initializing VOT1 Dashboard API")
    
    try:
        # Store references in API module globals
        global _socketio, _client, _memory_manager
        _socketio = socketio
        _client = client
        _memory_manager = memory_manager
        
        # Update global stats
        _update_system_stats()
        
        return api_bp
    
    except Exception as e:
        logger.error(f"Error initializing API: {e}")
        return api_bp

def _update_system_stats():
    """Update system statistics from memory manager and client"""
    pass  # This is now handled in the stats module

# Export public API
__all__ = ['api_bp', 'init_api'] 