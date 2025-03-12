"""
Advanced Memory Management for VOT1

This module provides sophisticated memory capabilities for the VOT1 system,
including long-term storage, semantic search, and memory summarization.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import os
import json
import logging
import datetime
from pathlib import Path
import yaml
import time
from uuid import uuid4

logger = logging.getLogger("vot1.memory")

class Memory:
    """Base memory class that defines the interface for all memory types."""
    
    def add(self, item: Dict[str, Any]) -> str:
        """Add an item to memory and return its ID."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item from memory by ID."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory for items matching the query."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def update(self, memory_id: str, item: Dict[str, Any]) -> bool:
        """Update an item in memory."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete(self, memory_id: str) -> bool:
        """Delete an item from memory."""
        raise NotImplementedError("Subclasses must implement this method")
    
    def clear(self) -> None:
        """Clear all items from memory."""
        raise NotImplementedError("Subclasses must implement this method")

class ConversationMemory(Memory):
    """Memory for storing and retrieving conversation history with advanced features."""
    
    def __init__(self, storage_path: Optional[str] = None, max_items: int = 1000) -> None:
        """Initialize ConversationMemory.
        
        Args:
            storage_path: Path to store conversation memory
            max_items: Maximum number of items to store
        """
        self.max_items = max_items
        self.items: List[Dict[str, Any]] = []
        self.storage_path = storage_path
        
        if storage_path:
            storage_dir = Path(storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_file = storage_dir / "conversation_memory.json"
            
            # Load existing memory if available
            if self.storage_file.exists():
                try:
                    with open(self.storage_file, "r") as f:
                        self.items = json.load(f)
                        logger.info(f"Loaded {len(self.items)} items from conversation memory")
                except Exception as e:
                    logger.error(f"Error loading conversation memory: {e}")
                    self.items = []
    
    def add(self, item: Dict[str, Any]) -> str:
        """Add an item to memory and return its ID.
        
        Args:
            item: Item to add to memory, should include at least "role" and "content"
                 Additional fields like "metadata" can be included
                 
        Returns:
            ID of the added item
        """
        # Generate ID if not provided
        if "id" not in item:
            item["id"] = str(uuid4())
        
        # Add timestamp if not provided
        if "timestamp" not in item:
            item["timestamp"] = datetime.datetime.now().isoformat()
        
        # Add the item to memory
        self.items.append(item)
        
        # Trim memory if needed
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]
        
        # Save to storage if configured
        self._save_to_storage()
        
        return item["id"]
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item from memory by ID."""
        for item in self.items:
            if item.get("id") == memory_id:
                return item
        return None
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory for items matching the query (simple keyword matching).
        
        A more sophisticated implementation would use embeddings and semantic search.
        """
        results = []
        query = query.lower()
        
        for item in reversed(self.items):  # Start with most recent
            content = item.get("content", "").lower()
            if query in content:
                results.append(item)
                if len(results) >= limit:
                    break
        
        return results
    
    def search_by_date(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                      limit: int = 10) -> List[Dict[str, Any]]:
        """Search memory for items within a date range."""
        results = []
        
        # Convert date strings to datetime objects if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.fromisoformat(start_date)
        
        if end_date:
            end_dt = datetime.datetime.fromisoformat(end_date)
        
        for item in reversed(self.items):
            item_dt = datetime.datetime.fromisoformat(item.get("timestamp", ""))
            
            if start_dt and item_dt < start_dt:
                continue
            
            if end_dt and item_dt > end_dt:
                continue
            
            results.append(item)
            if len(results) >= limit:
                break
        
        return results
    
    def update(self, memory_id: str, item: Dict[str, Any]) -> bool:
        """Update an item in memory."""
        for i, existing_item in enumerate(self.items):
            if existing_item.get("id") == memory_id:
                # Preserve ID and timestamp of original item
                item["id"] = memory_id
                if "timestamp" in existing_item:
                    item["timestamp"] = existing_item["timestamp"]
                
                # Add update timestamp
                item["updated_at"] = datetime.datetime.now().isoformat()
                
                self.items[i] = item
                self._save_to_storage()
                return True
        
        return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete an item from memory."""
        for i, item in enumerate(self.items):
            if item.get("id") == memory_id:
                del self.items[i]
                self._save_to_storage()
                return True
        
        return False
    
    def clear(self) -> None:
        """Clear all items from memory."""
        self.items = []
        self._save_to_storage()
    
    def get_all(self, limit: Optional[int] = None, reverse: bool = True) -> List[Dict[str, Any]]:
        """Get all items from memory, optionally limiting the number of items returned."""
        items = self.items
        
        if reverse:
            items = list(reversed(items))
        
        if limit is not None:
            return items[:limit]
        
        return items
    
    def summarize(self, max_length: int = 500) -> str:
        """Generate a summary of the conversation history.
        
        In a more advanced implementation, this would use Claude to generate a summary.
        """
        if not self.items:
            return "No conversation history available."
        
        # Simple implementation just takes the first few items
        summary_items = self.items[-10:]  # Last 10 items
        
        summary = "Conversation Summary:\n"
        for item in summary_items:
            role = item.get("role", "unknown")
            content = item.get("content", "")
            
            # Truncate content if needed
            if len(content) > 50:
                content = content[:47] + "..."
            
            summary += f"- {role}: {content}\n"
        
        return summary
    
    def _save_to_storage(self) -> None:
        """Save memory to storage if configured."""
        if self.storage_path:
            try:
                with open(self.storage_file, "w") as f:
                    json.dump(self.items, f, indent=2)
                logger.debug(f"Saved {len(self.items)} items to conversation memory")
            except Exception as e:
                logger.error(f"Error saving conversation memory: {e}")

