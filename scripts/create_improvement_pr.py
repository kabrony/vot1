#!/usr/bin/env python3
"""
Create Improvement PR Script

This script automatically generates and submits a Pull Request for repository improvements
identified by the GitHub API integration. It currently supports creating:
- CHANGELOG.md
- CODE_OF_CONDUCT.md
- Linting workflow
"""

import os
import sys
import asyncio
import logging
import time
import json
import argparse
from typing import Dict, List, Any, Optional
import base64
import uuid

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
    """GitHub API client for repository improvements."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, session: Optional[ClientSession] = None):
        """Initialize with a GitHub token."""
        self.token = token
        self.session = session
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self._is_external_session = session is not None
        logger.info("Initialized GitHub API client")
        
    async def __aenter__(self):
        """Context manager entry point."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if not self._is_external_session and self.session is not None:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, method: str, endpoint: str, 
                           params: Optional[Dict[str, Any]] = None,
                           data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request to GitHub."""
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
    
    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of a repository."""
        logger.info(f"Getting default branch for {owner}/{repo}")
        endpoint = f"/repos/{owner}/{repo}"
        result = await self._make_request("GET", endpoint)
        
        if result["success"]:
            return result["data"].get("default_branch", "main")
        else:
            logger.error(f"Could not get default branch: {result.get('error')}")
            return "main"  # Default fallback
    
    async def create_branch(self, owner: str, repo: str, branch_name: str, base_branch: Optional[str] = None) -> Dict[str, Any]:
        """Create a new branch in the repository."""
        logger.info(f"Creating branch {branch_name} in {owner}/{repo}")
        
        # Get the default branch if base_branch is not specified
        if not base_branch:
            base_branch = await self.get_default_branch(owner, repo)
            
        # Get the SHA of the latest commit on the base branch
        endpoint = f"/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
        result = await self._make_request("GET", endpoint)
        
        if not result["success"]:
            return {
                "success": False,
                "error": f"Failed to get base branch reference: {result.get('error')}"
            }
            
        base_sha = result["data"]["object"]["sha"]
        
        # Create the new branch
        endpoint = f"/repos/{owner}/{repo}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        result = await self._make_request("POST", endpoint, data=data)
        
        if result["success"]:
            return {
                "success": True,
                "branch": {
                    "name": branch_name,
                    "ref": f"refs/heads/{branch_name}",
                    "sha": base_sha
                }
            }
        else:
            logger.error(f"Failed to create branch: {result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to create branch: {result.get('error')}"
            }
    
    async def create_file(self, owner: str, repo: str, path: str, content: str, 
                         message: str, branch: str) -> Dict[str, Any]:
        """Create a new file in the repository."""
        logger.info(f"Creating file {path} in {owner}/{repo} on branch {branch}")
        
        # Encode content to base64
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": message,
            "content": content_encoded,
            "branch": branch
        }
        
        result = await self._make_request("PUT", endpoint, data=data)
        
        if result["success"]:
            return {
                "success": True,
                "file": {
                    "path": path,
                    "sha": result["data"]["content"]["sha"],
                    "url": result["data"]["content"]["html_url"]
                }
            }
        else:
            logger.error(f"Failed to create file: {result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to create file: {result.get('error')}"
            }
    
    async def create_pull_request(self, owner: str, repo: str, title: str, 
                                 head: str, base: str, body: str) -> Dict[str, Any]:
        """Create a pull request in the repository."""
        logger.info(f"Creating pull request from {head} to {base} in {owner}/{repo}")
        
        endpoint = f"/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        
        result = await self._make_request("POST", endpoint, data=data)
        
        if result["success"]:
            return {
                "success": True,
                "pull_request": {
                    "number": result["data"]["number"],
                    "html_url": result["data"]["html_url"],
                    "title": result["data"]["title"],
                    "state": result["data"]["state"]
                }
            }
        else:
            logger.error(f"Failed to create pull request: {result.get('error')}")
            return {
                "success": False,
                "error": f"Failed to create pull request: {result.get('error')}"
            }

    async def create_changelog(self, owner: str, repo: str) -> Dict[str, Any]:
        """Create a CHANGELOG.md file and submit a PR."""
        logger.info(f"Creating CHANGELOG.md for {owner}/{repo}")
        
        # Generate unique branch name
        branch_name = f"improvement/add-changelog-{uuid.uuid4().hex[:8]}"
        
        # Get default branch
        default_branch = await self.get_default_branch(owner, repo)
        
        # Create a new branch
        branch_result = await self.create_branch(owner, repo, branch_name, default_branch)
        if not branch_result["success"]:
            return branch_result
            
        # Generate CHANGELOG.md content
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core functionality

