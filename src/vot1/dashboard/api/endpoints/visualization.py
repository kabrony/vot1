"""
Visualization API Endpoints

This module provides API endpoints for data visualization operations,
including retrieving graph data, memory visualizations, and other
interactive visualizations.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from flask.views import MethodView

# Set up logging
logger = logging.getLogger(__name__)

# Create Visualization Blueprint
visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')

class VisualizationDataAPI(MethodView):
    """API endpoint for visualization data operations"""
    
    def get(self):
        """Get visualization data with optional filtering"""
        try:
            visualization_type = request.args.get('type', 'memory')
            time_range = request.args.get('range', '7d')  # Default to 7 days
            
            # Calculate time range
            end_time = datetime.now()
            if time_range == '24h':
                start_time = end_time - timedelta(hours=24)
            elif time_range == '7d':
                start_time = end_time - timedelta(days=7)
            elif time_range == '30d':
                start_time = end_time - timedelta(days=30)
            elif time_range == '90d':
                start_time = end_time - timedelta(days=90)
            else:
                return jsonify({"error": f"Invalid time range: {time_range}"}), 400
            
            # Get data based on visualization type
            if visualization_type == 'memory':
                data = self._get_memory_visualization_data(start_time, end_time)
            elif visualization_type == 'api_usage':
                data = self._get_api_usage_visualization_data(start_time, end_time)
            elif visualization_type == 'conversation':
                data = self._get_conversation_visualization_data(start_time, end_time)
            elif visualization_type == 'embedding':
                data = self._get_embedding_visualization_data()
            else:
                return jsonify({"error": f"Invalid visualization type: {visualization_type}"}), 400
            
            return jsonify(data)
        
        except Exception as e:
            logger.exception(f"Error getting visualization data: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _get_memory_visualization_data(self, start_time, end_time):
        """Get memory usage visualization data"""
        memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
        if not memory_manager:
            return {"error": "Memory manager not available"}
        
        try:
            # Get memory counts over time
            timestamps = []
            semantic_counts = []
            conversation_counts = []
            
            # Get all memories
            all_memories = memory_manager.get_all_memories(limit=10000)
            
            # Filter by timestamp and group by day
            date_counts = {}
            for memory in all_memories:
                timestamp = memory.get('timestamp')
                if not timestamp:
                    continue
                
                memory_time = datetime.fromtimestamp(timestamp)
                if start_time <= memory_time <= end_time:
                    date_key = memory_time.strftime('%Y-%m-%d')
                    memory_type = memory.get('type', 'unknown')
                    
                    if date_key not in date_counts:
                        date_counts[date_key] = {'semantic': 0, 'conversation': 0}
                    
                    if memory_type == 'semantic':
                        date_counts[date_key]['semantic'] += 1
                    elif memory_type == 'conversation':
                        date_counts[date_key]['conversation'] += 1
            
            # Sort dates and prepare data
            sorted_dates = sorted(date_counts.keys())
            timestamps = sorted_dates
            semantic_counts = [date_counts[date]['semantic'] for date in sorted_dates]
            conversation_counts = [date_counts[date]['conversation'] for date in sorted_dates]
            
            return {
                'type': 'memory',
                'timestamps': timestamps,
                'semantic_counts': semantic_counts,
                'conversation_counts': conversation_counts,
                'total_semantic': sum(semantic_counts),
                'total_conversation': sum(conversation_counts),
                'total': sum(semantic_counts) + sum(conversation_counts)
            }
        
        except Exception as e:
            logger.exception(f"Error getting memory visualization data: {e}")
            return {"error": str(e)}
    
    def _get_api_usage_visualization_data(self, start_time, end_time):
        """Get API usage visualization data"""
        # This would typically come from an API usage tracking system
        # For now, we'll return mock data
        
        # Generate sample data for demonstration
        dates = []
        api_calls = []
        
        current_date = start_time
        while current_date <= end_time:
            dates.append(current_date.strftime('%Y-%m-%d'))
            # Mock data: random-ish but increasing pattern
            day_number = (current_date - start_time).days + 1
            api_calls.append(100 + day_number * 10)
            current_date += timedelta(days=1)
        
        return {
            'type': 'api_usage',
            'dates': dates,
            'api_calls': api_calls,
            'total_calls': sum(api_calls)
        }
    
    def _get_conversation_visualization_data(self, start_time, end_time):
        """Get conversation visualization data"""
        memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
        if not memory_manager:
            return {"error": "Memory manager not available"}
        
        try:
            # Get conversation memories
            conversations = memory_manager.get_conversation_memories(limit=1000)
            
            # Filter by timestamp
            filtered_conversations = []
            for conv in conversations:
                timestamp = conv.get('timestamp')
                if not timestamp:
                    continue
                
                conv_time = datetime.fromtimestamp(timestamp)
                if start_time <= conv_time <= end_time:
                    filtered_conversations.append(conv)
            
            # Analyze user vs assistant messages
            user_messages = 0
            assistant_messages = 0
            avg_user_length = 0
            avg_assistant_length = 0
            
            user_length_sum = 0
            assistant_length_sum = 0
            
            for conv in filtered_conversations:
                content = conv.get('content', {})
                messages = content.get('messages', [])
                
                for msg in messages:
                    role = msg.get('role', '')
                    text = msg.get('content', '')
                    
                    if role == 'user':
                        user_messages += 1
                        user_length_sum += len(text)
                    elif role == 'assistant':
                        assistant_messages += 1
                        assistant_length_sum += len(text)
            
            if user_messages > 0:
                avg_user_length = user_length_sum / user_messages
            
            if assistant_messages > 0:
                avg_assistant_length = assistant_length_sum / assistant_messages
            
            return {
                'type': 'conversation',
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'total_messages': user_messages + assistant_messages,
                'avg_user_length': avg_user_length,
                'avg_assistant_length': avg_assistant_length,
                'conversation_count': len(filtered_conversations)
            }
        
        except Exception as e:
            logger.exception(f"Error getting conversation visualization data: {e}")
            return {"error": str(e)}
    
    def _get_embedding_visualization_data(self):
        """Get embedding visualization data (for 3D visualization)"""
        memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
        if not memory_manager:
            return {"error": "Memory manager not available"}
        
        try:
            # Check if we have vector embeddings available
            if not hasattr(memory_manager, 'get_semantic_embeddings'):
                return {
                    'type': 'embedding',
                    'error': 'Vector embeddings not available',
                    'points': []
                }
            
            # Get semantic memory embeddings
            embeddings = memory_manager.get_semantic_embeddings(limit=100)
            
            points = []
            for embed in embeddings:
                points.append({
                    'id': embed.get('id', ''),
                    'position': embed.get('position', [0, 0, 0]),
                    'content': embed.get('content', ''),
                    'type': embed.get('memory_type', 'semantic')
                })
            
            return {
                'type': 'embedding',
                'points': points
            }
        
        except Exception as e:
            logger.exception(f"Error getting embedding visualization data: {e}")
            return {
                'type': 'embedding',
                'error': str(e),
                'points': []
            }

# Register the endpoints
visualization_view = VisualizationDataAPI.as_view('visualization_api')
visualization_bp.add_url_rule('/', view_func=visualization_view, methods=['GET']) 