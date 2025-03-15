"""
TRILOGY BRAIN - IPFS Node Integration Module

This module implements the integration between TRILOGY BRAIN and IPFS (InterPlanetary File System)
for distributed storage of memories and data. It provides a Python interface for storing,
retrieving, and managing content on the IPFS network, enabling truly distributed operation.

Key features:
- Content addressing using IPFS CIDs (Content Identifiers)
- Memory storage and retrieval via IPFS
- Node management and connection handling
- Integration with VOT1 principles engine for secure operations
- Support for pinning to ensure persistence

Author: Organix (VOT1 Project)
"""

import os
import json
import time
import base64
import hashlib
import logging
import requests
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# For IPFS HTTP API interactions
import httpx

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine

logger = get_logger(__name__)

# Constants
DEFAULT_IPFS_API_URL = "http://127.0.0.1:5001/api/v0"
DEFAULT_IPFS_GATEWAY_URL = "http://127.0.0.1:8080/ipfs"
DEFAULT_IPFS_BINARY = "ipfs"  # Assumes ipfs is in PATH
DEFAULT_MEMORY_NAMESPACE = "/vot1/memory"
DEFAULT_CONFIG_NAMESPACE = "/vot1/config"
DEFAULT_TIMEOUT = 60  # seconds

class IPFSNodeError(Exception):
    """Base exception for IPFS node operations."""
    pass

class IPFSConnectionError(IPFSNodeError):
    """Exception raised when connection to IPFS daemon fails."""
    pass

class IPFSContentError(IPFSNodeError):
    """Exception raised when content operations fail."""
    pass

