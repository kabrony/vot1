#!/usr/bin/env python3
"""
Generate Folder Structure

Command-line utility to generate folder structure in Markdown format.
"""

import os
import sys
import argparse
import logging
from utils.file_structure_generator import FileStructureGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("folder_structure")

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Generate folder structure as Markdown")
    parser.add_argument("--root", "-r", type=str, default=".", help="Project root directory")
    parser.add_argument("--output", "-o", type=str, default="output/structure", help="Output directory")
    parser.add_argument("--depth", "-d", type=int, default=10, help="Maximum directory depth")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files and directories")
    parser.add_argument("--exclude", "-e", type=str, nargs="+", help="Additional directories to exclude")
    parser.add_argument("--stdout", "-s", action="store_true", help="Print Markdown to stdout instead of saving to file")
    
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
    
    # Create file structure generator
    generator = FileStructureGenerator(
        project_root=args.root,
        output_dir=args.output,
        max_depth=args.depth,
        include_hidden=args.include_hidden,
        excluded_dirs=excluded_dirs
    )
    
    # Generate markdown
    markdown = generator.generate_markdown()
    
    # Print to stdout if requested
    if args.stdout:
        print(markdown)
    else:
        markdown_path = os.path.join(args.output, "file_structure.md")
        print(f"✅ Markdown file structure saved to {markdown_path}")

if __name__ == "__main__":
    main() 