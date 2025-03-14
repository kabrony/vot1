"""
VOTai Local MCP Bridge Package

This package provides a local bridge to the Model Context Protocol (MCP) services,
enabling seamless integration between local applications and MCP services like
GitHub, Perplexity, Firecrawl, Figma, and Composio.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

from .bridge import LocalMCPBridge
from .server import LocalMCPServer
from .agent import FeedbackAgent
from .development_agent import DevelopmentAgent
from .ascii_art import get_votai_ascii

__version__ = "0.3.2"  # Updated with VOTai branding
__all__ = ['LocalMCPBridge', 'LocalMCPServer', 'FeedbackAgent', 'DevelopmentAgent', 'get_votai_ascii'] 