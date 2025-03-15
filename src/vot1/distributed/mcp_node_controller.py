"""
TRILOGY BRAIN - MCP Node Controller Module

This module implements the MCP (Model Control Protocol) Node Controller for TRILOGY BRAIN,
which manages distributed nodes, coordinates memory operations, and provides a unified
interface for controlling the distributed memory network. It acts as the orchestration
layer for TRILOGY BRAIN's continuous operation.

Key features:
- Node lifecycle management (start/stop/monitor)
- Coordination of memory operations across nodes
- Integration with Composio MCP for advanced AI capabilities
- Load balancing and fault tolerance
- Implementation of governance and consensus mechanisms

Author: Organix (VOT1 Project)
"""

import os
import json
import time
import uuid
import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine
from ..composio.client import ComposioClient
from .ipfs_node import IPFSNode, IPFSNodePool

logger = get_logger(__name__)

# Constants
DEFAULT_MCP_CONFIG_PATH = "config/mcp_config.json"
DEFAULT_NODE_REGISTRY_PATH = "registry/nodes.json"
DEFAULT_HEARTBEAT_INTERVAL = 30  # seconds
DEFAULT_MEMORY_SYNC_INTERVAL = 300  # seconds
DEFAULT_NODE_TIMEOUT = 120  # seconds
DEFAULT_MAX_RETRY_ATTEMPTS = 3

# Node types
NODE_TYPE_MEMORY = "memory"
NODE_TYPE_COMPUTE = "compute"
NODE_TYPE_COORDINATOR = "coordinator"
NODE_TYPE_VALIDATOR = "validator"
NODE_TYPE_GATEWAY = "gateway"

# Node statuses
NODE_STATUS_INITIALIZING = "initializing"
NODE_STATUS_ONLINE = "online"
NODE_STATUS_OFFLINE = "offline"
NODE_STATUS_ERROR = "error"
NODE_STATUS_SYNCING = "syncing"
NODE_STATUS_BACKUP = "backup"


class MCPNodeControllerError(Exception):
    """Base exception for MCP Node Controller operations."""
    pass


class NodeError(MCPNodeControllerError):
    """Exception raised when node operations fail."""
    pass


