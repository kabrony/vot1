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
import io
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from werkzeug.utils import secure_filename

from flask import Blueprint, request, jsonify, current_app, g, stream_with_context, Response
from flask.views import MethodView
from src.vot1.vot_mcp import VotModelControlProtocol
from src.vot1.memory import MemoryManager
from src.vot1.integrations.composio.openapi import OpenAPIComposioIntegration
import asyncio
from src.vot1.integrations.perplexity import PerplexitySearch

# Import MCP hybrid API
from .mcp_hybrid_api import init_mcp_hybrid_api

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
_openapi_integration = None
_mcp_hybrid_automation = None
_routes_registered = None

# Initialize MCP and Memory Manager
mcp = VotModelControlProtocol(
    primary_model=os.getenv("VOT1_PRIMARY_MODEL", "anthropic/claude-3-7-sonnet-20240620"),
    secondary_model=os.getenv("VOT1_SECONDARY_MODEL", "perplexity/pplx-70b-online")
)
memory_manager = MemoryManager(
    memory_path=os.getenv("VOT1_MEMORY_DIR", "memory")
)

# Initialize Composio Integration (if API key is available)
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")

# In-memory conversation store (would be a database in production)
conversation_store = {}

# Flag to track if routes have been registered
_routes_registered = False

def init_api(socketio, client, memory_manager):
    """
    Initialize the API with the required components.
    
    Args:
        socketio: SocketIO instance for real-time communication
        client: EnhancedClaudeClient instance for AI interactions
        memory_manager: MemoryManager instance for memory operations
    
    Returns:
        The API blueprint
    """
    global _socketio, _client, _memory_manager, _openapi_integration, _mcp_hybrid_automation, _routes_registered
    _socketio = socketio
    _client = client
    _memory_manager = memory_manager
    
    # Initialize OpenAPI integration if API key is available
    if COMPOSIO_API_KEY:
        try:
            from src.vot1.integrations.composio.openapi import OpenAPIComposioIntegration
            _openapi_integration = OpenAPIComposioIntegration(api_key=COMPOSIO_API_KEY)
            logger.info("OpenAPI integration initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OpenAPI integration: {e}")
            _openapi_integration = None
    
    # Initialize MCP Hybrid Automation
    try:
        from scripts.mcp_hybrid_automation import McpHybridAutomation
        
        # Get MCP hybrid options from app config
        mcp_hybrid_options = current_app.config.get('MCP_HYBRID_OPTIONS', {})
        
        _mcp_hybrid_automation = McpHybridAutomation(
            primary_model=mcp_hybrid_options.get("primary_model", "claude-3-7-sonnet-20240620"),
            secondary_model=mcp_hybrid_options.get("secondary_model", "claude-3-5-sonnet-20240620"),
            use_extended_thinking=mcp_hybrid_options.get("use_extended_thinking", False),
            max_thinking_tokens=mcp_hybrid_options.get("max_thinking_tokens", 8000)
        )
        
        # Initialize MCP hybrid API
        init_mcp_hybrid_api(_mcp_hybrid_automation)
        
        logger.info(f"MCP Hybrid Automation initialized with primary model: {_mcp_hybrid_automation.primary_model}")
    except ImportError as e:
        logger.warning(f"Could not initialize MCP Hybrid Automation: {e}")
        _mcp_hybrid_automation = None
    
    # Initialize system stats
    _update_system_stats()
    
    # Register API routes if not already registered
    if not _routes_registered:
        register_api_routes()
        _routes_registered = True
    
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


# Add new OpenAPI Integration API endpoints

