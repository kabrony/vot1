"""
Enhanced Memory Manager for VOT1 with Composio MCP Integration

This module provides an enhanced memory management system that integrates
with Composio MCP for advanced features like:
- Hierarchical memory organization
- Memory relationships and graph structures
- Advanced semantic search with Composio models
- Memory context optimization for LLM prompts
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

from vot1.memory import MemoryManager, VectorStore
from vot1.composio.client import ComposioClient

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedMemoryGraph:
    """
    Enhanced memory graph structure for storing relationships between memories.
    
    This class extends the memory capability with:
    - Memory node relationships
    - Hierarchical organization
    - Graph-based retrieval algorithms
    """
    
    def __init__(self, storage_path: str = "memory/memory_graph.db"):
        """
        Initialize the memory graph.
        
        Args:
            storage_path: Path to store the memory graph database
        """
        self.storage_path = storage_path
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Initialize SQLite database
        self.conn = sqlite3.connect(storage_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self._create_tables()
        
        logger.info(f"Enhanced memory graph initialized at {storage_path}")
    
    def _create_tables(self):
        """Create the necessary database tables if they don't exist."""
        # Nodes table - stores memory nodes
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT,
            metadata TEXT,
            importance REAL DEFAULT 1.0,
            created_at INTEGER NOT NULL
        )
        ''')
        
        # Edges table - stores relationships between nodes
        self.cursor.execute('''
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
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges (source_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges (target_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes (type)')
        
        self.conn.commit()
    
    def add_node(
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
        node_id = str(uuid.uuid4())
        created_at = int(time.time())
        
        # Convert metadata to JSON string if provided
        metadata_str = json.dumps(metadata) if metadata else "{}"
        
        # Insert node into database
        self.cursor.execute(
            '''
            INSERT INTO nodes (id, type, content, metadata, importance, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (node_id, node_type, content, metadata_str, importance, created_at)
        )
        self.conn.commit()
        
        logger.debug(f"Added node {node_id} of type {node_type}")
        return node_id
    
    def add_edge(
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
            relation_type: Type of relationship (e.g., "related_to", "caused", "part_of")
            weight: Weight of the relationship (higher = stronger relationship)
            metadata: Additional metadata for the edge
            
        Returns:
            str: ID of the created edge
        """
        edge_id = str(uuid.uuid4())
        created_at = int(time.time())
        
        # Convert metadata to JSON string if provided
        metadata_str = json.dumps(metadata) if metadata else "{}"
        
        # Insert edge into database
        self.cursor.execute(
            '''
            INSERT INTO edges (id, source_id, target_id, relation_type, weight, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (edge_id, source_id, target_id, relation_type, weight, metadata_str, created_at)
        )
        self.conn.commit()
        
        logger.debug(f"Added edge {edge_id} from {source_id} to {target_id} of type {relation_type}")
        return edge_id
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by its ID."""
        self.cursor.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
        row = self.cursor.fetchone()
        
        if not row:
            return None
            
        return {
            "id": row[0],
            "type": row[1],
            "content": row[2],
            "metadata": json.loads(row[3]),
            "importance": row[4],
            "created_at": row[5]
        }
    
    def get_connected_nodes(
        self, 
        node_id: str, 
        relation_type: Optional[str] = None,
        direction: str = "outgoing",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get nodes connected to a specific node.
        
        Args:
            node_id: ID of the node to get connections for
            relation_type: Optional filter for relationship type
            direction: "outgoing", "incoming", or "both"
            limit: Maximum number of nodes to return
            
        Returns:
            List of node dictionaries
        """
        results = []
        
        # Query based on direction
        if direction == "outgoing" or direction == "both":
            query = '''
            SELECT n.* FROM nodes n
            JOIN edges e ON n.id = e.target_id
            WHERE e.source_id = ?
            '''
            params = [node_id]
            
            if relation_type:
                query += " AND e.relation_type = ?"
                params.append(relation_type)
                
            query += " ORDER BY e.weight DESC LIMIT ?"
            params.append(limit)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            for row in rows:
                results.append({
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]),
                    "importance": row[4],
                    "created_at": row[5]
                })
        
        # If we need incoming connections and haven't reached limit
        if (direction == "incoming" or direction == "both") and (limit > len(results) or direction == "incoming"):
            remaining = limit - len(results) if direction == "both" else limit
            
            query = '''
            SELECT n.* FROM nodes n
            JOIN edges e ON n.id = e.source_id
            WHERE e.target_id = ?
            '''
            params = [node_id]
            
            if relation_type:
                query += " AND e.relation_type = ?"
                params.append(relation_type)
                
            query += " ORDER BY e.weight DESC LIMIT ?"
            params.append(remaining)
            
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            for row in rows:
                results.append({
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]),
                    "importance": row[4],
                    "created_at": row[5]
                })
        
        return results
    
    def get_graph_for_visualization(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get a representation of the memory graph for visualization.
        
        Returns:
            Dictionary with nodes and edges suitable for visualization
        """
        # Get nodes
        self.cursor.execute(
            'SELECT id, type, content, importance FROM nodes ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        node_rows = self.cursor.fetchall()
        
        nodes = []
        for row in node_rows:
            # Include a snippet of content for display
            content_snippet = row[2][:50] + "..." if row[2] and len(row[2]) > 50 else row[2]
            
            nodes.append({
                "id": row[0],
                "type": row[1],
                "label": content_snippet,
                "size": row[3]  # Use importance as size
            })
        
        # Get edges
        self.cursor.execute(
            '''
            SELECT source_id, target_id, relation_type, weight
            FROM edges
            WHERE source_id IN (SELECT id FROM nodes ORDER BY created_at DESC LIMIT ?)
            AND target_id IN (SELECT id FROM nodes ORDER BY created_at DESC LIMIT ?)
            ''',
            (limit, limit)
        )
        edge_rows = self.cursor.fetchall()
        
        edges = []
        for row in edge_rows:
            edges.append({
                "source": row[0],
                "target": row[1],
                "label": row[2],
                "weight": row[3]
            })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __del__(self):
        """Ensure the connection is closed when the object is deleted."""
        self.close()


class EnhancedMemoryManager(MemoryManager):
    """
    Enhanced memory manager with Composio MCP integration.
    
    This class extends the base MemoryManager with:
    - Memory graph for relationship storage
    - Enhanced semantic memory with Composio models
    - Memory consolidation and summarization
    - Hierarchical memory organization
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        memory_path: str = "memory",
        composio_client: Optional[ComposioClient] = None
    ):
        """
        Initialize the enhanced memory manager.
        
        Args:
            vector_store: Optional VectorStore instance
            memory_path: Path to store memory files
            composio_client: Optional ComposioClient instance
        """
        # Initialize base MemoryManager
        super().__init__(vector_store=vector_store, memory_path=memory_path)
        
        # Initialize memory graph
        self.memory_graph = EnhancedMemoryGraph(
            storage_path=os.path.join(memory_path, "memory_graph.db")
        )
        
        # Initialize Composio client
        self.composio_client = composio_client or ComposioClient()
        
        # Path for storing consolidated memories
        self.consolidated_memory_path = os.path.join(memory_path, "consolidated")
        os.makedirs(self.consolidated_memory_path, exist_ok=True)
        
        logger.info("Enhanced memory manager initialized")
    
    def add_semantic_memory_with_relations(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        importance: float = 1.0
    ) -> str:
        """
        Add semantic memory with relationship information.
        
        Args:
            content: Memory content
            metadata: Additional metadata
            relations: List of relations to other memories
                Each relation should have:
                - target_id: ID of the target memory
                - relation_type: Type of relationship
                - weight: Optional relationship strength (0-1)
            importance: Memory importance score
            
        Returns:
            str: Memory ID
        """
        # Add to base semantic memory
        memory_id = self.add_semantic_memory(content=content, metadata=metadata)
        
        # Add node to memory graph
        node_id = self.memory_graph.add_node(
            content=content,
            node_type="semantic_memory",
            metadata=metadata,
            importance=importance
        )
        
        # Store mapping between memory_id and node_id in metadata
        self._update_memory_metadata(memory_id, {"graph_node_id": node_id})
        
        # Add relations if provided
        if relations:
            for relation in relations:
                target_id = relation.get("target_id")
                relation_type = relation.get("relation_type", "related_to")
                weight = relation.get("weight", 0.7)
                
                if target_id:
                    # Get the graph node ID for the target memory
                    target_metadata = self._get_memory_metadata(target_id)
                    target_node_id = target_metadata.get("graph_node_id")
                    
                    if target_node_id:
                        self.memory_graph.add_edge(
                            source_id=node_id,
                            target_id=target_node_id,
                            relation_type=relation_type,
                            weight=weight
                        )
        
        return memory_id
    
    def _update_memory_metadata(self, memory_id: str, metadata_update: Dict[str, Any]):
        """Update metadata for a memory item."""
        memory_file = os.path.join(self.semantic_memory_path, f"{memory_id}.json")
        
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
    
    def _get_memory_metadata(self, memory_id: str) -> Dict[str, Any]:
        """Get metadata for a memory item."""
        memory_file = os.path.join(self.semantic_memory_path, f"{memory_id}.json")
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            return memory_data.get("metadata", {})
        
        return {}
    
    async def analyze_and_relate_memory(
        self, 
        memory_id: str, 
        max_relations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze a memory and automatically create relationships.
        
        Args:
            memory_id: ID of the memory to analyze
            max_relations: Maximum number of relations to create
            
        Returns:
            List of created relations
        """
        # Get memory content
        memory = self.get_memory(memory_id)
        if not memory:
            logger.error(f"Memory {memory_id} not found")
            return []
            
        memory_content = memory.get("content", "")
        
        # Search for related memories
        related_memories = self.search_memories(
            query=memory_content,
            limit=max_relations + 5,  # Get extra to filter out the current memory
            memory_types=["semantic"]
        )
        
        # Filter out the current memory
        related_memories = [m for m in related_memories if m.get("id") != memory_id][:max_relations]
        
        # Use Composio to analyze relationships
        system_prompt = """
        Analyze the relationships between the primary memory and the related memories.
        For each related memory, determine:
        1. The relationship type (e.g., 'elaborates', 'contradicts', 'supports', 'example_of', etc.)
        2. The strength of the relationship on a scale from 0.1 to 1.0
        3. A brief explanation of the relationship
        
        Return your analysis as a JSON array where each item has:
        - target_id: The ID of the related memory
        - relation_type: The type of relationship
        - weight: The strength of the relationship (0.1-1.0)
        - explanation: Brief explanation of the relationship
        """
        
        user_prompt = f"""
        Primary Memory:
        {memory_content}
        
        Related Memories:
        {json.dumps([{"id": m.get("id"), "content": m.get("content")} for m in related_memories], indent=2)}
        
        Analyze the relationships between the primary memory and each related memory.
        """
        
        try:
            response = await self.composio_client.process_request(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3
            )
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract JSON from the response - may need to handle various formats
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                relations_json = json_match.group(1)
            else:
                # Try to find any JSON array in the response
                json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                if json_match:
                    relations_json = json_match.group(0)
                else:
                    # Just try to parse the whole thing
                    relations_json = content
            
            # Parse the relations
            try:
                relations = json.loads(relations_json)
                
                # Create the relationships in the graph
                created_relations = []
                memory_metadata = self._get_memory_metadata(memory_id)
                source_node_id = memory_metadata.get("graph_node_id")
                
                if not source_node_id:
                    # Create a graph node for this memory if it doesn't exist
                    source_node_id = self.memory_graph.add_node(
                        content=memory_content,
                        node_type="semantic_memory",
                        metadata=memory_metadata
                    )
                    self._update_memory_metadata(memory_id, {"graph_node_id": source_node_id})
                
                for relation in relations:
                    target_id = relation.get("target_id")
                    relation_type = relation.get("relation_type", "related_to")
                    weight = float(relation.get("weight", 0.7))
                    explanation = relation.get("explanation", "")
                    
                    # Get or create graph node for target
                    target_metadata = self._get_memory_metadata(target_id)
                    target_node_id = target_metadata.get("graph_node_id")
                    
                    if not target_node_id:
                        target_memory = self.get_memory(target_id)
                        if target_memory:
                            target_node_id = self.memory_graph.add_node(
                                content=target_memory.get("content", ""),
                                node_type="semantic_memory",
                                metadata=target_metadata
                            )
                            self._update_memory_metadata(target_id, {"graph_node_id": target_node_id})
                    
                    if source_node_id and target_node_id:
                        edge_id = self.memory_graph.add_edge(
                            source_id=source_node_id,
                            target_id=target_node_id,
                            relation_type=relation_type,
                            weight=weight,
                            metadata={"explanation": explanation}
                        )
                        
                        created_relations.append({
                            "source_id": memory_id,
                            "target_id": target_id,
                            "relation_type": relation_type,
                            "weight": weight,
                            "explanation": explanation,
                            "edge_id": edge_id
                        })
                
                return created_relations
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse relationships JSON: {e}")
                logger.error(f"Content: {content}")
                return []
                
        except Exception as e:
            logger.error(f"Error analyzing memory relationships: {e}")
            return []
    
    async def consolidate_memories(
        self,
        topic: Optional[str] = None,
        time_range: Optional[Tuple[int, int]] = None,
        max_memories: int = 20
    ) -> Dict[str, Any]:
        """
        Consolidate multiple memories into a summary.
        
        Args:
            topic: Optional topic to filter memories
            time_range: Optional (start_time, end_time) unix timestamps
            max_memories: Maximum number of memories to consolidate
            
        Returns:
            Dict with consolidated memory information
        """
        # Gather memories to consolidate
        if topic:
            memories = self.search_memories(query=topic, limit=max_memories)
        else:
            # Get most recent memories
            memories = []
            memory_files = os.listdir(self.semantic_memory_path)
            memory_files = [f for f in memory_files if f.endswith('.json')]
            
            # Sort by creation time
            memory_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.semantic_memory_path, f)), reverse=True)
            
            for file in memory_files[:max_memories]:
                with open(os.path.join(self.semantic_memory_path, file), 'r') as f:
                    memory_data = json.load(f)
                    memories.append(memory_data)
        
        if not memories:
            logger.warning("No memories found to consolidate")
            return {"error": "No memories found to consolidate"}
        
        # Format memories for consolidation
        memory_texts = []
        for memory in memories:
            created_time = datetime.fromtimestamp(memory.get("created", time.time()))
            memory_texts.append(f"[{created_time.strftime('%Y-%m-%d %H:%M')}] {memory.get('content', '')}")
        
        memories_text = "\n\n---\n\n".join(memory_texts)
        
        # Use Composio to consolidate memories
        system_prompt = """
        You are an expert at memory consolidation and summarization. Your task is to:
        
        1. Analyze the provided memories
        2. Identify key themes, patterns, and insights
        3. Create a consolidated summary that preserves important information
        4. Extract key concepts that deserve their own memory entries
        
        Your response should be in this JSON format:
        {
            "summary": "The consolidated summary",
            "themes": ["theme1", "theme2", ...],
            "key_insights": ["insight1", "insight2", ...],
            "concepts": [
                {"name": "concept1", "description": "description1"},
                {"name": "concept2", "description": "description2"}
            ]
        }
        """
        
        user_prompt = f"""
        These are memories to consolidate:
        
        {memories_text}
        
        Please analyze these memories and create a consolidated summary with themes and key insights.
        """
        
        try:
            response = await self.composio_client.process_request(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                consolidated_json = json_match.group(1)
            else:
                # Try to find any JSON object in the response
                json_match = re.search(r'\{\s*".*"\s*:.*\}', content, re.DOTALL)
                if json_match:
                    consolidated_json = json_match.group(0)
                else:
                    # Just try to parse the whole thing
                    consolidated_json = content
            
            # Parse the consolidated memory
            try:
                consolidated = json.loads(consolidated_json)
                
                # Store the consolidated memory
                consolidated_id = str(uuid.uuid4())
                timestamp = int(time.time())
                
                consolidated_data = {
                    "id": consolidated_id,
                    "type": "consolidated_memory",
                    "content": consolidated.get("summary", ""),
                    "themes": consolidated.get("themes", []),
                    "key_insights": consolidated.get("key_insights", []),
                    "concepts": consolidated.get("concepts", []),
                    "source_memories": [m.get("id") for m in memories],
                    "created": timestamp,
                    "metadata": {
                        "source": "memory_consolidation",
                        "memory_count": len(memories),
                        "topic": topic
                    }
                }
                
                # Save to file
                consolidated_file = os.path.join(self.consolidated_memory_path, f"{consolidated_id}.json")
                with open(consolidated_file, 'w') as f:
                    json.dump(consolidated_data, f, indent=2)
                
                # Add to vector store
                self.vector_store.add(
                    content=consolidated.get("summary", ""),
                    metadata={
                        "id": consolidated_id,
                        "type": "consolidated_memory",
                        "created": timestamp,
                        "source": "memory_consolidation"
                    }
                )
                
                # Add as node to memory graph
                node_id = self.memory_graph.add_node(
                    content=consolidated.get("summary", ""),
                    node_type="consolidated_memory",
                    metadata=consolidated_data,
                    importance=1.5  # Higher importance for consolidated memories
                )
                
                # Add relationships to source memories
                for memory_id in consolidated_data["source_memories"]:
                    memory_metadata = self._get_memory_metadata(memory_id)
                    source_node_id = memory_metadata.get("graph_node_id")
                    
                    if source_node_id:
                        self.memory_graph.add_edge(
                            source_id=node_id,
                            target_id=source_node_id,
                            relation_type="consolidates",
                            weight=1.0
                        )
                
                # Add concept nodes if any
                for concept in consolidated.get("concepts", []):
                    concept_node_id = self.memory_graph.add_node(
                        content=concept.get("description", ""),
                        node_type="concept",
                        metadata={"name": concept.get("name")},
                        importance=1.2
                    )
                    
                    self.memory_graph.add_edge(
                        source_id=node_id,
                        target_id=concept_node_id,
                        relation_type="has_concept",
                        weight=1.0
                    )
                
                return consolidated_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse consolidated memory JSON: {e}")
                logger.error(f"Content: {content}")
                return {"error": f"Failed to parse response: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")
            return {"error": f"Error consolidating memories: {str(e)}"}
    
    def get_graph_for_memory(self, memory_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get the memory graph centered on a specific memory.
        
        Args:
            memory_id: ID of the memory at the center of the graph
            depth: How many levels of connections to include
            
        Returns:
            Dict with nodes and edges for visualization
        """
        # Get the graph node ID for this memory
        memory_metadata = self._get_memory_metadata(memory_id)
        center_node_id = memory_metadata.get("graph_node_id")
        
        if not center_node_id:
            return {"nodes": [], "edges": []}
        
        # Get the immediate connections
        connected_nodes = self.memory_graph.get_connected_nodes(
            node_id=center_node_id,
            direction="both",
            limit=20
        )
        
        # Start building the graph
        nodes = []
        edges = []
        processed_nodes = set()
        
        # Add the center node
        center_node = self.memory_graph.get_node(center_node_id)
        if center_node:
            nodes.append({
                "id": center_node["id"],
                "type": center_node["type"],
                "label": center_node["content"][:50] + "..." if center_node["content"] and len(center_node["content"]) > 50 else center_node["content"],
                "size": center_node["importance"] * 2  # Emphasize the center node
            })
            processed_nodes.add(center_node["id"])
        
        # Helper function to add nodes and edges recursively
        def add_connected_nodes(node_id, current_depth=1):
            if current_depth > depth:
                return
                
            # Get connected nodes in both directions
            connected = self.memory_graph.get_connected_nodes(
                node_id=node_id,
                direction="both",
                limit=10
            )
            
            for node in connected:
                if node["id"] not in processed_nodes:
                    nodes.append({
                        "id": node["id"],
                        "type": node["type"],
                        "label": node["content"][:50] + "..." if node["content"] and len(node["content"]) > 50 else node["content"],
                        "size": node["importance"]
                    })
                    processed_nodes.add(node["id"])
                    
                    # Recursively add connections for this node
                    if current_depth < depth:
                        add_connected_nodes(node["id"], current_depth + 1)
        
        # Add connected nodes up to desired depth
        add_connected_nodes(center_node_id)
        
        # Now add all edges between the processed nodes
        for node_id in processed_nodes:
            # Query edges from this node to any other processed node
            self.cursor.execute(
                '''
                SELECT source_id, target_id, relation_type, weight
                FROM edges
                WHERE source_id = ? AND target_id IN ({})
                '''.format(','.join(['?'] * len(processed_nodes))),
                [node_id] + list(processed_nodes)
            )
            
            rows = self.cursor.fetchall()
            for row in rows:
                edges.append({
                    "source": row[0],
                    "target": row[1],
                    "label": row[2],
                    "weight": row[3]
                })
        
        return {
            "nodes": nodes,
            "edges": edges
        }
    
    def close(self):
        """Close all database connections."""
        super().close()
        if hasattr(self, 'memory_graph'):
            self.memory_graph.close() 