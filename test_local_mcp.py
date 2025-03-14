#!/usr/bin/env python3
"""
Local MCP Bridge Test Script

This script tests the functionality of the Local MCP Bridge implementation.
"""

import os
import sys
import json
import time
import unittest
import requests
from typing import Dict, Any, Optional

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the bridge
from src.vot1.local_mcp import LocalMCPBridge

class TestLocalMCPBridge(unittest.TestCase):
    """Test case for the Local MCP Bridge"""
    
    def setUp(self):
        """Set up the test"""
        # Create a bridge instance
        self.bridge = LocalMCPBridge(
            config_path="src/vot1/local_mcp/config/mcp.json",
            cache_enabled=True
        )
    
    def test_config_loading(self):
        """Test that the configuration is loaded correctly"""
        # Verify that we have the MCP services in the config
        self.assertIn("mcpServers", self.bridge.config)
        
        services = self.bridge.config.get("mcpServers", {})
        # Check that we have at least some services
        self.assertGreater(len(services), 0)
        
        # Verify that each service has a URL
        for service_name, service_config in services.items():
            self.assertIn("url", service_config)
            self.assertTrue(service_config["url"].startswith("https://"))
    
    def test_service_url_retrieval(self):
        """Test that service URLs can be retrieved"""
        # Test known services
        for service in [
            LocalMCPBridge.SERVICE_GITHUB,
            LocalMCPBridge.SERVICE_PERPLEXITY,
            LocalMCPBridge.SERVICE_FIRECRAWL,
            LocalMCPBridge.SERVICE_FIGMA,
            LocalMCPBridge.SERVICE_COMPOSIO
        ]:
            url = self.bridge.get_service_url(service)
            if url:
                self.assertTrue(url.startswith("https://"))
    
    def test_check_connection(self):
        """Test that connection checking works"""
        # Try a connection check for GitHub
        result = self.bridge.check_connection(LocalMCPBridge.SERVICE_GITHUB)
        
        # Verify that the result is a dictionary with the expected keys
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        self.assertIn("active_connection", result)
    
    def test_get_required_parameters(self):
        """Test that required parameters can be retrieved"""
        # Get parameters for Perplexity
        result = self.bridge.get_required_parameters(LocalMCPBridge.SERVICE_PERPLEXITY)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        self.assertTrue(result["successful"])
        self.assertIn("parameters", result)
        self.assertIn("api_key", result["parameters"])
    
    def test_initiate_connection(self):
        """Test that connections can be initiated"""
        # Use a fake API key for testing
        api_key = "test_api_key_for_unit_tests"
        
        # Initiate a connection to Perplexity
        result = self.bridge.initiate_connection(
            LocalMCPBridge.SERVICE_PERPLEXITY,
            {"api_key": api_key}
        )
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        
        # If the connection was successful, check that we have a connection ID
        if result.get("successful", False):
            self.assertIn("connection_id", result)
            self.assertTrue(result["connection_id"].startswith("perplexity-"))
        
        # Check that the connection is stored
        self.assertIn(LocalMCPBridge.SERVICE_PERPLEXITY, self.bridge.connections)
        self.assertEqual(
            self.bridge.connections[LocalMCPBridge.SERVICE_PERPLEXITY]["parameters"]["api_key"],
            api_key
        )
    
    def test_call_function(self):
        """Test that functions can be called"""
        # Initiate a connection first
        self.bridge.initiate_connection(
            LocalMCPBridge.SERVICE_PERPLEXITY,
            {"api_key": "test_api_key_for_unit_tests"}
        )
        
        # Call a function
        result = self.bridge.call_function(
            "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH",
            {
                "params": {
                    "systemContent": "You are a helpful assistant.",
                    "userContent": "What is the capital of France?",
                    "temperature": 0.7
                }
            }
        )
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        self.assertIn("function", result)
        self.assertEqual(
            result["function"],
            "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH"
        )
    
    def test_invalid_function_name(self):
        """Test that invalid function names are handled"""
        # Call a function with an invalid name
        result = self.bridge.call_function(
            "invalid_function_name",
            {"params": {}}
        )
        
        # Verify that the call fails
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        self.assertFalse(result["successful"])
        self.assertIn("error", result)
    
    def test_performance_metrics(self):
        """Test that performance metrics are tracked"""
        # Make some API calls to generate metrics
        self.bridge.call_function(
            "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH",
            {"params": {"systemContent": "Test", "userContent": "Test"}}
        )
        
        # Get the metrics
        metrics = self.bridge.get_performance_metrics()
        
        # Verify the metrics
        self.assertIsInstance(metrics, dict)
        self.assertIn("api_calls", metrics)
        self.assertGreaterEqual(metrics["api_calls"], 1)
        self.assertIn("avg_response_time", metrics)
        self.assertGreater(metrics["avg_response_time"], 0)
    
    def test_clear_cache(self):
        """Test that the cache can be cleared"""
        # First, make a call to populate the cache
        self.bridge.call_function(
            "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH",
            {"params": {"systemContent": "Test", "userContent": "Test"}}
        )
        
        # Store the current cache stats
        before_stats = self.bridge.cache_stats.copy()
        
        # Clear the cache
        result = self.bridge.clear_cache()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("successful", result)
        self.assertTrue(result["successful"])
        
        # Verify that the cache is cleared
        self.assertEqual(len(self.bridge.cache), 0)
        
        # Verify that the cache stats are updated
        self.assertGreater(self.bridge.cache_stats["last_cleared"], before_stats["last_cleared"])


