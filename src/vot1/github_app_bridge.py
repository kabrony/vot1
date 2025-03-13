#!/usr/bin/env python3
"""
VOT1 GitHub App Bridge

This module serves as a bridge between the VOT1 system and GitHub, using the MCP GitHub
integration to enable autonomous repository interactions.
It provides functionality for working with repositories, issues, pull requests,
and other GitHub features through the MCP connection.

Key features:
1. Repository analysis and metrics
2. Automated issue and PR creation/management
3. Code review comment automation
4. Commit status reporting
5. Repository improvement tracking
"""

import os
import logging
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubAppBridge:
    """
    Bridge between VOT1 system and GitHub using MCP GitHub integration.
    
    This class provides methods for interacting with GitHub repositories,
    issues, pull requests, and other GitHub features through the MCP 
    GitHub connection.
    """
    
    def __init__(
        self,
        mcp=None,
        memory_manager=None,
        code_analyzer=None,
        feedback_bridge=None,
        default_owner: Optional[str] = None,
        default_repo: Optional[str] = None
    ):
        """
        Initialize the GitHub App Bridge.
        
        Args:
            mcp: VOT Model Control Protocol instance with GitHub integration
            memory_manager: Memory Manager instance
            code_analyzer: Code Analyzer instance
            feedback_bridge: Development Feedback Bridge instance
            default_owner: Default GitHub repository owner/organization
            default_repo: Default GitHub repository name
        """
        self.mcp = mcp
        self.memory_manager = memory_manager
        self.code_analyzer = code_analyzer
        self.feedback_bridge = feedback_bridge
        self.default_owner = default_owner or os.getenv("GITHUB_OWNER")
        self.default_repo = default_repo or os.getenv("GITHUB_REPO")
        
        logger.info(f"Initialized GitHub Bridge for {self.default_owner}/{self.default_repo}")
    
    async def check_connection(self) -> bool:
        """
        Check if the MCP GitHub connection is active.
        
        Returns:
            True if connection is active, False otherwise
        """
        if not self.mcp:
            logger.error("MCP is required for GitHub integration")
            return False
        
        try:
            # Check GitHub connection using MCP's direct capabilities
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_CHECK_ACTIVE_CONNECTION", {
                "params": {
                    "tool": "GitHub",
                    "connection_id": os.getenv("GITHUB_CONNECTION_ID", "")
                }
            })
            
            # Parse JSON response
            response = json.loads(result.get("content", "{}"))
            is_connected = response.get("active", False)
            
            if not is_connected:
                logger.warning("GitHub connection is not active. Some features may not work.")
            else:
                logger.info("GitHub connection is active and ready to use.")
            
            return is_connected
        except Exception as e:
            logger.error(f"Error checking GitHub connection: {e}")
            return False
    
    async def get_required_parameters(self) -> Dict[str, Any]:
        """
        Get the required parameters for GitHub connection.
        
        Returns:
            Dictionary with required parameters or empty dict if none required
        """
        if not self.mcp:
            logger.error("MCP is required for GitHub integration")
            return {}
        
        try:
            # Get required parameters using MCP's direct capabilities
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_GET_REQUIRED_PARAMETERS", {
                "params": {
                    "tool": "GitHub"
                }
            })
            
            # Parse JSON response
            response = json.loads(result.get("content", "{}"))
            return response.get("parameters", {})
        except Exception as e:
            logger.error(f"Error getting required parameters: {e}")
            return {}
    
    async def initiate_connection(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Initiate a connection to GitHub using MCP's direct capabilities.
        
        Args:
            params: Parameters for the connection (if any)
            
        Returns:
            Dictionary with connection results
        """
        if not self.mcp:
            logger.error("MCP is required for GitHub integration")
            return {"success": False, "error": "MCP not initialized"}
        
        try:
            # Initiate GitHub connection
            params = params or {}
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_INITIATE_CONNECTION", {
                "params": {
                    "tool": "GitHub",
                    "parameters": params
                }
            })
            
            # Parse JSON response
            response = json.loads(result.get("content", "{}"))
            connection_id = response.get("connection_id")
            
            if connection_id:
                logger.info(f"GitHub connection initiated successfully with ID: {connection_id}")
                # Store connection ID in environment for future use
                os.environ["GITHUB_CONNECTION_ID"] = connection_id
                return {"success": True, "connection_id": connection_id, "response": response}
            else:
                logger.warning("Failed to initiate GitHub connection.")
                return {"success": False, "error": "No connection ID returned"}
        except Exception as e:
            logger.error(f"Error initiating GitHub connection: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_repository(self, owner: Optional[str] = None, repo: Optional[str] = None, deep_analysis: bool = False) -> Dict[str, Any]:
        """
        Analyze a GitHub repository to gather metrics and insights.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            deep_analysis: Whether to perform a more thorough analysis (includes code quality analysis)
            
        Returns:
            Dictionary with repository analysis results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            logger.info(f"Starting repository analysis for {owner}/{repo} (deep_analysis={deep_analysis})")
            
            # Get repository information
            repo_info = await self._get_repository_info(owner, repo)
            
            # Search for code quality issues
            code_quality_issues = await self._search_code_quality_issues(owner, repo)
            
            # Get recent PRs and their status
            recent_prs = await self._get_recent_pull_requests(owner, repo)
            
            # Get recent commits
            recent_commits = await self._get_recent_commits(owner, repo)
            
            # Get repository structure
            repo_structure = await self._analyze_repository_structure(owner, repo)
            
            # Get commit activity
            commit_activity = await self._analyze_commit_activity(owner, repo)
            
            # Advanced analysis (can be time-consuming)
            code_quality_analysis = {}
            if deep_analysis and self.code_analyzer:
                logger.info(f"Performing deep code quality analysis for {owner}/{repo}")
                code_quality_analysis = await self._perform_code_quality_analysis(owner, repo)
            
            # Store analysis in memory
            if self.memory_manager:
                memory_content = f"""
                Repository Analysis for {owner}/{repo}
                
                Repository Information:
                {json.dumps(repo_info, indent=2)}
                
                Code Quality Issues:
                {json.dumps(code_quality_issues, indent=2)}
                
                Recent Pull Requests:
                {json.dumps(recent_prs, indent=2)}
                
                Recent Commits:
                {json.dumps(recent_commits, indent=2)}
                
                Repository Structure:
                {json.dumps(repo_structure, indent=2)}
                
                Commit Activity:
                {json.dumps(commit_activity, indent=2)}
                
                Code Quality Analysis:
                {json.dumps(code_quality_analysis, indent=2)}
                """
                
                metadata = {
                    "type": "github_repository_analysis",
                    "owner": owner,
                    "repo": repo,
                    "timestamp": time.time(),
                    "deep_analysis": deep_analysis
                }
                
                analysis_memory = self.memory_manager.add_semantic_memory(
                    content=memory_content,
                    metadata=metadata
                )
                logger.info(f"Repository analysis stored in memory: {analysis_memory}")
            
            return {
                "repository": repo_info,
                "code_quality_issues": code_quality_issues,
                "pull_requests": recent_prs,
                "commits": recent_commits,
                "repository_structure": repo_structure,
                "commit_activity": commit_activity,
                "code_quality_analysis": code_quality_analysis,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error analyzing repository {owner}/{repo}: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information using MCP GitHub tools."""
        try:
            # Use GitHub API to get repository info through MCP
            endpoint = f"/repos/{owner}/{repo}"
            
            # Use GitHub API root to get API endpoints
            api_result = await self.mcp.process_tool("mcp_MCP_GITHUB_GITHUB_API_ROOT", {
                "params": {}
            })
            
            # Execute API request through MCP
            result = await self.mcp.process_github_request(
                endpoint=endpoint,
                method="GET"
            )
            
            return json.loads(result.get("content", "{}"))
        except Exception as e:
            logger.error(f"Error getting repository info: {e}")
            return {}
    
    async def _search_code_quality_issues(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Search for code quality issues in the repository using MCP GitHub tools."""
        try:
            # Use GitHub search API to find code quality issues through MCP
            search_query = f"repo:{owner}/{repo} TODO OR FIXME OR HACK OR BUG in:file"
            
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_SEARCH_REPOSITORIES", {
                "params": {
                    "q": search_query
                }
            })
            
            response = json.loads(result.get("content", "{}"))
            return response.get("items", [])
        except Exception as e:
            logger.error(f"Error searching code quality issues: {e}")
            return []
    
    async def _get_recent_pull_requests(self, owner: str, repo: str, state: str = "all", limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent pull requests for a repository using MCP GitHub tools."""
        try:
            # Use direct MCP GitHub API to get recent PRs
            endpoint = f"/repos/{owner}/{repo}/pulls?state={state}&per_page={limit}"
            
            result = await self.mcp.process_github_request(
                endpoint=endpoint,
                method="GET"
            )
            
            return json.loads(result.get("content", "[]"))
        except Exception as e:
            logger.error(f"Error getting recent pull requests: {e}")
            return []
    
    async def _get_recent_commits(self, owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commits for a repository using MCP GitHub tools."""
        try:
            # Use direct MCP GitHub API to get recent commits
            endpoint = f"/repos/{owner}/{repo}/commits?per_page={limit}"
            
            result = await self.mcp.process_github_request(
                endpoint=endpoint,
                method="GET"
            )
            
            return json.loads(result.get("content", "[]"))
        except Exception as e:
            logger.error(f"Error getting recent commits: {e}")
            return []
    
    async def create_issue(
        self, 
        title: str, 
        body: str, 
        owner: Optional[str] = None, 
        repo: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue in the repository using MCP GitHub tools.
        
        Args:
            title: Issue title
            body: Issue body/description
            owner: Repository owner or organization
            repo: Repository name
            labels: List of labels to apply
            assignees: List of users to assign
            
        Returns:
            Dictionary with issue creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Prepare issue parameters
            params = {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body
            }
            
            if labels:
                params["labels"] = labels
                
            if assignees:
                params["assignees"] = assignees
            
            # Create the issue using MCP GitHub direct tool
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_CREATE_AN_ISSUE", {
                "params": params
            })
            
            response = json.loads(result.get("content", "{}"))
            
            # Store in memory if successful
            if "number" in response and self.memory_manager:
                memory_content = f"""
                Created GitHub Issue:
                Repository: {owner}/{repo}
                Issue Number: {response.get('number')}
                Title: {title}
                Body: {body}
                Labels: {labels if labels else []}
                Assignees: {assignees if assignees else []}
                """
                
                metadata = {
                    "type": "github_issue_created",
                    "owner": owner,
                    "repo": repo,
                    "issue_number": response.get('number'),
                    "title": title,
                    "timestamp": time.time()
                }
                
                self.memory_manager.add_semantic_memory(
                    content=memory_content,
                    metadata=metadata
                )
            
            return {
                "success": "number" in response,
                "issue": response,
                "url": response.get("html_url", "")
            }
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new pull request using MCP GitHub tools.
        
        Args:
            title: PR title
            body: PR description
            head: The name of the branch where changes are implemented
            base: The branch to merge changes into (default: main)
            owner: Repository owner or organization
            repo: Repository name
            draft: Whether to create a draft PR
            
        Returns:
            Dictionary with PR creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Prepare PR parameters
            params = {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft
            }
            
            # Create the PR using MCP GitHub direct tool
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_CREATE_A_PULL_REQUEST", {
                "params": params
            })
            
            response = json.loads(result.get("content", "{}"))
            
            # Store in memory if successful
            if "number" in response and self.memory_manager:
                memory_content = f"""
                Created GitHub Pull Request:
                Repository: {owner}/{repo}
                PR Number: {response.get('number')}
                Title: {title}
                Body: {body}
                From branch: {head}
                To branch: {base}
                Draft: {draft}
                """
                
                metadata = {
                    "type": "github_pr_created",
                    "owner": owner,
                    "repo": repo,
                    "pr_number": response.get('number'),
                    "title": title,
                    "head": head,
                    "base": base,
                    "timestamp": time.time()
                }
                
                self.memory_manager.add_semantic_memory(
                    content=memory_content,
                    metadata=metadata
                )
            
            return {
                "success": "number" in response,
                "pull_request": response,
                "url": response.get("html_url", "")
            }
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def add_pr_comment(
        self,
        pr_number: int,
        body: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a pull request using MCP GitHub tools.
        
        Args:
            pr_number: PR number
            body: Comment body
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with comment creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Add comment to the PR using MCP GitHub direct tool
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_CREATE_AN_ISSUE_COMMENT", {
                "params": {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": pr_number,
                    "body": body
                }
            })
            
            response = json.loads(result.get("content", "{}"))
            
            return {
                "success": "id" in response,
                "comment": response,
                "url": response.get("html_url", "")
            }
        except Exception as e:
            logger.error(f"Error adding PR comment: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def add_pr_review_comment(
        self,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
        owner: Optional[str] = None,
        repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a review comment to a specific line in a pull request using MCP GitHub tools.
        
        Args:
            pr_number: PR number
            body: Comment body
            commit_id: The SHA of the commit to comment on
            path: The relative path to the file to comment on
            line: The line number to comment on
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with review comment creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Add review comment to the PR using MCP GitHub direct tool
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_CREATE_A_REVIEW_COMMENT_FOR_A_PULL_REQUEST", {
                "params": {
                    "owner": owner,
                    "repo": repo,
                    "pull_number": pr_number,
                    "body": body,
                    "commit_id": commit_id,
                    "path": path,
                    "line": line,
                    "side": "RIGHT"  # RIGHT is for additions
                }
            })
            
            response = json.loads(result.get("content", "{}"))
            
            return {
                "success": "id" in response,
                "comment": response,
                "url": response.get("html_url", "")
            }
        except Exception as e:
            logger.error(f"Error adding PR review comment: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def analyze_pull_request(
        self,
        pr_number: int,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        with_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a pull request and optionally provide feedback using MCP GitHub tools.
        
        Args:
            pr_number: PR number
            owner: Repository owner or organization
            repo: Repository name
            with_feedback: Whether to generate and post feedback
            
        Returns:
            Dictionary with PR analysis results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Get PR details using MCP GitHub direct tool
            pr_result = await self.mcp.process_tool("mcp_MCP_GITHUB_GET_A_PULL_REQUEST", {
                "params": {
                    "owner": owner,
                    "repo": repo,
                    "pull_number": pr_number
                }
            })
            
            pr_details = json.loads(pr_result.get("content", "{}"))
            
            # Get PR commits using MCP GitHub direct tool
            commits_result = await self.mcp.process_tool("mcp_MCP_GITHUB_LIST_COMMITS_ON_A_PULL_REQUEST", {
                "params": {
                    "owner": owner,
                    "repo": repo,
                    "pull_number": pr_number
                }
            })
            
            commits = json.loads(commits_result.get("content", "[]"))
            
            # Get detailed information about the latest commit
            latest_commit = commits[0] if commits else None
            commit_details = None
            
            if latest_commit and "sha" in latest_commit:
                commit_result = await self.mcp.process_tool("mcp_MCP_GITHUB_GET_A_COMMIT", {
                    "params": {
                        "owner": owner,
                        "repo": repo,
                        "ref": latest_commit["sha"]
                    }
                })
                
                commit_details = json.loads(commit_result.get("content", "{}"))
            
            # Analyze PR and generate feedback if requested
            analysis_result = {
                "pull_request": pr_details,
                "commits": commits,
                "latest_commit_details": commit_details
            }
            
            # Use Development Feedback Bridge to analyze code quality if available
            feedback = None
            
            if with_feedback and self.feedback_bridge:
                # Use the PR URL to analyze
                pr_url = pr_details.get("html_url", "")
                if pr_url:
                    feedback = await self.feedback_bridge.analyze_pull_request(pr_url)
                    analysis_result["code_quality_feedback"] = feedback
                    
                    # Store analysis in memory
                    if self.memory_manager:
                        memory_content = f"""
                        Pull Request Analysis for {owner}/{repo}#{pr_number}
                        
                        Title: {pr_details.get('title', 'No title')}
                        Author: {pr_details.get('user', {}).get('login', 'Unknown')}
                        
                        Commits: {len(commits)}
                        Files Changed: {pr_details.get('changed_files', 0)}
                        Additions: {pr_details.get('additions', 0)}
                        Deletions: {pr_details.get('deletions', 0)}
                        
                        Code Quality Feedback:
                        {json.dumps(feedback, indent=2) if feedback else "No feedback available"}
                        """
                        
                        metadata = {
                            "type": "github_pr_analysis",
                            "owner": owner,
                            "repo": repo,
                            "pr_number": pr_number,
                            "title": pr_details.get('title', 'No title'),
                            "timestamp": time.time()
                        }
                        
                        self.memory_manager.add_semantic_memory(
                            content=memory_content,
                            metadata=metadata
                        )
            
            return {
                "success": True,
                "analysis": analysis_result
            }
        except Exception as e:
            logger.error(f"Error analyzing pull request: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def star_repository(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Star a GitHub repository using MCP GitHub tools.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with star operation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Star the repository using MCP GitHub direct tool
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_STAR_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER", {
                "params": {
                    "owner": owner,
                    "repo": repo
                }
            })
            
            response = json.loads(result.get("content", "{}"))
            
            return {
                "success": response.get("status_code", 0) in [204, 200],
                "message": f"Repository {owner}/{repo} starred successfully"
            }
        except Exception as e:
            logger.error(f"Error starring repository: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def create_improvement_issue(
        self,
        component_path: str,
        analysis_result: Dict[str, Any],
        owner: Optional[str] = None,
        repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an issue with improvement suggestions for a component.
        
        Args:
            component_path: Path to the component
            analysis_result: Analysis result from code analyzer
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with issue creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            # Extract quality score and suggestions
            quality_score = analysis_result.get("quality_score", 0.0)
            feedback = analysis_result.get("feedback", "No feedback available")
            suggestions = analysis_result.get("suggestions", [])
            
            # Generate issue title
            title = f"Improvement Suggestions for {component_path}"
            
            # Generate issue body
            body = f"""
## Improvement Suggestions for `{component_path}`

Current Quality Score: **{quality_score:.2f}** / 1.00

### Analysis Feedback

{feedback}

### Specific Improvement Suggestions

{self._format_suggestions_for_markdown(suggestions)}

---
*This issue was automatically generated by VOT1 Autonomous Feedback System.*
            """
            
            # Create issue with appropriate labels
            labels = ["improvement", "autonomous-feedback"]
            
            # Add quality level label based on score
            if quality_score < 0.5:
                labels.append("high-priority")
            elif quality_score < 0.7:
                labels.append("medium-priority")
            else:
                labels.append("low-priority")
            
            # Create the issue
            return await self.create_issue(
                title=title,
                body=body,
                owner=owner,
                repo=repo,
                labels=labels
            )
        except Exception as e:
            logger.error(f"Error creating improvement issue: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _format_suggestions_for_markdown(self, suggestions: List[Dict[str, Any]]) -> str:
        """Format improvement suggestions for GitHub markdown."""
        if not suggestions:
            return "*No specific suggestions available.*"
        
        markdown = ""
        
        for i, suggestion in enumerate(suggestions, 1):
            issue = suggestion.get("issue", "Unknown issue")
            impact = suggestion.get("impact", "")
            suggestion_text = suggestion.get("suggestion", "")
            example = suggestion.get("example", "")
            effort = suggestion.get("effort", "unknown")
            category = suggestion.get("category", "general")
            
            markdown += f"### {i}. {issue}\n\n"
            
            if category:
                markdown += f"**Category:** {category}\n\n"
                
            if impact:
                markdown += f"**Impact:** {impact}\n\n"
                
            if suggestion_text:
                markdown += f"**Suggestion:** {suggestion_text}\n\n"
                
            if example:
                markdown += f"**Example:**\n\n```\n{example}\n```\n\n"
                
            markdown += f"**Required Effort:** {effort}\n\n"
            markdown += "---\n\n"
        
        return markdown

    async def _analyze_repository_structure(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze the repository's structure to understand its organization.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with repository structure information
        """
        try:
            # This would ideally use the GitHub API to get the repository structure
            # For now, we'll use a simple approach to identify key files and directories
            
            # Check for common files
            has_readme = await self._check_file_exists(owner, repo, "README.md")
            has_license = await self._check_file_exists(owner, repo, "LICENSE")
            has_contributing = await self._check_file_exists(owner, repo, "CONTRIBUTING.md")
            has_coc = await self._check_file_exists(owner, repo, "CODE_OF_CONDUCT.md")
            has_gitignore = await self._check_file_exists(owner, repo, ".gitignore")
            has_github_dir = await self._check_file_exists(owner, repo, ".github")
            
            # Check for language-specific files
            has_requirements = await self._check_file_exists(owner, repo, "requirements.txt")
            has_setup_py = await self._check_file_exists(owner, repo, "setup.py")
            has_package_json = await self._check_file_exists(owner, repo, "package.json")
            has_cargo_toml = await self._check_file_exists(owner, repo, "Cargo.toml")
            has_gemfile = await self._check_file_exists(owner, repo, "Gemfile")
            has_go_mod = await self._check_file_exists(owner, repo, "go.mod")
            
            # Identify probable primary language based on files
            language = "unknown"
            if has_requirements or has_setup_py:
                language = "Python"
            elif has_package_json:
                language = "JavaScript/TypeScript"
            elif has_cargo_toml:
                language = "Rust"
            elif has_gemfile:
                language = "Ruby"
            elif has_go_mod:
                language = "Go"
            
            return {
                "common_files": {
                    "readme": has_readme,
                    "license": has_license,
                    "contributing": has_contributing,
                    "code_of_conduct": has_coc,
                    "gitignore": has_gitignore,
                    "github_directory": has_github_dir
                },
                "language_specific_files": {
                    "requirements_txt": has_requirements,
                    "setup_py": has_setup_py,
                    "package_json": has_package_json,
                    "cargo_toml": has_cargo_toml,
                    "gemfile": has_gemfile,
                    "go_mod": has_go_mod
                },
                "probable_language": language
            }
        except Exception as e:
            logger.error(f"Error analyzing repository structure for {owner}/{repo}: {e}")
            return {"error": str(e)}
    
    async def _check_file_exists(self, owner: str, repo: str, path: str) -> bool:
        """Check if a file exists in a repository using GitHub API."""
        try:
            # We're approximating this by searching for the file
            # A proper implementation would use the GitHub contents API
            search_query = f"filename:{path} repo:{owner}/{repo}"
            
            result = await self.mcp.process_tool("mcp_MCP_GITHUB_SEARCH_REPOSITORIES", {
                "params": {
                    "q": search_query,
                    "per_page": 1
                }
            })
            
            response = json.loads(result.get("content", "{}"))
            total_count = response.get("total_count", 0)
            
            return total_count > 0
        except Exception as e:
            logger.error(f"Error checking if file {path} exists: {e}")
            return False
    
    async def _analyze_commit_activity(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze commit activity to determine project health and activity levels.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with commit activity analysis
        """
        try:
            # Get the last 100 commits to analyze
            commits = await self._get_recent_commits(owner, repo, limit=100)
            
            if not commits:
                return {"error": "No commits found"}
            
            # Analyze commit frequency
            commit_dates = [commit.get("commit", {}).get("author", {}).get("date") for commit in commits if "commit" in commit]
            commit_dates = [date for date in commit_dates if date]  # Filter out None values
            
            # Convert to datetime objects
            import dateutil.parser
            commit_datetimes = [dateutil.parser.parse(date) for date in commit_dates]
            commit_datetimes.sort()
            
            # Calculate time between commits
            if len(commit_datetimes) > 1:
                time_diffs = []
                for i in range(1, len(commit_datetimes)):
                    diff = commit_datetimes[i] - commit_datetimes[i-1]
                    time_diffs.append(diff.total_seconds())
                
                avg_seconds_between_commits = sum(time_diffs) / len(time_diffs)
                
                # Get the most recent commit date
                most_recent = commit_datetimes[-1] if commit_datetimes else None
                oldest = commit_datetimes[0] if commit_datetimes else None
                
                # Get unique authors
                author_emails = {}
                for commit in commits:
                    commit_info = commit.get("commit", {})
                    author = commit_info.get("author", {})
                    email = author.get("email")
                    name = author.get("name")
                    if email and name:
                        author_emails[email] = name
                
                unique_authors = len(author_emails)
                
                # Determine if project is actively maintained
                import datetime
                now = datetime.datetime.now(datetime.timezone.utc)
                
                if most_recent:
                    days_since_last_commit = (now - most_recent).days
                    is_active = days_since_last_commit < 90  # Less than 90 days
                else:
                    days_since_last_commit = None
                    is_active = False
                
                return {
                    "total_commits_analyzed": len(commits),
                    "unique_contributors": unique_authors,
                    "most_recent_commit": most_recent.isoformat() if most_recent else None,
                    "oldest_commit_analyzed": oldest.isoformat() if oldest else None,
                    "average_days_between_commits": avg_seconds_between_commits / (60 * 60 * 24),
                    "days_since_last_commit": days_since_last_commit,
                    "is_actively_maintained": is_active
                }
            else:
                return {
                    "total_commits_analyzed": len(commits),
                    "unique_contributors": 1,
                    "is_actively_maintained": False,
                    "error": "Not enough commits to analyze activity properly"
                }
        except Exception as e:
            logger.error(f"Error analyzing commit activity for {owner}/{repo}: {e}")
            return {"error": str(e)}
    
    async def _perform_code_quality_analysis(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Perform detailed code quality analysis on the repository.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with code quality analysis results
        """
        if not self.code_analyzer:
            return {"error": "Code analyzer not initialized"}
        
        try:
            # In a real implementation, we'd clone the repository and analyze it
            # For this example, we'll use MCP to get a general assessment
            
            prompt = f"""
            Analyze the code quality of the GitHub repository {owner}/{repo}.
            
            Specifically, assess:
            1. Code maintainability
            2. Technical debt
            3. Architecture quality
            4. Test coverage (if applicable)
            5. Documentation quality
            6. Common code smells
            
            Format your response as a JSON object with keys for each aspect
            and numerical scores from 0-1 where appropriate.
            Include a "suggestions" array with specific improvement recommendations.
            """
            
            # Get a structured analysis using MCP
            response = await self.mcp.process_request(prompt, max_tokens=2000)
            
            try:
                # Try to parse JSON from the response
                import re
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response.get("content", ""))
                
                if json_match:
                    analysis_json = json.loads(json_match.group(1))
                else:
                    # Fallback if no JSON block found
                    analysis_json = {
                        "error": "Could not extract structured analysis",
                        "raw_response": response.get("content", "").strip()
                    }
                    
                return analysis_json
            except Exception as json_err:
                logger.error(f"Error parsing code quality analysis JSON: {json_err}")
                return {
                    "error": "Failed to parse analysis result",
                    "raw_response": response.get("content", "").strip()
                }
        except Exception as e:
            logger.error(f"Error performing code quality analysis for {owner}/{repo}: {e}")
            return {"error": str(e)}

    async def run_autonomous_improvement_cycle(
        self,
        components: List[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        max_improvements: int = 3,
        create_prs: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete autonomous improvement cycle for the repository.
        
        This method:
        1. Analyzes the repository
        2. Identifies components that could be improved
        3. Generates improvements for each component
        4. Creates PRs with the improvements (optional)
        
        Args:
            components: List of component paths to improve (if None, will detect automatically)
            owner: Repository owner or organization
            repo: Repository name
            max_improvements: Maximum number of improvements to make
            create_prs: Whether to create PRs for the improvements
            
        Returns:
            Dictionary with improvement results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            logger.info(f"Starting autonomous improvement cycle for {owner}/{repo}")
            
            # Step 1: Analyze the repository
            analysis_result = await self.analyze_repository(owner, repo, deep_analysis=True)
            
            if not analysis_result.get("success", False):
                return {"error": "Repository analysis failed", "success": False}
            
            # Step 2: Identify components to improve if not provided
            if not components:
                components = await self._identify_improvement_candidates(
                    analysis_result,
                    owner,
                    repo,
                    max_candidates=max_improvements
                )
                
                if not components:
                    return {
                        "message": "No components identified for improvement",
                        "success": True,
                        "improvements": []
                    }
            
            # Step 3: Generate improvements for each component
            improvements = []
            
            for component_path in components[:max_improvements]:
                logger.info(f"Generating improvement for component: {component_path}")
                
                # 3.1 Analyze the component
                component_analysis = None
                
                if self.code_analyzer:
                    # In a real implementation, we'd analyze the actual file content
                    # For this example, we'll skip detailed analysis
                    pass
                
                # 3.2 Create an improvement issue
                issue_result = await self.create_improvement_issue(
                    component_path,
                    component_analysis or {},
                    owner,
                    repo
                )
                
                if issue_result.get("success", False):
                    improvements.append({
                        "component": component_path,
                        "issue": issue_result.get("issue", {}),
                        "pr": None
                    })
                
                # 3.3 Create a PR with the improvement if requested
                if create_prs and self.code_analyzer and self.feedback_bridge:
                    # This would require more implementation to:
                    # - Create a branch
                    # - Generate code improvements
                    # - Commit changes
                    # - Create PR
                    # We'll skip this for the current implementation
                    pass
            
            return {
                "success": True,
                "components_analyzed": len(components),
                "improvements": improvements
            }
        except Exception as e:
            logger.error(f"Error in autonomous improvement cycle for {owner}/{repo}: {e}")
            return {"error": str(e), "success": False}
    
    async def _identify_improvement_candidates(
        self,
        analysis_result: Dict[str, Any],
        owner: str,
        repo: str,
        max_candidates: int = 3
    ) -> List[str]:
        """
        Identify components that would benefit most from improvements.
        
        Args:
            analysis_result: Repository analysis results
            owner: Repository owner
            repo: Repository name
            max_candidates: Maximum number of candidates to return
            
        Returns:
            List of component paths to improve
        """
        try:
            # This would typically involve:
            # 1. Examining code quality metrics
            # 2. Looking at test coverage
            # 3. Identifying frequently changed files
            # 4. Finding files with many issues or bugs
            
            # For this example, we'll return some default components for Python projects
            repo_info = analysis_result.get("repository", {})
            language = repo_info.get("language", "")
            
            if language.lower() == "python":
                return [
                    "src/main.py",
                    "src/utils.py",
                    "tests/test_main.py"
                ][:max_candidates]
            elif language.lower() in ["javascript", "typescript"]:
                return [
                    "src/index.js",
                    "src/utils.js",
                    "tests/index.test.js"
                ][:max_candidates]
            else:
                # Generic candidates
                return [
                    "README.md",
                    "src/main",
                    "src/utils"
                ][:max_candidates]
        except Exception as e:
            logger.error(f"Error identifying improvement candidates: {e}")
            return []

    async def generate_health_check_report(
        self, 
        owner: Optional[str] = None, 
        repo: Optional[str] = None,
        create_issue: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive health check report for the repository.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            create_issue: Whether to create an issue with the report
            
        Returns:
            Dictionary with health check results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        try:
            logger.info(f"Generating health check report for {owner}/{repo}")
            
            # Step 1: Analyze the repository
            analysis_result = await self.analyze_repository(owner, repo, deep_analysis=True)
            
            if not analysis_result.get("success", False):
                return {"error": "Repository analysis failed", "success": False}
            
            # Step 2: Generate a health score
            repo_structure = analysis_result.get("repository_structure", {})
            commit_activity = analysis_result.get("commit_activity", {})
            
            # Calculate scores for different aspects
            documentation_score = self._calculate_documentation_score(repo_structure)
            activity_score = self._calculate_activity_score(commit_activity)
            community_score = self._calculate_community_score(repo_structure, analysis_result.get("repository", {}))
            
            # Calculate overall health score (0-1)
            health_score = (documentation_score + activity_score + community_score) / 3
            
            # Generate improvements
            improvements = self._generate_health_improvements(
                documentation_score, 
                activity_score, 
                community_score, 
                repo_structure,
                commit_activity
            )
            
            # Create report
            report = {
                "repository": f"{owner}/{repo}",
                "timestamp": time.time(),
                "health_score": health_score,
                "documentation_score": documentation_score,
                "activity_score": activity_score,
                "community_score": community_score,
                "improvement_suggestions": improvements,
                "raw_analysis": analysis_result
            }
            
            # Create issue if requested
            issue = None
            if create_issue:
                issue_title = f"Repository Health Check: {health_score:.2f}/1.00"
                
                issue_body = f"""
                # Repository Health Check Report
                
                **Overall Health Score:** {health_score:.2f}/1.00
                
                ## Scores by Category
                
                - **Documentation:** {documentation_score:.2f}/1.00
                - **Activity:** {activity_score:.2f}/1.00
                - **Community:** {community_score:.2f}/1.00
                
                ## Improvement Suggestions
                
                {self._format_improvements_for_markdown(improvements)}
                
                ---
                
                This report was automatically generated by the VOT1 GitHub integration.
                """
                
                issue_result = await self.create_issue(
                    title=issue_title,
                    body=issue_body,
                    owner=owner,
                    repo=repo,
                    labels=["health-check", "documentation"]
                )
                
                if issue_result.get("success", False):
                    issue = issue_result.get("issue", {})
                    report["issue"] = issue
            
            return {
                "success": True,
                "health_check": report,
                "issue": issue
            }
        except Exception as e:
            logger.error(f"Error generating health check report for {owner}/{repo}: {e}")
            return {"error": str(e), "success": False}
    
    def _calculate_documentation_score(self, repo_structure: Dict[str, Any]) -> float:
        """Calculate a score for repository documentation (0-1)."""
        score = 0.0
        common_files = repo_structure.get("common_files", {})
        
        # Add points for each documentation file
        if common_files.get("readme", False):
            score += 0.4
        if common_files.get("contributing", False):
            score += 0.2
        if common_files.get("code_of_conduct", False):
            score += 0.1
        if common_files.get("license", False):
            score += 0.3
            
        # Cap at 1.0
        return min(score, 1.0)
    
    def _calculate_activity_score(self, commit_activity: Dict[str, Any]) -> float:
        """Calculate a score for repository activity (0-1)."""
        if "error" in commit_activity:
            return 0.3  # Default score if we couldn't analyze
            
        score = 0.0
        
        # Activity score based on recency and frequency
        is_active = commit_activity.get("is_actively_maintained", False)
        days_since_last_commit = commit_activity.get("days_since_last_commit", 999)
        unique_contributors = commit_activity.get("unique_contributors", 0)
        
        if is_active:
            score += 0.5
        elif days_since_last_commit is not None:
            # Gradually decrease score as time since last commit increases
            if days_since_last_commit < 180:  # Within 6 months
                score += 0.3
            elif days_since_last_commit < 365:  # Within 1 year
                score += 0.1
                
        # Add points for multiple contributors
        if unique_contributors > 5:
            score += 0.5
        elif unique_contributors > 1:
            score += 0.3
        else:
            score += 0.1
            
        # Cap at 1.0
        return min(score, 1.0)
    
    def _calculate_community_score(self, repo_structure: Dict[str, Any], repo_info: Dict[str, Any]) -> float:
        """Calculate a score for community aspects of the repository (0-1)."""
        score = 0.0
        common_files = repo_structure.get("common_files", {})
        
        # Community files
        if common_files.get("contributing", False):
            score += 0.3
        if common_files.get("code_of_conduct", False):
            score += 0.2
        if common_files.get("github_directory", False):
            score += 0.1
            
        # Issues and PRs
        has_issues = repo_info.get("has_issues", False)
        open_issues_count = repo_info.get("open_issues_count", 0)
        
        if has_issues:
            score += 0.1
        if open_issues_count > 0:
            score += 0.1
            
        # Stars and forks
        stars = repo_info.get("stargazers_count", 0)
        forks = repo_info.get("forks_count", 0)
        
        if stars > 100:
            score += 0.2
        elif stars > 10:
            score += 0.1
            
        if forks > 10:
            score += 0.1
            
        # Cap at 1.0
        return min(score, 1.0)
    
    def _generate_health_improvements(
        self, 
        documentation_score: float, 
        activity_score: float, 
        community_score: float,
        repo_structure: Dict[str, Any],
        commit_activity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on health check results."""
        improvements = []
        common_files = repo_structure.get("common_files", {})
        
        # Documentation improvements
        if documentation_score < 0.7:
            if not common_files.get("readme", False):
                improvements.append({
                    "category": "documentation",
                    "priority": "high",
                    "suggestion": "Add a README.md file to explain what the project does and how to use it."
                })
                
            if not common_files.get("license", False):
                improvements.append({
                    "category": "documentation",
                    "priority": "medium",
                    "suggestion": "Add a LICENSE file to clarify how others can use your code."
                })
                
            if not common_files.get("contributing", False):
                improvements.append({
                    "category": "documentation",
                    "priority": "low",
                    "suggestion": "Add a CONTRIBUTING.md file to help others contribute to the project."
                })
                
        # Activity improvements
        if activity_score < 0.7:
            days_since_last_commit = commit_activity.get("days_since_last_commit", 0)
            
            if days_since_last_commit and days_since_last_commit > 180:
                improvements.append({
                    "category": "activity",
                    "priority": "medium",
                    "suggestion": f"Repository hasn't been updated in {days_since_last_commit} days. Consider adding a status note to the README if it's no longer maintained."
                })
                
            unique_contributors = commit_activity.get("unique_contributors", 0)
            if unique_contributors < 2:
                improvements.append({
                    "category": "activity",
                    "priority": "low",
                    "suggestion": "Consider reaching out to the community to get more contributors involved."
                })
                
        # Community improvements
        if community_score < 0.7:
            if not common_files.get("code_of_conduct", False):
                improvements.append({
                    "category": "community",
                    "priority": "medium",
                    "suggestion": "Add a CODE_OF_CONDUCT.md file to establish community norms."
                })
                
            if not common_files.get("github_directory", False):
                improvements.append({
                    "category": "community",
                    "priority": "low",
                    "suggestion": "Add a .github directory with issue templates and workflows to streamline contributions."
                })
        
        return improvements
    
    def _format_improvements_for_markdown(self, improvements: List[Dict[str, Any]]) -> str:
        """Format the improvements list as Markdown."""
        if not improvements:
            return "_No specific improvements recommended at this time._"
            
        markdown = ""
        
        # Group by category
        by_category = {}
        for imp in improvements:
            category = imp.get("category", "other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(imp)
            
        # Format each category
        for category, items in by_category.items():
            markdown += f"### {category.title()}\n\n"
            
            for item in items:
                priority = item.get("priority", "medium").upper()
                suggestion = item.get("suggestion", "")
                
                markdown += f"- **[{priority}]** {suggestion}\n"
            
            markdown += "\n"
            
        return markdown


async def main():
    """Main function to demonstrate GitHub App Bridge usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 GitHub Integration Bridge")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # check-connection command
    subparsers.add_parser("check-connection", help="Check GitHub connection status")
    
    # initiate-connection command
    subparsers.add_parser("initiate-connection", help="Initiate a GitHub connection")
    
    # analyze-repo command
    analyze_repo_parser = subparsers.add_parser("analyze-repo", help="Analyze a GitHub repository")
    analyze_repo_parser.add_argument("--owner", help="Repository owner or organization")
    analyze_repo_parser.add_argument("--repo", help="Repository name")
    
    # analyze-pr command
    analyze_pr_parser = subparsers.add_parser("analyze-pr", help="Analyze a GitHub pull request")
    analyze_pr_parser.add_argument("pr_number", type=int, help="Pull request number")
    analyze_pr_parser.add_argument("--owner", help="Repository owner or organization")
    analyze_pr_parser.add_argument("--repo", help="Repository name")
    
    # create-issue command
    create_issue_parser = subparsers.add_parser("create-issue", help="Create a GitHub issue")
    create_issue_parser.add_argument("title", help="Issue title")
    create_issue_parser.add_argument("body", help="Issue body")
    create_issue_parser.add_argument("--labels", nargs="+", help="Labels to apply")
    create_issue_parser.add_argument("--owner", help="Repository owner or organization")
    create_issue_parser.add_argument("--repo", help="Repository name")
    
    # star-repo command
    star_repo_parser = subparsers.add_parser("star-repo", help="Star a GitHub repository")
    star_repo_parser.add_argument("--owner", help="Repository owner or organization")
    star_repo_parser.add_argument("--repo", help="Repository name")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize components
    from vot1.vot_mcp import VotModelControlProtocol
    from vot1.memory import MemoryManager
    from vot1.code_analyzer import create_analyzer
    from vot1.development_feedback_bridge import DevelopmentFeedbackBridge
    
    mcp = VotModelControlProtocol()
    memory_manager = MemoryManager()
    code_analyzer = create_analyzer(mcp=mcp)
    feedback_bridge = DevelopmentFeedbackBridge(mcp=mcp, code_analyzer=code_analyzer)
    
    # Create GitHub bridge
    github_bridge = GitHubAppBridge(
        mcp=mcp,
        memory_manager=memory_manager,
        code_analyzer=code_analyzer,
        feedback_bridge=feedback_bridge
    )
    
    # Execute command
    if args.command == "check-connection":
        is_connected = await github_bridge.check_connection()
        print(f"GitHub connection active: {is_connected}")
    
    elif args.command == "initiate-connection":
        params = await github_bridge.get_required_parameters()
        print(f"Required parameters: {json.dumps(params, indent=2)}")
        
        if params:
            print("Please provide the required parameters for connection.")
            # In a real application, would collect params from user
            connection_params = {}
        else:
            connection_params = {}
            
        result = await github_bridge.initiate_connection(connection_params)
        print(json.dumps(result, indent=2))
    
    elif args.command == "analyze-repo":
        result = await github_bridge.analyze_repository(args.owner, args.repo)
        print(json.dumps(result, indent=2))
    
    elif args.command == "analyze-pr":
        result = await github_bridge.analyze_pull_request(args.pr_number, args.owner, args.repo)
        print(json.dumps(result, indent=2))
    
    elif args.command == "create-issue":
        result = await github_bridge.create_issue(
            title=args.title,
            body=args.body,
            owner=args.owner,
            repo=args.repo,
            labels=args.labels
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "star-repo":
        result = await github_bridge.star_repository(args.owner, args.repo)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 