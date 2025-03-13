# <div align="center">📚 VOT1 Documentation</div>

<link rel="stylesheet" href="assets/custom.css">

<div align="center">
  
<img src="../docs/assets/vot1-docs-header.png" alt="VOT1 Documentation" width="600"/>

</div>

<p align="center">
  <b>Welcome to the comprehensive documentation for VOT1, a powerful, open-source integration system for AI models with advanced memory management, GitHub integration, and visualization capabilities.</b>
</p>

<div align="center">
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-core-features">Features</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-examples">Examples</a> •
  <a href="#-advanced-topics">Advanced</a>
</div>

<div class="grid-container">
  <div class="grid-item" onclick="window.location='guides/quickstart.md'">
    <h2>🚀 Quick Start</h2>
    <p>Get up and running with VOT1 in minutes</p>
  </div>
  <div class="grid-item" onclick="window.location='dashboard_ai_chat.md'">
    <h2>💬 AI Chat</h2>
    <p>Interact with the AI assistant in the dashboard</p>
  </div>
  <div class="grid-item" onclick="window.location='github_integration.md'">
    <h2>🤖 GitHub Integration</h2>
    <p>Autonomous repository analysis and improvement</p>
  </div>
  <div class="grid-item" onclick="window.location='brain_architecture.md'">
    <h2>🧠 Live Brain</h2>
    <p>Always-on vectorized memory system</p>
  </div>
  <div class="grid-item highlight" onclick="window.location='composio_integration.md'">
    <h2>🔌 Composio</h2>
    <p>Connect to 250+ external tools and services</p>
  </div>
</div>

## 🚀 Getting Started

<div class="feature-box">
  <div class="feature-content">
    <h3>Begin Your VOT1 Journey</h3>
    <p>Everything you need to install, configure, and start using VOT1 effectively.</p>
    <ul>
      <li><a href="guides/installation.md">📥 Complete Installation Guide</a></li>
      <li><a href="guides/configuration.md">⚙️ Configuration Options</a></li>
      <li><a href="guides/quickstart.md">🏃‍♂️ Quick Start Tutorial</a></li>
      <li><a href="guides/troubleshooting.md">🔧 Troubleshooting Common Issues</a></li>
    </ul>
  </div>
  <div class="feature-image">
    <img src="../docs/assets/installation-preview.png" alt="Installation" />
  </div>
</div>

## 🌟 Core Features

<div class="features-grid">
  <div class="feature-card">
    <div class="feature-icon">🧠</div>
    <h3>Memory Management</h3>
    <p>Store and retrieve information using advanced vector embeddings with semantic search capabilities</p>
    <a href="guides/memory.md">Learn more →</a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🦉</div>
    <h3>OWL Reasoning</h3>
    <p>Leverage powerful ontological reasoning for sophisticated knowledge inference</p>
    <a href="guides/owl_reasoning.md">Learn more →</a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔮</div>
    <h3>Interactive Dashboard</h3>
    <p>Explore and visualize your memory network with an immersive 3D interface</p>
    <a href="guides/dashboard.md">Learn more →</a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🤖</div>
    <h3>GitHub Integration</h3>
    <p>Autonomous repository analysis and code improvement workflows</p>
    <a href="github_integration.md">Learn more →</a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">💬</div>
    <h3>AI Chat Interface</h3>
    <p>Interact with a live AI assistant in the dashboard</p>
    <a href="dashboard_ai_chat.md">Learn more →</a>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">🔄</div>
    <h3>Self-Improvement</h3>
    <p>Autonomous code analysis and enhancement through AI-powered workflows</p>
    <a href="guides/self_improvement.md">Learn more →</a>
  </div>
</div>

## 📘 API Reference

<div class="api-section">
  <div class="api-card">
    <h3>Client API</h3>
    <p>Core functionality for interacting with VOT1</p>
    <a href="api/client.md">View Documentation</a>
  </div>
  
  <div class="api-card">
    <h3>Memory API</h3>
    <p>Store, retrieve, and manage vector-based memories</p>
    <a href="api/memory.md">View Documentation</a>
  </div>
  
  <div class="api-card">
    <h3>Dashboard API</h3>
    <p>Control and customize the VOT1 dashboard</p>
    <a href="api/dashboard.md">View Documentation</a>
  </div>
  
  <div class="api-card">
    <h3>GitHub API</h3>
    <p>Interface with GitHub repositories</p>
    <a href="api/github.md">View Documentation</a>
  </div>
</div>

## 📋 Examples

<div class="examples-container">
  <div class="example-box">
    <h3>Basic Usage</h3>
    <p>Get started with simple VOT1 operations</p>
    <pre><code>from vot1 import VOT1System

