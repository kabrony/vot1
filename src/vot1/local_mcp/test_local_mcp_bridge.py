#!/usr/bin/env python3
"""
Test Local MCP Bridge

This script tests the Local MCP Bridge functionality, including:
1. Port finder functionality
2. Server startup
3. Basic API calls
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
        logging.FileHandler(os.path.join('logs', 'test_local_mcp_bridge.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import local_mcp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.vot1.local_mcp.port_finder import is_port_in_use, find_available_port

class LocalMCPBridgeTester:
    """Tests the Local MCP Bridge functionality."""
    
    def __init__(self, host="localhost", start_port=5678):
        self.host = host
        self.start_port = start_port
        self.port = None
        self.server_process = None
        self.base_url = None
    
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
        """Start the local MCP bridge server.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting local MCP bridge server...")
        
        # Make sure we have a port to use
        if not self.port:
            self.port = find_available_port(self.start_port, host=self.host)
            if not self.port:
                logger.error("Could not find an available port")
                return False
            
        logger.info(f"Using port {self.port}")
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Start the server in a separate process
        script_path = Path(__file__).parent.parent.parent.parent / "run_local_mcp_bridge.py"
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
        """Stop the local MCP bridge server."""
        if self.server_process:
            logger.info("Stopping server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
    
    def test_api_status(self) -> bool:
        """Test the API status endpoint.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing API status endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code != 200:
                logger.error(f"Failed to get API status: {response.status_code}")
                return False
                
            status = response.json()
            if "status" not in status or status["status"] != "running":
                logger.error(f"Unexpected API status: {status}")
                return False
                
            logger.info("API status endpoint working correctly")
            return True
        except Exception as e:
            logger.error(f"Error testing API status: {e}")
            return False
    
    def test_api_health(self) -> bool:
        """Test the API health endpoint.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Testing API health endpoint...")
        
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code != 200:
                logger.error(f"Failed to get API health: {response.status_code}")
                return False
                
            health = response.json()
            if "status" not in health or health["status"] != "healthy":
                logger.error(f"Unexpected API health: {health}")
                return False
                
            logger.info("API health endpoint working correctly")
            return True
        except Exception as e:
            logger.error(f"Error testing API health: {e}")
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
                ("API Status", self.test_api_status),
                ("API Health", self.test_api_health)
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
    parser = argparse.ArgumentParser(description="Test the Local MCP Bridge")
    parser.add_argument("--host", default="localhost", help="Host to use for tests")
    parser.add_argument("--port", type=int, default=5678, help="Starting port for tests")
    
    args = parser.parse_args()
    
    tester = LocalMCPBridgeTester(args.host, args.port)
    success = tester.run_all_tests()
    
    if success:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed. See log for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 