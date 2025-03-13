"""
VOT1 Development Assistant

This module provides a unified development assistant that integrates:
1. Claude 3.7 for advanced reasoning and code analysis
2. Perplexity for real-time web research
3. Persistent memory system
4. Codebase analysis
5. Script generation and deployment

The assistant can analyze code, research solutions, generate scripts,
and maintain a memory of previous interactions.
"""

import os
import sys
import json
import logging
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime
import ast
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dev_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import VOT1-specific modules
try:
    from ...memory import MemoryManager
    from ..api.mcp_handler import init_mcp_api
    from ..utils.mcp_tools import call_mcp_function
except ImportError as e:
    logger.warning(f"Could not import VOT1 modules: {e}")
    logger.warning("Some functionality may be limited")

class CodeAnalysis:
    """Code analysis utilities for the development assistant."""
    
    @staticmethod
    def extract_imports(file_path: str) -> List[str]:
        """Extract all imports from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        if module:
                            imports.append(f"{module}.{name.name}")
                        else:
                            imports.append(name.name)
                            
            return imports
        except Exception as e:
            logger.error(f"Error extracting imports from {file_path}: {e}")
            return []
    
    @staticmethod
    def extract_classes_and_functions(file_path: str) -> Dict[str, List[str]]:
        """Extract all class and function definitions from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    
            return {
                'classes': classes,
                'functions': functions
            }
        except Exception as e:
            logger.error(f"Error extracting classes and functions from {file_path}: {e}")
            return {'classes': [], 'functions': []}
    
    @staticmethod
    def analyze_dependencies(file_path: str) -> Dict[str, Any]:
        """Analyze dependencies and complexity of a Python file."""
        imports = CodeAnalysis.extract_imports(file_path)
        classes_and_functions = CodeAnalysis.extract_classes_and_functions(file_path)
        
        # Count lines of code
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                line_count = len(lines)
                blank_lines = sum(1 for line in lines if line.strip() == '')
                comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
                code_lines = line_count - blank_lines - comment_lines
        except Exception as e:
            logger.error(f"Error counting lines in {file_path}: {e}")
            line_count = blank_lines = comment_lines = code_lines = 0
        
        return {
            'file_path': file_path,
            'imports': imports,
            'classes': classes_and_functions['classes'],
            'functions': classes_and_functions['functions'],
            'total_lines': line_count,
            'blank_lines': blank_lines,
            'comment_lines': comment_lines,
            'code_lines': code_lines,
            'import_count': len(imports),
            'class_count': len(classes_and_functions['classes']),
            'function_count': len(classes_and_functions['functions']),
        }
    
    @staticmethod
    def scan_directory(directory_path: str, file_extension: str = '.py') -> List[Dict[str, Any]]:
        """Scan a directory for files of a specific extension and analyze them."""
        results = []
        
        try:
            for root, _, files in os.walk(directory_path):
                for file in files:
                    if file.endswith(file_extension):
                        file_path = os.path.join(root, file)
                        analysis = CodeAnalysis.analyze_dependencies(file_path)
                        results.append(analysis)
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {e}")
        
        return results

