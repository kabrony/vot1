"""
Stats API Endpoints

This module provides API endpoints for system statistics and monitoring,
including memory usage, conversation stats, and overall performance metrics.
"""

import os
import time
import logging
import psutil
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from flask.views import MethodView

# Set up logging
logger = logging.getLogger(__name__)

# Create Stats Blueprint
stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

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

class StatsAPI(MethodView):
    """API endpoint for system statistics"""
    
    def get(self):
        """Get system statistics"""
        try:
            stats_type = request.args.get('type', 'all')
            
            # Update stats from the memory manager
            self._update_stats()
            
            # Calculate uptime
            uptime_seconds = time.time() - _system_stats.get("start_time", time.time())
            uptime = {
                "seconds": int(uptime_seconds),
                "minutes": int(uptime_seconds / 60),
                "hours": int(uptime_seconds / 3600),
                "days": int(uptime_seconds / 86400),
                "text": self._format_uptime(uptime_seconds)
            }
            
            # Get system information
            system_info = self._get_system_info()
            
            # Combine all stats
            combined_stats = {
                "uptime": uptime,
                "system": system_info,
                "memory_usage": {
                    "total_conversations": _system_stats.get("total_conversations", 0),
                    "total_semantic_memories": _system_stats.get("total_semantic_memories", 0)
                },
                "performance": {
                    "total_tokens_processed": _system_stats.get("total_tokens_processed", 0),
                    "total_api_calls": _system_stats.get("total_api_calls", 0),
                    "total_tool_uses": _system_stats.get("total_tool_uses", 0)
                }
            }
            
            # Filter by stats type if specified
            if stats_type != 'all':
                if stats_type in combined_stats:
                    return jsonify(combined_stats[stats_type])
                else:
                    return jsonify({"error": f"Invalid stats type: {stats_type}"}), 400
            
            return jsonify(combined_stats)
        
        except Exception as e:
            logger.exception(f"Error getting system stats: {e}")
            return jsonify({"error": str(e)}), 500
    
    def _update_stats(self):
        """Update system statistics from memory manager and other sources"""
        global _system_stats
        
        memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
        if memory_manager:
            try:
                # Get memory counts
                _system_stats["total_semantic_memories"] = memory_manager.get_memory_count("semantic")
                _system_stats["total_conversations"] = memory_manager.get_memory_count("conversation")
            except Exception as e:
                logger.error(f"Error updating memory stats: {e}")
        
        client = current_app.config.get('client')
        if client:
            try:
                # Get client stats if available
                if hasattr(client, 'get_stats'):
                    client_stats = client.get_stats()
                    _system_stats.update(client_stats)
            except Exception as e:
                logger.error(f"Error updating client stats: {e}")
    
    def _get_system_info(self):
        """Get system information"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Get network information
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent
                },
                "memory": {
                    "percent": memory_percent,
                    "used": memory_used,
                    "total": memory_total,
                    "used_gb": round(memory_used / (1024 ** 3), 2),
                    "total_gb": round(memory_total / (1024 ** 3), 2)
                },
                "disk": {
                    "percent": disk_percent,
                    "used": disk_used,
                    "total": disk_total,
                    "used_gb": round(disk_used / (1024 ** 3), 2),
                    "total_gb": round(disk_total / (1024 ** 3), 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "mb_sent": round(network.bytes_sent / (1024 ** 2), 2),
                    "mb_recv": round(network.bytes_recv / (1024 ** 2), 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "error": str(e)
            }
    
    def _format_uptime(self, uptime_seconds):
        """Format uptime in a human-readable way"""
        days = int(uptime_seconds / 86400)
        hours = int((uptime_seconds % 86400) / 3600)
        minutes = int((uptime_seconds % 3600) / 60)
        seconds = int(uptime_seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)

class StatusAPI(MethodView):
    """API endpoint for system status"""
    
    def get(self):
        """Get system status"""
        try:
            # Get current timestamp
            current_time = time.time()
            
            # Calculate idle time
            idle_time = current_time - _last_activity_time
            
            # Check if services are available
            memory_manager_available = self._check_memory_manager()
            client_available = self._check_client()
            
            # Set overall status
            if memory_manager_available and client_available:
                status = "healthy"
            elif memory_manager_available or client_available:
                status = "degraded"
            else:
                status = "unavailable"
            
            return jsonify({
                "status": status,
                "timestamp": current_time,
                "idle_time": idle_time,
                "services": {
                    "memory_manager": memory_manager_available,
                    "client": client_available
                }
            })
        
        except Exception as e:
            logger.exception(f"Error getting system status: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    def _check_memory_manager(self):
        """Check if memory manager is available"""
        memory_manager = getattr(g, 'memory_manager', None) or current_app.config.get('memory_manager')
        return memory_manager is not None
    
    def _check_client(self):
        """Check if client is available"""
        client = current_app.config.get('client')
        return client is not None

# Register activity event
def register_activity():
    """Register system activity to update the last activity time"""
    global _last_activity_time
    _last_activity_time = time.time()

# Register the endpoints
stats_view = StatsAPI.as_view('stats_api')
status_view = StatusAPI.as_view('status_api')

stats_bp.add_url_rule('/', view_func=stats_view, methods=['GET'])
stats_bp.add_url_rule('/status', view_func=status_view, methods=['GET'])

# Register activity on each request
@stats_bp.before_request
def update_activity_time():
    """Update last activity time on each request"""
    register_activity() 