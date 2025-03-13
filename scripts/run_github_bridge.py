#!/usr/bin/env python3
"""
VOT1 GitHub Integration CLI

This script provides a command-line interface to the VOT1 GitHub integration,
allowing autonomous repository analysis, issue management, PR feedback,
and continuous improvement using both MCP's direct GitHub capabilities
and the enhanced Composio-powered GitHub integration.

Usage:
    python -m scripts.run_github_bridge analyze-repo
    python -m scripts.run_github_bridge analyze-pr 123
    python -m scripts.run_github_bridge check-repo-health
    python -m scripts.run_github_bridge create-improvement-issue src/vot1/memory.py
    python -m scripts.run_github_bridge run-autonomous-cycle
    python -m scripts.run_github_bridge system-check
"""

import os
import sys
import json
import asyncio
import argparse
import logging
from pathlib import Path

# Add the parent directory to the path so we can import VOT1 modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vot1.github_bridge_cli")

# Global flag to track whether Composio is available
COMPOSIO_AVAILABLE = False


def check_composio_availability():
    """Check if Composio libraries are available."""
    global COMPOSIO_AVAILABLE
    try:
        from composio_openai import ComposioToolSet, App, Action
        from openai import OpenAI
        COMPOSIO_AVAILABLE = True
        logger.info("Composio libraries detected")
        return True
    except ImportError:
        logger.warning("Composio libraries not found. Only MCP GitHub integration will be available.")
        logger.warning("To enable Composio integration, install with: pip install composio-openai openai")
        COMPOSIO_AVAILABLE = False
        return False


