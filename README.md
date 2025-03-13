<!-- 
VOT1: Village Of Thousands - Autonomous Intelligence System
==========================================================
-->

<div align="center">
  
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-banner.png" alt="VOT1 Banner" width="100%">

  # VOT1 Autonomous Intelligence System
  
  <p align="center">
    <b>Advanced Memory Management • OWL Reasoning • Self-Improvement • Hybrid Intelligence</b>
    <br><br>
    <a href="#installation"><img src="https://img.shields.io/badge/Installation-3c1f3c?style=for-the-badge&logo=github" alt="Installation"></a>
    <a href="#documentation"><img src="https://img.shields.io/badge/Documentation-5c3f5c?style=for-the-badge&logo=gitbook" alt="Documentation"></a>
    <a href="#architecture"><img src="https://img.shields.io/badge/Architecture-6c4f9c?style=for-the-badge&logo=atom" alt="Architecture"></a>
    <a href="#contributing"><img src="https://img.shields.io/badge/Contributing-1f3c3c?style=for-the-badge&logo=github" alt="Contributing"></a>
  </p>
</div>

<br>

## 📋 Overview

VOT1 is an advanced autonomous intelligence system that combines vector-based memory management, OWL reasoning capabilities, self-improvement workflows, and powerful integrations to create a system that learns and improves over time.

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-dashboard.png" alt="VOT1 Dashboard" width="80%">
</div>

## 💫 About Us

VOT1 is being developed by a multidisciplinary team passionate about creating the next generation of self-improving AI systems. We're building technology that combines the best of symbolic reasoning and vector-based representations with the ability to enhance its own code.

Our mission is to create AI systems that can:
- **Think about themselves**: Analyze their own performance and architecture
- **Reason over memories**: Connect information using formal ontologies
- **Evolve autonomously**: Generate and validate their own improvements
- **Explain their thinking**: Make AI operations transparent and understandable

For a deeper dive into our philosophy, technical innovations, and roadmap, check out our [ABOUT.md](ABOUT.md) file.

## 🔮 Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🧠 Advanced Memory Management</h3>
      <p>Vector-based memory system for storing and retrieving knowledge with semantic understanding and contextual relevance.</p>
    </td>
    <td width="50%">
      <h3>🦉 OWL Reasoning Engine</h3>
      <p>Logical reasoning using OWL (Web Ontology Language) standards for knowledge representation and inference.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔄 Self-Improvement Workflows</h3>
      <p>Automatic capability enhancement through memory-based learning and continuous adaptation.</p>
    </td>
    <td width="50%">
      <h3>💬 AI Chat Interface</h3>
      <p>Natural language interaction with the memory system and visualization for intuitive exploration.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔗 GitHub Integration</h3>
      <p>Two integration methods (MCP-based and Composio-based) for repository analysis and code improvement.</p>
    </td>
    <td width="50%">
      <h3>🌐 External API Integration</h3>
      <p>OpenAPI specification support through Composio for connecting to external services.</p>
    </td>
  </tr>
