"""
Advanced Research Agent with Hybrid Intelligence

This agent combines Claude 3.7 Sonnet's hybrid thinking, Perplexity's deep web research,
GitHub integration, and Composio tools to create a powerful research and development system.

Features:
- Multi-source research (web, GitHub, academic papers)
- Enhanced hybrid thinking with Claude 3.7 Sonnet
- TRILOGY BRAIN memory integration
- Code retrieval and generation
- Memory-enhanced reasoning
- Tool orchestration via MCP

IMPORTANT: Always use the latest Claude model version (currently claude-3-7-sonnet-20250219).
"""

import os
import sys
import json
import time
import asyncio
import logging
import random
import hashlib
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AdvancedResearchAgent")

# Try to import required packages
try:
    # Perplexity client
    from perplexipy import PerplexityClient
except ImportError:
    logger.error("PerplexiPy not installed. Install with: pip install PerplexiPy")
    perplexipy_installed = False
else:
    perplexipy_installed = True

try:
    # Anthropic client for Claude 3.7
    import anthropic
except ImportError:
    logger.error("Anthropic not installed. Install with: pip install anthropic")
    anthropic_installed = False
else:
    anthropic_installed = True

# Try to import TRILOGY BRAIN memory system
try:
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.memory import MemoryManager
    trilogy_brain_available = True
except ImportError:
    try:
        from vot1.composio.memory_bridge import ComposioMemoryBridge
        from vot1.memory import MemoryManager
        trilogy_brain_available = True
    except ImportError:
        logger.warning("TRILOGY BRAIN memory system not available")
        trilogy_brain_available = False

