#!/usr/bin/env python3
"""
VOTai Setup Script

This script helps users install and set up the VOTai repository,
including setting up the environment, installing dependencies,
and initializing the memory system.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import sys
import argparse
import subprocess
import json
import logging
import shutil
from pathlib import Path
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('setup.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
REQUIRED_PYTHON_VERSION = (3, 8)
VENV_DIR = "venv"
MEMORY_DIR = os.path.expanduser("~/.vot1/memory")
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.vot1/config")

class SetupError(Exception):
    """Base exception for setup-related errors"""
    pass

def check_python_version():
    """Check if the Python version is sufficient."""
    current_version = sys.version_info[:2]
    if current_version < REQUIRED_PYTHON_VERSION:
        raise SetupError(f"Python version {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} or higher is required. You have {current_version[0]}.{current_version[1]}.")
    logger.info(f"Python version check passed: {sys.version}")
    return True

def setup_virtual_environment(force_recreate=False):
    """Set up a virtual environment."""
    if os.path.exists(VENV_DIR) and not force_recreate:
        logger.info(f"Virtual environment already exists at {VENV_DIR}")
        return VENV_DIR
    
    if os.path.exists(VENV_DIR) and force_recreate:
        logger.info(f"Removing existing virtual environment at {VENV_DIR}")
        shutil.rmtree(VENV_DIR)
    
    try:
        logger.info(f"Creating virtual environment at {VENV_DIR}")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
        logger.info("Virtual environment created successfully")
        return VENV_DIR
    except subprocess.CalledProcessError as e:
        raise SetupError(f"Failed to create virtual environment: {e}")

def install_dependencies(venv_dir, upgrade=False):
    """Install dependencies."""
    try:
        pip_path = os.path.join(venv_dir, "bin", "pip") if os.name != "nt" else os.path.join(venv_dir, "Scripts", "pip")
        
        # Upgrade pip itself
        logger.info("Upgrading pip")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # Install dependencies from requirements.txt
        if os.path.exists("requirements.txt"):
            logger.info("Installing dependencies from requirements.txt")
            cmd = [pip_path, "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.extend(["-r", "requirements.txt"])
            subprocess.run(cmd, check=True)
        else:
            logger.warning("requirements.txt not found, skipping dependency installation")
        
        # Install the package in development mode
        logger.info("Installing the VOTai package in development mode")
        subprocess.run([pip_path, "install", "-e", "."], check=True)
        
        logger.info("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        raise SetupError(f"Failed to install dependencies: {e}")

def initialize_memory_system():
    """Initialize the memory system."""
    try:
        # Create memory directories
        os.makedirs(MEMORY_DIR, exist_ok=True)
        
        # Create subdirectories for different memory categories
        os.makedirs(os.path.join(MEMORY_DIR, "agents"), exist_ok=True)
        os.makedirs(os.path.join(MEMORY_DIR, "github"), exist_ok=True)
        os.makedirs(os.path.join(MEMORY_DIR, "conversations"), exist_ok=True)
        os.makedirs(os.path.join(MEMORY_DIR, "knowledge"), exist_ok=True)
        
        # Create a simple initialization file
        init_file = os.path.join(MEMORY_DIR, "memory_initialized.json")
        with open(init_file, "w") as f:
            json.dump({
                "initialized_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "categories": ["agents", "github", "conversations", "knowledge"]
            }, f, indent=2)
        
        logger.info(f"Memory system initialized at {MEMORY_DIR}")
    except Exception as e:
        raise SetupError(f"Failed to initialize memory system: {e}")

def setup_config():
    """Set up configuration files."""
    try:
        # Create config directory
        os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
        
        # Copy default configs if they exist
        src_config_dir = os.path.join("src", "vot1", "config")
        if os.path.exists(src_config_dir):
            for config_file in os.listdir(src_config_dir):
                if config_file.endswith(".json") or config_file.endswith(".yaml") or config_file.endswith(".yml"):
                    src_path = os.path.join(src_config_dir, config_file)
                    dest_path = os.path.join(DEFAULT_CONFIG_DIR, config_file)
                    
                    if not os.path.exists(dest_path):
                        shutil.copy2(src_path, dest_path)
                        logger.info(f"Copied config file {config_file} to {DEFAULT_CONFIG_DIR}")
                    else:
                        logger.info(f"Config file {config_file} already exists in {DEFAULT_CONFIG_DIR}, skipping")
        
        logger.info(f"Configuration set up at {DEFAULT_CONFIG_DIR}")
    except Exception as e:
        raise SetupError(f"Failed to set up configuration: {e}")

def setup_workspace(clean=False):
    """Set up the workspace."""
    try:
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs(os.path.join("logs", "github_operations"), exist_ok=True)
        
        if clean:
            # Clean the workspace by removing temporary files
            for temp_file in Path(".").glob("**/*.pyc"):
                temp_file.unlink()
            
            for pycache_dir in Path(".").glob("**/__pycache__"):
                shutil.rmtree(pycache_dir)
        
        logger.info("Workspace set up successfully")
    except Exception as e:
        raise SetupError(f"Failed to set up workspace: {e}")

def verify_installation():
    """Verify the installation."""
    try:
        # Import key modules to verify they are installed correctly
        sys.path.insert(0, ".")
        
        try:
            from src.vot1.local_mcp.bridge import LocalMCPBridge
            from src.vot1.local_mcp.development_agent import DevelopmentAgent
            from src.vot1.memory import MemoryManager
            
            logger.info("VOTai modules imported successfully")
        except ImportError as e:
            raise SetupError(f"Failed to import VOTai modules: {e}")
        
        # Try creating a memory manager to verify it works
        try:
            from src.vot1.memory import MemoryManager
            memory = MemoryManager()
            logger.info("MemoryManager initialized successfully")
        except Exception as e:
            raise SetupError(f"Failed to initialize MemoryManager: {e}")
        
        logger.info("VOTai installation verified successfully")
        return True
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

def run_integration_tests():
    """Run basic integration tests."""
    try:
        # Run pytest if it exists
        if shutil.which("pytest") is not None:
            try:
                logger.info("Running integration tests")
                subprocess.run(["pytest", "-xvs", "tests/integration"], check=True)
                logger.info("Integration tests completed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"Integration tests failed: {e}")
                return False
        else:
            logger.warning("pytest not found, skipping integration tests")
            return None
    except Exception as e:
        logger.error(f"Error running integration tests: {e}")
        return False

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Set up the VOTai repository")
    parser.add_argument("--force", action="store_true", help="Force recreation of the virtual environment")
    parser.add_argument("--clean", action="store_true", help="Clean the workspace by removing temporary files")
    parser.add_argument("--skip-venv", action="store_true", help="Skip virtual environment creation")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-memory", action="store_true", help="Skip memory system initialization")
    parser.add_argument("--skip-config", action="store_true", help="Skip configuration setup")
    parser.add_argument("--skip-tests", action="store_true", help="Skip integration tests")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade dependencies")
    args = parser.parse_args()
    
    try:
        logger.info("Starting VOTai setup")
        
        # Check Python version
        check_python_version()
        
        # Set up virtual environment
        venv_dir = None
        if not args.skip_venv:
            venv_dir = setup_virtual_environment(args.force)
        
        # Install dependencies
        if not args.skip_deps and venv_dir:
            install_dependencies(venv_dir, args.upgrade)
        
        # Set up workspace
        setup_workspace(args.clean)
        
        # Initialize memory system
        if not args.skip_memory:
            initialize_memory_system()
        
        # Set up configuration
        if not args.skip_config:
            setup_config()
        
        # Verify installation
        if verify_installation():
            logger.info("VOTai installation successful!")
        else:
            logger.warning("VOTai installation verification failed!")
        
        # Run integration tests
        if not args.skip_tests:
            run_integration_tests()
        
        logger.info("VOTai setup completed successfully!")
        
        # Print activation command
        if venv_dir:
            if os.name == "nt":
                activate_cmd = f"{venv_dir}\\Scripts\\activate"
            else:
                activate_cmd = f"source {venv_dir}/bin/activate"
            
            logger.info(f"To activate the virtual environment, run: {activate_cmd}")
        
        # Print startup commands
        logger.info("\nTo start VOTai, run the following commands:")
        logger.info("  1. Start the Local MCP Bridge server:")
        logger.info("     python -m src.vot1.local_mcp.server")
        logger.info("  2. Start the Mock GitHub Server (for local testing):")
        logger.info("     python -m src.vot1.local_mcp.mock_github_server")
        logger.info("  3. Start the Development Agent:")
        logger.info("     python -m src.vot1.local_mcp.development_agent")
        logger.info("  4. Run the GitHub workflow test:")
        logger.info("     python src/vot1/local_mcp/test_github_workflow.py")
    
    except SetupError as e:
        logger.error(f"Setup failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    # Add the 'datetime' import for the initialize_memory_system function
    from datetime import datetime
    
    sys.exit(main()) 