class OpenAPIIntegrationAPI(MethodView):
    """API endpoints for OpenAPI integration with Composio"""
    
    async def _get_openapi_integration(self):
        """Get or initialize the OpenAPI integration"""
        global _openapi_integration
        
        if not _openapi_integration and COMPOSIO_API_KEY:
            try:
                from src.vot1.integrations.composio.openapi import create_openapi_integration
                _openapi_integration = await create_openapi_integration(COMPOSIO_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAPI integration: {e}")
                return None
                
        return _openapi_integration
    
    async def get(self):
        """List all imported OpenAPI tools"""
        try:
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available. Check if COMPOSIO_API_KEY is set."}), 503
            
            tools = await integration.list_imported_tools()
            
            return jsonify({
                "tools": tools,
                "count": len(tools)
            })
            
        except Exception as e:
            logger.error(f"Error listing OpenAPI tools: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
    
    async def post(self):
        """Import an OpenAPI specification"""
        try:
            # Check if integration is available
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available. Check if COMPOSIO_API_KEY is set."}), 503
            
            # Check if the post has the required files
            if 'spec_file' not in request.files:
                return jsonify({"error": "No spec_file provided"}), 400
                
            spec_file = request.files['spec_file']
            if spec_file.filename == '':
                return jsonify({"error": "Empty spec_file name"}), 400
            
            # Get auth file if provided
            auth_file = None
            if 'auth_file' in request.files:
                auth_file = request.files['auth_file']
                if auth_file.filename == '':
                    auth_file = None
            
            # Get additional parameters
            tool_name = request.form.get('tool_name')
            description = request.form.get('description')
            tags = request.form.get('tags')
            if tags:
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Import the OpenAPI spec
            result = await integration.import_openapi_spec(
                spec_content=spec_file.stream,
                auth_config=auth_file.stream if auth_file else None,
                tool_name=tool_name,
                description=description,
                tags=tags
            )
            
            return jsonify({
                "success": True,
                "tool": result,
                "message": f"OpenAPI spec imported successfully as '{result.get('name', 'unknown')}'"
            }), 201
            
        except Exception as e:
            logger.error(f"Error importing OpenAPI spec: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
            
    async def delete(self, tool_id):
        """Delete an imported OpenAPI tool"""
        try:
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available"}), 503
            
            success = await integration.delete_imported_tool(tool_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Tool '{tool_id}' deleted successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": f"Failed to delete tool '{tool_id}'"
                }), 404
                
        except Exception as e:
            logger.error(f"Error deleting OpenAPI tool: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


class OpenAPIToolAPI(MethodView):
    """API endpoints for specific OpenAPI tool operations"""
    
    async def _get_openapi_integration(self):
        """Get or initialize the OpenAPI integration"""
        global _openapi_integration
        
        if not _openapi_integration and COMPOSIO_API_KEY:
            try:
                from src.vot1.integrations.composio.openapi import create_openapi_integration
                _openapi_integration = await create_openapi_integration(COMPOSIO_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAPI integration: {e}")
                return None
                
        return _openapi_integration
    
    async def get(self, tool_id):
        """Get details of a specific OpenAPI tool"""
        try:
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available"}), 503
            
            tool_details = await integration.get_tool_details(tool_id)
            
            return jsonify(tool_details)
            
        except Exception as e:
            logger.error(f"Error getting tool details: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
    
    async def post(self, tool_id):
        """Execute an action on an OpenAPI tool"""
        try:
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available"}), 503
            
            data = request.json
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
                
            action = data.get('action')
            if not action:
                return jsonify({"error": "No action specified"}), 400
                
            parameters = data.get('parameters', {})
            
            # Execute the tool action
            result = await integration.execute_tool_action(
                tool_name_or_id=tool_id,
                action=action,
                parameters=parameters
            )
            
            # Track usage for stats
            global _system_stats
            _system_stats["total_tool_uses"] += 1
            
            return jsonify({
                "success": True,
                "result": result,
                "tool_id": tool_id,
                "action": action
            })
            
        except Exception as e:
            logger.error(f"Error executing tool action: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


class ComposioStatusAPI(MethodView):
    """API endpoint to check Composio connection status"""
    
    async def get(self):
        """Check Composio connection status"""
        try:
            if not COMPOSIO_API_KEY:
                return jsonify({
                    "connected": False,
                    "error": "COMPOSIO_API_KEY environment variable not set"
                }), 200
            
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({
                    "connected": False,
                    "error": "Failed to initialize OpenAPI integration"
                }), 200
            
            # Get status
            status = await integration.connector.get_status()
            
            return jsonify({
                "connected": status.get("status") == "active",
                "status": status.get("status"),
                "version": status.get("version"),
                "api_key_configured": bool(COMPOSIO_API_KEY)
            })
            
        except Exception as e:
            logger.error(f"Error checking Composio status: {e}", exc_info=True)
            return jsonify({
                "connected": False,
                "error": str(e)
            }), 200
    
    async def _get_openapi_integration(self):
        """Get or initialize the OpenAPI integration"""
        global _openapi_integration
        
        if not _openapi_integration and COMPOSIO_API_KEY:
            try:
                from src.vot1.integrations.composio.openapi import create_openapi_integration
                _openapi_integration = await create_openapi_integration(COMPOSIO_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAPI integration: {e}")
                return None
                
        return _openapi_integration


class RepositoryUsageAPI(MethodView):
    """API endpoint to check repository usage"""
    
    async def get(self, repository=None):
        """Check repository usage"""
        try:
            integration = await self._get_openapi_integration()
            if not integration:
                return jsonify({"error": "OpenAPI integration not available"}), 503
            
            # Use default repository if not specified
            if not repository:
                repository = "vot1"
            
            usage = await integration.check_daily_repository_usage(repository)
            
            return jsonify(usage)
            
        except Exception as e:
            logger.error(f"Error checking repository usage: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
    
    async def _get_openapi_integration(self):
        """Get or initialize the OpenAPI integration"""
        global _openapi_integration
        
        if not _openapi_integration and COMPOSIO_API_KEY:
            try:
                from src.vot1.integrations.composio.openapi import create_openapi_integration
                _openapi_integration = await create_openapi_integration(COMPOSIO_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAPI integration: {e}")
                return None
                
        return _openapi_integration


# Register OpenAPI endpoints
api_bp.add_url_rule('/openapi/tools', view_func=OpenAPIIntegrationAPI.as_view('openapi_tools'))
api_bp.add_url_rule('/openapi/tools/<tool_id>', view_func=OpenAPIToolAPI.as_view('openapi_tool'))
api_bp.add_url_rule('/openapi/status', view_func=ComposioStatusAPI.as_view('openapi_status'))
api_bp.add_url_rule('/openapi/usage', view_func=RepositoryUsageAPI.as_view('repository_usage'))
api_bp.add_url_rule('/openapi/usage/<repository>', view_func=RepositoryUsageAPI.as_view('repository_usage_specific'))

# Register existing endpoints
api_bp.add_url_rule('/memories', view_func=MemoryAPI.as_view('memories'))
api_bp.add_url_rule('/visualization-data', view_func=VisualizationDataAPI.as_view('visualization_data'))
api_bp.add_url_rule('/stats', view_func=StatsAPI.as_view('stats'))
api_bp.add_url_rule('/web-search', view_func=WebSearchAPI.as_view('web_search'))
api_bp.add_url_rule('/owl-reasoning', view_func=OWLReasoningAPI.as_view('owl_reasoning'))


# Modified API endpoint for chat message processing to support Composio integration
@api_bp.route('/chat/message', methods=['POST'])
def process_chat_message():
    """
    Process a chat message from the user and return a response.
    
    Request body should contain:
    - message: The user's message
    - conversation_id: Optional conversation ID (will be generated if not provided)
    - include_memory_context: Whether to include memory context (default: True)
    - memory_context_level: Level of memory context to include (default: medium)
    - visualization_mode: Optional mode for visualization updates
    - model: Optional model to use (default: primary model)
    - use_composio: Whether to enable Composio tool use (default: False)
    
    Returns a JSON response with:
    - response: The assistant's response
    - message_id: Unique ID for the message
    - conversation_id: The conversation ID
    - memory_references: Any memory references related to the query
    - visualization_update: Optional visualization update command
    - tools_used: List of tools used in processing the message (if any)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        message = data.get('message', '')
        if not message:
            return jsonify({"error": "No message provided"}), 400
            
        conversation_id = data.get('conversation_id', f'conv-{uuid.uuid4()}')
        include_memory = data.get('include_memory_context', True)
        memory_context_level = data.get('memory_context_level', 'medium')
        use_composio = data.get('use_composio', False)
        selected_model = data.get('model', None)  # Use default if None
        
        logger.info(f"Processing message for conversation {conversation_id}")
        
        # Get conversation history
        conversation_history = get_conversation_history(conversation_id)
        
        # Retrieve memory context if requested
        memory_context = None
        if include_memory:
            memory_context = get_memory_context(
                message, 
                max_items=10 if memory_context_level == 'high' else (5 if memory_context_level == 'medium' else 3)
            )
        
        # Process with MCP
        process_params = {
            'message': message,
            'conversation_history': conversation_history,
            'memory_context': memory_context,
            'use_composio': use_composio,
            'model': selected_model
        }
        
        response = asyncio.run(process_with_mcp(**process_params))
        
        # Save the conversation
        save_conversation(conversation_id, {
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        save_conversation(conversation_id, {
            'role': 'assistant',
            'content': response.get('content', ''),
            'timestamp': datetime.now().isoformat(),
            'memory_references': response.get('memory_references', []),
            'tools_used': response.get('tools_used', [])
        })
        
        # Format the response
        formatted_response = {
            'response': response.get('content', ''),
            'message_id': f'msg-{uuid.uuid4()}',
            'conversation_id': conversation_id,
            'memory_references': response.get('memory_references', []),
            'visualization_update': response.get('visualization_update'),
            'tools_used': response.get('tools_used', [])
        }
        
        return jsonify(formatted_response)
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route('/chat/available-models', methods=['GET'])
def get_available_models():
    """
    Get available AI models that can be used for chat.
    
    Returns a JSON array of available models with their IDs and names
    """
    try:
        # 2025 models
        models = [
            {
                'id': 'anthropic/claude-3-7-sonnet-20240620',
                'name': 'Claude 3.7 Sonnet (Default)',
                'provider': 'Anthropic',
                'supports_tools': True,
                'context_window': 200000
            },
            {
                'id': 'anthropic/claude-3-5-sonnet-20240620',
                'name': 'Claude 3.5 Sonnet',
                'provider': 'Anthropic',
                'supports_tools': True,
                'context_window': 180000
            },
            {
                'id': 'anthropic/claude-3-haiku-20240307',
                'name': 'Claude 3 Haiku (Fast)',
                'provider': 'Anthropic',
                'supports_tools': True,
                'context_window': 75000
            },
            {
                'id': 'openai/gpt-4o-turbo',
                'name': 'GPT-4o Turbo',
                'provider': 'OpenAI',
                'supports_tools': True,
                'context_window': 128000
            },
            {
                'id': 'openai/gpt-4o-mini',
                'name': 'GPT-4o Mini',
                'provider': 'OpenAI',
                'supports_tools': True,
                'context_window': 64000
            },
            {
                'id': 'perplexity/pplx-70b-online',
                'name': 'Perplexity 70B (Online)',
                'provider': 'Perplexity',
                'supports_tools': False,
                'context_window': 32000
            },
            {
                'id': 'deepseek/deepseek-r1-preview',
                'name': 'DeepSeek R1 Preview (Newest)',
                'provider': 'DeepSeek',
                'supports_tools': True,
                'context_window': 130000
            }
        ]
        
        return jsonify(models)
        
    except Exception as e:
        logger.error(f"Error retrieving available models: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

async def process_with_mcp(message, conversation_history, memory_context=None, use_composio=False, model=None):
    """
    Process a message with MCP and return the response.
    
    Args:
        message: The user's message
        conversation_history: List of previous messages
        memory_context: Optional memory context
        use_composio: Whether to enable Composio tool use
        model: Specific model to use (default: use primary model)
        
    Returns:
        Dictionary with response content, memory references, visualization update, and tools used
    """
    try:
        # Get the system prompt (with memory context included)
        system_prompt = get_system_prompt(memory_context, use_composio)
        
        # Format conversation history for MCP
        formatted_history = format_conversation_history(conversation_history)
        
        # Create the request for MCP
        request_data = {
            'prompt': message,
            'system': system_prompt,
            'context': {
                'conversation': formatted_history
            },
            'max_tokens': 1024
        }
        
        # Use specified model if provided
        if model:
            request_data['model'] = model
        
        # Add memory context if available
        if memory_context and memory_context.get('items'):
            request_data['context']['memories'] = memory_context.get('items')
        
        # Enable Composio tools if requested
        tools_used = []
        if use_composio and _openapi_integration:
            try:
                # List available tools for reference in the system prompt
                available_tools = await _openapi_integration.list_imported_tools()
                tool_descriptions = []
                
                for tool in available_tools[:5]:  # Limit to top 5 tools to avoid overloading context
                    tool_descriptions.append({
                        'name': tool.get('name'),
                        'description': tool.get('description'),
                        'actions': [a.get('name') for a in tool.get('actions', [])]
                    })
                
                # Add tools to request
                request_data['tools'] = {
                    'available': tool_descriptions,
                    'use_composio': True
                }
                
                # Set the flag for tool use
                request_data['use_tools'] = True
                
            except Exception as e:
                logger.error(f"Error setting up tools for MCP: {e}")
        
        # Process with MCP
        response = await mcp.process_request_async(**request_data)
        
        # Extract any visualization commands
        visualization_update = extract_visualization_commands(response.get('content', ''))
        
        # Check if any tools were used
        if response.get('tool_uses'):
            for tool_use in response.get('tool_uses', []):
                tools_used.append({
                    'name': tool_use.get('tool_name'),
                    'action': tool_use.get('action_name'),
                    'parameters': tool_use.get('parameters')
                })
        
        # Prepare the result
        result = {
            'content': response.get('content', ''),
            'memory_references': format_memory_references(memory_context),
            'tools_used': tools_used
        }
        
        # Add visualization update if any
        if visualization_update:
            result['visualization_update'] = visualization_update
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing with MCP: {e}", exc_info=True)
        return {
            'content': f"I'm having trouble processing your request. Error: {str(e)}",
            'memory_references': [],
            'tools_used': []
        }

def get_system_prompt(memory_context=None, use_composio=False):
    """
    Generate the system prompt based on context.
    
    Args:
        memory_context: Optional memory context to include
        use_composio: Whether Composio tools are enabled
        
    Returns:
        System prompt string
    """
    base_prompt = """
    You are VOT1 Assistant, an AI that helps users interact with the VOT1 memory system and dashboard.
    
    Your capabilities include:
    - Providing information about memories stored in the system
    - Helping control the visualization through commands
    - Searching for specific memories based on content
    - Explaining how the memory system works
    - Suggesting visualization commands to explore the memory network
    """
    
    # Add Composio tool capabilities if enabled
    if use_composio:
        base_prompt += """
    - Using external tools via Composio to perform tasks (weather, search, etc.)
    - Analyzing repositories and code quality
    - Accessing online information sources
        
    When using tools:
    - Only use tools when explicitly needed to answer the user's question
    - Always explain which tool you're using and why
    - Return results in a clear, formatted way
    """
    
    base_prompt += """
    Guidelines:
    - Be concise and helpful in your responses
    - When mentioning specific memories, include their ID (format: mem-XXXXX)
    - You can suggest visualization commands like [VISUALIZATION:{"command":"focus","params":{"query":"memory topic"}}]
    - For complex memory exploration, suggest specific search terms or filters
    
    Available visualization commands:
    - focus: Zoom in on specific memories matching a query
    - highlight: Highlight specific nodes in the visualization
    - filter: Filter the visualization by memory type or date
    - reset: Reset the visualization to its default state
    """
    
    # Include memory context if available
    if memory_context and memory_context.get('items'):
        base_prompt += "\n\nI'm providing you with relevant memories based on the user's query:"
        for i, item in enumerate(memory_context.get('items', [])[:3]):
            # Get a short excerpt of the memory content
            content_excerpt = item.get('content', '')[:200] + ('...' if len(item.get('content', '')) > 200 else '')
            
            # Get memory metadata
            memory_type = item.get('metadata', {}).get('type', 'Unknown type')
            memory_id = item.get('id', 'unknown')
            memory_title = item.get('metadata', {}).get('title', 'Untitled memory')
            
            # Add to the prompt
            base_prompt += f"\n\nMemory {i+1}:"
            base_prompt += f"\n- ID: {memory_id}"
            base_prompt += f"\n- Title: {memory_title}"
            base_prompt += f"\n- Type: {memory_type}"
            base_prompt += f"\n- Content: {content_excerpt}"
    
    return base_prompt

def get_memory_context(query, max_items=5):
    """
    Retrieve relevant memories based on the query.
    
    Args:
        query: The search query
        max_items: Maximum number of items to retrieve
        
    Returns:
        Dictionary with query and items
    """
    try:
        # Search for memories
        results = memory_manager.search_semantic_memory(
            query=query,
            num_results=max_items
        )
        
        # Format the results
        items = []
        for item in results:
            items.append({
                'id': item.id,
                'content': item.content,
                'metadata': item.metadata,
                'score': item.score
            })
        
        return {
            'query': query,
            'items': items
        }
    except Exception as e:
        logger.error(f"Error retrieving memory context: {e}", exc_info=True)
        return {'query': query, 'items': []}

def format_memory_references(memory_context):
    """
    Format memory references for the response.
    
    Args:
        memory_context: Memory context dictionary
        
    Returns:
        List of formatted memory references
    """
    if not memory_context or not memory_context.get('items'):
        return []
    
    references = []
    for item in memory_context.get('items', []):
        references.append({
            'id': item.get('id', ''),
            'relevance': item.get('score', 0.7),
            'summary': item.get('metadata', {}).get('title', item.get('id', 'Memory'))
        })
    
    return references

def extract_visualization_commands(content):
    """
    Extract visualization commands from the response text.
    
    Args:
        content: The response content
        
    Returns:
        Visualization command dictionary or None
    """
    # Check for visualization command pattern
    if '[VISUALIZATION:' in content:
        try:
            # Extract the command string
            start = content.find('[VISUALIZATION:')
            end = content.find(']', start)
            command_str = content[start+15:end].strip()
            
            # Parse the command as JSON
            command_data = json.loads(command_str)
            
            # Remove the command from the content
            clean_content = content[:start] + content[end+1:]
            
            return command_data
        except Exception as e:
            logger.error(f"Error extracting visualization command: {e}", exc_info=True)
    
    return None

def get_conversation_history(conversation_id, max_length=25):
    """
    Get the conversation history for a given ID.
    
    Args:
        conversation_id: The conversation ID
        max_length: Maximum number of messages to return
        
    Returns:
        List of messages in the conversation
    """
    history = conversation_store.get(conversation_id, [])
    return history[-max_length:] if history else []

def save_conversation(conversation_id, message):
    """
    Save a message to the conversation history.
    
    Args:
        conversation_id: The conversation ID
        message: The message to save
    """
    if conversation_id not in conversation_store:
        conversation_store[conversation_id] = []
    
    conversation_store[conversation_id].append(message)
    
    # In a production system, this would be saved to a database

def format_conversation_history(history):
    """
    Format conversation history for MCP.
    
    Args:
        history: List of message dictionaries
        
    Returns:
        List of formatted messages for MCP
    """
    return [
        {'role': item.get('role', 'user'), 'content': item.get('content', '')}
        for item in history
    ]

class PerplexitySearchAPI(MethodView):
    """API for Perplexity AI search functionality"""
    
    def __init__(self):
        self.perplexity = PerplexitySearch()
    
    def post(self):
        """Perform a search query using Perplexity AI"""
        data = request.get_json() or {}
        query = data.get('query', '')
        focus = data.get('focus')
        max_results = data.get('max_results', 5)
        
        if not query:
            return {'error': 'Query is required'}, 400
            
        results = self.perplexity.search(query, focus, max_results)
        return results

class PerplexityAnswerAPI(MethodView):
    """API for Perplexity AI question answering"""
    
    def __init__(self):
        self.perplexity = PerplexitySearch()
    
    def post(self):
        """Get an answer to a question using Perplexity AI"""
        data = request.get_json() or {}
        question = data.get('question', '')
        include_sources = data.get('include_sources', True)
        
        if not question:
            return {'error': 'Question is required'}, 400
            
        answer = self.perplexity.answer_question(question, include_sources)
        return answer

class PerplexitySummarizeAPI(MethodView):
    """API for Perplexity AI search and summarize"""
    
    def __init__(self):
        self.perplexity = PerplexitySearch()
    
    def post(self):
        """Search for information on a topic and provide a summarized report"""
        data = request.get_json() or {}
        topic = data.get('topic', '')
        depth = data.get('depth', 'medium')
        
        if not topic:
            return {'error': 'Topic is required'}, 400
            
        summary = self.perplexity.search_and_summarize(topic, depth)
        return summary

# Register the Perplexity API endpoints
api_bp.add_url_rule('/perplexity/search', view_func=PerplexitySearchAPI.as_view('perplexity_search'))
api_bp.add_url_rule('/perplexity/answer', view_func=PerplexityAnswerAPI.as_view('perplexity_answer'))
api_bp.add_url_rule('/perplexity/summarize', view_func=PerplexitySummarizeAPI.as_view('perplexity_summarize'))

# Add new Composio Integration API endpoints

class ComposioModelsAPI(MethodView):
    """API endpoints for Composio models"""
    
    def _get_composio_client(self):
        """Get or initialize the Composio client"""
        try:
            from src.vot1.integrations.composio import ComposioClient
            return ComposioClient()
        except Exception as e:
            logger.error(f"Failed to initialize Composio client: {e}")
            return None
    
    def get(self):
        """List all available Composio models"""
        try:
            client = self._get_composio_client()
            if not client:
                return jsonify({"error": "Composio client not available"}), 503
            
            models = client.list_models()
            
            return jsonify(models)
            
        except Exception as e:
            logger.error(f"Error listing Composio models: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


class ComposioGenerateAPI(MethodView):
    """API endpoints for Composio text generation"""
    
    def _get_composio_client(self):
        """Get or initialize the Composio client"""
        try:
            from src.vot1.integrations.composio import ComposioClient
            return ComposioClient()
        except Exception as e:
            logger.error(f"Failed to initialize Composio client: {e}")
            return None
    
    def post(self):
        """Generate text using Composio"""
        try:
            client = self._get_composio_client()
            if not client:
                return jsonify({"error": "Composio client not available"}), 503
            
            data = request.json
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
                
            prompt = data.get('prompt')
            if not prompt:
                return jsonify({"error": "No prompt provided"}), 400
                
            model_id = data.get('model')
            max_tokens = data.get('max_tokens', 1000)
            temperature = data.get('temperature', 0.7)
            stop_sequences = data.get('stop', None)
            
            # Generate text
            response = client.generate_text(
                prompt=prompt,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                stop_sequences=stop_sequences
            )
            
            # Track usage for stats
            global _system_stats
            _system_stats["total_api_calls"] += 1
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


class ComposioEmbeddingAPI(MethodView):
    """API endpoints for Composio embeddings"""
    
    def _get_composio_client(self):
        """Get or initialize the Composio client"""
        try:
            from src.vot1.integrations.composio import ComposioClient
            return ComposioClient()
        except Exception as e:
            logger.error(f"Failed to initialize Composio client: {e}")
            return None
    
    def post(self):
        """Create an embedding using Composio"""
        try:
            client = self._get_composio_client()
            if not client:
                return jsonify({"error": "Composio client not available"}), 503
            
            data = request.json
            if not data:
                return jsonify({"error": "No JSON data provided"}), 400
                
            text = data.get('text')
            if not text:
                return jsonify({"error": "No text provided"}), 400
                
            model_id = data.get('model')
            
            # Create embedding
            response = client.create_embedding(
                text=text,
                model_id=model_id
            )
            
            # Track usage for stats
            global _system_stats
            _system_stats["total_api_calls"] += 1
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error creating embedding: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


class ComposioStatusAPI(MethodView):
    """API endpoint to check Composio connection status"""
    
    def _get_composio_client(self):
        """Get or initialize the Composio client"""
        try:
            from src.vot1.integrations.composio import ComposioClient
            return ComposioClient()
        except Exception as e:
            logger.error(f"Failed to initialize Composio client: {e}")
            return None
    
    def get(self):
        """Check Composio connection status"""
        try:
            client = self._get_composio_client()
            if not client:
                return jsonify({
                    "connected": False,
                    "error": "Failed to initialize Composio client"
                }), 200
            
            # Get status
            status = client.check_connection()
            
            return jsonify(status)
            
        except Exception as e:
            logger.error(f"Error checking Composio status: {e}", exc_info=True)
            return jsonify({
                "connected": False,
                "error": str(e)
            }), 200


class ComposioUsageAPI(MethodView):
    """API endpoint to check Composio usage"""
    
    def _get_composio_client(self):
        """Get or initialize the Composio client"""
        try:
            from src.vot1.integrations.composio import ComposioClient
            return ComposioClient()
        except Exception as e:
            logger.error(f"Failed to initialize Composio client: {e}")
            return None
    
    def get(self):
        """Check Composio usage"""
        try:
            client = self._get_composio_client()
            if not client:
                return jsonify({"error": "Composio client not available"}), 503
            
            # Get usage
            usage = client.get_usage()
            
            return jsonify(usage)
            
        except Exception as e:
            logger.error(f"Error checking Composio usage: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500


# Register Composio endpoints
api_bp.add_url_rule('/composio/models', view_func=ComposioModelsAPI.as_view('composio_models'))
api_bp.add_url_rule('/composio/generate', view_func=ComposioGenerateAPI.as_view('composio_generate'))
api_bp.add_url_rule('/composio/embedding', view_func=ComposioEmbeddingAPI.as_view('composio_embedding'))
api_bp.add_url_rule('/composio/status', view_func=ComposioStatusAPI.as_view('composio_status'))
api_bp.add_url_rule('/composio/usage', view_func=ComposioUsageAPI.as_view('composio_usage'))

def register_api_routes():
    """Register all API routes."""
    # Check if the routes have already been registered
    if hasattr(api_bp, '_got_registered_once'):
        return
    
    # Register API routes with the blueprint
    api_bp.add_url_rule('/memory', view_func=MemoryAPI.as_view('memory_api'))
    api_bp.add_url_rule('/memory/<memory_id>', view_func=MemoryAPI.as_view('memory_detail_api'))
    api_bp.add_url_rule('/visualization-data', view_func=VisualizationDataAPI.as_view('visualization_data_api'))
    api_bp.add_url_rule('/stats', view_func=StatsAPI.as_view('stats_api'))
    api_bp.add_url_rule('/web-search', view_func=WebSearchAPI.as_view('web_search_api'))
    api_bp.add_url_rule('/owl-reasoning', view_func=OWLReasoningAPI.as_view('owl_reasoning_api'))
    api_bp.add_url_rule('/openapi', view_func=OpenAPIIntegrationAPI.as_view('openapi_api'))
    api_bp.add_url_rule('/openapi/<tool_id>', view_func=OpenAPIToolAPI.as_view('openapi_tool_api'))
    api_bp.add_url_rule('/composio-status', view_func=ComposioStatusAPI.as_view('composio_status_api'))
    api_bp.add_url_rule('/repository-usage', view_func=RepositoryUsageAPI.as_view('repository_usage_api'))
    api_bp.add_url_rule('/repository-usage/<repository>', view_func=RepositoryUsageAPI.as_view('repository_usage_detail_api'))
    api_bp.add_url_rule('/perplexity/search', view_func=PerplexitySearchAPI.as_view('perplexity_search_api'))
    api_bp.add_url_rule('/perplexity/answer', view_func=PerplexityAnswerAPI.as_view('perplexity_answer_api'))
    api_bp.add_url_rule('/perplexity/summarize', view_func=PerplexitySummarizeAPI.as_view('perplexity_summarize_api'))
    api_bp.add_url_rule('/composio/models', view_func=ComposioModelsAPI.as_view('composio_models_api'))
    api_bp.add_url_rule('/composio/generate', view_func=ComposioGenerateAPI.as_view('composio_generate_api'))
    api_bp.add_url_rule('/composio/embedding', view_func=ComposioEmbeddingAPI.as_view('composio_embedding_api'))
    api_bp.add_url_rule('/composio/status', view_func=ComposioStatusAPI.as_view('composio_status_api'))
    api_bp.add_url_rule('/composio/usage', view_func=ComposioUsageAPI.as_view('composio_usage_api'))
    
    # Mark the blueprint as registered
    api_bp._got_registered_once = True 

# Add a new endpoint for user feedback
@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback for system improvement.
    
    The feedback is stored in the memory system and used to improve future responses.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        feedback_type = data.get('type')
        content = data.get('content')
        source = data.get('source', 'dashboard')
        rating = data.get('rating')
        
        if not all([feedback_type, content]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Log the feedback
        logger.info(f"Received feedback: {feedback_type} from {source}")
        
        # Create metadata for the feedback
        metadata = {
            "type": "feedback",
            "feedback_type": feedback_type,
            "source": source,
            "timestamp": time.time(),
        }
        
        if rating is not None:
            metadata["rating"] = rating
        
        # Store in memory system if available
        if _memory_manager:
            try:
                # Use the new add_memory_with_metrics method for better retrieval
                memory_id = _memory_manager.add_memory_with_metrics(content, metadata)
                
                # If we have the MCP hybrid automation, trigger learning from feedback
                if _mcp_hybrid_automation:
                    asyncio.create_task(_process_feedback_for_learning(memory_id, content, metadata))
                
                return jsonify({
                    "status": "success",
                    "message": "Feedback submitted successfully",
                    "memory_id": memory_id
                })
            except Exception as e:
                logger.error(f"Error storing feedback in memory: {e}")
                return jsonify({
                    "status": "partial_success",
                    "message": f"Feedback logged but not stored in memory: {e}"
                })
        else:
            # If no memory manager, just log the feedback
            logger.warning("No memory manager available, feedback only logged")
            return jsonify({
                "status": "partial_success",
                "message": "Feedback logged but not stored (no memory system available)"
            })
    
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        return jsonify({"error": f"Error processing feedback: {e}"}), 500

async def _process_feedback_for_learning(memory_id, content, metadata):
    """
    Process feedback for learning and improvement.
    
    This function is called asynchronously after storing feedback in memory.
    It triggers the MCP hybrid automation to learn from the feedback.
    """
    try:
        if not _mcp_hybrid_automation:
            logger.warning("MCP hybrid automation not available for feedback learning")
            return
        
        # Prepare prompt for learning
        feedback_type = metadata.get("feedback_type", "general")
        
        if feedback_type == "correction":
            prompt = f"""
            The user has provided a correction to a previous response. 
            Learn from this correction to improve future responses:
            
            Correction: {content}
            
            Please analyze what went wrong in the original response and how to avoid this issue in the future.
            Identify specific knowledge gaps or misconceptions that should be addressed.
            """
        
        elif feedback_type == "suggestion":
            prompt = f"""
            The user has provided a suggestion for improvement:
            
            Suggestion: {content}
            
            Please analyze this suggestion and determine how it can be incorporated into the system's behavior.
            What specific changes in approach would implement this suggestion?
            """
        
        elif feedback_type == "rating":
            rating = metadata.get("rating", 0)
            prompt = f"""
            The user has rated a response {rating}/5.
            
            Additional feedback: {content}
            
            Please analyze what aspects of the response were good or bad based on this rating.
            How can future responses be improved to achieve higher ratings?
            """
        
        else:  # general feedback
            prompt = f"""
            The user has provided general feedback:
            
            Feedback: {content}
            
            Please analyze this feedback and determine what insights can be gained to improve future interactions.
            What specific changes would address this feedback?
            """
        
        # Send to MCP hybrid automation for processing
        result = await _mcp_hybrid_automation.process_feedback(prompt, metadata)
        
        # Store the insights back in memory
        if result and _memory_manager:
            insight_metadata = {
                "type": "system_insight",
                "source": "feedback_learning",
                "original_feedback_id": memory_id,
                "timestamp": time.time()
            }
            
            _memory_manager.add_memory_with_metrics(result, insight_metadata)
            
            logger.info(f"Processed feedback {memory_id} and stored insights")
        
    except Exception as e:
        logger.error(f"Error processing feedback for learning: {e}")

# Add a streaming feedback endpoint
@api_bp.route('/feedback/stream', methods=['POST'])
def stream_feedback_response():
    """
    Submit feedback and get a streaming response on how the system will improve.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        content = data.get('content')
        feedback_type = data.get('type', 'general')
        
        if not content:
            return jsonify({"error": "Missing feedback content"}), 400
        
        # Log the feedback
        logger.info(f"Received streaming feedback request: {feedback_type}")
        
        # Define streaming response
        def generate():
            # Initial thinking state
            yield json.dumps({
                "status": "thinking",
                "message": "Processing your feedback..."
            }) + "\n"
            
            time.sleep(0.5)
            
            # Processing state
            yield json.dumps({
                "status": "processing",
                "message": "Analyzing feedback patterns",
                "progress": 0.3
            }) + "\n"
            
            time.sleep(0.5)
            
            # More processing
            yield json.dumps({
                "status": "processing",
                "message": "Identifying improvement opportunities",
                "progress": 0.6
            }) + "\n"
            
            time.sleep(0.5)
            
            # Responding state
            yield json.dumps({
                "status": "responding",
                "message": "Generating response",
                "progress": 0.8
            }) + "\n"
            
            # Store feedback in memory
            metadata = {
                "type": "feedback",
                "feedback_type": feedback_type,
                "source": "dashboard",
                "timestamp": time.time(),
            }
            
            if _memory_manager:
                try:
                    memory_id = _memory_manager.add_memory_with_metrics(content, metadata)
                except Exception as e:
                    logger.error(f"Error storing feedback in memory: {e}")
            
            # Generate acknowledgment message
            response = "Thank you for your feedback. Here's how we'll use it to improve:\n\n"
            
            # Add specific details based on feedback type
            if feedback_type == "correction":
                response += "- We'll correct this information in our knowledge base\n"
                response += "- Future responses will reflect this correction\n"
                response += "- We'll analyze why this error occurred to prevent similar issues\n"
            elif feedback_type == "suggestion":
                response += "- We'll incorporate your suggestion into system improvements\n"
                response += "- Your idea will be prioritized for upcoming updates\n"
                response += "- We'll monitor how this change affects overall experience\n"
            else:
                response += "- Your feedback will be analyzed for insights\n"
                response += "- We'll identify specific areas for improvement\n"
                response += "- System behavior will be adjusted accordingly\n"
            
            # Stream response in chunks of words
            words = response.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3])
                progress = 0.8 + (0.2 * (i / len(words)))
                
                yield json.dumps({
                    "status": "complete",
                    "chunk": chunk + " ",
                    "progress": progress
                }) + "\n"
                
                time.sleep(0.1)
        
        return Response(generate(), mimetype='application/x-ndjson')
        
    except Exception as e:
        logger.error(f"Error processing streaming feedback: {e}")
        return jsonify({"error": f"Error processing feedback: {e}"}), 500 