class PerplexityResearcher:
    """Integration with Perplexity AI for real-time research."""
    
    def __init__(self, perplexity_connected: bool = False):
        self.connected = perplexity_connected
        
    def connect(self) -> bool:
        """Connect to Perplexity AI service."""
        try:
            from ..utils.mcp_tools import call_mcp_function
            
            # Check if already connected
            response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_CHECK_ACTIVE_CONNECTION", {
                "params": {"tool": "PERPLEXITYAI"}
            })
            
            if response.get('data', {}).get('active_connection', False):
                self.connected = True
                logger.info("Already connected to Perplexity AI")
                return True
            
            # Initialize connection
            response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_INITIATE_CONNECTION", {
                "params": {
                    "tool": "PERPLEXITYAI",
                    "parameters": {}
                }
            })
            
            self.connected = response.get('successful', False)
            if self.connected:
                logger.info("Successfully connected to Perplexity AI")
            else:
                logger.error(f"Failed to connect to Perplexity AI: {response.get('error')}")
            
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to Perplexity AI: {e}")
            self.connected = False
            return False
    
    def research(self, query: str, depth: str = 'deep') -> Dict[str, Any]:
        """Perform research using Perplexity AI."""
        if not self.connected:
            success = self.connect()
            if not success:
                return {"error": "Not connected to Perplexity AI", "content": ""}
        
        try:
            from ..utils.mcp_tools import call_mcp_function
            
            # Define system prompt based on depth
            system_prompts = {
                'basic': "You are a research assistant. Provide a concise answer with key information.",
                'medium': "You are a research assistant. Provide a balanced answer with relevant details and context.",
                'deep': "You are a research assistant. Provide a comprehensive analysis with detailed information, examples, recent developments, and nuanced perspectives."
            }
            
            system_prompt = system_prompts.get(depth, system_prompts['medium'])
            
            response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
                "params": {
                    "model": "pplx-70b-online",
                    "systemContent": system_prompt,
                    "userContent": query,
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "return_citations": True
                }
            })
            
            # Extract content from response
            content_text = ""
            citations = []
            
            response_data = response.get('content', [])
            for item in response_data:
                if item.get('type') == 'text':
                    content_text += item.get('text', '')
            
            # Try to parse JSON content
            try:
                parsed_content = json.loads(content_text)
                content = parsed_content.get('completion', '')
                citations = parsed_content.get('citations', [])
            except json.JSONDecodeError:
                # If not valid JSON, use the raw text
                content = content_text
            
            return {
                "content": content,
                "citations": citations,
                "timestamp": datetime.now().isoformat(),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error researching with Perplexity AI: {e}")
            return {
                "error": str(e),
                "content": "",
                "citations": [],
                "timestamp": datetime.now().isoformat(),
                "query": query
            }

class MemorySubsystem:
    """Memory management for persistent storage of development insights."""
    
    def __init__(self, memory_path: Optional[str] = None):
        self.memory_path = memory_path or os.environ.get('VOT1_MEMORY_PATH', 'memory')
        self.memory_manager = None
        
        # Initialize memory manager
        try:
            if not os.path.exists(self.memory_path):
                os.makedirs(self.memory_path, exist_ok=True)
                
            # Try to import and initialize MemoryManager
            try:
                from ...memory import MemoryManager
                self.memory_manager = MemoryManager(memory_path=self.memory_path)
                logger.info(f"Memory manager initialized at {self.memory_path}")
            except ImportError:
                logger.warning("Could not import MemoryManager. Using basic memory storage.")
                self.memory_manager = None
        except Exception as e:
            logger.error(f"Error initializing memory subsystem: {e}")
    
    def store(self, category: str, key: str, data: Any) -> bool:
        """Store data in memory."""
        if self.memory_manager:
            try:
                # Use MemoryManager if available
                self.memory_manager.store(category, key, data)
                return True
            except Exception as e:
                logger.error(f"Error storing in memory manager: {e}")
                return self._store_basic(category, key, data)
        else:
            return self._store_basic(category, key, data)
    
    def _store_basic(self, category: str, key: str, data: Any) -> bool:
        """Basic storage implementation when MemoryManager is unavailable."""
        try:
            # Create category directory if it doesn't exist
            category_dir = os.path.join(self.memory_path, category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Store data as JSON
            file_path = os.path.join(category_dir, f"{key}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error in basic memory storage: {e}")
            return False
    
    def retrieve(self, category: str, key: str) -> Optional[Any]:
        """Retrieve data from memory."""
        if self.memory_manager:
            try:
                # Use MemoryManager if available
                return self.memory_manager.retrieve(category, key)
            except Exception as e:
                logger.error(f"Error retrieving from memory manager: {e}")
                return self._retrieve_basic(category, key)
        else:
            return self._retrieve_basic(category, key)
    
    def _retrieve_basic(self, category: str, key: str) -> Optional[Any]:
        """Basic retrieval implementation when MemoryManager is unavailable."""
        try:
            file_path = os.path.join(self.memory_path, category, f"{key}.json")
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data')
        except Exception as e:
            logger.error(f"Error in basic memory retrieval: {e}")
            return None
    
    def list_categories(self) -> List[str]:
        """List all memory categories."""
        if self.memory_manager:
            try:
                return self.memory_manager.list_categories()
            except Exception as e:
                logger.error(f"Error listing categories from memory manager: {e}")
                return self._list_categories_basic()
        else:
            return self._list_categories_basic()
    
    def _list_categories_basic(self) -> List[str]:
        """Basic implementation to list categories when MemoryManager is unavailable."""
        try:
            if not os.path.exists(self.memory_path):
                return []
            
            return [d for d in os.listdir(self.memory_path) 
                   if os.path.isdir(os.path.join(self.memory_path, d))]
        except Exception as e:
            logger.error(f"Error in basic category listing: {e}")
            return []
    
    def list_keys(self, category: str) -> List[str]:
        """List all keys in a category."""
        if self.memory_manager:
            try:
                return self.memory_manager.list_keys(category)
            except Exception as e:
                logger.error(f"Error listing keys from memory manager: {e}")
                return self._list_keys_basic(category)
        else:
            return self._list_keys_basic(category)
    
    def _list_keys_basic(self, category: str) -> List[str]:
        """Basic implementation to list keys when MemoryManager is unavailable."""
        try:
            category_dir = os.path.join(self.memory_path, category)
            if not os.path.exists(category_dir):
                return []
            
            return [f.replace('.json', '') for f in os.listdir(category_dir) 
                   if f.endswith('.json') and os.path.isfile(os.path.join(category_dir, f))]
        except Exception as e:
            logger.error(f"Error in basic key listing: {e}")
            return []

class ScriptGenerator:
    """Generate scripts and deployment code."""
    
    def __init__(self, memory_subsystem: MemorySubsystem, perplexity_researcher: PerplexityResearcher):
        self.memory = memory_subsystem
        self.researcher = perplexity_researcher
    
    def generate_script(self, script_description: str, script_type: str = 'python', 
                        template: Optional[str] = None) -> Dict[str, Any]:
        """Generate a script based on description and optional template."""
        # Research best practices if needed
        research_query = f"Best practices for {script_type} script that {script_description}"
        research_result = self.researcher.research(research_query, depth='medium')
        
        # Prepare prompt
        prompt = f"""
        Generate a {script_type} script that {script_description}.
        The script should follow best practices and be well-documented.
        """
        
        if template:
            prompt += f"\nIt should follow this template or structure:\n{template}"
        
        # Add research insights
        if research_result.get('content'):
            prompt += f"\n\nIncorporate these best practices:\n{research_result.get('content')}"
        
        # For now, we'll use Claude directly via the MCP interface
        try:
            from ..utils.mcp_tools import call_mcp_function
            
            response = call_mcp_function("mcp_CLAUDE_CLAUDE_MODEL_COMPLETIONS", {
                "params": {
                    "model": "claude-3-7-sonnet-20240620",
                    "system": "You are an expert programmer. Your task is to generate high-quality, production-ready code based on the user's request. Include thorough documentation and error handling. Focus on readability, efficiency, and maintainability.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 4000
                }
            })
            
            # Extract script content from response
            content = ""
            response_data = response.get('content', [])
            for item in response_data:
                if item.get('type') == 'text':
                    content += item.get('text', '')
            
            # Extract code from markdown
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n([\s\S]*?)\n```', content)
            script_content = code_blocks[0] if code_blocks else content
            
            # Store the generated script in memory
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            script_key = f"{script_type}_script_{timestamp}"
            self.memory.store('generated_scripts', script_key, {
                'description': script_description,
                'content': script_content,
                'type': script_type,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                'script': script_content,
                'key': script_key,
                'description': script_description,
                'type': script_type
            }
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return {
                'error': str(e),
                'description': script_description,
                'type': script_type
            }
    
    def save_script_to_file(self, script_key: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Save a generated script to a file."""
        # Retrieve script from memory
        script_data = self.memory.retrieve('generated_scripts', script_key)
        
        if not script_data:
            return {
                'error': f"Script with key {script_key} not found",
                'success': False
            }
        
        script_content = script_data.get('content', '')
        script_type = script_data.get('type', 'python')
        
        # Determine file extension
        extensions = {
            'python': '.py',
            'bash': '.sh',
            'javascript': '.js',
            'typescript': '.ts',
            'html': '.html',
            'css': '.css',
            'sql': '.sql'
        }
        extension = extensions.get(script_type, '.txt')
        
        # Generate file path if not provided
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = f"generated_script_{timestamp}{extension}"
            file_path = os.path.join(os.getcwd(), file_name)
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Save the script
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Make executable if it's a bash script
            if script_type == 'bash':
                os.chmod(file_path, 0o755)
            
            return {
                'success': True,
                'file_path': file_path,
                'script_key': script_key
            }
        except Exception as e:
            logger.error(f"Error saving script to file: {e}")
            return {
                'error': str(e),
                'success': False,
                'script_key': script_key
            }

class DevelopmentAssistant:
    """Main development assistant that integrates all features."""
    
    def __init__(self, project_root: Optional[str] = None, memory_path: Optional[str] = None):
        self.project_root = project_root or os.getcwd()
        self.memory = MemorySubsystem(memory_path)
        self.researcher = PerplexityResearcher()
        self.script_generator = ScriptGenerator(self.memory, self.researcher)
        
        # Try to connect to Perplexity
        self.researcher.connect()
        
        logger.info(f"Development Assistant initialized with project root: {self.project_root}")
    
    def analyze_codebase(self, directory: Optional[str] = None, file_extension: str = '.py') -> Dict[str, Any]:
        """Analyze the structure and dependencies of the codebase."""
        directory = directory or self.project_root
        
        # Scan directory for files
        analysis_results = CodeAnalysis.scan_directory(directory, file_extension)
        
        # Aggregate statistics
        total_files = len(analysis_results)
        total_lines = sum(result['total_lines'] for result in analysis_results)
        total_code_lines = sum(result['code_lines'] for result in analysis_results)
        total_comment_lines = sum(result['comment_lines'] for result in analysis_results)
        total_blank_lines = sum(result['blank_lines'] for result in analysis_results)
        total_classes = sum(result['class_count'] for result in analysis_results)
        total_functions = sum(result['function_count'] for result in analysis_results)
        
        # Collect all unique imports
        all_imports = set()
        for result in analysis_results:
            all_imports.update(result['imports'])
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'directory': directory,
            'file_extension': file_extension,
            'total_files': total_files,
            'total_lines': total_lines,
            'total_code_lines': total_code_lines,
            'total_comment_lines': total_comment_lines,
            'total_blank_lines': total_blank_lines,
            'total_classes': total_classes,
            'total_functions': total_functions,
            'unique_imports': list(all_imports),
            'unique_import_count': len(all_imports),
            'file_details': analysis_results
        }
        
        # Store the analysis in memory
        self.memory.store('codebase_analysis', 
                         f'analysis_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                         summary)
        
        return summary
    
    def research_topic(self, query: str, depth: str = 'deep') -> Dict[str, Any]:
        """Research a topic using Perplexity AI."""
        research_result = self.researcher.research(query, depth)
        
        # Store the research result in memory
        if not research_result.get('error'):
            key = f"research_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.memory.store('research_results', key, research_result)
        
        return research_result
    
    def generate_script(self, description: str, script_type: str = 'python', 
                        template: Optional[str] = None) -> Dict[str, Any]:
        """Generate a script based on description."""
        return self.script_generator.generate_script(description, script_type, template)
    
    def save_script(self, script_key: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Save a generated script to a file."""
        return self.script_generator.save_script_to_file(script_key, file_path)
    
    def troubleshoot_code(self, code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Troubleshoot code issues using Claude and Perplexity research."""
        # Research common issues if error message is provided
        research_result = {}
        if error_message:
            research_query = f"Troubleshooting {error_message} in Python"
            research_result = self.researcher.research(research_query, depth='medium')
        
        # Prepare prompt for Claude
        prompt = f"""I need help troubleshooting this code:
        
        ```
        {code}
        ```
        """
        
        if error_message:
            prompt += f"\n\nI'm getting this error:\n{error_message}"
            
        if research_result.get('content'):
            prompt += f"\n\nHere is some research on similar issues:\n{research_result.get('content')}"
        
        # Use Claude for troubleshooting
        try:
            from ..utils.mcp_tools import call_mcp_function
            
            response = call_mcp_function("mcp_CLAUDE_CLAUDE_MODEL_COMPLETIONS", {
                "params": {
                    "model": "claude-3-7-sonnet-20240620",
                    "system": "You are an expert programmer focused on troubleshooting and debugging code. Analyze the provided code and error messages carefully, identify potential issues, and provide clear explanations and solutions.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                }
            })
            
            # Extract content from response
            content = ""
            response_data = response.get('content', [])
            for item in response_data:
                if item.get('type') == 'text':
                    content += item.get('text', '')
            
            troubleshooting_result = {
                'analysis': content,
                'error_message': error_message,
                'research': research_result.get('content'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store the troubleshooting result in memory
            key = f"troubleshooting_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.memory.store('troubleshooting', key, troubleshooting_result)
            
            return troubleshooting_result
            
        except Exception as e:
            logger.error(f"Error troubleshooting code: {e}")
            return {
                'error': str(e),
                'error_message': error_message
            }
    
    def analyze_project_architecture(self) -> Dict[str, Any]:
        """Analyze the overall project architecture and provide recommendations."""
        # Start by analyzing the codebase
        codebase_analysis = self.analyze_codebase()
        
        # Research best practices for similar project structures
        if codebase_analysis.get('unique_imports'):
            main_frameworks = []
            for imp in codebase_analysis.get('unique_imports', []):
                if any(framework in imp for framework in ['flask', 'django', 'fastapi', 'tornado', 'pyramid']):
                    main_frameworks.append('web framework')
                elif any(framework in imp for framework in ['tensorflow', 'pytorch', 'keras', 'sklearn']):
                    main_frameworks.append('machine learning')
                elif any(framework in imp for framework in ['numpy', 'pandas', 'matplotlib', 'scipy']):
                    main_frameworks.append('data science')
                elif any(framework in imp for framework in ['pydantic', 'typing']):
                    main_frameworks.append('type checking')
            
            if main_frameworks:
                research_query = f"Best practices for Python project architecture with {', '.join(main_frameworks)}"
                research_result = self.researcher.research(research_query, depth='deep')
            else:
                research_query = "Modern Python project architecture best practices"
                research_result = self.researcher.research(research_query, depth='deep')
        else:
            research_query = "Modern Python project architecture best practices"
            research_result = self.researcher.research(research_query, depth='deep')
        
        # Generate architecture analysis using Claude
        try:
            from ..utils.mcp_tools import call_mcp_function
            
            # Convert codebase analysis to a summarized format
            codebase_summary = {
                'total_files': codebase_analysis.get('total_files', 0),
                'total_lines': codebase_analysis.get('total_lines', 0),
                'total_classes': codebase_analysis.get('total_classes', 0),
                'total_functions': codebase_analysis.get('total_functions', 0),
                'unique_imports': codebase_analysis.get('unique_imports', [])
            }
            
            prompt = f"""
            Analyze this project architecture and provide recommendations for improvement:
            
            Project Analysis:
            {json.dumps(codebase_summary, indent=2)}
            
            Research on Best Practices:
            {research_result.get('content', '')}
            
            Please provide:
            1. Overall architecture assessment
            2. Identified patterns and anti-patterns
            3. Specific improvement recommendations
            4. Suggestions for better organization
            5. Potential technical debt
            """
            
            response = call_mcp_function("mcp_CLAUDE_CLAUDE_MODEL_COMPLETIONS", {
                "params": {
                    "model": "claude-3-7-sonnet-20240620",
                    "system": "You are an expert software architect with deep knowledge of Python project structures, design patterns, and best practices. Analyze the provided project information and provide actionable recommendations for improvement.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                }
            })
            
            # Extract content from response
            content = ""
            response_data = response.get('content', [])
            for item in response_data:
                if item.get('type') == 'text':
                    content += item.get('text', '')
            
            architecture_analysis = {
                'timestamp': datetime.now().isoformat(),
                'codebase_summary': codebase_summary,
                'research': research_result.get('content'),
                'analysis': content
            }
            
            # Store the architecture analysis in memory
            key = f"architecture_analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.memory.store('architecture_analysis', key, architecture_analysis)
            
            return architecture_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing project architecture: {e}")
            return {
                'error': str(e),
                'codebase_summary': codebase_analysis
            }


def init_dev_assistant(project_root: Optional[str] = None, memory_path: Optional[str] = None) -> DevelopmentAssistant:
    """Initialize the development assistant."""
    return DevelopmentAssistant(project_root, memory_path) 