#!/usr/bin/env python3
"""
Test script for the DevelopmentAgent functionality.

This script tests the various capabilities of the DevelopmentAgent,
including code generation, repository analysis, and code review.
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from typing import Dict, List, Any, Optional

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'test_development_agent.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class DevelopmentAgentTester:
    """
    Tester for the DevelopmentAgent capabilities.
    """
    
    def __init__(self, host="localhost", port=5678):
        """Initialize the tester."""
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"
        self.dev_agent_id = None
    
    def check_server_status(self) -> bool:
        """Check if the agent ecosystem server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                logger.info(f"Server is running: {response.json()}")
                return True
            else:
                logger.error(f"Server status check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error checking server status: {e}")
            return False
    
    def create_development_agent(self) -> Optional[str]:
        """Create a development agent and return its ID."""
        try:
            logger.info("Creating development agent...")
            response = requests.post(
                f"{self.base_url}/api/agents",
                json={
                    "name": "DevAgent",
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
            )
            
            if response.status_code != 201:
                logger.error(f"Failed to create development agent: {response.status_code} {response.text}")
                return None
            
            data = response.json()
            agent_id = data.get("agent", {}).get("id") or data.get("agent_id")
            
            if not agent_id:
                logger.error("No agent ID returned")
                return None
            
            logger.info(f"Created development agent with ID: {agent_id}")
            self.dev_agent_id = agent_id
            return agent_id
        except Exception as e:
            logger.error(f"Error creating development agent: {e}")
            return None
    
    def add_task(self, task_type: str, task_data: Dict[str, Any]) -> Optional[str]:
        """Add a task to the development agent."""
        if not self.dev_agent_id:
            logger.error("No development agent created")
            return None
        
        try:
            logger.info(f"Adding task '{task_type}' to development agent...")
            response = requests.post(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/task",
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
            
            logger.info(f"Added task '{task_type}' with ID: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return None
    
    def get_responses(self) -> List[Dict[str, Any]]:
        """Get responses from the development agent."""
        if not self.dev_agent_id:
            logger.error("No development agent created")
            return []
        
        try:
            logger.info("Getting responses from development agent...")
            response = requests.get(
                f"{self.base_url}/api/agents/{self.dev_agent_id}/response"
            )
            
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
    
    def wait_for_responses(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Wait for responses from the development agent."""
        logger.info(f"Waiting up to {timeout} seconds for responses...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            responses = self.get_responses()
            if responses:
                return responses
            logger.info("No responses yet, waiting...")
            time.sleep(2)
        
        logger.warning("Timeout waiting for responses")
        return []
    
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
                logger.error(f"Failed to delete agent: {response.status_code} {response.text}")
                return False
            
            logger.info("Development agent deleted successfully")
            self.dev_agent_id = None
            return True
        except Exception as e:
            logger.error(f"Error deleting agent: {e}")
            return False
    
    def test_code_generation(self) -> bool:
        """Test code generation capability."""
        logger.info("Testing code generation...")
        
        task_id = self.add_task("generate_code", {
            "language": "python",
            "description": "Create a function to calculate the Fibonacci sequence up to n terms",
            "requirements": [
                "Should handle edge cases (n <= 0)",
                "Include docstring with examples",
                "Optimize for performance"
            ]
        })
        
        if not task_id:
            return False
        
        responses = self.wait_for_responses()
        
        # Check response
        for response in responses:
            if response.get("type") == "code_generated" and response.get("task_id") == task_id:
                code = response.get("code", "")
                logger.info(f"Code generation successful, generated code: {code[:100]}...")
                return True
        
        logger.error("No code generation response received")
        return False
    
    def test_code_review(self) -> bool:
        """Test code review capability."""
        logger.info("Testing code review...")
        
        # Sample code to review
        code_to_review = """
def sort_numbers(numbers):
    # Sort a list of numbers
    n = len(numbers)
    for i in range(n):
        for j in range(0, n - i - 1):
            if numbers[j] > numbers[j + 1]:
                numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]
    return numbers
"""
        
        task_id = self.add_task("review_code", {
            "language": "python",
            "code": code_to_review,
            "criteria": ["efficiency", "readability", "best practices"]
        })
        
        if not task_id:
            return False
        
        responses = self.wait_for_responses()
        
        # Check response
        for response in responses:
            if response.get("type") == "code_review" and response.get("task_id") == task_id:
                review = response.get("review", "")
                logger.info(f"Code review successful, review: {review[:100]}...")
                return True
        
        logger.error("No code review response received")
        return False
    
    def test_repository_analysis(self) -> bool:
        """Test repository analysis capability."""
        logger.info("Testing repository analysis...")
        
        task_id = self.add_task("analyze_repository", {
            "repo": "microsoft/vscode",
            "depth": "summary",
            "focus": ["structure", "dependencies", "quality"]
        })
        
        if not task_id:
            return False
        
        responses = self.wait_for_responses(timeout=60)  # Repository analysis might take longer
        
        # Check response
        for response in responses:
            if response.get("type") == "repository_analysis" and response.get("task_id") == task_id:
                analysis = response.get("analysis", "")
                logger.info(f"Repository analysis successful, analysis: {analysis[:100]}...")
                return True
        
        logger.error("No repository analysis response received")
        return False
    
    def test_documentation_generation(self) -> bool:
        """Test documentation generation capability."""
        logger.info("Testing documentation generation...")
        
        # Sample code to document
        code_to_document = """
class DataProcessor:
    def __init__(self, data_source):
        self.data_source = data_source
        self.processed_data = None
    
    def process(self, filters=None):
        data = self.data_source.get_data()
        if filters:
            for filter_func in filters:
                data = filter_func(data)
        self.processed_data = data
        return data
    
    def save(self, destination):
        if self.processed_data is None:
            raise ValueError("No processed data available")
        destination.save(self.processed_data)
"""
        
        task_id = self.add_task("generate_documentation", {
            "language": "python",
            "code": code_to_document,
            "format": "docstring",
            "level": "detailed"
        })
        
        if not task_id:
            return False
        
        responses = self.wait_for_responses()
        
        # Check response
        for response in responses:
            if response.get("type") == "documentation_generated" and response.get("task_id") == task_id:
                documentation = response.get("documentation", "")
                logger.info(f"Documentation generation successful, documentation: {documentation[:100]}...")
                return True
        
        logger.error("No documentation generation response received")
        return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        if not self.check_server_status():
            logger.error("Server is not running, cannot run tests")
            return {
                "server_status": False
            }
        
        if not self.create_development_agent():
            logger.error("Failed to create development agent, cannot run tests")
            return {
                "server_status": True,
                "agent_creation": False
            }
        
        results = {
            "server_status": True,
            "agent_creation": True,
            "code_generation": self.test_code_generation(),
            "code_review": self.test_code_review(),
            "repository_analysis": self.test_repository_analysis(),
            "documentation_generation": self.test_documentation_generation()
        }
        
        # Clean up
        self.delete_agent()
        
        return results

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test DevelopmentAgent functionality')
    parser.add_argument('--host', default='localhost', help='Host where the agent ecosystem is running')
    parser.add_argument('--port', type=int, default=5678, help='Port where the agent ecosystem is running')
    parser.add_argument('--test', choices=['all', 'code_generation', 'code_review', 'repository_analysis', 'documentation_generation'],
                        default='all', help='Specific test to run')
    
    args = parser.parse_args()
    
    tester = DevelopmentAgentTester(host=args.host, port=args.port)
    
    if args.test == 'all':
        results = tester.run_all_tests()
        logger.info("Test Results:")
        for test_name, result in results.items():
            logger.info(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        
        # Exit with success if all tests passed
        success = all(results.values())
        return 0 if success else 1
    else:
        # Run a specific test
        if not tester.check_server_status():
            logger.error("Server is not running, cannot run test")
            return 1
        
        if not tester.create_development_agent():
            logger.error("Failed to create development agent, cannot run test")
            return 1
        
        # Run the selected test
        if args.test == 'code_generation':
            result = tester.test_code_generation()
        elif args.test == 'code_review':
            result = tester.test_code_review()
        elif args.test == 'repository_analysis':
            result = tester.test_repository_analysis()
        elif args.test == 'documentation_generation':
            result = tester.test_documentation_generation()
        
        # Clean up
        tester.delete_agent()
        
        logger.info(f"{args.test}: {'PASSED' if result else 'FAILED'}")
        return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main()) 