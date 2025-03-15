# TRILOGY BRAIN Memory Systems

<div align="center">
  <img src="https://via.placeholder.com/800x200/3A1078/FFFFFF?text=TRILOGY+BRAIN" alt="TRILOGY BRAIN" width="100%" />
  <p><em>Advanced memory systems for Large Language Models</em></p>
</div>

## Overview

TRILOGY BRAIN is a cognitive architecture for large language models that implements advanced memory systems, reasoning frameworks, and enhanced interaction capabilities. This repository contains the implementation of two key memory systems:

1. **CascadingMemoryCache** - Infinite context extension via cascading KV cache
2. **EpisodicMemoryManager** - Human-like episodic memory organization

Together, these systems enable Claude 3.7 to maintain effectively unlimited context while organizing information in a cognitively-inspired way.

## Key Components

### CascadingMemoryCache

The `CascadingMemoryCache` implements a novel approach to memory management based on the paper "Training-Free Exponential Context Extension via Cascading KV Cache" (Willette et al., Feb 2025). It enables effectively infinite context through hierarchical memory organization with:

- **Multi-level memory caching** with exponentially increasing capacity
- **Importance-based retention policies** that vary by level
- **Adaptive compression** to optimize token usage
- **Smart context building** based on importance, recency, and query relevance

[Learn more about CascadingMemoryCache](docs/CascadingMemoryCache.md)

### EpisodicMemoryManager

The `EpisodicMemoryManager` implements human-like episodic memory organization with:

- **Event boundary detection** using Bayesian surprise
- **Temporal organization** of memories into coherent episodes
- **Importance-based memory consolidation** for long-term retention
- **Multi-scale retrieval strategies** that balance temporal and semantic relationships

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trilogy-brain.git
cd trilogy-brain

# Install dependencies
pip install -r requirements.txt
```

### Usage Example

```python
from src.vot1.memory.cascading_cache import CascadingMemoryCache
from src.vot1.memory.episodic_memory import EpisodicMemoryManager

# Initialize memory systems
cascading_cache = CascadingMemoryCache(
    cascade_levels=3,
    base_cache_size=4096,
    token_budget=200000  # Claude 3.7 context size
)

# Process a memory
result = await cascading_cache.process_memory(
    memory={
        "id": "mem_12345",
        "content": "Important information to remember",
        "timestamp": time.time(),
        "importance": 0.8
    }
)

# Build context for a query
context = cascading_cache.build_context(
    query="information to remember",
    token_budget=150000
)

# Use the formatted context
formatted_context = context["formatted_context"]
```

## Performance Results

The memory systems have been extensively tested and shown to provide significant benefits:

- **Token Efficiency**: 2-3x improvement over standard caching approaches
- **Memory Retention**: >85% retention of important memories
- **Processing Speed**: <1ms average memory processing time 
- **Context Quality**: High relevance scores across different query types

[View detailed performance results](docs/CascadingMemoryCache_Results.md)

## Documentation

- [CascadingMemoryCache Documentation](docs/CascadingMemoryCache.md)
- [Performance Report](docs/CascadingMemoryCache_Results.md)

## Testing

Run the test suite for the CascadingMemoryCache:

```bash
python scripts/test_cascading_cache.py --memory-count 100
```

This will generate a detailed performance report in the `data` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Claude 3.7 Sonnet for implementation assistance and documentation generation
- The ideas in this project were inspired by research in cognitive psychology, memory systems, and large language model augmentation

<div align="center">
  <p>Developed with 💜 by the TRILOGY BRAIN team</p>
</div>

# VOTai System

VOTai is an advanced AI system that integrates Composio tools, Claude 3.7 Sonnet, and Perplexity for powerful hybrid reasoning and research capabilities.

## Key Features

- **Composio Integration**: Seamlessly connect with the Composio ecosystem to discover and execute external tools.
- **Claude 3.7 Sonnet Support**: Leverage the latest Claude model with hybrid thinking capabilities and a 15K token context window.
- **Advanced Memory System**: Persistent memory with semantic search and hybrid reasoning capabilities.
- **Deep Web Research**: Integrated Perplexity client for comprehensive research with citation tracking.
- **Streaming Support**: Efficient streaming responses for long-running processes.
- **Tool Execution**: Register and execute tools with parameter validation and error handling.

## Getting Started

### Installation

   ```bash
pip install votai
   ```

Or for development:

   ```bash
git clone https://github.com/your-username/votai.git
cd votai
pip install -e .
```

### Basic Usage

```python
import asyncio
from vot1.initialize import initialize_system

