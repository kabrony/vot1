"""
VOTai Branding Utilities

This module provides branding-related utility functions to maintain
consistent visual identity and messaging across the VOTai system.
"""

import os
import datetime
from typing import Dict, Any, Optional, List, Union

# VOTai branding constants
BRAND_NAME = "VOTai"
BRAND_VERSION = "2025.1"
BRAND_COLOR_PRIMARY = "#6E56CF"  # Main brand color
BRAND_COLOR_SECONDARY = "#4DC0B5"  # Secondary brand color
BRAND_COLOR_ACCENT = "#F6AD55"  # Accent color

# Status colors
STATUS_COLORS = {
    "success": "#10B981",  # Green
    "error": "#EF4444",    # Red
    "warning": "#F59E0B",  # Amber
    "info": "#3B82F6",     # Blue
    "debug": "#9CA3AF",    # Gray
}

# Unicode symbols for status indicators
STATUS_SYMBOLS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "info": "ℹ",
    "debug": "⚙",
    "loading": "⟳",
    "pending": "…",
}

def format_status(status_type: str, message: str) -> str:
    """
    Format a status message with appropriate styling.
    
    Args:
        status_type: Type of status (success, error, warning, info, debug)
        message: The message to format
        
    Returns:
        Formatted status message with symbol
    """
    symbol = STATUS_SYMBOLS.get(status_type, "")
    return f"{symbol} {message}"

def get_branded_header(title: str, width: int = 80) -> str:
    """
    Generate a branded header with the given title.
    
    Args:
        title: The title to display in the header
        width: Width of the header in characters
        
    Returns:
        Branded header string
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"{'=' * width}\n"
    header += f"{BRAND_NAME} v{BRAND_VERSION} | {title}\n"
    header += f"Generated: {now}\n"
    header += f"{'-' * width}\n"
    
    return header

def get_branded_footer(width: int = 80) -> str:
    """
    Generate a branded footer.
    
    Args:
        width: Width of the footer in characters
        
    Returns:
        Branded footer string
    """
    return f"{'-' * width}\n© {datetime.datetime.now().year} {BRAND_NAME} | Powered by VOTai\n{'=' * width}"

def format_result_block(title: str, content: str, status: str = "info") -> str:
    """
    Format a result block with branded styling.
    
    Args:
        title: Block title
        content: Block content
        status: Status type for styling (success, error, warning, info)
        
    Returns:
        Formatted result block
    """
    symbol = STATUS_SYMBOLS.get(status, "")
    separator = "-" * 50
    
    return f"{symbol} {title}\n{separator}\n{content}\n{separator}\n"

def format_tool_result(tool_name: str, result: Dict[str, Any], success: bool = True) -> str:
    """
    Format the result of a tool execution with branded styling.
    
    Args:
        tool_name: Name of the tool
        result: Result data dictionary
        success: Whether the execution was successful
        
    Returns:
        Formatted tool result string
    """
    status = "success" if success else "error"
    symbol = STATUS_SYMBOLS.get(status, "")
    
    header = f"{symbol} {tool_name} Result:"
    if not success:
        return f"{header}\nError: {result.get('error', 'Unknown error')}"
    
    content = str(result.get('data', ''))
    if len(content) > 1000:
        content = content[:997] + "..."
    
    return f"{header}\n{content}"

def format_memory_entry(
    content: str,
    memory_type: str,
    timestamp: Optional[Union[float, str]] = None,
    truncate: bool = True,
    max_length: int = 200
) -> str:
    """
    Format a memory entry with branded styling.
    
    Args:
        content: Memory content
        memory_type: Type of memory
        timestamp: Timestamp of the memory
        truncate: Whether to truncate long content
        max_length: Maximum length before truncation
        
    Returns:
        Formatted memory entry
    """
    if timestamp is None:
        timestamp = datetime.datetime.now()
        
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        
    if isinstance(timestamp, datetime.datetime):
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        timestamp_str = str(timestamp)
    
    if truncate and len(content) > max_length:
        content = content[:max_length-3] + "..."
    
    type_symbol = {
        "observation": "👁️",
        "thought": "💭",
        "action": "🔄",
        "tool_execution": "🔧",
        "query": "❓",
        "response": "💬",
    }.get(memory_type, "📝")
    
    return f"{type_symbol} [{timestamp_str}] ({memory_type}): {content}"

def format_status_table(statuses: List[Dict[str, Any]]) -> str:
    """
    Format a table of statuses with branded styling.
    
    Args:
        statuses: List of status dictionaries with 'name', 'status', and 'message' keys
        
    Returns:
        Formatted status table
    """
    if not statuses:
        return "No status information available."
    
    # Find the maximum length of each column
    name_width = max(len(status["name"]) for status in statuses)
    status_width = max(len(status["status"]) for status in statuses)
    
    # Create header
    header = f"{'Component':<{name_width+2}} | {'Status':<{status_width+2}} | Message"
    separator = f"{'-' * (name_width+2)}-+-{'-' * (status_width+2)}-+{'-' * 30}"
    
    # Create rows
    rows = []
    for status in statuses:
        symbol = STATUS_SYMBOLS.get(status["status"].lower(), "")
        rows.append(
            f"{status['name']:<{name_width+2}} | "
            f"{symbol} {status['status']:<{status_width}} | "
            f"{status['message']}"
        )
    
    # Combine all parts
    return f"{header}\n{separator}\n" + "\n".join(rows)

def get_theme_colors() -> Dict[str, str]:
    """
    Get all theme colors for web interfaces.
    
    Returns:
        Dictionary of color variables for CSS
    """
    return {
        "--color-primary": BRAND_COLOR_PRIMARY,
        "--color-secondary": BRAND_COLOR_SECONDARY,
        "--color-accent": BRAND_COLOR_ACCENT,
        "--color-success": STATUS_COLORS["success"],
        "--color-error": STATUS_COLORS["error"],
        "--color-warning": STATUS_COLORS["warning"],
        "--color-info": STATUS_COLORS["info"],
        "--color-debug": STATUS_COLORS["debug"],
        "--color-background": "#F9FAFB",
        "--color-surface": "#FFFFFF",
        "--color-text": "#1F2937",
        "--color-text-secondary": "#4B5563",
        "--color-border": "#E5E7EB",
    }

def generate_css_theme() -> str:
    """
    Generate CSS variables for the VOTai theme.
    
    Returns:
        CSS variables string
    """
    theme = get_theme_colors()
    css = ":root {\n"
    
    for name, color in theme.items():
        css += f"  {name}: {color};\n"
    
    css += "}"
    return css