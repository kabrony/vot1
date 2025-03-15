#!/bin/bash
#
# Composio MCP Setup Script for VOT1
#
# This script sets up the Composio Model Control Protocol (MCP) integration
# for the VOT1 advanced memory system.

# Exit on error
set -e

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

# Check for required env variables
if [ -z "$COMPOSIO_API_KEY" ] || [ -z "$COMPOSIO_MCP_URL" ]; then
    echo "Error: COMPOSIO_API_KEY and COMPOSIO_MCP_URL must be set in .env"
    exit 1
fi

echo "Setting up Composio MCP integration..."

# Ensure required packages are installed
echo "Installing required packages..."
pip install requests dotenv-python aiohttp asyncio

# Create required directories
echo "Creating necessary directories..."
mkdir -p memory/composio
mkdir -p logs

# Test Composio MCP connection
echo "Testing Composio MCP connection..."
python test_composio.py

if [ $? -eq 0 ]; then
    echo "Composio MCP connection successful!"
else
    echo "Warning: Composio MCP connection test failed. Please check your credentials and try again."
    echo "You can continue with setup, but integration may not work properly."
fi

# Create a dedicated MCP integration module
echo "Setting up Composio MCP integration module..."

if [ ! -d "src/vot1/composio" ]; then
    mkdir -p src/vot1/composio
    
    # Create __init__.py
    cat > src/vot1/composio/__init__.py << 'EOF'
"""
Composio MCP integration for VOT1

This package provides integration with Composio's Model Control Protocol.
"""

from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge

__all__ = ["ComposioClient", "ComposioMemoryBridge"]
EOF

    echo "Created src/vot1/composio/__init__.py"
    
    # Create client.py
    cat > src/vot1/composio/client.py << 'EOF'
"""
Composio MCP Client for VOT1

This module provides the client for interacting with Composio's MCP service.
"""

import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class ComposioClient:
    """
    Client for interacting with Composio's Model Control Protocol (MCP)
    """
    
    def __init__(self, api_key=None, mcp_url=None):
        """
        Initialize the Composio MCP client
        
        Args:
            api_key: Composio API key (defaults to COMPOSIO_API_KEY env var)
            mcp_url: Composio MCP URL (defaults to COMPOSIO_MCP_URL env var)
        """
        # Load API key and URL from environment if not provided
        self.api_key = api_key or os.getenv('COMPOSIO_API_KEY')
        self.mcp_url = mcp_url or os.getenv('COMPOSIO_MCP_URL')
        
        if not self.api_key:
            raise ValueError("Composio API key is required. Set COMPOSIO_API_KEY in .env or pass as argument.")
        
        if not self.mcp_url:
            raise ValueError("Composio MCP URL is required. Set COMPOSIO_MCP_URL in .env or pass as argument.")
        
        # Initialize HTTP session for async requests
        self._session = None
        logger.info(f"Composio client initialized with URL: {self.mcp_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._session
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def test_connection(self) -> bool:
        """
        Test the connection to Composio MCP
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        session = await self._get_session()
        
        try:
            # Just checking if the endpoint is reachable
            async with session.get(self.mcp_url) as response:
                # Log response status
                logger.info(f"Connection test status: {response.status}")
                
                if response.status == 200:
                    logger.info("Successfully connected to Composio MCP")
                    return True
                else:
                    text = await response.text()
                    logger.error(f"Failed to connect to Composio MCP: {text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to Composio MCP: {str(e)}")
            return False

    async def process_request(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a request through Composio MCP
        
        Args:
            prompt: The user message or prompt
            system: Optional system message
            tools: Optional list of tools
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            memory_context: Optional memory context to include
            
        Returns:
            Response from the model
        """
        session = await self._get_session()
        
        # Prepare payload based on Composio MCP API
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add system message if provided
        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})
            
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            
        # Add memory context if provided
        if memory_context:
            payload["context"] = memory_context
            
        try:
            async with session.post(
                f"{self.mcp_url}/chat/completions",
                json=payload
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error(f"Error from Composio MCP: {response.status} - {text}")
                    return {"error": text}
                    
        except Exception as e:
            logger.error(f"Exception calling Composio MCP: {str(e)}")
            return {"error": str(e)}
    
    def process_request_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of process_request
        
        This is a convenience wrapper around the async method.
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.process_request(
                prompt=prompt,
                system=system,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                memory_context=memory_context
            )
        )
EOF
    
    echo "Created src/vot1/composio/client.py"
    
    # Create memory_bridge.py
    cat > src/vot1/composio/memory_bridge.py << 'EOF'
