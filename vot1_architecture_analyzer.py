#!/usr/bin/env python3
"""
VOT1 Architecture Analyzer

This script analyzes the VOT1 system architecture, mapping dependencies,
identifying integration opportunities, and providing recommendations for
optimizing the entire system.

Features:
- Complete codebase mapping and visualization
- Dependency analysis between components
- Integration opportunity identification
- Performance bottleneck detection
- Recommendations for improved tool usage
- Leverages Perplexity for deep research
- Uses Claude 3.7 Sonnet for advanced reasoning
"""

import os
import sys
import json
import time
import logging
import argparse
import asyncio
import importlib
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime
import re
import ast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("architecture_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArchitectureAnalyzer")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
logger.info("Environment variables loaded from .env file")

# Try to import required packages
try:
    import anthropic
    anthropic_available = True
    logger.info("Anthropic SDK available")
except ImportError:
    logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")
    anthropic_available = False

try:
    from perplexipy import PerplexityClient
    perplexity_available = True
    logger.info("PerplexiPy available")
except ImportError:
    logger.warning("PerplexiPy not installed. Install with: pip install perplexipy")
    perplexity_available = False

# Base paths
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = PROJECT_ROOT / "output" / "architecture"
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger.info(f"Output directory: {OUTPUT_DIR}")

# API keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
CLAUDE_MODEL = os.environ.get("VOT1_PRIMARY_MODEL", "claude-3-7-sonnet-20250219")
PERPLEXITY_MODEL = os.environ.get("VOT1_SECONDARY_MODEL", "pplx-70b-online")

