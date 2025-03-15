# VOT1 File Structure Visualization Tools

This directory contains tools for visualizing the VOT1 file structure in both Three.js (3D) and Markdown formats.

## Components

1. **File Structure Generator** (`utils/file_structure_generator.py`): A utility for generating file structure data in both JSON format (for Three.js visualization) and Markdown format for documentation.

2. **File Structure API** (`api/file_structure_api.py`): A Flask API server that provides endpoints for the file structure visualization.

3. **Three.js Visualization** (`visualization/file_structure_3d.js`): A Three.js component for visualizing file structures in 3D with a cyberpunk aesthetic.

4. **Visualization Demo** (`visualization/file_structure_demo.html`): An HTML demo page for the Three.js visualization.

5. **Command-Line Markdown Generator** (`generate_folder_structure.py`): A command-line utility for generating file structure as Markdown.

## Usage

### Generating Markdown File Structure

```bash
# Generate Markdown file structure
./generate_folder_structure.py --root /path/to/project --output output/structure

# Print to stdout
./generate_folder_structure.py --stdout

# Specify maximum depth
./generate_folder_structure.py --depth 5

# Include hidden files
./generate_folder_structure.py --include-hidden

# Exclude additional directories
./generate_folder_structure.py --exclude node_modules dist build
```

### Viewing the 3D Visualization

1. Start the API server:

```bash
./api/file_structure_api.py --host 127.0.0.1 --port 5000 --debug
```

2. Open the visualization in your browser:
```
http://127.0.0.1:5000/visualization
```

3. The visualization includes controls for:
   - Including/excluding hidden files
   - Setting the maximum depth level
   - Toggling the cyberpunk grid
   - Exporting the structure as Markdown

## 3D Visualization Features

The Three.js visualization provides:

- Interactive 3D file structure with cyberpunk styling
- Color-coded files and folders
- Hover and click interactions
- Animated transitions when expanding/collapsing folders
- Cyberpunk-themed grid and particle effects
- Orbit controls for navigation

## Markdown Format Example

```
Project Root
├── api
│   ├── __init__.py
│   └── file_structure_api.py
├── output
│   └── structure
│       ├── file_structure.json
│       └── file_structure.md
├── utils
│   ├── __init__.py
│   └── file_structure_generator.py
├── visualization
│   ├── file_structure_3d.js
│   └── file_structure_demo.html
└── generate_folder_structure.py
```

## API Endpoints

- `GET /api/file-structure`: Returns the file structure in both JSON and Markdown formats.
- `GET /api/file-structure/markdown`: Returns the file structure in Markdown format only.

## Requirements

- Python 3.6+
- Flask
- Three.js (loaded from CDN in the demo) 