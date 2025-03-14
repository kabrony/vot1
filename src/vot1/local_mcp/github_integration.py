#!/usr/bin/env python3
"""
VOTai GitHub Integration Module

This module provides enhanced GitHub integration for the VOTai ecosystem,
enabling seamless interaction with GitHub repositories, issues, pull requests,
and other GitHub APIs.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import json
import logging
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .ascii_art import get_votai_ascii

logger = logging.getLogger(__name__)

# Mock GitHub server URL
MOCK_GITHUB_URL = "http://localhost:8000"

class GitHubIntegration:
    """
    Enhanced GitHub integration for the VOTai ecosystem.
    
    This class provides a unified interface for interacting with GitHub APIs,
    with improved error handling, caching, and VOTai branding.
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(self, mcp_bridge):
        """
        Initialize the GitHub integration.
        
        Args:
            mcp_bridge: The LocalMCPBridge instance for making API calls
        """
        self.bridge = mcp_bridge
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour in seconds
        
        # Display VOTai signature
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nVOTai GitHub Integration initialized")
        
        # Try to connect to the mock GitHub server
        try:
            response = requests.get(f"{MOCK_GITHUB_URL}/")
            if response.status_code == 200:
                logger.info(f"Successfully connected to mock GitHub server at {MOCK_GITHUB_URL}")
                self.mock_server_available = True
            else:
                logger.warning(f"Mock GitHub server returned status code {response.status_code}")
                self.mock_server_available = False
        except Exception as e:
            logger.warning(f"Could not connect to mock GitHub server: {e}")
            self.mock_server_available = False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed status information for the GitHub service.
        
        Returns:
            A dictionary with GitHub service status information
        """
        votai_ascii = get_votai_ascii("small")
        logger.info(f"\n{votai_ascii}\nGetting VOTai GitHub service status")
        
        # Check if GitHub service is configured
        github_url = self.bridge.get_service_url(self.bridge.SERVICE_GITHUB)
        if not github_url:
            return {
                "successful": False,
                "error": "GitHub service not configured",
                "status": {
                    "configured": False
                }
            }
        
        # Check connection to GitHub
        connection_result = self.bridge.check_connection(self.bridge.SERVICE_GITHUB)
        active_connection = connection_result.get("active_connection", False)
        
        # Get cache statistics
        github_cache_entries = {k: v for k, v in self.cache.items() if k.startswith("github_")}
        cache_stats = {
            "total_entries": len(github_cache_entries),
            "entries": [{"key": k, "expires_at": v.get("expires_at")} for k, v in github_cache_entries.items()]
        }
        
        # Build status object
        status = {
            "configured": True,
            "url": MOCK_GITHUB_URL if self.mock_server_available else github_url,
            "connection_active": active_connection or self.mock_server_available,
            "cache": cache_stats,
            "timestamp": time.time()
        }
        
        # Check if mock server is available
        if self.mock_server_available:
            status["mock_server"] = {
                "available": True,
                "url": MOCK_GITHUB_URL
            }
            status["api_available"] = True
        elif active_connection:
            # Try a simple API call to verify functionality
            try:
                # Try to connect to the GitHub API directly
                response = requests.get(github_url)
                if response.status_code == 200:
                    status["api_available"] = True
                else:
                    status["api_available"] = False
                    status["error"] = f"GitHub API returned status code {response.status_code}"
            except Exception as e:
                status["api_available"] = False
                status["error"] = str(e)
        
        return {
            "successful": True,
            "status": status
        }
    
    def get_repository(self, owner: str, repo: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get a GitHub repository's details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            force_refresh: Whether to force a refresh instead of using cache
            
        Returns:
            Repository information
        """
        cache_key = f"repo_{owner}_{repo}"
        if not force_refresh and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data.get("timestamp", 0) < self.cache_ttl:
                logger.debug(f"Using cached data for repository {owner}/{repo}")
                return {"successful": True, "data": cached_data.get("data"), "from_cache": True}
        
        try:
            # Try to get repository info from the mock GitHub server if available
            if self.mock_server_available:
                try:
                    response = requests.get(f"{MOCK_GITHUB_URL}/repos/{owner}/{repo}")
                    if response.status_code == 200:
                        data = response.json()
                        self.cache[cache_key] = {
                            "data": data,
                            "timestamp": time.time(),
                            "expires_at": time.time() + self.cache_ttl
                        }
                        return {"successful": True, "data": data, "from_cache": False}
                    else:
                        # Fall back to MCP function call
                        logger.warning(f"Mock GitHub server returned status code {response.status_code}, falling back to MCP")
                except Exception as e:
                    logger.warning(f"Error connecting to mock GitHub server: {e}, falling back to MCP")
            
            # Fall back to MCP function call
            result = self.bridge.call_function("mcp_MCP_GITHUB_GET_A_REPOSITORY", {
                "params": {
                    "owner": owner,
                    "repo": repo
                }
            })
            
            if result.get("successful", False):
                self.cache[cache_key] = {
                    "data": result.get("data", {}),
                    "timestamp": time.time(),
                    "expires_at": time.time() + self.cache_ttl
                }
                result["from_cache"] = False
            
            return result
        except Exception as e:
            logger.error(f"Error getting repository {owner}/{repo}: {str(e)}")
            return {"successful": False, "error": str(e)}
    
    def analyze_repository(self, owner: str, repo: str, depth: str = "full", focus: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            depth: Analysis depth (summary, standard, full)
            focus: Areas to focus on
            
        Returns:
            Analysis results
        """
        # Get repository info first
        repo_info = self.get_repository(owner, repo)
        if not repo_info.get("successful", False):
            return {
                "successful": False,
                "error": repo_info.get("error", "Failed to get repository information")
            }
        
        # For now, just return a simulated analysis
        return {
            "successful": True,
            "analysis": f"Repository analysis for {owner}/{repo} (depth: {depth}, focus: {focus or 'all'})\n\n"
                       f"This is a simulated analysis of the repository structure and code quality.",
            "metrics": {
                "files": 1000,
                "lines_of_code": 500000,
                "contributors": 50,
                "open_issues": 100,
                "stars": 5000
            },
            "timestamp": time.time()
        }
    
    def get_commits(self, owner: str, repo: str, per_page: int = 100, page: int = 1, 
                   since: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get commits for a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of commits per page
            page: Page number
            since: Only show commits after this timestamp (ISO 8601 format)
            force_refresh: Whether to force a refresh instead of using cache
            
        Returns:
            Commit information
        """
        cache_key = f"commits_{owner}_{repo}_{per_page}_{page}_{since}"
        if not force_refresh and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data.get("timestamp", 0) < self.cache_ttl:
                logger.debug(f"Using cached data for commits in {owner}/{repo}")
                return {"successful": True, "data": cached_data.get("data"), "from_cache": True}
        
        try:
            # Try to get commits from the mock GitHub server if available
            if self.mock_server_available:
                try:
                    url = f"{MOCK_GITHUB_URL}/repos/{owner}/{repo}/commits?per_page={per_page}&page={page}"
                    if since:
                        url += f"&since={since}"
                        
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        self.cache[cache_key] = {
                            "data": data,
                            "timestamp": time.time(),
                            "expires_at": time.time() + self.cache_ttl
                        }
                        return {"successful": True, "data": data, "from_cache": False}
                    else:
                        # Fall back to MCP function call
                        logger.warning(f"Mock GitHub server returned status code {response.status_code}, falling back to MCP")
                except Exception as e:
                    logger.warning(f"Error connecting to mock GitHub server: {e}, falling back to MCP")
            
            # Fall back to MCP function call
            params = {
                "owner": owner,
                "repo": repo,
                "per_page": per_page,
                "page": page
            }
            
            if since:
                params["since"] = since
            
            result = self.bridge.call_function("mcp_MCP_GITHUB_LIST_COMMITS", {
                "params": params
            })
            
            if result.get("successful", False):
                self.cache[cache_key] = {
                    "data": result.get("data", []),
                    "timestamp": time.time(),
                    "expires_at": time.time() + self.cache_ttl
                }
                result["from_cache"] = False
            
            return result
        except Exception as e:
            logger.error(f"Error getting commits for {owner}/{repo}: {str(e)}")
            return {"successful": False, "error": str(e)}
    
    def get_pull_request(self, owner: str, repo: str, pr_number: int, 
                       force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get a specific pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            force_refresh: Whether to force a refresh instead of using cache
            
        Returns:
            Pull request information
        """
        cache_key = f"pr_{owner}_{repo}_{pr_number}"
        if not force_refresh and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data.get("timestamp", 0) < self.cache_ttl:
                logger.debug(f"Using cached data for PR #{pr_number} in {owner}/{repo}")
                return {"successful": True, "data": cached_data.get("data"), "from_cache": True}
        
        try:
            # Try to get PR info from the mock GitHub server if available
            if self.mock_server_available:
                try:
                    response = requests.get(f"{MOCK_GITHUB_URL}/repos/{owner}/{repo}/pulls/{pr_number}")
                    if response.status_code == 200:
                        data = response.json()
                        self.cache[cache_key] = {
                            "data": data,
                            "timestamp": time.time(),
                            "expires_at": time.time() + self.cache_ttl
                        }
                        return {"successful": True, "data": data, "from_cache": False}
                    else:
                        # Fall back to MCP function call
                        logger.warning(f"Mock GitHub server returned status code {response.status_code}, falling back to MCP")
                except Exception as e:
                    logger.warning(f"Error connecting to mock GitHub server: {e}, falling back to MCP")
            
            # Fall back to MCP function call
            result = self.bridge.call_function("mcp_MCP_GITHUB_GET_A_PULL_REQUEST", {
                "params": {
                    "owner": owner,
                    "repo": repo,
                    "pull_number": pr_number
                }
            })
            
            if result.get("successful", False):
                self.cache[cache_key] = {
                    "data": result.get("data", {}),
                    "timestamp": time.time(),
                    "expires_at": time.time() + self.cache_ttl
                }
                result["from_cache"] = False
            
            return result
        except Exception as e:
            logger.error(f"Error getting PR #{pr_number} for {owner}/{repo}: {str(e)}")
            return {"successful": False, "error": str(e)}
    
    def analyze_pull_request(self, owner: str, repo: str, pr_number: int, focus: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            focus: Areas to focus on
            
        Returns:
            Analysis results
        """
        # Get PR info first
        pr_info = self.get_pull_request(owner, repo, pr_number)
        if not pr_info.get("successful", False):
            return {
                "successful": False,
                "error": pr_info.get("error", "Failed to get pull request information")
            }
        
        # For now, just return a simulated analysis
        return {
            "successful": True,
            "analysis": f"Pull request analysis for {owner}/{repo}#{pr_number} (focus: {focus or 'all'})\n\n"
                       f"This is a simulated analysis of the pull request changes and code quality.",
            "metrics": {
                "files_changed": 10,
                "additions": 500,
                "deletions": 200,
                "commits": 5
            },
            "timestamp": time.time()
        }
    
    def create_issue(self, owner: str, repo: str, title: str, body: str, 
                    labels: Optional[List[str]] = None, 
                    assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new issue in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Labels to apply to the issue
            assignees: Users to assign to the issue
            
        Returns:
            Issue creation result
        """
        try:
            # Try to create an issue using the mock GitHub server if available
            if self.mock_server_available:
                try:
                    payload = {
                        "title": title,
                        "body": body
                    }
                    
                    if labels:
                        payload["labels"] = labels
                        
                    if assignees:
                        payload["assignees"] = assignees
                        
                    response = requests.post(f"{MOCK_GITHUB_URL}/repos/{owner}/{repo}/issues", json=payload)
                    if response.status_code in (200, 201):
                        data = response.json()
                        return {"successful": True, "data": data}
                    else:
                        # Fall back to MCP function call
                        logger.warning(f"Mock GitHub server returned status code {response.status_code}, falling back to MCP")
                except Exception as e:
                    logger.warning(f"Error connecting to mock GitHub server: {e}, falling back to MCP")
            
            # Fall back to MCP function call
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
            
            result = self.bridge.call_function("mcp_MCP_GITHUB_CREATE_AN_ISSUE", {
                "params": params
            })
            
            return result
        except Exception as e:
            logger.error(f"Error creating issue in {owner}/{repo}: {str(e)}")
            return {"successful": False, "error": str(e)}
    
    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the GitHub integration cache.
        
        Returns:
            Cache clearing result
        """
        cache_count = len(self.cache)
        self.cache = {}
        
        return {
            "successful": True,
            "message": "GitHub integration cache cleared",
            "cleared_entries": cache_count
        } 