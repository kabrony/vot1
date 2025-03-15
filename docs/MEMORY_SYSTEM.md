# VOT1 Advanced Memory System

This document describes the advanced memory system architecture for the VOT1 project, which provides sophisticated memory management capabilities for AI agents using Claude 3.7.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Memory Components](#memory-components)
- [Composio MCP Integration](#composio-mcp-integration)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)

## Overview

The VOT1 Advanced Memory System provides a comprehensive solution for managing AI memory, enabling agents to store, retrieve, and reason with various types of memories. The system leverages graph-based memory representations, semantic search, and the powerful Claude 3.7 model through Composio MCP integration.

Key features:
- Hierarchical memory organization (episodic, semantic, procedural)
- Graph-based memory representation for relationships between memories
- Memory consolidation and summarization
- Temporal and contextual memory retrieval
- Integration with Composio MCP and Claude 3.7 
- Support for hybrid streaming with local thinking capabilities

## Architecture

The memory system architecture consists of several key components:

1. **Core Memory Manager**: Base memory management functionality (`MemoryManager`)
2. **Enhanced Memory Manager**: Advanced graph-based memory capabilities (`EnhancedMemoryManager`)
3. **Memory Bridge**: Integration with Composio MCP (`ComposioMemoryBridge`)
4. **Composio Client**: Client for interacting with Composio MCP (`ComposioClient`)

### System Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│   VOT1 Agent    │────▶│  Memory Bridge   │────▶│ Composio MCP   │
└─────────────────┘     └──────────────────┘     └────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│ Memory Manager  │◀───▶│ Enhanced Memory  │     │   Claude 3.7   │
└─────────────────┘     └──────────────────┘     └────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│ File Storage    │     │  Memory Graph    │
└─────────────────┘     └──────────────────┘
```

## Memory Components

### Memory Types

The system supports various types of memories:

- **Semantic Memory**: Factual knowledge and information
- **Episodic Memory**: Event-based memories with temporal context
- **Procedural Memory**: Skills, processes, and how-to knowledge
- **Conceptual Memory**: Abstract concepts and their relationships
- **Consolidated Memory**: Synthesized information from multiple memories

### Memory Graph

The memory graph represents the relationships between different memories, enabling:

- Contextual memory retrieval based on relationships
- Discovery of related memories through graph traversal
- Importance weighting of memories and relationships
- Temporal organization of memories

## Composio MCP Integration

The memory system integrates with Composio MCP through the `ComposioMemoryBridge`, allowing:

- Enhanced memory retrieval using Claude 3.7's capabilities
- Memory-augmented processing of user requests
- Memory consolidation through advanced reasoning
- Planning with memory context

### Hybrid Streaming

The system supports hybrid streaming, where:

1. Initial thinking is performed using a local model
2. Final processing is done with Claude 3.7 through Composio MCP
3. Memory context is provided to both phases

## Usage Examples

### Basic Usage

```python
from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.composio.enhanced_memory import EnhancedMemoryManager

# Initialize components
memory_manager = EnhancedMemoryManager(memory_path="memory")
composio_client = ComposioClient(
    api_key="your_api_key",
    mcp_url="your_mcp_url",
    default_model="claude-3-7-sonnet"
)

# Create memory bridge
memory_bridge = ComposioMemoryBridge(
    memory_manager=memory_manager,
    composio_client=composio_client
)

# Process a request with memory
response = await memory_bridge.process_with_memory(
    prompt="What can you tell me about quantum computing?",
    store_response=True
)

# Retrieve memories on a specific topic
memories = memory_manager.search_memories(
    query="quantum computing",
    limit=5
)

# Consolidate memories on a topic
consolidated = await memory_bridge.consolidate_memories(
    topic="quantum computing",
    max_memories=10
)
```

### Planning with Memory

```python
# Create a plan with memory context
plan = await memory_bridge.plan_with_memory(
    goal="Build a quantum computing simulator",
    context="The simulator should be educational and visual."
)
```

## Advanced Features

### Memory Consolidation

Memory consolidation processes multiple memories to create a synthesized understanding:

```python
# Consolidate memories on a topic
consolidated = await memory_bridge.consolidate_memories(
    topic="artificial intelligence",
    max_memories=20
)

# Access the consolidated information
print(f"Summary: {consolidated['content']}")
print(f"Key themes: {consolidated['themes']}")
print(f"Key insights: {consolidated['key_insights']}")
```

### Graph-Based Memory Operations

The memory graph enables sophisticated memory operations:

```python
# Get related memories from the graph
related_memories = memory_manager.get_related_memories(
    memory_id="some_memory_id",
    relation_types=["similar_to", "precedes"],
    max_depth=2
)

# Visualize the memory graph
memory_manager.visualize_memory_graph(
    central_memory_id="some_memory_id",
    max_depth=3,
    output_path="memory_graph.png"
)
```

## Configuration

The memory system can be configured through various parameters:

### Memory Manager Configuration

```python
memory_manager = EnhancedMemoryManager(
    memory_path="custom/memory/path",
    vector_db_path="custom/vector/db/path",
    conversation_memory_size=100,
    importance_threshold=0.5
)
```

### Composio Client Configuration

```python
composio_client = ComposioClient(
    api_key="your_api_key",
    mcp_url="your_mcp_url",
    default_model="claude-3-7-sonnet",
    max_thinking_tokens=10000,
    hybrid_local_model="llama-3-1-8b"
)
```

### Memory Bridge Configuration

```python
memory_bridge = ComposioMemoryBridge(
    memory_manager=memory_manager,
    composio_client=composio_client,
    use_enhanced_memory=True,
    memory_path="memory",
    graph_db_path="memory/graph/memory_graph.db"
)
```

## Performance Considerations

- Memory search operations are optimized but can be resource-intensive with large memory stores
- Graph operations scale with the number of nodes and edges
- Memory consolidation involves LLM processing and can take time for large memory sets

For large-scale deployments, consider:
- Implementing memory pruning strategies
- Using database sharding for large memory stores
- Setting appropriate importance thresholds to filter less relevant memories

## License

The VOT1 Advanced Memory System is released under the same license as the VOT1 project. 