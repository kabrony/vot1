#!/usr/bin/env python3
"""
VOT1 GitHub MCP Integration Initializer

This script initializes the connection between VOT1 and GitHub using direct MCP GitHub integration.
It checks for existing connections and helps you set up a new connection if needed.

Usage:
    python -m scripts.init_github [--check]

Options:
    --check    Only check if a connection exists without trying to create one
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("github_init")

async def check_connection(mcp):
    """Check if there is an active GitHub connection."""
    try:
        # Check GitHub connection using MCP's direct capabilities
        result = await mcp.process_tool("mcp_MCP_GITHUB_CHECK_ACTIVE_CONNECTION", {
            "params": {
                "tool": "GitHub",
                "connection_id": os.getenv("GITHUB_CONNECTION_ID", "")
            }
        })
        
        # Parse JSON response
        response = json.loads(result.get("content", "{}"))
        is_connected = response.get("active", False)
        
        if is_connected:
            logger.info("✅ GitHub connection is active and ready to use!")
            return True
        else:
            logger.warning("❌ No active GitHub connection found.")
            return False
    except Exception as e:
        logger.error(f"Error checking GitHub connection: {e}")
        return False

async def get_required_parameters(mcp):
    """Get the required parameters for GitHub connection."""
    try:
        # Get required parameters using MCP's direct capabilities
        result = await mcp.process_tool("mcp_MCP_GITHUB_GET_REQUIRED_PARAMETERS", {
            "params": {
                "tool": "GitHub"
            }
        })
        
        # Parse JSON response
        response = json.loads(result.get("content", "{}"))
        parameters = response.get("parameters", {})
        
        if parameters:
            logger.info(f"Required parameters for GitHub connection: {json.dumps(parameters, indent=2)}")
        else:
            logger.info("No specific parameters required for GitHub connection. Will use MCP OAuth flow.")
            
        return parameters
    except Exception as e:
        logger.error(f"Error getting required parameters: {e}")
        return {}

async def initiate_connection(mcp, params=None):
    """Initiate a connection to GitHub."""
    try:
        # Initiate GitHub connection
        params = params or {}
        result = await mcp.process_tool("mcp_MCP_GITHUB_INITIATE_CONNECTION", {
            "params": {
                "tool": "GitHub",
                "parameters": params
            }
        })
        
        # Parse JSON response
        response = json.loads(result.get("content", "{}"))
        connection_id = response.get("connection_id")
        
        if connection_id:
            logger.info(f"✅ GitHub connection initiated successfully with ID: {connection_id}")
            # Store connection ID in environment for future use
            os.environ["GITHUB_CONNECTION_ID"] = connection_id
            
            # Save connection ID to a local file for persistence
            connection_file = Path.home() / ".vot1" / "github_connection.json"
            connection_file.parent.mkdir(parents=True, exist_ok=True)
            
            connection_data = {
                "connection_id": connection_id,
                "timestamp": response.get("timestamp", ""),
                "expires_at": response.get("expires_at", "")
            }
            
            with open(connection_file, "w") as f:
                json.dump(connection_data, f, indent=2)
                
            logger.info(f"Connection data saved to {connection_file}")
            return {"success": True, "connection_id": connection_id, "response": response}
        else:
            logger.warning("❌ Failed to initiate GitHub connection.")
            return {"success": False, "error": "No connection ID returned"}
    except Exception as e:
        logger.error(f"Error initiating GitHub connection: {e}")
        return {"success": False, "error": str(e)}

async def test_github_api(mcp):
    """Test the GitHub API connection by making a simple request."""
    try:
        # Use GitHub API root to test the connection
        result = await mcp.process_tool("mcp_MCP_GITHUB_GITHUB_API_ROOT", {
            "params": {}
        })
        
        # Parse JSON response
        response = json.loads(result.get("content", "{}"))
        
        if response:
            logger.info("✅ GitHub API test successful.")
            return True
        else:
            logger.warning("⚠️ GitHub API test returned empty response.")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing GitHub API: {e}")
        return False

async def async_main():
    """Async main function to check or initiate GitHub connection."""
    parser = argparse.ArgumentParser(description="Initialize VOT1 GitHub connection")
    parser.add_argument("--check", action="store_true", help="Only check if a connection exists")
    args = parser.parse_args()
    
    try:
        # Import VOT Model Control Protocol
        from src.vot1.vot_mcp import VotModelControlProtocol
        mcp = VotModelControlProtocol()
        
        # Check if connection exists
        connected = await check_connection(mcp)
        
        if connected:
            # Test the API to verify it's working properly
            api_test = await test_github_api(mcp)
            if api_test:
                logger.info("GitHub connection is fully functional.")
            else:
                logger.warning("GitHub connection exists but API test failed.")
                if not args.check:
                    logger.info("Attempting to refresh the connection...")
                    await initiate_connection(mcp)
            # Connection exists and working, nothing more to do
            sys.exit(0)
        
        if args.check:
            # We were only asked to check, so exit now
            logger.info("No active GitHub connection found.")
            sys.exit(1)
        
        # No connection, and we were asked to set one up
        logger.info("Attempting to set up a new GitHub connection...")
        
        # Get required parameters (if any)
        params = await get_required_parameters(mcp)
        
        # If we need to collect parameters from the user
        if params:
            # For simplicity in this example, we're not collecting user input
            # In a real application, you'd prompt for each required parameter
            logger.info("Required parameters detected. Using default values for demo.")
            connection_params = {}
        else:
            connection_params = {}
        
        # Attempt to initiate connection
        result = await initiate_connection(mcp, connection_params)
        
        if result.get("success", False):
            logger.info("✅ GitHub connection successfully established!")
            # Test the new connection
            api_test = await test_github_api(mcp)
            if api_test:
                logger.info("GitHub API test successful. Connection is fully functional.")
            else:
                logger.warning("GitHub API test failed. Connection may have issues.")
            sys.exit(0)
        else:
            logger.error(f"❌ Failed to establish GitHub connection: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except ImportError as e:
        logger.error(f"Error importing VOT1 modules: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    """Entry point for the script."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main() 