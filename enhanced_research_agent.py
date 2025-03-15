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
"""

import os
import sys
import json
import time
import asyncio
import logging
import random
import hashlib
import uuid
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
    from src.vot1.perplexity_client import PerplexityClient
    logger.info("Successfully imported Perplexity client from src.vot1")
    perplexipy_installed = True
except ImportError:
    try:
        # Try relative import
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from perplexity_client import PerplexityClient
        logger.info("Successfully imported Perplexity client from local directory")
        perplexipy_installed = True
    except ImportError:
        logger.error("Perplexity client not installed")
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
    # Try importing from src.vot1
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.composio.client import ComposioClient
    from src.vot1.composio.enhanced_memory import EnhancedMemoryGraph
    from src.vot1.composio.memory_consolidation import MemoryConsolidationService
    from src.vot1.memory import MemoryManager
    logger.info("Successfully imported TRILOGY BRAIN from src.vot1")
    trilogy_brain_available = True
except ImportError:
    try:
        # Try relative imports
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from composio.memory_bridge import ComposioMemoryBridge
        from composio.client import ComposioClient
        from composio.enhanced_memory import EnhancedMemoryGraph
        from composio.memory_consolidation import MemoryConsolidationService
        from memory import MemoryManager
        logger.info("Successfully imported TRILOGY BRAIN from local directory")
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
        enable_trilogy_brain: bool = True,
        enable_memory_consolidation: bool = True,
        enable_autonomous_repair: bool = True,
        health_check_interval: int = 60  # Check system health every 60 seconds
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
            enable_memory_consolidation: Whether to enable memory consolidation
            enable_autonomous_repair: Whether to enable autonomous system repair
            health_check_interval: Interval for system health checks in seconds
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
        self.enable_memory_consolidation = enable_memory_consolidation and trilogy_brain_available
        self.enable_autonomous_repair = enable_autonomous_repair
        self.health_check_interval = health_check_interval
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a session ID
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._generate_id()}"
        
        # Initialize components
        self.components = {}
        
        # Initialize memory feedback system
        self.feedback_loops = []
        self.memory_consolidation_counter = 0
        self.memory_consolidation_threshold = 5  # Consolidate every 5 feedbacks
        self.claude_client = None
        self.perplexity_client = None
        
        # System health monitoring
        self.system_health = {
            "status": "initializing",
            "last_check": time.time(),
            "checks_performed": 0,
            "issues_detected": 0,
            "repairs_attempted": 0,
            "repairs_successful": 0,
            "components_status": {},
            "health_history": []
        }
        
        # Initialize state
        self.initialized = False
        self.missing_components = []
        
        # Model configuration - ALWAYS use Claude 3.7 Sonnet
        self.claude_model = "claude-3-7-sonnet-20250219"  # Latest Claude 3.7 Sonnet
        logger.info(f"Using Claude 3.7 Sonnet: {self.claude_model}")
        
        # Use the latest Perplexity model with online capabilities
        self.perplexity_model = "llama-3.1-sonar-large-128k-online"
        logger.info(f"Using Perplexity model: {self.perplexity_model}")
        
        # Enable hybrid thinking by default
        self.enable_hybrid_thinking = True
        self.enable_streaming = True
        
        # Research tracking
        self.research_status = {
            "started": False,
            "web_research": False,
            "code_analysis": False,
            "thinking": False,
            "results": False,
            "completed": False
        }
        
        # Memory storage
        self.memory_store = self._load_memory()
        
        # Health monitor task
        self.health_monitor_task = None
        
        # Initialize agent
        self._init_agent()
        
        # Start health monitoring if enabled
        if self.enable_autonomous_repair:
            self._start_health_monitoring()
    
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
                perplexity_client = PerplexityClient(
                    key=self.perplexity_api_key
                )
                self.components["perplexity"] = perplexity_client
                self.perplexity_client = perplexity_client
                self.system_health["components_status"]["perplexity"] = "operational"
                logger.info("Perplexity client initialized")
            else:
                self.missing_components.append("PerplexiPy")
                self.system_health["components_status"]["perplexity"] = "missing"
            
            # Initialize Claude client
            if anthropic_installed and self.anthropic_api_key:
                claude_client = anthropic.Anthropic(
                    api_key=self.anthropic_api_key
                )
                self.components["claude"] = claude_client
                self.claude_client = claude_client
                self.system_health["components_status"]["claude"] = "operational"
                logger.info("Claude client initialized")
            else:
                self.missing_components.append("Anthropic")
                self.system_health["components_status"]["claude"] = "missing"
            
            # Initialize GitHub client if token is available
            if self.github_token:
                # Store the GitHub token for now
                self.components["github"] = {"token": self.github_token}
                self.system_health["components_status"]["github"] = "configured"
                logger.info("GitHub access configured")
            else:
                self.missing_components.append("GITHUB_TOKEN")
                self.system_health["components_status"]["github"] = "missing"
            
            # Initialize Composio client if API key is available
            if self.composio_api_key and self.composio_mcp_url:
                try:
                    # For now, just record that Composio would be configured
                    self.components["composio"] = {
                        "api_key": self.composio_api_key,
                        "mcp_url": self.composio_mcp_url
                    }
                    self.system_health["components_status"]["composio"] = "configured"
                    logger.info("Composio access configured")
                except Exception as e:
                    logger.error(f"Error initializing Composio client: {e}")
                    self.missing_components.append("COMPOSIO_CLIENT")
                    self.system_health["components_status"]["composio"] = "error"
            else:
                if not self.composio_api_key:
                    self.missing_components.append("COMPOSIO_API_KEY")
                if not self.composio_mcp_url:
                    self.missing_components.append("COMPOSIO_MCP_URL")
                self.system_health["components_status"]["composio"] = "missing"
            
            # Initialize TRILOGY BRAIN memory system
            if self.enable_trilogy_brain and trilogy_brain_available:
                try:
                    # Create memory directory if it doesn't exist
                    os.makedirs(self.memory_path, exist_ok=True)
                    
                    # Record that TRILOGY BRAIN would be initialized
                    self.components["trilogy_brain"] = {
                        "status": "configured",
                        "memory_path": self.memory_path
                    }
                    self.system_health["components_status"]["trilogy_brain"] = "configured"
                    logger.info("TRILOGY BRAIN memory system configured")
                except Exception as e:
                    logger.error(f"Error initializing TRILOGY BRAIN: {e}")
                    self.missing_components.append("TRILOGY_BRAIN")
                    self.system_health["components_status"]["trilogy_brain"] = "error"
            else:
                if not trilogy_brain_available:
                    self.missing_components.append("TRILOGY_BRAIN_NOT_AVAILABLE")
                    self.system_health["components_status"]["trilogy_brain"] = "not_available"
                else:
                    self.system_health["components_status"]["trilogy_brain"] = "disabled"
            
            # Check if any components are missing
            if self.missing_components:
                logger.warning(f"Missing components: {', '.join(self.missing_components)}")
                logger.warning("Some features may be unavailable")
                self.system_health["status"] = "degraded"
            else:
                self.system_health["status"] = "operational"
            
            self.initialized = True
            self.system_health["last_check"] = time.time()
            self.system_health["checks_performed"] += 1
            logger.info("Agent initialization completed")
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error("Agent initialization failed")
            self.initialized = False
            self.system_health["status"] = "failed"
            self.system_health["last_check"] = time.time()
            self.system_health["checks_performed"] += 1
            self.system_health["issues_detected"] += 1
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
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            with open(memory_file, "w") as f:
                json.dump(self.memory_store, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    async def store_in_trilogy_brain(self, content: str, memory_type: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Store content in TRILOGY BRAIN memory system.
        
        Args:
            content: The content to store
            memory_type: Type of memory
            metadata: Additional metadata
            
        Returns:
            Memory ID if successful, None otherwise
        """
        if not self.enable_trilogy_brain or "memory_manager" not in self.components:
            return None
            
        if not metadata:
            metadata = {}
            
        metadata.update({
            "timestamp": time.time(),
            "session_id": self.session_id
        })
            
        try:
            memory_manager = self.components["memory_manager"]
            memory_id = await memory_manager.store_memory(
                content=content,
                memory_type=memory_type,
                metadata=metadata
            )
            return memory_id
        except Exception as e:
            logger.error(f"Error storing in TRILOGY BRAIN: {e}")
            return None
    
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
        
        # Also store in TRILOGY BRAIN if available (async, don't wait)
        if self.enable_trilogy_brain and "memory_manager" in self.components:
            asyncio.create_task(self.store_in_trilogy_brain(content, content_type, metadata))
        
        return memory_id
    
    async def retrieve_from_trilogy_brain(self, query: str, memory_types: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve memories from TRILOGY BRAIN using semantic search.
        
        Args:
            query: Search query
            memory_types: Types of memories to search for
            limit: Maximum number of results
            
        Returns:
            List of memory items
        """
        if not self.enable_trilogy_brain or "memory_manager" not in self.components:
            return []
            
        try:
            memory_manager = self.components["memory_manager"]
            memories = await memory_manager.retrieve_memories(
                query=query,
                memory_types=memory_types,
                limit=limit
            )
            return memories
        except Exception as e:
            logger.error(f"Error retrieving from TRILOGY BRAIN: {e}")
            return []
    
    async def retrieve_from_memory(self, query: str, content_types: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on semantic search.
        
        Args:
            query: Search query
            content_types: Types of content to search
            limit: Maximum number of results
            
        Returns:
            List of memory items
        """
        # First, try to use TRILOGY BRAIN if available
        if self.enable_trilogy_brain and "memory_manager" in self.components:
            trilogy_results = await self.retrieve_from_trilogy_brain(
                query=query,
                memory_types=content_types,
                limit=limit
            )
            
            if trilogy_results:
                return trilogy_results
        
        # Fall back to simple implementation if TRILOGY BRAIN is unavailable or returns no results
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
        Conduct deep web research using Perplexity with Composio Memory integration.
        
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
            # Check if we have any related memories that might be useful
            related_memories = []
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                related_memories = await self.retrieve_from_memory(
                    query=topic, 
                    content_types=["research_primary", "research_followup", "concept"],
                    limit=3
                )
            
            # Build context from related memories
            memory_context = ""
            if related_memories:
                memory_context = "Relevant information from previous research:\n\n"
                for i, memory in enumerate(related_memories, 1):
                    memory_context += f"Memory {i}:\n{memory.get('content', '')[:500]}...\n\n"
            
            # Craft research prompt
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
            
            {memory_context if memory_context else ''}
            """
            
            # Enhance prompt with hybrid thinking if bridge available
            enhanced_prompt = research_prompt
            if self.enable_trilogy_brain and "memory_bridge" in self.components:
                try:
                    memory_bridge = self.components["memory_bridge"]
                    enhanced_prompt = await memory_bridge.enhance_prompt(
                        prompt=research_prompt,
                        context_type="research",
                        max_memories=3
                    )
                except Exception as e:
                    logger.error(f"Error enhancing prompt with memory bridge: {e}")
            
            # Execute the research query
            research_results = await perplexity.query(
                enhanced_prompt,
                model=self.perplexity_model,
                stream=False,
                return_citations=True
            )
            
            # Extract content and citations
            research_content = research_results.get("text", "")
            citations = research_results.get("citations", [])
            
            # Store in TRILOGY BRAIN memory system
            research_id = None
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                research_id = await self.store_in_trilogy_brain(
                    content=research_content,
                    memory_type="research_primary",
                    metadata={
                        "topic": topic,
                        "focus": focus,
                        "depth": self.research_depth,
                        "citations": citations
                    }
                )
            
            # Fallback to local memory storage if TRILOGY BRAIN unavailable
            if not research_id:
                research_id = self.store_in_memory(
                    content=research_content,
                    content_type="research_primary",
                    metadata={
                        "topic": topic,
                        "focus": focus,
                        "source": "perplexity",
                        "query": research_prompt,
                        "has_citations": len(citations) > 0,
                        "citation_count": len(citations),
                        "timestamp": datetime.now().timestamp(),
                        "session_id": self.session_id
                    }
                )
            
            logger.info(f"Web research completed, stored with ID: {research_id}")
            
            # Generate follow-up questions using hybrid thinking
            followup_questions = await self._generate_followup_questions(research_content, topic)
            
            followup_results = {}
            followup_ids = []
            for question in followup_questions[:3]:  # Limit to 3 follow-up questions
                logger.info(f"Researching follow-up question: {question}")
                
                # Query perplexity for the follow-up question
                result = await perplexity.query(
                    question,
                    model=self.perplexity_model,
                    stream=False,
                    return_citations=True
                )
                
                follow_content = result.get("text", "")
                follow_citations = result.get("citations", [])
                
                followup_results[question] = {
                    "content": follow_content,
                    "citations": follow_citations
                }
                
                # Store follow-up research in memory
                followup_id = None
                if self.enable_trilogy_brain and "memory_manager" in self.components:
                    followup_id = await self.store_in_trilogy_brain(
                        content=follow_content,
                        memory_type="research_followup",
                        metadata={
                            "topic": topic,
                            "question": question,
                            "citations": follow_citations
                        }
                    )
                
                # Fallback to local memory storage
                if not followup_id:
                    followup_id = self.store_in_memory(
                        content=follow_content,
                    content_type="research_followup",
                    metadata={
                        "topic": topic,
                            "question": question,
                            "citations": follow_citations
                        }
                    )
                
                followup_ids.append(followup_id)
                
                # Create relationship between primary research and follow-up
                if self.enable_trilogy_brain and research_id and followup_id:
                    await self.create_memory_relationship(
                        source_id=research_id,
                        target_id=followup_id,
                        relationship_type="follow_up_research",
                        metadata={"question": question}
                    )
            
            # Compile results
            results = {
                "primary_research": research_content,
                "followup_research": followup_results,
                "topic": topic,
                "focus": focus,
                "research_id": research_id,
                "followup_ids": followup_ids,
                "citations": citations
            }
            
            self.research_status["web_research"] = "completed"
            return results
            
        except Exception as e:
            logger.error(f"Error during web research: {str(e)}")
            self.research_status["web_research"] = "failed"
            return {"error": str(e)}
    
    async def _generate_followup_questions(self, research_content: str, topic: str) -> List[str]:
        """
        Generate intelligent follow-up questions based on initial research.
        
        Uses Claude 3.7 Sonnet to analyze the research content and generate
        targeted, insightful questions that explore knowledge gaps, potential
        contradictions, and promising research directions.
        
        Args:
            research_content: The initial research content
            topic: The research topic
            
        Returns:
            List of follow-up questions
        """
        logger.info(f"Generating intelligent follow-up questions for: {topic}")
        
        # If Claude is not available, fall back to basic questions
        if not self.claude_client:
            logger.warning("Claude not available for generating follow-up questions, using basic fallback")
            
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
                        "protocol", "api", "mcp", "agi", "claude", "openai", "perplexity", 
                        "composio", "threejs", "visualization", "memory"]
            
            for term in terms:
                if term in tech_terms:
                    term_specific.append(f"How does {term} specifically contribute to {topic}?")
                    term_specific.append(f"What are the best {term} implementations for {topic}?")
            
            # Combine and shuffle to get diverse questions
            all_questions = questions + term_specific
            random.shuffle(all_questions)
            
            return all_questions[:6]  # Return max 6 questions
            
        try:
            # Prepare the prompt
            prompt = f"""Based on this initial research about "{topic}", generate 5-8 insightful follow-up questions.

The questions should:
1. Address knowledge gaps in the initial research
2. Explore potential contradictions or uncertainties
3. Probe deeper into the most promising areas
4. Cover technical implementation details where relevant
5. Address recent developments and future directions
6. Consider practical applications and challenges

Initial research:
{research_content[:3000]}

Generate diverse, specific questions that would significantly deepen understanding of this topic when answered.
"""

            # Use Claude to generate questions
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=1000,
                system="You are Claude 3.7 Sonnet, an AI assistant specialized in generating insightful research questions. Your task is to identify knowledge gaps and create targeted follow-up questions that would significantly deepen understanding when answered.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract questions from response
            questions_text = response.content[0].text
            
            # Parse questions line by line
            import re
            questions = []
            
            # Look for numbered or bulleted questions
            question_patterns = [
                r'^\s*\d+\.\s*(.+?)$',  # Numbered: 1. Question?
                r'^\s*\*\s*(.+?)$',     # Bullet: * Question?
                r'^\s*-\s*(.+?)$',      # Hyphen: - Question?
                r'^\s*[A-Z].*?\?$'      # Capitalized sentence ending with question mark
            ]
            
            for line in questions_text.split('\n'):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Try each pattern
                for pattern in question_patterns:
                    match = re.match(pattern, line)
                    if match:
                        # For the first 3 patterns, the question is in the first capture group
                        question = match.group(1) if len(match.groups()) > 0 else line
                        
                        # Ensure question ends with question mark
                        if not question.endswith('?'):
                            continue
                            
                        questions.append(question)
                        break
                
                # If no structured pattern found but line ends with '?', it might be a question
                if not any(re.match(pattern, line) for pattern in question_patterns) and line.endswith('?'):
                    questions.append(line)
            
            # If no questions were found using patterns, extract with a simple question mark regex
            if not questions:
                questions = re.findall(r'([A-Z][^.!?]*\?)', questions_text)
            
            # Ensure we have meaningful questions (not too short)
            questions = [q for q in questions if len(q) > 15]
            
            # Deduplicate questions
            questions = list(dict.fromkeys(questions))
            
            if not questions:
                logger.warning("Failed to extract questions from Claude response, using fallback")
                # Return some basic topical questions as fallback
                return [
                    f"What are the latest advancements in {topic}?",
                    f"What are the main technical challenges in implementing {topic}?",
                    f"How does {topic} compare to alternative approaches?",
                    f"What future developments are expected for {topic}?",
                    f"What practical applications exist for {topic}?"
                ]
            
            logger.info(f"Generated {len(questions)} intelligent follow-up questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}")
            # Return some basic questions as fallback
            return [
                f"What are the latest advancements in {topic}?",
                f"What are the technical challenges of {topic}?",
                f"How is {topic} implemented in practice?",
                f"What are the future directions for {topic}?"
            ]
    
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
        
        # Check if Composio client is available for enhanced GitHub search
        if "composio" in self.components and self.components["composio"]:
            try:
                composio_client = self.components["composio"]
                
                # Execute GitHub search via Composio MCP
                search_params = {
                    "q": f"{query} language:{language}" if language else query,
                    "sort": "stars",
                    "per_page": max_results
                }
                
                search_results = await composio_client.execute_tool(
                    "github",
                    "search_repositories",
                    params=search_params
                )
                
                # Process search results
                if search_results and isinstance(search_results, dict) and "items" in search_results:
                    code_results = []
                    
                    for repo in search_results["items"][:max_results]:
                        # Get repository details
                        repo_name = repo.get("full_name", "")
                        repo_url = repo.get("html_url", "")
                        repo_description = repo.get("description", "")
                        
                        # Get repository contents via Composio
                        try:
                            contents_params = {
                                "owner": repo_name.split("/")[0],
                                "repo": repo_name.split("/")[1],
                                "path": ""  # Root path
                            }
                            
                            contents = await composio_client.execute_tool(
                                "github",
                                "get_repository_content",
                                params=contents_params
                            )
                            
                            # Find relevant file(s)
                            relevant_files = []
                            if contents and isinstance(contents, list):
                                for item in contents:
                                    if item.get("type") == "file" and (
                                        not language or
                                        item.get("name", "").endswith(self._get_extension_for_language(language))
                                    ):
                                        relevant_files.append(item)
                            
                            # Get content of relevant files
                            for file in relevant_files[:2]:  # Limit to 2 files per repo
                                file_path = file.get("path", "")
                                file_url = file.get("html_url", "")
                                
                                # Get file content
                                file_params = {
                                    "owner": repo_name.split("/")[0],
                                    "repo": repo_name.split("/")[1],
                                    "path": file_path
                                }
                                
                                file_data = await composio_client.execute_tool(
                                    "github",
                                    "get_content",
                                    params=file_params
                                )
                                
                                if file_data and "content" in file_data:
                                    import base64
                                    
                                    # Decode base64 content
                                    content = base64.b64decode(file_data["content"]).decode("utf-8")
                                    
                                    # Add to results
                                    code_result = {
                                        "name": file.get("name", ""),
                                        "repo": repo_name,
                                        "repo_description": repo_description,
                                        "url": file_url,
                                        "language": language or self._detect_language(file.get("name", "")),
                                        "content": content
                                    }
                                    
                                    code_results.append(code_result)
                        
                        except Exception as e:
                            logger.error(f"Error getting repo contents: {e}")
                            continue
                    
                    # Store code snippets in memory
                    for i, result in enumerate(code_results):
                        code_id = None
                        
                        # Store in TRILOGY BRAIN if available
                        if self.enable_trilogy_brain and "memory_manager" in self.components:
                            code_id = await self.store_in_trilogy_brain(
                                content=result["content"],
                                memory_type="code_snippet",
                                metadata={
                                    "name": result["name"],
                                    "repo": result["repo"],
                                    "url": result["url"],
                                    "language": result["language"],
                                    "query": query
                                }
                            )
                        
                        # Fallback to local memory storage
                        if not code_id:
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
                        
                        code_results[i]["memory_id"] = code_id
                    
                    logger.info(f"GitHub code search completed via Composio, found {len(code_results)} results")
                    self.research_status["code_analysis"] = "completed"
                    
                    return code_results
            
            except Exception as e:
                logger.error(f"Error during GitHub search via Composio: {e}")
                # Fall back to standard implementation
        
        try:
            # Standard implementation using GitHub API directly
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
            
            # Use httpx for async HTTP requests
            import httpx
            
            async with httpx.AsyncClient() as client:
                # Search for repositories
                search_url = "https://api.github.com/search/code"
                response = await client.get(search_url, headers=headers, params=params)
                
                if response.status_code == 200:
                    search_data = response.json()
                    
                    # Process results
                    code_results = []
                    
                    for item in search_data.get("items", [])[:max_results]:
                        repo_name = item.get("repository", {}).get("full_name", "")
                        path = item.get("path", "")
                        url = item.get("html_url", "")
                        
                        # Get file content
                        content_url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
                        content_response = await client.get(content_url, headers=headers)
                        
                        if content_response.status_code == 200:
                            content_data = content_response.json()
                            
                            if "content" in content_data:
                                import base64
                                
                                # Decode base64 content
                                content = base64.b64decode(content_data["content"]).decode("utf-8")
                                
                                # Add to results
                                code_result = {
                                    "name": os.path.basename(path),
                                    "repo": repo_name,
                                    "url": url,
                                    "language": language or self._detect_language(path),
                                    "content": content
                                }
                                
                                code_results.append(code_result)
                    
                    # Store code snippets in memory
                    for i, result in enumerate(code_results):
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
                        code_results[i]["memory_id"] = code_id
                    
                    logger.info(f"GitHub code search completed, found {len(code_results)} results")
                    self.research_status["code_analysis"] = "completed"
                    
                    return code_results
                else:
                    logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                    return [{"error": f"GitHub API error: {response.status_code}"}]
                
        except Exception as e:
            logger.error(f"Error during GitHub search: {str(e)}")
            self.research_status["code_analysis"] = "failed"
            
            # Return mock results for demonstration purposes
            mock_results = [
                {
                    "name": f"example_{language}_implementation.{self._get_extension_for_language(language)}",
                    "repo": "example/repo",
                    "url": f"https://github.com/example/repo/blob/main/example_{language}_implementation.{self._get_extension_for_language(language)}",
                    "language": language or "python",
                    "content": f"# Example implementation for {query}\n\ndef main():\n    print('Implementing {query}')\n\nif __name__ == '__main__':\n    main()"
                },
                {
                    "name": f"advanced_{language}_example.{self._get_extension_for_language(language)}",
                    "repo": "advanced/repo",
                    "url": f"https://github.com/advanced/repo/blob/main/advanced_{language}_example.{self._get_extension_for_language(language)}",
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
            
            return mock_results
            
    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        extension = os.path.splitext(filename)[1].lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".rs": "rust"
        }
        
        return language_map.get(extension, "unknown")
    
    def _get_extension_for_language(self, language: str) -> str:
        """Get file extension for language"""
        language_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "go": ".go",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "rust": ".rs"
        }
        
        return language_map.get(language.lower(), "")
    
    async def analyze_with_claude(
        self, 
        topic: str, 
        research_results: Dict[str, Any], 
        analysis_type: str = "standard", 
        include_thinking: bool = True,
        visualization_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze research results using Claude 3.7 Sonnet's cognitive capabilities.
        
        Provides comprehensive analysis of research with multiple analysis types:
        - standard: Regular research analysis
        - brief: Concise key points
        - deep: In-depth exploration of implications and connections
        - threejs: Detailed THREE.js visualization guidance
        - technical: Technical implementation focus
        - creative: Creative applications and novel approaches
        - predictive: Future developments and trends
        
        Args:
            topic: The research topic
            research_results: The research results to analyze
            analysis_type: Type of analysis (standard, brief, deep, threejs, etc.)
            include_thinking: Whether to include hybrid thinking
            visualization_focus: Specific focus for visualization (when analysis_type is threejs)
            
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
                    content += f"### Question: {question}\n{answer}\n\n"
            
            # Include code examples if available
            if "code_search" in research_results and research_results["code_search"]:
                content += "## Code Examples\n\n"
                for i, code_item in enumerate(research_results["code_search"][:3], 1):  # Limit to 3 examples
                    if isinstance(code_item, dict) and "error" not in code_item:
                        code_name = code_item.get("name", f"Example {i}")
                        code_lang = code_item.get("language", "Unknown")
                        code_content = code_item.get("content", "")
                        
                        content += f"### Example {i}: {code_name} ({code_lang})\n```{code_lang.lower()}\n{code_content}\n```\n\n"
            
            # Configure analysis type
            analysis_config = {
                "brief": {
                    "prompt": f"Please analyze this research on {topic} and provide a brief summary of key points.",
                    "thinking_prompt": f"Let's think concisely about the research on {topic} to extract the most important points.",
                    "system_role": "You are Claude, a concise research analyst. Provide brief but insightful analysis."
                },
                "standard": {
                    "prompt": f"Please analyze this research on {topic} and provide a comprehensive analysis.",
                    "thinking_prompt": f"Let's analyze the research on {topic} systematically, identifying key findings, patterns, and implications.",
                    "system_role": "You are Claude, a research analyst. Provide balanced and comprehensive analysis."
                },
                "deep": {
                    "prompt": f"Please provide an in-depth analysis of this research on {topic}, identifying patterns, insights, connections, and broader implications.",
                    "thinking_prompt": f"Let's conduct a comprehensive analysis of the research on {topic}, exploring various dimensions, theoretical foundations, and potential applications.",
                    "system_role": "You are Claude, a deep research analyst. Provide extensive, multi-dimensional analysis that explores all aspects of the topic."
                },
                "threejs": {
                    "prompt": f"Analyze this research on {topic} and provide detailed guidance on creating an effective THREE.js visualization{' focused on ' + visualization_focus if visualization_focus else ''}.",
                    "thinking_prompt": f"Let's analyze this research from the perspective of creating an effective THREE.js visualization. Consider data structures, visual representations, user interactions, and technical implementation details.",
                    "system_role": "You are Claude, an expert in THREE.js visualization and WebGL graphics. Provide specialized analysis focused on THREE.js implementation."
                },
                "technical": {
                    "prompt": f"Provide a technical analysis of this research on {topic}, focusing on implementation details, architecture, performance considerations, and best practices.",
                    "thinking_prompt": f"Let's analyze the technical aspects of {topic}, focusing on concrete implementation approaches, technology stacks, and engineering considerations.",
                    "system_role": "You are Claude, a technical analyst specializing in software and systems engineering. Provide technically rigorous analysis."
                },
                "creative": {
                    "prompt": f"Analyze this research on {topic} from a creative perspective, exploring novel applications, unique approaches, and innovative possibilities.",
                    "thinking_prompt": f"Let's think creatively about {topic}, considering unconventional approaches and innovative applications that might not be immediately obvious.",
                    "system_role": "You are Claude, a creative analyst who specializes in identifying novel applications and unique approaches to technology."
                },
                "predictive": {
                    "prompt": f"Analyze this research on {topic} with a focus on future developments, emerging trends, and long-term implications.",
                    "thinking_prompt": f"Let's consider the future trajectory of {topic}, analyzing current signals, development patterns, and potential evolutionary paths.",
                    "system_role": "You are Claude, a strategic foresight analyst who specializes in identifying emerging trends and future developments."
                }
            }
            
            # Default to standard if analysis type not recognized
            if analysis_type not in analysis_config:
                logger.warning(f"Analysis type '{analysis_type}' not recognized, defaulting to 'standard'")
                analysis_type = "standard"
            
            config = analysis_config[analysis_type]
            
            # Add special instructions for THREE.js visualization
            if analysis_type == "threejs":
                # Add specialized THREE.js instructions based on visualization focus
                threejs_instructions = """
                Your analysis should include:
                
                1. Data Structure: How to organize and structure the data for effective visualization
                2. Visual Representation: Specific THREE.js techniques and approaches for representing the data
                3. User Interaction: How users should interact with the visualization
                4. Performance Optimization: How to ensure smooth performance
                5. Implementation Strategy: Step-by-step approach to building the visualization
                6. Code Architecture: How to structure the code for maintainability and extensibility
                7. Advanced Effects: Recommendations for enhancing visual appeal
                
                Include specific THREE.js components, techniques, and code patterns that would be most effective.
                """
                
                if visualization_focus:
                    # Customize based on visualization focus
                    focus_additions = {
                        "network": """
                        For network visualization, pay special attention to:
                        - Force-directed graph implementations in THREE.js
                        - Node and edge rendering techniques
                        - Dynamic data loading strategies
                        - Clustering and filtering approaches
                        - Performance optimization for large networks
                        - Visual cues for relationship types and strengths
                        """,
                        "dashboard": """
                        For dashboard visualization, pay special attention to:
                        - UI integration between THREE.js and HTML/CSS elements
                        - Multiple coordinated visualizations
                        - Data filtering and drill-down capabilities
                        - Performance optimization for interactive dashboards
                        - Responsive design considerations
                        - State management between visualization components
                        """,
                        "data": """
                        For data visualization, pay special attention to:
                        - Appropriate geometry selection for data types
                        - Color mapping and visual encoding strategies
                        - Scale and normalization approaches
                        - Transitions and animations for data changes
                        - Labels and annotations for data clarity
                        - Techniques for handling large datasets
                        """,
                        "immersive": """
                        For immersive visualization, pay special attention to:
                        - Camera controls and user navigation
                        - Advanced lighting and material effects
                        - Environmental elements and skyboxes
                        - Spatial audio integration possibilities
                        - Performance optimization for complex scenes
                        - Potential VR/AR compatibility considerations
                        """
                    }
                    
                    if visualization_focus.lower() in focus_additions:
                        threejs_instructions += focus_additions[visualization_focus.lower()]
                
                config["prompt"] += "\n\n" + threejs_instructions
            
            # Create system message
            system_message = config["system_role"]
            
            # Add thinking capabilities
            if include_thinking:
                system_message += "\n\nUse your hybrid thinking capabilities to explore the topic deeply before responding."
                prompt = f"{config['thinking_prompt']}\n\n{config['prompt']}\n\nResearch content:\n\n{content}"
            else:
                prompt = f"{config['prompt']}\n\nResearch content:\n\n{content}"
            
            # Call Claude API with hybrid thinking
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
            if include_thinking and hasattr(response, 'usage') and hasattr(response.usage, 'thinking_content'):
                thinking = response.usage.thinking_content
            
            analysis_content = response.content[0].text
            
            # For THREE.js analysis, extract code blocks
            code_blocks = []
            if analysis_type == "threejs":
                import re
                # Extract code blocks from response
                code_pattern = r"```(?:javascript|js|html|css)?\s*([\s\S]*?)```"
                matches = re.findall(code_pattern, analysis_content)
                code_blocks = [match.strip() for match in matches if match.strip()]
            
            result = {
                "analysis": analysis_content,
                "thinking": thinking,
                "analysis_type": analysis_type,
                "success": True
            }
            
            if code_blocks:
                result["code_blocks"] = code_blocks
            
            # Store analysis in memory
            memory_metadata = {
                "topic": topic,
                "timestamp": datetime.now().timestamp(),
                "session_id": self.session_id,
                "analysis_type": analysis_type
            }
            
            if visualization_focus:
                memory_metadata["visualization_focus"] = visualization_focus
            
            # Try to store in TRILOGY BRAIN first
            memory_id = await self.store_in_trilogy_brain(
                content=result["analysis"],
                memory_type="analysis",
                metadata=memory_metadata
            )
            
            # Fall back to local memory if needed
            if not memory_id:
                memory_id = self.store_in_memory(
                    content=result["analysis"],
                    content_type="analysis",
                    metadata=memory_metadata
                )
            
            result["analysis_id"] = memory_id
            
            # Add system feedback for continuous improvement
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                await self.add_system_feedback(
                    topic=topic,
                    analysis_type=analysis_type,
                    analysis_id=memory_id,
                    content_length=len(content),
                    has_explicit_thinking=thinking is not None
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Claude analysis: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error details: {error_details}")
            return {"error": str(e), "error_details": error_details}
    
    async def add_system_feedback(self, topic: str, analysis_type: str, analysis_id: str, content_length: int, has_explicit_thinking: bool) -> None:
        """
        Add system feedback to improve future analyses.
        
        Args:
            topic: Research topic
            analysis_type: Type of analysis
            analysis_id: ID of the analysis
            content_length: Length of analysis content
            has_explicit_thinking: Whether explicit thinking was used
        """
        try:
            feedback = {
                "id": self._generate_id(12),
                "type": "system_feedback",
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                        "topic": topic,
                "analysis_type": analysis_type,
                "analysis_id": analysis_id,
                "content_length": content_length,
                "has_explicit_thinking": has_explicit_thinking
            }
            
            # Store feedback in memory
            self.feedback_loops.append(feedback)
            
            # Store in TRILOGY BRAIN if available
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                feedback_content = f"Analysis feedback for topic '{topic}' ({analysis_type}): " \
                                 f"Analysis length: {content_length} chars, " \
                                 f"Explicit thinking: {'Yes' if has_explicit_thinking else 'No'}"
                
                await self.store_in_trilogy_brain(
                    content=feedback_content,
                    memory_type="system_feedback",
                    metadata=feedback
                )
            
            # Increment the feedback counter
            self.memory_consolidation_counter += 1
            
            # Trigger memory consolidation if threshold reached
            if self.enable_memory_consolidation and self.memory_consolidation_counter >= 5:
                self.memory_consolidation_counter = 0
                # Schedule consolidation without awaiting (run in background)
                asyncio.create_task(self.consolidate_memories())
        except Exception as e:
            logger.error(f"Error adding system feedback: {e}")

    async def consolidate_memories(self) -> Dict[str, Any]:
        """
        Consolidate memories to improve organization and reduce redundancy.
        This process helps the system learn from past operations and improve future performance.
        
        Returns:
            Dictionary with consolidation results
        """
        if not self.enable_memory_consolidation or "consolidation_service" not in self.components:
            return {"error": "Memory consolidation not available"}
            
        try:
            # Start consolidation process
            logger.info("Starting memory consolidation process")
            start_time = time.time()
            
            # Get recent memories to consolidate
            recent_memories = []
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                memory_manager = self.components["memory_manager"]
                recent_memories = await memory_manager.get_recent_memories(limit=50)
            
            # Fall back to local memory if needed
            if not recent_memories and self.feedback_loops:
                recent_memories = self.feedback_loops
            
            if not recent_memories:
                logger.info("No memories to consolidate")
                return {"status": "no_memories"}
            
            logger.info(f"Consolidating {len(recent_memories)} memories")
            
            # Group memories by type
            grouped_memories = {}
            for memory in recent_memories:
                if isinstance(memory, dict):
                    memory_type = memory.get("type", "unknown")
                    if memory_type not in grouped_memories:
                        grouped_memories[memory_type] = []
                    grouped_memories[memory_type].append(memory)
            
            # For each memory type, perform consolidation with Claude
            consolidation_results = {}
            
            for memory_type, memories in grouped_memories.items():
                if len(memories) < 3:  # Skip if too few memories
                    continue
                
                # Prepare context for Claude
                memory_context = "\n\n".join([
                    f"Memory {i+1}: " + json.dumps(memory) 
                    for i, memory in enumerate(memories[:10])  # Limit to 10 memories per type
                ])
                
                # Create system prompt for consolidation
                system_prompt = """You are Claude 3.7 Sonnet, assisting with memory consolidation for an advanced AI system.
                Your task is to analyze a set of memories and:
                1. Identify patterns, trends, and insights
                2. Suggest improvements to the system based on these patterns
                3. Create a consolidated summary that captures the essence of these memories
                
                Your analysis should be concise but comprehensive, focusing on actionable insights.
                """
                
                # Create user prompt
                user_prompt = f"""Please analyze these memory entries of type '{memory_type}':
                
                {memory_context}
                
                Based on these memories, please provide:
                1. A consolidated summary of key patterns and insights
                2. 3-5 concrete suggestions for improving system performance
                3. Any emerging trends that should be monitored
                """
                
                # Call Claude for consolidation
                if self.claude_client:
                    try:
                        response = self.claude_client.messages.create(
                            model=self.claude_model,
                            max_tokens=2000,
                            system=system_prompt,
                            messages=[
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.7
                        )
                        
                        consolidation_text = response.content[0].text
                        
                        # Store consolidation in memory
                        consolidation_id = None
                        if self.enable_trilogy_brain and "memory_manager" in self.components:
                            consolidation_id = await self.store_in_trilogy_brain(
                                content=consolidation_text,
                                memory_type=f"consolidated_{memory_type}",
                                metadata={
                                    "memory_count": len(memories),
                                    "memory_type": memory_type,
                                    "consolidation_timestamp": datetime.now().isoformat()
                                }
                            )
                        
                        # Store result
                        consolidation_results[memory_type] = {
                            "consolidation_id": consolidation_id,
                            "memory_count": len(memories),
                            "summary": consolidation_text[:200] + "..." if len(consolidation_text) > 200 else consolidation_text
                        }
                        
                    except Exception as e:
                        logger.error(f"Error consolidating memories of type {memory_type}: {e}")
                        consolidation_results[memory_type] = {"error": str(e)}
            
            # Calculate stats
            end_time = time.time()
            execution_time = end_time - start_time
            
            result = {
                "status": "success" if consolidation_results else "no_consolidation",
                "execution_time": execution_time,
                "memory_types_processed": list(consolidation_results.keys()),
                "consolidation_results": consolidation_results
            }
            
            logger.info(f"Memory consolidation completed in {execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")
            return {"error": str(e)}

    async def self_analyze(self) -> Dict[str, Any]:
        """
        Perform self-analysis to improve system performance.
        This method analyzes the agent's own operations and suggests improvements.
        
        Returns:
            Dictionary with self-analysis results
        """
        logger.info("Starting self-analysis")
        
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            # Collect statistics about recent operations
            stats = {
                        "session_id": self.session_id,
                "session_start": self.session_id.split("_")[1],
                "research_count": len([f for f in self.feedback_loops if f.get("type") == "system_feedback"]),
                "memory_count": len(self.memory_store) if hasattr(self.memory_store, "__len__") else "unknown",
                "missing_components": self.missing_components,
                "enabled_features": {
                    "trilogy_brain": self.enable_trilogy_brain,
                    "memory_consolidation": self.enable_memory_consolidation,
                    "hybrid_thinking": self.enable_hybrid_thinking
                }
            }
            
            # Prepare context for Claude
            context = f"""System Statistics:
            {json.dumps(stats, indent=2)}
            
            Recent Feedback Loop Entries:
            {json.dumps(self.feedback_loops[-10:], indent=2) if len(self.feedback_loops) > 0 else "No feedback entries"}
            """
            
            # Create system prompt for self-analysis
            system_prompt = """You are Claude 3.7 Sonnet, performing self-analysis for an advanced research agent.
            Your task is to analyze the system's operations and suggest improvements.
            
            Focus on:
            1. Identifying patterns in system performance
            2. Suggesting improvements to memory management
            3. Optimizing research and analysis workflows
            4. Enhancing hybrid thinking capabilities
            5. Improving feedback loop mechanisms
            
            Your analysis should be actionable and specific.
            """
            
            # Create user prompt
            user_prompt = f"""Please analyze the current state of the research agent system:
            
            {context}
            
            Based on this information, please provide:
            1. An assessment of current system performance
            2. 3-5 specific recommendations for system improvements
            3. Suggestions for enhancing the TRILOGY BRAIN memory system
            4. Potential new features or capabilities to develop
            """
            
            # Call Claude for self-analysis
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=3000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            analysis = response.content[0].text
            
            # Store self-analysis in memory
            analysis_id = None
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                analysis_id = await self.store_in_trilogy_brain(
                    content=analysis,
                    memory_type="self_analysis",
                    metadata={
                        "timestamp": datetime.now().isoformat(),
                        "session_id": self.session_id
                    }
                )
            
            result = {
                "status": "success",
                "self_analysis": analysis,
                "analysis_id": analysis_id,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Self-analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error during self-analysis: {e}")
            return {"error": str(e)}
    
    async def hybrid_thinking(self, prompt: str, context: Optional[str] = None, memory_types: List[str] = None, structured_output: bool = False) -> Dict[str, Any]:
        """
        Perform advanced hybrid thinking with Claude 3.7 Sonnet.
        
        This leverages Claude 3.7 Sonnet's enhanced cognitive capabilities for more
        sophisticated reasoning, exploration of multiple perspectives, and detailed analysis.
        
        Args:
            prompt: The prompt to think about
            context: Additional context
            memory_types: Types of memories to include
            structured_output: Whether to request structured JSON output
            
        Returns:
            Dictionary with thinking results
        """
        logger.info(f"Performing advanced hybrid thinking: {prompt[:50]}...")
        
        if not self.claude_client:
            logger.error("Claude client not initialized")
            return {"error": "Claude client not initialized"}
        
        try:
            # Retrieve relevant memories with improved semantic search
            memories = []
            memory_context = ""
            
            if memory_types and (self.memory_manager or self.enable_trilogy_brain):
                # First try TRILOGY BRAIN if available
                if self.enable_trilogy_brain and "memory_manager" in self.components:
                    memories = await self.retrieve_from_trilogy_brain(prompt, memory_types=memory_types, limit=10)
                    logger.info(f"Retrieved {len(memories)} memories from TRILOGY BRAIN")
                else:
                    # Fall back to local memory
                    memories = await self.retrieve_from_memory(prompt, content_types=memory_types, limit=10)
                    logger.info(f"Retrieved {len(memories)} memories from local storage")
            
                # Prepare memory context with improved formatting for better reasoning
                if memories:
                    memory_context = "## Relevant Prior Knowledge\n\n"
                    for i, memory in enumerate(memories, 1):
                        memory_type = memory.get('type', 'unknown')
                        memory_content = memory.get('content', '')
                        memory_meta = memory.get('metadata', {})
                        created_time = memory_meta.get('timestamp', 'unknown')
                        
                        # Format timestamp if it exists
                        if isinstance(created_time, (int, float)):
                            created_time = datetime.fromtimestamp(created_time).strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Add importance indicator if available
                        importance = memory_meta.get('importance', None)
                        importance_str = f" (Importance: {importance:.2f})" if importance is not None else ""
                        
                        memory_context += f"### Memory {i}: {memory_type.capitalize()}{importance_str}\n"
                        memory_context += f"**Created**: {created_time}\n\n"
                        memory_context += f"{memory_content[:2000]}"
                        if len(memory_content) > 2000:
                            memory_context += "...(truncated)..."
                        memory_context += "\n\n"
            
            # Construct improved system prompt that leverages Claude 3.7's capabilities
            system_prompt = """You are Claude 3.7 Sonnet, an advanced AI assistant with exceptional hybrid thinking abilities.
            
For this task, I'd like you to engage in thorough cognitive exploration before providing your final response.
Your thinking should demonstrate these key Claude 3.7 capabilities:

1. Break down complex problems into components with clear relationships
2. Consider multiple perspectives, methodologies, and conceptual frameworks
3. Identify potential challenges, limitations, and edge cases
4. Draw connections between diverse domains and concepts
5. Evaluate the strength of evidence and reasoning
6. Generate novel insights by combining different perspectives
7. Maintain epistemic humility by acknowledging areas of uncertainty

Begin with exploratory thinking where you actively consider multiple approaches.
Then provide a well-reasoned final response that reflects your deep analysis.

If any significant uncertainties or knowledge gaps exist, explicitly acknowledge them.
"""

            # Add structured output instructions if requested
            if structured_output:
                system_prompt += """
                
Your final output should be in the following structured JSON format:
{
  "exploratory_thinking": "Your detailed step-by-step exploration of the problem",
  "key_insights": ["List of the most important insights discovered"],
  "principal_conclusions": "Your primary conclusions based on analysis",
  "confidence_level": "A value from 0-1 indicating your confidence",
  "uncertainties": ["List of key areas of uncertainty"],
  "alternative_perspectives": ["List of alternative viewpoints considered"],
  "followup_directions": ["Promising directions for further exploration"]
}
"""
            
            # Combine prompt, context, and memories
            full_prompt = f"""# Task: {prompt}

{memory_context}

{context if context else ""}

Please think through this comprehensively using your advanced hybrid thinking capabilities.
"""
            
            # Make the API call with Claude 3.7 Sonnet
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            # Extract the content
            thinking_result = response.content[0].text
            
            # Process structured output if requested
            structured_data = None
            if structured_output:
                try:
                    # Try to extract JSON if it exists
                    import re
                    import json
                    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', thinking_result)
                    if json_match:
                        json_str = json_match.group(1)
                        structured_data = json.loads(json_str)
                    else:
                        # Try to extract as raw JSON
                        json_match = re.search(r'(\{[\s\S]*\})', thinking_result)
                        if json_match:
                            json_str = json_match.group(1)
                            structured_data = json.loads(json_str)
                except Exception as e:
                    logger.warning(f"Failed to parse structured output: {e}")
                    structured_data = {"error": "Failed to parse structured output"}
            
            # Generate a high-quality memory_id for retrieval
            memory_id = await self.store_in_trilogy_brain(
                content=thinking_result,
                memory_type="hybrid_thinking",
                metadata={
                    "prompt": prompt,
                    "memory_count": len(memories),
                    "structured": structured_output,
                    "model": self.claude_model,
                    "timestamp": datetime.now().timestamp(),
                    "session_id": self.session_id
                }
            )
            
            # If storage in TRILOGY BRAIN failed, fall back to local storage
            if not memory_id:
                memory_id = self.store_in_memory(
                    content=thinking_result,
                    content_type="hybrid_thinking",
                    metadata={
                        "prompt": prompt,
                        "memory_count": len(memories),
                        "structured": structured_output,
                        "model": self.claude_model
                    }
                )
            
            logger.info(f"Hybrid thinking completed, stored with ID: {memory_id}")
            
            result = {
                "thinking": thinking_result,
                "thinking_id": memory_id,
                "memory_count": len(memories)
            }
            
            if structured_data:
                result["structured_data"] = structured_data
            
            return result
            
        except Exception as e:
            logger.error(f"Error during hybrid thinking: {str(e)}")
            import traceback
            trace = traceback.format_exc()
            logger.error(f"Traceback: {trace}")
            return {"error": str(e), "traceback": trace}
    
    async def research_and_analyze(
        self, 
        topic: str, 
        focus: Optional[str] = None,
        code_search: bool = True,
        code_language: Optional[str] = None,
        include_thinking: bool = True,
        consolidate_memories: bool = True,
        analysis_type: str = "standard",
        generate_knowledge_graph: bool = False,
        graph_type: str = "standard",
        generate_visualization: bool = False,
        visualization_focus: Optional[str] = None,
        save_results: bool = True,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Comprehensive research and analysis on a topic with enhanced capabilities.
        
        Conducts web research, code search, and in-depth analysis with optional
        knowledge graph construction and THREE.js visualization guidance.
        
        Args:
            topic: The topic to research
            focus: Optional additional focus or aspect of the topic
            code_search: Whether to search for code examples
            code_language: Optional programming language for code examples
            include_thinking: Whether to include hybrid thinking
            consolidate_memories: Whether to consolidate memories at the end
            analysis_type: Type of analysis (standard, brief, deep, threejs, etc.)
            generate_knowledge_graph: Whether to generate a knowledge graph
            graph_type: Type of knowledge graph to generate 
            generate_visualization: Whether to generate THREE.js visualization guidance
            visualization_focus: Optional focus for visualization (network, dashboard, etc.)
            save_results: Whether to save results to disk
            output_format: Format for output files (json or markdown)
            
        Returns:
            Dictionary with research results
        """
        start_time = time.time()
        formatted_topic = self._format_topic_for_filename(topic)
        
        if not focus:
            full_topic = topic
        else:
            full_topic = f"{topic} - {focus}"
        
        logger.info(f"Starting research on '{full_topic}'")
        
        # Create session ID for this research
        self.session_id = str(uuid.uuid4())
        
        # Initialize results structure with new status fields
        results = {
            "topic": topic,
            "focus": focus,
            "full_topic": full_topic,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "status": {
                "web_research": "pending",
                "followup_research": "pending",
                "code_search": "not_requested" if not code_search else "pending",
                "analysis": "pending",
                "knowledge_graph": "not_requested" if not generate_knowledge_graph else "pending",
                "visualization": "not_requested" if not generate_visualization else "pending",
                "memory_consolidation": "not_requested" if not consolidate_memories else "pending"
            }
        }
        
        try:
            # Step 1: Primary web research
            logger.info(f"Conducting web research on '{full_topic}'")
            web_results = await self.conduct_web_research(topic, focus=focus)
            
            if "error" in web_results:
                logger.error(f"Web research failed: {web_results['error']}")
                results["status"]["web_research"] = "error"
                results["web_research_error"] = web_results["error"]
            else:
                results["primary_research"] = web_results["content"]
                results["status"]["web_research"] = "completed"
                
                # Store primary research in memory
                primary_research_id = await self.store_in_trilogy_brain(
                    content=web_results["content"],
                    memory_type="research",
                    metadata={
                        "topic": topic,
                        "focus": focus,
                        "source": "web_research",
                        "timestamp": datetime.now().timestamp(),
                        "session_id": self.session_id
                    }
                )
                
                results["primary_research_id"] = primary_research_id
            
            # Step 2: Generate follow-up questions
            logger.info(f"Generating follow-up questions for '{full_topic}'")
            if "primary_research" in results:
                followup_questions = await self._generate_followup_questions(
                    topic=full_topic, 
                    content=results["primary_research"]
                )
                
                results["followup_questions"] = followup_questions
                
                # Step 3: Research follow-up questions
                followup_results = {}
                
                for i, question in enumerate(followup_questions):
                    logger.info(f"Researching follow-up question {i+1}/{len(followup_questions)}: {question}")
                    question_result = await self.conduct_web_research(question)
                    
                    if "error" not in question_result:
                        followup_results[question] = question_result["content"]
                        
                        # Store followup research in memory
                        await self.store_in_trilogy_brain(
                            content=question_result["content"],
                            memory_type="research",
                            metadata={
                                "topic": topic,
                                "focus": focus,
                                "question": question,
                                "source": "followup_research",
                                "timestamp": datetime.now().timestamp(),
                                "session_id": self.session_id
                            }
                        )
                
                results["followup_research"] = followup_results
                results["status"]["followup_research"] = "completed"
            else:
                results["status"]["followup_research"] = "skipped"
            
            # Step 4: Code search (if requested)
            if code_search:
                logger.info(f"Searching for code examples related to '{full_topic}'")
                code_results = await self.search_github_code(topic, language=code_language)
                
                if isinstance(code_results, list) and len(code_results) > 0:
                    results["code_search"] = code_results
                    results["status"]["code_search"] = "completed"
                    
                    # Store code examples in memory
                    for i, code_item in enumerate(code_results):
                        if isinstance(code_item, dict) and "content" in code_item:
                            await self.store_in_trilogy_brain(
                                content=code_item["content"],
                                memory_type="code",
                                metadata={
                                    "topic": topic,
                                    "language": code_item.get("language", "unknown"),
                                    "name": code_item.get("name", f"Example {i+1}"),
                                    "source": "github",
                                    "timestamp": datetime.now().timestamp(),
                                    "session_id": self.session_id
                                }
                            )
                else:
                    logger.warning(f"No code examples found for '{full_topic}'")
                    results["code_search"] = []
                    results["status"]["code_search"] = "no_results"
            
            # Step 5: Analyze with Claude
            logger.info(f"Analyzing research results for '{full_topic}'")
            
            # Check if we need a specialized visualization analysis
            effective_analysis_type = analysis_type
            if generate_visualization and analysis_type != "threejs":
                logger.info(f"Using threejs analysis type for visualization guidance")
                effective_analysis_type = "threejs"
            
            analysis_results = await self.analyze_with_claude(
                topic=full_topic,
                research_results=results,
                analysis_type=effective_analysis_type,
                include_thinking=include_thinking,
                visualization_focus=visualization_focus
            )
            
            if "error" in analysis_results:
                logger.error(f"Analysis failed: {analysis_results['error']}")
                results["status"]["analysis"] = "error"
                results["analysis_error"] = analysis_results["error"]
            else:
                results["analysis"] = analysis_results["analysis"]
                
                if "thinking" in analysis_results and analysis_results["thinking"]:
                    results["analysis_thinking"] = analysis_results["thinking"]
                
                if "analysis_id" in analysis_results:
                    results["analysis_id"] = analysis_results["analysis_id"]
                
                if "code_blocks" in analysis_results:
                    results["visualization_code_blocks"] = analysis_results["code_blocks"]
                
                results["status"]["analysis"] = "completed"
            
            # Step 6: Generate knowledge graph if requested
            if generate_knowledge_graph:
                logger.info(f"Generating knowledge graph for '{full_topic}'")
                
                graph_results = await self.construct_knowledge_graph(
                    topic=full_topic,
                    research_results=results,
                    analysis_results=analysis_results if "error" not in analysis_results else None,
                    graph_type=graph_type
                )
                
                if "error" in graph_results:
                    logger.error(f"Knowledge graph generation failed: {graph_results['error']}")
                    results["status"]["knowledge_graph"] = "error"
                    results["knowledge_graph_error"] = graph_results["error"]
                else:
                    results["knowledge_graph"] = graph_results["knowledge_graph"]
                    
                    if "graph_id" in graph_results:
                        results["knowledge_graph_id"] = graph_results["graph_id"]
                    
                    results["status"]["knowledge_graph"] = "completed"
            
            # Step 7: Generate specialized THREE.js visualization guidance if requested
            if generate_visualization and effective_analysis_type != "threejs":
                logger.info(f"Generating THREE.js visualization guidance for '{full_topic}'")
                
                viz_analysis = await self.analyze_with_claude(
                    topic=full_topic,
                    research_results=results,
                    analysis_type="threejs",
                    include_thinking=include_thinking,
                    visualization_focus=visualization_focus
                )
                
                if "error" in viz_analysis:
                    logger.error(f"Visualization guidance failed: {viz_analysis['error']}")
                    results["status"]["visualization"] = "error"
                    results["visualization_error"] = viz_analysis["error"]
                else:
                    results["visualization_guidance"] = viz_analysis["analysis"]
                    
                    if "thinking" in viz_analysis and viz_analysis["thinking"]:
                        results["visualization_thinking"] = viz_analysis["thinking"]
                    
                    if "code_blocks" in viz_analysis:
                        results["visualization_code_blocks"] = viz_analysis["code_blocks"]
                    
                    if "analysis_id" in viz_analysis:
                        results["visualization_guidance_id"] = viz_analysis["analysis_id"]
                    
                    results["status"]["visualization"] = "completed"
            elif generate_visualization:
                # Analysis was already done with threejs type
                results["status"]["visualization"] = "completed"
                # Copy the relevant parts from the analysis if needed
                if "code_blocks" in analysis_results and "visualization_code_blocks" not in results:
                    results["visualization_code_blocks"] = analysis_results["code_blocks"]
            
            # Generate complete THREE.js visualization code if we have a knowledge graph
            if generate_visualization and generate_knowledge_graph and "knowledge_graph" in results:
                logger.info(f"Generating complete THREE.js visualization code for knowledge graph")
                
                visualization_options = {
                    "backgroundColor": "#111133",
                    "useForceDirectedLayout": True,
                    "enableLabels": True,
                    "colorByGroup": True,
                    "usePostprocessing": True
                }
                
                if visualization_focus:
                    # Customize visualization options based on focus
                    if visualization_focus.lower() == "network":
                        visualization_options.update({
                            "backgroundColor": "#000022",
                            "animateEdges": True,
                            "useForceDirectedLayout": True
                        })
                    elif visualization_focus.lower() == "dashboard":
                        visualization_options.update({
                            "backgroundColor": "#222222",
                            "useForceDirectedLayout": False,
                            "enableInteraction": True,
                            "showLegend": True
                        })
                    elif visualization_focus.lower() == "immersive":
                        visualization_options.update({
                            "backgroundColor": "#000000",
                            "usePostprocessing": True,
                            "enableProgressiveLoading": True,
                            "useEnvironmentMap": True
                        })
                
                viz_code_results = await self.generate_threejs_visualization(
                    knowledge_graph=results["knowledge_graph"],
                    visualization_options=visualization_options
                )
                
                if "error" in viz_code_results:
                    logger.error(f"THREE.js code generation failed: {viz_code_results['error']}")
                    results["threejs_code_error"] = viz_code_results["error"]
                else:
                    results["threejs_visualization"] = viz_code_results["visualization"]
                    logger.info(f"Successfully generated THREE.js visualization code for knowledge graph")
            
            # Step 8: Create relationships between research, code, and analysis in TRILOGY BRAIN
            if self.enable_trilogy_brain and "memory_manager" in self.components:
                try:
                    # Create relationships between primary research and followup research
                    if "primary_research_id" in results:
                        primary_id = results["primary_research_id"]
                        
                        # Connect to follow-up questions
                        for i, question in enumerate(results.get("followup_questions", [])):
                            question_id = await self.store_in_trilogy_brain(
                                content=question,
                                memory_type="question",
                                metadata={
                                    "topic": topic,
                                    "focus": focus,
                                    "index": i,
                                    "timestamp": datetime.now().timestamp(),
                                    "session_id": self.session_id
                                }
                            )
                            
                            if question_id:
                                await self.create_memory_relationship(
                                    source_id=primary_id,
                                    target_id=question_id,
                                    relationship_type="generated_question",
                                    metadata={"topic": topic, "index": i}
                                )
                        
                        # Connect to analysis
                        if "analysis_id" in results:
                            await self.create_memory_relationship(
                                source_id=primary_id,
                                target_id=results["analysis_id"],
                                relationship_type="analyzed",
                                metadata={"topic": topic}
                            )
                        
                        # Connect to knowledge graph
                        if "knowledge_graph_id" in results:
                            await self.create_memory_relationship(
                                source_id=primary_id,
                                target_id=results["knowledge_graph_id"],
                                relationship_type="generated_graph",
                                metadata={"topic": topic}
                            )
                    
                    logger.info("Created relationships between research components in TRILOGY BRAIN")
                except Exception as e:
                    logger.error(f"Error creating relationships in TRILOGY BRAIN: {e}")
            
            # Step 9: Consolidate memories if requested
            if consolidate_memories and self.enable_trilogy_brain and "memory_manager" in self.components:
                logger.info(f"Consolidating memories for '{full_topic}'")
                try:
                    await self.consolidate_session_memories(self.session_id, topic)
                    results["status"]["memory_consolidation"] = "completed"
                except Exception as e:
                    logger.error(f"Error consolidating memories: {e}")
                    results["status"]["memory_consolidation"] = "error"
                    results["memory_consolidation_error"] = str(e)
            
            # Calculate total time
            results["execution_time_seconds"] = time.time() - start_time
            
            # Save results if requested
            if save_results:
                self._save_results(results, formatted_topic, output_format)
            
            # Add completion status
            results["completed"] = True
            
            return results
        
        except Exception as e:
            logger.error(f"Error in research process: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Save partial results
            results["error"] = str(e)
            results["completed"] = False
            results["error_details"] = traceback.format_exc()
            results["execution_time_seconds"] = time.time() - start_time
            
            if save_results:
                self._save_results(results, formatted_topic, output_format)
            
            return results
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename"""
        # Remove characters that aren't alphanumerics, underscores, or hyphens
        # Replace spaces with underscores
        return ''.join(c if c.isalnum() or c in '-_' else '_' for c in name.replace(' ', '_'))
    
    async def _generate_final_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a final report from research results"""
        # Use TRILOGY BRAIN if available for generating the report
        if self.enable_trilogy_brain and "memory_bridge" in self.components:
            try:
                memory_bridge = self.components["memory_bridge"]
                
                # Prepare topic and focus
                topic = results.get("topic", "Unknown Topic")
                focus = results.get("focus", "General")
                
                # Get the best available summary
                summary = ""
                if "hybrid_thinking" in results and results["hybrid_thinking"] and "thinking" in results["hybrid_thinking"]:
                    summary = results["hybrid_thinking"]["thinking"]
                elif "research_analysis" in results and results["research_analysis"] and "analysis" in results["research_analysis"]:
                    summary = results["research_analysis"]["analysis"]
                elif "web_research" in results and "primary_research" in results["web_research"]:
                    primary_research = results["web_research"]["primary_research"]
                    if isinstance(primary_research, str):
                        summary = primary_research
                
                # Get code examples
                code_examples = []
                if "code_search" in results and results["code_search"]:
                    for code in results["code_search"]:
                        if isinstance(code, dict):
                            code_examples.append({
                                "name": code.get("name", "Unknown"),
                                "language": code.get("language", "Unknown"),
                                "snippet": code.get("content", "")[:500] + "..." if len(code.get("content", "")) > 500 else code.get("content", "")
                            })
                
                # Use memory bridge to enhance the report
                thinking_prompt = f"""Based on the research on "{topic}" with focus on "{focus}", 
                create a comprehensive final report that synthesizes:
                
                1. Key findings and insights
                2. Technical details and implementation considerations
                3. Practical applications and use cases
                4. Limitations and challenges
                5. Future directions and opportunities
                
                Provide a thorough yet concise summary that captures the most important information from the research.
                """
                
                report_thinking = await memory_bridge.perform_hybrid_thinking(
                    prompt=thinking_prompt,
                    context=summary[:8000],
                    memory_types=["research", "analysis", "hybrid_thinking"],
                    max_tokens=self.max_thinking_tokens
                )
                
                # Store the report thinking in memory
                report_thinking_content = report_thinking.get("thinking", "")
                report_thinking_id = None
                
                if report_thinking_content:
                    report_thinking_id = await self.store_in_trilogy_brain(
                        content=report_thinking_content,
                        memory_type="report_thinking",
                        metadata={
                            "topic": topic,
                            "focus": focus
                        }
                    )
                
                # Create the report
                report = {
                    "title": f"Research Report: {topic}",
                    "focus": focus,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "summary": report_thinking_content if report_thinking_content else summary,
                    "web_research_summary": results.get("web_research", {}).get("primary_research", "")[:1000] + "..." 
                                          if isinstance(results.get("web_research", {}).get("primary_research", ""), str) else "",
                    "code_examples": code_examples
                }
                
                # Store the report in memory
                report_id = await self.store_in_trilogy_brain(
                    content=json.dumps(report, indent=2),
                    memory_type="research_report",
                    metadata={
                        "topic": topic,
                        "focus": focus
                    }
                )
                
                # Create relationships between report and other elements
                if "memory_graph" in self.components and report_id:
                    memory_graph = self.components["memory_graph"]
                    
                    # Relate report to research
                    if "web_research" in results and "research_id" in results["web_research"]:
                        research_id = results["web_research"]["research_id"]
                        await self.create_memory_relationship(
                            source_id=report_id,
                            target_id=research_id,
                            relationship_type="report_from_research",
                            metadata={"topic": topic}
                        )
                    
                    # Relate report to analysis
                    if "research_analysis" in results and "analysis_id" in results["research_analysis"]:
                        analysis_id = results["research_analysis"]["analysis_id"]
                        await self.create_memory_relationship(
                            source_id=report_id,
                            target_id=analysis_id,
                            relationship_type="report_from_analysis",
                            metadata={"topic": topic}
                        )
                    
                    # Relate report to thinking
                    if report_thinking_id:
                        await self.create_memory_relationship(
                            source_id=report_id,
                            target_id=report_thinking_id,
                            relationship_type="report_from_thinking",
                            metadata={"topic": topic}
                        )
                
                report["report_id"] = report_id
                return report
                
            except Exception as e:
                logger.error(f"Error generating enhanced report: {e}")
                # Fall back to standard implementation
        
        # Standard implementation
        report = {
            "title": f"Research Report: {results['topic']}",
            "focus": results.get("focus", "General"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": results.get("hybrid_thinking", {}).get("thinking", "No hybrid thinking available.") 
                      if "hybrid_thinking" in results else 
                      results.get("research_analysis", {}).get("analysis", "No analysis available."),
            "web_research_summary": results.get("web_research", {}).get("primary_research", "")[:1000] + "..."
                                   if isinstance(results.get("web_research", {}).get("primary_research", ""), str) else "",
            "code_examples": [
                {
                    "name": code.get("name", "Unknown"),
                    "language": code.get("language", "Unknown"),
                    "snippet": code.get("content", "")[:500] + "..." if len(code.get("content", "")) > 500 else code.get("content", "")
                }
                for code in results.get("code_search", [])
                if isinstance(code, dict)
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
            if self.components["perplexity"]:
                research_query = f"Latest THREE.js techniques for {visualization_type} visualizations, include performance optimization, responsive design, integration with data sources, and best practices for user interaction"
                
                research_response = await self.components["perplexity"].query(
                    research_query,
                    stream=False
                )
                
                research = research_response["text"] if "text" in research_response else ""
                
                # Step 2: Research implementation examples
                implementation_query = f"Detailed implementation examples for {visualization_type} visualizations with THREE.js, including code structure, shader techniques, animation approaches, performance considerations, and user interaction patterns"
                
                implementation_response = await self.components["perplexity"].query(
                    implementation_query,
                    stream=False
                )
                
                implementation_examples = implementation_response["text"] if "text" in implementation_response else ""
                
                # Step 3: Generate custom code example
                code_query = f"Provide a complete modern THREE.js visualization for a {visualization_type} with clean, modular code structure using r160 or newer. The code should be optimized for performance and include interactive elements."
                
                code_response = await self.components["perplexity"].query(
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
                if self.components["memory_manager"]:
                    memory_id = await self.components["memory_manager"].store_memory(
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
        if self.components["memory_manager"]:
            memory_id = await self.components["memory_manager"].store_memory(
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

    async def create_memory_relationship(self, source_id: str, target_id: str, relationship_type: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Create a relationship between two memory items.
        
        Args:
            source_id: Source memory ID
            target_id: Target memory ID
            relationship_type: Type of relationship
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enable_trilogy_brain or "memory_graph" not in self.components:
            return False
            
        try:
            memory_graph = self.components["memory_graph"]
            success = await memory_graph.create_relationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                metadata=metadata or {}
            )
            return success
        except Exception as e:
            logger.error(f"Error creating memory relationship: {e}")
            return False
            
    def _start_health_monitoring(self):
        """Start autonomous system health monitoring."""
        if not self.enable_autonomous_repair:
            logger.info("Autonomous repair disabled, health monitoring not started")
            return
            
        try:
            # Create asyncio task for health monitoring
            loop = asyncio.get_event_loop()
            self.health_monitor_task = loop.create_task(self._health_monitor_loop())
            logger.info(f"System health monitoring started (interval: {self.health_check_interval}s)")
        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")
    
    def _stop_health_monitoring(self):
        """Stop autonomous system health monitoring."""
        if self.health_monitor_task and not self.health_monitor_task.done():
            self.health_monitor_task.cancel()
            logger.info("System health monitoring stopped")
    
    async def _health_monitor_loop(self):
        """
        Continuous health monitoring loop.
        Checks system health periodically and attempts repairs when issues are detected.
        """
        logger.info("Health monitoring loop started")
        
        try:
            while True:
                # Perform health check
                health_report = await self.check_system_health()
                
                # Stream health data to TRILOGY BRAIN if available
                await self._stream_health_data(health_report)
                
                # If issues detected, attempt repair
                if health_report["status"] != "operational" and self.enable_autonomous_repair:
                    repair_success = await self.repair_system()
                    if repair_success:
                        logger.info("Autonomous system repair successful")
                    else:
                        logger.warning("Autonomous system repair unsuccessful")
                
                # Wait for next check
                await asyncio.sleep(self.health_check_interval)
                
        except asyncio.CancelledError:
            logger.info("Health monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in health monitoring loop: {e}")
            # Try to restart the monitoring
            logger.info("Attempting to restart health monitoring...")
            loop = asyncio.get_event_loop()
            self.health_monitor_task = loop.create_task(self._health_monitor_loop())
    
    async def _stream_health_data(self, health_data: Dict[str, Any]) -> bool:
        """
        Stream health data to TRILOGY BRAIN for continuous monitoring.
        
        Args:
            health_data: Current health status and metrics
            
        Returns:
            True if successfully streamed, False otherwise
        """
        if not self.enable_trilogy_brain or "trilogy_brain" not in self.components:
            return False
            
        try:
            # Create a summary of the health data
            health_summary = {
                "timestamp": datetime.now().isoformat(),
                "status": health_data["status"],
                "component_status": health_data["components_status"],
                "metrics": {
                    "checks": health_data["checks_performed"],
                    "issues": health_data["issues_detected"],
                    "repairs": health_data["repairs_attempted"],
                    "successful_repairs": health_data["repairs_successful"]
                }
            }
            
            # Stream to TRILOGY BRAIN
            memory_id = await self.store_in_trilogy_brain(
                content=json.dumps(health_summary),
                memory_type="system_health",
                metadata={
                    "status": health_data["status"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return memory_id is not None
            
        except Exception as e:
            logger.error(f"Failed to stream health data: {e}")
            return False
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Check the health of all system components and dependencies.
        
        Returns:
            Dictionary with health status for each component
        """
        logger.info("Checking system health...")
        
        health_check = {
            "timestamp": datetime.now().isoformat(),
            "status": "operational",
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
        # Update system health record
        self.system_health["last_check"] = time.time()
        self.system_health["checks_performed"] += 1
        
        # Check Perplexity client
        if "perplexity" in self.components:
            try:
                # Simple test for connectivity
                perplexity_operational = self.perplexity_client is not None
                health_check["components"]["perplexity"] = "operational" if perplexity_operational else "error"
                self.system_health["components_status"]["perplexity"] = health_check["components"]["perplexity"]
                
                if not perplexity_operational:
                    issue = "Perplexity client instantiated but not operational"
                    health_check["issues"].append(issue)
                    health_check["recommendations"].append("Reinitialize Perplexity client")
                    self.system_health["issues_detected"] += 1
                    health_check["status"] = "degraded"
            except Exception as e:
                health_check["components"]["perplexity"] = "error"
                self.system_health["components_status"]["perplexity"] = "error"
                health_check["issues"].append(f"Perplexity error: {str(e)}")
                health_check["recommendations"].append("Reinstall PerplexiPy or check API key")
                self.system_health["issues_detected"] += 1
                health_check["status"] = "degraded"
        else:
            health_check["components"]["perplexity"] = "missing"
            self.system_health["components_status"]["perplexity"] = "missing"
            health_check["issues"].append("Perplexity client not initialized")
            health_check["recommendations"].append("Install PerplexiPy and configure API key")
            self.system_health["issues_detected"] += 1
            health_check["status"] = "degraded"
        
        # Check Claude client
        if "claude" in self.components:
            try:
                # Simple test for connectivity
                claude_operational = self.claude_client is not None
                health_check["components"]["claude"] = "operational" if claude_operational else "error"
                self.system_health["components_status"]["claude"] = health_check["components"]["claude"]
                
                if not claude_operational:
                    issue = "Claude client instantiated but not operational"
                    health_check["issues"].append(issue)
                    health_check["recommendations"].append("Reinitialize Claude client")
                    self.system_health["issues_detected"] += 1
                    health_check["status"] = "degraded"
            except Exception as e:
                health_check["components"]["claude"] = "error"
                self.system_health["components_status"]["claude"] = "error"
                health_check["issues"].append(f"Claude error: {str(e)}")
                health_check["recommendations"].append("Reinstall Anthropic package or check API key")
                self.system_health["issues_detected"] += 1
                health_check["status"] = "degraded"
        else:
            health_check["components"]["claude"] = "missing"
            self.system_health["components_status"]["claude"] = "missing"
            health_check["issues"].append("Claude client not initialized")
            health_check["recommendations"].append("Install Anthropic package and configure API key")
            self.system_health["issues_detected"] += 1
            health_check["status"] = "degraded"
        
        # Check TRILOGY BRAIN
        if "trilogy_brain" in self.components:
            try:
                trilogy_status = self.components["trilogy_brain"]["status"]
                health_check["components"]["trilogy_brain"] = trilogy_status
                self.system_health["components_status"]["trilogy_brain"] = trilogy_status
                
                if trilogy_status != "operational":
                    issue = f"TRILOGY BRAIN status: {trilogy_status}"
                    health_check["issues"].append(issue)
                    health_check["recommendations"].append("Initialize TRILOGY BRAIN memory system")
                    self.system_health["issues_detected"] += 1
                    health_check["status"] = "degraded"
            except Exception as e:
                health_check["components"]["trilogy_brain"] = "error"
                self.system_health["components_status"]["trilogy_brain"] = "error"
                health_check["issues"].append(f"TRILOGY BRAIN error: {str(e)}")
                health_check["recommendations"].append("Check TRILOGY BRAIN configuration")
                self.system_health["issues_detected"] += 1
                health_check["status"] = "degraded"
        else:
            health_check["components"]["trilogy_brain"] = "missing"
            self.system_health["components_status"]["trilogy_brain"] = "missing"
            health_check["issues"].append("TRILOGY BRAIN not configured")
            health_check["recommendations"].append("Initialize TRILOGY BRAIN memory system")
            self.system_health["issues_detected"] += 1
            health_check["status"] = "degraded"
        
        # Update overall system health
        self.system_health["status"] = health_check["status"]
        self.system_health["health_history"].append({
            "timestamp": datetime.now().isoformat(),
            "status": health_check["status"],
            "issues_count": len(health_check["issues"])
        })
        
        # Keep only the last 100 health checks in history
        if len(self.system_health["health_history"]) > 100:
            self.system_health["health_history"] = self.system_health["health_history"][-100:]
        
        logger.info(f"System health check completed. Status: {health_check['status']}")
        if health_check["issues"]:
            for i, issue in enumerate(health_check["issues"]):
                logger.warning(f"Issue {i+1}: {issue}")
                logger.info(f"Recommendation: {health_check['recommendations'][i]}")
        
        return health_check
    
    async def repair_system(self) -> bool:
        """
        Attempt to repair system issues autonomously.
        
        Returns:
            True if repairs were successful, False otherwise
        """
        if not self.enable_autonomous_repair:
            logger.warning("Autonomous repair disabled")
            return False
            
        logger.info("Attempting autonomous system repair...")
        self.system_health["repairs_attempted"] += 1
        
        repair_success = True
        
        # Try to fix Perplexity
        if self.system_health["components_status"]["perplexity"] != "operational":
            logger.info("Attempting to repair Perplexity client...")
            if perplexipy_installed and self.perplexity_api_key:
                try:
                    self.perplexity_client = PerplexityClient(
                        key=self.perplexity_api_key
                    )
                    self.components["perplexity"] = self.perplexity_client
                    self.system_health["components_status"]["perplexity"] = "operational"
                    logger.info("Perplexity client repaired successfully")
                except Exception as e:
                    logger.error(f"Failed to repair Perplexity client: {e}")
                    repair_success = False
            else:
                logger.warning("Cannot repair Perplexity client: PerplexiPy not installed or API key missing")
                repair_success = False
        
        # Try to fix Claude
        if self.system_health["components_status"]["claude"] != "operational":
            logger.info("Attempting to repair Claude client...")
            if anthropic_installed and self.anthropic_api_key:
                try:
                    self.claude_client = anthropic.Anthropic(
                        api_key=self.anthropic_api_key
                    )
                    self.components["claude"] = self.claude_client
                    self.system_health["components_status"]["claude"] = "operational"
                    logger.info("Claude client repaired successfully")
                except Exception as e:
                    logger.error(f"Failed to repair Claude client: {e}")
                    repair_success = False
            else:
                logger.warning("Cannot repair Claude client: Anthropic not installed or API key missing")
                repair_success = False
        
        # Try to initialize TRILOGY BRAIN
        if (self.system_health["components_status"]["trilogy_brain"] == "configured" and 
            self.enable_trilogy_brain and trilogy_brain_available):
            logger.info("Attempting to initialize TRILOGY BRAIN...")
            try:
                # Initialize lazy-loaded TRILOGY BRAIN
                trilogy_initialized = await self._ensure_trilogy_brain_initialized()
                if trilogy_initialized:
                    self.system_health["components_status"]["trilogy_brain"] = "operational"
                    self.components["trilogy_brain"]["status"] = "operational"
                    logger.info("TRILOGY BRAIN initialized successfully")
                else:
                    logger.warning("Failed to initialize TRILOGY BRAIN")
                    repair_success = False
            except Exception as e:
                logger.error(f"Failed to initialize TRILOGY BRAIN: {e}")
                repair_success = False
        
        # Check repair status
        if repair_success:
            self.system_health["repairs_successful"] += 1
            self.system_health["status"] = "operational"
            logger.info("System repair completed successfully")
        else:
            logger.warning("System repair partially successful or unsuccessful")
            
        # Update health status after repair
        await self.check_system_health()
        
        return repair_success
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive system health report.
        
        Returns:
            Dictionary with detailed health information
        """
        # Calculate health metrics
        uptime = time.time() - float(self.session_id.split("_")[1])
        health_trend = "stable"
        
        if len(self.system_health["health_history"]) > 5:
            recent_statuses = [h["status"] for h in self.system_health["health_history"][-5:]]
            if all(status == "operational" for status in recent_statuses):
                health_trend = "excellent"
            elif recent_statuses[-1] == "operational" and any(status != "operational" for status in recent_statuses[:-1]):
                health_trend = "improving"
            elif recent_statuses[-1] != "operational" and any(status == "operational" for status in recent_statuses[:-1]):
                health_trend = "degrading"
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "uptime_seconds": uptime,
            "status": self.system_health["status"],
            "health_trend": health_trend,
            "components": self.system_health["components_status"],
            "metrics": {
                "checks_performed": self.system_health["checks_performed"],
                "issues_detected": self.system_health["issues_detected"],
                "repairs_attempted": self.system_health["repairs_attempted"],
                "repairs_successful": self.system_health["repairs_successful"],
                "repair_success_rate": (self.system_health["repairs_successful"] / 
                                       self.system_health["repairs_attempted"]
                                       if self.system_health["repairs_attempted"] > 0 else 0)
            },
            "recent_history": self.system_health["health_history"][-10:],
            "missing_components": self.missing_components
        }
        
        return report

    async def construct_knowledge_graph(
        self, 
        topic: str, 
        research_results: Dict[str, Any], 
        analysis_results: Optional[Dict[str, Any]] = None,
        graph_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Constructs a knowledge graph from research findings and analysis.
        
        Creates structured representation of concepts, relationships, and insights
        that can be visualized and explored in THREE.js.
        
        Args:
            topic: The research topic
            research_results: Primary and follow-up research results
            analysis_results: Optional analysis results to include
            graph_type: Type of knowledge graph to construct (standard, detailed, technical, threejs)
            
        Returns:
            Dictionary with knowledge graph data
        """
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            # Prepare content from research and analysis
            content = f"## Research Topic: {topic}\n\n"
            
            # Add primary research
            if "primary_research" in research_results:
                content += f"## Primary Research\n\n{research_results['primary_research']}\n\n"
            
            # Add follow-up research
            if "followup_research" in research_results:
                content += "## Follow-up Research\n\n"
                for question, answer in research_results["followup_research"].items():
                    content += f"### Question: {question}\n{answer}\n\n"
            
            # Add code examples if available
            if "code_search" in research_results and research_results["code_search"]:
                content += "## Code Examples\n\n"
                for i, code_item in enumerate(research_results["code_search"][:2], 1):
                    if isinstance(code_item, dict) and "error" not in code_item:
                        code_name = code_item.get("name", f"Example {i}")
                        content += f"### {code_name}\n{code_item.get('description', 'No description')}\n\n"
            
            # Add analysis if available
            if analysis_results and "analysis" in analysis_results:
                content += f"## Analysis\n\n{analysis_results['analysis']}\n\n"
            
            # Configure graph type
            graph_config = {
                "standard": {
                    "prompt": "Please analyze this research and create a knowledge graph with key concepts and their relationships.",
                    "thinking_prompt": "Let's identify the key concepts, entities, relationships, and insights in this research that should be represented in a knowledge graph.",
                    "system_role": "You are Claude, a knowledge graph expert. Create a well-structured, comprehensive knowledge graph from research findings."
                },
                "detailed": {
                    "prompt": "Please analyze this research and create a detailed knowledge graph with concepts, properties, relationships, and hierarchies.",
                    "thinking_prompt": "Let's create a comprehensive ontology and knowledge graph from this research, focusing on detailed relationships, properties, and hierarchical structures.",
                    "system_role": "You are Claude, a knowledge graph expert specializing in detailed ontologies and complex knowledge structures."
                },
                "technical": {
                    "prompt": "Please analyze this research and create a technical knowledge graph focused on implementation details, components, and dependencies.",
                    "thinking_prompt": "Let's analyze the technical components, dependencies, architectures, and implementation details in this research for a technical knowledge graph.",
                    "system_role": "You are Claude, a technical knowledge graph expert specializing in software architecture and technical relationships."
                },
                "threejs": {
                    "prompt": "Please analyze this research and create a knowledge graph optimized for THREE.js visualization with visual properties and interaction hints.",
                    "thinking_prompt": "Let's create a knowledge graph specifically designed for visualization in THREE.js, with visual properties, groupings, and interaction possibilities.",
                    "system_role": "You are Claude, an expert in knowledge representation and THREE.js visualization. Create knowledge graphs optimized for interactive 3D visualization."
                }
            }
            
            # Default to standard if graph type not recognized
            if graph_type not in graph_config:
                logger.warning(f"Graph type '{graph_type}' not recognized, defaulting to 'standard'")
                graph_type = "standard"
            
            config = graph_config[graph_type]
            
            # Add specialized instructions for knowledge graph structure
            graph_instructions = """
            Please create a structured knowledge graph with the following components:

            1. Nodes representing key concepts, entities, and ideas
            2. Edges representing relationships between nodes
            3. Properties for nodes and edges that describe their attributes
            4. Groups or categories that nodes belong to

            Structure your response as valid JSON with the following format:
            ```json
            {
                "nodes": [
                    {
                        "id": "unique_id",
                        "label": "Concept Name",
                        "type": "concept|entity|process|technology|resource|etc",
                        "properties": {
                            "property1": "value1",
                            "property2": "value2"
                        },
                        "group": "category_name",
                        "description": "Brief description of this concept",
                        "size": 1-10 (relative importance/size),
                        "source": "primary_research|followup|code|analysis"
                    },
                    ...
                ],
                "edges": [
                    {
                        "source": "source_node_id",
                        "target": "target_node_id",
                        "label": "relationship_type",
                        "properties": {
                            "property1": "value1"
                        },
                        "weight": 1-10 (relationship strength),
                        "description": "Brief description of this relationship"
                    },
                    ...
                ],
                "groups": [
                    {
                        "id": "group_id",
                        "label": "Group Name",
                        "description": "Description of this group of nodes"
                    },
                    ...
                ],
                "metadata": {
                    "topic": "research topic",
                    "nodeCount": integer,
                    "edgeCount": integer,
                    "groupCount": integer,
                    "description": "Brief description of this knowledge graph",
                    "suggestedVisualization": "Description of how to visualize this graph effectively"
                }
            }
            ```
            
            Ensure your knowledge graph:
            - Has clear, meaningful relationships
            - Captures the key concepts from the research
            - Uses descriptive labels for relationships
            - Has appropriate grouping of related concepts
            - Includes 15-40 nodes for standard graphs, more for detailed graphs
            - Has properly connected edges (no orphaned nodes)
            """
            
            # Add specialized instructions based on graph type
            if graph_type == "threejs":
                graph_instructions += """
                For THREE.js visualization optimization, also include these additional properties:
                
                - For nodes:
                  - "visualProperties": {
                      "color": "#hexcolor",
                      "texture": "suggested texture type",
                      "shape": "sphere|cube|cylinder|custom",
                      "initialPosition": [x, y, z], (suggested coordinates)
                      "highlightColor": "#hexcolor",
                      "labelVisibility": "always|onHover|onSelect"
                    }
                
                - For edges:
                  - "visualProperties": {
                      "color": "#hexcolor",
                      "style": "solid|dashed|dotted|arrow",
                      "width": 1-5 (visual width),
                      "curvature": 0-1 (how curved the connection should be),
                      "animated": true|false
                    }
                
                - For the overall graph:
                  - Add a "visualization" object in metadata with:
                    "visualization": {
                      "layout": "force|radial|hierarchical|cluster",
                      "groups": { "groupId": {"color": "#hexcolor"} },
                      "background": "#hexcolor",
                      "defaultNodeSize": number,
                      "defaultEdgeWidth": number,
                      "physics": {
                        "gravity": number,
                        "linkDistance": number,
                        "charge": number
                      }
                    }
                """
            
            # Create prompt for Claude
            system_message = config["system_role"]
            prompt = f"{config['thinking_prompt']}\n\n{config['prompt']}\n\n{graph_instructions}\n\nResearch content:\n\n{content}"
            
            # Call Claude API
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from response
            analysis_content = response.content[0].text
            
            # Extract JSON
            import re
            import json
            
            # Find JSON in the response
            json_pattern = r"```(?:json)?\s*({[\s\S]*?})```"
            json_matches = re.findall(json_pattern, analysis_content)
            
            if not json_matches:
                # Try to find anything that looks like JSON
                json_pattern = r"{[\s\S]*\"nodes\"[\s\S]*\"edges\"[\s\S]*}"
                json_matches = re.findall(json_pattern, analysis_content)
            
            if json_matches:
                try:
                    graph_data = json.loads(json_matches[0])
                    
                    # Validate the structure
                    if "nodes" not in graph_data or "edges" not in graph_data:
                        return {
                            "error": "Invalid knowledge graph structure",
                            "raw_content": analysis_content,
                            "success": False
                        }
                    
                    # Add metadata if missing
                    if "metadata" not in graph_data:
                        graph_data["metadata"] = {
                            "topic": topic,
                            "nodeCount": len(graph_data["nodes"]),
                            "edgeCount": len(graph_data["edges"]),
                            "groupCount": len(graph_data.get("groups", [])),
                            "description": f"Knowledge graph for {topic}",
                            "graphType": graph_type
                        }
                    
                    # Store graph in memory
                    graph_id = str(uuid.uuid4())
                    memory_metadata = {
                        "topic": topic,
                        "timestamp": datetime.now().timestamp(),
                        "session_id": self.session_id,
                        "graph_type": graph_type,
                        "node_count": len(graph_data["nodes"]),
                        "edge_count": len(graph_data["edges"])
                    }
                    
                    # Try to store in TRILOGY BRAIN first
                    memory_id = await self.store_in_trilogy_brain(
                        content=json.dumps(graph_data),
                        memory_type="knowledge_graph",
                        metadata=memory_metadata
                    )
                    
                    # Fall back to local memory if needed
                    if not memory_id:
                        memory_id = self.store_in_memory(
                            content=json.dumps(graph_data),
                            content_type="knowledge_graph",
                            metadata=memory_metadata
                        )
                    
                    # Create result with graph data
                    result = {
                        "knowledge_graph": graph_data,
                        "graph_id": memory_id,
                        "success": True,
                        "graph_type": graph_type
                    }
                    
                    return result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing knowledge graph JSON: {e}")
                    return {
                        "error": "Failed to parse knowledge graph JSON",
                        "raw_content": analysis_content,
                        "json_error": str(e),
                        "success": False
                    }
            else:
                return {
                    "error": "No knowledge graph JSON found in response",
                    "raw_content": analysis_content,
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error in knowledge graph construction: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error details: {error_details}")
            return {"error": str(e), "error_details": error_details, "success": False}

    async def generate_threejs_visualization(
        self,
        knowledge_graph: Dict[str, Any],
        visualization_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates THREE.js visualization code from a knowledge graph.
        
        Takes a knowledge graph structure and produces ready-to-use THREE.js
        code for visualizing the graph in an interactive 3D environment.
        
        Args:
            knowledge_graph: The knowledge graph data with nodes and edges
            visualization_options: Optional customization options for the visualization
                Can include: backgroundColor, nodeSize, edgeWidth, physics settings, etc.
                
        Returns:
            Dictionary with visualization code and metadata
        """
        if not self.claude_client:
            return {"error": "Claude client not initialized"}
        
        try:
            # Set default visualization options
            default_options = {
                "backgroundColor": "#000000",
                "defaultNodeSize": 5,
                "defaultEdgeWidth": 1,
                "highlightColor": "#ffffff",
                "useForceDirectedLayout": True,
                "useOrbitControls": True,
                "enableLabels": True,
                "colorByGroup": True,
                "animateEdges": True,
                "enableProgressiveLoading": True,
                "usePostprocessing": True,
                "enableInteraction": True
            }
            
            # Merge with provided options
            options = default_options.copy()
            if visualization_options:
                options.update(visualization_options)
            
            # Extract graph metadata
            nodes = knowledge_graph.get("nodes", [])
            edges = knowledge_graph.get("edges", [])
            groups = knowledge_graph.get("groups", [])
            metadata = knowledge_graph.get("metadata", {})
            
            if not nodes or not edges:
                return {"error": "Knowledge graph missing nodes or edges"}
            
            # Prepare prompt for Claude
            system_message = """You are Claude, an expert in THREE.js visualization and 3D graphics programming.

Your task is to generate complete, production-ready THREE.js code to visualize a knowledge graph in an interactive 3D environment.

The code should:
1. Be well-structured, modular, and optimized for performance
2. Include all necessary HTML, CSS, and JavaScript
3. Implement modern THREE.js best practices
4. Handle user interactions (zooming, panning, selecting)
5. Be aesthetically pleasing with good lighting and effects
6. Include detailed comments explaining key implementation details
7. Be ready to copy-paste and run immediately

Your code should be COMPLETE and SELF-CONTAINED without requiring any external dependencies beyond THREE.js itself.
"""

            prompt = f"""I need complete THREE.js code to visualize this knowledge graph:

KNOWLEDGE GRAPH METADATA:
- Nodes: {len(nodes)}
- Edges: {len(edges)}
- Groups: {len(groups)}
- Topic: {metadata.get('topic', 'Knowledge Graph')}

VISUALIZATION OPTIONS:
{json.dumps(options, indent=2)}

KNOWLEDGE GRAPH DATA (SAMPLE):
Nodes: {json.dumps(nodes[:3] if len(nodes) > 3 else nodes, indent=2)}
Edges: {json.dumps(edges[:3] if len(edges) > 3 else edges, indent=2)}
Groups: {json.dumps(groups[:3] if len(groups) > 3 else groups, indent=2)}

Please generate complete, production-ready THREE.js code to visualize this knowledge graph with the following components:

1. HTML file with proper structure and embedded CSS for styling
2. JavaScript code using modern THREE.js that:
   - Creates a scene with the specified background color
   - Implements a force-directed layout for the graph
   - Creates nodes as spheres/objects with sizes based on their importance
   - Creates edges as lines/tubes connecting the nodes
   - Implements color coding based on node groups
   - Adds proper lighting and camera controls
   - Handles user interactions (hover, click, zoom, pan)
   - Shows node labels on hover/selection
   - Implements progressive loading for performance
   - Adds subtle animations for visual appeal
   - Includes post-processing effects if specified

Make sure the code is complete, well-commented, and ready to use. Include all necessary initialization, setup, and event handling.
"""

            # Call Claude API
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_content = response.content[0].text
            
            # Extract code blocks
            import re
            
            # Extract HTML
            html_pattern = r"```html\s*([\s\S]*?)```"
            html_matches = re.findall(html_pattern, response_content)
            html_code = html_matches[0] if html_matches else ""
            
            # Extract JavaScript
            js_pattern = r"```(?:javascript|js)\s*([\s\S]*?)```"
            js_matches = re.findall(js_pattern, response_content)
            js_code = js_matches[0] if js_matches else ""
            
            # Extract CSS
            css_pattern = r"```(?:css)\s*([\s\S]*?)```"
            css_matches = re.findall(css_pattern, response_content)
            css_code = css_matches[0] if css_matches else ""
            
            # If no HTML found but we have JS, try to extract a complete HTML file
            if not html_code and js_code:
                complete_html_pattern = r"<!DOCTYPE html>[\s\S]*?<html>[\s\S]*?</html>"
                complete_matches = re.findall(complete_html_pattern, response_content)
                if complete_matches:
                    html_code = complete_matches[0]
            
            # Create result with visualization code
            result = {
                "visualization": {
                    "html": html_code,
                    "javascript": js_code,
                    "css": css_code,
                    "combined": html_code if html_code and "<script>" in html_code else None,
                    "options": options
                },
                "metadata": {
                    "nodeCount": len(nodes),
                    "edgeCount": len(edges),
                    "groupCount": len(groups),
                    "topic": metadata.get("topic", "Knowledge Graph")
                },
                "success": True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating THREE.js visualization: {e}")
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error details: {error_details}")
            return {"error": str(e), "error_details": error_details, "success": False}


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
        parser.add_argument("--self-analyze", action="store_true", help="Perform system self-analysis")
        parser.add_argument("--consolidate", action="store_true", help="Force memory consolidation")
        parser.add_argument("--health-check", action="store_true", help="Run system health check")
        parser.add_argument("--repair", action="store_true", help="Attempt system repair")
        parser.add_argument("--auto-repair", action="store_true", help="Enable continuous autonomous repair")
        parser.add_argument("--health-interval", type=int, default=60, help="Health check interval in seconds")
        
        args = parser.parse_args()
        
        # Create agent with autonomous repair if specified
        agent = AdvancedResearchAgent(
            enable_autonomous_repair=args.auto_repair,
            health_check_interval=args.health_interval
        )
        
        async def run_research():
            # Check for system operations first
            if args.health_check:
                result = await agent.check_system_health()
                print("\n" + "=" * 80)
                print(f"System Health Check Results")
                print(f"Status: {result['status']}")
                print(f"Components:")
                for component, status in result["components"].items():
                    print(f"  {component}: {status}")
                if result["issues"]:
                    print(f"Issues detected ({len(result['issues'])}):")
                    for i, issue in enumerate(result["issues"]):
                        print(f"  {i+1}. {issue}")
                        print(f"     Recommendation: {result['recommendations'][i]}")
                else:
                    print(f"No issues detected")
                print("=" * 80 + "\n")
                return result
                
            if args.repair:
                result = await agent.repair_system()
                print("\n" + "=" * 80)
                print(f"System Repair {'Successful' if result else 'Failed'}")
                print("=" * 80 + "\n")
                # Run a health check after repair
                health = await agent.check_system_health()
                print(f"System Status After Repair: {health['status']}")
                return result

            if args.self_analyze:
                result = await agent.self_analyze()
                print("\n" + "=" * 80)
                print(f"System self-analysis completed")
                print(f"Analysis summary:")
                if "self_analysis" in result:
                    # Print first 500 characters
                    analysis_preview = result["self_analysis"][:500] + "..." if len(result["self_analysis"]) > 500 else result["self_analysis"]
                    print(analysis_preview)
                print("=" * 80 + "\n")
                return result
                
            if args.consolidate:
                result = await agent.consolidate_memories()
                print("\n" + "=" * 80)
                print(f"Memory consolidation completed")
                print(f"Types processed: {result.get('memory_types_processed', [])}")
                print("=" * 80 + "\n")
                return result
            
            # Ensure a topic is provided for research
        if not args.topic:
            print("Error: Please provide a research topic with --topic")
            parser.print_help()
            return
        
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