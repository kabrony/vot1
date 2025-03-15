"""
Memory Benchmarking for TRILOGY BRAIN

This module provides benchmarking tools for evaluating memory system performance.
It tests various aspects of memory operations and provides detailed performance metrics.
"""

import os
import json
import time
import asyncio
import random
import uuid
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    # Try absolute imports first (for installed package)
    from vot1.composio.memory_bridge import ComposioMemoryBridge
    from vot1.composio.client import ComposioClient
    from vot1.memory import MemoryManager
    from vot1.utils.logging import get_logger
    from vot1.agent_core.base_agent import BaseAgent
    from vot1.agent_core.agent_commandments import AgentType
except ImportError:
    # Fall back to relative imports (for development)
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.composio.client import ComposioClient
    from src.vot1.memory import MemoryManager
    from src.vot1.utils.logging import get_logger
    from src.vot1.agent_core.base_agent import BaseAgent
    from src.vot1.agent_core.agent_commandments import AgentType

# Configure logging - now handled by BaseAgent
# logger = get_logger(__name__)

class MemoryBenchmark(BaseAgent):
    """
    Benchmark for evaluating TRILOGY BRAIN memory performance.
    
    This class provides tools for measuring:
    1. Memory storage performance
    2. Memory retrieval performance
    3. Memory relationship operations
    4. Memory reflection performance
    5. Memory consolidation performance
    6. Hybrid thinking capabilities
    """
    
    def __init__(
        self,
        memory_bridge: Optional[ComposioMemoryBridge] = None,
        composio_client: Optional[ComposioClient] = None,
        memory_manager: Optional[MemoryManager] = None,
        memory_path: str = "memory/benchmark",
        benchmark_data_path: str = "data/benchmark",
        clean_after_benchmark: bool = True,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the memory benchmark.
        
        Args:
            memory_bridge: ComposioMemoryBridge instance to benchmark
            composio_client: ComposioClient instance
            memory_manager: MemoryManager instance
            memory_path: Path to memory storage for benchmark
            benchmark_data_path: Path to store benchmark data
            clean_after_benchmark: Whether to clean up after benchmarking
            agent_id: Unique identifier for this agent instance
            config: Configuration dictionary
        """
        # Initialize BaseAgent
        super().__init__(
            agent_type=AgentType.PERFORMANCE,
            agent_id=agent_id,
            config=config or {}
        )
        
        # Create benchmark directories
        os.makedirs(memory_path, exist_ok=True)
        os.makedirs(benchmark_data_path, exist_ok=True)
        
        # Initialize components
        self.memory_bridge = memory_bridge or ComposioMemoryBridge(memory_path=memory_path)
        self.composio_client = composio_client or self.memory_bridge.composio_client
        self.memory_manager = memory_manager or self.memory_bridge.memory_manager
        
        # Configuration
        self.memory_path = memory_path
        self.benchmark_data_path = benchmark_data_path
        self.clean_after_benchmark = clean_after_benchmark
        
        # Benchmark data
        self._test_memories: List[Dict[str, Any]] = []
        self._benchmark_results: Dict[str, Any] = {}
        
        # Claude 3.7 Sonnet specific capabilities
        self.hybrid_thinking_enabled = True
        self.max_thinking_tokens = 15000
        self.model_version = "claude-3-7-sonnet"
        
        self.logger.info("Memory Benchmark initialized")
    
    async def process(self, memory_count: int = 100, include_hybrid_thinking: bool = True) -> Dict[str, Any]:
        """
        Process a benchmark request (implementation of abstract method from BaseAgent).
        
        Args:
            memory_count: Number of test memories to generate
            include_hybrid_thinking: Whether to include hybrid thinking benchmarks
            
        Returns:
            Dictionary with benchmark results
        """
        return await self.run_full_benchmark(memory_count, include_hybrid_thinking)
    
    async def run_full_benchmark(self, memory_count: int = 100, include_hybrid_thinking: bool = True) -> Dict[str, Any]:
        """
        Run a comprehensive memory benchmark.
        
        Args:
            memory_count: Number of test memories to generate
            include_hybrid_thinking: Whether to include hybrid thinking benchmarks
            
        Returns:
            Dictionary with benchmark results
        """
        self.logger.info(f"Starting comprehensive memory benchmark with {memory_count} memories")
        start_time = time.time()
        
        try:
            # Activate the agent
            self.activate()
            
            # Phase 1: Generate test data
            self.logger.info(f"Generating {memory_count} test memories")
            operation_start = time.time()
            await self._generate_test_data(memory_count)
            self.record_operation("generate_test_data", True, time.time() - operation_start)
            
            # Phase 2: Benchmark memory storage
            operation_start = time.time()
            storage_results = await self.benchmark_memory_storage()
            self.record_operation("benchmark_memory_storage", True, time.time() - operation_start)
            
            # Phase 3: Benchmark memory retrieval
            operation_start = time.time()
            retrieval_results = await self.benchmark_memory_retrieval()
            self.record_operation("benchmark_memory_retrieval", True, time.time() - operation_start)
            
            # Phase 4: Benchmark relationship operations
            operation_start = time.time()
            relationship_results = await self.benchmark_relationship_operations()
            self.record_operation("benchmark_relationship_operations", True, time.time() - operation_start)
            
            # Phase 5: Benchmark reflection
            operation_start = time.time()
            reflection_results = await self.benchmark_memory_reflection()
            self.record_operation("benchmark_memory_reflection", True, time.time() - operation_start)
            
            # Phase 6: Benchmark hybrid processing
            operation_start = time.time()
            hybrid_results = await self.benchmark_hybrid_processing()
            self.record_operation("benchmark_hybrid_processing", True, time.time() - operation_start)
            
            # Phase 7: Benchmark hybrid thinking (Claude 3.7 specific)
            hybrid_thinking_results = {}
            if include_hybrid_thinking and self.hybrid_thinking_enabled:
                operation_start = time.time()
                hybrid_thinking_results = await self.benchmark_hybrid_thinking()
                self.record_operation("benchmark_hybrid_thinking", True, time.time() - operation_start)
            
            # Compile results
            self._benchmark_results = {
                "storage": storage_results,
                "retrieval": retrieval_results,
                "relationships": relationship_results,
                "reflection": reflection_results,
                "hybrid_processing": hybrid_results,
                "hybrid_thinking": hybrid_thinking_results if include_hybrid_thinking else {},
                "memory_count": memory_count,
                "total_time": time.time() - start_time,
                "timestamp": time.time(),
                "model_version": self.model_version,
                "agent_info": self.get_info()
            }
            
            # Save results
            operation_start = time.time()
            self._save_benchmark_results()
            self.record_operation("save_benchmark_results", True, time.time() - operation_start)
            
            # Clean up if needed
            if self.clean_after_benchmark:
                operation_start = time.time()
                await self._cleanup()
                self.record_operation("cleanup", True, time.time() - operation_start)
            
            # Deactivate the agent
            self.deactivate()
            
            benchmark_time = time.time() - start_time
            self.logger.info(f"Comprehensive benchmark completed in {benchmark_time:.2f}s")
            
            # Format the benchmark summary with branding
            summary = f"Completed benchmark with {memory_count} memories in {benchmark_time:.2f}s"
            self.logger.info(self.format_response(summary, include_header=True))
            
            return self._benchmark_results
            
        except Exception as e:
            self.logger.error(f"Error during benchmark: {e}")
            self.record_operation("run_full_benchmark", False, time.time() - start_time)
            if self.clean_after_benchmark:
                await self._cleanup()
            self.deactivate()
            raise
    
    async def benchmark_memory_storage(self, batch_sizes: List[int] = [1, 10, 50, 100]) -> Dict[str, Any]:
        """
        Benchmark memory storage performance.
        
        Args:
            batch_sizes: List of batch sizes to test
            
        Returns:
            Dictionary with storage benchmark results
        """
        self.logger.info("Starting memory storage benchmark")
        results = {
            "single_operation": {},
            "batch_operations": {},
            "concurrent_operations": {}
        }
        
        # Ensure we have test data
        if not self._test_memories:
            await self._generate_test_data(max(batch_sizes) * 2)
        
        # Test single memory storage
        single_times = []
        for _ in range(10):  # 10 trials
            memory = self._generate_memory()
            start_time = time.time()
            memory_id = await self.memory_manager.store_memory(
                content=memory["content"],
                memory_type=memory["type"],
                metadata=memory.get("metadata", {})
            )
            elapsed = time.time() - start_time
            single_times.append(elapsed)
        
        results["single_operation"] = {
            "min": min(single_times),
            "max": max(single_times),
            "mean": statistics.mean(single_times),
            "median": statistics.median(single_times)
        }
        
        # Test batch operations
        for batch_size in batch_sizes:
            batch_times = []
            for _ in range(3):  # 3 trials per batch size
                memories = [self._generate_memory() for _ in range(batch_size)]
                
                start_time = time.time()
                for memory in memories:
                    await self.memory_manager.store_memory(
                        content=memory["content"],
                        memory_type=memory["type"],
                        metadata=memory.get("metadata", {})
                    )
                elapsed = time.time() - start_time
                
                batch_times.append(elapsed)
            
            results["batch_operations"][batch_size] = {
                "total_time": statistics.mean(batch_times),
                "per_memory": statistics.mean(batch_times) / batch_size
            }
        
        # Test concurrent operations
        for batch_size in batch_sizes:
            if batch_size < 5:
                continue  # Skip small batches for concurrent test
                
            memories = [self._generate_memory() for _ in range(batch_size)]
            
            async def store_memory(memory):
                return await self.memory_manager.store_memory(
                    content=memory["content"],
                    memory_type=memory["type"],
                    metadata=memory.get("metadata", {})
                )
            
            start_time = time.time()
            tasks = [store_memory(memory) for memory in memories]
            await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            results["concurrent_operations"][batch_size] = {
                "total_time": elapsed,
                "per_memory": elapsed / batch_size
            }
        
        self.logger.info("Memory storage benchmark completed")
        return results
    
    async def benchmark_memory_retrieval(self) -> Dict[str, Any]:
        """
        Benchmark memory retrieval performance.
        
        Returns:
            Dictionary with retrieval benchmark results
        """
        self.logger.info("Starting memory retrieval benchmark")
        results = {
            "direct_retrieval": {},
            "search_operations": {},
            "strategy_comparison": {}
        }
        
        # Ensure we have test data
        if not self._test_memories:
            await self._generate_test_data(100)
        
        # Test direct memory retrieval by ID
        memory_ids = [memory.get("id") for memory in self._test_memories if memory.get("id")]
        if memory_ids:
            direct_times = []
            for _ in range(10):  # 10 trials
                memory_id = random.choice(memory_ids)
                
                start_time = time.time()
                memory = await self.memory_manager.get_memory(memory_id)
                elapsed = time.time() - start_time
                
                direct_times.append(elapsed)
            
            results["direct_retrieval"] = {
                "min": min(direct_times),
                "max": max(direct_times),
                "mean": statistics.mean(direct_times),
                "median": statistics.median(direct_times)
            }
        
        # Test search operations
        search_queries = [
            "TRILOGY BRAIN architecture",
            "memory consolidation",
            "neural network",
            "blockchain technology",
            "security protocol"
        ]
        
        search_times = []
        for query in search_queries:
            start_time = time.time()
            memories = await self.memory_manager.search_memories(
                query=query,
                limit=10
            )
            elapsed = time.time() - start_time
            
            search_times.append({
                "query": query,
                "time": elapsed,
                "result_count": len(memories)
            })
        
        results["search_operations"] = {
            "queries": search_times,
            "mean_time": statistics.mean([s["time"] for s in search_times])
        }
        
        # Test different retrieval strategies
        strategies = ["semantic", "temporal", "hybrid"]
        strategy_times = {}
        
        for strategy in strategies:
            start_time = time.time()
            if strategy == "semantic":
                memories = await self.memory_manager.retrieve_memories(
                    query="TRILOGY BRAIN",
                    limit=10
                )
            elif strategy == "temporal":
                memories = await self.memory_manager.retrieve_recent_memories(
                    limit=10
                )
            else:  # hybrid
                response = await self.memory_bridge.process_with_memory(
                    prompt="Tell me about TRILOGY BRAIN",
                    memory_limit=10,
                    memory_retrieval_strategy="hybrid",
                    store_response=False
                )
                memories = []
            
            elapsed = time.time() - start_time
            
            strategy_times[strategy] = {
                "time": elapsed,
                "memory_count": len(memories) if strategy != "hybrid" else "N/A"
            }
        
        results["strategy_comparison"] = strategy_times
        
        self.logger.info("Memory retrieval benchmark completed")
        return results
    
    async def benchmark_relationship_operations(self) -> Dict[str, Any]:
        """
        Benchmark memory relationship operations.
        
        Returns:
            Dictionary with relationship benchmark results
        """
        if not self.memory_bridge.enhanced_memory:
            self.logger.warning("Enhanced memory not enabled, skipping relationship benchmark")
            return {"error": "Enhanced memory not enabled"}
        
        self.logger.info("Starting memory relationship benchmark")
        results = {
            "create_relationship": {},
            "get_relationships": {},
            "traverse_graph": {}
        }
        
        # Ensure we have test data
        if not self._test_memories:
            await self._generate_test_data(50)
        
        # Get memory IDs
        memory_ids = [memory.get("id") for memory in self._test_memories if memory.get("id")]
        if len(memory_ids) < 10:
            self.logger.warning("Not enough memories for relationship benchmark")
            return {"error": "Not enough memories"}
        
        # Test creating relationships
        create_times = []
        for _ in range(20):  # 20 trials
            source_id = random.choice(memory_ids)
            target_id = random.choice(memory_ids)
            
            if source_id == target_id:
                continue
                
            relationship_type = random.choice([
                "related_to", "precedes", "follows", "references", "contradicts"
            ])
            strength = random.uniform(0.5, 1.0)
            
            start_time = time.time()
            await self.memory_manager.create_relationship(
                source_id, target_id, relationship_type, strength
            )
            elapsed = time.time() - start_time
            
            create_times.append(elapsed)
        
        if create_times:
            results["create_relationship"] = {
                "min": min(create_times),
                "max": max(create_times),
                "mean": statistics.mean(create_times),
                "median": statistics.median(create_times)
            }
        
        # Test getting relationships
        get_times = []
        for _ in range(10):  # 10 trials
            memory_id = random.choice(memory_ids)
            
            start_time = time.time()
            relationships = await self.memory_manager.get_memory_relationships(memory_id)
            elapsed = time.time() - start_time
            
            get_times.append({
                "time": elapsed,
                "relationship_count": len(relationships)
            })
        
        results["get_relationships"] = {
            "times": get_times,
            "mean_time": statistics.mean([g["time"] for g in get_times]) if get_times else 0
        }
        
        # Test graph traversal
        traversal_times = []
        for _ in range(5):  # 5 trials
            start_id = random.choice(memory_ids)
            
            for depth in [1, 2, 3]:
                start_time = time.time()
                graph = await self.memory_manager.build_memory_graph(
                    [start_id],
                    depth=depth
                )
                elapsed = time.time() - start_time
                
                traversal_times.append({
                    "depth": depth,
                    "time": elapsed,
                    "node_count": len(graph.get("nodes", [])),
                    "edge_count": len(graph.get("edges", []))
                })
        
        results["traverse_graph"] = {
            "times": traversal_times,
            "mean_time": statistics.mean([t["time"] for t in traversal_times]) if traversal_times else 0
        }
        
        self.logger.info("Memory relationship benchmark completed")
        return results
    
    async def benchmark_memory_reflection(self) -> Dict[str, Any]:
        """
        Benchmark memory reflection performance.
        
        Returns:
            Dictionary with reflection benchmark results
        """
        self.logger.info("Starting memory reflection benchmark")
        results = {
            "reflection_depth": {},
            "memory_count_impact": {}
        }
        
        # Ensure we have test data
        if not self._test_memories:
            await self._generate_test_data(50)
        
        # Get memory IDs
        memory_ids = [memory.get("id") for memory in self._test_memories if memory.get("id")]
        if len(memory_ids) < 10:
            self.logger.warning("Not enough memories for reflection benchmark")
            return {"error": "Not enough memories"}
        
        # Test different reflection depths
        depths = ["brief", "standard", "deep"]
        depth_times = {}
        
        for depth in depths:
            # Sample 10 random memories
            sample_ids = random.sample(memory_ids, min(10, len(memory_ids)))
            
            start_time = time.time()
            reflection = await self.memory_bridge.advanced_memory_reflection(
                memory_ids=sample_ids,
                reflection_depth=depth,
                include_thinking=True
            )
            elapsed = time.time() - start_time
            
            depth_times[depth] = {
                "time": elapsed,
                "success": reflection.get("success", False),
                "memory_count": len(sample_ids)
            }
        
        results["reflection_depth"] = depth_times
        
        # Test impact of memory count on performance
        counts = [5, 10, 15, 20]
        count_times = {}
        
        for count in counts:
            if len(memory_ids) < count:
                continue
                
            sample_ids = random.sample(memory_ids, count)
            
            start_time = time.time()
            reflection = await self.memory_bridge.advanced_memory_reflection(
                memory_ids=sample_ids,
                reflection_depth="standard",
                include_thinking=True
            )
            elapsed = time.time() - start_time
            
            count_times[count] = {
                "time": elapsed,
                "per_memory": elapsed / count
            }
        
        results["memory_count_impact"] = count_times
        
        self.logger.info("Memory reflection benchmark completed")
        return results
    
    async def benchmark_hybrid_processing(self) -> Dict[str, Any]:
        """
        Benchmark hybrid memory processing performance.
        
        Returns:
            Dictionary with hybrid processing benchmark results
        """
        self.logger.info("Starting hybrid processing benchmark")
        results = {
            "memory_limit_impact": {},
            "retrieval_strategy_comparison": {}
        }
        
        # Test different memory limits
        limits = [5, 10, 20]
        limit_times = {}
        
        for limit in limits:
            start_time = time.time()
            response = await self.memory_bridge.process_with_hybrid_memory(
                prompt="Explain the TRILOGY BRAIN architecture",
                memory_limit=limit,
                store_response=False
            )
            elapsed = time.time() - start_time
            
            # Extract performance metrics
            memory_count = response.get("memory_context", {}).get("memory_count", 0)
            retrieval_time = response.get("memory_context", {}).get("retrieval_time", 0)
            processing_time = response.get("performance", {}).get("processing_time", 0)
            
            limit_times[limit] = {
                "total_time": elapsed,
                "memory_count": memory_count,
                "retrieval_time": retrieval_time,
                "processing_time": processing_time,
                "overhead": elapsed - retrieval_time - processing_time
            }
        
        results["memory_limit_impact"] = limit_times
        
        # Test different retrieval strategies
        strategies = ["semantic", "temporal", "hybrid"]
        strategy_times = {}
        
        for strategy in strategies:
            start_time = time.time()
            response = await self.memory_bridge.process_with_hybrid_memory(
                prompt="Explain the key components of the TRILOGY BRAIN",
                memory_limit=10,
                memory_retrieval_strategy=strategy,
                store_response=False
            )
            elapsed = time.time() - start_time
            
            # Extract performance metrics
            memory_count = response.get("memory_context", {}).get("memory_count", 0)
            retrieval_time = response.get("memory_context", {}).get("retrieval_time", 0)
            processing_time = response.get("performance", {}).get("processing_time", 0)
            
            strategy_times[strategy] = {
                "total_time": elapsed,
                "memory_count": memory_count,
                "retrieval_time": retrieval_time,
                "processing_time": processing_time
            }
        
        results["retrieval_strategy_comparison"] = strategy_times
        
        self.logger.info("Hybrid processing benchmark completed")
        return results
    
    async def benchmark_hybrid_thinking(self) -> Dict[str, Any]:
        """
        Benchmark Claude 3.7 Sonnet's hybrid thinking capabilities.

        Tests processing with varying thinking token limits and complexity levels.
        
        Returns:
            Dictionary with hybrid thinking benchmark results
        """
        self.logger.info("Starting hybrid thinking benchmark")
        results = {
            "thinking_token_limits": {},
            "complexity_levels": {},
            "thinking_performance": {}
        }
        
        if not self.hybrid_thinking_enabled:
            self.logger.warning("Hybrid thinking not enabled, skipping benchmark")
            return {"error": "Hybrid thinking not enabled"}
        
        # Test different thinking token limits
        token_limits = [2000, 5000, 10000, 15000]
        token_limit_times = {}
        
        for limit in token_limits:
            start_time = time.time()
            response = await self.composio_client.process_request(
                prompt="Analyze the performance characteristics of distributed memory systems with attention to scaling and retrieval efficiency",
                max_thinking_tokens=limit,
                include_thinking=True
            )
            elapsed = time.time() - start_time
            
            # Extract performance metrics
            thinking_tokens = len(response.get("thinking", "")) // 4  # Approximate token count
            output_tokens = len(response.get("content", "")) // 4  # Approximate token count
            
            token_limit_times[limit] = {
                "total_time": elapsed,
                "thinking_tokens": thinking_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": (thinking_tokens + output_tokens) / elapsed if elapsed > 0 else 0
            }
        
        results["thinking_token_limits"] = token_limit_times
        
        # Test different complexity levels
        complexity_levels = {
            "low": "List five key components of memory systems",
            "medium": "Explain how semantic indexing improves memory retrieval in AI systems",
            "high": "Compare and contrast three different approaches to memory consolidation in distributed AI architectures, analyzing tradeoffs between efficiency, accuracy, and resource utilization"
        }
        
        complexity_times = {}
        
        for level, prompt in complexity_levels.items():
            start_time = time.time()
            response = await self.composio_client.process_request(
                prompt=prompt,
                max_thinking_tokens=10000,
                include_thinking=True
            )
            elapsed = time.time() - start_time
            
            # Extract performance metrics
            thinking_tokens = len(response.get("thinking", "")) // 4  # Approximate token count
            output_tokens = len(response.get("content", "")) // 4  # Approximate token count
            thinking_time = response.get("performance", {}).get("thinking_time", 0)
            generation_time = response.get("performance", {}).get("generation_time", 0)
            
            complexity_times[level] = {
                "total_time": elapsed,
                "thinking_tokens": thinking_tokens,
                "output_tokens": output_tokens,
                "thinking_time": thinking_time,
                "generation_time": generation_time,
                "tokens_per_second": (thinking_tokens + output_tokens) / elapsed if elapsed > 0 else 0
            }
        
        results["complexity_levels"] = complexity_times
        
        # Test different memory-thinking integration approaches
        memory_samples = random.sample(self._test_memories, min(5, len(self._test_memories)))
        memory_context = "\n\n".join([m.get("content", "") for m in memory_samples])
        
        thinking_performance = {}
        
        # Direct integration test
        start_time = time.time()
        response = await self.composio_client.process_request(
            prompt=f"Given these memories:\n\n{memory_context}\n\nIdentify patterns and connections between them.",
            max_thinking_tokens=10000,
            include_thinking=True
        )
        direct_elapsed = time.time() - start_time
        
        # Iterative integration test
        start_time = time.time()
        initial_response = await self.composio_client.process_request(
            prompt="What are key questions I should ask about a set of memories to understand their relationships?",
            max_thinking_tokens=5000,
            include_thinking=True
        )
        
        second_response = await self.composio_client.process_request(
            prompt=f"Given these memories:\n\n{memory_context}\n\nAnd considering your previous analysis: {initial_response.get('content', '')}\n\nIdentify patterns and connections between them.",
            max_thinking_tokens=5000,
            include_thinking=True
        )
        iterative_elapsed = time.time() - start_time
        
        thinking_performance = {
            "direct_integration": {
                "total_time": direct_elapsed,
                "thinking_tokens": len(response.get("thinking", "")) // 4,
                "output_tokens": len(response.get("content", "")) // 4
            },
            "iterative_integration": {
                "total_time": iterative_elapsed,
                "thinking_tokens": len(initial_response.get("thinking", "")) // 4 + len(second_response.get("thinking", "")) // 4,
                "output_tokens": len(initial_response.get("content", "")) // 4 + len(second_response.get("content", "")) // 4
            }
        }
        
        results["thinking_performance"] = thinking_performance
        
        self.logger.info("Hybrid thinking benchmark completed")
        return results
    
    async def _generate_test_data(self, count: int):
        """
        Generate test memories for benchmarking.
        
        Args:
            count: Number of test memories to generate
        """
        self.logger.info(f"Generating {count} test memories")
        
        self._test_memories = []
        memory_ids = []
        
        # Generate and store test memories
        for i in range(count):
            memory = self._generate_memory()
            
            memory_id = await self.memory_manager.store_memory(
                content=memory["content"],
                memory_type=memory["type"],
                metadata=memory.get("metadata", {})
            )
            
            memory["id"] = memory_id
            self._test_memories.append(memory)
            memory_ids.append(memory_id)
            
            # Create some random relationships (for 30% of memories)
            if self.memory_bridge.enhanced_memory and i > 0 and random.random() < 0.3:
                source_id = memory_id
                target_id = random.choice(memory_ids[:-1])  # Pick a previous memory
                
                relationship_type = random.choice([
                    "related_to", "precedes", "follows", "references", "contradicts"
                ])
                strength = random.uniform(0.5, 1.0)
                
                await self.memory_manager.create_relationship(
                    source_id, target_id, relationship_type, strength
                )
        
        self.logger.info(f"Generated {len(self._test_memories)} test memories")
    
    def _generate_memory(self) -> Dict[str, Any]:
        """
        Generate a single test memory.
        
        Returns:
            Dictionary with memory data
        """
        memory_types = [
            "general", "conversation", "code_snippet", "concept", 
            "reasoning", "fact", "reference", "procedure"
        ]
        
        # Select a memory type
        memory_type = random.choice(memory_types)
        
        # Generate content based on type
        content = ""
        if memory_type == "general":
            content = f"This is a general memory about the TRILOGY BRAIN system, version {random.uniform(1.0, 3.0):.1f}."
        elif memory_type == "conversation":
            content = f"User: What is the TRILOGY BRAIN?\nAssistant: The TRILOGY BRAIN is an advanced distributed AI memory system with three core components."
        elif memory_type == "code_snippet":
            content = f"""```python
def process_memory(memory_id):
    memory = get_memory(memory_id)
    importance = calculate_importance(memory)
    return update_memory(memory_id, importance=importance)
```"""
        elif memory_type == "concept":
            content = f"The Executive Cortex in the TRILOGY BRAIN is responsible for resource allocation and decision-making processes."
        elif memory_type == "reasoning":
            content = f"When analyzing memory patterns, we should consider both temporal and semantic relationships to fully understand the context."
        elif memory_type == "fact":
            content = f"The TRILOGY BRAIN system was established in 2025 and has processed over {random.randint(1, 10)} million memories."
        elif memory_type == "reference":
            content = f"According to the research paper 'Advanced Memory Systems' (Smith et al., 2024), hierarchical memory organization improves retrieval efficiency by up to 45%."
        elif memory_type == "procedure":
            content = f"To initialize the TRILOGY BRAIN, first configure the environment variables, then initialize the memory foundation, and finally connect to the distributed network."
        
        # Generate metadata
        metadata = {
            "importance": random.uniform(0.1, 1.0),
            "timestamp": time.time() - random.randint(0, 30 * 86400),  # Up to 30 days old
            "source": random.choice(["user_input", "system_generated", "external_reference", "analysis"]),
            "version": f"1.{random.randint(0, 9)}"
        }
        
        return {
            "content": content,
            "type": memory_type,
            "metadata": metadata
        }
    
    def _save_benchmark_results(self):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(self.benchmark_data_path, f"benchmark_{timestamp}.json")
        
        with open(result_file, "w") as f:
            json.dump(self._benchmark_results, f, indent=2)
        
        self.logger.info(f"Benchmark results saved to {result_file}")
    
    async def _cleanup(self):
        """Clean up benchmark data"""
        # Clear test memories
        for memory in self._test_memories:
            memory_id = memory.get("id")
            if memory_id:
                try:
                    await self.memory_manager.delete_memory(memory_id)
                except Exception as e:
                    self.logger.warning(f"Error deleting test memory {memory_id}: {e}")
        
        self._test_memories = []
        self.logger.info("Benchmark cleanup completed")
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get the latest benchmark results"""
        return self._benchmark_results
    
    async def generate_benchmark_report(self) -> str:
        """
        Generate a comprehensive benchmark report.
        
        Returns:
            Markdown report with benchmark analysis
        """
        if not self._benchmark_results:
            return self.format_response("No benchmark results available", include_header=True)
        
        report = "# TRILOGY BRAIN Memory System Benchmark Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Overall summary
        report += "## Summary\n\n"
        report += f"- **Total memories tested**: {self._benchmark_results.get('memory_count', 'N/A')}\n"
        report += f"- **Total benchmark time**: {self._benchmark_results.get('total_time', 0):.2f} seconds\n"
        report += f"- **Model version**: {self.model_version}\n"
        
        # Storage performance
        if "storage" in self._benchmark_results:
            storage = self._benchmark_results["storage"]
            report += "\n## Memory Storage Performance\n\n"
            
            if "single_operation" in storage:
                single = storage["single_operation"]
                report += "### Single Memory Storage\n\n"
                report += f"- **Average time**: {single.get('mean', 0):.4f} seconds\n"
                report += f"- **Median time**: {single.get('median', 0):.4f} seconds\n"
                report += f"- **Min/Max times**: {single.get('min', 0):.4f}s / {single.get('max', 0):.4f}s\n\n"
            
            if "batch_operations" in storage:
                report += "### Batch Operations\n\n"
                report += "| Batch Size | Total Time (s) | Time Per Memory (s) |\n"
                report += "|------------|---------------|---------------------|\n"
                
                for batch_size, data in storage["batch_operations"].items():
                    report += f"| {batch_size} | {data.get('total_time', 0):.4f} | {data.get('per_memory', 0):.4f} |\n"
                
                report += "\n"
            
            if "concurrent_operations" in storage:
                report += "### Concurrent Operations\n\n"
                report += "| Batch Size | Total Time (s) | Time Per Memory (s) |\n"
                report += "|------------|---------------|---------------------|\n"
                
                for batch_size, data in storage["concurrent_operations"].items():
                    report += f"| {batch_size} | {data.get('total_time', 0):.4f} | {data.get('per_memory', 0):.4f} |\n"
                
                report += "\n"
        
        # Retrieval performance
        if "retrieval" in self._benchmark_results:
            retrieval = self._benchmark_results["retrieval"]
            report += "\n## Memory Retrieval Performance\n\n"
            
            if "direct_retrieval" in retrieval:
                direct = retrieval["direct_retrieval"]
                report += "### Direct Memory Retrieval\n\n"
                report += f"- **Average time**: {direct.get('mean', 0):.4f} seconds\n"
                report += f"- **Median time**: {direct.get('median', 0):.4f} seconds\n"
                report += f"- **Min/Max times**: {direct.get('min', 0):.4f}s / {direct.get('max', 0):.4f}s\n\n"
            
            if "search_operations" in retrieval:
                search = retrieval["search_operations"]
                report += "### Search Operations\n\n"
                report += f"- **Average search time**: {search.get('mean_time', 0):.4f} seconds\n\n"
                report += "| Query | Time (s) | Results |\n"
                report += "|-------|----------|----------|\n"
                
                for query_data in search.get("queries", []):
                    report += f"| {query_data.get('query')} | {query_data.get('time', 0):.4f} | {query_data.get('result_count', 0)} |\n"
                
                report += "\n"
            
            if "strategy_comparison" in retrieval:
                report += "### Retrieval Strategies\n\n"
                report += "| Strategy | Time (s) | Memory Count |\n"
                report += "|----------|----------|---------------|\n"
                
                for strategy, data in retrieval["strategy_comparison"].items():
                    report += f"| {strategy} | {data.get('time', 0):.4f} | {data.get('memory_count', 'N/A')} |\n"
                
                report += "\n"
        
        # Hybrid processing performance
        if "hybrid_processing" in self._benchmark_results:
            hybrid = self._benchmark_results["hybrid_processing"]
            report += "\n## Hybrid Processing Performance\n\n"
            
            if "memory_limit_impact" in hybrid:
                report += "### Impact of Memory Limit\n\n"
                report += "| Memory Limit | Total Time (s) | Retrieval Time (s) | Processing Time (s) | Overhead (s) |\n"
                report += "|--------------|---------------|-------------------|-------------------|-------------|\n"
                
                for limit, data in hybrid["memory_limit_impact"].items():
                    report += f"| {limit} | {data.get('total_time', 0):.4f} | {data.get('retrieval_time', 0):.4f} | {data.get('processing_time', 0):.4f} | {data.get('overhead', 0):.4f} |\n"
                
                report += "\n"
            
            if "retrieval_strategy_comparison" in hybrid:
                report += "### Retrieval Strategy Comparison\n\n"
                report += "| Strategy | Total Time (s) | Memory Count | Retrieval Time (s) | Processing Time (s) |\n"
                report += "|----------|---------------|--------------|-------------------|-------------------|\n"
                
                for strategy, data in hybrid["retrieval_strategy_comparison"].items():
                    report += f"| {strategy} | {data.get('total_time', 0):.4f} | {data.get('memory_count', 0)} | {data.get('retrieval_time', 0):.4f} | {data.get('processing_time', 0):.4f} |\n"
                
                report += "\n"
        
        # Hybrid thinking performance (Claude 3.7 specific)
        if "hybrid_thinking" in self._benchmark_results and self._benchmark_results["hybrid_thinking"]:
            hybrid_thinking = self._benchmark_results["hybrid_thinking"]
            report += "\n## Hybrid Thinking Performance (Claude 3.7)\n\n"
            
            if "thinking_token_limits" in hybrid_thinking:
                report += "### Impact of Thinking Token Limits\n\n"
                report += "| Token Limit | Total Time (s) | Thinking Tokens | Output Tokens | Tokens/Second |\n"
                report += "|-------------|---------------|----------------|--------------|---------------|\n"
                
                for limit, data in hybrid_thinking["thinking_token_limits"].items():
                    report += f"| {limit} | {data.get('total_time', 0):.4f} | {data.get('thinking_tokens', 0)} | {data.get('output_tokens', 0)} | {data.get('tokens_per_second', 0):.2f} |\n"
                
                report += "\n"
            
            if "complexity_levels" in hybrid_thinking:
                report += "### Complexity Level Impact\n\n"
                report += "| Complexity | Total Time (s) | Thinking Tokens | Output Tokens | Thinking Time (s) | Generation Time (s) |\n"
                report += "|------------|---------------|----------------|--------------|-------------------|--------------------|\n"
                
                for level, data in hybrid_thinking["complexity_levels"].items():
                    report += f"| {level} | {data.get('total_time', 0):.4f} | {data.get('thinking_tokens', 0)} | {data.get('output_tokens', 0)} | {data.get('thinking_time', 0):.4f} | {data.get('generation_time', 0):.4f} |\n"
                
                report += "\n"
            
            if "thinking_performance" in hybrid_thinking:
                report += "### Memory-Thinking Integration Approaches\n\n"
                report += "| Approach | Total Time (s) | Thinking Tokens | Output Tokens | Tokens/Second |\n"
                report += "|----------|---------------|----------------|--------------|---------------|\n"
                
                for approach, data in hybrid_thinking["thinking_performance"].items():
                    tokens = data.get('thinking_tokens', 0) + data.get('output_tokens', 0)
                    tokens_per_sec = tokens / data.get('total_time', 1) if data.get('total_time', 0) > 0 else 0
                    report += f"| {approach} | {data.get('total_time', 0):.4f} | {data.get('thinking_tokens', 0)} | {data.get('output_tokens', 0)} | {tokens_per_sec:.2f} |\n"
                
                report += "\n"
        
        # Recommendations
        report += "\n## Performance Recommendations\n\n"
        
        # Generate recommendations based on results
        recommendations = []
        
        # Storage recommendations
        if "storage" in self._benchmark_results:
            storage = self._benchmark_results["storage"]
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
        if "retrieval" in self._benchmark_results:
            retrieval = self._benchmark_results["retrieval"]
            if "strategy_comparison" in retrieval:
                strategies = retrieval["strategy_comparison"]
                if "semantic" in strategies and "hybrid" in strategies and "temporal" in strategies:
                    semantic_time = strategies["semantic"].get("time", 0)
                    hybrid_time = strategies["hybrid"].get("time", 0)
                    temporal_time = strategies["temporal"].get("time", 0)
                    
                    fastest = min((semantic_time, "semantic"), (hybrid_time, "hybrid"), (temporal_time, "temporal"), key=lambda x: x[0])
                    recommendations.append(f"The '{fastest[1]}' retrieval strategy is most efficient ({fastest[0]:.4f}s)")
        
        # Hybrid processing recommendations
        if "hybrid_processing" in self._benchmark_results:
            hybrid = self._benchmark_results["hybrid_processing"]
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
        if "hybrid_thinking" in self._benchmark_results and self._benchmark_results["hybrid_thinking"]:
            hybrid_thinking = self._benchmark_results["hybrid_thinking"]
            
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
        
        # Add recommendations to report
        for i, recommendation in enumerate(recommendations, 1):
            report += f"{i}. {recommendation}\n"
        
        # Add agent commandments as reference
        report += "\n## Agent Commandments\n\n"
        for i, commandment in enumerate(self.commandments, 1):
            report += f"{i}. {commandment}\n"
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.benchmark_data_path, f"benchmark_report_{timestamp}.md")
        
        with open(report_file, "w") as f:
            f.write(report)
        
        self.logger.info(f"Benchmark report generated: {report_file}")
        
        # Return formatted report with agent branding
        return self.format_response(report, include_header=True) 