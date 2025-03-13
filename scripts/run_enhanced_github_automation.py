#!/usr/bin/env python3
"""
Enhanced GitHub Automation System

This script demonstrates the enhanced GitHub automation system with:
- Advanced memory management and optimization
- Real-time UI dashboard with operation tracking
- Improved webhook and workflow management
- Better error handling and performance monitoring

Utilizes Claude 3.7 Sonnet's powerful thinking capabilities for improved analysis.

Usage:
    python run_enhanced_github_automation.py --owner <github-owner> --repo <github-repo>
"""

import os
import sys
import asyncio
import logging
import argparse
import json
from pathlib import Path
import webbrowser

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.vot1.github_composio_bridge import GitHubComposioBridge
from src.vot1.memory import MemoryManager
from src.vot1.github_ui import create_dashboard
from src.vot1.vot_mcp import VotModelControlProtocol
from scripts.github_update_automation import GitHubUpdateAutomation
from scripts.github_demo import GitHubDemo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs/enhanced_github_automation.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("enhanced_github_automation")

def load_mcp_config():
    """Load MCP configuration from file or create a default one."""
    config_dir = os.path.join('src', 'vot1', 'config')
    config_file = os.path.join(config_dir, 'mcp.json')
    
    os.makedirs(config_dir, exist_ok=True)
    
    default_config = {
        "providers": {
            "github": {
                "url": "https://mcp.composio.dev/github/api"
            },
            "perplexity": {
                "url": "https://mcp.composio.dev/perplexity/api"
            }
        }
    }
    
    if not os.path.exists(config_file):
        logger.info(f"Creating default MCP config at {config_file}")
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
    else:
        logger.info(f"Found existing MCP config at {config_file}")
    
    return config_file

async def run_enhanced_automation(args):
    """Run the enhanced GitHub automation with all improvements."""
    
    # Create dashboard first for real-time operation tracking
    dashboard = create_dashboard(storage_path=os.path.join(project_root, "logs/github_operations"))
    dashboard_path = dashboard.generate_dashboard()
    logger.info(f"Dashboard initialized at: {dashboard_path}")
    
    # Open dashboard in web browser if requested
    if args.open_dashboard:
        webbrowser.open(f"file://{dashboard_path}")
        logger.info(f"Opened dashboard in web browser")
    
    # Memory optimization setup
    memory_path = os.path.join(project_root, "memory")
    os.makedirs(memory_path, exist_ok=True)
    memory_manager = MemoryManager(
        memory_path=memory_path,
        max_conversation_history=100,
        auto_cleanup_threshold=1000,
        compression_enabled=True
    )
    
    # Run memory optimization
    logger.info("Running initial memory optimization...")
    health_check = await memory_manager.check_memory_health()
    logger.info(f"Memory health check: {health_check}")
    
    if health_check["status"] != "healthy":
        logger.info("Memory needs optimization, running optimizer...")
        optimization_result = await memory_manager.optimize_memory()
        logger.info(f"Memory optimization completed: {optimization_result}")
    
    # Ensure GitHub token is available
    github_token = args.token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token is required. Set it with --token or GITHUB_TOKEN environment variable.")
        return 1
    
    # Ensure MCP config is available
    mcp_config_file = load_mcp_config()
    logger.info(f"Using MCP config from {mcp_config_file}")
    
    # Initialize GitHubUpdateAutomation with enhancements
    logger.info("Initializing Enhanced GitHubUpdateAutomation...")
    automation = GitHubUpdateAutomation(
        primary_model="claude-3-7-sonnet",
        secondary_model="claude-3-5-sonnet",
        use_extended_thinking=True,
        max_thinking_tokens=16000,  # Maximum thinking power for Claude 3.7
        memory_path=memory_path,
        github_token=github_token,
        auto_approve=args.auto_approve,
        use_composio=args.use_composio,
        use_perplexity=args.use_perplexity
    )
    
    logger.info(f"Enhanced GitHub Automation initialized")
    logger.info(f"Repository: {args.owner}/{args.repo}")
    logger.info(f"Max thinking tokens: 16,000")
    logger.info(f"Using MCP integrations: GitHub and Perplexity")
    
    # Run the GitHub Demo to showcase UI and operation tracking
    if args.run_demo:
        logger.info("Running GitHub automation demo...")
        demo = GitHubDemo(
            github_token=github_token,
            owner=args.owner,
            repo=args.repo,
            use_mcp=args.use_composio,
            mcp_url=None,  # Will use default config
            mcp_key=None   # Will use default config
        )
        
        demo_dashboard = await demo.run_demo()
        logger.info(f"Demo completed, dashboard available at: {demo_dashboard}")
    
    # Start repository analysis and update with the enhanced system
    if args.analyze:
        logger.info("Starting enhanced repository analysis and update...")
        try:
            # Set up webhook if requested
            if args.create_webhook:
                logger.info("Setting up repository webhook...")
                webhook_url = args.webhook_url or "https://example.com/github/webhook"
                webhook_result = await automation.create_webhook(
                    owner=args.owner,
                    repo=args.repo,
                    webhook_url=webhook_url,
                    events=["push", "pull_request"]
                )
                logger.info(f"Webhook setup result: {webhook_result}")
            
            # Analyze repository and generate improvement plan
            analysis_result = await automation.analyze_and_update(
                owner=args.owner,
                repo=args.repo,
                deep_analysis=args.deep_analysis,
                update_areas=args.update_areas,
                max_updates=args.max_updates
            )
            
            if analysis_result.get("success"):
                logger.info(f"Analysis and update completed successfully")
                logger.info(f"Generated {len(analysis_result.get('updates', []))} updates")
                
                for i, update in enumerate(analysis_result.get("updates", [])):
                    logger.info(f"Update {i+1}: {update.get('title')} - {update.get('type')}")
                
                logger.info("Enhanced GitHub Automation completed successfully")
                return 0
            else:
                logger.error(f"Analysis and update failed: {analysis_result.get('error')}")
                return 1
        except Exception as e:
            logger.error(f"Error in analysis and update: {str(e)}", exc_info=True)
            return 1

def main():
    """Parse arguments and run the enhanced GitHub automation."""
    parser = argparse.ArgumentParser(description="Enhanced GitHub Automation System")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--token", help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--use-composio", action="store_true", help="Use MCP Composio integration")
    parser.add_argument("--use-perplexity", action="store_true", help="Use Perplexity for web search")
    parser.add_argument("--analyze", action="store_true", help="Perform repository analysis and updates")
    parser.add_argument("--deep-analysis", action="store_true", help="Perform deep analysis")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve generated pull requests")
    parser.add_argument("--create-webhook", action="store_true", help="Create repository webhook")
    parser.add_argument("--webhook-url", help="Webhook URL to use if creating webhook")
    parser.add_argument("--run-demo", action="store_true", help="Run the GitHub automation demo")
    parser.add_argument("--open-dashboard", action="store_true", help="Open dashboard in web browser")
    parser.add_argument("--max-thinking-tokens", type=int, default=16000, help="Max thinking tokens for Claude 3.7")
    parser.add_argument("--max-updates", type=int, default=3, help="Maximum number of updates per area")
    parser.add_argument("--update-areas", nargs="+", 
                        default=["documentation", "workflows", "code_quality"],
                        help="Areas to update (documentation, workflows, code_quality, dependencies)")
    
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(run_enhanced_automation(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(130)

if __name__ == "__main__":
    main() 