"""
Composio Memory Bridge for VOT1

This module bridges the VOT1 memory system with Composio MCP.
It provides advanced memory capabilities including graph-based memory organization,
episodic memory, and semantic memory integration with Claude 3.7.

Key Features:
- Semantic and temporal memory retrieval strategies
- Graph-based memory relationships and traversal
- Hybrid processing mode leveraging Claude 3.7's thinking capabilities
- Memory importance and relevance scoring
- Memory consolidation and reflection
- Extended context window utilization (up to 200K tokens)
"""

import os
import json
import time
import logging
import uuid
import sqlite3
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import asyncio

from vot1.memory import MemoryManager
from vot1.composio.client import ComposioClient
from vot1.composio.enhanced_memory import EnhancedMemoryManager
from ..utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class ComposioMemoryBridge:
    """
    Bridge between VOT1 memory system and Composio MCP
    
    This class provides methods for:
    1. Storing memories in VOT1 from Composio responses
    2. Retrieving memories from VOT1 for Composio context
    3. Performing memory operations through Composio
    4. Graph-based memory storage and retrieval
    
    Enhanced for Claude 3.7:
    - Hybrid memory retrieval combining semantic and temporal strategies
    - Advanced thinking capabilities with memory reflection
    - Extended context window support (up to 200K tokens)
    - Improved memory metadata and relationship handling
    - Memory importance scoring and filtering
    - Optimized graph-based memory traversal
    """
    
    def __init__(
        self,
        memory_manager: Optional[Union[MemoryManager, EnhancedMemoryManager]] = None,
        composio_client: Optional[ComposioClient] = None,
        use_enhanced_memory: bool = True,
        memory_path: str = "memory",
        graph_db_path: str = "memory/graph/memory_graph.db",
        memory_store_path: str = "memory/conversations"
    ):
        """
        Initialize the memory bridge
        
        Args:
            memory_manager: VOT1 memory manager instance
            composio_client: Composio client instance
            use_enhanced_memory: Whether to use the enhanced memory manager
            memory_path: Path to memory storage
            graph_db_path: Path to graph database
            memory_store_path: Path to store memory-related data
        """
        # Create or use provided memory manager
        if memory_manager:
            self.memory_manager = memory_manager
        elif use_enhanced_memory:
            self.memory_manager = EnhancedMemoryManager(memory_path=memory_path)
        else:
            self.memory_manager = MemoryManager(memory_path=memory_path)
            
        self.enhanced_memory = isinstance(self.memory_manager, EnhancedMemoryManager)
        self.composio_client = composio_client or ComposioClient()
        self.graph_db_path = graph_db_path
        self.memory_store_path = memory_store_path
        
        # Ensure graph database directory exists
        os.makedirs(os.path.dirname(graph_db_path), exist_ok=True)
        
        # Initialize graph database if using standard memory manager
        if not self.enhanced_memory:
            self._init_graph_db()
            
        logger.info("Composio Memory Bridge initialized")
    
    def _init_graph_db(self):
        """Initialize graph database for standard memory manager"""
        # Only needed if we're not using the enhanced memory manager
        if not self.enhanced_memory:
            self.graph_conn = sqlite3.connect(self.graph_db_path)
            self.graph_cursor = self.graph_conn.cursor()
            
            # Create tables if they don't exist
            self.graph_cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT,
                metadata TEXT,
                importance REAL DEFAULT 1.0,
                created_at INTEGER NOT NULL
            )
            ''')
            
            self.graph_cursor.execute('''
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                metadata TEXT,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (source_id) REFERENCES nodes (id),
                FOREIGN KEY (target_id) REFERENCES nodes (id)
            )
            ''')
            
            # Create indices for faster queries
            self.graph_cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_id)')
            self.graph_cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_id)')
            self.graph_cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes (type)')
            
            self.graph_conn.commit()
    
    async def store_memory_from_response(
        self,
        response: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0,
        memory_type: str = "semantic_memory"
    ) -> str:
        """
        Store a memory from a Composio MCP response
        
        Args:
            response: Composio response dict
            metadata: Additional metadata to store
            importance: Importance score for memory (0.0-2.0)
            memory_type: Type of memory to store
            
        Returns:
            str: Memory ID
        """
        if "error" in response:
            logger.error(f"Cannot store memory from error response: {response['error']}")
            return None
            
        try:
            # Extract content from response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                logger.warning("No content found in Composio response")
                return None
                
            # Combine provided metadata with response metadata
            full_metadata = {
                "source": "composio_mcp",
                "timestamp": response.get("created", int(time.time())),
                "model": response.get("model", "composio"),
                "response_id": response.get("id", str(uuid.uuid4())),
                "type": memory_type
            }
            
            if metadata:
                full_metadata.update(metadata)
            
            # Use enhanced memory if available
            if self.enhanced_memory:
                memory_id = self.memory_manager.add_semantic_memory_with_relations(
                    content=content,
                    metadata=full_metadata,
                    importance=importance
                )
            else:
                # Store in standard memory manager
                memory_id = self.memory_manager.add_semantic_memory(
                    content=content,
                    metadata=full_metadata
                )
                
                # Also store in graph database
                node_id = self._add_graph_node(
                    content=content,
                    node_type=memory_type,
                    metadata=full_metadata,
                    importance=importance
                )
                
                # Store node mapping to memory
                self._update_memory_metadata(memory_id, {"graph_node_id": node_id})
            
            logger.info(f"Stored Composio response as memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory from Composio response: {str(e)}")
            return None
    
    def _add_graph_node(
        self, 
        content: str, 
        node_type: str = "memory",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0
    ) -> str:
        """
        Add a node to the memory graph.
        
        Args:
            content: The content of the node
            node_type: The type of node (e.g., "memory", "concept", "event")
            metadata: Additional metadata for the node
            importance: Importance score (higher = more important)
            
        Returns:
            str: ID of the created node
        """
        if self.enhanced_memory:
            return self.memory_manager.memory_graph.add_node(
                content=content,
                node_type=node_type,
                metadata=metadata,
                importance=importance
            )
            
        # If using standard memory
        node_id = str(uuid.uuid4())
        created_at = int(time.time())
        
        # Convert metadata to JSON string if provided
        metadata_str = json.dumps(metadata) if metadata else "{}"
        
        # Insert node into database
        self.graph_cursor.execute(
            '''
            INSERT INTO nodes (id, type, content, metadata, importance, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (node_id, node_type, content, metadata_str, importance, created_at)
        )
        self.graph_conn.commit()
        
        logger.debug(f"Added node {node_id} of type {node_type}")
        return node_id
    
    def _update_memory_metadata(self, memory_id: str, metadata_update: Dict[str, Any]):
        """Update metadata for a memory item."""
        if self.enhanced_memory:
            self.memory_manager._update_memory_metadata(memory_id, metadata_update)
            return
            
        # For standard memory manager
        memory_file = os.path.join(self.memory_manager.semantic_memory_path, f"{memory_id}.json")
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            # Update metadata
            if "metadata" not in memory_data:
                memory_data["metadata"] = {}
                
            memory_data["metadata"].update(metadata_update)
            
            # Write back to file
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
    
    def build_memory_context(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None,
        include_graph: bool = True,
        depth: int = 1,
        importance_threshold: float = 0.0,
        include_relationships: bool = True,
        max_relationship_count: int = 10,
        include_metadata: bool = True,
        format_style: str = "markdown"
    ) -> Dict[str, Any]:
        """
        Build memory context for Composio requests, optimized for Claude 3.7
        
        Args:
            query: Query to search memories
            limit: Maximum number of memories to include
            memory_types: Types of memories to include
            include_graph: Whether to include memory graph
            depth: Depth of memory graph to include
            importance_threshold: Minimum importance score for included memories
            include_relationships: Whether to include memory relationships
            max_relationship_count: Maximum number of relationships to include per memory
            include_metadata: Whether to include metadata in memory context
            format_style: Format style for memory context ("markdown", "json", "text")
            
        Returns:
            Dict containing memory context
        """
        start_time = time.time()
        try:
            # Search memories with enhanced parameters
            memories = self.memory_manager.search_memories(
                query=query,
                limit=limit,
                memory_types=memory_types,
                min_importance=importance_threshold
            )
            
            # Get conversation history with more context for Claude 3.7
            conversation_history = self.memory_manager.get_conversation_history(
                limit=10,  # Increased from default for better context
                include_timestamps=True
            )
            
            # Format memories based on requested style
            if format_style == "json":
                # JSON format for structured processing
                memory_items = [
                    {
                        "id": memory.get("id"),
                        "content": memory.get("content"),
                        "type": memory.get("type", "general"),
                        "importance": memory.get("importance", 1.0),
                        "timestamp": memory.get("timestamp"),
                        "metadata": memory.get("metadata", {}) if include_metadata else {}
                    }
                    for memory in memories
                ]
            elif format_style == "text":
                # Simple text format
                memory_items = [
                    f"Memory {i+1} ({memory.get('type', 'general')}): {memory.get('content')}"
                    for i, memory in enumerate(memories)
                ]
            else:
                # Default markdown format optimized for Claude 3.7
                memory_items = []
                for i, memory in enumerate(memories):
                    memory_id = memory.get("id", f"mem_{i}")
                    memory_content = memory.get("content", "")
                    memory_type = memory.get("type", "general")
                    memory_importance = memory.get("importance", 1.0)
                    
                    # Format timestamp if available
                    timestamp = memory.get("timestamp")
                    if timestamp:
                        if isinstance(timestamp, (int, float)):
                            from datetime import datetime
                            formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            formatted_timestamp = str(timestamp)
                    else:
                        formatted_timestamp = "Unknown"
                    
                    # Build formatted memory item
                    memory_item = {
                        "id": memory_id,
                        "content": memory_content,
                        "type": memory_type,
                        "importance": memory_importance,
                        "timestamp": formatted_timestamp
                    }
                    
                    # Add metadata if requested
                    if include_metadata and "metadata" in memory and memory["metadata"]:
                        memory_item["metadata"] = memory["metadata"]
                    
                    # Add relationships if requested
                    if include_relationships and self.enhanced_memory:
                        try:
                            relationships = self.memory_manager.get_memory_relationships(memory_id, limit=max_relationship_count)
                            if relationships and len(relationships) > 0:
                                memory_item["relationships"] = relationships
                        except Exception as e:
                            logger.warning(f"Failed to get relationships for memory {memory_id}: {e}")
                    
                    memory_items.append(memory_item)
            
            # Build complete memory context
            memory_dict = {
                "memories": memory_items,
                "conversation_history": conversation_history,
                "query": query,
                "retrieved_count": len(memories),
                "retrieval_time": time.time() - start_time
            }
            
            # Add memory graph if requested
            if include_graph and self.enhanced_memory:
                try:
                    # Get memory IDs
                    memory_ids = [memory.get("id") for memory in memories if memory.get("id")]
                    
                    # Build memory graph with specified depth
                    memory_graph = self.memory_manager.build_memory_graph(
                        memory_ids, 
                        depth=depth,
                        include_node_content=True
                    )
                    
                    # Add graph to context
                    memory_dict["memory_graph"] = memory_graph
                except Exception as e:
                    logger.warning(f"Failed to build memory graph: {e}")
            
            return memory_dict
        except Exception as e:
            logger.error(f"Error building memory context: {e}")
            # Return minimal context on error
            return {
                "memories": [],
                "conversation_history": [],
                "error": str(e)
            }
    
    async def process_with_memory(
        self,
        prompt: str,
        memory_limit: int = 10,
        store_response: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        include_graph: bool = True,
        model: Optional[str] = None,
        thinking: bool = True,
        hybrid_mode: bool = True,
        max_thinking_tokens: Optional[int] = None,
        memory_retrieval_strategy: str = "hybrid",
        memory_importance_threshold: float = 0.3,
        enable_memory_reflection: bool = True,
        include_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Process a request with memory integration, optimized for Claude 3.7.
        
        Args:
            prompt: User prompt to process
            memory_limit: Maximum number of memories to retrieve
            store_response: Whether to store the response in memory
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            include_graph: Whether to include graph relationships in memory retrieval
            model: Model to use (defaults to client's default)
            thinking: Whether to include thinking in the response
            hybrid_mode: Whether to use hybrid mode (defaults to True)
            max_thinking_tokens: Maximum tokens for thinking (defaults to client setting)
            memory_retrieval_strategy: Strategy for retrieving memories ("semantic", "temporal", "hybrid")
            memory_importance_threshold: Minimum importance score for included memories
            enable_memory_reflection: Whether to enable reflection on memories
            include_timestamps: Whether to include timestamps in memory context
            
        Returns:
            Response dictionary with memory context
        """
        start_time = time.time()
        
        # Retrieve relevant memories with performance timing
        memory_start = time.time()
        
        # Enhanced memory retrieval based on selected strategy
        if memory_retrieval_strategy == "hybrid":
            # Hybrid retrieval combines semantic and temporal factors
            memories = await self.memory_manager.retrieve_memories(
                prompt, 
                limit=memory_limit,
                include_graph=include_graph,
                importance_threshold=memory_importance_threshold
            )
        elif memory_retrieval_strategy == "temporal":
            # Prioritize recent memories
            memories = await self.memory_manager.retrieve_recent_memories(
                limit=memory_limit,
                filter_query=prompt if len(prompt) > 10 else None
            )
        elif memory_retrieval_strategy == "semantic":
            # Pure semantic search
            memories = await self.memory_manager.retrieve_memories(
                prompt, 
                limit=memory_limit,
                include_graph=include_graph
            )
        else:
            # Default to hybrid if invalid strategy provided
            memories = await self.memory_manager.retrieve_memories(
                prompt, 
                limit=memory_limit,
                include_graph=include_graph,
                importance_threshold=memory_importance_threshold
            )
            
        memory_retrieval_time = time.time() - memory_start
        
        # Log memory retrieval performance
        memory_count = len(memories)
        logger.info(f"Retrieved {memory_count} memories in {memory_retrieval_time:.2f}s using {memory_retrieval_strategy} strategy")
        
        # Format memory context for the AI with enhanced structure
        memory_context = ""
        memory_ids = []
        memory_types = {}
        
        if memory_count > 0:
            memory_context = "## MEMORY CONTEXT\nThe following memories may be relevant to the current query:\n\n"
            
            for i, memory in enumerate(memories):
                memory_id = memory.get("id", f"unknown_{i}")
                memory_ids.append(memory_id)
                
                # Track memory types for analytics
                memory_type = memory.get("type", "general")
                if memory_type in memory_types:
                    memory_types[memory_type] += 1
                else:
                    memory_types[memory_type] = 1
                
                # Format memory with enhanced structure
                memory_context += f"### Memory #{i+1} [ID: {memory_id}]\n"
                memory_context += f"- **Content**: {memory.get('content', 'No content')}\n"
                
                # Include timestamp if requested
                if include_timestamps and "timestamp" in memory:
                    # Format timestamp as readable date if it's a number
                    timestamp = memory.get("timestamp")
                    if isinstance(timestamp, (int, float)):
                        from datetime import datetime
                        timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    memory_context += f"- **Created**: {timestamp}\n"
                
                memory_context += f"- **Type**: {memory_type}\n"
                memory_context += f"- **Importance**: {memory.get('importance', 1.0)}\n"
                
                # Include additional metadata if available
                if "metadata" in memory and isinstance(memory["metadata"], dict):
                    memory_context += "- **Metadata**:\n"
                    for key, value in memory["metadata"].items():
                        memory_context += f"  - {key}: {value}\n"
                
                # Include graph relationships if available and requested
                if include_graph and "relationships" in memory and memory["relationships"]:
                    memory_context += "- **Relationships**:\n"
                    for rel in memory["relationships"][:5]:  # Limit to 5 relationships
                        rel_type = rel.get("type", "related_to")
                        rel_id = rel.get("target_id", "unknown")
                        rel_strength = rel.get("strength", 1.0)
                        memory_context += f"  - {rel_type} → Memory {rel_id} (strength: {rel_strength:.2f})\n"
                
                memory_context += "\n"
            
            # Enhanced memory usage instructions optimized for Claude 3.7
            memory_context += "\n## MEMORY USAGE INSTRUCTIONS\n"
            memory_context += "1. Use these memories to inform your response, integrating insights naturally.\n"
            memory_context += "2. Prioritize memories based on relevance and recency.\n"
            memory_context += "3. If memories contradict each other, prefer more recent or higher importance memories.\n"
            memory_context += "4. Do not mention the memory system directly unless the user explicitly asks about it.\n"
            memory_context += "5. If you recognize patterns across multiple memories, you may synthesize insights from them.\n"
            
            if enable_memory_reflection:
                memory_context += "6. If appropriate, include brief reflections on how past interactions inform your current response.\n"
        
        # Create system message with memory context
        system_message = """You are VOT1, an advanced AI assistant enhanced with memory and cognitive capabilities, powered by Claude 3.7 Sonnet.

When responding to the user:
- Provide thoughtful, accurate, and helpful information
- Use a conversational yet professional tone
- If you don't know something, be honest about it
- Be concise unless asked for detailed information
- Respond directly to the user's question first, then provide additional context if helpful
- Leverage your expanded context window and reasoning capabilities
"""

        # Append memory context if available
        if memory_context:
            system_message += f"\n{memory_context}"
        
        # Set default thinking token limit if not specified
        if max_thinking_tokens is None:
            max_thinking_tokens = 120000  # Claude 3.7 Sonnet max thinking tokens
        
        # Process with Composio client
        process_start_time = time.time()
        response = await self.composio_client.process_request(
            prompt=prompt,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking=thinking,
            model=model,
            hybrid_mode=hybrid_mode,
            memory_context={
                "memory_count": memory_count,
                "memory_types": memory_types,
                "memory_ids": memory_ids,
                "retrieval_strategy": memory_retrieval_strategy
            }
        )
        process_time = time.time() - process_start_time
        logger.info(f"Claude 3.7 processing completed in {process_time:.2f}s")
        
        # Add memory context to the response
        response["memory_context"] = {
            "memory_count": memory_count,
            "memory_ids": memory_ids,
            "memory_types": dict(memory_types),
            "retrieval_strategy": memory_retrieval_strategy,
            "retrieval_time": memory_retrieval_time,
            "importance_threshold": memory_importance_threshold
        }
        
        # Store the response in memory if requested
        if store_response and "choices" in response and len(response["choices"]) > 0:
            assistant_response = response["choices"][0]["message"]["content"]
            thinking_content = response["choices"][0].get("thinking", "")
            
            # Store assistant response in memory
            memory_store_start = time.time()
            memory_id = await self.memory_manager.store_memory(
                content=assistant_response,
                memory_type="assistant_response",
                metadata={
                    "prompt": prompt,
                    "timestamp": time.time(),
                    "model": model or self.composio_client.model,
                    "related_memories": memory_ids,
                    "processing_time": process_time
                },
                importance=1.0  # Default high importance for assistant responses
            )
            
            # Store thinking process in memory if available and significant
            if thinking and thinking_content and len(thinking_content) > 100:
                # Extract the most valuable parts of thinking content if it's very long
                thinking_to_store = thinking_content
                if len(thinking_content) > 30000:
                    # Store beginning and end of thinking, which often contain the most valuable insights
                    thinking_to_store = thinking_content[:15000] + "\n...[content truncated]...\n" + thinking_content[-15000:]
                    
                thinking_id = await self.memory_manager.store_memory(
                    content=thinking_to_store,
                    memory_type="thinking_process",
                    metadata={
                        "prompt": prompt,
                        "timestamp": time.time(),
                        "model": model or self.composio_client.model,
                        "related_response": memory_id,
                        "related_memories": memory_ids,
                        "tokens": len(thinking_content) // 4  # Rough estimate of token count
                    },
                    importance=0.7  # Medium-high importance for thinking
                )
                
                # Add thinking ID to response
                response["memory_context"]["thinking_id"] = thinking_id
                
                # Create relationships between thinking and response
                if self.enhanced_memory:
                    await self.memory_manager.create_relationship(
                        thinking_id, memory_id, "informs", 1.0
                    )
                    
                    # Also link thinking to retrieved memories that were used
                    for mem_id in memory_ids:
                        await self.memory_manager.create_relationship(
                            mem_id, thinking_id, "used_in", 0.8
                        )
            
            memory_store_time = time.time() - memory_store_start
            response["memory_context"]["memory_id"] = memory_id
            response["memory_context"]["store_time"] = memory_store_time
            
            logger.info(f"Stored response in memory with ID {memory_id} in {memory_store_time:.2f}s")
            
            # Create relationships between response and retrieved memories
            if self.enhanced_memory and memory_ids:
                for mem_id in memory_ids:
                    await self.memory_manager.create_relationship(
                        mem_id, memory_id, "informed", 0.9
                    )
        
        # Add total processing time
        total_time = time.time() - start_time
        response["memory_context"]["total_time"] = total_time
        response["memory_context"]["process_time"] = process_time
        
        logger.info(f"Total memory-augmented processing time: {total_time:.2f}s")
        
        return response
    
    def process_with_memory_sync(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Synchronous version of process_with_memory.
        
        This is a convenience wrapper for non-async code.
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.process_with_memory(*args, **kwargs))
        
    async def enhance_memory_with_reflection(self, 
                                          memory_id: str,
                                          prompt: Optional[str] = None,
                                          reflection_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhance an existing memory with AI reflection.
        
        Args:
            memory_id: ID of the memory to enhance
            prompt: Optional custom prompt for the reflection
            reflection_prompt: Optional template for reflection
            
        Returns:
            Response dictionary with reflection information
        """
        # Retrieve the original memory
        memory = await self.memory_manager.get_memory(memory_id)
        if not memory:
            logger.error(f"Memory with ID {memory_id} not found")
            return {"error": f"Memory with ID {memory_id} not found"}
        
        # Use default reflection prompt if not provided
        if not reflection_prompt:
            reflection_prompt = """
            Analyze the following content and provide a reflective summary:
            
            {content}
            
            Please provide:
            1. A concise summary of the key points
            2. The main concepts and their relationships
            3. Potential insights or implications not explicitly stated
            4. Questions that might arise from this content
            5. How this information might be relevant in different contexts
            """
        
        # Format the reflection prompt
        if not prompt:
            prompt = reflection_prompt.format(content=memory.get("content", ""))
        
        # Process with Composio client
        reflection_response = await self.composio_client.process_request(
            prompt=prompt,
            system="You are an analytical AI tasked with reflecting on information to extract deeper insights and connections.",
            temperature=0.7,
            thinking=True,
            hybrid_mode=True
        )
        
        if "choices" in reflection_response and len(reflection_response["choices"]) > 0:
            reflection_content = reflection_response["choices"][0]["message"]["content"]
            
            # Store the reflection as a new memory
            reflection_id = await self.memory_manager.store_memory(
                content=reflection_content,
                memory_type="memory_reflection",
                metadata={
                    "original_memory_id": memory_id,
                    "timestamp": time.time(),
                    "reflection_type": "standard"
                }
            )
            
            # Create a connection between the memories
            await self.memory_manager.create_connection(
                source_id=memory_id,
                target_id=reflection_id,
                connection_type="has_reflection"
            )
            
            logger.info(f"Created reflection for memory {memory_id} with ID {reflection_id}")
            
            reflection_response["reflection"] = {
                "original_memory_id": memory_id,
                "reflection_id": reflection_id,
                "success": True
            }
            
            return reflection_response
        else:
            logger.error("Failed to generate reflection")
            return {"error": "Failed to generate reflection", "raw_response": reflection_response}
    
    async def consolidate_memories(self, 
                                query: Optional[str] = None, 
                                memory_ids: Optional[List[str]] = None,
                                limit: int = 5) -> Dict[str, Any]:
        """
        Consolidate related memories to generate new insights.
        
        Args:
            query: Optional query to find related memories
            memory_ids: Optional list of specific memory IDs to consolidate
            limit: Maximum number of memories to retrieve if using query
            
        Returns:
            Response dictionary with consolidation information
        """
        memories_to_consolidate = []
        
        # Either use provided memory IDs or retrieve based on query
        if memory_ids:
            for memory_id in memory_ids:
                memory = await self.memory_manager.get_memory(memory_id)
                if memory:
                    memories_to_consolidate.append(memory)
        elif query:
            memories = await self.memory_manager.retrieve_memories(query, limit=limit)
            memories_to_consolidate = memories
        else:
            logger.error("Either query or memory_ids must be provided")
            return {"error": "Either query or memory_ids must be provided"}
        
        if not memories_to_consolidate:
            logger.warning("No memories found to consolidate")
            return {"error": "No memories found to consolidate"}
        
        # Prepare consolidation prompt
        consolidation_prompt = "Analyze the following related memories and identify patterns, insights, and new understanding that emerges from considering them together:\n\n"
        
        memory_ids = []
        for i, memory in enumerate(memories_to_consolidate):
            memory_ids.append(memory.get("id", f"unknown_{i}"))
            consolidation_prompt += f"Memory #{i+1} [ID: {memory.get('id', 'unknown')}]:\n"
            consolidation_prompt += f"Content: {memory.get('content', 'No content')}\n"
            consolidation_prompt += f"Type: {memory.get('type', 'general')}\n"
            consolidation_prompt += "\n"
        
        consolidation_prompt += "\nBased on these memories, please provide:\n"
        consolidation_prompt += "1. Common themes or patterns across these memories\n"
        consolidation_prompt += "2. New insights that emerge from considering these memories together\n"
        consolidation_prompt += "3. Potential knowledge gaps or contradictions between memories\n"
        consolidation_prompt += "4. A synthesized understanding that integrates all the information\n"
        
        # Process consolidation request
        consolidation_response = await self.composio_client.process_request(
            prompt=consolidation_prompt,
            system="You are an analytical AI specialized in knowledge synthesis and pattern recognition.",
            temperature=0.7,
            thinking=True,
            hybrid_mode=True
        )
        
        if "choices" in consolidation_response and len(consolidation_response["choices"]) > 0:
            consolidation_content = consolidation_response["choices"][0]["message"]["content"]
            
            # Store consolidation as a new memory
            consolidation_id = await self.memory_manager.store_memory(
                content=consolidation_content,
                memory_type="memory_consolidation",
                metadata={
                    "source_memory_ids": memory_ids,
                    "timestamp": time.time(),
                    "memory_count": len(memories_to_consolidate)
                }
            )
            
            # Create connections to all source memories
            for memory_id in memory_ids:
                await self.memory_manager.create_connection(
                    source_id=memory_id,
                    target_id=consolidation_id,
                    connection_type="used_in_consolidation"
                )
            
            logger.info(f"Created memory consolidation with ID {consolidation_id} from {len(memory_ids)} memories")
            
            consolidation_response["consolidation"] = {
                "consolidation_id": consolidation_id,
                "source_memory_ids": memory_ids,
                "success": True
            }
            
            return consolidation_response
        else:
            logger.error("Failed to generate memory consolidation")
            return {"error": "Failed to generate consolidation", "raw_response": consolidation_response}
    
    def _add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add an edge between two nodes in the memory graph.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            relation_type: Type of relationship
            weight: Weight of the relationship
            metadata: Additional metadata
            
        Returns:
            str: ID of the created edge
        """
        if self.enhanced_memory:
            return self.memory_manager.memory_graph.add_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                weight=weight,
                metadata=metadata
            )
            
        # For standard memory manager
        edge_id = str(uuid.uuid4())
        created_at = int(time.time())
        
        # Convert metadata to JSON string if provided
        metadata_str = json.dumps(metadata) if metadata else "{}"
        
        # Insert edge into database
        self.graph_cursor.execute(
            '''
            INSERT INTO edges (id, source_id, target_id, relation_type, weight, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (edge_id, source_id, target_id, relation_type, weight, metadata_str, created_at)
        )
        self.graph_conn.commit()
        
        logger.debug(f"Added edge {edge_id} from {source_id} to {target_id} of type {relation_type}")
        return edge_id
        
    async def plan_with_memory(
        self,
        goal: str,
        context: Optional[str] = None,
        memory_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Create a plan using memory context
        
        Args:
            goal: The goal to plan for
            context: Additional context
            memory_limit: Maximum number of memories to include
            
        Returns:
            Dict with plan information
        """
        # Build memory context
        memory_context = self.build_memory_context(
            query=goal,
            limit=memory_limit,
            include_graph=True
        )
        
        # Create system prompt for planning
        system_prompt = """
        You are an expert planner. Your task is to create a detailed plan to achieve a goal.
        Use the provided memories and context to inform your planning.
        
        Your response should be in this JSON format:
        {
            "plan": {
                "goal": "The main goal",
                "steps": [
                    {"step": 1, "description": "Step 1 description", "expected_outcome": "Expected outcome"},
                    {"step": 2, "description": "Step 2 description", "expected_outcome": "Expected outcome"}
                ],
                "required_resources": ["resource1", "resource2"],
                "potential_challenges": ["challenge1", "challenge2"],
                "success_criteria": ["criteria1", "criteria2"]
            }
        }
        """
        
        # Combine goal and context
        prompt = f"Goal: {goal}"
        if context:
            prompt += f"\n\nAdditional context: {context}"
            
        # Process request with memory context
        response = await self.composio_client.process_request(
            prompt=prompt,
            system=system_prompt,
            temperature=0.7,
            max_tokens=2048,
            memory_context=memory_context,
            thinking=True
        )
        
        # Store the plan in memory
        if "error" not in response:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            await self.store_memory_from_response(
                response=response,
                metadata={
                    "type": "plan",
                    "goal": goal,
                    "created_at": int(time.time())
                },
                importance=1.5,
                memory_type="plan"
            )
            
        return response
    
    async def advanced_memory_reflection(
        self,
        query: Optional[str] = None,
        memory_ids: Optional[List[str]] = None,
        reflection_depth: str = "deep",
        max_memories: int = 20,
        include_thinking: bool = True,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform advanced reflection on memories using Claude 3.7's enhanced thinking.
        
        This method analyzes patterns across memories, identifies insights,
        and generates reflections that can enhance future interactions.
        
        Args:
            query: Optional query to filter memories for reflection
            memory_ids: Optional list of memory IDs to reflect on (overrides query)
            reflection_depth: Depth of reflection ("brief", "standard", "deep")
            max_memories: Maximum number of memories to include
            include_thinking: Whether to include thinking in the response
            model: Model to use (defaults to client's default)
            
        Returns:
            Dict containing reflection results
        """
        start_time = time.time()
        
        # Determine memories to reflect on
        memories_to_reflect = []
        
        if memory_ids and len(memory_ids) > 0:
            # Use specified memory IDs
            for memory_id in memory_ids[:max_memories]:
                try:
                    memory = await self.memory_manager.get_memory(memory_id)
                    if memory:
                        memories_to_reflect.append(memory)
                except Exception as e:
                    logger.warning(f"Failed to get memory {memory_id}: {e}")
        elif query:
            # Use query to retrieve memories
            memories_to_reflect = await self.memory_manager.retrieve_memories(
                query, 
                limit=max_memories, 
                include_graph=True
            )
        else:
            # Default to recent memories
            memories_to_reflect = await self.memory_manager.retrieve_recent_memories(limit=max_memories)
        
        if not memories_to_reflect:
            return {
                "success": False,
                "error": "No memories found for reflection",
                "reflections": [],
                "time_taken": time.time() - start_time
            }
        
        # Organize memories by type
        memories_by_type = {}
        for memory in memories_to_reflect:
            memory_type = memory.get("type", "general")
            if memory_type not in memories_by_type:
                memories_by_type[memory_type] = []
            memories_by_type[memory_type].append(memory)
        
        # Create context for reflection
        memory_context = "## MEMORIES TO REFLECT ON\n\n"
        
        for memory_type, memories in memories_by_type.items():
            memory_context += f"### {memory_type.upper()} MEMORIES ({len(memories)})\n\n"
            for i, memory in enumerate(memories):
                memory_context += f"Memory #{i+1} [ID: {memory.get('id', 'unknown')}]:\n"
                memory_context += f"- Content: {memory.get('content', 'No content')}\n"
                
                # Format timestamp if available
                timestamp = memory.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, (int, float)):
                        from datetime import datetime
                        formatted_timestamp = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        memory_context += f"- Created: {formatted_timestamp}\n"
                    else:
                        memory_context += f"- Created: {timestamp}\n"
                
                # Include metadata for context
                if "metadata" in memory and isinstance(memory["metadata"], dict):
                    memory_context += "- Metadata:\n"
                    for key, value in memory["metadata"].items():
                        if key != "content" and key != "timestamp":  # Skip duplicates
                            memory_context += f"  - {key}: {value}\n"
                
                memory_context += "\n"
        
        # Define reflection prompts based on depth
        if reflection_depth == "brief":
            reflection_prompt = "Provide a brief summary of key patterns in these memories."
            reflection_depth_tokens = 30000
        elif reflection_depth == "deep":
            reflection_prompt = """Perform a deep reflection on these memories, considering:
1. Recurring patterns and themes
2. Potential insights or knowledge that can be derived
3. Contradictions or inconsistencies
4. Temporal evolution of concepts or relationships
5. Opportunities for knowledge consolidation
6. Meta-level observations about the memory system itself"""
            reflection_depth_tokens = 120000
        else:  # standard
            reflection_prompt = """Reflect on these memories to identify:
1. Key patterns and connections
2. Important insights or principles
3. Potential gaps or opportunities for further exploration"""
            reflection_depth_tokens = 60000
            
        # System message for reflection
        system_message = f"""You are VOT1's Memory Reflection System, powered by Claude 3.7.
Your task is to analyze memories and generate insightful reflections.

{memory_context}

When performing memory reflection:
- Look for patterns, connections and insights across memories
- Consider temporal relationships and evolution of concepts
- Identify knowledge gaps or contradictions
- Suggest potential areas for memory consolidation
- Format your analysis in a clear, structured way
- Each insight should be actionable and useful for future interactions

Perform reflection at {reflection_depth} depth, providing detailed analysis.
"""

        # Process with Composio client
        response = await self.composio_client.process_request(
            prompt=reflection_prompt,
            system=system_message,
            temperature=0.5,  # Lower temperature for more deterministic reflection
            max_tokens=8000,  # Substantial but not excessive
            thinking=include_thinking,
            model=model,
            hybrid_mode=True,
            memory_context={
                "reflection_depth": reflection_depth,
                "memory_count": len(memories_to_reflect),
                "memory_types": list(memories_by_type.keys())
            }
        )
        
        # Extract reflection content
        if "choices" in response and len(response["choices"]) > 0:
            reflection_content = response["choices"][0]["message"]["content"]
            thinking_content = response["choices"][0].get("thinking", "")
            
            # Store the reflection as a metacognitive memory
            memory_id = await self.memory_manager.store_memory(
                content=reflection_content,
                memory_type="metacognitive_reflection",
                metadata={
                    "reflection_depth": reflection_depth,
                    "memory_count": len(memories_to_reflect),
                    "memory_types": list(memories_by_type.keys()),
                    "reflected_memory_ids": [m.get("id") for m in memories_to_reflect if m.get("id")],
                    "timestamp": time.time(),
                    "query": query
                },
                importance=0.9  # High importance for reflections
            )
            
            # Create relationships between the reflection and the original memories
            if self.enhanced_memory:
                for memory in memories_to_reflect:
                    memory_id_to_link = memory.get("id")
                    if memory_id_to_link:
                        await self.memory_manager.create_relationship(
                            memory_id_to_link, memory_id, "reflected_in", 1.0
                        )
            
            # Construct the final response
            reflection_result = {
                "success": True,
                "memory_id": memory_id,
                "reflection": reflection_content,
                "memory_count": len(memories_to_reflect),
                "memory_types": dict([(t, len(m)) for t, m in memories_by_type.items()]),
                "time_taken": time.time() - start_time
            }
            
            # Include thinking if requested
            if include_thinking and thinking_content:
                reflection_result["thinking"] = thinking_content
            
            return reflection_result
        else:
            return {
                "success": False,
                "error": "Failed to generate reflection",
                "reflections": [],
                "time_taken": time.time() - start_time
            } 
    
    async def process_with_hybrid_memory(
        self,
        prompt: str,
        memory_context_query: Optional[str] = None,
        memory_limit: int = 10,
        store_response: bool = True,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        planning_model: Optional[str] = None,
        execution_model: Optional[str] = None,
        memory_retrieval_strategy: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Process a request using Claude 3.7's hybrid mode with optimized memory integration.
        
        This method combines local planning and thinking with remote execution,
        enabling efficient use of memory for complex tasks.
        
        Args:
            prompt: User prompt to process
            memory_context_query: Optional query to use for memory retrieval (defaults to prompt)
            memory_limit: Maximum number of memories to retrieve
            store_response: Whether to store the response in memory
            max_tokens: Maximum tokens to generate
            model: Model to use for primary processing (defaults to client's default)
            planning_model: Model to use for planning phase (defaults to secondary model)
            execution_model: Model to use for execution phase (defaults to primary model)
            memory_retrieval_strategy: Strategy for retrieving memories
            
        Returns:
            Response dictionary with memory context
        """
        start_time = time.time()
        
        # Use prompt as memory context query if not specified
        memory_query = memory_context_query or prompt
        
        # Set up performance tracking
        performance_metrics = {
            "start_time": start_time,
            "memory_retrieval_start": time.time()
        }
        
        # Step 1: Retrieve relevant memories
        if memory_retrieval_strategy == "hybrid":
            memories = await self.memory_manager.retrieve_memories(
                memory_query, 
                limit=memory_limit,
                include_graph=True
            )
        elif memory_retrieval_strategy == "temporal":
            memories = await self.memory_manager.retrieve_recent_memories(
                limit=memory_limit,
                filter_query=memory_query if len(memory_query) > 10 else None
            )
        else: # semantic
            memories = await self.memory_manager.retrieve_memories(
                memory_query, 
                limit=memory_limit
            )
        
        performance_metrics["memory_retrieval_time"] = time.time() - performance_metrics["memory_retrieval_start"]
        performance_metrics["memory_count"] = len(memories)
        
        # Format memory context for the AI
        memory_content = self._format_memories_for_hybrid(memories)
        
        # Track memory IDs for relationships
        memory_ids = [memory.get("id") for memory in memories if memory.get("id")]
        
        # Step 2: Apply optimized hybrid processing
        performance_metrics["processing_start"] = time.time()
        
        # Create system message with memory context
        system_message = f"""You are VOT1, an advanced AI assistant enhanced with memory and cognitive capabilities, powered by Claude 3.7 Sonnet.

When responding to the user:
- Provide thoughtful, accurate, and helpful information
- Use a conversational yet professional tone
- If you don't know something, be honest about it
- Be concise unless asked for detailed information
- Respond directly to the user's question first, then provide additional context if helpful
- Leverage your expanded context window and reasoning capabilities

{memory_content}
"""

        # Process with Composio client's hybrid mode
        response = await self.composio_client.process_hybrid(
            prompt=prompt,
            system=system_message,
            planning_model=planning_model,
            execution_model=execution_model or model,
            memory_context={
                "memory_count": len(memories),
                "memory_ids": memory_ids,
                "retrieval_strategy": memory_retrieval_strategy
            }
        )
        
        performance_metrics["processing_time"] = time.time() - performance_metrics["processing_start"]
        
        # Step 3: Store response if requested
        if store_response and "choices" in response and len(response["choices"]) > 0:
            performance_metrics["store_start"] = time.time()
            
            # Extract content
            assistant_response = response["choices"][0]["message"]["content"]
            thinking_content = response["choices"][0].get("thinking", "")
            
            # Store the response
            response_memory_id = await self.memory_manager.store_memory(
                content=assistant_response,
                memory_type="assistant_response",
                metadata={
                    "prompt": prompt,
                    "timestamp": time.time(),
                    "model": execution_model or model or self.composio_client.model,
                    "processing_mode": "hybrid",
                    "related_memories": memory_ids
                },
                importance=1.0  # Default high importance for assistant responses
            )
            
            # Store thinking separately if available
            if thinking_content and len(thinking_content) > 100:
                thinking_memory_id = await self.memory_manager.store_memory(
                    content=thinking_content[:30000] if len(thinking_content) > 30000 else thinking_content,
                    memory_type="hybrid_thinking",
                    metadata={
                        "prompt": prompt,
                        "timestamp": time.time(),
                        "related_response": response_memory_id,
                        "planning_model": planning_model or self.composio_client.model,
                        "execution_model": execution_model or model or self.composio_client.model
                    },
                    importance=0.8
                )
                
                # Link thinking and response
                if self.enhanced_memory:
                    await self.memory_manager.create_relationship(
                        thinking_memory_id, response_memory_id, "informs", 1.0
                    )
            
            # Create relationships with retrieved memories
            if self.enhanced_memory and memory_ids:
                for mem_id in memory_ids:
                    await self.memory_manager.create_relationship(
                        mem_id, response_memory_id, "informed", 0.9
                    )
            
            performance_metrics["store_time"] = time.time() - performance_metrics["store_start"]
            response["memory_context"]["memory_id"] = response_memory_id
        
        # Add memory context and performance metrics to response
        response["memory_context"] = response.get("memory_context", {})
        response["memory_context"].update({
            "memory_count": len(memories),
            "memory_ids": memory_ids,
            "retrieval_strategy": memory_retrieval_strategy,
            "retrieval_time": performance_metrics["memory_retrieval_time"],
            "total_time": time.time() - start_time
        })
        
        # Add performance metrics
        response["performance"] = {
            "total_time": time.time() - start_time,
            "memory_retrieval_time": performance_metrics["memory_retrieval_time"],
            "processing_time": performance_metrics.get("processing_time", 0),
            "store_time": performance_metrics.get("store_time", 0)
        }
        
        logger.info(f"Hybrid memory processing completed in {response['performance']['total_time']:.2f}s")
        
        return response
        
    def _format_memories_for_hybrid(self, memories: List[Dict[str, Any]]) -> str:
        """
        Format memories for hybrid processing mode
        
        Args:
            memories: List of memory objects
            
        Returns:
            Formatted memory context string
        """
        if not memories:
            return ""
            
        # Organize memories by type for better structure
        memories_by_type = {}
        for memory in memories:
            memory_type = memory.get("type", "general")
            if memory_type not in memories_by_type:
                memories_by_type[memory_type] = []
            memories_by_type[memory_type].append(memory)
        
        # Create context with section for each memory type
        memory_context = "## MEMORY CONTEXT\n\n"
        
        for memory_type, type_memories in memories_by_type.items():
            # Format memory type header
            formatted_type = memory_type.replace("_", " ").title()
            memory_context += f"### {formatted_type} Memories ({len(type_memories)})\n\n"
            
            # Add each memory of this type
            for i, memory in enumerate(type_memories):
                memory_context += f"Memory #{i+1} [ID: {memory.get('id', 'unknown')}]:\n"
                
                # Format content
                content = memory.get("content", "")
                # Truncate very long content
                if len(content) > 1000:
                    content = content[:997] + "..."
                memory_context += f"- **Content**: {content}\n"
                
                # Add timestamp if available
                timestamp = memory.get("timestamp")
                if timestamp:
                    if isinstance(timestamp, (int, float)):
                        from datetime import datetime
                        formatted = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                        memory_context += f"- **Created**: {formatted}\n"
                    else:
                        memory_context += f"- **Created**: {timestamp}\n"
                
                # Add importance if available
                importance = memory.get("importance")
                if importance is not None:
                    memory_context += f"- **Importance**: {importance:.2f}\n"
                
                # Add selected metadata if available and relevant
                if "metadata" in memory and isinstance(memory["metadata"], dict):
                    relevant_keys = ["source", "topic", "tags", "category", "interaction_id"]
                    metadata_items = []
                    
                    for key in relevant_keys:
                        if key in memory["metadata"]:
                            metadata_items.append(f"{key}: {memory['metadata'][key]}")
                    
                    if metadata_items:
                        memory_context += f"- **Context**: {', '.join(metadata_items)}\n"
                
                memory_context += "\n"
        
        # Add instructions for using memories
        memory_context += """
## MEMORY USAGE INSTRUCTIONS

When using these memories in your response:
1. Draw on relevant memories to inform your understanding
2. Prioritize memories that are most relevant and recent
3. Do not mention the memory system directly unless the user asks about it
4. Integrate insights from memories naturally into your response
5. If memories contradict each other, use your judgment on which is most reliable
"""
        
        return memory_context 