class TestLocalMCPServer(unittest.TestCase):
    """
    Test case for the Local MCP Server
    
    Note: These tests require a running server. They will be skipped if the server is not running.
    To run these tests, start the server first:
    
    python run_local_mcp_bridge.py
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class"""
        # Check if the server is running
        try:
            response = requests.get("http://localhost:5678/api/status", timeout=2)
            cls.server_running = response.status_code == 200
        except:
            cls.server_running = False
    
    def setUp(self):
        """Set up the test"""
        # Skip tests if the server is not running
        if not self.__class__.server_running:
            self.skipTest("Server not running")
    
    def test_status_endpoint(self):
        """Test the status endpoint"""
        response = requests.get("http://localhost:5678/api/status")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("successful", data)
        self.assertTrue(data["successful"])
        self.assertIn("status", data)
        self.assertEqual(data["status"], "running")
        self.assertIn("uptime", data)
        self.assertGreater(data["uptime"], 0)
    
    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        response = requests.get("http://localhost:5678/api/metrics")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("successful", data)
        self.assertTrue(data["successful"])
        self.assertIn("metrics", data)
        metrics = data["metrics"]
        self.assertIn("api_calls", metrics)
        self.assertIn("api_errors", metrics)
        self.assertIn("avg_response_time", metrics)
    
    def test_clear_cache_endpoint(self):
        """Test the clear cache endpoint"""
        response = requests.post("http://localhost:5678/api/clear-cache")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("successful", data)
        self.assertTrue(data["successful"])
        self.assertIn("message", data)
        self.assertEqual(data["message"], "Cache cleared")
    
    def test_check_connection_endpoint(self):
        """Test the check connection endpoint"""
        response = requests.get("http://localhost:5678/api/check-connection/GITHUB")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("successful", data)
        self.assertTrue(data["successful"])
        self.assertIn("active_connection", data)
    
    def test_get_required_parameters_endpoint(self):
        """Test the get required parameters endpoint"""
        response = requests.get("http://localhost:5678/api/get-required-parameters/PERPLEXITY")
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("successful", data)
        self.assertTrue(data["successful"])
        self.assertIn("parameters", data)


def run_tests():
    """Run the tests"""
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add the test cases
    suite.addTest(unittest.makeSuite(TestLocalMCPBridge))
    suite.addTest(unittest.makeSuite(TestLocalMCPServer))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    run_tests() 