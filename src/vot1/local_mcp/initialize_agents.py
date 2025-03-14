#!/usr/bin/env python3
"""
Initialize default agents in the MCP Agent Ecosystem.

This script creates a set of default agents with appropriate capabilities
and establishes connections between them.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, List, Any, Optional

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "initialize_agents.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AgentInitializer:
    """Client for initializing agents in the MCP Agent Ecosystem."""
    
    def __init__(self, host: str = "localhost", port: int = 5678):
        """Initialize the agent initializer.
        
        Args:
            host: Host where the agent ecosystem is running
            port: Port where the agent ecosystem is running
        """
        self.base_url = f"http://{host}:{port}"
        logger.info(f"Initializing agent ecosystem client at {self.base_url}")
    
    def check_server_status(self) -> bool:
        """Check if the agent ecosystem server is running.
        
        Returns:
            True if the server is running, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"Server status: {status_data}")
                return True
            else:
                logger.error(f"Failed to get server status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to server at {self.base_url}")
            return False
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents.
        
        Returns:
            List of agent data
        """
        try:
            response = requests.get(f"{self.base_url}/api/agents")
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                logger.info(f"Found {len(agents)} agents")
                return agents
            else:
                logger.error(f"Failed to list agents: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing agents: {e}")
            return []
    
    def create_agent(self, name: str, capabilities: List[str]) -> Optional[str]:
        """Create a new agent.
        
        Args:
            name: Name of the agent
            capabilities: List of capabilities the agent has
        
        Returns:
            Agent ID if successful, None otherwise
        """
        try:
            payload = {
                "name": name,
                "capabilities": capabilities
            }
            response = requests.post(
                f"{self.base_url}/api/agents",
                json=payload
            )
            if response.status_code == 201:
                agent_id = response.json().get("agent_id")
                logger.info(f"Created agent {name} with ID {agent_id}")
                return agent_id
            else:
                logger.error(f"Failed to create agent {name}: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating agent {name}: {e}")
            return None
    
    def connect_agents(self, source_id: str, target_id: str) -> bool:
        """Connect two agents.
        
        Args:
            source_id: ID of the source agent
            target_id: ID of the target agent
        
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "target_agent_id": target_id
            }
            response = requests.post(
                f"{self.base_url}/api/agents/{source_id}/connect",
                json=payload
            )
            if response.status_code == 200:
                logger.info(f"Connected agent {source_id} to {target_id}")
                return True
            else:
                logger.error(f"Failed to connect agents: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting agents: {e}")
            return False
    
    def store_shared_memory(self, key: str, value: Any, tags: List[str] = None) -> bool:
        """Store a memory in the shared memory.
        
        Args:
            key: Memory key
            value: Memory value
            tags: Optional list of tags
        
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "key": key,
                "value": value,
                "tags": tags or []
            }
            response = requests.post(
                f"{self.base_url}/api/memory",
                json=payload
            )
            if response.status_code == 200:
                logger.info(f"Stored memory with key {key}")
                return True
            else:
                logger.error(f"Failed to store memory: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error storing memory: {e}")
            return False

def create_default_agents(client: AgentInitializer) -> Dict[str, str]:
    """Create the default set of agents.
    
    Args:
        client: AgentInitializer instance
    
    Returns:
        Dictionary mapping agent names to their IDs
    """
    agents = {}
    
    # Define agent configurations
    default_agents = [
        {
            "name": "SearchAgent",
            "capabilities": ["search", "perplexity"]
        },
        {
            "name": "RepositoryAgent",
            "capabilities": ["github", "code_analysis"]
        },
        {
            "name": "WebAgent",
            "capabilities": ["web_scraping", "firecrawl"]
        },
        {
            "name": "AnalysisAgent",
            "capabilities": ["data_analysis", "memory"]
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
            ]
        }
    ]
    
    # Create agents
    for agent_config in default_agents:
        agent_id = client.create_agent(
            agent_config["name"],
            agent_config["capabilities"]
        )
        if agent_id:
            agents[agent_config["name"]] = agent_id
    
    return agents

def connect_default_agents(client: AgentInitializer, agents: Dict[str, str]) -> None:
    """Connect the default agents.
    
    Args:
        client: AgentInitializer instance
        agents: Dictionary mapping agent names to their IDs
    """
    # Define connections: every agent should be connected to AnalysisAgent
    # and other specific connections
    connections = [
        ("SearchAgent", "WebAgent"),
        ("SearchAgent", "AnalysisAgent"),
        ("RepositoryAgent", "AnalysisAgent"),
        ("WebAgent", "AnalysisAgent"),
        ("WebAgent", "SearchAgent"),
        ("AnalysisAgent", "SearchAgent"),
        ("AnalysisAgent", "RepositoryAgent"),
        ("AnalysisAgent", "WebAgent")
    ]
    
    for source, target in connections:
        if source in agents and target in agents:
            client.connect_agents(agents[source], agents[target])
        else:
            logger.warning(f"Could not connect {source} to {target}: one or both agents not found")

def store_default_memories(client: AgentInitializer) -> None:
    """Store default memories in the shared memory.
    
    Args:
        client: AgentInitializer instance
    """
    default_memories = [
        {
            "key": "agent_capabilities",
            "value": {
                "SearchAgent": ["search", "perplexity"],
                "RepositoryAgent": ["github", "code_analysis"],
                "WebAgent": ["web_scraping", "firecrawl"],
                "AnalysisAgent": ["data_analysis", "memory"]
            },
            "tags": ["system", "capabilities", "reference"]
        },
        {
            "key": "task_routing",
            "value": {
                "query": "SearchAgent",
                "analyze_repo": "RepositoryAgent",
                "scrape_url": "WebAgent",
                "process_search_results": "WebAgent",
                "memory": "AnalysisAgent",
                "call_function": "any"
            },
            "tags": ["system", "routing", "reference"]
        }
    ]
    
    for memory in default_memories:
        client.store_shared_memory(
            memory["key"],
            memory["value"],
            memory["tags"]
        )

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Initialize default agents in the MCP Agent Ecosystem")
    parser.add_argument("--host", default="localhost", help="Host where the agent ecosystem is running")
    parser.add_argument("--port", type=int, default=5678, help="Port where the agent ecosystem is running")
    parser.add_argument("--clean", action="store_true", help="Clean existing agents before initialization")
    
    args = parser.parse_args()
    
    client = AgentInitializer(args.host, args.port)
    
    # Check server status
    if not client.check_server_status():
        logger.error("Server is not running or not accessible. Exiting.")
        sys.exit(1)
    
    # Create default agents
    logger.info("Creating default agents...")
    agents = create_default_agents(client)
    
    if not agents:
        logger.error("Failed to create agents. Exiting.")
        sys.exit(1)
    
    # Connect agents
    logger.info("Connecting agents...")
    connect_default_agents(client, agents)
    
    # Store default memories
    logger.info("Storing default memories...")
    store_default_memories(client)
    
    logger.info("Agent initialization complete.")

if __name__ == "__main__":
    main() 