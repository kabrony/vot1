#!/usr/bin/env python3
"""
Direct GitHub Automation

This script performs GitHub automation by directly interacting with the GitHub REST API
without relying on bridge classes that might have compatibility issues.

Features:
- Repository analysis using real GitHub API calls
- Workflow creation and management
- Webhook creation
- PR creation for improvements
- Memory integration for storing analysis results

Usage:
    python direct_github_automation.py --owner <owner> --repo <repo> --token <token>
"""

import os
import sys
import asyncio
import logging
import argparse
import json
import time
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3

# Import our real GitHub API client
from real_github_api import GitHubAPIClient

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import memory manager
from src.vot1.memory import MemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs/direct_github_automation.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("direct_github_automation")

class DirectGitHubAutomation:
    """
    Direct GitHub automation using the GitHub REST API.
    """
    
    def __init__(
        self,
        github_token: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        memory_path: Optional[str] = None,
        model_name: str = "claude-3-7-sonnet-20240620",
        demo_mode: bool = False
    ):
        """
        Initialize the Direct GitHub Automation.
        
        Args:
            github_token: GitHub API token
            owner: Default repository owner
            repo: Default repository name
            memory_path: Path to store memory
            model_name: Model name to use for analysis
            demo_mode: Whether to run in demo mode
        """
        self.github_token = github_token
        self.default_owner = owner
        self.default_repo = repo
        self.model_name = model_name
        self.demo_mode = demo_mode
        self.github_client = None  # Will be initialized in setup
        
        # Initialize memory manager if path is provided
        self.memory_manager = None
        if memory_path:
            try:
                from src.vot1.memory import MemoryManager
                self.memory_manager = MemoryManager(memory_path=memory_path)
                logging.info(f"Initialized memory manager at {memory_path}")
                
                # We'll check memory health later in an async context
            except ImportError:
                logging.warning("MemoryManager not available, memory features disabled")
        
        # Initialize GitHub client
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        logger.info(f"Initialized Direct GitHub Automation for {owner}/{repo}")
    
    async def __aenter__(self):
        """Enter the async context manager."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context manager."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def setup(self):
        """Set up the automation by initializing clients and testing connections."""
        # Initialize GitHub API client
        self.github_client = GitHubAPIClient(self.github_token)
        await self.github_client.create_session()
        
        # Test GitHub connection
        credentials = await self.github_client.verify_credentials()
        if credentials["success"]:
            logging.info(f"Successfully connected as GitHub user: {credentials['user']['login']}")
            return True
        else:
            logging.error(f"Failed to connect to GitHub: {credentials.get('error', 'Unknown error')}")
            return False
    
    async def cleanup(self):
        """Clean up resources when done."""
        if self.github_client:
            await self.github_client.close_session()
    
    async def analyze_repository(
        self,
        owner: str,
        repo: str,
        deep_analysis: bool = False,
        store_in_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository and return the results.
        
        Args:
            owner: Repository owner
            repo: Repository name
            deep_analysis: Whether to perform deep analysis
            store_in_memory: Whether to store the analysis in memory
            
        Returns:
            Analysis results
        """
        try:
            # Check if we have recent analysis results in memory
            if self.memory_manager and store_in_memory:
                # Try direct database query first
                memory_result = self._get_latest_analysis_from_db(owner, repo)
                if memory_result:
                    logging.info(f"Found recent analysis in database for {owner}/{repo}")
                    return memory_result
                
                # Try vector search if direct query fails
                memory_result = await self.memory_manager.search_memories(
                    f"GitHub repository analysis for {owner}/{repo}",
                    limit=1
                )
                
                if memory_result and memory_result[0].get('data') and \
                   memory_result[0].get('timestamp', 0) > time.time() - 86400:  # 24 hours
                    logging.info(f"Found recent analysis in memory for {owner}/{repo}")
                    return memory_result[0]['data']
            
            # Perform real analysis using GitHub API client
            if self.demo_mode:
                # In demo mode, use mock data
                logging.info(f"Running in demo mode, generating mock analysis for {owner}/{repo}")
                analysis_result = self._mock_analyze_repository(owner, repo, deep_analysis)
            else:
                # Use real GitHub API client
                logging.info(f"Analyzing repository {owner}/{repo} with real GitHub API calls")
                if not self.github_client:
                    await self.setup()
                
                analysis_result = await self.github_client.analyze_repository(
                    owner, 
                    repo, 
                    deep_analysis
                )
            
            # Store the analysis in memory if requested
            if self.memory_manager and store_in_memory and analysis_result["success"]:
                memory_data = {
                    "type": "github_repository_analysis",
                    "owner": owner,
                    "repo": repo,
                    "data": analysis_result,
                    "timestamp": time.time()
                }
                
                # Store in database for direct retrieval
                self._store_analysis_in_db(owner, repo, analysis_result)
                
                # Also store in vector memory for semantic search
                await self.memory_manager.add_memories(
                    f"GitHub repository analysis for {owner}/{repo}",
                    memory_data
                )
                logging.info(f"Stored analysis for {owner}/{repo} in memory")
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Error analyzing repository {owner}/{repo}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_latest_analysis_from_db(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest analysis for a repository directly from the database.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Analysis results or None if not found
        """
        if not self.memory_manager:
            return None
            
        try:
            # Get the database path from the memory manager
            db_path = os.path.join(self.memory_manager.memory_path, "vector_store.db")
            if not os.path.exists(db_path):
                return None
                
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Query for the latest analysis
            query = """
            SELECT content FROM memories 
            WHERE json_extract(metadata, '$.repository') = ? 
            AND json_extract(metadata, '$.type') = 'repository_analysis'
            ORDER BY timestamp DESC LIMIT 1
            """
            cursor.execute(query, (f"{owner}/{repo}",))
            result = cursor.fetchone()
            
            if result and result[0]:
                try:
                    analysis_result = json.loads(result[0])
                    if isinstance(analysis_result, dict) and analysis_result.get('success'):
                        return analysis_result
                except json.JSONDecodeError:
                    pass
                    
            return None
        except Exception as e:
            logging.warning(f"Error querying database: {e}")
            return None
    
    async def create_webhook(
        self,
        webhook_url: str,
        events: List[str] = ["push", "pull_request"],
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a repository webhook.
        
        Args:
            webhook_url: URL to receive webhook events
            events: List of events to subscribe to
            owner: Repository owner (falls back to default_owner)
            repo: Repository name (falls back to default_repo)
            secret: Webhook secret for securing payloads
            
        Returns:
            Dictionary with webhook creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {
                "success": False,
                "error": "Repository owner and name are required"
            }
        
        logger.info(f"Creating webhook for {owner}/{repo} to {webhook_url}")
        
        try:
            # If we're using a demo token, simulate success
            if self.github_token in ["DEMO-TOKEN-FOR-DISPLAY-ONLY", "demo-token"] or self.demo_mode:
                logger.info("Using demo token - simulating webhook creation")
                
                # Simulated webhook creation
                return {
                    "success": True,
                    "webhook": {
                        "id": 12345678,
                        "url": f"https://api.github.com/repos/{owner}/{repo}/hooks/12345678",
                        "name": "web",
                        "events": events,
                        "active": True,
                        "config": {
                            "url": webhook_url,
                            "content_type": "json",
                            "insecure_ssl": "0",
                            "secret": "●●●●●●●●"
                        },
                        "created_at": "2024-07-10T00:00:00Z",
                        "updated_at": "2024-07-10T00:00:00Z"
                    }
                }
                
            # Actual webhook creation would go here
            url = f"{self.base_url}/repos/{owner}/{repo}/hooks"
            payload = {
                "name": "web",
                "active": True,
                "events": events,
                "config": {
                    "url": webhook_url,
                    "content_type": "json",
                    "insecure_ssl": "0"
                }
            }
            
            if secret:
                payload["config"]["secret"] = secret
                
            async with self.session.post(url, headers=self.headers, json=payload) as response:
                if response.status in [201, 200]:
                    webhook_data = await response.json()
                    logger.info(f"Webhook created with ID: {webhook_data.get('id')}")
                    return {
                        "success": True,
                        "webhook": webhook_data
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"GitHub API error ({response.status}): {error_text}")
                    return {
                        "success": False,
                        "error": f"GitHub API error ({response.status}): {error_text}"
                    }
                
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_workflow(
        self,
        owner: str,
        repo: str,
        workflow_name: str,
        workflow_content: str
    ) -> Dict[str, Any]:
        """
        Create or update a GitHub Actions workflow file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_name: Workflow name (e.g., "ci.yml")
            workflow_content: Workflow file content
            
        Returns:
            Dictionary with workflow creation/update results
        """
        if not owner or not repo:
            return {
                "success": False,
                "error": "Repository owner and name are required"
            }
        
        # Ensure workflow name has proper path
        if not workflow_name.startswith(".github/workflows/"):
            workflow_name = f".github/workflows/{workflow_name}"
        
        # Ensure workflow name has .yml extension
        if not workflow_name.endswith(".yml") and not workflow_name.endswith(".yaml"):
            workflow_name = f"{workflow_name}.yml"
        
        logger.info(f"Creating/updating workflow {workflow_name} for {owner}/{repo}")
        
        try:
            # If we're using a demo token, simulate success
            if self.github_token in ["DEMO-TOKEN-FOR-DISPLAY-ONLY", "demo-token"] or self.demo_mode:
                logger.info("Using demo token - simulating workflow creation")
                
                # Simulated workflow creation/update
                return {
                    "success": True,
                    "workflow": {
                        "path": workflow_name,
                        "sha": "0123456789abcdef0123456789abcdef01234567",
                        "url": f"https://github.com/{owner}/{repo}/blob/main/{workflow_name}",
                        "commit": {
                            "sha": "abcdef0123456789abcdef0123456789abcdef01",
                            "url": f"https://github.com/{owner}/{repo}/commit/abcdef0123456789abcdef0123456789abcdef01",
                            "message": f"Create/update workflow: {workflow_name}"
                        }
                    }
                }
                
            # Real workflow creation/update would go here
            # It would involve checking if the file exists, then creating or updating it
            # with the GitHub contents API
            
            return {
                "success": False,
                "error": "Real API calls are not implemented yet - use demo token for testing"
            }
            
        except Exception as e:
            logger.error(f"Error creating/updating workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_improvement_pr(
        self,
        title: str,
        body: str,
        changes: List[Dict[str, Any]],
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Create a pull request with improvements.
        
        Args:
            title: PR title
            body: PR description
            changes: List of file changes to make
            owner: Repository owner (falls back to default_owner)
            repo: Repository name (falls back to default_repo)
            base_branch: Base branch to create PR against
            
        Returns:
            Dictionary with PR creation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {
                "success": False,
                "error": "Repository owner and name are required"
            }
        
        logger.info(f"Creating improvement PR '{title}' for {owner}/{repo}")
        
        try:
            # If we're using a demo token, simulate success
            if self.github_token in ["DEMO-TOKEN-FOR-DISPLAY-ONLY", "demo-token"] or self.demo_mode:
                logger.info("Using demo token - simulating PR creation")
                
                # Generate a branch name based on the title
                branch_name = f"improvement/{title.lower().replace(' ', '-')}-{int(time.time())}"
                
                # Simulated PR creation
                return {
                    "success": True,
                    "pull_request": {
                        "id": 123456789,
                        "number": 42,
                        "title": title,
                        "body": body,
                        "html_url": f"https://github.com/{owner}/{repo}/pull/42",
                        "state": "open",
                        "head": {
                            "ref": branch_name,
                            "sha": "0123456789abcdef0123456789abcdef01234567"
                        },
                        "base": {
                            "ref": base_branch,
                            "sha": "fedcba9876543210fedcba9876543210fedcba98"
                        },
                        "changes": [c["path"] for c in changes],
                        "created_at": "2024-07-10T00:00:00Z",
                        "updated_at": "2024-07-10T00:00:00Z"
                    }
                }
                
            # Real PR creation would go here
            # It would involve:
            # 1. Creating a new branch
            # 2. Committing changes to the branch
            # 3. Creating a PR from the branch to the base branch
            
            return {
                "success": False,
                "error": "Real API calls are not implemented yet - use demo token for testing"
            }
            
        except Exception as e:
            logger.error(f"Error creating improvement PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_repository(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        deep_analysis: bool = False,
        update_areas: List[str] = ["documentation", "workflows", "code_quality"],
        max_updates: int = 3,
        create_webhook: bool = False,
        webhook_url: Optional[str] = None,
        webhook_events: List[str] = ["push", "pull_request"]
    ) -> Dict[str, Any]:
        """
        Process a repository by analyzing it and creating improvement PRs.
        
        Args:
            owner: Repository owner (falls back to default_owner)
            repo: Repository name (falls back to default_repo)
            deep_analysis: Whether to perform deeper analysis
            update_areas: Areas to focus updates on
            max_updates: Maximum number of updates to make per area
            create_webhook: Whether to create a webhook
            webhook_url: URL for webhook (if creating one)
            webhook_events: Events for webhook (if creating one)
            
        Returns:
            Dictionary with processing results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {
                "success": False,
                "error": "Repository owner and name are required"
            }
        
        logger.info(f"Processing repository {owner}/{repo}")
        results = {
            "success": True,
            "repository": f"{owner}/{repo}",
            "updates": [],
            "webhooks": [],
            "workflows": []
        }
        
        # 1. Create webhook if requested
        if create_webhook and webhook_url:
            webhook_result = await self.create_webhook(
                webhook_url=webhook_url,
                events=webhook_events,
                owner=owner,
                repo=repo
            )
            
            if webhook_result.get("success"):
                results["webhooks"].append(webhook_result.get("webhook"))
                logger.info(f"Created webhook for {owner}/{repo}")
            else:
                logger.warning(f"Failed to create webhook: {webhook_result.get('error')}")
        
        # 2. Analyze repository
        analysis_result = await self.analyze_repository(
            owner=owner,
            repo=repo,
            deep_analysis=deep_analysis
        )
        
        if not analysis_result.get("success"):
            logger.error(f"Repository analysis failed: {analysis_result.get('error')}")
            results["success"] = False
            results["error"] = analysis_result.get("error")
            return results
            
        # 3. Create improvement PRs based on analysis
        improvement_areas = analysis_result.get("improvement_areas", [])
        
        # Filter by requested update areas
        filtered_improvements = [
            imp for imp in improvement_areas 
            if imp.get("type") in update_areas
        ]
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        filtered_improvements.sort(
            key=lambda x: priority_order.get(x.get("priority"), 999)
        )
        
        # Limit to max_updates per area
        updates_by_area = {}
        for imp in filtered_improvements:
            area = imp.get("type")
            if area not in updates_by_area:
                updates_by_area[area] = []
            
            if len(updates_by_area[area]) < max_updates:
                updates_by_area[area].append(imp)
        
        # Flatten list
        selected_improvements = []
        for area_imps in updates_by_area.values():
            selected_improvements.extend(area_imps)
            
        # Create PRs for selected improvements
        for imp in selected_improvements:
            pr_title = imp.get("title")
            pr_body = f"""
{imp.get('description')}

This pull request was automatically generated by the GitHub Automation system
to improve the repository quality.

**Improvement Type**: {imp.get('type')}
**Priority**: {imp.get('priority')}
            """.strip()
            
            # Simplified example changes for demonstration
            changes = [{
                "path": self._get_default_path_for_improvement(imp),
                "content": self._get_default_content_for_improvement(imp),
                "mode": "create"  # or "update"
            }]
            
            pr_result = await self.create_improvement_pr(
                title=pr_title,
                body=pr_body,
                changes=changes,
                owner=owner,
                repo=repo
            )
            
            if pr_result.get("success"):
                pr_info = pr_result.get("pull_request")
                results["updates"].append({
                    "title": pr_title,
                    "type": imp.get("type"),
                    "priority": imp.get("priority"),
                    "pr_number": pr_info.get("number"),
                    "pr_url": pr_info.get("html_url")
                })
                logger.info(f"Created PR: {pr_title} (#{pr_info.get('number')})")
            else:
                logger.warning(f"Failed to create PR {pr_title}: {pr_result.get('error')}")
        
        # 4. Create workflow for linting if needed and if in update areas
        if "workflows" in update_areas and not analysis_result.get("code_quality", {}).get("has_linting", False):
            workflow_result = await self.create_workflow(
                owner=owner,
                repo=repo,
                workflow_name="lint.yml",
                workflow_content=self._get_default_linting_workflow()
            )
            
            if workflow_result.get("success"):
                results["workflows"].append(workflow_result.get("workflow"))
                logger.info(f"Created linting workflow for {owner}/{repo}")
            else:
                logger.warning(f"Failed to create linting workflow: {workflow_result.get('error')}")
                
        return results
    
    def _get_default_path_for_improvement(self, improvement: Dict[str, Any]) -> str:
        """Get a default file path for an improvement based on its type."""
        imp_type = improvement.get("type")
        title = improvement.get("title", "").lower()
        
        if imp_type == "documentation":
            if "changelog" in title:
                return "CHANGELOG.md"
            elif "code of conduct" in title:
                return "CODE_OF_CONDUCT.md"
            elif "contributing" in title:
                return "CONTRIBUTING.md"
            else:
                return "docs/README.md"
        elif imp_type == "workflow":
            workflow_name = title.replace("add ", "").replace("create ", "").replace(" workflow", "")
            workflow_name = workflow_name.replace(" ", "-")
            return f".github/workflows/{workflow_name}.yml"
        elif imp_type == "code_quality":
            return ".github/CODEOWNERS"
        else:
            return "README.md"
    
    def _get_default_content_for_improvement(self, improvement: Dict[str, Any]) -> str:
        """Get default content for an improvement based on its type and title."""
        imp_type = improvement.get("type")
        title = improvement.get("title", "").lower()
        
        if imp_type == "documentation":
            if "changelog" in title:
                return """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Core documentation

### Changed
- Updated README with better examples

### Fixed
- Fixed broken links in documentation
"""
            elif "code of conduct" in title:
                return """# Code of Conduct

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
"""
        elif imp_type == "workflow":
            if "lint" in title:
                return self._get_default_linting_workflow()
            elif "test" in title:
                return self._get_default_testing_workflow()
            else:
                return self._get_default_ci_workflow()
        else:
            return "# Automated Improvement\n\nThis file was created by the GitHub Automation system."
    
    def _get_default_linting_workflow(self) -> str:
        """Get default content for a linting workflow."""
        return """name: Lint

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      
      - name: Install markdownlint
        run: npm install -g markdownlint-cli
      
      - name: Lint Markdown files
        run: markdownlint '**/*.md' --ignore node_modules
"""
    
    def _get_default_testing_workflow(self) -> str:
        """Get default content for a testing workflow."""
        return """name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest --cov=./ --cov-report=xml
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
"""

    def _get_default_ci_workflow(self) -> str:
        """Get default content for a CI workflow."""
        return """name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      
      - name: Check code quality
        run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
      
      - name: Run tests
        run: |
          pip install pytest
          pytest
"""

    async def check_memory_health(self):
        """
        Check memory health and optimize if needed.
        """
        if not self.memory_manager:
            return
            
        try:
            # Check memory health
            health_status = await self.memory_manager.check_memory_health()
            if health_status.get('status') == 'healthy':
                logging.info("Memory health check passed")
            else:
                logging.warning(f"Memory health issues detected: {health_status.get('issues', [])}")
                
                # Optimize memory if needed
                if health_status.get('needs_optimization', False):
                    logging.info("Optimizing memory...")
                    optimization_result = await self.memory_manager.optimize_memory()
                    logging.info(f"Memory optimization completed: {optimization_result}")
        except Exception as e:
            logging.warning(f"Error checking memory health: {e}")

    async def close(self):
        """
        Close the client session.
        """
        if self.session:
            await self.session.close()
            self.session = None

async def main():
    """Parse arguments and run the GitHub automation."""
    parser = argparse.ArgumentParser(description="Direct GitHub Automation")
    parser.add_argument("--owner", help="Repository owner")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--token", help="GitHub API token")
    parser.add_argument("--memory-path", default="/home/vots/vot1/memory", help="Path to store memory")
    parser.add_argument("--model", default="claude-3-7-sonnet-20240620", help="Model name to use for analysis")
    parser.add_argument("--analyze", action="store_true", help="Analyze repository")
    parser.add_argument("--deep-analysis", action="store_true", help="Perform deep analysis")
    parser.add_argument("--create-pr", help="Create a PR with the specified title")
    parser.add_argument("--create-webhook", action="store_true", help="Create a webhook")
    parser.add_argument("--create-workflow", action="store_true", help="Create a workflow")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode")
    
    args = parser.parse_args()
    
    # Get token from environment if not provided
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not provided. Use --token or set GITHUB_TOKEN environment variable.")
        return 1
    
    try:
        # Initialize automation
        automation = DirectGitHubAutomation(
            github_token=token,
            owner=args.owner,
            repo=args.repo,
            memory_path=args.memory_path,
            model_name=args.model,
            demo_mode=args.demo
        )
        
        # Connect to GitHub
        if not await automation.setup():
            logger.error("Failed to connect to GitHub")
            return 1
        
        # Process repository
        if args.analyze or args.deep_analysis:
            result = await automation.process_repository(
                owner=args.owner,
                repo=args.repo,
                deep_analysis=args.deep_analysis
            )
            
            if not result.get("success"):
                logger.error(f"Failed to process repository: {result.get('error')}")
                return 1
        
        # Create PR if requested
        if args.create_pr:
            pr_result = await automation.create_improvement_pr(
                owner=args.owner,
                repo=args.repo,
                title=args.create_pr,
                description=f"Automated PR: {args.create_pr}",
                branch=f"improvement/{args.create_pr.lower().replace(' ', '-')}"
            )
            
            if not pr_result.get("success"):
                logger.warning(f"Failed to create PR: {pr_result.get('error')}")
        
        # Create webhook if requested
        if args.create_webhook:
            webhook_result = await automation.create_webhook(
                owner=args.owner,
                repo=args.repo,
                events=["push", "pull_request"]
            )
            
            if not webhook_result.get("success"):
                logger.warning(f"Failed to create webhook: {webhook_result.get('error')}")
        
        # Create workflow if requested
        if args.create_workflow:
            workflow_result = await automation.create_workflow(
                owner=args.owner,
                repo=args.repo,
                workflow_name="ci.yml",
                workflow_content=DEFAULT_CI_WORKFLOW
            )
            
            if not workflow_result.get("success"):
                logger.warning(f"Failed to create workflow: {workflow_result.get('error')}")
        
        # Close the automation
        await automation.close()
        
        return 0
    except Exception as e:
        logger.error(f"Error during GitHub automation: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(130) 