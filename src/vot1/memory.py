#!/usr/bin/env python3
"""
VOT1 Memory Management System

This module provides a memory management system for VOT1, including vector storage
for semantic memory and conversation history management.
"""

import os
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """
    Basic vector storage for semantic search capabilities.
    
    This is a simplified implementation for testing purposes.
    """
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        dimension: int = 384,
        storage_path: str = "memory/vector_store.db"
    ):
        """
        Initialize the vector store.
        
        Args:
            model_name: Name of the sentence transformer model to use for embeddings
            dimension: Dimension of the embeddings
            storage_path: Path to store the vector database
        """
        self.dimension = dimension
        self.storage_path = storage_path
        self.model_name = model_name
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logger.info(f"Initialized VectorStore with model {model_name} at {storage_path}")
    
    def _get_connection(self):
        """Get a thread-local connection to the database."""
        return sqlite3.connect(self.storage_path)
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp REAL NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                memory_id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add content to the vector store.
        
        Args:
            content: Text content to store
            metadata: Additional information about this content
            
        Returns:
            ID of the stored content
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.now().timestamp()
        
        # Serialize metadata
        metadata_json = json.dumps(metadata or {})
        
        # Generate embedding (mock implementation)
        embedding = np.random.rand(self.dimension).astype(np.float32)
        embedding_blob = embedding.tobytes()
        
        # Store in database
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO memories (id, content, metadata, timestamp) VALUES (?, ?, ?, ?)",
                (memory_id, content, metadata_json, timestamp)
            )
            
            cursor.execute(
                "INSERT INTO embeddings (memory_id, embedding) VALUES (?, ?)",
                (memory_id, embedding_blob)
            )
            
            conn.commit()
        finally:
            conn.close()
        
        return memory_id
    
    def search(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of results with similarity scores
        """
        # In a real implementation, we would:
        # 1. Generate an embedding for the query
        # 2. Find the nearest neighbors in the vector space
        # 3. Return the corresponding memories
        
        # For this mock implementation, we'll just return random memories
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, content, metadata, timestamp FROM memories ORDER BY RANDOM() LIMIT ?",
                (limit,)
            )
            
            results = []
            for row in cursor.fetchall():
                memory_id, content, metadata_json, timestamp = row
                metadata = json.loads(metadata_json)
                
                # Generate a random similarity score
                similarity = np.random.rand()
                
                results.append({
                    "id": memory_id,
                    "content": content,
                    "metadata": metadata,
                    "timestamp": timestamp,
                    "similarity": float(similarity)
                })
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            return results
        finally:
            conn.close()
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory data or None if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT content, metadata, timestamp FROM memories WHERE id = ?",
                (memory_id,)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            content, metadata_json, timestamp = row
            metadata = json.loads(metadata_json)
            
            return {
                "id": memory_id,
                "content": content,
                "metadata": metadata,
                "timestamp": timestamp
            }
        finally:
            conn.close()
    
    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Check if memory exists
            cursor.execute("SELECT 1 FROM memories WHERE id = ?", (memory_id,))
            if not cursor.fetchone():
                return False
            
            # Delete from embeddings table
            cursor.execute("DELETE FROM embeddings WHERE memory_id = ?", (memory_id,))
            
            # Delete from memories table
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            conn.commit()
            return True
        finally:
            conn.close()
    
    def clear(self):
        """Clear all memories from the store."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM embeddings")
            cursor.execute("DELETE FROM memories")
            
            conn.commit()
        finally:
            conn.close()


