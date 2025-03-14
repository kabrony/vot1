"""
Development Assistant Module

This module provides a comprehensive development assistant with code analysis,
research capabilities, memory management, and script generation.
"""

import os
import re
import json
import logging
import traceback
import time
from typing import Dict, Any, List, Optional, Union, Callable
from collections import defaultdict
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import enhanced Perplexity client
try:
    from .utils.enhanced_perplexity import EnhancedPerplexityClient, PerplexityError
    ENHANCED_PERPLEXITY_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced Perplexity client not available, falling back to standard implementation")
    ENHANCED_PERPLEXITY_AVAILABLE = False

# Memory Manager import
try:
    from ..memory import MemoryManager
    MEMORY_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("Memory Manager not available")
    MEMORY_MANAGER_AVAILABLE = False

class DevelopmentAssistant:
    """
    A comprehensive development assistant that provides code analysis, research,
    memory management, and script generation capabilities.
    """
    
    def __init__(
        self,
        memory_path: Optional[str] = None,
        project_root: Optional[str] = None,
        perplexity_api_key: Optional[str] = None,
        redis_url: Optional[str] = None,
        max_thinking_tokens: int = 20000,
        smart_token_management: bool = True,
        **kwargs
    ):
        """
        Initialize the Development Assistant with specified configurations.
        
        Args:
            memory_path (str, optional): Path to store memory data. Defaults to None.
            project_root (str, optional): Root directory of the project. Defaults to None.
            perplexity_api_key (str, optional): API key for Perplexity AI. Defaults to None.
            redis_url (str, optional): URL for Redis cache. Defaults to None.
            max_thinking_tokens (int, optional): Maximum tokens for thinking. Defaults to 20000.
            smart_token_management (bool, optional): Enable intelligent token allocation. Defaults to True.
            **kwargs: Additional keyword arguments.
        """
        self.project_root = project_root or os.getcwd()
        self.max_thinking_tokens = max_thinking_tokens
        self.smart_token_management = smart_token_management
        
        # For tracking token usage
        self.token_usage = {
            "thinking": 0,
            "research": 0,
            "total": 0
        }
        
        # Initialize memory manager
        if MEMORY_MANAGER_AVAILABLE:
            self.memory_manager = MemoryManager(base_path=memory_path)
            logger.info(f"Memory manager initialized with base path: {memory_path}")
        else:
            self.memory_manager = None
            logger.warning("Memory manager not available")
        
        # Initialize Perplexity client
        self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.redis_url = redis_url
        
        if ENHANCED_PERPLEXITY_AVAILABLE and self.perplexity_api_key:
            try:
                self.perplexity_client = EnhancedPerplexityClient(
                    api_key=self.perplexity_api_key,
                    redis_url=self.redis_url
                )
                logger.info("Enhanced Perplexity client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Enhanced Perplexity client: {e}")
                self.perplexity_client = None
        else:
            self.perplexity_client = None
            if not self.perplexity_api_key:
                logger.warning("Perplexity API key not provided")
            if not ENHANCED_PERPLEXITY_AVAILABLE:
                logger.warning("Enhanced Perplexity client not available")
        
        # Initialize analysis cache
        self.analysis_cache = {}
        
        logger.info("Development Assistant initialized")
    
    def is_initialized(self) -> bool:
        """
        Check if the Development Assistant is properly initialized.
        
        Returns:
            bool: True if initialized, False otherwise
        """
        return (
            self.project_root is not None and
            (
                self.perplexity_client is not None or 
                self.perplexity_api_key is not None
            )
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration of the Development Assistant.
        
        Returns:
            Dict containing the configuration details
        """
        return {
            "initialized": self.is_initialized(),
            "project_root": self.project_root,
            "memory_available": self.memory_manager is not None,
            "perplexity_available": self.perplexity_client is not None,
            "max_thinking_tokens": self.max_thinking_tokens,
            "smart_token_management": self.smart_token_management,
            "token_usage": self.token_usage
        }
    
    def analyze_codebase(
        self, 
        path: Optional[str] = None, 
        file_extension: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the codebase structure and dependencies.
        
        Args:
            path: Path to analyze, defaults to project_root
            file_extension: Filter by file extension (e.g., '.py', '.js')
        
        Returns:
            Dict containing analysis results
        """
        try:
            start_time = time.time()
            path = path or self.project_root
            
            # Cache key based on path and file extension
            cache_key = f"{path}:{file_extension or 'all'}"
            
            # Check cache
            if cache_key in self.analysis_cache:
                logger.info(f"Using cached analysis for {cache_key}")
                return self.analysis_cache[cache_key]
            
            # Validate path exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}"
                }
            
            # List of file extensions to ignore
            ignore_extensions = {
                '.git', '.idea', '.vscode', 'node_modules', '__pycache__',
                '.pyc', '.pyo', '.pyd', '.so', '.dll', '.class'
            }
            
            # Pattern for file extension filter
            pattern = None
            if file_extension:
                if not file_extension.startswith('.'):
                    file_extension = f".{file_extension}"
                pattern = re.compile(f".*\\{file_extension}$")
            
            # Collect files and directories
            file_count = 0
            dir_count = 0
            file_sizes = []
            file_extensions = defaultdict(int)
            largest_files = []
            
            # Walk the directory
            for root, dirs, files in os.walk(path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_extensions]
                
                dir_count += 1
                
                for file in files:
                    # Skip ignored files
                    if any(file.endswith(ext) for ext in ignore_extensions):
                        continue
                    
                    # Apply file extension filter if specified
                    if pattern and not pattern.match(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    file_count += 1
                    
                    # Get file extension
                    _, ext = os.path.splitext(file)
                    if ext:
                        file_extensions[ext] += 1
                    
                    # Get file size
                    try:
                        size = os.path.getsize(file_path)
                        file_sizes.append(size)
                        
                        # Track largest files
                        largest_files.append((file_path, size))
                        largest_files = sorted(largest_files, key=lambda x: x[1], reverse=True)[:10]
                    except:
                        pass
            
            # Calculate statistics
            total_size = sum(file_sizes)
            avg_size = total_size / max(file_count, 1)
            
            # Format file paths relative to project root
            largest_files = [
                {"path": os.path.relpath(path, self.project_root), "size": size, "size_formatted": self._format_size(size)}
                for path, size in largest_files
            ]
            
            # Format extensions
            extensions = [
                {"extension": ext, "count": count}
                for ext, count in sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Prepare result
            result = {
                "success": True,
                "path": path,
                "file_extension_filter": file_extension,
                "file_count": file_count,
                "directory_count": dir_count,
                "total_size": total_size,
                "total_size_formatted": self._format_size(total_size),
                "average_file_size": avg_size,
                "average_file_size_formatted": self._format_size(avg_size),
                "file_extensions": extensions,
                "largest_files": largest_files,
                "analysis_time": time.time() - start_time
            }
            
            # Cache the result
            self.analysis_cache[cache_key] = result
            
            return result
        
        except Exception as e:
            logger.error(f"Error analyzing codebase: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_size(self, size_in_bytes: int) -> str:
        """
        Format byte size to human-readable format.
        
        Args:
            size_in_bytes: Size in bytes
        
        Returns:
            Formatted size string (e.g., '2.5 MB')
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0 or unit == 'TB':
                break
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} {unit}"
    
    def allocate_tokens(self, task_type: str, complexity: str = "medium") -> int:
        """
        Intelligently allocate tokens based on task type and complexity.
        
        Args:
            task_type: Type of task (research, analysis, generation, etc.)
            complexity: Task complexity (low, medium, high)
            
        Returns:
            Number of tokens allocated for the task
        """
        if not self.smart_token_management:
            return self.max_thinking_tokens
            
        # Base allocations for different task types
        base_allocations = {
            "research": {
                "low": 3000,
                "medium": 6000,
                "high": 10000
            },
            "analysis": {
                "low": 5000,
                "medium": 8000,
                "high": 12000
            },
            "generation": {
                "low": 4000,
                "medium": 7000,
                "high": 10000
            },
            "troubleshooting": {
                "low": 5000,
                "medium": 8000,
                "high": 12000
            },
            "default": {
                "low": 4000,
                "medium": 7000,
                "high": 10000
            }
        }
        
        # Get allocation for task type and complexity
        task_allocations = base_allocations.get(task_type, base_allocations["default"])
        allocation = task_allocations.get(complexity, task_allocations["medium"])
        
        # Adjust allocation based on current token usage and remaining tokens
        remaining_tokens = self.max_thinking_tokens - self.token_usage["total"]
        if remaining_tokens < allocation:
            # If not enough tokens remaining, use what's available or reset usage
            if remaining_tokens < 1000:
                # Reset token usage if too few tokens remaining
                self.token_usage = {
                    "thinking": 0,
                    "research": 0,
                    "total": 0
                }
                logger.info(f"Token usage reset due to low remaining tokens.")
                return min(allocation, self.max_thinking_tokens)
            else:
                logger.info(f"Token allocation adjusted: requested {allocation}, available {remaining_tokens}")
                return remaining_tokens
        
        return allocation
    
    def research(
        self, 
        query: str, 
        depth: str = "standard",
        model: str = "sonar-reasoning-pro",
        system_prompt: Optional[str] = None,
        skip_cache: bool = False,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Perform research using Perplexity AI.
        
        Args:
            query: Research query
            depth: Research depth ('quick', 'standard', 'deep')
            model: Model to use for research
            system_prompt: Custom system prompt
            skip_cache: Whether to skip cache and force a new query
            complexity: Task complexity ('low', 'medium', 'high')
        
        Returns:
            Dict containing research results
        """
        try:
            start_time = time.time()
            
            # Allocate tokens based on complexity if smart token management is enabled
            if self.smart_token_management:
                allocated_tokens = self.allocate_tokens("research", complexity)
                logger.info(f"Allocated {allocated_tokens} tokens for research with {complexity} complexity")
            else:
                allocated_tokens = None  # Use depth-based defaults
            
            # Validate depth option
            depth_options = {
                "quick": {"max_tokens": 2000, "temperature": 0.7},
                "standard": {"max_tokens": 4000, "temperature": 0.7},
                "deep": {"max_tokens": 8000, "temperature": 0.5}
            }
            
            if depth not in depth_options:
                return {
                    "success": False,
                    "error": f"Invalid depth option: {depth}. Choose from {list(depth_options.keys())}"
                }
            
            # Check if Perplexity client is available
            if not self.perplexity_client and not ENHANCED_PERPLEXITY_AVAILABLE:
                return {
                    "success": False,
                    "error": "Perplexity client not available"
                }
            
            # Try to initialize client if not already initialized
            if not self.perplexity_client and self.perplexity_api_key:
                try:
                    self.perplexity_client = EnhancedPerplexityClient(
                        api_key=self.perplexity_api_key,
                        redis_url=self.redis_url
                    )
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to initialize Perplexity client: {e}"
                    }
            
            # Set depth options
            options = depth_options[depth]
            
            # Override token limit if smart allocation is used
            if allocated_tokens:
                options["max_tokens"] = min(allocated_tokens, options["max_tokens"])
            
            # Default system prompt based on depth
            if not system_prompt:
                if depth == "quick":
                    system_prompt = (
                        "You are a research assistant. Provide a concise summary of the key information "
                        "related to the query, focusing on the most important points. Aim for brevity "
                        "and clarity."
                    )
                elif depth == "standard":
                    system_prompt = (
                        "You are a research assistant. Provide detailed information on the query, "
                        "including facts, recent developments, and multiple perspectives when appropriate. "
                        "Balance depth with readability."
                    )
                else:  # deep
                    system_prompt = (
                        "You are a research assistant conducting comprehensive research. Provide an in-depth "
                        "analysis of the query, including historical context, technical details, competing "
                        "viewpoints, and recent developments. Include specific examples, statistics, and "
                        "citations where relevant. Be thorough and detailed."
                    )
            
            # Perform the research
            response = self.perplexity_client.search(
                query=query,
                model=model,
                system_prompt=system_prompt,
                temperature=options.get("temperature", 0.7),
                max_tokens=options.get("max_tokens", 4000),
                return_citations=True,
                skip_cache=skip_cache
            )
            
            # Extract and format results
            result = {
                "success": True,
                "query": query,
                "depth": depth,
                "model": model,
                "content": response.get("content", ""),
                "citations": response.get("citations", []),
                "from_cache": response.get("from_cache", False),
                "timestamp": datetime.now().isoformat(),
                "processing_time": time.time() - start_time
            }
            
            # Update token usage if smart token management is enabled
            if self.smart_token_management:
                # Estimate tokens used (roughly 4 characters per token)
                content = result.get("content", "")
                tokens_used = len(content) // 4
                self.token_usage["research"] += tokens_used
                self.token_usage["total"] += tokens_used
                
                result["tokens_used"] = tokens_used
                result["token_allocation"] = options["max_tokens"]
                logger.info(f"Research used approximately {tokens_used} tokens (allocated: {options['max_tokens']})")
            
            # Store in memory if available
            if self.memory_manager:
                memory_key = f"research_{int(time.time())}"
                self.memory_manager.save("research", memory_key, result)
                result["memory_key"] = memory_key
            
            return result
        
        except PerplexityError as e:
            logger.error(f"Perplexity error: {e}")
            return {
                "success": False,
                "error": f"Perplexity error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error performing research: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_script(
        self, 
        description: str, 
        script_type: Optional[str] = None,
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a script, document, or test based on description.
        
        Args:
            description: Description of what to generate
            script_type: Type of script to generate (e.g., 'python', 'javascript', 'markdown')
            template: Optional template to use for generation
        
        Returns:
            Dict containing the generated script
        """
        try:
            start_time = time.time()
            
            # Default script type if not specified
            if not script_type:
                # Try to infer from description
                if any(kw in description.lower() for kw in ["python", "py", ".py"]):
                    script_type = "python"
                elif any(kw in description.lower() for kw in ["javascript", "js", ".js"]):
                    script_type = "javascript"
                elif any(kw in description.lower() for kw in ["markdown", "md", ".md"]):
                    script_type = "markdown"
                else:
                    # Default to Python
                    script_type = "python"
            
            # Create system prompt based on script type
            if script_type == "python":
                system_prompt = (
                    "You are an expert Python developer. Generate well-documented Python code "
                    "based on the provided description. Include docstrings, comments, and follow "
                    "PEP 8 style guidelines. The code should be complete, robust, and ready to run."
                )
            elif script_type == "javascript":
                system_prompt = (
                    "You are an expert JavaScript developer. Generate well-documented JavaScript code "
                    "based on the provided description. Include comments, use modern ES6+ features, "
                    "and follow standard style guidelines. The code should be complete, robust, and ready to run."
                )
            elif script_type == "markdown":
                system_prompt = (
                    "You are an expert technical writer. Generate well-structured Markdown documentation "
                    "based on the provided description. Include clear headers, proper formatting, and "
                    "complete information. The document should be comprehensive and professional."
                )
            else:
                system_prompt = (
                    f"You are an expert in {script_type}. Generate well-documented code or content "
                    f"based on the provided description. Follow best practices for {script_type}. "
                    f"The output should be complete, robust, and ready to use."
                )
            
            # Add template information if provided
            if template:
                system_prompt += f"\n\nUse the following template as a starting point:\n{template}"
            
            # Construct the full query
            query = f"Generate {script_type} code for: {description}"
            
            # Use research function for generation
            result = self.research(
                query=query,
                depth="standard",
                system_prompt=system_prompt
            )
            
            if not result.get("success", False):
                return result
            
            # Process the generated content
            content = result.get("content", "")
            
            # Extract code blocks if present
            code_block_pattern = r"```(?:\w+)?\n([\s\S]+?)\n```"
            code_blocks = re.findall(code_block_pattern, content)
            
            if code_blocks:
                # Combine all code blocks
                code = "\n\n".join(code_blocks)
            else:
                # Use the full content if no code blocks found
                code = content
            
            # Store in memory if available
            memory_key = None
            if self.memory_manager:
                memory_key = f"script_{script_type}_{int(time.time())}"
                self.memory_manager.save("scripts", memory_key, {
                    "description": description,
                    "script_type": script_type,
                    "code": code,
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "description": description,
                "script_type": script_type,
                "code": code,
                "memory_key": memory_key,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def troubleshoot(
        self, 
        code: str, 
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Troubleshoot code issues.
        
        Args:
            code: The code to troubleshoot
            error_message: Optional error message to help debugging
        
        Returns:
            Dict containing troubleshooting results
        """
        try:
            start_time = time.time()
            
            # Create system prompt for troubleshooting
            system_prompt = (
                "You are an expert software engineer specialized in debugging. "
                "Analyze the provided code and identify potential issues. "
                "Explain the problems in detail and provide specific fixes. "
                "Your response should follow this format:\n"
                "1. Problem Summary: Brief overview of the main issues\n"
                "2. Detailed Analysis: Line-by-line analysis of problematic code\n"
                "3. Recommended Fixes: Specific code changes to resolve the issues\n"
                "4. Fixed Code: Complete corrected version of the code\n"
            )
            
            # Construct the query based on whether an error message is provided
            if error_message:
                query = f"Debug the following code that produces this error: {error_message}\n\nCode:\n{code}"
                system_prompt += f"\nThe code is generating the following error, use this to guide your analysis:\n{error_message}"
            else:
                query = f"Debug the following code for potential issues:\n{code}"
            
            # Use research function for troubleshooting
            result = self.research(
                query=query,
                depth="standard",
                system_prompt=system_prompt
            )
            
            if not result.get("success", False):
                return result
            
            # Process the response
            troubleshooting_result = {
                "success": True,
                "analysis": result.get("content", ""),
                "timestamp": datetime.now().isoformat(),
                "processing_time": time.time() - start_time
            }
            
            # Extract fixed code if present
            code_block_pattern = r"```(?:\w+)?\n([\s\S]+?)\n```"
            code_blocks = re.findall(code_block_pattern, result.get("content", ""))
            
            if code_blocks:
                # Use the last code block as the fixed code
                troubleshooting_result["fixed_code"] = code_blocks[-1]
            
            # Store in memory if available
            if self.memory_manager:
                memory_key = f"troubleshoot_{int(time.time())}"
                self.memory_manager.save("troubleshooting", memory_key, troubleshooting_result)
                troubleshooting_result["memory_key"] = memory_key
            
            return troubleshooting_result
            
        except Exception as e:
            logger.error(f"Error troubleshooting code: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_architecture(self, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze the project architecture and provide recommendations.
        
        Args:
            path: Path to analyze, defaults to project_root
        
        Returns:
            Dict containing architecture analysis
        """
        try:
            start_time = time.time()
            path = path or self.project_root
            
            # First perform codebase analysis to get statistics
            analysis = self.analyze_codebase(path)
            
            if not analysis.get("success", False):
                return analysis
            
            # Create system prompt for architecture analysis
            system_prompt = (
                "You are an expert software architect specializing in analyzing codebases. "
                "Based on the provided codebase analysis, identify the architectural patterns, "
                "evaluate the structure, and provide recommendations for improvement. "
                "Your response should include:\n"
                "1. Architecture Overview: Identification of the likely architecture pattern(s)\n"
                "2. Structure Evaluation: Assessment of the codebase organization\n"
                "3. Key Metrics Analysis: Interpretation of the provided metrics\n"
                "4. Strengths: What aspects of the architecture appear well-designed\n"
                "5. Improvement Opportunities: Specific recommendations for architectural enhancement\n"
                "6. Refactoring Suggestions: Priority areas that would benefit from restructuring"
            )
            
            # Construct the query with codebase analysis
            query = f"Analyze the architecture of a codebase with the following characteristics:\n{json.dumps(analysis, indent=2)}"
            
            # Use research function for analysis
            result = self.research(
                query=query,
                depth="deep",
                system_prompt=system_prompt
            )
            
            if not result.get("success", False):
                return result
            
            # Combine results
            architecture_analysis = {
                "success": True,
                "codebase_analysis": analysis,
                "architecture_evaluation": result.get("content", ""),
                "timestamp": datetime.now().isoformat(),
                "processing_time": time.time() - start_time
            }
            
            # Store in memory if available
            if self.memory_manager:
                memory_key = f"architecture_{int(time.time())}"
                self.memory_manager.save("architecture", memory_key, architecture_analysis)
                architecture_analysis["memory_key"] = memory_key
            
            return architecture_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing architecture: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_memory(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        List memory categories or keys within a category.
        
        Args:
            category: Optional category to list keys for
        
        Returns:
            Dict containing memory listing
        """
        try:
            # Check if memory manager is available
            if not self.memory_manager:
                return {
                    "success": False,
                    "error": "Memory manager not available"
                }
            
            if category:
                # List keys within a category
                keys = self.memory_manager.list_keys(category)
                return {
                    "success": True,
                    "category": category,
                    "keys": keys
                }
            else:
                # List categories
                categories = self.memory_manager.list_categories()
                return {
                    "success": True,
                    "categories": categories
                }
        
        except Exception as e:
            logger.error(f"Error listing memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_memory(self, category: str, key: str) -> Dict[str, Any]:
        """
        Get data from memory.
        
        Args:
            category: Memory category
            key: Memory key
        
        Returns:
            Dict containing memory data
        """
        try:
            # Check if memory manager is available
            if not self.memory_manager:
                return {
                    "success": False,
                    "error": "Memory manager not available"
                }
            
            # Get data from memory
            data = self.memory_manager.load(category, key)
            
            if data is None:
                return {
                    "success": False,
                    "error": f"Memory not found for category '{category}' and key '{key}'"
                }
            
            return {
                "success": True,
                "category": category,
                "key": key,
                "data": data
            }
        
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_memory(self, category: str, key: str, data: Any) -> Dict[str, Any]:
        """
        Save data to memory.
        
        Args:
            category: Memory category
            key: Memory key
            data: Data to save
        
        Returns:
            Dict containing result of save operation
        """
        try:
            # Check if memory manager is available
            if not self.memory_manager:
                return {
                    "success": False,
                    "error": "Memory manager not available"
                }
            
            # Save data to memory
            self.memory_manager.save(category, key, data)
            
            return {
                "success": True,
                "category": category,
                "key": key,
                "message": f"Data saved successfully to {category}/{key}"
            }
        
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_memory(self, category: str, key: str) -> Dict[str, Any]:
        """
        Delete data from memory.
        
        Args:
            category: Memory category
            key: Memory key
        
        Returns:
            Dict containing result of delete operation
        """
        try:
            # Check if memory manager is available
            if not self.memory_manager:
                return {
                    "success": False,
                    "error": "Memory manager not available"
                }
            
            # Check if memory exists
            data = self.memory_manager.load(category, key)
            if data is None:
                return {
                    "success": False,
                    "error": f"Memory not found for category '{category}' and key '{key}'"
                }
            
            # Delete data from memory
            self.memory_manager.delete(category, key)
            
            return {
                "success": True,
                "category": category,
                "key": key,
                "message": f"Data deleted successfully from {category}/{key}"
            }
        
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_to_file(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Save content to a file.
        
        Args:
            content: Content to save
            file_path: Path to save the file to
        
        Returns:
            Dict containing result of save operation
        """
        try:
            # If path is not absolute, make it relative to project root
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": file_path,
                "message": f"File saved successfully to {file_path}"
            }
        
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return {
                "success": False,
                "error": str(e)
            } 