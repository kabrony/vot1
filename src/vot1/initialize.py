"""
VOTai System Initialization

This module provides the initialization functions for setting up the VOTai system,
including all components like Composio integration, Claude 3.7 Sonnet client,
memory bridge, and Perplexity integration.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple, List

try:
    # Absolute imports (for installed package)
    from vot1.utils.branding import format_status
    from vot1.utils.logging import get_logger, configure_root_logger
    from vot1.composio.client import ComposioClient
    from vot1.composio.memory_bridge import ComposioMemoryBridge
    from vot1.claude_client import ClaudeClient
    from vot1.perplexity_client import PerplexityClient
except ImportError:
    # Relative imports (for development)
    from src.vot1.utils.branding import format_status
    from src.vot1.utils.logging import get_logger, configure_root_logger
    from src.vot1.composio.client import ComposioClient
    from src.vot1.composio.memory_bridge import ComposioMemoryBridge
    from src.vot1.claude_client import ClaudeClient
    from src.vot1.perplexity_client import PerplexityClient

# Configure logger
logger = get_logger(__name__)

class VOTaiSystem:
    """
    VOTai System main class for initialization and management of all components.
    
    This class serves as a central point for initializing and accessing all
    VOTai components, making it easier to integrate the system into applications.
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        log_level: str = "info",
        log_dir: Optional[str] = None,
        enable_all_components: bool = True
    ):
        """
        Initialize the VOTai system.
        
        Args:
            config_path: Path to configuration file (if None, uses environment variables)
            log_level: Logging level (debug, info, warning, error)
            log_dir: Directory for log files (if None, logs to console only)
            enable_all_components: Whether to initialize all components or allow lazy loading
        """
        self.config = self._load_config(config_path)
        self.components = {}
        
        # Configure logging
        self.logger = configure_root_logger(
            level=log_level,
            log_dir=log_dir
        )
        
        # Initialize core components if requested
        if enable_all_components:
            asyncio.run(self.initialize_all_components())
        
        logger.info(format_status("success", "VOTai system initialized"))
    
    async def initialize_all_components(self) -> None:
        """Initialize all system components"""
        # Initialize memory bridge first as it's used by other components
        await self.get_memory_bridge()
        
        # Initialize other components
        await self.get_claude_client()
        await self.get_composio_client()
        await self.get_perplexity_client()
        
        logger.info(format_status("success", "All VOTai components initialized"))
    
    async def get_memory_bridge(self) -> ComposioMemoryBridge:
        """
        Get or initialize the memory bridge.
        
        Returns:
            Initialized memory bridge
        """
        if "memory_bridge" not in self.components:
            logger.info(format_status("info", "Initializing memory bridge..."))
            
            # Initialize memory bridge
            self.components["memory_bridge"] = ComposioMemoryBridge(
                max_memory_items=self.config.get("memory", {}).get("max_items", 1000),
                max_tokens_per_memory=self.config.get("memory", {}).get("max_tokens_per_memory", 500),
                enable_hybrid_thinking=self.config.get("memory", {}).get("enable_hybrid_thinking", True),
                streaming_buffer_size=self.config.get("memory", {}).get("streaming_buffer_size", 100)
            )
            
            logger.info(format_status("success", "Memory bridge initialized"))
        
        return self.components["memory_bridge"]
    
    async def get_claude_client(self) -> ClaudeClient:
        """
        Get or initialize the Claude client.
        
        Returns:
            Initialized Claude client
        """
        if "claude_client" not in self.components:
            logger.info(format_status("info", "Initializing Claude client..."))
            
            # Get memory bridge (initializing if needed)
            memory_bridge = await self.get_memory_bridge()
            
            # Get API key from config or environment
            api_key = self.config.get("claude", {}).get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
            
            # Initialize Claude client
            self.components["claude_client"] = ClaudeClient(
                api_key=api_key,
                model=self.config.get("claude", {}).get("model"),
                max_tokens=self.config.get("claude", {}).get("max_tokens"),
                timeout=self.config.get("claude", {}).get("timeout", 120),
                max_retries=self.config.get("claude", {}).get("max_retries", 3),
                default_system_prompt=self.config.get("claude", {}).get("default_system_prompt"),
                memory_bridge=memory_bridge
            )
            
            # Set Claude client in memory bridge for hybrid thinking
            memory_bridge.claude_client = self.components["claude_client"]
            
            logger.info(format_status("success", "Claude client initialized"))
        
        return self.components["claude_client"]
    
    async def get_composio_client(self) -> ComposioClient:
        """
        Get or initialize the Composio client.
        
        Returns:
            Initialized Composio client
        """
        if "composio_client" not in self.components:
            logger.info(format_status("info", "Initializing Composio client..."))
            
            # Get memory bridge (initializing if needed)
            memory_bridge = await self.get_memory_bridge()
            
            # Get API key and integration ID from config or environment
            api_key = self.config.get("composio", {}).get("api_key") or os.environ.get("COMPOSIO_API_KEY")
            integration_id = self.config.get("composio", {}).get("integration_id") or os.environ.get("COMPOSIO_INTEGRATION_ID")
            
            # Initialize Composio client
            self.components["composio_client"] = ComposioClient(
                api_key=api_key,
                integration_id=integration_id,
                endpoint=self.config.get("composio", {}).get("endpoint"),
                timeout=self.config.get("composio", {}).get("timeout", 60),
                max_retries=self.config.get("composio", {}).get("max_retries", 3),
                max_concurrent_executions=self.config.get("composio", {}).get("max_concurrent_executions", 5),
                cache_ttl=self.config.get("composio", {}).get("cache_ttl", 300),
                memory_bridge=memory_bridge
            )
            
            logger.info(format_status("success", "Composio client initialized"))
        
        return self.components["composio_client"]
    
    async def get_perplexity_client(self) -> PerplexityClient:
        """
        Get or initialize the Perplexity client.
        
        Returns:
            Initialized Perplexity client
        """
        if "perplexity_client" not in self.components:
            logger.info(format_status("info", "Initializing Perplexity client..."))
            
            # Get memory bridge (initializing if needed)
            memory_bridge = await self.get_memory_bridge()
            
            # Get API key from config or environment
            api_key = self.config.get("perplexity", {}).get("api_key") or os.environ.get("PERPLEXITY_API_KEY")
            
            # Initialize Perplexity client
            self.components["perplexity_client"] = PerplexityClient(
                api_key=api_key,
                model_name=self.config.get("perplexity", {}).get("model_name"),
                timeout=self.config.get("perplexity", {}).get("timeout", 120),
                max_retries=self.config.get("perplexity", {}).get("max_retries", 3),
                memory_bridge=memory_bridge
            )
            
            # Set Perplexity client in memory bridge for research capabilities
            memory_bridge.perplexity_client = self.components["perplexity_client"]
            
            logger.info(format_status("success", "Perplexity client initialized"))
        
        return self.components["perplexity_client"]
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or environment variables.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        config = {
            "memory": {
                "max_items": 1000,
                "max_tokens_per_memory": 500,
                "enable_hybrid_thinking": True,
                "streaming_buffer_size": 100
            },
            "claude": {
                "model": "claude-3-7-sonnet-20240708",
                "max_tokens": 15000,
                "timeout": 120,
                "max_retries": 3
            },
            "composio": {
                "timeout": 60,
                "max_retries": 3,
                "max_concurrent_executions": 5,
                "cache_ttl": 300
            },
            "perplexity": {
                "model_name": "llama-3-sonar-large-online",
                "timeout": 120,
                "max_retries": 3
            }
        }
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                
                # Merge file config with default config
                config = self._merge_configs(config, file_config)
                logger.info(format_status("success", f"Loaded configuration from {config_path}"))
            except Exception as e:
                logger.error(format_status("error", f"Error loading configuration from {config_path}: {str(e)}"))
        else:
            logger.info(format_status("info", "Using default configuration with environment variables"))
        
        return config
    
    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries, with override_config taking precedence.
        
        Args:
            base_config: Base configuration
            override_config: Override configuration
            
        Returns:
            Merged configuration dictionary
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override with new value
                result[key] = value
        
        return result
    
    def get_component_status(self) -> List[Dict[str, str]]:
        """
        Get status information for all initialized components.
        
        Returns:
            List of component status dictionaries
        """
        status = []
        
        # Memory bridge status
        if "memory_bridge" in self.components:
            memory_bridge = self.components["memory_bridge"]
            memory_stats = memory_bridge.get_stats()
            status.append({
                "name": "Memory Bridge",
                "status": "active",
                "message": f"Memories: {memory_stats.get('total_memories', 0)}, Hybrid thinking calls: {memory_stats.get('hybrid_thinking_calls', 0)}"
            })
        else:
            status.append({
                "name": "Memory Bridge",
                "status": "inactive",
                "message": "Not initialized"
            })
        
        # Claude client status
        if "claude_client" in self.components:
            claude_client = self.components["claude_client"]
            claude_stats = claude_client.get_stats()
            status.append({
                "name": "Claude Client",
                "status": "active" if claude_client.api_key else "limited",
                "message": f"Model: {claude_client.model}, Requests: {claude_stats.get('requests', 0)}, Tools: {len(claude_client.registered_tools)}"
            })
        else:
            status.append({
                "name": "Claude Client",
                "status": "inactive",
                "message": "Not initialized"
            })
        
        # Composio client status
        if "composio_client" in self.components:
            composio_client = self.components["composio_client"]
            composio_stats = composio_client.get_stats()
            status.append({
                "name": "Composio Client",
                "status": "active" if composio_client.api_key else "limited",
                "message": f"Tool executions: {composio_stats.get('tool_executions', 0)}, Success rate: {composio_stats.get('success_rate', 0):.2f}"
            })
        else:
            status.append({
                "name": "Composio Client",
                "status": "inactive",
                "message": "Not initialized"
            })
        
        # Perplexity client status
        if "perplexity_client" in self.components:
            perplexity_client = self.components["perplexity_client"]
            perplexity_stats = perplexity_client.get_stats()
            status.append({
                "name": "Perplexity Client",
                "status": "active" if perplexity_client.api_key else "limited",
                "message": f"Model: {perplexity_client.model_name}, Queries: {perplexity_stats.get('queries', 0)}, Research sessions: {perplexity_stats.get('research_sessions', 0)}"
            })
        else:
            status.append({
                "name": "Perplexity Client",
                "status": "inactive",
                "message": "Not initialized"
            })
        
        return status

