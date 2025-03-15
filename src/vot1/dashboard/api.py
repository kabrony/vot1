"""
VOT1 Dashboard API

This module provides the RESTful API endpoints for the VOT1 dashboard, serving
data for the web interface including conversation history, memory contents,
and system statistics. It handles interactions with the VOT1 system.

Copyright 2025 VillageOfThousands.io
"""

import os
import json
import time
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from flask import Blueprint, request, jsonify, current_app, g
from flask.views import MethodView

# Set up logging
logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global variables to store system state
_last_activity_time = time.time()
_system_stats = {
    "total_conversations": 0,
    "total_semantic_memories": 0,
    "total_tokens_processed": 0,
    "total_api_calls": 0, 
    "total_tool_uses": 0,
    "start_time": time.time()
}

# Global references to system components
_socketio = None
_client = None
_memory_manager = None

def init_api(socketio, client, memory_manager):
    """
    Initialize the API with required dependencies.
    
    Args:
        socketio: The SocketIO instance for real-time communication
        client: The VOT1 client instance
        memory_manager: The memory manager instance
    """
    global _socketio, _client, _memory_manager
    _socketio = socketio
    _client = client
    _memory_manager = memory_manager
    
    logger.info("API initialized with dependencies")
    
    # Register API endpoints
    api_bp.add_url_rule('/memory', view_func=MemoryAPI.as_view('memory_api'))
    api_bp.add_url_rule('/visualization', view_func=VisualizationDataAPI.as_view('visualization_api'))
    api_bp.add_url_rule('/stats', view_func=StatsAPI.as_view('stats_api'))
    api_bp.add_url_rule('/search', view_func=WebSearchAPI.as_view('search_api'))
    api_bp.add_url_rule('/reason', view_func=OWLReasoningAPI.as_view('reasoning_api'))
    
    # Initialize system stats
    _update_system_stats()
    
    return api_bp

def _update_system_stats():
    """Update system statistics from memory manager and client"""
    global _system_stats
    
    if _memory_manager:
        try:
            # Get memory counts
            _system_stats["total_semantic_memories"] = _memory_manager.get_memory_count("semantic")
            _system_stats["total_conversations"] = _memory_manager.get_memory_count("conversation")
        except Exception as e:
            logger.error(f"Error updating memory stats: {e}")
    
    if _client:
        try:
            # Get client stats if available
            if hasattr(_client, 'get_stats'):
                client_stats = _client.get_stats()
                _system_stats.update(client_stats)
        except Exception as e:
            logger.error(f"Error updating client stats: {e}")

