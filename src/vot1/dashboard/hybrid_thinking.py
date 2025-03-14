"""
Hybrid Thinking System

This module provides integration between Claude 3.7's thinking capabilities,
Perplexity research, and memory management to create an enhanced thinking system
that can reason over complex problems with external knowledge.
"""

import os
import re
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    from .utils.enhanced_perplexity import EnhancedPerplexityClient, PerplexityError
    ENHANCED_PERPLEXITY_AVAILABLE = True
except ImportError:
    logger.warning("Enhanced Perplexity client not available, hybrid thinking capabilities will be limited")
    ENHANCED_PERPLEXITY_AVAILABLE = False

try:
    from ..memory import MemoryManager
    MEMORY_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("Memory Manager not available, hybrid thinking capabilities will be limited")
    MEMORY_MANAGER_AVAILABLE = False

class HybridThinkingSystem:
    """
    A system that integrates Claude 3.7's thinking capabilities with Perplexity research
    and memory management for enhanced reasoning and problem-solving.
    """
    
    def __init__(
        self,
        memory_path: str = None,
        perplexity_api_key: str = None,
        redis_url: str = None,
        max_thinking_tokens: int = 20000,
        max_research_tokens: int = 8000,
        enable_memory: bool = True,
        enable_perplexity: bool = True,
        smart_token_management: bool = True
    ):
        """
        Initialize the Hybrid Thinking System.
        
        Args:
            memory_path: Path to store memory data
            perplexity_api_key: API key for Perplexity AI
            redis_url: Redis URL for caching
            max_thinking_tokens: Maximum tokens for thinking context
            max_research_tokens: Maximum tokens for research responses
            enable_memory: Whether to enable memory features
            enable_perplexity: Whether to enable Perplexity research
            smart_token_management: Whether to enable smart token allocation
        """
        self.max_thinking_tokens = max_thinking_tokens
        self.max_research_tokens = max_research_tokens
        self.enable_memory = enable_memory
        self.enable_perplexity = enable_perplexity
        self.smart_token_management = smart_token_management
        
        # Token usage tracking
        self.token_usage = {
            "thinking": 0,
            "research": 0,
            "total": 0
        }
        
        # Initialize memory manager if available and enabled
        self.memory_manager = None
        if MEMORY_MANAGER_AVAILABLE and enable_memory:
            try:
                self.memory_manager = MemoryManager(base_path=memory_path)
                logger.info(f"Memory manager initialized with base path: {memory_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Memory Manager: {e}")
        
        # Initialize Perplexity client if available and enabled
        self.perplexity_client = None
        if ENHANCED_PERPLEXITY_AVAILABLE and enable_perplexity:
            try:
                self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
                if self.perplexity_api_key:
                    self.perplexity_client = EnhancedPerplexityClient(
                        api_key=self.perplexity_api_key,
                        redis_url=redis_url
                    )
                    logger.info("Perplexity client initialized for hybrid thinking")
                else:
                    logger.warning("Perplexity API key not provided, research capabilities will be limited")
            except Exception as e:
                logger.error(f"Failed to initialize Perplexity client: {e}")
        
        # Initialize session state
        self.session_id = str(uuid.uuid4())
        self.thinking_steps = []
        self.research_results = {}
        self.session_memory = {}
        
        logger.info("Hybrid Thinking System initialized")
    
    def is_initialized(self) -> bool:
        """
        Check if the Hybrid Thinking System is properly initialized.
        
        Returns:
            bool: True if initialized with at least one component, False otherwise
        """
        return (
            (self.enable_memory and self.memory_manager is not None) or
            (self.enable_perplexity and self.perplexity_client is not None)
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration of the Hybrid Thinking System.
        
        Returns:
            Dict containing the configuration details
        """
        return {
            "initialized": self.is_initialized(),
            "memory_enabled": self.enable_memory and self.memory_manager is not None,
            "perplexity_enabled": self.enable_perplexity and self.perplexity_client is not None,
            "max_thinking_tokens": self.max_thinking_tokens,
            "max_research_tokens": self.max_research_tokens,
            "smart_token_management": self.smart_token_management,
            "token_usage": self.token_usage,
            "session_id": self.session_id
        }
    
    def start_session(self) -> str:
        """
        Start a new thinking session.
        
        Returns:
            Session ID for the new session
        """
        self.session_id = str(uuid.uuid4())
        self.thinking_steps = []
        self.research_results = {}
        self.session_memory = {}
        
        logger.info(f"Started new thinking session: {self.session_id}")
        return self.session_id
    
    def allocate_tokens(self, task_type: str, complexity: str = "medium") -> int:
        """
        Intelligently allocate tokens based on task type and complexity.
        
        Args:
            task_type: Type of task (thinking, research, etc.)
            complexity: Task complexity (low, medium, high)
            
        Returns:
            Number of tokens allocated for the task
        """
        if not self.smart_token_management:
            return self.max_thinking_tokens if task_type == "thinking" else self.max_research_tokens
            
        # Base allocations for different task types
        base_allocations = {
            "thinking": {
                "low": 5000,
                "medium": 10000,
                "high": 15000
            },
            "research": {
                "low": 2000,
                "medium": 4000,
                "high": 6000
            },
            "conclusion": {
                "low": 3000,
                "medium": 5000,
                "high": 8000
            },
            "default": {
                "low": 4000,
                "medium": 8000,
                "high": 12000
            }
        }
        
        # Get allocation for task type and complexity
        task_allocations = base_allocations.get(task_type, base_allocations["default"])
        allocation = task_allocations.get(complexity, task_allocations["medium"])
        
        # Maximum limit based on task type
        max_limit = self.max_research_tokens if task_type == "research" else self.max_thinking_tokens
        
        # Adjust allocation based on current token usage and remaining tokens
        remaining_tokens = max_limit - self.token_usage["total"]
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
                return min(allocation, max_limit)
            else:
                logger.info(f"Token allocation adjusted: requested {allocation}, available {remaining_tokens}")
                return remaining_tokens
        
        return min(allocation, max_limit)
    
    def add_thinking_step(
        self,
        thought: str,
        step_type: str = "reasoning",
        metadata: Optional[Dict[str, Any]] = None,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Add a thinking step to the current session.
        
        Args:
            thought: The thinking content
            step_type: Type of thinking (reasoning, question, conclusion, etc.)
            metadata: Additional metadata for this thinking step
            complexity: Complexity of the thinking step (low, medium, high)
        
        Returns:
            Dict containing information about the thinking step
        """
        # Check token limit if smart token management is enabled
        if self.smart_token_management:
            # Estimate tokens
            estimated_tokens = len(thought) // 4
            allocated_tokens = self.allocate_tokens("thinking", complexity)
            
            if estimated_tokens > allocated_tokens:
                logger.warning(f"Thinking step exceeds allocated tokens ({estimated_tokens} > {allocated_tokens})")
                # Truncate thought to fit allocation if needed
                if estimated_tokens > allocated_tokens * 1.5:  # Only truncate if significantly over
                    truncation_point = allocated_tokens * 4  # Convert back to characters
                    thought = thought[:truncation_point] + f"\n[... truncated due to token limit ({estimated_tokens} tokens) ...]"
                    logger.info(f"Thought truncated to fit within token allocation: {allocated_tokens} tokens")
            
            # Update token usage
            self.token_usage["thinking"] += min(estimated_tokens, allocated_tokens)
            self.token_usage["total"] += min(estimated_tokens, allocated_tokens)
        
        # Create step object
        step = {
            "id": str(uuid.uuid4()),
            "thought": thought,
            "type": step_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add token information if smart token management is enabled
        if self.smart_token_management:
            step["token_info"] = {
                "estimated_tokens": len(thought) // 4,
                "complexity": complexity
            }
        
        # Add to thinking steps
        self.thinking_steps.append(step)
        
        # Save to memory if available
        if self.memory_manager:
            memory_key = f"thinking_{self.session_id}_{len(self.thinking_steps)}"
            self.memory_manager.save("thinking", memory_key, step)
            step["memory_key"] = memory_key
        
        logger.debug(f"Added thinking step: {step_type} [{step['id']}]")
        return step
    
    def get_thinking_context(self, max_steps: Optional[int] = None) -> str:
        """
        Get the accumulated thinking context for the current session.
        
        Args:
            max_steps: Maximum number of steps to include
        
        Returns:
            Formatted thinking context string
        """
        steps = self.thinking_steps
        if max_steps:
            steps = steps[-max_steps:]
        
        # Format thinking context
        context_parts = []
        for i, step in enumerate(steps):
            step_type = step["type"].upper()
            thought = step["thought"]
            context_parts.append(f"Step {i+1} [{step_type}]: {thought}")
        
        return "\n\n".join(context_parts)
    
    def research(
        self,
        query: str,
        depth: str = "standard",
        system_prompt: Optional[str] = None,
        add_to_thinking: bool = True,
        skip_cache: bool = False,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        Perform research using Perplexity AI and integrate it with thinking.
        
        Args:
            query: Research query
            depth: Research depth ('quick', 'standard', 'deep')
            system_prompt: Custom system prompt for research
            add_to_thinking: Whether to add research results to thinking context
            skip_cache: Whether to skip cache and force a new query
            complexity: Complexity level of the research task
        
        Returns:
            Dict containing research results
        """
        # Check if research is available
        if not self.enable_perplexity or not self.perplexity_client:
            error_msg = "Perplexity research not available"
            logger.warning(error_msg)
            
            research_result = {
                "success": False,
                "error": error_msg,
                "query": query,
                "depth": depth
            }
            
            # Add to thinking even though it failed
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Research query: {query}\nError: {error_msg}",
                    step_type="research_error",
                    metadata={"query": query, "error": error_msg}
                )
            
            return research_result
        
        try:
            # Allocate tokens if smart token management is enabled
            if self.smart_token_management:
                allocated_tokens = self.allocate_tokens("research", complexity)
                logger.info(f"Allocated {allocated_tokens} tokens for research with {complexity} complexity")
            else:
                allocated_tokens = None  # Use depth-based defaults
            
            # Determine token limits based on depth
            depth_options = {
                "quick": {"max_tokens": min(2000, self.max_research_tokens), "temperature": 0.7},
                "standard": {"max_tokens": min(4000, self.max_research_tokens), "temperature": 0.7},
                "deep": {"max_tokens": min(8000, self.max_research_tokens), "temperature": 0.5}
            }
            
            if depth not in depth_options:
                depth = "standard"  # Default to standard if invalid depth provided
            
            options = depth_options[depth]
            
            # Override with allocated tokens if smart token management is enabled
            if allocated_tokens:
                options["max_tokens"] = min(allocated_tokens, options["max_tokens"])
            
            # Default system prompt based on depth
            if not system_prompt:
                if depth == "quick":
                    system_prompt = (
                        "You are a research assistant providing concise information to help with "
                        "step-by-step reasoning. Focus only on the most relevant facts and context "
                        "that would help advance the thinking process. Be brief and to the point."
                    )
                elif depth == "standard":
                    system_prompt = (
                        "You are a research assistant supporting a sophisticated reasoning process. "
                        "Provide relevant information, context, and perspectives on the query to help "
                        "with step-by-step thinking. Include factual information and different viewpoints, "
                        "but stay focused on what's most useful for reasoning through this specific question."
                    )
                else:  # deep
                    system_prompt = (
                        "You are a research assistant supporting complex analytical reasoning. Provide "
                        "comprehensive information about the query, including historical context, technical "
                        "details, competing viewpoints, relevant examples, and nuanced considerations. "
                        "Your goal is to support sophisticated reasoning by ensuring all relevant perspectives "
                        "and facts are available. Include citations where appropriate."
                    )
            
            # Perform research
            logger.info(f"Performing {depth} research: {query}")
            
            response = self.perplexity_client.search(
                query=query,
                model="sonar-reasoning-pro",  # Use appropriate model
                system_prompt=system_prompt,
                temperature=options.get("temperature", 0.7),
                max_tokens=options.get("max_tokens", 4000),
                return_citations=True,
                skip_cache=skip_cache
            )
            
            # Extract content
            content = response.get("content", "")
            citations = response.get("citations", [])
            
            # Update token usage if smart token management is enabled
            if self.smart_token_management:
                # Estimate tokens used
                tokens_used = len(content) // 4
                self.token_usage["research"] += tokens_used
                self.token_usage["total"] += tokens_used
                
                logger.info(f"Research used approximately {tokens_used} tokens (allocated: {options['max_tokens']})")
            
            # Format research result
            research_result = {
                "success": True,
                "query": query,
                "depth": depth,
                "content": content,
                "citations": citations,
                "from_cache": response.get("from_cache", False),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add token information if smart token management is enabled
            if self.smart_token_management:
                research_result["token_info"] = {
                    "tokens_used": len(content) // 4,
                    "allocated_tokens": options["max_tokens"],
                    "complexity": complexity
                }
            
            # Store in session
            research_key = f"research_{len(self.research_results) + 1}"
            self.research_results[research_key] = research_result
            
            # Add to thinking if requested
            if add_to_thinking:
                citation_text = ""
                if citations:
                    citation_text = "\n\nCitations:\n" + "\n".join(
                        f"[{i+1}] {citation.get('title', 'Untitled')} - {citation.get('url', 'No URL')}"
                        for i, citation in enumerate(citations[:5])  # Limit to 5 citations
                    )
                
                research_thought = f"Research query: {query}\n\nFindings:\n{content}{citation_text}"
                
                # Add to thinking context
                self.add_thinking_step(
                    thought=research_thought,
                    step_type="research",
                    metadata={"query": query, "research_key": research_key},
                    complexity=complexity  # Pass complexity to thinking step
                )
            
            # Save to memory if available
            if self.memory_manager:
                memory_key = f"research_{self.session_id}_{research_key}"
                self.memory_manager.save("research", memory_key, research_result)
                research_result["memory_key"] = memory_key
            
            return research_result
            
        except Exception as e:
            logger.error(f"Error performing research: {e}")
            
            research_result = {
                "success": False,
                "error": str(e),
                "query": query,
                "depth": depth
            }
            
            # Add to thinking even though it failed
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Research query: {query}\nError: {str(e)}",
                    step_type="research_error",
                    metadata={"query": query, "error": str(e)}
                )
            
            return research_result
    
    def store_in_memory(
        self,
        key: str,
        value: Any,
        category: str = "session",
        add_to_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Store a value in memory for later recall.
        
        Args:
            key: Key to store the value under
            value: Value to store
            category: Memory category
            add_to_thinking: Whether to add memory storage to thinking context
        
        Returns:
            Dict containing result of memory storage
        """
        # Check if memory is available
        if not self.enable_memory or not self.memory_manager:
            error_msg = "Memory storage not available"
            logger.warning(error_msg)
            
            result = {
                "success": False,
                "error": error_msg,
                "key": key,
                "category": category
            }
            
            # Store in session memory as fallback
            self.session_memory[f"{category}:{key}"] = value
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory storage: {key} in category {category}\nError: {error_msg} (stored in session memory instead)",
                    step_type="memory_store",
                    metadata={"key": key, "category": category, "session_only": True}
                )
            
            return result
        
        try:
            # Create memory key
            memory_key = f"{self.session_id}_{key}"
            
            # Store in memory
            success = self.memory_manager.save(category, memory_key, value)
            
            result = {
                "success": success,
                "key": key,
                "memory_key": memory_key,
                "category": category,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to thinking if requested
            if add_to_thinking:
                value_summary = str(value)
                if len(value_summary) > 100:
                    value_summary = value_summary[:100] + "..."
                
                self.add_thinking_step(
                    thought=f"Stored in memory: '{key}' = {value_summary}",
                    step_type="memory_store",
                    metadata={"key": key, "category": category, "memory_key": memory_key}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing in memory: {e}")
            
            # Store in session memory as fallback
            self.session_memory[f"{category}:{key}"] = value
            
            result = {
                "success": False,
                "error": str(e),
                "key": key,
                "category": category,
                "session_only": True
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory storage: {key} in category {category}\nError: {str(e)} (stored in session memory instead)",
                    step_type="memory_store",
                    metadata={"key": key, "category": category, "session_only": True}
                )
            
            return result
    
    def recall_from_memory(
        self,
        key: str,
        category: str = "session",
        add_to_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Recall a value from memory.
        
        Args:
            key: Key to recall
            category: Memory category
            add_to_thinking: Whether to add memory recall to thinking context
        
        Returns:
            Dict containing recalled value
        """
        # First check session memory
        session_key = f"{category}:{key}"
        if session_key in self.session_memory:
            value = self.session_memory[session_key]
            
            result = {
                "success": True,
                "key": key,
                "category": category,
                "value": value,
                "from_session": True
            }
            
            if add_to_thinking:
                value_summary = str(value)
                if len(value_summary) > 100:
                    value_summary = value_summary[:100] + "..."
                
                self.add_thinking_step(
                    thought=f"Recalled from session memory: '{key}' = {value_summary}",
                    step_type="memory_recall",
                    metadata={"key": key, "category": category, "from_session": True}
                )
            
            return result
        
        # Check if memory manager is available
        if not self.enable_memory or not self.memory_manager:
            error_msg = "Memory recall not available"
            logger.warning(error_msg)
            
            result = {
                "success": False,
                "error": error_msg,
                "key": key,
                "category": category
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory recall: {key} from category {category}\nError: {error_msg}",
                    step_type="memory_recall_error",
                    metadata={"key": key, "category": category}
                )
            
            return result
        
        try:
            # Create memory key
            memory_key = f"{self.session_id}_{key}"
            
            # Try to recall from memory
            value = self.memory_manager.load(category, memory_key)
            
            # If not found, try looking for just the key without session prefix
            if value is None:
                value = self.memory_manager.load(category, key)
            
            if value is None:
                result = {
                    "success": False,
                    "error": f"Memory not found: {key} in category {category}",
                    "key": key,
                    "category": category
                }
                
                if add_to_thinking:
                    self.add_thinking_step(
                        thought=f"Memory recall: {key} from category {category}\nError: Not found",
                        step_type="memory_recall_error",
                        metadata={"key": key, "category": category}
                    )
            else:
                result = {
                    "success": True,
                    "key": key,
                    "category": category,
                    "value": value
                }
                
                if add_to_thinking:
                    value_summary = str(value)
                    if len(value_summary) > 100:
                        value_summary = value_summary[:100] + "..."
                    
                    self.add_thinking_step(
                        thought=f"Recalled from memory: '{key}' = {value_summary}",
                        step_type="memory_recall",
                        metadata={"key": key, "category": category}
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Error recalling from memory: {e}")
            
            result = {
                "success": False,
                "error": str(e),
                "key": key,
                "category": category
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory recall: {key} from category {category}\nError: {str(e)}",
                    step_type="memory_recall_error",
                    metadata={"key": key, "category": category}
                )
            
            return result
    
    def search_memory(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        add_to_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Search for memories matching the query.
        
        Args:
            query: Search query
            categories: Optional list of categories to search in
            add_to_thinking: Whether to add search results to thinking context
        
        Returns:
            Dict containing search results
        """
        # Check if memory is available
        if not self.enable_memory or not self.memory_manager:
            error_msg = "Memory search not available"
            logger.warning(error_msg)
            
            result = {
                "success": False,
                "error": error_msg,
                "query": query
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory search: {query}\nError: {error_msg}",
                    step_type="memory_search_error",
                    metadata={"query": query}
                )
            
            return result
        
        try:
            # Search in memory
            results = self.memory_manager.search(query, categories=categories)
            
            result = {
                "success": True,
                "query": query,
                "categories": categories,
                "results": results,
                "count": len(results)
            }
            
            # Add to thinking if requested
            if add_to_thinking:
                if not results:
                    thought = f"Memory search: {query}\nNo matching memories found."
                else:
                    thought = f"Memory search: {query}\nFound {len(results)} matching memories:\n"
                    for i, memory in enumerate(results[:5]):  # Limit to 5 results
                        category = memory.get("category", "unknown")
                        key = memory.get("key", "unknown")
                        match_type = memory.get("match_type", "unknown")
                        
                        data = memory.get("data")
                        if data:
                            data_str = str(data)
                            if len(data_str) > 100:
                                data_str = data_str[:100] + "..."
                        else:
                            data_str = "No data"
                        
                        thought += f"\n{i+1}. [{category}/{key}] ({match_type} match): {data_str}"
                    
                    if len(results) > 5:
                        thought += f"\n\n... and {len(results) - 5} more results."
                
                self.add_thinking_step(
                    thought=thought,
                    step_type="memory_search",
                    metadata={"query": query, "categories": categories, "result_count": len(results)}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            
            result = {
                "success": False,
                "error": str(e),
                "query": query,
                "categories": categories
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Memory search: {query}\nError: {str(e)}",
                    step_type="memory_search_error",
                    metadata={"query": query, "categories": categories}
                )
            
            return result
    
    def generate_conclusion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        add_to_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a conclusion based on the thinking context.
        
        Args:
            prompt: Prompt for the conclusion generation
            system_prompt: Optional system prompt to guide the conclusion
            add_to_thinking: Whether to add the conclusion to thinking context
        
        Returns:
            Dict containing the generated conclusion
        """
        # Default system prompt if not provided
        if not system_prompt:
            system_prompt = (
                "You are a reasoning assistant synthesizing a conclusion based on a detailed "
                "thinking process. Your task is to create a clear, coherent conclusion that "
                "integrates all important insights, research findings, and intermediate reasoning "
                "steps. Focus on providing a comprehensive yet concise answer that directly addresses "
                "the original question while incorporating the most relevant evidence and logic from "
                "the thinking process."
            )
        
        try:
            # Use Perplexity as a conclusion generator if available
            if self.enable_perplexity and self.perplexity_client:
                # Get thinking context
                thinking_context = self.get_thinking_context()
                
                # Construct the query with thinking context
                query = f"""
                Based on the following thinking process, generate a conclusion for: {prompt}
                
                THINKING PROCESS:
                {thinking_context}
                
                CONCLUSION:
                """
                
                # Generate conclusion using Perplexity
                response = self.perplexity_client.search(
                    query=query,
                    model="sonar-reasoning-pro",
                    system_prompt=system_prompt,
                    temperature=0.5,  # Lower temperature for more focused output
                    max_tokens=min(4000, self.max_research_tokens),
                    return_citations=False
                )
                
                conclusion = response.get("content", "")
            else:
                # Fallback if Perplexity is not available
                conclusion = "Unable to generate a conclusion because Perplexity is not available. Please review the thinking steps and formulate your own conclusion."
            
            result = {
                "success": True,
                "prompt": prompt,
                "conclusion": conclusion,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to thinking if requested
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Conclusion for '{prompt}':\n\n{conclusion}",
                    step_type="conclusion",
                    metadata={"prompt": prompt}
                )
            
            # Save to memory if available
            if self.memory_manager:
                memory_key = f"conclusion_{self.session_id}"
                self.memory_manager.save("conclusions", memory_key, result)
                result["memory_key"] = memory_key
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating conclusion: {e}")
            
            result = {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
            
            if add_to_thinking:
                self.add_thinking_step(
                    thought=f"Error generating conclusion for '{prompt}': {str(e)}",
                    step_type="conclusion_error",
                    metadata={"prompt": prompt, "error": str(e)}
                )
            
            return result
    
    def save_session(self) -> Dict[str, Any]:
        """
        Save the current thinking session to memory.
        
        Returns:
            Dict containing information about the saved session
        """
        # Check if memory is available
        if not self.enable_memory or not self.memory_manager:
            logger.warning("Memory not available, cannot save session")
            return {
                "success": False,
                "error": "Memory not available",
                "session_id": self.session_id
            }
        
        try:
            # Create session summary
            session_data = {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "thinking_steps": self.thinking_steps,
                "research_results": self.research_results,
                "step_count": len(self.thinking_steps),
                "research_count": len(self.research_results)
            }
            
            # Save to memory
            success = self.memory_manager.save("sessions", self.session_id, session_data)
            
            return {
                "success": success,
                "session_id": self.session_id,
                "step_count": len(self.thinking_steps),
                "research_count": len(self.research_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error saving thinking session: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load a thinking session from memory.
        
        Args:
            session_id: ID of the session to load
        
        Returns:
            Dict containing information about the loaded session
        """
        # Check if memory is available
        if not self.enable_memory or not self.memory_manager:
            logger.warning("Memory not available, cannot load session")
            return {
                "success": False,
                "error": "Memory not available",
                "session_id": session_id
            }
        
        try:
            # Load from memory
            session_data = self.memory_manager.load("sessions", session_id)
            
            if not session_data:
                logger.warning(f"Session not found: {session_id}")
                return {
                    "success": False,
                    "error": f"Session not found: {session_id}",
                    "session_id": session_id
                }
            
            # Update current session
            self.session_id = session_id
            self.thinking_steps = session_data.get("thinking_steps", [])
            self.research_results = session_data.get("research_results", {})
            
            return {
                "success": True,
                "session_id": session_id,
                "step_count": len(self.thinking_steps),
                "research_count": len(self.research_results),
                "timestamp": session_data.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error loading thinking session: {e}")
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }
    
    def list_sessions(self) -> Dict[str, Any]:
        """
        List all saved thinking sessions.
        
        Returns:
            Dict containing information about available sessions
        """
        # Check if memory is available
        if not self.enable_memory or not self.memory_manager:
            logger.warning("Memory not available, cannot list sessions")
            return {
                "success": False,
                "error": "Memory not available"
            }
        
        try:
            # List sessions from memory
            session_keys = self.memory_manager.list_keys("sessions")
            
            sessions = []
            for session_id in session_keys:
                session_data = self.memory_manager.load("sessions", session_id)
                if session_data:
                    sessions.append({
                        "session_id": session_id,
                        "timestamp": session_data.get("timestamp"),
                        "step_count": len(session_data.get("thinking_steps", [])),
                        "research_count": len(session_data.get("research_results", {}))
                    })
            
            return {
                "success": True,
                "sessions": sessions,
                "count": len(sessions)
            }
            
        except Exception as e:
            logger.error(f"Error listing thinking sessions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_token_usage(self) -> Dict[str, int]:
        """
        Get an estimate of the token usage for the current session.
        
        Returns:
            Dict containing token usage information
        """
        # Simple estimation based on character count (rough approximation)
        def estimate_tokens(text: str) -> int:
            if not text:
                return 0
            return len(text) // 4  # Rough approximation of tokens (4 chars ~= 1 token)
        
        thinking_tokens = sum(estimate_tokens(step.get("thought", "")) for step in self.thinking_steps)
        
        research_tokens = 0
        for result in self.research_results.values():
            research_tokens += estimate_tokens(result.get("content", ""))
        
        return {
            "thinking_tokens": thinking_tokens,
            "research_tokens": research_tokens,
            "total_tokens": thinking_tokens + research_tokens,
            "thinking_token_limit": self.max_thinking_tokens,
            "research_token_limit": self.max_research_tokens
        } 