# TRILOGY BRAIN User Interface

This directory contains the user interface components for the TRILOGY BRAIN distributed memory system, part of the VOT1 project.

## Overview

TRILOGY BRAIN UI is a modern, immersive interface for interacting with the distributed memory system. It provides real-time visualization of the memory network, node management, memory exploration, and system monitoring capabilities.

The UI consists of:

1. A 3D visualization of the network built with Three.js
2. A RESTful API for programmatic interaction
3. WebSocket support for real-time updates
4. Integration with the VOT1 principles engine

## Features

- Immersive 3D visualization of memory nodes and connections
- Real-time monitoring of system health and performance
- Interactive node management (add, remove, configure)
- Memory exploration and analysis
- Principles-aligned user experiences
- Responsive design for various device sizes

## Directory Structure

```
src/vot1/ui/
├── web/                        # Web interface files
│   ├── assets/                 # Static assets (images, icons, etc.)
│   │   ├── trilogy-logo.svg    # TRILOGY BRAIN logo
│   │   └── favicon.svg         # Favicon
│   ├── index.html              # Main HTML file
│   └── trilogy_brain_ui.js     # Three.js visualization module
├── web_server.py               # Web server implementation
└── README.md                   # This file
```

## Setup

### Prerequisites

- Python 3.8+
- A modern web browser with WebGL support
- Required Python packages:
  - aiohttp
  - aiohttp_cors
  - websockets

### Installation

1. Install required packages:

```bash
pip install aiohttp aiohttp_cors websockets
```

2. Ensure that the VOT1 package is in your Python path

## Usage

### Running the Web Server

To start the TRILOGY BRAIN web server:

```bash
python src/vot1/ui/web_server.py
```

This will start the server on http://127.0.0.1:8080 by default and open a browser window.

### Command-line Options

```
python web_server.py [--port PORT] [--host HOST] [--no-browser]
```

- `--port PORT`: Specify the port to listen on (default: 8080)
- `--host HOST`: Specify the host to bind to (default: 127.0.0.1)
- `--no-browser`: Don't automatically open a browser window

### Navigating the Interface

The interface is divided into several sections:

1. **Network Visualization**: The main 3D view showing nodes and connections
2. **Memory Explorer**: Browse and search memories
3. **System Analytics**: Monitor system performance
4. **System Logs**: View system events and logs

The sidebar provides navigation between these views and shows a list of active nodes.

### Keyboard and Mouse Controls

In the 3D visualization:

- **Left-click + drag**: Rotate the view
- **Right-click + drag**: Pan the view
- **Scroll wheel**: Zoom in/out
- **Click on node**: Select node and show details

## API Documentation

The TRILOGY BRAIN UI provides a RESTful API for programmatic interaction.

### Endpoints

#### System Status

```
GET /api/status
```

Returns the current system status.

#### Nodes

```
GET /api/nodes
```

Returns a list of all nodes in the system.

```
GET /api/nodes/{node_id}
```

Returns details for a specific node.

```
POST /api/nodes
```

Adds a new node to the system. Request body should include:
- `type`: Node type (memory, compute, coordinator, validator, gateway)
- `host`: Node hostname or IP
- `port`: Node port

```
DELETE /api/nodes/{node_id}
```

Removes a node from the system.

#### Memories

```
GET /api/memories
```

Returns a list of memories in the system.

#### System Statistics

```
GET /api/stats
```

Returns system statistics and performance metrics.

### WebSocket API

The WebSocket endpoint is available at `/ws` and provides real-time updates.

#### Commands

Send JSON messages with the following format:

```json
{
  "command": "get_nodes"
}
```

Available commands:
- `get_nodes`: Get all nodes
- `get_stats`: Get system statistics

#### Updates

The server sends JSON messages with the following format:

```json
{
  "type": "nodes",
  "data": [...]
}
```

Update types:
- `status`: Connection status
- `nodes`: Node updates
- `stats`: Statistics updates

## Development

### Extending the UI

To extend the UI with new features:

1. Add new API endpoints in `web_server.py`
2. Update the web interface files in the `web/` directory
3. Add new visualization components to `trilogy_brain_ui.js`

### Integration with VOT1

The UI integrates with VOT1 through the MCP Node Controller and Principles Engine. When these components are available, the UI will use them to provide enhanced functionality.

## License

VOT1 Project - © 2025 Organix - All rights reserved 