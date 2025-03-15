"""
Agent Core Module for TRILOGY BRAIN

This module provides core functionality for TRILOGY BRAIN agents,
including branding, commandments, and common agent behaviors.
"""

from .agent_commandments import (
    AgentType,
    AgentBranding,
    BrandColors,
    BrandFonts,
    get_agent_branding,
    get_agent_commandments,
    generate_agent_header,
    AGENT_COMMANDMENTS,
    MEMORY_AGENT_COMMANDMENTS,
    BENCHMARK_AGENT_COMMANDMENTS,
    VISUALIZATION_AGENT_COMMANDMENTS
)

__all__ = [
    'AgentType',
    'AgentBranding',
    'BrandColors',
    'BrandFonts',
    'get_agent_branding',
    'get_agent_commandments',
    'generate_agent_header',
    'AGENT_COMMANDMENTS',
    'MEMORY_AGENT_COMMANDMENTS',
    'BENCHMARK_AGENT_COMMANDMENTS',
    'VISUALIZATION_AGENT_COMMANDMENTS'
] 