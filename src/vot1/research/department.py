"""
VOT1 Research & Development Department

This module implements the R&D department for VOT1, focused on continuous 
improvement of the TRILOGY BRAIN architecture and exploration of cutting-edge 
technologies like IPFS, blockchain, and distributed AI systems.
"""

import os
import json
import time
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine
from ..blockchain.solana_memory_agent import SolanaMemoryAgent
from ..blockchain.zk_verification_agent import ZKVerificationAgent

logger = get_logger(__name__)

# Research areas
RESEARCH_AREA_DISTRIBUTED_STORAGE = "distributed_storage"
RESEARCH_AREA_NEURAL_ARCHITECTURE = "neural_architecture"
RESEARCH_AREA_CONSENSUS_MECHANISMS = "consensus_mechanisms"
RESEARCH_AREA_ZERO_KNOWLEDGE = "zero_knowledge"
RESEARCH_AREA_MEMORY_OPTIMIZATION = "memory_optimization"
RESEARCH_AREA_TOKEN_ECONOMICS = "token_economics"

class ResearchProject:
    """
    Represents a research project in the R&D department.
    """
    
    def __init__(self,
                project_id: str,
                name: str,
                description: str,
                area: str,
                priority: int = 5,
                status: str = "proposed",
                start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None,
                lead_researcher: Optional[str] = None,
                team_members: Optional[List[str]] = None,
                resources: Optional[Dict[str, Any]] = None,
                metrics: Optional[Dict[str, Any]] = None):
        """
        Initialize a research project.
        
        Args:
            project_id: Unique project identifier
            name: Project name
            description: Project description
            area: Research area (use constants defined above)
            priority: Priority level (1-10, 10 being highest)
            status: Project status (proposed, active, paused, completed)
            start_date: Project start date
            end_date: Expected or actual end date
            lead_researcher: Lead researcher name or ID
            team_members: List of team member names or IDs
            resources: Dict of resources allocated to the project
            metrics: Dict of metrics to track project success
        """
        self.project_id = project_id
        self.name = name
        self.description = description
        self.area = area
        self.priority = priority
        self.status = status
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.lead_researcher = lead_researcher
        self.team_members = team_members or []
        self.resources = resources or {}
        self.metrics = metrics or {}
        self.milestones = []
        self.findings = []
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.progress = 0.0  # 0.0 to 1.0
    
    def add_milestone(self, title: str, description: str, 
                      due_date: datetime, priority: int = 5) -> str:
        """Add a milestone to the project."""
        milestone_id = f"{self.project_id}_m{len(self.milestones) + 1}"
        milestone = {
            "id": milestone_id,
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "completed_at": None,
            "created_at": datetime.now()
        }
        self.milestones.append(milestone)
        self.updated_at = datetime.now()
        return milestone_id
    
    def update_milestone(self, milestone_id: str, 
                         status: str, completed_at: Optional[datetime] = None) -> bool:
        """Update a milestone's status."""
        for i, milestone in enumerate(self.milestones):
            if milestone["id"] == milestone_id:
                self.milestones[i]["status"] = status
                if status == "completed" and not completed_at:
                    completed_at = datetime.now()
                if completed_at:
                    self.milestones[i]["completed_at"] = completed_at
                self.updated_at = datetime.now()
                self._recalculate_progress()
                return True
        return False
    
    def add_finding(self, title: str, description: str, 
                   significance: int = 5, 
                   potential_applications: Optional[List[str]] = None) -> str:
        """Add a research finding to the project."""
        finding_id = f"{self.project_id}_f{len(self.findings) + 1}"
        finding = {
            "id": finding_id,
            "title": title,
            "description": description,
            "significance": significance,  # 1-10
            "potential_applications": potential_applications or [],
            "created_at": datetime.now(),
            "validated": False
        }
        self.findings.append(finding)
        self.updated_at = datetime.now()
        return finding_id
    
    def validate_finding(self, finding_id: str, 
                        validation_note: Optional[str] = None) -> bool:
        """Mark a finding as validated with optional notes."""
        for i, finding in enumerate(self.findings):
            if finding["id"] == finding_id:
                self.findings[i]["validated"] = True
                if validation_note:
                    self.findings[i]["validation_note"] = validation_note
                self.findings[i]["validated_at"] = datetime.now()
                self.updated_at = datetime.now()
                return True
        return False
    
    def update_progress(self, progress: float) -> None:
        """Update project progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now()
    
    def _recalculate_progress(self) -> None:
        """Recalculate project progress based on milestones."""
        if not self.milestones:
            return
            
        completed = sum(1 for m in self.milestones if m["status"] == "completed")
        self.progress = completed / len(self.milestones)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "area": self.area,
            "priority": self.priority,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "lead_researcher": self.lead_researcher,
            "team_members": self.team_members,
            "resources": self.resources,
            "metrics": self.metrics,
            "milestones": self.milestones,
            "findings": self.findings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchProject':
        """Create a project from a dictionary."""
        project = cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data["description"],
            area=data["area"],
            priority=data["priority"],
            status=data["status"],
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            lead_researcher=data.get("lead_researcher"),
            team_members=data.get("team_members", []),
            resources=data.get("resources", {}),
            metrics=data.get("metrics", {})
        )
        
        project.milestones = data.get("milestones", [])
        project.findings = data.get("findings", [])
        project.created_at = datetime.fromisoformat(data["created_at"])
        project.updated_at = datetime.fromisoformat(data["updated_at"])
        project.progress = data.get("progress", 0.0)
        
        return project


class ResearchDepartment:
    """
    Manages research projects and initiatives for VOT1 R&D.
    """
    
    def __init__(self, 
                 data_path: str = "research",
                 principles_engine: Optional[CorePrinciplesEngine] = None,
                 auto_save: bool = True,
                 auto_backup: bool = True):
        """
        Initialize the Research Department.
        
        Args:
            data_path: Path to store research data
            principles_engine: CorePrinciplesEngine instance
            auto_save: Whether to automatically save changes
            auto_backup: Whether to automatically backup data
        """
        self.data_path = data_path
        self.principles_engine = principles_engine
        self.auto_save = auto_save
        self.auto_backup = auto_backup
        
        # Create data directories
        os.makedirs(os.path.join(data_path, "projects"), exist_ok=True)
        os.makedirs(os.path.join(data_path, "findings"), exist_ok=True)
        os.makedirs(os.path.join(data_path, "experiments"), exist_ok=True)
        os.makedirs(os.path.join(data_path, "backups"), exist_ok=True)
        
        # Initialize projects and research areas
        self.projects = {}
        self.research_areas = {
            RESEARCH_AREA_DISTRIBUTED_STORAGE: {
                "name": "Distributed Storage",
                "description": "Research on IPFS, blockchain storage, and decentralized data systems",
                "priority": 10,
                "leads": []
            },
            RESEARCH_AREA_NEURAL_ARCHITECTURE: {
                "name": "Neural Architecture",
                "description": "Improvements to TRILOGY BRAIN architecture and neural processing",
                "priority": 9,
                "leads": []
            },
            RESEARCH_AREA_CONSENSUS_MECHANISMS: {
                "name": "Consensus Mechanisms",
                "description": "Research on distributed consensus for memory verification",
                "priority": 8,
                "leads": []
            },
            RESEARCH_AREA_ZERO_KNOWLEDGE: {
                "name": "Zero Knowledge Proofs",
                "description": "Advanced ZK systems for memory verification and privacy",
                "priority": 7,
                "leads": []
            },
            RESEARCH_AREA_MEMORY_OPTIMIZATION: {
                "name": "Memory Optimization",
                "description": "Optimization of memory storage, retrieval, and management",
                "priority": 8,
                "leads": []
            },
            RESEARCH_AREA_TOKEN_ECONOMICS: {
                "name": "Token Economics",
                "description": "Economic models for incentivizing node operators and participants",
                "priority": 6,
                "leads": []
            }
        }
        
        # Load existing projects
        self._load_projects()
        
        # Setup background tasks if needed
        if auto_save or auto_backup:
            self._setup_background_tasks()
            
        logger.info(f"VOT1 Research Department initialized with {len(self.projects)} projects")
    
    def _load_projects(self) -> None:
        """Load projects from disk."""
        projects_dir = os.path.join(self.data_path, "projects")
        
        for filename in os.listdir(projects_dir):
            if not filename.endswith(".json"):
                continue
                
            try:
                filepath = os.path.join(projects_dir, filename)
                with open(filepath, 'r') as f:
                    project_data = json.load(f)
                    
                project = ResearchProject.from_dict(project_data)
                self.projects[project.project_id] = project
                logger.debug(f"Loaded project {project.project_id}: {project.name}")
                
            except Exception as e:
                logger.error(f"Error loading project from {filename}: {str(e)}")
    
    def _save_project(self, project: ResearchProject) -> bool:
        """Save a project to disk."""
        try:
            filepath = os.path.join(self.data_path, "projects", f"{project.project_id}.json")
            with open(filepath, 'w') as f:
                json.dump(project.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving project {project.project_id}: {str(e)}")
            return False
    
    def _setup_background_tasks(self) -> None:
        """Setup background tasks for auto-save and auto-backup."""
        if self.auto_save:
            threading.Thread(target=self._auto_save_task, daemon=True).start()
            
        if self.auto_backup:
            threading.Thread(target=self._auto_backup_task, daemon=True).start()
    
    def _auto_save_task(self) -> None:
        """Background task for auto-saving projects."""
        while True:
            try:
                for project_id, project in self.projects.items():
                    if project.updated_at > project.created_at:  # Only save if updated
                        self._save_project(project)
                
                logger.debug("Auto-saved projects")
            except Exception as e:
                logger.error(f"Error in auto-save task: {str(e)}")
                
            time.sleep(300)  # 5 minutes
    
    def _auto_backup_task(self) -> None:
        """Background task for auto-backing up research data."""
        while True:
            try:
                # Create a timestamp for the backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = os.path.join(self.data_path, "backups", timestamp)
                os.makedirs(backup_dir, exist_ok=True)
                
                # Backup projects
                for project_id, project in self.projects.items():
                    filepath = os.path.join(backup_dir, f"{project.project_id}.json")
                    with open(filepath, 'w') as f:
                        json.dump(project.to_dict(), f, indent=2)
                
                # Backup research areas
                filepath = os.path.join(backup_dir, "research_areas.json")
                with open(filepath, 'w') as f:
                    json.dump(self.research_areas, f, indent=2)
                
                logger.info(f"Created research backup at {backup_dir}")
                
                # Clean up old backups (keep last 10)
                backup_dirs = sorted([
                    d for d in os.listdir(os.path.join(self.data_path, "backups"))
                    if os.path.isdir(os.path.join(self.data_path, "backups", d))
                ])
                
                if len(backup_dirs) > 10:
                    for old_dir in backup_dirs[:-10]:
                        old_path = os.path.join(self.data_path, "backups", old_dir)
                        import shutil
                        shutil.rmtree(old_path)
                        logger.debug(f"Removed old backup: {old_path}")
                
            except Exception as e:
                logger.error(f"Error in auto-backup task: {str(e)}")
                
            time.sleep(86400)  # 24 hours
    
    def create_project(self, 
                      name: str, 
                      description: str, 
                      area: str,
                      priority: int = 5,
                      lead_researcher: Optional[str] = None,
                      team_members: Optional[List[str]] = None,
                      resources: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new research project.
        
        Args:
            name: Project name
            description: Project description
            area: Research area (use constants defined above)
            priority: Priority level (1-10)
            lead_researcher: Lead researcher name or ID
            team_members: List of team member names or IDs
            resources: Dict of resources allocated to the project
            
        Returns:
            Project ID if successful
        """
        # Verify area is valid
        if area not in self.research_areas:
            logger.warning(f"Invalid research area: {area}")
            return None
            
        # Verify with principles engine if available
        if self.principles_engine:
            action = {
                "type": "research_operation",
                "operation": "create_project",
                "name": name,
                "area": area
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Project creation rejected by principles engine: {reason}")
                return None
        
        # Generate project ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = f"proj_{area}_{timestamp}"
        
        # Create project
        project = ResearchProject(
            project_id=project_id,
            name=name,
            description=description,
            area=area,
            priority=priority,
            status="proposed",
            lead_researcher=lead_researcher,
            team_members=team_members,
            resources=resources
        )
        
        # Add to projects
        self.projects[project_id] = project
        
        # Save if auto_save is disabled (otherwise background task will handle it)
        if not self.auto_save:
            self._save_project(project)
            
        logger.info(f"Created new research project: {project_id} - {name}")
        return project_id
    
    def update_project_status(self, project_id: str, status: str) -> bool:
        """Update a project's status."""
        if project_id not in self.projects:
            logger.warning(f"Project not found: {project_id}")
            return False
            
        valid_statuses = ["proposed", "active", "paused", "completed", "cancelled"]
        if status not in valid_statuses:
            logger.warning(f"Invalid status: {status}")
            return False
            
        project = self.projects[project_id]
        project.status = status
        project.updated_at = datetime.now()
        
        if status == "active" and not project.start_date:
            project.start_date = datetime.now()
            
        if status == "completed" and not project.end_date:
            project.end_date = datetime.now()
            
        # Save if auto_save is disabled
        if not self.auto_save:
            self._save_project(project)
            
        logger.info(f"Updated project {project_id} status to {status}")
        return True
    
    def get_project(self, project_id: str) -> Optional[ResearchProject]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def get_projects_by_area(self, area: str) -> List[ResearchProject]:
        """Get all projects in a research area."""
        return [p for p in self.projects.values() if p.area == area]
    
    def get_active_projects(self) -> List[ResearchProject]:
        """Get all active projects."""
        return [p for p in self.projects.values() if p.status == "active"]
    
    def add_research_finding(self, 
                           project_id: str,
                           title: str,
                           description: str,
                           significance: int = 5,
                           potential_applications: Optional[List[str]] = None) -> Optional[str]:
        """
        Add a research finding to a project.
        
        Args:
            project_id: Project ID
            title: Finding title
            description: Finding description
            significance: Significance level (1-10)
            potential_applications: List of potential applications
            
        Returns:
            Finding ID if successful, None otherwise
        """
        if project_id not in self.projects:
            logger.warning(f"Project not found: {project_id}")
            return None
            
        project = self.projects[project_id]
        finding_id = project.add_finding(
            title=title,
            description=description,
            significance=significance,
            potential_applications=potential_applications
        )
        
        # Save if auto_save is disabled
        if not self.auto_save:
            self._save_project(project)
            
        # If significant finding (8+), save to dedicated findings directory
        if significance >= 8:
            try:
                finding_data = next(f for f in project.findings if f["id"] == finding_id)
                filepath = os.path.join(self.data_path, "findings", f"{finding_id}.json")
                with open(filepath, 'w') as f:
                    json.dump({
                        "finding_id": finding_id,
                        "project_id": project_id,
                        "project_name": project.name,
                        "title": title,
                        "description": description,
                        "significance": significance,
                        "potential_applications": potential_applications or [],
                        "created_at": finding_data["created_at"],
                        "area": project.area,
                        "area_name": self.research_areas[project.area]["name"]
                    }, f, indent=2)
                logger.info(f"Saved significant finding {finding_id} to findings directory")
            except Exception as e:
                logger.error(f"Error saving significant finding: {str(e)}")
            
        logger.info(f"Added finding {finding_id} to project {project_id}")
        return finding_id
    
    def validate_finding(self, 
                       project_id: str,
                       finding_id: str,
                       validation_note: Optional[str] = None) -> bool:
        """Validate a research finding."""
        if project_id not in self.projects:
            logger.warning(f"Project not found: {project_id}")
            return False
            
        project = self.projects[project_id]
        if project.validate_finding(finding_id, validation_note):
            # Save if auto_save is disabled
            if not self.auto_save:
                self._save_project(project)
                
            logger.info(f"Validated finding {finding_id} in project {project_id}")
            return True
        else:
            logger.warning(f"Finding not found: {finding_id}")
            return False
    
    def get_research_roadmap(self) -> Dict[str, Any]:
        """
        Get a research roadmap with projects organized by area and priority.
        
        Returns:
            Dictionary with research roadmap
        """
        roadmap = {}
        
        for area_id, area_info in self.research_areas.items():
            area_projects = self.get_projects_by_area(area_id)
            active_projects = [p for p in area_projects if p.status == "active"]
            proposed_projects = [p for p in area_projects if p.status == "proposed"]
            completed_projects = [p for p in area_projects if p.status == "completed"]
            
            # Sort by priority
            active_projects.sort(key=lambda p: p.priority, reverse=True)
            proposed_projects.sort(key=lambda p: p.priority, reverse=True)
            
            roadmap[area_id] = {
                "name": area_info["name"],
                "description": area_info["description"],
                "priority": area_info["priority"],
                "leads": area_info["leads"],
                "active_projects": [p.to_dict() for p in active_projects],
                "proposed_projects": [p.to_dict() for p in proposed_projects],
                "completed_projects": len(completed_projects),
                "total_projects": len(area_projects)
            }
            
        return roadmap
    
    def get_department_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the research department.
        
        Returns:
            Dictionary with department statistics
        """
        total_projects = len(self.projects)
        active_projects = len([p for p in self.projects.values() if p.status == "active"])
        completed_projects = len([p for p in self.projects.values() if p.status == "completed"])
        
        # Calculate findings stats
        total_findings = sum(len(p.findings) for p in self.projects.values())
        validated_findings = sum(
            sum(1 for f in p.findings if f.get("validated", False))
            for p in self.projects.values()
        )
        significant_findings = sum(
            sum(1 for f in p.findings if f.get("significance", 0) >= 8)
            for p in self.projects.values()
        )
        
        # Calculate milestone stats
        total_milestones = sum(len(p.milestones) for p in self.projects.values())
        completed_milestones = sum(
            sum(1 for m in p.milestones if m.get("status") == "completed")
            for p in self.projects.values()
        )
        
        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "completed_projects": completed_projects,
            "total_findings": total_findings,
            "validated_findings": validated_findings,
            "significant_findings": significant_findings,
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "research_areas": len(self.research_areas),
            "department_health": self._calculate_department_health(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _calculate_department_health(self) -> float:
        """
        Calculate the overall health of the research department (0.0 to 1.0).
        This is a composite score based on project progress, finding validation, etc.
        
        Returns:
            Health score from 0.0 to 1.0
        """
        if not self.projects:
            return 0.0
            
        # Factor 1: Project progress
        active_projects = [p for p in self.projects.values() if p.status == "active"]
        if active_projects:
            avg_progress = sum(p.progress for p in active_projects) / len(active_projects)
        else:
            avg_progress = 0.0
            
        # Factor 2: Finding validation rate
        total_findings = sum(len(p.findings) for p in self.projects.values())
        if total_findings > 0:
            validated_findings = sum(
                sum(1 for f in p.findings if f.get("validated", False))
                for p in self.projects.values()
            )
            validation_rate = validated_findings / total_findings
        else:
            validation_rate = 0.0
            
        # Factor 3: Project completion rate (over all time)
        completed_projects = len([p for p in self.projects.values() if p.status == "completed"])
        completion_rate = completed_projects / len(self.projects) if self.projects else 0.0
        
        # Factor 4: Milestone completion rate
        total_milestones = sum(len(p.milestones) for p in self.projects.values())
        if total_milestones > 0:
            completed_milestones = sum(
                sum(1 for m in p.milestones if m.get("status") == "completed")
                for p in self.projects.values()
            )
            milestone_rate = completed_milestones / total_milestones
        else:
            milestone_rate = 0.0
            
        # Combined score (weighted)
        health_score = (
            0.4 * avg_progress +
            0.2 * validation_rate +
            0.2 * completion_rate +
            0.2 * milestone_rate
        )
        
        return max(0.0, min(1.0, health_score))


# Example initial research projects for TRILOGY BRAIN
INITIAL_RESEARCH_PROJECTS = [
    {
        "name": "IPFS Integration for Distributed Memory Storage",
        "description": (
            "Research and develop integration between TRILOGY BRAIN memory "
            "foundation and IPFS network for distributed storage of non-critical memories. "
            "This will enable truly distributed operation and resilience."
        ),
        "area": RESEARCH_AREA_DISTRIBUTED_STORAGE,
        "priority": 10,
        "milestones": [
            {
                "title": "IPFS Architecture Design",
                "description": "Design the integration architecture between TRILOGY BRAIN and IPFS",
                "due_date": datetime.now() + timedelta(days=14)
            },
            {
                "title": "Content Addressing Implementation",
                "description": "Implement content addressing for memories compatible with IPFS CIDs",
                "due_date": datetime.now() + timedelta(days=28)
            },
            {
                "title": "Memory Storage/Retrieval via IPFS",
                "description": "Implement storage and retrieval of memories via IPFS",
                "due_date": datetime.now() + timedelta(days=42)
            }
        ]
    },
    {
        "name": "Continuous Neural Architecture",
        "description": (
            "Research and develop continuous operation capabilities for the "
            "TRILOGY BRAIN neural architecture. This includes fault tolerance, "
            "self-healing, and dynamic resource allocation."
        ),
        "area": RESEARCH_AREA_NEURAL_ARCHITECTURE,
        "priority": 9,
        "milestones": [
            {
                "title": "Continuous Operation Requirements",
                "description": "Define requirements for continuous operation of TRILOGY BRAIN",
                "due_date": datetime.now() + timedelta(days=10)
            },
            {
                "title": "Fault Tolerance Design",
                "description": "Design fault tolerance mechanisms for continuous operation",
                "due_date": datetime.now() + timedelta(days=24)
            },
            {
                "title": "Self-Healing Implementation",
                "description": "Implement self-healing capabilities for TRILOGY BRAIN",
                "due_date": datetime.now() + timedelta(days=38)
            }
        ]
    },
    {
        "name": "TRILOGY NODE Economy and Rewards",
        "description": (
            "Develop an economic model for incentivizing node operators "
            "in the TRILOGY BRAIN network. This includes token distribution, "
            "rewards for memory storage/validation, and governance mechanisms."
        ),
        "area": RESEARCH_AREA_TOKEN_ECONOMICS,
        "priority": 8,
        "milestones": [
            {
                "title": "Node Operator Incentives Model",
                "description": "Design economic incentives for node operators",
                "due_date": datetime.now() + timedelta(days=21)
            },
            {
                "title": "Token Distribution Mechanism",
                "description": "Develop token distribution mechanisms for node rewards",
                "due_date": datetime.now() + timedelta(days=35)
            },
            {
                "title": "Governance Model",
                "description": "Design governance mechanisms for the TRILOGY BRAIN network",
                "due_date": datetime.now() + timedelta(days=49)
            }
        ]
    }
]


def initialize_research_department(data_path: str = "research",
                                  principles_engine: Optional[CorePrinciplesEngine] = None) -> ResearchDepartment:
    """
    Initialize the research department with initial projects.
    
    Args:
        data_path: Path to store research data
        principles_engine: CorePrinciplesEngine instance
        
    Returns:
        Initialized ResearchDepartment
    """
    department = ResearchDepartment(data_path, principles_engine)
    
    # Check if we already have projects
    if department.projects:
        logger.info(f"Research department already has {len(department.projects)} projects")
        return department
    
    # Create initial projects
    for project_data in INITIAL_RESEARCH_PROJECTS:
        project_id = department.create_project(
            name=project_data["name"],
            description=project_data["description"],
            area=project_data["area"],
            priority=project_data["priority"]
        )
        
        if project_id:
            project = department.projects[project_id]
            
            # Add milestones
            for milestone in project_data.get("milestones", []):
                project.add_milestone(
                    title=milestone["title"],
                    description=milestone["description"],
                    due_date=milestone["due_date"],
                    priority=project_data["priority"]
                )
            
            # Set to active
            department.update_project_status(project_id, "active")
    
    logger.info(f"Initialized research department with {len(department.projects)} projects")
    return department 