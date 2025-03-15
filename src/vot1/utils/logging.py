"""
Logging utilities for TRILOGY BRAIN

This module provides logging configuration and utilities for the TRILOGY BRAIN system.
"""

import os
import logging
import sys
from typing import Optional
from datetime import datetime

# Default logging level
DEFAULT_LOG_LEVEL = logging.INFO

def configure_logging(log_level: Optional[int] = None):
    """
    Configure the logging system.
    
    Args:
        log_level: Logging level to use, or None to use environment variable or default
    """
    # Determine log level
    if log_level is None:
        level_str = os.environ.get("VOT1_LOG_LEVEL", "INFO")
        log_level = getattr(logging, level_str, DEFAULT_LOG_LEVEL)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with the specified name and level.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatter to console handler
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger 