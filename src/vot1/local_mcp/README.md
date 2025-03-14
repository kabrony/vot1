# VOTai Local MCP Bridge and Agent Ecosystem

```
__     _____ _____       _   
\ \   / / _ \_   _|____ (_)  
 \ \ / / | | || |/ _` | | |  
  \ V /| |_| || | (_| | | |  
   \_/  \___/ |_|\__,_|_|_|  
                             
 A New Dawn of a Holistic Paradigm
```

The VOTai Local MCP Bridge provides a local server that acts as a bridge between your applications and Model Context Protocol (MCP) services such as GitHub, Perplexity, Firecrawl, Figma, and Composio. The VOTai Agent Ecosystem extends this functionality with a multi-agent system for task execution and memory management.

## Features

### Local MCP Bridge
- **Local HTTP Server**: Exposes MCP functionality through a REST API
- **Service Connections**: Manages connections to various MCP services
- **Function Calling**: Enables calling MCP functions through a consistent interface
- **Caching**: Improves performance with response caching
- **Monitoring**: Provides performance metrics and status information

### VOTai Agent Ecosystem
- **Multi-Agent System**: Create and manage multiple agents with different capabilities
- **Agent Communication**: Connect agents and enable message passing between them
- **Task Execution**: Assign tasks to agents and retrieve responses
- **Memory Management**: Store, retrieve, and search shared memories
- **Extensible Architecture**: Add new agent types and capabilities easily

## Installation

The VOTai Local MCP Bridge and Agent Ecosystem are included as part of the VOT1 system. No additional installation is required.

## Configuration

The bridge uses a configuration file to determine the URLs for remote MCP services. By default, it looks for a file named `mcp.json` in the following locations:

1. `src/vot1/config/mcp.json`
2. `src/vot1/local_mcp/config/mcp.json`
3. `~/.cursor/mcp.json`
4. `~/.vot1/config/mcp.json`
5. `./mcp.json` (in the current working directory)

An example configuration file looks like this:

```json
{
  "mcpServers": {
    "GITHUB": {
      "url": "https://mcp.composio.dev/github/your-instance-id"
    },
    "PERPLEXITY": {
      "url": "https://mcp.composio.dev/perplexityai/your-instance-id"
    },
    "FIRECRAWL": {
      "url": "https://mcp.composio.dev/firecrawl/your-instance-id"
    },
    "FIGMA": {
      "url": "https://mcp.composio.dev/figma/your-instance-id"
    },
    "COMPOSIO": {
      "url": "https://mcp.composio.dev/composio/your-instance-id"
    }
  }
}
```

## Usage

### Starting the Bridge

You can start the Local MCP Bridge using the provided script:

```bash
python run_local_mcp_bridge.py
```

This will start a server on `localhost:5678` by default.

### Starting the Agent Ecosystem

You can start the Agent Ecosystem using the provided script:

```bash
python run_agent_ecosystem.py
```

This will start a server on `localhost:5678` by default. If the port is in use, it will automatically find an available port.

### Command-Line Options

The bridge and agent ecosystem support various command-line options:

```bash
python run_local_mcp_bridge.py --help
python run_agent_ecosystem.py --help
```

Common options include:

- `--host`: Host to bind to (default: localhost)
- `--port`: Port to bind to (default: 5678)
- `--config`: Path to MCP configuration file
- `--debug`: Run in debug mode
- `--find-port`: Automatically find an available port if the default is in use (agent ecosystem only)

### API Endpoints

#### Local MCP Bridge Endpoints

- `GET /api/check-connection/<service>`: Check if a connection to a service is active
- `GET /api/get-required-parameters/<service>`: Get the required parameters for connecting to a service
- `POST /api/initiate-connection/<service>`: Initiate a connection to a service
- `POST /api/call-function`: Call an MCP function
- `GET /api/status`: Get server status
- `GET /api/metrics`: Get performance metrics
- `POST /api/clear-cache`: Clear the response cache
- `GET /`: Health check endpoint

#### Agent Ecosystem Endpoints

- `GET /api/agents`: List all agents
- `POST /api/agents`: Create a new agent
- `GET /api/agents/<agent_id>`: Get agent details
- `DELETE /api/agents/<agent_id>`: Delete an agent
- `POST /api/agents/<agent_id>/connect`: Connect an agent to another agent
- `POST /api/agents/<agent_id>/disconnect`: Disconnect an agent from another agent
- `POST /api/agents/<agent_id>/message`: Send a message to an agent
- `GET /api/agents/<agent_id>/message`: Get messages for an agent
- `POST /api/agents/<agent_id>/task`: Add a task to an agent's queue
- `GET /api/agents/<agent_id>/response`: Get responses from an agent
- `POST /api/memory`: Store a memory
- `GET /api/memory/<key>`: Get a memory by key
- `POST /api/memory/search`: Search memories by tags
- `DELETE /api/memory/<key>`: Delete a memory

### Example: Creating and Using Agents

```bash
# Create a search agent
curl -X POST http://localhost:5678/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SearchAgent",
    "capabilities": ["search", "perplexity"]
  }'

