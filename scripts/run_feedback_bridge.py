#!/usr/bin/env python3
"""
VOT1 Development Feedback Bridge CLI

This script provides a command-line interface to the VOT1 Development Feedback Bridge,
allowing developers to analyze code quality, set up git hooks, monitor files for changes,
and receive real-time feedback during development.

Usage:
    python -m scripts.run_feedback_bridge analyze-file src/vot1/memory.py
    python -m scripts.run_feedback_bridge analyze-commit HEAD
    python -m scripts.run_feedback_bridge setup-hooks
    python -m scripts.run_feedback_bridge monitor --patterns "**/*.py" "**/*.js"
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path so we can import VOT1 modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.vot1.vot_mcp import VotModelControlProtocol
    from src.vot1.memory import MemoryManager
    from src.vot1.owl_reasoning import OWLReasoningEngine
    from src.vot1.code_analyzer import create_analyzer
    from src.vot1.development_feedback_bridge import DevelopmentFeedbackBridge
except ImportError as e:
    print(f"Failed to import VOT1 modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vot1.feedback_bridge_cli")


async def run_command(args):
    """Run the appropriate command based on the arguments."""
    # Set up workspace directory
    workspace_dir = os.getenv("VOT1_WORKSPACE_DIR", os.getcwd())
    
    # Initialize components
    mcp = VotModelControlProtocol(
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="perplexity/pplx-70b-online"
    )
    
    memory_manager = MemoryManager(
        storage_dir=os.path.join(workspace_dir, "memory")
    )
    
    owl_engine = OWLReasoningEngine(
        ontology_path=os.path.join(workspace_dir, "owl", "vot1_ontology.owl"),
        memory_manager=memory_manager
    )
    
    code_analyzer = create_analyzer(
        mcp=mcp,
        owl_engine=owl_engine,
        workspace_dir=workspace_dir
    )
    
    # Create feedback bridge
    bridge = DevelopmentFeedbackBridge(
        mcp=mcp,
        code_analyzer=code_analyzer,
        memory_manager=memory_manager,
        owl_engine=owl_engine,
        workspace_dir=workspace_dir,
        feedback_threshold=0.7,  # Configurable threshold
        auto_suggestions=True
    )
    
    # Execute the appropriate command
    if args.command == "analyze-file":
        logger.info(f"Analyzing file: {args.file_path}")
        result = await bridge.analyze_file_on_save(args.file_path)
        
        # Print results
        if result.get("success", True):
            print(f"\n📊 Code Quality Analysis for {args.file_path}")
            print(f"Quality Score: {result.get('quality_score', 0.0):.2f} / 1.00")
            
            if result.get("feedback"):
                print("\n📝 Feedback:")
                print(result.get("feedback"))
            
            if result.get("improvement_suggestions"):
                print("\n💡 Improvement Suggestions:")
                for i, suggestion in enumerate(result.get("improvement_suggestions", []), 1):
                    print(f"\n{i}. {suggestion.get('issue', 'Issue')} ({suggestion.get('category', 'general')})")
                    print(f"   Impact: {suggestion.get('impact', 'Unknown')}")
                    print(f"   Suggestion: {suggestion.get('suggestion', 'No suggestion')}")
                    if 'example' in suggestion:
                        print(f"   Example: {suggestion.get('example')}")
                    print(f"   Effort: {suggestion.get('effort', 'unknown')}")
        else:
            print(f"❌ Error analyzing file: {result.get('error', 'Unknown error')}")
    
    elif args.command == "analyze-commit":
        logger.info(f"Analyzing commit: {args.commit}")
        result = await bridge.analyze_git_commit(args.commit)
        
        # Print results
        if result.get("success", True):
            print(f"\n📊 Code Quality Analysis for Commit {args.commit}")
            print(f"Overall Quality Score: {result.get('overall_quality', 0.0):.2f} / 1.00")
            
            if result.get("issues_found"):
                print("\n⚠️ Issues Found")
            else:
                print("\n✅ No Significant Issues Found")
            
            if result.get("feedback"):
                print("\n📝 Feedback:")
                print(result.get("feedback"))
            
            print("\n📄 File Results:")
            for file_path, file_result in result.get("file_results", {}).items():
                print(f"  - {file_path}: Score {file_result.get('quality_score', 0.0):.2f}")
        else:
            print(f"❌ Error analyzing commit: {result.get('error', 'Unknown error')}")
    
    elif args.command == "setup-hooks":
        logger.info("Setting up git hooks")
        success = await bridge.setup_git_hooks()
        
        if success:
            print("✅ Git hooks set up successfully!")
            print("  Pre-commit hook will now check code quality before each commit.")
            print("  To bypass this check, use 'git commit --no-verify'")
        else:
            print("❌ Failed to set up git hooks. Make sure you're in a git repository.")
    
    elif args.command == "monitor":
        logger.info(f"Starting file monitoring with patterns: {args.patterns}")
        print("📡 Starting real-time code quality monitoring...")
        
        # Register a callback to print feedback
        async def on_quality_issue(file_path, analysis, score):
            print(f"\n⚠️ Quality issues detected in {file_path} (Score: {score:.2f})")
            if "feedback" in analysis and analysis["feedback"]:
                print("\n" + analysis["feedback"])
        
        await bridge.register_callback("on_quality_issue", on_quality_issue)
        
        # Start monitoring
        success = await bridge.start_file_monitoring(args.patterns)
        
        if success:
            print(f"✅ Monitoring started for patterns: {args.patterns}")
            print("  Save any file to trigger analysis.")
            print("  Press Ctrl+C to stop monitoring.")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped.")
        else:
            print("❌ Failed to start file monitoring.")
    
    elif args.command == "analyze-pr":
        logger.info(f"Analyzing PR: {args.pr_url}")
        result = await bridge.analyze_pull_request(args.pr_url)
        
        # Print results
        if result.get("success", True):
            print(f"\n📊 Code Quality Analysis for Pull Request: {args.pr_url}")
            print(f"Overall Quality Score: {result.get('overall_quality', 0.0):.2f} / 1.00")
            
            if result.get("issues_found"):
                print("\n⚠️ Issues Found")
            else:
                print("\n✅ No Significant Issues Found")
            
            if result.get("feedback"):
                print("\n📝 Feedback:")
                print(result.get("feedback"))
            
            print("\n📄 File Results:")
            for file_path, file_result in result.get("file_results", {}).items():
                if "quality_score" in file_result:
                    print(f"  - {file_path}: Score {file_result.get('quality_score', 0.0):.2f}")
                else:
                    print(f"  - {file_path}: Error - {file_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Error analyzing PR: {result.get('error', 'Unknown error')}")


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="VOT1 Development Feedback Bridge CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # analyze-file command
    analyze_file_parser = subparsers.add_parser("analyze-file", help="Analyze a file and provide feedback")
    analyze_file_parser.add_argument("file_path", help="Path to the file to analyze")
    
    # analyze-commit command
    analyze_commit_parser = subparsers.add_parser("analyze-commit", help="Analyze a git commit")
    analyze_commit_parser.add_argument("--commit", default="HEAD", help="Git commit ID to analyze")
    
    # analyze-pr command
    analyze_pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a GitHub pull request")
    analyze_pr_parser.add_argument("pr_url", help="URL of the pull request to analyze")
    
    # setup-hooks command
    subparsers.add_parser("setup-hooks", help="Set up git hooks for automatic analysis")
    
    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor files for changes")
    monitor_parser.add_argument("--patterns", nargs="+", default=["**/*.py"], 
                                help="Glob patterns for files to monitor")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run the command
    try:
        asyncio.run(run_command(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"Error running command: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 