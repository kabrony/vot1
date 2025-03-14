#!/usr/bin/env python3
"""
Integration Test for Agent Ecosystem

This script performs a comprehensive integration test of the Agent Ecosystem, testing:
1. Server startup with port finding
2. Agent creation, retrieval, and management
3. Agent connections and messaging
4. Memory operations (store, retrieve, search)
5. Task execution across multiple agents
6. Error handling and recovery
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import requests
import socket
import uuid
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_ecosystem_integration.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import local_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.vot1.local_mcp.port_finder import find_available_port

class AgentEcosystemTester:
    """
    Integration tester for the Agent Ecosystem.
    """
    
    def __init__(self, host="localhost", start_port=5678):
        """Initialize the tester."""
        self.host = host
        self.port = find_available_port(start_port)
        if not self.port:
            raise RuntimeError("Could not find an available port")
            
        self.base_url = f"http://{self.host}:{self.port}"
        self.server_process = None
        self.test_agents = []
    
    def start_server(self) -> bool:
        """Start the agent ecosystem server."""
        logger.info(f"Starting agent ecosystem server on port {self.port}...")
        
        # Start the server in a separate process
        script_path = Path(__file__).parent / "run_agent_ecosystem.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--host", self.host,
            "--port", str(self.port),
            "--debug"
        ]
        
        try:
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait for the server to start
            max_attempts = 15
            for attempt in range(max_attempts):
                try:
                    time.sleep(1)  # Give the server time to start
                    response = requests.get(f"{self.base_url}/api/status")
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "running" and data.get("agent_ecosystem", {}).get("enabled"):
                            logger.info("Agent ecosystem server started successfully")
                            return True
                        else:
                            logger.warning("Server is running but agent ecosystem is not enabled")
                except requests.exceptions.ConnectionError:
                    if attempt < max_attempts - 1:
                        logger.info(f"Waiting for server to start (attempt {attempt + 1}/{max_attempts})...")
                    else:
                        logger.error("Server failed to start")
                        self.stop_server()
                        return False
            
            logger.error("Server is running but agent ecosystem is not enabled")
            return False
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the agent ecosystem server."""
        if self.server_process:
            logger.info("Stopping server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    def create_test_agent(self, name="TestAgent", capabilities=None) -> Optional[str]:
        """Create a test agent and return its ID."""
        try:
            logger.info(f"Creating test agent '{name}'...")
            
            if capabilities is None:
                capabilities = ["test", "memory"]
                
            response = requests.post(
                f"{self.base_url}/api/agents",
                json={
                    "name": name,
                    "capabilities": capabilities
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to create agent: {response.status_code} {response.text}")
                return None
                
            data = response.json()
            agent_id = data.get("agent", {}).get("id") or data.get("agent_id")
            
            if not agent_id:
                logger.error("No agent ID returned")
                return None
                
            logger.info(f"Created agent {name} with ID {agent_id}")
            self.test_agents.append(agent_id)
            return agent_id
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents in the ecosystem."""
        try:
            logger.info("Listing agents...")
            
            response = requests.get(f"{self.base_url}/api/agents")
            
            if response.status_code != 200:
                logger.error(f"Failed to list agents: {response.status_code} {response.text}")
                return []
                
            data = response.json()
            agents = data.get("agents", [])
            
            logger.info(f"Found {len(agents)} agents")
            return agents
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details."""
        try:
            logger.info(f"Getting agent {agent_id}...")
            
            response = requests.get(f"{self.base_url}/api/agents/{agent_id}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get agent: {response.status_code} {response.text}")
                return None
                
            data = response.json()
            agent = data.get("agent")
            
            if not agent:
                logger.error("No agent data returned")
                return None
                
            logger.info(f"Got agent: {agent}")
            return agent
        except Exception as e:
            logger.error(f"Error getting agent: {e}")
            return None
    
    def connect_agents(self, agent_id: str, target_agent_id: str) -> bool:
        """Connect two agents."""
        try:
            logger.info(f"Connecting agent {agent_id} to {target_agent_id}...")
            
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id}/connect",
                json={
                    "target_agent_id": target_agent_id
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to connect agents: {response.status_code} {response.text}")
                return False
                
            logger.info(f"Agents connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting agents: {e}")
            return False
    
    def disconnect_agents(self, agent_id: str, target_agent_id: str) -> bool:
        """Disconnect two agents."""
        try:
            logger.info(f"Disconnecting agent {agent_id} from {target_agent_id}...")
            
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id}/disconnect",
                json={
                    "target_agent_id": target_agent_id
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to disconnect agents: {response.status_code} {response.text}")
                return False
                
            logger.info(f"Agents disconnected successfully")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting agents: {e}")
            return False
    
    def send_message(self, agent_id: str, content: str, from_agent_id: Optional[str] = None) -> Optional[str]:
        """Send a message to an agent and return the message ID."""
        try:
            logger.info(f"Sending message to agent {agent_id}...")
            
            data = {
                "content": content
            }
            
            if from_agent_id:
                data["from_agent_id"] = from_agent_id
                
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id}/message",
                json=data
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send message: {response.status_code} {response.text}")
                return None
                
            data = response.json()
            message_id = data.get("message_id")
            
            if not message_id:
                logger.error("No message ID returned")
                return None
                
            logger.info(f"Message sent successfully with ID {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def add_task(self, agent_id: str, task_type: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Add a task to an agent's queue and return the task ID."""
        try:
            logger.info(f"Adding task to agent {agent_id}...")
            
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id}/task",
                json={
                    "task_type": task_type,
                    "task_data": task_data
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to add task: {response.status_code} {response.text}")
                return None
                
            data = response.json()
            task_id = data.get("task_id")
            
            if not task_id:
                logger.error("No task ID returned")
                return None
                
            logger.info(f"Task added successfully with ID {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return None
    
    def get_responses(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get responses from an agent."""
        try:
            logger.info(f"Getting responses from agent {agent_id}...")
            
            response = requests.get(f"{self.base_url}/api/agents/{agent_id}/response")
            
            if response.status_code != 200:
                logger.error(f"Failed to get responses: {response.status_code} {response.text}")
                return []
                
            data = response.json()
            responses = data.get("responses", [])
            
            logger.info(f"Got {len(responses)} responses")
            return responses
        except Exception as e:
            logger.error(f"Error getting responses: {e}")
            return []
    
    def store_memory(self, key: str, value: Any, tags: List[str] = None) -> bool:
        """Store a memory in the shared memory."""
        try:
            logger.info(f"Storing memory with key '{key}'...")
            
            if tags is None:
                tags = []
                
            response = requests.post(
                f"{self.base_url}/api/memory",
                json={
                    "key": key,
                    "value": value,
                    "tags": tags
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to store memory: {response.status_code} {response.text}")
                return False
                
            logger.info(f"Memory stored successfully")
            return True
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Get a memory from the shared memory."""
        try:
            logger.info(f"Getting memory with key '{key}'...")
            
            response = requests.get(f"{self.base_url}/api/memory/{key}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get memory: {response.status_code} {response.text}")
                return None
                
            data = response.json()
            value = data.get("value")
            
            logger.info(f"Memory retrieved successfully")
            return value
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return None
    
    def search_memories(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        try:
            logger.info(f"Searching memories with tags {tags}...")
            
            response = requests.post(
                f"{self.base_url}/api/memory/search",
                json={
                    "tags": tags,
                    "limit": limit
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to search memories: {response.status_code} {response.text}")
                return []
                
            data = response.json()
            results = data.get("results", [])
            
            logger.info(f"Found {len(results)} memories")
            return results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def wait_for_responses(self, agent_id: str, expected_count: int, timeout: int = 5) -> List[Dict[str, Any]]:
        """Wait for a specific number of responses from an agent."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            responses = self.get_responses(agent_id)
            if len(responses) >= expected_count:
                return responses
            time.sleep(0.5)
        
        logger.warning(f"Timeout waiting for {expected_count} responses, only got {len(responses)}")
        return self.get_responses(agent_id)
    
    def cleanup(self):
        """Clean up test resources."""
        for agent_id in reversed(self.test_agents):
            try:
                logger.info(f"Deleting test agent {agent_id}...")
                requests.delete(f"{self.base_url}/api/agents/{agent_id}")
            except Exception as e:
                logger.error(f"Error deleting agent {agent_id}: {e}")
        
        self.test_agents.clear()
    
    def test_agent_creation_and_retrieval(self) -> bool:
        """Test agent creation and retrieval."""
        logger.info("Testing agent creation and retrieval...")
        
        # Create a test agent
        agent_id = self.create_test_agent("CreationTestAgent")
        if not agent_id:
            return False
            
        # Get the agent details
        agent = self.get_agent(agent_id)
        if not agent:
            return False
            
        # Verify agent details
        if agent.get("name") != "CreationTestAgent" or agent.get("id") != agent_id:
            logger.error(f"Agent details don't match: {agent}")
            return False
            
        logger.info("Agent creation and retrieval test passed")
        return True
    
    def test_agent_connections(self) -> bool:
        """Test agent connections."""
        logger.info("Testing agent connections...")
        
        # Create two test agents
        agent1_id = self.create_test_agent("ConnectionAgent1")
        agent2_id = self.create_test_agent("ConnectionAgent2")
        
        if not agent1_id or not agent2_id:
            return False
            
        # Connect the agents
        if not self.connect_agents(agent1_id, agent2_id):
            return False
            
        # Verify the connection
        agent1 = self.get_agent(agent1_id)
        agent2 = self.get_agent(agent2_id)
        
        if not agent1 or not agent2:
            return False
            
        if agent2_id not in agent1.get("connections", []):
            logger.error(f"Agent1 is not connected to Agent2: {agent1}")
            return False
            
        if agent1_id not in agent2.get("connections", []):
            logger.error(f"Agent2 is not connected to Agent1: {agent2}")
            return False
            
        # Disconnect the agents
        if not self.disconnect_agents(agent1_id, agent2_id):
            return False
            
        # Verify the disconnection
        agent1 = self.get_agent(agent1_id)
        agent2 = self.get_agent(agent2_id)
        
        if not agent1 or not agent2:
            return False
            
        if agent2_id in agent1.get("connections", []):
            logger.error(f"Agent1 is still connected to Agent2: {agent1}")
            return False
            
        if agent1_id in agent2.get("connections", []):
            logger.error(f"Agent2 is still connected to Agent1: {agent2}")
            return False
            
        logger.info("Agent connections test passed")
        return True
    
    def test_memory_operations(self) -> bool:
        """Test memory operations."""
        logger.info("Testing memory operations...")
        
        # Store a memory
        test_value = {
            "message": f"Test memory {uuid.uuid4()}",
            "timestamp": time.time(),
            "tags": ["test", "integration"]
        }
        
        if not self.store_memory("test_memory_key", test_value, ["test", "integration"]):
            return False
            
        # Get the memory
        retrieved_value = self.get_memory("test_memory_key")
        if not retrieved_value:
            return False
            
        # Verify the memory value
        if retrieved_value.get("message") != test_value.get("message"):
            logger.error(f"Retrieved memory value doesn't match: {retrieved_value}")
            return False
            
        # Search for memories by tag
        results = self.search_memories(["test"])
        if not results:
            logger.error("No memories found with tag 'test'")
            return False
            
        # Verify search results
        found = False
        for result in results:
            # Check if the memory is in the result
            memory_value = result.get("value", {})
            if memory_value.get("message") == test_value.get("message"):
                found = True
                break
                
        if not found:
            logger.error(f"Test memory not found in search results: {results}")
            return False
            
        logger.info("Memory operations test passed")
        return True
    
    def test_task_execution(self) -> bool:
        """Test task execution."""
        logger.info("Testing task execution...")
        
        # Create a test agent
        agent_id = self.create_test_agent("TaskAgent")
        if not agent_id:
            return False
            
        # Store a memory for the agent to retrieve
        test_value = {
            "message": f"Task test memory {uuid.uuid4()}",
            "timestamp": time.time()
        }
        
        memory_key = f"task_test_memory_{int(time.time())}"
        if not self.store_memory(memory_key, test_value, ["task", "test"]):
            return False
            
        # Add a task to retrieve the memory
        task_id = self.add_task(
            agent_id,
            "memory_retrieval",
            {"key": memory_key}
        )
        
        if not task_id:
            return False
            
        # Wait for the task to complete and get the response
        responses = self.wait_for_responses(agent_id, 1)
        if not responses:
            logger.error("No responses received")
            return False
            
        # Verify the response
        response = responses[0]
        if response.get("task_id") != task_id:
            logger.error(f"Response task_id doesn't match: {response}")
            return False
            
        if response.get("type") != "memory_retrieved":
            logger.error(f"Response type is not 'memory_retrieved': {response}")
            return False
            
        value = response.get("value")
        if not value or value.get("message") != test_value.get("message"):
            logger.error(f"Response value doesn't match: {value}")
            return False
            
        logger.info("Task execution test passed")
        return True
    
    def test_cross_agent_messaging(self) -> bool:
        """Test messaging between agents."""
        logger.info("Testing cross-agent messaging...")
        
        # Create two test agents
        agent1_id = self.create_test_agent("MessageAgent1")
        agent2_id = self.create_test_agent("MessageAgent2")
        
        if not agent1_id or not agent2_id:
            return False
            
        # Connect the agents
        if not self.connect_agents(agent1_id, agent2_id):
            return False
            
        # Send a message from agent1 to agent2
        test_message = f"Test message {uuid.uuid4()}"
        message_id = self.send_message(agent2_id, test_message, agent1_id)
        
        if not message_id:
            return False
            
        # Wait for the message to be processed and check responses
        responses = self.wait_for_responses(agent2_id, 1)
        if not responses:
            logger.error("No responses received")
            return False
            
        # Verify the response
        response = responses[0]
        if response.get("from_agent_id") != agent1_id:
            logger.error(f"Response from_agent_id doesn't match: {response}")
            return False
            
        if response.get("content") != test_message:
            logger.error(f"Response content doesn't match: {response}")
            return False
            
        logger.info("Cross-agent messaging test passed")
        return True
    
    def run_integration_tests(self) -> Dict[str, bool]:
        """Run all integration tests."""
        tests = [
            ("Agent Creation and Retrieval", self.test_agent_creation_and_retrieval),
            ("Agent Connections", self.test_agent_connections),
            ("Memory Operations", self.test_memory_operations),
            ("Task Execution", self.test_task_execution),
            ("Cross-Agent Messaging", self.test_cross_agent_messaging)
        ]
        
        results = {}
        
        try:
            # Start the server
            if not self.start_server():
                logger.error("Failed to start the agent ecosystem server")
                return {"Server Startup": False}
                
            results["Server Startup"] = True
            
            # List the default agents
            default_agents = self.list_agents()
            logger.info(f"Default agents: {[a.get('name') for a in default_agents]}")
            
            # Run the tests
            for test_name, test_func in tests:
                logger.info(f"===== Running Test: {test_name} =====")
                try:
                    success = test_func()
                    results[test_name] = success
                    if not success:
                        logger.error(f"Test {test_name} FAILED")
                except Exception as e:
                    logger.error(f"Exception in test {test_name}: {e}")
                    results[test_name] = False
                
            return results
        finally:
            # Clean up
            self.cleanup()
            self.stop_server()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Agent Ecosystem Integration Tests")
    parser.add_argument("--host", default="localhost", help="Host to use for tests")
    parser.add_argument("--port", type=int, default=5678, help="Starting port for tests")
    
    args = parser.parse_args()
    
    try:
        tester = AgentEcosystemTester(args.host, args.port)
        results = tester.run_integration_tests()
        
        logger.info("===== Integration Test Results =====")
        all_passed = True
        for test_name, success in results.items():
            status = "PASSED" if success else "FAILED"
            logger.info(f"{test_name}: {status}")
            all_passed = all_passed and success
        
        if all_passed:
            logger.info("All integration tests passed!")
            return 0
        else:
            logger.error("Some integration tests failed. See log for details.")
            return 1
    except Exception as e:
        logger.error(f"Error running integration tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 