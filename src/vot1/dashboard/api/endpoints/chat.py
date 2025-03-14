"""
Chat API Endpoints

This module provides API endpoints for chat and message handling,
including sending messages, managing conversations, and retrieving
chat history.
"""

import os
import json
import time
import uuid
import logging
from flask import Blueprint, request, jsonify, current_app, g, stream_with_context, Response
from flask.views import MethodView

# Set up logging
logger = logging.getLogger(__name__)

# Create Chat Blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# In-memory conversation store (would be a database in production)
conversation_store = {}

class ChatAPI(MethodView):
    """API endpoint for chat operations"""
    
    def get(self):
        """Get chat history"""
        try:
            conversation_id = request.args.get('conversation_id')
            limit = int(request.args.get('limit', 50))
            
            if not conversation_id:
                # Return a list of all conversations
                return jsonify(self._get_all_conversations(limit))
            
            # Get a specific conversation
            conversation = self._get_conversation(conversation_id)
            
            if not conversation:
                return jsonify({"error": f"Conversation not found: {conversation_id}"}), 404
            
            return jsonify(conversation)
        
        except Exception as e:
            logger.exception(f"Error getting chat history: {e}")
            return jsonify({"error": str(e)}), 500
    
    def post(self):
        """Send a message to the chat"""
        try:
            data = request.json
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            message = data.get('message')
            conversation_id = data.get('conversation_id')
            
            if not message:
                return jsonify({"error": "Message is required"}), 400
            
            # Create a new conversation if none provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                self._create_conversation(conversation_id)
            
            # Check if conversation exists
            if conversation_id not in conversation_store:
                return jsonify({"error": f"Conversation not found: {conversation_id}"}), 404
            
            # Get AI client
            client = current_app.config.get('client')
            if not client:
                return jsonify({"error": "AI client not available"}), 503
            
            # Add user message to conversation
            user_message = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": message,
                "timestamp": time.time()
            }
            conversation_store[conversation_id]["messages"].append(user_message)
            
            # Get conversation memory context if available
            memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
            memory_context = []
            
            if memory_manager:
                try:
                    # Get relevant memories
                    semantic_memories = memory_manager.search_semantic_memories(message, limit=5)
                    
                    if semantic_memories:
                        memory_context = [
                            {
                                "role": "system",
                                "content": f"Relevant memory: {memory['content']}"
                            }
                            for memory in semantic_memories
                        ]
                except Exception as e:
                    logger.error(f"Error getting memory context: {e}")
            
            # Generate AI response
            try:
                # Check if streaming is requested
                stream = data.get('stream', False)
                
                if stream:
                    return self._stream_response(client, conversation_id, message, memory_context)
                else:
                    # Generate non-streaming response
                    response = self._generate_response(client, message, memory_context)
                    
                    if not response:
                        return jsonify({"error": "Failed to generate response"}), 500
                    
                    # Add assistant message to conversation
                    assistant_message = {
                        "id": str(uuid.uuid4()),
                        "role": "assistant",
                        "content": response,
                        "timestamp": time.time()
                    }
                    conversation_store[conversation_id]["messages"].append(assistant_message)
                    
                    # Save conversation to memory if available
                    if memory_manager:
                        try:
                            memory_manager.add_conversation_memory(
                                conversation_store[conversation_id],
                                metadata={"id": conversation_id}
                            )
                        except Exception as e:
                            logger.error(f"Error saving conversation to memory: {e}")
                    
                    return jsonify({
                        "conversation_id": conversation_id,
                        "message": assistant_message
                    })
            
            except Exception as e:
                logger.exception(f"Error generating response: {e}")
                return jsonify({"error": str(e)}), 500
        
        except Exception as e:
            logger.exception(f"Error processing chat message: {e}")
            return jsonify({"error": str(e)}), 500
    
    def delete(self):
        """Clear chat history"""
        try:
            conversation_id = request.args.get('conversation_id')
            
            if not conversation_id:
                # Clear all conversations
                conversation_store.clear()
                return jsonify({"status": "cleared all conversations"})
            
            # Clear a specific conversation
            if conversation_id in conversation_store:
                del conversation_store[conversation_id]
                return jsonify({"status": f"cleared conversation {conversation_id}"})
            else:
                return jsonify({"error": f"Conversation not found: {conversation_id}"}), 404
        
        except Exception as e:
            logger.exception(f"Error clearing chat history: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _create_conversation(self, conversation_id):
        """Create a new conversation"""
        conversation_store[conversation_id] = {
            "id": conversation_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        return conversation_store[conversation_id]
    
    def _get_conversation(self, conversation_id):
        """Get a conversation by ID"""
        return conversation_store.get(conversation_id)
    
    def _get_all_conversations(self, limit=50):
        """Get all conversations"""
        conversations = []
        
        # Sort conversations by updated_at time (newest first)
        sorted_conversations = sorted(
            conversation_store.values(),
            key=lambda conv: conv.get("updated_at", 0),
            reverse=True
        )
        
        # Take the requested number of conversations
        for conversation in sorted_conversations[:limit]:
            # Create a summary without full message content
            summary = {
                "id": conversation["id"],
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "message_count": len(conversation.get("messages", [])),
                "last_message": None
            }
            
            # Add the last message if available
            messages = conversation.get("messages", [])
            if messages:
                last_message = messages[-1]
                summary["last_message"] = {
                    "role": last_message.get("role"),
                    "content_preview": last_message.get("content", "")[:100],
                    "timestamp": last_message.get("timestamp")
                }
            
            conversations.append(summary)
        
        return conversations
    
    def _generate_response(self, client, message, memory_context=None):
        """Generate a response using the AI client"""
        try:
            # Prepare messages for the client
            messages = []
            
            # Add system message
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant. Respond in a concise and helpful manner."
            })
            
            # Add memory context if available
            if memory_context:
                messages.extend(memory_context)
            
            # Add user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Use perplexity integration if available for knowledge-heavy queries
            if "?" in message and len(message.split()) > 5:
                try:
                    perplexity_client = getattr(g, 'perplexity_client', None)
                    if perplexity_client:
                        perplexity_result = perplexity_client.search(message)
                        if perplexity_result:
                            # Add perplexity result to context
                            messages.append({
                                "role": "system",
                                "content": f"Research results: {perplexity_result}"
                            })
                except Exception as e:
                    logger.error(f"Error using perplexity integration: {e}")
            
            # Generate response
            response = client.generate_text(messages)
            return response
        
        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            return None
    
    def _stream_response(self, client, conversation_id, message, memory_context=None):
        """Stream a response using the AI client"""
        @stream_with_context
        def generate():
            try:
                # Prepare messages for the client
                messages = []
                
                # Add system message
                messages.append({
                    "role": "system",
                    "content": "You are a helpful AI assistant. Respond in a concise and helpful manner."
                })
                
                # Add memory context if available
                if memory_context:
                    messages.extend(memory_context)
                
                # Add user message
                messages.append({
                    "role": "user",
                    "content": message
                })
                
                # Generate streaming response
                response_chunks = client.generate_text_stream(messages)
                
                full_response = ""
                
                for chunk in response_chunks:
                    full_response += chunk
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                # Add assistant message to conversation
                assistant_message = {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                }
                conversation_store[conversation_id]["messages"].append(assistant_message)
                
                # Save conversation to memory if available
                memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
                if memory_manager:
                    try:
                        memory_manager.add_conversation_memory(
                            conversation_store[conversation_id],
                            metadata={"id": conversation_id}
                        )
                    except Exception as e:
                        logger.error(f"Error saving conversation to memory: {e}")
                
                # Send 'done' event
                yield f"data: {json.dumps({'done': True})}\n\n"
            
            except Exception as e:
                logger.exception(f"Error generating streaming response: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/event-stream')


# Register the endpoints
chat_view = ChatAPI.as_view('chat_api')
chat_bp.add_url_rule('/', view_func=chat_view, methods=['GET', 'POST', 'DELETE'])

# Setup before request handler
@chat_bp.before_request
def setup_chat_api():
    """Ensure necessary services are available"""
    if not hasattr(g, 'memory_manager'):
        g.memory_manager = current_app.config.get('memory_manager') 