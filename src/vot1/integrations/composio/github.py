"""
VOT1 GitHub Integration via Composio

This module provides specialized GitHub integration utilizing Composio's
extensive API capabilities. It enables repository analysis, code quality assessment,
issue management, and autonomous improvement workflows.

Copyright 2025 Village of Thousands
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from vot1.integrations.composio import (
    ComposioAuthManager,
    ComposioConnector,
    ComposioToolRegistry,
    ComposioAPIError,
    ComposioRateLimitError
)

# Setup logging
logger = logging.getLogger(__name__)

class GitHubComposioIntegration:
    """GitHub integration using Composio's API capabilities"""
    
    def __init__(self, auth_manager: ComposioAuthManager = None, api_key: str = None):
        """
        Initialize the GitHub integration with Composio
        
        Args:
            auth_manager: An existing ComposioAuthManager instance
            api_key: Composio API key (if auth_manager not provided)
        """
        if not auth_manager and not api_key:
            api_key = os.environ.get("COMPOSIO_API_KEY")
            if not api_key:
                raise ValueError("Either auth_manager or api_key must be provided")
        
        self.auth_manager = auth_manager or ComposioAuthManager(api_key)
        self.connector = ComposioConnector(self.auth_manager)
        self.tool_registry = ComposioToolRegistry(self.auth_manager)
        self.github_tool = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the integration and verify GitHub tool availability"""
        if not self.auth_manager.session:
            await self.auth_manager.initialize()
            
        try:
            # Get GitHub tool details
            tool_details = await self.tool_registry.get_tool_details("github")
            self.github_tool = tool_details
            self._initialized = True
            logger.info(f"GitHub tool initialized with {len(tool_details.get('actions', []))} available actions")
            return tool_details
        except Exception as e:
            logger.error(f"Failed to initialize GitHub integration: {e}")
            raise RuntimeError(f"GitHub integration initialization failed: {e}")
    
    async def _ensure_initialized(self):
        """Ensure the integration is initialized before use"""
        if not self._initialized:
            await self.initialize()
        
    async def analyze_repository(
        self, 
        owner: str, 
        repo: str, 
        branch: str = "main",
        llm_model: str = "gpt-4o-mini", 
        deep_analysis: bool = False,
        include_security: bool = True,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository using Composio's advanced analysis capabilities
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            branch: Branch to analyze (default: main)
            llm_model: LLM model to use for analysis (default: gpt-4o-mini)
            deep_analysis: Whether to perform deep analysis (more thorough but slower)
            include_security: Whether to include security analysis
            focus_areas: Specific areas to focus on (e.g., "performance", "documentation")
            
        Returns:
            Analysis results including code quality metrics, improvement suggestions,
            architecture assessment, and more
        """
        await self._ensure_initialized()
            
        try:
            # Prepare focus areas
            focus_params = {}
            if focus_areas:
                focus_params = {
                    "focus_areas": focus_areas,
                    "focus_priority": "high"
                }
            
            result = await self.connector.execute_tool(
                tool_name="github",
                action="analyze_repository",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "branch": branch,
                    "llm_model": llm_model,
                    "analysis_depth": "deep" if deep_analysis else "standard",
                    "include_metrics": True,
                    "include_security": include_security,
                    "include_architecture": True,
                    "include_test_coverage": True,
                    "include_dependency_analysis": True,
                    "api_version": "2025-05",  # Latest GitHub API version as of 2025
                    "version": "2025.5",  # Latest Composio version as of 2025
                    **focus_params
                }
            )
            
            logger.info(f"Successfully analyzed repository {owner}/{repo}")
            return result
        except ComposioRateLimitError as e:
            logger.warning(f"Rate limited: {e}. Retry after {e.retry_after} seconds.")
            raise
        except ComposioAPIError as e:
            logger.error(f"Error analyzing repository: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error analyzing repository: {e}")
            raise RuntimeError(f"Repository analysis failed: {e}")
            
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a GitHub issue using Composio
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            title: Issue title
            body: Issue body content
            labels: List of labels to apply (optional)
            assignees: List of users to assign (optional)
            milestone: Milestone ID (optional)
            draft: Whether to create as draft issue (GitHub 2025 feature)
            
        Returns:
            Created issue data
        """
        await self._ensure_initialized()
            
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="create_issue",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "title": title,
                    "body": body,
                    "labels": labels or [],
                    "assignees": assignees or [],
                    "milestone": milestone,
                    "draft": draft,
                    "api_version": "2025-05"
                }
            )
            
            logger.info(f"Created issue #{result.get('number')} in {owner}/{repo}")
            return result
        except ComposioAPIError as e:
            logger.error(f"Error creating issue: {e}")
            raise
            
    async def get_repository_metrics(
        self,
        owner: str,
        repo: str,
        time_period: str = "30d", # Accepts: 7d, 30d, 90d, 365d, all
        include_ai_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Get repository metrics using Composio's enhanced GitHub metrics
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            time_period: Time period for metrics (default: 30d)
            include_ai_insights: Whether to include AI-generated insights about the data
            
        Returns:
            Repository metrics including commits, contributors, code churn, and more
        """
        await self._ensure_initialized()
            
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="get_repository_metrics",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "time_period": time_period,
                    "include_commit_analysis": True,
                    "include_contributor_stats": True,
                    "include_code_health": True,
                    "include_ai_insights": include_ai_insights,
                    "include_trend_analysis": True,
                    "include_anomaly_detection": True,
                    "api_version": "2025-05"  # Latest GitHub API version as of 2025
                }
            )
            
            logger.info(f"Retrieved metrics for {owner}/{repo} over {time_period}")
            return result
        except ComposioAPIError as e:
            logger.error(f"Error getting repository metrics: {e}")
            raise
    
    async def run_autonomous_improvement(
        self,
        owner: str,
        repo: str,
        target_branch: str = "vot1-improvements",
        focus_areas: Optional[List[str]] = None,
        llm_model: str = "gpt-4o-turbo", # 2025 latest model
        max_prs: int = 3,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Run an autonomous improvement cycle on a repository
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            target_branch: Branch to create PRs against (default: vot1-improvements)
            focus_areas: Specific areas to focus on (e.g., "performance", "security")
            llm_model: LLM model to use (default: gpt-4o-turbo)
            max_prs: Maximum number of PRs to create
            auto_approve: Whether to auto-approve the generated PRs
            
        Returns:
            Results of the improvement cycle including PRs created
        """
        await self._ensure_initialized()
            
        # Default focus areas if none specified
        focus_areas = focus_areas or ["code_quality", "documentation", "tests"]
        
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="run_autonomous_improvement",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "target_branch": target_branch,
                    "focus_areas": focus_areas,
                    "llm_model": llm_model,
                    "max_prs": max_prs,
                    "auto_approve": auto_approve,
                    "include_tests": True,
                    "reasoning_depth": "advanced",
                    "include_performance_optimizations": True,
                    "include_code_modernization": True,
                    "version": "2025.5",
                    "api_version": "2025-05"
                }
            )
            
            logger.info(f"Completed autonomous improvement cycle for {owner}/{repo}")
            if "pull_requests" in result:
                for pr in result["pull_requests"]:
                    logger.info(f"Created PR #{pr['number']}: {pr['title']}")
                    
            return result
        except ComposioAPIError as e:
            logger.error(f"Error running autonomous improvement: {e}")
            raise
    
    async def analyze_code_quality(
        self,
        owner: str,
        repo: str,
        path: Optional[str] = None,
        branch: str = "main",
        standards: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze code quality for a repository or specific path
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            path: Specific file or directory path (optional)
            branch: Branch to analyze (default: main)
            standards: Specific coding standards to check against
            
        Returns:
            Code quality analysis results
        """
        await self._ensure_initialized()
        
        try:
            # Use default standards if none provided
            standards = standards or ["pep8", "modern-js", "clean-code", "solid"]
            
            result = await self.connector.execute_tool(
                tool_name="github",
                action="analyze_code_quality",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "path": path,
                    "branch": branch,
                    "standards": standards,
                    "include_suggestions": True,
                    "include_metrics": True,
                    "include_examples": True,
                    "api_version": "2025-05"
                }
            )
            
            path_desc = f" for path '{path}'" if path else ""
            logger.info(f"Completed code quality analysis of {owner}/{repo}{path_desc}")
            return result
        except ComposioAPIError as e:
            logger.error(f"Error analyzing code quality: {e}")
            raise
            
    async def check_connection(self) -> Dict[str, Any]:
        """
        Verify connection to GitHub via Composio
        
        Returns:
            Connection status and user information
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            result = await self.connector.execute_tool(
                tool_name="github",
                action="get_authenticated_user",
                parameters={}
            )
            
            return {
                "connected": True,
                "github_username": result.get("login"),
                "user_info": result,
                "scope": result.get("scope", "unknown"),
                "composio_status": "active",
                "tool_version": self.github_tool.get("version", "unknown"),
                "rate_limit": {
                    "remaining": result.get("rate", {}).get("remaining", "unknown"),
                    "reset_at": result.get("rate", {}).get("reset_at", "unknown")
                }
            }
        except Exception as e:
            logger.error(f"Error checking GitHub connection: {e}")
            return {
                "connected": False,
                "error": str(e),
                "composio_status": "error"
            }
    
    async def suggest_improvements(
        self,
        owner: str,
        repo: str,
        file_path: str,
        llm_model: str = "gpt-4o-turbo"
    ) -> Dict[str, Any]:
        """
        Get AI-suggested improvements for a specific file
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            file_path: Path to the file to analyze
            llm_model: LLM model to use (default: gpt-4o-turbo)
            
        Returns:
            Suggested improvements with code examples
        """
        await self._ensure_initialized()
        
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="suggest_improvements",
                parameters={
                    "owner": owner,
                    "repo": repo, 
                    "file_path": file_path,
                    "llm_model": llm_model,
                    "include_code_examples": True,
                    "explanation_detail": "detailed",
                    "api_version": "2025-05"
                }
            )
            
            logger.info(f"Generated {len(result.get('suggestions', []))} improvement suggestions for {file_path}")
            return result
        except ComposioAPIError as e:
            logger.error(f"Error suggesting improvements: {e}")
            raise
            
    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open",  # open, closed, all
        sort: str = "created",  # created, updated, popularity, long-running
        direction: str = "desc",  # asc, desc
        include_ai_review: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get pull requests for a repository with enhanced data
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            state: PR state to filter by (default: open)
            sort: Sort method (default: created)
            direction: Sort direction (default: desc)
            include_ai_review: Whether to include AI review comments (2025 feature)
            
        Returns:
            List of pull requests with enhanced data
        """
        await self._ensure_initialized()
            
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="list_pull_requests",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "state": state,
                    "sort": sort,
                    "direction": direction,
                    "include_reviews": True,
                    "include_stats": True,
                    "include_checks": True,
                    "include_ai_review": include_ai_review,
                    "api_version": "2025-05"
                }
            )
            
            logger.info(f"Retrieved {len(result.get('pull_requests', []))} {state} pull requests for {owner}/{repo}")
            return result.get("pull_requests", [])
        except ComposioAPIError as e:
            logger.error(f"Error getting pull requests: {e}")
            raise
    
    async def create_release(
        self,
        owner: str,
        repo: str,
        tag_name: str,
        name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False,
        generate_release_notes: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new release for a repository
        
        Args:
            owner: Repository owner/organization
            repo: Repository name
            tag_name: Tag name for the release
            name: Release title
            body: Release description
            draft: Whether it's a draft release
            prerelease: Whether it's a pre-release
            generate_release_notes: Auto-generate notes from PRs and commits
            
        Returns:
            Created release data
        """
        await self._ensure_initialized()
        
        try:
            result = await self.connector.execute_tool(
                tool_name="github",
                action="create_release",
                parameters={
                    "owner": owner,
                    "repo": repo,
                    "tag_name": tag_name,
                    "name": name,
                    "body": body,
                    "draft": draft,
                    "prerelease": prerelease,
                    "generate_release_notes": generate_release_notes,
                    "api_version": "2025-05"
                }
            )
            
            logger.info(f"Created release {tag_name} for {owner}/{repo}")
            return result
        except ComposioAPIError as e:
            logger.error(f"Error creating release: {e}")
            raise
            
    async def close(self):
        """Close connections and clean up resources"""
        if self.auth_manager and self.auth_manager.session:
            await self.auth_manager.close()
            logger.info("GitHub Composio integration closed")
            self._initialized = False


# Convenience function to create a GitHub integration instance
async def create_github_integration(api_key: Optional[str] = None) -> GitHubComposioIntegration:
    """
    Create and initialize a GitHub integration instance
    
    Args:
        api_key: Composio API key (optional, can use environment variable)
        
    Returns:
        Initialized GitHubComposioIntegration instance
    """
    integration = GitHubComposioIntegration(api_key=api_key)
    await integration.initialize()
    return integration


# Examples of using the integration
async def example_usage():
    """Example of using the GitHub Composio integration"""
    # Create and initialize the integration
    github = await create_github_integration()
    
    try:
        # Check connection
        connection = await github.check_connection()
        print(f"Connected as: {connection.get('github_username')}")
        
        # Analyze a repository
        analysis = await github.analyze_repository(
            owner="villageofthousands",
            repo="vot1",
            llm_model="gpt-4o-turbo"
        )
        
        print(f"Analysis score: {analysis.get('overall_score')}")
        print(f"Areas for improvement: {', '.join(analysis.get('improvement_areas', []))}")
        
        # Get code quality for a specific file
        quality = await github.analyze_code_quality(
            owner="villageofthousands",
            repo="vot1",
            path="src/vot1/dashboard/api.py"
        )
        
        print(f"Code quality score: {quality.get('overall_score')}/100")
        
        # Run autonomous improvement
        improvement = await github.run_autonomous_improvement(
            owner="villageofthousands",
            repo="vot1",
            focus_areas=["documentation", "code_quality"]
        )
        
        print(f"Created {len(improvement.get('pull_requests', []))} pull requests")
    finally:
        # Close the integration
        await github.close()


if __name__ == "__main__":
    # Run the example if script is executed directly
    asyncio.run(example_usage()) 