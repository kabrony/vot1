# VOT1 Dashboard Installation & Usage Guide

## Installation

### Prerequisites

Before installing the VOT1 Dashboard, ensure you have the following prerequisites:

- Python 3.8 or higher
- pip (Python package manager)
- Node.js 14+ and npm (for frontend development, optional)
- Git

### Environment Setup

1. **Clone the Repository**

```bash
git clone https://github.com/village-of-thousands/vot1.git
cd vot1
```

2. **Create a Virtual Environment**

```bash
python -m venv venv
```

3. **Activate the Virtual Environment**

On Windows:
```bash
venv\Scripts\activate
```

On macOS/Linux:
```bash
source venv/bin/activate
```

4. **Install Dependencies**

```bash
pip install -e .
pip install -r requirements.txt
```

5. **Set Up Environment Variables**

Create a `.env` file in the project root with the following variables:

```
# Core Configuration
VOT1_PRIMARY_MODEL=anthropic/claude-3-7-sonnet-20240620
VOT1_SECONDARY_MODEL=anthropic/claude-3-5-sonnet-20240620
VOT1_MAX_THINKING_TOKENS=60000
VOT1_MEMORY_PATH=./memory

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional MCP Keys
PERPLEXITY_API_KEY=your_perplexity_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Development Settings
FLASK_APP=src/vot1/dashboard/app.py
FLASK_ENV=development
FLASK_DEBUG=1
```

### Running the Dashboard

1. **Start the Flask Server**

```bash
python -m src.vot1.dashboard.app
```

Or using Flask CLI:

```bash
flask run
```

2. **Access the Dashboard**

Open your browser and navigate to:

```
http://localhost:5000/
```

For the cyberpunk chat interface, navigate to:

```
http://localhost:5000/cyberpunk-chat
```

## Configuration Options

### Core Configuration

The VOT1 Dashboard can be configured using environment variables or by passing parameters to the `create_app()` function:

| Parameter | Environment Variable | Description | Default |
|-----------|----------------------|-------------|---------|
| `client` | N/A | EnhancedClaudeClient instance | `None` |
| `memory_path` | `VOT1_MEMORY_PATH` | Path to memory storage | `./memory` |
| `no_memory` | N/A | Disable memory management | `False` |
| `mcp_hybrid_options` | N/A | MCP configuration options | See below |
| `dev_assistant_options` | N/A | Dev assistant configuration | See below |

### MCP Hybrid Options

```python
mcp_hybrid_options = {
    "enabled": True,  # Enable MCP by default
    "primary_model": "claude-3-7-sonnet-20240620",
    "secondary_model": "claude-3-5-sonnet-20240620",
    "use_extended_thinking": True,
    "max_thinking_tokens": 60000,
    "enable_streaming": True,
    "perplexity_integration": True,
    "firecrawl_integration": True
}
```

### Development Assistant Options

```python
dev_assistant_options = {
    "enabled": True,
    "project_root": os.getcwd(),
    "memory_path": "./memory",
    "max_thinking_tokens": 60000,
    "perplexity_research": True
}
```

## Usage Guide

### Cyberpunk Chat Interface

The cyberpunk chat interface provides access to Claude 3.7 with extended thinking capabilities, Perplexity AI for research, and Firecrawl for web crawling.

#### Basic Chat

1. Navigate to `/cyberpunk-chat`
2. Type your message in the input field
3. Press Enter or click the send button
4. View the AI's response in the chat window

#### Chat Commands

The interface supports several slash commands:

| Command | Description | Example |
|---------|-------------|---------|
| `/research [topic]` | Research a topic using Perplexity | `/research quantum computing` |
| `/crawl [url]` | Crawl a website using Firecrawl | `/crawl https://example.com` |
| `/analyze [path]` | Analyze codebase structure | `/analyze src/vot1` |
| `/architecture` | Analyze project architecture | `/architecture` |
| `/generate [type] [desc]` | Generate code or documentation | `/generate script "Web scraper for news"` |
| `/troubleshoot [code]` | Troubleshoot code issues | `/troubleshoot "import pandas as pd; pd.read_csv()"` |
| `/memory [action]` | Manage memory | `/memory list` |

#### Chat Settings

The chat interface includes several settings accessible via the gear icon:

1. **Appearance**
   - Layout: Default, Compact, Fullscreen
   - Theme: Cyberpunk, Matrix, Midnight

