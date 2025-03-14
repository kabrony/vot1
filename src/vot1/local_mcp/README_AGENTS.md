# VOTai Agent Ecosystem

```
__     _____ _____       _   
\ \   / / _ \_   _|____ (_)  
 \ \ / / | | || |/ _` | | |  
  \ V /| |_| || | (_| | | |  
   \_/  \___/ |_|\__,_|_|_|  
                             
 A New Dawn of a Holistic Paradigm
```

The VOTai Agent Ecosystem extends the Local MCP Bridge with multi-agent communication and coordination capabilities. This system allows you to create, connect, and manage specialized agents that can perform tasks and share information within the VOTai holistic paradigm.

## Overview

The VOTai Agent Ecosystem consists of the following core components:

1. **MCPOrchestrator**: Coordinates communication between agents, manages agent states, and provides shared memory.
2. **AgentState**: Represents the state of an agent, including its capabilities, connections, and messages.
3. **FeedbackAgent**: An implementation of an agent that can perform tasks and communicate with other agents.
4. **Agent API**: A RESTful API for managing agents, sending tasks, and retrieving results.

## Features

- Agent creation, management, and deletion
- Inter-agent communication
- Task processing by specialized agents
- Shared memory system for storing and retrieving data
- Event-based communication
- API for agent interaction from outside the system

## Running the VOTai Agent Ecosystem

To start the VOTai Agent Ecosystem, use the `run_agent_ecosystem.py` script:

```bash
python src/vot1/local_mcp/run_agent_ecosystem.py --find-port
```

Options:
- `--host`: Host to bind to (default: localhost)
- `--port`: Port to bind to (default: 5678)
- `--debug`: Run in debug mode
- `--find-port`: Find an available port if the specified port is in use

### Initializing Default Agents

Once the ecosystem is running, you can initialize a set of default agents using the `initialize_agents.py` script:

```bash
python src/vot1/local_mcp/initialize_agents.py
```

This script will:
1. Create four specialized agents (SearchAgent, RepositoryAgent, WebAgent, and AnalysisAgent)
2. Establish connections between the agents
3. Store default memories with agent capabilities and task routing information

Options:
- `--host`: Host where the agent ecosystem is running (default: localhost)
- `--port`: Port where the agent ecosystem is running (default: 5678)
- `--clean`: Clean existing agents before initialization (not implemented yet)

## Agent Types and Capabilities

By default, the VOTai Agent Ecosystem creates four types of agents with different capabilities:

1. **SearchAgent**: Capable of performing web searches using Perplexity.
   - Capabilities: `search`, `perplexity`

2. **RepositoryAgent**: Analyzes GitHub repositories.
   - Capabilities: `github`, `code_analysis`

3. **WebAgent**: Scrapes and extracts data from web pages.
   - Capabilities: `web_scraping`, `firecrawl`

4. **AnalysisAgent**: Processes data and manages memory.
   - Capabilities: `data_analysis`, `memory`

## API Endpoints

### Agent Management

- `GET /api/agents`: List all registered agents
- `POST /api/agents`: Create a new agent
- `GET /api/agents/{agent_id}`: Get agent details
- `DELETE /api/agents/{agent_id}`: Delete an agent

### Agent Communication

- `POST /api/agents/{agent_id}/connect`: Connect an agent to another agent
- `POST /api/agents/{agent_id}/disconnect`: Disconnect an agent from another agent
- `POST /api/agents/{agent_id}/message`: Send a message to an agent

### Task Management

- `POST /api/agents/{agent_id}/task`: Add a task to an agent's queue
- `GET /api/agents/{agent_id}/response`: Get responses from an agent

### Memory Operations

- `POST /api/memory`: Store a memory
- `GET /api/memory/{key}`: Retrieve a memory
- `POST /api/memory/search`: Search memories by tags

## Example Usage

### Creating an Agent

```bash
curl -X POST http://localhost:5678/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "MyAgent", "capabilities": ["search", "memory"]}'
```

### Sending a Task to an Agent

```bash
curl -X POST http://localhost:5678/api/agents/{agent_id}/task \
  -H "Content-Type: application/json" \
  -d '{"task_type": "query", "task_data": {"query": "What is machine learning?"}}'
```

### Retrieving Agent Responses

```bash
curl -X GET http://localhost:5678/api/agents/{agent_id}/response
```

## Task Types

Agents can handle various types of tasks:

- **query**: Perform a web search
- **analyze_repo**: Analyze a GitHub repository
- **scrape_url**: Scrape a URL and extract content
- **process_search_results**: Process search results and extract URLs
- **memory**: Perform memory operations (store, retrieve)
- **call_function**: Call an MCP function directly

## Testing the VOTai Agent Ecosystem

You can test the VOTai Agent Ecosystem using the provided test script:

```bash
python src/vot1/local_mcp/test_agent_ecosystem.py
```

This script will:
1. Create a test agent
2. Store a memory
3. Add a task to retrieve the memory
4. Get responses from the agent
5. Clean up by deleting the agent

## Quick Start Guide

To quickly get the agent ecosystem up and running with default agents:

1. Start the agent ecosystem server:
   ```bash
   python src/vot1/local_mcp/run_agent_ecosystem.py --find-port
   ```

2. Initialize the default agents:
   ```bash
   python src/vot1/local_mcp/initialize_agents.py
   ```

3. Test the functionality:
   ```bash
   python src/vot1/local_mcp/test_agent_ecosystem.py
   ```

## Programmatic Usage

You can also use the VOTai Agent Ecosystem programmatically in your Python code:

```python
from src.vot1.local_mcp.agent import FeedbackAgent
from src.vot1.local_mcp.orchestrator import MCPOrchestrator
from src.vot1.local_mcp.bridge import LocalMCPBridge

# Create a bridge
bridge = LocalMCPBridge()

# Create an orchestrator
orchestrator = MCPOrchestrator(bridge)

# Create an agent
agent = FeedbackAgent(orchestrator, "MyAgent", ["search"])

# Add a task
task_id = agent.add_task("query", {"query": "What is machine learning?"})

# Get responses
responses = agent.wait_for_responses(timeout=10.0)
print(responses)
```

## Architecture

The VOTai Agent Ecosystem follows a modular architecture:

- **Bridge Layer**: Connects to external MCP services
- **Orchestration Layer**: Manages agents and their communication
- **Agent Layer**: Implements the agent behavior and task processing
- **API Layer**: Exposes the agent functionality through HTTP endpoints

## Files Overview

The VOTai Agent Ecosystem consists of the following files:

- `orchestrator.py`: Contains the `MCPOrchestrator` and `AgentState` classes
- `agent.py`: Contains the `FeedbackAgent` class
- `server_agents.py`: Contains the API endpoints for agent management
- `server.py`: Contains the main server functionality
- `run_agent_ecosystem.py`: Script to start the agent ecosystem
- `test_agent_ecosystem.py`: Script to test the agent ecosystem
- `initialize_agents.py`: Script to initialize default agents
- `port_finder.py`: Utility to find available ports
- `bridge.py`: Contains the `LocalMCPBridge` class
- `ascii_art.py`: Contains the VOTai ASCII art representations
- `README_AGENTS.md`: Documentation for the agent ecosystem (this file)

## Troubleshooting

### Port in Use

If the default port (5678) is already in use, use the `--find-port` option:

```bash
python src/vot1/local_mcp/run_agent_ecosystem.py --find-port
```

### API Key Issues

If you encounter authentication errors with external services, check your API keys:

1. Create a `.env` file in the `src/vot1/local_mcp` directory
2. Add your API keys in the format: `SERVICE_API_KEY=your_api_key_here`

### Debugging

To enable debug logging, use the `--debug` flag:

```bash
python src/vot1/local_mcp/run_agent_ecosystem.py --debug
```

Log files are stored in the `logs` directory.

## VOTai Integration

The VOTai ecosystem provides a holistic approach to agent-based systems, representing a new dawn in multi-agent coordination and communication. Each agent in the ecosystem displays the VOTai signature upon initialization, visually unifying the components of the system.

To access the VOTai ASCII art in your own code:

```python
from src.vot1.local_mcp.ascii_art import get_votai_ascii

# Get the VOTai ASCII art in different sizes
small_ascii = get_votai_ascii("small")
medium_ascii = get_votai_ascii("medium")
large_ascii = get_votai_ascii("large")
minimal_ascii = get_votai_ascii("minimal")

print(medium_ascii)
```