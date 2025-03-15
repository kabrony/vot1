#!/usr/bin/env python3
"""
VOT1 Unified Dashboard Application

A comprehensive dashboard that integrates file visualization, MCP tools,
AI chat with memory, and modular functionality blocks similar to Cursor AI.

Features:
- Unified interface for all VOT1 tools and modules
- Modular block-based UI with drag-and-drop capabilities
- Integrated AI chat with access to all tools
- File structure visualization with THREE.js
- MCP integration for distributed tools
- Advanced memory system integration with TRILOGY BRAIN
- Real-time performance monitoring
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("vot1_dashboard")

# Try to import required packages
try:
    from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
    from flask_socketio import SocketIO, emit
    flask_available = True
except ImportError:
    logger.warning("Flask or Flask-SocketIO not installed. Install with: pip install flask flask-socketio")
    flask_available = False

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import visualization components
try:
    from utils.file_structure_generator import FileStructureGenerator
    visualization_available = True
except ImportError:
    logger.warning("File structure visualization not available")
    visualization_available = False

# Import MCP components if available
try:
    from src.vot1.distributed.mcp_node_controller import MCPNodeController
    mcp_available = True
except ImportError:
    try:
        from vot1.distributed.mcp_node_controller import MCPNodeController
        mcp_available = True
    except ImportError:
        logger.warning("MCP components not available")
        mcp_available = False

# Import memory components if available
try:
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.memory import MemoryManager
    memory_available = True
except ImportError:
    try:
        from vot1.composio.memory_bridge import ComposioMemoryBridge
        from vot1.memory import MemoryManager
        memory_available = True
    except ImportError:
        logger.warning("Memory components not available")
        memory_available = False

# Try to import hybrid reasoning if available
try:
    from hybrid_reasoning import HybridReasoning
    hybrid_reasoning_available = True
except ImportError:
    logger.warning("Hybrid reasoning module not available")
    hybrid_reasoning_available = False

class Component:
    """Base class for dashboard components/blocks"""
    
    def __init__(self, component_id: str, name: str, type_: str, config: Dict[str, Any] = None):
        self.id = component_id
        self.name = name
        self.type = type_
        self.config = config or {}
        self.status = "initialized"
        self.last_updated = datetime.now().isoformat()
        self.data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "status": self.status,
            "last_updated": self.last_updated,
            "data": self.data
        }
    
    async def initialize(self) -> bool:
        """Initialize the component"""
        self.status = "active"
        self.last_updated = datetime.now().isoformat()
        return True
    
    async def update(self) -> Dict[str, Any]:
        """Update component data"""
        self.last_updated = datetime.now().isoformat()
        return self.data

class VisualizationComponent(Component):
    """File structure visualization component"""
    
    def __init__(self, component_id: str, name: str = "File Visualization", config: Dict[str, Any] = None):
        super().__init__(component_id, name, "visualization", config)
        
        defaults = {
            "project_root": ".",
            "output_dir": "output/structure",
            "max_depth": 10,
            "excluded_dirs": [
                ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
                "node_modules", "venv", ".venv", "env", "dist", "build"
            ],
            "excluded_files": [
                "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.exe", "*.min.js", "*.min.css"
            ],
            "include_hidden": False,
            "theme": "cyberpunk"
        }
        
        # Apply defaults for missing config values
        self.config = {**defaults, **(config or {})}
        
        # Initialize generator
        if visualization_available:
            self.generator = FileStructureGenerator(
                project_root=self.config["project_root"],
                output_dir=self.config["output_dir"],
                max_depth=self.config["max_depth"],
                excluded_dirs=self.config["excluded_dirs"],
                excluded_files=self.config["excluded_files"],
                include_hidden=self.config["include_hidden"]
            )
        else:
            self.generator = None
    
    async def initialize(self) -> bool:
        """Initialize the visualization component"""
        if not visualization_available or not self.generator:
            self.status = "error"
            self.data = {"error": "Visualization components not available"}
            return False
        
        # Create output directory
        os.makedirs(self.config["output_dir"], exist_ok=True)
        
        # Generate initial file structure
        await self.update()
        
        self.status = "active"
        return True
    
    async def update(self) -> Dict[str, Any]:
        """Update visualization data"""
        if not visualization_available or not self.generator:
            return {"error": "Visualization components not available"}
        
        try:
            # Generate file structure
            results = self.generator.generate_all()
            
            # Read the generated files
            with open(results["json_path"], "r") as f:
                structure = json.load(f)
            
            with open(results["markdown_path"], "r") as f:
                markdown = f.read()
            
            self.data = {
                "structure": structure,
                "markdown": markdown,
                "json_path": results["json_path"],
                "markdown_path": results["markdown_path"],
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_updated = datetime.now().isoformat()
            return self.data
            
        except Exception as e:
            logger.error(f"Error updating visualization: {str(e)}")
            self.status = "error"
            self.data = {"error": str(e)}
            return self.data

class MCPComponent(Component):
    """MCP integration component"""
    
    def __init__(self, component_id: str, name: str = "MCP Controller", config: Dict[str, Any] = None):
        super().__init__(component_id, name, "mcp", config)
        
        defaults = {
            "config_path": "config/mcp_config.json",
            "auto_start": False,
            "node_count": 1
        }
        
        # Apply defaults for missing config values
        self.config = {**defaults, **(config or {})}
        
        # Initialize MCP controller
        self.controller = None
        if mcp_available:
            try:
                self.controller = MCPNodeController(
                    config_path=self.config["config_path"]
                )
            except Exception as e:
                logger.error(f"Error initializing MCP controller: {str(e)}")
    
    async def initialize(self) -> bool:
        """Initialize the MCP component"""
        if not mcp_available or not self.controller:
            self.status = "error"
            self.data = {"error": "MCP components not available"}
            return False
        
        # Start nodes if auto_start is enabled
        if self.config["auto_start"]:
            try:
                for i in range(self.config["node_count"]):
                    node_id = f"node_{i}"
                    await self.controller.start_node(node_id)
                
                self.status = "active"
                return True
            except Exception as e:
                logger.error(f"Error starting MCP nodes: {str(e)}")
                self.status = "error"
                self.data = {"error": str(e)}
                return False
        
        self.status = "active"
        return True
    
    async def update(self) -> Dict[str, Any]:
        """Update MCP data"""
        if not mcp_available or not self.controller:
            return {"error": "MCP components not available"}
        
        try:
            # Get node status
            nodes = await self.controller.get_nodes()
            
            # Get memory stats if available
            memory_stats = await self.controller.get_memory_stats() if hasattr(self.controller, "get_memory_stats") else {}
            
            self.data = {
                "nodes": nodes,
                "memory_stats": memory_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_updated = datetime.now().isoformat()
            return self.data
            
        except Exception as e:
            logger.error(f"Error updating MCP data: {str(e)}")
            self.status = "error"
            self.data = {"error": str(e)}
            return self.data

class MemoryComponent(Component):
    """Memory system component"""
    
    def __init__(self, component_id: str, name: str = "TRILOGY BRAIN", config: Dict[str, Any] = None):
        super().__init__(component_id, name, "memory", config)
        
        defaults = {
            "memory_path": "memory/dashboard",
            "memory_limit": 1000,
            "enable_reflection": True
        }
        
        # Apply defaults for missing config values
        self.config = {**defaults, **(config or {})}
        
        # Initialize memory components
        self.memory_bridge = None
        self.memory_manager = None
        
        if memory_available:
            try:
                self.memory_bridge = ComposioMemoryBridge(
                    memory_path=self.config["memory_path"]
                )
                self.memory_manager = MemoryManager(
                    memory_bridge=self.memory_bridge,
                    enable_reflection=self.config["enable_reflection"]
                )
            except Exception as e:
                logger.error(f"Error initializing memory components: {str(e)}")
    
    async def initialize(self) -> bool:
        """Initialize the memory component"""
        if not memory_available or not self.memory_manager:
            self.status = "error"
            self.data = {"error": "Memory components not available"}
            return False
        
        try:
            # Initialize memory system
            await self.memory_manager.initialize()
            
            self.status = "active"
            return True
        except Exception as e:
            logger.error(f"Error initializing memory: {str(e)}")
            self.status = "error"
            self.data = {"error": str(e)}
            return False
    
    async def update(self) -> Dict[str, Any]:
        """Update memory data"""
        if not memory_available or not self.memory_manager:
            return {"error": "Memory components not available"}
        
        try:
            # Get memory stats
            stats = await self.memory_manager.get_stats()
            
            # Get recent memories
            recent_memories = await self.memory_manager.get_recent_memories(limit=10)
            
            self.data = {
                "stats": stats,
                "recent_memories": recent_memories,
                "timestamp": datetime.now().isoformat()
            }
            
            self.last_updated = datetime.now().isoformat()
            return self.data
            
        except Exception as e:
            logger.error(f"Error updating memory data: {str(e)}")
            self.status = "error"
            self.data = {"error": str(e)}
            return self.data
    
    async def store_memory(self, content: str, memory_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store a memory"""
        if not memory_available or not self.memory_manager:
            return {"error": "Memory components not available"}
        
        try:
            memory_id = await self.memory_manager.store_memory(
                content=content,
                memory_type=memory_type,
                metadata=metadata or {}
            )
            
            # Update component data
            await self.update()
            
            return memory_id
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return {"error": str(e)}

