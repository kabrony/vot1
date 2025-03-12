"""
VOT1 Doctor Command

This module provides a command-line interface for checking the health of a VOT1 installation.
It verifies API keys, connectivity, and system requirements.
"""

import os
import sys
import platform
import argparse
import logging
import anthropic
import importlib.metadata
import requests
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vot1.doctor")

def check_python_version():
    """Check if Python version is compatible."""
    version = platform.python_version()
    major, minor, _ = map(int, version.split('.'))
    
    if major == 3 and minor >= 8:
        logger.info(f"✅ Python version {version} is compatible")
        return True
    else:
        logger.error(f"❌ Python version {version} is not compatible, need 3.8+")
        return False

def check_package_version(package_name):
    """Check the installed version of a package."""
    try:
        version = importlib.metadata.version(package_name)
        logger.info(f"✅ {package_name} version {version} is installed")
        return True
    except importlib.metadata.PackageNotFoundError:
        logger.error(f"❌ {package_name} is not installed")
        return False

def check_required_packages():
    """Check if all required packages are installed."""
    required_packages = ["anthropic", "requests", "python-dotenv", "aiohttp", "pyyaml"]
    all_installed = True
    
    for package in required_packages:
        if not check_package_version(package):
            all_installed = False
    
    return all_installed

def check_api_key(key, name, url):
    """Check if an API key is valid (basic format check)."""
    if key and len(key) > 10:
        logger.info(f"✅ {name} key found")
        return True
    else:
        logger.warning(f"❌ {name} key not found or invalid")
        logger.info(f"You can get a {name} key from: {url}")
        return False

def check_anthropic_api(api_key):
    """Test connection to Anthropic API."""
    if not api_key:
        logger.error("❌ Cannot test Anthropic API connection: No API key")
        return False
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Simple test request - list available models
        logger.info("🔄 Testing connection to Anthropic API...")
        models_response = client.models.list()
        model_ids = [model.id for model in models_response.data]
        
        if model_ids:
            logger.info(f"✅ Connected to Anthropic API. Available models: {', '.join(model_ids)}")
            
            # Check if Claude 3.7 Sonnet is available
            if any("claude-3.7-sonnet" in model_id for model_id in model_ids):
                logger.info("✅ Claude 3.7 Sonnet model is available")
            else:
                logger.warning("⚠️ Claude 3.7 Sonnet model not found in available models")
            
            return True
        else:
            logger.warning("⚠️ Connected to Anthropic API, but no models found")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to Anthropic API: {str(e)}")
        return False

def check_github_integration(token, repo, owner):
    """Test GitHub integration."""
    if not token:
        logger.info("ℹ️ GitHub integration is not configured")
        return None
    
    if not repo or not owner:
        logger.warning("⚠️ GitHub token found, but repo or owner is missing")
        return False
    
    try:
        logger.info("🔄 Testing GitHub API connection...")
        headers = {"Authorization": f"token {token}"}
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=headers
        )
        
        if response.status_code == 200:
            repo_data = response.json()
            logger.info(f"✅ Successfully connected to GitHub repo: {repo_data['full_name']}")
            logger.info(f"ℹ️ Repository info: {repo_data['description'] or 'No description'}")
            logger.info(f"ℹ️ Stars: {repo_data['stargazers_count']}, Forks: {repo_data['forks_count']}")
            return True
        else:
            error_msg = response.json().get("message", "Unknown error")
            logger.error(f"❌ GitHub API returned error: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to GitHub API: {str(e)}")
        return False

def check_perplexity_api(api_key):
    """Test Perplexity API connection."""
    if not api_key:
        logger.info("ℹ️ Perplexity API integration is not configured")
        return None
    
    try:
        logger.info("🔄 Testing Perplexity API connection...")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "query": "What is the capital of France?",
            "max_tokens": 30
        }
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            logger.info("✅ Successfully connected to Perplexity API")
            return True
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            logger.error(f"❌ Perplexity API returned error: {error_msg}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Perplexity API: {str(e)}")
        return False

def generate_report(results):
    """Generate a summary report of all checks."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "=" * 50,
        f"VOT1 HEALTH CHECK REPORT - {now}",
        "=" * 50,
        "",
        "SYSTEM",
        "------",
        f"Python: {results['python_version']}",
        f"Operating System: {platform.system()} {platform.release()}",
        f"Required Packages: {'All installed' if results['required_packages'] else 'Some missing'}",
        "",
        "API KEYS",
        "--------",
        f"Anthropic API: {'Found' if results['anthropic_key'] else 'Missing'}",
        f"Perplexity API: {'Found' if results['perplexity_key'] else 'Not configured'}",
        f"GitHub Token: {'Found' if results['github_token'] else 'Not configured'}",
        "",
        "CONNECTIVITY",
        "-----------",
        f"Anthropic API: {results['anthropic_api']}",
    ]
    
    if results['perplexity_api'] is not None:
        report.append(f"Perplexity API: {results['perplexity_api']}")
    else:
        report.append("Perplexity API: Not tested (no API key)")
    
    if results['github_api'] is not None:
        report.append(f"GitHub API: {results['github_api']}")
    else:
        report.append("GitHub API: Not tested (no token)")
    
    report.extend([
        "",
        "SUMMARY",
        "-------",
        f"VOT1 is {'ready to use' if results['ready'] else 'not fully configured'}",
        "",
        "=" * 50
    ])
    
    return "\n".join(report)

def main():
    """Run the VOT1 doctor command."""
    parser = argparse.ArgumentParser(description="Check VOT1 installation health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load environment variables
    load_dotenv()
    
    # Track all results
    results = {
        "python_version": platform.python_version(),
        "required_packages": check_required_packages(),
        "anthropic_key": False,
        "perplexity_key": False,
        "github_token": False,
        "anthropic_api": "Failed",
        "perplexity_api": None,
        "github_api": None,
        "ready": False
    }
    
    # Get API keys from environment
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPO", "")
    github_owner = os.environ.get("GITHUB_OWNER", "")
    
    # Check API keys
    results["anthropic_key"] = check_api_key(
        anthropic_key, 
        "Anthropic API", 
        "https://console.anthropic.com/"
    )
    
    results["perplexity_key"] = check_api_key(
        perplexity_key,
        "Perplexity API",
        "https://www.perplexity.ai/api"
    )
    
    results["github_token"] = check_api_key(
        github_token,
        "GitHub",
        "https://github.com/settings/tokens"
    )
    
    # Test API connections
    if results["anthropic_key"]:
        anthropic_api_result = check_anthropic_api(anthropic_key)
        results["anthropic_api"] = "Connected" if anthropic_api_result else "Failed"
    
    if results["perplexity_key"]:
        perplexity_api_result = check_perplexity_api(perplexity_key)
        results["perplexity_api"] = "Connected" if perplexity_api_result else "Failed"
    
    if results["github_token"]:
        github_api_result = check_github_integration(github_token, github_repo, github_owner)
        results["github_api"] = "Connected" if github_api_result else "Failed"
    
    # Determine if VOT1 is ready to use
    results["ready"] = (
        check_python_version() and
        results["required_packages"] and
        results["anthropic_key"] and
        results["anthropic_api"] == "Connected"
    )
    
    # Generate and print summary report
    report = generate_report(results)
    print(report)
    
    # Return exit code based on readiness
    return 0 if results["ready"] else 1

if __name__ == "__main__":
    sys.exit(main()) 