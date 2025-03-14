#!/usr/bin/env python3
"""
GitHub Update Automation Runner with Claude 3.7 Maximum Thinking

This script provides a convenient way to run the GitHub Update Automation tool
with sensible defaults and integration with the VOT1 dashboard.

It leverages Claude 3.7 Sonnet's maximum thinking capabilities (16,000 tokens)
and integrates with MCP for GitHub and Perplexity web search.
"""

import os
import sys
import argparse
import asyncio
import json
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.github_update_automation import GitHubUpdateAutomation
from src.vot1.memory import MemoryManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'github_automation.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Run the GitHub Update Automation with Claude 3.7 Maximum Thinking."""
    parser = argparse.ArgumentParser(description="GitHub Update Automation Runner with Claude 3.7 Maximum Thinking")
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--repos-file", help="JSON file containing multiple repositories to update")
    parser.add_argument("--output-file", help="JSON file to write results to")
    parser.add_argument("--deep-analysis", action="store_true", default=True, help="Perform deep analysis with the primary model (default: enabled)")
    parser.add_argument("--no-deep-analysis", action="store_false", dest="deep_analysis", help="Disable deep analysis")
    parser.add_argument("--update-areas", nargs='+', choices=["documentation", "workflows", "dependencies", "code_quality"], 
                        default=["documentation", "workflows", "dependencies", "code_quality"], 
                        help="Areas to update")
    parser.add_argument("--max-updates", type=int, default=5, help="Maximum number of updates per repository")
    parser.add_argument("--memory-path", default="./memory", help="Path to memory storage")
    parser.add_argument("--github-token", help="GitHub API token (can also be set via GITHUB_TOKEN env var)")
    parser.add_argument("--composio-api-key", help="Composio API key (can also be set via COMPOSIO_API_KEY env var)")
    parser.add_argument("--use-composio", action="store_true", default=True, help="Use Composio integration for GitHub operations (default: enabled)")
    parser.add_argument("--no-composio", action="store_false", dest="use_composio", help="Do not use Composio integration for GitHub operations")
    parser.add_argument("--use-perplexity", action="store_true", default=True, help="Use Perplexity for web search (default: enabled)")
    parser.add_argument("--no-perplexity", action="store_false", dest="use_perplexity", help="Do not use Perplexity for web search")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve pull requests (use with caution)")
    parser.add_argument("--primary-model", default="anthropic/claude-3-7-sonnet-20240620", help="Primary model to use for analysis")
    parser.add_argument("--secondary-model", default="anthropic/claude-3-5-sonnet-20240620", help="Secondary model to use for faster operations")
    parser.add_argument("--max-thinking-tokens", type=int, default=16000, help="Maximum tokens to use for thinking process (default: 16000)")
    parser.add_argument("--disable-extended-thinking", action="store_false", dest="use_extended_thinking", default=True, help="Disable extended thinking process")
    
    args = parser.parse_args()
    
    # Validate arguments
    if (args.owner and args.repo) and args.repos_file:
        parser.error("Please provide either --owner and --repo OR --repos-file, not both")
    
    if not ((args.owner and args.repo) or args.repos_file):
        parser.error("Please provide either --owner and --repo OR --repos-file")
    
    # Check for GitHub token
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GitHub token is required. Set it with --github-token or GITHUB_TOKEN environment variable.")
        return 1
    
    # Log configuration
    logger.info(f"GitHub Update Automation with Claude 3.7 Maximum Thinking")
    logger.info(f"Primary model: {args.primary_model}")
    logger.info(f"Max thinking tokens: {args.max_thinking_tokens}")
    logger.info(f"Deep analysis: {'Enabled' if args.deep_analysis else 'Disabled'}")
    logger.info(f"Using MCP GitHub: {'Enabled' if args.use_composio else 'Disabled'}")
    logger.info(f"Using Perplexity: {'Enabled' if args.use_perplexity else 'Disabled'}")
    
    # Initialize GitHubUpdateAutomation
    automation = GitHubUpdateAutomation(
        primary_model=args.primary_model,
        secondary_model=args.secondary_model,
        use_extended_thinking=args.use_extended_thinking,
        max_thinking_tokens=args.max_thinking_tokens,
        memory_path=args.memory_path,
        github_token=github_token,
        composio_api_key=args.composio_api_key,
        auto_approve=args.auto_approve,
        use_composio=args.use_composio,
        use_perplexity=args.use_perplexity
    )
    
    results = []
    
    if args.owner and args.repo:
        # Process single repository
        logger.info(f"Processing repository: {args.owner}/{args.repo}")
        result = await automation.analyze_and_update(
            owner=args.owner,
            repo=args.repo,
            update_areas=args.update_areas,
            deep_analysis=args.deep_analysis,
            max_updates=args.max_updates
        )
        results.append({
            "owner": args.owner,
            "repo": args.repo,
            "result": result
        })
    else:
        # Process multiple repositories from file
        with open(args.repos_file, "r") as f:
            repos = json.load(f)
            
        for repo_info in repos:
            owner = repo_info.get("owner")
            repo = repo_info.get("repo")
            if not owner or not repo:
                logger.warning(f"Skipping invalid repository entry: {repo_info}")
                continue
                
            logger.info(f"Processing repository: {owner}/{repo}")
            result = await automation.analyze_and_update(
                owner=owner,
                repo=repo,
                update_areas=args.update_areas,
                deep_analysis=args.deep_analysis,
                max_updates=args.max_updates
            )
            results.append({
                "owner": owner,
                "repo": repo,
                "result": result
            })
    
    # Write results to output file if provided
    if args.output_file:
        with open(args.output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output_file}")
    else:
        logger.info("Results summary:")
        for result in results:
            logger.info(f"{result['owner']}/{result['repo']}: {len(result['result'].get('updates', []))} updates created")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 