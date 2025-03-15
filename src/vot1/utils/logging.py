"""
VOTai Logging Utilities

This module provides a standardized logging setup for the VOTai system,
ensuring consistent log formatting and centralized configuration.
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union

try:
    # Try to import the branding module
    from vot1.utils.branding import format_status
except ImportError:
    # Fall back to relative import for development
    try:
        from src.vot1.utils.branding import format_status
    except ImportError:
        # Define a simple function if branding module is not available
        def format_status(status_type: str, message: str) -> str:
            return f"[{status_type.upper()}] {message}"

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Mapping from string log levels to logging constants
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

class VOTaiLogFormatter(logging.Formatter):
    """Custom formatter for VOTai logs with color support and branding"""
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        validate: bool = True,
        use_colors: bool = True
    ):
        """
        Initialize the formatter.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
            style: Style of the format string (%, {, or $)
            validate: Whether to validate the format string
            use_colors: Whether to use colors in the output
        """
        super().__init__(fmt or DEFAULT_LOG_FORMAT, datefmt or DEFAULT_DATE_FORMAT, style, validate)
        self.use_colors = use_colors and sys.stdout.isatty()
        
        # ANSI color codes
        self.colors = {
            "reset": "\033[0m",
            "debug": "\033[36m",    # Cyan
            "info": "\033[32m",     # Green
            "warning": "\033[33m",  # Yellow
            "error": "\033[31m",    # Red
            "critical": "\033[41m", # Red background
            "bold": "\033[1m",
            "name": "\033[35m"      # Magenta for logger name
        } if use_colors else {k: "" for k in ["reset", "debug", "info", "warning", "error", "critical", "bold", "name"]}
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors and branding.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Make a copy of the record to avoid modifying the original
        record_copy = logging.makeLogRecord(record.__dict__)
        
        # Apply colors to level name if enabled
        if self.use_colors:
            levelname = record_copy.levelname.lower()
            color = self.colors.get(levelname, self.colors["reset"])
            record_copy.levelname = f"{color}{record_copy.levelname}{self.colors['reset']}"
            
            # Color the logger name
            record_copy.name = f"{self.colors['name']}{record_copy.name}{self.colors['reset']}"
        
        # Format with base formatter
        formatted_message = super().format(record_copy)
        
        return formatted_message

def get_logger(
    name: str,
    level: Optional[Union[str, int]] = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    use_colors: bool = True,
    propagate: bool = False
) -> logging.Logger:
    """
    Get a configured logger with the VOTai styling.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (debug, info, warning, error, critical)
        log_file: Optional file path to write logs to
        format_string: Custom log format string
        date_format: Custom date format string
        use_colors: Whether to use colors in console output
        propagate: Whether to propagate logs to parent loggers
        
    Returns:
        Configured logger instance
    """
    # Convert string level to logging constant if needed
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.lower(), DEFAULT_LOG_LEVEL)
    elif level is None:
        # Check for environment variable, default to INFO
        env_level = os.environ.get("VOTAI_LOG_LEVEL", "info").lower()
        level = LOG_LEVELS.get(env_level, DEFAULT_LOG_LEVEL)
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been configured yet
    if not logger.handlers:
        logger.setLevel(level)
        logger.propagate = propagate
        
        # Use the VOTai formatter
        formatter = VOTaiLogFormatter(
            fmt=format_string or DEFAULT_LOG_FORMAT,
            datefmt=date_format or DEFAULT_DATE_FORMAT,
            use_colors=use_colors
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if requested
        if log_file:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                
                # Create file handler (no colors in file)
                file_formatter = VOTaiLogFormatter(
                    fmt=format_string or DEFAULT_LOG_FORMAT,
                    datefmt=date_format or DEFAULT_DATE_FORMAT,
                    use_colors=False
                )
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                # Fall back to console only and log the error
                console_handler.setLevel(logging.WARNING)
                logger.warning(format_status("warning", f"Failed to set up log file '{log_file}': {str(e)}"))
    
    return logger

def configure_root_logger(
    level: Optional[Union[str, int]] = None,
    log_dir: Optional[str] = None,
    log_filename: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    use_colors: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the entire application.
    
    Args:
        level: Log level
        log_dir: Directory to store log files
        log_filename: Name of the log file (defaults to votai_{timestamp}.log)
        format_string: Custom log format string
        date_format: Custom date format string
        use_colors: Whether to use colors in console output
        
    Returns:
        Configured root logger
    """
    # Generate default log filename if needed
    if log_dir and not log_filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"votai_{timestamp}.log"
    
    # Construct full log path if directory is provided
    log_file = None
    if log_dir:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir_path / log_filename)
    
    # Configure root logger
    return get_logger(
        name="votai",
        level=level,
        log_file=log_file,
        format_string=format_string,
        date_format=date_format,
        use_colors=use_colors,
        propagate=False
    )