</table>

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/villageofthousands/vot1.git
   cd vot1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
   # For GitHub integration
   pip install -r github_requirements.txt
   
   # For Composio integration (optional but recommended)
   pip install -r composio_requirements.txt
   ```

3. Configure environment variables:
   ```bash
   # Core system
   export VOT1_PRIMARY_MODEL="anthropic/claude-3-7-sonnet-20240620"
   export VOT1_MEMORY_DIR="./memory"
   
   # GitHub integration
   export GITHUB_TOKEN="your_github_token"
   
   # Composio integration (for OpenAPI and enhanced GitHub features)
   export COMPOSIO_API_KEY="your_composio_api_key"
   ```

4. Start the VOT1 system:
   ```bash
   python -m src.vot1.run_dashboard
   ```

## 🔍 System Verification

To verify your installation and check the health of each component:

```bash
python -m scripts.run_system_check
```

This command will test:
- MCP connection status
- Memory management system
- OWL reasoning engine health
- Code analyzer functionality
- GitHub integration status
- Composio connectivity (if configured)

## 📊 Dashboard Navigation

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-dashboard-nav.png" alt="VOT1 Dashboard Navigation" width="80%">
</div>

The VOT1 dashboard provides several views:

1. **Overview**: Visualize the memory network and connections
2. **Memories**: Browse and search through stored memories
3. **Reasoning Engine**: Ask questions and see reasoning outputs
4. **Integrations**: Configure and use external integrations
5. **Settings**: Adjust visualization and system parameters

## 🐙 GitHub Integration

VOT1 offers comprehensive GitHub integration with repository analysis and automated updates:

### 1. GitHub Repository Analysis

Gain deep insights into repository structure, code quality, and potential improvements:

```bash
python -m scripts.run_github_analyzer analyze owner/repo  # Basic repository analysis
python -m scripts.run_github_analyzer analyze --deep owner/repo  # Deep analysis
```

### 2. GitHub Update Automation

The GitHub Update Automation feature allows VOT1 to analyze repositories and automatically create meaningful improvements:

```bash
# Create automated updates for a repository
python -m scripts.run_github_automation update --owner username --repo repository

# Run update with specific focus areas
python -m scripts.run_github_automation update --owner username --repo repository --areas documentation,workflows,dependencies,code_quality

# Run deep analysis before creating updates
python -m scripts.run_github_automation update --owner username --repo repository --deep-analysis
```

#### Key Features of GitHub Update Automation:

<table>
  <tr>
    <td width="50%">
      <h4>🔍 AI-Driven Analysis</h4>
      <p>Uses dual-model approach for thorough repository analysis with extended thinking capacity.</p>
    </td>
    <td width="50%">
      <h4>📊 3D Visualization</h4>
      <p>Interactive THREE.js visualization of repository updates and their relationships.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h4>📝 Documentation Updates</h4>
      <p>Automatic creation and improvement of READMEs, inline documentation, and API docs.</p>
    </td>
    <td width="50%">
      <h4>⚙️ Workflow Optimization</h4>
      <p>GitHub Actions, CI/CD, and development workflow improvements.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h4>🔄 Dependency Management</h4>
      <p>Updates and security audits for project dependencies.</p>
    </td>
    <td width="50%">
      <h4>💻 Code Quality Enhancements</h4>
      <p>Refactoring suggestions, performance improvements, and best practices.</p>
    </td>
  </tr>
</table>

#### Dashboard Integration:

The GitHub Update Automation is fully integrated into the VOT1 dashboard:

1. Navigate to the **Integrations** tab in the dashboard
2. Select the **GitHub** tab
3. Enter repository details and select update areas
4. View results with standard or 3D visualization
5. See AI reasoning and memory integration for context

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/github-automation.png" alt="GitHub Automation" width="80%">
</div>

### 3. MCP-based GitHub Integration

This integration uses VOT1's Model Control Protocol to analyze repositories:

```bash
python -m scripts.run_github_bridge status  # Check connection status
python -m scripts.run_github_bridge analyze owner/repo  # Analyze a repository
```

### 4. Composio-based GitHub Integration (Enhanced)

This integration provides advanced features through Composio:

```bash
# Check Composio connection
python -m scripts.run_github_bridge --composio status

# Analyze repository with enhanced features
python -m scripts.run_github_bridge --composio analyze owner/repo

