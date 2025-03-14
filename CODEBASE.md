<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-codebase-banner.png" alt="VOT1 Codebase" width="100%">
  
  <h1>VOT1 Codebase Structure</h1>
  
  <p align="center">
    <b>Autonomous Intelligence System Architecture & Organization</b>
  </p>
</div>

## 📂 Directory Structure

```
vot1/
├── assets/              # Static assets for the project
├── docs/                # Documentation files
├── memory/              # Memory storage directory
├── scripts/             # Utility scripts
├── src/                 # Source code
│   └── vot1/
│       ├── dashboard/   # Web dashboard UI
│       ├── integrations/# External system integrations
│       ├── mcp/         # Model Control Protocol
│       ├── memory/      # Memory management system
│       ├── owl/         # OWL reasoning engine
│       └── utils/       # Utility functions
├── tests/               # Test suite
└── tools/               # Development tools
```

## 🧩 Core Components

### 🧠 Memory Management System

**Location**: `src/vot1/memory/`

The Memory Management System is responsible for storing, retrieving, and managing memories using vector embeddings. It includes:

- **Vector Store** - Storage and efficient retrieval of vector-based memories
- **Memory Manager** - High-level interface for creating and updating memories
- **Context Builder** - Creates relevant context from retrieved memories
- **Embedding Service** - Generates embeddings from text/data

Key files:
- `memory_manager.py` - Core memory management class
- `vector_store.py` - Vector database integration
- `embedding.py` - Text embedding utilities
- `context.py` - Context building from memories

<div align="center" style="padding: 10px; margin: 20px 0; background-color: #3c1f3c; border-radius: 5px;">
  <p style="color: #f9f9fb;">The memory system uses a hybrid approach combining semantic vector search with metadata filtering for optimal retrieval.</p>
</div>

### 🦉 OWL Reasoning Engine

**Location**: `src/vot1/owl/`

The OWL Reasoning Engine provides logical reasoning capabilities using Web Ontology Language standards. It includes:

- **Ontology Manager** - Manages OWL ontologies
- **Reasoner** - Performs logical inference
- **Knowledge Base** - Stores facts and relationships
- **Query Engine** - Interface for querying the knowledge base

Key files:
- `reasoner.py` - Core reasoning implementation
- `ontology.py` - Ontology management
- `knowledge_base.py` - Fact storage and retrieval
- `query.py` - Query processing

<div align="center" style="padding: 10px; margin: 20px 0; background-color: #1f3c3c; border-radius: 5px;">
  <p style="color: #f9f9fb;">The reasoning engine supports both Description Logic and Rule-based reasoning approaches.</p>
</div>

### 🎮 Model Control Protocol (MCP)

**Location**: `src/vot1/mcp/`

The Model Control Protocol coordinates interactions with AI models, providing a unified interface for:

- **Model Selection** - Choosing appropriate models for tasks
- **Prompting** - Structured prompt creation and management
- **Response Processing** - Parsing and processing model outputs
- **Hybrid Automation** - Managing multiple models in tandem

Key files:
- `mcp_controller.py` - Core MCP controller
- `prompt_templates.py` - Structured prompt templates
- `model_registry.py` - Available model registry
- `hybrid_automation.py` - Hybrid model automation

<div align="center" style="padding: 10px; margin: 20px 0; background-color: #6c4f9c; border-radius: 5px;">
  <p style="color: #f9f9fb;">MCP enables dynamic model selection based on task complexity, context, and performance history.</p>
</div>

### 🌐 Dashboard

**Location**: `src/vot1/dashboard/`

The Dashboard provides a web interface for interacting with VOT1, including:

- **Visualization** - Memory network visualization
- **Chat Interface** - Natural language interaction
- **Management Controls** - System configuration
- **Integration Management** - External system integration controls

Key files:
- `server.py` - Flask server setup
- `api.py` - API endpoints
- `static/` - CSS, JavaScript, and other static assets
- `templates/` - HTML templates

<div align="center" style="padding: 10px; margin: 20px 0; background-color: #5c3f5c; border-radius: 5px;">
  <p style="color: #f9f9fb;">The dashboard uses THREE.js for 3D visualization of the memory network, providing an immersive way to explore relationships.</p>
</div>

### 🔌 Integrations

**Location**: `src/vot1/integrations/`

The Integrations module provides connections to external systems:

- **GitHub** - Repository analysis and code improvement
- **Composio** - OpenAPI integration
- **Authentication** - Authentication for external services
- **Data Extraction** - Utilities for extracting data from APIs

Key files:
- `github/` - GitHub integration
- `composio/` - Composio API client
- `openapi.py` - OpenAPI specification handling
- `auth.py` - Authentication utilities

## 🔄 Data Flow

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-data-flow.png" alt="VOT1 Data Flow" width="80%">
</div>

1. **Input Processing** - User inputs or system events are processed
2. **Memory Retrieval** - Relevant memories are retrieved
3. **Context Building** - Context is constructed from memories
4. **Reasoning** - Logical reasoning is applied to the context
5. **Model Interaction** - MCP coordinates model interactions
6. **Response Generation** - Responses are generated and returned
7. **Memory Update** - New information is stored in memory

## 🧪 Testing Approach

**Location**: `tests/`

Our testing approach includes:

- **Unit Tests** - Testing individual components
- **Integration Tests** - Testing component interactions
- **E2E Tests** - Testing full system workflows
- **Simulation Tests** - Testing self-improvement capabilities

Key testing files:
- `test_memory.py` - Memory system tests
- `test_reasoning.py` - Reasoning engine tests
- `test_mcp.py` - MCP tests
- `test_integration.py` - Integration tests

## 🛠️ Development Tools

**Location**: `tools/`

Development tools to assist with:

- **Data Generation** - Tools for generating test data
- **Benchmarking** - Performance measurement
- **Visualization** - Development visualizations
- **Analysis** - Code and performance analysis

## 🌱 Getting Started

To understand how the components work together, we recommend:

1. Start with the `scripts/run_dashboard.py` file to see system initialization
2. Explore the `memory_manager.py` to understand memory management
3. Check out `mcp_controller.py` to understand model interaction
4. Look at `dashboard/server.py` to understand the web interface

## 📊 Performance Considerations

- Memory system is optimized for retrieval speed using HNSW indexes
- OWL reasoning uses incremental reasoning for efficiency
- Dashboard uses WebSockets for real-time updates
- MCP implements batching for efficient model usage

<div align="center" style="padding: 15px; margin: 30px 0; background-color: #3c1f3c; border-radius: 10px; border: 1px solid #6c4f9c;">
  <h3 style="color: #f9f9fb; margin-top: 0;">💡 Contribution Tip</h3>
  <p style="color: #f9f9fb;">When modifying the codebase, consider the interaction between components. Changes to the memory system may affect reasoning capabilities and dashboard visualization.</p>
</div>

---

<div align="center">
  <p>
    <sub>This document is maintained by the VOT1 Core Team. Last updated: July 2024</sub>
  </p>
</div> 