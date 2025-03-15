#!/usr/bin/env python3
"""
TRILOGY BRAIN Web Server

This module provides a simple web server for the TRILOGY BRAIN user interface,
serving the 3D visualization interface and API endpoints for the distributed
memory system.

Features:
- Serves static files for the web interface
- Provides REST API endpoints for node management
- Handles WebSocket connections for real-time updates
- Integrates with the VOT1 Memory System and MCP Node Controller

Usage:
    python web_server.py [--port PORT] [--host HOST]

Author: Organix (VOT1 Project)
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

import aiohttp
from aiohttp import web
import aiohttp_cors
import websockets

# Add parent directory to path to allow importing VOT1 modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, parent_dir)

try:
    from vot1.distributed.mcp_node_controller import MCPNodeController
    from vot1.core.principles import PrinciplesEngine
except ImportError:
    print("Warning: Could not import VOT1 modules. Running in standalone mode.")
    MCPNodeController = None
    PrinciplesEngine = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "web_server.log"))
    ]
)
logger = logging.getLogger("trilogy_brain_web")

# WebSocket clients for broadcasting updates
websocket_clients = set()

class TrilogyBrainWebServer:
    """Main web server class for the TRILOGY BRAIN interface"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080, node_controller=None):
        """
        Initialize the web server
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            node_controller: Optional MCPNodeController instance
        """
        self.host = host
        self.port = port
        self.node_controller = node_controller
        self.app = web.Application()
        self.principles_engine = PrinciplesEngine() if PrinciplesEngine else None
        
        # Path to web files
        self.web_dir = os.path.join(os.path.dirname(__file__), "web")
        if not os.path.exists(self.web_dir):
            logger.error(f"Web directory not found: {self.web_dir}")
            raise FileNotFoundError(f"Web directory not found: {self.web_dir}")
        
        self._setup_routes()
        self._setup_cors()
        
        logger.info(f"Web directory: {self.web_dir}")
        logger.info(f"Initialized TRILOGY BRAIN Web Server on {host}:{port}")
    
    def _setup_routes(self):
        """Configure the web server routes"""
        
        # Static files
        self.app.router.add_static('/assets/', path=os.path.join(self.web_dir, "assets"), name='assets')
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/trilogy_brain_ui.js', self.handle_ui_js)
        
        # API endpoints
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/nodes', self.handle_nodes)
        self.app.router.add_get('/api/nodes/{node_id}', self.handle_node)
        self.app.router.add_post('/api/nodes', self.handle_add_node)
        self.app.router.add_delete('/api/nodes/{node_id}', self.handle_remove_node)
        self.app.router.add_get('/api/memories', self.handle_memories)
        self.app.router.add_get('/api/stats', self.handle_stats)
        
        # WebSocket endpoint
        self.app.router.add_get('/ws', self.handle_websocket)
    
    def _setup_cors(self):
        """Configure CORS for the API endpoints"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*"
            )
        })
        
        # Apply CORS to all routes
        for route in list(self.app.router.routes()):
            if not isinstance(route.resource, web.StaticResource):
                cors.add(route)
    
    async def handle_index(self, request):
        """Serve the index.html file"""
        return web.FileResponse(os.path.join(self.web_dir, "index.html"))
    
    async def handle_ui_js(self, request):
        """Serve the trilogy_brain_ui.js file"""
        return web.FileResponse(os.path.join(self.web_dir, "trilogy_brain_ui.js"))
    
    async def handle_status(self, request):
        """API endpoint for system status"""
        status = {
            "status": "online",
            "version": "1.0.0",
            "uptime": get_uptime(),
            "timestamp": datetime.now().isoformat(),
            "node_count": self.node_controller.get_node_count() if self.node_controller else 0,
            "memory_count": self.node_controller.get_memory_count() if self.node_controller else 0
        }
        return web.json_response(status)
    
    async def handle_nodes(self, request):
        """API endpoint for getting all nodes"""
        if self.node_controller:
            nodes = self.node_controller.get_all_nodes()
            return web.json_response({"nodes": nodes})
        else:
            # Return mock data in standalone mode
            return web.json_response({"nodes": self._get_mock_nodes()})
    
    async def handle_node(self, request):
        """API endpoint for getting a specific node"""
        node_id = request.match_info.get('node_id')
        
        if self.node_controller:
            node = self.node_controller.get_node(node_id)
            if node:
                return web.json_response({"node": node})
            else:
                return web.json_response({"error": "Node not found"}, status=404)
        else:
            # Return mock data in standalone mode
            mock_nodes = self._get_mock_nodes()
            node = next((n for n in mock_nodes if n["id"] == node_id), None)
            if node:
                return web.json_response({"node": node})
            else:
                return web.json_response({"error": "Node not found"}, status=404)
    
    async def handle_add_node(self, request):
        """API endpoint for adding a new node"""
        try:
            data = await request.json()
            node_type = data.get("type")
            host = data.get("host")
            port = data.get("port")
            
            if not all([node_type, host, port]):
                return web.json_response({"error": "Missing required fields"}, status=400)
            
            if self.node_controller:
                # Verify action with principles engine if available
                if self.principles_engine:
                    action_data = {
                        "action": "add_node",
                        "node_type": node_type,
                        "host": host,
                        "port": port
                    }
                    if not self.principles_engine.verify_action(action_data):
                        return web.json_response({"error": "Action not permitted by principles"}, status=403)
                
                node_id = self.node_controller.add_node(node_type, host, port)
                return web.json_response({"success": True, "node_id": node_id})
            else:
                # Mock response in standalone mode
                return web.json_response({
                    "success": True, 
                    "node_id": f"{node_type}_node_{str(hash(host + str(port)))[-4:]}"
                })
                
        except Exception as e:
            logger.error(f"Error adding node: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_remove_node(self, request):
        """API endpoint for removing a node"""
        node_id = request.match_info.get('node_id')
        
        # Verify action with principles engine if available
        if self.principles_engine:
            action_data = {
                "action": "remove_node",
                "node_id": node_id
            }
            if not self.principles_engine.verify_action(action_data):
                return web.json_response({"error": "Action not permitted by principles"}, status=403)
        
        if self.node_controller:
            success = self.node_controller.remove_node(node_id)
            return web.json_response({"success": success})
        else:
            # Mock response in standalone mode
            return web.json_response({"success": True})
    
    async def handle_memories(self, request):
        """API endpoint for getting memories"""
        if self.node_controller:
            limit = int(request.query.get('limit', 100))
            offset = int(request.query.get('offset', 0))
            memories = self.node_controller.get_memories(limit, offset)
            return web.json_response({"memories": memories})
        else:
            # Return mock data in standalone mode
            return web.json_response({"memories": self._get_mock_memories()})
    
    async def handle_stats(self, request):
        """API endpoint for system statistics"""
        if self.node_controller:
            stats = self.node_controller.get_system_stats()
            return web.json_response(stats)
        else:
            # Return mock data in standalone mode
            return web.json_response(self._get_mock_stats())
    
    async def handle_websocket(self, request):
        """WebSocket handler for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        websocket_clients.add(ws)
        logger.info(f"WebSocket client connected. Total clients: {len(websocket_clients)}")
        
        try:
            # Send initial status
            await ws.send_json({
                "type": "status",
                "data": {
                    "status": "connected",
                    "timestamp": datetime.now().isoformat(),
                    "message": "Connected to TRILOGY BRAIN WebSocket"
                }
            })
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        command = data.get("command")
                        
                        if command == "get_nodes":
                            # Handle node request
                            if self.node_controller:
                                nodes = self.node_controller.get_all_nodes()
                            else:
                                nodes = self._get_mock_nodes()
                            await ws.send_json({"type": "nodes", "data": nodes})
                            
                        elif command == "get_stats":
                            # Handle stats request
                            if self.node_controller:
                                stats = self.node_controller.get_system_stats()
                            else:
                                stats = self._get_mock_stats()
                            await ws.send_json({"type": "stats", "data": stats})
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received: {msg.data}")
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket connection closed with exception {ws.exception()}")
        
        finally:
            websocket_clients.remove(ws)
            logger.info(f"WebSocket client disconnected. Total clients: {len(websocket_clients)}")
        
        return ws
    
    async def broadcast_update(self, update_type: str, data: Any):
        """
        Broadcast an update to all connected WebSocket clients
        
        Args:
            update_type: Type of update (e.g., "nodes", "stats")
            data: Data to broadcast
        """
        if not websocket_clients:
            return
        
        message = json.dumps({"type": update_type, "data": data})
        await asyncio.gather(
            *[client.send_str(message) for client in websocket_clients if not client.closed]
        )
    
    def _get_mock_nodes(self) -> List[Dict[str, Any]]:
        """Get mock node data for standalone mode"""
        node_types = ["memory", "compute", "coordinator", "validator", "gateway"]
        statuses = ["online", "offline", "error", "syncing"]
        
        nodes = []
        for i in range(10):
            node_type = node_types[i % len(node_types)]
            nodes.append({
                "id": f"{node_type}_node_{i}",
                "type": node_type,
                "status": statuses[i % len(statuses)],
                "host": f"192.168.1.{10 + i}",
                "port": 8000 + i,
                "uptime": 3600 * (i + 1),
                "memory_usage": round(0.1 + (i * 0.05), 2),
                "cpu_usage": round(0.2 + (i * 0.07), 2),
                "connections": i + 1,
                "last_ping": (datetime.now().timestamp() - (i * 60)) * 1000
            })
        return nodes
    
    def _get_mock_memories(self) -> List[Dict[str, Any]]:
        """Get mock memory data for standalone mode"""
        memory_types = ["episodic", "semantic", "procedural", "metacognitive"]
        
        memories = []
        for i in range(20):
            memory_type = memory_types[i % len(memory_types)]
            memories.append({
                "id": f"memory_{i}",
                "type": memory_type,
                "created_at": (datetime.now().timestamp() - (i * 3600)) * 1000,
                "last_accessed": (datetime.now().timestamp() - (i * 600)) * 1000,
                "size": 1024 * (i + 1),
                "tags": [f"tag{j}" for j in range(1, (i % 5) + 2)],
                "importance": round(0.1 + (i * 0.04), 2),
                "access_count": i * 3
            })
        return memories
    
    def _get_mock_stats(self) -> Dict[str, Any]:
        """Get mock system statistics for standalone mode"""
        return {
            "node_count": 10,
            "memory_count": 1248,
            "active_connections": 18,
            "system_uptime": get_uptime(),
            "memory_usage": 0.45,
            "cpu_usage": 0.32,
            "network_health": 87,
            "memory_nodes": {"total": 4, "online": 3},
            "compute_nodes": {"total": 2, "online": 2},
            "validator_nodes": {"total": 2, "online": 1},
            "coordinator_nodes": {"total": 1, "online": 1},
            "gateway_nodes": {"total": 1, "online": 0}
        }
    
    async def start(self):
        """Start the web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        url = f"http://{self.host}:{self.port}"
        logger.info(f"TRILOGY BRAIN Web Server started at {url}")
        
        # Start background tasks
        self.update_task = asyncio.create_task(self._periodic_updates())
        
        return url
    
    async def _periodic_updates(self):
        """Send periodic updates to connected WebSocket clients"""
        while True:
            try:
                # Update nodes
                if self.node_controller:
                    nodes = self.node_controller.get_all_nodes()
                else:
                    nodes = self._get_mock_nodes()
                await self.broadcast_update("nodes", nodes)
                
                # Update stats
                if self.node_controller:
                    stats = self.node_controller.get_system_stats()
                else:
                    stats = self._get_mock_stats()
                await self.broadcast_update("stats", stats)
                
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")
            
            # Wait before next update
            await asyncio.sleep(5)


def get_uptime() -> int:
    """Get system uptime in seconds"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds)
    except:
        # Fallback if /proc/uptime is not available
        return 0


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="TRILOGY BRAIN Web Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()
    
    # Try to import and initialize MCP Node Controller
    node_controller = None
    if MCPNodeController:
        try:
            node_controller = MCPNodeController()
            logger.info("MCP Node Controller initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Node Controller: {e}")
    
    # Create and start the web server
    server = TrilogyBrainWebServer(host=args.host, port=args.port, node_controller=node_controller)
    url = await server.start()
    
    # Open web browser
    if not args.no_browser:
        webbrowser.open(url)
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)  # Sleep for an hour (or until interrupted)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1) 