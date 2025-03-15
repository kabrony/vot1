#!/usr/bin/env python3
"""
Test script to verify that the VOT1 dashboard can be imported and instantiated.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dashboard_imports():
    """Test that dashboard modules can be imported."""
    try:
        from src.vot1.dashboard import server
        from src.vot1.dashboard.app import main as run_dashboard
        
        logger.info("✅ Successfully imported dashboard modules")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import dashboard modules: {e}")
        return False

def test_dashboard_files():
    """Test that all required dashboard files exist."""
    dashboard_dir = Path("src/vot1/dashboard")
    
    # Check critical files
    critical_files = [
        dashboard_dir / "app.py",
        dashboard_dir / "server.py",
        dashboard_dir / "api.py",
        dashboard_dir / "templates" / "dashboard.html",
        dashboard_dir / "static" / "js" / "three-visualization.js",
        dashboard_dir / "static" / "js" / "dashboard.js",
        dashboard_dir / "static" / "css" / "dashboard.css",
    ]
    
    missing_files = [f for f in critical_files if not f.exists()]
    
    if missing_files:
        logger.error(f"❌ Missing dashboard files: {missing_files}")
        return False
    
    logger.info("✅ All critical dashboard files exist")
    return True

def test_github_workflows():
    """Test that GitHub workflow files exist."""
    workflow_dir = Path(".github/workflows")
    
    critical_files = [
        workflow_dir / "ci.yml",
        workflow_dir / "self-improvement.yml",
    ]
    
    missing_files = [f for f in critical_files if not f.exists()]
    
    if missing_files:
        logger.error(f"❌ Missing GitHub workflow files: {missing_files}")
        return False
    
    logger.info("✅ All GitHub workflow files exist")
    return True

def run_tests():
    """Run all tests."""
    tests = [
        test_dashboard_imports,
        test_dashboard_files,
        test_github_workflows,
    ]
    
    results = [test() for test in tests]
    
    if all(results):
        logger.info("🎉 All tests passed! The VOT1 system is properly set up.")
        return True
    else:
        logger.error("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 