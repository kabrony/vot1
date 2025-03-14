#!/usr/bin/env python3
"""
Comprehensive test script for the Agent Ecosystem.

This script tests the entire agent ecosystem, including:
1. Creating different agent types
2. Connecting agents and sending messages
3. Executing tasks on different agents
4. Testing memory operations
5. Verifying DevelopmentAgent functionality
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, Any, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentEcosystemTester:
    """Test the complete agent ecosystem functionality."""
    
    def __init__(self, host="localhost", port=5678):
        """Initialize the tester."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.agents = {}  # agent_id -> {name, type}
    
    def verify_server(self) -> bool:
        """Verify the server is running."""
        try:
            logger.info(f"Verifying server at {self.base_url}")
            response = requests.get(f"{self.base_url}/api/status")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Server status: {data.get('status')}")
                
                # Check if agent ecosystem is enabled
                agent_ecosystem = data.get("agent_ecosystem", {})
                if agent_ecosystem.get("enabled", False):
                    logger.info(f"Agent ecosystem is enabled with {agent_ecosystem.get('agent_count', 0)} agents")
                    return True
                else:
                    logger.error("Agent ecosystem is not enabled")
                    return False
            else:
                logger.error(f"Server status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            return False
    
    def create_agent(self, name: str, agent_type: str, capabilities: List[str]) -> Optional[str]:
        """Create an agent of the specified type."""
        try:
            logger.info(f"Creating {agent_type} agent named '{name}'...")
            
            payload = {
                "name": name,
                "capabilities": capabilities
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents",
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                agent_id = data.get("agent_id") or data.get("agent", {}).get("id")
                
                if agent_id:
                    logger.info(f"Created {agent_type} agent '{name}' with ID: {agent_id}")
                    self.agents[agent_id] = {"name": name, "type": agent_type}
                    return agent_id
                else:
                    logger.error(f"Agent created but no ID returned")
                    return None
            else:
                logger.error(f"Failed to create agent: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            return None
    
    def create_search_agent(self) -> Optional[str]:
        """Create a search agent."""
        return self.create_agent(
            name="TestSearchAgent",
            agent_type="SearchAgent",
            capabilities=["search", "perplexity"]
        )
    
    def create_web_agent(self) -> Optional[str]:
        """Create a web agent."""
        return self.create_agent(
            name="TestWebAgent",
            agent_type="WebAgent",
            capabilities=["web_scraping", "firecrawl"]
        )
    
    def create_development_agent(self) -> Optional[str]:
        """Create a development agent."""
        return self.create_agent(
            name="TestDevAgent",
            agent_type="DevelopmentAgent",
            capabilities=[
                "code_generation",
                "code_review",
                "repository_analysis",
                "testing"
            ]
        )
    
    def connect_agents(self, agent_id1: str, agent_id2: str) -> bool:
        """Connect two agents."""
        try:
            logger.info(f"Connecting agents: {self.agents[agent_id1]['name']} and {self.agents[agent_id2]['name']}")
            
            payload = {
                "target_agent_id": agent_id2
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id1}/connect",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully connected agents {agent_id1} and {agent_id2}")
                return True
            else:
                logger.error(f"Failed to connect agents: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error connecting agents: {e}")
            return False
    
    def send_message(self, from_agent_id: str, to_agent_id: str, content: str) -> bool:
        """Send a message from one agent to another."""
        try:
            from_name = self.agents[from_agent_id]["name"]
            to_name = self.agents[to_agent_id]["name"]
            logger.info(f"Sending message from {from_name} to {to_name}")
            
            payload = {
                "from_agent_id": from_agent_id,
                "content": content
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{to_agent_id}/message",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent message from {from_name} to {to_name}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def add_task(self, agent_id: str, task_type: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Add a task to an agent."""
        try:
            agent_name = self.agents[agent_id]["name"]
            logger.info(f"Adding task '{task_type}' to {agent_name}")
            
            payload = {
                "task_type": task_type,
                "task_data": task_data
            }
            
            response = requests.post(
                f"{self.base_url}/api/agents/{agent_id}/task",
                json=payload
            )
            
            if response.status_code == 201:
                data = response.json()
                task_id = data.get("task_id")
                
                if task_id:
                    logger.info(f"Added task '{task_type}' to {agent_name} with ID: {task_id}")
                    return task_id
                else:
                    logger.error(f"Task added but no ID returned")
                    return None
            else:
                logger.error(f"Failed to add task: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return None
    
    def get_responses(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get responses from an agent."""
        try:
            response = requests.get(f"{self.base_url}/api/agents/{agent_id}/response")
            
            if response.status_code == 200:
                data = response.json()
                responses = data.get("responses", [])
                return responses
            else:
                logger.error(f"Failed to get responses: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error getting responses: {e}")
            return []
    
    def wait_for_response(self, agent_id: str, task_id: str, max_wait: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for a response to a specific task."""
        logger.info(f"Waiting for response to task {task_id} from agent {self.agents[agent_id]['name']}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            responses = self.get_responses(agent_id)
            
            for resp in responses:
                if resp.get("task_id") == task_id:
                    logger.info(f"Found response for task {task_id}")
                    return resp
            
            logger.info(f"No response yet, waiting... (elapsed: {time.time() - start_time:.1f}s)")
            time.sleep(2)
        
        logger.error(f"Timed out waiting for response to task {task_id}")
        return None
    
    def store_memory(self, key: str, value: Any, tags: List[str] = None) -> bool:
        """Store a memory."""
        try:
            tags = tags or []
            logger.info(f"Storing memory with key '{key}' and tags {tags}")
            
            payload = {
                "key": key,
                "value": value,
                "tags": tags
            }
            
            response = requests.post(
                f"{self.base_url}/api/memory",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully stored memory with key '{key}'")
                return True
            else:
                logger.error(f"Failed to store memory: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Get a memory by key."""
        try:
            logger.info(f"Getting memory with key '{key}'")
            
            response = requests.get(f"{self.base_url}/api/memory/{key}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved memory with key '{key}'")
                return data.get("value")
            elif response.status_code == 404:
                logger.error(f"Memory with key '{key}' not found")
                return None
            else:
                logger.error(f"Failed to get memory: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return None
    
    def search_memories(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        try:
            logger.info(f"Searching memories with tags {tags}")
            
            payload = {
                "tags": tags,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.base_url}/api/memory/search",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.info(f"Found {len(results)} memories matching tags {tags}")
                return results
            else:
                logger.error(f"Failed to search memories: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def test_memory_operations(self) -> Tuple[bool, bool, bool]:
        """Test memory operations (store, retrieve, search)."""
        # Store a memory
        store_success = self.store_memory(
            key="test_memory",
            value={"data": "Test memory data", "timestamp": time.time()},
            tags=["test", "memory"]
        )
        
        # Get the memory
        memory = self.get_memory("test_memory")
        retrieve_success = memory is not None
        
        # Search memories
        search_results = self.search_memories(tags=["test"])
        search_success = len(search_results) > 0
        
        return store_success, retrieve_success, search_success
    
    def test_development_tasks(self) -> Tuple[bool, bool]:
        """Test development-specific tasks."""
        dev_agent_id = self.create_development_agent()
        if not dev_agent_id:
            logger.error("Failed to create development agent")
            return False, False
        
        # Test code generation
        code_gen_task_id = self.add_task(
            agent_id=dev_agent_id,
            task_type="generate_code",
            task_data={
                "language": "python",
                "description": "Create a function that sorts a list using merge sort",
                "requirements": [
                    "Include docstring",
                    "Handle empty lists",
                    "Add performance notes"
                ]
            }
        )
        
        code_gen_response = None
        if code_gen_task_id:
            code_gen_response = self.wait_for_response(dev_agent_id, code_gen_task_id, max_wait=30)
        
        code_gen_success = code_gen_response is not None
        
        # Test code review
        code_review_task_id = self.add_task(
            agent_id=dev_agent_id,
            task_type="review_code",
            task_data={
                "language": "python",
                "code": """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result
                """,
                "criteria": ["readability", "performance", "error handling"]
            }
        )
        
        code_review_response = None
        if code_review_task_id:
            code_review_response = self.wait_for_response(dev_agent_id, code_review_task_id, max_wait=30)
        
        code_review_success = code_review_response is not None
        
        return code_gen_success, code_review_success
    
    def cleanup(self) -> bool:
        """Clean up by deleting all created agents."""
        success = True
        for agent_id, agent_info in list(self.agents.items()):
            try:
                logger.info(f"Deleting agent {agent_info['name']} ({agent_id})")
                response = requests.delete(f"{self.base_url}/api/agents/{agent_id}")
                
                if response.status_code == 200:
                    logger.info(f"Successfully deleted agent {agent_info['name']}")
                    del self.agents[agent_id]
                else:
                    logger.error(f"Failed to delete agent {agent_info['name']}: {response.status_code} - {response.text}")
                    success = False
            except Exception as e:
                logger.error(f"Error deleting agent {agent_info['name']}: {e}")
                success = False
        
        return success
    
    def run_tests(self) -> Dict[str, bool]:
        """Run all tests."""
        results = {}
        
        # Verify server
        results["server_verified"] = self.verify_server()
        if not results["server_verified"]:
            logger.error("Server verification failed, stopping tests")
            return results
        
        # Test agent creation
        search_agent_id = self.create_search_agent()
        web_agent_id = self.create_web_agent()
        
        results["agent_creation"] = search_agent_id is not None and web_agent_id is not None
        
        if not results["agent_creation"]:
            logger.error("Agent creation failed, stopping tests")
            return results
        
        # Test agent connection
        if search_agent_id and web_agent_id:
            results["agent_connection"] = self.connect_agents(search_agent_id, web_agent_id)
        else:
            results["agent_connection"] = False
        
        # Test memory operations
        store_success, retrieve_success, search_success = self.test_memory_operations()
        results["memory_store"] = store_success
        results["memory_retrieve"] = retrieve_success 
        results["memory_search"] = search_success
        
        # Test development tasks
        code_gen_success, code_review_success = self.test_development_tasks()
        results["code_generation"] = code_gen_success
        results["code_review"] = code_review_success
        
        # Clean up
        results["cleanup"] = self.cleanup()
        
        return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Agent Ecosystem")
    parser.add_argument("--host", default="localhost", help="Host where the server is running")
    parser.add_argument("--port", type=int, default=5678, help="Port where the server is running")
    
    args = parser.parse_args()
    
    logger.info("=============== STARTING AGENT ECOSYSTEM TESTS ===============")
    
    tester = AgentEcosystemTester(host=args.host, port=args.port)
    results = tester.run_tests()
    
    logger.info("=============== TEST RESULTS ===============")
    all_passed = True
    for test, passed in results.items():
        logger.info(f"{test}: {'PASSED' if passed else 'FAILED'}")
        if not passed:
            all_passed = False
    
    logger.info("=============== END OF TESTS ===============")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 