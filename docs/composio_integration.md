# <div align="center">🔌 Composio Integration</div>
# <div align="center">External API Connectivity Layer</div>

<link rel="stylesheet" href="assets/custom.css">
<script src="assets/docs.js"></script>

<div align="center">
  <img src="../docs/assets/composio-integration.png" alt="Composio Integration" width="700"/>
</div>

<p align="center">
  <b>A powerful bridge connecting VOT1's Brain architecture to Composio's extensive tool ecosystem, enabling real-world interactions with 250+ external services.</b>
</p>

<div align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-authentication">Authentication</a> •
  <a href="#-tool-integration">Tool Integration</a> •
  <a href="#-event-handling">Event Handling</a> •
  <a href="#-implementation">Implementation</a>
</div>

## ✨ Overview

<div class="brain-overview">
  <div class="overview-content">
    <p>The VOT1-Composio integration extends the Brain's capabilities by connecting it with Composio's extensive library of 250+ external tools and services. This integration allows the VOT1 Brain to interact with real-world systems, retrieve external data, control third-party services, and execute complex workflows without manual configuration.</p>
    
    <p>Key benefits of Composio integration:</p>
    <ul>
      <li><strong>Expanded Capabilities:</strong> Access to 250+ pre-built tool integrations</li>
      <li><strong>Unified Authentication:</strong> Centralized management of API credentials</li>
      <li><strong>Real-time Data Exchange:</strong> Bidirectional synchronization with external services</li>
      <li><strong>Event-driven Workflows:</strong> Trigger VOT1 processes based on external events</li>
      <li><strong>Framework Agnostic:</strong> Works with existing VOT1 MCP infrastructure</li>
    </ul>
  </div>
  
  <div class="overview-image">
    <img src="../docs/assets/composio-overview.png" alt="Composio Overview" />
  </div>
</div>

## 🏗️ Architecture

<div class="architecture-diagram">
  <img src="../docs/assets/composio-architecture.png" alt="Integration Architecture" width="100%" />
</div>

The VOT1-Composio integration consists of four key components:

<div class="component-grid">
  <div class="component-card">
    <div class="component-icon">🔑</div>
    <h3>Authentication Manager</h3>
    <p>Handles secure storage and management of Composio API credentials, token refreshing, and permission scopes.</p>
    <ul>
      <li>API key management</li>
      <li>Secure credential storage</li>
      <li>OAuth token lifecycle</li>
    </ul>
  </div>
  
  <div class="component-card">
    <div class="component-icon">🔄</div>
    <h3>Service Connector</h3>
    <p>Establishes and maintains connections to Composio's services, handling request formatting, rate limiting, and error recovery.</p>
    <ul>
      <li>Request/response handling</li>
      <li>Rate limit management</li>
      <li>Error recovery strategies</li>
    </ul>
  </div>
  
  <div class="component-card">
    <div class="component-icon">🧩</div>
    <h3>Tool Registry</h3>
    <p>Maintains a catalog of available Composio tools, their capabilities, required parameters, and authentication requirements.</p>
    <ul>
      <li>Tool discovery and registration</li>
      <li>Capability mapping</li>
      <li>Parameter validation</li>
    </ul>
  </div>
  
  <div class="component-card">
    <div class="component-icon">📡</div>
    <h3>Event Bridge</h3>
    <p>Enables bidirectional event flow between VOT1 and external services via Composio webhooks and triggers.</p>
    <ul>
      <li>Webhook registration</li>
      <li>Event transformation</li>
      <li>Trigger management</li>
    </ul>
  </div>
</div>

## 🔐 Authentication

Secure authentication with Composio is managed through a dedicated authentication module that handles API key management and credential security.

### API Key Setup

```python
from vot1.integrations.composio import ComposioAuthManager

# Initialize with your Composio API key
auth_manager = ComposioAuthManager(
    api_key="af20c9ht05ouuhwo6zkzs7",
    # Optional: Override default settings
    config={
        "credential_store": "keychain",  # Options: keychain, environment, file
        "token_refresh_margin_seconds": 300,
        "auto_refresh": True
    }
)

# Verify authentication
client_info = auth_manager.verify_credentials()
print(f"Connected as: {client_info['client']['name']}")
print(f"Plan: {client_info['client']['plan']}")
```