class ArchitectureAnalyzer:
    """
    Analyzes the VOT1 system architecture to identify integration opportunities
    and provide recommendations for optimization.
    """
    
    def __init__(
        self,
        project_root: str = ".",
        output_dir: str = "output/architecture",
        enable_perplexity: bool = True,
        enable_claude: bool = True,
        analyze_imports: bool = True,
        analyze_classes: bool = True,
        analyze_functions: bool = True,
        analyze_dependencies: bool = True,
        analyze_ui: bool = True,
        analyze_docs: bool = True,
        check_github_issues: bool = True,
    ):
        """
        Initialize the architecture analyzer.
        
        Args:
            project_root: Root directory of the project to analyze
            output_dir: Directory to store analysis output
            enable_perplexity: Whether to use Perplexity AI for research
            enable_claude: Whether to use Claude for recommendations
            analyze_imports: Whether to analyze imports
            analyze_classes: Whether to analyze classes
            analyze_functions: Whether to analyze functions
            analyze_dependencies: Whether to analyze dependencies
            analyze_ui: Whether to analyze UI/UX components
            analyze_docs: Whether to analyze documentation
            check_github_issues: Whether to check GitHub issues
        """
        # Set configuration
        self.project_root = os.path.abspath(project_root)
        self.output_dir = output_dir
        self.enable_perplexity = enable_perplexity
        self.enable_claude = enable_claude
        self.analyze_imports = analyze_imports
        self.analyze_classes = analyze_classes
        self.analyze_functions = analyze_functions
        self.analyze_dependencies = analyze_dependencies
        self.analyze_ui = analyze_ui
        self.analyze_docs = analyze_docs
        self.check_github_issues = check_github_issues
        
        # Initialize state
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.analysis_dir = os.path.join(self.output_dir, f"analysis_{self.timestamp}")
        
        # Create directories
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Data structures
        self.modules = {}
        self.classes = {}
        self.functions = {}
        self.dependencies = {}
        self.components = {}
        self.integration_points = {}
        self.optimization_opportunities = {}
        self.ui_components = {}
        self.documentation_analysis = {}
        self.github_issues = {}
        self.recommendations = []
        self.perplexity_insights = {}
        self.claude_insights = {}
        
        # API keys
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_owner = os.environ.get("GITHUB_OWNER")
        self.github_repo = os.environ.get("GITHUB_REPO")
        
        # Initialize clients
        self.perplexity_client = None
        self.claude_client = None
        self.github_client = None
        self.CLAUDE_MODEL = os.environ.get("VOT1_PRIMARY_MODEL", "claude-3-7-sonnet-20240620")
        
        if self.enable_perplexity:
            try:
                import perplexipy
                self.perplexity_client = perplexipy.Client(
                    api_key=os.environ.get("PERPLEXITY_API_KEY")
                )
            except ImportError:
                logger.warning("PerplexiPy not available - continuing without Perplexity AI research")
                self.enable_perplexity = False
            except Exception as e:
                logger.warning(f"Error initializing Perplexity client: {str(e)}")
                self.enable_perplexity = False
        
        if self.enable_claude:
            try:
                import anthropic
                self.claude_client = anthropic.Anthropic(
                    api_key=os.environ.get("ANTHROPIC_API_KEY")
                )
            except ImportError:
                logger.warning("Anthropic SDK not available - continuing without Claude recommendations")
                self.enable_claude = False
            except Exception as e:
                logger.warning(f"Error initializing Claude client: {str(e)}")
                self.enable_claude = False
        
        if self.check_github_issues and self.github_token and self.github_owner and self.github_repo:
            try:
                import requests
                self.github_client = requests
                logger.info("GitHub API client initialized")
            except ImportError:
                logger.warning("Requests not available - continuing without GitHub issue checking")
                self.check_github_issues = False
        else:
            if self.check_github_issues:
                logger.warning("GitHub token, owner, or repo not found in environment variables - continuing without GitHub issue checking")
                self.check_github_issues = False
        
        logger.info(f"Output directory: {self.output_dir}")
    
    async def analyze(self):
        """
        Perform a comprehensive analysis of the VOT1 architecture.
        
        Returns:
            dict: Analysis results summary
        """
        try:
            logger.info(f"Starting VOT1 architecture analysis in {self.project_root}")
            
            # Find all Python files in the project
            python_files = self._find_python_files()
            logger.info(f"Found {len(python_files)} Python files to analyze")
            
            # Analyze modules, classes, and functions
            await self._analyze_module_structure(python_files)
            logger.info(f"Analyzed {len(self.modules)} modules with {sum(len(c) for c in self.classes.values())} classes and {sum(len(f) for f in self.functions.values())} functions")
            
            # Analyze dependencies between modules
            if self.analyze_dependencies:
                await self._analyze_dependencies()
                logger.info(f"Analyzed dependencies between modules")
            
            # Identify components
            await self._identify_components()
            logger.info(f"Identified {len(self.components)} major components")
            
            # Analyze UI/UX components if enabled
            if self.analyze_ui:
                await self._analyze_ui_components()
                
                # Count UI components
                ui_component_count = 0
                for category in self.ui_components.values():
                    for components in category.values():
                        ui_component_count += len(components)
                        
                logger.info(f"Identified {ui_component_count} UI/UX components")
            
            # Analyze documentation if enabled
            if self.analyze_docs:
                await self._analyze_documentation()
                logger.info("Completed documentation analysis")
            
            # Check GitHub issues if enabled
            if self.check_github_issues:
                await self._check_github_issues()
                logger.info(f"Retrieved and analyzed GitHub issues")
            
            # Identify integration points
            await self._identify_integration_points()
            logger.info(f"Identified {len(self.integration_points)} integration points")
            
            # Identify optimization opportunities
            await self._identify_optimization_opportunities()
            logger.info(f"Identified {len(self.optimization_opportunities)} optimization opportunities")
            
            # Generate recommendations using Perplexity AI if enabled
            if self.enable_perplexity:
                try:
                    await self._analyze_with_perplexity()
                    logger.info("Successfully analyzed with Perplexity AI")
                except Exception as e:
                    logger.warning(f"Perplexity AI analysis failed: {str(e)}")
            
            # Generate recommendations using Claude if enabled
            if self.enable_claude:
                try:
                    await self._analyze_with_claude()
                    logger.info("Successfully analyzed with Claude")
                except Exception as e:
                    logger.warning(f"Claude analysis failed: {str(e)}")
            
            # Generate recommendations
            await self._generate_recommendations()
            logger.info(f"Generated {len(self.recommendations)} recommendations")
            
            # Save analysis results
            self._save_analysis()
            logger.info(f"Saved analysis results to {self.output_dir}")
            
            # Return analysis summary
            return {
                "status": "success",
                "modules_count": len(self.modules),
                "classes_count": sum(len(classes) for classes in self.classes.values()),
                "functions_count": sum(len(funcs) for funcs in self.functions.values()),
                "components_count": len(self.components),
                "integration_points_count": len(self.integration_points),
                "optimization_opportunities_count": len(self.optimization_opportunities),
                "recommendations_count": len(self.recommendations),
                "ui_components_count": sum(sum(len(components) for components in category.values()) for category in self.ui_components.values()) if self.analyze_ui else 0,
                "output_dir": self.output_dir
            }
        except Exception as e:
            logger.error(f"VOT1 architecture analysis failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "output_dir": self.output_dir
            }
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        python_files = []
        
        # Define directories to exclude
        exclude_patterns = [
            "venv",
            ".venv",
            "env",
            ".env",
            "__pycache__",
            ".git",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
        ]
        
        for root, dirs, files in os.walk(self.project_root):
            # Modify dirs in-place to exclude directories
            dirs[:] = [d for d in dirs if d not in exclude_patterns and not d.startswith('.')]
            
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        return python_files

    async def _analyze_module_structure(self, python_files: List[str]) -> None:
        """Analyze the structure of all Python modules."""
        logger.info("Analyzing module structure...")
        
        for file_path in python_files:
            try:
                # Get file stats
                file_stats = os.stat(file_path)
                size_bytes = file_stats.st_size
                
                # Generate module name from file path
                rel_path = os.path.relpath(file_path, self.project_root)
                module_name = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                
                # Skip files that don't represent modules
                if module_name.startswith("."):
                    module_name = module_name[1:]
                
                # Read file content
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Count lines
                line_count = len(content.splitlines())
                
                # Parse with AST
                tree = ast.parse(content)
                
                # Extract imports
                imports = []
                from_imports = []
                
                if self.analyze_imports:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import) and hasattr(node, 'names'):
                            for name in node.names:
                                if hasattr(name, 'name'):
                                    imports.append(name.name)
                        
                        elif isinstance(node, ast.ImportFrom) and hasattr(node, 'module') and hasattr(node, 'names'):
                            for name in node.names:
                                if hasattr(name, 'name') and node.module:
                                    from_imports.append((node.module, name.name))
                
                # Extract classes
                classes = {}
                
                if self.analyze_classes:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef) and hasattr(node, 'name'):
                            methods = {}
                            for child in ast.iter_child_nodes(node):
                                if isinstance(child, ast.FunctionDef) and hasattr(child, 'name'):
                                    method_name = child.name
                                    args = self._get_arg_names(child)
                                    line_count = self._get_node_line_count(child)
                                    
                                    methods[method_name] = {
                                        "args": args,
                                        "line_count": line_count,
                                    }
                            
                            classes[node.name] = {
                                "methods": methods,
                                "line_count": self._get_node_line_count(node),
                            }
                
                # Extract functions
                functions = {}
                
                if self.analyze_functions:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and hasattr(node, 'name'):
                            # Skip methods (they're already in classes)
                            parent_classes = [cls for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)]
                            is_method = False
                            
                            for cls in parent_classes:
                                for child in ast.iter_child_nodes(cls):
                                    if isinstance(child, ast.FunctionDef) and child.name == node.name:
                                        is_method = True
                                        break
                            
                            if not is_method:
                                func_name = node.name
                                args = self._get_arg_names(node)
                                line_count = self._get_node_line_count(node)
                                
                                functions[func_name] = {
                                    "args": args,
                                    "line_count": line_count,
                                }
                
                # Store module information
                self.modules[module_name] = {
                    "path": file_path,
                    "imports": imports,
                    "from_imports": from_imports,
                    "size_bytes": size_bytes,
                    "line_count": line_count,
                }
                
                # Store classes and functions
                if classes:
                    self.classes[module_name] = classes
                
                if functions:
                    self.functions[module_name] = functions
                
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {str(e)}")
        
        logger.info(f"Analyzed structure of {len(self.modules)} modules")
    
    def _get_name(self, node: ast.AST) -> str:
        """Get the name of an AST node."""
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
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif hasattr(node, 'id'):
            return node.id
        elif hasattr(node, 'attr'):
            return node.attr
        elif hasattr(node, 'name'):
            return node.name
        elif hasattr(node, 'n'):
            return str(node.n)
        elif hasattr(node, 's'):
            return node.s
        else:
            return str(node)

    def _get_arg_names(self, node: ast.FunctionDef) -> List[str]:
        """Get the argument names of a function definition."""
        if not hasattr(node, 'args'):
            return []
        
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            if hasattr(arg, 'arg'):
                args.append(arg.arg)
        
        # Keyword-only arguments
        for arg in node.args.kwonlyargs:
            if hasattr(arg, 'arg'):
                args.append(f"*{arg.arg}")
        
        # Varargs
        if node.args.vararg and hasattr(node.args.vararg, 'arg'):
            args.append(f"*{node.args.vararg.arg}")
        
        # Kwargs
        if node.args.kwarg and hasattr(node.args.kwarg, 'arg'):
            args.append(f"**{node.args.kwarg.arg}")
        
        return args

    def _get_node_line_count(self, node: ast.AST) -> int:
        """Get the line count of an AST node."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            return node.end_lineno - node.lineno + 1
        return 0

    async def _analyze_dependencies(self) -> None:
        """Analyze dependencies between modules."""
        logger.info("Analyzing dependencies between modules...")
        
        # Initialize dependencies
        for module_name in self.modules:
            self.dependencies[module_name] = {
                "imports": set(),
                "imported_by": set(),
            }
        
        # Analyze imports
        for module_name, module_info in self.modules.items():
            # Direct imports
            for import_name in module_info["imports"]:
                # Check if this is a module we've analyzed
                if import_name in self.modules:
                    self.dependencies[module_name]["imports"].add(import_name)
                    self.dependencies[import_name]["imported_by"].add(module_name)
                else:
                    # Check if it's a submodule
                    for analyzed_module in self.modules:
                        if analyzed_module.startswith(import_name + "."):
                            self.dependencies[module_name]["imports"].add(analyzed_module)
                            self.dependencies[analyzed_module]["imported_by"].add(module_name)
            
            # From imports
            for from_module, import_name in module_info["from_imports"]:
                # Check if this is a module we've analyzed
                if from_module in self.modules:
                    self.dependencies[module_name]["imports"].add(from_module)
                    self.dependencies[from_module]["imported_by"].add(module_name)
                else:
                    # Check if it's a submodule
                    for analyzed_module in self.modules:
                        if analyzed_module.startswith(from_module + "."):
                            self.dependencies[module_name]["imports"].add(analyzed_module)
                            self.dependencies[analyzed_module]["imported_by"].add(module_name)
        
        # Convert sets to lists for JSON serialization
        for module_name in self.dependencies:
            self.dependencies[module_name]["imports"] = list(self.dependencies[module_name]["imports"])
            self.dependencies[module_name]["imported_by"] = list(self.dependencies[module_name]["imported_by"])
        
        logger.info("Dependency analysis completed")
    
    async def _identify_components(self) -> None:
        """Identify major components in the system."""
        logger.info("Identifying major components...")
        
        # Component patterns to look for
        component_patterns = [
            (r".*client\.py$", "Client"),
            (r".*_client\.py$", "Client"),
            (r".*server\.py$", "Server"),
            (r".*_server\.py$", "Server"),
            (r".*api\.py$", "API"),
            (r".*_api\.py$", "API"),
            (r".*database\.py$", "Database"),
            (r".*_database\.py$", "Database"),
            (r".*memory\.py$", "Memory"),
            (r".*_memory\.py$", "Memory"),
            (r".*memory_bridge\.py$", "Memory Bridge"),
            (r".*dashboard.*", "Dashboard"),
            (r".*cli.*", "CLI"),
            (r".*agent\.py$", "Agent"),
            (r".*_agent\.py$", "Agent"),
            (r".*research.*", "Research"),
            (r".*benchmark.*", "Benchmark"),
            (r".*test.*", "Test"),
            (r".*troubleshoot.*", "Troubleshooting"),
            (r".*hybrid.*", "Hybrid Intelligence"),
            (r".*utils.*", "Utilities"),
        ]
        
        # Module name patterns to look for 
        module_patterns = [
            (r"^src\.vot1\.composio", "Composio Integration"),
            (r"^src\.vot1\.memory", "Memory System"),
            (r"^src\.vot1\.agent", "Agent System"),
            (r"^src\.vot1\.dashboard", "Dashboard"),
            (r"^src\.vot1\.cli", "CLI"),
            (r"^src\.vot1\.blockchain", "Blockchain Integration"),
            (r"^src\.vot1\.distributed", "Distributed Systems"),
            (r"^src\.vot1\.research", "Research"),
            (r"^src\.vot1\.ui", "User Interface"),
            (r"^src\.vot1\.utils", "Utilities"),
        ]
        
        # Identify components based on file patterns
        for module_name, module_info in self.modules.items():
            path = module_info["path"]
            
            # Check file patterns
            for pattern, component_type in component_patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    if component_type not in self.components:
                        self.components[component_type] = []
                    self.components[component_type].append({
                        "module": module_name,
                        "path": path,
                        "size_bytes": module_info["size_bytes"],
                        "line_count": module_info["line_count"]
                    })
            
            # Check module patterns
            for pattern, component_type in module_patterns:
                if re.search(pattern, module_name, re.IGNORECASE):
                    if component_type not in self.components:
                        self.components[component_type] = []
                    
                    # Check if already added by file pattern
                    already_added = False
                    for components in self.components.values():
                        for component in components:
                            if component["module"] == module_name:
                                already_added = True
                                break
                        if already_added:
                            break
                    
                    if not already_added:
                        self.components[component_type].append({
                            "module": module_name,
                            "path": path,
                            "size_bytes": module_info["size_bytes"],
                            "line_count": module_info["line_count"]
                        })
        
        logger.info(f"Identified {len(self.components)} major components")
    
    async def _identify_integration_points(self) -> None:
        """Identify integration points between components."""
        logger.info("Identifying integration points between components...")
        
        # Look for specific integration patterns
        for module_name, module_info in self.modules.items():
            # Look for imports of important integration libraries
            integration_libraries = {
                "perplexipy": "Perplexity Integration",
                "anthropic": "Claude Integration",
                "composio": "Composio Integration",
                "mcp": "MCP Integration",
                "openai": "OpenAI Integration",
                "github": "GitHub Integration",
                "requests": "HTTP API Integration",
                "httpx": "HTTP API Integration",
                "fastapi": "FastAPI Integration",
                "flask": "Flask Integration",
                "websockets": "WebSocket Integration",
            }
            
            for import_name in module_info["imports"]:
                for lib, integration_type in integration_libraries.items():
                    if lib in import_name:
                        if integration_type not in self.integration_points:
                            self.integration_points[integration_type] = []
                        
                        self.integration_points[integration_type].append({
                            "module": module_name,
                            "path": module_info["path"],
                            "import": import_name
                        })
            
            for from_module, import_name in module_info["from_imports"]:
                for lib, integration_type in integration_libraries.items():
                    if lib in from_module:
                        if integration_type not in self.integration_points:
                            self.integration_points[integration_type] = []
                        
                        self.integration_points[integration_type].append({
                            "module": module_name,
                            "path": module_info["path"],
                            "import": f"{from_module}.{import_name}"
                        })
        
        logger.info(f"Identified {len(self.integration_points)} integration points")

    async def _identify_optimization_opportunities(self) -> None:
        """Identify optimization opportunities in the codebase."""
        logger.info("Identifying optimization opportunities...")
        
        # Identify modules with high complexity
        complexity_threshold = 10
        high_complexity_modules = []
        for module_name, module_info in self.modules.items():
            for function_name, function_info in self.functions.get(module_name, {}).items():
                if function_info.get("complexity", 0) > complexity_threshold:
                    high_complexity_modules.append({
                        "module": module_name,
                        "function": function_name,
                        "complexity": function_info.get("complexity", 0),
                        "path": module_info["path"],
                        "line_count": function_info.get("line_count", 0),
                        "opportunity": "Refactor high complexity function"
                    })
        
        if high_complexity_modules:
            self.optimization_opportunities["high_complexity"] = high_complexity_modules
        
        # Identify modules with high number of dependencies
        dependency_threshold = 5
        high_dependency_modules = []
        for module_name, deps in self.dependencies.items():
            if len(deps["imports"]) > dependency_threshold:
                high_dependency_modules.append({
                    "module": module_name,
                    "path": self.modules[module_name]["path"],
                    "dependency_count": len(deps["imports"]),
                    "dependencies": deps["imports"],
                    "opportunity": "Consider splitting module with high dependencies"
                })
        
        if high_dependency_modules:
            self.optimization_opportunities["high_dependencies"] = high_dependency_modules
        
        # Identify central modules (imported by many)
        centrality_threshold = 3
        central_modules = []
        for module_name, deps in self.dependencies.items():
            if len(deps["imported_by"]) > centrality_threshold:
                central_modules.append({
                    "module": module_name,
                    "path": self.modules[module_name]["path"],
                    "imported_by_count": len(deps["imported_by"]),
                    "imported_by": deps["imported_by"],
                    "opportunity": "Critical module imported by many - ensure robust testing"
                })
        
        if central_modules:
            self.optimization_opportunities["central_modules"] = central_modules
        
        # Identify large files
        size_threshold = 1000  # lines
        large_modules = []
        for module_name, module_info in self.modules.items():
            if module_info["line_count"] > size_threshold:
                large_modules.append({
                    "module": module_name,
                    "path": module_info["path"],
                    "line_count": module_info["line_count"],
                    "opportunity": "Consider splitting large file"
                })
        
        if large_modules:
            self.optimization_opportunities["large_modules"] = large_modules
        
        # Identify potential circular dependencies
        circular_deps = []
        for module_name, deps in self.dependencies.items():
            for imported in deps["imports"]:
                if imported in self.dependencies and module_name in self.dependencies[imported]["imports"]:
                    circular_deps.append({
                        "module1": module_name,
                        "module2": imported,
                        "opportunity": "Resolve circular dependency"
                    })
        
        if circular_deps:
            self.optimization_opportunities["circular_dependencies"] = circular_deps
        
        logger.info(f"Identified {sum(len(opps) for opps in self.optimization_opportunities.values())} optimization opportunities")
    
    async def _analyze_with_perplexity(self) -> None:
        """Use Perplexity AI to analyze the architecture and generate suggestions."""
        if not self.enable_perplexity:
            logger.info("Skipping Perplexity analysis (disabled)")
            return
        
        try:
            logger.info("Running Perplexity AI analysis...")
            
            # Prepare data for Perplexity
            analysis_summary = {
                "modules_count": len(self.modules),
                "classes_count": sum(len(classes) for classes in self.classes.values()),
                "functions_count": sum(len(funcs) for funcs in self.functions.values()),
                "major_components": list(self.components.keys()),
                "integration_points": list(self.integration_points.keys()),
                "optimization_opportunities_count": sum(len(opps) for opps in self.optimization_opportunities.values()),
            }
            
            # Create a context string with the architecture summary
            context = json.dumps(analysis_summary, indent=2)
            
            # Prepare the system prompt
            system_content = """You are an expert software architect specializing in Python systems. 
            You're analyzing the VOT1 system architecture to provide actionable recommendations for improvements.
            Focus on architectural patterns, integration opportunities, and optimization strategies based on the 
            provided analysis data. Consider modern best practices, scalability, maintainability, and performance.
            Provide specific, actionable recommendations with clear justifications."""
            
            # Prepare the user query
            user_content = f"""Based on the following architecture analysis of the VOT1 system, provide:
            1. An evaluation of the overall architecture design
            2. Recommendations for improving component integration
            3. Suggestions for optimizing performance and maintainability
            4. Modern architectural patterns that could benefit this system
            
            Architecture Analysis Summary:
            {context}"""
            
            # Call Perplexity API
            perplexity_response = self.perplexity_client.search(
                system_content=system_content,
                user_content=user_content
            )
            
            # Extract and save insights
            if perplexity_response and isinstance(perplexity_response, dict) and "response" in perplexity_response:
                self.perplexity_insights = {
                    "timestamp": datetime.now().isoformat(),
                    "analysis": perplexity_response["response"],
                }
                
                # Save to file
                perplexity_file = os.path.join(self.output_dir, "perplexity_analysis.json")
                with open(perplexity_file, "w") as f:
                    json.dump(self.perplexity_insights, f, indent=2)
                
                logger.info(f"Perplexity analysis saved to {perplexity_file}")
            else:
                logger.error("Failed to get valid response from Perplexity")
                
        except Exception as e:
            logger.error(f"Error in Perplexity analysis: {str(e)}")
            self.perplexity_insights = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_with_claude(self) -> None:
        """Use Claude 3.7 to analyze the architecture and generate suggestions."""
        if not self.enable_claude:
            logger.info("Skipping Claude analysis (disabled)")
            return
        
        try:
            logger.info("Running Claude 3.7 Sonnet analysis...")
            
            # Prepare data for Claude
            # Include more details than for Perplexity
            analysis_data = {
                "modules": {k: v for k, v in list(self.modules.items())[:10]},  # First 10 modules as example
                "components": self.components,
                "integration_points": self.integration_points,
                "optimization_opportunities": self.optimization_opportunities,
            }
            
            # Create a context string with the architecture details
            context = json.dumps(analysis_data, indent=2)
            
            # Prepare the system prompt for Claude
            system_message = """You are Claude 3.7 Sonnet, an expert in software architecture analysis and optimization.
            You're analyzing the VOT1 system architecture to provide detailed, actionable recommendations.
            Focus on:
            1. Architectural coherence and modularity
            2. Integration opportunities between components
            3. Performance optimization strategies
            4. Modern patterns and practices to implement
            5. Specific code structure improvements
            
            Provide a detailed analysis with concrete, specific recommendations that could be implemented immediately.
            Use your advanced reasoning capabilities to identify non-obvious optimization opportunities."""
            
            # Call Claude API
            claude_response = self.claude_client.messages.create(
                model=self.CLAUDE_MODEL,
                max_tokens=4000,
                system=system_message,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this VOT1 system architecture data and provide detailed recommendations:
                    
                    {context}
                    
                    Please provide:
                    1. An overall architectural assessment
                    2. Specific integration improvement recommendations
                    3. Performance optimization strategies
                    4. Modern architectural patterns to implement
                    5. Code structure improvements"""
                }]
            )
            
            # Extract and save insights
            if claude_response and hasattr(claude_response, 'content'):
                content = claude_response.content[0].text if hasattr(claude_response.content[0], 'text') else str(claude_response.content[0])
                
                self.claude_insights = {
                    "timestamp": datetime.now().isoformat(),
                    "analysis": content,
                }
                
                # Save to file
                claude_file = os.path.join(self.output_dir, "claude_analysis.json")
                with open(claude_file, "w") as f:
                    json.dump(self.claude_insights, f, indent=2)
                
                logger.info(f"Claude analysis saved to {claude_file}")
            else:
                logger.error("Failed to get valid response from Claude")
                
        except Exception as e:
            logger.error(f"Error in Claude analysis: {str(e)}")
            self.claude_insights = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_recommendations(self) -> None:
        """Generate final recommendations based on all analyses."""
        logger.info("Generating final recommendations...")
        
        # Start with basic recommendations from direct analysis
        self.recommendations = []
        
        # Add recommendations from optimization opportunities
        for category, opportunities in self.optimization_opportunities.items():
            for opp in opportunities:
                self.recommendations.append({
                    "type": category,
                    "target": opp.get("module", opp.get("module1", "Unknown")),
                    "description": opp.get("opportunity", "Optimization opportunity"),
                    "details": opp
                })
        
        # Add integration recommendations
        if self.integration_points:
            # Find missing integrations
            potential_integrations = {
                "Perplexity Integration": "Consider integrating with Perplexity AI for advanced research capabilities",
                "Claude Integration": "Consider integrating with Claude 3.7 for advanced reasoning capabilities",
                "Composio Integration": "Consider integrating with Composio for workflow automation",
                "GitHub Integration": "Consider integrating with GitHub for version control features",
                "FastAPI Integration": "Consider using FastAPI for high-performance API development",
            }
            
            for integration, description in potential_integrations.items():
                if integration not in self.integration_points:
                    self.recommendations.append({
                        "type": "missing_integration",
                        "target": "system",
                        "description": description,
                        "details": {"integration": integration}
                    })
        
        # Add architectural recommendations
        component_types = list(self.components.keys())
        if "API" not in component_types:
            self.recommendations.append({
                "type": "architecture",
                "target": "system",
                "description": "Consider adding a dedicated API layer for better service integration",
                "details": {"missing_component": "API"}
            })
        
        if "Database" not in component_types:
            self.recommendations.append({
                "type": "architecture",
                "target": "system",
                "description": "Consider adding structured database access layer",
                "details": {"missing_component": "Database"}
            })
        
        # Add AI-generated insights if available
        if self.perplexity_insights and "analysis" in self.perplexity_insights:
            self.recommendations.append({
                "type": "perplexity_insight",
                "target": "system",
                "description": "Perplexity AI architectural assessment",
                "details": {"source": "perplexity", "file": "perplexity_analysis.json"}
            })
        
        if self.claude_insights and "analysis" in self.claude_insights:
            self.recommendations.append({
                "type": "claude_insight",
                "target": "system",
                "description": "Claude 3.7 architectural assessment",
                "details": {"source": "claude", "file": "claude_analysis.json"}
            })
        
        # Save recommendations to file
        recommendations_file = os.path.join(self.output_dir, "recommendations.json")
        with open(recommendations_file, "w") as f:
            json.dump({"recommendations": self.recommendations}, f, indent=2)
        
        logger.info(f"Generated {len(self.recommendations)} recommendations saved to {recommendations_file}")

    def _save_analysis(self) -> None:
        """Save the analysis results to JSON files."""
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save modules
        with open(os.path.join(self.output_dir, "modules.json"), "w") as f:
            json.dump(self.modules, f, indent=2)
        
        # Save classes
        with open(os.path.join(self.output_dir, "classes.json"), "w") as f:
            json.dump(self.classes, f, indent=2)
        
        # Save functions
        with open(os.path.join(self.output_dir, "functions.json"), "w") as f:
            json.dump(self.functions, f, indent=2)
        
        # Save dependencies
        with open(os.path.join(self.output_dir, "dependencies.json"), "w") as f:
            json.dump(self.dependencies, f, indent=2)
        
        # Save components
        with open(os.path.join(self.output_dir, "components.json"), "w") as f:
            json.dump(self.components, f, indent=2)
        
        # Save integration points
        with open(os.path.join(self.output_dir, "integration_points.json"), "w") as f:
            json.dump(self.integration_points, f, indent=2)
        
        # Save optimization opportunities
        with open(os.path.join(self.output_dir, "optimization_opportunities.json"), "w") as f:
            json.dump(self.optimization_opportunities, f, indent=2)
        
        # Save recommendations if available
        if hasattr(self, 'recommendations') and self.recommendations:
            with open(os.path.join(self.output_dir, "recommendations.json"), "w") as f:
                json.dump(self.recommendations, f, indent=2)
        
        # Save UI components analysis if available
        if self.analyze_ui and self.ui_components:
            with open(os.path.join(self.output_dir, "ui_components.json"), "w") as f:
                json.dump(self.ui_components, f, indent=2)
        
        # Save documentation analysis if available
        if self.analyze_docs and self.documentation_analysis:
            with open(os.path.join(self.output_dir, "documentation_analysis.json"), "w") as f:
                json.dump(self.documentation_analysis, f, indent=2)
        
        # Save GitHub issues if available
        if self.check_github_issues and self.github_issues:
            with open(os.path.join(self.output_dir, "github_issues.json"), "w") as f:
                json.dump(self.github_issues, f, indent=2)
            
        logger.info(f"Analysis results saved to {self.output_dir}")
        
        # Generate a summary report
        self._generate_summary_report()

    async def _analyze_ui_components(self) -> None:
        """Analyze UI/UX components in the codebase."""
        if not self.analyze_ui:
            logger.info("Skipping UI/UX analysis (disabled)")
            return

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
            (r".*input.*\.py$", "Input"),
            (r".*button.*\.py$", "Button"),
            (r".*menu.*\.py$", "Menu"),
            (r".*navigation.*\.py$", "Navigation"),
            (r".*chart.*\.py$", "Chart"),
            (r".*graph.*\.py$", "Graph"),
            (r".*plot.*\.py$", "Plot"),
            (r".*visualiz.*\.py$", "Visualization"),
            (r".*theme.*\.py$", "Theme"),
            (r".*style.*\.py$", "Style"),
            (r".*color.*\.py$", "Color"),
            (r".*animation.*\.py$", "Animation"),
            (r".*transition.*\.py$", "Transition"),
            (r".*modal.*\.py$", "Modal"),
            (r".*popup.*\.py$", "Popup"),
            (r".*tooltip.*\.py$", "Tooltip"),
            (r".*notification.*\.py$", "Notification"),
            (r".*alert.*\.py$", "Alert"),
            (r".*toast.*\.py$", "Toast"),
            (r".*snackbar.*\.py$", "Snackbar"),
            (r".*dialog.*\.py$", "Dialog"),
            (r".*drawer.*\.py$", "Drawer"),
            (r".*sidebar.*\.py$", "Sidebar"),
            (r".*navbar.*\.py$", "Navbar"),
            (r".*header.*\.py$", "Header"),
            (r".*footer.*\.py$", "Footer"),
            (r".*card.*\.py$", "Card"),
            (r".*list.*\.py$", "List"),
            (r".*table.*\.py$", "Table"),
            (r".*grid.*\.py$", "Grid"),
            (r".*flex.*\.py$", "Flex"),
            (r".*responsive.*\.py$", "Responsive"),
            (r".*mobile.*\.py$", "Mobile"),
            (r".*desktop.*\.py$", "Desktop"),
            (r".*tablet.*\.py$", "Tablet"),
            (r".*accessibility.*\.py$", "Accessibility"),
            (r".*a11y.*\.py$", "Accessibility"),
            (r".*i18n.*\.py$", "Internationalization"),
            (r".*l10n.*\.py$", "Localization"),
            (r".*dark.*\.py$", "Dark Mode"),
            (r".*light.*\.py$", "Light Mode"),
            (r".*theme.*\.py$", "Theme"),
        ]
        
        # Common UI/UX class names
        ui_class_patterns = [
            "Dashboard",
            "UI",
            "View",
            "Template",
            "Component",
            "Widget",
            "Page",
            "Screen",
            "Layout",
            "Form",
            "Input",
            "Button",
            "Menu",
            "Navigation",
            "Chart",
            "Graph",
            "Plot",
            "Visualization",
            "Theme",
            "Style",
            "Color",
            "Animation",
            "Transition",
            "Modal",
            "Popup",
            "Tooltip",
            "Notification",
            "Alert",
            "Toast",
            "Snackbar",
            "Dialog",
            "Drawer",
            "Sidebar",
            "Navbar",
            "Header",
            "Footer",
            "Card",
            "List",
            "Table",
            "Grid",
            "Flex",
            "Responsive",
            "Mobile",
            "Desktop",
            "Tablet",
            "Accessibility",
            "I18n",
            "L10n",
            "DarkMode",
            "LightMode",
            "ThemeProvider",
        ]
        
        # Initialize UI component categories
        self.ui_components = {
            "frameworks": {},
            "components": {},
            "modules": {},
            "patterns": {},
        }
        
        # Analyze import statements for UI frameworks
        for module_name, module_info in self.modules.items():
            # Check imports for UI frameworks
            for import_name in module_info["imports"] + [i[0] for i in module_info["from_imports"]]:
                for framework_key, framework_name in ui_frameworks.items():
                    if framework_key in import_name.lower():
                        if framework_name not in self.ui_components["frameworks"]:
                            self.ui_components["frameworks"][framework_name] = []
                        
                        self.ui_components["frameworks"][framework_name].append({
                            "module": module_name,
                            "path": module_info["path"],
                            "import": import_name
                        })
            
            # Check file patterns for UI components
            for pattern, component_type in ui_file_patterns:
                if re.search(pattern, module_info["path"], re.IGNORECASE):
                    if component_type not in self.ui_components["components"]:
                        self.ui_components["components"][component_type] = []
                    
                    self.ui_components["components"][component_type].append({
                        "module": module_name,
                        "path": module_info["path"],
                        "size_bytes": module_info["size_bytes"],
                        "line_count": module_info["line_count"]
                    })
            
            # Check class names for UI patterns
            if module_name in self.classes:
                for class_name in self.classes[module_name]:
                    for pattern in ui_class_patterns:
                        if pattern.lower() in class_name.lower():
                            if pattern not in self.ui_components["patterns"]:
                                self.ui_components["patterns"][pattern] = []
                            
                            self.ui_components["patterns"][pattern].append({
                                "module": module_name,
                                "class": class_name,
                                "path": module_info["path"]
                            })
                            break
        
        # Look for common UI module patterns in directory structure
        ui_directories = [
            "ui",
            "frontend",
            "web",
            "templates",
            "views",
            "pages",
            "components",
            "widgets",
            "dashboard",
            "interface",
            "visualization",
            "viz",
        ]
        
        for module_name in self.modules:
            for ui_dir in ui_directories:
                if f".{ui_dir}." in f".{module_name}." or module_name.startswith(f"{ui_dir}."):
                    if ui_dir not in self.ui_components["modules"]:
                        self.ui_components["modules"][ui_dir] = []
                    
                    self.ui_components["modules"][ui_dir].append({
                        "module": module_name,
                        "path": self.modules[module_name]["path"]
                    })
        
        # Count total UI components
        total_components = (
            sum(len(comps) for comps in self.ui_components["frameworks"].values()) +
            sum(len(comps) for comps in self.ui_components["components"].values()) +
            sum(len(comps) for comps in self.ui_components["modules"].values()) +
            sum(len(comps) for comps in self.ui_components["patterns"].values())
        )
        
        logger.info(f"Identified {total_components} UI/UX components")
        
        # Save UI components to file
        ui_file = os.path.join(self.output_dir, "ui_components.json")
        with open(ui_file, "w") as f:
            json.dump({"ui_components": self.ui_components}, f, indent=2)
        
        logger.info(f"UI/UX analysis saved to {ui_file}")

    async def _analyze_documentation(self) -> None:
        """Analyze documentation quality and completeness."""
        if not self.analyze_docs:
            logger.info("Skipping documentation analysis (disabled)")
            return
        
        logger.info("Analyzing documentation...")
        
        # Initialize documentation analysis structure
        self.documentation_analysis = {
            "readme": {},
            "api_docs": {},
            "inline_docs": {},
            "markdown_files": {},
            "documentation_coverage": {},
            "missing_documentation": [],
            "improvement_opportunities": []
        }
        
        # Analyze README.md
        readme_path = os.path.join(self.project_root, "README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()
                
                readme_lines = readme_content.splitlines()
                readme_sections = []
                current_section = None
                
                for line in readme_lines:
                    if line.startswith("#"):
                        level = len(line) - len(line.lstrip("#"))
                        title = line.lstrip("# ").strip()
                        if current_section:
                            readme_sections.append(current_section)
                        current_section = {"title": title, "level": level, "content": ""}
                    elif current_section:
                        current_section["content"] += line + "\n"
                
                if current_section:
                    readme_sections.append(current_section)
                
                # Analyze README.md quality
                self.documentation_analysis["readme"] = {
                    "path": readme_path,
                    "size_bytes": os.path.getsize(readme_path),
                    "line_count": len(readme_lines),
                    "sections": len(readme_sections),
                    "sections_details": readme_sections,
                    "has_installation": any("install" in section["title"].lower() for section in readme_sections),
                    "has_usage": any("usage" in section["title"].lower() for section in readme_sections),
                    "has_api": any("api" in section["title"].lower() for section in readme_sections),
                    "has_example": any("example" in section["title"].lower() for section in readme_sections),
                    "has_contributing": any("contribut" in section["title"].lower() for section in readme_sections),
                    "quality_score": 0  # Will be calculated later
                }
                
                # Calculate README quality score (1-10)
                quality_score = 5  # Start with a neutral score
                required_sections = ["install", "usage", "api", "example", "contribut"]
                for section in required_sections:
                    if any(section in s["title"].lower() for s in readme_sections):
                        quality_score += 1
                
                # Adjust for length (too short is not good)
                if len(readme_lines) < 50:
                    quality_score -= 2
                elif len(readme_lines) > 300:
                    quality_score += 1
                
                # Ensure score is between 1-10
                quality_score = max(1, min(10, quality_score))
                self.documentation_analysis["readme"]["quality_score"] = quality_score
                
                # Add improvement opportunities
                if quality_score < 7:
                    missing_sections = [section for section in required_sections 
                                      if not any(section in s["title"].lower() for s in readme_sections)]
                    if missing_sections:
                        self.documentation_analysis["improvement_opportunities"].append({
                            "target": "README.md",
                            "description": f"README.md is missing sections: {', '.join(missing_sections)}",
                            "severity": "medium"
                        })
            except Exception as e:
                logger.error(f"Error analyzing README.md: {str(e)}")
        else:
            self.documentation_analysis["missing_documentation"].append({
                "file": "README.md",
                "description": "Missing README.md file",
                "severity": "high"
            })
        
        # Find all Markdown files
        md_files = []
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".md") and not file.startswith("."):
                    md_path = os.path.join(root, file)
                    rel_path = os.path.relpath(md_path, self.project_root)
                    
                    # Skip README.md as it's already analyzed
                    if rel_path == "README.md":
                        continue
                    
                    md_files.append({
                        "path": md_path,
                        "rel_path": rel_path,
                        "size_bytes": os.path.getsize(md_path)
                    })
        
        # Analyze Markdown files
        self.documentation_analysis["markdown_files"] = {
            "count": len(md_files),
            "files": md_files,
            "total_size_bytes": sum(file["size_bytes"] for file in md_files)
        }
        
        # Analyze inline documentation
        module_with_docstrings = 0
        class_with_docstrings = 0
        function_with_docstrings = 0
        total_modules = len(self.modules)
        total_classes = sum(len(classes) for classes in self.classes.values())
        total_functions = sum(len(funcs) for funcs in self.functions.values())
        
        # Check docstrings in modules
        for module_path in self.modules.values():
            try:
                with open(module_path["path"], "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                # Check for module docstring
                if ast.get_docstring(tree):
                    module_with_docstrings += 1
            except Exception as e:
                logger.debug(f"Error checking docstring in {module_path['path']}: {str(e)}")
        
        # Check docstrings in classes and functions
        for module_name, classes in self.classes.items():
            module_path = self.modules.get(module_name, {}).get("path")
            if not module_path:
                continue
                
            try:
                with open(module_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check class docstrings
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name in classes:
                        if ast.get_docstring(node):
                            class_with_docstrings += 1
                        
                        # Check method docstrings
                        for subnode in ast.walk(node):
                            if isinstance(subnode, ast.FunctionDef) and hasattr(subnode, 'parent') and subnode.parent == node:
                                if ast.get_docstring(subnode):
                                    function_with_docstrings += 1
            except Exception as e:
                logger.debug(f"Error checking docstrings in {module_path}: {str(e)}")
        
        # Calculate documentation coverage
        module_coverage = module_with_docstrings / total_modules if total_modules > 0 else 0
        class_coverage = class_with_docstrings / total_classes if total_classes > 0 else 0
        function_coverage = function_with_docstrings / total_functions if total_functions > 0 else 0
        total_coverage = (module_coverage + class_coverage + function_coverage) / 3
        
        self.documentation_analysis["inline_docs"] = {
            "module_coverage": module_coverage,
            "class_coverage": class_coverage,
            "function_coverage": function_coverage,
            "total_coverage": total_coverage,
            "modules_with_docstrings": module_with_docstrings,
            "classes_with_docstrings": class_with_docstrings,
            "functions_with_docstrings": function_with_docstrings,
            "total_modules": total_modules,
            "total_classes": total_classes,
            "total_functions": total_functions
        }
        
        # Add improvement opportunities
        if total_coverage < 0.5:
            self.documentation_analysis["improvement_opportunities"].append({
                "target": "inline_documentation",
                "description": f"Low documentation coverage ({total_coverage:.2%})",
                "severity": "high"
            })
        elif total_coverage < 0.7:
            self.documentation_analysis["improvement_opportunities"].append({
                "target": "inline_documentation",
                "description": f"Moderate documentation coverage ({total_coverage:.2%})",
                "severity": "medium"
            })
        
        # Save documentation analysis to file
        docs_file = os.path.join(self.output_dir, "documentation_analysis.json")
        with open(docs_file, "w") as f:
            json.dump({"documentation_analysis": self.documentation_analysis}, f, indent=2)
        
        logger.info(f"Documentation analysis saved to {docs_file}")
    
    async def _check_github_issues(self) -> None:
        """Check GitHub issues for the repository."""
        if not self.check_github_issues or not self.github_client:
            logger.info("Skipping GitHub issue checking (disabled or client not available)")
            return
        
        if not self.github_token or not self.github_owner or not self.github_repo:
            logger.warning("GitHub token, owner, or repo not available - skipping GitHub issue checking")
            return
        
        logger.info(f"Checking GitHub issues for {self.github_owner}/{self.github_repo}...")
        
        # Initialize GitHub issues structure
        self.github_issues = {
            "open_issues": [],
            "closed_issues": [],
            "open_count": 0,
            "closed_count": 0,
            "open_by_label": {},
            "issues_by_component": {},
            "frequent_issues": []
        }
        
        try:
            # Get open issues
            open_issues_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/issues?state=open&per_page=100"
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            open_issues_response = self.github_client.get(open_issues_url, headers=headers)
            if open_issues_response.status_code == 200:
                open_issues = open_issues_response.json()
                
                # Process open issues
                self.github_issues["open_issues"] = [{
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "labels": [label["name"] for label in issue["labels"]],
                    "assignees": [assignee["login"] for assignee in issue["assignees"]],
                    "comments": issue["comments"],
                    "body": issue.get("body", "")[:500] + ("..." if issue.get("body", "") and len(issue.get("body", "")) > 500 else "")
                } for issue in open_issues if not "pull_request" in issue]
                
                self.github_issues["open_count"] = len(self.github_issues["open_issues"])
                
                # Group issues by label
                for issue in self.github_issues["open_issues"]:
                    for label in issue["labels"]:
                        if label not in self.github_issues["open_by_label"]:
                            self.github_issues["open_by_label"][label] = []
                        self.github_issues["open_by_label"][label].append(issue["number"])
                
                # Group issues by component (using labels or title patterns)
                component_patterns = {
                    "ui": r"(ui|ux|interface|frontend|dashboard|visualization)",
                    "api": r"(api|endpoint|rest|http|server)",
                    "database": r"(db|database|storage|sql|nosql|mongodb|postgres)",
                    "auth": r"(auth|login|permission|access|security)",
                    "performance": r"(performance|slow|speed|optimization)",
                    "documentation": r"(doc|docs|documentation|readme)",
                    "testing": r"(test|tests|testing|spec|specs)",
                    "build": r"(build|ci|cd|pipeline|github action)",
                    "dependency": r"(dependency|dependencies|package|library)"
                }
                
                for issue in self.github_issues["open_issues"]:
                    # Check labels first
                    found_component = False
                    for label in issue["labels"]:
                        for component, _ in component_patterns.items():
                            if component.lower() in label.lower():
                                if component not in self.github_issues["issues_by_component"]:
                                    self.github_issues["issues_by_component"][component] = []
                                self.github_issues["issues_by_component"][component].append(issue["number"])
                                found_component = True
                                break
                    
                    # If no component found in labels, check title patterns
                    if not found_component:
                        title_lower = issue["title"].lower()
                        for component, pattern in component_patterns.items():
                            if re.search(pattern, title_lower, re.IGNORECASE):
                                if component not in self.github_issues["issues_by_component"]:
                                    self.github_issues["issues_by_component"][component] = []
                                self.github_issues["issues_by_component"][component].append(issue["number"])
                                break
                
                # Get recent closed issues (for reference)
                closed_issues_url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/issues?state=closed&per_page=20"
                closed_issues_response = self.github_client.get(closed_issues_url, headers=headers)
                
                if closed_issues_response.status_code == 200:
                    closed_issues = closed_issues_response.json()
                    
                    # Process closed issues
                    self.github_issues["closed_issues"] = [{
                        "number": issue["number"],
                        "title": issue["title"],
                        "url": issue["html_url"],
                        "closed_at": issue["closed_at"],
                        "labels": [label["name"] for label in issue["labels"]]
                    } for issue in closed_issues if not "pull_request" in issue]
                    
                    self.github_issues["closed_count"] = len(self.github_issues["closed_issues"])
                else:
                    logger.warning(f"Failed to fetch closed issues: {closed_issues_response.status_code}")
                
                # Identify frequent issue patterns
                title_words = {}
                for issue in self.github_issues["open_issues"]:
                    words = re.findall(r'\b\w+\b', issue["title"].lower())
                    for word in words:
                        if len(word) > 3:  # Skip short words
                            if word not in title_words:
                                title_words[word] = 0
                            title_words[word] += 1
                
                # Find common patterns (words that appear in multiple issues)
                frequent_words = {word: count for word, count in title_words.items() if count > 1}
                sorted_words = sorted(frequent_words.items(), key=lambda x: x[1], reverse=True)
                
                # Add top frequent words
                for word, count in sorted_words[:10]:
                    self.github_issues["frequent_issues"].append({
                        "term": word,
                        "count": count,
                        "related_issues": [issue["number"] for issue in self.github_issues["open_issues"] 
                                         if word in issue["title"].lower()]
                    })
                
                logger.info(f"Found {self.github_issues['open_count']} open issues and {self.github_issues['closed_count']} recently closed issues")
            else:
                logger.warning(f"Failed to fetch GitHub issues: {open_issues_response.status_code}")
        except Exception as e:
            logger.error(f"Error checking GitHub issues: {str(e)}")
        
        # Save GitHub issues to file
        github_file = os.path.join(self.output_dir, "github_issues.json")
        with open(github_file, "w") as f:
            json.dump({"github_issues": self.github_issues}, f, indent=2)
        
        logger.info(f"GitHub issues analysis saved to {github_file}")

    def _generate_summary_report(self):
        """Generate a summary report in Markdown format."""
        summary_path = os.path.join(self.output_dir, "analysis_summary.md")
        
        try:
            with open(summary_path, "w") as f:
                # Title
                f.write("# VOT1 Architecture Analysis Summary\n\n")
                
                # Timestamp
                f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # System overview
                f.write("## System Overview\n\n")
                
                # Statistics
                f.write("### Statistics\n\n")
                f.write("| Category | Count |\n")
                f.write("|----------|-------|\n")
                f.write(f"| Python Files | {len(self.modules)} |\n")
                f.write(f"| Classes | {sum(len(c) for c in self.classes.values())} |\n")
                f.write(f"| Functions | {sum(len(f) for f in self.functions.values())} |\n")
                f.write(f"| Components | {len(self.components)} |\n")
                f.write(f"| Integration Points | {len(self.integration_points)} |\n")
                f.write(f"| Optimization Opportunities | {len(self.optimization_opportunities)} |\n")
                
                if self.analyze_ui:
                    ui_component_count = sum(sum(len(components) for components in category.values()) 
                                            for category in self.ui_components.values())
                    f.write(f"| UI/UX Components | {ui_component_count} |\n")
                
                f.write("\n")
                
                # Components
                f.write("## Components\n\n")
                if self.components:
                    for name, component in self.components.items():
                        f.write(f"### {name}\n\n")
                        f.write(f"- **Module:** {component.get('module', 'N/A')}\n")
                        f.write(f"- **Path:** {component.get('path', 'N/A')}\n")
                        f.write(f"- **Size:** {component.get('size', 0)} bytes\n")
                        f.write(f"- **Line Count:** {component.get('line_count', 0)}\n\n")
                else:
                    f.write("No components identified.\n\n")
                
                # UI components
                if self.analyze_ui and self.ui_components:
                    f.write("## UI/UX Components\n\n")
                    
                    # UI Frameworks
                    if "frameworks" in self.ui_components and self.ui_components["frameworks"]:
                        f.write("### UI Frameworks\n\n")
                        for framework, instances in self.ui_components["frameworks"].items():
                            if instances:
                                f.write(f"#### {framework}\n\n")
                                for instance in instances:
                                    f.write(f"- {instance}\n")
                                f.write("\n")
                    
                    # UI Components
                    if "components" in self.ui_components and self.ui_components["components"]:
                        f.write("### UI Components\n\n")
                        for component_type, instances in self.ui_components["components"].items():
                            if instances:
                                f.write(f"#### {component_type}\n\n")
                                for instance in instances:
                                    f.write(f"- {instance}\n")
                                f.write("\n")
                
                # Documentation Analysis
                if self.analyze_docs and self.documentation_analysis:
                    f.write("## Documentation Analysis\n\n")
                    
                    # README quality
                    if "readme" in self.documentation_analysis:
                        readme = self.documentation_analysis["readme"]
                        f.write("### README Quality\n\n")
                        f.write(f"- **Score:** {readme.get('score', 'N/A')}/100\n")
                        f.write(f"- **Missing Sections:** {', '.join(readme.get('missing_sections', ['None']))}\n\n")
                    
                    # Documentation Coverage
                    if "coverage" in self.documentation_analysis:
                        coverage = self.documentation_analysis["coverage"]
                        f.write("### Documentation Coverage\n\n")
                        f.write(f"- **Module Documentation:** {coverage.get('module_coverage', 0)}%\n")
                        f.write(f"- **Class Documentation:** {coverage.get('class_coverage', 0)}%\n")
                        f.write(f"- **Function Documentation:** {coverage.get('function_coverage', 0)}%\n\n")
                    
                    # Documentation Improvement Opportunities
                    if "improvement_opportunities" in self.documentation_analysis and self.documentation_analysis["improvement_opportunities"]:
                        f.write("### Documentation Improvement Opportunities\n\n")
                        for opportunity in self.documentation_analysis["improvement_opportunities"]:
                            f.write(f"- {opportunity}\n")
                        f.write("\n")
                
                # GitHub Issues
                if self.check_github_issues and self.github_issues:
                    f.write("## GitHub Issues\n\n")
                    
                    # Open Issues
                    if "open_issues" in self.github_issues:
                        f.write(f"### Open Issues ({len(self.github_issues['open_issues'])})\n\n")
                        if len(self.github_issues['open_issues']) > 0:
                            f.write("| Issue | Title | Labels |\n")
                            f.write("|-------|-------|--------|\n")
                            for issue in self.github_issues['open_issues'][:10]:  # Show only first 10
                                f.write(f"| #{issue['number']} | {issue['title']} | {', '.join(issue.get('labels', []))} |\n")
                                
                                if len(self.github_issues['open_issues']) > 10:
                                    f.write(f"\n*... and {len(self.github_issues['open_issues']) - 10} more*\n")
                        else:
                            f.write("No open issues.\n")
                        f.write("\n")
                    
                    # Issue Patterns
                    if "patterns" in self.github_issues and self.github_issues["patterns"]:
                        f.write("### Common Issue Patterns\n\n")
                        for pattern, count in self.github_issues["patterns"].items():
                            f.write(f"- **{pattern}:** {count} issues\n")
                        f.write("\n")
                
                # Optimization Opportunities
                if self.optimization_opportunities:
                    f.write("## Optimization Opportunities\n\n")
                    for opportunity in self.optimization_opportunities:
                        f.write(f"- {opportunity}\n")
                    f.write("\n")
                
                # Recommendations
                if hasattr(self, 'recommendations') and self.recommendations:
                    f.write("## Recommendations\n\n")
                    for recommendation in self.recommendations:
                        f.write(f"- {recommendation}\n")
                    f.write("\n")
            
            logger.info(f"Generated summary report at {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {str(e)}")
            # Continue execution even if report generation fails

    async def generate_improved_documentation(self):
        """
        Generate improved documentation based on the analysis results.
        
        This method creates or updates documentation files including:
        - Updated README.md with missing sections
        - Architecture overview document
        - Component documentation
        - API reference
        
        Returns:
            dict: Information about the generated documentation
        """
        logger.info("Generating improved documentation based on analysis results")
        
        docs_dir = os.path.join(self.project_root, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        generated_docs = []
        
        try:
            # Generate architecture overview document
            arch_overview_path = os.path.join(docs_dir, "architecture_overview.md")
            await self._generate_architecture_overview(arch_overview_path)
            generated_docs.append(arch_overview_path)
            
            # Generate component documentation
            components_dir = os.path.join(docs_dir, "components")
            os.makedirs(components_dir, exist_ok=True)
            
            for name, component in self.components.items():
                component_path = os.path.join(components_dir, f"{name.lower().replace(' ', '_')}.md")
                await self._generate_component_doc(name, component, component_path)
                generated_docs.append(component_path)
            
            # Generate API reference
            api_reference_path = os.path.join(docs_dir, "api_reference.md")
            await self._generate_api_reference(api_reference_path)
            generated_docs.append(api_reference_path)
            
            # Improve README if documentation analysis is available
            if self.analyze_docs and self.documentation_analysis and "readme" in self.documentation_analysis:
                readme_path = os.path.join(self.project_root, "README.md")
                if os.path.exists(readme_path):
                    await self._improve_readme(readme_path)
                    generated_docs.append(readme_path)
            
            # Generate UI/UX documentation if UI analysis is available
            if self.analyze_ui and self.ui_components:
                ui_docs_path = os.path.join(docs_dir, "ui_components.md")
                await self._generate_ui_documentation(ui_docs_path)
                generated_docs.append(ui_docs_path)
            
            logger.info(f"Generated {len(generated_docs)} improved documentation files")
            
            return {
                "status": "success",
                "generated_docs": generated_docs
            }
        except Exception as e:
            logger.error(f"Failed to generate improved documentation: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "generated_docs": generated_docs
            }

    async def _generate_architecture_overview(self, output_path):
        """Generate an architecture overview document."""
        with open(output_path, "w") as f:
            # Title
            f.write("# VOT1 Architecture Overview\n\n")
            
            # Introduction
            f.write("## Introduction\n\n")
            f.write("This document provides a comprehensive overview of the VOT1 system architecture.\n")
            f.write("It covers the main components, their interactions, and design principles.\n\n")
            
            # System Overview
            f.write("## System Overview\n\n")
            f.write("VOT1 is composed of several key components that work together to provide a robust and efficient system.\n\n")
            
            # Components diagram placeholder
            f.write("```\n")
            f.write("┌─────────────────────────┐     ┌─────────────────────────┐\n")
            f.write("│                         │     │                         │\n")
            f.write("│    Hybrid Intelligence  │────▶│      Troubleshooting    │\n")
            f.write("│                         │     │                         │\n")
            f.write("└─────────────────────────┘     └─────────────────────────┘\n")
            f.write("            │                              ▲               \n")
            f.write("            │                              │               \n")
            f.write("            ▼                              │               \n")
            f.write("┌─────────────────────────┐     ┌─────────────────────────┐\n")
            f.write("│                         │     │                         │\n")
            f.write("│        Core Engine      │────▶│          UI/UX          │\n")
            f.write("│                         │     │                         │\n")
            f.write("└─────────────────────────┘     └─────────────────────────┘\n")
            f.write("```\n\n")
            
            # Components
            f.write("## Components\n\n")
            
            for name, component in self.components.items():
                f.write(f"### {name}\n\n")
                f.write(f"**Module:** {component.get('module', 'N/A')}\n\n")
                f.write(f"**Description:** A core component of the VOT1 system.\n\n")
                f.write(f"**File Path:** {component.get('path', 'N/A')}\n\n")
                f.write(f"**Size:** {component.get('size', 0)} bytes\n\n")
                f.write(f"**Line Count:** {component.get('line_count', 0)}\n\n")
            
            # Integration Points
            f.write("## Integration Points\n\n")
            
            if self.integration_points:
                for point in self.integration_points:
                    f.write(f"- {point}\n")
            else:
                f.write("No specific integration points identified.\n")
            
            f.write("\n")
            
            # Design Principles
            f.write("## Design Principles\n\n")
            f.write("The VOT1 system is designed with the following principles in mind:\n\n")
            f.write("1. **Modularity** - Components are designed to be modular and independent\n")
            f.write("2. **Extensibility** - The system can be easily extended with new components\n")
            f.write("3. **Robustness** - Error handling and recovery are built into each component\n")
            f.write("4. **Efficiency** - The system is optimized for performance\n\n")
            
            # Conclusion
            f.write("## Conclusion\n\n")
            f.write("This architecture overview provides a high-level understanding of the VOT1 system. ")
            f.write("For more detailed information about specific components, please refer to the component documentation.\n")
        
        logger.info(f"Generated architecture overview at {output_path}")

    async def _generate_component_doc(self, name, component, output_path):
        """Generate documentation for a specific component."""
        with open(output_path, "w") as f:
            # Title
            f.write(f"# {name} Component\n\n")
            
            # Basic information
            f.write("## Overview\n\n")
            f.write(f"**Module:** {component.get('module', 'N/A')}\n\n")
            f.write(f"**File Path:** {component.get('path', 'N/A')}\n\n")
            f.write(f"**Size:** {component.get('size', 0)} bytes\n\n")
            f.write(f"**Line Count:** {component.get('line_count', 0)}\n\n")
            
            # Description
            f.write("## Description\n\n")
            f.write(f"The {name} component is a core part of the VOT1 system. ")
            f.write("It provides essential functionality for the system's operation.\n\n")
            
            # Classes
            module_name = component.get('module', '')
            if module_name in self.classes and self.classes[module_name]:
                f.write("## Classes\n\n")
                
                for class_name, class_info in self.classes[module_name].items():
                    f.write(f"### {class_name}\n\n")
                    f.write(f"**Line Count:** {class_info.get('line_count', 0)}\n\n")
                    
                    if 'methods' in class_info and class_info['methods']:
                        f.write("#### Methods\n\n")
                        
                        for method_name, method_info in class_info['methods'].items():
                            args = ", ".join(method_info.get('args', []))
                            f.write(f"- **{method_name}({args})** - {method_info.get('line_count', 0)} lines\n")
                    
                    f.write("\n")
            
            # Usage Examples
            f.write("## Usage Examples\n\n")
            f.write("```python\n")
            f.write(f"# Example usage of the {name} component\n")
            
            if module_name in self.classes and self.classes[module_name]:
                class_name = list(self.classes[module_name].keys())[0]
                f.write(f"from {module_name} import {class_name}\n\n")
                f.write(f"# Initialize the component\n")
                f.write(f"{module_name.lower()} = {class_name}()\n\n")
                f.write(f"# Use the component\n")
                if 'methods' in self.classes[module_name][class_name] and self.classes[module_name][class_name]['methods']:
                    method_name = next((m for m in self.classes[module_name][class_name]['methods'].keys() 
                                       if m != '__init__'), None)
                    if method_name:
                        f.write(f"result = {module_name.lower()}.{method_name}()\n")
            
            f.write("```\n\n")
            
            # Integration with other components
            f.write("## Integration with Other Components\n\n")
            f.write(f"The {name} component interacts with other components in the VOT1 system ")
            f.write("to provide comprehensive functionality.\n\n")
            
            # Known limitations
            f.write("## Known Limitations\n\n")
            f.write("- This documentation is auto-generated and may not be complete\n")
            f.write("- Additional details about implementation specifics may be needed\n\n")
        
        logger.info(f"Generated component documentation for {name} at {output_path}")

    async def _generate_api_reference(self, output_path):
        """Generate API reference documentation."""
        with open(output_path, "w") as f:
            # Title
            f.write("# VOT1 API Reference\n\n")
            
            # Introduction
            f.write("## Introduction\n\n")
            f.write("This document provides a reference for all public APIs exposed by the VOT1 system.\n\n")
            
            # Classes
            f.write("## Classes\n\n")
            
            for module_name, classes in self.classes.items():
                f.write(f"### Module: {module_name}\n\n")
                
                for class_name, class_info in classes.items():
                    f.write(f"#### {class_name}\n\n")
                    f.write(f"**Line Count:** {class_info.get('line_count', 0)}\n\n")
                    
                    # Methods
                    if 'methods' in class_info and class_info['methods']:
                        f.write("##### Methods\n\n")
                        
                        for method_name, method_info in class_info['methods'].items():
                            args = ", ".join(method_info.get('args', []))
                            f.write(f"###### `{method_name}({args})`\n\n")
                            f.write(f"**Line Count:** {method_info.get('line_count', 0)}\n\n")
                            f.write(f"*No description available*\n\n")
                
                f.write("\n")
            
            # Functions
            if any(self.functions.values()):
                f.write("## Functions\n\n")
                
                for module_name, functions in self.functions.items():
                    if functions:
                        f.write(f"### Module: {module_name}\n\n")
                        
                        for func_name, func_info in functions.items():
                            args = ", ".join(func_info.get('args', []))
                            f.write(f"#### `{func_name}({args})`\n\n")
                            f.write(f"**Line Count:** {func_info.get('line_count', 0)}\n\n")
                            f.write(f"*No description available*\n\n")
    
    logger.info(f"Generated API reference at {output_path}")

    def _save_analysis(self) -> None:
        """Save the analysis results to JSON files."""
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save modules
        with open(os.path.join(self.output_dir, "modules.json"), "w") as f:
            json.dump(self.modules, f, indent=2)
        
        # Save classes
        with open(os.path.join(self.output_dir, "classes.json"), "w") as f:
            json.dump(self.classes, f, indent=2)
        
        # Save functions
        with open(os.path.join(self.output_dir, "functions.json"), "w") as f:
            json.dump(self.functions, f, indent=2)
        
        # Save dependencies
        with open(os.path.join(self.output_dir, "dependencies.json"), "w") as f:
            json.dump(self.dependencies, f, indent=2)
        
        # Save components
        with open(os.path.join(self.output_dir, "components.json"), "w") as f:
            json.dump(self.components, f, indent=2)
        
        # Save integration points
        with open(os.path.join(self.output_dir, "integration_points.json"), "w") as f:
            json.dump(self.integration_points, f, indent=2)
        
        # Save optimization opportunities
        with open(os.path.join(self.output_dir, "optimization_opportunities.json"), "w") as f:
            json.dump(self.optimization_opportunities, f, indent=2)
        
        # Save recommendations if available
        if hasattr(self, 'recommendations') and self.recommendations:
            with open(os.path.join(self.output_dir, "recommendations.json"), "w") as f:
                json.dump(self.recommendations, f, indent=2)
        
        # Save UI components analysis if available
        if self.analyze_ui and self.ui_components:
            with open(os.path.join(self.output_dir, "ui_components.json"), "w") as f:
                json.dump(self.ui_components, f, indent=2)
        
        # Save documentation analysis if available
        if self.analyze_docs and self.documentation_analysis:
            with open(os.path.join(self.output_dir, "documentation_analysis.json"), "w") as f:
                json.dump(self.documentation_analysis, f, indent=2)
        
        # Save GitHub issues if available
        if self.check_github_issues and self.github_issues:
            with open(os.path.join(self.output_dir, "github_issues.json"), "w") as f:
                json.dump(self.github_issues, f, indent=2)
            
        logger.info(f"Analysis results saved to {self.output_dir}")
        
        # Generate a summary report
        self._generate_summary_report()

    async def _analyze_ui_components(self) -> None:
        """Analyze UI/UX components in the codebase."""
        if not self.analyze_ui:
            logger.info("Skipping UI/UX analysis (disabled)")
            return

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
                "output_dir": analyzer.output_dir
            }
    elif args.ui_focus:
        # Create analyzer instance with UI focus
        analyzer = ArchitectureAnalyzer(
            project_root=args.root,
            output_dir=args.output,
            enable_perplexity=not args.no_perplexity,
            enable_claude=not args.no_claude,
            analyze_imports=True,
            analyze_classes=True,
            analyze_functions=False,
            analyze_dependencies=False,
            analyze_ui=True,
            analyze_docs=not args.skip_docs,
            check_github_issues=not args.skip_github,
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
            
            # Analyze with Claude if enabled
            if analyzer.enable_claude:
                await analyzer._analyze_with_claude()
            
            # Generate recommendations
            await analyzer._generate_recommendations()
            
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
            
            # Generate documentation if requested
            if args.generate_docs:
                print("\n🔄 Generating improved documentation...")
                doc_results = await analyzer.generate_improved_documentation()
                print(f"📝 Generated {len(doc_results['generated_docs'])} documentation files")
            
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
else:
    # Create analyzer instance for full analysis
    analyzer = ArchitectureAnalyzer(
        project_root=args.root,
        output_dir=args.output,
        enable_perplexity=not args.no_perplexity,
        enable_claude=not args.no_claude,
        analyze_imports=not args.skip_imports,
        analyze_classes=not args.skip_classes,
        analyze_functions=not args.skip_functions,
        analyze_dependencies=not args.skip_dependencies,
        analyze_ui=not args.skip_ui,
        analyze_docs=not args.skip_docs,
        check_github_issues=not args.skip_github,
    )
    
    # Run the analysis
    results = await analyzer.analyze()
    
    # Print summary
    if results["status"] == "success":
        print("\n✅ VOT1 Architecture Analysis Completed Successfully")
        print(f"📊 Analyzed {results['modules_count']} modules, {results['classes_count']} classes, and {results['functions_count']} functions")
        print(f"🔍 Identified {results['components_count']} major components and {results['integration_points_count']} integration points")
        print(f"💡 Generated {results['optimization_opportunities_count']} optimization opportunities and {results['recommendations_count']} recommendations")
        print(f"📂 Results saved to {results['output_dir']}")
        
        # Generate improved documentation if requested
        if args.generate_docs:
            print("\n🔄 Generating improved documentation based on analysis...")
            doc_results = await analyzer.generate_improved_documentation()
            print(f"📝 Generated {len(doc_results['generated_docs'])} documentation files")
    else:
        print(f"\n❌ VOT1 Architecture Analysis Failed: {results['error']}")
        print(f"📂 Partial results may have been saved to {results['output_dir']}")
    
    return results

async def main():
    """Main entry point for the VOT1 architecture analyzer."""
    parser = argparse.ArgumentParser(description="VOT1 Architecture Analyzer")
    parser.add_argument("--root", "-r", type=str, default=".", help="Root directory of the VOT1 project to analyze")
    parser.add_argument("--output", "-o", type=str, default="architecture_analysis", help="Output directory for analysis results")
    parser.add_argument("--no-perplexity", action="store_true", help="Disable Perplexity AI analysis")
    parser.add_argument("--no-claude", action="store_true", help="Disable Claude analysis")
    parser.add_argument("--skip-imports", action="store_true", help="Skip import analysis")
    parser.add_argument("--skip-classes", action="store_true", help="Skip class analysis")
    parser.add_argument("--skip-functions", action="store_true", help="Skip function analysis")
    parser.add_argument("--skip-dependencies", action="store_true", help="Skip dependency analysis")
    parser.add_argument("--skip-ui", action="store_true", help="Skip UI/UX component analysis")
    parser.add_argument("--skip-docs", action="store_true", help="Skip documentation analysis")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub issue checking")
    parser.add_argument("--test", action="store_true", help="Run a quick test on a small set of files")
    parser.add_argument("--generate-docs", action="store_true", help="Generate improved documentation based on analysis")
    parser.add_argument("--ui-focus", action="store_true", help="Focus analysis on UI/UX components")
    parser.add_argument("--docs-only", action="store_true", help="Generate documentation only, using existing analysis results")
    
    args = parser.parse_args()
    
    if args.test:
        # Run a quick test on hybrid_reasoning.py only
        test_files = [
            os.path.join(args.root, "hybrid_reasoning.py"),
            os.path.join(args.root, "json_fixer.py"),
            os.path.join(args.root, "memory_troubleshooter.py")
        ]
        
        # Create analyzer instance for test
        analyzer = ArchitectureAnalyzer(
            project_root=args.root,
            output_dir=args.output,
            enable_perplexity=False,
            enable_claude=False,
            analyze_imports=True,
            analyze_classes=True,
            analyze_functions=True,
            analyze_dependencies=False,
            analyze_ui=False,
            analyze_docs=False,
            check_github_issues=False,
        )
        
        # Run manual test analysis
        try:
            logger.info(f"Starting test analysis on {len(test_files)} files")
            
            # Analyze module structure
            await analyzer._analyze_module_structure(test_files)
            logger.info(f"Analyzed {len(analyzer.modules)} modules, {sum(len(c) for c in analyzer.classes.values())} classes, and {sum(len(f) for f in analyzer.functions.values())} functions")
            
            # Identify components
            await analyzer._identify_components()
            
            # Save test results
            analyzer._save_analysis()
            
            print("\n✅ Test Analysis Completed Successfully")
            print(f"📊 Analyzed {len(analyzer.modules)} modules, {sum(len(c) for c in analyzer.classes.values())} classes, and {sum(len(f) for f in analyzer.functions.values())} functions")
            print(f"📂 Results saved to {analyzer.output_dir}")
            
            return {
                "status": "success",
                "modules_count": len(analyzer.modules),
                "classes_count": sum(len(classes) for classes in analyzer.classes.values()),
                "functions_count": sum(len(funcs) for funcs in analyzer.functions.values()),
                "output_dir": analyzer.output_dir
            }
        except Exception as e:
            logger.error(f"Test analysis failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "output_dir": analyzer.output_dir
            }
    elif args.docs_only:
        # Create analyzer instance for documentation generation only
        analyzer = ArchitectureAnalyzer(
            project_root=args.root,
            output_dir=args.output,
            enable_perplexity=False,
            enable_claude=False,
            analyze_imports=False,
            analyze_classes=False,
            analyze_functions=False,
            analyze_dependencies=False,
            analyze_ui=True,
            analyze_docs=True,
            check_github_issues=True,
        )
        
        # Load existing analysis results if available
        try:
            # Load modules
            modules_path = os.path.join(args.output, "modules.json")
            if os.path.exists(modules_path):
                with open(modules_path, "r") as f:
                    analyzer.modules = json.load(f)
            
            # Load classes
            classes_path = os.path.join(args.output, "classes.json")
            if os.path.exists(classes_path):
                with open(classes_path, "r") as f:
                    analyzer.classes = json.load(f)
            
            # Load functions
            functions_path = os.path.join(args.output, "functions.json")
            if os.path.exists(functions_path):
                with open(functions_path, "r") as f:
                    analyzer.functions = json.load(f)
            
            # Load components
            components_path = os.path.join(args.output, "components.json")
            if os.path.exists(components_path):
                with open(components_path, "r") as f:
                    analyzer.components = json.load(f)
            
            # Load UI components
            ui_components_path = os.path.join(args.output, "ui_components.json")
            if os.path.exists(ui_components_path):
                with open(ui_components_path, "r") as f:
                    analyzer.ui_components = json.load(f)
            
            # Load documentation analysis
            doc_analysis_path = os.path.join(args.output, "documentation_analysis.json")
            if os.path.exists(doc_analysis_path):
                with open(doc_analysis_path, "r") as f:
                    analyzer.documentation_analysis = json.load(f)
            
            # Generate improved documentation
            doc_results = await analyzer.generate_improved_documentation()
            
            print("\n✅ Documentation Generation Completed Successfully")
            print(f"📝 Generated {len(doc_results['generated_docs'])} documentation files:")
            for doc_path in doc_results["generated_docs"]:
                print(f"  - {doc_path}")
            
            return {
                "status": "success",
                "generated_docs": doc_results["generated_docs"]
            }
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    elif args.ui_focus:
        # Create analyzer instance with UI focus
        analyzer = ArchitectureAnalyzer(
            project_root=args.root,
            output_dir=args.output,
            enable_perplexity=not args.no_perplexity,
            enable_claude=not args.no_claude,
            analyze_imports=True,
            analyze_classes=True,
            analyze_functions=False,
            analyze_dependencies=False,
            analyze_ui=True,
            analyze_docs=not args.skip_docs,
            check_github_issues=not args.skip_github,
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
            
            # Analyze with Claude if enabled
            if analyzer.enable_claude:
                await analyzer._analyze_with_claude()
            
            # Generate recommendations
            await analyzer._generate_recommendations()
            
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
            
            # Generate documentation if requested
            if args.generate_docs:
                print("\n🔄 Generating improved documentation...")
                doc_results = await analyzer.generate_improved_documentation()
                print(f"📝 Generated {len(doc_results['generated_docs'])} documentation files")
            
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
    else:
        # Create analyzer instance for full analysis
        analyzer = ArchitectureAnalyzer(
            project_root=args.root,
            output_dir=args.output,
            enable_perplexity=not args.no_perplexity,
            enable_claude=not args.no_claude,
            analyze_imports=not args.skip_imports,
            analyze_classes=not args.skip_classes,
            analyze_functions=not args.skip_functions,
            analyze_dependencies=not args.skip_dependencies,
            analyze_ui=not args.skip_ui,
            analyze_docs=not args.skip_docs,
            check_github_issues=not args.skip_github,
        )
        
        # Run the analysis
        results = await analyzer.analyze()
        
        # Print summary
        if results["status"] == "success":
            print("\n✅ VOT1 Architecture Analysis Completed Successfully")
            print(f"📊 Analyzed {results['modules_count']} modules, {results['classes_count']} classes, and {results['functions_count']} functions")
            print(f"🔍 Identified {results['components_count']} major components and {results['integration_points_count']} integration points")
            print(f"💡 Generated {results['optimization_opportunities_count']} optimization opportunities and {results['recommendations_count']} recommendations")
            print(f"📂 Results saved to {results['output_dir']}")
            
            # Generate improved documentation if requested
            if args.generate_docs:
                print("\n🔄 Generating improved documentation based on analysis...")
                doc_results = await analyzer.generate_improved_documentation()
                print(f"📝 Generated {len(doc_results['generated_docs'])} documentation files")
        else:
            print(f"\n❌ VOT1 Architecture Analysis Failed: {results['error']}")
            print(f"📂 Partial results may have been saved to {results['output_dir']}")
        
        return results

if __name__ == "__main__":
    # Set up asyncio to run on Windows properly
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the main function
    asyncio.run(main())