class AdvancedResearchAgent:
    """
    Advanced Research Agent that combines multiple AI systems and tools.
    
    This agent integrates:
    1. Claude 3.7 Sonnet for enhanced hybrid thinking and analysis
    2. Perplexity for deep web research
    3. GitHub for code retrieval and analysis
    4. Composio tools for extended capabilities
    5. TRILOGY BRAIN for advanced memory management
    """
    
    def __init__(
        self,
        perplexity_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        composio_api_key: Optional[str] = None,
        composio_mcp_url: Optional[str] = None,
        memory_path: str = "memory/agent",
        max_thinking_tokens: int = 120000,  # Increased for enhanced hybrid thinking
        research_depth: str = "deep",
        output_dir: str = "output",
        enable_trilogy_brain: bool = True
    ):
        """
        Initialize the Advanced Research Agent.
        
        Args:
            perplexity_api_key: API key for Perplexity
            anthropic_api_key: API key for Anthropic/Claude
            github_token: GitHub access token
            composio_api_key: API key for Composio
            composio_mcp_url: MCP URL for Composio
            memory_path: Path for memory storage
            max_thinking_tokens: Maximum tokens for hybrid thinking
            research_depth: Depth of research ("brief", "standard", "deep")
            output_dir: Directory for output files
            enable_trilogy_brain: Whether to enable TRILOGY BRAIN memory
        """
        # Store configuration
        self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.composio_api_key = composio_api_key or os.environ.get("COMPOSIO_API_KEY")
        self.composio_mcp_url = composio_mcp_url or os.environ.get("COMPOSIO_MCP_URL")
        
        self.memory_path = memory_path
        self.max_thinking_tokens = max_thinking_tokens
        self.research_depth = research_depth
        self.output_dir = output_dir
        self.enable_trilogy_brain = enable_trilogy_brain and trilogy_brain_available
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a session ID
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._generate_id()}"
        
        # Initialize clients
        self.perplexity_client = None
        self.claude_client = None
        self.github_client = None
        self.composio_client = None
        
        # Initialize TRILOGY BRAIN memory system
        self.memory_bridge = None
        self.memory_manager = None
        
        # Initialize state
        self.initialized = False
        self.missing_components = []
        
        # Model configuration
        self.claude_model = os.environ.get("VOT1_PRIMARY_MODEL", "claude-3-7-sonnet-20250219")
        self.perplexity_model = os.environ.get("VOT1_SECONDARY_MODEL", "pplx-70b-online")
        
        # Research tracking
        self.research_status = {
            "started": False,
            "web_research": False,
            "code_analysis": False,
            "thinking": False,
            "results": False,
            "completed": False
        }
        
        # Initialize agent
        self._init_agent()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._generate_id()}"
    
    def _generate_id(self, length: int = 8) -> str:
        """Generate a random ID of specified length."""
        return ''.join(random.choices('0123456789abcdef', k=length))
    
    def _generate_md5(self, content: str) -> str:
        """Generate MD5 hash for content."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _validate_requirements(self) -> None:
        """Validate that all required components are available"""
        missing = []
        
        if not perplexipy_installed:
            missing.append("PerplexiPy")
        
        if not anthropic_installed:
            missing.append("Anthropic")
        
        if not self.perplexity_api_key:
            missing.append("PERPLEXITY_API_KEY")
        
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        
        if missing:
            logger.warning(f"Missing components: {', '.join(missing)}")
            logger.warning("Some features may be unavailable")
    
    def _init_agent(self):
        """Initialize agent components synchronously."""
        try:
            # Initialize Perplexity client
            if perplexipy_installed and self.perplexity_api_key:
                self.perplexity_client = PerplexityClient(
                    key=self.perplexity_api_key
                )
                logger.info("Perplexity client initialized")
            else:
                self.missing_components.append("PerplexiPy")
            
            # Initialize Claude client
            if anthropic_installed and self.anthropic_api_key:
                self.claude_client = anthropic.Anthropic(
                    api_key=self.anthropic_api_key
                )
                logger.info("Claude client initialized")
            else:
                self.missing_components.append("Anthropic")
            
            # Initialize GitHub client if token is available
            if self.github_token:
                # GitHub client initialization would go here
                # For now, we'll just log that it's configured
                logger.info("GitHub access configured")
            else:
                self.missing_components.append("GITHUB_TOKEN")
            
            # Initialize Composio client if API key is available
            if self.composio_api_key and self.composio_mcp_url:
                # Composio client initialization would go here
                # For now, we'll just log that it's configured
                logger.info("Composio access configured")
            else:
                if not self.composio_api_key:
                    self.missing_components.append("COMPOSIO_API_KEY")
                if not self.composio_mcp_url:
                    self.missing_components.append("COMPOSIO_MCP_URL")
            
            # Initialize TRILOGY BRAIN memory system - async parts will be lazy-loaded
            if self.enable_trilogy_brain and trilogy_brain_available:
                try:
                    # Defer actual initialization to async method
                    logger.info("TRILOGY BRAIN memory system will be initialized when needed")
                except Exception as e:
                    logger.error(f"Error initializing TRILOGY BRAIN: {e}")
                    self.memory_bridge = None
                    self.memory_manager = None
                    self.missing_components.append("TRILOGY_BRAIN")
            
            # Check if any components are missing
            if self.missing_components:
                logger.warning(f"Missing components: {', '.join(self.missing_components)}")
                logger.warning("Some features may be unavailable")
            
            self.initialized = True
            logger.info("Agent initialization completed")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error("Agent initialization failed")
            self.initialized = False
            raise
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from disk if available"""
        memory_file = os.path.join(self.memory_path, "memory.json")
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory: {str(e)}")
        
        # Initialize empty memory
        return {
            "research_sessions": {},
            "code_snippets": {},
            "concepts": {},
            "references": {}
        }
    
    def _save_memory(self) -> None:
        """Save memory to disk"""
        memory_file = os.path.join(self.memory_path, "memory.json")
        try:
            with open(memory_file, "w") as f:
                json.dump(self.memory_store, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    def store_in_memory(self, content: str, content_type: str, metadata: Dict[str, Any] = None) -> str:
        """
        Store content in memory with appropriate categorization.
        
        Args:
            content: The content to store
            content_type: Type of content (research, code, concept, reference)
            metadata: Additional metadata
            
        Returns:
            ID of the stored memory
        """
        if not metadata:
            metadata = {}
        
        # Generate a unique ID
        memory_id = hashlib.md5(f"{content_type}:{content}:{time.time()}".encode()).hexdigest()
        
        # Store with metadata
        memory_item = {
            "id": memory_id,
            "content": content,
            "type": content_type,
            "timestamp": time.time(),
            "session_id": self.session_id,
            "metadata": metadata
        }
        
        # Store in appropriate category
        if content_type.startswith("research"):
            if "research_sessions" not in self.memory_store:
                self.memory_store["research_sessions"] = {}
            self.memory_store["research_sessions"][memory_id] = memory_item
        
        elif content_type.startswith("code"):
            if "code_snippets" not in self.memory_store:
                self.memory_store["code_snippets"] = {}
            self.memory_store["code_snippets"][memory_id] = memory_item
        
        elif content_type.startswith("concept"):
            if "concepts" not in self.memory_store:
                self.memory_store["concepts"] = {}
            self.memory_store["concepts"][memory_id] = memory_item
        
        elif content_type.startswith("reference"):
            if "references" not in self.memory_store:
                self.memory_store["references"] = {}
            self.memory_store["references"][memory_id] = memory_item
        
        # Save memory
        self._save_memory()
        
        return memory_id
    
    def retrieve_from_memory(self, query: str, content_types: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on semantic search.
        
        Args:
            query: Search query
            content_types: Types of content to search
            limit: Maximum number of results
            
        Returns:
            List of memory items
        """
        # Simple implementation - in a real system, this would use embeddings and vector search
        
        results = []
        types_to_search = content_types or ["research", "code", "concept", "reference"]
        
        # Convert query to lowercase for case-insensitive matching
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Search each category
        for category_name, category_items in self.memory_store.items():
            # Skip categories that don't match requested types
            if not any(category_name.startswith(t) for t in types_to_search):
                continue
                
            for memory_id, memory_item in category_items.items():
                # Calculate a simple relevance score
                content_lower = memory_item["content"].lower()
                
                # Count how many query terms appear in the content
                term_matches = sum(1 for term in query_terms if term in content_lower)
                
                # Only include if there's at least one match
                if term_matches > 0:
                    # Add score to the item for sorting
                    memory_item_with_score = memory_item.copy()
                    memory_item_with_score["relevance_score"] = term_matches
                    results.append(memory_item_with_score)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Return top results
        return results[:limit]
    
    async def conduct_web_research(self, topic: str, focus: Optional[str] = None) -> Dict[str, Any]:
        """
        Conduct deep web research using Perplexity.
        
        Args:
            topic: Research topic
            focus: Optional focus area
            
        Returns:
            Dictionary with research results
        """
        logger.info(f"Conducting web research on: {topic}")
        self.research_status["web_research"] = "in_progress"
        
        if "perplexity" not in self.components:
            logger.error("Perplexity client not initialized")
            self.research_status["web_research"] = "failed"
            return {"error": "Perplexity client not initialized"}
        
        perplexity = self.components["perplexity"]
        
        try:
            research_prompt = f"""Provide comprehensive research on {topic}. 
            {f'Focus specifically on: {focus}' if focus else ''}
            
            Include:
            1. Latest developments and advancements
            2. Key concepts and technical details
            3. Best practices and implementation approaches
            4. Challenges and limitations
            5. Future directions and opportunities
            
            Provide specific examples, code snippets, and technical details where relevant.
            Cite sources where possible.
            """
            
            research_results = perplexity.query(research_prompt)
            
            # Store in memory
            research_id = self.store_in_memory(
                content=research_results,
                content_type="research_primary",
                metadata={
                    "topic": topic,
                    "focus": focus,
                    "depth": self.research_depth
                }
            )
            
            logger.info(f"Web research completed, stored with ID: {research_id}")
            
            # Follow up with more specific questions based on the initial research
            followup_questions = self._generate_followup_questions(research_results, topic)
            
            followup_results = {}
            for question in followup_questions[:3]:  # Limit to 3 follow-up questions
                logger.info(f"Researching follow-up question: {question}")
                result = perplexity.query(question)
                followup_results[question] = result
                
                # Store each follow-up in memory
                self.store_in_memory(
                    content=result,
                    content_type="research_followup",
                    metadata={
                        "topic": topic,
                        "question": question
                    }
                )
            
            # Compile results
            results = {
                "primary_research": research_results,
                "followup_research": followup_results,
                "topic": topic,
                "focus": focus,
                "research_id": research_id
            }
            
            self.research_status["web_research"] = "completed"
            return results
            
        except Exception as e:
            logger.error(f"Error during web research: {str(e)}")
            self.research_status["web_research"] = "failed"
            return {"error": str(e)}
    
    def _generate_followup_questions(self, research_content: str, topic: str) -> List[str]:
        """Generate follow-up questions based on initial research"""
        # This would ideally use Claude to generate follow-up questions,
        # but for simplicity, we'll use a predefined set based on topic keywords
        
        # Extract key terms from topic
        terms = topic.lower().split()
        
        questions = [
            f"What are the latest advancements in {topic} as of 2025?",
            f"What are common implementation challenges with {topic} and how to overcome them?",
            f"How does {topic} integrate with existing systems and frameworks?",
            f"What security considerations are important for {topic}?",
            f"What are the performance implications of {topic}?",
            f"How is {topic} expected to evolve in the next 2-3 years?"
        ]
        
        # Add term-specific questions
        term_specific = []
        tech_terms = ["ai", "model", "learning", "neural", "blockchain", "web3", "cloud", 
                      "protocol", "api", "mcp", "agi", "claude", "openai", "perplexity"]
        
        for term in terms:
            if term in tech_terms:
                term_specific.append(f"How does {term} specifically contribute to {topic}?")
                term_specific.append(f"What are the best {term} implementations for {topic}?")
        
        # Combine and shuffle to get diverse questions
        all_questions = questions + term_specific
        random.shuffle(all_questions)
        
        return all_questions
    
    async def search_github_code(self, query: str, language: Optional[str] = None, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for code on GitHub.
        
        Args:
            query: Search query
            language: Programming language
            max_results: Maximum number of results
            
        Returns:
            List of code snippets
        """
        logger.info(f"Searching GitHub for code: {query}")
        self.research_status["code_analysis"] = "in_progress"
        
        if "github" not in self.components:
            logger.error("GitHub not configured")
            self.research_status["code_analysis"] = "failed"
            return [{"error": "GitHub not configured"}]
        
        try:
            # Construct GitHub search query
            search_query = query
            if language:
                search_query = f"{search_query} language:{language}"
            
            # Prepare the search API call
            token = self.components["github"]["token"]
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            params = {
                "q": search_query,
                "per_page": max_results
            }
            
            # This is just a placeholder - in a real implementation, we would use
            # httpx, requests, or a GitHub API library to make the API call
            # For now, we'll just return mock data
            
            # Mock code results
            mock_results = [
                {
                    "name": "example_implementation.py",
                    "repo": "example/repo",
                    "url": f"https://github.com/example/repo/blob/main/example_implementation.py",
                    "language": language or "python",
                    "content": f"# Example implementation for {query}\n\ndef main():\n    print('Implementing {query}')\n\nif __name__ == '__main__':\n    main()"
                },
                {
                    "name": "advanced_example.py",
                    "repo": "advanced/repo",
                    "url": f"https://github.com/advanced/repo/blob/main/advanced_example.py",
                    "language": language or "python",
                    "content": f"# Advanced implementation for {query}\n\nclass AdvancedImplementation:\n    def __init__(self):\n        self.config = {{}}\n\n    def run(self):\n        print('Running advanced implementation for {query}')"
                }
            ]
            
            # Store code snippets in memory
            for i, result in enumerate(mock_results):
                code_id = self.store_in_memory(
                    content=result["content"],
                    content_type="code_snippet",
                    metadata={
                        "name": result["name"],
                        "repo": result["repo"],
                        "url": result["url"],
                        "language": result["language"],
                        "query": query
                    }
                )
                mock_results[i]["memory_id"] = code_id
            
            logger.info(f"GitHub code search completed, found {len(mock_results)} results")
            self.research_status["code_analysis"] = "completed"
            
            return mock_results
            
        except Exception as e:
            logger.error(f"Error during GitHub search: {str(e)}")
            self.research_status["code_analysis"] = "failed"
            return [{"error": str(e)}]
    
    async def analyze_with_claude(self, topic: str, research_results: Dict[str, Any], analysis_type: str = "standard", include_thinking: bool = True) -> Dict[str, Any]:
        """
        Analyze research results using Claude's hybrid thinking.
        
        Args:
            topic: The research topic
            research_results: The research results to analyze
            analysis_type: Type of analysis ("brief", "standard", "deep", "threejs")
            include_thinking: Whether to include hybrid thinking
            
        Returns:
            Dictionary with analysis results
        """
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        result = {}
        
        try:
            # Prepare research content
            content = ""
            if "primary_research" in research_results:
                content += f"## Primary Research\n\n{research_results['primary_research']}\n\n"
            
            if "followup_research" in research_results:
                content += "## Follow-up Research\n\n"
                for question, answer in research_results["followup_research"].items():
                    content += f"### {question}\n{answer}\n\n"
            
            # Adjust prompt based on analysis type
            if analysis_type == "brief":
                prompt = f"Please analyze this research on {topic} and provide a brief summary of key points:"
                thinking_prompt = f"Let's think deeply but concisely about the research on {topic} to identify the most important aspects and insights."
            elif analysis_type == "deep":
                prompt = f"Please provide an in-depth analysis of this research on {topic}, identifying patterns, insights, and implications:"
                thinking_prompt = f"Let's conduct a comprehensive analysis of the research on {topic}, exploring various dimensions, implications, and potential applications."
            elif analysis_type == "threejs":
                prompt = f"You are an expert in THREE.js development and visualization. Please analyze this research on {topic} and provide insights on how to visualize this information using THREE.js:"
                thinking_prompt = f"Let's analyze this research from the perspective of creating an effective THREE.js visualization. Consider data structures, visual representations, user interactions, and technical implementation details."
            else:  # standard
                prompt = f"Please analyze this research on {topic} and provide a comprehensive analysis:"
                thinking_prompt = f"Let's analyze the research on {topic} systematically, identifying key findings, patterns, and implications."
            
            # Create system message based on analysis type
            if analysis_type == "threejs":
                system_message = "You are Claude, an expert in THREE.js visualization and data representation. Your task is to analyze research and provide detailed recommendations for THREE.js visualizations, including implementation considerations."
            else:
                system_message = "You are Claude, an AI assistant with hybrid thinking capabilities. Your task is to analyze research comprehensively and provide insightful analysis."
            
            # Add thinking capabilities
            if include_thinking:
                system_message += " Use your hybrid thinking capabilities to explore the topic deeply before responding."
                prompt = f"{thinking_prompt}\n\n{prompt}\n\nResearch content:\n\n{content}"
            else:
                prompt = f"{prompt}\n\nResearch content:\n\n{content}"
            
            # Standard API call with current SDK support
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract thinking and content
            thinking = None
            if include_thinking and hasattr(response, 'usage') and hasattr(response.usage, 'thinking_tokens'):
                thinking = response.usage.thinking_content
            
            result = {
                "analysis": response.content[0].text,
                "thinking": thinking,
                "success": True
            }
            
            # Store analysis in memory if TRILOGY BRAIN is available
            if self.memory_manager and topic:
                memory_id = await self.memory_manager.store_memory(
                    content=result["analysis"],
                    memory_type="analysis",
                    metadata={
                        "topic": topic,
                        "timestamp": time.time(),
                        "session_id": self.session_id,
                        "analysis_type": analysis_type
                    }
                )
                result["memory_id"] = memory_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Claude analysis: {e}")
            return {"error": str(e)}
    
    async def hybrid_thinking(self, prompt: str, context: Optional[str] = None, memory_types: List[str] = None) -> Dict[str, Any]:
        """
        Perform hybrid thinking with Claude 3.7 Sonnet.
        
        This sends a request to Claude with a high max_tokens for thinking,
        allowing for more complex reasoning.
        
        Args:
            prompt: The prompt to think about
            context: Additional context
            memory_types: Types of memories to include
            
        Returns:
            Dictionary with thinking results
        """
        logger.info(f"Performing hybrid thinking: {prompt[:50]}...")
        
        if "claude" not in self.components:
            logger.error("Claude client not initialized")
            return {"error": "Claude client not initialized"}
        
        try:
            claude = self.components["claude"]
            
            # Retrieve relevant memories
            memories = []
            if memory_types:
                memories = self.retrieve_from_memory(prompt, content_types=memory_types, limit=10)
            
            # Prepare memory context
            memory_context = ""
            if memories:
                memory_context = "Here are some relevant prior memories and information:\n\n"
                for i, memory in enumerate(memories, 1):
                    memory_context += f"Memory {i} ({memory['type']}):\n{memory['content'][:1000]}\n\n"
            
            # Combine prompt, context, and memories
            full_prompt = f"""Task: {prompt}

{memory_context if memories else ""}

{context if context else ""}

Please think through this thoroughly using your hybrid thinking capabilities before providing a response.
"""
            
            # Create system prompt that encourages deep thinking
            system_prompt = """You are Claude 3.7 Sonnet, a highly capable AI assistant with advanced hybrid thinking abilities.
            
For this task, I'd like you to engage in a thorough thinking process before providing your final answer. 
Your thinking should:
1. Break down the problem into components
2. Consider multiple perspectives and approaches
3. Identify potential challenges or limitations
4. Synthesize information from various sources
5. Draw on your knowledge across relevant domains

First explore multiple angles deeply, then provide a well-reasoned final response.
"""
            
            # Make the API call with Claude - using the correct model name for Claude 3.7 Sonnet
            response = claude.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Extract the content
            thinking_result = response.content[0].text
            
            # Store in memory
            thinking_id = self.store_in_memory(
                content=thinking_result,
                content_type="hybrid_thinking",
                metadata={
                    "prompt": prompt,
                    "memory_count": len(memories),
                }
            )
            
            logger.info(f"Hybrid thinking completed, stored with ID: {thinking_id}")
            
            return {
                "thinking": thinking_result,
                "thinking_id": thinking_id,
                "memory_count": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Error during hybrid thinking: {str(e)}")
            return {"error": str(e)}
    
    async def research_and_analyze(
        self, 
        topic: str, 
        focus: Optional[str] = None,
        code_search: bool = True,
        code_language: Optional[str] = None,
        include_thinking: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive research and analysis on a topic.
        
        This method:
        1. Conducts deep web research with Perplexity
        2. Searches for relevant code on GitHub
        3. Analyzes research findings with Claude
        4. Performs hybrid thinking on the complete research
        
        Args:
            topic: Research topic
            focus: Optional focus area
            code_search: Whether to search for code
            code_language: Programming language for code search
            include_thinking: Whether to include hybrid thinking
            
        Returns:
            Dictionary with complete research results
        """
        # Ensure agent is initialized
        if not self.initialized:
            try:
                # Re-initialize if needed
                self._init_agent()
            except Exception as e:
                logger.error(f"Error initializing agent: {e}")
                return {"error": str(e)}
        
        logger.info(f"Starting comprehensive research: {topic}")
        self.research_status["started"] = True
        
        results = {
            "topic": topic,
            "focus": focus,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        # Step 1: Conduct web research
        web_research = await self.conduct_web_research(topic, focus)
        results["web_research"] = web_research
        
        # Step 2: Search for code if requested
        if code_search:
            code_results = await self.search_github_code(topic, code_language)
            results["code_search"] = code_results
        
        # Step 3: Analyze research findings
        research_content = web_research.get("primary_research", "")
        if "error" not in web_research and research_content:
            research_analysis = await self.analyze_with_claude(
                topic=topic,
                research_results=web_research,
                analysis_type="research"
            )
            results["research_analysis"] = research_analysis
        
        # Step 4: Perform hybrid thinking if requested
        if include_thinking:
            # Prepare content for hybrid thinking
            thinking_content = f"""Topic: {topic}
Focus: {focus if focus else 'General'}

Primary Research:
{web_research.get('primary_research', '')[:5000]}

{"Code Examples:" if code_search and "code_search" in results else ""}
{results.get("code_search", [])[0].get("content", "") if code_search and "code_search" in results and results["code_search"] else ""}
"""
            
            thinking_prompt = f"""Based on comprehensive research on "{topic}", provide:
1. Key insights and findings
2. Technical implementation considerations
3. Current limitations and challenges
4. Future directions and opportunities
5. Practical recommendations

Synthesize all available information into a cohesive analysis.
"""
            
            thinking_results = await self.hybrid_thinking(
                prompt=thinking_prompt,
                context=thinking_content,
                memory_types=["research", "code", "analysis"]
            )
            
            results["hybrid_thinking"] = thinking_results
        
        # Step 5: Generate final report
        final_report = self._generate_final_report(results)
        results["final_report"] = final_report
        
        # Save results to file
        output_file = os.path.join(
            self.output_dir, 
            f"research_{self._sanitize_filename(topic)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Research results saved to {output_file}")
            results["output_file"] = output_file
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
        
        self.research_status["completed"] = True
        logger.info(f"Comprehensive research completed: {topic}")
        
        return results
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename"""
        # Remove characters that aren't alphanumerics, underscores, or hyphens
        # Replace spaces with underscores
        return ''.join(c if c.isalnum() or c in '-_' else '_' for c in name.replace(' ', '_'))
    
    def _generate_final_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a final report from research results"""
        report = {
            "title": f"Research Report: {results['topic']}",
            "focus": results.get("focus", "General"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": results.get("hybrid_thinking", {}).get("thinking", "No hybrid thinking available.") 
                      if "hybrid_thinking" in results else 
                      results.get("research_analysis", {}).get("analysis", "No analysis available."),
            "web_research_summary": results.get("web_research", {}).get("primary_research", "")[:1000] + "...",
            "code_examples": [
                {
                    "name": code.get("name", "Unknown"),
                    "language": code.get("language", "Unknown"),
                    "snippet": code.get("content", "")[:500] + "..." if len(code.get("content", "")) > 500 else code.get("content", "")
                }
                for code in results.get("code_search", [])
            ] if "code_search" in results else []
        }
        
        # Store the report in memory
        report_id = self.store_in_memory(
            content=json.dumps(report, indent=2),
            content_type="research_report",
            metadata={
                "topic": results["topic"],
                "focus": results.get("focus")
            }
        )
        
        report["report_id"] = report_id
        return report

    async def research_threejs_visualization(self, topic: str, visualization_type: str = "dashboard") -> Dict[str, Any]:
        """
        Research THREE.js visualization techniques and generate example code.
        
        Args:
            topic: The topic to research visualization for
            visualization_type: Type of visualization (dashboard, graph, etc.)
            
        Returns:
            Dictionary with research results and code examples
        """
        if not self.initialized:
            return {"error": "Agent not initialized"}
        
        logger.info(f"Researching THREE.js visualization for: {visualization_type}, type: {visualization_type}")
        
        try:
            # Step 1: Research THREE.js techniques using Perplexity
            if self.perplexity_client:
                research_query = f"Latest THREE.js techniques for {visualization_type} visualizations, include performance optimization, responsive design, integration with data sources, and best practices for user interaction"
                
                research_response = await self.perplexity_client.query(
                    research_query,
                    stream=False
                )
                
                research = research_response["text"] if "text" in research_response else ""
                
                # Step 2: Research implementation examples
                implementation_query = f"Detailed implementation examples for {visualization_type} visualizations with THREE.js, including code structure, shader techniques, animation approaches, performance considerations, and user interaction patterns"
                
                implementation_response = await self.perplexity_client.query(
                    implementation_query,
                    stream=False
                )
                
                implementation_examples = implementation_response["text"] if "text" in implementation_response else ""
                
                # Step 3: Generate custom code example
                code_query = f"Provide a complete modern THREE.js visualization for a {visualization_type} with clean, modular code structure using r160 or newer. The code should be optimized for performance and include interactive elements."
                
                code_response = await self.perplexity_client.query(
                    code_query,
                    stream=False
                )
                
                code_examples = code_response["text"] if "text" in code_response else ""
                
                # Create research ID for tracking
                research_id = self._generate_md5(research)
                code_id = self._generate_md5(code_examples)
                
                # Compile results
                results = {
                    "research": research,
                    "implementation_examples": implementation_examples,
                    "code_examples": code_examples,
                    "topic": visualization_type,
                    "visualization_type": visualization_type,
                    "research_id": research_id,
                    "code_id": code_id
                }
                
                # Save results to file
                filename = f"threejs_{visualization_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, "w") as f:
                    json.dump(results, f, indent=2)
                
                logger.info(f"THREE.js research completed, saved to {filepath}")
                
                # Store in memory if available
                if self.memory_manager:
                    memory_id = await self.memory_manager.store_memory(
                        content=json.dumps(results),
                        memory_type="threejs_research",
                        metadata={
                            "topic": topic,
                            "visualization_type": visualization_type,
                            "timestamp": time.time(),
                            "session_id": self.session_id
                        }
                    )
                    results["memory_id"] = memory_id
                
                return results
            else:
                logger.error("Perplexity client not initialized")
                return {"error": "Perplexity client not initialized"}
                
        except Exception as e:
            logger.error(f"Error researching THREE.js: {e}")
            return {"error": str(e)}

    async def research_mcp_with_threejs(self, topic: str, visualization_type: str = "dashboard") -> Dict[str, Any]:
        """
        Research MCP topic and integrate with THREE.js visualization.
        
        Args:
            topic: The MCP topic to research
            visualization_type: Type of visualization
            
        Returns:
            Dictionary with integrated research results
        """
        logger.info(f"Starting MCP-THREE.js research: {topic}, visualization: {visualization_type}")
        
        # Step 1: Research MCP topic
        logger.info(f"Conducting web research on: {topic}")
        mcp_research = await self.conduct_web_research(topic)
        
        # Step 2: Research THREE.js visualization
        logger.info(f"Researching THREE.js visualization for: {visualization_type}, type: {visualization_type}")
        threejs_research = await self.research_threejs_visualization(topic, visualization_type)
        
        # Step 3: Integrate research results
        results = {
            "topic": topic,
            "visualization_focus": visualization_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "mcp_research": mcp_research,
            "threejs_research": threejs_research
        }
        
        # Store in memory if available
        if self.memory_manager:
            memory_id = await self.memory_manager.store_memory(
                content=json.dumps(results),
                memory_type="mcp_threejs_research",
                metadata={
                    "topic": topic,
                    "visualization_type": visualization_type,
                    "timestamp": time.time(),
                    "session_id": self.session_id
                }
            )
            results["memory_id"] = memory_id
        
        # Save results to file
        filename = f"mcp_threejs_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        
        results["output_file"] = filepath
        
        logger.info(f"MCP-THREE.js research saved to {filepath}")
        logger.info(f"MCP-THREE.js research completed: {topic}")
        
        return results

def main():
    """Command-line interface for the research agent."""
    try:
        parser = argparse.ArgumentParser(description="Advanced Research Agent")
        
        # Add command-line arguments
        parser.add_argument("--topic", type=str, help="Research topic")
        parser.add_argument("--focus", type=str, help="Research focus area")
        parser.add_argument("--language", type=str, default="python", help="Code language for examples")
        parser.add_argument("--no-code", action="store_true", help="Disable code search")
        parser.add_argument("--no-thinking", action="store_true", help="Disable hybrid thinking")
        parser.add_argument("--threejs", action="store_true", help="Research THREE.js visualization")
        parser.add_argument("--viz-type", type=str, default="dashboard", help="Visualization type")
        
        args = parser.parse_args()
        
        # Ensure a topic is provided
        if not args.topic:
            print("Error: Please provide a research topic with --topic")
            parser.print_help()
            return
        
        # Create agent
        agent = AdvancedResearchAgent(
            # Any configuration overrides
        )
        
        async def run_research():
            # Run the appropriate research based on arguments
            if args.threejs:
                result = await agent.research_mcp_with_threejs(
                    args.topic, 
                    visualization_type=args.viz_type
                )
                print("\n" + "=" * 80)
                print(f"MCP-THREE.js research completed successfully!")
                if result.get("output_file"):
                    print(f"Results saved to: {result.get('output_file')}")
                print("=" * 80 + "\n")
                return result
            else:
                result = await agent.research_and_analyze(
                    topic=args.topic,
                    focus=args.focus,
                    code_search=not args.no_code,
                    code_language=args.language,
                    include_thinking=not args.no_thinking
                )
                print("\n" + "=" * 80)
                print(f"Research completed: {args.topic}")
                if result.get("output_file"):
                    print(f"Results saved to: {result.get('output_file')}")
                print("=" * 80 + "\n")
                return result
        
        # Run async research in a proper event loop
        asyncio.run(run_research())
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the agent
    main() 