# Run autonomous improvement cycle
python -m scripts.run_github_bridge --composio improve owner/repo
```

Benefits of Composio integration:
- Enhanced repository analysis with deeper insights
- Better code quality assessment
- Integration with multiple LLM models
- Support for autonomous improvement suggestions

You can specify LLM models for analysis:
```bash
python -m scripts.run_github_bridge --composio --model deepseek-r1 analyze owner/repo
```

## 🔌 OpenAPI Integration

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-openapi.png" alt="VOT1 OpenAPI Integration" width="80%">
</div>

VOT1 can interact with external APIs through OpenAPI specifications:

1. Navigate to the Integrations tab in the dashboard
2. Select the "Composio OpenAPI" tab
3. Upload an OpenAPI specification (YAML/JSON format)
4. Optionally provide authentication configuration
5. Use the imported tools via the dashboard or AI chat

See the [Integrations Documentation](docs/integrations.md) for more details.

## 💬 Dashboard AI Chat

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-chat.png" alt="VOT1 AI Chat" width="80%">
</div>

The AI chat interface allows natural language interaction with the VOT1, providing:

1. **Memory Exploration**: Ask questions about memories and receive contextual answers
2. **Visualization Control**: Use commands to focus, filter, or highlight parts of the visualization
3. **Integration Usage**: Interact with GitHub and OpenAPI integrations through natural language
4. **System Information**: Ask about system status and settings

### Example Chat Commands

Memory exploration:
```
What memories do you have about machine learning?
When was the last memory about data structures created?
```

Visualization commands:
```
Focus on memories related to Python
Highlight connections between web development and databases
Reset the visualization view
```

Integration usage:
```
Check the weather in San Francisco
Analyze the code quality of username/repo repository
```

## 📚 Documentation

- [Dashboard Usage](docs/dashboard.md)
- [Memory System](docs/memory_system.md)
- [AI Chat Interface](docs/dashboard_ai_chat.md)
- [External Integrations](docs/integrations.md)
- [API Reference](docs/api_reference.md)

## 🏗 Architecture

VOT1 consists of several main components:

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-architecture.png" alt="VOT1 Architecture" width="80%">
</div>

1. **Memory System**: Vector database and memory management
2. **MCP (Model Control Protocol)**: Coordination of AI model interactions
3. **OWL Reasoning Engine**: Logical inference and knowledge base management
4. **Visualization Engine**: THREE.js-based visualization of memory network
5. **Dashboard**: Web interface for system interaction
6. **AI Chat Interface**: Natural language interaction layer
7. **Integration Layer**: Connectors for GitHub, Composio, and other services

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Credits

- **MCP Hybrid Automation**: The MCP Hybrid API implementation was developed with assistance from Claude 3.7 Sonnet, an AI assistant by Anthropic. Claude helped design and implement the streaming response architecture and API integration for the dashboard.

<div align="center">
  <br>
  <p>
    <a href="https://villageofthousands.io"><img src="https://img.shields.io/badge/Powered_by-Village_of_Thousands-6c4f9c?style=for-the-badge&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cGF0aCBkPSJNMTIgMkM2LjQ3NyAyIDIgNi40NzcgMiAxMkMyIDE3LjUyMyA2LjQ3NyAyMiAxMiAyMkMxNy41MjMgMjIgMjIgMTcuNTIzIDIyIDEyQzIyIDYuNDc3IDE3LjUyMyAyIDEyIDJaTTEyIDIwQzcuNTkgMjAgNCAxNi40MSA0IDEyQzQgNy41OSA3LjU5IDQgMTIgNEMxNi40MSA0IDIwIDcuNTkgMjAgMTJDMjAgMTYuNDEgMTYuNDEgMjAgMTIgMjBaIiBmaWxsPSJ3aGl0ZSIvPgogIDxwYXRoIGQ9Ik0xMiAxMEw4IDdMOCAxN0wxMiAxNFYxMFoiIGZpbGw9IndoaXRlIi8+CiAgPHBhdGggZD0iTTEyIDEwTDE2IDdMMTYgMTdMMTIgMTRWMTBaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K" alt="Village of Thousands"></a>
  </p>
</div>

# VOT1 - Self-Improving Memory System

[![CI](https://github.com/villageofthousands/vot1/actions/workflows/ci.yml/badge.svg)](https://github.com/villageofthousands/vot1/actions/workflows/ci.yml)
[![Self-Improvement](https://github.com/villageofthousands/vot1/actions/workflows/self-improvement.yml/badge.svg)](https://github.com/villageofthousands/vot1/actions/workflows/self-improvement.yml)

VOT1 is an advanced AI system that evolves beyond traditional machine learning, combining vector-based memory management, OWL reasoning, and autonomous self-improvement capabilities. Our system doesn't just learn—it actively enhances its own architecture and algorithms through principled self-modification.

With an immersive THREE.js visualization dashboard, VOT1 makes complex AI operations visually intuitive, allowing developers and researchers to explore the system's "mind" in real-time as it processes, reasons, and improves.


VOT1 is being developed by a multidisciplinary team passionate about creating the next generation of self-improving AI systems. We're building technology that combines the best of symbolic reasoning and vector-based representations with the ability to enhance its own code.

Our mission is to create AI systems that can:
- **Think about themselves**: Analyze their own performance and architecture
- **Reason over memories**: Connect information using formal ontologies
- **Evolve autonomously**: Generate and validate their own improvements
- **Explain their thinking**: Make AI operations transparent and understandable

For a deeper dive into our philosophy, technical innovations, and roadmap, check out our [ABOUT.md](ABOUT.md) file.

## Key Features

- **Vector-based Memory Management**: Store and retrieve memories using vector embeddings for semantic similarity search with advanced clustering and contextual retrieval
- **OWL Reasoning Engine**: Apply ontology-based reasoning to memories and system components, enabling formal inference and inconsistency detection
- **Self-Improvement Workflows**: Automated analysis, code generation, and validation cycles that enhance system components without human intervention
- **THREE.js Dashboard**: Interactive 3D visualization of memory connections with cyberpunk aesthetic, providing an immersive way to explore the system's "mind"

## 📋 Overview

VOT1 is an advanced autonomous intelligence system that combines vector-based memory management, OWL reasoning capabilities, self-improvement workflows, and powerful integrations to create a system that learns and improves over time.

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-dashboard.png" alt="VOT1 Dashboard" width="80%">
</div>


VOT1 is being developed by a multidisciplinary team passionate about creating the next generation of self-improving AI systems. We're building technology that combines the best of symbolic reasoning and vector-based representations with the ability to enhance its own code.

Our mission is to create AI systems that can:
- **Think about themselves**: Analyze their own performance and architecture
- **Reason over memories**: Connect information using formal ontologies
- **Evolve autonomously**: Generate and validate their own improvements
- **Explain their thinking**: Make AI operations transparent and understandable

For a deeper dive into our philosophy, technical innovations, and roadmap, check out our [ABOUT.md](ABOUT.md) file.

## 🔮 Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🧠 Advanced Memory Management</h3>
      <p>Vector-based memory system for storing and retrieving knowledge with semantic understanding and contextual relevance.</p>
    </td>
    <td width="50%">
      <h3>🦉 OWL Reasoning Engine</h3>
      <p>Logical reasoning using OWL (Web Ontology Language) standards for knowledge representation and inference.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔄 Self-Improvement Workflows</h3>
      <p>Automatic capability enhancement through memory-based learning and continuous adaptation.</p>
    </td>
    <td width="50%">
      <h3>💬 AI Chat Interface</h3>
      <p>Natural language interaction with the memory system and visualization for intuitive exploration.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔗 GitHub Integration</h3>
      <p>Two integration methods (MCP-based and Composio-based) for repository analysis and code improvement.</p>
    </td>
    <td width="50%">
      <h3>🌐 External API Integration</h3>
      <p>OpenAPI specification support through Composio for connecting to external services.</p>
    </td>
  </tr>
</table>

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/villageofthousands/vot1.git
   cd vot1
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
   # For GitHub integration
   pip install -r github_requirements.txt
   
   # For Composio integration (optional but recommended)
   pip install -r composio_requirements.txt
   ```

