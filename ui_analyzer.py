#!/usr/bin/env python3
"""
UI/UX Analyzer for VOT1 Architecture.

This script analyzes the UI/UX components in the VOT1 codebase.
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import re
import ast
from typing import Dict, List, Any, Optional, Set, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("ui_analyzer")

class UIAnalyzer:
    """Analyzer for UI/UX components in the VOT1 codebase."""
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = "ui_analysis",
    ):
        """
        Initialize the UI analyzer.
        
        Args:
            project_root: Root directory of the VOT1 project to analyze
            output_dir: Output directory for analysis results
        """
        self.project_root = os.path.abspath(project_root)
        self.output_dir = os.path.join(self.project_root, output_dir)
        
        # Initialize data structures
        self.modules = {}
        self.classes = {}
        self.ui_components = {
            "frameworks": {},
            "components": {},
            "modules": {},
            "patterns": {}
        }
        
        # Excluded directories
        self.excluded_dirs = [
            "venv",
            ".venv",
            "env",
            ".env",
            ".git",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            ".coverage",
        ]
        
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
        
        return python_files
    
    def _get_name(self, node: ast.AST) -> str:
        """Get the name of a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Index):
            return self._get_name(node.value)
        elif isinstance(node, ast.Slice):
            lower = self._get_name(node.lower) if node.lower else ""
            upper = self._get_name(node.upper) if node.upper else ""
            step = self._get_name(node.step) if node.step else ""
            return f"{lower}:{upper}:{step}"
        else:
            return str(node)
    
    def _get_arg_names(self, args: List[ast.arg]) -> List[str]:
        """Get the names of function arguments."""
        return [arg.arg for arg in args]
    
    def _get_node_line_count(self, node: ast.AST) -> int:
        """Get the line count of a node."""
        if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
            return node.end_lineno - node.lineno + 1
        return 0
    
    async def _analyze_module_structure(self, python_files: List[str]) -> None:
        """Analyze the structure of all Python modules."""
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Get module name from file path
                rel_path = os.path.relpath(file_path, self.project_root)
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # Parse the AST
                tree = ast.parse(content)
                
                # Initialize module data
                self.modules[module_name] = {
                    "path": rel_path,
                    "imports": [],
                    "classes": [],
                    "functions": [],
                    "size": len(content),
                    "line_count": len(content.splitlines())
                }
                
                # Initialize classes and functions for this module
                self.classes[module_name] = {}
                
                # Analyze imports, classes, and functions
                for node in ast.walk(tree):
                    # Analyze imports
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                self.modules[module_name]["imports"].append(name.name)
                        else:  # ImportFrom
                            module = node.module or ""
                            for name in node.names:
                                self.modules[module_name]["imports"].append(f"{module}.{name.name}")
                    
                    # Analyze classes
                    elif isinstance(node, ast.ClassDef):
                        class_name = node.name
                        self.modules[module_name]["classes"].append(class_name)
                        
                        # Get class methods
                        methods = {}
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                method_name = item.name
                                methods[method_name] = {
                                    "args": self._get_arg_names(item.args.args),
                                    "line_count": self._get_node_line_count(item)
                                }
                        
                        # Store class info
                        self.classes[module_name][class_name] = {
                            "methods": methods,
                            "line_count": self._get_node_line_count(node)
                        }
                    
                    # Analyze functions (not methods)
                    elif isinstance(node, ast.FunctionDef):
                        # Check if this is a top-level function (not a method)
                        is_top_level = True
                        for parent in ast.walk(tree):
                            if isinstance(parent, ast.ClassDef) and node in parent.body:
                                is_top_level = False
                                break
                        
                        if is_top_level:
                            function_name = node.name
                            self.modules[module_name]["functions"].append(function_name)
            
            except Exception as e:
                logger.error(f"Error analyzing module {file_path}: {str(e)}")
    
    async def _analyze_ui_components(self) -> None:
        """Analyze UI/UX components in the codebase."""
        logger.info("Analyzing UI/UX components...")
        
        # UI frameworks and libraries to look for
        ui_frameworks = {
            "react": "React",
            "vue": "Vue.js",
            "angular": "Angular",
            "svelte": "Svelte",
            "threejs": "Three.js",
            "d3": "D3.js",
            "plotly": "Plotly",
            "bokeh": "Bokeh",
            "dash": "Dash",
            "streamlit": "Streamlit",
            "flask": "Flask",
            "django": "Django",
            "bootstrap": "Bootstrap",
            "tailwind": "TailwindCSS",
            "material-ui": "Material UI",
            "chakra-ui": "Chakra UI",
            "blueprint": "Blueprint",
            "antd": "Ant Design",
        }
        
        # UI/UX file patterns
        ui_file_patterns = [
            (r".*dashboard.*\.py$", "Dashboard"),
            (r".*ui.*\.py$", "UI Module"),
            (r".*view.*\.py$", "View"),
            (r".*template.*\.py$", "Template"),
            (r".*component.*\.py$", "Component"),
            (r".*widget.*\.py$", "Widget"),
            (r".*page.*\.py$", "Page"),
            (r".*screen.*\.py$", "Screen"),
            (r".*layout.*\.py$", "Layout"),
            (r".*form.*\.py$", "Form"),
        ]
        
        # Common UI/UX class names
        ui_class_patterns = [
            "Dashboard",
            "View",
            "Template",
            "Component",
            "Widget",
            "Page",
            "Screen",
            "Layout",
            "Form",
            "Button",
            "Input",
            "Dropdown",
            "Menu",
            "Modal",
            "Dialog",
            "Tooltip",
            "Card",
            "Panel",
            "Tab",
            "Navbar",
            "Sidebar",
            "Footer",
            "Header",
        ]
        
        # Initialize UI components
        self.ui_components = {
            "frameworks": {framework: [] for framework in ui_frameworks.values()},
            "components": {pattern: [] for _, pattern in ui_file_patterns},
            "modules": {"UI Module": []},
            "patterns": {pattern: [] for pattern in ui_class_patterns}
        }
        
        # Analyze imports for UI frameworks
        for module_name, module_info in self.modules.items():
            for import_name in module_info["imports"]:
                for framework_key, framework_name in ui_frameworks.items():
                    if framework_key in import_name.lower():
                        self.ui_components["frameworks"][framework_name].append(f"{module_name} ({module_info['path']})")
                        break
        
        # Check file patterns for UI components
        for module_name, module_info in self.modules.items():
            file_path = module_info["path"]
            for pattern, component_type in ui_file_patterns:
                if re.match(pattern, file_path):
                    self.ui_components["components"][component_type].append(f"{module_name} ({file_path})")
                    break
        
        # Look for common UI module patterns in directory structure
        ui_dirs = ["ui", "interface", "frontend", "view", "template", "component", "widget", "page", "screen", "layout", "form"]
        for module_name, module_info in self.modules.items():
            file_path = module_info["path"]
            dir_path = os.path.dirname(file_path)
            for ui_dir in ui_dirs:
                if f"/{ui_dir}/" in dir_path or dir_path.endswith(f"/{ui_dir}"):
                    self.ui_components["modules"]["UI Module"].append(f"{module_name} ({file_path})")
                    break
        
        # Look for UI class patterns
        for module_name, classes in self.classes.items():
            for class_name in classes:
                for pattern in ui_class_patterns:
                    if pattern.lower() in class_name.lower():
                        self.ui_components["patterns"][pattern].append(f"{module_name}.{class_name}")
                        break
        
        # Count total UI components
        ui_component_count = 0
        for category in self.ui_components.values():
            for components in category.values():
                ui_component_count += len(components)
        
        logger.info(f"Identified {ui_component_count} UI/UX components")
        
        # Save UI components analysis
        ui_file = os.path.join(self.output_dir, "ui_components.json")
        os.makedirs(os.path.dirname(ui_file), exist_ok=True)
        with open(ui_file, "w") as f:
            json.dump(self.ui_components, f, indent=2)
        
        logger.info(f"UI/UX components analysis saved to {ui_file}")
    
    def save_analysis(self) -> None:
        """Save the analysis results to JSON files."""
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save modules
        with open(os.path.join(self.output_dir, "modules.json"), "w") as f:
            json.dump(self.modules, f, indent=2)
        
        # Save classes
        with open(os.path.join(self.output_dir, "classes.json"), "w") as f:
            json.dump(self.classes, f, indent=2)
        
        # Save UI components
        with open(os.path.join(self.output_dir, "ui_components.json"), "w") as f:
            json.dump(self.ui_components, f, indent=2)
        
        logger.info(f"Analysis results saved to {self.output_dir}")
    
    async def analyze(self) -> Dict[str, Any]:
        """Run the UI/UX analysis."""
        try:
            logger.info(f"Starting UI/UX analysis in {self.project_root}")
            
            # Find all Python files in the project
            python_files = self._find_python_files()
            logger.info(f"Found {len(python_files)} Python files to analyze")
            
            # Analyze modules and classes
            await self._analyze_module_structure(python_files)
            logger.info(f"Analyzed {len(self.modules)} modules with {sum(len(c) for c in self.classes.values())} classes")
            
            # Analyze UI components
            await self._analyze_ui_components()
            
            # Save analysis results
            self.save_analysis()
            
            # Count UI components
            ui_component_count = 0
            for category in self.ui_components.values():
                for components in category.values():
                    ui_component_count += len(components)
            
            logger.info(f"UI/UX analysis completed successfully")
            
            return {
                "status": "success",
                "modules_count": len(self.modules),
                "classes_count": sum(len(classes) for classes in self.classes.values()),
                "ui_components_count": ui_component_count,
                "output_dir": self.output_dir
            }
        except Exception as e:
            logger.error(f"UI/UX analysis failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "output_dir": self.output_dir
            }

