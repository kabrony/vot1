import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
import threading

logger = logging.getLogger(__name__)

class AgentState:
    """Represents the state of an agent in the ecosystem."""
    
    def __init__(self, agent_id: str, name: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.last_activity = time.time()
        self.memory = {}
        self.connections = set()
        self.tasks = []
        self.messages = []
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = time.time()
    
    def add_memory(self, key: str, value: Any):
        """Add an item to agent's memory."""
        self.memory[key] = value
    
    def get_memory(self, key: str) -> Any:
        """Get an item from agent's memory."""
        return self.memory.get(key)
    
    def add_message(self, from_agent: str, content: Dict[str, Any]):
        """Add a message to the agent's message queue."""
        message = {
            "id": str(uuid.uuid4()),
            "from": from_agent,
            "to": self.agent_id,
            "content": content,
            "timestamp": time.time()
        }
        self.messages.append(message)
        return message["id"]
    
    def pop_messages(self) -> List[Dict[str, Any]]:
        """Get and clear all messages for this agent."""
        messages = self.messages.copy()
        self.messages = []
        return messages


class MCPOrchestrator:
    """
    Orchestrates multiple agents and facilitates communication between them.
    """
    
    def __init__(self, bridge):
        """Initialize the orchestrator with a reference to the MCP bridge."""
        self.bridge = bridge
        self.agents = {}  # agent_id -> AgentState
        self.callbacks = {}  # event_type -> [callbacks]
        self.memory_store = {}  # shared memory between agents
        self.logger = logging.getLogger(__name__)
        self.lock = threading.RLock()  # For thread-safe operations
    
    def register_agent(self, name: str, capabilities: List[str]) -> str:
        """
        Register a new agent with the orchestrator.
        
        Args:
            name: Name of the agent
            capabilities: List of capabilities the agent has
            
        Returns:
            Agent ID
        """
        with self.lock:
            agent_id = str(uuid.uuid4())
            self.agents[agent_id] = AgentState(agent_id, name, capabilities)
            self.logger.info(f"Registered agent: {name} (ID: {agent_id})")
            
            # Trigger event
            self._trigger_event("agent_registered", {
                "agent_id": agent_id,
                "name": name,
                "capabilities": capabilities
            })
            
            return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the orchestrator.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            if agent_id not in self.agents:
                return False
            
            # Get the agent state
            agent = self.agents[agent_id]
            
            # Remove all connections
            for connected_id in list(agent.connections):
                self.disconnect_agents(agent_id, connected_id)
            
            # Remove the agent
            del self.agents[agent_id]
            
            # Trigger event
            self._trigger_event("agent_unregistered", {
                "agent_id": agent_id
            })
            
            return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID."""
        return self.agents.get(agent_id)
    
    # Added for compatibility with server_agents.py
    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Get agent state by ID (alias for get_agent)."""
        return self.get_agent(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents."""
        return [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "capabilities": agent.capabilities,
                "last_activity": agent.last_activity
            }
            for agent in self.agents.values()
        ]
    
    def connect_agents(self, agent_id_1: str, agent_id_2: str) -> bool:
        """Create a connection between two agents."""
        with self.lock:
            if agent_id_1 not in self.agents or agent_id_2 not in self.agents:
                return False
                
            # Establish bi-directional connection
            self.agents[agent_id_1].connections.add(agent_id_2)
            self.agents[agent_id_2].connections.add(agent_id_1)
            
            # Trigger event
            self._trigger_event("agents_connected", {
                "agent_id_1": agent_id_1,
                "agent_id_2": agent_id_2
            })
            
            return True
    
    def disconnect_agents(self, agent_id_1: str, agent_id_2: str) -> bool:
        """Remove a connection between two agents."""
        with self.lock:
            if agent_id_1 not in self.agents or agent_id_2 not in self.agents:
                return False
                
            # Remove bi-directional connection
            self.agents[agent_id_1].connections.discard(agent_id_2)
            self.agents[agent_id_2].connections.discard(agent_id_1)
            
            # Trigger event
            self._trigger_event("agents_disconnected", {
                "agent_id_1": agent_id_1,
                "agent_id_2": agent_id_2
            })
            
            return True
    
    def send_message(self, from_agent_id: str, to_agent_id: str, 
                     content: Dict[str, Any]) -> Optional[str]:
        """Send a message from one agent to another."""
        with self.lock:
            if to_agent_id not in self.agents:
                return None
                
            # For system messages or broadcasts, we don't require a connection
            if from_agent_id != "system" and from_agent_id != "user":
                if from_agent_id not in self.agents:
                    return None
                    
                # Verify connection exists
                if to_agent_id not in self.agents[from_agent_id].connections:
                    self.logger.warning(f"No connection between {from_agent_id} and {to_agent_id}")
                    return None
                
            # Add message to recipient's queue
            message_id = self.agents[to_agent_id].add_message(from_agent_id, content)
            self.logger.debug(f"Message sent from {from_agent_id} to {to_agent_id}: {message_id}")
            
            # Trigger callback
            self._trigger_event("message", {
                "from_agent_id": from_agent_id,
                "to_agent_id": to_agent_id,
                "message_id": message_id,
                "content": content
            })
            
            return message_id
    
    def broadcast_message(self, from_agent_id: str, content: Dict[str, Any]) -> List[str]:
        """
        Broadcast a message to all connected agents.
        
        Args:
            from_agent_id: ID of the agent sending the message
            content: Message content
            
        Returns:
            List of message IDs
        """
        with self.lock:
            if from_agent_id not in self.agents:
                return []
                
            message_ids = []
            for connected_id in self.agents[from_agent_id].connections:
                message_id = self.send_message(from_agent_id, connected_id, content)
                if message_id:
                    message_ids.append(message_id)
                    
            return message_ids
    
    def get_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all messages for an agent."""
        if agent_id not in self.agents:
            return []
        return self.agents[agent_id].pop_messages()
    
    def call_mcp_function(self, agent_id: str, function_name: str, 
                          params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP function on behalf of an agent.
        
        Args:
            agent_id: ID of the agent making the call
            function_name: MCP function name
            params: Function parameters
            
        Returns:
            Function result
        """
        if agent_id not in self.agents:
            return {"successful": False, "error": "Agent not found"}
            
        # Record the activity
        self.agents[agent_id].update_activity()
        
        # Log the function call
        self.logger.info(f"Agent {agent_id} ({self.agents[agent_id].name}) calling {function_name}")
        
        # Call the MCP function
        result = self.bridge.call_function(function_name, params)
        
        # Trigger callback
        self._trigger_event("function_call", {
            "agent_id": agent_id,
            "function_name": function_name,
            "params": params,
            "result": result
        })
        
        return result
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type."""
        with self.lock:
            if event_type not in self.callbacks:
                self.callbacks[event_type] = []
            self.callbacks[event_type].append(callback)
    
    def _trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger all callbacks for an event type."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    self.logger.error(f"Error in callback for {event_type}: {e}")
    
    def set_shared_memory(self, key: str, value: Any, tags: List[str] = None):
        """Set a value in the shared memory store."""
        with self.lock:
            stored_value = value
            # Add tags if provided
            if tags:
                if isinstance(value, dict):
                    # If value is already a dict, add tags to it
                    stored_value = value.copy()
                    stored_value["tags"] = tags
                else:
                    # Wrap the value in a dict with tags
                    stored_value = {
                        "value": value,
                        "tags": tags
                    }
                    
            self.memory_store[key] = stored_value
            
            # Trigger event
            self._trigger_event("memory_updated", {
                "key": key,
                "action": "set"
            })
    
    def get_shared_memory(self, key: str) -> Any:
        """Get a value from the shared memory store."""
        return self.memory_store.get(key)
    
    def delete_shared_memory(self, key: str) -> bool:
        """Delete a value from the shared memory store."""
        with self.lock:
            if key not in self.memory_store:
                return False
                
            del self.memory_store[key]
            
            # Trigger event
            self._trigger_event("memory_updated", {
                "key": key,
                "action": "delete"
            })
            
            return True
    
    def list_shared_memory(self) -> List[str]:
        """List all keys in the shared memory store."""
        return list(self.memory_store.keys())
    
    # Direct memory access methods for server_agents.py compatibility
    def store_memory(self, key: str, value: Any, tags: List[str] = None):
        """Store a memory (alias for set_shared_memory)."""
        self.set_shared_memory(key, value, tags)
        return {"key": key, "status": "success"}
    
    def retrieve_memory(self, key: str) -> Any:
        """Retrieve a memory (alias for get_shared_memory)."""
        return self.get_shared_memory(key)
    
    def search_memories(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        results = []
        for key, value in self.memory_store.items():
            if isinstance(value, dict) and "tags" in value:
                memory_tags = value["tags"]
                if any(tag in memory_tags for tag in tags):
                    results.append({
                        "key": key,
                        "value": value
                    })
                    
                    if len(results) >= limit:
                        break
        return results
    
    def handle_internal_function(self, function_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle internal function calls.
        
        Args:
            function_name: Name of the internal function
            params: Parameters for the function
            
        Returns:
            Result of the function call
        """
        # Check if this is a memory-related function
        if function_name.startswith("memory_"):
            # Extract the actual function name
            memory_function = function_name[len("memory_"):]
            
            # Call the appropriate memory function
            if memory_function == "store":
                if "key" not in params or "value" not in params:
                    return {
                        "successful": False,
                        "error": "Missing required parameters: key, value"
                    }
                
                tags = params.get("tags", [])
                self.set_shared_memory(params["key"], params["value"], tags)
                return {
                    "successful": True,
                    "message": f"Memory stored with key: {params['key']}"
                }
                
            elif memory_function == "retrieve":
                if "key" not in params:
                    return {
                        "successful": False,
                        "error": "Missing required parameter: key"
                    }
                
                value = self.get_shared_memory(params["key"])
                if value is None:
                    return {
                        "successful": False,
                        "error": f"No memory found with key: {params['key']}"
                    }
                
                return {
                    "successful": True,
                    "value": value
                }
                
            elif memory_function == "search":
                tags = params.get("tags", [])
                limit = params.get("limit", 10)
                
                results = self.search_memories(tags, limit)
                return {
                    "successful": True,
                    "results": results
                }
        
        # If we have a bridge, try to use it for internal functions
        if self.bridge and hasattr(self.bridge, 'call_internal_function'):
            # Split the function name into tool and function parts
            if "_" in function_name:
                parts = function_name.split("_", 1)
                if len(parts) == 2:
                    tool_name, tool_function = parts
                    return self.bridge.call_internal_function(tool_name, tool_function, params)
        
        # If we get here, the function is not supported
        return {
            "successful": False,
            "error": f"Unsupported internal function: {function_name}"
        } 