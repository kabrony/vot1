# VOTai Repository Organization Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Repository Structure](#repository-structure)
3. [Agent System](#agent-system)
   - [Development Agent](#development-agent)
   - [Agent Memory System](#agent-memory-system)
   - [Orchestration](#orchestration)
4. [MCP Bridge](#mcp-bridge)
5. [GitHub Integration](#github-integration)
6. [Memory Management](#memory-management)
7. [Dashboard and APIs](#dashboard-and-apis)
8. [Development Workflow](#development-workflow)
9. [Best Practices](#best-practices)

## Introduction

VOTai is a holistic AI ecosystem designed to provide advanced agent capabilities, memory management, and integration services. This guide provides an overview of the repository structure, the agent system, and the key components that make up the VOTai platform.

## Repository Structure

The VOTai repository is organized as follows:

```
/home/vots/vot1/
├── assets/                # Static assets for documentation, etc.
├── docs/                  # Documentation files and guides
├── examples/              # Example code and use cases
├── logs/                  # Log files for various components
├── memory/                # Memory storage directory
├── scripts/               # Utility scripts
├── src/                   # Main source code
│   └── vot1/
│       ├── cli/           # Command-line interface
│       ├── config/        # Configuration files
│       ├── core/          # Core functionality
│       ├── dashboard/     # Web dashboard
│       ├── github/        # GitHub specific functionality
│       ├── integrations/  # External service integrations
│       ├── local_mcp/     # Local MCP Bridge
│       ├── security/      # Security-related code
│       ├── tests/         # Unit and integration tests
│       └── utils/         # Utility functions
├── templates/             # Template files
└── tests/                 # System-level tests
```

## Agent System

The VOTai Agent System provides a flexible framework for creating and managing AI agents with specific capabilities. The system is composed of several key components:

### Development Agent

The Development Agent (`/home/vots/vot1/src/vot1/local_mcp/development_agent.py`) is a specialized agent designed for software development tasks, including:

- Code generation
- Repository analysis
- Code review
- Pull request analysis
- Ecosystem analysis
- Performance analysis
- Recommendations

The Development Agent extends the base `FeedbackAgent` class and implements task handlers for each supported task type. It uses the `AgentMemoryManager` to track its activities, store knowledge, and manage tasks.

#### Key Features

- Task management and tracking
- Performance metrics collection
- Knowledge storage and retrieval
- Advanced memory management
- GitHub integration

### Agent Memory System

The Agent Memory System (`/home/vots/vot1/src/vot1/local_mcp/agent_memory_manager.py`) extends the base Memory Manager to provide agent-specific memory capabilities, including:

- Activity logging
- Task tracking
- Performance metrics storage
- Knowledge management
- Memory indexing for faster retrieval

This system enables agents to store and retrieve information about their activities, tasks, and knowledge, providing a comprehensive memory system for the agent ecosystem.

#### Memory Categories

- `agent_activities`: Records of agent activities
- `agent_tasks`: Task data and status
- `agent_metrics`: Performance metrics
- `agent_knowledge`: Knowledge gained by agents
- `ecosystem_status`: Status of the agent ecosystem

### Orchestration

The Agent Orchestrator (`/home/vots/vot1/src/vot1/local_mcp/orchestrator.py`) manages the agent ecosystem, providing:

- Agent registration and lifecycle management
- Inter-agent communication
- Task distribution
- Shared memory access
- API call routing

## MCP Bridge

The MCP (Model Context Protocol) Bridge provides a standardized interface for connecting Large Language Models (LLMs) to external tools and services. The VOTai implementation includes:

- Local MCP Bridge: A local implementation of the MCP protocol
- Server implementation: A Flask-based server for exposing MCP functionality
- Agent integration: MCP-enabled agents that can call external services

## GitHub Integration

The GitHub Integration module (`/home/vots/vot1/src/vot1/local_mcp/github_integration.py`) provides a seamless interface for interacting with GitHub APIs, enabling:

- Repository analysis
- Pull request analysis
- Commit retrieval
- Issue creation and management

The integration supports both direct GitHub API access and a mock GitHub server for local testing.

## Memory Management

The Memory Manager (`/home/vots/vot1/src/vot1/memory.py`) provides a comprehensive memory management system for storing and retrieving structured data. Key features include:

- Category-based organization
- Caching for improved performance
- Full-text search capabilities
- Memory statistics and monitoring

The Agent Memory Manager extends this system with agent-specific capabilities for tracking agent activities, storing agent states, and managing advanced memory features.

## Dashboard and APIs

The VOTai Dashboard (`/home/vots/vot1/src/vot1/dashboard/`) provides a web-based interface for interacting with the VOTai ecosystem, including:

- Agent management
- Task monitoring
- Memory exploration
- Performance metrics visualization
- API endpoints for programmatic access

## Development Workflow

To work effectively with the VOTai repository, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/vot1.git
   cd vot1
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Start the Local MCP Bridge server**:
   ```bash
   python -m src.vot1.local_mcp.server
   ```

4. **Run the Development Agent**:
   ```bash
   python -m src.vot1.local_mcp.development_agent
   ```

5. **Start the Dashboard**:
   ```bash
   python -m src.vot1.dashboard
   ```

## Best Practices

When working with the VOTai repository, follow these best practices:

1. **Organized Code**: Follow the existing directory structure and organization patterns
2. **Memory First**: Use the memory management system for storing and retrieving data
3. **Agent-Based Design**: Design new features as agent capabilities when appropriate
4. **Comprehensive Testing**: Write tests for new features and ensure they pass
5. **Documentation**: Document your code and update this guide when needed
6. **Memory Tracking**: Use the `AgentMemoryManager` to track agent activities and tasks
7. **Metrics Collection**: Collect and analyze performance metrics
8. **Error Handling**: Implement proper error handling and logging
9. **Security**: Follow security best practices, especially when dealing with external services
10. **Modularization**: Design modular and reusable components 