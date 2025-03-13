#!/usr/bin/env python3
"""
VOT1 System Check Module

This module provides functionality to check the health and status of all VOT1 components.
It can perform diagnostics on MCP, Memory, OWL Reasoning, GitHub integration (both MCP and Composio),
and other core components. Use this for system verification and troubleshooting.
"""

import os
import sys
import logging
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemCheck:
    """
    Main system check class that verifies the health and connectivity of all VOT1 components.
    This helps ensure that all parts of the system are properly initialized and functioning.
    """
    
    def __init__(
        self,
        mcp=None,
        memory_manager=None,
        owl_engine=None,
        code_analyzer=None,
        github_bridge=None,
        workspace_dir: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the System Check with VOT1 component instances.
        
        Args:
            mcp: VotModelControlProtocol instance
            memory_manager: MemoryManager instance
            owl_engine: OWLReasoningEngine instance
            code_analyzer: Code Analyzer instance
            github_bridge: GitHub bridge instance (MCP or Composio)
            workspace_dir: VOT1 workspace directory
            verbose: Whether to print verbose output during checks
        """
        self.mcp = mcp
        self.memory_manager = memory_manager
        self.owl_engine = owl_engine
        self.code_analyzer = code_analyzer
        self.github_bridge = github_bridge
        self.workspace_dir = workspace_dir or os.getenv("VOT1_WORKSPACE_DIR", os.getcwd())
        self.verbose = verbose
        
        # Initialize components lazily if not provided
        self._initialized = False
        
    async def initialize_components(self):
        """Initialize any missing components as needed."""
        if self._initialized:
            return
            
        try:
            # Import components only when needed
            from src.vot1.vot_mcp import VotModelControlProtocol
            from src.vot1.memory import MemoryManager
            from src.vot1.owl_reasoning import OWLReasoningEngine
            from src.vot1.code_analyzer import create_analyzer
            
            # Initialize MCP if not provided
            if not self.mcp:
                self.mcp = VotModelControlProtocol(
                    primary_model="anthropic/claude-3-7-sonnet-20240620",
                    secondary_model="perplexity/pplx-70b-online"
                )
                logger.info("MCP initialized")
            
            # Initialize Memory Manager if not provided
            if not self.memory_manager:
                self.memory_manager = MemoryManager(
                    storage_dir=os.path.join(self.workspace_dir, "memory")
                )
                logger.info("Memory Manager initialized")
            
            # Initialize OWL Reasoning Engine if not provided
            if not self.owl_engine:
                ontology_path = os.path.join(self.workspace_dir, "owl", "vot1_ontology.owl")
                if os.path.exists(ontology_path):
                    self.owl_engine = OWLReasoningEngine(
                        ontology_path=ontology_path,
                        memory_manager=self.memory_manager
                    )
                    logger.info("OWL Reasoning Engine initialized")
                else:
                    logger.warning(f"Ontology file not found at {ontology_path}")
            
            # Initialize Code Analyzer if not provided
            if not self.code_analyzer:
                self.code_analyzer = create_analyzer(
                    mcp=self.mcp,
                    owl_engine=self.owl_engine,
                    workspace_dir=self.workspace_dir
                )
                logger.info("Code Analyzer initialized")
            
            # Initialize GitHub Bridge if not provided
            if not self.github_bridge:
                # Try to use Composio bridge first, fall back to MCP bridge
                try:
                    # Import Composio bridge
                    from src.vot1.github_composio_bridge import GitHubComposioBridge, COMPOSIO_AVAILABLE
                    
                    if COMPOSIO_AVAILABLE:
                        self.github_bridge = GitHubComposioBridge(
                            mcp=self.mcp,
                            memory_manager=self.memory_manager,
                            code_analyzer=self.code_analyzer
                        )
                        logger.info("Composio GitHub Bridge initialized")
                    else:
                        # Fall back to MCP bridge
                        from src.vot1.github_app_bridge import GitHubAppBridge
                        self.github_bridge = GitHubAppBridge(
                            mcp=self.mcp,
                            memory_manager=self.memory_manager,
                            code_analyzer=self.code_analyzer
                        )
                        logger.info("MCP GitHub Bridge initialized")
                except ImportError:
                    # Fall back to MCP bridge
                    from src.vot1.github_app_bridge import GitHubAppBridge
                    self.github_bridge = GitHubAppBridge(
                        mcp=self.mcp,
                        memory_manager=self.memory_manager,
                        code_analyzer=self.code_analyzer
                    )
                    logger.info("MCP GitHub Bridge initialized")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Run all system checks to verify the health of the VOT1 system.
        
        Returns:
            Dictionary with check results for each component
        """
        # Initialize components if needed
        await self.initialize_components()
        
        # Run all checks
        results = {
            "timestamp": time.time(),
            "system_info": self._get_system_info(),
            "components": {}
        }
        
        # Check MCP
        results["components"]["mcp"] = await self.check_mcp()
        
        # Check Memory Manager
        results["components"]["memory"] = await self.check_memory()
        
        # Check OWL Reasoning Engine
        results["components"]["owl_reasoning"] = await self.check_owl_reasoning()
        
        # Check Code Analyzer
        results["components"]["code_analyzer"] = await self.check_code_analyzer()
        
        # Check GitHub Bridge
        results["components"]["github"] = await self.check_github()
        
        # Calculate overall health
        overall_status = True
        for component, result in results["components"].items():
            if not result.get("status", False):
                overall_status = False
                break
        
        results["status"] = overall_status
        results["status_message"] = "All components are healthy" if overall_status else "One or more components have issues"
        
        return results
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        import platform
        import psutil
        
        try:
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_available": psutil.virtual_memory().available / (1024 * 1024 * 1024),  # GB
                "memory_total": psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
                "disk_free": psutil.disk_usage('/').free / (1024 * 1024 * 1024),  # GB
                "disk_total": psutil.disk_usage('/').total / (1024 * 1024 * 1024),  # GB
                "hostname": platform.node()
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "error": str(e),
                "python_version": platform.python_version()
            }
    
    async def check_mcp(self) -> Dict[str, Any]:
        """
        Check the health and connectivity of the MCP component.
        
        Returns:
            Dictionary with MCP check results
        """
        if not self.mcp:
            return {
                "status": False,
                "message": "MCP not initialized",
                "error": "Component missing"
            }
        
        try:
            # Test MCP with a simple request
            test_prompt = "Respond with a single word: 'healthy'"
            response = await self.mcp.process_request(test_prompt, max_tokens=10)
            
            content = response.get("content", "").strip().lower()
            
            # Check for expected response
            if "healthy" in content:
                models_info = {
                    "primary_model": getattr(self.mcp, "primary_model", "unknown"),
                    "secondary_model": getattr(self.mcp, "secondary_model", "unknown")
                }
                return {
                    "status": True,
                    "message": "MCP is responding correctly",
                    "models": models_info,
                    "response_time_ms": getattr(response, "latency", 0) * 1000
                }
            else:
                return {
                    "status": False,
                    "message": "MCP response is unexpected",
                    "error": f"Expected 'healthy', got: {content[:30]}..." if len(content) > 30 else content,
                    "models": {
                        "primary_model": getattr(self.mcp, "primary_model", "unknown"),
                        "secondary_model": getattr(self.mcp, "secondary_model", "unknown")
                    }
                }
                
        except Exception as e:
            logger.error(f"Error checking MCP: {e}")
            return {
                "status": False,
                "message": "Error checking MCP",
                "error": str(e)
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """
        Check the health of the Memory Manager component.
        
        Returns:
            Dictionary with Memory Manager check results
        """
        if not self.memory_manager:
            return {
                "status": False,
                "message": "Memory Manager not initialized",
                "error": "Component missing"
            }
        
        try:
            # Try to add a test memory and retrieve it
            test_content = f"Test memory created by system check at {time.time()}"
            test_metadata = {
                "type": "system_check",
                "timestamp": time.time()
            }
            
            # Add test memory
            test_memory = self.memory_manager.add_semantic_memory(
                content=test_content,
                metadata=test_metadata
            )
            
            # Verify memory was added successfully
            if not test_memory or not hasattr(test_memory, 'id'):
                return {
                    "status": False,
                    "message": "Failed to add test memory",
                    "error": "Memory add operation did not return a valid memory object"
                }
            
            # Retrieve the memory to verify it was stored
            retrieved_memory = self.memory_manager.get_memory_by_id(test_memory.id)
            
            if not retrieved_memory:
                return {
                    "status": False,
                    "message": "Failed to retrieve test memory",
                    "error": f"Memory with ID {test_memory.id} could not be retrieved"
                }
            
            # Get storage stats
            storage_info = {
                "total_memories": len(self.memory_manager.get_all_memories()),
                "storage_path": getattr(self.memory_manager, "storage_dir", "unknown")
            }
            
            return {
                "status": True,
                "message": "Memory Manager is functioning correctly",
                "storage": storage_info,
                "test_memory_id": test_memory.id
            }
            
        except Exception as e:
            logger.error(f"Error checking Memory Manager: {e}")
            return {
                "status": False,
                "message": "Error checking Memory Manager",
                "error": str(e)
            }
    
    async def check_owl_reasoning(self) -> Dict[str, Any]:
        """
        Check the health of the OWL Reasoning Engine.
        
        Returns:
            Dictionary with OWL Reasoning Engine check results
        """
        if not self.owl_engine:
            return {
                "status": False,
                "message": "OWL Reasoning Engine not initialized",
                "error": "Component missing"
            }
        
        try:
            # Check if ontology is loaded
            ontology_loaded = hasattr(self.owl_engine, "ontology") and self.owl_engine.ontology is not None
            
            if not ontology_loaded:
                return {
                    "status": False,
                    "message": "OWL Reasoning Engine has no ontology loaded",
                    "error": "Missing ontology"
                }
            
            # Get ontology stats
            try:
                stats = {
                    "classes_count": len(list(self.owl_engine.ontology.classes())),
                    "properties_count": len(list(self.owl_engine.ontology.object_properties())),
                    "individuals_count": len(list(self.owl_engine.ontology.individuals())),
                    "ontology_path": getattr(self.owl_engine, "ontology_path", "unknown")
                }
            except Exception as stats_err:
                stats = {
                    "error": f"Failed to get ontology stats: {stats_err}"
                }
            
            return {
                "status": True,
                "message": "OWL Reasoning Engine is properly initialized",
                "ontology_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error checking OWL Reasoning Engine: {e}")
            return {
                "status": False,
                "message": "Error checking OWL Reasoning Engine",
                "error": str(e)
            }
    
    async def check_code_analyzer(self) -> Dict[str, Any]:
        """
        Check the health of the Code Analyzer.
        
        Returns:
            Dictionary with Code Analyzer check results
        """
        if not self.code_analyzer:
            return {
                "status": False,
                "message": "Code Analyzer not initialized",
                "error": "Component missing"
            }
        
        try:
            # Check if analyzer is properly initialized
            analyzer_type = type(self.code_analyzer).__name__
            
            # Create a simple test file to analyze
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write("""
                # Test file for code analyzer
                def hello_world():
                    print("Hello, world!")
                    return True
                
                # TODO: Add more functionality
                
                if __name__ == "__main__":
                    hello_world()
                """)
                tmp_path = tmp.name
            
            try:
                # Analyze the test file
                analysis_result = await self.code_analyzer.analyze_file(tmp_path)
                
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                
                if not analysis_result:
                    return {
                        "status": False,
                        "message": "Code Analyzer failed to analyze test file",
                        "error": "No analysis result returned"
                    }
                
                return {
                    "status": True,
                    "message": "Code Analyzer is functioning correctly",
                    "analyzer_type": analyzer_type,
                    "sample_analysis": {
                        "has_todos": "TODO" in str(analysis_result),
                        "analysis_length": len(str(analysis_result))
                    }
                }
            except Exception as analyze_err:
                # Clean up the temporary file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
                
                logger.error(f"Error during code analysis: {analyze_err}")
                return {
                    "status": False,
                    "message": "Code Analyzer failed to analyze test file",
                    "error": str(analyze_err),
                    "analyzer_type": analyzer_type
                }
            
        except Exception as e:
            logger.error(f"Error checking Code Analyzer: {e}")
            return {
                "status": False,
                "message": "Error checking Code Analyzer",
                "error": str(e)
            }
    
    async def check_github(self) -> Dict[str, Any]:
        """
        Check the health of the GitHub integration.
        
        Returns:
            Dictionary with GitHub integration check results
        """
        if not self.github_bridge:
            return {
                "status": False,
                "message": "GitHub bridge not initialized",
                "error": "Component missing"
            }
        
        try:
            # Determine bridge type
            from src.vot1.github_app_bridge import GitHubAppBridge
            
            try:
                from src.vot1.github_composio_bridge import GitHubComposioBridge
                is_composio = isinstance(self.github_bridge, GitHubComposioBridge)
            except ImportError:
                is_composio = False
            
            bridge_type = "Composio" if is_composio else "MCP"
            
            # Check connection
            is_connected = await self.github_bridge.check_connection()
            
            if not is_connected:
                return {
                    "status": False,
                    "message": f"GitHub {bridge_type} bridge is not connected",
                    "error": "No active GitHub connection",
                    "bridge_type": bridge_type
                }
            
            # Get bridge info
            bridge_info = {
                "type": bridge_type,
                "default_owner": getattr(self.github_bridge, "default_owner", None),
                "default_repo": getattr(self.github_bridge, "default_repo", None)
            }
            
            if is_composio:
                bridge_info["composio_available"] = getattr(self.github_bridge, "has_composio", False)
                bridge_info["model_name"] = getattr(self.github_bridge, "model_name", "unknown")
            
            return {
                "status": True,
                "message": f"GitHub {bridge_type} bridge is connected and functioning",
                "bridge_info": bridge_info
            }
            
        except Exception as e:
            logger.error(f"Error checking GitHub bridge: {e}")
            return {
                "status": False,
                "message": "Error checking GitHub bridge",
                "error": str(e)
            }
    
    async def print_check_results(self, results: Dict[str, Any]):
        """Print check results in a user-friendly format."""
        print("\n" + "="*80)
        print(f" VOT1 SYSTEM CHECK RESULTS - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Print overall status
        status = "✅ HEALTHY" if results.get("status", False) else "❌ ISSUES DETECTED"
        print(f"\nOverall Status: {status}")
        print(f"  {results.get('status_message', '')}")
        
        # Print system info
        system_info = results.get("system_info", {})
        print("\nSystem Information:")
        print(f"  Platform: {system_info.get('platform', 'unknown')}")
        print(f"  Python: {system_info.get('python_version', 'unknown')}")
        print(f"  Memory: {system_info.get('memory_available', 0):.1f} GB free / {system_info.get('memory_total', 0):.1f} GB total")
        print(f"  Disk: {system_info.get('disk_free', 0):.1f} GB free / {system_info.get('disk_total', 0):.1f} GB total")
        
        # Print component results
        components = results.get("components", {})
        
        for name, result in components.items():
            status_icon = "✅" if result.get("status", False) else "❌"
            print(f"\n{status_icon} {name.upper()}:")
            print(f"  Status: {result.get('message', 'Unknown')}")
            
            if "error" in result:
                print(f"  Error: {result['error']}")
            
            # Print component-specific details
            if name == "mcp" and "models" in result:
                models = result["models"]
                print(f"  Primary Model: {models.get('primary_model', 'unknown')}")
                print(f"  Secondary Model: {models.get('secondary_model', 'unknown')}")
            
            elif name == "memory" and "storage" in result:
                storage = result["storage"]
                print(f"  Total Memories: {storage.get('total_memories', 0)}")
                print(f"  Storage Path: {storage.get('storage_path', 'unknown')}")
            
            elif name == "owl_reasoning" and "ontology_stats" in result:
                stats = result["ontology_stats"]
                if "error" not in stats:
                    print(f"  Classes: {stats.get('classes_count', 0)}")
                    print(f"  Properties: {stats.get('properties_count', 0)}")
                    print(f"  Individuals: {stats.get('individuals_count', 0)}")
                
            elif name == "github" and "bridge_info" in result:
                bridge = result["bridge_info"]
                print(f"  Bridge Type: {bridge.get('type', 'unknown')}")
                print(f"  Default Repo: {bridge.get('default_owner', 'none')}/{bridge.get('default_repo', 'none')}")
        
        print("\n" + "="*80)


async def run_system_check(verbose: bool = True):
    """Run a system check and print results."""
    system_check = SystemCheck(verbose=verbose)
    results = await system_check.check_all()
    
    if verbose:
        await system_check.print_check_results(results)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_system_check()) 