### Connection Status Monitoring

The authentication manager continuously monitors connection status and provides real-time updates:

```python
# Register connection status listener
def connection_status_changed(status):
    if status["connected"]:
        print(f"Connected to Composio: {status['client_name']}")
    else:
        print(f"Disconnected from Composio: {status['reason']}")

auth_manager.add_status_listener(connection_status_changed)
```

## 🧰 Tool Integration

VOT1-Composio integration provides seamless access to all available Composio tools through a unified interface.

### Available Tool Categories

<div class="tool-categories">
  <table>
    <thead>
      <tr>
        <th>Category</th>
        <th>Tools</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Productivity</td>
        <td>Gmail, Calendar, Drive, Docs, Sheets</td>
        <td>Interact with Google Workspace and other productivity tools</td>
      </tr>
      <tr>
        <td>Communication</td>
        <td>Slack, Discord, Teams, SMS, Email</td>
        <td>Send and receive messages across communication platforms</td>
      </tr>
      <tr>
        <td>Development</td>
        <td>GitHub, GitLab, Jira, BitBucket, VS Code</td>
        <td>Integrate with development workflows and code repositories</td>
      </tr>
      <tr>
        <td>Data</td>
        <td>SQL, MongoDB, Firebase, Airtable, Excel</td>
        <td>Query and manipulate data across various databases</td>
      </tr>
      <tr>
        <td>AI Services</td>
        <td>OpenAI, Claude, HuggingFace, Stability AI</td>
        <td>Leverage external AI capabilities and model APIs</td>
      </tr>
    </tbody>
  </table>
</div>

### Tool Discovery and Usage

```python
from vot1.integrations.composio import ComposioToolRegistry, ComposioConnector

# Initialize the tool registry
tool_registry = ComposioToolRegistry(auth_manager)

# List available tools
available_tools = tool_registry.list_tools()
print(f"Found {len(available_tools)} available tools")

# Filter tools by category
github_tools = tool_registry.find_tools(category="Development", name_contains="GitHub")

# Get tool details
github_tool = tool_registry.get_tool_details("github")
print(f"GitHub tool requires auth: {github_tool['requires_auth']}")
print(f"Available actions: {', '.join(github_tool['actions'])}")

# Initialize connector
connector = ComposioConnector(auth_manager)

# Execute a tool action
result = await connector.execute_tool(
    tool_name="github",
    action="create_issue",
    parameters={
        "repo": "username/repo",
        "title": "Investigate memory optimization",
        "body": "We need to optimize the vector quantization further",
        "labels": ["enhancement", "memory"]
    }
)

print(f"Created issue #{result['issue_number']}: {result['url']}")
```

## 📡 Event Handling

The VOT1-Composio integration supports event-driven workflows through Composio's trigger system.

### Registering Event Triggers

```python
from vot1.integrations.composio import ComposioEventBridge

# Initialize the event bridge
event_bridge = ComposioEventBridge(auth_manager)

# Register a webhook to receive GitHub events
github_webhook = await event_bridge.register_trigger(
    trigger_type="github",
    trigger_config={
        "events": ["push", "pull_request", "issues"],
        "repositories": ["username/repo"]
    },
    handler_function=process_github_event
)

# Register a scheduled trigger
schedule_trigger = await event_bridge.register_trigger(
    trigger_type="schedule",
    trigger_config={
        "cron": "0 9 * * 1-5",  # 9am weekdays
        "timezone": "UTC"
    },
    handler_function=run_daily_analysis
)

# Handler function for GitHub events
async def process_github_event(event_data):
    event_type = event_data["event"]
    repo = event_data["repository"]["full_name"]
    
    if event_type == "push":
        # Process new commits
        await analyze_commits(event_data["commits"])
    elif event_type == "issues":
        # Process issue events
        if event_data["action"] == "opened":
            await process_new_issue(event_data["issue"])
```

