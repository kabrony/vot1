#!/usr/bin/env python3
"""
VOT1 Self-Improvement Runner

This script provides a convenient interface for running the VOT1 self-improvement
workflow. It allows users to target specific components for improvement, with
a focus on enhancing the THREE.js visualization with a cyberpunk aesthetic.

Usage:
    python scripts/run_self_improvement.py --target three-js --thinking-tokens 8192
    python scripts/run_self_improvement.py --mode agent --iterations 10 --threshold 0.3

Features:
1. Support for both workflow and agent modes
2. Configurable GitHub integration
3. Control over safety and evaluation parameters
4. Customizable thinking tokens for Claude 3.7 Sonnet
5. Detailed logging of improvement steps
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src to Python path if running from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/self_improvement.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import VOT1 modules
try:
    from src.vot1.self_improvement_workflow import SelfImprovementWorkflow
    from src.vot1.self_improvement_agent import SelfImprovementAgent
except ImportError:
    try:
        # Try alternate import path
        from vot1.self_improvement_workflow import SelfImprovementWorkflow
        from vot1.self_improvement_agent import SelfImprovementAgent
    except ImportError as e:
        logger.error(f"Failed to import VOT1 modules: {e}")
        logger.error("Please ensure VOT1 is properly installed or run from project root")
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run VOT1 self-improvement workflow")
    
    # Mode selection
    parser.add_argument("--mode", type=str, choices=["workflow", "agent"], default="agent",
                      help="Run mode: workflow (more guided) or agent (more autonomous)")
    
    # Target component
    parser.add_argument("--target", type=str, 
                      choices=["all", "owl", "memory", "three-js", "agent"],
                      default="three-js", help="Component to improve")
    
    # Agent parameters
    parser.add_argument("--thinking-tokens", type=int, default=8192,
                      help="Maximum tokens for Claude 3.7 Sonnet thinking (default: 8192)")
    parser.add_argument("--iterations", type=int, default=5,
                      help="Maximum improvement iterations (agent mode only)")
    parser.add_argument("--threshold", type=float, default=0.2,
                      help="Minimum improvement threshold 0.0-1.0 (agent mode only)")
    parser.add_argument("--no-safety", action="store_true",
                      help="Disable safety checks (agent mode only)")
    
    # GitHub integration
    parser.add_argument("--github-token", type=str,
                      help="GitHub API token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--github-repo", type=str,
                      help="GitHub repository name (or set GITHUB_REPO env var)")
    parser.add_argument("--github-owner", type=str,
                      help="GitHub repository owner (or set GITHUB_OWNER env var)")
    parser.add_argument("--no-github", action="store_true",
                      help="Disable GitHub integration")
    
    # Perplexity integration
    parser.add_argument("--no-perplexity", action="store_true",
                      help="Disable Perplexity integration")
    
    # Output options
    parser.add_argument("--verbose", action="store_true",
                      help="Enable verbose logging")
    parser.add_argument("--output", type=str,
                      help="Output file for improvement results (JSON)")
    
    return parser.parse_args()


async def run_workflow_mode(args):
    """Run the self-improvement in workflow mode."""
    # Configure GitHub integration
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    github_repo = args.github_repo or os.environ.get("GITHUB_REPO")
    github_owner = args.github_owner or os.environ.get("GITHUB_OWNER")
    
    # Create workflow instance
    workflow = SelfImprovementWorkflow(
        github_token=None if args.no_github else github_token,
        github_repo=None if args.no_github else github_repo,
        github_owner=None if args.no_github else github_owner,
        max_thinking_tokens=args.thinking_tokens,
        use_perplexity=not args.no_perplexity,
        workspace_dir=os.getcwd()
    )
    
    logger.info(f"Running workflow mode for target: {args.target}")
    
    # Run selected improvement
    if args.target == "all":
        results = await workflow.run_full_workflow()
    elif args.target == "owl":
        results = await workflow.integrate_owl_reasoning()
    elif args.target == "memory":
        results = await workflow.enhance_memory_system()
    elif args.target == "three-js":
        results = await workflow.improve_three_js_visualization()
    elif args.target == "agent":
        results = await workflow.create_self_improvement_agent()
    
    logger.info(f"Workflow completed for target: {args.target}")
    return results


async def run_agent_mode(args):
    """Run the self-improvement in agent mode."""
    # Create workflow instance (will be used by agent)
    workflow = SelfImprovementWorkflow(
        github_token=None if args.no_github else args.github_token or os.environ.get("GITHUB_TOKEN"),
        github_repo=None if args.no_github else args.github_repo or os.environ.get("GITHUB_REPO"),
        github_owner=None if args.no_github else args.github_owner or os.environ.get("GITHUB_OWNER"),
        max_thinking_tokens=args.thinking_tokens,
        use_perplexity=not args.no_perplexity,
        workspace_dir=os.getcwd()
    )
    
    # Create agent instance
    agent = SelfImprovementAgent(
        workflow=workflow,
        max_thinking_tokens=args.thinking_tokens,
        max_iterations=args.iterations,
        improvement_threshold=args.threshold,
        safety_checks=not args.no_safety,
        workspace_dir=os.getcwd()
    )
    
    logger.info(f"Running agent mode for target: {args.target}")
    
    # Run selected improvement
    if args.target == "all":
        results = await agent.run_full_improvement_cycle()
    elif args.target == "owl":
        results = await agent.run_owl_improvement()
    elif args.target == "memory":
        results = await agent.run_memory_improvement()
    elif args.target == "three-js":
        results = await agent.run_three_js_improvement()
    elif args.target == "agent":
        results = await agent.run_self_improvement()
    
    logger.info(f"Agent completed improvement for target: {args.target}")
    return results


async def main():
    """Main function to run the self-improvement workflow or agent."""
    # Parse arguments
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Run in selected mode
        if args.mode == "workflow":
            results = await run_workflow_mode(args)
        else:  # agent mode
            results = await run_agent_mode(args)
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        
        # Print summary
        print("\n=== Improvement Summary ===")
        if args.mode == "workflow":
            if "success" in results and results["success"]:
                print("✅ Workflow completed successfully")
            else:
                print("❌ Workflow encountered errors")
        else:  # agent mode
            if "success" in results and results["success"]:
                successful = results.get("stats", {}).get("successful", 0)
                attempts = results.get("stats", {}).get("attempts", 0)
                print(f"✅ Agent completed successfully: {successful}/{attempts} improvements")
            else:
                print("❌ Agent encountered errors")
        
        print(f"\nTarget: {args.target}")
        print(f"Mode: {args.mode}")
        
        # Return success status
        return 0 if results.get("success", False) else 1
    
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 