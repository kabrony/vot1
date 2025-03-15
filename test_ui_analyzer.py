#!/usr/bin/env python3
"""
Test script for UI analysis functionality.
"""

import os
import sys
import logging
import argparse
import asyncio
from vot1_architecture_analyzer import ArchitectureAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("test_ui_analyzer")

async def main():
    """Test the UI analysis functionality."""
    # Create analyzer instance with UI focus
    analyzer = ArchitectureAnalyzer(
        project_root=".",
        output_dir="ui_analysis",
        enable_perplexity=False,
        enable_claude=False,
        analyze_imports=True,
        analyze_classes=True,
        analyze_functions=False,
        analyze_dependencies=False,
        analyze_ui=True,
        analyze_docs=False,
        check_github_issues=False,
    )
    
    # Run UI-focused analysis
    try:
        logger.info("Starting UI/UX focused analysis")
        
        # Find all Python files
        python_files = analyzer._find_python_files()
        logger.info(f"Found {len(python_files)} Python files to analyze")
        
        # Analyze module structure (required for UI analysis)
        await analyzer._analyze_module_structure(python_files)
        logger.info(f"Analyzed {len(analyzer.modules)} modules, {sum(len(c) for c in analyzer.classes.values())} classes, and {sum(len(f) for f in analyzer.functions.values())} functions")
        
        # Analyze UI components
        await analyzer._analyze_ui_components()
        
        # Save analysis
        analyzer._save_analysis()
        
        print("\n✅ UI/UX Analysis Completed Successfully")
        print(f"📊 Analyzed {len(analyzer.modules)} modules and UI/UX components")
        
        # Count UI components
        ui_component_count = 0
        for category in analyzer.ui_components.values():
            for components in category.values():
                ui_component_count += len(components)
        
        print(f"🎨 Identified {ui_component_count} UI/UX components")
        print(f"📂 Results saved to {analyzer.output_dir}")
        
        return {
            "status": "success",
            "ui_components_count": ui_component_count,
            "output_dir": analyzer.output_dir
        }
    except Exception as e:
        logger.error(f"UI/UX analysis failed: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "output_dir": analyzer.output_dir
        }

if __name__ == "__main__":
    # Set up asyncio to run on Windows properly
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main function
    asyncio.run(main()) 