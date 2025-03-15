#!/usr/bin/env python3
"""
VOT1 File Structure Visualizer

Integrates the file structure visualization with hybrid reasoning capabilities
to provide an enhanced project visualization experience.

Features:
- Generates interactive 3D file structure visualization
- Uses hybrid reasoning to analyze the codebase
- Provides intelligent insights about the project structure
"""

import os
import sys
import json
import argparse
import logging
import webbrowser
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("visualize_file_structure")

# Try to import the required modules
try:
    from flask import Flask, request, jsonify, send_from_directory
    flask_available = True
except ImportError:
    logger.warning("Flask not installed. Web API will not be available.")
    flask_available = False

# Import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.file_structure_generator import FileStructureGenerator

# Try to import hybrid reasoning if available
try:
    from hybrid_reasoning import HybridReasoning
    hybrid_reasoning_available = True
except ImportError:
    logger.warning("Hybrid reasoning module not available. Advanced analysis will be disabled.")
    hybrid_reasoning_available = False

class FileStructureVisualizer:
    """Combines file structure visualization with hybrid reasoning for enhanced insights."""
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = "output/structure",
        max_depth: int = 10,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
        include_hidden: bool = False,
        enable_hybrid_reasoning: bool = True,
        host: str = "127.0.0.1",
        port: int = 5000
    ):
        """
        Initialize the file structure visualizer.
        
        Args:
            project_root: Root directory of the project
            output_dir: Output directory for generated files
            max_depth: Maximum depth to traverse
            excluded_dirs: List of directories to exclude
            excluded_files: List of file patterns to exclude
            include_hidden: Whether to include hidden files and directories
            enable_hybrid_reasoning: Whether to enable hybrid reasoning
            host: Host for the web server
            port: Port for the web server
        """
        self.project_root = os.path.abspath(project_root)
        self.output_dir = os.path.join(self.project_root, output_dir)
        self.max_depth = max_depth
        self.include_hidden = include_hidden
        self.enable_hybrid_reasoning = enable_hybrid_reasoning and hybrid_reasoning_available
        self.host = host
        self.port = port
        
        # Default excluded directories and files
        self.excluded_dirs = excluded_dirs or [
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
        ]
        
        self.excluded_files = excluded_files or [
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.dll",
            "*.exe",
            "*.min.js",
            "*.min.css"
        ]
        
        # Initialize file structure generator
        self.generator = FileStructureGenerator(
            project_root=self.project_root,
            output_dir=self.output_dir,
            max_depth=self.max_depth,
            excluded_dirs=self.excluded_dirs,
            excluded_files=self.excluded_files,
            include_hidden=self.include_hidden
        )
        
        # Initialize hybrid reasoning if available
        self.hybrid_reasoning = None
        if self.enable_hybrid_reasoning:
            try:
                self.hybrid_reasoning = HybridReasoning()
                logger.info("Hybrid reasoning initialized")
            except Exception as e:
                logger.error(f"Error initializing hybrid reasoning: {e}")
                self.hybrid_reasoning = None
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Flask app for API server
        self.app = None
        if flask_available:
            self.initialize_flask_app()
        
        logger.info(f"File structure visualizer initialized for {self.project_root}")
    
    def initialize_flask_app(self):
        """Initialize Flask app for the API server."""
        self.app = Flask(__name__)
        
        # Add routes
        @self.app.route('/visualization')
        def visualization():
            """Serve the visualization HTML page."""
            visualization_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visualization')
            return send_from_directory(visualization_dir, 'file_structure_demo.html')
        
        @self.app.route('/visualization/<path:filename>')
        def visualization_files(filename):
            """Serve static files for the visualization."""
            visualization_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visualization')
            return send_from_directory(visualization_dir, filename)
        
        @self.app.route('/api/file-structure')
        def get_file_structure():
            """API endpoint to get file structure data."""
            # Get query parameters
            project_root = request.args.get('root', self.project_root)
            output_dir = request.args.get('output', self.output_dir)
            max_depth = int(request.args.get('max_depth', self.max_depth))
            include_hidden = request.args.get('include_hidden', str(self.include_hidden).lower()) == 'true'
            
            # Create generator with current parameters
            generator = FileStructureGenerator(
                project_root=project_root,
                output_dir=output_dir,
                max_depth=max_depth,
                excluded_dirs=self.excluded_dirs,
                excluded_files=self.excluded_files,
                include_hidden=include_hidden
            )
            
            try:
                # Generate file structure data
                results = generator.generate_all()
                
                # Add insights if hybrid reasoning is available
                insights = {}
                if self.hybrid_reasoning and self.enable_hybrid_reasoning:
                    insights = self.generate_structure_insights()
                
                # Read the generated files
                with open(results['json_path'], 'r') as f:
                    structure = json.load(f)
                    
                with open(results['markdown_path'], 'r') as f:
                    markdown = f.read()
                
                # Return the results
                return jsonify({
                    'status': 'success',
                    'structure': structure,
                    'markdown': markdown,
                    'insights': insights,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error generating file structure: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/insights')
        def get_insights():
            """API endpoint to get project insights from hybrid reasoning."""
            if not self.hybrid_reasoning or not self.enable_hybrid_reasoning:
                return jsonify({
                    'status': 'error',
                    'error': 'Hybrid reasoning not available'
                }), 400
            
            try:
                insights = self.generate_structure_insights()
                return jsonify({
                    'status': 'success',
                    'insights': insights,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error generating insights: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': str(e)
                }), 500
    
    def generate_file_structure(self) -> Dict[str, Any]:
        """
        Generate the file structure data.
        
        Returns:
            Dictionary with results including structure, markdown, and insights
        """
        logger.info("Generating file structure data...")
        
        # Generate structure and markdown
        results = self.generator.generate_all()
        
        # Add insights if hybrid reasoning is available
        if self.hybrid_reasoning and self.enable_hybrid_reasoning:
            results['insights'] = self.generate_structure_insights()
        
        return results
    
    def generate_structure_insights(self) -> Dict[str, Any]:
        """
        Generate insights about the project structure using hybrid reasoning.
        
        Returns:
            Dictionary with insights
        """
        if not self.hybrid_reasoning:
            return {"error": "Hybrid reasoning not available"}
        
        logger.info("Generating project structure insights using hybrid reasoning...")
        
        try:
            # Read the generated markdown file
            markdown_path = os.path.join(self.output_dir, "file_structure.md")
            if not os.path.exists(markdown_path):
                self.generator.generate_markdown()
            
            with open(markdown_path, 'r') as f:
                structure_markdown = f.read()
            
            # Construct prompt for hybrid reasoning
            prompt = f"""
            Analyze the following file structure and provide insights:
            
            {structure_markdown}
            
            Please provide the following insights:
            1. Main components of the project
            2. Architectural patterns observed
            3. Potential strengths of the structure
            4. Potential areas for improvement
            5. Recommendations for better organization
            
            Format your response as structured JSON with the above categories.
            """
            
            # Perform hybrid thinking
            result = self.hybrid_reasoning.perform_hybrid_thinking(
                prompt=prompt,
                domain="programming"
            )
            
            # Extract solution from thinking
            if hasattr(self.hybrid_reasoning, '_extract_solution'):
                insights_json = self.hybrid_reasoning._extract_solution(result)
            else:
                insights_json = result
            
            # Save insights to file
            insights_path = os.path.join(self.output_dir, "structure_insights.json")
            with open(insights_path, 'w') as f:
                json.dump(insights_json, f, indent=2)
            
            logger.info(f"Project structure insights saved to {insights_path}")
            
            return insights_json
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {"error": str(e)}
    
    def start_server(self, open_browser: bool = True) -> None:
        """
        Start the web server to serve the visualization.
        
        Args:
            open_browser: Whether to open a browser automatically
        """
        if not flask_available:
            logger.error("Flask not installed. Cannot start server.")
            return
        
        if not self.app:
            self.initialize_flask_app()
        
        # Generate file structure data first
        self.generate_file_structure()
        
        # Open browser in a separate thread after a delay
        if open_browser:
            def open_browser_after_delay():
                time.sleep(1.5)  # Wait for server to start
                webbrowser.open(f"http://{self.host}:{self.port}/visualization")
            
            threading.Thread(target=open_browser_after_delay).start()
        
        logger.info(f"Starting web server at http://{self.host}:{self.port}/visualization")
        self.app.run(host=self.host, port=self.port, debug=False)

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="VOT1 File Structure Visualizer")
    parser.add_argument("--root", "-r", type=str, default=".", help="Project root directory")
    parser.add_argument("--output", "-o", type=str, default="output/structure", help="Output directory")
    parser.add_argument("--depth", "-d", type=int, default=10, help="Maximum directory depth")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and directories")
    parser.add_argument("--exclude", "-e", type=str, nargs="+", help="Additional directories to exclude")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable hybrid reasoning")
    parser.add_argument("--markdown-only", action="store_true", help="Generate only markdown, no visualization")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    # Create excluded directories list
    excluded_dirs = [
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
    ]
    
    # Add user-specified excluded directories
    if args.exclude:
        excluded_dirs.extend(args.exclude)
    
    # Create visualizer
    visualizer = FileStructureVisualizer(
        project_root=args.root,
        output_dir=args.output,
        max_depth=args.depth,
        excluded_dirs=excluded_dirs,
        include_hidden=args.include_hidden,
        enable_hybrid_reasoning=not args.no_hybrid,
        host=args.host,
        port=args.port
    )
    
    if args.markdown_only:
        # Generate only markdown
        results = visualizer.generate_file_structure()
        print(f"✅ File structure generated:")
        print(f"   - Markdown: {results['markdown_path']}")
        print(f"   - JSON: {results['json_path']}")
        if 'insights' in results:
            insights_path = os.path.join(args.output, "structure_insights.json")
            print(f"   - Insights: {insights_path}")
    else:
        # Start web server with visualization
        visualizer.start_server(open_browser=not args.no_browser)

if __name__ == "__main__":
    main() 