3. Configure environment variables:
   ```bash
   # Core system
   export VOT1_PRIMARY_MODEL="anthropic/claude-3-7-sonnet-20240620"
   export VOT1_MEMORY_DIR="./memory"
   
   # GitHub integration
   export GITHUB_TOKEN="your_github_token"
   
   # Composio integration (for OpenAPI and enhanced GitHub features)
   export COMPOSIO_API_KEY="your_composio_api_key"
   ```

4. Start the VOT1 system:
   ```bash
   python -m src.vot1.run_dashboard
   ```

## 🔍 System Verification

To verify your installation and check the health of each component:

```bash
python -m scripts.run_system_check
```

This command will test:
- MCP connection status
- Memory management system
- OWL reasoning engine health
- Code analyzer functionality
- GitHub integration status
- Composio connectivity (if configured)

## 📊 Dashboard Navigation

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-dashboard-nav.png" alt="VOT1 Dashboard Navigation" width="80%">
</div>

The VOT1 dashboard provides several views:

1. **Overview**: Visualize the memory network and connections
2. **Memories**: Browse and search through stored memories
3. **Reasoning Engine**: Ask questions and see reasoning outputs
4. **Integrations**: Configure and use external integrations
5. **Settings**: Adjust visualization and system parameters

## 🐙 GitHub Integration

