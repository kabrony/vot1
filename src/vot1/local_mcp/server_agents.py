import json
import logging
import threading
from flask import Blueprint, jsonify, request
from .orchestrator import MCPOrchestrator
from .agent import FeedbackAgent
from .development_agent import DevelopmentAgent

logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None
agents = {}

def create_agent_blueprint(mcp_bridge=None):
    """Create a Flask Blueprint for agent-related endpoints."""
    global orchestrator
    
    if orchestrator is None:
        orchestrator = MCPOrchestrator(mcp_bridge)
    
    agent_bp = Blueprint('agent', __name__)
    
    @agent_bp.route('/agents', methods=['GET'])
    def list_agents():
        """List all registered agents."""
        try:
            agent_list = orchestrator.list_agents()
            return jsonify({
                "status": "success",
                "agents": agent_list
            }), 200
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents', methods=['POST'])
    def create_agent():
        """Create a new agent."""
        try:
            data = request.json
            agent_name = data.get('name')
            capabilities = data.get('capabilities', [])
            
            if not agent_name:
                return jsonify({
                    "status": "error",
                    "message": "Agent name is required"
                }), 400
            
            # Determine the agent class based on capabilities
            agent_class = FeedbackAgent
            if "code_generation" in capabilities or "code_review" in capabilities or agent_name == "DevelopmentAgent":
                agent_class = DevelopmentAgent
                logger.info(f"Creating a DevelopmentAgent instance for {agent_name}")
            
            # Create the agent - handle DevelopmentAgent differently
            if agent_class == DevelopmentAgent:
                agent = agent_class(
                    orchestrator=orchestrator,
                    name=agent_name
                )
            else:
                agent = agent_class(
                    orchestrator=orchestrator,
                    name=agent_name,
                    capabilities=capabilities
                )
            
            # Store the agent in the global registry
            agents[agent.id] = agent
            
            logger.info(f"Created agent: {agent.name} ({agent.id}) with capabilities: {agent.capabilities}")
            
            return jsonify({
                "status": "success",
                "agent": {
                    "id": agent.id,
                    "name": agent.name,
                    "capabilities": agent.capabilities
                },
                "agent_id": agent.id  # For compatibility
            }), 201
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>', methods=['GET'])
    def get_agent(agent_id):
        """Get agent details."""
        try:
            # Using get_agent method instead of get_agent_state
            agent_state = orchestrator.get_agent(agent_id)
            if agent_state:
                return jsonify({
                    "status": "success",
                    "agent": {
                        "id": agent_id,
                        "name": agent_state.name,
                        "last_activity": agent_state.last_activity,
                        "connections": list(agent_state.connections),
                        "capabilities": agent_state.capabilities if hasattr(agent_state, 'capabilities') else []
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Agent {agent_id} not found"
                }), 404
        except Exception as e:
            logger.error(f"Error getting agent {agent_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>', methods=['DELETE'])
    def delete_agent(agent_id):
        """Delete an agent."""
        try:
            if agent_id in agents:
                agent = agents[agent_id]
                # Stop the agent
                agent.stop()
                # Unregister from orchestrator
                orchestrator.unregister_agent(agent_id)
                # Remove from the global dictionary
                del agents[agent_id]
                
                return jsonify({
                    "status": "success",
                    "message": f"Agent {agent_id} deleted"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Agent {agent_id} not found"
                }), 404
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>/connect', methods=['POST'])
    def connect_agents(agent_id):
        """Connect an agent to another agent."""
        try:
            data = request.json
            target_agent_id = data.get('target_agent_id')
            
            if not target_agent_id:
                return jsonify({
                    "status": "error",
                    "message": "Target agent ID is required"
                }), 400
            
            # Connect the agents
            success = orchestrator.connect_agents(agent_id, target_agent_id)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Agent {agent_id} connected to {target_agent_id}"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to connect agents {agent_id} and {target_agent_id}"
                }), 400
        except Exception as e:
            logger.error(f"Error connecting agents: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>/disconnect', methods=['POST'])
    def disconnect_agents(agent_id):
        """Disconnect an agent from another agent."""
        try:
            data = request.json
            target_agent_id = data.get('target_agent_id')
            
            if not target_agent_id:
                return jsonify({
                    "status": "error",
                    "message": "Target agent ID is required"
                }), 400
            
            # Disconnect the agents
            success = orchestrator.disconnect_agents(agent_id, target_agent_id)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Agent {agent_id} disconnected from {target_agent_id}"
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to disconnect agents {agent_id} and {target_agent_id}"
                }), 400
        except Exception as e:
            logger.error(f"Error disconnecting agents: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>/message', methods=['POST'])
    def send_message(agent_id):
        """Send a message to an agent."""
        try:
            data = request.json
            content = data.get('content')
            from_agent_id = data.get('from_agent_id', 'user')
            
            if not content:
                return jsonify({
                    "status": "error",
                    "message": "Message content is required"
                }), 400
            
            # Send the message
            message_id = orchestrator.send_message(from_agent_id, agent_id, content)
            
            if message_id:
                return jsonify({
                    "status": "success",
                    "message": f"Message sent to agent {agent_id}",
                    "message_id": message_id
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to send message to agent {agent_id}"
                }), 400
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>/task', methods=['POST'])
    def add_task(agent_id):
        """Add a task to an agent's queue."""
        try:
            data = request.json
            task_type = data.get('task_type')
            task_data = data.get('task_data', {})
            
            if not task_type:
                return jsonify({
                    "status": "error",
                    "message": "Task type is required"
                }), 400
            
            # Get the agent
            agent = agents.get(agent_id)
            if not agent:
                agent_state = orchestrator.get_agent(agent_id)
                if not agent_state:
                    return jsonify({
                        "status": "error",
                        "message": f"Agent {agent_id} not found"
                    }), 404
                
                # This is a fallback for agents not in our registry
                return jsonify({
                    "status": "error",
                    "message": f"Agent {agent_id} exists but is not accessible for tasks"
                }), 400
            
            # Check if this is a development-specific task
            dev_tasks = [
                "generate_code", "review_code", "analyze_repository", 
                "generate_documentation", "suggest_improvements", 
                "analyze_dependencies", "create_tests", "analyze_pr"
            ]
            
            if task_type in dev_tasks and not isinstance(agent, DevelopmentAgent):
                logger.warning(f"Task {task_type} requires a DevelopmentAgent, but agent {agent_id} is a {type(agent).__name__}")
                
                # Try to find a DevelopmentAgent
                dev_agent = next((a for a in agents.values() if isinstance(a, DevelopmentAgent)), None)
                if dev_agent:
                    logger.info(f"Redirecting task {task_type} to DevelopmentAgent {dev_agent.id}")
                    agent = dev_agent
                    agent_id = dev_agent.id
                else:
                    logger.error(f"No DevelopmentAgent available for task {task_type}")
            
            # Add the task to the agent's queue
            task_id = agent.add_task(task_type, task_data)
            
            logger.info(f"Added task {task_type} (ID: {task_id}) to agent {agent.name} ({agent_id})")
            
            return jsonify({
                "status": "success",
                "task_id": task_id,
                "agent_id": agent_id
            }), 201
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/agents/<agent_id>/response', methods=['GET'])
    def get_responses(agent_id):
        """Get responses from an agent."""
        try:
            if agent_id not in agents:
                return jsonify({
                    "status": "error",
                    "message": f"Agent {agent_id} not found"
                }), 404
            
            # Get responses from the agent
            agent = agents[agent_id]
            responses = agent.get_responses()
            
            return jsonify({
                "status": "success",
                "responses": responses
            }), 200
        except Exception as e:
            logger.error(f"Error getting responses from agent {agent_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    # Memory routes
    @agent_bp.route('/memory', methods=['POST'])
    def store_memory():
        """Store a memory in the shared memory."""
        try:
            data = request.json
            key = data.get('key')
            value = data.get('value')
            tags = data.get('tags', [])
            
            if not key:
                return jsonify({
                    "status": "error",
                    "message": "Memory key is required"
                }), 400
                
            if value is None:
                return jsonify({
                    "status": "error",
                    "message": "Memory value is required"
                }), 400
            
            # Store the memory
            orchestrator.set_shared_memory(key, value, tags)
            
            return jsonify({
                "status": "success",
                "message": f"Memory stored with key {key}"
            }), 200
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/memory/<key>', methods=['GET'])
    def get_memory(key):
        """Get a memory from the shared memory."""
        try:
            # Get the memory
            value = orchestrator.get_shared_memory(key)
            
            if value is None:
                return jsonify({
                    "status": "error",
                    "message": f"Memory with key {key} not found"
                }), 404
            
            return jsonify({
                "status": "success",
                "key": key,
                "value": value
            }), 200
        except Exception as e:
            logger.error(f"Error getting memory {key}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @agent_bp.route('/memory/search', methods=['POST'])
    def search_memories():
        """Search memories by tags."""
        try:
            data = request.json
            tags = data.get('tags', [])
            limit = data.get('limit', 10)
            
            if not tags:
                return jsonify({
                    "status": "error",
                    "message": "Tags are required for search"
                }), 400
            
            # Search for memories by tags
            results = orchestrator.search_memories(tags, limit)
            
            return jsonify({
                "status": "success",
                "results": results
            }), 200
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    return agent_bp

def register_internal_tools(mcp_bridge, orchestrator):
    """Register internal tool handlers with the MCP bridge."""
    # Memory tools
    mcp_bridge.register_tool_handler("memory", "store_memory", 
                                    lambda params: orchestrator.set_shared_memory(
                                        params.get("key"), 
                                        params.get("value"), 
                                        params.get("tags", [])
                                    ))
    
    mcp_bridge.register_tool_handler("memory", "retrieve_memory", 
                                    lambda params: orchestrator.get_shared_memory(
                                        params.get("key")
                                    ))
    
    mcp_bridge.register_tool_handler("memory", "search_memories", 
                                    lambda params: orchestrator.search_memories(
                                        params.get("tags"), 
                                        params.get("limit", 10)
                                    ))
    
    # Agent tools
    mcp_bridge.register_tool_handler("agent", "list_agents", 
                                    lambda params: orchestrator.list_agents())
    
    mcp_bridge.register_tool_handler("agent", "send_task", 
                                    lambda params: send_task_to_agent(
                                        params.get("agent_id"),
                                        params.get("task_type"),
                                        params.get("task_data", {})
                                    ))

def send_task_to_agent(agent_id, task_type, task_data):
    """Send a task to an agent and return the result."""
    global agents
    
    if agent_id not in agents:
        return {"error": f"Agent {agent_id} not found"}
    
    agent = agents[agent_id]
    task_id = agent.add_task(task_type, task_data)
    
    # Return immediately with the task ID
    return {"task_id": task_id}

def start_agent_ecosystem(mcp_bridge):
    """Start the agent ecosystem with default agents."""
    global orchestrator, agents
    
    if orchestrator is None:
        orchestrator = MCPOrchestrator(mcp_bridge)
    
    # Register internal tools
    register_internal_tools(mcp_bridge, orchestrator)
    
    # Create default agents
    default_agents = [
        {
            "name": "SearchAgent",
            "capabilities": ["search", "perplexity"],
            "agent_class": FeedbackAgent
        },
        {
            "name": "RepositoryAgent",
            "capabilities": ["github", "code_analysis"],
            "agent_class": FeedbackAgent
        },
        {
            "name": "WebAgent",
            "capabilities": ["web_scraping", "firecrawl"],
            "agent_class": FeedbackAgent
        },
        {
            "name": "AnalysisAgent",
            "capabilities": ["data_analysis", "memory"],
            "agent_class": FeedbackAgent
        },
        {
            "name": "DevelopmentAgent",
            "capabilities": [
                "code_generation",
                "code_review",
                "repository_analysis",
                "documentation",
                "testing",
                "debugging",
                "dependency_management",
                "github"
            ],
            "agent_class": DevelopmentAgent
        }
    ]
    
    for agent_config in default_agents:
        agent_class = agent_config.get("agent_class", FeedbackAgent)
        
        # Handle DevelopmentAgent differently
        if agent_class == DevelopmentAgent:
            agent = agent_class(
                orchestrator=orchestrator,
                name=agent_config["name"]
            )
        else:
            agent = agent_class(
                orchestrator=orchestrator,
                name=agent_config["name"],
                capabilities=agent_config["capabilities"]
            )
            
        agents[agent.id] = agent
        logger.info(f"Created agent: {agent.name} ({agent.id}) with capabilities: {agent.capabilities}")
    
    # Connect all agents in a network
    agent_ids = list(agents.keys())
    for i in range(len(agent_ids)):
        for j in range(i+1, len(agent_ids)):
            orchestrator.connect_agents(agent_ids[i], agent_ids[j])
            logger.info(f"Connected agents: {agent_ids[i]} and {agent_ids[j]}")
    
    logger.info(f"Agent ecosystem started with {len(agents)} agents")
    return orchestrator 