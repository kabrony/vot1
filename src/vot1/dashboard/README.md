# VOT1 Dashboard

A modern web dashboard with Three.js visualization for the VOT1 project, providing an interactive interface to interact with the Claude API, manage memory, and configure system settings.

## Features

- **3D Memory Visualization**: Interactive Three.js visualization of memory nodes
- **Chat Interface**: Send messages to Claude with optional memory and web search enhancement
- **Memory Management**: Search, browse, and add knowledge to semantic memory
- **System Configuration**: Configure API keys, model selection, and integration settings
- **Real-time Updates**: Monitor system status and memory statistics

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