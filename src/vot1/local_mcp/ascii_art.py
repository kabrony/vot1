#!/usr/bin/env python3
"""
ASCII Art for VOTai

This module provides ASCII art representations of the VOTai brand
to be used across the agent ecosystem.
"""

# Simple version for constrained spaces
VOTAI_SMALL = """
__     _____ _____       _ 
\\ \\   / / _ \\_   _|____ (_)
 \\ \\ / / | | || |/ _` | | |
  \\ V /| |_| || | (_| | | |
   \\_/  \\___/ |_|\\__,_|_|_|
"""

# More detailed version with tagline
VOTAI_MEDIUM = """
__     _____ _____       _   
\\ \\   / / _ \\_   _|____ (_)  
 \\ \\ / / | | || |/ _` | | |  
  \\ V /| |_| || | (_| | | |  
   \\_/  \\___/ |_|\\__,_|_|_|  
                             
 A New Dawn of a Holistic Paradigm
"""

# Large detailed version for documentation headers
VOTAI_LARGE = """
 _    __      __     _____ _____       _ 
| |   \\ \\    / /\\   / / _ \\_   _|____ (_)
| |    \\ \\  / /  \\ / / | | || |/ _` | | |
| |___  \\ \\/ / /\\ V /| |_| || | (_| | | |
|_____|  \\__/_/  \\_/  \\___/ |_|\\__,_|_|_|

       A New Dawn of a Holistic Paradigm
"""

# Minimal version for compact display
VOTAI_MINIMAL = """
V O T a i
"""

def get_votai_ascii(size="medium"):
    """
    Get the VOTai ASCII art in the specified size.
    
    Args:
        size: Size of the ASCII art ("minimal", "small", "medium", "large")
        
    Returns:
        The ASCII art as a string
    """
    if size.lower() == "minimal":
        return VOTAI_MINIMAL
    elif size.lower() == "small":
        return VOTAI_SMALL
    elif size.lower() == "large":
        return VOTAI_LARGE
    else:  # Default to medium
        return VOTAI_MEDIUM 