async def main():
    """Main entry point for the UI analyzer."""
    parser = argparse.ArgumentParser(description="VOT1 UI/UX Analyzer")
    parser.add_argument("--root", "-r", type=str, default=".", help="Root directory of the VOT1 project to analyze")
    parser.add_argument("--output", "-o", type=str, default="ui_analysis", help="Output directory for analysis results")
    parser.add_argument("--test", action="store_true", help="Run a quick test on a small set of files")
    
    args = parser.parse_args()
    
    if args.test:
        # Run a quick test on a small set of files
        test_files = [
            os.path.join(args.root, "hybrid_reasoning.py"),
            os.path.join(args.root, "json_fixer.py"),
            os.path.join(args.root, "memory_troubleshooter.py")
        ]
        
        # Create analyzer instance
        analyzer = UIAnalyzer(
            project_root=args.root,
            output_dir=args.output
        )
        
        # Run manual test analysis
        try:
            logger.info(f"Starting test analysis on {len(test_files)} files")
            
            # Analyze module structure
            await analyzer._analyze_module_structure(test_files)
            logger.info(f"Analyzed {len(analyzer.modules)} modules and {sum(len(c) for c in analyzer.classes.values())} classes")
            
            # Analyze UI components
            await analyzer._analyze_ui_components()
            
            # Save analysis results
            analyzer.save_analysis()
            
            # Count UI components
            ui_component_count = 0
            for category in analyzer.ui_components.values():
                for components in category.values():
                    ui_component_count += len(components)
            
            print("\n✅ Test Analysis Completed Successfully")
            print(f"📊 Analyzed {len(analyzer.modules)} modules and {sum(len(c) for c in analyzer.classes.values())} classes")
            print(f"🎨 Identified {ui_component_count} UI/UX components")
            print(f"📂 Results saved to {analyzer.output_dir}")
            
            return {
                "status": "success",
                "modules_count": len(analyzer.modules),
                "classes_count": sum(len(classes) for classes in analyzer.classes.values()),
                "ui_components_count": ui_component_count,
                "output_dir": analyzer.output_dir
            }
        except Exception as e:
            logger.error(f"Test analysis failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "output_dir": analyzer.output_dir
            }
    else:
        # Create analyzer instance
        analyzer = UIAnalyzer(
            project_root=args.root,
            output_dir=args.output
        )
        
        # Run the analysis
        results = await analyzer.analyze()
        
        # Print summary
        if results["status"] == "success":
            print("\n✅ VOT1 UI/UX Analysis Completed Successfully")
            print(f"📊 Analyzed {results['modules_count']} modules and {results['classes_count']} classes")
            print(f"🎨 Identified {results['ui_components_count']} UI/UX components")
            print(f"📂 Results saved to {results['output_dir']}")
        else:
            print(f"\n❌ VOT1 UI/UX Analysis Failed: {results['error']}")
            print(f"📂 Partial results may have been saved to {results['output_dir']}")
        
        return results

if __name__ == "__main__":
    # Set up asyncio to run on Windows properly
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main function
    asyncio.run(main()) 