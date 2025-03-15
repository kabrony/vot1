"""
VOT1 Setup Command

This module provides a command-line interface for setting up VOT1.
It guides users through configuring required API keys and settings.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from getpass import getpass
import configparser
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vot1.setup")

def check_api_key(key, name, url):
    """Check if an API key is valid (basic format check)."""
    if key and len(key) > 10:
        logger.info(f"✅ {name} key found")
        return True
    else:
        logger.warning(f"❌ {name} key not found or invalid")
        logger.info(f"You can get a {name} key from: {url}")
        return False

def create_env_file(config):
    """Create a .env file with configuration values."""
    env_file = Path(".env")
    
    # Check if file exists already
    if env_file.exists():
        logger.info("Found existing .env file. Creating .env.new instead.")
        env_file = Path(".env.new")
    
    with open(env_file, "w") as f:
        f.write("# VOT1 Configuration\n")
        f.write(f"# Created by vot1-setup on {os.path.basename(sys.argv[0])}\n\n")
        
        # Write the API keys
        f.write("# Anthropic API Key (Required)\n")
        f.write(f"ANTHROPIC_API_KEY={config.get('api', 'anthropic_key', fallback='')}\n\n")
        
        # Write Perplexity key if available
        if config.get('api', 'perplexity_key', fallback=''):
            f.write("# Perplexity API Key (Optional but recommended for web search)\n")
            f.write(f"PERPLEXITY_API_KEY={config.get('api', 'perplexity_key')}\n\n")
        
        # Write GitHub config if available
        if config.get('github', 'token', fallback=''):
            f.write("# GitHub Integration\n")
            f.write(f"GITHUB_TOKEN={config.get('github', 'token')}\n")
            f.write(f"GITHUB_REPO={config.get('github', 'repo', fallback='')}\n")
            f.write(f"GITHUB_OWNER={config.get('github', 'owner', fallback='')}\n\n")
        
        # Write logging config
        f.write("# Logging Configuration\n")
        f.write(f"LOG_LEVEL={config.get('logging', 'level', fallback='INFO')}\n")
    
    logger.info(f"Configuration saved to {env_file}")
    if env_file.name == ".env.new":
        logger.info("To use the new configuration, rename .env.new to .env")

def main():
    """Run the VOT1 setup process."""
    parser = argparse.ArgumentParser(description="Setup VOT1 configuration")
    parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode")
    args = parser.parse_args()
    
    # Load existing .env file if present
    load_dotenv(override=True)
    
    config = configparser.ConfigParser()
    config.add_section('api')
    config.add_section('github')
    config.add_section('logging')
    
    # Print welcome message
    print("\n" + "=" * 50)
    print("Welcome to VOT1 Setup")
    print("=" * 50)
    print("This utility will help you configure VOT1.\n")
    
    # Check for existing configuration
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    perplexity_key = os.environ.get("PERPLEXITY_API_KEY", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPO", "")
    github_owner = os.environ.get("GITHUB_OWNER", "")
    
    # Set default values from environment
    config.set('api', 'anthropic_key', anthropic_key)
    config.set('api', 'perplexity_key', perplexity_key)
    config.set('github', 'token', github_token)
    config.set('github', 'repo', github_repo)
    config.set('github', 'owner', github_owner)
    config.set('logging', 'level', os.environ.get("LOG_LEVEL", "INFO"))
    
    if not args.non_interactive:
        # Anthropic API Key (required)
        print("\n1. Anthropic API Key")
        print("-" * 20)
        if check_api_key(anthropic_key, "Anthropic API", "https://console.anthropic.com/"):
            print(f"Using existing Anthropic API key: {anthropic_key[:5]}...")
            change = input("Would you like to change it? (y/N): ").lower()
            if change == 'y':
                anthropic_key = getpass("Enter your Anthropic API key: ")
                config.set('api', 'anthropic_key', anthropic_key)
        else:
            anthropic_key = getpass("Enter your Anthropic API key: ")
            config.set('api', 'anthropic_key', anthropic_key)
        
        # Perplexity API Key (optional)
        print("\n2. Perplexity API Key (optional for web search)")
        print("-" * 20)
        if perplexity_key:
            print(f"Using existing Perplexity API key: {perplexity_key[:5]}...")
            change = input("Would you like to change it? (y/N): ").lower()
            if change == 'y':
                perplexity_key = getpass("Enter your Perplexity API key (or leave empty to disable): ")
                config.set('api', 'perplexity_key', perplexity_key)
        else:
            perplexity_key = getpass("Enter your Perplexity API key (or leave empty to disable): ")
            config.set('api', 'perplexity_key', perplexity_key)
        
        # GitHub Integration (optional)
        print("\n3. GitHub Integration (optional)")
        print("-" * 20)
        use_github = False
        if github_token:
            print(f"Using existing GitHub token: {github_token[:5]}...")
            use_github = True
            change = input("Would you like to change it? (y/N): ").lower()
            if change == 'y':
                github_token = getpass("Enter your GitHub token (or leave empty to disable): ")
                config.set('github', 'token', github_token)
                use_github = bool(github_token)
        else:
            enable = input("Would you like to enable GitHub integration? (y/N): ").lower()
            if enable == 'y':
                github_token = getpass("Enter your GitHub token: ")
                config.set('github', 'token', github_token)
                use_github = bool(github_token)
        
        if use_github:
            if github_repo:
                print(f"Using existing GitHub repo: {github_repo}")
                change = input("Would you like to change it? (y/N): ").lower()
                if change == 'y':
                    github_repo = input("Enter your GitHub repository name: ")
                    config.set('github', 'repo', github_repo)
            else:
                github_repo = input("Enter your GitHub repository name: ")
                config.set('github', 'repo', github_repo)
            
            if github_owner:
                print(f"Using existing GitHub owner: {github_owner}")
                change = input("Would you like to change it? (y/N): ").lower()
                if change == 'y':
                    github_owner = input("Enter your GitHub username: ")
                    config.set('github', 'owner', github_owner)
            else:
                github_owner = input("Enter your GitHub username: ")
                config.set('github', 'owner', github_owner)
        
        # Logging Configuration
        print("\n4. Logging Configuration")
        print("-" * 20)
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        print(f"Current log level: {log_level}")
        change = input("Would you like to change the log level? (y/N): ").lower()
        if change == 'y':
            print("Available log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL")
            new_level = input("Enter log level: ").upper()
            if new_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                config.set('logging', 'level', new_level)
            else:
                print(f"Invalid log level: {new_level}. Using default: INFO")
                config.set('logging', 'level', "INFO")
    
    # Create .env file
    create_env_file(config)
    
    # Final message
    print("\n" + "=" * 50)
    print("VOT1 Setup Complete!")
    print("=" * 50)
    
    # Check if all required settings are present
    if not config.get('api', 'anthropic_key'):
        print("\n⚠️  WARNING: Anthropic API key is required but not set.")
        print("You will need to edit your .env file manually before using VOT1.")
    
    print("\nYou can now use VOT1! Run 'vot1-doctor' to verify your installation.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 