class AIAssistantComponent(Component):
    """AI assistant with chat and tool access"""
    
    def __init__(self, component_id: str, name: str = "AI Assistant", config: Dict[str, Any] = None):
        super().__init__(component_id, name, "ai_assistant", config)
        
        defaults = {
            "memory_enabled": True,
            "hybrid_thinking": True,
            "model": "claude-3-7-sonnet-20250219",
            "max_thinking_tokens": 120000,
            "tools_enabled": True
        }
        
        # Apply defaults for missing config values
        self.config = {**defaults, **(config or {})}
        
        # Initialize AI components
        self.hybrid_reasoning = None
        if hybrid_reasoning_available and self.config["hybrid_thinking"]:
            try:
                self.hybrid_reasoning = HybridReasoning()
            except Exception as e:
                logger.error(f"Error initializing hybrid reasoning: {str(e)}")
        
        # Chat history
        self.chat_history = []
    
    async def initialize(self) -> bool:
        """Initialize the AI assistant"""
        self.status = "active"
        return True
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and generate a response"""
        if not self.hybrid_reasoning and self.config["hybrid_thinking"]:
            return {
                "response": "AI assistant is not fully initialized. Hybrid thinking is not available.",
                "thinking": None,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Add message to history
            self.chat_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Prepare context
            full_context = {
                "chat_history": self.chat_history,
                "timestamp": datetime.now().isoformat()
            }
            
            if context:
                full_context.update(context)
            
            # Process with hybrid thinking if available
            if self.hybrid_reasoning and self.config["hybrid_thinking"]:
                result = await self.hybrid_reasoning.perform_hybrid_thinking(
                    prompt=message,
                    context=json.dumps(full_context),
                    domain="general",
                    max_thinking_tokens=self.config["max_thinking_tokens"]
                )
                
                response = result.get("solution", "No response generated")
                thinking = result.get("thinking", "No thinking process available")
            else:
                # Simple response without hybrid thinking
                response = f"Processed message: {message}"
                thinking = None
            
            # Add response to history
            self.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update component data
            self.data = {
                "chat_history": self.chat_history,
                "last_message": message,
                "last_response": response
            }
            
            self.last_updated = datetime.now().isoformat()
            
            return {
                "response": response,
                "thinking": thinking,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": f"Error: {str(e)}",
                "thinking": None,
                "timestamp": datetime.now().isoformat()
            }

class DashboardApp:
    """Unified dashboard application"""
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        components_config: Optional[Dict[str, Any]] = None,
        enable_memory: bool = True,
        enable_mcp: bool = True,
        enable_visualization: bool = True,
        enable_ai_assistant: bool = True,
        theme: str = "cyberpunk",
        debug: bool = False
    ):
        """
        Initialize the dashboard application.
        
        Args:
            host: Host for the web server
            port: Port for the web server
            components_config: Configuration for dashboard components
            enable_memory: Whether to enable memory integration
            enable_mcp: Whether to enable MCP integration
            enable_visualization: Whether to enable file visualization
            enable_ai_assistant: Whether to enable AI assistant
            theme: Dashboard theme (cyberpunk, light, dark)
            debug: Enable debug mode
        """
        self.host = host
        self.port = port
        self.theme = theme
        self.debug = debug
        
        # Component configuration
        self.components_config = components_config or {}
        
        # Feature flags
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp
        self.enable_visualization = enable_visualization
        self.enable_ai_assistant = enable_ai_assistant
        
        # Initialize components
        self.components = {}
        
        # Initialize Flask app
        self.app = None
        self.socketio = None
        
        if flask_available:
            self.initialize_flask_app()
    
    def initialize_components(self):
        """Initialize dashboard components"""
        # Generate component IDs
        component_id = lambda name: f"{name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Add visualization component
        if self.enable_visualization and visualization_available:
            vis_config = self.components_config.get("visualization", {})
            vis_component = VisualizationComponent(
                component_id=component_id("visualization"),
                name="File Structure Visualization",
                config=vis_config
            )
            self.components[vis_component.id] = vis_component
        
        # Add MCP component
        if self.enable_mcp and mcp_available:
            mcp_config = self.components_config.get("mcp", {})
            mcp_component = MCPComponent(
                component_id=component_id("mcp"),
                name="MCP Controller",
                config=mcp_config
            )
            self.components[mcp_component.id] = mcp_component
        
        # Add memory component
        if self.enable_memory and memory_available:
            memory_config = self.components_config.get("memory", {})
            memory_component = MemoryComponent(
                component_id=component_id("memory"),
                name="TRILOGY BRAIN",
                config=memory_config
            )
            self.components[memory_component.id] = memory_component
        
        # Add AI assistant component
        if self.enable_ai_assistant:
            ai_config = self.components_config.get("ai_assistant", {})
            ai_component = AIAssistantComponent(
                component_id=component_id("ai_assistant"),
                name="AI Assistant",
                config=ai_config
            )
            self.components[ai_component.id] = ai_component
    
    def initialize_flask_app(self):
        """Initialize Flask app and routes"""
        static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        # Create folders if they don't exist
        os.makedirs(static_folder, exist_ok=True)
        os.makedirs(template_folder, exist_ok=True)
        
        # Create Flask app and SocketIO
        self.app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize components
        self.initialize_components()
        
        # Set up routes
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard page"""
            return render_template(
                'index.html',
                title="VOT1 Dashboard",
                theme=self.theme,
                components=self.components
            )
        
        @self.app.route('/api/components')
        def get_components():
            """API endpoint to get all components"""
            return jsonify({
                'status': 'success',
                'components': {k: v.to_dict() for k, v in self.components.items()},
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/components/<component_id>')
        def get_component(component_id):
            """API endpoint to get a specific component"""
            if component_id not in self.components:
                return jsonify({
                    'status': 'error',
                    'error': f'Component {component_id} not found'
                }), 404
            
            return jsonify({
                'status': 'success',
                'component': self.components[component_id].to_dict(),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/visualization')
        def get_visualization():
            """API endpoint for visualization data"""
            # Find visualization component
            for component in self.components.values():
                if component.type == "visualization":
                    return jsonify({
                        'status': 'success',
                        'data': component.data,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return jsonify({
                'status': 'error',
                'error': 'Visualization component not found'
            }), 404
        
        @self.app.route('/api/mcp')
        def get_mcp():
            """API endpoint for MCP data"""
            # Find MCP component
            for component in self.components.values():
                if component.type == "mcp":
                    return jsonify({
                        'status': 'success',
                        'data': component.data,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return jsonify({
                'status': 'error',
                'error': 'MCP component not found'
            }), 404
        
        @self.app.route('/api/memory')
        def get_memory():
            """API endpoint for memory data"""
            # Find memory component
            for component in self.components.values():
                if component.type == "memory":
                    return jsonify({
                        'status': 'success',
                        'data': component.data,
                        'timestamp': datetime.now().isoformat()
                    })
            
            return jsonify({
                'status': 'error',
                'error': 'Memory component not found'
            }), 404
        
        # SocketIO events
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat message from client"""
            logger.info(f"Received message: {data}")
            
            # Find AI assistant component
            ai_component = None
            for component in self.components.values():
                if component.type == "ai_assistant":
                    ai_component = component
                    break
            
            if ai_component:
                # Process message asynchronously
                def process_message_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(
                        ai_component.process_message(
                            message=data.get('message', ''),
                            context=data.get('context', {})
                        )
                    )
                    
                    # Emit response back to client
                    self.socketio.emit('chat_response', result)
                    
                    loop.close()
                
                threading.Thread(target=process_message_async).start()
            else:
                # No AI assistant component found
                self.socketio.emit('chat_response', {
                    'response': 'AI assistant not available',
                    'thinking': None,
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('update_component')
        def handle_update_component(data):
            """Handle component update request"""
            component_id = data.get('component_id')
            
            if component_id in self.components:
                # Update component asynchronously
                def update_component_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    result = loop.run_until_complete(
                        self.components[component_id].update()
                    )
                    
                    # Emit updated component data
                    self.socketio.emit('component_updated', {
                        'component_id': component_id,
                        'data': result,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    loop.close()
                
                threading.Thread(target=update_component_async).start()
            else:
                # Component not found
                self.socketio.emit('error', {
                    'error': f'Component {component_id} not found',
                    'timestamp': datetime.now().isoformat()
                })
    
    async def initialize_async_components(self):
        """Initialize async components"""
        for component_id, component in self.components.items():
            try:
                await component.initialize()
                logger.info(f"Initialized component: {component.name} ({component_id})")
            except Exception as e:
                logger.error(f"Error initializing component {component_id}: {str(e)}")
    
    def start(self, open_browser: bool = True):
        """Start the dashboard application"""
        if not flask_available:
            logger.error("Flask not installed. Cannot start dashboard.")
            return
        
        if not self.app:
            self.initialize_flask_app()
        
        # Initialize components asynchronously
        def init_components_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            loop.run_until_complete(
                self.initialize_async_components()
            )
            
            loop.close()
        
        threading.Thread(target=init_components_async).start()
        
        # Open browser in a separate thread after a delay
        if open_browser:
            def open_browser_after_delay():
                time.sleep(1.5)  # Wait for server to start
                webbrowser.open(f"http://{self.host}:{self.port}")
            
            threading.Thread(target=open_browser_after_delay).start()
        
        logger.info(f"Starting dashboard at http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=self.debug)

def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(description="VOT1 Unified Dashboard")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--no-memory", action="store_true", help="Disable memory integration")
    parser.add_argument("--no-mcp", action="store_true", help="Disable MCP integration")
    parser.add_argument("--no-visualization", action="store_true", help="Disable file visualization")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI assistant")
    parser.add_argument("--theme", type=str, default="cyberpunk", choices=["cyberpunk", "light", "dark"], help="Dashboard theme")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Create dashboard app
    dashboard = DashboardApp(
        host=args.host,
        port=args.port,
        enable_memory=not args.no_memory,
        enable_mcp=not args.no_mcp,
        enable_visualization=not args.no_visualization,
        enable_ai_assistant=not args.no_ai,
        theme=args.theme,
        debug=args.debug
    )
    
    # Start dashboard
    dashboard.start(open_browser=not args.no_browser)

if __name__ == "__main__":
    main() 