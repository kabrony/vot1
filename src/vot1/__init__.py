"""
TRILOGY BRAIN - Advanced Language Model Cognitive Architecture

A cognitive architecture for large language models, implementing advanced memory
systems, reasoning frameworks, and enhanced interaction capabilities.
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