# Singleton instance
_system_instance = None

def get_system(
    config_path: Optional[str] = None,
    log_level: str = "info",
    log_dir: Optional[str] = None,
    enable_all_components: bool = False
) -> VOTaiSystem:
    """
    Get or initialize the VOTai system singleton instance.
    
    Args:
        config_path: Path to configuration file
        log_level: Logging level
        log_dir: Directory for log files
        enable_all_components: Whether to initialize all components or allow lazy loading
        
    Returns:
        VOTai system instance
    """
    global _system_instance
    
    if _system_instance is None:
        _system_instance = VOTaiSystem(
            config_path=config_path,
            log_level=log_level,
            log_dir=log_dir,
            enable_all_components=enable_all_components
        )
    
    return _system_instance

async def initialize_system(
    config_path: Optional[str] = None,
    log_level: str = "info",
    log_dir: Optional[str] = None
) -> VOTaiSystem:
    """
    Initialize the VOTai system with all components.
    
    This is a convenience function for asynchronous contexts.
    
    Args:
        config_path: Path to configuration file
        log_level: Logging level
        log_dir: Directory for log files
        
    Returns:
        Initialized VOTai system instance
    """
    system = get_system(
        config_path=config_path,
        log_level=log_level,
        log_dir=log_dir,
        enable_all_components=False
    )
    
    # Initialize all components
    await system.initialize_all_components()
    
    return system

# Direct initialization when module is run as script
if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Initialize VOTai system")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", default="info", help="Logging level (debug, info, warning, error)")
    parser.add_argument("--log-dir", help="Directory for log files")
    args = parser.parse_args()
    
    # Initialize system
    system = asyncio.run(initialize_system(
        config_path=args.config,
        log_level=args.log_level,
        log_dir=args.log_dir
    ))
    
    # Print status
    from vot1.utils.branding import format_status_table
    status = system.get_component_status()
    print("\nVOTai System Status:")
    print(format_status_table(status)) 