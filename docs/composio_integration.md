# Composio MCP Integration for VOT1

This document provides information about integrating Composio's Model Control Protocol (MCP) with VOT1's advanced memory system.

## Overview

VOT1 integrates with Composio's Model Control Protocol to enable advanced features:

1. **Advanced Memory Integration**: Bridge between VOT1's memory system and Composio MCP
2. **Multi-model Processing**: Use multiple models through a single API
3. **Enhanced Context Management**: Include memory context in model requests
4. **Tool Integration**: Execute tools through Composio MCP

## Setup

### Prerequisites

- Composio API Key and MCP URL (set in your `.env` file)
- Python 3.8+ with required packages installed

### Installation

1. Run the setup script:

```bash
./setup_mcp.sh
```

This script:
- Verifies your Composio credentials
- Creates necessary modules and directories
- Tests the connection to Composio MCP

### Configuration

In your `.env` file, ensure you have the following variables set:

```
COMPOSIO_API_KEY="your_api_key_here"
COMPOSIO_MCP_URL="https://mcp.composio.dev/your_account_path"
```

## Usage

### Basic Client Usage

```python
from vot1.composio.client import ComposioClient

# Create client
client = ComposioClient()

# Synchronous request
response = client.process_request_sync(
    prompt="How can I improve my memory system?",
    system="You are a helpful AI assistant."
)

# Asynchronous request
async def process_async():
    response = await client.process_request(
        prompt="How can I improve my memory system?",
        system="You are a helpful AI assistant."
    )
    print(response)
```

### Memory Integration

```python
from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.memory import MemoryManager

# Create memory manager and bridge
memory_manager = MemoryManager()
bridge = ComposioMemoryBridge(memory_manager=memory_manager)

# Process with memory integration
async def process_with_memory():
    response = await bridge.process_with_memory(
        prompt="What have we discussed about memory systems?",
        memory_limit=10,
        store_response=True
    )
    print(response)
```

### Integration with VOT MCP

```python
from vot1.vot_mcp import VotModelControlProtocol
from vot1.composio.integration import register_composio_with_vot_mcp

# Create VOT MCP instance
mcp = VotModelControlProtocol()

# Register Composio tools
register_composio_with_vot_mcp(mcp)

# Now VOT MCP can use Composio-specific tools
```

## Advanced Memory System

The integration provides several memory-related features:

### Memory Context Building

When making requests to Composio, relevant memories can be included as context:

```python
# Build memory context based on a query
context = bridge.build_memory_context(
    query="project planning",
    limit=5
)

# Include in request
response = await client.process_request(
    prompt="What should I focus on next?",
    memory_context=context
)
```

### Memory Storage

Responses from Composio can be automatically stored in the VOT1 memory system:

```python
# Store a response in memory
memory_id = await bridge.store_memory_from_response(
    response=composio_response,
    metadata={"category": "planning", "priority": "high"}
)
```

## Tool Integration

The following tools are available when using VOT MCP with Composio:

- `composio_process`: Process a request through Composio MCP
- `composio_memory_search`: Search memories through Composio MCP
- `composio_memory_store`: Store a memory through Composio MCP

Example tool definition:

```json
{
  "name": "composio_process",
  "description": "Process a request through Composio MCP",
  "parameters": {
    "type": "object",
    "properties": {
      "prompt": {
        "type": "string",
        "description": "The prompt to send to Composio"
      },
      "system": {
        "type": "string",
        "description": "Optional system message"
      }
    },
    "required": ["prompt"]
  }
}
```

## Troubleshooting

### Connection Issues

If you're having trouble connecting to Composio MCP:

1. Verify your API key and MCP URL in `.env`
2. Run `python test_composio.py` to test the connection
3. Check network connectivity and firewall settings

### Memory Integration Issues

If memory integration isn't working properly:

1. Check that your memory directory exists and is writeable
2. Verify that the memory manager is properly initialized
3. Check logs for specific error messages

## API Reference

For detailed API reference, see the docstrings in the following modules:

- `vot1.composio.client`: Composio MCP client
- `vot1.composio.memory_bridge`: Memory bridge between VOT1 and Composio
- `vot1.composio.integration`: Integration with VOT MCP 