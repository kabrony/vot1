#!/usr/bin/env python3
"""
Real GitHub API Integration Test

This script makes actual API calls to GitHub to demonstrate the real integration.
It includes proper error handling, authentication, and rate limiting awareness.
"""

import os
import sys
import asyncio
import logging
import time
import json
import argparse
from typing import Dict, List, Any, Optional

# For GitHub API
import aiohttp
from aiohttp import ClientSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubAPIClient:
    """A real GitHub API client that makes actual API calls."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, session: Optional[ClientSession] = None):
        """Initialize with an actual GitHub token."""
        self.token = token
        self.session = session
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self._is_external_session = session is not None
        logger.info("Initialized GitHub API client")
        
    async def __aenter__(self):
        """Context manager entry point - creates session if needed."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes session if we created it."""
        if not self._is_external_session and self.session is not None:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, endpoint: str, 
                           params: Optional[Dict[str, Any]] = None,
                           data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an actual API request to GitHub."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._is_external_session = False
            
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VOT1-GitHub-Integration"
        }
        
        # Handle potential rate limiting
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 5:
            wait_time = max(0, self.rate_limit_reset - time.time())
            if wait_time > 0:
                logger.warning(f"Rate limit low, waiting {wait_time:.1f} seconds before next request")
                await asyncio.sleep(wait_time + 1)  # Add a buffer
                
        try:
            async with self.session.request(
                method, url, headers=headers, params=params, 
                json=data, raise_for_status=False
            ) as response:
                # Update rate limit information
                if 'X-RateLimit-Remaining' in response.headers:
                    self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                if 'X-RateLimit-Reset' in response.headers:
                    self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
                
                # Handle common response codes
                if response.status == 401:
                    logger.error("Authentication failed. Check your GitHub token.")
                    return {"success": False, "error": "Authentication failed", "status": 401}
                elif response.status == 403:
                    if self.rate_limit_remaining == 0:
                        reset_time = time.strftime('%H:%M:%S', time.localtime(self.rate_limit_reset))
                        logger.error(f"Rate limit exceeded. Resets at {reset_time}")
                        return {"success": False, "error": f"Rate limit exceeded. Resets at {reset_time}", "status": 403}
                    else:
                        logger.error("Forbidden. Check permissions for this token.")
                        return {"success": False, "error": "Forbidden", "status": 403}
                elif response.status == 404:
                    logger.error(f"Resource not found: {url}")
                    return {"success": False, "error": "Resource not found", "status": 404}
                elif response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return {"success": False, "error": error_text, "status": response.status}
                
                # Parse and return successful response
                try:
                    result = await response.json()
                    return {"success": True, "data": result}
                except json.JSONDecodeError:
                    text_response = await response.text()
                    if text_response:
                        return {"success": True, "data": text_response}
                    return {"success": True, "data": {}}
                    
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"success": False, "error": f"Connection error: {str(e)}"}
            
    async def verify_credentials(self) -> Dict[str, Any]:
        """Verify GitHub credentials by calling the user endpoint."""
        logger.info("Verifying GitHub credentials...")
        result = await self._make_request("GET", "/user")
        
        if result["success"]:
            return {
                "success": True,
                "user": result["data"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }
        
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information from GitHub API."""
        logger.info(f"Getting repository info for {owner}/{repo}...")
        endpoint = f"/repos/{owner}/{repo}"
        result = await self._make_request("GET", endpoint)
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get repository: {result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }
        
    async def get_repository_contents(self, owner: str, repo: str, path: str = "", ref: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get repository contents from GitHub API."""
        logger.info(f"Getting repository contents at path '{path}'...")
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref
            
        result = await self._make_request("GET", endpoint, params=params)
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get repository contents: {result.get('error', 'Unknown error')}")
            return []
        
    async def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Optional[str]:
        """Get a specific file's content from GitHub API."""
        logger.info(f"Getting file content for {path}...")
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref
            
        result = await self._make_request("GET", endpoint, params=params)
        
        if result["success"] and isinstance(result["data"], dict) and "content" in result["data"]:
            # GitHub API returns content as base64 encoded
            import base64
            content = result["data"]["content"]
            try:
                # Replace newlines and decode
                decoded_content = base64.b64decode(content.replace('\n', '')).decode('utf-8')
                return decoded_content
            except Exception as e:
                logger.error(f"Error decoding file content: {str(e)}")
                return None
        else:
            logger.error(f"Failed to get file content: {result.get('error', 'Unknown error')}")
            return None
        
    async def get_workflows(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get GitHub Actions workflows from the repository."""
        logger.info(f"Getting workflows for {owner}/{repo}...")
        endpoint = f"/repos/{owner}/{repo}/actions/workflows"
        result = await self._make_request("GET", endpoint)
        
        if result["success"] and "workflows" in result["data"]:
            return result["data"]["workflows"]
        else:
            logger.error(f"Failed to get workflows: {result.get('error', 'Unknown error')}")
            return []
    
    async def get_issues(self, owner: str, repo: str, state: str = "open", 
                        since: Optional[str] = None, labels: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get issues from a repository with filtering options."""
        logger.info(f"Getting {state} issues for {owner}/{repo}...")
        endpoint = f"/repos/{owner}/{repo}/issues"
        params = {"state": state}
        
        if since:
            params["since"] = since
        if labels:
            params["labels"] = labels
            
        result = await self._make_request("GET", endpoint, params=params)
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Failed to get issues: {result.get('error', 'Unknown error')}")
            return []
            
    async def analyze_repository(self, owner: str, repo: str, deep_analysis: bool = False) -> Dict[str, Any]:
        """Perform a comprehensive analysis of a GitHub repository using real API calls."""
        logger.info(f"Analyzing repository {owner}/{repo} (deep_analysis={deep_analysis})...")
        
        try:
            # Gather repository data
            repository = await self.get_repository(owner, repo)
            if not isinstance(repository, dict) or "id" not in repository:
                return {
                    "success": False,
                    "error": "Failed to retrieve repository data"
                }
                
            # Get top-level contents
            contents = await self.get_repository_contents(owner, repo)
            if not contents:
                logger.warning(f"Could not retrieve contents for {owner}/{repo}")
                contents = []
                
            # Get workflows
            workflows = await self.get_workflows(owner, repo)
            
            # Analyze documentation
            doc_score = {
                "has_readme": any(item.get("name") == "README.md" for item in contents if isinstance(item, dict)),
                "has_contributing": any(item.get("name") == "CONTRIBUTING.md" for item in contents if isinstance(item, dict)),
                "has_codeofconduct": any(item.get("name") == "CODE_OF_CONDUCT.md" for item in contents if isinstance(item, dict)),
                "has_license": any(item.get("name") == "LICENSE" or item.get("name") == "LICENSE.md" or item.get("name") == "LICENSE.txt" for item in contents if isinstance(item, dict)),
                "has_changelog": any(item.get("name") == "CHANGELOG.md" for item in contents if isinstance(item, dict)),
                "score": 0.0
            }
            
            # Calculate score
            doc_score_value = 0
            if doc_score["has_readme"]: doc_score_value += 0.4
            if doc_score["has_contributing"]: doc_score_value += 0.15
            if doc_score["has_codeofconduct"]: doc_score_value += 0.15
            if doc_score["has_license"]: doc_score_value += 0.15
            if doc_score["has_changelog"]: doc_score_value += 0.15
            doc_score["score"] = doc_score_value
            
            # Analyze code quality
            code_quality = {
                "has_ci": len(workflows) > 0,
                "has_tests": any(item.get("name") == "test" or item.get("name") == "tests" for item in contents if isinstance(item, dict)),
                "has_linting": False,  # We'll check workflow files for linting
                "score": 0.0
            }
            
            # Look for linting in workflows
            for workflow in workflows:
                if isinstance(workflow, dict) and "path" in workflow:
                    workflow_content = await self.get_file_content(owner, repo, workflow["path"])
                    if workflow_content and ("lint" in workflow_content.lower() or "eslint" in workflow_content.lower()):
                        code_quality["has_linting"] = True
                        break
            
            # Calculate score
            code_score = 0
            if code_quality["has_ci"]: code_score += 0.4
            if code_quality["has_tests"]: code_score += 0.3
            if code_quality["has_linting"]: code_score += 0.3
            code_quality["score"] = code_score
            
            # Analyze workflows
            workflow_analysis = {
                "count": len(workflows),
                "has_pr_checks": any("pull_request" in str(w) for w in workflows if isinstance(w, dict)),
                "has_deployment": any("deploy" in str(w) for w in workflows if isinstance(w, dict)),
                "score": min(1.0, len(workflows) / 5)
            }
            
            # Generate improvement areas
            improvement_areas = []
            
            if not doc_score["has_changelog"]:
                improvement_areas.append({
                    "type": "documentation",
                    "title": "Add CHANGELOG.md",
                    "description": "Add a CHANGELOG.md file to track changes between releases",
                    "priority": "medium"
                })
                
            if not doc_score["has_codeofconduct"]:
                improvement_areas.append({
                    "type": "documentation",
                    "title": "Add Code of Conduct",
                    "description": "Add a CODE_OF_CONDUCT.md file to define community standards",
                    "priority": "low"
                })
                
            if not code_quality["has_linting"]:
                improvement_areas.append({
                    "type": "workflow",
                    "title": "Add linting workflow",
                    "description": "Add a GitHub Actions workflow for linting code",
                    "priority": "medium"
                })
            
            # Deep analysis results
            deep_analysis_results = None
            if deep_analysis:
                logger.info("Performing deep analysis...")
                
                # Get issues
                issues = await self.get_issues(owner, repo, state="all")
                
                # Identify stale issues (open issues with no activity for 30+ days)
                stale_issues = 0
                if issues:
                    for issue in issues:
                        if issue.get("state") == "open" and "updated_at" in issue:
                            last_updated = time.strptime(issue["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                            last_updated_timestamp = time.mktime(last_updated)
                            if (time.time() - last_updated_timestamp) > (30 * 24 * 60 * 60):  # 30 days
                                stale_issues += 1
                
                # Identify documentation gaps by checking for README sections
                documentation_gaps = []
                if doc_score["has_readme"]:
                    readme_content = await self.get_file_content(owner, repo, "README.md")
                    if readme_content:
                        if "installation" not in readme_content.lower():
                            documentation_gaps.append("Installation Instructions")
                        if "usage" not in readme_content.lower():
                            documentation_gaps.append("Usage Examples")
                        if "contributing" not in readme_content.lower() and not doc_score["has_contributing"]:
                            documentation_gaps.append("Contributing Guide")
                
                # Calculate health score
                health_score = (
                    doc_score["score"] * 0.3 + 
                    code_quality["score"] * 0.3 + 
                    workflow_analysis["score"] * 0.2 + 
                    (1 - min(1, stale_issues / 50)) * 0.2  # Lower score for more stale issues
                )
                
                deep_analysis_results = {
                    "stale_issues": stale_issues,
                    "documentation_gaps": documentation_gaps,
                    "health_score": health_score
                }
            
            return {
                "success": True,
                "repository": repository,
                "documentation": doc_score,
                "code_quality": code_quality,
                "workflows": workflow_analysis,
                "improvement_areas": improvement_areas,
                "deep_analysis_results": deep_analysis_results,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error during repository analysis: {str(e)}")
            return {
                "success": False,
                "error": f"Error during analysis: {str(e)}"
            }

async def main():
    parser = argparse.ArgumentParser(description="Test the GitHub API Integration")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--deep-analysis", action="store_true", help="Perform deep analysis")
    parser.add_argument("--token", help="GitHub API token (if not provided, uses GITHUB_TOKEN env var)")
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("No GitHub token provided. Set GITHUB_TOKEN environment variable or use --token.")
        sys.exit(1)
        
    try:
        # Test the API client
        logger.info(f"Testing GitHub API integration with {args.owner}/{args.repo}")
        
        async with GitHubAPIClient(token) as client:
            # Verify credentials
            auth_result = await client.verify_credentials()
            if not auth_result["success"]:
                logger.error(f"Authentication failed: {auth_result.get('error', 'Unknown error')}")
                sys.exit(1)
                
            logger.info(f"Successfully authenticated as {auth_result['user']['login']}")
            
            # Perform repository analysis
            logger.info(f"Analyzing repository {args.owner}/{args.repo}...")
            analysis = await client.analyze_repository(args.owner, args.repo, args.deep_analysis)
            
            if not analysis["success"]:
                logger.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
                sys.exit(1)
                
            # Print analysis results
            repo_data = analysis["repository"]
            logger.info("\nRepository Analysis Results:")
            logger.info(f"  Repository: {repo_data['full_name']}")
            logger.info(f"  Description: {repo_data.get('description', 'No description')}")
            logger.info(f"  Stars: {repo_data.get('stargazers_count', 0)}")
            logger.info(f"  Forks: {repo_data.get('forks_count', 0)}")
            logger.info(f"  Open Issues: {repo_data.get('open_issues_count', 0)}")
            logger.info(f"  Default Branch: {repo_data.get('default_branch', 'main')}")
            
            logger.info("\nDocumentation Score:")
            for key, value in analysis["documentation"].items():
                if key != "score":
                    logger.info(f"  {key}: {value}")
            logger.info(f"  Overall Score: {analysis['documentation']['score']:.2f}")
            
            logger.info("\nCode Quality:")
            for key, value in analysis["code_quality"].items():
                if key != "score":
                    logger.info(f"  {key}: {value}")
            logger.info(f"  Overall Score: {analysis['code_quality']['score']:.2f}")
            
            logger.info("\nWorkflows:")
            for key, value in analysis["workflows"].items():
                logger.info(f"  {key}: {value}")
                
            if analysis["improvement_areas"]:
                logger.info("\nImprovement Areas:")
                for area in analysis["improvement_areas"]:
                    logger.info(f"  - {area['title']} ({area['priority']}): {area['description']}")
            
            if analysis["deep_analysis_results"]:
                logger.info("\nDeep Analysis Results:")
                deep = analysis["deep_analysis_results"]
                logger.info(f"  Stale Issues: {deep['stale_issues']}")
                logger.info(f"  Documentation Gaps: {', '.join(deep['documentation_gaps']) or 'None'}")
                logger.info(f"  Overall Health Score: {deep['health_score']:.2f}")
            
            logger.info("\nGitHub API integration test completed successfully!")
            
    except Exception as e:
        logger.error(f"Error during GitHub API testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0) 