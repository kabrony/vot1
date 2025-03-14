#!/usr/bin/env python3
"""
Memory Manager Module

This module provides a comprehensive memory management system for storing and
retrieving structured data with optimized performance and organization.
"""

import os
import json
import shutil
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryError(Exception):
    """Base exception for memory-related errors"""
    pass

class MemoryManager:
    """
    A comprehensive memory management system for storing and retrieving structured data
    with optimized performance and organization.
    """
    
    def __init__(
        self, 
        base_path: Optional[str] = None,
        auto_create_dirs: bool = True,
        use_compression: bool = False
    ):
        """
        Initialize the Memory Manager.
        
        Args:
            base_path: Base directory for storing memory, defaults to ~/.vot1/memory
            auto_create_dirs: Automatically create directories when saving
            use_compression: Whether to compress stored data (not implemented yet)
        """
        if base_path is None:
            # Default to user's home directory
            home_dir = os.path.expanduser("~")
            base_path = os.path.join(home_dir, ".vot1", "memory")
        
        self.base_path = os.path.abspath(base_path)
        self.auto_create_dirs = auto_create_dirs
        self.use_compression = use_compression
        
        # Create base directory if it doesn't exist
        if auto_create_dirs and not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                logger.info(f"Created memory base directory: {self.base_path}")
            except Exception as e:
                logger.error(f"Failed to create memory base directory: {e}")
                raise MemoryError(f"Failed to create memory base directory: {e}")
        
        # Initialize in-memory cache for frequently accessed data
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        logger.info(f"Memory Manager initialized with base path: {self.base_path}")
    
    def _get_category_path(self, category: str) -> str:
        """
        Get the directory path for a category.
        
        Args:
            category: Memory category
            
        Returns:
            Path to the category directory
        """
        # Normalize category name
        category = category.strip().lower().replace(" ", "_")
        return os.path.join(self.base_path, category)
    
    def _get_file_path(self, category: str, key: str) -> str:
        """
        Get the file path for a specific memory key.
        
        Args:
            category: Memory category
            key: Memory key
            
        Returns:
            Path to the memory file
        """
        # Normalize key name
        key = key.strip().replace(" ", "_").replace("/", "_")
        return os.path.join(self._get_category_path(category), f"{key}.json")
    
    def _build_cache_key(self, category: str, key: str) -> str:
        """
        Build a cache key from category and key.
        
        Args:
            category: Memory category
            key: Memory key
            
        Returns:
            Cache key string
        """
        return f"{category}:{key}"
    
    def list_categories(self) -> List[str]:
        """
        List all memory categories.
            
        Returns:
            List of category names
        """
        try:
            if not os.path.exists(self.base_path):
                return []
            
            categories = []
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    categories.append(item)
            
            return sorted(categories)
        
        except Exception as e:
            logger.error(f"Error listing categories: {e}")
            return []
    
    def list_keys(self, category: str) -> List[str]:
        """
        List all memory keys in a category.
        
        Args:
            category: Memory category
            
        Returns:
            List of memory keys
        """
        try:
            category_path = self._get_category_path(category)
            if not os.path.exists(category_path):
                return []
            
            keys = []
            for item in os.listdir(category_path):
                if item.endswith(".json"):
                    keys.append(item[:-5])  # Remove .json extension
            
            return sorted(keys)
        
        except Exception as e:
            logger.error(f"Error listing keys for category '{category}': {e}")
            return []
    
    def save(self, category: str, key: str, data: Any) -> bool:
        """
        Save data to memory.
        
        Args:
            category: Memory category
            key: Memory key
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file path
            category_path = self._get_category_path(category)
            file_path = self._get_file_path(category, key)
            
            # Create category directory if it doesn't exist
            if self.auto_create_dirs and not os.path.exists(category_path):
                os.makedirs(category_path, exist_ok=True)
            
            # Add metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "category": category,
                "key": key
            }
            
            # Prepare data for storage
            storage_data = {
                "metadata": metadata,
                "data": data
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2)
            
            # Update cache
            cache_key = self._build_cache_key(category, key)
            self.cache[cache_key] = data
            
            logger.debug(f"Saved data to {category}/{key}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving memory {category}/{key}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def load(self, category: str, key: str) -> Optional[Any]:
        """
        Load data from memory.
        
        Args:
            category: Memory category
            key: Memory key
            
        Returns:
            Loaded data or None if not found
        """
        try:
            # Check cache first
            cache_key = self._build_cache_key(category, key)
            if cache_key in self.cache:
                self.cache_hits += 1
                logger.debug(f"Cache hit for {category}/{key}")
                return self.cache[cache_key]
            
            self.cache_misses += 1
            
            # Get file path
            file_path = self._get_file_path(category, key)
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.debug(f"Memory not found for {category}/{key}")
                return None
            
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                storage_data = json.load(f)
            
            # Extract data
            data = storage_data.get("data")
            
            # Update cache
            self.cache[cache_key] = data
            
            logger.debug(f"Loaded data from {category}/{key}")
            return data
        
        except Exception as e:
            logger.error(f"Error loading memory {category}/{key}: {e}")
            return None
    
    def delete(self, category: str, key: str) -> bool:
        """
        Delete data from memory.
        
        Args:
            category: Memory category
            key: Memory key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file path
            file_path = self._get_file_path(category, key)
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.debug(f"Memory not found for {category}/{key}")
                return False
            
            # Delete file
            os.remove(file_path)
            
            # Remove from cache
            cache_key = self._build_cache_key(category, key)
            if cache_key in self.cache:
                del self.cache[cache_key]
            
            logger.debug(f"Deleted memory {category}/{key}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting memory {category}/{key}: {e}")
            return False
    
    def delete_category(self, category: str) -> bool:
        """
        Delete an entire category from memory.
        
        Args:
            category: Memory category
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get category path
            category_path = self._get_category_path(category)
            
            # Check if directory exists
            if not os.path.exists(category_path):
                logger.debug(f"Category not found: {category}")
                return False
            
            # Delete directory
            shutil.rmtree(category_path)
            
            # Remove from cache
            category_prefix = f"{category}:"
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(category_prefix)]
            for k in keys_to_remove:
                del self.cache[k]
            
            logger.debug(f"Deleted category: {category}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting category {category}: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.debug("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache usage statistics.
        
        Returns:
            Dict containing cache statistics
        """
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_ratio": self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
        }
    
    def search(self, query: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for memories matching the query.
        
        Args:
            query: Search query
            categories: Optional list of categories to search in
        
        Returns:
            List of matching memories with metadata
        """
        try:
            query = query.lower()
            results = []
            
            # Get categories to search
            if categories is None:
                categories = self.list_categories()
            
            # Search in each category
            for category in categories:
                category_path = self._get_category_path(category)
                if not os.path.exists(category_path):
                    continue
                
                for key in self.list_keys(category):
                    # Check if query matches key
                    if query in key.lower():
                        data = self.load(category, key)
                        if data is not None:
                            results.append({
                                "category": category,
                                "key": key,
                                "data": data,
                                "match_type": "key"
                            })
                        continue
                    
                    # Load data and search in content
                    data = self.load(category, key)
                    if data is None:
                        continue
                    
                    # Convert data to string for searching
                    data_str = json.dumps(data).lower()
                    if query in data_str:
                        results.append({
                            "category": category,
                            "key": key,
                            "data": data,
                            "match_type": "content"
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get information about the memory storage.
            
        Returns:
            Dict containing memory information
        """
        try:
            info = {
                "base_path": self.base_path,
                "categories": {},
                "total_memories": 0,
                "total_size_bytes": 0
            }
            
            # Get categories
            categories = self.list_categories()
            for category in categories:
                category_path = self._get_category_path(category)
                keys = self.list_keys(category)
                
                # Calculate size
                category_size = 0
                for key in keys:
                    file_path = self._get_file_path(category, key)
                    if os.path.exists(file_path):
                        category_size += os.path.getsize(file_path)
                
                info["categories"][category] = {
                    "memory_count": len(keys),
                    "size_bytes": category_size
                }
                
                info["total_memories"] += len(keys)
                info["total_size_bytes"] += category_size
            
            return info
        
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {"error": str(e)}