### Changed
- Updated documentation

### Fixed
- Initial bug fixes

## [0.1.0] - YYYY-MM-DD

### Added
- Initial release

"""
        
        # Create the file
        file_result = await self.create_file(
            owner=owner,
            repo=repo,
            path="CHANGELOG.md",
            content=changelog_content,
            message="Add CHANGELOG.md to track project changes",
            branch=branch_name
        )
        
        if not file_result["success"]:
            return file_result
            
        # Create the pull request
        pr_title = "Add CHANGELOG.md"
        pr_body = """## Add CHANGELOG.md file

This pull request adds a CHANGELOG.md file to track changes between releases.

### Why this is important:
- Helps users understand what has changed in each release
- Provides a structured format for documenting changes
- Follows the [Keep a Changelog](https://keepachangelog.com/) standard

This PR was automatically generated by the GitHub Repository Improvement tool.
"""
        
        pr_result = await self.create_pull_request(
            owner=owner,
            repo=repo,
            title=pr_title,
            head=branch_name,
            base=default_branch,
            body=pr_body
        )
        
        return pr_result
    
    async def create_code_of_conduct(self, owner: str, repo: str) -> Dict[str, Any]:
        """Create a CODE_OF_CONDUCT.md file and submit a PR."""
        logger.info(f"Creating CODE_OF_CONDUCT.md for {owner}/{repo}")
        
        # Generate unique branch name
        branch_name = f"improvement/add-code-of-conduct-{uuid.uuid4().hex[:8]}"
        
        # Get default branch
        default_branch = await self.get_default_branch(owner, repo)
        
        # Create a new branch
        branch_result = await self.create_branch(owner, repo, branch_name, default_branch)
        if not branch_result["success"]:
            return branch_result
            
        # Generate CODE_OF_CONDUCT.md content
        conduct_content = """# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or
  advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Project maintainers are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the project team. All complaints will be reviewed and investigated
promptly and fairly.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org),
version 2.0, available at
[https://www.contributor-covenant.org/version/2/0/code_of_conduct.html](https://www.contributor-covenant.org/version/2/0/code_of_conduct.html).
"""
        
        # Create the file
        file_result = await self.create_file(
            owner=owner,
            repo=repo,
            path="CODE_OF_CONDUCT.md",
            content=conduct_content,
            message="Add CODE_OF_CONDUCT.md to define community standards",
            branch=branch_name
        )
        
        if not file_result["success"]:
            return file_result
            
        # Create the pull request
        pr_title = "Add CODE_OF_CONDUCT.md"
        pr_body = """## Add CODE_OF_CONDUCT.md file

This pull request adds a CODE_OF_CONDUCT.md file to define community standards.

### Why this is important:
- Explicitly defines expectations for behavior in the project community
- Creates a more welcoming environment for new contributors
- Establishes processes for addressing unacceptable behavior

This PR was automatically generated by the GitHub Repository Improvement tool.
"""
        
        pr_result = await self.create_pull_request(
            owner=owner,
            repo=repo,
            title=pr_title,
            head=branch_name,
            base=default_branch,
            body=pr_body
        )
        
        return pr_result
    
    async def create_linting_workflow(self, owner: str, repo: str) -> Dict[str, Any]:
        """Create a linting workflow and submit a PR."""
        logger.info(f"Creating linting workflow for {owner}/{repo}")
        
        # Generate unique branch name
        branch_name = f"improvement/add-linting-workflow-{uuid.uuid4().hex[:8]}"
        
        # Get default branch
        default_branch = await self.get_default_branch(owner, repo)
        
        # Create a new branch
        branch_result = await self.create_branch(owner, repo, branch_name, default_branch)
        if not branch_result["success"]:
            return branch_result
        
        # Determine primary language for the repository
        endpoint = f"/repos/{owner}/{repo}/languages"
        result = await self._make_request("GET", endpoint)
        
        languages = {}
        if result["success"]:
            languages = result["data"]
            
        # Generate appropriate linting workflow based on language
        top_language = max(languages.items(), key=lambda x: x[1])[0] if languages else "JavaScript"
        
        workflow_content = ""
        if top_language in ["Python"]:
            workflow_content = """name: Python Lint

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pylint black isort
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      
      - name: Check formatting with black
        run: black --check .
      
      - name: Check imports with isort
        run: isort --check --profile black .
      
      - name: Lint with flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Lint with pylint
        run: pylint $(git ls-files '*.py')
"""
        elif top_language in ["JavaScript", "TypeScript"]:
            workflow_content = """name: JS/TS Lint

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      
      - name: Install dependencies
        run: |
          npm ci || npm install
      
      - name: Lint with ESLint
        run: |
          npm install eslint --no-save
          npx eslint . --ext .js,.jsx,.ts,.tsx
"""
        else:
            # Generic workflow for other languages
            workflow_content = """name: Code Quality

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check file formatting
        uses: FranzDiebold/github-actions-markdown-link-check@v1
      
      - name: Super-Linter
        uses: github/super-linter@v4
        env:
          VALIDATE_ALL_CODEBASE: true
          DEFAULT_BRANCH: main
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""
            
        # Create the file
        file_result = await self.create_file(
            owner=owner,
            repo=repo,
            path=".github/workflows/lint.yml",
            content=workflow_content,
            message="Add linting workflow",
            branch=branch_name
        )
        
        if not file_result["success"]:
            return file_result
            
        # Create the pull request
        pr_title = "Add linting workflow"
        pr_body = f"""## Add linting workflow

This pull request adds a GitHub Actions workflow for linting code.

### Why this is important:
- Automatically checks code quality on every push and pull request
- Enforces consistent code style across the project
- Reduces time spent on code reviews for style issues
- Customized for {top_language}, the primary language in this repository

This PR was automatically generated by the GitHub Repository Improvement tool.
"""
        
        pr_result = await self.create_pull_request(
            owner=owner,
            repo=repo,
            title=pr_title,
            head=branch_name,
            base=default_branch,
            body=pr_body
        )
        
        return pr_result

async def main():
    parser = argparse.ArgumentParser(description="Create improvement PRs for a GitHub repository")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--improvement", required=True, choices=["changelog", "codeofconduct", "linting"],
                      help="Type of improvement to create")
    parser.add_argument("--token", help="GitHub API token (if not provided, uses GITHUB_TOKEN env var)")
    args = parser.parse_args()
    
    # Get token from args or environment
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("No GitHub token provided. Set GITHUB_TOKEN environment variable or use --token.")
        sys.exit(1)
    
    try:
        async with GitHubAPIClient(token) as client:
            # Verify credentials before proceeding
            endpoint = "/user"
            result = await client._make_request("GET", endpoint)
            
            if not result["success"]:
                logger.error(f"Authentication failed: {result.get('error')}")
                sys.exit(1)
                
            logger.info(f"Authenticated as {result['data']['login']}")
            
            # Create the requested improvement
            if args.improvement == "changelog":
                result = await client.create_changelog(args.owner, args.repo)
            elif args.improvement == "codeofconduct":
                result = await client.create_code_of_conduct(args.owner, args.repo)
            elif args.improvement == "linting":
                result = await client.create_linting_workflow(args.owner, args.repo)
            
            if result["success"]:
                pr = result["pull_request"]
                logger.info(f"Successfully created PR #{pr['number']}: {pr['title']}")
                logger.info(f"PR URL: {pr['html_url']}")
            else:
                logger.error(f"Failed to create improvement: {result.get('error')}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Error creating improvement PR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0) 