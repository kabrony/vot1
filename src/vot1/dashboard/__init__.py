"""
VOT1 Dashboard Package
=====================

This package provides a web-based dashboard for the VOT1 system,
allowing users to interact with the system, monitor memory,
and perform web searches using Perplexity's sonar-reasoning-pro model.
"""

import os
import logging
from typing import Optional, Union
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO

# Import routes and API handlers conditionally to handle potential import errors
try:
    from .routes import init_routes
except ImportError as e:
    logging.warning(f"Could not import routes: {e}")
    def init_routes(app):
        logging.error("Routes initialization not available")

try:
    from .api.mcp_handler import init_mcp_api  # Import MCP API initializer
except ImportError as e:
    logging.warning(f"Could not import MCP API handler: {e}")
    def init_mcp_api(app):
        logging.error("MCP API initialization not available")

try:
    from .api.dev_assistant_api import init_dev_assistant_api  # Import Development Assistant API initializer
except ImportError as e:
    logging.warning(f"Could not import Development Assistant API initializer: {e}")
    def init_dev_assistant_api(app):
        logging.error("Development Assistant API initialization not available")

# Import the server implementation
try:
    from .server import DashboardServer, create_dashboard
except ImportError as e:
    logging.warning(f"Dashboard server not fully available: {e}")
    
    # Provide minimal placeholder implementations
    class DashboardServer:
        def __init__(self, *args, **kwargs):
            logging.error("DashboardServer not available, missing dependencies")
            
        def start(self, *args, **kwargs):
            logging.error("DashboardServer not available, missing dependencies")
    
    def create_dashboard(*args, **kwargs):
        logging.error("Dashboard creation failed, missing dependencies")
        return None

# Package version
__version__ = "0.2.0"

# Determine the path to the static folder
DASHBOARD_PATH = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(DASHBOARD_PATH, "static")

def ensure_static_files():
    """
    Ensure all required static files exist.
    Returns True if all files are present, False otherwise.
    """
    required_files = [
        "index.html",
        "css/style.css",
        "js/api.js",
        "js/app.js",
        "js/init.js",
        "js/memory-chart.js",
        "js/three-visualization.js"
    ]
    
    for file in required_files:
        if not os.path.exists(os.path.join(STATIC_FOLDER, file)):
            logging.warning(f"Missing dashboard file: {file}")
            return False
    
    return True

# Ensure dashboard files are available
if not os.path.exists(STATIC_FOLDER):
    logging.warning(f"Dashboard static folder not found at {STATIC_FOLDER}")
else:
    if not ensure_static_files():
        logging.warning("Dashboard is missing some required files")
    else:
        logging.info("Dashboard files verified successfully")

# Export the public interface
__all__ = ["create_dashboard", "DashboardServer"]

# Import API and routes
try:
    from .api import api_bp, init_api
except ImportError as e:
    logging.warning(f"Could not import API blueprint: {e}")
    api_bp = None
    def init_api(*args, **kwargs):
        logging.error("API initialization not available")

try:
    from .mcp_hybrid_api import mcp_hybrid_bp
except ImportError as e:
    logging.warning(f"Could not import MCP hybrid blueprint: {e}")
    mcp_hybrid_bp = None

try:
    from .github_ecosystem_api import github_ecosystem_bp
except ImportError as e:
    logging.warning(f"Could not import GitHub ecosystem blueprint: {e}")
    github_ecosystem_bp = None

try:
    from ..memory import MemoryManager
