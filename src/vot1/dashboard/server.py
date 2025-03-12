"""
VOT1 Dashboard Server

This module provides a Flask-based web server for the VOT1 dashboard.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import time

from ..memory import MemoryManager
from ..client import EnhancedClaudeClient

# Setup logging
logger = logging.getLogger("vot1.dashboard")

class DashboardServer:
    """Flask server for VOT1 dashboard."""
    
    def __init__(
        self,
        client: Optional[EnhancedClaudeClient] = None,
        memory_manager: Optional[MemoryManager] = None,
        host: str = "127.0.0.1", 
        port: int = 5000,
        static_folder: str = None
    ) -> None:
        """Initialize dashboard server.
        
        Args:
            client: EnhancedClaudeClient instance
            memory_manager: MemoryManager instance
            host: Host to bind the server to
            port: Port to bind the server to
            static_folder: Folder containing static web assets
        """
        self.host = host
        self.port = port
        self.client = client
        self.memory_manager = memory_manager
        
        # If no client or memory_manager provided, create new ones
        if not self.client:
            self.client = EnhancedClaudeClient()
        
        if not self.memory_manager:
            # Use the client's memory_manager if available
            if hasattr(self.client, 'memory'):
                self.memory_manager = self.client.memory
            else:
                self.memory_manager = MemoryManager()
        
        # Find the static folder
        if static_folder is None:
            # Use the default location relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            static_folder = os.path.join(current_dir, "static")
        
        # Initialize Flask app
        self.app = Flask(__name__, static_folder=static_folder)
        CORS(self.app)
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Initialized DashboardServer on {host}:{port}")
    
    def _setup_routes(self) -> None:
        """Set up Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard page."""
            return send_from_directory(self.app.static_folder, 'index.html')
        
        @self.app.route('/<path:path>')
        def static_files(path):
            """Serve static files."""
            return send_from_directory(self.app.static_folder, path)
        
        @self.app.route('/api/status', methods=['GET'])
        def status():
            """Get system status."""
            return jsonify({
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "model": self.client.model,
                "github_enabled": self.client.github_enabled,
                "perplexity_enabled": self.client.perplexity_enabled,
            })
        
        @self.app.route('/api/memory', methods=['GET'])
        def get_memory():
            """Get memory contents."""
            query = request.args.get('query', '')
            limit = int(request.args.get('limit', 10))
            
            if query:
                # Search memory
                results = self.memory_manager.search_all(query, limit)
                return jsonify(results)
            else:
                # Get recent items
                conversation = self.memory_manager.conversation.get_all(limit)
                return jsonify({"conversation": conversation})
        
        @self.app.route('/api/memory/stats', methods=['GET'])
        def memory_stats():
            """Get memory statistics."""
            return jsonify(self.memory_manager.get_stats())
        
        @self.app.route('/api/message', methods=['POST'])
        def send_message():
            """Send a message to Claude."""
            data = request.json
            
            if not data or 'prompt' not in data:
                return jsonify({"error": "Missing prompt"}), 400
            
            prompt = data.get('prompt', '')
            system_prompt = data.get('system_prompt')
            use_memory = data.get('use_memory', True)
            use_perplexity = data.get('use_perplexity', False)
            
            try:
                response = self.client.send_message(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    use_perplexity=use_perplexity,
                    use_memory=use_memory
                )
                
                return jsonify({
                    "success": True,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/knowledge', methods=['POST'])
        def add_knowledge():
            """Add knowledge to semantic memory."""
            data = request.json
            
            if not data or 'content' not in data:
                return jsonify({"error": "Missing content"}), 400
            
            content = data.get('content', '')
            metadata = data.get('metadata', {})
            
            try:
                memory_id = self.client.add_knowledge(content, metadata)
                
                return jsonify({
                    "success": True,
                    "memory_id": memory_id,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error adding knowledge: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
    
    def start(self, debug: bool = False, use_thread: bool = False) -> None:
        """Start the Flask server.
        
        Args:
            debug: Whether to run in debug mode
            use_thread: Whether to run in a separate thread (non-blocking)
        """
        if use_thread:
            thread = threading.Thread(
                target=self.app.run,
                kwargs={"host": self.host, "port": self.port, "debug": debug, "use_reloader": False}
            )
            thread.daemon = True
            thread.start()
            logger.info(f"Dashboard server started in thread on http://{self.host}:{self.port}")
        else:
            logger.info(f"Starting dashboard server on http://{self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=debug)
    
def create_dashboard(
    client: Optional[EnhancedClaudeClient] = None,
    memory_manager: Optional[MemoryManager] = None,
    host: str = "127.0.0.1",
    port: int = 5000,
    static_folder: str = None,
    start: bool = True,
    debug: bool = False,
    use_thread: bool = False
) -> DashboardServer:
    """Create and optionally start a dashboard server.
    
    Args:
        client: EnhancedClaudeClient instance
        memory_manager: MemoryManager instance
        host: Host to bind the server to
        port: Port to bind the server to
        static_folder: Folder containing static web assets
        start: Whether to start the server immediately
        debug: Whether to run in debug mode
        use_thread: Whether to run in a separate thread (non-blocking)
        
    Returns:
        Initialized DashboardServer instance
    """
    server = DashboardServer(
        client=client,
        memory_manager=memory_manager,
        host=host,
        port=port,
        static_folder=static_folder
    )
    
    if start:
        server.start(debug=debug, use_thread=use_thread)
    
    return server

if __name__ == "__main__":
    # Create and start dashboard server when run directly
    server = create_dashboard(debug=True) 