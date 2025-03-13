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
    <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-3c1f3c?style=for-the-badge&logo=github" alt="Quick Start"></a>
    <a href="#-documentation"><img src="https://img.shields.io/badge/Documentation-5c3f5c?style=for-the-badge&logo=gitbook" alt="Documentation"></a>
    <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-6c4f9c?style=for-the-badge&logo=atom" alt="Architecture"></a>
    <a href="#-contributing"><img src="https://img.shields.io/badge/Contributing-1f3c3c?style=for-the-badge&logo=github" alt="Contributing"></a>
    <br>
    <img src="https://img.shields.io/github/license/kabrony/vot1?style=flat-square" alt="License">
    <img src="https://img.shields.io/github/last-commit/kabrony/vot1?style=flat-square" alt="Last Commit">
    <img src="https://img.shields.io/github/issues/kabrony/vot1?style=flat-square" alt="Issues">
    <img src="https://img.shields.io/github/stars/kabrony/vot1?style=flat-square" alt="Stars">
  </p>
</div>

<br>

## 📋 Overview

VOT1 is an advanced autonomous intelligence system that combines vector-based memory management, OWL reasoning capabilities, self-improvement workflows, and powerful integrations to create a system that learns and improves over time.

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-dashboard.png" alt="VOT1 Dashboard" width="80%">
</div>

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-key-features)
- [Quick Start](#-quick-start)
- [System Verification](#-system-verification)
- [Dashboard Navigation](#-dashboard-navigation)
- [GitHub Integration](#-github-integration)
- [Composio Integration](#-composio-integration)
- [OpenAPI Integration](#-openapi-integration)
- [Dashboard AI Chat](#-dashboard-ai-chat)
- [Documentation](#-documentation)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)

## 💫 About VOT1

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

## 🚀 Quick Start

### Prerequisites

Before getting started, ensure you have the following prerequisites installed:

- Python 3.9+ 
- Git
- Node.js 14+ (for dashboard)

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kabrony/vot1.git
   cd vot1
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Core dependencies
   pip install -r requirements.txt
   
   # GitHub integration (optional)
   pip install -r github_requirements.txt
   
   # Composio integration (optional but recommended)
   pip install -r composio_requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Open .env in your editor and configure:
   # - VOT1_PRIMARY_MODEL: Your preferred AI model
   # - VOT1_MEMORY_DIR: Directory for storing memories
   # - GITHUB_TOKEN: For GitHub integration
   # - COMPOSIO_API_KEY: For OpenAPI and enhanced features
   ```

5. **Start the VOT1 system**:
   ```bash
   python -m src.vot1.run_dashboard
   ```

6. **Access the dashboard**:
   Open your browser and navigate to `http://localhost:5000`

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

### Troubleshooting

If you encounter issues during installation or verification:

1. Check the logs in the `logs/` directory
2. Verify environment variables in your `.env` file
3. Ensure all dependencies are correctly installed
4. Refer to the [Troubleshooting Guide](docs/troubleshooting.md)

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
# Basic repository analysis
python -m scripts.run_github_analyzer analyze owner/repo

# Deep analysis with more comprehensive insights
python -m scripts.run_github_analyzer analyze --deep owner/repo
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
      <h4>📈 Code Quality Enhancements</h4>
      <p>Automated code improvements following best practices.</p>
    </td>
  </tr>
</table>

For more advanced usage, see the [GitHub Integration Guide](docs/github_integration.md).

## 🔌 Composio Integration

VOT1 supports integration with [Composio](https://composio.dev/) for enhanced capabilities:

```bash
# Run GitHub analysis with Composio integration
python -m scripts.run_github_bridge --composio analyze owner/repo

# Generate detailed dependency report with Composio
python -m scripts.run_github_bridge --composio analyze --focus=dependencies owner/repo

# Create PR with automatic improvements
python -m scripts.run_github_bridge --composio update owner/repo
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

The AI chat interface allows natural language interaction with VOT1, providing:

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

Comprehensive documentation is available for all VOT1 features:

- [Getting Started Guide](docs/getting_started.md)
- [Dashboard Usage](docs/dashboard.md)
- [Memory System](docs/memory_system.md)
- [AI Chat Interface](docs/dashboard_ai_chat.md)
- [External Integrations](docs/integrations.md)
- [API Reference](docs/api_reference.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development Guide](docs/development.md)

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

For more details about the architecture, see the [Architecture Documentation](docs/architecture.md).

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes** and commit them:
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📝 Changelog

For a detailed list of changes between versions, see our [CHANGELOG.md](CHANGELOG.md).

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
