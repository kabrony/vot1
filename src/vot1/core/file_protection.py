"""
File Protection Module for VOT1

This module ensures that critical files (like .env and memory) are never deleted or modified
without proper authorization. It implements protection mechanisms and logging for file operations.
"""

import os
import logging
import json
import fnmatch
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Set
from functools import wraps

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine

logger = get_logger(__name__)

class FileProtectionSystem:
    """
    A system to protect critical files from unauthorized deletion or modification.
    """
    
    def __init__(self, config_path: str = "vot1_config.json", principles_engine: Optional[CorePrinciplesEngine] = None):
        """
        Initialize the file protection system.
        
        Args:
            config_path: Path to the configuration file
            principles_engine: Optional CorePrinciplesEngine instance
        """
        self.config_path = config_path
        self.principles_engine = principles_engine
        self.protected_paths: List[str] = []
        self.protection_active = True
        self.load_config()
        logger.info(f"File Protection System initialized with {len(self.protected_paths)} protected paths")
        
    def load_config(self) -> None:
        """Load protected paths from the configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                if 'system' in config and 'security' in config['system'] and 'protected_paths' in config['system']['security']:
                    self.protected_paths = config['system']['security']['protected_paths']
                    logger.info(f"Loaded protected paths: {self.protected_paths}")
                else:
                    # Default protected paths if not specified in config
                    self.protected_paths = ['.env', 'memory/', 'vot1_config.json']
                    logger.warning("Protected paths not found in config, using defaults")
            else:
                # Default protected paths if config doesn't exist
                self.protected_paths = ['.env', 'memory/', 'vot1_config.json']
                logger.warning(f"Config file {self.config_path} not found, using default protected paths")
        except Exception as e:
            logger.error(f"Error loading protected paths: {str(e)}")
            # Default protected paths if loading fails
            self.protected_paths = ['.env', 'memory/', 'vot1_config.json']
    
    def is_protected(self, file_path: str) -> bool:
        """
        Check if a file path is protected.
        
        Args:
            file_path: The path to check
            
        Returns:
            True if the path is protected, False otherwise
        """
        absolute_path = os.path.abspath(file_path)
        normalized_path = os.path.normpath(file_path)
        
        for protected_pattern in self.protected_paths:
            if fnmatch.fnmatch(normalized_path, protected_pattern) or \
               fnmatch.fnmatch(os.path.basename(normalized_path), protected_pattern) or \
               (protected_pattern.endswith('/') and normalized_path.startswith(protected_pattern[:-1])):
                logger.debug(f"Path {file_path} matches protected pattern {protected_pattern}")
                return True
                
        return False
    
    def verify_file_operation(self, operation: str, file_path: str, 
                             authorized: bool = False) -> Tuple[bool, str]:
        """
        Verify if a file operation is allowed.
        
        Args:
            operation: The operation being performed ('delete', 'write', 'move', etc.)
            file_path: The path of the file being operated on
            authorized: Whether the operation is pre-authorized
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        if not self.protection_active:
            return True, "Protection inactive"
            
        if authorized:
            logger.info(f"Pre-authorized {operation} operation on {file_path}")
            return True, "Operation pre-authorized"
            
        if self.is_protected(file_path):
            violation_message = f"Attempted {operation} on protected path: {file_path}"
            logger.warning(violation_message)
            
            # Use principles engine if available
            if self.principles_engine:
                action = {
                    "type": "file_operation",
                    "operation": operation,
                    "path": file_path,
                    "authorized": authorized
                }
                is_valid, reason = self.principles_engine.verify_action(action)
                if not is_valid:
                    logger.error(f"Principles violation: {reason}")
                    return False, f"Protected file operation violates principles: {reason}"
                    
            return False, f"Path {file_path} is protected and cannot be {operation}d"
            
        return True, "Operation allowed"

    def safe_delete(self, file_path: str, force: bool = False) -> Tuple[bool, str]:
        """
        Safely delete a file if it's not protected.
        
        Args:
            file_path: Path to the file to delete
            force: Whether to force deletion (requires proper authorization)
            
        Returns:
            Tuple of (success, message)
        """
        is_allowed, reason = self.verify_file_operation('delete', file_path, authorized=force)
        
        if not is_allowed:
            return False, reason
            
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    logger.info(f"Deleting directory: {file_path}")
                    # Implement directory deletion with caution
                    return False, "Directory deletion not implemented for safety"
                else:
                    logger.info(f"Deleting file: {file_path}")
                    os.remove(file_path)
                    return True, f"Successfully deleted {file_path}"
            else:
                return False, f"File {file_path} does not exist"
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {str(e)}")
            return False, f"Error: {str(e)}"
            
    def safe_write(self, file_path: str, content: str, mode: str = 'w', 
                   force: bool = False) -> Tuple[bool, str]:
        """
        Safely write to a file if it's not protected or if force=True.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            mode: File mode ('w', 'a', etc.)
            force: Whether to force write (requires proper authorization)
            
        Returns:
            Tuple of (success, message)
        """
        is_allowed, reason = self.verify_file_operation('write', file_path, authorized=force)
        
        if not is_allowed:
            return False, reason
            
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, mode) as f:
                f.write(content)
            logger.info(f"Successfully wrote to {file_path}")
            return True, f"Successfully wrote to {file_path}"
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def get_protected_paths(self) -> List[str]:
        """Return the list of protected paths."""
        return self.protected_paths
        
    def add_protected_path(self, path: str, save_to_config: bool = False) -> bool:
        """
        Add a path to the protected paths list.
        
        Args:
            path: Path pattern to protect
            save_to_config: Whether to save changes to the config file
            
        Returns:
            True if successful, False otherwise
        """
        if path not in self.protected_paths:
            self.protected_paths.append(path)
            logger.info(f"Added {path} to protected paths")
            
            if save_to_config and os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r') as f:
                        config = json.load(f)
                    
                    if 'system' not in config:
                        config['system'] = {}
                    if 'security' not in config['system']:
                        config['system']['security'] = {}
                    if 'protected_paths' not in config['system']['security']:
                        config['system']['security']['protected_paths'] = []
                        
                    config['system']['security']['protected_paths'] = self.protected_paths
                    
                    with open(self.config_path, 'w') as f:
                        json.dump(config, f, indent=4)
                    
                    logger.info(f"Updated protected paths in config file")
                    return True
                except Exception as e:
                    logger.error(f"Error updating config: {str(e)}")
                    return False
            return True
        return False

