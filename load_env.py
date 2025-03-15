#!/usr/bin/env python3
"""
Environment Variable Loader for Enhanced Research Agent

This module handles loading environment variables from a .env file and provides
access to them through a simple interface with default values and type conversion.
"""

import os
import logging
from typing import Optional, Dict, Any, Union, List, TypeVar, Type, cast
from pathlib import Path

# Try to import dotenv package
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Configure logger
logger = logging.getLogger("env_loader")

# Type variable for type conversion
T = TypeVar('T')

class EnvLoader:
    """
    Environment variable loader with type conversion and default values.
    """
    
    def __init__(self, env_file: Optional[str] = None, auto_load: bool = True):
        """
        Initialize the environment loader.
        
        Args:
            env_file: Path to .env file, defaults to .env in current directory
            auto_load: Whether to automatically load environment variables on initialization
        """
        self.env_file = env_file or ".env"
        self.loaded = False
        
        if auto_load:
            self.load()
    
    def load(self) -> bool:
        """
        Load environment variables from the .env file.
        
        Returns:
            True if successful, False otherwise
        """
        # Check if .env file exists
        if not Path(self.env_file).exists():
            logger.warning(f".env file not found at {self.env_file}")
            return False
        
        # Try to load environment variables
        if DOTENV_AVAILABLE:
            loaded = load_dotenv(self.env_file)
            if loaded:
                logger.info(f"Loaded environment variables from {self.env_file}")
                self.loaded = True
                return True
            else:
                logger.warning(f"Failed to load environment variables from {self.env_file}")
                return False
        else:
            logger.warning("python-dotenv not installed, using system environment variables")
            self.loaded = True  # Mark as loaded since we're using system env vars
            return True
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set
            
        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)
    
    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """
        Get an environment variable as an integer.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set or not an integer
            
        Returns:
            Environment variable value as an integer or default
        """
        value = self.get(key)
        if value is None:
            return default
        
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Environment variable {key} is not an integer: {value}")
            return default
    
    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """
        Get an environment variable as a float.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set or not a float
            
        Returns:
            Environment variable value as a float or default
        """
        value = self.get(key)
        if value is None:
            return default
        
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Environment variable {key} is not a float: {value}")
            return default
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """
        Get an environment variable as a boolean.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set
            
        Returns:
            Environment variable value as a boolean or default
        """
        value = self.get(key)
        if value is None:
            return default
        
        return value.lower() in ('true', 'yes', '1', 'y', 't')
    
    def get_list(self, key: str, default: Optional[List[str]] = None, 
                delimiter: str = ',') -> Optional[List[str]]:
        """
        Get an environment variable as a list of strings.
        
        Args:
            key: Environment variable name
            default: Default value if environment variable is not set
            delimiter: Delimiter to split the string by
            
        Returns:
            Environment variable value as a list of strings or default
        """
        value = self.get(key)
        if value is None:
            return default
        
        return [item.strip() for item in value.split(delimiter)]
    
    def get_typed(self, key: str, type_class: Type[T], default: Optional[T] = None) -> Optional[T]:
        """
        Get an environment variable with a specific type conversion.
        
        Args:
            key: Environment variable name
            type_class: Type to convert the value to
            default: Default value if environment variable is not set or conversion fails
            
        Returns:
            Environment variable value converted to the specified type or default
        """
        value = self.get(key)
        if value is None:
            return default
        
        try:
            return cast(T, type_class(value))
        except (ValueError, TypeError):
            logger.warning(f"Failed to convert environment variable {key} to {type_class.__name__}")
            return default
    
    def get_api_key(self, key: str, required: bool = False) -> Optional[str]:
        """
        Get an API key from environment variables.
        
        Args:
            key: Environment variable name
            required: Whether the API key is required
            
        Returns:
            API key or None if not set and not required
            
        Raises:
            ValueError: If the API key is required but not set
        """
        api_key = self.get(key)
        
        if required and (api_key is None or api_key == "" or 
                        api_key == "your_api_key_here" or
                        api_key.startswith("your_")):
            raise ValueError(f"Required API key {key} is not set")
        
        return api_key
    
    def get_all(self) -> Dict[str, str]:
        """
        Get all environment variables.
        
        Returns:
            Dictionary of all environment variables
        """
        return dict(os.environ)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get configuration dictionary from specific environment variables.
        
        Returns:
            Dictionary of configuration values
        """
        # API Keys
        anthropic_api_key = self.get_api_key("ANTHROPIC_API_KEY")
        perplexity_api_key = self.get_api_key("PERPLEXITY_API_KEY")
        github_token = self.get_api_key("GITHUB_TOKEN")
        composio_api_key = self.get_api_key("COMPOSIO_API_KEY")
        composio_mcp_url = self.get("COMPOSIO_MCP_URL")
        composio_connection_id = self.get("COMPOSIO_CONNECTION_ID")
        
        # System Configuration
        memory_path = self.get("MEMORY_PATH", "memory/agent")
        health_check_interval = self.get_int("HEALTH_CHECK_INTERVAL", 60)
        enable_auto_repair = self.get_bool("ENABLE_AUTO_REPAIR", True)
        enable_autonomous_mode = self.get_bool("ENABLE_AUTONOMOUS_MODE", False)
        
        # Model Configuration
        claude_model = self.get("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")
        claude_max_tokens = self.get_int("CLAUDE_MAX_TOKENS", 4096)
        claude_temperature = self.get_float("CLAUDE_TEMPERATURE", 0.7)
        
        perplexity_model = self.get("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")
        perplexity_max_tokens = self.get_int("PERPLEXITY_MAX_TOKENS", 4096)
        perplexity_temperature = self.get_float("PERPLEXITY_TEMPERATURE", 0.7)
        
        # TRILOGY BRAIN Configuration
        trilogy_brain_enabled = self.get_bool("TRILOGY_BRAIN_ENABLED", True)
        trilogy_brain_memory_path = self.get("TRILOGY_BRAIN_MEMORY_PATH", "memory/trilogy")
        trilogy_brain_consolidation_interval = self.get_int("TRILOGY_BRAIN_CONSOLIDATION_INTERVAL", 3600)
        trilogy_brain_feedback_threshold = self.get_int("TRILOGY_BRAIN_FEEDBACK_THRESHOLD", 5)
        
        # Combine all configuration
        config = {
            "api_keys": {
                "anthropic": anthropic_api_key,
                "perplexity": perplexity_api_key,
                "github": github_token,
                "composio": composio_api_key
            },
            "composio": {
                "api_key": composio_api_key,
                "mcp_url": composio_mcp_url,
                "connection_id": composio_connection_id
            },
            "system": {
                "memory_path": memory_path,
                "health_check_interval": health_check_interval,
                "enable_auto_repair": enable_auto_repair,
                "enable_autonomous_mode": enable_autonomous_mode
            },
            "models": {
                "claude": {
                    "model": claude_model,
                    "max_tokens": claude_max_tokens,
                    "temperature": claude_temperature
                },
                "perplexity": {
                    "model": perplexity_model,
                    "max_tokens": perplexity_max_tokens,
                    "temperature": perplexity_temperature
                }
            },
            "trilogy_brain": {
                "enabled": trilogy_brain_enabled,
                "memory_path": trilogy_brain_memory_path,
                "consolidation_interval": trilogy_brain_consolidation_interval,
                "feedback_threshold": trilogy_brain_feedback_threshold
            }
        }
        
        return config


# Create a global instance for easy import
env = EnvLoader()

# Convenience functions
def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable."""
    return env.get(key, default)

def get_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
    """Get an environment variable as an integer."""
    return env.get_int(key, default)

def get_float_env(key: str, default: Optional[float] = None) -> Optional[float]:
    """Get an environment variable as a float."""
    return env.get_float(key, default)

def get_bool_env(key: str, default: Optional[bool] = None) -> Optional[bool]:
    """Get an environment variable as a boolean."""
    return env.get_bool(key, default)

def get_list_env(key: str, default: Optional[List[str]] = None, 
                delimiter: str = ',') -> Optional[List[str]]:
    """Get an environment variable as a list of strings."""
    return env.get_list(key, default, delimiter)

def get_api_key(key: str, required: bool = False) -> Optional[str]:
    """Get an API key from environment variables."""
    return env.get_api_key(key, required)

def get_config() -> Dict[str, Any]:
    """Get configuration dictionary from environment variables."""
    return env.get_config()


if __name__ == "__main__":
    # Example usage when run as a script
    import json
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load environment variables
    env_loader = EnvLoader()
    
    # Get configuration
    config = env_loader.get_config()
    
    # Print configuration
    print(json.dumps(config, indent=2)) 