# Initialize the system
system = VOT1System()

# Add a memory
memory_id = system.memory.add("This is an important concept to remember")

# Retrieve similar memories
similar = system.memory.find_similar("important concepts")</code></pre>
    <a href="examples/basic.md">More Basic Examples →</a>
  </div>
  
  <div class="example-box">
    <h3>Memory Management</h3>
    <p>Advanced memory operations</p>
    <pre><code>from vot1.memory import MemoryManager

# Create a memory manager
manager = MemoryManager()

# Add structured memory with metadata
manager.add_semantic_memory(
    content="Important AI research finding",
    metadata={
        "source": "research paper",
        "date": "2023-09-15",
        "relevance": 0.95
    }
)</code></pre>
    <a href="examples/memory.md">More Memory Examples →</a>
  </div>
  
  <div class="example-box">
    <h3>GitHub Integration</h3>
    <p>Automate repository analysis</p>
    <pre><code>from vot1.github import GitHubBridge
import asyncio

async def analyze_repo():
    bridge = GitHubBridge()
    result = await bridge.analyze_repository(
        "username", "repo", deep_analysis=True
    )
    print(f"Analysis score: {result['score']}")

asyncio.run(analyze_repo())</code></pre>
    <a href="examples/github.md">More GitHub Examples →</a>
  </div>
</div>

## 🔍 Advanced Topics

<div class="advanced-topics">
  <div class="topic">
    <h3>Custom Memory Models</h3>
    <p>Create and integrate your own memory embedding models</p>
    <a href="advanced/custom_embeddings.md">Learn more</a>
  </div>
  
  <div class="topic">
    <h3>Extending the OWL Ontology</h3>
    <p>Add custom reasoning capabilities to the system</p>
    <a href="advanced/extending_ontology.md">Learn more</a>
  </div>
  
  <div class="topic">
    <h3>Custom Visualization Plugins</h3>
    <p>Create your own dashboard visualizations</p>
    <a href="advanced/visualization_plugins.md">Learn more</a>
  </div>
  
  <div class="topic">
    <h3>Autonomous Workflows</h3>
    <p>Create complex self-improvement workflows</p>
    <a href="advanced/autonomous_workflows.md">Learn more</a>
  </div>
</div>

## 🤝 Contributing

<div class="contribute-section">
  <p>We welcome contributions of all kinds! Whether you're fixing bugs, improving documentation, or proposing new features, your help is appreciated.</p>
  
  <div class="contribute-links">
    <a href="../CONTRIBUTING.md" class="contribute-button">Contribution Guidelines</a>
    <a href="https://github.com/villageofthousands/vot1/issues" class="contribute-button">Open Issues</a>
    <a href="community/roadmap.md" class="contribute-button">Development Roadmap</a>
  </div>
</div>

<style>
/* Base styles */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #333;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  background-color: #f8f9fa;
}

/* Grid container for feature cards */
.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 40px 0;
}

.grid-item {
  background: linear-gradient(145deg, #ffffff, #f0f0f0);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.grid-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

/* Feature box */
.feature-box {
  display: flex;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  margin: 30px 0;
}

.feature-content {
  flex: 1;
  padding: 30px;
}

.feature-image {
  flex: 1;
  max-width: 50%;
  overflow: hidden;
}

.feature-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Features grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin: 30px 0;
}

.feature-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 15px;
}

/* API Section */
.api-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.api-card {
  background: #ffffff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease;
}

.api-card:hover {
  transform: translateY(-3px);
}

/* Examples */
.examples-container {
  display: flex;
  flex-direction: column;
  gap: 25px;
  margin: 30px 0;
}

.example-box {
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
}

.example-box pre {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  overflow-x: auto;
}

/* Advanced Topics */
.advanced-topics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin: 30px 0;
}

.topic {
  background: #ffffff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
}

/* Contributing section */
.contribute-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
  margin: 30px 0;
  text-align: center;
}

.contribute-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 20px;
}

.contribute-button {
  display: inline-block;
  background: #5661f0;
  color: white;
  padding: 10px 20px;
  border-radius: 30px;
  text-decoration: none;
  font-weight: 500;
  transition: background 0.3s ease;
}

.contribute-button:hover {
  background: #4149d9;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .feature-box {
    flex-direction: column;
  }
  
  .feature-image {
    max-width: 100%;
  }
}
</style>

---

<div align="center">
  <p>
    <a href="https://github.com/villageofthousands/vot1">GitHub</a> •
    <a href="https://twitter.com/vot_ai">Twitter</a> •
    <a href="https://villageofthousands.io">Website</a>
  </p>
  <p>© 2023-2024 Village of Thousands</p>
</div> 