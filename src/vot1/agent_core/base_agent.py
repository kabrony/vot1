"""
Base Agent for TRILOGY BRAIN

This module provides the base agent class that all TRILOGY BRAIN agents inherit from.
It implements common functionality such as commandment adherence, branding,
logging, and telemetry.
"""

import os
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
import logging

try:
    # Try absolute imports first (for installed package)
    from vot1.agent_core.agent_commandments import (
        AgentType, 
        get_agent_branding, 
        get_agent_commandments,
        generate_agent_header
    )
    from vot1.utils.logging import get_logger
except ImportError:
    # Fall back to relative imports (for development)
    from src.vot1.agent_core.agent_commandments import (
        AgentType, 
        get_agent_branding, 
        get_agent_commandments,
        generate_agent_header
    )
    from src.vot1.utils.logging import get_logger


class BaseAgent(ABC):
    """
    Base Agent for all TRILOGY BRAIN agents
    
    This class provides common functionality for all agents in the system:
    1. Branding and identification
    2. Commandment adherence
    3. Logging and telemetry
    4. Status tracking
    5. Lifecycle management
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_type: Type of agent
            agent_id: Unique identifier for this agent instance, generated if None
            config: Configuration dictionary
        """
        # Agent identity
        self.agent_type = agent_type
        self.agent_id = agent_id or str(uuid.uuid4())
        self.branding = get_agent_branding(agent_type)
        self.commandments = get_agent_commandments(agent_type)
        
        # Configuration
        self.config = config or {}
        
        # State tracking
        self.start_time = time.time()
        self.last_active_time = self.start_time
        self.status = "initialized"
        self.health = 1.0  # 0.0 to 1.0
        
        # Performance metrics
        self.performance_metrics = {
            "operations_count": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_operation_time": 0.0,
            "avg_operation_time": 0.0
        }
        
        # Setup logging
        self.logger = get_logger(f"{self.branding.name}_{self.agent_id[:8]}")
        self.logger.info(f"Agent initialized: {self.branding.name} ({self.agent_id})")
        
        # Log commandments (debug level)
        for i, commandment in enumerate(self.commandments, 1):
            self.logger.debug(f"Commandment {i}: {commandment}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        uptime = time.time() - self.start_time
        
        return {
            "id": self.agent_id,
            "type": self.agent_type,
            "name": self.branding.name,
            "description": self.branding.description,
            "version": self.branding.version,
            "status": self.status,
            "health": self.health,
            "uptime": uptime,
            "performance": self.performance_metrics
        }
    
    def get_header(self) -> str:
        """Get a formatted header for agent outputs"""
        return generate_agent_header(self.agent_type)
    
    def record_operation(self, operation_name: str, success: bool, duration: float) -> None:
        """
        Record an operation for performance tracking.
        
        Args:
            operation_name: Name of the operation
            success: Whether the operation was successful
            duration: Duration of the operation in seconds
        """
        self.last_active_time = time.time()
        self.performance_metrics["operations_count"] += 1
        
        if success:
            self.performance_metrics["successful_operations"] += 1
        else:
            self.performance_metrics["failed_operations"] += 1
        
        self.performance_metrics["total_operation_time"] += duration
        
        if self.performance_metrics["operations_count"] > 0:
            self.performance_metrics["avg_operation_time"] = (
                self.performance_metrics["total_operation_time"] / 
                self.performance_metrics["operations_count"]
            )
        
        # Update health score based on success rate
        if self.performance_metrics["operations_count"] > 0:
            self.health = (
                self.performance_metrics["successful_operations"] / 
                self.performance_metrics["operations_count"]
            )
    
    def activate(self) -> None:
        """Activate the agent"""
        self.status = "active"
        self.logger.info(f"Agent activated: {self.branding.name}")
    
    def deactivate(self) -> None:
        """Deactivate the agent"""
        self.status = "inactive"
        self.logger.info(f"Agent deactivated: {self.branding.name}")
    
    def check_health(self) -> float:
        """
        Check agent health (0.0 to 1.0)
        
        Returns:
            Health score between 0.0 (unhealthy) and 1.0 (healthy)
        """
        return self.health
    
    def format_response(self, content: str, include_header: bool = True) -> str:
        """
        Format a response with proper branding.
        
        Args:
            content: Response content
            include_header: Whether to include the agent header
            
        Returns:
            Formatted response
        """
        if include_header:
            return f"{self.get_header()}\n\n{content}"
        return content
    
    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """
        Process a request (to be implemented by derived classes).
        
        Returns:
            Processing result
        """
        pass 