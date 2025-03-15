# VOT1 Composio Memory Integration

This module integrates VOT1's memory system with Claude 3.7 via Composio's Model Control Protocol (MCP).

## Overview

The Composio integration provides advanced memory capabilities leveraging Claude 3.7's enhanced features:

- Extended context windows (up to 200K tokens)
- Advanced thinking and reflection capabilities
- Hybrid memory retrieval strategies
- Graph-based memory relationships
- Memory importance scoring and filtering

## Components

### ComposioMemoryBridge

The primary bridge between VOT1's memory system and Composio MCP.

**Key Features:**
- Memory retrieval with hybrid strategies (semantic + temporal)
- Advanced memory reflection and metacognition
- Optimized memory context formatting
- Graph-based memory relationship traversal
- Performance tracking and metrics

### ComposioClient

Client for interacting with the Composio MCP service.

**Key Features:**
- Supports hybrid processing mode (local planning + remote execution)
- Handles extended token contexts
- Manages streaming responses
- Optimized for Claude 3.7 capabilities

### EnhancedMemoryManager

Extended memory manager with advanced memory operations.

**Key Features:**
- Graph-based memory storage and retrieval
- Memory importance scoring
- Memory relationship management
- Advanced memory search and filtering

## Usage

```python
from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.composio.client import ComposioClient

# Initialize components
client = ComposioClient()
memory_bridge = ComposioMemoryBridge(composio_client=client)

# Process a request with memory integration
async def example():
    response = await memory_bridge.process_with_memory(
        prompt="What have we discussed about memory systems?",
        memory_limit=10,
        memory_retrieval_strategy="hybrid",
        hybrid_mode=True,
        thinking=True
    )
    print(response["choices"][0]["message"]["content"])
    
    # Use hybrid processing for complex tasks
    hybrid_response = await memory_bridge.process_with_hybrid_memory(
        prompt="Analyze our past conversations for patterns and insights",
        memory_limit=20
    )
    
    # Perform advanced memory reflection
    reflection = await memory_bridge.advanced_memory_reflection(
        query="memory systems",
        reflection_depth="deep"
    )
```

## Benefits of Claude 3.7 Integration

1. **Extended Context Window**: Utilize Claude 3.7's 200K token context window for more comprehensive memory inclusion
2. **Enhanced Thinking**: Leverage Claude 3.7's improved thinking capabilities for deeper memory analysis
3. **Hybrid Processing**: Combine local planning with remote execution for optimized memory operations
4. **Advanced Memory Operations**: Support for metacognitive reflection on memories

## Memory System Architecture

The memory system integrates three key components:

1. **Storage Layer**: Vector storage for semantic embeddings
2. **Graph Layer**: Relationship management between memories
3. **Access Layer**: Optimized retrieval and integration strategies

This architecture enables efficient retrieval, relationship tracking, and context integration for Claude 3.7's expanded capabilities. 