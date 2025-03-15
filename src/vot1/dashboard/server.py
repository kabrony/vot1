#!/usr/bin/env python3
"""
VOT1 Dashboard Server

This module implements a web-based dashboard for monitoring and interacting with the VOT1 system.
It provides visualizations for memory, tools to interact with the AI, and system monitoring.
"""

import os
import logging
import argparse
from typing import Dict, Any

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv

from vot1.client import EnhancedClaudeClient
from vot1.memory import MemoryManager
from vot1.dashboard.api import api_bp, init_api

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize VOT1 components
def init_vot1_components(args):
    """
    Initialize VOT1 components based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Tuple of (client, memory_manager)
    """
    # Get API keys from environment
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    perplexity_api_key = os.environ.get('PERPLEXITY_API_KEY')
    
    if not anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables")
    
    # Set up memory manager
    memory_path = args.memory_path or os.environ.get('VOT1_MEMORY_PATH', os.path.join(os.getcwd(), 'memory'))
    logger.info(f"Initializing memory manager with path: {memory_path}")
    memory_manager = MemoryManager(storage_dir=memory_path)
    
    # Create enhanced client
    client = EnhancedClaudeClient(
        api_key=anthropic_api_key,
        model=args.model,
        hybrid_mode=not args.no_hybrid,
        memory_manager=memory_manager
    )
    
    # Add web search capability if Perplexity API key is available
    if perplexity_api_key:
        try:
            client.add_web_search_capability()
            logger.info("Added web search capability to VOT1 client")
        except Exception as e:
            logger.error(f"Failed to add web search capability: {e}")
    
    # Add OWL reasoning capability
    try:
        client.add_reasoning_capability()
        logger.info("Added OWL reasoning capability to VOT1 client")
    except Exception as e:
        logger.error(f"Failed to add OWL reasoning capability: {e}")
    
    return client, memory_manager

# Register API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    """Render the dashboard home page."""
    return render_template('index.html')

@app.route('/status')
def status():
    """Return basic status information."""
    return jsonify({
        "status": "online",
        "version": "0.2.0"
    })

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Start the VOT1 dashboard server')
    parser.add_argument('--host', type=str, default=os.environ.get('VOT1_DASHBOARD_HOST', '127.0.0.1'),
                        help='Host to run the server on')
    parser.add_argument('--port', type=int, default=int(os.environ.get('VOT1_DASHBOARD_PORT', 8000)),
                        help='Port to run the server on')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    parser.add_argument('--memory-path', type=str, default=None,
                        help='Path to store memory data')
    parser.add_argument('--model', type=str, default="claude-3-7-sonnet-20240620",
                        help='Primary Claude model to use')
    parser.add_argument('--no-hybrid', action='store_true',
                        help='Disable hybrid model mode')
    return parser.parse_args()

def main():
    """Main entry point for the dashboard server."""
    args = parse_args()
    
    # Initialize VOT1 components
    client, memory_manager = init_vot1_components(args)
    
    # Initialize API with dependencies
    init_api(socketio, client, memory_manager)
    
    # Start the server
    logger.info(f"Starting VOT1 dashboard on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main() 