class IPFSNode:
    """
    Provides an interface to interact with IPFS nodes for TRILOGY BRAIN memory operations.
    
    This class manages IPFS node connections, content operations, and memory management
    for the TRILOGY BRAIN distributed memory system. It can operate against a local IPFS
    daemon or remote IPFS API endpoints.
    """
    
    def __init__(self,
                 api_url: str = DEFAULT_IPFS_API_URL,
                 gateway_url: str = DEFAULT_IPFS_GATEWAY_URL,
                 ipfs_binary: str = DEFAULT_IPFS_BINARY,
                 memory_namespace: str = DEFAULT_MEMORY_NAMESPACE,
                 config_namespace: str = DEFAULT_CONFIG_NAMESPACE,
                 timeout: int = DEFAULT_TIMEOUT,
                 auto_start: bool = False,
                 principles_engine: Optional["CorePrinciplesEngine"] = None):
        """
        Initialize an IPFS node interface.
        
        Args:
            api_url: URL of the IPFS API
            gateway_url: URL of the IPFS Gateway
            ipfs_binary: Path to the IPFS binary
            memory_namespace: IPFS namespace for memory storage
            config_namespace: IPFS namespace for configuration
            timeout: Timeout for IPFS operations in seconds
            auto_start: Whether to start an IPFS daemon if none is running
            principles_engine: CorePrinciplesEngine instance for action verification
        """
        self.api_url = api_url
        self.gateway_url = gateway_url
        self.ipfs_binary = ipfs_binary
        self.memory_namespace = memory_namespace
        self.config_namespace = config_namespace
        self.timeout = timeout
        self.principles_engine = principles_engine
        self.node_info = None
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Initialize daemon
        if auto_start:
            self._ensure_daemon_running()
            
        logger.info(f"IPFS Node initialized with API: {api_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close client connections."""
        await self.client.aclose()
        logger.debug("IPFS Node client closed")
    
    def _ensure_daemon_running(self) -> bool:
        """
        Ensure that an IPFS daemon is running. If not, attempt to start one.
        
        Returns:
            True if daemon is running, False otherwise
        """
        try:
            response = requests.get(f"{self.api_url}/version", timeout=2)
            if response.status_code == 200:
                logger.debug("IPFS daemon already running")
                return True
        except requests.RequestException:
            logger.info("IPFS daemon not detected, attempting to start...")
            
        # Attempt to start daemon
        try:
            subprocess.Popen(
                [self.ipfs_binary, "daemon", "--enable-pubsub-experiment"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Wait for daemon to start
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    time.sleep(1)
                    response = requests.get(f"{self.api_url}/version", timeout=2)
                    if response.status_code == 200:
                        logger.info("IPFS daemon started successfully")
                        return True
                except requests.RequestException:
                    if attempt == max_attempts - 1:
                        logger.error("Failed to start IPFS daemon")
                        return False
                    continue
        except Exception as e:
            logger.error(f"Error starting IPFS daemon: {str(e)}")
            return False
        
        return False
    
    async def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about the connected IPFS node.
        
        Returns:
            Dictionary with node information
        """
        if self.node_info:
            return self.node_info
        
        try:
            id_res = await self._api_request("id")
            version_res = await self._api_request("version")
            
            self.node_info = {
                "id": id_res.get("ID"),
                "version": version_res.get("Version"),
                "protocol_version": id_res.get("ProtocolVersion"),
                "addresses": id_res.get("Addresses", []),
                "public_key": id_res.get("PublicKey"),
                "agent_version": id_res.get("AgentVersion"),
                "peer_count": len(await self._api_request("swarm/peers")),
            }
            
            return self.node_info
        except Exception as e:
            logger.error(f"Error getting node info: {str(e)}")
            raise IPFSConnectionError(f"Failed to get node info: {str(e)}")
    
    async def _api_request(self, path: str, method: str = "post", 
                          params: Optional[Dict[str, Any]] = None, 
                          files: Optional[Dict[str, Any]] = None,
                          stream: bool = False) -> Any:
        """
        Make a request to the IPFS API.
        
        Args:
            path: API endpoint path
            method: HTTP method to use
            params: Query parameters
            files: Files to upload
            stream: Whether to stream the response
            
        Returns:
            Response data as a dictionary or raw response
        """
        url = f"{self.api_url}/{path}"
        params = params or {}
        
        try:
            if method.lower() == "post":
                if files:
                    response = await self.client.post(
                        url, 
                        params=params, 
                        files=files,
                        timeout=self.timeout
                    )
                else:
                    response = await self.client.post(
                        url, 
                        params=params,
                        timeout=self.timeout
                    )
            elif method.lower() == "get":
                response = await self.client.get(
                    url, 
                    params=params,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if stream:
                return response
                
            response.raise_for_status()
            
            try:
                return response.json()
            except ValueError:
                return response.text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during IPFS API request to {path}: {str(e)}")
            raise IPFSNodeError(f"HTTP error: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Network error during IPFS API request to {path}: {str(e)}")
            raise IPFSConnectionError(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during IPFS API request to {path}: {str(e)}")
            raise IPFSNodeError(f"Unexpected error: {str(e)}")
    
    async def add_content(self, content: Union[str, bytes], 
                        memory_type: str = "raw",
                        metadata: Optional[Dict[str, Any]] = None,
                        pin: bool = True) -> Dict[str, Any]:
        """
        Add content to IPFS.
        
        Args:
            content: Content to add (string or bytes)
            memory_type: Type of memory (raw, semantic, episodic, etc.)
            metadata: Additional metadata to store with the content
            pin: Whether to pin the content to ensure persistence
            
        Returns:
            Dictionary with CID and other information
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "memory_operation",
                "operation": "store",
                "memory_type": memory_type
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Content storage rejected by principles engine: {reason}")
                raise IPFSContentError(f"Content storage rejected: {reason}")
        
        # Prepare content
        if isinstance(content, str):
            content_bytes = content.encode()
        else:
            content_bytes = content
        
        # Add metadata if provided
        if metadata:
            wrapped_content = {
                "content": base64.b64encode(content_bytes).decode(),
                "metadata": metadata,
                "memory_type": memory_type,
                "timestamp": time.time(),
                "version": "1.0"
            }
            content_bytes = json.dumps(wrapped_content).encode()
        
        # Add content to IPFS
        files = {
            "file": ("memory", content_bytes)
        }
        
        params = {}
        if pin:
            params["pin"] = "true"
        
        try:
            result = await self._api_request("add", params=params, files=files)
            if isinstance(result, list):
                result = result[0]
                
            cid = result.get("Hash")
            if not cid:
                raise IPFSContentError("Failed to get CID from IPFS response")
                
            # Store memory reference in namespace
            if memory_type:
                await self._add_to_namespace(cid, memory_type)
                
            return {
                "cid": cid,
                "size": result.get("Size"),
                "name": result.get("Name"),
                "memory_type": memory_type,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error adding content to IPFS: {str(e)}")
            raise IPFSContentError(f"Failed to add content: {str(e)}")
    
    async def get_content(self, cid: str, 
                         decode: bool = True,
                         extract_metadata: bool = True) -> Union[str, bytes, Dict[str, Any]]:
        """
        Get content from IPFS by CID.
        
        Args:
            cid: Content Identifier
            decode: Whether to decode bytes to string
            extract_metadata: Whether to extract and return metadata
            
        Returns:
            Content as string, bytes, or dictionary with content and metadata
        """
        try:
            response = await self._api_request(f"cat?arg={cid}", method="get", stream=True)
            content = await response.aread()
            
            # Check if it's JSON with metadata
            if extract_metadata:
                try:
                    data = json.loads(content)
                    if isinstance(data, dict) and "content" in data and "metadata" in data:
                        content_bytes = base64.b64decode(data["content"])
                        if decode:
                            return {
                                "content": content_bytes.decode(),
                                "metadata": data["metadata"],
                                "memory_type": data.get("memory_type"),
                                "timestamp": data.get("timestamp")
                            }
                        else:
                            return {
                                "content": content_bytes,
                                "metadata": data["metadata"],
                                "memory_type": data.get("memory_type"),
                                "timestamp": data.get("timestamp")
                            }
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                    # Not JSON or not our metadata format, continue with raw content
                    pass
            
            # Return raw content
            if decode:
                try:
                    return content.decode()
                except UnicodeDecodeError:
                    # If can't decode, return bytes
                    return content
            return content
        except Exception as e:
            logger.error(f"Error getting content from IPFS: {str(e)}")
            raise IPFSContentError(f"Failed to get content: {str(e)}")
    
    async def _add_to_namespace(self, cid: str, memory_type: str) -> bool:
        """
        Add a CID reference to a namespace in MFS (Mutable File System).
        
        Args:
            cid: Content Identifier
            memory_type: Type of memory for namespace organization
            
        Returns:
            Success status
        """
        namespace_path = f"{self.memory_namespace}/{memory_type}"
        
        try:
            # Ensure namespace directory exists
            try:
                await self._api_request("files/mkdir", params={
                    "arg": namespace_path,
                    "parents": "true"
                })
            except Exception:
                # Directory might already exist
                pass
            
            # Create entry in the namespace
            entry_name = f"{int(time.time())}_{cid}"
            entry_path = f"{namespace_path}/{entry_name}"
            
            # Write a reference file pointing to the CID
            reference = f"/ipfs/{cid}"
            await self._api_request("files/write", params={
                "arg": entry_path,
                "create": "true",
                "truncate": "true"
            }, files={
                "data": ("reference", reference.encode())
            })
            
            return True
        except Exception as e:
            logger.error(f"Error adding CID to namespace: {str(e)}")
            return False
    
    async def list_namespace(self, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List contents of a memory namespace.
        
        Args:
            memory_type: Type of memory to list, or None for all
            
        Returns:
            List of memory entries with CIDs and metadata
        """
        namespace_path = self.memory_namespace
        if memory_type:
            namespace_path = f"{namespace_path}/{memory_type}"
        
        try:
            entries = await self._api_request("files/ls", params={
                "arg": namespace_path,
                "long": "true"
            })
            
            results = []
            entries_data = entries.get("Entries", [])
            
            for entry in entries_data:
                if entry.get("Type") == 0:  # File
                    name = entry.get("Name", "")
                    if "_" in name:
                        timestamp, cid = name.split("_", 1)
                        results.append({
                            "cid": cid,
                            "timestamp": int(timestamp),
                            "memory_type": memory_type,
                            "size": entry.get("Size", 0)
                        })
            
            return results
        except Exception as e:
            logger.error(f"Error listing namespace: {str(e)}")
            return []
    
    async def pin_content(self, cid: str) -> bool:
        """
        Pin content to ensure it is not garbage collected.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Success status
        """
        try:
            result = await self._api_request("pin/add", params={"arg": cid})
            return "Pins" in result and cid in result["Pins"]
        except Exception as e:
            logger.error(f"Error pinning content: {str(e)}")
            return False
    
    async def unpin_content(self, cid: str) -> bool:
        """
        Unpin content allowing it to be garbage collected.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Success status
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "memory_operation",
                "operation": "unpin",
                "cid": cid
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Content unpinning rejected by principles engine: {reason}")
                return False
        
        try:
            result = await self._api_request("pin/rm", params={"arg": cid})
            return "Pins" in result and cid in result["Pins"]
        except Exception as e:
            logger.error(f"Error unpinning content: {str(e)}")
            return False
    
    async def list_pins(self) -> Dict[str, Any]:
        """
        List all pinned content.
        
        Returns:
            Dictionary mapping CIDs to pin types
        """
        try:
            result = await self._api_request("pin/ls")
            return result.get("Keys", {})
        except Exception as e:
            logger.error(f"Error listing pins: {str(e)}")
            return {}
    
    async def publish_to_pubsub(self, topic: str, message: Union[str, Dict[str, Any]]) -> bool:
        """
        Publish a message to an IPFS pubsub topic.
        
        Args:
            topic: PubSub topic name
            message: Message to publish (string or JSON-serializable dictionary)
            
        Returns:
            Success status
        """
        if isinstance(message, dict):
            message = json.dumps(message)
        
        try:
            await self._api_request("pubsub/pub", params={
                "arg": [topic, message]
            })
            return True
        except Exception as e:
            logger.error(f"Error publishing to pubsub: {str(e)}")
            return False
    
    async def connect_to_peer(self, peer_id: str) -> bool:
        """
        Connect to a specific IPFS peer.
        
        Args:
            peer_id: Peer ID to connect to
            
        Returns:
            Success status
        """
        try:
            result = await self._api_request("swarm/connect", params={"arg": peer_id})
            return "Strings" in result and len(result["Strings"]) > 0
        except Exception as e:
            logger.error(f"Error connecting to peer: {str(e)}")
            return False
    
    async def get_peers(self) -> List[Dict[str, Any]]:
        """
        Get a list of connected peers.
        
        Returns:
            List of peer information
        """
        try:
            result = await self._api_request("swarm/peers")
            return result.get("Peers", [])
        except Exception as e:
            logger.error(f"Error getting peers: {str(e)}")
            return []
    
    async def create_dag(self, data: Dict[str, Any]) -> str:
        """
        Create a DAG object with the given data.
        
        Args:
            data: Data to store in the DAG object
            
        Returns:
            CID of the created DAG object
        """
        try:
            data_json = json.dumps(data)
            result = await self._api_request("dag/put", params={"format": "json", "pin": "true"},
                                           files={"data": ("data", data_json.encode())})
            return result.get("Cid", {}).get("/")
        except Exception as e:
            logger.error(f"Error creating DAG: {str(e)}")
            raise IPFSContentError(f"Failed to create DAG: {str(e)}")
    
    async def get_dag(self, cid: str, path: str = "") -> Dict[str, Any]:
        """
        Get a DAG object by CID and optional path.
        
        Args:
            cid: Content Identifier
            path: Optional path within the DAG object
            
        Returns:
            DAG object data
        """
        arg = cid
        if path:
            arg = f"{cid}/{path}"
            
        try:
            result = await self._api_request("dag/get", params={"arg": arg})
            return result
        except Exception as e:
            logger.error(f"Error getting DAG: {str(e)}")
            raise IPFSContentError(f"Failed to get DAG: {str(e)}")
    
    @staticmethod
    def cid_to_base32(cid: str) -> str:
        """
        Convert a CID to base32 format for use in content path.
        
        Args:
            cid: Content Identifier
            
        Returns:
            Base32-encoded CID
        """
        try:
            result = subprocess.run(
                [DEFAULT_IPFS_BINARY, "cid", "format", "-v", "1", "-b", "base32", cid],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Error converting CID to base32: {str(e)}")
            return cid  # Return original as fallback


class IPFSNodePool:
    """
    Manages a pool of IPFS nodes for distributed operations.
    
    This class provides load balancing, redundancy, and coordination across
    multiple IPFS nodes, allowing TRILOGY BRAIN to maintain high availability
    and fault tolerance for memory operations.
    """
    
    def __init__(self, 
                 nodes: Optional[List[Dict[str, Any]]] = None,
                 discovery_enabled: bool = True,
                 max_nodes: int = 5,
                 principles_engine: Optional["CorePrinciplesEngine"] = None):
        """
        Initialize an IPFS node pool.
        
        Args:
            nodes: List of node configurations to connect to
            discovery_enabled: Whether to discover nodes automatically
            max_nodes: Maximum number of nodes to manage
            principles_engine: CorePrinciplesEngine instance for action verification
        """
        self.principles_engine = principles_engine
        self.max_nodes = max_nodes
        self.discovery_enabled = discovery_enabled
        self.nodes = []
        self.active_nodes = []
        
        # Initialize with provided nodes
        if nodes:
            for node_config in nodes:
                self._add_node(node_config)
                
        # Add default node if none provided
        if not self.nodes:
            self._add_node({
                "api_url": DEFAULT_IPFS_API_URL,
                "gateway_url": DEFAULT_IPFS_GATEWAY_URL
            })
            
        logger.info(f"IPFS Node Pool initialized with {len(self.nodes)} nodes")
    
    def _add_node(self, config: Dict[str, Any]) -> IPFSNode:
        """
        Add a node to the pool.
        
        Args:
            config: Node configuration
            
        Returns:
            Created IPFSNode instance
        """
        if len(self.nodes) >= self.max_nodes:
            logger.warning(f"Node pool full (max {self.max_nodes}), not adding new node")
            return None
            
        node = IPFSNode(
            api_url=config.get("api_url", DEFAULT_IPFS_API_URL),
            gateway_url=config.get("gateway_url", DEFAULT_IPFS_GATEWAY_URL),
            ipfs_binary=config.get("ipfs_binary", DEFAULT_IPFS_BINARY),
            principles_engine=self.principles_engine
        )
        
        self.nodes.append(node)
        self.active_nodes.append(node)
        return node
    
    async def close(self):
        """Close all node connections."""
        for node in self.nodes:
            await node.close()
        logger.debug("IPFS Node Pool closed")
    
    async def get_healthy_node(self) -> Optional[IPFSNode]:
        """
        Get a healthy node from the pool.
        
        Returns:
            A healthy IPFSNode instance or None if none available
        """
        if not self.active_nodes:
            await self._refresh_nodes()
            
        if not self.active_nodes:
            logger.error("No active IPFS nodes available")
            return None
            
        # Simple round-robin for now
        node = self.active_nodes[0]
        self.active_nodes = self.active_nodes[1:] + [node]
        return node
    
    async def _refresh_nodes(self):
        """Refresh the list of active nodes by checking their health."""
        self.active_nodes = []
        
        for node in self.nodes:
            try:
                # Simple health check
                await node.get_node_info()
                self.active_nodes.append(node)
            except Exception as e:
                logger.warning(f"Node {node.api_url} is unhealthy: {str(e)}")
    
    async def add_content(self, content: Union[str, bytes], 
                        memory_type: str = "raw",
                        metadata: Optional[Dict[str, Any]] = None,
                        redundancy: int = 1) -> List[Dict[str, Any]]:
        """
        Add content to IPFS with optional redundancy across nodes.
        
        Args:
            content: Content to add
            memory_type: Type of memory
            metadata: Additional metadata
            redundancy: Number of nodes to store on (for redundancy)
            
        Returns:
            List of results from each node
        """
        results = []
        node_count = min(redundancy, len(self.nodes))
        
        for _ in range(node_count):
            node = await self.get_healthy_node()
            if not node:
                continue
                
            try:
                result = await node.add_content(
                    content=content,
                    memory_type=memory_type,
                    metadata=metadata
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error adding content to node: {str(e)}")
        
        return results
    
    async def get_content(self, cid: str, 
                         decode: bool = True,
                         extract_metadata: bool = True) -> Union[str, bytes, Dict[str, Any]]:
        """
        Get content from any available node.
        
        Args:
            cid: Content Identifier
            decode: Whether to decode bytes to string
            extract_metadata: Whether to extract metadata
            
        Returns:
            Retrieved content
        """
        # Try nodes until content is retrieved
        for _ in range(len(self.nodes)):
            node = await self.get_healthy_node()
            if not node:
                continue
                
            try:
                return await node.get_content(
                    cid=cid,
                    decode=decode,
                    extract_metadata=extract_metadata
                )
            except Exception as e:
                logger.warning(f"Error getting content from node: {str(e)}")
                
        raise IPFSContentError(f"Failed to retrieve content with CID {cid} from any node")


# Example usage
async def example_usage():
    """Example usage of the IPFS node integration."""
    # Initialize node
    node = IPFSNode(auto_start=True)
    
    try:
        # Add content
        result = await node.add_content(
            content="This is a test memory for TRILOGY BRAIN",
            memory_type="test",
            metadata={"source": "example", "importance": 5}
        )
        
        print(f"Added content with CID: {result['cid']}")
        
        # Retrieve content
        content = await node.get_content(result["cid"])
        
        if isinstance(content, dict):
            print(f"Retrieved content: {content['content']}")
            print(f"Metadata: {content['metadata']}")
        else:
            print(f"Retrieved content: {content}")
        
        # List namespace
        entries = await node.list_namespace("test")
        print(f"Namespace entries: {entries}")
        
    finally:
        await node.close()


# Run example if executed directly
if __name__ == "__main__":
    asyncio.run(example_usage()) 