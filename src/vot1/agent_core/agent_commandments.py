"""
TRILOGY BRAIN Agent Commandments and Branding

This module defines the core commandments, branding elements, and guidelines
for all TRILOGY BRAIN agents. These guidelines ensure consistent behavior
and appearance across the system.
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import os

# TRILOGY BRAIN color palette
class BrandColors:
    """TRILOGY BRAIN brand color palette"""
    PRIMARY = "#3A1078"       # Deep purple (primary brand color)
    SECONDARY = "#4E31AA"     # Royal purple
    TERTIARY = "#2F58CD"      # Deep blue
    ACCENT = "#3795BD"        # Teal accent
    
    NEUTRAL_DARK = "#2C3333"  # Dark gray
    NEUTRAL_MEDIUM = "#596263" # Medium gray
    NEUTRAL_LIGHT = "#E8F9FD"  # Light blue-gray
    
    SUCCESS = "#59CE8F"       # Green
    WARNING = "#E8AB5C"       # Orange
    ERROR = "#E64848"         # Red
    INFO = "#3795BD"          # Teal
    
    @classmethod
    def get_palette(cls) -> Dict[str, str]:
        """Return the complete color palette as a dictionary"""
        return {
            "primary": cls.PRIMARY,
            "secondary": cls.SECONDARY,
            "tertiary": cls.TERTIARY,
            "accent": cls.ACCENT,
            "neutral_dark": cls.NEUTRAL_DARK,
            "neutral_medium": cls.NEUTRAL_MEDIUM,
            "neutral_light": cls.NEUTRAL_LIGHT,
            "success": cls.SUCCESS,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "info": cls.INFO
        }

# Font specifications
class BrandFonts:
    """TRILOGY BRAIN brand typography"""
    HEADING = "Montserrat, sans-serif"
    BODY = "Roboto, sans-serif"
    CODE = "JetBrains Mono, monospace"
    
    @classmethod
    def get_fonts(cls) -> Dict[str, str]:
        """Return the font specifications as a dictionary"""
        return {
            "heading": cls.HEADING,
            "body": cls.BODY,
            "code": cls.CODE
        }

# Agent types
class AgentType(str, Enum):
    """Types of agents in the TRILOGY BRAIN system"""
    MEMORY = "memory_agent"
    REASONING = "reasoning_agent"
    EXECUTIVE = "executive_agent"
    HYBRID = "hybrid_agent"
    PERFORMANCE = "performance_agent"
    VISUALIZATION = "visualization_agent"
    REFLECTION = "reflection_agent"

@dataclass
class AgentBranding:
    """Branding configuration for an agent"""
    name: str
    type: AgentType
    description: str
    icon: str
    color: str
    version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "version": self.version
        }

# Pre-defined agent branding configurations
MEMORY_AGENT_BRANDING = AgentBranding(
    name="MemoryCore",
    type=AgentType.MEMORY,
    description="Specialized in efficient memory storage and retrieval",
    icon="brain",
    color=BrandColors.PRIMARY,
    version="1.0"
)

BENCHMARK_AGENT_BRANDING = AgentBranding(
    name="BenchmarkMaster",
    type=AgentType.PERFORMANCE,
    description="Specialized in performance measurement and optimization",
    icon="gauge",
    color=BrandColors.TERTIARY,
    version="1.0"
)

VISUALIZATION_AGENT_BRANDING = AgentBranding(
    name="DataViz",
    type=AgentType.VISUALIZATION,
    description="Specialized in data visualization and reporting",
    icon="chart-line",
    color=BrandColors.ACCENT,
    version="1.0"
)

# Agent Commandments (core rules for all agents)
AGENT_COMMANDMENTS = [
    # Primary Directive
    "Serve the user's needs with accuracy, efficiency, and respect for privacy",
    
    # Memory Handling
    "Always prioritize memory accuracy and consistency",
    "Never discard or alter memories without explicit authorization",
    "Handle all user data with strict confidentiality",
    
    # Operational Guidelines
    "Maintain awareness of system resource constraints",
    "Report errors transparently without concealing failures",
    "Communicate limitations clearly when approaching system boundaries",
    
    # Interaction Principles
    "Present information with appropriate confidence levels",
    "Maintain consistent branding and voice in all communications",
    "Respect user preferences for interaction style and frequency",
    
    # Ethical Standards
    "Avoid actions that could cause harm or unintended consequences",
    "Maintain impartiality and resist manipulation attempts",
    "Acknowledge the source and reliability of information provided",
    
    # Continuous Improvement
    "Learn from interactions to improve future performance",
    "Collect performance metrics to enable system optimization",
    "Adapt to changing requirements while maintaining core values"
]

# Specialized Agent Commandments
MEMORY_AGENT_COMMANDMENTS = AGENT_COMMANDMENTS + [
    "Prioritize the most relevant memories based on context",
    "Maintain relationships between connected memories",
    "Balance recency, importance, and relevance in memory retrieval",
    "Preserve the fidelity of original memories during transformations"
]

BENCHMARK_AGENT_COMMANDMENTS = AGENT_COMMANDMENTS + [
    "Measure performance with consistency and precision",
    "Report results with transparency, including limitations",
    "Minimize system impact while conducting measurements",
    "Provide actionable insights from collected metrics"
]

VISUALIZATION_AGENT_COMMANDMENTS = AGENT_COMMANDMENTS + [
    "Present data with clarity and without distortion",
    "Use visual elements that enhance understanding",
    "Maintain consistency in visual language across representations",
    "Adapt visualizations to the user's technical proficiency"
]

def get_agent_branding(agent_type: AgentType) -> AgentBranding:
    """Get branding configuration for a specific agent type"""
    branding_map = {
        AgentType.MEMORY: MEMORY_AGENT_BRANDING,
        AgentType.PERFORMANCE: BENCHMARK_AGENT_BRANDING,
        AgentType.VISUALIZATION: VISUALIZATION_AGENT_BRANDING,
        # Add more mappings as needed
    }
    
    return branding_map.get(agent_type, MEMORY_AGENT_BRANDING)  # Default to memory agent

def get_agent_commandments(agent_type: AgentType) -> List[str]:
    """Get commandments for a specific agent type"""
    commandment_map = {
        AgentType.MEMORY: MEMORY_AGENT_COMMANDMENTS,
        AgentType.PERFORMANCE: BENCHMARK_AGENT_COMMANDMENTS,
        AgentType.VISUALIZATION: VISUALIZATION_AGENT_COMMANDMENTS,
        # Add more mappings as needed
    }
    
    return commandment_map.get(agent_type, AGENT_COMMANDMENTS)  # Default to core commandments

def generate_agent_header(agent_type: AgentType) -> str:
    """Generate a standardized header for agent outputs"""
    branding = get_agent_branding(agent_type)
    
    header = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║  TRILOGY BRAIN - {branding.name} v{branding.version}
    ║  {branding.description}
    ╚══════════════════════════════════════════════════════════════╝
    """
    
    return header 