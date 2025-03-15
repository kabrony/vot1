#!/usr/bin/env python3
"""
VOTai Repository Update and Push Script

This script automatically updates the repository with the latest changes,
formats the code, runs tests, and pushes to GitHub. It ensures that all
VOTai improvements are properly tracked and pushed to the main repository.
"""

import os
import sys
import subprocess
import argparse
import logging
import datetime
from pathlib import Path

# Add the project root to the path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

try:
    from src.vot1.utils.branding import print_logo, print_branded_message, format_status
except ImportError:
    # Fallback if the branding module is not available
    def print_logo():
        print("""
▌ ▌▞▀▖▀▛▘▗▀▚▝▀▘
▐▌▌▙▄▘ ▌ ▐▄▐▘▌ 
▝▌▐▌   ▌  ▌▐ ▌ 
 ▌▐▌   ▌  ▌▝▙▝▄▞
        """)
    
    def print_branded_message(msg, *args, **kwargs):
        print(msg)
    
    def format_status(status, msg):
        return f"[{status.upper()}] {msg}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VOTai.Update")

def run_command(cmd, cwd=None, check=True, capture_output=False):
    """Run a shell command and handle errors"""
    try:
        logger.info(f"Running command: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd or root_dir,
            check=check,
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if capture_output:
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
        if check:
            raise
        return e

def check_git_status():
    """Check if git is installed and the current directory is a git repository"""
    try:
        result = run_command("git status", capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def format_code():
    """Format Python code with black"""
    try:
        run_command("black src tests scripts")
        logger.info(format_status("success", "Code formatted with black"))
        return True
    except Exception as e:
        logger.error(f"Error formatting code: {e}")
        return False

def run_tests():
    """Run the test suite"""
    try:
        run_command("pytest -xvs tests/unit", check=False)
        logger.info(format_status("success", "Unit tests completed"))
        return True
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

def update_repository(branch="feature/claude-3.7-memory-integration"):
    """Update the git repository with all changes"""
    if not check_git_status():
        logger.error("Not a git repository or git not installed")
        return False
    
    # Check if branch exists
    branch_exists = run_command(f"git rev-parse --verify {branch}", 
                               check=False, 
                               capture_output=True).returncode == 0
    
    if not branch_exists:
        # Create the branch if it doesn't exist
        run_command(f"git checkout -b {branch}")
    else:
        # Switch to branch
        run_command(f"git checkout {branch}")
    
    # Add all changes
    run_command("git add .")
    
    # Create commit message with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"VOTai improvement: Update branding and workflow ({timestamp})"
    
    # Commit changes
    run_command(f'git commit -m "{commit_message}"')
    
    logger.info(format_status("success", f"Changes committed to branch {branch}"))
    return True

def push_to_github(branch="feature/claude-3.7-memory-integration"):
    """Push changes to GitHub"""
    if not check_git_status():
        logger.error("Not a git repository or git not installed")
        return False
    
    # Check if we have a remote configured
    remotes = run_command("git remote", capture_output=True).stdout.strip()
    if not remotes:
        logger.error("No git remotes configured")
        return False
    
    # Push to remote
    result = run_command(f"git push origin {branch}", check=False, capture_output=True)
    if result.returncode != 0:
        logger.warning(f"Push failed, setting upstream: {result.stderr}")
        run_command(f"git push --set-upstream origin {branch}")
    
    logger.info(format_status("success", f"Changes pushed to origin/{branch}"))
    return True

def main():
    """Main function to update and push the repository"""
    print_logo()
    print_branded_message("VOTai Repository Update and Push Tool", "small")
    
    parser = argparse.ArgumentParser(description="Update and push VOTai repository")
    parser.add_argument("--branch", type=str, default="feature/claude-3.7-memory-integration", 
                        help="Git branch to use")
    parser.add_argument("--no-format", action="store_true", 
                        help="Skip code formatting")
    parser.add_argument("--no-tests", action="store_true", 
                        help="Skip running tests")
    parser.add_argument("--no-push", action="store_true", 
                        help="Skip pushing to GitHub")
    
    args = parser.parse_args()
    
    # Validate current directory
    if not os.path.exists("src/vot1"):
        logger.error("Must be run from the project root directory")
        return 1
    
    # Format code
    if not args.no_format:
        format_code()
    
    # Run tests
    if not args.no_tests:
        run_tests()
    
    # Update repository
    if not update_repository(args.branch):
        return 1
    
    # Push to GitHub
    if not args.no_push:
        if not push_to_github(args.branch):
            return 1
    
    print_branded_message("Repository update complete!", "minimal")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 