async def create_github_bridge(args, mcp, memory_manager, code_analyzer, feedback_bridge):
    """
    Create the appropriate GitHub bridge based on available components and user preferences.
    
    Args:
        args: Command-line arguments
        mcp: VotModelControlProtocol instance
        memory_manager: Memory Manager instance
        code_analyzer: Code Analyzer instance
        feedback_bridge: Development Feedback Bridge instance
        
    Returns:
        An instance of either GitHubComposioBridge or GitHubAppBridge
    """
    # Check if --use-composio flag is set
    use_composio = getattr(args, 'use_composio', False)
    
    # If Composio is requested but not available, warn the user
    if use_composio and not COMPOSIO_AVAILABLE:
        logger.warning("Composio was requested but libraries are not available. Falling back to MCP GitHub integration.")
        use_composio = False
    
    if use_composio and COMPOSIO_AVAILABLE:
        # Use Composio GitHub bridge
        try:
            from src.vot1.github_composio_bridge import GitHubComposioBridge
            
            logger.info("Creating Composio GitHub bridge")
            return GitHubComposioBridge(
                mcp=mcp,
                memory_manager=memory_manager,
                code_analyzer=code_analyzer,
                feedback_bridge=feedback_bridge,
                default_owner=args.owner,
                default_repo=args.repo,
                composio_api_key=os.getenv("COMPOSIO_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model_name=args.model if hasattr(args, 'model') else "anthropic/claude-3-7-sonnet-20240620"
            )
        except Exception as e:
            logger.error(f"Error creating Composio GitHub bridge: {e}")
            logger.info("Falling back to MCP GitHub bridge")
    
    # Default: use MCP GitHub bridge
    from src.vot1.github_app_bridge import GitHubAppBridge
    
    logger.info("Creating MCP GitHub bridge")
    return GitHubAppBridge(
        mcp=mcp,
        memory_manager=memory_manager,
        code_analyzer=code_analyzer,
        feedback_bridge=feedback_bridge,
        default_owner=args.owner,
        default_repo=args.repo
    )


async def verify_github_connection(github_bridge):
    """
    Verify that the GitHub connection is active, and attempt to initialize if it's not.
    
    Args:
        github_bridge: The GitHub bridge instance (either MCP or Composio)
        
    Returns:
        True if connection is active, False otherwise
    """
    try:
        # Check if connection is active
        is_connected = await github_bridge.check_connection()
        
        if not is_connected:
            logger.warning("No active GitHub connection found. Attempting to initialize...")
            
            # Get required parameters for connection
            params = await github_bridge.get_required_parameters()
            
            # Attempt to initialize connection
            connection_result = await github_bridge.initiate_connection(params or {})
            
            if connection_result.get("success", False):
                logger.info("GitHub connection successfully initialized!")
                return True
            else:
                logger.error("Failed to initialize GitHub connection. Please run 'python -m scripts.init_github' first.")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error verifying GitHub connection: {e}")
        return False


async def run_command(args):
    """Run the appropriate command based on the arguments."""
    # Set up workspace directory
    workspace_dir = os.getenv("VOT1_WORKSPACE_DIR", os.getcwd())
    
    # Initialize VOT-MCP
    from src.vot1.vot_mcp import VotModelControlProtocol
    mcp = VotModelControlProtocol(
        primary_model="anthropic/claude-3-7-sonnet-20240620",
        secondary_model="perplexity/pplx-70b-online"
    )
    
    # Initialize memory manager
    from src.vot1.memory import MemoryManager
    memory_manager = MemoryManager(
        storage_dir=os.path.join(workspace_dir, "memory")
    )
    
    # Initialize OWL reasoning engine
    from src.vot1.owl_reasoning import OWLReasoningEngine
    owl_engine = OWLReasoningEngine(
        ontology_path=os.path.join(workspace_dir, "owl", "vot1_ontology.owl"),
        memory_manager=memory_manager
    )
    
    # Initialize code analyzer
    from src.vot1.code_analyzer import create_analyzer
    code_analyzer = create_analyzer(
        mcp=mcp,
        owl_engine=owl_engine,
        workspace_dir=workspace_dir
    )
    
    # Initialize feedback bridge
    from src.vot1.development_feedback_bridge import DevelopmentFeedbackBridge
    feedback_bridge = DevelopmentFeedbackBridge(
        mcp=mcp,
        code_analyzer=code_analyzer,
        memory_manager=memory_manager,
        owl_engine=owl_engine,
        workspace_dir=workspace_dir
    )
    
    # Special case: system-check doesn't need a GitHub bridge
    if args.command == "system-check":
        from src.vot1.system_check import SystemCheck
        
        print(f"🔍 Running VOT1 system check...")
        system_check = SystemCheck(
            mcp=mcp,
            memory_manager=memory_manager,
            owl_engine=owl_engine,
            code_analyzer=code_analyzer,
            workspace_dir=workspace_dir,
            verbose=not args.quiet
        )
        
        results = await system_check.check_all()
        
        if not args.quiet:
            await system_check.print_check_results(results)
        
        # Return non-zero exit code if system check failed
        if not results.get("status", False):
            sys.exit(1)
        
        return
    
    # Initialize the appropriate GitHub bridge
    github_bridge = await create_github_bridge(
        args=args,
        mcp=mcp,
        memory_manager=memory_manager,
        code_analyzer=code_analyzer,
        feedback_bridge=feedback_bridge
    )
    
    # Verify GitHub connection (except for check-connection command)
    if args.command != "check-connection":
        if not await verify_github_connection(github_bridge):
            if args.force:
                logger.warning("Proceeding despite GitHub connection issues (--force flag is set)")
            else:
                logger.error("Aborting due to GitHub connection issues. Use --force to override.")
                return
    
    # Execute the appropriate command
    if args.command == "check-connection":
        is_connected = await github_bridge.check_connection()
        print(f"✅ GitHub connection is {'active' if is_connected else 'inactive'}")
        
        # Get bridge type
        bridge_type = "Composio" if hasattr(github_bridge, "has_composio") else "MCP"
        print(f"🔌 Using {bridge_type} GitHub bridge")
        
        if is_connected:
            # Try to get basic repository info to test full API access
            try:
                if args.owner and args.repo:
                    print(f"🔍 Testing API with repository: {args.owner}/{args.repo}")
                    repo_info = await github_bridge._get_repository_info(args.owner, args.repo)
                    if repo_info and "name" in repo_info:
                        print(f"✅ GitHub API access confirmed for {args.owner}/{args.repo}")
                        print(f"  Description: {repo_info.get('description', 'N/A')}")
                        print(f"  Stars: {repo_info.get('stargazers_count', 0)}")
                        print(f"  Forks: {repo_info.get('forks_count', 0)}")
                    else:
                        print(f"⚠️ Could not retrieve full repository info")
            except Exception as e:
                print(f"⚠️ API test had an error: {e}")
        
    elif args.command == "analyze-repo":
        print(f"🔍 Analyzing repository: {args.owner}/{args.repo}")
        
        # Set deep_analysis flag based on args
        deep_analysis = getattr(args, 'deep', False)
        
        result = await github_bridge.analyze_repository(
            args.owner, 
            args.repo,
            deep_analysis=deep_analysis
        )
        
        if result.get("success", False):
            print(f"\n✅ Repository analysis complete for {args.owner}/{args.repo}")
            
            # Print repository info
            repo_info = result.get("repository", {})
            print(f"\n📊 Repository Information:")
            print(f"  Name: {repo_info.get('name')}")
            print(f"  Description: {repo_info.get('description')}")
            print(f"  Stars: {repo_info.get('stargazers_count')}")
            print(f"  Forks: {repo_info.get('forks_count')}")
            print(f"  Open Issues: {repo_info.get('open_issues_count')}")
            print(f"  Default Branch: {repo_info.get('default_branch')}")
            
            # Print code quality issues
            code_quality_issues = result.get("code_quality_issues", [])
            print(f"\n🐛 Code Quality Issues: {len(code_quality_issues)}")
            for i, issue in enumerate(code_quality_issues[:5], 1):
                print(f"  {i}. {issue.get('name', 'Unknown')} - {issue.get('html_url', '')}")
            
            if len(code_quality_issues) > 5:
                print(f"  ... and {len(code_quality_issues) - 5} more")
            
            # Print recent PRs
            recent_prs = result.get("pull_requests", [])
            print(f"\n🔄 Recent Pull Requests: {len(recent_prs)}")
            for i, pr in enumerate(recent_prs[:5], 1):
                print(f"  {i}. #{pr.get('number')} - {pr.get('title')} ({pr.get('state')})")
            
            if len(recent_prs) > 5:
                print(f"  ... and {len(recent_prs) - 5} more")
            
            # Print recent commits
            recent_commits = result.get("commits", [])
            print(f"\n📝 Recent Commits: {len(recent_commits)}")
            for i, commit in enumerate(recent_commits[:5], 1):
                commit_info = commit.get('commit', {})
                author = commit_info.get('author', {}).get('name', 'Unknown')
                message = commit_info.get('message', '').split('\n')[0]
                print(f"  {i}. {commit.get('sha')[:7]} - {message} (by {author})")
            
            if len(recent_commits) > 5:
                print(f"  ... and {len(recent_commits) - 5} more")
            
            # Print repository structure if available (from deep analysis)
            if "repository_structure" in result:
                repo_structure = result.get("repository_structure", {})
                common_files = repo_structure.get("common_files", {})
                
                print(f"\n📁 Repository Structure:")
                print(f"  README: {'✅' if common_files.get('readme', False) else '❌'}")
                print(f"  LICENSE: {'✅' if common_files.get('license', False) else '❌'}")
                print(f"  Contributing Guide: {'✅' if common_files.get('contributing', False) else '❌'}")
                print(f"  Code of Conduct: {'✅' if common_files.get('code_of_conduct', False) else '❌'}")
                print(f"  GitHub Workflows: {'✅' if common_files.get('github_directory', False) else '❌'}")
                
                probable_language = repo_structure.get("probable_language", "Unknown")
                print(f"  Probable Language: {probable_language}")
            
            # Print commit activity if available (from deep analysis)
            if "commit_activity" in result:
                commit_activity = result.get("commit_activity", {})
                
                if "error" not in commit_activity:
                    print(f"\n📈 Commit Activity:")
                    print(f"  Active Maintenance: {'✅' if commit_activity.get('is_actively_maintained', False) else '❌'}")
                    
                    days_since = commit_activity.get("days_since_last_commit")
                    if days_since is not None:
                        print(f"  Days Since Last Commit: {days_since}")
                    
                    contributors = commit_activity.get("unique_contributors", 0)
                    print(f"  Unique Contributors: {contributors}")
                    
                    avg_days = commit_activity.get("average_days_between_commits")
                    if avg_days is not None:
                        print(f"  Average Days Between Commits: {avg_days:.1f}")
        else:
            print(f"❌ Error analyzing repository: {result.get('error', 'Unknown error')}")
    
    elif args.command == "analyze-pr":
        print(f"🔍 Analyzing pull request: #{args.pr_number} in {args.owner}/{args.repo}")
        result = await github_bridge.analyze_pull_request(args.pr_number, args.owner, args.repo)
        
        if result.get("success", False):
            analysis = result.get("analysis", {})
            pr_details = analysis.get("pull_request", {})
            
            print(f"\n✅ Pull request analysis complete for #{args.pr_number}")
            
            # Print PR details
            print(f"\n📊 Pull Request Information:")
            print(f"  Title: {pr_details.get('title')}")
            print(f"  State: {pr_details.get('state')}")
            print(f"  Author: {pr_details.get('user', {}).get('login')}")
            print(f"  Created: {pr_details.get('created_at')}")
            print(f"  Updated: {pr_details.get('updated_at')}")
            print(f"  URL: {pr_details.get('html_url')}")
            
            # Print PR stats
            print(f"\n📈 Pull Request Stats:")
            print(f"  Commits: {pr_details.get('commits')}")
            print(f"  Changed Files: {pr_details.get('changed_files')}")
            print(f"  Additions: {pr_details.get('additions')}")
            print(f"  Deletions: {pr_details.get('deletions')}")
            
            # Print code quality feedback if available
            if "code_quality_feedback" in analysis:
                feedback = analysis.get("code_quality_feedback", {})
                print(f"\n🔬 Code Quality Feedback:")
                print(f"  Overall Quality: {feedback.get('overall_quality', 0.0):.2f} / 1.00")
                
                if feedback.get("issues_found", False):
                    print(f"  ⚠️ Issues Found")
                else:
                    print(f"  ✅ No Significant Issues Found")
                
                if "feedback" in feedback and feedback["feedback"]:
                    print(f"\n📝 Feedback Summary:")
                    print(f"{feedback['feedback'][:500]}...")
                    
                    # Ask if we should post the feedback as a comment
                    if not args.no_prompt:
                        post_feedback = input("\nPost this feedback as a PR comment? (y/n): ").lower() == 'y'
                        if post_feedback:
                            comment_result = await github_bridge.add_pr_comment(
                                pr_number=args.pr_number,
                                body=feedback['feedback'],
                                owner=args.owner,
                                repo=args.repo
                            )
                            if comment_result.get("success", False):
                                print(f"✅ Comment posted successfully: {comment_result.get('url')}")
                            else:
                                print(f"❌ Error posting comment: {comment_result.get('error')}")
        else:
            print(f"❌ Error analyzing pull request: {result.get('error', 'Unknown error')}")
    
    elif args.command == "star-repo":
        print(f"⭐ Starring repository: {args.owner}/{args.repo}")
        result = await github_bridge.star_repository(args.owner, args.repo)
        
        if result.get("success", False):
            print(f"✅ Repository {args.owner}/{args.repo} starred successfully!")
        else:
            print(f"❌ Error starring repository: {result.get('error', 'Unknown error')}")
    
    elif args.command == "check-repo-health":
        print(f"🔍 Checking repository health: {args.owner}/{args.repo}")
        
        # For Composio bridge, use the dedicated health check method
        if hasattr(github_bridge, "has_composio") and github_bridge.has_composio:
            health_result = await github_bridge.generate_health_check_report(
                owner=args.owner,
                repo=args.repo,
                create_issue=args.create_issue
            )
            
            if health_result.get("success", False):
                health_check = health_result.get("health_check", {})
                
                print(f"\n📋 Repository Health Report:")
                print(f"  Overall Health Score: {health_check.get('health_score', 0):.2f} / 1.00")
                print(f"  Documentation Score: {health_check.get('documentation_score', 0):.2f} / 1.00")
                print(f"  Activity Score: {health_check.get('activity_score', 0):.2f} / 1.00")
                print(f"  Community Score: {health_check.get('community_score', 0):.2f} / 1.00")
                
                # Print improvement suggestions
                suggestions = health_check.get("improvement_suggestions", [])
                if suggestions:
                    print(f"\n🔧 Improvement Suggestions:")
                    
                    # Group by category
                    by_category = {}
                    for suggestion in suggestions:
                        category = suggestion.get("category", "other")
                        if category not in by_category:
                            by_category[category] = []
                        by_category[category].append(suggestion)
                    
                    # Print each category
                    for category, items in by_category.items():
                        print(f"  {category.title()}:")
                        for item in items:
                            priority = item.get("priority", "medium").upper()
                            suggestion_text = item.get("suggestion", "")
                            print(f"    [{priority}] {suggestion_text}")
                
                # Print issue info if created
                if args.create_issue and "issue" in health_result:
                    issue = health_result.get("issue", {})
                    print(f"\n📝 Health check issue created: {issue.get('html_url')}")
            else:
                print(f"❌ Error generating health check report: {health_result.get('error', 'Unknown error')}")
        
        else:
            # For MCP bridge, use the old approach
            # First analyze the repository
            repo_result = await github_bridge.analyze_repository(args.owner, args.repo)
            
            if not repo_result.get("success", False):
                print(f"❌ Error analyzing repository: {repo_result.get('error', 'Unknown error')}")
                return
            
            # Use MCP to generate health report based on analysis
            report_prompt = f"""
            Generate a comprehensive health report for the GitHub repository {args.owner}/{args.repo} based on the provided analysis.
            
            Assessment should cover:
            1. Code quality (based on TODOs, FIXMEs, etc.)
            2. Repository activity level
            3. Pull request health and review process
            4. Potential areas for improvement
            5. Overall health score (0-100)
            
            Provide specific, actionable recommendations.
            """
            
            try:
                report_response = await mcp.process_request_async(
                    prompt=report_prompt,
                    system="You are an expert repository health analyzer. Provide a comprehensive, balanced assessment of repository health with clear recommendations for improvement.",
                    context={
                        "repository_analysis": repo_result
                    },
                    max_tokens=2048
                )
                
                health_report = report_response.get("content", "Error generating health report")
                
                print("\n📋 Repository Health Report:")
                print(health_report)
                
                # Create an issue with the health report if requested
                if args.create_issue:
                    print("\n📝 Creating health report issue...")
                    issue_result = await github_bridge.create_issue(
                        title=f"Repository Health Report - {args.owner}/{args.repo}",
                        body=health_report,
                        owner=args.owner,
                        repo=args.repo,
                        labels=["health-report", "maintenance"]
                    )
                    
                    if issue_result.get("success", False):
                        print(f"✅ Health report issue created: {issue_result.get('url')}")
                    else:
                        print(f"❌ Error creating issue: {issue_result.get('error')}")
                
            except Exception as e:
                print(f"❌ Error generating health report: {e}")
    
    elif args.command == "create-improvement-issue":
        component_path = args.component
        print(f"🔍 Analyzing component for improvement: {component_path}")
        
        # First analyze the component using the feedback bridge
        try:
            analysis_result = await feedback_bridge.analyze_file_on_save(component_path)
            
            if not analysis_result.get("success", False) and "error" in analysis_result:
                print(f"❌ Error analyzing component: {analysis_result['error']}")
                return
            
            # Check if the component needs improvement
            quality_score = analysis_result.get("quality_score", 1.0)
            print(f"📊 Component quality score: {quality_score:.2f} / 1.00")
            
            if quality_score >= 0.85 and not args.force:
                print(f"✅ Component quality is already high (>= 0.85). No improvement issue needed.")
                print(f"   Use --force to create an issue anyway.")
                return
            
            # Create an improvement issue
            print(f"📝 Creating improvement issue for component...")
            issue_result = await github_bridge.create_improvement_issue(
                component_path=component_path,
                analysis_result=analysis_result,
                owner=args.owner,
                repo=args.repo
            )
            
            if issue_result.get("success", False):
                print(f"✅ Improvement issue created: {issue_result.get('url')}")
            else:
                print(f"❌ Error creating issue: {issue_result.get('error')}")
            
        except Exception as e:
            print(f"❌ Error creating improvement issue: {e}")
    
    elif args.command == "run-autonomous-cycle":
        print(f"🤖 Running autonomous improvement cycle on {args.owner}/{args.repo}")
        
        # For Composio bridge, use the dedicated autonomous improvement cycle method
        if hasattr(github_bridge, "has_composio") and github_bridge.has_composio:
            cycle_result = await github_bridge.run_autonomous_improvement_cycle(
                components=args.components,
                owner=args.owner,
                repo=args.repo,
                max_improvements=args.max_improvements if hasattr(args, 'max_improvements') else 3,
                create_prs=not args.no_prs if hasattr(args, 'no_prs') else True
            )
            
            if cycle_result.get("success", False):
                print(f"\n✅ Autonomous improvement cycle completed!")
                
                improvements = cycle_result.get("improvements", [])
                print(f"  Components analyzed: {cycle_result.get('components_analyzed', 0)}")
                print(f"  Improvements created: {len(improvements)}")
                
                # Print each improvement
                for i, improvement in enumerate(improvements, 1):
                    component = improvement.get("component", "Unknown")
                    issue = improvement.get("issue", {})
                    pr = improvement.get("pr", None)
                    
                    print(f"\n  {i}. {component}:")
                    if issue:
                        print(f"     Issue: {issue.get('html_url', 'No URL')}")
                    if pr:
                        print(f"     PR: {pr.get('html_url', 'No URL')}")
            else:
                print(f"❌ Error in autonomous improvement cycle: {cycle_result.get('error', 'Unknown error')}")
        
        else:
            # For MCP bridge, use the old approach
            # 1. Analyze the repository
            print(f"Step 1: Analyzing repository...")
            repo_result = await github_bridge.analyze_repository(args.owner, args.repo)
            
            if not repo_result.get("success", False):
                print(f"❌ Error analyzing repository: {repo_result.get('error', 'Unknown error')}")
                return
            
            # 2. Identify components to improve
            print(f"Step 2: Identifying components to improve...")
            components_to_improve = []
            
            # If components were specified, use those
            if args.components:
                components_to_improve = args.components
            else:
                # Use MCP to identify candidate components for improvement
                discover_prompt = """
                Based on the repository analysis, identify 3-5 components that would benefit most from improvement.
                Focus on components with:
                1. High complexity
                2. Many TODOs or FIXMEs
                3. Recent changes with potential issues
                4. Core functionality importance
                
                Return a JSON array of file paths relative to the repository root.
                Example: ["src/core/memory.py", "src/api/routes.py"]
                """
                
                try:
                    discovery_response = await mcp.process_request_async(
                        prompt=discover_prompt,
                        system="You are a code improvement expert. Identify components that need improvement based on repository analysis.",
                        context={
                            "repository_analysis": repo_result
                        },
                        max_tokens=1024
                    )
                    
                    # Parse the response to get component paths
                    discovery_content = discovery_response.get("content", "[]").strip()
                    # Extract JSON from the response if it's not pure JSON
                    if not discovery_content.startswith("["):
                        import re
                        json_match = re.search(r'\[.*\]', discovery_content, re.DOTALL)
                        if json_match:
                            discovery_content = json_match.group(0)
                    
                    try:
                        discovered_components = json.loads(discovery_content)
                        if isinstance(discovered_components, list) and discovered_components:
                            components_to_improve = discovered_components
                        else:
                            # Fallback to defaults if discovery failed
                            components_to_improve = ["src/vot1/memory.py", "src/vot1/github_app_bridge.py"]
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse discovered components: {discovery_content}")
                        # Fallback to defaults
                        components_to_improve = ["src/vot1/memory.py", "src/vot1/github_app_bridge.py"]
                except Exception as e:
                    logger.error(f"Error discovering components: {e}")
                    # Fallback to defaults
                    components_to_improve = ["src/vot1/memory.py", "src/vot1/github_app_bridge.py"]
            
            print(f"Found {len(components_to_improve)} components to improve:")
            for component in components_to_improve:
                print(f"  - {component}")
            
            # 3. Analyze and create improvement issues for each component
            print(f"Step 3: Creating improvement issues...")
            for component in components_to_improve:
                print(f"  Analyzing {component}...")
                try:
                    analysis_result = await feedback_bridge.analyze_file_on_save(component)
                    
                    quality_score = analysis_result.get("quality_score", 1.0)
                    print(f"  Quality score: {quality_score:.2f} / 1.00")
                    
                    if quality_score < 0.85 or args.force:
                        print(f"  Creating improvement issue...")
                        issue_result = await github_bridge.create_improvement_issue(
                            component_path=component,
                            analysis_result=analysis_result,
                            owner=args.owner,
                            repo=args.repo
                        )
                        
                        if issue_result.get("success", False):
                            print(f"  ✅ Issue created: {issue_result.get('url')}")
                        else:
                            print(f"  ❌ Error creating issue: {issue_result.get('error')}")
                    else:
                        print(f"  ✅ Component quality is already high. No improvement issue needed.")
                except Exception as e:
                    print(f"  ❌ Error processing component {component}: {e}")
            
            print(f"\n✅ Autonomous improvement cycle completed!")


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(description="VOT1 GitHub Integration CLI")
    
    # Global arguments
    parser.add_argument("--owner", help="Repository owner or organization", 
                        default=os.getenv("GITHUB_OWNER"))
    parser.add_argument("--repo", help="Repository name", 
                        default=os.getenv("GITHUB_REPO"))
    parser.add_argument("--no-prompt", action="store_true", 
                        help="Run without interactive prompts")
    parser.add_argument("--force", action="store_true",
                        help="Force execution even if GitHub connection issues exist")
    parser.add_argument("--use-composio", action="store_true",
                        help="Use Composio GitHub integration instead of MCP")
    parser.add_argument("--model", help="LLM model to use with Composio",
                       default="anthropic/claude-3-7-sonnet-20240620")
    
    # Check for Composio availability
    has_composio = check_composio_availability()
    
    # Set up subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # system-check command
    system_check_parser = subparsers.add_parser("system-check", help="Check the health of all VOT1 components")
    system_check_parser.add_argument("--quiet", action="store_true", help="Don't print detailed output")
    
    # check-connection command
    subparsers.add_parser("check-connection", help="Check GitHub connection status")
    
    # analyze-repo command
    analyze_repo_parser = subparsers.add_parser("analyze-repo", help="Analyze a GitHub repository")
    analyze_repo_parser.add_argument("--deep", action="store_true", help="Perform deep analysis")
    
    # analyze-pr command
    analyze_pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a GitHub pull request")
    analyze_pr_parser.add_argument("pr_number", type=int, help="Pull request number")
    
    # star-repo command
    subparsers.add_parser("star-repo", help="Star a GitHub repository")
    
    # check-repo-health command
    check_health_parser = subparsers.add_parser("check-repo-health", 
                                               help="Check repository health and generate report")
    check_health_parser.add_argument("--create-issue", action="store_true", 
                                    help="Create an issue with the health report")
    
    # create-improvement-issue command
    improve_parser = subparsers.add_parser("create-improvement-issue", 
                                          help="Create an issue with improvement suggestions")
    improve_parser.add_argument("component", help="Path to the component to improve")
    
    # run-autonomous-cycle command
    cycle_parser = subparsers.add_parser("run-autonomous-cycle", 
                                        help="Run a complete autonomous improvement cycle")
    cycle_parser.add_argument("--components", nargs="+", 
                             help="Specific components to analyze and improve")
    cycle_parser.add_argument("--max-improvements", type=int, default=3,
                             help="Maximum number of improvements to make")
    cycle_parser.add_argument("--no-prs", action="store_true",
                             help="Don't create pull requests, only issues")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # For most commands, we need owner and repo
    if args.command not in ["check-connection", "system-check"] and (not args.owner or not args.repo):
        print("Error: Repository owner and name are required for this command. "
              "Set them with --owner and --repo or through environment variables "
              "GITHUB_OWNER and GITHUB_REPO.")
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