# Create a singleton instance
_protection_system = None

def get_protection_system(config_path: str = "vot1_config.json", 
                         principles_engine: Optional[CorePrinciplesEngine] = None) -> FileProtectionSystem:
    """Get the singleton instance of the FileProtectionSystem."""
    global _protection_system
    if _protection_system is None:
        _protection_system = FileProtectionSystem(config_path, principles_engine)
    return _protection_system

def protect_file_operations(func):
    """
    Decorator to protect file operations in a function.
    This can be used to wrap functions that perform file operations.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Identify file paths in args or kwargs
        # This is a simplified approach and might need customization
        file_paths = []
        for arg in args:
            if isinstance(arg, (str, Path)) and os.path.exists(str(arg)):
                file_paths.append(str(arg))
        
        for key, value in kwargs.items():
            if key in ['file', 'path', 'file_path', 'filepath', 'destination'] and \
               isinstance(value, (str, Path)) and os.path.exists(str(value)):
                file_paths.append(str(value))
        
        # Check if any file path is protected
        protection_system = get_protection_system()
        for path in file_paths:
            if protection_system.is_protected(path):
                operation = func.__name__.replace('_', ' ')
                logger.warning(f"Protected file operation attempted: {operation} on {path}")
                # Decide whether to proceed or not based on your requirements
                # For strict protection:
                # return None  # Or an appropriate error value/exception
        
        # If allowed or no protected files found, proceed with the function
        return func(*args, **kwargs)
    
    return wrapper 