VOT1 offers comprehensive GitHub integration with repository analysis and automated updates:

### 1. GitHub Repository Analysis

Gain deep insights into repository structure, code quality, and potential improvements:

```bash
python -m scripts.run_github_analyzer analyze owner/repo  # Basic repository analysis
python -m scripts.run_github_analyzer analyze --deep owner/repo  # Deep analysis
```

### 2. GitHub Update Automation

The GitHub Update Automation feature allows VOT1 to analyze repositories and automatically create meaningful improvements:

```bash
# Create automated updates for a repository
python -m scripts.run_github_automation update --owner username --repo repository

# Run update with specific focus areas
python -m scripts.run_github_automation update --owner username --repo repository --areas documentation,workflows,dependencies,code_quality

# Run deep analysis before creating updates
python -m scripts.run_github_automation update --owner username --repo repository --deep-analysis
```

#### Key Features of GitHub Update Automation:

<table>
  <tr>
    <td width="50%">
      <h4>🔍 AI-Driven Analysis</h4>
      <p>Uses dual-model approach for thorough repository analysis with extended thinking capacity.</p>
    </td>
    <td width="50%">
      <h4>📊 3D Visualization</h4>
      <p>Interactive THREE.js visualization of repository updates and their relationships.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h4>📝 Documentation Updates</h4>
      <p>Automatic creation and improvement of READMEs, inline documentation, and API docs.</p>
    </td>
    <td width="50%">
      <h4>⚙️ Workflow Optimization</h4>
      <p>GitHub Actions, CI/CD, and development workflow improvements.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h4>🔄 Dependency Management</h4>
      <p>Updates and security audits for project dependencies.</p>
    </td>
    <td width="50%">
      <h4>💻 Code Quality Enhancements</h4>
      <p>Refactoring suggestions, performance improvements, and best practices.</p>
    </td>
  </tr>
</table>

#### Dashboard Integration:

The GitHub Update Automation is fully integrated into the VOT1 dashboard:

1. Navigate to the **Integrations** tab in the dashboard
2. Select the **GitHub** tab
3. Enter repository details and select update areas
4. View results with standard or 3D visualization
5. See AI reasoning and memory integration for context

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/github-automation.png" alt="GitHub Automation" width="80%">
</div>

### 3. MCP-based GitHub Integration

This integration uses VOT1's Model Control Protocol to analyze repositories:

```bash
python -m scripts.run_github_bridge status  # Check connection status
python -m scripts.run_github_bridge analyze owner/repo  # Analyze a repository
```

### 4. Composio-based GitHub Integration (Enhanced)

This integration provides advanced features through Composio:

```bash
# Check Composio connection
python -m scripts.run_github_bridge --composio status

# Analyze repository with enhanced features
python -m scripts.run_github_bridge --composio analyze owner/repo

# Run autonomous improvement cycle
python -m scripts.run_github_bridge --composio improve owner/repo
```