class MemoryManager:
    """
    Memory management system for VOT1.
    
    This class manages different types of memory, including:
    - Semantic memory (vector store)
    - Conversation history
    - Project memory
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        memory_path: str = "memory",
        max_conversation_history: int = 100,
        auto_cleanup_threshold: int = 1000,
        compression_enabled: bool = True,
        compression_ratio: float = 0.5
    ):
        """
        Initialize the memory manager.
        
        Args:
            vector_store: Vector store instance (created if None)
            memory_path: Path to store memory files
            max_conversation_history: Maximum number of conversation entries to keep
            auto_cleanup_threshold: Number of entries before auto cleanup is triggered
            compression_enabled: Whether to use memory compression
            compression_ratio: Compression ratio for vector embeddings (0.0-1.0)
        """
        # Create directory if it doesn't exist
        os.makedirs(memory_path, exist_ok=True)
        
        # Initialize vector store if not provided
        self.vector_store = vector_store or VectorStore(
            storage_path=os.path.join(memory_path, "vector_store.db")
        )
        
        self.memory_path = memory_path
        self.conversation_path = os.path.join(memory_path, "conversations")
        os.makedirs(self.conversation_path, exist_ok=True)
        
        # Initialize conversation memory file
        self.conversation_file = os.path.join(self.conversation_path, "current_conversation.json")
        if not os.path.exists(self.conversation_file):
            with open(self.conversation_file, "w") as f:
                json.dump([], f)
        
        # Memory optimization settings
        self.max_conversation_history = max_conversation_history
        self.auto_cleanup_threshold = auto_cleanup_threshold
        self.compression_enabled = compression_enabled
        self.compression_ratio = compression_ratio
        self.memory_stats = {
            "total_memories": 0,
            "compressed_memories": 0,
            "last_cleanup": datetime.now().timestamp(),
            "cleanup_count": 0
        }
        
        # Load memory statistics if they exist
        self.stats_file = os.path.join(memory_path, "memory_stats.json")
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    self.memory_stats.update(json.load(f))
            except:
                logger.warning("Failed to load memory statistics, using defaults")
        
        logger.info(f"Initialized MemoryManager with storage at {memory_path}")
    
    def add_semantic_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add semantic memory that can be searched later.
        
        Args:
            content: Text content to remember
            metadata: Additional information about this memory
            
        Returns:
            ID of the stored memory
        """
        # Add type information to metadata
        metadata = metadata or {}
        if "type" not in metadata:
            metadata["type"] = "semantic"
        
        # Add to vector store
        memory_id = self.vector_store.add(content, metadata)
        
        logger.debug(f"Added semantic memory: {content[:50]}... [id: {memory_id}]")
        return memory_id
    
    def add_conversation_memory(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add an entry to the conversation history.
        
        Args:
            role: Role of the speaker (user, assistant, system, etc.)
            content: Message content
            metadata: Additional information about this message
            
        Returns:
            The conversation memory entry
        """
        # Create memory entry
        memory = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().timestamp(),
            "metadata": metadata or {}
        }
        
        # Add to conversation history
        self.conversation_history.append(memory)
        
        # Add to semantic memory as well for search
        self.add_semantic_memory(
            content=content,
            metadata={
                "type": "conversation",
                "role": role,
                "conversation_id": memory["id"],
                **(metadata or {})
            }
        )
        
        logger.debug(f"Added conversation memory: {role} - {content[:50]}...")
        return memory
    
    def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for memories similar to the query.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            memory_types: Optional filter for memory types
            
        Returns:
            List of memories with similarity scores
        """
        # Search vector store
        results = self.vector_store.search(query, limit=limit)
        
        # Filter by memory type if specified
        if memory_types:
            results = [
                r for r in results 
                if r.get("metadata", {}).get("type") in memory_types
            ]
        
        return results
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Alias for search_memories that supports the API expected by McpHybridAutomation.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of memories with similarity scores
        """
        return self.search_memories(query, limit=limit)
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent memories.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of recent memories
        """
        try:
            # Query the most recent memories from the vector store
            self.vector_store.cursor.execute(
                """
                SELECT id, content, metadata, timestamp 
                FROM memories 
                ORDER BY timestamp DESC
                LIMIT ?
                """, 
                (limit,)
            )
            
            results = []
            for row in self.vector_store.cursor.fetchall():
                memory_id, content, metadata_str, timestamp = row
                metadata = json.loads(metadata_str) if metadata_str else {}
                
                results.append({
                    "id": memory_id,
                    "content": content,
                    "metadata": metadata,
                    "timestamp": timestamp
                })
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving recent memories: {e}")
            return []
    
    def get_conversation_history(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            limit: Optional limit on number of messages to return
            
        Returns:
            List of conversation messages
        """
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        
    def get_memory_graph(self) -> Dict[str, Any]:
        """
        Get a graph representation of memories for visualization.
        
        Returns:
            Dictionary with nodes and links for visualization
        """
        # Simplified implementation for testing purposes
        nodes = []
        links = []
        
        # Get some memories from the vector store
        conn = self.vector_store._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, content, metadata FROM memories LIMIT 20"
            )
            
            for i, row in enumerate(cursor.fetchall()):
                memory_id, content, metadata_str = row
                metadata = json.loads(metadata_str)
                memory_type = metadata.get("type", "default")
                
                # Create node
                node = {
                    "id": memory_id,
                    "label": content[:20] + "..." if len(content) > 20 else content,
                    "type": memory_type,
                    "size": 1.0,
                    "x": (np.random.rand() - 0.5) * 100,
                    "y": (np.random.rand() - 0.5) * 100, 
                    "z": (np.random.rand() - 0.5) * 100
                }
                nodes.append(node)
                
                # Create some random links between nodes
                if i > 0 and np.random.rand() < 0.5:
                    target_idx = np.random.randint(0, i)
                    links.append({
                        "source": memory_id,
                        "target": nodes[target_idx]["id"],
                        "value": np.random.rand()
                    })
        finally:
            conn.close()
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    async def optimize_memory(self) -> Dict[str, Any]:
        """
        Optimize memory usage by cleaning up old, low-relevance memories and compressing vectors.
        
        Returns:
            Dictionary with optimization statistics
        """
        start_time = datetime.now()
        stats = {
            "memories_before": 0,
            "memories_after": 0,
            "bytes_saved": 0,
            "duration_seconds": 0
        }
        
        try:
            # Get connection to vector database
            conn = self.vector_store._get_connection()
            cursor = conn.cursor()
            
            # Count memories before optimization
            cursor.execute("SELECT COUNT(*) FROM memories")
            stats["memories_before"] = cursor.fetchone()[0]
            
            # Get database size before optimization
            cursor.execute("PRAGMA page_count")
            page_count_before = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            size_before = page_count_before * page_size
            
            # Identify low-relevance memories based on access patterns and age
            # Keep memories that are frequently accessed or recently added
            thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            
            # Find candidates for removal - old and rarely accessed memories
            cursor.execute("""
                SELECT id FROM memories 
                WHERE timestamp < ? 
                ORDER BY timestamp ASC 
                LIMIT 100
            """, (thirty_days_ago,))
            
            candidates = [row[0] for row in cursor.fetchall()]
            
            # Only remove a percentage of candidates to avoid aggressive cleanup
            to_remove = candidates[:int(len(candidates) * 0.5)]
            
            # Delete low-relevance memories
            for memory_id in to_remove:
                self.vector_store.delete(memory_id)
            
            # Vacuum database to reclaim space
            cursor.execute("VACUUM")
            
            # Get new database size
            cursor.execute("PRAGMA page_count")
            page_count_after = cursor.fetchone()[0]
            size_after = page_count_after * page_size
            
            # Update stats
            cursor.execute("SELECT COUNT(*) FROM memories")
            stats["memories_after"] = cursor.fetchone()[0]
            stats["bytes_saved"] = max(0, size_before - size_after)
            
            # Clean up conversation history if it exceeds the limit
            if await self._conversation_count() > self.max_conversation_history:
                await self._trim_conversation_history()
            
            # Update memory stats
            self.memory_stats["last_cleanup"] = datetime.now().timestamp()
            self.memory_stats["cleanup_count"] += 1
            self.memory_stats["total_memories"] = stats["memories_after"]
            
            # Save stats
            with open(self.stats_file, "w") as f:
                json.dump(self.memory_stats, f)
            
            conn.close()
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            stats["error"] = str(e)
        
        stats["duration_seconds"] = (datetime.now() - start_time).total_seconds()
        return stats
    
    async def _trim_conversation_history(self) -> int:
        """
        Trim conversation history to the maximum allowed size.
        
        Returns:
            Number of entries removed
        """
        try:
            # Load current conversation
            conversations = []
            with open(self.conversation_file, "r") as f:
                conversations = json.load(f)
            
            # Calculate how many entries to remove
            current_count = len(conversations)
            entries_to_keep = self.max_conversation_history
            entries_to_remove = max(0, current_count - entries_to_keep)
            
            if entries_to_remove > 0:
                # Keep the most recent entries
                conversations = conversations[-entries_to_keep:]
                
                # Save trimmed conversation
                with open(self.conversation_file, "w") as f:
                    json.dump(conversations, f)
                
                logger.info(f"Trimmed conversation history, removed {entries_to_remove} entries")
                return entries_to_remove
            return 0
        except Exception as e:
            logger.error(f"Error trimming conversation history: {e}")
            return 0
    
    async def _conversation_count(self) -> int:
        """Get the number of entries in the conversation history."""
        try:
            with open(self.conversation_file, "r") as f:
                conversations = json.load(f)
            return len(conversations)
        except:
            return 0
    
    async def check_memory_health(self) -> Dict[str, Any]:
        """
        Check the health of the memory system.
        
        Returns:
            Dictionary with health statistics
        """
        health = {
            "total_memories": 0,
            "vector_store_size_bytes": 0,
            "conversation_count": 0,
            "conversation_size_bytes": 0,
            "last_cleanup": self.memory_stats.get("last_cleanup", 0),
            "cleanup_count": self.memory_stats.get("cleanup_count", 0),
            "status": "healthy"
        }
        
        try:
            # Check vector store health
            conn = self.vector_store._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memories")
            health["total_memories"] = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            health["vector_store_size_bytes"] = page_count * page_size
            
            # Check if optimization is needed
            if health["total_memories"] > self.auto_cleanup_threshold:
                health["status"] = "needs_optimization"
            
            conn.close()
            
            # Check conversation health
            health["conversation_count"] = await self._conversation_count()
            if os.path.exists(self.conversation_file):
                health["conversation_size_bytes"] = os.path.getsize(self.conversation_file)
            
            if health["conversation_count"] > self.max_conversation_history:
                health["status"] = "needs_optimization"
            
        except Exception as e:
            logger.error(f"Error checking memory health: {e}")
            health["status"] = "error"
            health["error"] = str(e)
        
        return health
    
    async def advanced_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Advanced semantic search with filtering.
        
        Args:
            query: Search query
            filters: Metadata filters to apply
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching memory entries
        """
        # Start with basic vector search
        results = self.vector_store.search(query, limit=limit * 2)  # Get more results for filtering
        
        # Apply filters if provided
        if filters and isinstance(filters, dict):
            filtered_results = []
            for result in results:
                # Skip entries below threshold
                if result.get("score", 0) < threshold:
                    continue
                
                # Apply metadata filters
                metadata = result.get("metadata", {})
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                
                # Check if all filters match
                matches = True
                for key, value in filters.items():
                    if key not in metadata or metadata[key] != value:
                        matches = False
                        break
                
                if matches:
                    filtered_results.append(result)
            
            results = filtered_results[:limit]
        else:
            # Just apply threshold
            results = [r for r in results if r.get("score", 0) >= threshold][:limit]
        
        return results 