#!/usr/bin/env python3
"""
VOTai Dashboard Module

A web-based dashboard for monitoring and managing the VOTai agent ecosystem.
Provides real-time status updates, agent management, and GitHub integration monitoring.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import traceback
import threading

import flask
from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.serving import run_simple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.expanduser('~/.vot1/logs/dashboard.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Try to import VOTai components, with graceful fallbacks
try:
    from ..local_mcp.agent_memory_manager import AgentMemoryManager
    MEMORY_MANAGER_AVAILABLE = True
except ImportError:
    logger.warning("AgentMemoryManager not available, some features will be disabled")
    MEMORY_MANAGER_AVAILABLE = False

try:
    from ..local_mcp.github_integration import GitHubIntegration
    GITHUB_INTEGRATION_AVAILABLE = True
except ImportError:
    logger.warning("GitHubIntegration not available, GitHub features will be disabled")
    GITHUB_INTEGRATION_AVAILABLE = False

try:
    from ..local_mcp.bridge import LocalMCPBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    logger.warning("LocalMCPBridge not available, MCP features will be disabled")
    BRIDGE_AVAILABLE = False

class VOTaiDashboard:
    """
    Main dashboard class for the VOTai ecosystem.
    
    Manages the web interface, real-time monitoring, and integration with
    various VOTai components like agents, memory system, and GitHub integration.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5000,
        debug: bool = False,
        enable_memory: bool = True,
        enable_github: bool = True,
        enable_bridge: bool = True,
        auto_refresh: bool = True,
        refresh_interval: int = 30  # seconds
    ):
        """
        Initialize the VOTai Dashboard.
        
        Args:
            host: Hostname to run the dashboard on
            port: Port to run the dashboard on
            debug: Whether to enable debug mode
            enable_memory: Whether to enable memory system integration
            enable_github: Whether to enable GitHub integration
            enable_bridge: Whether to enable MCP Bridge integration
            auto_refresh: Whether to enable automatic refresh of dashboard data
            refresh_interval: Refresh interval in seconds
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        
        # Initialize Flask app
        self.app = Flask(
            __name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static")
        )
        
        # Initialize components
        self.memory_manager = None
        self.github_integration = None
        self.bridge = None
        
        # Initialize bridge first since others depend on it
        if enable_bridge and BRIDGE_AVAILABLE:
            try:
                self.bridge = LocalMCPBridge()
                logger.info("MCP Bridge initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MCP Bridge: {e}")
                traceback.print_exc()
        
        if enable_memory and MEMORY_MANAGER_AVAILABLE:
            try:
                self.memory_manager = AgentMemoryManager()
                logger.info("Memory manager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize memory manager: {e}")
                traceback.print_exc()
        
        # Initialize GitHub integration after bridge
        if enable_github and GITHUB_INTEGRATION_AVAILABLE and self.bridge:
            try:
                self.github_integration = GitHubIntegration(mcp_bridge=self.bridge)
                logger.info("GitHub integration initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub integration: {e}")
                traceback.print_exc()
        
        # Dashboard state
        self.last_refresh = datetime.now()
        self.system_status = {
            "memory": None,
            "github": None,
            "bridge": None,
            "agents": [],
            "last_update": datetime.now().isoformat()
        }
        
        # Background refresh thread
        self.refresh_thread = None
        if self.auto_refresh:
            self.start_auto_refresh()
        
        # Initialize routes
        self._setup_routes()
    
    def start_auto_refresh(self):
        """Start the background refresh thread."""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop, daemon=True)
            self.refresh_thread.start()
            logger.info(f"Auto-refresh started with interval {self.refresh_interval} seconds")
    
    def _auto_refresh_loop(self):
        """Background thread to periodically refresh dashboard data."""
        while True:
            try:
                self.refresh_dashboard()
                time.sleep(self.refresh_interval)
            except Exception as e:
                logger.error(f"Error in auto-refresh: {e}")
                traceback.print_exc()
                time.sleep(self.refresh_interval * 2)  # Backoff on errors
    
    def refresh_dashboard(self):
        """Refresh all dashboard data."""
        logger.info("Refreshing dashboard data")
        self.last_refresh = datetime.now()
        
        # Update Bridge status
        if self.bridge:
            try:
                # Use get_performance_metrics() instead of health_check
                bridge_metrics = self.bridge.get_performance_metrics()
                self.system_status["bridge"] = {
                    "status": "active",
                    "last_updated": datetime.now().isoformat(),
                    "metrics": bridge_metrics
                }
                logger.info(f"Bridge status updated: active")
            except Exception as e:
                logger.error(f"Failed to update Bridge status: {e}")
                self.system_status["bridge"] = {
                    "status": "error",
                    "error": str(e),
                    "last_updated": datetime.now().isoformat()
                }
        
        # Update GitHub status
        if self.github_integration:
            try:
                github_status = self.github_integration.get_status()
                self.system_status["github"] = {
                    "status": "active" if github_status.get("active", False) else "inactive",
                    "connection_url": github_status.get("connection_url", ""),
                    "last_updated": datetime.now().isoformat(),
                    "details": github_status
                }
                logger.info(f"GitHub status updated: {self.system_status['github']['status']}")
                
                # Check GitHub repository sync status
                if github_status.get("active", False):
                    try:
                        repo_info = self.github_integration.get_repository("kabrony", "vot1")
                        self.system_status["github"]["repo_status"] = {
                            "name": repo_info.get("name", ""),
                            "description": repo_info.get("description", ""),
                            "updated_at": repo_info.get("updated_at", ""),
                            "open_issues_count": repo_info.get("open_issues_count", 0),
                            "sync_status": "synced" if repo_info else "not_synced"
                        }
                        logger.info(f"GitHub repository status updated: {self.system_status['github']['repo_status']['sync_status']}")
                    except Exception as e:
                        logger.error(f"Failed to get repository status: {e}")
                        self.system_status["github"]["repo_status"] = {
                            "sync_status": "error",
                            "error": str(e)
                        }
            except Exception as e:
                logger.error(f"Failed to update GitHub status: {e}")
                self.system_status["github"] = {
                    "status": "error",
                    "error": str(e),
                    "last_updated": datetime.now().isoformat()
                }
        
        # Update Memory status
        if self.memory_manager:
            try:
                # Get memory statistics
                activity_count = len(self.memory_manager.list_files("agent_activity")) if hasattr(self.memory_manager, "list_files") else 0
                tasks_count = len(self.memory_manager.list_files("agent_tasks")) if hasattr(self.memory_manager, "list_files") else 0
                knowledge_count = len(self.memory_manager.list_files("agent_knowledge")) if hasattr(self.memory_manager, "list_files") else 0
                
                self.system_status["memory"] = {
                    "status": "active",
                    "activity_count": activity_count,
                    "tasks_count": tasks_count,
                    "knowledge_count": knowledge_count,
                    "last_updated": datetime.now().isoformat()
                }
                logger.info(f"Memory status updated: active with {activity_count} activities")
            except Exception as e:
                logger.error(f"Failed to update Memory status: {e}")
                self.system_status["memory"] = {
                    "status": "error",
                    "error": str(e),
                    "last_updated": datetime.now().isoformat()
                }
        
        # Update last update timestamp
        self.system_status["last_update"] = datetime.now().isoformat()
    
    def _setup_routes(self):
        """Set up Flask routes for the dashboard."""
        @self.app.route('/')
        def index():
            """Home page."""
            return render_template('index.html', 
                                memory_status=self.system_status.get("memory", {}),
                                github_status=self.system_status.get("github", {}),
                                bridge_status=self.system_status.get("bridge", {}),
                                agents=self.system_status.get("agents", []),
                                last_refresh=self.last_refresh.strftime('%Y-%m-%d %H:%M:%S'))
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for dashboard status."""
            return jsonify(self.system_status)
        
        @self.app.route('/api/refresh', methods=['POST'])
        def api_refresh():
            """API endpoint to refresh dashboard data."""
            self.refresh_dashboard()
            return jsonify({"success": True})
        
        @self.app.route('/github')
        def github_page():
            """GitHub integration page."""
            return render_template('github.html', 
                                github_status=self.system_status.get("github", {}),
                                auto_sync_enabled=getattr(self, 'github_auto_sync', False),
                                auto_sync_interval=getattr(self, 'github_auto_sync_interval', 3600),
                                auto_sync_next=getattr(self, 'github_next_sync', 'Not scheduled'),
                                last_refresh=self.last_refresh.strftime('%Y-%m-%d %H:%M:%S'))
        
        @self.app.route('/api/github/initialize', methods=['POST'])
        def initialize_github_connection():
            """API endpoint to initialize GitHub connection."""
            if not self.github_integration:
                return jsonify({
                    "success": False, 
                    "error": "GitHub integration not available"
                })
                
            try:
                # Get status using the correct method
                status = self.github_integration.get_status()
                
                # Update system status
                self.refresh_dashboard()
                
                return jsonify({
                    "success": True,
                    "message": "GitHub connection checked",
                    "status": status
                })
            except Exception as e:
                logger.error(f"Failed to initialize GitHub connection: {e}")
                traceback.print_exc()
                return jsonify({
                    "success": False,
                    "error": str(e)
                })
        
        @self.app.route('/api/github/actions', methods=['POST'])
        def github_actions():
            """API endpoint for GitHub actions."""
            if not self.github_integration:
                return jsonify({"success": False, "error": "GitHub integration not available"}), 503
            
            action = request.json.get('action')
            params = request.json.get('params', {})
            
            result = {"success": False, "error": "Unknown action"}
            
            if action == "sync_repo":
                try:
                    owner = params.get('owner', 'kabrony')
                    repo = params.get('repo', 'vot1')
                    repo_info = self.github_integration.get_repository(owner, repo)
                    result = {
                        "success": True,
                        "data": repo_info
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": str(e)
                    }
            elif action == "create_issue":
                try:
                    owner = params.get('owner', 'kabrony')
                    repo = params.get('repo', 'vot1')
                    title = params.get('title', 'Issue created from VOTai Dashboard')
                    body = params.get('body', 'This issue was automatically created by the VOTai Dashboard')
                    
                    # Check if create_issue method exists in GitHubIntegration
                    if hasattr(self.github_integration, 'create_issue'):
                        issue = self.github_integration.create_issue(owner, repo, title, body)
                        result = {
                            "success": True,
                            "data": issue
                        }
                    else:
                        # Fallback to MCP function
                        bridge_params = {
                            "params": {
                                "owner": owner,
                                "repo": repo,
                                "title": title,
                                "body": body
                            }
                        }
                        response = self.bridge.call_function("mcp_MCP_GITHUB_CREATE_AN_ISSUE", bridge_params)
                        result = {
                            "success": response.get("status_code", 0) == 200,
                            "data": response.get("data", {})
                        }
                except Exception as e:
                    result = {
                        "success": False,
                        "error": str(e)
                    }
            
            return jsonify(result)
        
        @self.app.route('/memory')
        def memory_page():
            """Render the Memory System page."""
            memory_status = self.system_status.get("memory", {})
            return render_template('memory.html', 
                                  memory_status=memory_status,
                                  last_refresh=self.last_refresh.strftime("%Y-%m-%d %H:%M:%S"))
        
        @self.app.route('/agents')
        def agents_page():
            """Render the Agents page."""
            agents = self.system_status.get("agents", [])
            return render_template('agents.html', 
                                  agents=agents,
                                  last_refresh=self.last_refresh.strftime("%Y-%m-%d %H:%M:%S"))
        
        @self.app.route('/api/memory/search', methods=['GET'])
        def memory_search():
            """API endpoint for searching memory."""
            if not self.memory_manager:
                return jsonify({"success": False, "error": "Memory manager not available"}), 503
            
            query = request.args.get('query', '')
            category = request.args.get('category', '')
            limit = int(request.args.get('limit', 10))
            
            results = []
            
            try:
                if category == "agent_knowledge":
                    knowledge_results = self.memory_manager.search_agent_knowledge(query)
                    results = knowledge_results[:limit]
                elif category:
                    # For other categories, do a simple key search for now
                    keys = self.memory_manager.list_keys(category)
                    matching_keys = [k for k in keys if query.lower() in k.lower()][:limit]
                    
                    for key in matching_keys:
                        item = self.memory_manager.load(category, key)
                        if item:
                            results.append({"key": key, "data": item})
                else:
                    # Search across all categories
                    for search_category in [
                        self.memory_manager.AGENT_ACTIVITY_CATEGORY,
                        self.memory_manager.AGENT_TASKS_CATEGORY,
                        self.memory_manager.AGENT_KNOWLEDGE_CATEGORY
                    ]:
                        keys = self.memory_manager.list_keys(search_category)
                        matching_keys = [k for k in keys if query.lower() in k.lower()][:limit//3]  # Divide limit among categories
                        
                        for key in matching_keys:
                            item = self.memory_manager.load(search_category, key)
                            if item:
                                results.append({
                                    "key": key, 
                                    "category": search_category,
                                    "data": item
                                })
                
                return jsonify({"success": True, "results": results})
            except Exception as e:
                logger.error(f"Error searching memory: {e}")
                traceback.print_exc()
                return jsonify({"success": False, "error": str(e)}), 500
        
        @self.app.route('/api/github/sync_repository', methods=['POST'])
        def github_sync_repository():
            """API endpoint for syncing a GitHub repository."""
            if not self.github_integration:
                return jsonify({"success": False, "error": "GitHub integration not available"}), 503
            
            data = request.json or {}
            owner = data.get('owner', 'kabrony')
            repo = data.get('repo', 'vot1')
            
            result = self.sync_github_repository(owner, repo)
            return jsonify(result)
        
        @self.app.route('/api/github/status', methods=['GET'])
        def github_status_api():
            """API endpoint for getting detailed GitHub status."""
            status = self.get_github_status()
            return jsonify(status)
        
        @self.app.route('/api/github/auto_sync', methods=['POST'])
        def github_auto_sync():
            """API endpoint for enabling auto-sync with GitHub."""
            if not self.github_integration:
                return jsonify({"success": False, "error": "GitHub integration not available"}), 503
            
            data = request.json or {}
            owner = data.get('owner', 'kabrony')
            repo = data.get('repo', 'vot1')
            enabled = data.get('enabled', True)
            interval = data.get('interval', 3600)  # Default to hourly
            
            # Store auto-sync configuration
            self.auto_sync_config = {
                "enabled": enabled,
                "owner": owner,
                "repo": repo,
                "interval": interval,
                "last_sync": None,
                "next_sync": datetime.now() + timedelta(seconds=interval) if enabled else None
            }
            
            # Start background thread if enabled and not already running
            if enabled and (not hasattr(self, 'auto_sync_thread') or not self.auto_sync_thread.is_alive()):
                self.auto_sync_thread = threading.Thread(target=self._auto_sync_github, daemon=True)
                self.auto_sync_thread.start()
                logger.info(f"Auto-sync started for {owner}/{repo} with interval {interval} seconds")
            
            return jsonify({"success": True, "config": self.auto_sync_config})
        
        @self.app.route('/api/github/create_issue', methods=['POST'])
        def github_create_issue_api():
            """API endpoint for creating a GitHub issue."""
            if not self.github_integration:
                return jsonify({"success": False, "error": "GitHub integration not available"}), 503
            
            data = request.json or {}
            owner = data.get('owner', 'kabrony')
            repo = data.get('repo', 'vot1')
            title = data.get('title')
            body = data.get('body')
            labels = data.get('labels', [])
            
            if not title or not body:
                return jsonify({"success": False, "error": "Title and body are required"}), 400
            
            result = self.create_github_issue(owner, repo, title, body, labels)
            return jsonify(result)
    
    def sync_github_repository(self, owner: str = "kabrony", repo: str = "vot1"):
        """
        Sync a GitHub repository.
        
        This pulls the latest information from the GitHub repository and caches it.
        
        Args:
            owner: The repository owner
            repo: The repository name
            
        Returns:
            Dict with sync status information
        """
        if not self.github_integration:
            return {
                "success": False,
                "error": "GitHub integration not available"
            }
        
        try:
            # Get repository info with force_refresh to ensure we get the latest data
            repo_info = self.github_integration.get_repository(owner, repo, force_refresh=True)
            
            # Get commits with force_refresh
            commits = self.github_integration.get_commits(owner, repo, force_refresh=True)
            
            # Determine commits count safely
            commits_count = 0
            if isinstance(commits, dict) and "data" in commits:
                commits_data = commits.get("data", [])
                if isinstance(commits_data, list):
                    commits_count = len(commits_data)
            elif isinstance(commits, list):
                commits_count = len(commits)
            
            # Return success with repository info
            return {
                "success": True,
                "repository": {
                    "name": repo_info.get("name", ""),
                    "description": repo_info.get("description", ""),
                    "stars": repo_info.get("stargazers_count", 0),
                    "forks": repo_info.get("forks_count", 0),
                    "open_issues": repo_info.get("open_issues_count", 0),
                    "updated_at": repo_info.get("updated_at", "")
                },
                "commits_count": commits_count,
                "synced_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing GitHub repository {owner}/{repo}: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_github_issue(self, owner: str, repo: str, title: str, body: str, labels: List[str] = None):
        """
        Create a new issue in a GitHub repository.
        
        Args:
            owner: The repository owner
            repo: The repository name
            title: The issue title
            body: The issue body
            labels: Optional list of labels to apply
            
        Returns:
            Dict with issue creation status
        """
        if not self.github_integration:
            return {
                "success": False,
                "error": "GitHub integration not available"
            }
        
        try:
            # Create the issue using the GitHub integration
            result = self.github_integration.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                labels=labels
            )
            
            if result.get("success", False):
                issue_data = result.get("data", {})
                return {
                    "success": True,
                    "issue": {
                        "number": issue_data.get("number", 0),
                        "html_url": issue_data.get("html_url", ""),
                        "title": issue_data.get("title", ""),
                        "created_at": issue_data.get("created_at", "")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
            
        except Exception as e:
            logger.error(f"Error creating GitHub issue in {owner}/{repo}: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_github_status(self):
        """Get detailed GitHub integration status.
        
        Returns:
            Dictionary with GitHub status
        """
        if not self.github_integration:
            return {
                "status": "unavailable",
                "error": "GitHub integration not available",
                "last_updated": datetime.now().isoformat()
            }
        
        try:
            # Get basic status
            github_status = self.github_integration.get_status()
            status = {
                "status": "active" if github_status.get("active", False) else "inactive",
                "connection_url": github_status.get("connection_url", ""),
                "details": github_status,
                "repo_kabrony_vot1": {},
                "last_updated": datetime.now().isoformat()
            }
            
            # Try to get kabrony/vot1 repo info
            if github_status.get("active", False):
                try:
                    repo_info = self.sync_github_repository("kabrony", "vot1")
                    status["repo_kabrony_vot1"] = repo_info
                except Exception as e:
                    logger.error(f"Failed to get kabrony/vot1 repository info: {e}")
                    status["repo_kabrony_vot1"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Add info about available GitHub methods
            try:
                methods = []
                for attr in dir(self.github_integration):
                    if not attr.startswith('_') and callable(getattr(self.github_integration, attr)):
                        methods.append(attr)
                
                status["available_methods"] = methods
            except Exception:
                pass
            
            return status
        except Exception as e:
            logger.error(f"Failed to get GitHub status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    def _auto_sync_github(self):
        """Background thread for automatic GitHub synchronization."""
        while getattr(self, 'auto_sync_config', {}).get('enabled', False):
            try:
                now = datetime.now()
                next_sync = self.auto_sync_config.get('next_sync')
                
                if next_sync and now >= next_sync:
                    # Time to sync
                    owner = self.auto_sync_config.get('owner', 'kabrony')
                    repo = self.auto_sync_config.get('repo', 'vot1')
                    logger.info(f"Auto-syncing GitHub repository {owner}/{repo}")
                    
                    result = self.sync_github_repository(owner, repo)
                    interval = self.auto_sync_config.get('interval', 3600)
                    
                    # Update sync status
                    self.auto_sync_config['last_sync'] = now.isoformat()
                    self.auto_sync_config['next_sync'] = now + timedelta(seconds=interval)
                    self.auto_sync_config['last_result'] = result
                    
                    logger.info(f"Auto-sync completed for {owner}/{repo}, next sync at {self.auto_sync_config['next_sync']}")
                
                # Sleep for a minute or half the interval, whichever is smaller
                sleep_time = min(60, self.auto_sync_config.get('interval', 3600) / 2)
                time.sleep(sleep_time)
            except Exception as e:
                logger.error(f"Error in auto-sync thread: {e}")
                traceback.print_exc()
                time.sleep(300)  # Sleep for 5 minutes on error
    
    def run(self):
        """Run the dashboard server."""
        logger.info(f"Starting VOTai Dashboard on {self.host}:{self.port}")
        run_simple(self.host, self.port, self.app, use_reloader=self.debug, use_debugger=self.debug)

if __name__ == "__main__":
    dashboard = VOTaiDashboard()
    dashboard.run() 