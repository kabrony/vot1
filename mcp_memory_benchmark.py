"""
Memory Benchmark for VOTai with MCP and Composio Integration

This script benchmarks the performance of the VOTai memory system when used with
Model Control Protocol (MCP) and Composio tools.
"""

import os
import sys
import time
import json
import asyncio
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    # Try to import from the VOTai system
    from src.vot1.composio.memory_benchmark import MemoryBenchmark
    from src.vot1.vot_mcp import VotModelControlProtocol
    from src.vot1.composio.client import ComposioClient
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
except ImportError:
    print("VOTai system not found. Please ensure you're in the correct directory.")
    sys.exit(1)

async def run_benchmark(memory_count: int = 100, include_hybrid_thinking: bool = True):
    """
    Run a comprehensive memory benchmark with MCP and Composio integration.
    
    Args:
        memory_count: Number of test memories to generate
        include_hybrid_thinking: Whether to include hybrid thinking benchmarks
    """
    print(f"Starting memory benchmark with {memory_count} memories...")
    print(f"Hybrid thinking: {'Enabled' if include_hybrid_thinking else 'Disabled'}")
    print("=" * 80)
    
    # Initialize the benchmark
    benchmark = MemoryBenchmark(
        memory_path="memory/benchmark",
        benchmark_data_path="data/benchmark",
        clean_after_benchmark=True
    )
    
    # Run the benchmark
    start_time = time.time()
    results = await benchmark.run_full_benchmark(
        memory_count=memory_count,
        include_hybrid_thinking=include_hybrid_thinking
    )
    total_time = time.time() - start_time
    
    # Print summary
    print("\nBenchmark completed in {:.2f} seconds".format(total_time))
    print("=" * 80)
    
    # Print key metrics
    if "storage" in results:
        storage = results["storage"]
        if "single_operation" in storage:
            print("\nMemory Storage Performance:")
            print(f"  Single operation: {storage['single_operation'].get('mean', 0):.4f}s (avg)")
        
        if "batch_operations" in storage and 100 in storage["batch_operations"]:
            batch_100 = storage["batch_operations"][100]
            print(f"  Batch (100): {batch_100.get('total_time', 0):.4f}s total, {batch_100.get('per_memory', 0):.4f}s per memory")
    
    if "retrieval" in results:
        retrieval = results["retrieval"]
        if "search_operations" in retrieval:
            print("\nMemory Retrieval Performance:")
            print(f"  Search: {retrieval['search_operations'].get('mean_time', 0):.4f}s (avg)")
    
    if "hybrid_processing" in results:
        hybrid = results["hybrid_processing"]
        if "memory_limit_impact" in hybrid and 10 in hybrid["memory_limit_impact"]:
            print("\nHybrid Processing Performance:")
            hybrid_10 = hybrid["memory_limit_impact"][10]
            print(f"  10 memories: {hybrid_10.get('total_time', 0):.4f}s total")
            print(f"  Retrieval: {hybrid_10.get('retrieval_time', 0):.4f}s, Processing: {hybrid_10.get('processing_time', 0):.4f}s")
    
    if "hybrid_thinking" in results and include_hybrid_thinking:
        thinking = results["hybrid_thinking"]
        if "thinking_token_limits" in thinking and 5000 in thinking["thinking_token_limits"]:
            print("\nHybrid Thinking Performance (Claude 3.7):")
            thinking_5k = thinking["thinking_token_limits"][5000]
            print(f"  5K tokens: {thinking_5k.get('total_time', 0):.4f}s, {thinking_5k.get('tokens_per_second', 0):.2f} tokens/s")
    
    # Generate report
    print("\nGenerating benchmark report...")
    report = await benchmark.generate_benchmark_report()
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"mcp_memory_benchmark_{timestamp}.md"
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"Report saved to {report_file}")
    
    return results

async def main():
    """Run the benchmark script"""
    import argparse
    parser = argparse.ArgumentParser(description="VOTai Memory Benchmark with MCP and Composio")
    parser.add_argument("--count", type=int, default=100, help="Number of test memories")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable hybrid thinking benchmarks")
    args = parser.parse_args()
    
    try:
        await run_benchmark(
            memory_count=args.count,
            include_hybrid_thinking=not args.no_hybrid
        )
    except Exception as e:
        print(f"Error in benchmark: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the benchmark
    asyncio.run(main()) 