class Node:
    """
    Represents a node in the TRILOGY BRAIN distributed network.
    
    A node can be a memory node, compute node, coordinator node, etc.,
    and has various properties and capabilities depending on its type.
    """
    
    def __init__(self,
                 node_id: str = None,
                 node_type: str = NODE_TYPE_MEMORY,
                 host: str = "localhost",
                 port: int = 8000,
                 capabilities: Optional[List[str]] = None,
                 resources: Optional[Dict[str, Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 ipfs_config: Optional[Dict[str, Any]] = None,
                 principles_engine: Optional[CorePrinciplesEngine] = None):
        """
        Initialize a node.
        
        Args:
            node_id: Unique identifier for the node (generated if None)
            node_type: Type of node (memory, compute, coordinator, etc.)
            host: Hostname or IP address of the node
            port: Port number to connect to the node
            capabilities: List of node capabilities
            resources: Dict of node resources (CPU, memory, storage, etc.)
            metadata: Additional metadata for the node
            ipfs_config: IPFS configuration for the node
            principles_engine: CorePrinciplesEngine instance for action verification
        """
        self.node_id = node_id or f"{node_type}_{uuid.uuid4().hex[:8]}"
        self.node_type = node_type
        self.host = host
        self.port = port
        self.capabilities = capabilities or []
        self.resources = resources or {}
        self.metadata = metadata or {}
        self.ipfs_config = ipfs_config or {}
        self.principles_engine = principles_engine
        
        self.status = NODE_STATUS_INITIALIZING
        self.last_heartbeat = None
        self.last_sync = None
        self.error_count = 0
        self.ipfs_node = None
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        
        logger.info(f"Node {self.node_id} ({node_type}) initialized")
    
    async def start(self) -> bool:
        """
        Start the node and initialize its services.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize IPFS node if configured
            if self.ipfs_config:
                self.ipfs_node = IPFSNode(
                    api_url=self.ipfs_config.get("api_url"),
                    gateway_url=self.ipfs_config.get("gateway_url"),
                    auto_start=self.ipfs_config.get("auto_start", False),
                    principles_engine=self.principles_engine
                )
                
                # Test IPFS connection
                await self.ipfs_node.get_node_info()
            
            self.status = NODE_STATUS_ONLINE
            self.last_heartbeat = datetime.now()
            self.updated_at = datetime.now()
            logger.info(f"Node {self.node_id} started successfully")
            return True
        except Exception as e:
            self.status = NODE_STATUS_ERROR
            self.error_count += 1
            logger.error(f"Error starting node {self.node_id}: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the node and its services.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.ipfs_node:
                await self.ipfs_node.close()
                self.ipfs_node = None
                
            self.status = NODE_STATUS_OFFLINE
            self.updated_at = datetime.now()
            logger.info(f"Node {self.node_id} stopped")
            return True
        except Exception as e:
            self.status = NODE_STATUS_ERROR
            self.error_count += 1
            logger.error(f"Error stopping node {self.node_id}: {str(e)}")
            return False
    
    async def heartbeat(self) -> bool:
        """
        Send a heartbeat to check if the node is still alive.
        
        Returns:
            True if node is alive, False otherwise
        """
        try:
            if self.ipfs_node:
                # Simple health check
                await self.ipfs_node.get_node_info()
                
            self.last_heartbeat = datetime.now()
            if self.status == NODE_STATUS_ERROR:
                self.status = NODE_STATUS_ONLINE
                
            return True
        except Exception as e:
            logger.warning(f"Heartbeat failed for node {self.node_id}: {str(e)}")
            self.error_count += 1
            
            if self.error_count >= DEFAULT_MAX_RETRY_ATTEMPTS:
                self.status = NODE_STATUS_ERROR
                
            return False
    
    async def sync_memory(self) -> Dict[str, Any]:
        """
        Synchronize memory with other nodes in the network.
        
        Returns:
            Dict with sync statistics
        """
        if not self.ipfs_node or self.node_type != NODE_TYPE_MEMORY:
            return {"synced": False, "reason": "Node not configured for memory sync"}
            
        try:
            # Get local pins
            local_pins = await self.ipfs_node.list_pins()
            
            # Example sync logic - in a real implementation, this would
            # communicate with other nodes to synchronize content
            stats = {
                "local_pins": len(local_pins),
                "synced_pins": 0,
                "failed_pins": 0,
                "sync_time": 0
            }
            
            sync_start = time.time()
            
            # Placeholder for actual sync implementation
            # In a real system, this would:
            # 1. Discover peers and their content
            # 2. Compare with local content
            # 3. Request missing content
            # 4. Verify and store content
            
            stats["sync_time"] = time.time() - sync_start
            self.last_sync = datetime.now()
            
            logger.info(f"Memory sync completed for node {self.node_id}: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error syncing memory for node {self.node_id}: {str(e)}")
            return {"synced": False, "error": str(e)}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to dictionary for serialization.
        
        Returns:
            Dict representation of the node
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "host": self.host,
            "port": self.port,
            "capabilities": self.capabilities,
            "resources": self.resources,
            "metadata": self.metadata,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "error_count": self.error_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], 
                 principles_engine: Optional[CorePrinciplesEngine] = None) -> 'Node':
        """
        Create a node from a dictionary.
        
        Args:
            data: Dict representation of the node
            principles_engine: CorePrinciplesEngine instance
            
        Returns:
            Node instance
        """
        node = cls(
            node_id=data.get("node_id"),
            node_type=data.get("node_type", NODE_TYPE_MEMORY),
            host=data.get("host", "localhost"),
            port=data.get("port", 8000),
            capabilities=data.get("capabilities", []),
            resources=data.get("resources", {}),
            metadata=data.get("metadata", {}),
            ipfs_config=data.get("ipfs_config", {}),
            principles_engine=principles_engine
        )
        
        node.status = data.get("status", NODE_STATUS_INITIALIZING)
        
        if data.get("last_heartbeat"):
            node.last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
            
        if data.get("last_sync"):
            node.last_sync = datetime.fromisoformat(data["last_sync"])
            
        node.error_count = data.get("error_count", 0)
        
        if data.get("created_at"):
            node.created_at = datetime.fromisoformat(data["created_at"])
            
        if data.get("updated_at"):
            node.updated_at = datetime.fromisoformat(data["updated_at"])
            
        return node


class MCPNodeController:
    """
    Controller for managing distributed nodes in the TRILOGY BRAIN network.
    
    This class orchestrates the operation of multiple nodes, manages their lifecycle,
    and coordinates memory operations across the distributed network.
    """
    
    def __init__(self,
                 config_path: str = DEFAULT_MCP_CONFIG_PATH,
                 registry_path: str = DEFAULT_NODE_REGISTRY_PATH,
                 heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
                 memory_sync_interval: int = DEFAULT_MEMORY_SYNC_INTERVAL,
                 node_timeout: int = DEFAULT_NODE_TIMEOUT,
                 principles_engine: Optional[CorePrinciplesEngine] = None,
                 composio_client: Optional[ComposioClient] = None,
                 auto_start: bool = False):
        """
        Initialize the MCP Node Controller.
        
        Args:
            config_path: Path to the MCP configuration file
            registry_path: Path to the node registry file
            heartbeat_interval: Interval for node heartbeats in seconds
            memory_sync_interval: Interval for memory synchronization in seconds
            node_timeout: Timeout for considering nodes offline in seconds
            principles_engine: CorePrinciplesEngine instance for action verification
            composio_client: ComposioClient instance for AI operations
            auto_start: Whether to automatically start the controller
        """
        self.config_path = config_path
        self.registry_path = registry_path
        self.heartbeat_interval = heartbeat_interval
        self.memory_sync_interval = memory_sync_interval
        self.node_timeout = node_timeout
        self.principles_engine = principles_engine
        self.composio_client = composio_client
        
        self.nodes = {}
        self.running = False
        self.heartbeat_task = None
        self.memory_sync_task = None
        
        # Initialize
        self._load_config()
        self._load_registry()
        
        # Auto-start if configured
        if auto_start:
            asyncio.create_task(self.start())
            
        logger.info(f"MCP Node Controller initialized with {len(self.nodes)} nodes")
    
    def _load_config(self) -> None:
        """Load configuration from the config file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Create directory if it doesn't exist
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Create default config
                default_config = {
                    "heartbeat_interval": self.heartbeat_interval,
                    "memory_sync_interval": self.memory_sync_interval,
                    "node_timeout": self.node_timeout,
                    "default_node_types": [
                        NODE_TYPE_MEMORY,
                        NODE_TYPE_COMPUTE,
                        NODE_TYPE_COORDINATOR
                    ],
                    "auto_discovery": True,
                    "consensus_mechanism": "distributed_vote",
                    "version": "1.0.0"
                }
                
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    
                logger.info(f"Created default MCP config at {self.config_path}")
            else:
                # Load existing config
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                # Update settings from config
                self.heartbeat_interval = config.get("heartbeat_interval", self.heartbeat_interval)
                self.memory_sync_interval = config.get("memory_sync_interval", self.memory_sync_interval)
                self.node_timeout = config.get("node_timeout", self.node_timeout)
                
                logger.debug(f"Loaded MCP config from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading MCP config: {str(e)}")
    
    def _load_registry(self) -> None:
        """Load node registry from the registry file."""
        try:
            registry_file = Path(self.registry_path)
            if not registry_file.exists():
                # Create directory if it doesn't exist
                registry_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Create empty registry
                with open(registry_file, 'w') as f:
                    json.dump({"nodes": {}}, f, indent=2)
                    
                logger.info(f"Created empty node registry at {self.registry_path}")
            else:
                # Load existing registry
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
                    
                # Initialize nodes from registry
                for node_id, node_data in registry.get("nodes", {}).items():
                    self.nodes[node_id] = Node.from_dict(node_data, self.principles_engine)
                    
                logger.debug(f"Loaded {len(self.nodes)} nodes from registry")
        except Exception as e:
            logger.error(f"Error loading node registry: {str(e)}")
    
    def _save_registry(self) -> None:
        """Save node registry to the registry file."""
        try:
            registry_file = Path(self.registry_path)
            registry_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert nodes to dict
            nodes_dict = {
                node_id: node.to_dict() 
                for node_id, node in self.nodes.items()
            }
            
            # Save registry
            with open(registry_file, 'w') as f:
                json.dump({"nodes": nodes_dict}, f, indent=2)
                
            logger.debug(f"Saved {len(self.nodes)} nodes to registry")
        except Exception as e:
            logger.error(f"Error saving node registry: {str(e)}")
    
    async def start(self) -> bool:
        """
        Start the MCP Node Controller and all registered nodes.
        
        Returns:
            True if successful, False otherwise
        """
        if self.running:
            logger.warning("MCP Node Controller is already running")
            return True
            
        # Start monitoring tasks
        try:
            # Start nodes
            startup_results = await asyncio.gather(
                *[node.start() for node in self.nodes.values()],
                return_exceptions=True
            )
            
            # Start monitoring tasks
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            self.memory_sync_task = asyncio.create_task(self._memory_sync_monitor())
            
            self.running = True
            logger.info("MCP Node Controller started")
            
            # Save registry after starting
            self._save_registry()
            
            return True
        except Exception as e:
            logger.error(f"Error starting MCP Node Controller: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the MCP Node Controller and all nodes.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.running:
            logger.warning("MCP Node Controller is not running")
            return True
            
        # Stop monitoring tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
            
        if self.memory_sync_task:
            self.memory_sync_task.cancel()
            self.memory_sync_task = None
            
        # Stop nodes
        try:
            await asyncio.gather(
                *[node.stop() for node in self.nodes.values()],
                return_exceptions=True
            )
            
            self.running = False
            logger.info("MCP Node Controller stopped")
            
            # Save registry after stopping
            self._save_registry()
            
            return True
        except Exception as e:
            logger.error(f"Error stopping MCP Node Controller: {str(e)}")
            return False
    
    async def _heartbeat_monitor(self) -> None:
        """Background task for monitoring node heartbeats."""
        logger.info("Starting heartbeat monitor")
        
        while self.running:
            try:
                # Check each node
                offline_nodes = []
                
                for node_id, node in list(self.nodes.items()):
                    # Skip offline nodes
                    if node.status == NODE_STATUS_OFFLINE:
                        continue
                        
                    # Check if node is overdue for heartbeat
                    if (node.last_heartbeat and 
                        (datetime.now() - node.last_heartbeat).total_seconds() > self.node_timeout):
                        logger.warning(f"Node {node_id} missed heartbeat, marking as error")
                        node.status = NODE_STATUS_ERROR
                        offline_nodes.append(node_id)
                        continue
                        
                    # Send heartbeat
                    try:
                        await node.heartbeat()
                    except Exception as e:
                        logger.error(f"Error during heartbeat for node {node_id}: {str(e)}")
                
                # Save registry after updates
                self._save_registry()
                
                # Log offline nodes
                if offline_nodes:
                    logger.warning(f"Offline nodes: {offline_nodes}")
                    
                    # If using MCP, notify about offline nodes
                    if self.composio_client:
                        await self.composio_client.process_request(
                            system_message="You are monitoring the TRILOGY BRAIN node network. Please analyze the offline nodes and suggest recovery actions.",
                            user_message=f"The following nodes are offline or experiencing errors: {offline_nodes}. Please recommend actions to restore network health.",
                            temperature=0.3
                        )
                
            except asyncio.CancelledError:
                logger.info("Heartbeat monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {str(e)}")
                
            # Wait for next interval
            await asyncio.sleep(self.heartbeat_interval)
    
    async def _memory_sync_monitor(self) -> None:
        """Background task for monitoring memory synchronization."""
        logger.info("Starting memory sync monitor")
        
        while self.running:
            try:
                # Only sync memory nodes that are online
                memory_nodes = [
                    node for node in self.nodes.values()
                    if node.node_type == NODE_TYPE_MEMORY and node.status == NODE_STATUS_ONLINE
                ]
                
                if not memory_nodes:
                    logger.warning("No online memory nodes available for sync")
                else:
                    logger.info(f"Syncing {len(memory_nodes)} memory nodes")
                    
                    # Sync all memory nodes
                    for node in memory_nodes:
                        try:
                            node.status = NODE_STATUS_SYNCING
                            await node.sync_memory()
                            node.status = NODE_STATUS_ONLINE
                        except Exception as e:
                            logger.error(f"Error syncing memory for node {node.node_id}: {str(e)}")
                            node.status = NODE_STATUS_ERROR
                    
                    # Save registry after updates
                    self._save_registry()
                    
            except asyncio.CancelledError:
                logger.info("Memory sync monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in memory sync monitor: {str(e)}")
                
            # Wait for next interval
            await asyncio.sleep(self.memory_sync_interval)
    
    async def register_node(self, node: Node) -> bool:
        """
        Register a node with the controller.
        
        Args:
            node: Node to register
            
        Returns:
            True if successful, False otherwise
        """
        # Verify with principles engine if available
        if self.principles_engine:
            action = {
                "type": "node_operation",
                "operation": "register",
                "node_id": node.node_id,
                "node_type": node.node_type
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Node registration rejected: {reason}")
                return False
        
        # Check if node already exists
        if node.node_id in self.nodes:
            logger.warning(f"Node {node.node_id} already registered")
            return False
            
        # Register node
        self.nodes[node.node_id] = node
        
        # Start node if controller is running
        if self.running:
            await node.start()
            
        # Save registry after update
        self._save_registry()
        
        logger.info(f"Registered node {node.node_id} ({node.node_type})")
        return True
    
    async def unregister_node(self, node_id: str) -> bool:
        """
        Unregister a node from the controller.
        
        Args:
            node_id: ID of the node to unregister
            
        Returns:
            True if successful, False otherwise
        """
        # Verify with principles engine if available
        if self.principles_engine:
            action = {
                "type": "node_operation",
                "operation": "unregister",
                "node_id": node_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Node unregistration rejected: {reason}")
                return False
        
        # Check if node exists
        if node_id not in self.nodes:
            logger.warning(f"Node {node_id} not found")
            return False
            
        # Stop node if running
        node = self.nodes[node_id]
        if node.status != NODE_STATUS_OFFLINE:
            await node.stop()
            
        # Unregister node
        del self.nodes[node_id]
        
        # Save registry after update
        self._save_registry()
        
        logger.info(f"Unregistered node {node_id}")
        return True
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node to get
            
        Returns:
            Node if found, None otherwise
        """
        return self.nodes.get(node_id)
    
    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: Type of nodes to get
            
        Returns:
            List of nodes
        """
        return [node for node in self.nodes.values() if node.node_type == node_type]
    
    def get_healthy_nodes(self) -> List[Node]:
        """
        Get all healthy (online) nodes.
        
        Returns:
            List of healthy nodes
        """
        return [
            node for node in self.nodes.values() 
            if node.status == NODE_STATUS_ONLINE
        ]
    
    async def create_memory_node(self, 
                               host: str = "localhost",
                               port: int = 8000,
                               ipfs_config: Optional[Dict[str, Any]] = None,
                               capabilities: Optional[List[str]] = None) -> Optional[Node]:
        """
        Create and register a new memory node.
        
        Args:
            host: Hostname or IP address of the node
            port: Port number for the node
            ipfs_config: IPFS configuration for the node
            capabilities: List of node capabilities
            
        Returns:
            Created node if successful, None otherwise
        """
        # Default IPFS config if not provided
        if not ipfs_config:
            ipfs_config = {
                "api_url": DEFAULT_IPFS_API_URL,
                "gateway_url": DEFAULT_IPFS_GATEWAY_URL,
                "auto_start": True
            }
            
        # Create node
        node = Node(
            node_type=NODE_TYPE_MEMORY,
            host=host,
            port=port,
            capabilities=capabilities or ["store", "retrieve", "sync"],
            ipfs_config=ipfs_config,
            principles_engine=self.principles_engine
        )
        
        # Register node
        if await self.register_node(node):
            return node
        else:
            return None
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the node network.
        
        Returns:
            Dictionary with network statistics
        """
        total_nodes = len(self.nodes)
        online_nodes = len([n for n in self.nodes.values() if n.status == NODE_STATUS_ONLINE])
        offline_nodes = len([n for n in self.nodes.values() if n.status == NODE_STATUS_OFFLINE])
        error_nodes = len([n for n in self.nodes.values() if n.status == NODE_STATUS_ERROR])
        
        # Count by type
        node_types = {}
        for node in self.nodes.values():
            if node.node_type not in node_types:
                node_types[node.node_type] = 0
            node_types[node.node_type] += 1
            
        # Get memory stats from memory nodes
        memory_stats = {
            "total_memories": 0,
            "total_size": 0
        }
        
        # Example: in a real implementation, we would query each memory node
        # for its statistics and aggregate them
        
        return {
            "total_nodes": total_nodes,
            "online_nodes": online_nodes,
            "offline_nodes": offline_nodes,
            "error_nodes": error_nodes,
            "node_types": node_types,
            "memory_stats": memory_stats,
            "network_health": self._calculate_network_health(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_network_health(self) -> float:
        """
        Calculate the overall health of the node network (0.0 to 1.0).
        
        Returns:
            Health score from 0.0 to 1.0
        """
        if not self.nodes:
            return 0.0
            
        total_nodes = len(self.nodes)
        online_nodes = sum(1 for n in self.nodes.values() if n.status == NODE_STATUS_ONLINE)
        
        # Basic health calculation based on percentage of online nodes
        return online_nodes / total_nodes


# Example initialization for TRILOGY BRAIN network
async def initialize_mcp_network(principles_engine=None, composio_client=None):
    """
    Initialize the MCP Node Controller with a basic network for TRILOGY BRAIN.
    
    Args:
        principles_engine: CorePrinciplesEngine instance
        composio_client: ComposioClient instance
        
    Returns:
        Initialized MCPNodeController
    """
    controller = MCPNodeController(
        principles_engine=principles_engine,
        composio_client=composio_client,
        auto_start=False
    )
    
    # Create initial nodes if none exist
    if not controller.nodes:
        # Create a coordinator node
        await controller.register_node(Node(
            node_type=NODE_TYPE_COORDINATOR,
            host="localhost",
            port=8000,
            principles_engine=principles_engine
        ))
        
        # Create memory nodes
        for i in range(3):
            await controller.create_memory_node(
                host="localhost",
                port=8001 + i
            )
            
        # Create compute nodes
        for i in range(2):
            await controller.register_node(Node(
                node_type=NODE_TYPE_COMPUTE,
                host="localhost",
                port=9001 + i,
                capabilities=["inference", "reasoning", "planning"],
                principles_engine=principles_engine
            ))
            
        logger.info(f"Initialized MCP network with {len(controller.nodes)} nodes")
        
    # Start the controller
    await controller.start()
    
    return controller


# Run example if executed directly
if __name__ == "__main__":
    async def main():
        controller = await initialize_mcp_network()
        
        try:
            # Display network stats
            stats = await controller.get_network_stats()
            print(f"Network stats: {json.dumps(stats, indent=2)}")
            
            # Wait for a while to observe the network
            await asyncio.sleep(60)
        finally:
            await controller.stop()
            
    asyncio.run(main()) 