2. **Tools**
   - Web Search: Toggle web search capability
   - Code Execution: Toggle code execution
   - File Access: Toggle file system access
   - Visualization: Toggle thinking visualization
   - Perplexity Research: Toggle Perplexity integration
   - Firecrawl: Toggle Firecrawl integration
   - Development Assistant: Toggle development assistant

3. **Advanced**
   - System Prompt: Custom system instructions
   - Max Thinking Tokens: Adjust thinking depth
   - Hybrid System Settings: Configure AI integration

4. **MCP Connection**
   - Connect Perplexity: Connect to Perplexity AI
   - Connect Firecrawl: Connect to Firecrawl with API key

### Development Assistant

The Development Assistant provides tools for code analysis, research, script generation, and memory management.

#### Code Analysis

1. Click the code branch icon in the status bar
2. Configure project settings
3. Click "Analyze Codebase"
4. View analysis results in the chat

Or use the command:

```
/analyze [optional path]
```

#### Research

Use the research command to leverage Perplexity AI for in-depth research:

```
/research "How to implement async/await in JavaScript"
```

#### Script Generation

Generate scripts, documentation, or tests:

```
/generate script "A utility function to parse CSV files"
/generate docs "API documentation for user authentication"
/generate test "Unit tests for the payment processing module"
```

#### Memory Management

Manage persistent memory with:

```
/memory list
/memory list [category]
/memory get [category] [key]
/memory save [script_key] [file_path]
/memory delete [category] [key]
```

### GitHub Ecosystem Analysis

The GitHub Ecosystem Analyzer provides tools for repository analysis and improvement suggestions.

1. Navigate to the GitHub tab (if available)
2. Enter repository owner and name
3. Select analysis options
4. Click "Analyze Repository"
5. View analysis results and visualizations

## Troubleshooting

### Connection Issues

If you encounter connection issues with Perplexity or Firecrawl:

1. Check API keys in your environment variables
2. Verify internet connectivity
3. Try reconnecting via the MCP connect modal
4. Check browser console for error messages

### Application Errors

If the application crashes or behaves unexpectedly:

1. Check the terminal output for error messages
2. Review Flask error logs
3. Verify Python and package versions
4. Ensure environment variables are set correctly

### Performance Issues

If the dashboard is slow or unresponsive:

1. Reduce max thinking tokens in settings
2. Disable 3D visualizations
3. Clear browser cache and reload
4. Close other resource-intensive applications

## Development Workflow

### Adding New Features

To add new features to the dashboard:

1. Create feature branch from main
2. Implement backend components (Flask routes, API endpoints)
3. Implement frontend components (HTML, CSS, JavaScript)
4. Update documentation
5. Test thoroughly
6. Submit pull request

### Code Structure Guidelines

When contributing to the codebase:

1. Follow modular architecture with clear separation of concerns
2. Use consistent naming conventions
3. Add comprehensive docstrings
4. Include error handling
5. Write unit tests for new features

## API Documentation

The dashboard exposes several API endpoints for integration with other systems:

### Chat API

- `POST /api/chat/message`: Send a message to Claude
  - Parameters: `{ "message": "Your message", "streaming": true }`
  - Returns: Message response or stream

### Development Assistant API

- `GET /api/dev-assistant/status`: Check status
- `POST /api/dev-assistant/analyze`: Analyze codebase
  - Parameters: `{ "path": "src/", "file_extension": ".py" }`
- `POST /api/dev-assistant/research`: Research a topic
  - Parameters: `{ "query": "Your query", "depth": "deep" }`

### MCP API

- `GET /api/mcp/status`: Check MCP status
- `POST /api/mcp/perplexity/connect`: Connect to Perplexity
- `POST /api/mcp/perplexity/search`: Search with Perplexity
  - Parameters: `{ "query": "Your query", "options": { ... } }`

## Advanced Configuration

### Custom CSS Themes

Create a custom theme by adding a new CSS file to `static/css/themes/` and updating the theme selector in `cyberpunk-chat.js`.

### Backend Extensions

Extend the dashboard with new backend capabilities:

1. Create a new module in the `api/` directory
2. Define API endpoints with Flask Blueprint
3. Register the blueprint in `__init__.py`
4. Implement frontend integration

### Frontend Extensions

Add new frontend features:

1. Create JavaScript modules in `static/js/`
2. Update HTML templates as needed
3. Add styles to CSS files
4. Register event handlers and components

## Conclusion

The VOT1 Dashboard provides a powerful interface for AI interactions, development assistance, and data visualization. By following this guide, you can install, configure, and use all aspects of the dashboard effectively.

For additional help or to report issues, please contact the development team or submit issues on GitHub. 