class SemanticMemory(Memory):
    """Memory with semantic search capabilities using embeddings (stub implementation).
    
    A full implementation would use embeddings from a model like Ada to enable
    semantic search of memories.
    """
    
    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initialize SemanticMemory."""
        self.items: Dict[str, Dict[str, Any]] = {}
        self.storage_path = storage_path
        
        if storage_path:
            storage_dir = Path(storage_path)
            storage_dir.mkdir(parents=True, exist_ok=True)
            self.storage_file = storage_dir / "semantic_memory.json"
            
            # Load existing memory if available
            if self.storage_file.exists():
                try:
                    with open(self.storage_file, "r") as f:
                        self.items = json.load(f)
                        logger.info(f"Loaded {len(self.items)} items from semantic memory")
                except Exception as e:
                    logger.error(f"Error loading semantic memory: {e}")
                    self.items = {}
    
    def add(self, item: Dict[str, Any]) -> str:
        """Add an item to memory with embedded representation."""
        # Generate ID if not provided
        if "id" not in item:
            item["id"] = str(uuid4())
        
        # Add timestamp if not provided
        if "timestamp" not in item:
            item["timestamp"] = datetime.datetime.now().isoformat()
        
        # In a real implementation, we would compute embeddings here
        # item["embedding"] = compute_embedding(item["content"])
        
        # Add the item to memory
        self.items[item["id"]] = item
        
        # Save to storage if configured
        self._save_to_storage()
        
        return item["id"]
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an item from memory by ID."""
        return self.items.get(memory_id)
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search memory using semantic similarity."""
        # In a real implementation, we would:
        # 1. Compute embedding for the query
        # 2. Calculate cosine similarity with all item embeddings
        # 3. Return top-k most similar items
        
        # For now, just return the most recent items as a placeholder
        results = list(self.items.values())
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
    
    def update(self, memory_id: str, item: Dict[str, Any]) -> bool:
        """Update an item in memory."""
        if memory_id in self.items:
            # Preserve ID and timestamp of original item
            item["id"] = memory_id
            if "timestamp" in self.items[memory_id]:
                item["timestamp"] = self.items[memory_id]["timestamp"]
            
            # Add update timestamp
            item["updated_at"] = datetime.datetime.now().isoformat()
            
            # In a real implementation, we would recompute embeddings here
            # item["embedding"] = compute_embedding(item["content"])
            
            self.items[memory_id] = item
            self._save_to_storage()
            return True
        
        return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete an item from memory."""
        if memory_id in self.items:
            del self.items[memory_id]
            self._save_to_storage()
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all items from memory."""
        self.items = {}
        self._save_to_storage()
    
    def _save_to_storage(self) -> None:
        """Save memory to storage if configured."""
        if self.storage_path:
            try:
                with open(self.storage_file, "w") as f:
                    json.dump(self.items, f, indent=2)
                logger.debug(f"Saved {len(self.items)} items to semantic memory")
            except Exception as e:
                logger.error(f"Error saving semantic memory: {e}")

class MemoryManager:
    """Central manager for different types of memory in VOT1."""
    
    def __init__(self, storage_dir: str = ".vot1/memory") -> None:
        """Initialize MemoryManager with different memory types."""
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize different memory types
        self.conversation = ConversationMemory(storage_path=f"{storage_dir}/conversation")
        self.semantic = SemanticMemory(storage_path=f"{storage_dir}/semantic")
        
        logger.info(f"Initialized MemoryManager with storage at {storage_dir}")
    
    def add_conversation_item(self, role: str, content: str, 
                             metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convenience method to add a conversation item."""
        item = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if metadata:
            item["metadata"] = metadata
        
        return self.conversation.add(item)
    
    def add_semantic_item(self, content: str, 
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Convenience method to add a semantic memory item."""
        item = {
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if metadata:
            item["metadata"] = metadata
        
        return self.semantic.add(item)
    
    def search_all(self, query: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Search all memory types and return combined results."""
        results = {
            "conversation": self.conversation.search(query, limit),
            "semantic": self.semantic.search(query, limit)
        }
        
        return results
    
    def save_all(self) -> None:
        """Force save all memory types."""
        self.conversation._save_to_storage()
        self.semantic._save_to_storage()
        logger.info("Saved all memory types")
    
    def clear_all(self) -> None:
        """Clear all memory types."""
        self.conversation.clear()
        self.semantic.clear()
        logger.info("Cleared all memory types")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        return {
            "conversation_items": len(self.conversation.items),
            "semantic_items": len(self.semantic.items),
            "storage_dir": self.storage_dir
        } 