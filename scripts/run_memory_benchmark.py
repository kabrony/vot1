#!/usr/bin/env python
"""
Memory Benchmark Runner for TRILOGY BRAIN

This script runs benchmarks for the TRILOGY BRAIN memory system.
It provides command-line options for configuring benchmark parameters.
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.vot1.composio.memory_benchmark import MemoryBenchmark
    from src.vot1.composio.benchmark_visualization import BenchmarkVisualizer
    from src.vot1.utils.logging import configure_logging
    from src.vot1.agent_core.agent_commandments import AgentType, generate_agent_header
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)

# Configure logging
configure_logging()
logger = logging.getLogger('memory_benchmark_runner')

async def run_benchmark(args):
    """Run the memory benchmark with specified options."""
    logger.info(f"Running benchmark with {args.memory_count} memories")
    logger.info(f"Memory path: {args.memory_path}")
    logger.info(f"Output path: {args.output_path}")
    
    try:
        # Print agent header if available
        try:
            benchmark_header = generate_agent_header(AgentType.PERFORMANCE)
            print(benchmark_header)
        except Exception:
            pass
        
        logger.info("Starting memory benchmark")
        
        # Create the benchmark instance
        benchmark = MemoryBenchmark(
            memory_path=args.memory_path,
            benchmark_data_path=args.output_path,
            clean_after_benchmark=not args.no_cleanup
        )
        
        # Run the benchmark
        if args.dry_run:
            # Run with minimal memory count for testing
            results = await benchmark.process(
                memory_count=min(args.memory_count, 10),
                include_hybrid_thinking=args.include_hybrid_thinking
            )
        else:
            results = await benchmark.process(
                memory_count=args.memory_count,
                include_hybrid_thinking=args.include_hybrid_thinking
            )
        
        # Generate report if requested
        if args.generate_report:
            report = await benchmark.generate_benchmark_report()
            logger.info(f"Generated benchmark report: {report}")
        
        # Generate visualizations if requested
        if args.visualize:
            visualizer = BenchmarkVisualizer(
                results_dir=args.output_path,
                output_dir=os.path.join(args.output_path, "visualizations")
            )
            
            viz_results = await visualizer.process(
                results=results,
                output_format="both" if args.generate_report else "charts"
            )
            
            if viz_results.get("success", False):
                logger.info(f"Generated {len(viz_results.get('charts', []))} visualization charts")
            else:
                logger.error(f"Visualization failed: {viz_results.get('error', 'Unknown error')}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        return 1

def main():
    """Parse command-line arguments and run the benchmark."""
    parser = argparse.ArgumentParser(description='Run memory benchmarks for TRILOGY BRAIN')
    
    parser.add_argument('--memory-count', type=int, default=100,
                        help='Number of test memories to generate')
    
    parser.add_argument('--memory-path', type=str, default='memory/benchmark',
                        help='Path to store benchmark memories')
    
    parser.add_argument('--output-path', type=str, default='data/benchmark',
                        help='Path to store benchmark results')
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Run a quick test with minimal memory count')
    
    parser.add_argument('--no-cleanup', action='store_true',
                        help='Do not clean up test memories after benchmark')
    
    parser.add_argument('--visualize', action='store_true',
                        help='Generate visualizations of benchmark results')
    
    parser.add_argument('--generate-report', action='store_true',
                        help='Generate a detailed benchmark report')
    
    parser.add_argument('--include-hybrid-thinking', action='store_true',
                        help='Include hybrid thinking benchmarks (Claude 3.7 specific)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_path, exist_ok=True)
    os.makedirs(args.memory_path, exist_ok=True)
    
    # Run the benchmark
    return asyncio.run(run_benchmark(args))

if __name__ == '__main__':
    sys.exit(main()) 