"""
Composio Memory Bridge for VOT1

This module bridges the VOT1 memory system with Composio MCP.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from vot1.memory import MemoryManager
from vot1.composio.client import ComposioClient

# Configure logging
logger = logging.getLogger(__name__)

class ComposioMemoryBridge:
    """
    Bridge between VOT1 memory system and Composio MCP
    
    This class provides methods for:
    1. Storing memories in VOT1 from Composio responses
    2. Retrieving memories from VOT1 for Composio context
    3. Performing memory operations through Composio
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        composio_client: Optional[ComposioClient] = None
    ):
        """
        Initialize the memory bridge
        
        Args:
            memory_manager: VOT1 memory manager instance
            composio_client: Composio client instance
        """
        # Create or use provided memory manager
        self.memory_manager = memory_manager or MemoryManager()
        self.composio_client = composio_client or ComposioClient()
        
        logger.info("Composio Memory Bridge initialized")
    
    async def store_memory_from_response(
        self,
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory from a Composio MCP response
        
        Args:
            response: Composio response dict
            metadata: Additional metadata to store
            
        Returns:
            str: Memory ID
        """
        if "error" in response:
            logger.error(f"Cannot store memory from error response: {response['error']}")
            return None
            
        try:
            # Extract content from response - structure depends on Composio's API
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                logger.warning("No content found in Composio response")
                return None
                
            # Combine provided metadata with response metadata
            full_metadata = {
                "source": "composio_mcp",
                "timestamp": response.get("created"),
                "model": response.get("model", "composio"),
                "response_id": response.get("id")
            }
            
            if metadata:
                full_metadata.update(metadata)
                
            # Store in semantic memory
            memory_id = self.memory_manager.add_semantic_memory(
                content=content,
                metadata=full_metadata
            )
            
            logger.info(f"Stored Composio response as memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory from Composio response: {str(e)}")
            return None
    
    def build_memory_context(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build memory context for Composio requests
        
        Args:
            query: Query to search memories
            limit: Maximum number of memories to include
            memory_types: Types of memories to include
            
        Returns:
            Dict containing memory context
        """
        try:
            # Search memories
            memories = self.memory_manager.search_memories(
                query=query,
                limit=limit,
                memory_types=memory_types
            )
            
            # Format memories for Composio context
            memory_context = {
                "memories": [
                    {
                        "id": memory.get("id"),
                        "content": memory.get("content"),
                        "metadata": memory.get("metadata", {})
                    }
                    for memory in memories
                ],
                "conversation_history": self.memory_manager.get_conversation_history()
            }
            
            return memory_context
            
        except Exception as e:
            logger.error(f"Error building memory context: {str(e)}")
            return {"memories": [], "conversation_history": []}
    
    async def process_with_memory(
        self,
        prompt: str,
        system: Optional[str] = None,
        query: Optional[str] = None,
        memory_limit: int = 5,
        store_response: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Process a request with memory integration
        
        Args:
            prompt: User prompt or message
            system: Optional system message
            query: Memory search query (defaults to prompt if not provided)
            memory_limit: Maximum number of memories to include
            store_response: Whether to store the response in memory
            temperature: Model temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Composio response dict
        """
        # Use prompt as query if not provided
        memory_query = query or prompt
        
        # Build memory context
        memory_context = self.build_memory_context(
            query=memory_query,
            limit=memory_limit
        )
        
        # Process request with memory context
        response = await self.composio_client.process_request(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            memory_context=memory_context
        )
        
        # Store response in memory if requested
        if store_response and "error" not in response:
            await self.store_memory_from_response(
                response=response,
                metadata={"original_prompt": prompt}
            )
            
        return response
EOF
    
    echo "Created src/vot1/composio/memory_bridge.py"
    
    # Integration with VOT1 MCP
    cat > src/vot1/composio/integration.py << 'EOF'
"""
Composio Integration with VOT1 MCP

This module provides integration between VOT1's MCP and Composio's MCP.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from vot1.vot_mcp import VotModelControlProtocol
from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge

# Configure logging
logger = logging.getLogger(__name__)

def register_composio_with_vot_mcp(mcp: VotModelControlProtocol) -> None:
    """
    Register Composio tools with VOT MCP
    
    Args:
        mcp: The VOT MCP instance
    """
    # Ensure Composio client is available
    try:
        client = ComposioClient()
        bridge = ComposioMemoryBridge()
        
        # Register Composio-specific tools
        mcp.register_tool("composio_process", _handle_composio_process)
        mcp.register_tool("composio_memory_search", _handle_composio_memory_search)
        mcp.register_tool("composio_memory_store", _handle_composio_memory_store)
        
        logger.info("Composio tools registered with VOT MCP")
        
    except Exception as e:
        logger.error(f"Failed to register Composio with VOT MCP: {str(e)}")

# Tool handler implementations
async def _handle_composio_process(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle processing through Composio"""
    try:
        client = ComposioClient()
        prompt = tool_args.get("prompt", "")
        system = tool_args.get("system")
        temperature = tool_args.get("temperature", 0.7)
        max_tokens = tool_args.get("max_tokens", 1024)
        
        response = await client.process_request(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {"success": True, "result": response}
        
    except Exception as e:
        logger.error(f"Error in composio_process tool: {str(e)}")
        return {"success": False, "error": str(e)}

async def _handle_composio_memory_search(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle memory search through Composio"""
    try:
        bridge = ComposioMemoryBridge()
        query = tool_args.get("query", "")
        limit = tool_args.get("limit", 5)
        
        context = bridge.build_memory_context(query=query, limit=limit)
        
        return {"success": True, "memories": context.get("memories", [])}
        
    except Exception as e:
        logger.error(f"Error in composio_memory_search tool: {str(e)}")
        return {"success": False, "error": str(e)}

async def _handle_composio_memory_store(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle storing memory through Composio"""
    try:
        bridge = ComposioMemoryBridge()
        content = tool_args.get("content", "")
        metadata = tool_args.get("metadata", {})
        
        # Create a mock response structure that matches what would come from Composio
        mock_response = {
            "id": "memory_" + str(hash(content))[:8],
            "created": int(time.time()),
            "choices": [{"message": {"content": content}}]
        }
        
        memory_id = await bridge.store_memory_from_response(
            response=mock_response,
            metadata=metadata
        )
        
        return {"success": True, "memory_id": memory_id}
        
    except Exception as e:
        logger.error(f"Error in composio_memory_store tool: {str(e)}")
        return {"success": False, "error": str(e)}
EOF
    
    echo "Created src/vot1/composio/integration.py"
fi

echo "Composio MCP integration setup complete!"
echo
echo "Next steps:"
echo "1. Update your code to use the Composio MCP integration"
echo "2. Run 'python test_composio.py' to test the connection"
echo
echo "For more information, see the documentation in docs/composio_integration.md"
