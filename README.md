# TRILOGY BRAIN Memory Systems

<div align="center">
  <img src="https://via.placeholder.com/800x200/3A1078/FFFFFF?text=TRILOGY+BRAIN" alt="TRILOGY BRAIN" width="100%" />
  <p><em>Advanced memory systems for Large Language Models</em></p>
</div>

## Overview

TRILOGY BRAIN is a cognitive architecture for large language models that implements advanced memory systems, reasoning frameworks, and enhanced interaction capabilities. This repository contains the implementation of two key memory systems:

1. **CascadingMemoryCache** - Infinite context extension via cascading KV cache
2. **EpisodicMemoryManager** - Human-like episodic memory organization

Together, these systems enable Claude 3.7 to maintain effectively unlimited context while organizing information in a cognitively-inspired way.

## Key Components

### CascadingMemoryCache

The `CascadingMemoryCache` implements a novel approach to memory management based on the paper "Training-Free Exponential Context Extension via Cascading KV Cache" (Willette et al., Feb 2025). It enables effectively infinite context through hierarchical memory organization with:

- **Multi-level memory caching** with exponentially increasing capacity
- **Importance-based retention policies** that vary by level
- **Adaptive compression** to optimize token usage
- **Smart context building** based on importance, recency, and query relevance

[Learn more about CascadingMemoryCache](docs/CascadingMemoryCache.md)

### EpisodicMemoryManager

The `EpisodicMemoryManager` implements human-like episodic memory organization with:

- **Event boundary detection** using Bayesian surprise
- **Temporal organization** of memories into coherent episodes
- **Importance-based memory consolidation** for long-term retention
- **Multi-scale retrieval strategies** that balance temporal and semantic relationships

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trilogy-brain.git
cd trilogy-brain

# Install dependencies
pip install -r requirements.txt
```

### Usage Example

```python
from src.vot1.memory.cascading_cache import CascadingMemoryCache
from src.vot1.memory.episodic_memory import EpisodicMemoryManager

# Initialize memory systems
cascading_cache = CascadingMemoryCache(
    cascade_levels=3,
    base_cache_size=4096,
    token_budget=200000  # Claude 3.7 context size
)

# Process a memory
result = await cascading_cache.process_memory(
    memory={
        "id": "mem_12345",
        "content": "Important information to remember",
        "timestamp": time.time(),
        "importance": 0.8
    }
)

# Build context for a query
context = cascading_cache.build_context(
    query="information to remember",
    token_budget=150000
)

# Use the formatted context
formatted_context = context["formatted_context"]
```

## Performance Results

The memory systems have been extensively tested and shown to provide significant benefits:

- **Token Efficiency**: 2-3x improvement over standard caching approaches
- **Memory Retention**: >85% retention of important memories
- **Processing Speed**: <1ms average memory processing time 
- **Context Quality**: High relevance scores across different query types

[View detailed performance results](docs/CascadingMemoryCache_Results.md)

## Documentation

- [CascadingMemoryCache Documentation](docs/CascadingMemoryCache.md)
- [Performance Report](docs/CascadingMemoryCache_Results.md)

## Testing

Run the test suite for the CascadingMemoryCache:

```bash
python scripts/test_cascading_cache.py --memory-count 100
```

This will generate a detailed performance report in the `data` directory.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Claude 3.7 Sonnet for implementation assistance and documentation generation
- The ideas in this project were inspired by research in cognitive psychology, memory systems, and large language model augmentation

<div align="center">
  <p>Developed with 💜 by the TRILOGY BRAIN team</p>
</div> 