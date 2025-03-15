#!/usr/bin/env python3
"""
VOT1 Unified Dashboard Server
Handles HTTP and WebSocket connections for the dashboard interface
"""

import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import visualization module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visualization.file_structure import FileStructureVisualizer

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('VOT1_SECRET_KEY', 'vot1-dashboard-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*")

# Current state
components = {}
connected_clients = {}
active_nodes = {}
hybrid_thinking_enabled = True

class DashboardServer:
    """Server for the VOT1 Dashboard application"""
    
    def __init__(self):
        self.visualizer = FileStructureVisualizer()
        self.mcp_config = self._load_mcp_config()
        self.memory_config = self._load_memory_config()
        
    def _load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration"""
        try:
            config_path = Path(__file__).parent / 'config' / 'mcp_config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                return {
                    "tools": ["github", "perplexity", "figma", "firecrawl"],
                    "nodes": [
                        {"id": "node-1", "name": "API Node", "status": "stopped", "type": "api"},
                        {"id": "node-2", "name": "Memory Node", "status": "stopped", "type": "memory"},
                        {"id": "node-3", "name": "Processing Node", "status": "stopped", "type": "processing"},
                        {"id": "node-4", "name": "Visualization Node", "status": "stopped", "type": "visualization"}
                    ]
                }
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return {"tools": [], "nodes": []}
    
    def _load_memory_config(self) -> Dict[str, Any]:
        """Load memory system configuration"""
        try:
            config_path = Path(__file__).parent / 'config' / 'memory_config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                return {
                    "max_memory_items": 1000,
                    "memory_types": ["fact", "concept", "code", "conversation", "reflection"],
                    "default_memory_type": "fact"
                }
        except Exception as e:
            logger.error(f"Error loading memory config: {e}")
            return {"max_memory_items": 1000, "memory_types": []}
            
    def get_file_structure(self, root_dir: Optional[str] = None, depth: int = 3) -> Dict[str, Any]:
        """Get file structure data"""
        if not root_dir:
            root_dir = os.path.dirname(os.path.abspath(__file__))
        
        try:
            return self.visualizer.generate_structure(root_dir, max_depth=depth)
        except Exception as e:
            logger.error(f"Error generating file structure: {e}")
            return {"name": "error", "children": []}
    
    def get_memory_graph(self) -> Dict[str, Any]:
        """Get memory graph data"""
        # This would connect to the actual memory system in a real implementation
        # For now, we'll generate demo data
        nodes = []
        links = []
        
        # Generate some demo nodes
        memory_types = self.memory_config.get("memory_types", [])
        for i in range(20):
            memory_type = memory_types[i % len(memory_types)] if memory_types else "fact"
            nodes.append({
                "id": f"memory-{i}",
                "label": f"Memory {i}",
                "type": memory_type,
                "created": "2025-02-19T10:00:00Z",
                "importance": (i % 5) + 1
            })
        
        # Generate some demo links
        for i in range(15):
            source = i % len(nodes)
            target = (i + 3) % len(nodes)
            if source != target:
                links.append({
                    "source": nodes[source]["id"],
                    "target": nodes[target]["id"],
                    "type": "related" if i % 2 == 0 else "references"
                })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def get_active_mcp_nodes(self) -> List[Dict[str, Any]]:
        """Get active MCP nodes"""
        return [node for node in self.mcp_config.get("nodes", []) if node.get("status") == "running"]
    
    def process_chat_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a chat message and generate a response"""
        hybrid_thinking = context.get("hybridThinking", hybrid_thinking_enabled)
        panel = context.get("panel", "dashboard")
        
        # In a real implementation, this would call the AI backend
        # For now, we'll generate a demo response
        thinking = None
        if hybrid_thinking:
            thinking = f"Processing message: '{message}'\n\nStep 1: Analyze the query\n- User is asking about {panel}\n- Need to provide relevant information\n\nStep 2: Gather context\n- Current panel: {panel}\n- Looking at related information\n\nStep 3: Generate response\n- Providing helpful information about {panel}"
        
        response = f"I understand you're asking about {panel}. This is a demo response. In a real implementation, this would call the Claude 3.7 Sonnet API to generate a helpful response."
        
        return {
            "message": response,
            "thinking": thinking
        }

# Initialize server
server = DashboardServer()

# Routes
@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/components')
def get_components():
    """Get all dashboard components"""
    return jsonify({
        "visualization": {
            "id": "visualization",
            "name": "File Structure Visualization",
            "type": "visualization",
            "status": "active"
        },
        "mcp": {
            "id": "mcp",
            "name": "Modular Component Platform",
            "type": "mcp",
            "status": "active",
            "tools": server.mcp_config.get("tools", []),
            "nodes": server.mcp_config.get("nodes", [])
        },
        "memory": {
            "id": "memory",
            "name": "TRILOGY BRAIN Memory System",
            "type": "memory",
            "status": "active",
            "config": server.memory_config
        },
        "assistant": {
            "id": "assistant",
            "name": "AI Assistant",
            "type": "assistant",
            "status": "active",
            "model": "Claude 3.7 Sonnet",
            "hybridThinking": hybrid_thinking_enabled
        }
    })

@app.route('/api/file-structure')
def get_file_structure():
    """Get file structure data"""
    root_dir = request.args.get('root', None)
    depth = int(request.args.get('depth', 3))
    return jsonify(server.get_file_structure(root_dir, depth))

@app.route('/api/memory-graph')
def get_memory_graph():
    """Get memory graph data"""
    return jsonify(server.get_memory_graph())

@app.route('/api/mcp/nodes')
def get_mcp_nodes():
    """Get MCP nodes"""
    return jsonify(server.mcp_config.get("nodes", []))

@app.route('/api/mcp/tools')
def get_mcp_tools():
    """Get MCP tools"""
    return jsonify(server.mcp_config.get("tools", []))

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update settings"""
    global hybrid_thinking_enabled
    
    if request.method == 'POST':
        settings = request.json
        if 'hybridThinking' in settings:
            hybrid_thinking_enabled = settings['hybridThinking']
        return jsonify({"success": True})
    else:
        return jsonify({
            "hybridThinking": hybrid_thinking_enabled,
            "theme": "cyberpunk",
            "defaultPanel": "dashboard"
        })

# Socket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        "connected_at": socketio.server.manager.handlers,
        "page": "dashboard"
    }
    logger.info(f"Client connected: {client_id}")
    emit('connection_status', {'status': 'connected', 'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    logger.info(f"Client disconnected: {client_id}")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle chat message"""
    message = data.get('message', '')
    context = data.get('context', {})
    
    logger.info(f"Received chat message: {message}")
    
    # Process the message
    response = server.process_chat_message(message, context)
    
    # If hybrid thinking is enabled, first emit the thinking update
    if 'thinking' in response and response['thinking']:
        emit('thinking_update', {'thinking': response['thinking']})
    
    # Then emit the chat response
    emit('chat_response', {'message': response.get('message', '')})

@socketio.on('start_node')
def handle_start_node(data):
    """Handle node start request"""
    node_id = data.get('node_id')
    if not node_id:
        emit('node_status', {'success': False, 'message': 'Missing node ID'})
        return
    
    # Update node status in configuration
    for node in server.mcp_config.get("nodes", []):
        if node["id"] == node_id:
            node["status"] = "running"
            break
    
    emit('node_status', {
        'success': True,
        'node_id': node_id,
        'status': 'running'
    })
    socketio.emit('mcp_update', {'nodes': server.mcp_config.get("nodes", [])})

@socketio.on('stop_node')
def handle_stop_node(data):
    """Handle node stop request"""
    node_id = data.get('node_id')
    if not node_id:
        emit('node_status', {'success': False, 'message': 'Missing node ID'})
        return
    
    # Update node status in configuration
    for node in server.mcp_config.get("nodes", []):
        if node["id"] == node_id:
            node["status"] = "stopped"
            break
    
    emit('node_status', {
        'success': True,
        'node_id': node_id,
        'status': 'stopped'
    })
    socketio.emit('mcp_update', {'nodes': server.mcp_config.get("nodes", [])})

@socketio.on('connect_tool')
def handle_connect_tool(data):
    """Handle tool connection request"""
    tool = data.get('tool')
    params = data.get('params', {})
    
    if not tool:
        emit('tool_connection', {'success': False, 'message': 'Missing tool name'})
        return
    
    # In a real implementation, this would connect to the actual tool
    # For now, we'll simulate a successful connection
    emit('tool_connection', {
        'success': True,
        'tool': tool,
        'connection_id': f"{tool}-connection-{hash(str(params)) % 10000}",
        'status': 'connected'
    })

def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the server"""
    logger.info(f"Starting VOT1 Dashboard server on http://{host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='VOT1 Dashboard Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    # Run server
    run_server(args.host, args.port, args.debug) 