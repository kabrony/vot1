#!/usr/bin/env python3
"""
VOT1 File Structure Generator

A utility class for generating file structure data in JSON and Markdown formats.
Used by the visualization and API components.
"""

import os
import re
import json
import fnmatch
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("file_structure_generator")

class FileStructureGenerator:
    """Generates file structure data in various formats."""
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = "output/structure",
        max_depth: int = 10,
        excluded_dirs: Optional[List[str]] = None,
        excluded_files: Optional[List[str]] = None,
        include_hidden: bool = False
    ):
        """
        Initialize the file structure generator.
        
        Args:
            project_root: Root directory of the project
            output_dir: Output directory for generated files
            max_depth: Maximum depth to traverse
            excluded_dirs: List of directories to exclude
            excluded_files: List of file patterns to exclude
            include_hidden: Whether to include hidden files and directories
        """
        self.project_root = os.path.abspath(project_root)
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.include_hidden = include_hidden
        
        # Default excluded directories
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
        
        # Default excluded files
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
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _should_exclude(self, path: str) -> bool:
        """
        Check if a path should be excluded based on exclusion patterns.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # Get the relative path
        rel_path = os.path.relpath(path, self.project_root)
        
        # Check if it's a hidden file/directory
        if not self.include_hidden and os.path.basename(path).startswith('.'):
            return True
        
        # Check if it's in excluded directories
        for excluded_dir in self.excluded_dirs:
            if fnmatch.fnmatch(rel_path, excluded_dir) or \
               any(part == excluded_dir for part in rel_path.split(os.sep)):
                return True
        
        # Check if it's an excluded file pattern
        if os.path.isfile(path):
            for excluded_file in self.excluded_files:
                if fnmatch.fnmatch(os.path.basename(path), excluded_file):
                    return True
        
        return False
    
    def generate_json(self) -> Dict[str, Any]:
        """
        Generate file structure data in JSON format.
        
        Returns:
            Dictionary with the JSON file path and the file structure data
        """
        logger.info("Generating file structure data...")
        
        structure = self._scan_directory(self.project_root)
        
        # Save to file
        json_path = os.path.join(self.output_dir, "file_structure.json")
        with open(json_path, 'w') as f:
            json.dump(structure, f, indent=2)
        
        logger.info(f"File structure JSON saved to {json_path}")
        
        return {
            "json_path": json_path,
            "structure": structure
        }
    
    def generate_markdown(self) -> Dict[str, Any]:
        """
        Generate file structure in Markdown format.
        
        Returns:
            Dictionary with the Markdown file path and content
        """
        logger.info("Generating Markdown representation...")
        
        # Get the project name from the root directory
        project_name = os.path.basename(self.project_root)
        
        # Generate the markdown
        markdown = f"# {project_name} File Structure\n\n```\n{project_name}\n"
        
        # Build the tree structure
        markdown += self._generate_tree(self.project_root, "", 0, is_last=True)
        
        # Close the code block
        markdown += "```\n"
        
        # Save to file
        markdown_path = os.path.join(self.output_dir, "file_structure.md")
        with open(markdown_path, 'w') as f:
            f.write(markdown)
        
        logger.info(f"Markdown file structure saved to {markdown_path}")
        
        return {
            "markdown_path": markdown_path,
            "content": markdown
        }
    
    def generate_all(self) -> Dict[str, Any]:
        """
        Generate all file structure representations.
        
        Returns:
            Dictionary with paths and data for all generated formats
        """
        json_result = self.generate_json()
        markdown_result = self.generate_markdown()
        
        return {
            "json_path": json_result["json_path"],
            "markdown_path": markdown_result["markdown_path"],
            "structure": json_result["structure"]
        }
    
    def _scan_directory(
        self, 
        directory: str, 
        rel_path: str = "", 
        depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recursively scan a directory to build the file structure.
        
        Args:
            directory: Directory to scan
            rel_path: Relative path from the project root
            depth: Current depth in the directory tree
            
        Returns:
            List of dictionaries representing the directory contents
        """
        if depth > self.max_depth:
            return []
        
        result = []
        
        try:
            # Get all items in the directory
            items = sorted(os.listdir(directory))
            
            for item in items:
                item_path = os.path.join(directory, item)
                item_rel_path = os.path.join(rel_path, item) if rel_path else item
                
                # Skip excluded items
                if self._should_exclude(item_path):
                    continue
                
                if os.path.isdir(item_path):
                    # Directory
                    children = self._scan_directory(
                        item_path, 
                        item_rel_path, 
                        depth + 1
                    )
                    
                    result.append({
                        "name": item,
                        "type": "folder",
                        "path": item_rel_path,
                        "children": children
                    })
                else:
                    # File
                    result.append({
                        "name": item,
                        "type": "file",
                        "path": item_rel_path,
                        "size": os.path.getsize(item_path)
                    })
        except PermissionError:
            logger.warning(f"Permission denied for directory: {directory}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")
        
        return result
    
    def _generate_tree(
        self, 
        directory: str, 
        prefix: str = "", 
        depth: int = 0, 
        is_last: bool = False
    ) -> str:
        """
        Generate a tree-like representation of the file structure for Markdown.
        
        Args:
            directory: Directory to represent
            prefix: Prefix for the current line
            depth: Current depth in the directory tree
            is_last: Whether this is the last item in the parent directory
            
        Returns:
            String representation of the directory tree
        """
        if depth > self.max_depth:
            return ""
        
        result = ""
        
        try:
            # Get and sort items
            items = sorted(os.listdir(directory))
            items = [item for item in items if not self._should_exclude(os.path.join(directory, item))]
            
            for i, item in enumerate(items):
                item_path = os.path.join(directory, item)
                is_current_last = (i == len(items) - 1)
                
                # Add the current item to the tree
                if depth == 0:
                    # Skip root representation as it's already in the header
                    pass
                else:
                    # Choose the correct symbol based on whether this is the last item
                    symbol = "└── " if is_current_last else "├── "
                    result += f"{prefix}{symbol}{item}\n"
                
                # Add children if this is a directory
                if os.path.isdir(item_path):
                    # Determine the new prefix for children
                    if depth == 0:
                        new_prefix = ""
                    else:
                        new_prefix = prefix + ("    " if is_current_last else "│   ")
                    
                    # Recursively add children
                    result += self._generate_tree(
                        item_path, 
                        new_prefix, 
                        depth + 1, 
                        is_current_last
                    )
        except PermissionError:
            logger.warning(f"Permission denied for directory: {directory}")
            result += f"{prefix}└── [Permission Denied]\n"
        except Exception as e:
            logger.error(f"Error generating tree for {directory}: {str(e)}")
            result += f"{prefix}└── [Error: {str(e)}]\n"
        
        return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate file structure data")
    parser.add_argument("--root", "-r", type=str, default=".", help="Project root directory")
    parser.add_argument("--output", "-o", type=str, default="output/structure", help="Output directory")
    parser.add_argument("--depth", "-d", type=int, default=10, help="Maximum directory depth")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and directories")
    parser.add_argument("--exclude", "-e", type=str, nargs="+", help="Additional directories to exclude")
    parser.add_argument("--format", "-f", type=str, choices=["json", "markdown", "all"], default="all", help="Output format")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of saving to file")
    
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
    
    # Create generator
    generator = FileStructureGenerator(
        project_root=args.root,
        output_dir=args.output,
        max_depth=args.depth,
        excluded_dirs=excluded_dirs,
        include_hidden=args.include_hidden
    )
    
    if args.stdout:
        # Print directly to stdout
        if args.format == "json" or args.format == "all":
            result = generator.generate_json()
            print(json.dumps(result["structure"], indent=2))
            
        if args.format == "markdown" or args.format == "all":
            result = generator.generate_markdown()
            print(result["content"])
    else:
        # Save to files
        if args.format == "json":
            generator.generate_json()
        elif args.format == "markdown":
            generator.generate_markdown()
        else:
            generator.generate_all() 