async def main():
    # Initialize the system
    system = await initialize_system()
    
    # Get components
    claude = await system.get_claude_client()
    composio = await system.get_composio_client()
    perplexity = await system.get_perplexity_client()
    memory = await system.get_memory_bridge()
    
    # Generate a response with Claude
    response = await claude.generate(
        prompt="Explain the concept of hybrid thinking in AI systems.",
        with_thinking=True
    )
    
    print(response)

# Run the example
asyncio.run(main())
```

## Hybrid Research Example

The system combines Claude's reasoning with Perplexity's web research:

```python
from vot1.examples.hybrid_research import HybridResearcher

async def research_example():
    researcher = HybridResearcher()
    
    results = await researcher.research_and_analyze(
        topic="Advances in quantum computing in 2024",
        depth="deep",
        with_hybrid_thinking=True
    )
    
    print(results["summary"])
    print(results["analysis"])

asyncio.run(research_example())
```

## Components

### Composio Client

The Composio client allows for discovery and execution of tools from the Composio ecosystem.

```python
async def composio_example():
    system = await initialize_system()
    composio = await system.get_composio_client()
    
    # List available tools
    tools = await composio.list_tools()
    
    # Execute a tool
    result = await composio.execute_tool(
        tool_id="example-tool",
        parameters={"param1": "value"}
    )
    
    print(result)
```

### Memory Bridge

The memory bridge provides advanced memory capabilities with semantic search and hybrid thinking.

```python
async def memory_example():
    system = await initialize_system()
    memory = await system.get_memory_bridge()
    
    # Store a memory
    await memory.store_memory(
        content="Important information to remember",
        memory_type="observation",
        metadata={"importance": "high"}
    )
    
    # Retrieve memories
    memories = await memory.retrieve_memories(
        query="important information",
        memory_types=["observation"],
        max_results=5
    )
    
    # Use hybrid thinking
    thinking_results = await memory.hybrid_thinking(
        prompt="Analyze the relationship between A and B",
        max_iterations=3
    )
    
    print(thinking_results["response"])
```

## Environment Variables

The system uses the following environment variables:

- `ANTHROPIC_API_KEY`: API key for Claude
- `COMPOSIO_API_KEY`: API key for Composio
- `COMPOSIO_INTEGRATION_ID`: Integration ID for Composio
- `PERPLEXITY_API_KEY`: API key for Perplexity
- `VOTAI_LOG_LEVEL`: Logging level (debug, info, warning, error)

## Advanced Configuration

You can customize the system behavior using a configuration file:

```json
{
  "memory": {
    "max_items": 2000,
    "max_tokens_per_memory": 1000,
    "enable_hybrid_thinking": true
  },
  "claude": {
    "model": "claude-3-7-sonnet-20240708",
    "max_tokens": 15000
  },
  "perplexity": {
    "model_name": "llama-3-sonar-large-online"
  }
}
```

Then initialize the system with the configuration:

```python
system = await initialize_system(config_path="config.json")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Enhanced Research Agent with TRILOGY BRAIN

An advanced research agent powered by Claude and Perplexity, with autonomous health monitoring, self-repair capabilities, and the innovative TRILOGY BRAIN memory system.

## Features

- **Hybrid Thinking**: Combines Claude's reasoning with Perplexity's real-time web search capabilities
- **TRILOGY BRAIN Memory System**: Consolidates insights and maintains a continuous learning feedback loop
- **Autonomous System Health Monitoring**: Self-checks and repairs system components
- **Environment Variable Management**: Easily configurable via `.env` file
- **Extensible Architecture**: Modular design for easy customization and extension

## Requirements

- Python 3.8+
- API keys for:
  - Anthropic (for Claude)
  - Perplexity (for web searches)
  - GitHub (optional, for code searches)
  - Composio (optional, for MCP integration)

## Quick Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/enhanced-research-agent.git
cd enhanced-research-agent
```

2. Run the setup script to create a virtual environment and install dependencies:
```bash
./setup_venv.sh
```

3. Activate the virtual environment:
```bash
source venv/bin/activate
```

4. Edit the `.env` file created by the setup script to add your API keys.

5. Run the agent:
```bash
python enhanced_research_agent.py --topic "Your research topic" --focus "Your research focus"
```

## Detailed Setup

### Manual Environment Setup

If you prefer to set up the environment manually:

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install the required packages:
```bash
pip install --upgrade pip
pip install anthropic python-dotenv perplexipy requests
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Edit the `.env` file to add your API keys and configuration.

### Configuration Options

The agent can be configured through environment variables in the `.env` file:

#### Required API Keys
- `ANTHROPIC_API_KEY`: API key for Anthropic's Claude
- `PERPLEXITY_API_KEY`: API key for Perplexity AI