except ImportError as e:
    logging.warning(f"Could not import MemoryManager: {e}")
    class MemoryManager:
        def __init__(self, *args, **kwargs):
            self.storage_dir = kwargs.get('memory_path', 'memory')
            logging.error("MemoryManager not available, using placeholder")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(client=None, memory_path=None, no_memory=False, mcp_hybrid_options=None, dev_assistant_options=None):
    """
    Create and configure the Flask application for the VOT1 dashboard.
    
    Args:
        client: An instance of EnhancedClaudeClient for AI interactions
        memory_path: Path to the memory storage directory
        no_memory: Whether to disable memory management
        mcp_hybrid_options: Configuration options for MCP hybrid automation
        dev_assistant_options: Configuration options for Development Assistant
    
    Returns:
        A Flask application instance
    """
    app = Flask(__name__, 
                static_folder='static', 
                template_folder='templates')
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    app.config['JSON_SORT_KEYS'] = False
    app.config['MCP_HYBRID_OPTIONS'] = mcp_hybrid_options or {
        "enabled": True,  # Enable MCP by default
        "primary_model": "claude-3-7-sonnet-20240620",
        "secondary_model": "claude-3-5-sonnet-20240620",
        "use_extended_thinking": True,
        "max_thinking_tokens": 60000,  # Increased for deep research
        "enable_streaming": True,
        "perplexity_integration": True,  # Enable Perplexity integration
        "firecrawl_integration": True   # Enable Firecrawl integration
    }
    
    # Configure Development Assistant options
    app.config['DEV_ASSISTANT_OPTIONS'] = dev_assistant_options or {
        "enabled": True,  # Enable Development Assistant by default
        "project_root": os.getcwd(),
        "memory_path": memory_path or os.path.join(os.getcwd(), 'memory'),
        "max_thinking_tokens": 60000,
        "perplexity_research": True
    }
    
    # Set the project root and memory path for the Development Assistant
    app.config['PROJECT_ROOT'] = app.config['DEV_ASSISTANT_OPTIONS']['project_root']
    app.config['MEMORY_PATH'] = app.config['DEV_ASSISTANT_OPTIONS']['memory_path']
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize memory manager if enabled
    memory_manager = None
    if not no_memory:
        try:
            # Ensure a valid memory path
            if memory_path is None:
                memory_path = os.environ.get('VOT1_MEMORY_PATH', os.path.join(os.getcwd(), 'memory'))
                logger.info(f"Using default memory path: {memory_path}")
            
            # Create memory directory if it doesn't exist
            os.makedirs(memory_path, exist_ok=True)
            
            memory_manager = MemoryManager(memory_path=memory_path)
            logger.info(f"Memory manager initialized at {memory_manager.storage_dir}")
        except Exception as e:
            logger.warning(f"Failed to initialize memory manager: {e}")
    
    # Store memory manager in app config for access by views
    app.config['memory_manager'] = memory_manager
    
    # Initialize API with components - using new modular API system
    with app.app_context():
        try:
            # Initialize the main API with its components
            main_api = init_api(socketio, client, memory_manager)
            
            # Register the API blueprint directly (endpoint registration is handled internally)
            if api_bp:
                # Use the new modular API system
                try:
                    from .api.endpoints import register_endpoints
                    register_endpoints(app)
                    logger.info("Registered API endpoints using modular system")
                except ImportError:
                    # Fallback to direct blueprint registration
                    app.register_blueprint(api_bp)
                    logger.info("Registered API blueprint directly")
            
            # Set up research and development assistant
            perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
            
            dev_assistant_options = {
                "project_root": os.path.abspath(os.getcwd()),
                "perplexity_api_key": perplexity_api_key,
                "redis_url": os.environ.get('REDIS_URL'),
                "max_thinking_tokens": 20000,  # Smart token limit for development assistant
                "smart_token_management": True  # Enable intelligent token allocation
            }
            
            app.config['DEV_ASSISTANT'] = DevelopmentAssistant(**dev_assistant_options)
            logger.info("Development Assistant initialized")
            
            # Set up hybrid thinking system
            hybrid_thinking_options = {
                "perplexity_api_key": perplexity_api_key,
                "redis_url": os.environ.get('REDIS_URL'),
                "max_thinking_tokens": 20000,  # Smart token limit for hybrid thinking
                "max_research_tokens": 8000,
                "smart_token_management": True  # Enable intelligent token allocation
            }
            
            app.config['HYBRID_THINKING'] = HybridThinkingSystem(**hybrid_thinking_options)
            logger.info("Hybrid Thinking System initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize API: {e}")
    
    # Register MCP hybrid blueprint if available
    if mcp_hybrid_bp:
        app.register_blueprint(mcp_hybrid_bp)
        logger.info("Registered MCP hybrid blueprint")
    
    # Register GitHub ecosystem analyzer blueprint if available
    if github_ecosystem_bp:
        app.register_blueprint(github_ecosystem_bp)
        logger.info("Registered GitHub ecosystem blueprint")
    
    # Initialize UI routes
    try:
        init_routes(app)
        logger.info("Initialized UI routes")
    except Exception as e:
        logger.warning(f"Failed to initialize routes: {e}")
    
    # Initialize MCP API
    try:
        init_mcp_api(app)
        logger.info("Initialized MCP API")
    except Exception as e:
        logger.warning(f"Failed to initialize MCP API: {e}")
    
    # Initialize Development Assistant API if enabled
    if app.config['DEV_ASSISTANT_OPTIONS']['enabled']:
        try:
            init_dev_assistant_api(app)
            logger.info("Development Assistant API initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Development Assistant API: {e}")
    
    logger.info("VOT1 Dashboard initialized successfully with MCP and Development Assistant integration")
    
    return app 