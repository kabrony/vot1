# VOT1 Dashboard

The VOT1 Dashboard provides a web-based interface for interacting with the VOT1 memory system, visualization tools, and integrations. This document covers setup, configuration, and usage of the dashboard.

## Features

- Memory visualization and exploration
- Memory search and filtering
- Reasoning engine interface
- GitHub ecosystem analysis and automation
- OpenAPI integration management
- Chat interface with visualization controls
- System settings and configuration

## GitHub Integration

The dashboard includes powerful GitHub integration through the Integrations tab:

### GitHub Repository Analysis

1. Navigate to the **Integrations** tab
2. Select the **GitHub** tab
3. Enter repository owner/organization and name
4. Select analysis type (Standard, Deep, Code Quality Focus, Security Focus)
5. Click "Analyze Repository"

Analysis results include:
- Code quality metrics
- Architecture overview
- Potential improvements
- Security considerations

### GitHub Update Automation

The dashboard provides a visual interface for creating automated updates to GitHub repositories:

1. In the GitHub tab, scroll to the "Repository Update Automation" section
2. Enter repository owner/organization and name
3. Select update areas (Documentation, Workflows, Dependencies, Code Quality)
4. Configure options:
   - Maximum updates to create
   - Deep analysis toggle
   - Auto-approve PRs toggle
5. Click "Create Updates"

#### Visualization Options

The update results can be viewed in two formats:

1. **Standard View**: Card-based view of all updates with details
2. **3D Visualization**: Interactive THREE.js visualization showing:
   - Updates as 3D nodes with shapes representing update types
   - Connections between related updates
   - Color coding based on update category
   - Hover information for each update

The 3D visualization provides intuitive understanding of how updates relate to each other and affect different parts of the repository.

#### AI Reasoning Display

The dashboard shows how the AI reasoned about repository improvements:
- Analysis approach
- Key observations
- Decision factors for updates

This transparency helps understand why specific updates were suggested and the AI's thought process.

#### Memory Integration

The system connects updates with related memories from previous analyses:
- Similar repositories
- Common patterns
- Historical context

This integration improves update quality through learned patterns and repository-specific knowledge.

## Configuration

The GitHub integration can be configured in a few ways:

1. **Environment Variables**:
   ```
   GITHUB_TOKEN=your_token_here
   VOT1_PRIMARY_MODEL=anthropic/claude-3-7-sonnet-20240620
   VOT1_SECONDARY_MODEL=anthropic/claude-3-5-sonnet-20240620
   VOT1_MAX_THINKING_TOKENS=10000
   ```

2. **Settings Panel**:
   - Navigate to the Settings tab in the dashboard
   - Scroll to "GitHub Integration Settings"
   - Configure API tokens, models, and default behavior

## Running with Maximum Thinking

To run the GitHub analyzer with maximum thinking capacity:

1. In the "Repository Update Automation" section, check the "Deep Analysis" toggle
2. This activates extended reasoning capabilities
3. Results will include more comprehensive analysis but take longer to generate

You can also run with maximum thinking via the CLI:
```bash
python -m scripts.run_github_automation update --owner username --repo repository --deep-analysis --max-thinking 10000
```

## Getting Started

### Prerequisites

- VOT1 project installed
- Python 3.8 or higher
- Flask for the server component

### Running the Dashboard

The dashboard is integrated into the VOT1 project and can be started using:

```python
from vot1.dashboard import create_dashboard
from vot1.client import EnhancedClaudeClient
from vot1.memory import MemoryManager

# Initialize components
client = EnhancedClaudeClient()
memory_manager = MemoryManager()

# Create and start the dashboard
dashboard = create_dashboard(
    client=client,
    memory_manager=memory_manager,
    start_server=True,
    debug=True
)
```

This will start the dashboard server at `http://127.0.0.1:5000` by default.

### Demo Mode

You can run the dashboard in demo mode by accessing it with the `demo=true` parameter:

```
http://127.0.0.1:5000/?demo=true
```

This will populate the dashboard with example data for demonstration purposes.

## Dashboard Structure

The dashboard is organized into four main tabs:

1. **Overview**: Displays the 3D memory visualization, memory statistics, and recent activity
2. **Memory**: Allows searching, browsing, and adding knowledge to memory
3. **Chat**: Provides an interface to interact with Claude
4. **Settings**: Enables configuration of API keys, models, and integration settings

## API Endpoints

The dashboard server exposes several API endpoints:

- `GET /api/status`: Returns system status information
- `GET /api/memory`: Retrieves memory contents with optional search
- `GET /api/memory/stats`: Returns memory statistics
- `POST /api/message`: Sends a message to Claude
- `POST /api/knowledge`: Adds knowledge to semantic memory

## Customization

The dashboard appearance can be customized by modifying the CSS files in the `static/css` directory. The visualization can be customized by editing the Three.js implementation in `static/js/three-visualization.js`.

## Files Structure

```
dashboard/
├── __init__.py          # Package initialization
├── server.py            # Flask server implementation
├── static/              # Static web assets
│   ├── css/             # Stylesheets
│   │   └── style.css    # Main dashboard styles
│   ├── js/              # JavaScript files
│   │   ├── api.js       # API client
│   │   ├── app.js       # Main application logic
│   │   ├── init.js      # Initialization script
│   │   ├── memory-chart.js  # Chart.js visualization
│   │   └── three-visualization.js  # Three.js visualization
│   └── index.html       # Main dashboard HTML
└── README.md            # This documentation
```

## Technologies Used

- **Flask**: Backend server
- **Three.js**: 3D visualization
- **Chart.js**: Data visualization
- **Vanilla JS**: Frontend logic without frameworks

## Browser Compatibility

The dashboard is compatible with modern browsers that support ES6, WebGL, and CSS Grid:

- Chrome 60+
- Firefox 54+
- Safari 10.1+
- Edge 16+

## Contributing

Contributions to improve the dashboard are welcome! Please feel free to submit pull requests or open issues to suggest features or report bugs.

---

**Powered by [VillageOfThousands.io](https://villageofthousands.io)** 