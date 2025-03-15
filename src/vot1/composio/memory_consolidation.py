"""
Memory Consolidation for TRILOGY BRAIN

This module provides consolidation services for the TRILOGY BRAIN memory system.
It optimizes memory storage, improves relationships, and performs cleanup operations.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta

from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.composio.client import ComposioClient
from vot1.memory import MemoryManager
from vot1.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

class MemoryConsolidationService:
    """
    Service for consolidating and optimizing the TRILOGY BRAIN memory system.
    
    This service performs several optimization tasks:
    1. Memory summarization: Create summaries of related memories
    2. Relationship enhancement: Improve connections between memories
    3. Redundancy detection: Identify and merge redundant memories
    4. Importance recalculation: Update memory importance scores
    5. Memory pruning: Remove low-value memories based on configurable policies
    """
    
    def __init__(
        self,
        memory_bridge: Optional[ComposioMemoryBridge] = None,
        composio_client: Optional[ComposioClient] = None,
        memory_manager: Optional[MemoryManager] = None,
        memory_path: str = "memory",
        consolidation_interval: int = 86400,  # Default: once per day
        min_importance_threshold: float = 0.2,
        redundancy_threshold: float = 0.85,
        max_memories_per_batch: int = 100,
        enable_auto_consolidation: bool = True
    ):
        """
        Initialize the memory consolidation service.
        
        Args:
            memory_bridge: ComposioMemoryBridge instance
            composio_client: ComposioClient instance
            memory_manager: MemoryManager instance
            memory_path: Path to memory storage
            consolidation_interval: Seconds between consolidation runs
            min_importance_threshold: Minimum importance to keep memories
            redundancy_threshold: Similarity threshold for redundancy detection
            max_memories_per_batch: Maximum memories to process in a batch
            enable_auto_consolidation: Whether to enable automatic consolidation
        """
        # Initialize components
        self.memory_bridge = memory_bridge or ComposioMemoryBridge(memory_path=memory_path)
        self.composio_client = composio_client or self.memory_bridge.composio_client
        self.memory_manager = memory_manager or self.memory_bridge.memory_manager
        
        # Configuration
        self.memory_path = memory_path
        self.consolidation_interval = consolidation_interval
        self.min_importance_threshold = min_importance_threshold
        self.redundancy_threshold = redundancy_threshold
        self.max_memories_per_batch = max_memories_per_batch
        self.enable_auto_consolidation = enable_auto_consolidation
        
        # State tracking
        self.last_consolidation_time = 0
        self.is_consolidating = False
        self.consolidated_memories: Set[str] = set()
        self.consolidation_stats: Dict[str, Any] = {
            "total_runs": 0,
            "memories_processed": 0,
            "memories_summarized": 0,
            "memories_merged": 0,
            "memories_pruned": 0,
            "relationships_created": 0,
            "last_run_duration": 0
        }
        
        # Start automatic consolidation if enabled
        if self.enable_auto_consolidation:
            self._start_auto_consolidation()
        
        logger.info(f"Memory Consolidation Service initialized with interval: {consolidation_interval}s")
    
    def _start_auto_consolidation(self):
        """Start automatic consolidation task"""
        asyncio.create_task(self._auto_consolidation_loop())
        logger.info("Automatic memory consolidation started")
    
    async def _auto_consolidation_loop(self):
        """Background task for automatic consolidation"""
        while self.enable_auto_consolidation:
            current_time = time.time()
            
            # Check if it's time to consolidate
            if current_time - self.last_consolidation_time >= self.consolidation_interval:
                try:
                    logger.info("Starting scheduled memory consolidation")
                    await self.consolidate()
                except Exception as e:
                    logger.error(f"Error during automatic consolidation: {e}")
            
            # Sleep for a while before checking again
            await asyncio.sleep(min(3600, self.consolidation_interval / 10))
    
    async def consolidate(self) -> Dict[str, Any]:
        """
        Perform a full memory consolidation.
        
        Returns:
            Statistics about the consolidation process
        """
        if self.is_consolidating:
            logger.warning("Consolidation already in progress, skipping")
            return self.consolidation_stats
        
        self.is_consolidating = True
        start_time = time.time()
        
        try:
            # Phase 1: Group memories by type and relevance
            memory_groups = await self._group_memories()
            
            # Phase 2: Process each group
            for group_name, memory_ids in memory_groups.items():
                logger.info(f"Processing memory group: {group_name} with {len(memory_ids)} memories")
                await self._process_memory_group(group_name, memory_ids)
            
            # Phase 3: Update importance scores
            await self._recalculate_importance_scores()
            
            # Phase 4: Prune low-value memories
            pruned_count = await self._prune_memories()
            self.consolidation_stats["memories_pruned"] += pruned_count
            
            # Update statistics
            self.consolidation_stats["total_runs"] += 1
            self.last_consolidation_time = time.time()
            self.consolidation_stats["last_run_duration"] = time.time() - start_time
            
            logger.info(f"Memory consolidation completed in {self.consolidation_stats['last_run_duration']:.2f}s")
            
            return self.consolidation_stats
            
        except Exception as e:
            logger.error(f"Error during consolidation: {e}")
            raise
        finally:
            self.is_consolidating = False
    
    async def _group_memories(self) -> Dict[str, List[str]]:
        """
        Group memories by type and relevance.
        
        Returns:
            Dictionary mapping group names to lists of memory IDs
        """
        # Get all memories (limit to reasonable number)
        all_memories = await self.memory_manager.list_memories(limit=10000)
        
        # Group by memory type
        groups: Dict[str, List[str]] = {}
        
        for memory in all_memories:
            memory_type = memory.get("type", "general")
            memory_id = memory.get("id")
            
            if not memory_id:
                continue
                
            if memory_type not in groups:
                groups[memory_type] = []
                
            groups[memory_type].append(memory_id)
        
        # Further group large categories by time period
        refined_groups: Dict[str, List[str]] = {}
        
        for group_name, memory_ids in groups.items():
            if len(memory_ids) > self.max_memories_per_batch:
                # Split large groups into time-based chunks
                time_grouped = await self._group_by_time_period(group_name, memory_ids)
                refined_groups.update(time_grouped)
            else:
                refined_groups[group_name] = memory_ids
        
        return refined_groups
    
    async def _group_by_time_period(self, base_group: str, memory_ids: List[str]) -> Dict[str, List[str]]:
        """
        Further group memories by time period.
        
        Args:
            base_group: Base group name
            memory_ids: List of memory IDs to group
            
        Returns:
            Dictionary mapping time-based group names to lists of memory IDs
        """
        time_groups: Dict[str, List[str]] = {}
        
        # Get memories with timestamps
        memories_with_time: List[Tuple[str, float]] = []
        
        for memory_id in memory_ids:
            memory = await self.memory_manager.get_memory(memory_id)
            if not memory:
                continue
                
            timestamp = memory.get("timestamp", 0)
            memories_with_time.append((memory_id, timestamp))
        
        # Sort by timestamp
        memories_with_time.sort(key=lambda x: x[1])
        
        # Group into batches of max_memories_per_batch
        for i in range(0, len(memories_with_time), self.max_memories_per_batch):
            batch = memories_with_time[i:i+self.max_memories_per_batch]
            
            if not batch:
                continue
                
            # Create group name based on time range
            start_time = datetime.fromtimestamp(batch[0][1])
            end_time = datetime.fromtimestamp(batch[-1][1])
            
            group_name = f"{base_group}_{start_time.strftime('%Y%m%d')}_{end_time.strftime('%Y%m%d')}"
            time_groups[group_name] = [memory_id for memory_id, _ in batch]
        
        return time_groups
    
    async def _process_memory_group(self, group_name: str, memory_ids: List[str]):
        """
        Process a group of memories for consolidation.
        
        Args:
            group_name: Name of the memory group
            memory_ids: List of memory IDs in the group
        """
        if not memory_ids:
            return
            
        # Step 1: Detect redundancies
        redundant_groups = await self._detect_redundancies(memory_ids)
        
        # Step 2: Merge redundant memories
        for redundant_group in redundant_groups:
            if len(redundant_group) > 1:
                merged_id = await self._merge_memories(redundant_group)
                if merged_id:
                    self.consolidation_stats["memories_merged"] += len(redundant_group) - 1
        
        # Step 3: Create a summary for the group
        if len(memory_ids) >= 3:
            summary_id = await self._create_group_summary(group_name, memory_ids)
            if summary_id:
                self.consolidation_stats["memories_summarized"] += 1
        
        # Step 4: Enhance relationships within the group
        relationship_count = await self._enhance_relationships(memory_ids)
        self.consolidation_stats["relationships_created"] += relationship_count
        
        # Update statistics
        self.consolidated_memories.update(memory_ids)
        self.consolidation_stats["memories_processed"] += len(memory_ids)
    
    async def _detect_redundancies(self, memory_ids: List[str]) -> List[List[str]]:
        """
        Detect redundant memories based on content similarity.
        
        Args:
            memory_ids: List of memory IDs to check
            
        Returns:
            List of groups of redundant memory IDs
        """
        redundant_groups: List[List[str]] = []
        
        # Use the memory manager to find similar memories
        for memory_id in memory_ids:
            memory = await self.memory_manager.get_memory(memory_id)
            if not memory or "content" not in memory:
                continue
                
            similar_memories = await self.memory_manager.find_similar_memories(
                memory["content"],
                limit=10,
                min_similarity=self.redundancy_threshold
            )
            
            # Create a group if we found similar memories
            similar_ids = [m.get("id") for m in similar_memories if m.get("id") != memory_id]
            
            if similar_ids:
                group = [memory_id] + similar_ids
                
                # Check if this group overlaps with existing groups
                is_new_group = True
                for existing_group in redundant_groups:
                    if any(memory_id in existing_group for memory_id in group):
                        # Merge with existing group
                        existing_group.extend(id for id in group if id not in existing_group)
                        is_new_group = False
                        break
                
                if is_new_group:
                    redundant_groups.append(group)
        
        return redundant_groups
    
    async def _merge_memories(self, memory_ids: List[str]) -> Optional[str]:
        """
        Merge redundant memories into a consolidated memory.
        
        Args:
            memory_ids: List of memory IDs to merge
            
        Returns:
            ID of the merged memory, or None if merging failed
        """
        if not memory_ids or len(memory_ids) < 2:
            return None
            
        try:
            # Get all memories to merge
            memories = []
            for memory_id in memory_ids:
                memory = await self.memory_manager.get_memory(memory_id)
                if memory:
                    memories.append(memory)
            
            if not memories:
                return None
                
            # Sort by importance and timestamp (prefer newer and more important)
            memories.sort(key=lambda m: (m.get("importance", 0), m.get("timestamp", 0)))
            
            # Use the most recent/important memory as the base
            base_memory = memories[-1]
            
            # Collect all metadata
            combined_metadata = {}
            for memory in memories:
                if "metadata" in memory and isinstance(memory["metadata"], dict):
                    combined_metadata.update(memory["metadata"])
            
            # Add special metadata about the merge
            combined_metadata["merged_from"] = memory_ids
            combined_metadata["merge_time"] = time.time()
            
            # Create the merged memory
            merged_id = await self.memory_manager.store_memory(
                content=base_memory.get("content", ""),
                memory_type=f"merged_{base_memory.get('type', 'general')}",
                metadata=combined_metadata,
                importance=max(m.get("importance", 0) for m in memories)
            )
            
            # Create relationships from original memories to merged memory
            if self.memory_bridge.enhanced_memory:
                for memory_id in memory_ids:
                    await self.memory_manager.create_relationship(
                        memory_id, merged_id, "merged_into", 1.0
                    )
            
            logger.info(f"Merged {len(memories)} memories into {merged_id}")
            return merged_id
            
        except Exception as e:
            logger.error(f"Error merging memories: {e}")
            return None
    
    async def _create_group_summary(self, group_name: str, memory_ids: List[str]) -> Optional[str]:
        """
        Create a summary memory for a group of memories.
        
        Args:
            group_name: Name of the memory group
            memory_ids: List of memory IDs in the group
            
        Returns:
            ID of the summary memory, or None if summarization failed
        """
        try:
            # Get memories to summarize (limit to reasonable number)
            memories_to_summarize = []
            for memory_id in memory_ids[:50]:  # Limit to 50 memories
                memory = await self.memory_manager.get_memory(memory_id)
                if memory:
                    memories_to_summarize.append(memory)
            
            if len(memories_to_summarize) < 3:
                return None
            
            # Create a prompt for summarization
            prompt = f"Create a concise summary of these {len(memories_to_summarize)} memories about {group_name}."
            
            # Use the memory bridge's advanced reflection capabilities
            reflection = await self.memory_bridge.advanced_memory_reflection(
                memory_ids=memory_ids[:50],
                reflection_depth="brief",
                include_thinking=True
            )
            
            if not reflection or not reflection.get("success"):
                logger.warning(f"Failed to create summary for {group_name}")
                return None
            
            # Extract summary from reflection
            summary_content = reflection.get("reflection", "")
            
            if not summary_content:
                return None
            
            # Store the summary as a new memory
            summary_id = await self.memory_manager.store_memory(
                content=summary_content,
                memory_type="memory_summary",
                metadata={
                    "group_name": group_name,
                    "summarized_memory_count": len(memories_to_summarize),
                    "summarized_memory_ids": memory_ids[:50],
                    "timestamp": time.time()
                },
                importance=0.9  # High importance for summaries
            )
            
            # Create relationships between memories and summary
            if self.memory_bridge.enhanced_memory:
                for memory_id in memory_ids[:50]:
                    await self.memory_manager.create_relationship(
                        memory_id, summary_id, "summarized_in", 0.8
                    )
            
            logger.info(f"Created summary {summary_id} for {len(memories_to_summarize)} memories in {group_name}")
            return summary_id
            
        except Exception as e:
            logger.error(f"Error creating group summary: {e}")
            return None
    
    async def _enhance_relationships(self, memory_ids: List[str]) -> int:
        """
        Enhance relationships between memories.
        
        Args:
            memory_ids: List of memory IDs to process
            
        Returns:
            Number of relationships created
        """
        if not self.memory_bridge.enhanced_memory:
            return 0
            
        relationship_count = 0
        
        try:
            # Get memories with their content
            memories = []
            for memory_id in memory_ids:
                memory = await self.memory_manager.get_memory(memory_id)
                if memory:
                    memories.append(memory)
            
            # Use the memory manager to find relationships
            for i, memory1 in enumerate(memories):
                memory1_id = memory1.get("id")
                if not memory1_id:
                    continue
                    
                # Find semantically similar memories
                similar_memories = await self.memory_manager.find_similar_memories(
                    memory1.get("content", ""),
                    limit=5,
                    min_similarity=0.6
                )
                
                for similar_memory in similar_memories:
                    similar_id = similar_memory.get("id")
                    similarity = similar_memory.get("similarity", 0)
                    
                    if not similar_id or similar_id == memory1_id or similarity < 0.6:
                        continue
                    
                    # Create relationship if it doesn't exist
                    relationship_type = "related_to"
                    
                    # Check temporal relationship
                    memory1_time = memory1.get("timestamp", 0)
                    memory2_time = similar_memory.get("timestamp", 0)
                    
                    if abs(memory2_time - memory1_time) < 3600:  # Within an hour
                        relationship_type = "temporally_related"
                    elif similarity > 0.8:
                        relationship_type = "strongly_related"
                        
                    # Create bidirectional relationship
                    await self.memory_manager.create_relationship(
                        memory1_id, similar_id, relationship_type, similarity
                    )
                    relationship_count += 1
                    
                    # Create reverse relationship with slightly lower strength
                    await self.memory_manager.create_relationship(
                        similar_id, memory1_id, relationship_type, similarity * 0.9
                    )
                    relationship_count += 1
            
            return relationship_count
            
        except Exception as e:
            logger.error(f"Error enhancing relationships: {e}")
            return relationship_count
    
    async def _recalculate_importance_scores(self):
        """Recalculate importance scores for memories"""
        try:
            # Get memories that have been processed
            for memory_id in self.consolidated_memories:
                memory = await self.memory_manager.get_memory(memory_id)
                if not memory:
                    continue
                
                # Base importance
                base_importance = memory.get("importance", 0.5)
                
                # Factors affecting importance
                factors = []
                
                # 1. Relationship count (more relationships = more important)
                if self.memory_bridge.enhanced_memory:
                    relationships = await self.memory_manager.get_memory_relationships(memory_id)
                    relationship_count = len(relationships)
                    relationship_factor = min(1.0, relationship_count / 10)  # Cap at 1.0
                    factors.append(relationship_factor)
                
                # 2. Recency factor (newer = more important)
                timestamp = memory.get("timestamp", 0)
                if timestamp > 0:
                    age_in_days = (time.time() - timestamp) / 86400
                    recency_factor = max(0.2, 1.0 - (age_in_days / 365))  # Decay over a year
                    factors.append(recency_factor)
                
                # 3. Memory type factor
                memory_type = memory.get("type", "general")
                type_importance = {
                    "memory_summary": 0.9,
                    "metacognitive_reflection": 0.85,
                    "thinking_process": 0.7,
                    "merged_memory": 0.8,
                    "assistant_response": 0.75,
                    "general": 0.5
                }
                type_factor = type_importance.get(memory_type, 0.5)
                factors.append(type_factor)
                
                # Calculate new importance
                if factors:
                    new_importance = (base_importance + sum(factors)) / (1 + len(factors))
                    
                    # Update if different enough
                    if abs(new_importance - base_importance) > 0.1:
                        await self.memory_manager.update_memory_metadata(
                            memory_id,
                            {"importance": new_importance}
                        )
            
        except Exception as e:
            logger.error(f"Error recalculating importance scores: {e}")
    
    async def _prune_memories(self) -> int:
        """
        Prune low-value memories based on importance threshold.
        
        Returns:
            Number of memories pruned
        """
        pruned_count = 0
        
        try:
            # Get candidates for pruning
            for memory_id in self.consolidated_memories:
                memory = await self.memory_manager.get_memory(memory_id)
                if not memory:
                    continue
                
                importance = memory.get("importance", 0.5)
                memory_type = memory.get("type", "general")
                
                # Skip certain memory types
                if memory_type in ["memory_summary", "metacognitive_reflection"]:
                    continue
                
                # Prune if below threshold
                if importance < self.min_importance_threshold:
                    # Check if this memory has important relationships
                    should_prune = True
                    
                    if self.memory_bridge.enhanced_memory:
                        relationships = await self.memory_manager.get_memory_relationships(memory_id)
                        important_relationships = [r for r in relationships if r.get("strength", 0) > 0.8]
                        
                        if important_relationships:
                            should_prune = False
                    
                    if should_prune:
                        # Archive instead of delete
                        await self._archive_memory(memory_id, memory)
                        pruned_count += 1
            
            return pruned_count
            
        except Exception as e:
            logger.error(f"Error pruning memories: {e}")
            return pruned_count
    
    async def _archive_memory(self, memory_id: str, memory: Dict[str, Any]):
        """
        Archive a memory instead of deleting it.
        
        Args:
            memory_id: ID of the memory to archive
            memory: Memory data
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = os.path.join(self.memory_path, "archive")
            os.makedirs(archive_dir, exist_ok=True)
            
            # Write memory to archive
            archive_path = os.path.join(archive_dir, f"{memory_id}.json")
            with open(archive_path, "w") as f:
                json.dump(memory, f, indent=2)
            
            # Delete the original memory
            await self.memory_manager.delete_memory(memory_id)
            
            logger.info(f"Archived memory {memory_id}")
            
        except Exception as e:
            logger.error(f"Error archiving memory {memory_id}: {e}")
    
    def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get statistics about the consolidation process"""
        return self.consolidation_stats.copy()
    
    def set_consolidation_interval(self, interval: int):
        """Set the interval between consolidation runs"""
        self.consolidation_interval = max(3600, interval)  # Minimum 1 hour
        logger.info(f"Consolidation interval set to {self.consolidation_interval}s")
    
    def stop_auto_consolidation(self):
        """Stop automatic consolidation"""
        self.enable_auto_consolidation = False
        logger.info("Automatic consolidation stopped")
    
    def start_auto_consolidation(self):
        """Start automatic consolidation"""
        if not self.enable_auto_consolidation:
            self.enable_auto_consolidation = True
            self._start_auto_consolidation()
            logger.info("Automatic consolidation started") 