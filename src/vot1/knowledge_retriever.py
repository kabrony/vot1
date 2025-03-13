"""
VOT1 Knowledge Retriever Module

This module provides efficient access to knowledge stored in the VOT1 memory graph,
with semantic search capabilities, filtering, and relevance ranking.
"""

import os
import re
import json
import math
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# For vectorization and similarity
try:
    import tensorflow as tf
    import tensorflow_hub as hub
    USE_TENSORFLOW = True
except ImportError:
    USE_TENSORFLOW = False
    
try:
    import torch
    from sentence_transformers import SentenceTransformer
    USE_TORCH = True
except ImportError:
    USE_TORCH = False

# Local imports
try:
    from vot1.memory_graph import MemoryGraph
except ImportError:
    # Relative imports for when imported from the same directory
    from memory_graph import MemoryGraph

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/knowledge_retriever.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    """
    Provides efficient access to knowledge stored in the VOT1 memory graph.
    
    Features:
    - Semantic search using embeddings
    - Keyword-based search
    - Filtering by metadata and tags
    - Relevance ranking
    - Caching for performance
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the knowledge retriever with configuration.
        
        Args:
            config_path: Path to configuration file (JSON)
        """
        self.config = self._load_config(config_path)
        self.memory_graph = MemoryGraph()
        
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
        
        # Cache for embeddings to avoid recomputing
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Cache expiry settings
        self.cache_expiry = self.config.get("cache_expiry", 3600)  # 1 hour default
        self.last_cache_cleanup = time.time()
        
        logger.info("Knowledge Retriever initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "search_mode": "semantic",
            "cache_size": 1000,  # Max number of embeddings to cache
            "cache_expiry": 3600,  # Time in seconds before cache entries expire
            "default_top_k": 10,  # Default number of results to return
            "minimum_similarity": 0.6,  # Minimum similarity score for semantic search
            "reranking": {
                "enabled": True,
                "recency_weight": 0.2,  # 0-1, higher means more recent items ranked higher
                "connectivity_weight": 0.1,  # 0-1, higher means more connected items ranked higher
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    for key, value in user_config.items():
                        if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                            # Merge nested dictionaries
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Loaded knowledge retriever configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {str(e)}")
                logger.info("Using default configuration")
        else:
            logger.info("Using default configuration")
            
        return default_config
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model based on available libraries."""
        model_name = self.config.get("embedding_model")
        
        if USE_TORCH:
            try:
                logger.info(f"Initializing SentenceTransformer model: {model_name}")
                model = SentenceTransformer(model_name)
                logger.info("SentenceTransformer model initialized successfully")
                return model
            except Exception as e:
                logger.error(f"Error initializing SentenceTransformer: {str(e)}")
        
        if USE_TENSORFLOW:
            try:
                logger.info("Initializing Universal Sentence Encoder")
                model = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
                logger.info("Universal Sentence Encoder initialized successfully")
                return model
            except Exception as e:
                logger.error(f"Error initializing Universal Sentence Encoder: {str(e)}")
        
        logger.warning("No embedding model could be initialized. Semantic search will be unavailable.")
        return None
    
    def search(self, query: str, filters: Dict[str, Any] = None, 
              max_results: int = None) -> List[Dict[str, Any]]:
        """
        Search for nodes in the memory graph based on query and filters.
        
        Args:
            query: Search query string
            filters: Dictionary of metadata filters
            max_results: Maximum number of results to return
            
        Returns:
            List of matching nodes
        """
        if not max_results:
            max_results = self.config.get("default_top_k", 10)
            
        if not filters:
            filters = {}
            
        search_mode = self.config.get("search_mode", "semantic")
        
        # Perform semantic search if model is available
        if search_mode == "semantic" and self.embedding_model is not None:
            results = self._semantic_search(query, filters, max_results)
        else:
            # Fall back to keyword search
            results = self._keyword_search(query, filters, max_results)
            
        # Apply reranking if enabled
        if self.config.get("reranking", {}).get("enabled", True):
            results = self._rerank_results(results, query)
            
        # Limit to max_results
        return results[:max_results]
    
    def _semantic_search(self, query: str, filters: Dict[str, Any], 
                        max_results: int) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query string
            filters: Dictionary of metadata filters
            max_results: Maximum number of results to return
            
        Returns:
            List of matching nodes with similarity scores
        """
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            
            # Get all nodes that match filters
            nodes = self.memory_graph.get_all_nodes()
            filtered_nodes = self._apply_filters(nodes, filters)
            
            # Calculate similarity with each node
            similarities = []
            
            for node in filtered_nodes:
                # Create a text representation of the node
                node_text = f"{node['title']} {node['content']}"
                if node.get('tags'):
                    node_text += " " + " ".join(node['tags'])
                
                # Get node embedding
                node_embedding = self._get_embedding(node_text)
                
                # Calculate similarity
                similarity = self._calculate_similarity(query_embedding, node_embedding)
                
                # Apply minimum similarity threshold
                min_similarity = self.config.get("minimum_similarity", 0.6)
                if similarity >= min_similarity:
                    similarities.append((node, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Extract nodes and add similarity scores
            results = []
            for node, similarity in similarities[:max_results]:
                node_with_score = node.copy()
                node_with_score['similarity_score'] = float(similarity)
                results.append(node_with_score)
                
            logger.info(f"Semantic search for '{query}' found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            # Fall back to keyword search
            logger.info("Falling back to keyword search")
            return self._keyword_search(query, filters, max_results)
    
    def _keyword_search(self, query: str, filters: Dict[str, Any], 
                       max_results: int) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search.
        
        Args:
            query: Search query string
            filters: Dictionary of metadata filters
            max_results: Maximum number of results to return
            
        Returns:
            List of matching nodes with match scores
        """
        # Get all nodes that match filters
        nodes = self.memory_graph.get_all_nodes()
        filtered_nodes = self._apply_filters(nodes, filters)
        
        # Prepare query for matching
        query_terms = query.lower().split()
        
        # Calculate match scores for each node
        matches = []
        
        for node in filtered_nodes:
            # Create a text representation of the node
            title = node.get('title', '').lower()
            content = node.get('content', '').lower()
            tags = " ".join(node.get('tags', [])).lower()
            
            # Count matches in title (with higher weight), content, and tags
            score = 0
            
            # Title matches carry more weight
            for term in query_terms:
                if term in title:
                    score += 3 * title.count(term)
                if term in content:
                    score += content.count(term)
                if term in tags:
                    score += 2 * tags.count(term)
            
            # Only include nodes with at least one match
            if score > 0:
                node_with_score = node.copy()
                node_with_score['match_score'] = score
                matches.append((node_with_score, score))
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Extract nodes
        results = [node for node, _ in matches[:max_results]]
        
        logger.info(f"Keyword search for '{query}' found {len(results)} results")
        return results
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for the given text, using cache if available.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Check cache for the embedding
        if text in self.embedding_cache:
            self.cache_hits += 1
            cache_entry = self.embedding_cache[text]
            
            # Check if the cache entry has expired
            if time.time() - cache_entry["timestamp"] < self.cache_expiry:
                return cache_entry["embedding"]
            
            # Cache entry has expired
            del self.embedding_cache[text]
        
        self.cache_misses += 1
        
        # Clean up cache if it's time
        if time.time() - self.last_cache_cleanup > 300:  # 5 minutes
            self._cleanup_cache()
            
        # Generate the embedding
        if isinstance(self.embedding_model, SentenceTransformer):
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        else:
            # Assume TensorFlow model
            embedding = self.embedding_model([text])[0].numpy()
        
        # Store in cache
        if len(self.embedding_cache) < self.config.get("cache_size", 1000):
            self.embedding_cache[text] = {
                "embedding": embedding,
                "timestamp": time.time()
            }
            
        return embedding
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        now = time.time()
        expired_keys = []
        
        for key, entry in self.embedding_cache.items():
            if now - entry["timestamp"] > self.cache_expiry:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.embedding_cache[key]
            
        self.last_cache_cleanup = now
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (0-1)
        """
        # Normalize the embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0
            
        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        similarity = dot_product / (norm1 * norm2)
        
        return similarity
    
    def _apply_filters(self, nodes: List[Dict[str, Any]], 
                      filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of nodes.
        
        Args:
            nodes: List of nodes to filter
            filters: Dictionary of filters to apply
            
        Returns:
            List of nodes that match the filters
        """
        if not filters:
            return nodes
            
        filtered_nodes = []
        
        for node in nodes:
            match = True
            
            # Filter by tags
            if 'tags' in filters:
                filter_tags = filters['tags']
                if isinstance(filter_tags, list):
                    # Check if all required tags are present
                    node_tags = node.get('tags', [])
                    for tag in filter_tags:
                        if tag not in node_tags:
                            match = False
                            break
                else:
                    # Single tag filter
                    if filter_tags not in node.get('tags', []):
                        match = False
            
            # Filter by node type
            if 'node_type' in filters and node.get('node_type') != filters['node_type']:
                match = False
            
            # Filter by date range
            if 'date_range' in filters:
                date_range = filters['date_range']
                node_date = node.get('created_at') or node.get('updated_at')
                
                if node_date:
                    if isinstance(node_date, str):
                        node_date = datetime.fromisoformat(node_date)
                        
                    if 'start' in date_range and node_date < date_range['start']:
                        match = False
                    if 'end' in date_range and node_date > date_range['end']:
                        match = False
            
            # Filter by metadata
            if 'metadata' in filters:
                metadata_filters = filters['metadata']
                node_metadata = node.get('metadata', {})
                
                for key, value in metadata_filters.items():
                    if key not in node_metadata or node_metadata[key] != value:
                        match = False
                        break
            
            if match:
                filtered_nodes.append(node)
        
        return filtered_nodes
    
    def _rerank_results(self, results: List[Dict[str, Any]], 
                       query: str) -> List[Dict[str, Any]]:
        """
        Rerank search results based on recency and connectivity.
        
        Args:
            results: List of search results
            query: Original search query
            
        Returns:
            Reranked list of results
        """
        if not results:
            return results
            
        reranking_config = self.config.get("reranking", {})
        recency_weight = reranking_config.get("recency_weight", 0.2)
        connectivity_weight = reranking_config.get("connectivity_weight", 0.1)
        
        # Skip reranking if weights are zero
        if recency_weight == 0 and connectivity_weight == 0:
            return results
            
        # Get base similarity scores (normalize to 0-1)
        base_scores = {}
        max_score = 0
        
        for node in results:
            score = node.get('similarity_score', 0)
            if 'match_score' in node:
                # For keyword search results
                score = node['match_score']
                max_score = max(max_score, score)
                
            base_scores[node['id']] = score
        
        # Normalize keyword search scores
        if max_score > 0:
            for node_id in base_scores:
                if max_score > 1:  # Only normalize if scores are not already 0-1
                    base_scores[node_id] /= max_score
        
        # Calculate recency scores
        recency_scores = {}
        
        if recency_weight > 0:
            # Find the most recent node
            latest_time = datetime.min
            
            for node in results:
                node_time = node.get('updated_at') or node.get('created_at')
                if isinstance(node_time, str):
                    node_time = datetime.fromisoformat(node_time)
                
                if node_time and node_time > latest_time:
                    latest_time = node_time
            
            # Calculate recency score for each node
            if latest_time > datetime.min:
                for node in results:
                    node_time = node.get('updated_at') or node.get('created_at')
                    if isinstance(node_time, str):
                        node_time = datetime.fromisoformat(node_time)
                    
                    if node_time:
                        # Calculate days difference
                        time_diff = (latest_time - node_time).total_seconds() / 86400  # seconds in a day
                        # Exponential decay based on recency
                        recency_score = math.exp(-0.1 * time_diff)  # Adjust decay rate as needed
                        recency_scores[node['id']] = recency_score
        
        # Calculate connectivity scores
        connectivity_scores = {}
        
        if connectivity_weight > 0:
            # Get all links
            links = self.memory_graph.get_all_links()
            
            # Count connections for each node
            connection_counts = {}
            
            for node in results:
                node_id = node['id']
                connection_counts[node_id] = 0
                
                for link in links:
                    if link['source_id'] == node_id or link['target_id'] == node_id:
                        connection_counts[node_id] += 1
            
            # Normalize connection counts
            max_connections = max(connection_counts.values()) if connection_counts else 0
            
            if max_connections > 0:
                for node_id, count in connection_counts.items():
                    connectivity_scores[node_id] = count / max_connections
        
        # Calculate final scores and rerank
        final_scores = {}
        
        for node in results:
            node_id = node['id']
            base_score = base_scores.get(node_id, 0)
            recency_score = recency_scores.get(node_id, 0)
            connectivity_score = connectivity_scores.get(node_id, 0)
            
            # Calculate weighted score
            base_weight = 1 - recency_weight - connectivity_weight
            final_score = (
                base_weight * base_score +
                recency_weight * recency_score +
                connectivity_weight * connectivity_score
            )
            
            final_scores[node_id] = final_score
            
            # Add scores to node for debugging/transparency
            node['final_score'] = final_score
            if recency_weight > 0:
                node['recency_score'] = recency_scores.get(node_id, 0)
            if connectivity_weight > 0:
                node['connectivity_score'] = connectivity_scores.get(node_id, 0)
        
        # Sort by final score
        results.sort(key=lambda x: final_scores.get(x['id'], 0), reverse=True)
        
        return results
    
    def get_related_nodes(self, node_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get nodes related to a specific node based on links and semantic similarity.
        
        Args:
            node_id: ID of the node to find related nodes for
            max_results: Maximum number of related nodes to return
            
        Returns:
            List of related nodes with relevance scores
        """
        # Get the source node
        source_node = self.memory_graph.get_node(node_id)
        
        if not source_node:
            logger.error(f"Node with ID {node_id} not found")
            return []
        
        # Get directly connected nodes through links
        links = self.memory_graph.get_all_links()
        connected_nodes = {}
        
        for link in links:
            if link['source_id'] == node_id:
                target_node = self.memory_graph.get_node(link['target_id'])
                if target_node:
                    # Higher score for directly connected nodes
                    connected_nodes[link['target_id']] = {
                        'node': target_node,
                        'score': 0.9,
                        'relationship': 'outgoing',
                        'link_type': link['link_type']
                    }
            elif link['target_id'] == node_id:
                source_node_obj = self.memory_graph.get_node(link['source_id'])
                if source_node_obj:
                    # Slightly lower score for nodes that point to this one
                    connected_nodes[link['source_id']] = {
                        'node': source_node_obj,
                        'score': 0.8,
                        'relationship': 'incoming',
                        'link_type': link['link_type']
                    }
        
        # If we have a semantic model, find semantically similar nodes
        if self.embedding_model is not None:
            try:
                # Create a text representation of the source node
                source_text = f"{source_node['title']} {source_node['content']}"
                if source_node.get('tags'):
                    source_text += " " + " ".join(source_node['tags'])
                
                # Get source node embedding
                source_embedding = self._get_embedding(source_text)
                
                # Get all nodes except the source and already connected nodes
                all_nodes = self.memory_graph.get_all_nodes()
                candidate_nodes = [
                    node for node in all_nodes 
                    if node['id'] != node_id and node['id'] not in connected_nodes
                ]
                
                # Find semantic similarities
                for node in candidate_nodes:
                    # Create a text representation of the node
                    node_text = f"{node['title']} {node['content']}"
                    if node.get('tags'):
                        node_text += " " + " ".join(node['tags'])
                    
                    # Get node embedding and calculate similarity
                    node_embedding = self._get_embedding(node_text)
                    similarity = self._calculate_similarity(source_embedding, node_embedding)
                    
                    # Only include nodes with significant similarity
                    if similarity >= 0.7:
                        connected_nodes[node['id']] = {
                            'node': node,
                            'score': similarity,
                            'relationship': 'semantic'
                        }
            except Exception as e:
                logger.error(f"Error finding semantically similar nodes: {str(e)}")
        
        # Convert to a sorted list
        related_nodes = list(connected_nodes.values())
        related_nodes.sort(key=lambda x: x['score'], reverse=True)
        
        # Prepare result with limited fields
        results = []
        
        for item in related_nodes[:max_results]:
            node = item['node'].copy()
            node['relevance_score'] = item['score']
            node['relationship'] = item['relationship']
            if 'link_type' in item:
                node['link_type'] = item['link_type']
            results.append(node)
        
        return results
    
    def get_tag_cloud(self) -> List[Dict[str, Any]]:
        """
        Get a tag cloud with tag frequencies.
        
        Returns:
            List of tags with frequency counts
        """
        nodes = self.memory_graph.get_all_nodes()
        tag_counts = {}
        
        for node in nodes:
            for tag in node.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Convert to sorted list
        tag_cloud = [
            {'tag': tag, 'count': count}
            for tag, count in tag_counts.items()
        ]
        
        tag_cloud.sort(key=lambda x: x['count'], reverse=True)
        
        return tag_cloud
    
    def suggest_tags(self, text: str, max_suggestions: int = 5) -> List[str]:
        """
        Suggest tags for a piece of text based on existing tag patterns.
        
        Args:
            text: Text to suggest tags for
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggested tags
        """
        # Get existing tag cloud
        tag_cloud = self.get_tag_cloud()
        
        # Extract common patterns from text
        # This is a very simple implementation - could be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', text.lower())
        word_counts = {}
        
        for word in words:
            if word not in ['and', 'the', 'for', 'with', 'this', 'that']:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # First, check for existing tags in the text
        existing_tags = []
        for tag_info in tag_cloud:
            tag = tag_info['tag'].lower()
            if tag in text.lower():
                existing_tags.append(tag_info['tag'])
        
        # Then add frequently occurring words that aren't already tags
        word_suggestions = sorted(
            [(word, count) for word, count in word_counts.items() if word not in existing_tags],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Combine and limit
        suggestions = existing_tags + [word for word, _ in word_suggestions]
        return suggestions[:max_suggestions]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the embedding cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": len(self.embedding_cache),
            "max_cache_size": self.config.get("cache_size", 1000),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_ratio": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.embedding_cache = {}
        self.last_cache_cleanup = time.time()
        logger.info("Embedding cache cleared")

# Create a convenience function to get a knowledge retriever instance
def get_knowledge_retriever(config_path: Optional[str] = None) -> KnowledgeRetriever:
    """
    Get a configured knowledge retriever instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured KnowledgeRetriever instance
    """
    return KnowledgeRetriever(config_path)

# Example usage when run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 Knowledge Retriever")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--query", help="Search query")
    args = parser.parse_args()
    
    retriever = KnowledgeRetriever(args.config)
    
    if args.query:
        results = retriever.search(args.query)
        print(f"Found {len(results)} results for '{args.query}':")
        
        for i, result in enumerate(results):
            score = result.get('similarity_score') or result.get('match_score') or result.get('final_score', 0)
            print(f"{i+1}. {result['title']} (Score: {score:.2f})")
            print(f"   {result['content'][:100]}...") 