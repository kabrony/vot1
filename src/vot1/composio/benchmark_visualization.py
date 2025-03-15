"""
Benchmark Visualization for TRILOGY BRAIN

This module provides visualization tools for memory benchmark results.
It generates charts and graphs to help analyze performance metrics.
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

try:
    # Try absolute imports first (for installed package)
    from vot1.utils.logging import get_logger
    from vot1.agent_core.base_agent import BaseAgent
    from vot1.agent_core.agent_commandments import AgentType
except ImportError:
    # Fall back to relative imports (for development)
    from src.vot1.utils.logging import get_logger
    from src.vot1.agent_core.base_agent import BaseAgent
    from src.vot1.agent_core.agent_commandments import AgentType

# Configure logging now handled by BaseAgent
# logger = get_logger(__name__)

class BenchmarkVisualizer(BaseAgent):
    """
    Visualizer for TRILOGY BRAIN memory benchmark results.
    
    This class provides methods to generate visualizations for benchmark data:
    1. Storage performance charts
    2. Retrieval performance charts  
    3. Relationship operation charts
    4. Memory reflection charts
    5. Hybrid processing charts
    6. Hybrid thinking charts (Claude 3.7 specific)
    """
    
    def __init__(
        self,
        results_dir: str = "data/benchmark",
        output_dir: str = "data/benchmark/visualizations",
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the benchmark visualizer.
        
        Args:
            results_dir: Directory containing benchmark results
            output_dir: Directory to store visualizations
            agent_id: Unique identifier for this agent instance
            config: Configuration dictionary
        """
        # Initialize BaseAgent
        super().__init__(
            agent_type=AgentType.VISUALIZATION,
            agent_id=agent_id,
            config=config or {}
        )
        
        self.results_dir = results_dir
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Hybrid thinking visualization settings
        self.hybrid_thinking_enabled = True
        self.use_enhanced_visuals = True
        self.include_branding = True
        self.model_version = "claude-3-7-sonnet"
        
        self.logger.info("Benchmark Visualizer initialized")
    
    async def process(self, results: Optional[Dict[str, Any]] = None, output_format: str = "both") -> Dict[str, Any]:
        """
        Process visualization request (implementation of abstract method from BaseAgent).
        
        Args:
            results: Benchmark results to visualize, or None to load the latest
            output_format: Output format, one of "charts", "html", or "both"
            
        Returns:
            Dictionary with visualization results
        """
        self.activate()
        
        try:
            # Load results if not provided
            if results is None:
                results = self.load_benchmark_results()
            
            if not results:
                self.logger.warning("No benchmark results available for visualization")
                self.deactivate()
                return {"success": False, "error": "No benchmark results available"}
            
            # Generate charts
            operation_start = time.time()
            chart_files = self.generate_all_charts(results)
            self.record_operation("generate_charts", True, time.time() - operation_start)
            
            response = {
                "success": True,
                "charts": chart_files,
                "html_report": ""
            }
            
            # Generate HTML report if requested
            if output_format in ["html", "both"]:
                operation_start = time.time()
                html_report = self.generate_html_report(chart_files, results)
                self.record_operation("generate_html_report", True, time.time() - operation_start)
                response["html_report"] = html_report
            
            self.deactivate()
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing visualization request: {e}")
            self.record_operation("process", False, 0)
            self.deactivate()
            return {"success": False, "error": str(e)}
    
    def load_benchmark_results(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Load benchmark results from file.
        
        Args:
            filename: Specific results file to load, or None to load the latest
            
        Returns:
            Dictionary with benchmark results
        """
        try:
            operation_start = time.time()
            
            if filename:
                result_path = os.path.join(self.results_dir, filename)
            else:
                # Find latest results file
                result_files = [f for f in os.listdir(self.results_dir) 
                              if f.startswith("benchmark_") and f.endswith(".json")]
                
                if not result_files:
                    self.logger.error("No benchmark results found")
                    return {}
                
                result_files.sort(reverse=True)  # Latest first
                result_path = os.path.join(self.results_dir, result_files[0])
            
            with open(result_path, "r") as f:
                results = json.load(f)
            
            self.logger.info(f"Loaded benchmark results from {result_path}")
            self.record_operation("load_benchmark_results", True, time.time() - operation_start)
            return results
            
        except Exception as e:
            self.logger.error(f"Error loading benchmark results: {e}")
            self.record_operation("load_benchmark_results", False, time.time() - operation_start if 'operation_start' in locals() else 0)
            return {}
    
    def generate_all_charts(self, results: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Generate all visualization charts for benchmark results.
        
        Args:
            results: Benchmark results to visualize, or None to load the latest
            
        Returns:
            List of paths to generated chart files
        """
        # Load results if not provided
        if results is None:
            results = self.load_benchmark_results()
        
        if not results:
            self.logger.warning("No benchmark results available for visualization")
            return []
        
        generated_files = []
        
        try:
            # Apply branding to matplotlib
            if self.include_branding:
                self._apply_branding_to_plots()
            
            # Generate charts for each category
            operation_start = time.time()
            if "storage" in results:
                storage_charts = self.visualize_storage_performance(results["storage"])
                self.record_operation("visualize_storage", True, time.time() - operation_start)
                generated_files.extend(storage_charts)
            
            operation_start = time.time()
            if "retrieval" in results:
                retrieval_charts = self.visualize_retrieval_performance(results["retrieval"])
                self.record_operation("visualize_retrieval", True, time.time() - operation_start)
                generated_files.extend(retrieval_charts)
            
            operation_start = time.time()
            if "relationships" in results:
                relationship_charts = self.visualize_relationship_operations(results["relationships"])
                self.record_operation("visualize_relationships", True, time.time() - operation_start)
                generated_files.extend(relationship_charts)
            
            operation_start = time.time()
            if "reflection" in results:
                reflection_charts = self.visualize_memory_reflection(results["reflection"])
                self.record_operation("visualize_reflection", True, time.time() - operation_start)
                generated_files.extend(reflection_charts)
            
            operation_start = time.time()
            if "hybrid_processing" in results:
                hybrid_charts = self.visualize_hybrid_processing(results["hybrid_processing"])
                self.record_operation("visualize_hybrid_processing", True, time.time() - operation_start)
                generated_files.extend(hybrid_charts)
            
            # Claude 3.7 specific - visualize hybrid thinking
            operation_start = time.time()
            if "hybrid_thinking" in results and results["hybrid_thinking"] and self.hybrid_thinking_enabled:
                hybrid_thinking_charts = self.visualize_hybrid_thinking(results["hybrid_thinking"])
                self.record_operation("visualize_hybrid_thinking", True, time.time() - operation_start)
                generated_files.extend(hybrid_thinking_charts)
            
            # Generate summary chart
            operation_start = time.time()
            summary_chart = self.create_performance_summary(results)
            if summary_chart:
                self.record_operation("create_performance_summary", True, time.time() - operation_start)
                generated_files.append(summary_chart)
            
            self.logger.info(f"Generated {len(generated_files)} visualization charts")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")
            return generated_files
    
    def _apply_branding_to_plots(self):
        """Apply TRILOGY BRAIN branding to matplotlib plots"""
        try:
            from vot1.agent_core.agent_commandments import BrandColors
            
            # Set color cycle using brand colors
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=[
                BrandColors.PRIMARY,
                BrandColors.SECONDARY, 
                BrandColors.TERTIARY,
                BrandColors.ACCENT,
                BrandColors.SUCCESS,
                BrandColors.WARNING,
                BrandColors.ERROR
            ])
            
            # Set figure style
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Other matplotlib styling
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.titlesize'] = 16
            plt.rcParams['axes.titleweight'] = 'bold'
            plt.rcParams['figure.titlesize'] = 18
            plt.rcParams['figure.figsize'] = (12, 8)
            
        except ImportError:
            self.logger.warning("Brand colors not available, using default matplotlib style")
    
    def visualize_storage_performance(self, storage_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for storage performance.
        
        Args:
            storage_results: Dictionary with storage benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. Single operation timing chart
            if "single_operation" in storage_results:
                plt.figure(figsize=(10, 6))
                
                single_op = storage_results["single_operation"]
                stats = [single_op.get("min", 0), 
                         single_op.get("median", 0), 
                         single_op.get("mean", 0), 
                         single_op.get("max", 0)]
                
                plt.bar(["Min", "Median", "Mean", "Max"], stats, color="skyblue")
                plt.title("Single Memory Storage Operation Timing")
                plt.ylabel("Time (seconds)")
                plt.grid(axis="y", linestyle="--", alpha=0.7)
                
                for i, v in enumerate(stats):
                    plt.text(i, v + 0.0005, f"{v:.4f}s", ha="center")
                
                output_path = os.path.join(self.output_dir, f"storage_single_op_{timestamp}.png")
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                plt.close()
                
                generated_files.append(output_path)
            
            # 2. Batch vs Concurrent Operations
            if "batch_operations" in storage_results and "concurrent_operations" in storage_results:
                plt.figure(figsize=(12, 7))
                
                batch_sizes = []
                batch_times = []
                concurrent_times = []
                
                for batch_size, data in storage_results["batch_operations"].items():
                    if str(batch_size) in storage_results["concurrent_operations"]:
                        batch_sizes.append(int(batch_size))
                        batch_times.append(data.get("per_memory", 0))
                        concurrent_times.append(storage_results["concurrent_operations"][str(batch_size)].get("per_memory", 0))
                
                if batch_sizes:
                    x = np.arange(len(batch_sizes))
                    width = 0.35
                    
                    plt.bar(x - width/2, batch_times, width, label="Sequential", color="coral")
                    plt.bar(x + width/2, concurrent_times, width, label="Concurrent", color="royalblue")
                    
                    plt.xlabel("Batch Size")
                    plt.ylabel("Time Per Memory (seconds)")
                    plt.title("Sequential vs Concurrent Memory Storage Performance")
                    plt.xticks(x, batch_sizes)
                    plt.legend()
                    plt.grid(axis="y", linestyle="--", alpha=0.7)
                    
                    # Add values above bars
                    for i, (batch, concurrent) in enumerate(zip(batch_times, concurrent_times)):
                        plt.text(i - width/2, batch + 0.0005, f"{batch:.4f}s", ha="center", va="bottom", fontsize=8)
                        plt.text(i + width/2, concurrent + 0.0005, f"{concurrent:.4f}s", ha="center", va="bottom", fontsize=8)
                    
                    output_path = os.path.join(self.output_dir, f"storage_batch_vs_concurrent_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing storage performance: {e}")
            plt.close()
            return generated_files
    
    def visualize_retrieval_performance(self, retrieval_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for retrieval performance.
        
        Args:
            retrieval_results: Dictionary with retrieval benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. Direct retrieval timing
            if "direct_retrieval" in retrieval_results:
                plt.figure(figsize=(10, 6))
                
                direct = retrieval_results["direct_retrieval"]
                stats = [direct.get("min", 0), 
                         direct.get("median", 0), 
                         direct.get("mean", 0), 
                         direct.get("max", 0)]
                
                plt.bar(["Min", "Median", "Mean", "Max"], stats, color="lightgreen")
                plt.title("Direct Memory Retrieval Timing")
                plt.ylabel("Time (seconds)")
                plt.grid(axis="y", linestyle="--", alpha=0.7)
                
                for i, v in enumerate(stats):
                    plt.text(i, v + 0.0005, f"{v:.4f}s", ha="center")
                
                output_path = os.path.join(self.output_dir, f"retrieval_direct_{timestamp}.png")
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                plt.close()
                
                generated_files.append(output_path)
            
            # 2. Strategy comparison
            if "strategy_comparison" in retrieval_results:
                plt.figure(figsize=(10, 6))
                
                strategies = []
                times = []
                
                for strategy, data in retrieval_results["strategy_comparison"].items():
                    strategies.append(strategy.capitalize())
                    times.append(data.get("time", 0))
                
                if strategies:
                    plt.bar(strategies, times, color=["cornflowerblue", "salmon", "mediumseagreen"])
                    plt.title("Memory Retrieval Strategy Comparison")
                    plt.ylabel("Time (seconds)")
                    plt.grid(axis="y", linestyle="--", alpha=0.7)
                    
                    for i, v in enumerate(times):
                        plt.text(i, v + 0.0005, f"{v:.4f}s", ha="center")
                    
                    output_path = os.path.join(self.output_dir, f"retrieval_strategies_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing retrieval performance: {e}")
            plt.close()
            return generated_files
    
    def visualize_relationship_operations(self, relationship_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for relationship operations.
        
        Args:
            relationship_results: Dictionary with relationship benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        if "error" in relationship_results:
            self.logger.warning(f"Skipping relationship visualization due to error: {relationship_results['error']}")
            return []
        
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Relationship operation timing
            plt.figure(figsize=(10, 6))
            
            operations = []
            times = []
            
            if "create_relationship" in relationship_results:
                operations.append("Create")
                times.append(relationship_results["create_relationship"].get("mean", 0))
            
            if "get_relationships" in relationship_results:
                operations.append("Get")
                times.append(relationship_results["get_relationships"].get("mean_time", 0))
            
            if "traverse_graph" in relationship_results:
                operations.append("Traverse")
                times.append(relationship_results["traverse_graph"].get("mean_time", 0))
            
            if operations:
                plt.bar(operations, times, color=["lightcoral", "lightskyblue", "plum"])
                plt.title("Memory Relationship Operation Timing")
                plt.ylabel("Time (seconds)")
                plt.grid(axis="y", linestyle="--", alpha=0.7)
                
                for i, v in enumerate(times):
                    plt.text(i, v + 0.0005, f"{v:.4f}s", ha="center")
                
                output_path = os.path.join(self.output_dir, f"relationship_operations_{timestamp}.png")
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                plt.close()
                
                generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing relationship operations: {e}")
            plt.close()
            return generated_files
    
    def visualize_memory_reflection(self, reflection_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for memory reflection.
        
        Args:
            reflection_results: Dictionary with reflection benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        if "error" in reflection_results:
            self.logger.warning(f"Skipping reflection visualization due to error: {reflection_results['error']}")
            return []
        
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. Reflection depth comparison
            if "reflection_depth" in reflection_results:
                plt.figure(figsize=(10, 6))
                
                depths = []
                times = []
                
                for depth, data in reflection_results["reflection_depth"].items():
                    depths.append(depth.capitalize())
                    times.append(data.get("time", 0))
                
                if depths:
                    plt.bar(depths, times, color=["lightblue", "skyblue", "steelblue"])
                    plt.title("Memory Reflection Performance by Depth")
                    plt.ylabel("Time (seconds)")
                    plt.grid(axis="y", linestyle="--", alpha=0.7)
                    
                    for i, v in enumerate(times):
                        plt.text(i, v + 0.0005, f"{v:.2f}s", ha="center")
                    
                    output_path = os.path.join(self.output_dir, f"reflection_depth_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            # 2. Memory count impact
            if "memory_count_impact" in reflection_results:
                plt.figure(figsize=(10, 6))
                
                memory_counts = []
                times = []
                per_memory_times = []
                
                for count, data in reflection_results["memory_count_impact"].items():
                    memory_counts.append(int(count))
                    times.append(data.get("time", 0))
                    per_memory_times.append(data.get("per_memory", 0))
                
                if memory_counts:
                    # Sort by memory count
                    sorted_data = sorted(zip(memory_counts, times, per_memory_times))
                    memory_counts, times, per_memory_times = zip(*sorted_data)
                    
                    fig, ax1 = plt.subplots(figsize=(10, 6))
                    
                    color = 'tab:blue'
                    ax1.set_xlabel('Memory Count')
                    ax1.set_ylabel('Total Time (s)', color=color)
                    ax1.plot(memory_counts, times, 'o-', color=color)
                    ax1.tick_params(axis='y', labelcolor=color)
                    
                    ax2 = ax1.twinx()
                    color = 'tab:red'
                    ax2.set_ylabel('Time Per Memory (s)', color=color)
                    ax2.plot(memory_counts, per_memory_times, 'o-', color=color)
                    ax2.tick_params(axis='y', labelcolor=color)
                    
                    plt.title("Impact of Memory Count on Reflection Performance")
                    fig.tight_layout()
                    
                    output_path = os.path.join(self.output_dir, f"reflection_memory_count_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing memory reflection: {e}")
            plt.close()
            return generated_files
    
    def visualize_hybrid_processing(self, hybrid_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for hybrid processing.
        
        Args:
            hybrid_results: Dictionary with hybrid processing benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. Memory limit impact on processing time
            if "memory_limit_impact" in hybrid_results:
                plt.figure(figsize=(12, 7))
                
                limits = []
                total_times = []
                retrieval_times = []
                processing_times = []
                
                for limit, data in hybrid_results["memory_limit_impact"].items():
                    limits.append(int(limit))
                    total_times.append(data.get("total_time", 0))
                    retrieval_times.append(data.get("retrieval_time", 0))
                    processing_times.append(data.get("processing_time", 0))
                
                if limits:
                    # Sort by memory limit
                    sorted_data = sorted(zip(limits, total_times, retrieval_times, processing_times))
                    limits, total_times, retrieval_times, processing_times = zip(*sorted_data)
                    
                    # Stacked bar chart
                    plt.figure(figsize=(10, 6))
                    
                    overhead_times = [total - retrieval - processing 
                                     for total, retrieval, processing 
                                     in zip(total_times, retrieval_times, processing_times)]
                    
                    p1 = plt.bar(limits, retrieval_times, color='skyblue')
                    p2 = plt.bar(limits, processing_times, bottom=retrieval_times, color='lightgreen')
                    p3 = plt.bar(limits, overhead_times, 
                                bottom=[r+p for r, p in zip(retrieval_times, processing_times)], 
                                color='salmon')
                    
                    plt.xlabel("Memory Limit")
                    plt.ylabel("Time (seconds)")
                    plt.title("Impact of Memory Limit on Hybrid Processing Performance")
                    plt.legend((p1[0], p2[0], p3[0]), 
                              ('Retrieval Time', 'Processing Time', 'Overhead Time'))
                    plt.grid(axis="y", linestyle="--", alpha=0.7)
                    
                    output_path = os.path.join(self.output_dir, f"hybrid_memory_limit_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            # 2. Retrieval strategy comparison
            if "retrieval_strategy_comparison" in hybrid_results:
                plt.figure(figsize=(12, 7))
                
                strategies = []
                total_times = []
                retrieval_times = []
                processing_times = []
                
                for strategy, data in hybrid_results["retrieval_strategy_comparison"].items():
                    strategies.append(strategy.capitalize())
                    total_times.append(data.get("total_time", 0))
                    retrieval_times.append(data.get("retrieval_time", 0))
                    processing_times.append(data.get("processing_time", 0))
                
                if strategies:
                    # Stacked bar chart
                    overhead_times = [total - retrieval - processing 
                                     for total, retrieval, processing 
                                     in zip(total_times, retrieval_times, processing_times)]
                    
                    p1 = plt.bar(strategies, retrieval_times, color='skyblue')
                    p2 = plt.bar(strategies, processing_times, bottom=retrieval_times, color='lightgreen')
                    p3 = plt.bar(strategies, overhead_times, 
                                bottom=[r+p for r, p in zip(retrieval_times, processing_times)], 
                                color='salmon')
                    
                    plt.ylabel("Time (seconds)")
                    plt.title("Hybrid Processing Performance by Retrieval Strategy")
                    plt.legend((p1[0], p2[0], p3[0]), 
                              ('Retrieval Time', 'Processing Time', 'Overhead'))
                    plt.grid(axis="y", linestyle="--", alpha=0.7)
                    
                    output_path = os.path.join(self.output_dir, f"hybrid_strategies_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing hybrid processing: {e}")
            plt.close()
            return generated_files
    
    def create_performance_summary(self, results: Dict[str, Any]) -> Optional[str]:
        """
        Create a summary chart of overall performance metrics.
        
        Args:
            results: Dictionary with benchmark results
            
        Returns:
            Path to generated chart file, or None if generation failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Extract key performance metrics
            metrics = {}
            
            if "storage" in results and "single_operation" in results["storage"]:
                metrics["Storage (Single)"] = results["storage"]["single_operation"].get("mean", 0)
            
            if "retrieval" in results and "direct_retrieval" in results["retrieval"]:
                metrics["Retrieval (Direct)"] = results["retrieval"]["direct_retrieval"].get("mean", 0)
            
            if "retrieval" in results and "search_operations" in results["retrieval"]:
                metrics["Retrieval (Search)"] = results["retrieval"]["search_operations"].get("mean_time", 0)
            
            if "relationships" in results and "create_relationship" in results["relationships"]:
                metrics["Relationship"] = results["relationships"]["create_relationship"].get("mean", 0)
            
            if "reflection" in results and "reflection_depth" in results["reflection"]:
                if "standard" in results["reflection"]["reflection_depth"]:
                    metrics["Reflection"] = results["reflection"]["reflection_depth"]["standard"].get("time", 0)
            
            if "hybrid_processing" in results and "retrieval_strategy_comparison" in results["hybrid_processing"]:
                if "hybrid" in results["hybrid_processing"]["retrieval_strategy_comparison"]:
                    metrics["Hybrid Processing"] = results["hybrid_processing"]["retrieval_strategy_comparison"]["hybrid"].get("total_time", 0)
            
            if not metrics:
                return None
            
            # Create summary chart
            plt.figure(figsize=(12, 7))
            
            operations = list(metrics.keys())
            times = list(metrics.values())
            colors = ['skyblue', 'lightgreen', 'salmon', 'lightcoral', 'plum', 'cornflowerblue']
            
            plt.bar(operations, times, color=colors[:len(operations)])
            plt.title("TRILOGY BRAIN Memory System Performance Summary")
            plt.ylabel("Time (seconds)")
            plt.xticks(rotation=30, ha='right')
            plt.grid(axis="y", linestyle="--", alpha=0.7)
            plt.tight_layout()
            
            for i, v in enumerate(times):
                plt.text(i, v + 0.0005, f"{v:.4f}s", ha="center")
            
            output_path = os.path.join(self.output_dir, f"performance_summary_{timestamp}.png")
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error creating performance summary: {e}")
            plt.close()
            return None
            
    def generate_html_report(self, chart_files: List[str], results: Dict[str, Any]) -> str:
        """
        Generate an HTML report with charts and analysis.
        
        Args:
            chart_files: List of paths to chart files
            results: Dictionary with benchmark results
            
        Returns:
            Path to the generated HTML report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"benchmark_report_{timestamp}.html"
        report_path = os.path.join(self.output_dir, report_filename)
        
        try:
            # Get branding colors
            try:
                from vot1.agent_core.agent_commandments import BrandColors, get_agent_commandments, AgentType
                colors = BrandColors
                commandments = get_agent_commandments(AgentType.VISUALIZATION)
            except ImportError:
                # Default colors if branding not available
                colors = type('obj', (object,), {
                    'PRIMARY': "#3A1078",
                    'SECONDARY': "#4E31AA",
                    'TERTIARY': "#2F58CD",
                    'ACCENT': "#3795BD",
                    'NEUTRAL_DARK': "#2C3333",
                    'NEUTRAL_MEDIUM': "#596263",
                    'NEUTRAL_LIGHT': "#E8F9FD",
                    'SUCCESS': "#59CE8F",
                    'WARNING': "#E8AB5C",
                    'ERROR': "#E64848",
                    'INFO': "#3795BD"
                })
                commandments = []
            
            # Create enhanced HTML template with branding
            html = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "    <title>TRILOGY BRAIN Memory Benchmark Report</title>",
                "    <meta charset='UTF-8'>",
                "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                "    <style>",
                f"        :root {{",
                f"            --primary: {colors.PRIMARY};",
                f"            --secondary: {colors.SECONDARY};",
                f"            --tertiary: {colors.TERTIARY};",
                f"            --accent: {colors.ACCENT};",
                f"            --neutral-dark: {colors.NEUTRAL_DARK};",
                f"            --neutral-medium: {colors.NEUTRAL_MEDIUM};",
                f"            --neutral-light: {colors.NEUTRAL_LIGHT};",
                f"            --success: {colors.SUCCESS};",
                f"            --warning: {colors.WARNING};",
                f"            --error: {colors.ERROR};",
                f"            --info: {colors.INFO};",
                "        }",
                "        body { font-family: 'Roboto', 'Segoe UI', sans-serif; margin: 0; padding: 0; color: var(--neutral-dark); line-height: 1.6; }",
                "        .container { width: 90%; max-width: 1200px; margin: 0 auto; padding: 20px; }",
                "        header { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 2rem 0; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
                "        header .container { display: flex; justify-content: space-between; align-items: center; }",
                "        .header-logo { font-size: 2.5rem; font-weight: bold; margin: 0; }",
                "        .header-subtitle { opacity: 0.9; margin-top: 0.5rem; }",
                "        h1 { color: var(--primary); margin-top: 2rem; font-size: 2.2rem; }",
                "        h2 { color: var(--secondary); margin-top: 2rem; font-size: 1.8rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }",
                "        h3 { color: var(--tertiary); margin-top: 1.5rem; font-size: 1.5rem; }",
                "        .chart-container { margin: 2rem 0; background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }",
                "        .chart { width: 100%; max-width: 100%; height: auto; border-radius: 4px; }",
                "        .summary-card { background: var(--neutral-light); padding: 1.5rem; border-radius: 8px; margin: 2rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }",
                "        .summary-card h2 { margin-top: 0; color: var(--primary); }",
                "        .metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; margin: 1.5rem 0; }",
                "        .metric-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }",
                "        .metric-value { font-size: 2rem; font-weight: bold; color: var(--primary); margin: 0.5rem 0; }",
                "        .metric-label { font-size: 1rem; color: var(--neutral-medium); }",
                "        table { border-collapse: collapse; width: 100%; margin: 1.5rem 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }",
                "        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }",
                "        th { background-color: var(--neutral-light); color: var(--primary); font-weight: 600; }",
                "        tr:nth-child(even) { background-color: #f9f9f9; }",
                "        .recommendations { background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 5px solid var(--accent); }",
                "        .commandments { background: linear-gradient(135deg, var(--neutral-light), #f0f4f8); padding: 1.5rem; border-radius: 8px; margin: 2rem 0; border-left: 5px solid var(--tertiary); }",
                "        .commandment-item { margin-bottom: 0.8rem; }",
                "        footer { background: var(--neutral-dark); color: white; padding: 2rem 0; margin-top: 3rem; text-align: center; }",
                "        footer a { color: var(--accent); text-decoration: none; }",
                "        @media (max-width: 768px) {",
                "            header .container { flex-direction: column; text-align: center; }",
                "            .metric-grid { grid-template-columns: 1fr; }",
                "        }",
                "    </style>",
                "</head>",
                "<body>",
                "    <header>",
                "        <div class='container'>",
                "            <div>",
                "                <h1 class='header-logo'>TRILOGY BRAIN</h1>",
                "                <p class='header-subtitle'>Memory Benchmark Report</p>",
                "            </div>",
                f"            <div>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>",
                "        </div>",
                "    </header>",
                "    <div class='container'>"
            ]
            
            # Add summary section with metrics
            html.extend([
                "        <div class='summary-card'>",
                "            <h2>Benchmark Summary</h2>",
                "            <div class='metric-grid'>",
                f"                <div class='metric-card'>",
                f"                    <div class='metric-label'>Total Memories</div>",
                f"                    <div class='metric-value'>{results.get('memory_count', 'N/A')}</div>",
                f"                </div>",
                f"                <div class='metric-card'>",
                f"                    <div class='metric-label'>Total Runtime</div>",
                f"                    <div class='metric-value'>{results.get('total_time', 0):.2f}s</div>",
                f"                </div>",
                f"                <div class='metric-card'>",
                f"                    <div class='metric-label'>Model</div>",
                f"                    <div class='metric-value'>{results.get('model_version', 'Claude 3.7')}</div>",
                f"                </div>"
            ])
            
            # Add agent info if available
            if "agent_info" in results:
                agent_info = results["agent_info"]
                html.extend([
                    f"                <div class='metric-card'>",
                    f"                    <div class='metric-label'>Agent Health</div>",
                    f"                    <div class='metric-value'>{agent_info.get('health', 1.0) * 100:.1f}%</div>",
                    f"                </div>"
                ])
            
            html.append("            </div>")
            html.append("        </div>")
            
            # Add chart sections
            for chart_file in chart_files:
                if not os.path.exists(chart_file):
                    continue
                    
                # Get relative path for HTML
                rel_path = os.path.relpath(chart_file, self.output_dir)
                chart_name = os.path.basename(chart_file).replace('.png', '').replace('_', ' ').title()
                
                html.extend([
                    f"        <div class='chart-container'>",
                    f"            <h2>{chart_name}</h2>",
                    f"            <img class='chart' src='{rel_path}' alt='{chart_name}'>",
                    f"        </div>"
                ])
            
            # Add recommendations section
            html.extend([
                "        <div class='recommendations'>",
                "            <h2>Performance Recommendations</h2>",
                "            <ul>"
            ])
            
            # Generate recommendations based on results
            recommendations = []
            
            # Storage recommendations
            if "storage" in results:
                storage = results["storage"]
                if "concurrent_operations" in storage and "batch_operations" in storage:
                    for batch_size in storage["concurrent_operations"]:
                        if batch_size in storage["batch_operations"]:
                            concurrent = storage["concurrent_operations"][batch_size].get("per_memory", 0)
                            sequential = storage["batch_operations"][batch_size].get("per_memory", 0)
                            
                            if concurrent < sequential * 0.8:
                                recommendations.append(f"Use concurrent processing for batch storage operations (approximately {(1 - concurrent/sequential) * 100:.1f}% faster)")
                            else:
                                recommendations.append("Sequential processing is efficient for memory storage operations")
            
            # Retrieval recommendations
            if "retrieval" in results:
                retrieval = results["retrieval"]
                if "strategy_comparison" in retrieval:
                    strategies = retrieval["strategy_comparison"]
                    if "semantic" in strategies and "hybrid" in strategies and "temporal" in strategies:
                        semantic_time = strategies["semantic"].get("time", 0)
                        hybrid_time = strategies["hybrid"].get("time", 0)
                        temporal_time = strategies["temporal"].get("time", 0)
                        
                        fastest = min((semantic_time, "semantic"), (hybrid_time, "hybrid"), (temporal_time, "temporal"), key=lambda x: x[0])
                        recommendations.append(f"The '{fastest[1]}' retrieval strategy is most efficient ({fastest[0]:.4f}s)")
            
            # Hybrid processing recommendations
            if "hybrid_processing" in results:
                hybrid = results["hybrid_processing"]
                if "memory_limit_impact" in hybrid:
                    limits = hybrid["memory_limit_impact"]
                    
                    # Calculate efficiency (processing time per memory)
                    efficiencies = {}
                    for limit, data in limits.items():
                        memory_count = data.get("memory_count", 0)
                        if memory_count > 0:
                            efficiencies[limit] = data.get("total_time", 0) / memory_count
                    
                    if efficiencies:
                        optimal_limit = min(efficiencies.items(), key=lambda x: x[1])
                        recommendations.append(f"Optimal memory limit for hybrid processing is around {optimal_limit[0]} memories")
            
            # Hybrid thinking recommendations (Claude 3.7 specific)
            if "hybrid_thinking" in results and results["hybrid_thinking"]:
                hybrid_thinking = results["hybrid_thinking"]
                
                if "thinking_token_limits" in hybrid_thinking:
                    limits = hybrid_thinking["thinking_token_limits"]
                    
                    # Find optimal token limit based on tokens per second
                    efficiencies = {
                        limit: data.get("tokens_per_second", 0) 
                        for limit, data in limits.items()
                    }
                    
                    if efficiencies:
                        optimal_limit = max(efficiencies.items(), key=lambda x: x[1])
                        recommendations.append(f"Optimal thinking token limit is around {optimal_limit[0]} tokens for efficiency ({optimal_limit[1]:.2f} tokens/s)")
                
                if "complexity_levels" in hybrid_thinking:
                    complexities = hybrid_thinking["complexity_levels"]
                    
                    # Compare thinking vs generation time ratios
                    if "high" in complexities and "low" in complexities:
                        high_thinking_ratio = complexities["high"].get("thinking_time", 0) / (complexities["high"].get("total_time", 1) or 1)
                        low_thinking_ratio = complexities["low"].get("thinking_time", 0) / (complexities["low"].get("total_time", 1) or 1)
                        
                        if high_thinking_ratio > low_thinking_ratio * 1.5:
                            recommendations.append(f"Complex queries benefit significantly more from hybrid thinking (thinking ratio: {high_thinking_ratio:.2f} vs {low_thinking_ratio:.2f})")
                
                if "thinking_performance" in hybrid_thinking:
                    approaches = hybrid_thinking["thinking_performance"]
                    
                    if "direct_integration" in approaches and "iterative_integration" in approaches:
                        direct_time = approaches["direct_integration"].get("total_time", 0)
                        iterative_time = approaches["iterative_integration"].get("total_time", 0)
                        
                        if direct_time < iterative_time * 0.8:
                            recommendations.append(f"Direct memory-thinking integration is more efficient ({(1 - direct_time/iterative_time) * 100:.1f}% faster)")
                        else:
                            recommendations.append(f"Iterative memory-thinking integration provides better results despite {(iterative_time/direct_time - 1) * 100:.1f}% longer processing time")
            
            # Add recommendations to HTML
            if recommendations:
                for recommendation in recommendations:
                    html.append(f"                <li>{recommendation}</li>")
            else:
                html.append(f"                <li>No specific recommendations available from the current benchmark data</li>")
            
            html.append("            </ul>")
            html.append("        </div>")
            
            # Add agent commandments if available
            if commandments:
                html.extend([
                    "        <div class='commandments'>",
                    "            <h2>Visualization Agent Commandments</h2>",
                    "            <ol>"
                ])
                
                for commandment in commandments:
                    html.append(f"                <li class='commandment-item'>{commandment}</li>")
                
                html.extend([
                    "            </ol>",
                    "        </div>"
                ])
            
            # Close HTML
            html.extend([
                "    </div>",
                "    <footer>",
                "        <div class='container'>",
                f"            <p>TRILOGY BRAIN Memory Benchmark Report &copy; {datetime.now().year} • Generated by DataViz Agent</p>",
                "        </div>",
                "    </footer>",
                "</body>",
                "</html>"
            ])
            
            # Write HTML to file
            with open(report_path, "w") as f:
                f.write("\n".join(html))
            
            self.logger.info(f"Generated HTML report: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return ""
    
    def visualize_hybrid_thinking(self, hybrid_thinking_results: Dict[str, Any]) -> List[str]:
        """
        Generate visualizations for Claude 3.7's hybrid thinking performance.
        
        Args:
            hybrid_thinking_results: Dictionary with hybrid thinking benchmark results
            
        Returns:
            List of paths to generated chart files
        """
        if not self.hybrid_thinking_enabled or not hybrid_thinking_results:
            return []
        
        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 1. Token limit impact chart
            if "thinking_token_limits" in hybrid_thinking_results:
                plt.figure(figsize=(12, 7))
                
                limits = []
                total_times = []
                thinking_tokens = []
                output_tokens = []
                token_rates = []
                
                for limit, data in hybrid_thinking_results["thinking_token_limits"].items():
                    limits.append(int(limit))
                    total_times.append(data.get("total_time", 0))
                    thinking_tokens.append(data.get("thinking_tokens", 0))
                    output_tokens.append(data.get("output_tokens", 0))
                    token_rates.append(data.get("tokens_per_second", 0))
                
                if limits:
                    # Sort by token limit
                    sorted_indices = sorted(range(len(limits)), key=lambda i: limits[i])
                    limits = [limits[i] for i in sorted_indices]
                    total_times = [total_times[i] for i in sorted_indices]
                    thinking_tokens = [thinking_tokens[i] for i in sorted_indices]
                    output_tokens = [output_tokens[i] for i in sorted_indices]
                    token_rates = [token_rates[i] for i in sorted_indices]
                    
                    # Create figure with two y-axes
                    fig, ax1 = plt.subplots(figsize=(12, 7))
                    
                    # Plot stacked bar chart for tokens
                    width = 0.4
                    ax1.bar(np.array(limits) - width/2, thinking_tokens, width, label='Thinking Tokens', color='#3A1078')
                    ax1.bar(np.array(limits) - width/2, output_tokens, width, bottom=thinking_tokens, 
                           label='Output Tokens', color='#4E31AA')
                    
                    ax1.set_xlabel('Thinking Token Limit')
                    ax1.set_ylabel('Token Count')
                    ax1.set_title('Impact of Thinking Token Limit on Claude 3.7 Performance')
                    ax1.tick_params(axis='y')
                    ax1.legend(loc='upper left')
                    
                    # Secondary y-axis for time and rate
                    ax2 = ax1.twinx()
                    ax2.plot(limits, total_times, 'o-', color='#E64848', label='Processing Time')
                    ax2.set_ylabel('Time (seconds)', color='#E64848')
                    ax2.tick_params(axis='y', labelcolor='#E64848')
                    
                    # Third y-axis for token rate
                    ax3 = ax1.twinx()
                    ax3.spines["right"].set_position(("axes", 1.1))
                    ax3.plot(limits, token_rates, 's--', color='#59CE8F', label='Tokens/Second')
                    ax3.set_ylabel('Tokens/Second', color='#59CE8F')
                    ax3.tick_params(axis='y', labelcolor='#59CE8F')
                    
                    # Combine legends
                    lines1, labels1 = ax1.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    lines3, labels3 = ax3.get_legend_handles_labels()
                    ax3.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc='upper right')
                    
                    fig.tight_layout()
                    
                    output_path = os.path.join(self.output_dir, f"hybrid_thinking_token_limits_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            # 2. Complexity level chart
            if "complexity_levels" in hybrid_thinking_results:
                plt.figure(figsize=(12, 7))
                
                levels = []
                thinking_times = []
                generation_times = []
                thinking_tokens = []
                output_tokens = []
                
                for level, data in hybrid_thinking_results["complexity_levels"].items():
                    levels.append(level.capitalize())
                    thinking_times.append(data.get("thinking_time", 0))
                    generation_times.append(data.get("generation_time", 0))
                    thinking_tokens.append(data.get("thinking_tokens", 0))
                    output_tokens.append(data.get("output_tokens", 0))
                
                if levels:
                    # Create figure with two subplots
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
                    
                    # Left plot: Stacked bar chart for processing time
                    width = 0.5
                    ax1.bar(levels, thinking_times, width, label='Thinking Time', color='#3A1078')
                    ax1.bar(levels, generation_times, width, bottom=thinking_times, 
                           label='Generation Time', color='#4E31AA')
                    
                    ax1.set_ylabel('Time (seconds)')
                    ax1.set_title('Processing Time by Complexity Level')
                    ax1.legend()
                    
                    # Right plot: Stacked bar chart for tokens
                    ax2.bar(levels, thinking_tokens, width, label='Thinking Tokens', color='#2F58CD')
                    ax2.bar(levels, output_tokens, width, bottom=thinking_tokens, 
                           label='Output Tokens', color='#3795BD')
                    
                    ax2.set_ylabel('Token Count')
                    ax2.set_title('Token Usage by Complexity Level')
                    ax2.legend()
                    
                    fig.suptitle('Impact of Task Complexity on Claude 3.7 Performance', fontsize=16)
                    fig.tight_layout(rect=[0, 0, 1, 0.95])
                    
                    output_path = os.path.join(self.output_dir, f"hybrid_thinking_complexity_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            # 3. Memory-thinking integration approaches
            if "thinking_performance" in hybrid_thinking_results:
                plt.figure(figsize=(12, 7))
                
                approaches = []
                thinking_tokens = []
                output_tokens = []
                total_times = []
                
                for approach, data in hybrid_thinking_results["thinking_performance"].items():
                    approaches.append(approach.replace('_', ' ').title())
                    thinking_tokens.append(data.get("thinking_tokens", 0))
                    output_tokens.append(data.get("output_tokens", 0))
                    total_times.append(data.get("total_time", 0))
                
                if approaches:
                    # Create figure with two subplots
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
                    
                    # Left plot: Stacked bar chart for tokens
                    width = 0.5
                    ax1.bar(approaches, thinking_tokens, width, label='Thinking Tokens', color='#3A1078')
                    ax1.bar(approaches, output_tokens, width, bottom=thinking_tokens, 
                           label='Output Tokens', color='#4E31AA')
                    
                    ax1.set_ylabel('Token Count')
                    ax1.set_title('Token Usage by Integration Approach')
                    ax1.legend()
                    
                    # Right plot: Bar chart for processing time
                    ax2.bar(approaches, total_times, width, color='#E64848')
                    
                    ax2.set_ylabel('Time (seconds)')
                    ax2.set_title('Processing Time by Integration Approach')
                    
                    # Add values above bars
                    for i, v in enumerate(total_times):
                        ax2.text(i, v + 0.1, f"{v:.2f}s", ha='center')
                    
                    fig.suptitle('Memory-Thinking Integration Approaches', fontsize=16)
                    fig.tight_layout(rect=[0, 0, 1, 0.95])
                    
                    output_path = os.path.join(self.output_dir, f"hybrid_thinking_integration_{timestamp}.png")
                    plt.savefig(output_path, dpi=300, bbox_inches="tight")
                    plt.close()
                    
                    generated_files.append(output_path)
            
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error visualizing hybrid thinking: {e}")
            plt.close()
            return generated_files 