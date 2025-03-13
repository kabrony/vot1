"""
VOT1 GitHub Integration Module - Enhanced Version

This module provides advanced integration with GitHub for repository analysis,
automated improvements, and workflow management.
"""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Tuple, Union, Any
import base64
import urllib.parse
import requests
from github import Github, GithubIntegration
from github.Repository import Repository
from github.ContentFile import ContentFile
from github.PullRequest import PullRequest
from github.Issue import Issue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/github_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubIntegration:
    """
    Enhanced GitHub Integration class providing advanced capabilities for VOT1's
    interaction with GitHub repositories.
    """
    
    def __init__(self, token: Optional[str] = None, app_id: Optional[int] = None, 
                 private_key_path: Optional[str] = None, installation_id: Optional[int] = None):
        """
        Initialize GitHub integration with either a personal access token or GitHub App credentials.
        
        Args:
            token: GitHub personal access token
            app_id: GitHub App ID
            private_key_path: Path to the GitHub App's private key
            installation_id: GitHub App installation ID
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.app_id = app_id or os.environ.get("GITHUB_APP_ID")
        self.installation_id = installation_id or os.environ.get("GITHUB_INSTALLATION_ID")
        self.private_key_path = private_key_path or os.environ.get("GITHUB_PRIVATE_KEY_PATH")
        
        # Setup client based on available credentials
        if self.token:
            self.client = Github(self.token)
            self.using_app = False
            logger.info("GitHub client initialized with personal access token")
        elif self.app_id and self.private_key_path and self.installation_id:
            with open(self.private_key_path, 'r') as key_file:
                private_key = key_file.read()
            
            self.integration = GithubIntegration(self.app_id, private_key)
            self.using_app = True
            self.token = self.integration.get_access_token(self.installation_id).token
            self.client = Github(self.token)
            logger.info("GitHub client initialized with GitHub App credentials")
        else:
            raise ValueError("Either GitHub token or GitHub App credentials (app_id, private_key_path, installation_id) must be provided")
    
    def get_repository(self, repo_name: str) -> Repository:
        """
        Get a GitHub repository by name.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            
        Returns:
            GitHub Repository object
        """
        try:
            return self.client.get_repo(repo_name)
        except Exception as e:
            logger.error(f"Error accessing repository {repo_name}: {str(e)}")
            raise
    
    def get_repository_content(self, repo_name: str, path: str, ref: Optional[str] = None) -> Dict:
        """
        Get repository content with advanced error handling and retry logic.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            path: Path to the file or directory
            ref: Git reference (branch, tag, or commit SHA)
            
        Returns:
            Dictionary with file content and metadata
        """
        repo = self.get_repository(repo_name)
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                content = repo.get_contents(path, ref=ref)
                if isinstance(content, list):
                    # Directory content
                    return {
                        "type": "directory",
                        "path": path,
                        "items": [
                            {
                                "name": item.name,
                                "path": item.path,
                                "type": "file" if item.type == "file" else "directory",
                                "size": item.size if hasattr(item, "size") else None,
                                "sha": item.sha
                            } for item in content
                        ]
                    }
                else:
                    # File content
                    content_decoded = base64.b64decode(content.content).decode("utf-8")
                    return {
                        "type": "file",
                        "path": path,
                        "content": content_decoded,
                        "size": content.size,
                        "sha": content.sha
                    }
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error getting {path} in {repo_name} (attempt {retry_count+1}/{max_retries}): {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
            except Exception as e:
                logger.error(f"Error getting {path} in {repo_name}: {str(e)}")
                raise
        
        raise Exception(f"Failed to get repository content after {max_retries} attempts")
    
    def create_or_update_file(self, repo_name: str, path: str, content: str, 
                              commit_message: str, branch: str = "main", 
                              update_if_exists: bool = True) -> Dict:
        """
        Create or update a file in the repository with improved error handling.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            path: Path to the file
            content: Content to write to the file
            commit_message: Commit message
            branch: Branch to commit to
            update_if_exists: Whether to update the file if it already exists
            
        Returns:
            Dictionary with information about the commit
        """
        repo = self.get_repository(repo_name)
        file_sha = None
        
        try:
            contents = repo.get_contents(path, ref=branch)
            if not update_if_exists:
                logger.warning(f"File {path} already exists and update_if_exists is False")
                return {"error": "File already exists", "status": "error"}
            file_sha = contents.sha
        except:
            # File doesn't exist, which is fine if we're creating it
            pass
        
        try:
            result = repo.create_file(
                path=path, 
                message=commit_message,
                content=content,
                branch=branch,
                sha=file_sha
            )
            
            # Format the response
            if file_sha:
                logger.info(f"Updated file {path} in {repo_name}")
                return {
                    "status": "updated",
                    "file": path,
                    "commit": result["commit"].sha
                }
            else:
                logger.info(f"Created file {path} in {repo_name}")
                return {
                    "status": "created",
                    "file": path,
                    "commit": result["commit"].sha
                }
        except Exception as e:
            logger.error(f"Error creating/updating file {path} in {repo_name}: {str(e)}")
            raise
    
    def create_pull_request(self, repo_name: str, title: str, body: str, 
                           head: str, base: str = "main", draft: bool = False) -> PullRequest:
        """
        Create a pull request with enhanced functionality.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            title: Pull request title
            body: Pull request description
            head: Name of the branch where changes are implemented
            base: Name of the branch to merge into
            draft: Whether to create a draft pull request
            
        Returns:
            GitHub PullRequest object
        """
        repo = self.get_repository(repo_name)
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )
            logger.info(f"Created pull request #{pr.number} in {repo_name}")
            return pr
        except Exception as e:
            logger.error(f"Error creating pull request in {repo_name}: {str(e)}")
            raise
    
    def create_issue(self, repo_name: str, title: str, body: str, 
                    labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> Issue:
        """
        Create an issue with enhanced functionality.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            title: Issue title
            body: Issue description
            labels: List of labels to apply
            assignees: List of users to assign
            
        Returns:
            GitHub Issue object
        """
        repo = self.get_repository(repo_name)
        try:
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or []
            )
            logger.info(f"Created issue #{issue.number} in {repo_name}")
            return issue
        except Exception as e:
            logger.error(f"Error creating issue in {repo_name}: {str(e)}")
            raise
    
    def analyze_code(self, repo_name: str, path: str, branch: str = "main") -> Dict[str, Any]:
        """
        Analyze code in the repository to identify improvement opportunities.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            path: Path to analyze (file or directory)
            branch: Branch to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            content = self.get_repository_content(repo_name, path, ref=branch)
            
            if content["type"] == "file":
                # Perform analysis on file content
                analysis = {
                    "file": path,
                    "loc": len(content["content"].splitlines()),
                    "suggestions": self._analyze_file_content(content["content"], path)
                }
                return analysis
            elif content["type"] == "directory":
                # Recursively analyze directory contents
                analyses = []
                for item in content["items"]:
                    if item["type"] == "file" and item["name"].endswith((".py", ".js", ".html", ".css")):
                        file_analysis = self.analyze_code(repo_name, item["path"], branch)
                        analyses.append(file_analysis)
                
                return {
                    "directory": path,
                    "file_count": len(analyses),
                    "analyses": analyses
                }
        except Exception as e:
            logger.error(f"Error analyzing code in {path} ({repo_name}): {str(e)}")
            return {"error": str(e), "path": path}
    
    def _analyze_file_content(self, content: str, path: str) -> List[Dict[str, Any]]:
        """
        Analyze file content for improvement opportunities.
        
        Args:
            content: File content
            path: File path
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        lines = content.splitlines()
        
        # Check for TODOs
        for i, line in enumerate(lines):
            if "TODO" in line or "FIXME" in line:
                suggestions.append({
                    "type": "todo",
                    "line": i + 1,
                    "message": f"Found TODO/FIXME: {line.strip()}",
                    "severity": "info"
                })
        
        # Check for long lines
        for i, line in enumerate(lines):
            if len(line) > 100:
                suggestions.append({
                    "type": "style",
                    "line": i + 1,
                    "message": f"Line exceeds 100 characters ({len(line)} chars)",
                    "severity": "warning"
                })
        
        # File-specific checks
        if path.endswith(".py"):
            # Python-specific checks
            suggestions.extend(self._analyze_python_content(content))
        elif path.endswith(".js"):
            # JavaScript-specific checks
            suggestions.extend(self._analyze_javascript_content(content))
            
        return suggestions
    
    def _analyze_python_content(self, content: str) -> List[Dict[str, Any]]:
        """Simple Python code analysis."""
        suggestions = []
        lines = content.splitlines()
        
        # Check for missing docstrings
        has_docstring = False
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if '"""' in line or "'''" in line:
                has_docstring = True
                break
        
        if not has_docstring and len(lines) > 5:  # Only suggest for non-trivial files
            suggestions.append({
                "type": "style",
                "line": 1,
                "message": "Missing module docstring",
                "severity": "warning"
            })
            
        # Check for print statements (which might indicate debugging code)
        for i, line in enumerate(lines):
            if "print(" in line and not line.strip().startswith("#"):
                suggestions.append({
                    "type": "debug",
                    "line": i + 1,
                    "message": "Found print statement, consider using logging",
                    "severity": "info"
                })
                
        return suggestions
    
    def _analyze_javascript_content(self, content: str) -> List[Dict[str, Any]]:
        """Simple JavaScript code analysis."""
        suggestions = []
        lines = content.splitlines()
        
        # Check for console.log statements
        for i, line in enumerate(lines):
            if "console.log(" in line and not line.strip().startswith("//"):
                suggestions.append({
                    "type": "debug",
                    "line": i + 1,
                    "message": "Found console.log statement, consider removing or replacing with proper logging",
                    "severity": "info"
                })
                
        # Check for var instead of let/const
        for i, line in enumerate(lines):
            if "var " in line and not line.strip().startswith("//"):
                suggestions.append({
                    "type": "style",
                    "line": i + 1,
                    "message": "Using 'var', consider using 'let' or 'const' instead",
                    "severity": "warning"
                })
                
        return suggestions
    
    def create_webhook(self, repo_name: str, webhook_url: str, 
                       events: List[str] = None, active: bool = True) -> Dict:
        """
        Create a webhook for the repository.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            webhook_url: URL to send webhook events to
            events: List of events to trigger the webhook
            active: Whether the webhook is active
            
        Returns:
            Webhook information
        """
        repo = self.get_repository(repo_name)
        if events is None:
            events = ["push", "pull_request"]
            
        try:
            webhook = repo.create_hook(
                name="web",
                config={"url": webhook_url, "content_type": "json"},
                events=events,
                active=active
            )
            
            logger.info(f"Created webhook in {repo_name} pointing to {webhook_url}")
            return {
                "id": webhook.id,
                "url": webhook_url,
                "events": events,
                "active": active
            }
        except Exception as e:
            logger.error(f"Error creating webhook in {repo_name}: {str(e)}")
            raise
            
    def setup_branch_protection(self, repo_name: str, branch: str = "main", 
                               required_reviews: int = 1, require_status_checks: bool = True,
                               status_checks: List[str] = None) -> Dict:
        """
        Set up branch protection rules.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            branch: Branch to protect
            required_reviews: Number of required reviews to merge
            require_status_checks: Whether to require status checks to pass
            status_checks: List of required status checks
            
        Returns:
            Branch protection information
        """
        repo = self.get_repository(repo_name)
        
        # Get branch reference
        try:
            branch_ref = repo.get_branch(branch)
            
            # Set up protection
            protection_params = {
                "required_pull_request_reviews": {
                    "required_approving_review_count": required_reviews,
                    "dismiss_stale_reviews": True,
                    "require_code_owner_reviews": False
                },
                "enforce_admins": False,
                "restrictions": None
            }
            
            if require_status_checks and status_checks:
                protection_params["required_status_checks"] = {
                    "strict": True,
                    "contexts": status_checks
                }
            
            branch_ref.edit_protection(**protection_params)
            
            logger.info(f"Set up branch protection for {branch} in {repo_name}")
            return {
                "branch": branch,
                "required_reviews": required_reviews,
                "require_status_checks": require_status_checks,
                "status_checks": status_checks
            }
        except Exception as e:
            logger.error(f"Error setting up branch protection in {repo_name}: {str(e)}")
            raise
    
    def create_github_action(self, repo_name: str, workflow_name: str, 
                           workflow_content: str, commit_message: str = None,
                           branch: str = "main") -> Dict:
        """
        Create or update a GitHub Actions workflow file.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            workflow_name: Name of the workflow (without .yml extension)
            workflow_content: YAML content of the workflow
            commit_message: Commit message
            branch: Branch to commit to
            
        Returns:
            Result of the file creation
        """
        if not workflow_name.endswith(".yml"):
            workflow_name += ".yml"
            
        workflow_path = f".github/workflows/{workflow_name}"
        
        if commit_message is None:
            commit_message = f"Add GitHub Actions workflow: {workflow_name}"
            
        # Make sure the directory exists
        repo = self.get_repository(repo_name)
        try:
            repo.get_contents(".github/workflows", ref=branch)
        except:
            # Create the workflows directory if it doesn't exist
            try:
                repo.get_contents(".github", ref=branch)
            except:
                # Create .github directory if it doesn't exist
                self.create_or_update_file(
                    repo_name=repo_name,
                    path=".github/.gitkeep",
                    content="# GitHub configuration directory",
                    commit_message="Create .github directory",
                    branch=branch
                )
            
            # Now create the workflows directory
            self.create_or_update_file(
                repo_name=repo_name,
                path=".github/workflows/.gitkeep",
                content="# GitHub Actions workflows directory",
                commit_message="Create GitHub Actions workflows directory",
                branch=branch
            )
        
        # Create or update the workflow file
        return self.create_or_update_file(
            repo_name=repo_name,
            path=workflow_path,
            content=workflow_content,
            commit_message=commit_message,
            branch=branch
        )
    
    def generate_workflow_file(self, workflow_type: str, repo_name: str) -> str:
        """
        Generate GitHub Actions workflow file content based on type.
        
        Args:
            workflow_type: Type of workflow to generate (e.g., "python", "node", "docker")
            repo_name: Repository name to customize the workflow
            
        Returns:
            Workflow file content as YAML string
        """
        if workflow_type == "python":
            return self._generate_python_workflow(repo_name)
        elif workflow_type == "node":
            return self._generate_node_workflow(repo_name)
        elif workflow_type == "docker":
            return self._generate_docker_workflow(repo_name)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    def _generate_python_workflow(self, repo_name: str) -> str:
        """Generate a Python CI workflow."""
        return f"""name: Python CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v4
      with:
        python-version: ${{{{ matrix.python-version }}}}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest pytest-cov flake8
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - name: Test with pytest
      run: |
        pytest --cov=./ --cov-report=xml
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
"""
    
    def _generate_node_workflow(self, repo_name: str) -> str:
        """Generate a Node.js CI workflow."""
        return f"""name: Node.js CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [14.x, 16.x, 18.x]

    steps:
    - uses: actions/checkout@v3
    - name: Use Node.js ${{{{ matrix.node-version }}}}
      uses: actions/setup-node@v3
      with:
        node-version: ${{{{ matrix.node-version }}}}
        cache: 'npm'
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test
"""
    
    def _generate_docker_workflow(self, repo_name: str) -> str:
        """Generate a Docker build and push workflow."""
        repo_parts = repo_name.split("/")
        image_name = repo_parts[1].lower() if len(repo_parts) > 1 else repo_name.lower()
        
        return f"""name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Login to GitHub Container Registry
      if: github.event_name != 'pull_request'
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{{{ github.actor }}}}
        password: ${{{{ secrets.GITHUB_TOKEN }}}}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/${{{{ github.repository_owner }}}}/{image_name}
        
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: ${{{{ github.event_name != 'pull_request' }}}}
        tags: ${{{{ steps.meta.outputs.tags }}}}
        labels: ${{{{ steps.meta.outputs.labels }}}}
        cache-from: type=gha
        cache-to: type=gha,mode=max
"""
    
    def get_repo_health_check(self, repo_name: str) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on a repository.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            
        Returns:
            Dictionary with health check results
        """
        repo = self.get_repository(repo_name)
        
        try:
            # Get repository metadata
            issues_count = repo.open_issues_count
            stars_count = repo.stargazers_count
            forks_count = repo.forks_count
            
            # Check for essential files
            has_readme = False
            has_license = False
            has_contributing = False
            has_code_of_conduct = False
            has_gitignore = False
            has_ci = False
            
            try:
                repo.get_contents("README.md")
                has_readme = True
            except:
                pass
                
            try:
                repo.get_license()
                has_license = True
            except:
                pass
                
            try:
                repo.get_contents("CONTRIBUTING.md")
                has_contributing = True
            except:
                pass
                
            try:
                repo.get_contents("CODE_OF_CONDUCT.md")
                has_code_of_conduct = True
            except:
                pass
                
            try:
                repo.get_contents(".gitignore")
                has_gitignore = True
            except:
                pass
                
            try:
                workflows = repo.get_contents(".github/workflows")
                has_ci = len(workflows) > 0 if isinstance(workflows, list) else False
            except:
                pass
            
            # Collect suggestions
            suggestions = []
            
            if not has_readme:
                suggestions.append({
                    "type": "missing_file",
                    "file": "README.md",
                    "severity": "high",
                    "message": "Repository is missing a README.md file"
                })
                
            if not has_license:
                suggestions.append({
                    "type": "missing_file",
                    "file": "LICENSE",
                    "severity": "medium",
                    "message": "Repository is missing a LICENSE file"
                })
                
            if not has_contributing and (issues_count > 0 or forks_count > 0):
                suggestions.append({
                    "type": "missing_file",
                    "file": "CONTRIBUTING.md",
                    "severity": "low",
                    "message": "Repository with active issues or forks should have a CONTRIBUTING.md file"
                })
                
            if not has_code_of_conduct and (issues_count > 0 or forks_count > 5):
                suggestions.append({
                    "type": "missing_file",
                    "file": "CODE_OF_CONDUCT.md",
                    "severity": "low",
                    "message": "Popular repositories should have a CODE_OF_CONDUCT.md file"
                })
                
            if not has_gitignore:
                suggestions.append({
                    "type": "missing_file",
                    "file": ".gitignore",
                    "severity": "medium",
                    "message": "Repository is missing a .gitignore file"
                })
                
            if not has_ci:
                suggestions.append({
                    "type": "missing_ci",
                    "severity": "medium",
                    "message": "Repository does not have CI/CD workflows set up"
                })
            
            # Compile health check report
            health_check = {
                "repository": repo_name,
                "metadata": {
                    "issues_count": issues_count,
                    "stars_count": stars_count,
                    "forks_count": forks_count,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
                },
                "essential_files": {
                    "readme": has_readme,
                    "license": has_license,
                    "contributing": has_contributing,
                    "code_of_conduct": has_code_of_conduct,
                    "gitignore": has_gitignore,
                    "ci_workflows": has_ci
                },
                "suggestions": suggestions,
                "health_score": self._calculate_health_score(
                    has_readme, has_license, has_contributing, 
                    has_code_of_conduct, has_gitignore, has_ci
                )
            }
            
            return health_check
            
        except Exception as e:
            logger.error(f"Error performing health check on {repo_name}: {str(e)}")
            raise
    
    def _calculate_health_score(self, has_readme: bool, has_license: bool, 
                              has_contributing: bool, has_code_of_conduct: bool, 
                              has_gitignore: bool, has_ci: bool) -> int:
        """Calculate a health score for the repository from 0-100."""
        score = 0
        
        # Essential files
        if has_readme:
            score += 30  # README is the most important
        if has_license:
            score += 20  # License is very important
        if has_gitignore:
            score += 15  # .gitignore is important
        if has_ci:
            score += 15  # CI is important
        if has_contributing:
            score += 10  # Contributing guidelines are good to have
        if has_code_of_conduct:
            score += 10  # Code of conduct is good to have
            
        return score

# Define a convenience function to get GitHub integration instance
def get_github_integration(token: Optional[str] = None, app_id: Optional[int] = None, 
                          private_key_path: Optional[str] = None, 
                          installation_id: Optional[int] = None) -> GitHubIntegration:
    """
    Get a configured GitHub integration instance.
    
    This function will try to use the provided parameters or fall back to environment variables.
    
    Args:
        token: GitHub personal access token
        app_id: GitHub App ID
        private_key_path: Path to the GitHub App's private key
        installation_id: GitHub App installation ID
        
    Returns:
        Configured GitHubIntegration instance
    """
    return GitHubIntegration(token, app_id, private_key_path, installation_id) 