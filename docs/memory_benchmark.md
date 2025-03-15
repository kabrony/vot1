# TRILOGY BRAIN Memory Benchmarking System

This document provides information about the memory benchmarking tools available in the TRILOGY BRAIN system, which help evaluate and optimize memory performance.

## Overview

The memory benchmarking system consists of several components:

1. **Memory Benchmark** - Core benchmarking tool that tests various aspects of memory operations
2. **Benchmark Visualization** - Tool for generating visualizations of benchmark results
3. **Command-line Runner** - Script for running benchmarks and generating reports

These tools help measure and visualize performance metrics for memory operations, enabling data-driven optimization of the memory system.

## Installation

To install the required dependencies for the benchmarking system:

```bash
pip install -r requirements-benchmark.txt
```

## Running Benchmarks

The benchmark runner script (`scripts/run_memory_benchmark.py`) provides a convenient way to run comprehensive memory benchmarks:

```bash
# Basic benchmark with default settings
./scripts/run_memory_benchmark.py

# Run a benchmark with 200 memories and generate visualizations
./scripts/run_memory_benchmark.py --memory-count 200 --visualize

# Run a comprehensive benchmark with reports and visualizations
./scripts/run_memory_benchmark.py --memory-count 150 --generate-report --visualize --keep-data
```

### Command-line Options

- `--memory-count` - Number of test memories to generate (default: 100)
- `--memory-path` - Path to store test memories (default: memory/benchmark)
- `--output-path` - Path to store benchmark results (default: data/benchmark)
- `--keep-data` - Keep test data after benchmark (default: False)
- `--generate-report` - Generate a benchmark report (default: False)
- `--visualize` - Generate visualization charts (default: False)
- `--dry-run` - Run in dry run mode without actual Composio client (default: False)

## Benchmark Components

The benchmark tests the following aspects of the memory system:

### Memory Storage

- Single memory storage performance
- Batch memory storage operations
- Concurrent memory storage operations

### Memory Retrieval

- Direct memory retrieval by ID
- Semantic search operations
- Comparison of retrieval strategies (semantic, temporal, hybrid)

### Relationship Operations

- Relationship creation performance
- Relationship retrieval performance
- Graph traversal performance

### Memory Reflection

- Reflection performance at different depths
- Impact of memory count on reflection performance

### Hybrid Processing

- Impact of memory limit on hybrid processing
- Comparison of retrieval strategies in hybrid mode

## Visualization

The visualization system generates charts for each benchmark category and produces an HTML report with:

- Performance charts
- Summary statistics
- Recommendations for optimization

Visualizations are stored in the `{output_path}/visualizations` directory, and the HTML report provides an integrated view of all results.

## Extending Benchmarks

To extend the benchmarking system with new tests:

1. Add new benchmark methods to the `MemoryBenchmark` class in `src/vot1/composio/memory_benchmark.py`
2. Add visualization methods for new benchmarks to `BenchmarkVisualizer` in `src/vot1/composio/benchmark_visualization.py`
3. Update the command-line runner if needed

## Performance Tuning

The benchmark results can help identify bottlenecks and optimization opportunities:

- If direct retrieval is slow, consider optimizing the storage backend
- If concurrent operations show significant improvement, update memory operations to use concurrency
- Use the recommended memory limit for hybrid processing
- Select the most efficient retrieval strategy for your use case

## Example Reports

After running a benchmark with visualizations, you can find:

- JSON results in `data/benchmark/benchmark_*.json`
- Markdown reports in `data/benchmark/benchmark_report_*.md`
- Visualization charts in `data/benchmark/visualizations/*.png`
- HTML report in `data/benchmark/visualizations/benchmark_report_*.html` 