def log_exception(logger: logging.Logger, exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception with context information.
    
    Args:
        logger: Logger to use
        exception: Exception to log
        context: Additional context information
    """
    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join(f"{k}={v}" for k, v in context.items())
    
    logger.exception(format_status("error", f"{exception.__class__.__name__}: {str(exception)}{context_str}"))

def log_method_call(
    logger: logging.Logger,
    method_name: str,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
    level: str = "debug"
) -> None:
    """
    Log a method call with its arguments.
    
    Args:
        logger: Logger to use
        method_name: Name of the method being called
        args: Positional arguments
        kwargs: Keyword arguments
        level: Log level to use
    """
    args_str = ""
    if args:
        args_str = ", ".join(repr(a) for a in args)
    
    kwargs_str = ""
    if kwargs:
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
    
    if args_str and kwargs_str:
        params = f"{args_str}, {kwargs_str}"
    elif args_str:
        params = args_str
    else:
        params = kwargs_str
    
    log_func = getattr(logger, level.lower())
    log_func(f"Call: {method_name}({params})")

def get_memory_handler(memory_bridge: Any, level: int = logging.INFO) -> logging.Handler:
    """
    Create a logging handler that sends logs to the memory bridge.
    
    Args:
        memory_bridge: Memory bridge instance
        level: Minimum log level to send to memory
        
    Returns:
        Handler that sends logs to memory
    """
    class MemoryHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                # Format the log message
                msg = self.format(record)
                
                # Determine memory type based on log level
                if record.levelno >= logging.ERROR:
                    memory_type = "error"
                elif record.levelno >= logging.WARNING:
                    memory_type = "warning"
                else:
                    memory_type = "log"
                
                # Store in memory (async-compatible)
                import asyncio
                if asyncio.iscoroutinefunction(memory_bridge.store_memory):
                    # Create task to store memory
                    loop = asyncio.get_event_loop() if asyncio.get_event_loop_policy().get_event_loop().is_running() else asyncio.new_event_loop()
                    loop.create_task(memory_bridge.store_memory(
                        content=msg,
                        memory_type=memory_type,
                        metadata={
                            "logger": record.name,
                            "level": record.levelname,
                            "function": record.funcName,
                            "line": record.lineno,
                        }
                    ))
                else:
                    # Synchronous storage
                    memory_bridge.store_memory(
                        content=msg,
                        memory_type=memory_type,
                        metadata={
                            "logger": record.name,
                            "level": record.levelname,
                            "function": record.funcName,
                            "line": record.lineno,
                        }
                    )
            except Exception as e:
                # Silently fail since we can't log the error without causing a loop
                pass
    
    # Create and configure the handler
    handler = MemoryHandler()
    handler.setLevel(level)
    handler.setFormatter(VOTaiLogFormatter(use_colors=False))
    
    return handler

def add_memory_handler(logger: logging.Logger, memory_bridge: Any, level: int = logging.INFO) -> None:
    """
    Add a memory handler to the given logger.
    
    Args:
        logger: Logger to add the handler to
        memory_bridge: Memory bridge instance
        level: Minimum log level to send to memory
    """
    handler = get_memory_handler(memory_bridge, level)
    logger.addHandler(handler) 