### Event-Driven Memory Creation

```python
# Create memories from external events
async def run_daily_analysis(event_data):
    # Fetch data from external systems via Composio
    jira_data = await connector.execute_tool(
        tool_name="jira",
        action="search_issues",
        parameters={
            "jql": "project = VOT and updated >= -1d"
        }
    )
    
    # Process and store as memories in VOT1 Brain
    for issue in jira_data["issues"]:
        await brain.remember(
            content=f"Jira issue update: {issue['key']} - {issue['fields']['summary']}",
            modality="text",
            source="jira",
            metadata={
                "issue_key": issue["key"],
                "status": issue["fields"]["status"]["name"],
                "priority": issue["fields"]["priority"]["name"]
            }
        )
```

## 💻 Implementation

<div class="implementation-phases">
  <div class="phase-card">
    <h3>Phase 1: Core Integration</h3>
    <ul>
      <li>Implement Composio authentication manager</li>
      <li>Develop basic service connector</li>
      <li>Create tool registry with GitHub integration</li>
      <li>Set up configuration and credential management</li>
    </ul>
    <div class="phase-timeline">Weeks 1-2</div>
  </div>
  
  <div class="phase-card">
    <h3>Phase 2: Tool Integration</h3>
    <ul>
      <li>Map Composio tools to VOT1 capabilities</li>
      <li>Implement parameter validation and transformation</li>
      <li>Develop error handling and retry mechanisms</li>
      <li>Create tool usage documentation</li>
    </ul>
    <div class="phase-timeline">Weeks 3-4</div>
  </div>
  
  <div class="phase-card">
    <h3>Phase 3: Event System</h3>
    <ul>
      <li>Implement webhook registration and management</li>
      <li>Develop event transformation pipeline</li>
      <li>Create trigger management interface</li>
      <li>Integrate with VOT1 memory system</li>
    </ul>
    <div class="phase-timeline">Weeks 5-6</div>
  </div>
  
  <div class="phase-card">
    <h3>Phase 4: MCP Integration</h3>
    <ul>
      <li>Bridge Composio capabilities with MCP</li>
      <li>Implement unified tool calling interface</li>
      <li>Develop MCP prompt extensions for Composio tools</li>
      <li>Create comprehensive documentation</li>
    </ul>
    <div class="phase-timeline">Weeks 7-8</div>
  </div>
</div>

## 🚀 Getting Started

To begin using Composio with VOT1:

1. Install the required dependencies:

```bash
pip install vot1-composio-integration
```

2. Configure your authentication:

```python
from vot1.config import ComposioConfig
from vot1.integrations.composio import setup_composio

# Configure Composio integration
composio_config = ComposioConfig(
    api_key="af20c9ht05ouuhwo6zkzs7",
    webhook_url="https://your-vot1-server.com/webhooks/composio",
    allowed_tools=["github", "jira", "slack", "gmail"],  # Optional: limit tool access
    log_level="INFO"
)

# Initialize the integration
composio = setup_composio(composio_config)

# Register with the VOT1 Brain
brain.register_extension(composio)
```

3. Use tools in your code:

```python
# Example: Create a GitHub issue based on a memory
relevant_memory = brain.recall(
    query="memory optimization issues",
    limit=1,
    min_relevance=0.8
)[0]

# Use Composio to create a GitHub issue
issue = await composio.github.create_issue(
    repo="villageofthousands/vot1",
    title=f"Memory Optimization: {relevant_memory.metadata.get('category', 'General')}",
    body=relevant_memory.content,
    labels=["memory", "optimization"]
)

print(f"Created issue: {issue['html_url']}")
```

4. Use tools through MCP:

VOT1's MCP interface now automatically recognizes Composio tools and can use them in conversations:

```
<User>: Analyze the performance issues in our GitHub repository

<Assistant>: I'll analyze the recent performance issues in the repository.

[Using GitHub tool to fetch recent issues labeled 'performance']
[Found 3 performance-related issues in the past week]

Based on my analysis of recent GitHub issues, there are three main performance concerns:

1. Vector quantization overhead in memory retrieval (Issue #42)
2. Slow initialization of the OWL reasoning engine (Issue #47)
3. Memory leaks in the integration bus during high-volume events (Issue #51)

The vector quantization issue seems most critical as it's affecting response times. Would you like me to:
1. Create a task to optimize the vector quantization code
2. Analyze the memory profiling data from recent tests
3. Research alternative quantization approaches
```

## 🔗 Integration with MCP

The Composio integration works seamlessly with VOT1's existing MCP (Model Control Protocol) system:

<div class="method-card">
  <h3>Tool Registration</h3>
  <p>Composio tools are automatically registered with MCP's tool registry, making them available for use in AI conversations.</p>
  <div class="code-example">
    <pre><code>
# Automatically register Composio tools with MCP
from vot1.mcp import MCPToolRegistry
from vot1.integrations.composio import ComposioToolAdapter

# Get the MCP tool registry
mcp_registry = MCPToolRegistry.get_instance()

# Register Composio tools with MCP
composio_adapter = ComposioToolAdapter(composio)
registered_tools = composio_adapter.register_with_mcp(mcp_registry)

print(f"Registered {len(registered_tools)} Composio tools with MCP")
    </code></pre>
  </div>
</div>

<div class="method-card">
  <h3>Prompt Enhancement</h3>
  <p>MCP system prompts are automatically enhanced with information about available Composio tools and their capabilities.</p>
  <div class="code-example">
    <pre><code>
# Example of enhanced system prompt with Composio tools
system_prompt = f"""You are an AI assistant with access to external tools through Composio.
Available tools:
- GitHub: Create issues, search repositories, analyze code
- Slack: Send messages, create channels, manage users
- Gmail: Send emails, search inbox, manage drafts
- Jira: Create tickets, update status, search issues

When using these tools, specify the tool name, action, and parameters.
"""

# MCP uses this enhanced prompt automatically when Composio tools are registered
    </code></pre>
  </div>
</div>

## 🔄 Switching Between MCP and Composio

The VOT1 system allows flexible switching between direct MCP usage and Composio-powered tools:

```python
# Configure tool preference
from vot1.config import ToolPreferenceConfig

tool_config = ToolPreferenceConfig(
    # For GitHub operations, prefer Composio over MCP
    "github": {
        "preferred_provider": "composio",
        "fallback_provider": "mcp"
    },
    # For memory operations, prefer MCP
    "memory": {
        "preferred_provider": "mcp",
        "fallback_provider": None  # No fallback
    }
)

# Apply configuration
brain.configure_tool_preferences(tool_config)
```

This configuration ensures that:
1. GitHub operations use Composio's implementation by default
2. If Composio is unavailable, operations fall back to MCP's GitHub implementation
3. Memory operations always use MCP's native implementation

## 🔍 Debugging Integration

The VOT1-Composio integration includes comprehensive debugging tools:

```python
from vot1.integrations.composio import ComposioDebugger

# Initialize the debugger
debugger = ComposioDebugger(composio)

# Enable verbose logging
debugger.set_log_level("DEBUG")

# Test connection to Composio
connection_result = debugger.test_connection()
if connection_result["success"]:
    print(f"Connected successfully (latency: {connection_result['latency_ms']}ms)")
else:
    print(f"Connection failed: {connection_result['error']}")

# Test specific tool
github_test = debugger.test_tool("github")
for action, result in github_test.items():
    status = "✅" if result["success"] else "❌"
    print(f"{status} github.{action}: {result['message']}")
```

---

<div align="center">
  <p>
    <a href="https://github.com/villageofthousands/vot1">GitHub</a> •
    <a href="https://docs.composio.dev">Composio Docs</a> •
    <a href="https://villageofthousands.io">Website</a>
  </p>
  <p>© 2023-2024 Village of Thousands</p>
</div> 