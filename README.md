# VOT1 - TRILOGY BRAIN

VOT1 (Voice of Truth 1) is an advanced distributed AI memory system built on principles of transparency, integrity, and scalability. The TRILOGY BRAIN is its core architecture, integrating neuromimetic processing, blockchain verification, and distributed computing.

## Overview

The VOT1 system implements a principles-driven distributed memory architecture that combines advanced AI techniques with blockchain technology. The TRILOGY BRAIN architecture (Executive Cortex, Associative Network, and Memory Foundation) provides a robust framework for memory storage, retrieval, and processing.

![TRILOGY BRAIN Architecture](docs/trilogy_brain_architecture.png)

## Key Features

- **Distributed Memory System**: Scalable and resilient memory storage across distributed nodes
- **Neuromimetic Processing**: Brain-inspired architecture with specialized memory types
- **Blockchain Integration**: Secure memory verification using Solana blockchain
- **Zero-Knowledge Proofs**: Memory integrity verification without revealing content
- **Principles-Aligned Design**: All operations adhere to system principles for ethical use
- **Claude 3.7 Integration**: Enhanced memory capabilities leveraging Claude 3.7's 200K token context window and hybrid processing
- **MCP Integration**: Complete integration with Claude 3.7 through a comprehensive Model Control Protocol
- **Immersive 3D UI**: Modern Three.js visualization for system monitoring and interaction

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+ (for web interface)
- Modern web browser with WebGL support
- For full functionality:
  - Solana CLI tools
  - Claude 3.7 API access

### Installation

1. Clone the repository:

```bash
git clone https://github.com/organix/vot1.git
cd vot1
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env file with your API keys and configuration
```

## Usage

### Running the TRILOGY BRAIN Web Interface

The most user-friendly way to interact with the VOT1 system is through the TRILOGY BRAIN web interface:

```bash
python src/vot1/ui/web_server.py
```

This will start the web server on http://127.0.0.1:8080 and open a browser window. The interface provides:

- 3D visualization of the memory network
- Node management
- Memory exploration
- System monitoring

### Command Line Interface

The VOT1 system can also be interacted with through the command line:

```bash
python -m vot1.cli.main
```

For help on available commands:

```bash
python -m vot1.cli.main --help
```

### API Usage with Claude 3.7 Integration

The VOT1 system leverages Claude 3.7's advanced capabilities through its enhanced memory bridge:

```python
from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge

# Initialize the Composio client with Claude 3.7
client = ComposioClient(
    model="claude-3-7-sonnet-20240620",
    hybrid_mode=True,
    max_thinking_tokens=120000
)

# Initialize the enhanced memory bridge
memory_bridge = ComposioMemoryBridge(
    composio_client=client,
    use_enhanced_memory=True
)

# Process a request with advanced memory integration
async def example():
    # Basic memory integration
    response = await memory_bridge.process_with_memory(
        prompt="What is the TRILOGY BRAIN architecture?",
        memory_limit=10,
        memory_retrieval_strategy="hybrid",
        thinking=True
    )
    
    # Advanced memory reflection
    reflection = await memory_bridge.advanced_memory_reflection(
        query="memory systems",
        reflection_depth="deep"
    )
    
    # Hybrid processing mode
    hybrid_response = await memory_bridge.process_with_hybrid_memory(
        prompt="Analyze the key components of neuromimetic processing",
        memory_limit=20
    )
```

## System Architecture

The VOT1 system consists of several core components:

1. **Memory System**: Responsible for storing, organizing, and retrieving memories
   - Vector Store: Efficient embedding-based memory storage
   - Memory Manager: Coordinates memory operations
   - Memory Bridge: Connects memory system to Composio MCP with enhanced Claude 3.7 capabilities
   - Memory Reflection: Advanced memory analysis using Claude 3.7's thinking capabilities

2. **Blockchain Integration**: Provides security and verification
   - Solana Memory Agent: Interfaces with Solana blockchain
   - ZK-Verification Agent: Generates and verifies zero-knowledge proofs
   - Consensus Agent: Coordinates distributed operations

3. **TRILOGY BRAIN**: The core architectural framework
   - Executive Cortex: Resource allocation and decision-making
   - Associative Network: Manages relationships between memories
   - Memory Foundation: Primary storage layer

4. **User Interfaces**:
   - Web Interface: Three.js visualization and control panel
   - CLI: Command-line tools for system management
   - API: Programmatic access for integration

## Claude 3.7 Memory Integration

The VOT1 system integrates with Claude 3.7 to provide enhanced memory capabilities:

### Key Enhancements

- **Extended Context Window**: Utilize Claude 3.7's 200K token context window for comprehensive memory inclusion
- **Hybrid Memory Retrieval**: Combine semantic, temporal, and importance-based strategies for optimal memory retrieval
- **Advanced Memory Reflection**: Leverage Claude 3.7's thinking capabilities for deeper memory analysis and pattern detection
- **Graph-Based Memory Relationships**: Create and traverse sophisticated memory relationship graphs
- **Memory Importance Scoring**: Prioritize memories based on relevance and importance metrics
- **Hybrid Processing Mode**: Combine local planning with remote execution for complex memory operations

### Memory Retrieval Strategies

The system supports multiple retrieval strategies optimized for different use cases:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `semantic` | Pure semantic search based on embeddings | Finding conceptually related memories |
| `temporal` | Time-based retrieval prioritizing recency | Recent conversation context |
| `hybrid` | Combined semantic + temporal with importance scoring | General-purpose retrieval |

For detailed documentation, see [Claude 3.7 Memory Integration](docs/claude_3.7_memory_integration.md).

## Development

### Project Structure

```
vot1/
├── docs/                       # Documentation
│   └── claude_3.7_memory_integration.md  # Claude 3.7 technical specification
├── examples/                   # Example scripts
│   └── claude_3.7_memory_example.py      # Claude 3.7 usage examples
├── src/                        # Source code
│   └── vot1/
│       ├── blockchain/         # Blockchain integration
│       ├── cli/                # Command-line interface
│       ├── composio/           # Claude 3.7 integration via Composio MCP
│       │   ├── memory_bridge.py         # Enhanced memory bridge
│       │   ├── client.py                # Composio client
│       │   └── enhanced_memory.py       # Enhanced memory manager
│       ├── core/               # Core system components
│       ├── distributed/        # Distributed system components
│       ├── memory/             # Memory system
│       ├── research/           # R&D experiments
│       └── ui/                 # User interfaces
├── tests/                      # Test suite
├── .env                        # Environment variables
└── requirements.txt            # Python dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

VOT1 - TRILOGY BRAIN - © 2025 Organix - All rights reserved

## Acknowledgments

- Claude 3.7 for advanced AI capabilities and memory operations
- Composio MCP for model control protocol integration
- Solana blockchain for secure memory verification
- Three.js for immersive visualization 