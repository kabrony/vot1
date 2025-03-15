#!/usr/bin/env python3
"""
File Structure Visualization Module
Generates tree-structured data for visualization
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


class FileStructureVisualizer:
    """
    Generates a hierarchical representation of a file structure
    for visualization with THREE.js
    """
    
    def __init__(self, excluded_dirs: Optional[List[str]] = None):
        """Initialize the visualizer"""
        self.excluded_dirs = excluded_dirs or [
            '.git', '.github', '__pycache__', 'node_modules',
            'venv', '.env', '.venv', '.idea', '.vscode'
        ]
    
    def generate_structure(self, root_dir: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Generate a hierarchical structure of files and directories
        
        Args:
            root_dir: The root directory to start from
            max_depth: Maximum depth to traverse
            
        Returns:
            Dict representing the hierarchical structure
        """
        root_path = Path(root_dir)
        if not root_path.exists() or not root_path.is_dir():
            return {"name": str(root_path), "error": "Directory not found"}
        
        return self._process_directory(root_path, max_depth, current_depth=0)
    
    def _process_directory(self, path: Path, max_depth: int, current_depth: int) -> Dict[str, Any]:
        """
        Process a directory and its contents
        
        Args:
            path: The directory path
            max_depth: Maximum depth to traverse
            current_depth: Current depth level
            
        Returns:
            Dict representing the directory structure
        """
        if current_depth > max_depth:
            return {"name": path.name, "type": "dir", "truncated": True}
        
        # Get directory stats
        try:
            stats = path.stat()
            size = stats.st_size
            modified = stats.st_mtime
        except (PermissionError, OSError):
            size = 0
            modified = 0
        
        # Create directory node
        result = {
            "name": path.name,
            "path": str(path),
            "type": "dir",
            "size": size,
            "modified": modified,
            "children": []
        }
        
        # Process children
        try:
            children = list(path.iterdir())
            
            # Sort directories first, then files
            children.sort(key=lambda p: (0 if p.is_dir() else 1, p.name.lower()))
            
            for child in children:
                # Skip excluded directories
                if child.name in self.excluded_dirs:
                    continue
                
                # Skip hidden files if needed
                if child.name.startswith('.') and child.name not in ['.gitignore', '.env.example']:
                    continue
                
                if child.is_dir():
                    child_node = self._process_directory(child, max_depth, current_depth + 1)
                    result["children"].append(child_node)
                else:
                    # Process file
                    file_node = self._process_file(child)
                    result["children"].append(file_node)
        
        except (PermissionError, OSError):
            result["error"] = "Permission denied"
        
        return result
    
    def _process_file(self, path: Path) -> Dict[str, Any]:
        """
        Process a file
        
        Args:
            path: The file path
            
        Returns:
            Dict representing the file
        """
        # Get file stats
        try:
            stats = path.stat()
            size = stats.st_size
            modified = stats.st_mtime
        except (PermissionError, OSError):
            size = 0
            modified = 0
        
        # Determine file type
        file_type = "file"
        if path.suffix in ['.py', '.js', '.html', '.css', '.json', '.md', '.txt']:
            file_type = "code"
        elif path.suffix in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico']:
            file_type = "image"
        elif path.suffix in ['.mp3', '.wav', '.ogg']:
            file_type = "audio"
        elif path.suffix in ['.mp4', '.avi', '.mov', '.wmv']:
            file_type = "video"
        elif path.suffix in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            file_type = "document"
        
        # Create file node
        return {
            "name": path.name,
            "path": str(path),
            "type": file_type,
            "size": size,
            "modified": modified,
            "extension": path.suffix
        }
    
    def save_structure(self, structure: Dict[str, Any], output_file: str) -> None:
        """
        Save the structure to a JSON file
        
        Args:
            structure: The structure to save
            output_file: Path to the output file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2)


if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Generate file structure visualization data")
    parser.add_argument("--root", "-r", default=".", help="Root directory")
    parser.add_argument("--output", "-o", default="file_structure.json", help="Output file")
    parser.add_argument("--depth", "-d", type=int, default=3, help="Maximum depth")
    args = parser.parse_args()
    
    # Generate structure
    visualizer = FileStructureVisualizer()
    structure = visualizer.generate_structure(args.root, args.depth)
    
    # Save structure
    visualizer.save_structure(structure, args.output)
    print(f"File structure saved to {args.output}") 