"""
VOT1 Dashboard API Endpoints

This package contains modular API endpoints for the VOT1 dashboard,
implementing the Blueprint pattern for better organization and maintainability.
Each module focuses on a specific domain of functionality.
"""

import logging
from flask import Blueprint

logger = logging.getLogger(__name__)

# Main API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import and register all endpoint modules
def register_endpoints(app):
    """
    Register all endpoint Blueprints with the main API blueprint.
    
    Args:
        app: Flask application instance
    """
    try:
        # Import endpoint modules
        from .memory import memory_bp
        from .visualization import visualization_bp
        from .chat import chat_bp
        from .stats import stats_bp
        from .wallet import wallet_bp  # Import our new wallet blueprint
        
        # Register endpoint Blueprints with the main API blueprint
        api_bp.register_blueprint(memory_bp)
        api_bp.register_blueprint(visualization_bp)
        api_bp.register_blueprint(chat_bp)
        api_bp.register_blueprint(stats_bp)
        api_bp.register_blueprint(wallet_bp)  # Register our new wallet blueprint
        
        # Optional: try to import and register additional modules if available
        try:
            from .perplexity import perplexity_bp
            api_bp.register_blueprint(perplexity_bp)
        except ImportError:
            logger.info("Perplexity API module not available")
        
        try:
            from .web_search import web_search_bp
            api_bp.register_blueprint(web_search_bp)
        except ImportError:
            logger.info("Web search API module not available")
            
        try:
            from .composio import composio_bp
            api_bp.register_blueprint(composio_bp)
        except ImportError:
            logger.info("Composio API module not available")
        
        # Register the API blueprint with the Flask app
        app.register_blueprint(api_bp)
        logger.info("All API endpoints registered successfully")
        
    except Exception as e:
        logger.error(f"Error registering API endpoints: {e}")
        raise

# Export all modules
__all__ = ['api_bp', 'register_endpoints'] 