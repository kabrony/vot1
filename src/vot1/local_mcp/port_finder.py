#!/usr/bin/env python3
"""
Port Finder Utility

This module provides functionality to find available ports on the local system.
"""

import socket
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """
    Check if a port is in use.
    
    Args:
        port: Port number to check
        host: Host to check on
        
    Returns:
        True if the port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except socket.error:
            return True

def find_available_port(start_port: int = 5678, max_attempts: int = 50, host: str = 'localhost') -> Optional[int]:
    """
    Find an available port starting from start_port.
    
    Args:
        start_port: Port to start checking from
        max_attempts: Maximum number of ports to check
        host: Host to check on
        
    Returns:
        Available port number or None if no port is available
    """
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port, host):
            return port
    
    logger.error(f"Could not find an available port after {max_attempts} attempts")
    return None

if __name__ == "__main__":
    # Basic test
    import sys
    start_port = int(sys.argv[1]) if len(sys.argv) > 1 else 5678
    port = find_available_port(start_port)
    if port:
        print(f"Available port: {port}")
    else:
        print(f"No available port found starting from {start_port}")
        sys.exit(1) 