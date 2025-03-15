#!/usr/bin/env python3
"""
VOT1 File Structure API

A RESTful API for serving file structure data and the 3D visualization.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, render_template, send_from_directory

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import local module
from utils.file_structure_generator import FileStructureGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("file_structure_api")

# Initialize Flask app
app = Flask(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "project_root": project_root,
    "output_dir": os.path.join(project_root, "output/structure"),
    "max_depth": 10,
    "excluded_dirs": [
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        "venv",
        ".venv",
        "env",
        "dist",
        "build"
    ],
    "excluded_files": [
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.exe",
        "*.min.js",
        "*.min.css"
    ],
    "include_hidden": False
}

# Create output directory
os.makedirs(DEFAULT_CONFIG["output_dir"], exist_ok=True)

@app.route("/")
def index():
    """Main landing page."""
    return """
    <html>
        <head>
            <title>VOT1 File Structure API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #333;
                }
                ul {
                    margin-top: 20px;
                }
                li {
                    margin-bottom: 10px;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                code {
                    background-color: #f5f5f5;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>VOT1 File Structure API</h1>
            <p>This API provides access to file structure data and visualization.</p>
            
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/visualization">/visualization</a> - Interactive 3D file structure visualization</li>
                <li><a href="/api/file-structure">/api/file-structure</a> - Get file structure data in JSON format</li>
                <li><a href="/api/markdown">/api/markdown</a> - Get file structure in Markdown format</li>
            </ul>
            
            <h2>Query Parameters:</h2>
            <ul>
                <li><code>root</code> - Project root directory (default: current project)</li>
                <li><code>max_depth</code> - Maximum directory depth (default: 10)</li>
                <li><code>include_hidden</code> - Include hidden files (default: false)</li>
            </ul>
        </body>
    </html>
    """

@app.route("/visualization")
def visualization():
    """Serve the visualization page."""
    visualization_dir = os.path.join(project_root, "visualization")
    return send_from_directory(visualization_dir, "file_structure_demo.html")

@app.route("/visualization/<path:filename>")
def visualization_files(filename):
    """Serve static files for visualization."""
    visualization_dir = os.path.join(project_root, "visualization")
    return send_from_directory(visualization_dir, filename)

@app.route("/api/file-structure")
def get_file_structure():
    """API endpoint for file structure data in JSON format."""
    # Get query parameters
    config = _get_config_from_request()
    
    try:
        # Create generator with current parameters
        generator = FileStructureGenerator(**config)
        
        # Generate file structure
        result = generator.generate_json()
        
        return jsonify({
            "status": "success",
            "data": result["structure"],
            "metadata": {
                "project_root": config["project_root"],
                "max_depth": config["max_depth"],
                "include_hidden": config["include_hidden"]
            }
        })
    except Exception as e:
        logger.error(f"Error generating file structure: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/markdown")
def get_markdown():
    """API endpoint for file structure in Markdown format."""
    # Get query parameters
    config = _get_config_from_request()
    
    try:
        # Create generator with current parameters
        generator = FileStructureGenerator(**config)
        
        # Generate markdown
        result = generator.generate_markdown()
        
        return jsonify({
            "status": "success",
            "markdown": result["content"],
            "metadata": {
                "project_root": config["project_root"],
                "max_depth": config["max_depth"],
                "include_hidden": config["include_hidden"]
            }
        })
    except Exception as e:
        logger.error(f"Error generating markdown: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def _get_config_from_request() -> Dict[str, Any]:
    """Extract configuration from request parameters."""
    config = DEFAULT_CONFIG.copy()
    
    # Get project root (with validation)
    if request.args.get("root"):
        requested_root = os.path.abspath(request.args.get("root"))
        # Simple security check - only allow paths within the parent of the project
        project_parent = os.path.dirname(project_root)
        if requested_root.startswith(project_parent):
            config["project_root"] = requested_root
        else:
            logger.warning(f"Attempted to access path outside allowed directory: {requested_root}")
    
    # Get max depth
    if request.args.get("max_depth"):
        try:
            max_depth = int(request.args.get("max_depth"))
            if 1 <= max_depth <= 20:  # Reasonable limits
                config["max_depth"] = max_depth
        except ValueError:
            pass
    
    # Get include_hidden
    if request.args.get("include_hidden"):
        include_hidden = request.args.get("include_hidden").lower() in ("true", "1", "yes")
        config["include_hidden"] = include_hidden
    
    # Update output directory based on project root
    config["output_dir"] = os.path.join(config["project_root"], "output/structure")
    os.makedirs(config["output_dir"], exist_ok=True)
    
    return config

def start_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Start the Flask server."""
    # Generate initial file structure data
    logger.info("Generating initial file structure data...")
    generator = FileStructureGenerator(**DEFAULT_CONFIG)
    generator.generate_all()
    
    # Start the server
    logger.info(f"Starting file structure API server at http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="File Structure API Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    start_server(host=args.host, port=args.port, debug=args.debug) 