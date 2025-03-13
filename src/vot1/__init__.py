"""
VOT1 - Memory Management System with OWL Reasoning and Self-Improvement

This package provides a sophisticated memory management system with OWL reasoning
capabilities and self-improvement workflows for autonomous code enhancement.

Key modules:
- memory: Vector-based memory storage and retrieval
- owl_reasoning: Semantic reasoning using OWL ontologies
- vot_mcp: Model Control Protocol for AI model interaction
- self_improvement_workflow: Framework for autonomous system improvement
- self_improvement_agent: Agent for autonomous code enhancement
- dashboard: THREE.js visualization with cyberpunk aesthetic
"""

__version__ = "0.1.0"

# Import key classes for easier access
try:
    from vot1.enhanced_client import VOT1Client
    from vot1.perplexity_client import PerplexityMcpClient
    from vot1.memory import MemoryManager, VectorStore
except ImportError:
    # During initial setup these imports might not be available yet
    pass 