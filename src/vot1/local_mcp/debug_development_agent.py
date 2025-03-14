#!/usr/bin/env python3
"""
Debug script for the DevelopmentAgent functionality.

This script provides detailed diagnostics for the DevelopmentAgent to identify why tasks are failing.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import traceback
from typing import Dict, List, Any, Optional

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Set up logging with detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'debug_development_agent.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class DevelopmentAgentDebugger:
    """
    Debugger for the DevelopmentAgent capabilities.
    """
    
    def __init__(self, host="localhost", port=5679):
        """Initialize the debugger with the correct port."""
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.dev_agent_id = None
        
        # Enable detailed HTTP request logging
        requests_logger = logging.getLogger("requests.packages.urllib3")
        requests_logger.setLevel(logging.DEBUG)
        requests_logger.propagate = True
    
    def check_server_status(self, verbose=True) -> Dict[str, Any]:
        """Check detailed server status."""
        try:
            logger.info(f"Checking server status at {self.base_url}/api/status")
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                status_data = response.json()
                if verbose:
                    logger.info(f"Server status details: {json.dumps(status_data, indent=2)}")
                return status_data
            else:
                logger.error(f"Server status check failed: {response.status_code} - {response.text}")
                return {"status": "error", "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Error checking server status: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all existing agents."""
        try:
            logger.info("Listing agents...")
            response = requests.get(f"{self.base_url}/api/agents")
            
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                logger.info(f"Found {len(agents)} agents:")
                for i, agent in enumerate(agents):
                    logger.info(f"Agent {i+1}: {agent.get('name')} (ID: {agent.get('id')})")
                return agents
            else:
                logger.error(f"Failed to list agents: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def create_development_agent(self) -> Optional[str]:
        """Create a development agent with detailed response parsing."""
        try:
            logger.info("Creating development agent...")
            payload = {
                "name": "DebugDevAgent",
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
            logger.debug(f"Agent creation payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/api/agents",
                json=payload
            )
            
            logger.debug(f"Agent creation response status: {response.status_code}")
            logger.debug(f"Agent creation response headers: {dict(response.headers)}")
            
            if response.status_code != 201:
                logger.error(f"Failed to create development agent: {response.status_code} - {response.text}")
                return None
            
            try:
                data = response.json()
                logger.debug(f"Agent creation response data: {json.dumps(data, indent=2)}")
                
                # Try multiple possible response formats
                agent_id = None
                if "agent" in data and isinstance(data["agent"], dict) and "id" in data["agent"]:
                    agent_id = data["agent"]["id"]
                elif "agent_id" in data:
                    agent_id = data["agent_id"]
                elif "id" in data:
                    agent_id = data["id"]
                
                if not agent_id:
                    logger.error("No agent ID found in response. Response structure:")
                    logger.error(json.dumps(data, indent=2))
                    return None
                
                logger.info(f"Created development agent with ID: {agent_id}")
                self.dev_agent_id = agent_id
                return agent_id
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse agent creation response: {e}")
                logger.error(f"Raw response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating development agent: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an agent."""
        try:
            logger.info(f"Getting details for agent {agent_id}...")
            response = requests.get(f"{self.base_url}/api/agents/{agent_id}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get agent details: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            logger.info(f"Agent details: {json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            logger.error(f"Error getting agent details: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def add_task(self, task_type: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Add a task with detailed diagnostics."""
        if not self.dev_agent_id:
            logger.error("No development agent created")
            return None
        
        try:
            logger.info(f"Adding task '{task_type}' to development agent...")
            payload = {
                "task_type": task_type,
                "task_data": task_data
            }
            logger.debug(f"Task payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/task",
                json=payload
            )
            
            logger.debug(f"Task addition response status: {response.status_code}")
            logger.debug(f"Task addition response headers: {dict(response.headers)}")
            
            if response.status_code not in [200, 201]:
                logger.error(f"Failed to add task: {response.status_code} - {response.text}")
                return None
            
            try:
                data = response.json()
                logger.debug(f"Task addition response data: {json.dumps(data, indent=2)}")
                
                task_id = data.get("task_id")
                if not task_id:
                    logger.error("No task ID returned")
                    return None
                
                logger.info(f"Added task '{task_type}' with ID: {task_id}")
                return task_id
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse task addition response: {e}")
                logger.error(f"Raw response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def get_agent_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks for the agent."""
        if not self.dev_agent_id:
            logger.error("No development agent created")
            return []
        
        try:
            logger.info(f"Getting tasks for agent {self.dev_agent_id}...")
            response = requests.get(f"{self.base_url}/api/agents/{self.dev_agent_id}/task")
            
            if response.status_code != 200:
                logger.error(f"Failed to get tasks: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            tasks = data.get("tasks", [])
            logger.info(f"Found {len(tasks)} tasks:")
            for i, task in enumerate(tasks):
                logger.info(f"Task {i+1}: {task.get('type')} (ID: {task.get('id')}, Status: {task.get('status')})")
            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def get_responses(self, verbose=True) -> List[Dict[str, Any]]:
        """Get responses with detailed output."""
        if not self.dev_agent_id:
            logger.error("No development agent created")
            return []
        
        try:
            logger.info(f"Getting responses for agent {self.dev_agent_id}...")
            response = requests.get(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/response"
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get responses: {response.status_code} - {response.text}")
                return []
            
            try:
                data = response.json()
                responses = data.get("responses", [])
                
                logger.info(f"Got {len(responses)} responses")
                if verbose and responses:
                    for i, resp in enumerate(responses):
                        logger.info(f"Response {i+1} - Type: {resp.get('type')}, Task ID: {resp.get('task_id')}")
                        # Pretty print the first 200 characters of any content
                        for key, value in resp.items():
                            if key not in ['type', 'task_id', 'timestamp']:
                                if isinstance(value, str) and len(value) > 200:
                                    logger.info(f"  {key}: {value[:200]}...")
                                elif isinstance(value, dict):
                                    logger.info(f"  {key}: {json.dumps(value, indent=2)[:200]}...")
                                else:
                                    logger.info(f"  {key}: {value}")
                
                return responses
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse responses: {e}")
                logger.error(f"Raw response: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting responses: {e}")
            logger.error(traceback.format_exc())
            return []
    
    def wait_for_responses(self, timeout: int = 30, check_interval: float = 2.0) -> List[Dict[str, Any]]:
        """Wait for responses with progress updates."""
        logger.info(f"Waiting up to {timeout} seconds for responses...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            responses = self.get_responses(verbose=False)
            
            if responses:
                logger.info(f"Received {len(responses)} responses after {elapsed:.1f} seconds")
                return responses
                
            logger.info(f"No responses yet after {elapsed:.1f} seconds, checking tasks...")
            tasks = self.get_agent_tasks()
            if tasks:
                task_status = {task.get('id'): task.get('status') for task in tasks}
                logger.info(f"Current task statuses: {task_status}")
            
            logger.info(f"Waiting {check_interval} seconds before checking again...")
            time.sleep(check_interval)
        
        logger.warning(f"Timeout after {timeout} seconds waiting for responses")
        return []
    
    def debug_agent_implementation(self):
        """Check if the DevelopmentAgent implementation is correctly registered."""
        try:
            # Let's check if the module is correctly imported
            import importlib
            
            try:
                dev_agent_module = importlib.import_module('src.vot1.local_mcp.development_agent')
                logger.info("Successfully imported development_agent module")
                
                if hasattr(dev_agent_module, 'DevelopmentAgent'):
                    logger.info("DevelopmentAgent class exists in the module")
                    
                    from src.vot1.local_mcp.agent import FeedbackAgent
                    dev_agent_class = dev_agent_module.DevelopmentAgent
                    
                    if issubclass(dev_agent_class, FeedbackAgent):
                        logger.info("DevelopmentAgent correctly inherits from FeedbackAgent")
                    else:
                        logger.error("DevelopmentAgent does not inherit from FeedbackAgent")
                else:
                    logger.error("DevelopmentAgent class not found in module")
            except ImportError as e:
                logger.error(f"Failed to import development_agent module: {e}")
                
            # Check __init__.py to ensure it's properly exposed
            try:
                import src.vot1.local_mcp
                if hasattr(src.vot1.local_mcp, 'DevelopmentAgent'):
                    logger.info("DevelopmentAgent is correctly exposed in the package __init__.py")
                else:
                    logger.error("DevelopmentAgent is not exposed in the package __init__.py")
            except Exception as e:
                logger.error(f"Error checking package exports: {e}")
                
        except Exception as e:
            logger.error(f"Error debugging agent implementation: {e}")
            logger.error(traceback.format_exc())
    
    def debug_task_handling(self, task_type: str, task_data: Dict[str, Any]) -> bool:
        """Debug task handling for a specific task type."""
        logger.info(f"Debugging task handling for {task_type}...")
        
        # 1. First, check if the agent exists
        agent_details = self.get_agent_details(self.dev_agent_id) if self.dev_agent_id else None
        if not agent_details:
            logger.error("Cannot debug task handling: agent not available")
            return False
        
        # 2. Add the task
        task_id = self.add_task(task_type, task_data)
        if not task_id:
            logger.error(f"Failed to add {task_type} task")
            return False
        
        logger.info(f"Added {task_type} task with ID: {task_id}")
        
        # 3. Wait briefly for initial processing
        logger.info("Waiting for task processing to begin...")
        time.sleep(3)
        
        # 4. Check task status
        tasks = self.get_agent_tasks()
        task = next((t for t in tasks if t.get('id') == task_id), None)
        
        if not task:
            logger.error(f"Task {task_id} not found in agent tasks")
            return False
        
        logger.info(f"Task status: {task.get('status', 'unknown')}")
        
        # 5. Wait for responses
        responses = self.wait_for_responses(timeout=30)
        
        # 6. Check if we got the expected response
        task_response = None
        expected_response_type = self._get_expected_response_type(task_type)
        
        for resp in responses:
            if resp.get('task_id') == task_id:
                logger.info(f"Found response for task {task_id} with type: {resp.get('type')}")
                if resp.get('type') == expected_response_type:
                    task_response = resp
                    break
        
        if task_response:
            logger.info(f"Task {task_type} successfully completed with response type {expected_response_type}")
            return True
        else:
            logger.error(f"No {expected_response_type} response found for task {task_id}")
            if responses:
                logger.info("Available response types: " + ", ".join([r.get('type', 'unknown') for r in responses]))
            return False
    
    def _get_expected_response_type(self, task_type: str) -> str:
        """Map task types to expected response types."""
        response_types = {
            "generate_code": "code_generated",
            "review_code": "code_review",
            "analyze_repository": "repository_analysis",
            "generate_documentation": "documentation_generated",
            "suggest_improvements": "improvement_suggestions",
            "analyze_dependencies": "dependency_analysis",
            "create_tests": "tests_created",
            "analyze_pr": "pr_analysis"
        }
        return response_types.get(task_type, "unknown")
    
    def delete_agent(self) -> bool:
        """Delete the development agent."""
        if not self.dev_agent_id:
            logger.warning("No development agent to delete")
            return True
        
        try:
            logger.info(f"Deleting development agent {self.dev_agent_id}...")
            response = requests.delete(
                f"{self.base_url}/api/agents/{self.dev_agent_id}"
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to delete agent: {response.status_code} - {response.text}")
                return False
            
            logger.info("Development agent deleted successfully")
            self.dev_agent_id = None
            return True
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run_debug_session(self) -> Dict[str, Any]:
        """Run a complete debug session."""
        results = {
            "server_status": False,
            "agent_creation": False,
            "implementation_check": False,
            "task_tests": {}
        }
        
        # 1. Check server status
        status = self.check_server_status()
        results["server_status"] = status.get("status") == "running"
        
        if not results["server_status"]:
            logger.error("Server is not running, cannot continue debugging")
            return results
        
        # 2. Check existing agents
        agents = self.list_agents()
        results["existing_agents"] = len(agents)
        
        # 3. Debug agent implementation
        self.debug_agent_implementation()
        results["implementation_check"] = True
        
        # 4. Create development agent
        agent_id = self.create_development_agent()
        results["agent_creation"] = agent_id is not None
        
        if not results["agent_creation"]:
            logger.error("Failed to create development agent, cannot continue debugging")
            return results
        
        # 5. Debug basic task handling with enhanced logging
        simple_tasks = {
            "generate_code": {
                "language": "python",
                "description": "Print 'Hello, World!' to the console",
                "requirements": ["Simple", "One line only"]
            },
            "review_code": {
                "language": "python",
                "code": "print('Hello, World!')",
                "criteria": ["simplicity"]
            }
        }
        
        for task_type, task_data in simple_tasks.items():
            logger.info(f"=============== TESTING {task_type} ===============")
            success = self.debug_task_handling(task_type, task_data)
            results["task_tests"][task_type] = success
        
        # 6. Clean up
        self.delete_agent()
        
        return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Debug DevelopmentAgent functionality')
    parser.add_argument('--host', default='localhost', help='Host where the agent ecosystem is running')
    parser.add_argument('--port', type=int, default=5679, help='Port where the agent ecosystem is running')
    
    args = parser.parse_args()
    
    logger.info("=============== STARTING DEVELOPMENT AGENT DEBUG SESSION ===============")
    debugger = DevelopmentAgentDebugger(host=args.host, port=args.port)
    results = debugger.run_debug_session()
    
    logger.info("=============== DEBUG SESSION RESULTS ===============")
    for key, value in results.items():
        if key != "task_tests":
            logger.info(f"{key}: {value}")
    
    if "task_tests" in results:
        logger.info("Task Tests:")
        for task, success in results["task_tests"].items():
            logger.info(f"  {task}: {'PASSED' if success else 'FAILED'}")
    
    logger.info("=============== END OF DEBUG SESSION ===============")
    
    # Exit with success if all important tests passed
    success = results.get("server_status", False) and results.get("agent_creation", False)
    if "task_tests" in results:
        success = success and all(results["task_tests"].values())
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 