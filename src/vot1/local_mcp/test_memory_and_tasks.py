#!/usr/bin/env python3
"""
Simplified Test for Memory Operations and Task Execution

This script tests:
1. Memory operations (store, retrieve, search)
2. Task execution for memory retrieval
"""

import os
import sys
import json
import time
import logging
import uuid
import requests
from typing import Dict, List, Any, Optional

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_memory_and_tasks.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class MemoryAndTaskTester:
    """
    Tester for memory operations and task execution.
    """
    
    def __init__(self, host="localhost", port=5678):
        """Initialize the tester."""
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.test_agents = []
    
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
        responses = []
        while time.time() < deadline:
            responses = self.get_responses(agent_id)
            if len(responses) >= expected_count:
                return responses
            time.sleep(0.5)
        
        logger.warning(f"Timeout waiting for {expected_count} responses, only got {len(responses)}")
        return responses
    
    def cleanup(self):
        """Clean up test resources."""
        for agent_id in reversed(self.test_agents):
            try:
                logger.info(f"Deleting test agent {agent_id}...")
                requests.delete(f"{self.base_url}/api/agents/{agent_id}")
                time.sleep(0.5)  # Give the server time to process the deletion
            except Exception as e:
                logger.error(f"Error deleting agent {agent_id}: {e}")
        
        self.test_agents.clear()
    
    def test_memory_operations(self) -> bool:
        """Test memory operations."""
        logger.info("===== Testing Memory Operations =====")
        
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
        logger.info("===== Testing Task Execution =====")
        
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

def main():
    """Main entry point."""
    try:
        tester = MemoryAndTaskTester()
        
        # Test memory operations
        memory_test_result = tester.test_memory_operations()
        
        # Test task execution
        task_test_result = tester.test_task_execution()
        
        # Clean up
        tester.cleanup()
        
        # Print results
        logger.info("===== Test Results =====")
        logger.info(f"Memory Operations: {'PASSED' if memory_test_result else 'FAILED'}")
        logger.info(f"Task Execution: {'PASSED' if task_test_result else 'FAILED'}")
        
        if memory_test_result and task_test_result:
            logger.info("All tests passed!")
            return 0
        else:
            logger.error("Some tests failed. See log for details.")
            return 1
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 