class MemoryAPI(MethodView):
    """API endpoint for memory operations"""
    
    def get(self):
        """Get memories with optional filtering"""
        try:
            memory_type = request.args.get('type', 'all')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            query = request.args.get('query', '')
            
            memory_manager = getattr(g, 'memory_manager', None)
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            if memory_type == 'all':
                results = memory_manager.get_all_memories(limit=limit, offset=offset, query=query)
            elif memory_type == 'semantic':
                results = memory_manager.get_semantic_memories(limit=limit, offset=offset, query=query)
            elif memory_type == 'conversation':
                results = memory_manager.get_conversation_memories(limit=limit, offset=offset, query=query)
            else:
                return jsonify({"error": f"Invalid memory type: {memory_type}"}), 400
            
            return jsonify(results)
        
        except Exception as e:
            logger.exception(f"Error getting memories: {e}")
            return jsonify({"error": str(e)}), 500
    
    def post(self):
        """Create a new memory"""
        try:
            data = request.json
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            memory_type = data.get('type')
            content = data.get('content')
            
            if not memory_type or not content:
                return jsonify({"error": "Type and content are required"}), 400
            
            memory_manager = getattr(g, 'memory_manager', None)
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            metadata = data.get('metadata', {})
            
            if memory_type == 'semantic':
                memory_id = memory_manager.add_semantic_memory(content, metadata)
                _system_stats['total_semantic_memories'] += 1
            elif memory_type == 'conversation':
                memory_id = memory_manager.add_conversation_memory(content, metadata)
                _system_stats['total_conversations'] += 1
            else:
                return jsonify({"error": f"Invalid memory type: {memory_type}"}), 400
            
            socketio = current_app.extensions.get('socketio')
            if socketio:
                socketio.emit('memory_updated', {
                    'id': memory_id,
                    'type': memory_type,
                    'timestamp': time.time()
                })
            
            return jsonify({"id": memory_id, "status": "created"}), 201
        
        except Exception as e:
            logger.exception(f"Error creating memory: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete(self):
        """Clear memories"""
        try:
            memory_type = request.args.get('type', 'all')
            
            memory_manager = getattr(g, 'memory_manager', None)
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            if memory_type == 'all':
                memory_manager.clear_all_memories()
            elif memory_type == 'semantic':
                memory_manager.clear_semantic_memories()
            elif memory_type == 'conversation':
                memory_manager.clear_conversation_memories()
            else:
                return jsonify({"error": f"Invalid memory type: {memory_type}"}), 400
            
            socketio = current_app.extensions.get('socketio')
            if socketio:
                socketio.emit('memory_cleared', {
                    'type': memory_type,
                    'timestamp': time.time()
                })
            
            return jsonify({"status": f"{memory_type} memories cleared"}), 200
        
        except Exception as e:
            logger.exception(f"Error clearing memories: {e}")
            return jsonify({"error": str(e)}), 500


class VisualizationDataAPI(MethodView):
    """API endpoint for visualization data"""
    
    def get(self):
        """Get data for the THREE.js visualization"""
        try:
            memory_manager = getattr(g, 'memory_manager', None)
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            # Get raw memories
            semantic_memories = memory_manager.get_semantic_memories(limit=1000)
            conversation_memories = memory_manager.get_conversation_memories(limit=1000)
            
            # Format for visualization
            viz_data = {
                "semantic": [],
                "conversation": [],
                "swarm": [],  # Will be populated if available
                "feedback": [] # Will be populated if available
            }
            
            # Process semantic memories
            for memory in semantic_memories:
                viz_data["semantic"].append({
                    "id": memory.get("id", str(uuid.uuid4())),
                    "content": memory.get("content", ""),
                    "timestamp": memory.get("timestamp", time.time()),
                    "metadata": memory.get("metadata", {})
                })
            
            # Process conversation memories
            for memory in conversation_memories:
                viz_data["conversation"].append({
                    "id": memory.get("id", str(uuid.uuid4())),
                    "content": memory.get("content", ""),
                    "timestamp": memory.get("timestamp", time.time()),
                    "metadata": memory.get("metadata", {})
                })
            
            # Get swarm agent memories if available
            swarm_agent_manager = getattr(g, 'swarm_agent_manager', None)
            if swarm_agent_manager:
                swarm_memories = swarm_agent_manager.get_agent_memories(limit=100)
                for memory in swarm_memories:
                    viz_data["swarm"].append({
                        "id": memory.get("id", str(uuid.uuid4())),
                        "content": memory.get("content", ""),
                        "timestamp": memory.get("timestamp", time.time()),
                        "metadata": memory.get("metadata", {})
                    })
            
            # Get feedback memories if available
            feedback_manager = getattr(g, 'feedback_manager', None)
            if feedback_manager:
                feedback_memories = feedback_manager.get_feedback(limit=100)
                for memory in feedback_memories:
                    viz_data["feedback"].append({
                        "id": memory.get("id", str(uuid.uuid4())),
                        "content": memory.get("content", ""),
                        "timestamp": memory.get("timestamp", time.time()),
                        "metadata": memory.get("metadata", {})
                    })
            
            return jsonify(viz_data)
        
        except Exception as e:
            logger.exception(f"Error getting visualization data: {e}")
            return jsonify({"error": str(e)}), 500


class StatsAPI(MethodView):
    """API endpoint for system statistics"""
    
    def get(self):
        """Get system statistics"""
        try:
            # Calculate uptime
            uptime_seconds = time.time() - _system_stats["start_time"]
            uptime = {
                "days": int(uptime_seconds // (24 * 3600)),
                "hours": int((uptime_seconds % (24 * 3600)) // 3600),
                "minutes": int((uptime_seconds % 3600) // 60),
                "seconds": int(uptime_seconds % 60)
            }
            
            # Get memory manager stats
            memory_manager = getattr(g, 'memory_manager', None)
            memory_stats = {}
            
            if memory_manager:
                memory_stats = {
                    "total_memories": memory_manager.count_all_memories(),
                    "semantic_memories": memory_manager.count_semantic_memories(),
                    "conversation_memories": memory_manager.count_conversation_memories()
                }
            
            # Get Claude client stats
            claude_client = getattr(g, 'claude_client', None)
            claude_stats = {}
            
            if claude_client and hasattr(claude_client, 'get_stats'):
                claude_stats = claude_client.get_stats()
            
            # Combine stats
            stats = {
                **_system_stats,
                "uptime": uptime,
                "uptime_seconds": uptime_seconds,
                "memory": memory_stats,
                "claude": claude_stats,
                "last_activity": _last_activity_time,
                "idle_time": time.time() - _last_activity_time
            }
            
            return jsonify(stats)
        
        except Exception as e:
            logger.exception(f"Error getting system statistics: {e}")
            return jsonify({"error": str(e)}), 500


class WebSearchAPI(MethodView):
    """API endpoint for web search"""
    
    def post(self):
        """Perform a web search"""
        try:
            data = request.json
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            query = data.get('query')
            
            if not query:
                return jsonify({"error": "Search query is required"}), 400
            
            web_search = getattr(g, 'web_search', None)
            if not web_search:
                return jsonify({"error": "Web search client not available"}), 503
            
            results = web_search.search(query)
            
            global _last_activity_time
            _last_activity_time = time.time()
            
            return jsonify(results)
        
        except Exception as e:
            logger.exception(f"Error performing web search: {e}")
            return jsonify({"error": str(e)}), 500


class OWLReasoningAPI(MethodView):
    """API endpoint for OWL reasoning"""
    
    def post(self):
        """Perform OWL reasoning"""
        try:
            data = request.json
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            query = data.get('query')
            context = data.get('context', [])
            
            if not query:
                return jsonify({"error": "Reasoning query is required"}), 400
            
            owl_reasoning = getattr(g, 'owl_reasoning', None)
            if not owl_reasoning:
                return jsonify({"error": "OWL reasoning client not available"}), 503
            
            result = owl_reasoning.reason(query, context)
            
            global _last_activity_time
            _last_activity_time = time.time()
            
            return jsonify(result)
        
        except Exception as e:
            logger.exception(f"Error performing OWL reasoning: {e}")
            return jsonify({"error": str(e)}), 500


# Register API endpoints
api_bp.add_url_rule('/memories', view_func=MemoryAPI.as_view('memories'))
api_bp.add_url_rule('/visualization-data', view_func=VisualizationDataAPI.as_view('visualization_data'))
api_bp.add_url_rule('/stats', view_func=StatsAPI.as_view('stats'))
api_bp.add_url_rule('/web-search', view_func=WebSearchAPI.as_view('web_search'))
api_bp.add_url_rule('/owl-reasoning', view_func=OWLReasoningAPI.as_view('owl_reasoning'))

# Simple API routes
@api_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint to check API availability"""
    return jsonify({"status": "ok", "timestamp": time.time()})

@api_bp.route('/version', methods=['GET'])
def version():
    """Get VOT1 version information"""
    try:
        from vot1 import __version__
        
        return jsonify({
            "version": __version__,
            "api_version": "1.0",
            "build_date": getattr(current_app, 'build_date', 'unknown'),
            "python_version": os.environ.get("PYTHON_VERSION", "unknown")
        })
    except ImportError:
        return jsonify({
            "version": "unknown",
            "api_version": "1.0"
        })

@api_bp.route('/update-activity', methods=['POST'])
def update_activity():
    """Update the last activity timestamp"""
    global _last_activity_time
    _last_activity_time = time.time()
    return jsonify({"status": "ok", "timestamp": _last_activity_time})

# Error handlers
@api_bp.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found"}), 404

@api_bp.errorhandler(500)
def handle_500(e):
    return jsonify({"error": "Internal server error"}), 500 