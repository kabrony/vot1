#!/usr/bin/env python3
"""
Test script for advanced memory systems in TRILOGY BRAIN.
This script performs benchmarks on the CascadingMemoryCache and EpisodicMemoryManager.
"""

import os
import sys
import json
import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestAdvancedMemory")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("dotenv module not found, using existing environment variables")
    try:
        with open(".env", "r") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        logger.info("Environment variables manually loaded from .env file")
    except Exception as e:
        logger.warning(f"Failed to manually load .env file: {e}")

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # Try absolute imports first (for installed package)
    from src.vot1.composio.memory_benchmark import MemoryBenchmark
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.memory import MemoryManager
except ImportError:
    try:
        # Fall back to relative imports (for development)
        from vot1.composio.memory_benchmark import MemoryBenchmark
        from vot1.composio.memory_bridge import ComposioMemoryBridge
        from vot1.memory import MemoryManager
    except ImportError as e:
        logger.error(f"Error importing memory modules: {e}")
        logger.error("Make sure you're running from the project root and have installed the required dependencies.")
        sys.exit(1)

class AdvancedMemoryTest:
    """
    Test class for advanced memory functionality in TRILOGY BRAIN.
    Tests CascadingMemoryCache and EpisodicMemoryManager.
    """
    
    def __init__(self, memory_path: str = "memory/test"):
        """Initialize the test class."""
        self.memory_path = memory_path
        self.composio_api_key = os.environ.get("COMPOSIO_API_KEY")
        self.composio_mcp_url = os.environ.get("COMPOSIO_MCP_URL")
        self.benchmark_data_path = "output/memory_test"
        
        # Create output directory
        os.makedirs(self.benchmark_data_path, exist_ok=True)
        os.makedirs(self.memory_path, exist_ok=True)
        
        logger.info(f"Initialized AdvancedMemoryTest with memory path: {self.memory_path}")
        logger.info(f"Output directory: {self.benchmark_data_path}")
    
    async def initialize_memory_system(self) -> bool:
        """Initialize the memory system components."""
        try:
            # Initialize memory system
            self.memory_manager = MemoryManager(memory_path=self.memory_path)
            
            # Initialize memory bridge
            self.memory_bridge = ComposioMemoryBridge(
                memory_storage=self.memory_manager,
                max_memory_items=1000,
                max_tokens_per_memory=500,
                enable_hybrid_thinking=True
            )
            
            # Initialize a dummy composio client for testing
            class DummyComposioClient:
                def __init__(self):
                    self.api_key = "dummy_key"
                    self.mcp_url = "https://dummy.url"
                
                async def execute_tool(self, *args, **kwargs):
                    return {"success": True, "result": "Dummy result"}
                
                async def list_tools(self):
                    return []
            
            # Set the composio client
            self.composio_client = DummyComposioClient()
            
            # Initialize memory benchmark
            self.benchmark = MemoryBenchmark(
                memory_bridge=self.memory_bridge,
                memory_manager=self.memory_manager,
                composio_client=self.composio_client,
                memory_path=self.memory_path,
                benchmark_data_path=self.benchmark_data_path,
                clean_after_benchmark=False  # Keep test data for inspection
            )
            
            logger.info("Memory system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def run_basic_tests(self) -> Dict[str, Any]:
        """Run basic memory storage and retrieval tests."""
        logger.info("Running basic memory tests")
        
        results = {
            "storage": {},
            "retrieval": {},
            "start_time": time.time(),
            "success": False
        }
        
        try:
            # Store a test memory
            memory_id = await self.memory_manager.store_memory(
                content="This is a test memory for the TRILOGY BRAIN system with advanced features.",
                memory_type="test",
                metadata={
                    "importance": 0.8,
                    "test_id": "basic_test_1",
                    "timestamp": time.time()
                }
            )
            
            results["storage"]["memory_id"] = memory_id
            results["storage"]["success"] = memory_id is not None
            logger.info(f"Stored test memory with ID: {memory_id}")
            
            # Retrieve the memory
            memory = await self.memory_manager.get_memory(memory_id)
            results["retrieval"]["success"] = memory is not None
            results["retrieval"]["content_match"] = "test memory" in memory.get("content", "")
            logger.info(f"Retrieved memory: {memory.get('content', '')[:50]}...")
            
            # Test semantic search
            search_results = await self.memory_manager.search_memories(
                query="advanced features",
                limit=5
            )
            
            results["search"] = {
                "success": len(search_results) > 0,
                "count": len(search_results),
                "first_result": search_results[0] if search_results else None
            }
            
            logger.info(f"Search returned {len(search_results)} results")
            
            results["success"] = results["storage"]["success"] and results["retrieval"]["success"]
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in basic memory tests: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            results["error"] = str(e)
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            
            return results
    
    async def test_cascading_memory_cache(self, memory_count: int = 20) -> Dict[str, Any]:
        """Test the CascadingMemoryCache functionality."""
        logger.info(f"Testing CascadingMemoryCache with {memory_count} memories")
        
        results = {
            "cache_metrics": {},
            "start_time": time.time(),
            "success": False
        }
        
        try:
            # Access the cascading cache from the memory manager
            if hasattr(self.memory_manager, "cascading_cache"):
                cache = self.memory_manager.cascading_cache
                
                # Generate and process test memories
                memories = []
                for i in range(memory_count):
                    memory = {
                        "id": f"test_mem_{i}",
                        "content": f"Test memory {i} with varying importance for cascading cache test.",
                        "timestamp": time.time(),
                        "importance": random.random(),  # Random importance
                        "metadata": {
                            "test_id": f"cache_test_{i}",
                            "group": f"group_{i % 5}"  # Create 5 groups
                        }
                    }
                    memories.append(memory)
                    
                    # Process the memory through the cache
                    cache_result = await cache.process_memory(memory)
                    logger.debug(f"Processed memory {i}: {cache_result}")
                
                # Check cache metrics
                metrics = cache.get_metrics()
                results["cache_metrics"] = metrics
                logger.info(f"Cache metrics: {metrics}")
                
                # Test context building
                context_result = cache.build_context(
                    query="importance for cascading cache",
                    token_budget=10000
                )
                
                results["context_building"] = {
                    "success": context_result is not None,
                    "token_count": context_result.get("token_count") if context_result else 0,
                    "memory_count": len(context_result.get("memories", [])) if context_result else 0
                }
                
                logger.info(f"Built context with {results['context_building'].get('memory_count')} memories")
                
                results["success"] = True
                results["end_time"] = time.time()
                results["duration"] = results["end_time"] - results["start_time"]
                
                return results
            else:
                results["error"] = "CascadingMemoryCache not found in memory manager"
                return results
                
        except Exception as e:
            logger.error(f"Error testing CascadingMemoryCache: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            results["error"] = str(e)
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            
            return results
    
    async def test_episodic_memory(self, event_count: int = 10) -> Dict[str, Any]:
        """Test the EpisodicMemoryManager functionality."""
        logger.info(f"Testing EpisodicMemoryManager with {event_count} events")
        
        results = {
            "episodic_metrics": {},
            "start_time": time.time(),
            "success": False
        }
        
        try:
            # Access the episodic memory from the memory manager
            if hasattr(self.memory_manager, "episodic_memory"):
                episodic = self.memory_manager.episodic_memory
                
                # Generate and process test events
                events = []
                for i in range(event_count):
                    # Create an event with time progression
                    time_offset = i * 60  # 1 minute between events
                    event_time = time.time() - (event_count - i) * 60
                    
                    event = {
                        "id": f"event_{i}",
                        "content": f"Event {i} occurred at timestamp {event_time}",
                        "timestamp": event_time,
                        "importance": 0.5 + random.random() * 0.5,  # Higher importance
                        "metadata": {
                            "test_id": f"episodic_test_{i}",
                            "event_type": f"type_{i % 3}"  # Create 3 event types
                        }
                    }
                    events.append(event)
                    
                    # Process the event through episodic memory
                    episodic_result = await episodic.process_event(event)
                    logger.debug(f"Processed event {i}: {episodic_result}")
                
                # Check episodic memory metrics
                metrics = episodic.get_metrics()
                results["episodic_metrics"] = metrics
                logger.info(f"Episodic memory metrics: {metrics}")
                
                # Test episode retrieval
                episodes = await episodic.get_episodes(limit=5)
                
                results["episode_retrieval"] = {
                    "success": episodes is not None,
                    "episode_count": len(episodes) if episodes else 0,
                    "first_episode": episodes[0] if episodes else None
                }
                
                logger.info(f"Retrieved {results['episode_retrieval'].get('episode_count')} episodes")
                
                # Test timeline generation
                timeline = await episodic.generate_timeline(
                    start_time=time.time() - (event_count + 1) * 60,
                    end_time=time.time(),
                    resolution="minutes"
                )
                
                results["timeline"] = {
                    "success": timeline is not None,
                    "event_count": len(timeline.get("events", [])) if timeline else 0
                }
                
                logger.info(f"Generated timeline with {results['timeline'].get('event_count')} events")
                
                results["success"] = True
                results["end_time"] = time.time()
                results["duration"] = results["end_time"] - results["start_time"]
                
                return results
            else:
                results["error"] = "EpisodicMemoryManager not found in memory manager"
                return results
                
        except Exception as e:
            logger.error(f"Error testing EpisodicMemoryManager: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            results["error"] = str(e)
            results["end_time"] = time.time()
            results["duration"] = results["end_time"] - results["start_time"]
            
            return results
    
    async def run_benchmark(self, memory_count: int = 50, include_hybrid_thinking: bool = False) -> Dict[str, Any]:
        """Run a full memory benchmark."""
        logger.info(f"Running full memory benchmark with {memory_count} memories")
        
        try:
            # Run the benchmark
            benchmark_results = await self.benchmark.process(
                memory_count=memory_count,
                include_hybrid_thinking=include_hybrid_thinking
            )
            
            # Generate a report
            report_path = await self.benchmark.generate_benchmark_report()
            logger.info(f"Benchmark report generated at: {report_path}")
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Error running memory benchmark: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {"error": str(e), "success": False}

async def run_test():
    """Run the advanced memory test."""
    logger.info("Starting advanced memory system test")
    
    # Create test instance
    test = AdvancedMemoryTest(memory_path="memory/advanced_test")
    
    # Initialize memory system
    init_success = await test.initialize_memory_system()
    if not init_success:
        logger.error("Failed to initialize memory system, aborting test")
        return False
    
    # Run basic tests
    logger.info("Running basic memory tests")
    basic_results = await test.run_basic_tests()
    logger.info(f"Basic test results: success={basic_results.get('success', False)}")
    
    # Test cascading memory cache
    logger.info("Testing CascadingMemoryCache")
    cascading_results = await test.test_cascading_memory_cache(memory_count=20)
    logger.info(f"CascadingMemoryCache test results: success={cascading_results.get('success', False)}")
    
    # Test episodic memory
    logger.info("Testing EpisodicMemoryManager")
    episodic_results = await test.test_episodic_memory(event_count=10)
    logger.info(f"EpisodicMemoryManager test results: success={episodic_results.get('success', False)}")
    
    # Run benchmark
    logger.info("Running memory benchmark")
    benchmark_results = await test.run_benchmark(memory_count=50, include_hybrid_thinking=False)
    logger.info(f"Benchmark results: success={benchmark_results.get('success', False)}")
    
    # Combine results
    all_results = {
        "basic_test": basic_results,
        "cascading_cache": cascading_results,
        "episodic_memory": episodic_results,
        "benchmark": benchmark_results,
        "timestamp": datetime.now().isoformat(),
        "overall_success": all([
            basic_results.get("success", False),
            cascading_results.get("success", False),
            episodic_results.get("success", False),
            benchmark_results.get("success", False)
        ])
    }
    
    # Save results
    results_path = os.path.join("output/memory_test", f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info(f"Test results saved to {results_path}")
    
    # Print summary
    print("\n=== Advanced Memory Test Summary ===")
    print(f"Basic Memory Test: {'✅' if basic_results.get('success', False) else '❌'}")
    print(f"CascadingMemoryCache Test: {'✅' if cascading_results.get('success', False) else '❌'}")
    print(f"EpisodicMemoryManager Test: {'✅' if episodic_results.get('success', False) else '❌'}")
    print(f"Memory Benchmark: {'✅' if benchmark_results.get('success', False) else '❌'}")
    print(f"Overall: {'✅' if all_results['overall_success'] else '❌'}")
    print(f"Detailed results saved to: {results_path}")
    
    return all_results["overall_success"]

if __name__ == "__main__":
    import random
    random.seed(42)  # For reproducible tests
    asyncio.run(run_test()) 