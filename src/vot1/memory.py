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
        
        # Connect to SQLite database
        self.conn = sqlite3.connect(storage_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
        
        logger.info(f"Initialized VectorStore with model {model_name} at {storage_path}")
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT,
            timestamp REAL NOT NULL
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            memory_id TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            FOREIGN KEY (memory_id) REFERENCES memories(id)
        )
        ''')
        
        self.conn.commit()
    
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add content to the vector store.
        
        Args:
            content: Text content to store
            metadata: Optional metadata associated with the content
            
        Returns:
            ID of the stored memory
        """
        memory_id = str(uuid.uuid4())
        timestamp = datetime.now().timestamp()
        
        # Store memory
        self.cursor.execute(
            "INSERT INTO memories (id, content, metadata, timestamp) VALUES (?, ?, ?, ?)",
            (memory_id, content, json.dumps(metadata or {}), timestamp)
        )
        
        # Create a dummy embedding (random vector)
        embedding = np.random.rand(self.dimension).astype(np.float32)
        
        # Store embedding
        self.cursor.execute(
            "INSERT INTO embeddings (memory_id, embedding) VALUES (?, ?)",
            (memory_id, embedding.tobytes())
        )
        
        self.conn.commit()
        return memory_id
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        This is a simplified implementation that returns random results.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of similar memories with similarity scores
        """
        # Simplified implementation: return random memories
        self.cursor.execute(
            "SELECT id, content, metadata FROM memories ORDER BY RANDOM() LIMIT ?",
            (limit,)
        )
        
        results = []
        for row in self.cursor.fetchall():
            memory_id, content, metadata_str = row
            metadata = json.loads(metadata_str)
            
            # Generate a random similarity score between 0.5 and 1.0
            similarity = 0.5 + np.random.rand() * 0.5
            
            results.append({
                "id": memory_id,
                "content": content,
                "metadata": metadata,
                "similarity": similarity
            })
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory data or None if not found
        """
        self.cursor.execute(
            "SELECT content, metadata, timestamp FROM memories WHERE id = ?",
            (memory_id,)
        )
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        content, metadata_str, timestamp = row
        return {
            "id": memory_id,
            "content": content,
            "metadata": json.loads(metadata_str),
            "timestamp": timestamp
        }
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __del__(self):
        """Ensure connection is closed on object deletion."""
        try:
            self.conn.close()
        except:
            pass


class MemoryManager:
    """
    Memory management system combining vector storage and other memory types.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        memory_path: str = "memory"
    ):
        """
        Initialize the memory manager.
        
        Args:
            vector_store: VectorStore instance or None to create a new one
            memory_path: Path to the memory storage directory
        """
        self.storage_dir = memory_path
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize vector store if not provided
        self.vector_store = vector_store or VectorStore(
            storage_path=os.path.join(self.storage_dir, "vector_store.db")
        )
        
        # Conversation history
        self.conversation_history = []
        
        logger.info(f"Initialized MemoryManager with storage at {self.storage_dir}")
    
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
        self.vector_store.cursor.execute(
            "SELECT id, content, metadata FROM memories LIMIT 20"
        )
        
        for i, row in enumerate(self.vector_store.cursor.fetchall()):
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
        
        return {
            "nodes": nodes,
            "links": links
        } 