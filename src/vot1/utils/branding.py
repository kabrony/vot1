"""
VOTai Branding Module

This module provides branding elements for VOTai, including ASCII art logo,
color schemes, and formatting utilities for consistent visual identity.
"""

import sys
from typing import Dict, List, Optional, Union, Literal

# ANSI color codes for terminal output
COLORS = {
    "reset": "\033[0m",
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
    "bg_black": "\033[40m",
    "bg_red": "\033[41m",
    "bg_green": "\033[42m",
    "bg_yellow": "\033[43m",
    "bg_blue": "\033[44m",
    "bg_magenta": "\033[45m",
    "bg_cyan": "\033[46m",
    "bg_white": "\033[47m",
    "bold": "\033[1m",
    "underline": "\033[4m",
    "italic": "\033[3m"
}

# VOTai brand colors
BRAND_COLORS = {
    "primary": COLORS["bright_cyan"],
    "secondary": COLORS["bright_magenta"],
    "accent": COLORS["bright_yellow"],
    "success": COLORS["bright_green"],
    "warning": COLORS["bright_yellow"],
    "error": COLORS["bright_red"],
    "info": COLORS["bright_blue"],
    "neutral": COLORS["bright_white"]
}

# VOTai ASCII Art Logo (Large)
VOTAI_LOGO_LARGE = f"""{BRAND_COLORS["primary"]}
▌   ▌ ▞▀▖▀▛▘▗▜   ▗▀▚   ▝▀▘
▐  ▌  ▙▄▘ ▌ ▄▐  ▐▄▐▘    ▌  
 ▐▐   ▌   ▌ ▌▐   ▌▐    ▌   
 ▌▐   ▌   ▌ ▗▟   ▌▝▙  ▝▄▞   

▀▛▘▐▄▄▌▝▀▖▗▜    ▐   ▝▀▖▞▀▖▗▀▚
 ▌ ▌ ▐  ▗ ▄▐    ▌ ▄  ▞ ▛▀ ▐▄▐▘
 ▌ ▌ ▐  ▄ ▌▐   ▗▟ ▌  ▌ ▌  ▌▐ 
 ▘ ▐▄▄▌▝▄▞▗▟    ▌ ▐▄ ▝▄▌  ▌▝▙{COLORS["reset"]}
"""

# VOTai ASCII Art Logo (Small)
VOTAI_LOGO_SMALL = f"""{BRAND_COLORS["primary"]}
▌ ▌▞▀▖▀▛▘▗▀▚▝▀▘
▐▌▌▙▄▘ ▌ ▐▄▐▘▌ 
▝▌▐▌   ▌  ▌▐ ▌ 
 ▌▐▌   ▌  ▌▝▙▝▄▞{COLORS["reset"]}
"""

# VOTai ASCII Art Logo (Minimal)
VOTAI_LOGO_MINIMAL = f"""{BRAND_COLORS["primary"]}
V▪O▪T▪a▪i
▄▄▄▄▄▄▄▄▄{COLORS["reset"]}
"""

def get_logo(size: Literal["large", "small", "minimal"] = "small") -> str:
    """Get VOTai ASCII logo in specified size

    Args:
        size: Size of logo ("large", "small", or "minimal")

    Returns:
        ASCII art logo as string
    """
    if size == "large":
        return VOTAI_LOGO_LARGE
    elif size == "small":
        return VOTAI_LOGO_SMALL
    else:
        return VOTAI_LOGO_MINIMAL

def color_text(text: str, color: str) -> str:
    """Apply color to text

    Args:
        text: Text to colorize
        color: Color name from COLORS dict

    Returns:
        Colored text
    """
    if color not in COLORS:
        return text
    return f"{COLORS[color]}{text}{COLORS['reset']}"

def format_header(text: str, logo_size: Literal["large", "small", "minimal", "none"] = "small") -> str:
    """Format text as header with logo

    Args:
        text: Header text
        logo_size: Size of logo to include

    Returns:
        Formatted header
    """
    logo = "" if logo_size == "none" else get_logo(logo_size)
    header = f"{logo}\n{BRAND_COLORS['secondary']}{text}{COLORS['reset']}"
    return header

def format_status(status: str, message: str) -> str:
    """Format status message with appropriate color

    Args:
        status: Status type (success, warning, error, info)
        message: Status message

    Returns:
        Formatted status message
    """
    status_color = BRAND_COLORS.get(status.lower(), BRAND_COLORS["neutral"])
    return f"{status_color}[{status.upper()}]{COLORS['reset']} {message}"

def print_logo() -> None:
    """Print VOTai logo to console with standard size"""
    print(get_logo("small"))

def print_branded_message(message: str, logo_size: Literal["large", "small", "minimal", "none"] = "minimal") -> None:
    """Print a branded message with logo

    Args:
        message: Message to print
        logo_size: Size of logo to include
    """
    print(format_header(message, logo_size)) 