#### Optional API Keys
- `GITHUB_TOKEN`: GitHub access token for code search capabilities
- `COMPOSIO_API_KEY`: API key for Composio integration
- `COMPOSIO_MCP_URL`: MCP URL for Composio

#### System Configuration
- `MEMORY_PATH`: Path for agent memory storage (default: `memory/agent`)
- `HEALTH_CHECK_INTERVAL`: Interval for health checks in seconds (default: `60`)
- `ENABLE_AUTO_REPAIR`: Whether to enable automatic system repairs (default: `true`)
- `ENABLE_AUTONOMOUS_MODE`: Whether to enable autonomous mode (default: `false`)

#### Model Configuration
- `CLAUDE_MODEL`: Claude model to use (default: `claude-3-7-sonnet-20250219`)
- `CLAUDE_MAX_TOKENS`: Maximum output tokens for Claude (default: `4096`)
- `CLAUDE_TEMPERATURE`: Temperature for Claude (default: `0.7`)
- `PERPLEXITY_MODEL`: Perplexity model to use (default: `llama-3.1-sonar-large-128k-online`)
- `PERPLEXITY_MAX_TOKENS`: Maximum output tokens for Perplexity (default: `4096`)
- `PERPLEXITY_TEMPERATURE`: Temperature for Perplexity (default: `0.7`)

#### TRILOGY BRAIN Configuration
- `TRILOGY_BRAIN_ENABLED`: Whether to enable TRILOGY BRAIN (default: `true`)
- `TRILOGY_BRAIN_MEMORY_PATH`: Path for TRILOGY BRAIN memory storage (default: `memory/trilogy`)
- `TRILOGY_BRAIN_CONSOLIDATION_INTERVAL`: Interval for memory consolidation in seconds (default: `3600`)
- `TRILOGY_BRAIN_FEEDBACK_THRESHOLD`: Threshold for feedback triggering consolidation (default: `5`)

## Usage

### Basic Usage

To perform research on a topic:

```bash
python enhanced_research_agent.py --topic "Quantum computing advancements" --focus "Recent breakthroughs"
```

### Advanced Options

```bash
python enhanced_research_agent.py --topic "Your topic" --focus "Your focus" --depth 3 --format json --output output/research_results.json
```

Parameters:
- `--topic`: The main research topic
- `--focus`: Specific focus area within the topic
- `--depth`: Research depth (1-5, default: 2)
- `--format`: Output format (markdown, json, text, default: markdown)
- `--language`: Programming language for code examples (if applicable)
- `--output`: Output file path (default: automatically generated)
- `--no-web`: Disable web research
- `--no-code`: Disable code search
- `--health-check`: Run a system health check and exit

### System Health Monitoring

To run a system health check:

```bash
python trilogy_health_monitor.py --check-only
```

To start continuous health monitoring:

```bash
python trilogy_health_monitor.py
```

Options:
- `--check-interval`: Interval for health checks in seconds
- `--no-auto-repair`: Disable automatic system repairs
- `--no-notifications`: Disable notifications
- `--check-only`: Perform a single health check and exit
- `--repair`: Perform a system repair and exit
- `--report`: Show system health report and exit

## System Architecture

The Enhanced Research Agent consists of several key components:

1. **Core Agent**: Manages the research process and coordinates other components
2. **Claude Client**: Provides reasoning and synthesis capabilities
3. **Perplexity Client**: Performs web searches and retrieves information
4. **TRILOGY BRAIN**: Memory system that consolidates insights and enables continuous learning
5. **Health Monitor**: Monitors system health and performs automatic repairs

## TRILOGY BRAIN

The TRILOGY BRAIN memory system is a sophisticated component that:

- Stores and consolidates research results and insights
- Analyzes patterns across multiple research sessions
- Provides feedback for continuous agent improvement
- Streams health data for system monitoring
- Enables autonomous learning and adaptation

## Troubleshooting

If you encounter issues:

1. Check that your API keys are correct in the `.env` file
2. Ensure Python 3.8+ is installed and accessible
3. Run `python trilogy_health_monitor.py --check-only` to diagnose system issues
4. Check the logs in `trilogy_health.log` for detailed error information
5. Make sure all dependencies are installed by running `pip install -r requirements.txt`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Anthropic for the Claude AI model
- Perplexity AI for their web search capabilities
- Contributors to the open-source libraries used in this project

# Knowledge Graph Visualization with Claude 3.7 Sonnet

This project demonstrates the use of Claude 3.7 Sonnet for knowledge graph construction and interactive visualization using THREE.js.

## IMPORTANT: Always Use Latest Claude Model