# Get the agent ID from the response
AGENT_ID="agent-id-from-response"

# Add a search task to the agent
curl -X POST http://localhost:5678/api/agents/$AGENT_ID/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "query",
    "task_data": {
      "query": "What are the latest advancements in artificial intelligence?"
    }
  }'

# Get the responses from the agent
curl -X GET http://localhost:5678/api/agents/$AGENT_ID/response
```

## Testing

The system includes several test scripts to verify functionality:

### `test_memory_and_tasks.py`

Tests memory operations and task execution:

```bash
python test_memory_and_tasks.py
```

This script verifies:
- Memory storage, retrieval, and search
- Task execution for memory retrieval

### `test_ecosystem_integration.py`

Comprehensive integration test for the Agent Ecosystem:

```bash
python test_ecosystem_integration.py
```

This script tests:
- Server startup with port finding
- Agent creation, retrieval, and management
- Agent connections and messaging
- Memory operations
- Task execution across multiple agents
- Error handling and recovery

### `test_all_agents.py`

Tests all components of the agent ecosystem:

```bash
python test_all_agents.py
```

### `test_development_agent_tasks.py`

Tests the specialized DevelopmentAgent capabilities:

```bash
python test_development_agent_tasks.py
```

This script verifies:
- Creation of a DevelopmentAgent with specific capabilities
- Code generation task execution and response handling
- Code review task execution with customizable criteria
- Task completion and result retrieval

## Agent Types

The Agent Ecosystem includes several specialized agent types:

### FeedbackAgent

The base agent type that supports task execution, response handling, and message processing.

### DevelopmentAgent

A specialized agent for software development tasks, including:
- Code generation with language-specific settings
- Code review with customizable criteria
- Repository analysis for GitHub repositories
- Documentation generation
- Test creation and dependency analysis
- Code improvement suggestions
- PR analysis and evaluation

To create a DevelopmentAgent:

```bash
curl -X POST http://localhost:5678/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DevAgent",
    "capabilities": ["code_generation", "code_review", "repository_analysis"]
  }'
```

Example tasks for the DevelopmentAgent:

```bash
# Code generation task
curl -X POST http://localhost:5678/api/agents/$AGENT_ID/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "generate_code",
    "task_data": {
      "language": "python",
      "description": "Create a function to calculate fibonacci numbers",
      "requirements": ["Include error handling", "Use recursive approach"]
    }
  }'

# Code review task
curl -X POST http://localhost:5678/api/agents/$AGENT_ID/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "review_code",
    "task_data": {
      "language": "python",
      "code": "def fib(n):\n    return 1 if n <= 1 else fib(n-1) + fib(n-2)",
      "criteria": ["performance", "readability", "error handling"]
    }
  }'
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**: The system will automatically find an available port if the default port is in use
2. **Connection Failed**: Check that the service URL is correct in your `mcp.json` file
3. **Authentication Failed**: Make sure you've provided the correct API keys
4. **Function Not Found**: Verify that the function name is correct and follows the format `mcp_SERVICE_FUNCTION_NAME`

### Logs

The system logs are stored in the `logs` directory:

- `logs/local_mcp_bridge.log`: Logs from the bridge component
- `logs/local_mcp_server.log`: Logs from the server component
- `logs/agent_ecosystem.log`: Logs from the agent ecosystem
- `logs/test_*.log`: Logs from the test scripts

## License

This component is part of the VOT1 system and is subject to the same license terms. 