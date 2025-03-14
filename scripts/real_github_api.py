#!/usr/bin/env python3
"""
Real GitHub API Client for VOT1

This module provides a comprehensive implementation of GitHub API calls
for the VOT1 system. It uses real API calls instead of mocks to interact
with GitHub repositories.
"""

import os
import json
import time
import logging
import aiohttp
import asyncio
import backoff
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubAPIClient:
    """
    A client for interacting with the GitHub API using real API calls.
    
    This class provides methods for all GitHub operations needed by the VOT1 system,
    including repository analysis, PR creation, webhook management, and more.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str):
        """
        Initialize the GitHub API client with an authentication token.
        
        Args:
            token: GitHub API token for authentication
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VOT1-GitHub-Integration"
        }
        self.session = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
    async def __aenter__(self):
        """Create session on enter context."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close session on exit context."""
        if self.session:
            await self.session.close()
            
    async def create_session(self):
        """Create an aiohttp session for API requests."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def close_session(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, aiohttp.ServerTimeoutError),
        max_tries=5
    )
    async def _make_request(
        self, 
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request to GitHub with automatic retries and rate limit handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response data as a dictionary
        """
        # Create session if not exists
        if not self.session:
            await self.create_session()
            
        # Prepare request
        url = f"{self.BASE_URL}{endpoint}"
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
            
        # Check rate limits before making request
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 10:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset)
            now = datetime.now()
            if reset_time > now:
                wait_seconds = (reset_time - now).total_seconds() + 1
                logger.warning(f"Rate limit almost exceeded. Waiting {wait_seconds:.2f} seconds")
                await asyncio.sleep(wait_seconds)
                
        # Make request
        try:
            async with getattr(self.session, method.lower())(
                url,
                json=data,
                params=params,
                headers=request_headers
            ) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 1000))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
                
                # Handle rate limiting
                if response.status == 429:  # Too Many Requests
                    reset_time = datetime.fromtimestamp(self.rate_limit_reset)
                    now = datetime.now()
                    wait_seconds = (reset_time - now).total_seconds() + 1
                    logger.warning(f"Rate limit exceeded. Waiting {wait_seconds:.2f} seconds")
                    await asyncio.sleep(wait_seconds)
                    return await self._make_request(method, endpoint, data, params, headers)
                    
                # Handle successful responses
                if 200 <= response.status < 300:
                    if response.status == 204:  # No Content
                        return {"success": True, "status_code": response.status}
                    try:
                        result = await response.json()
                        return result
                    except aiohttp.ContentTypeError:
                        text = await response.text()
                        return {"success": True, "status_code": response.status, "text": text}
                        
                # Handle errors
                error_text = await response.text()
                try:
                    error_json = json.loads(error_text)
                    error_message = error_json.get('message', error_text)
                except json.JSONDecodeError:
                    error_message = error_text
                    
                logger.error(f"GitHub API error ({response.status}): {error_message}")
                return {
                    "success": False,
                    "status_code": response.status,
                    "error": error_message
                }
                
        except (aiohttp.ClientError, aiohttp.ServerTimeoutError) as e:
            logger.error(f"Request error: {str(e)}")
            raise
            
    async def verify_credentials(self) -> Dict[str, Any]:
        """
        Verify GitHub credentials by retrieving authenticated user information.
        
        Returns:
            User information if successful, error otherwise
        """
        result = await self._make_request("GET", "/user")
        if "login" in result:
            logger.info(f"Successfully authenticated as: {result['login']}")
            return {
                "success": True,
                "user": result
            }
        return {
            "success": False,
            "error": result.get("error", "Authentication failed")
        }
        
    async def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        return await self._make_request("GET", f"/repos/{owner}/{repo}")
        
    async def get_repository_contents(
        self, 
        owner: str, 
        repo: str, 
        path: str = "", 
        ref: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get repository contents.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path within repository
            ref: Git reference (branch, tag, commit)
            
        Returns:
            List of content items
        """
        params = {}
        if ref:
            params["ref"] = ref
            
        return await self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/contents/{path}", 
            params=params
        )
        
    async def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get file content from repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch, tag, commit)
            
        Returns:
            File content as string or None if file not found
        """
        import base64
        
        response = await self.get_repository_contents(owner, repo, path, ref)
        
        if isinstance(response, dict) and "content" in response:
            content = response["content"]
            encoding = response.get("encoding")
            
            if encoding == "base64":
                return base64.b64decode(content).decode("utf-8")
            return content
            
        return None
        
    async def create_fork(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Create a fork of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Fork information
        """
        return await self._make_request("POST", f"/repos/{owner}/{repo}/forks")
        
    async def create_branch(
        self, 
        owner: str, 
        repo: str, 
        branch_name: str, 
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a new branch in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch_name: New branch name
            base_branch: Base branch to create from
            
        Returns:
            Branch creation result
        """
        # Get the SHA of the base branch
        base_ref = await self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
        )
        
        if not base_ref.get("object", {}).get("sha"):
            return {
                "success": False,
                "error": f"Could not get SHA for branch {base_branch}"
            }
            
        sha = base_ref["object"]["sha"]
        
        # Create new branch
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
        
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/git/refs", 
            data=data
        )
        
    async def create_file(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str, 
        message: str, 
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a file in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            branch: Branch to commit to
            
        Returns:
            File creation result
        """
        import base64
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
        }
        
        if branch:
            data["branch"] = branch
            
        return await self._make_request(
            "PUT", 
            f"/repos/{owner}/{repo}/contents/{path}", 
            data=data
        )
        
    async def update_file(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str, 
        message: str, 
        sha: str, 
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a file in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: New file content
            message: Commit message
            sha: File SHA
            branch: Branch to commit to
            
        Returns:
            File update result
        """
        import base64
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "sha": sha
        }
        
        if branch:
            data["branch"] = branch
            
        return await self._make_request(
            "PUT", 
            f"/repos/{owner}/{repo}/contents/{path}", 
            data=data
        )
        
    async def create_pull_request(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        head: str, 
        base: str = "main", 
        body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description
            
        Returns:
            Pull request information
        """
        data = {
            "title": title,
            "head": head,
            "base": base
        }
        
        if body:
            data["body"] = body
            
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/pulls", 
            data=data,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
    async def get_issues(
        self, 
        owner: str, 
        repo: str, 
        state: str = "open", 
        labels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get repository issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open, closed, all)
            labels: Filter by labels
            
        Returns:
            List of issues
        """
        params = {"state": state}
        
        if labels:
            params["labels"] = ",".join(labels)
            
        return await self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/issues", 
            params=params
        )
        
    async def create_issue(
        self, 
        owner: str, 
        repo: str, 
        title: str, 
        body: Optional[str] = None, 
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: Issue labels
            
        Returns:
            Issue information
        """
        data = {"title": title}
        
        if body:
            data["body"] = body
            
        if labels:
            data["labels"] = labels
            
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/issues", 
            data=data
        )
        
    async def close_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """
        Close an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Updated issue information
        """
        data = {"state": "closed"}
        
        return await self._make_request(
            "PATCH", 
            f"/repos/{owner}/{repo}/issues/{issue_number}", 
            data=data
        )
        
    async def add_issue_comment(
        self, 
        owner: str, 
        repo: str, 
        issue_number: int, 
        comment: str
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            comment: Comment text
            
        Returns:
            Comment information
        """
        data = {"body": comment}
        
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments", 
            data=data
        )
        
    async def create_webhook(
        self, 
        owner: str, 
        repo: str, 
        webhook_url: str, 
        events: List[str] = ["push", "pull_request"], 
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a webhook.
        
        Args:
            owner: Repository owner
            repo: Repository name
            webhook_url: Webhook URL
            events: Events to trigger webhook
            secret: Webhook secret
            
        Returns:
            Webhook information
        """
        data = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json"
            }
        }
        
        if secret:
            data["config"]["secret"] = secret
            
        return await self._make_request(
            "POST", 
            f"/repos/{owner}/{repo}/hooks", 
            data=data
        )
        
    async def get_workflows(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        Get repository workflows.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of workflows
        """
        response = await self._make_request(
            "GET", 
            f"/repos/{owner}/{repo}/actions/workflows"
        )
        
        return response.get("workflows", [])
        
    async def create_workflow(
        self, 
        owner: str, 
        repo: str, 
        path: str, 
        content: str, 
        message: str = "Create workflow"
    ) -> Dict[str, Any]:
        """
        Create a workflow file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Workflow file path (should be in .github/workflows/)
            content: Workflow YAML content
            message: Commit message
            
        Returns:
            File creation result
        """
        workflow_path = path
        if not path.startswith(".github/workflows/"):
            workflow_path = f".github/workflows/{path}"
            
        # Ensure directory exists
        dirs = workflow_path.split("/")
        current_path = ""
        
        for i, dir_name in enumerate(dirs[:-1]):
            if not current_path:
                current_path = dir_name
            else:
                current_path = f"{current_path}/{dir_name}"
                
            # Check if directory exists
            if i > 0:  # Skip checking the root .github directory
                contents = await self.get_repository_contents(owner, repo, current_path)
                if isinstance(contents, dict) and "message" in contents and contents["message"] == "Not Found":
                    # Create directory by creating a .gitkeep file
                    await self.create_file(
                        owner,
                        repo,
                        f"{current_path}/.gitkeep",
                        "",
                        f"Create {current_path} directory"
                    )
        
        return await self.create_file(
            owner,
            repo,
            workflow_path,
            content,
            message
        )
        
    async def analyze_repository(self, owner: str, repo: str, deep_analysis: bool = False) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            deep_analysis: Whether to perform deep analysis
            
        Returns:
            Analysis results
        """
        # This is a real implementation that uses the GitHub API
        analysis_result = {
            "success": True,
            "repository": await self.get_repository(owner, repo),
            "documentation": {},
            "code_quality": {},
            "workflows": {},
            "improvement_areas": [],
            "deep_analysis_results": {} if deep_analysis else None,
            "timestamp": time.time()
        }
        
        # Get repository contents
        try:
            root_contents = await self.get_repository_contents(owner, repo)
            
            if isinstance(root_contents, dict) and "message" in root_contents:
                analysis_result["success"] = False
                analysis_result["error"] = root_contents["message"]
                return analysis_result
                
            # Analyze documentation
            doc_score = await self._analyze_documentation(owner, repo, root_contents)
            analysis_result["documentation"] = doc_score
            
            # Analyze code quality
            code_quality = await self._analyze_code_quality(owner, repo, root_contents)
            analysis_result["code_quality"] = code_quality
            
            # Analyze workflows
            workflows = await self._analyze_workflows(owner, repo)
            analysis_result["workflows"] = workflows
            
            # Generate improvement areas
            improvements = await self._generate_improvements(doc_score, code_quality, workflows)
            analysis_result["improvement_areas"] = improvements
            
            # Perform deep analysis if requested
            if deep_analysis:
                deep_results = await self._perform_deep_analysis(owner, repo)
                analysis_result["deep_analysis_results"] = deep_results
                
                # Calculate overall health score
                doc_weight = 0.3
                code_weight = 0.3
                workflow_weight = 0.2
                issues_weight = 0.2
                
                health_score = (
                    doc_score["score"] * doc_weight +
                    code_quality["score"] * code_weight +
                    workflows["score"] * workflow_weight +
                    (1 - min(1, deep_results["stale_issues"] / 50)) * issues_weight
                )
                
                analysis_result["deep_analysis_results"]["health_score"] = health_score
                
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            analysis_result["success"] = False
            analysis_result["error"] = str(e)
            return analysis_result
            
    async def _analyze_documentation(
        self, 
        owner: str, 
        repo: str, 
        contents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze repository documentation.
        
        Args:
            owner: Repository owner
            repo: Repository name
            contents: Repository contents
            
        Returns:
            Documentation analysis results
        """
        # Initialize result
        result = {
            "has_readme": False,
            "has_contributing": False,
            "has_codeofconduct": False,
            "has_license": False,
            "has_changelog": False,
            "score": 0
        }
        
        # Check for documentation files
        for item in contents:
            name = item["name"].lower()
            
            if name == "readme.md":
                result["has_readme"] = True
            elif name == "contributing.md":
                result["has_contributing"] = True
            elif name in ["code_of_conduct.md", "codeofconduct.md"]:
                result["has_codeofconduct"] = True
            elif name in ["license", "license.md", "license.txt"]:
                result["has_license"] = True
            elif name in ["changelog.md", "changes.md", "history.md"]:
                result["has_changelog"] = True
                
        # Calculate score
        score = 0
        score += 0.4 if result["has_readme"] else 0
        score += 0.15 if result["has_contributing"] else 0
        score += 0.15 if result["has_codeofconduct"] else 0
        score += 0.15 if result["has_license"] else 0
        score += 0.15 if result["has_changelog"] else 0
        
        result["score"] = score
        return result
        
    async def _analyze_code_quality(
        self, 
        owner: str, 
        repo: str, 
        contents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze repository code quality.
        
        Args:
            owner: Repository owner
            repo: Repository name
            contents: Repository contents
            
        Returns:
            Code quality analysis results
        """
        # Initialize result
        result = {
            "has_ci": False,
            "has_tests": False,
            "has_linting": False,
            "score": 0
        }
        
        # Check for GitHub Actions (CI)
        github_dir = [item for item in contents if item["name"] == ".github" and item["type"] == "dir"]
        if github_dir:
            workflows = await self.get_repository_contents(owner, repo, ".github/workflows")
            if isinstance(workflows, list) and workflows:
                result["has_ci"] = True
                
        # Check for test directory
        test_dirs = [item for item in contents if item["name"].lower() in ["test", "tests", "spec", "specs"] and item["type"] == "dir"]
        if test_dirs:
            result["has_tests"] = True
            
        # Check for linting configuration
        linting_files = [
            ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml",
            ".pylintrc", "pylintrc", ".flake8", "setup.cfg",
            ".prettier", ".prettierrc", ".prettierrc.js", ".prettierrc.json"
        ]
        
        for item in contents:
            if item["name"].lower() in linting_files:
                result["has_linting"] = True
                break
                
        # Calculate score
        score = 0
        score += 0.4 if result["has_ci"] else 0
        score += 0.3 if result["has_tests"] else 0
        score += 0.3 if result["has_linting"] else 0
        
        result["score"] = score
        return result
        
    async def _analyze_workflows(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Analyze repository workflows.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Workflow analysis results
        """
        # Initialize result
        result = {
            "count": 0,
            "has_pr_checks": False,
            "has_deployment": False,
            "score": 0
        }
        
        # Get workflows
        workflows = await self.get_workflows(owner, repo)
        result["count"] = len(workflows)
        
        # Check workflow types
        for workflow in workflows:
            path = workflow.get("path", "")
            try:
                content = await self.get_file_content(owner, repo, path)
                if content:
                    if "pull_request" in content:
                        result["has_pr_checks"] = True
                    if "deploy" in content:
                        result["has_deployment"] = True
            except Exception:
                # Continue even if there's an error reading a workflow
                pass
                
        # Calculate score
        if result["count"] > 0:
            score = 1.0
        else:
            score = 0.0
            
        result["score"] = score
        return result
        
    async def _generate_improvements(
        self, 
        documentation: Dict[str, Any],
        code_quality: Dict[str, Any],
        workflows: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement areas based on analysis.
        
        Args:
            documentation: Documentation analysis
            code_quality: Code quality analysis
            workflows: Workflow analysis
            
        Returns:
            List of improvement areas
        """
        improvements = []
        
        # Documentation improvements
        if not documentation["has_changelog"]:
            improvements.append({
                "type": "documentation",
                "title": "Add CHANGELOG.md",
                "description": "Add a CHANGELOG.md file to track changes between releases",
                "priority": "medium"
            })
            
        if not documentation["has_codeofconduct"]:
            improvements.append({
                "type": "documentation",
                "title": "Add Code of Conduct",
                "description": "Add a CODE_OF_CONDUCT.md file to define community standards",
                "priority": "low"
            })
            
        # Code quality improvements
        if not code_quality["has_linting"]:
            improvements.append({
                "type": "workflow",
                "title": "Add linting workflow",
                "description": "Add a GitHub Actions workflow for linting code",
                "priority": "medium"
            })
            
        if not code_quality["has_tests"]:
            improvements.append({
                "type": "workflow",
                "title": "Add testing workflow",
                "description": "Add a GitHub Actions workflow for running tests",
                "priority": "high"
            })
            
        return improvements
        
    async def _perform_deep_analysis(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Perform deep analysis of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Deep analysis results
        """
        # Initialize result
        result = {
            "stale_issues": 0,
            "documentation_gaps": []
        }
        
        # Find stale issues
        month_ago = datetime.now() - timedelta(days=30)
        issues = await self.get_issues(owner, repo, state="open")
        
        if isinstance(issues, list):
            stale_count = 0
            for issue in issues:
                updated_at = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
                if updated_at < month_ago:
                    stale_count += 1
                    
            result["stale_issues"] = stale_count
            
        # Find documentation gaps
        files = await self.get_repository_contents(owner, repo, "docs" if await self.get_repository_contents(owner, repo, "docs") else "")
        if isinstance(files, list):
            common_docs = ["installation", "configuration", "usage", "api", "troubleshooting"]
            found_docs = [file["name"].lower().split(".")[0] for file in files if file["type"] == "file" and "." in file["name"]]
            
            missing_docs = []
            for doc in common_docs:
                if not any(doc in found_doc for found_doc in found_docs):
                    missing_docs.append(doc.capitalize())
                    
            result["documentation_gaps"] = missing_docs
            
        return result

# Example usage
async def main():
    """Example usage of the GitHub API client."""
    # Get token from environment variable
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN environment variable not set")
        return
        
    # Create client
    async with GitHubAPIClient(token) as client:
        # Verify credentials
        creds = await client.verify_credentials()
        if not creds["success"]:
            print(f"Failed to authenticate: {creds.get('error')}")
            return
            
        print(f"Authenticated as: {creds['user']['login']}")
        
        # Analyze repository
        owner = "microsoft"
        repo = "vscode"
        
        print(f"Analyzing repository: {owner}/{repo}")
        result = await client.analyze_repository(owner, repo, deep_analysis=True)
        
        if result["success"]:
            # Print analysis results
            print(f"Repository: {result['repository']['full_name']}")
            print(f"Stars: {result['repository']['stargazers_count']}")
            print(f"Documentation score: {result['documentation']['score']:.2f}")
            print(f"Code quality score: {result['code_quality']['score']:.2f}")
            print(f"Workflows: {result['workflows']['count']}")
            
            if result['deep_analysis_results']:
                print(f"Stale issues: {result['deep_analysis_results']['stale_issues']}")
                print(f"Health score: {result['deep_analysis_results']['health_score']:.2f}")
                
            print("\nImprovement areas:")
            for area in result["improvement_areas"]:
                print(f"- {area['title']} ({area['priority']}): {area['description']}")
        else:
            print(f"Analysis failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main()) 