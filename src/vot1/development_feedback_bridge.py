#!/usr/bin/env python3
"""
VOT1 Development Feedback Bridge

This module serves as a bridge between code analysis and development workflows,
providing real-time feedback, insights, and guidance to ensure seamless and
high-quality development. It integrates with the code analyzer, self-improvement
agent, and version control systems to create a continuous feedback loop.

Key features:
1. Real-time code quality feedback during development
2. Integration with IDE and version control hooks
3. Automated improvement suggestions
4. Progress tracking and quality metrics
5. Learning from developer interactions
"""

import os
import logging
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple

from vot1.code_analyzer import CodeAnalyzer, create_analyzer
from vot1.memory import MemoryManager
from vot1.owl_reasoning import OWLReasoningEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DevelopmentFeedbackBridge:
    """
    Bridge between code analysis and development workflows.
    
    This class provides real-time feedback during development,
    integrates with IDEs and version control systems, and creates
    a continuous feedback loop to improve code quality.
    """
    
    def __init__(
        self,
        mcp=None,
        code_analyzer=None,
        memory_manager=None,
        owl_engine=None,
        workspace_dir: Optional[str] = None,
        feedback_threshold: float = 0.7,
        auto_suggestions: bool = True,
        store_feedback_history: bool = True
    ):
        """
        Initialize the development feedback bridge.
        
        Args:
            mcp: VOT Model Control Protocol instance
            code_analyzer: CodeAnalyzer instance or None to create a new one
            memory_manager: MemoryManager instance or None to create a new one
            owl_engine: OWL reasoning engine or None to create a new one
            workspace_dir: Root directory of the workspace
            feedback_threshold: Minimum quality score to trigger feedback
            auto_suggestions: Whether to generate improvement suggestions automatically
            store_feedback_history: Whether to store feedback history in memory
        """
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        self.mcp = mcp
        self.feedback_threshold = feedback_threshold
        self.auto_suggestions = auto_suggestions
        self.store_feedback_history = store_feedback_history
        
        # Initialize or use provided components
        self.code_analyzer = code_analyzer or create_analyzer(
            mcp=self.mcp,
            owl_engine=owl_engine,
            workspace_dir=self.workspace_dir
        )
        
        self.memory_manager = memory_manager
        self.owl_engine = owl_engine
        
        # Feedback history
        self.feedback_history = {}
        
        # Components currently being monitored
        self.monitored_components = set()
        
        # Callbacks for different events
        self.callbacks = {
            "on_quality_issue": [],
            "on_improvement_suggestion": [],
            "on_feedback_provided": [],
            "on_code_change": []
        }
        
        logger.info(f"Initialized DevelopmentFeedbackBridge with workspace at {self.workspace_dir}")
    
    async def analyze_file_on_save(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a file when it's saved and provide immediate feedback.
        
        This can be integrated with IDE hooks to trigger on file save.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Analysis results with feedback
        """
        relative_path = self._get_relative_path(file_path)
        
        try:
            # Perform code analysis
            analysis = await self.code_analyzer.analyze_code(relative_path)
            
            # Calculate quality score
            quality_score = self.code_analyzer.calculate_quality_score(analysis)
            
            # Generate feedback if score is below threshold
            feedback = None
            improvement_suggestions = None
            
            if quality_score < self.feedback_threshold:
                feedback = await self._generate_feedback(analysis, relative_path)
                
                # Generate improvement suggestions if enabled
                if self.auto_suggestions:
                    improvement_suggestions = await self._generate_improvement_suggestions(
                        analysis, relative_path
                    )
                
                # Notify callbacks
                for callback in self.callbacks["on_quality_issue"]:
                    callback(relative_path, analysis, quality_score)
            
            # Store results in history
            self.feedback_history[relative_path] = {
                "timestamp": time.time(),
                "quality_score": quality_score,
                "analysis": analysis,
                "feedback": feedback,
                "suggestions": improvement_suggestions
            }
            
            # Store in memory if enabled
            if self.store_feedback_history and self.memory_manager and feedback:
                self._store_feedback_in_memory(relative_path, quality_score, feedback, improvement_suggestions)
            
            # Return results
            return {
                "file_path": relative_path,
                "quality_score": quality_score,
                "feedback": feedback,
                "improvement_suggestions": improvement_suggestions,
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error analyzing file {relative_path}: {e}")
            return {
                "file_path": relative_path,
                "error": str(e),
                "success": False
            }
    
    async def analyze_git_commit(self, commit_id: str = "HEAD") -> Dict[str, Any]:
        """
        Analyze all files in a git commit and provide feedback.
        
        Args:
            commit_id: Git commit ID to analyze
            
        Returns:
            Analysis results for all files in the commit
        """
        try:
            # Get files changed in the commit
            import subprocess
            cmd = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_id]
            result = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True)
            changed_files = result.stdout.strip().split("\n")
            
            # Filter for relevant file types
            relevant_files = [
                f for f in changed_files 
                if f.endswith((".py", ".js", ".ts", ".html", ".css", ".jsx", ".tsx"))
            ]
            
            # Analyze each file
            results = {}
            feedback = {}
            overall_quality = 0.0
            
            for file_path in relevant_files:
                try:
                    # Analyze the file
                    analysis = await self.analyze_file_on_save(file_path)
                    results[file_path] = analysis
                    
                    # Collect feedback if quality is below threshold
                    if analysis.get("quality_score", 1.0) < self.feedback_threshold:
                        feedback[file_path] = {
                            "quality_score": analysis["quality_score"],
                            "feedback": analysis["feedback"],
                            "suggestions": analysis["improvement_suggestions"]
                        }
                    
                    # Add to overall quality score
                    overall_quality += analysis.get("quality_score", 0.0)
                except Exception as e:
                    logger.error(f"Error analyzing {file_path} in commit {commit_id}: {e}")
                    results[file_path] = {"error": str(e)}
            
            # Calculate average quality
            if relevant_files:
                overall_quality /= len(relevant_files)
            
            # Generate commit-level feedback
            commit_feedback = await self._generate_commit_feedback(
                commit_id, feedback, overall_quality
            )
            
            return {
                "commit_id": commit_id,
                "overall_quality": overall_quality,
                "feedback": commit_feedback,
                "file_results": results,
                "issues_found": len(feedback) > 0
            }
        except Exception as e:
            logger.error(f"Error analyzing commit {commit_id}: {e}")
            return {
                "commit_id": commit_id,
                "error": str(e),
                "success": False
            }
    
    async def setup_git_hooks(self) -> bool:
        """
        Set up git hooks to automatically analyze code on commit.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create pre-commit hook
            hooks_dir = self.workspace_dir / ".git" / "hooks"
            if not hooks_dir.exists():
                logger.error(f"Git hooks directory not found: {hooks_dir}")
                return False
            
            # Create pre-commit hook script
            pre_commit_path = hooks_dir / "pre-commit"
            with open(pre_commit_path, 'w') as f:
                f.write("""#!/bin/bash
# VOT1 Development Feedback Bridge pre-commit hook
echo "Running VOT1 code quality analysis..."
# Get all staged files
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(py|js|ts|jsx|tsx|html|css)$')
if [ -z "$staged_files" ]; then
    echo "No relevant files to analyze"
    exit 0
fi

# Run analysis script
python -m vot1.development_feedback_bridge analyze-staged
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "Code quality issues found. Please fix them before committing."
    echo "To bypass this check, use 'git commit --no-verify'"
    exit 1
fi

echo "Code quality check passed!"
exit 0
""")
            
            # Make hook executable
            os.chmod(pre_commit_path, 0o755)
            
            logger.info(f"Successfully set up git pre-commit hook at {pre_commit_path}")
            return True
        except Exception as e:
            logger.error(f"Error setting up git hooks: {e}")
            return False
    
    async def analyze_staged_files(self) -> Dict[str, Any]:
        """
        Analyze all staged files in git and provide feedback.
        
        This is called by the pre-commit hook.
        
        Returns:
            Analysis results for all staged files
        """
        try:
            # Get staged files
            import subprocess
            cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
            result = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True)
            staged_files = result.stdout.strip().split("\n")
            
            # Filter for relevant file types
            relevant_files = [
                f for f in staged_files 
                if f.endswith((".py", ".js", ".ts", ".html", ".css", ".jsx", ".tsx"))
            ]
            
            # Analyze each file
            results = {}
            issues_found = False
            
            for file_path in relevant_files:
                try:
                    # Analyze the file
                    analysis = await self.analyze_file_on_save(file_path)
                    results[file_path] = analysis
                    
                    # Check if quality is below threshold
                    if analysis.get("quality_score", 1.0) < self.feedback_threshold:
                        issues_found = True
                except Exception as e:
                    logger.error(f"Error analyzing staged file {file_path}: {e}")
                    results[file_path] = {"error": str(e)}
            
            return {
                "issues_found": issues_found,
                "results": results
            }
        except Exception as e:
            logger.error(f"Error analyzing staged files: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def start_file_monitoring(self, file_patterns: List[str] = None) -> bool:
        """
        Start monitoring files for changes and provide real-time feedback.
        
        Args:
            file_patterns: Glob patterns for files to monitor, e.g. ["**/*.py"]
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            import watchdog.observers
            import watchdog.events
            
            if file_patterns is None:
                file_patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx"]
            
            # Set up watchdog event handler
            class FeedbackEventHandler(watchdog.events.FileSystemEventHandler):
                def __init__(self, bridge):
                    self.bridge = bridge
                
                def on_modified(self, event):
                    if not event.is_directory:
                        file_path = event.src_path
                        # Check if file matches patterns
                        from fnmatch import fnmatch
                        if any(fnmatch(file_path, pattern) for pattern in file_patterns):
                            asyncio.create_task(self.bridge.analyze_file_on_save(file_path))
            
            # Set up observer
            event_handler = FeedbackEventHandler(self)
            observer = watchdog.observers.Observer()
            observer.schedule(event_handler, str(self.workspace_dir), recursive=True)
            observer.start()
            
            logger.info(f"Started file monitoring for patterns: {file_patterns}")
            return True
        except Exception as e:
            logger.error(f"Error starting file monitoring: {e}")
            return False
    
    async def analyze_pull_request(self, pr_url: str) -> Dict[str, Any]:
        """
        Analyze a pull request and provide feedback.
        
        Args:
            pr_url: URL to the pull request
            
        Returns:
            Analysis results for the pull request
        """
        try:
            # Extract repo and PR number from URL
            import re
            match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
            if not match:
                raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
            
            owner, repo, pr_number = match.groups()
            
            # Get PR files using GitHub API
            if not self.mcp:
                raise ValueError("MCP is required for GitHub API access")
            
            # Use MCP GitHub API to get PR files
            pr_files_response = await self.mcp.process_github_request(
                endpoint=f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
                method="GET"
            )
            
            pr_files = json.loads(pr_files_response.get("content", "[]"))
            
            # Analyze each file
            results = {}
            feedback = {}
            overall_quality = 0.0
            analyzed_files = 0
            
            for file_info in pr_files:
                file_path = file_info.get("filename")
                if not file_path or not file_path.endswith((".py", ".js", ".ts", ".html", ".css", ".jsx", ".tsx")):
                    continue
                
                try:
                    # Download file content
                    file_content = file_info.get("raw_url")
                    if not file_content:
                        continue
                    
                    # Save to temp file for analysis
                    temp_file = self.workspace_dir / f"temp_{os.path.basename(file_path)}"
                    with open(temp_file, 'w') as f:
                        f.write(file_content)
                    
                    # Analyze the file
                    analysis = await self.analyze_file_on_save(str(temp_file))
                    results[file_path] = analysis
                    
                    # Clean up temp file
                    os.remove(temp_file)
                    
                    # Collect feedback if quality is below threshold
                    if analysis.get("quality_score", 1.0) < self.feedback_threshold:
                        feedback[file_path] = {
                            "quality_score": analysis["quality_score"],
                            "feedback": analysis["feedback"],
                            "suggestions": analysis["improvement_suggestions"]
                        }
                    
                    # Add to overall quality score
                    overall_quality += analysis.get("quality_score", 0.0)
                    analyzed_files += 1
                except Exception as e:
                    logger.error(f"Error analyzing PR file {file_path}: {e}")
                    results[file_path] = {"error": str(e)}
            
            # Calculate average quality
            if analyzed_files > 0:
                overall_quality /= analyzed_files
            
            # Generate PR-level feedback
            pr_feedback = await self._generate_pr_feedback(
                pr_url, feedback, overall_quality
            )
            
            # Post feedback as PR comment if significant issues found
            if feedback and self.mcp:
                await self._post_pr_comment(
                    owner, repo, pr_number, pr_feedback
                )
            
            return {
                "pr_url": pr_url,
                "overall_quality": overall_quality,
                "feedback": pr_feedback,
                "file_results": results,
                "issues_found": len(feedback) > 0
            }
        except Exception as e:
            logger.error(f"Error analyzing pull request {pr_url}: {e}")
            return {
                "pr_url": pr_url,
                "error": str(e),
                "success": False
            }
    
    async def register_callback(self, event_type: str, callback: Callable) -> bool:
        """
        Register a callback for a specific event.
        
        Args:
            event_type: Event type (on_quality_issue, on_improvement_suggestion, etc.)
            callback: Callable to invoke when the event occurs
            
        Returns:
            True if registered successfully, False otherwise
        """
        if event_type not in self.callbacks:
            logger.error(f"Unknown event type: {event_type}")
            return False
        
        self.callbacks[event_type].append(callback)
        return True
    
    async def _generate_feedback(self, analysis: Dict[str, Any], file_path: str) -> str:
        """Generate user-friendly feedback based on code analysis."""
        if not self.mcp:
            # Simple feedback generation without MCP
            issues = []
            
            # Collect issues from different categories
            for category in ["static_analysis", "performance", "security", "documentation", "complexity", "memory_management"]:
                category_issues = analysis.get(category, {}).get("issues", [])
                for issue in category_issues:
                    severity = issue.get("severity", "").upper()
                    message = issue.get("message", "")
                    suggestion = issue.get("suggestion", "")
                    
                    issues.append(f"{severity}: {message} - {suggestion}")
            
            if issues:
                return "Code quality issues found:\n" + "\n".join(issues)
            else:
                return "No significant issues found."
        
        # Use MCP for more sophisticated feedback
        try:
            feedback_prompt = f"""
            Generate clear, constructive feedback based on the code analysis results.
            
            File: {file_path}
            
            Focus on the most important issues first, and provide actionable suggestions.
            Be constructive and helpful, not critical.
            
            Include:
            1. A brief summary of the overall code quality
            2. The most critical issues that should be addressed
            3. Concrete suggestions for improvement
            4. Any positive aspects worth mentioning
            
            Format the feedback in markdown for readability.
            """
            
            feedback_response = await self.mcp.process_request_async(
                prompt=feedback_prompt,
                system="You are an expert software mentor providing constructive feedback to help developers improve their code. Your feedback is clear, specific, actionable, and presented in a helpful, supportive tone.",
                context={
                    "analysis": analysis,
                    "file_path": file_path
                },
                max_tokens=1024
            )
            
            return feedback_response.get("content", "No feedback available.")
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return f"Error generating feedback: {str(e)}"
    
    async def _generate_improvement_suggestions(self, analysis: Dict[str, Any], file_path: str) -> List[Dict[str, Any]]:
        """Generate specific improvement suggestions based on code analysis."""
        if not self.mcp:
            return []
        
        try:
            suggestions_prompt = f"""
            Based on the code analysis for {file_path}, generate specific, actionable improvement suggestions.
            
            For each suggestion:
            1. Identify the specific issue or opportunity
            2. Explain why it matters (performance, security, maintainability, etc.)
            3. Provide a concrete example of how to improve it
            4. Estimate the effort required (low, medium, high)
            
            Focus on the most impactful improvements first.
            Return your suggestions as a JSON array with the following structure:
            
            [
                {{
                    "issue": "Brief description of the issue",
                    "impact": "Why this matters",
                    "suggestion": "Specific suggestion for improvement",
                    "example": "Code example or implementation hint",
                    "effort": "low|medium|high",
                    "category": "performance|security|readability|maintainability|etc."
                }}
            ]
            """
            
            suggestions_response = await self.mcp.process_request_async(
                prompt=suggestions_prompt,
                system="You are an expert software engineer specializing in code improvement. You provide specific, actionable suggestions that help developers enhance their code quality, performance, and maintainability.",
                context={
                    "analysis": analysis,
                    "file_path": file_path
                },
                max_tokens=1536
            )
            
            content = suggestions_response.get("content", "[]")
            
            # Extract JSON array from response
            import re
            json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', content)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            # Clean up the JSON string
            json_str = re.sub(r'(?m)^\s*//.*$', '', json_str)
            
            # Parse JSON
            suggestions = json.loads(json_str)
            return suggestions
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
            return []
    
    async def _generate_commit_feedback(self, commit_id: str, file_feedback: Dict[str, Any], overall_quality: float) -> str:
        """Generate feedback for an entire commit."""
        if not self.mcp:
            # Simple feedback without MCP
            if not file_feedback:
                return "No significant issues found in this commit."
            
            feedback_str = f"Issues found in {len(file_feedback)} files:\n\n"
            for file_path, info in file_feedback.items():
                feedback_str += f"## {file_path} (Quality: {info['quality_score']:.2f})\n"
                feedback_str += info["feedback"] + "\n\n"
            
            return feedback_str
        
        # Use MCP for more sophisticated feedback
        try:
            feedback_prompt = f"""
            Generate comprehensive feedback for commit {commit_id}.
            
            Overall code quality score: {overall_quality:.2f}
            
            Issues were found in {len(file_feedback)} files.
            
            Summarize the key issues across the commit, focusing on:
            1. Common patterns or problems
            2. Most critical issues to address
            3. Overall improvement recommendations
            4. Positive aspects worth highlighting
            
            Format the feedback in markdown for readability.
            """
            
            feedback_response = await self.mcp.process_request_async(
                prompt=feedback_prompt,
                system="You are an expert code reviewer providing feedback on a git commit. Your feedback is clear, comprehensive, and actionable, helping developers improve their code quality.",
                context={
                    "commit_id": commit_id,
                    "file_feedback": file_feedback,
                    "overall_quality": overall_quality
                },
                max_tokens=1536
            )
            
            return feedback_response.get("content", "No feedback available.")
        except Exception as e:
            logger.error(f"Error generating commit feedback: {e}")
            return f"Error generating commit feedback: {str(e)}"
    
    async def _generate_pr_feedback(self, pr_url: str, file_feedback: Dict[str, Any], overall_quality: float) -> str:
        """Generate feedback for a pull request."""
        if not self.mcp:
            # Simple feedback without MCP
            if not file_feedback:
                return "No significant issues found in this pull request."
            
            feedback_str = f"Issues found in {len(file_feedback)} files:\n\n"
            for file_path, info in file_feedback.items():
                feedback_str += f"## {file_path} (Quality: {info['quality_score']:.2f})\n"
                feedback_str += info["feedback"] + "\n\n"
            
            return feedback_str
        
        # Use MCP for more sophisticated feedback
        try:
            feedback_prompt = f"""
            Generate comprehensive feedback for pull request: {pr_url}
            
            Overall code quality score: {overall_quality:.2f}
            
            Issues were found in {len(file_feedback)} files.
            
            Provide a thorough review that:
            1. Summarizes the overall quality and key issues
            2. Highlights critical problems that should be addressed before merging
            3. Suggests specific improvements for the most important issues
            4. Mentions positive aspects and good practices observed
            
            Format your feedback as a professional PR review comment using markdown.
            """
            
            feedback_response = await self.mcp.process_request_async(
                prompt=feedback_prompt,
                system="You are an expert code reviewer providing feedback on a GitHub pull request. Your reviews are thorough, constructive, and balanced, helping developers improve their code while acknowledging positive aspects.",
                context={
                    "pr_url": pr_url,
                    "file_feedback": file_feedback,
                    "overall_quality": overall_quality
                },
                max_tokens=2048
            )
            
            return feedback_response.get("content", "No feedback available.")
        except Exception as e:
            logger.error(f"Error generating PR feedback: {e}")
            return f"Error generating PR feedback: {str(e)}"
    
    async def _post_pr_comment(self, owner: str, repo: str, pr_number: int, comment: str) -> bool:
        """Post a comment on a GitHub pull request."""
        if not self.mcp:
            logger.error("MCP is required to post PR comments")
            return False
        
        try:
            # Use MCP GitHub API to post comment
            response = await self.mcp.process_github_request(
                endpoint=f"/repos/{owner}/{repo}/issues/{pr_number}/comments",
                method="POST",
                data={"body": comment}
            )
            
            return "id" in json.loads(response.get("content", "{}"))
        except Exception as e:
            logger.error(f"Error posting PR comment: {e}")
            return False
    
    def _get_relative_path(self, file_path: str) -> str:
        """Convert an absolute path to a relative path from workspace_dir."""
        try:
            absolute_path = Path(file_path).resolve()
            relative_path = absolute_path.relative_to(self.workspace_dir)
            return str(relative_path)
        except ValueError:
            # If the path is not within workspace_dir, return as is
            return file_path
    
    def _store_feedback_in_memory(self, 
                           file_path: str, 
                           quality_score: float, 
                           feedback: str, 
                           suggestions: List[Dict[str, Any]]):
        """Store feedback in memory for future reference."""
        if not self.memory_manager:
            return
        
        # Create metadata
        metadata = {
            "type": "code_feedback",
            "file_path": file_path,
            "quality_score": quality_score,
            "timestamp": time.time()
        }
        
        # Prepare content
        content = f"""
        Code Quality Feedback for {file_path}
        Quality Score: {quality_score:.2f}
        
        {feedback}
        
        Improvement Suggestions:
        {json.dumps(suggestions, indent=2) if suggestions else "None"}
        """
        
        # Store in memory
        self.memory_manager.add_semantic_memory(
            content=content,
            metadata=metadata
        )
        
        logger.info(f"Stored feedback for {file_path} in memory system")


async def main():
    """Main function for the development feedback bridge CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 Development Feedback Bridge")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # analyze-file command
    analyze_file_parser = subparsers.add_parser("analyze-file", help="Analyze a file and provide feedback")
    analyze_file_parser.add_argument("file_path", help="Path to the file to analyze")
    
    # analyze-commit command
    analyze_commit_parser = subparsers.add_parser("analyze-commit", help="Analyze a git commit")
    analyze_commit_parser.add_argument("--commit", default="HEAD", help="Git commit ID to analyze")
    
    # analyze-staged command
    subparsers.add_parser("analyze-staged", help="Analyze staged files in git")
    
    # analyze-pr command
    analyze_pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a GitHub pull request")
    analyze_pr_parser.add_argument("pr_url", help="URL of the pull request to analyze")
    
    # setup-hooks command
    subparsers.add_parser("setup-hooks", help="Set up git hooks for automatic analysis")
    
    # monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor files for changes")
    monitor_parser.add_argument("--patterns", nargs="+", default=["**/*.py"], help="Glob patterns for files to monitor")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize components
    from vot1.vot_mcp import VotModelControlProtocol
    from vot1.memory import MemoryManager
    from vot1.owl_reasoning import OWLReasoningEngine
    
    workspace_dir = os.getenv("VOT1_WORKSPACE_DIR", os.getcwd())
    
    mcp = VotModelControlProtocol()
    memory_manager = MemoryManager(storage_dir=os.path.join(workspace_dir, "memory"))
    owl_engine = OWLReasoningEngine(
        ontology_path=os.path.join(workspace_dir, "owl", "vot1_ontology.owl"),
        memory_manager=memory_manager
    )
    
    # Create feedback bridge
    bridge = DevelopmentFeedbackBridge(
        mcp=mcp,
        memory_manager=memory_manager,
        owl_engine=owl_engine,
        workspace_dir=workspace_dir
    )
    
    # Execute command
    if args.command == "analyze-file":
        result = await bridge.analyze_file_on_save(args.file_path)
        print(json.dumps(result, indent=2))
    
    elif args.command == "analyze-commit":
        result = await bridge.analyze_git_commit(args.commit)
        print(json.dumps(result, indent=2))
    
    elif args.command == "analyze-staged":
        result = await bridge.analyze_staged_files()
        print(json.dumps(result, indent=2))
        
        if result.get("issues_found", False):
            print("\nCode quality issues found in staged files.")
            sys.exit(1)
    
    elif args.command == "analyze-pr":
        result = await bridge.analyze_pull_request(args.pr_url)
        print(json.dumps(result, indent=2))
    
    elif args.command == "setup-hooks":
        success = await bridge.setup_git_hooks()
        if success:
            print("Git hooks set up successfully!")
        else:
            print("Failed to set up git hooks.")
            sys.exit(1)
    
    elif args.command == "monitor":
        print(f"Starting file monitoring for patterns: {args.patterns}")
        success = await bridge.start_file_monitoring(args.patterns)
        if not success:
            print("Failed to start file monitoring.")
            sys.exit(1)
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Monitoring stopped.")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 