This project is designed to work with Claude 3.7 Sonnet, which provides exceptional reasoning capabilities for complex tasks. The current recommended model identifier is:

```
claude-3-7-sonnet-20250219
```

**NEVER DOWNGRADE** to older models as they offer inferior reasoning capabilities and may lack important features.

## Features

- Knowledge graph construction from research data
- Interactive 3D visualization using THREE.js
- Leverages Claude 3.7 Sonnet's advanced hybrid reasoning
- Supports multiple graph types: standard, detailed, technical, THREE.js-optimized

## Environment Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install required packages:
   ```
   pip install anthropic python-dotenv
   ```

3. Set up your `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   VOT1_PRIMARY_MODEL=claude-3-7-sonnet-20250219
   ```

## Running the Test

Execute the test script to generate a knowledge graph and visualization:

```
python test_kg_visualization.py
```

The script will:
1. Connect to Claude 3.7 Sonnet
2. Generate a knowledge graph from sample research data
3. Create interactive THREE.js visualizations
4. Save outputs to the `output/test_kg/` directory

## Output Files

- `knowledge_graph.json`: The generated knowledge graph data
- `visualization/graph_visualization.html`: Basic THREE.js visualization
- `visualization/complete_visualization.html`: Enhanced visualization with full graph data

## Implementation Notes

This project currently uses anthropic-python SDK version 0.49.0, which does not yet support the `extended_thinking` parameter. Future SDK releases may include support for Claude 3.7 Sonnet's extended thinking capabilities.

## Planned Improvements

- Integration with the extended_thinking parameter when SDK support is added
- Enhanced error handling for complex JSON structures
- More customization options for THREE.js visualizations

## License

MIT

# VOT1 Unified Dashboard

A comprehensive dashboard interface integrating file visualization, memory systems, modular component platform (MCP), and an AI assistant with hybrid reasoning capabilities.

## Features

- **Unified Dashboard Interface**: Modern cyberpunk-themed interface integrating all components
- **3D File Structure Visualization**: Interactive THREE.js visualization of project structure
- **Modular Component Platform (MCP)**: Connect to various tools and manage processing nodes
- **TRILOGY BRAIN Memory System**: Advanced neural-symbolic memory with visual graph representation
- **AI Assistant with Hybrid Thinking**: Claude 3.7 Sonnet-based assistant that can show its reasoning process
- **Real-time Updates**: Socket.io-based real-time updates for all components

## Integrated Tools

- **GitHub**: Repository access and management
- **Perplexity AI**: Advanced search and question answering
- **Figma**: Design file access and asset management
- **Firecrawl**: Web scraping and data extraction

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/vot1.git
   cd vot1
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env file with your API keys and settings
   ```

## Usage

Start the dashboard server:
```
python server.py
```

Or with specific host and port:
```
python server.py --host 127.0.0.1 --port 8000
```

Access the dashboard at http://localhost:5000 (or the host/port you specified).

## Dashboard Components

### File Structure Visualization

Interactive 3D visualization of your project's file structure. Features include:
- Depth control for visualization detail
- Interactive node selection for details
- Different visualization styles (sphere/cube nodes, colors by file type)

### MCP (Modular Component Platform)

Manage modular components and external tools:
- Start/stop processing nodes
- Connect to external tools like GitHub, Perplexity, etc.
- View node status and capabilities

### TRILOGY BRAIN Memory System

Advanced memory architecture with:
- Various memory types (facts, concepts, code, etc.)
- Interactive memory graph visualization
- Semantic search capabilities

### AI Assistant

Claude 3.7 Sonnet-powered AI assistant with:
- Hybrid reasoning mode to show thinking process
- Integration with all dashboard components
- Context-aware responses

## Development

### Project Structure

```
vot1/
├── config/               # Configuration files
├── static/               # Static assets (CSS, JS, images)
│   ├── css/              # CSS styles
│   ├── js/               # JavaScript files
│   └── img/              # Image assets
├── templates/            # HTML templates
├── visualization/        # File structure visualization
├── server.py             # Flask server
├── dashboard.py          # Dashboard application
└── requirements.txt      # Python dependencies
```

### Adding New Components

To add a new component to the dashboard:

1. Create a new component script in `static/js/`
2. Register the component in `dashboard.js`
3. Add corresponding routes in `server.py`
4. Update the UI in `templates/index.html`

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [THREE.js](https://threejs.org/) for 3D visualization
- [D3.js](https://d3js.org/) for memory graph visualization
- [Flask](https://flask.palletsprojects.com/) and [Flask-SocketIO](https://flask-socketio.readthedocs.io/) for server components
- [Anthropic Claude](https://www.anthropic.com/claude) for the AI assistant capabilities