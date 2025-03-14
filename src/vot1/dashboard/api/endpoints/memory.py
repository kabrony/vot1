"""
Memory API Endpoints

This module provides API endpoints for memory operations including
retrieving, storing, and managing semantic and conversation memories.
"""

import time
import logging
from flask import Blueprint, request, jsonify, current_app, g
from flask.views import MethodView

# Set up logging
logger = logging.getLogger(__name__)

# Create Memory Blueprint
memory_bp = Blueprint('memory', __name__, url_prefix='/memory')

class MemoryAPI(MethodView):
    """API endpoint for memory operations"""
    
    def get(self):
        """Get memories with optional filtering"""
        try:
            memory_type = request.args.get('type', 'all')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            query = request.args.get('query', '')
            
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
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
            
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            metadata = data.get('metadata', {})
            
            if memory_type == 'semantic':
                memory_id = memory_manager.add_semantic_memory(content, metadata)
            elif memory_type == 'conversation':
                memory_id = memory_manager.add_conversation_memory(content, metadata)
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
            
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
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
            
            return jsonify({"status": "cleared", "type": memory_type}), 200
        
        except Exception as e:
            logger.exception(f"Error clearing memories: {e}")
            return jsonify({"error": str(e)}), 500

class MemoryDetailAPI(MethodView):
    """API endpoint for operations on specific memories"""
    
    def get(self, memory_id):
        """Get a specific memory by ID"""
        try:
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            memory = memory_manager.get_memory_by_id(memory_id)
            
            if not memory:
                return jsonify({"error": f"Memory with ID {memory_id} not found"}), 404
            
            return jsonify(memory)
        
        except Exception as e:
            logger.exception(f"Error getting memory {memory_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def put(self, memory_id):
        """Update a specific memory by ID"""
        try:
            data = request.json
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            content = data.get('content')
            metadata = data.get('metadata')
            
            result = memory_manager.update_memory(memory_id, content, metadata)
            
            if not result:
                return jsonify({"error": f"Memory with ID {memory_id} not found"}), 404
            
            return jsonify({"status": "updated", "id": memory_id}), 200
        
        except Exception as e:
            logger.exception(f"Error updating memory {memory_id}: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete(self, memory_id):
        """Delete a specific memory by ID"""
        try:
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
            if not memory_manager:
                return jsonify({"error": "Memory manager not available"}), 503
            
            result = memory_manager.delete_memory(memory_id)
            
            if not result:
                return jsonify({"error": f"Memory with ID {memory_id} not found"}), 404
            
            return jsonify({"status": "deleted", "id": memory_id}), 200
        
        except Exception as e:
            logger.exception(f"Error deleting memory {memory_id}: {e}")
            return jsonify({"error": str(e)}), 500

# Register the endpoints
memory_view = MemoryAPI.as_view('memory_api')
memory_detail_view = MemoryDetailAPI.as_view('memory_detail_api')

memory_bp.add_url_rule('/', view_func=memory_view, methods=['GET', 'POST', 'DELETE'])
memory_bp.add_url_rule('/<string:memory_id>', view_func=memory_detail_view, methods=['GET', 'PUT', 'DELETE'])

# Setup before request handler to ensure memory manager is available
@memory_bp.before_request
def setup_memory_manager():
    """Ensure memory manager is available in g"""
    if not hasattr(g, 'memory_manager'):
        g.memory_manager = current_app.config.get('memory_manager') 