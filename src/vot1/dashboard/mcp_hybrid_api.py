"""
MCP Hybrid Automation API
=========================

This module provides an API endpoint for MCP hybrid automation.

Credit: Implemented with assistance from Claude 3.7 Sonnet, an AI assistant by Anthropic.
"""

import json
import logging
import time
from flask import Blueprint, jsonify, request, Response, stream_with_context, current_app
from flask.views import MethodView

# Configure logging
logger = logging.getLogger(__name__)

# Create MCP hybrid blueprint
mcp_hybrid_bp = Blueprint('mcp_hybrid', __name__, url_prefix='/api')

# Global variable to store MCP hybrid automation instance
_mcp_hybrid_automation = None

def init_mcp_hybrid_api(mcp_hybrid_automation):
    """
    Initialize the MCP hybrid API with the MCP hybrid automation instance.
    
    Args:
        mcp_hybrid_automation: McpHybridAutomation instance
    """
    global _mcp_hybrid_automation
    _mcp_hybrid_automation = mcp_hybrid_automation
    logger.info(f"MCP Hybrid API initialized with automation instance using models: "
               f"{mcp_hybrid_automation.primary_model} and {mcp_hybrid_automation.secondary_model}")
    
    # Log memory manager status
    if mcp_hybrid_automation.memory_manager:
        logger.info(f"MCP Hybrid API has access to memory manager at: {mcp_hybrid_automation.memory_manager.storage_dir}")
    else:
        logger.warning("MCP Hybrid API initialized without memory manager")

class MCPHybridAPI(MethodView):
    """API endpoint for MCP hybrid automation."""
    
    def get(self):
        """Get MCP hybrid automation configuration."""
        if _mcp_hybrid_automation is None:
            return jsonify({
                "status": "error",
                "message": "MCP Hybrid Automation is not available"
            }), 404
        
        # Include memory manager status in response
        memory_status = "available" if _mcp_hybrid_automation.memory_manager else "unavailable"
        
        return jsonify({
            "status": "success",
            "enabled": True,
            "primary_model": _mcp_hybrid_automation.primary_model,
            "secondary_model": _mcp_hybrid_automation.secondary_model,
            "extended_thinking": _mcp_hybrid_automation.use_extended_thinking,
            "max_thinking_tokens": _mcp_hybrid_automation.max_thinking_tokens,
            "streaming_enabled": True,
            "memory_system": memory_status
        })
    
    def post(self):
        """Process a request using MCP hybrid automation."""
        if _mcp_hybrid_automation is None:
            return jsonify({
                "status": "error",
                "message": "MCP Hybrid Automation is not available"
            }), 404
        
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing prompt in request"
            }), 400
        
        prompt = data.get('prompt')
        system = data.get('system')
        complexity = data.get('complexity', 'auto')
        max_tokens = data.get('max_tokens')
        temperature = data.get('temperature', 0.7)
        stream = data.get('stream', False)
        use_memory = data.get('use_memory', True)
        
        # Log the request
        logger.info(f"MCP Hybrid API request: complexity={complexity}, use_memory={use_memory}, stream={stream}")
        
        # Handle streaming responses
        if stream:
            try:
                def generate():
                    # Get relevant memory context if enabled
                    memory_context = None
                    if use_memory and _mcp_hybrid_automation.memory_manager:
                        memory_context = _mcp_hybrid_automation.get_memory_context(prompt)
                        if memory_context:
                            yield f"data: {json.dumps({'memory_context': f'Using {len(memory_context)} relevant memories'})}\n\n"
                    
                    # Process with MCP hybrid automation
                    start_time = time.time()
                    result = _mcp_hybrid_automation.process_with_optimal_model(
                        prompt=prompt,
                        task_complexity=complexity,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        use_memory=use_memory
                    )
                    processing_time = time.time() - start_time
                    
                    # Get response text
                    if isinstance(result, str):
                        text = result
                    else:
                        text = result.get('content', '')
                    
                    # Stream in chunks of approximately 20 characters
                    chunk_size = 20
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i+chunk_size]
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                        # Small delay for streaming effect
                        time.sleep(0.05)
                    
                    # Send metadata
                    metadata = {
                        'done': True,
                        'processing_time': processing_time,
                        'model_used': _mcp_hybrid_automation.primary_model if complexity == 'complex' else _mcp_hybrid_automation.secondary_model,
                        'memory_used': use_memory and memory_context is not None
                    }
                    yield f"data: {json.dumps(metadata)}\n\n"
                
                return Response(
                    stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    }
                )
            
            except Exception as e:
                logger.error(f"Error streaming response with MCP hybrid automation: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        # Handle non-streaming responses
        try:
            # Get relevant memory information for metadata
            memory_context = None
            if use_memory and _mcp_hybrid_automation.memory_manager:
                memory_context = _mcp_hybrid_automation.get_memory_context(prompt)
            
            # Process with MCP hybrid automation
            start_time = time.time()
            result = _mcp_hybrid_automation.process_with_optimal_model(
                prompt=prompt,
                task_complexity=complexity,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                use_memory=use_memory
            )
            processing_time = time.time() - start_time
            
            # Format the result
            if isinstance(result, str):
                response_text = result
            else:
                response_text = result.get('content', '')
            
            # Include metadata in response
            return jsonify({
                "status": "success",
                "result": response_text,
                "metadata": {
                    "processing_time": processing_time,
                    "model_used": _mcp_hybrid_automation.primary_model if complexity == 'complex' else _mcp_hybrid_automation.secondary_model,
                    "memory_used": use_memory and memory_context is not None,
                    "memory_contexts": len(memory_context) if memory_context else 0
                }
            })
        except Exception as e:
            logger.error(f"Error processing request with MCP hybrid automation: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

# Register the MCP hybrid API route
mcp_hybrid_bp.add_url_rule('/mcp-hybrid', view_func=MCPHybridAPI.as_view('mcp_hybrid_api'))

# Add endpoint to retrieve recent memories
@mcp_hybrid_bp.route('/mcp-hybrid/memories', methods=['GET'])
def get_recent_memories():
    """Get recent memories from the memory system."""
    if _mcp_hybrid_automation is None or _mcp_hybrid_automation.memory_manager is None:
        return jsonify({
            "status": "error",
            "message": "Memory system is not available"
        }), 404
    
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        query = request.args.get('query', '')
        
        # Get memories
        if query:
            memories = _mcp_hybrid_automation.memory_manager.search(query, limit=limit)
        else:
            memories = _mcp_hybrid_automation.memory_manager.get_recent_memories(limit=limit)
        
        return jsonify({
            "status": "success",
            "memories": memories
        })
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Add endpoint to add a test memory
@mcp_hybrid_bp.route('/mcp-hybrid/memories', methods=['POST'])
def add_test_memory():
    """Add a test memory to the memory system."""
    if _mcp_hybrid_automation is None or _mcp_hybrid_automation.memory_manager is None:
        return jsonify({
            "status": "error",
            "message": "Memory system is not available"
        }), 404
    
    data = request.json
    if not data or 'content' not in data:
        return jsonify({
            "status": "error",
            "message": "Missing content in request"
        }), 400
    
    try:
        content = data.get('content')
        metadata = data.get('metadata', {})
        
        # Add memory directly to vector store
        memory_id = _mcp_hybrid_automation.memory_manager.add_semantic_memory(
            content=content,
            metadata=metadata
        )
        
        return jsonify({
            "status": "success",
            "memory_id": memory_id
        })
    except Exception as e:
        logger.error(f"Error adding test memory: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500 