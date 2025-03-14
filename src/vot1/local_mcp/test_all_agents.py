#!/usr/bin/env python3
"""
Comprehensive Test Suite for MCP Agent Ecosystem

This script tests all components of the agent ecosystem, including:
1. Port finder utility
2. Server startup
3. Agent initialization
4. Agent communication
5. Task execution
6. Memory operations
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
import requests
import signal
import socket
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_all_agents.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import local_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.vot1.local_mcp.port_finder import is_port_in_use, find_available_port

class AgentEcosystemTester:
    """Tests all components of the MCP Agent Ecosystem."""
    
    def __init__(self, host="localhost", start_port=5678):
        self.host = host
        self.start_port = start_port
        self.port = None
        self.server_process = None
        self.base_url = None
        self.agent_ids = {}
    
    def test_port_finder(self) -> bool:
        """Test the port finder utility.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing port finder utility...")
        
        try:
            # First find an available port using our utility
            self.port = find_available_port(self.start_port, host=self.host)
            if not self.port:
                logger.error("Could not find an available port")
                return False
                
            logger.info(f"Port finder found available port: {self.port}")
            
            # Test if port is available
            in_use = is_port_in_use(self.port, self.host)
            if in_use:
                logger.warning(f"Port {self.port} seems to be in use, finding another one")
                self.port = find_available_port(self.port + 1, host=self.host)
                if not self.port:
                    logger.error("Could not find an available port")
                    return False
                logger.info(f"New available port found: {self.port}")
            
            # Occupy the port to test detection
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                test_sock.bind((self.host, self.port))
                test_sock.listen(1)
                
                # Now with the port occupied, check if our detector reports it as in use
                in_use = is_port_in_use(self.port, self.host)
                if not in_use:
                    logger.error(f"Port {self.port} should be in use, but is_port_in_use returns False")
                    test_sock.close()
                    return False
                    
                logger.info("Port finder correctly detected occupied port")
                test_sock.close()
                
                # Find another port after closing
                another_port = find_available_port(self.port, host=self.host)
                if not another_port:
                    logger.error("Could not find another available port")
                    return False
                    
                logger.info(f"Port finder found another available port: {another_port}")
                self.port = another_port
                logger.info("Port finder utility works correctly")
                return True
            finally:
                try:
                    test_sock.close()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Error testing port finder: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the agent ecosystem server.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting agent ecosystem server...")
        
        # Make sure we have a port to use
        if not self.port:
            self.port = find_available_port(self.start_port, host=self.host)
            if not self.port:
                logger.error("Could not find an available port")
                return False
            
        logger.info(f"Using port {self.port}")
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Start the server in a separate process
        script_path = Path(__file__).parent / "run_agent_ecosystem.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--host", self.host,
            "--port", str(self.port),
            "--find-port"
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
                    time.sleep(2)  # Give the server time to start
                    response = requests.get(f"{self.base_url}/api/status")
                    if response.status_code == 200:
                        logger.info("Server started successfully")
                        return True
                except requests.exceptions.ConnectionError:
                    if attempt < max_attempts - 1:
                        logger.info(f"Waiting for server to start (attempt {attempt + 1}/{max_attempts})...")
                    else:
                        logger.error("Server failed to start")
                        self.stop_server()
                        return False
            
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
    
    def initialize_agents(self) -> bool:
        """Initialize agents.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing agents...")
        
        script_path = Path(__file__).parent / "initialize_agents.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--host", self.host,
            "--port", str(self.port)
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate(timeout=30)
            
            if process.returncode != 0:
                logger.error(f"Failed to initialize agents: {stderr}")
                return False
                
            logger.info("Agents initialized successfully")
            
            # Get the list of agents
            response = requests.get(f"{self.base_url}/api/agents")
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                for agent in agents:
                    self.agent_ids[agent["name"]] = agent["id"]
                logger.info(f"Found {len(agents)} agents: {', '.join(self.agent_ids.keys())}")
                return True
            else:
                logger.error(f"Failed to list agents: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            return False
    
    def test_agent_connections(self) -> bool:
        """Test agent connections.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing agent connections...")
        
        if not self.agent_ids:
            logger.error("No agents found")
            return False
            
        try:
            # Verify that the connections are established as expected
            for agent_name, agent_id in self.agent_ids.items():
                response = requests.get(f"{self.base_url}/api/agents/{agent_id}")
                if response.status_code != 200:
                    logger.error(f"Failed to get agent {agent_name}: {response.status_code}")
                    return False
                    
                agent_data = response.json().get("agent", {})
                connections = agent_data.get("connections", [])
                
                if not connections:
                    logger.warning(f"Agent {agent_name} has no connections")
                else:
                    logger.info(f"Agent {agent_name} has {len(connections)} connections")
            
            return True
        except Exception as e:
            logger.error(f"Error testing agent connections: {e}")
            return False
    
    def test_memory_operations(self) -> bool:
        """Test memory operations.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing memory operations...")
        
        try:
            # Store a memory
            memory_data = {
                "test_message": "This is a test memory",
                "timestamp": time.time()
            }
            
            response = requests.post(
                f"{self.base_url}/api/memory",
                json={
                    "key": "test_key",
                    "value": memory_data,
                    "tags": ["test", "memory"]
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to store memory: {response.status_code}")
                return False
                
            logger.info("Memory stored successfully")
            
            # Retrieve the memory
            response = requests.get(f"{self.base_url}/api/memory/test_key")
            if response.status_code != 200:
                logger.error(f"Failed to retrieve memory: {response.status_code}")
                return False
                
            retrieved_data = response.json().get("value")
            if not retrieved_data or retrieved_data.get("test_message") != memory_data["test_message"]:
                logger.error(f"Retrieved memory data does not match: {retrieved_data}")
                return False
                
            logger.info("Memory retrieved successfully")
            
            # Search memories by tag
            response = requests.post(
                f"{self.base_url}/api/memory/search",
                json={
                    "tags": ["test"],
                    "limit": 10
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to search memories: {response.status_code}")
                return False
                
            search_results = response.json().get("results", [])
            if not search_results:
                logger.error("No memory search results found")
                return False
                
            logger.info(f"Found {len(search_results)} memories with tag 'test'")
            return True
            
        except Exception as e:
            logger.error(f"Error testing memory operations: {e}")
            return False
    
    def test_task_execution(self) -> bool:
        """Test task execution.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing task execution...")
        
        if "AnalysisAgent" not in self.agent_ids:
            logger.error("AnalysisAgent not found")
            return False
            
        try:
            analysis_agent_id = self.agent_ids["AnalysisAgent"]
            
            # Add a memory task
            response = requests.post(
                f"{self.base_url}/api/agents/{analysis_agent_id}/task",
                json={
                    "task_type": "memory",
                    "task_data": {
                        "operation": "retrieve",
                        "key": "test_key"
                    }
                }
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to add task: {response.status_code}")
                return False
                
            task_id = response.json().get("task_id")
            if not task_id:
                logger.error("No task ID returned")
                return False
                
            logger.info(f"Task added successfully with ID: {task_id}")
            
            # Wait for the task to complete
            max_attempts = 15
            for attempt in range(max_attempts):
                time.sleep(1)
                
                # Get responses
                response = requests.get(f"{self.base_url}/api/agents/{analysis_agent_id}/response")
                if response.status_code != 200:
                    logger.error(f"Failed to get responses: {response.status_code}")
                    return False
                    
                responses = response.json().get("responses", [])
                for resp in responses:
                    if resp.get("task_id") == task_id:
                        logger.info(f"Task completed: {resp}")
                        return True
                
                if attempt < max_attempts - 1:
                    logger.info(f"Waiting for task completion (attempt {attempt + 1}/{max_attempts})...")
            
            logger.error("Task did not complete within the expected time")
            return False
            
        except Exception as e:
            logger.error(f"Error testing task execution: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        try:
            tests = [
                ("Port Finder", self.test_port_finder),
                ("Server Startup", self.start_server),
                ("Agent Initialization", self.initialize_agents),
                ("Agent Connections", self.test_agent_connections),
                ("Memory Operations", self.test_memory_operations),
                ("Task Execution", self.test_task_execution)
            ]
            
            results = {}
            
            for test_name, test_func in tests:
                logger.info(f"===== Running Test: {test_name} =====")
                try:
                    success = test_func()
                    results[test_name] = success
                    if not success:
                        logger.error(f"Test {test_name} FAILED")
                        break
                except Exception as e:
                    logger.error(f"Exception in test {test_name}: {e}")
                    results[test_name] = False
                    break
            
            logger.info("===== Test Results =====")
            all_passed = True
            for test_name, success in results.items():
                status = "PASSED" if success else "FAILED"
                logger.info(f"{test_name}: {status}")
                all_passed = all_passed and success
            
            return all_passed
            
        finally:
            self.stop_server()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test all components of the MCP Agent Ecosystem")
    parser.add_argument("--host", default="localhost", help="Host to use for tests")
    parser.add_argument("--port", type=int, default=5678, help="Starting port for tests")
    
    args = parser.parse_args()
    
    tester = AgentEcosystemTester(args.host, args.port)
    success = tester.run_all_tests()
    
    if success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed. See log for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 