Benefits of Composio integration:
- Enhanced repository analysis with deeper insights
- Better code quality assessment
- Integration with multiple LLM models
- Support for autonomous improvement suggestions

You can specify LLM models for analysis:
```bash
python -m scripts.run_github_bridge --composio --model deepseek-r1 analyze owner/repo
```

## 🔌 OpenAPI Integration

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-openapi.png" alt="VOT1 OpenAPI Integration" width="80%">
</div>

VOT1 can interact with external APIs through OpenAPI specifications:

1. Navigate to the Integrations tab in the dashboard
2. Select the "Composio OpenAPI" tab
3. Upload an OpenAPI specification (YAML/JSON format)
4. Optionally provide authentication configuration
5. Use the imported tools via the dashboard or AI chat

See the [Integrations Documentation](docs/integrations.md) for more details.

## 💬 Dashboard AI Chat

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-chat.png" alt="VOT1 AI Chat" width="80%">
</div>

The AI chat interface allows natural language interaction with the VOT1, providing:

1. **Memory Exploration**: Ask questions about memories and receive contextual answers
2. **Visualization Control**: Use commands to focus, filter, or highlight parts of the visualization
3. **Integration Usage**: Interact with GitHub and OpenAPI integrations through natural language
4. **System Information**: Ask about system status and settings

### Example Chat Commands

Memory exploration:
```
What memories do you have about machine learning?
When was the last memory about data structures created?
```

Visualization commands:
```
Focus on memories related to Python
Highlight connections between web development and databases
Reset the visualization view
```

Integration usage:
```
Check the weather in San Francisco
Analyze the code quality of username/repo repository
```

## 📚 Documentation

- [Dashboard Usage](docs/dashboard.md)
- [Memory System](docs/memory_system.md)
- [AI Chat Interface](docs/dashboard_ai_chat.md)
- [External Integrations](docs/integrations.md)
- [API Reference](docs/api_reference.md)

## 🏗 Architecture

VOT1 consists of several main components:

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-architecture.png" alt="VOT1 Architecture" width="80%">
</div>

1. **Memory System**: Vector database and memory management
2. **MCP (Model Control Protocol)**: Coordination of AI model interactions
3. **OWL Reasoning Engine**: Logical inference and knowledge base management
4. **Visualization Engine**: THREE.js-based visualization of memory network
5. **Dashboard**: Web interface for system interaction
6. **AI Chat Interface**: Natural language interaction layer
7. **Integration Layer**: Connectors for GitHub, Composio, and other services

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Credits

- **MCP Hybrid Automation**: The MCP Hybrid API implementation was developed with assistance from Claude 3.7 Sonnet, an AI assistant by Anthropic. Claude helped design and implement the streaming response architecture and API integration for the dashboard.

<div align="center">
  <br>
  <p>
    <a href="https://villageofthousands.io"><img src="https://img.shields.io/badge/Powered_by-Village_of_Thousands-6c4f9c?style=for-the-badge&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cGF0aCBkPSJNMTIgMkM2LjQ3NyAyIDIgNi40NzcgMiAxMkMyIDE3LjUyMyA2LjQ3NyAyMiAxMiAyMkMxNy41MjMgMjIgMjIgMTcuNTIzIDIyIDEyQzIyIDYuNDc3IDE3LjUyMyAyIDEyIDJaTTEyIDIwQzcuNTkgMjAgNCAxNi40MSA0IDEyQzQgNy41OSA3LjU5IDQgMTIgNEMxNi40MSA0IDIwIDcuNTkgMjAgMTJDMjAgMTYuNDEgMTYuNDEgMjAgMTIgMjBaIiBmaWxsPSJ3aGl0ZSIvPgogIDxwYXRoIGQ9Ik0xMiAxMEw4IDdMOCAxN0wxMiAxNFYxMFoiIGZpbGw9IndoaXRlIi8+CiAgPHBhdGggZD0iTTEyIDEwTDE2IDdMMTYgMTdMMTIgMTRWMTBaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4K" alt="Village of Thousands"></a>
  </p>
</div> 
