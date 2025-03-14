#!/usr/bin/env python3
"""
Agent Memory Manager Module

This module extends the base MemoryManager with specialized functionality
for tracking agent activities, storing agent states, and managing
advanced memory capabilities for the agent ecosystem.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import traceback

from ..memory import MemoryManager
from .ascii_art import get_votai_ascii

logger = logging.getLogger(__name__)

class AgentMemoryManager(MemoryManager):
    """
    Enhanced memory manager specifically designed for agent operations.
    
    This class extends the base MemoryManager with advanced capabilities for
    tracking agent activities, recording agent operations, and providing
    a structured memory system for the agent ecosystem.
    
    Features:
    - Agent activity logging
    - Operation tracking
    - Task history
    - Performance metrics
    - Memory indexing for faster retrieval
    - Cross-agent memory sharing
    """
    
    AGENT_ACTIVITY_CATEGORY = "agent_activities"
    AGENT_TASKS_CATEGORY = "agent_tasks"
    AGENT_METRICS_CATEGORY = "agent_metrics"
    AGENT_KNOWLEDGE_CATEGORY = "agent_knowledge"
    ECOSYSTEM_STATUS_CATEGORY = "ecosystem_status"
    
    def __init__(
        self, 
        base_path: Optional[str] = None,
        auto_create_dirs: bool = True,
        use_compression: bool = False,
        enable_indexing: bool = True
    ):
        """
        Initialize the Agent Memory Manager.
        
        Args:
            base_path: Base directory for storing memory, defaults to ~/.vot1/memory/agents
            auto_create_dirs: Automatically create directories when saving
            use_compression: Whether to compress stored data
            enable_indexing: Whether to enable memory indexing for faster retrieval
        """
        if base_path is None:
            # Default to specialized agent memory directory
            home_dir = os.path.expanduser("~")
            base_path = os.path.join(home_dir, ".vot1", "memory", "agents")
        
        super().__init__(base_path, auto_create_dirs, use_compression)
        
        self.enable_indexing = enable_indexing
        self.indices = {}
        self.activity_counter = 0
        
        # Display VOTai signature
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai Agent Memory Manager initialized at {base_path}")
        
        # Initialize indices if enabled
        if self.enable_indexing:
            self._initialize_indices()
    
    def _initialize_indices(self):
        """Initialize memory indices for faster retrieval."""
        for category in [
            self.AGENT_ACTIVITY_CATEGORY,
            self.AGENT_TASKS_CATEGORY,
            self.AGENT_METRICS_CATEGORY,
            self.AGENT_KNOWLEDGE_CATEGORY,
            self.ECOSYSTEM_STATUS_CATEGORY
        ]:
            try:
                keys = self.list_keys(category)
                self.indices[category] = {
                    "last_updated": time.time(),
                    "keys": keys
                }
                logger.debug(f"Initialized index for category '{category}' with {len(keys)} keys")
            except Exception as e:
                logger.warning(f"Failed to initialize index for category '{category}': {e}")
    
    def record_agent_activity(self, agent_id: str, activity_type: str, details: Dict[str, Any]) -> str:
        """
        Record an agent activity in the memory system.
        
        Args:
            agent_id: ID of the agent performing the activity
            activity_type: Type of activity (e.g., "task_start", "task_complete", "error")
            details: Additional details about the activity
            
        Returns:
            The activity ID (key) in the memory system
        """
        self.activity_counter += 1
        timestamp = datetime.now().isoformat()
        activity_id = f"{agent_id}_{activity_type}_{timestamp}_{self.activity_counter}"
        
        activity_data = {
            "agent_id": agent_id,
            "activity_type": activity_type,
            "timestamp": timestamp,
            "details": details
        }
        
        success = self.save(self.AGENT_ACTIVITY_CATEGORY, activity_id, activity_data)
        if success and self.enable_indexing:
            if self.AGENT_ACTIVITY_CATEGORY not in self.indices:
                self.indices[self.AGENT_ACTIVITY_CATEGORY] = {"last_updated": time.time(), "keys": []}
            self.indices[self.AGENT_ACTIVITY_CATEGORY]["keys"].append(activity_id)
            self.indices[self.AGENT_ACTIVITY_CATEGORY]["last_updated"] = time.time()
        
        return activity_id
    
    def record_task(self, agent_id: str, task_id: str, task_type: str, task_data: Dict[str, Any]) -> bool:
        """
        Record a task assigned to an agent.
        
        Args:
            agent_id: ID of the agent assigned the task
            task_id: ID of the task
            task_type: Type of task
            task_data: Task parameters and data
            
        Returns:
            Whether the task was successfully recorded
        """
        task_record = {
            "agent_id": agent_id,
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "status": "assigned",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [
                {
                    "status": "assigned",
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        success = self.save(self.AGENT_TASKS_CATEGORY, task_id, task_record)
        if success and self.enable_indexing:
            if self.AGENT_TASKS_CATEGORY not in self.indices:
                self.indices[self.AGENT_TASKS_CATEGORY] = {"last_updated": time.time(), "keys": []}
            self.indices[self.AGENT_TASKS_CATEGORY]["keys"].append(task_id)
            self.indices[self.AGENT_TASKS_CATEGORY]["last_updated"] = time.time()
        
        return success
    
    def update_task_status(self, task_id: str, new_status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            new_status: New status of the task (e.g., "in_progress", "completed", "failed")
            result: Optional result data if the task is completed
            
        Returns:
            Whether the task was successfully updated
        """
        task_record = self.load(self.AGENT_TASKS_CATEGORY, task_id)
        if task_record is None:
            logger.warning(f"Task '{task_id}' not found in memory")
            return False
        
        task_record["status"] = new_status
        task_record["updated_at"] = datetime.now().isoformat()
        task_record["history"].append({
            "status": new_status,
            "timestamp": datetime.now().isoformat()
        })
        
        if result is not None:
            task_record["result"] = result
        
        return self.save(self.AGENT_TASKS_CATEGORY, task_id, task_record)
    
    def get_agent_tasks(self, agent_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to an agent, optionally filtered by status.
        
        Args:
            agent_id: ID of the agent
            status: Optional status filter (e.g., "assigned", "in_progress", "completed")
            
        Returns:
            List of task records matching the criteria
        """
        tasks = []
        for key in self.list_keys(self.AGENT_TASKS_CATEGORY):
            task = self.load(self.AGENT_TASKS_CATEGORY, key)
            if task["agent_id"] == agent_id and (status is None or task["status"] == status):
                tasks.append(task)
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t["created_at"], reverse=True)
        return tasks
    
    def record_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Record performance metrics for an agent.
        
        Args:
            agent_id: ID of the agent
            metrics: Performance metrics to record
            
        Returns:
            Whether the metrics were successfully recorded
        """
        timestamp = datetime.now().isoformat()
        metrics_key = f"{agent_id}_{timestamp}"
        
        metrics_record = {
            "agent_id": agent_id,
            "timestamp": timestamp,
            "metrics": metrics
        }
        
        return self.save(self.AGENT_METRICS_CATEGORY, metrics_key, metrics_record)
    
    def get_agent_metrics(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get performance metrics for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of metric records to return
            
        Returns:
            List of metric records for the agent (newest first)
        """
        metrics = []
        for key in self.list_keys(self.AGENT_METRICS_CATEGORY):
            if key.startswith(f"{agent_id}_"):
                metric = self.load(self.AGENT_METRICS_CATEGORY, key)
                metrics.append(metric)
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda m: m["timestamp"], reverse=True)
        return metrics[:limit]
    
    def store_agent_knowledge(self, agent_id: str, knowledge_type: str, content: Any, tags: List[str] = None) -> str:
        """
        Store knowledge gained by an agent.
        
        Args:
            agent_id: ID of the agent
            knowledge_type: Type of knowledge (e.g., "repository_analysis", "code_pattern")
            content: The knowledge content
            tags: Optional tags for easier searching
            
        Returns:
            The knowledge ID in the memory system
        """
        timestamp = datetime.now().isoformat()
        knowledge_id = f"{agent_id}_{knowledge_type}_{timestamp}"
        
        knowledge_record = {
            "agent_id": agent_id,
            "knowledge_type": knowledge_type,
            "timestamp": timestamp,
            "content": content,
            "tags": tags or []
        }
        
        success = self.save(self.AGENT_KNOWLEDGE_CATEGORY, knowledge_id, knowledge_record)
        if not success:
            logger.error(f"Failed to store agent knowledge: {knowledge_id}")
            return None
        
        return knowledge_id
    
    def search_agent_knowledge(self, query: str, agent_id: Optional[str] = None, 
                              knowledge_type: Optional[str] = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for knowledge in the memory system.
        
        Args:
            query: Search query (will be matched against content)
            agent_id: Optional agent ID filter
            knowledge_type: Optional knowledge type filter
            tags: Optional tags filter (any match)
            
        Returns:
            List of knowledge records matching the criteria
        """
        results = []
        query = query.lower()
        
        for key in self.list_keys(self.AGENT_KNOWLEDGE_CATEGORY):
            knowledge = self.load(self.AGENT_KNOWLEDGE_CATEGORY, key)
            
            # Apply filters
            if agent_id and knowledge["agent_id"] != agent_id:
                continue
                
            if knowledge_type and knowledge["knowledge_type"] != knowledge_type:
                continue
                
            if tags and not any(tag in knowledge["tags"] for tag in tags):
                continue
            
            # Search in content (basic text search)
            content_str = str(knowledge["content"]).lower()
            if query in content_str:
                results.append(knowledge)
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda k: k["timestamp"], reverse=True)
        return results
    
    def save_ecosystem_status(self, status: Dict[str, Any]) -> bool:
        """
        Save the current status of the agent ecosystem.
        
        Args:
            status: The ecosystem status data
            
        Returns:
            Whether the status was successfully saved
        """
        timestamp = datetime.now().isoformat()
        status_key = f"ecosystem_status_{timestamp}"
        
        status_record = {
            "timestamp": timestamp,
            "status": status
        }
        
        return self.save(self.ECOSYSTEM_STATUS_CATEGORY, status_key, status_record)
    
    def get_latest_ecosystem_status(self) -> Optional[Dict[str, Any]]:
        """
        Get the latest ecosystem status.
        
        Returns:
            The latest ecosystem status record, or None if no status exists
        """
        keys = self.list_keys(self.ECOSYSTEM_STATUS_CATEGORY)
        if not keys:
            return None
        
        # Sort keys by timestamp (newest first)
        keys.sort(reverse=True)
        
        # Load the latest status
        return self.load(self.ECOSYSTEM_STATUS_CATEGORY, keys[0])
    
    def generate_agent_report(self, agent_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive report for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            A report containing agent activities, tasks, metrics, and knowledge
        """
        try:
            # Get tasks
            tasks = self.get_agent_tasks(agent_id)
            task_count = len(tasks)
            completed_tasks = [t for t in tasks if t["status"] == "completed"]
            failed_tasks = [t for t in tasks if t["status"] == "failed"]
            
            # Get metrics
            metrics = self.get_agent_metrics(agent_id)
            latest_metrics = metrics[0] if metrics else None
            
            # Get knowledge
            knowledge_keys = [k for k in self.list_keys(self.AGENT_KNOWLEDGE_CATEGORY) 
                             if k.startswith(f"{agent_id}_")]
            knowledge_count = len(knowledge_keys)
            
            # Get activities
            activity_keys = [k for k in self.list_keys(self.AGENT_ACTIVITY_CATEGORY) 
                            if k.startswith(f"{agent_id}_")]
            activity_count = len(activity_keys)
            
            # Build report
            report = {
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tasks": task_count,
                    "completed_tasks": len(completed_tasks),
                    "failed_tasks": len(failed_tasks),
                    "success_rate": len(completed_tasks) / task_count if task_count > 0 else 0,
                    "knowledge_count": knowledge_count,
                    "activity_count": activity_count
                },
                "recent_tasks": tasks[:5],  # Get 5 most recent tasks
                "latest_metrics": latest_metrics,
                "report_generation_time": datetime.now().isoformat()
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating agent report: {e}")
            traceback.print_exc()
            return {
                "agent_id": agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 