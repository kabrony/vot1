#!/usr/bin/env python3
"""
VOTai Mock GitHub MCP Server

This module provides a simple Flask server that mocks the GitHub MCP API,
allowing for local testing of the VOTai GitHub integration without requiring
actual GitHub API access.

Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
"""

import os
import json
import logging
import argparse
import time
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'mock_github_server.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class MockGitHubServer:
    """
    Flask server that mocks the GitHub MCP API for local testing.
    
    Part of the VOTai ecosystem - A New Dawn of a Holistic Paradigm.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        debug: bool = False
    ):
        """
        Initialize the mock GitHub server.
        
        Args:
            host: The host to run the server on
            port: The port to run the server on
            debug: Whether to run the server in debug mode
        """
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        self.host = host
        self.port = port
        self.debug = debug
        
        # Initialize tasks storage
        self.tasks = {}
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize routes
        self._init_routes()
        
        # Initialize mock data
        self._init_mock_data()
        
        logger.info("VOTai Mock GitHub MCP Server initialized successfully")
    
    def _init_routes(self):
        """Register routes with the Flask app."""
        # Root route for health check
        self.app.route('/')(self.health_check)
        
        # GitHub API routes
        self.app.route('/v1')(self.api_root)
        self.app.route('/repos/<owner>/<repo>')(self.get_repository)
        self.app.route('/repos/<owner>/<repo>/commits')(self.get_commits)
        self.app.route('/repos/<owner>/<repo>/pulls/<int:pr_number>')(self.get_pull_request)
        
        # MCP function routes
        self.app.route('/v1/github/check_connection', methods=['POST'])(self.check_connection)
        self.app.route('/v1/github/get_required_parameters', methods=['POST'])(self.get_required_parameters)
        self.app.route('/v1/github/initiate_connection', methods=['POST'])(self.initiate_connection)
        
        # Add an alias route for initiate_connection to match the test script
        self.app.route('/v1/mcp/github/initiate_connection', methods=['POST'])(self.initiate_connection)
        
        # Mock Routes for API testing
        self.app.route('/api/agents', methods=['GET'])(self.get_agents)
        self.app.route('/api/agents/DevelopmentAgent/tasks', methods=['POST'])(self.handle_agent_task)
        self.app.route('/api/agents/task/<task_id>', methods=['GET'])(self.get_task_result)
    
    def _init_mock_data(self):
        """Initialize mock data for the server."""
        self.repositories = {
            "microsoft/vscode": {
                "id": 41881900,
                "node_id": "MDEwOlJlcG9zaXRvcnk0MTg4MTkwMA==",
                "name": "vscode",
                "full_name": "microsoft/vscode",
                "private": False,
                "owner": {
                    "login": "microsoft",
                    "id": 6154722,
                    "type": "Organization"
                },
                "html_url": "https://github.com/microsoft/vscode",
                "description": "Visual Studio Code",
                "fork": False,
                "url": "https://api.github.com/repos/microsoft/vscode",
                "created_at": "2015-09-03T20:23:38Z",
                "updated_at": "2025-03-14T06:00:00Z",
                "pushed_at": "2025-03-14T06:30:00Z",
                "homepage": "https://code.visualstudio.com",
                "size": 500000,
                "stargazers_count": 150000,
                "watchers_count": 150000,
                "language": "TypeScript",
                "forks_count": 25000,
                "open_issues_count": 5000,
                "license": {
                    "key": "mit",
                    "name": "MIT License",
                    "url": "https://api.github.com/licenses/mit"
                },
                "topics": [
                    "editor",
                    "typescript",
                    "ide",
                    "vscode",
                    "visual-studio-code"
                ]
            }
        }
        
        self.pull_requests = {
            "microsoft/vscode": {
                "180000": {
                    "id": 1234567890,
                    "number": 180000,
                    "state": "open",
                    "title": "Add new feature for VOTai integration",
                    "user": {
                        "login": "vot-contributor",
                        "id": 12345678
                    },
                    "body": "This PR adds support for VOTai integration with Visual Studio Code.",
                    "created_at": "2025-03-10T12:00:00Z",
                    "updated_at": "2025-03-14T06:00:00Z",
                    "head": {
                        "ref": "feature/votai-integration",
                        "sha": "abcdef1234567890"
                    },
                    "base": {
                        "ref": "main",
                        "sha": "0987654321fedcba"
                    },
                    "merged": False,
                    "mergeable": True,
                    "comments": 5,
                    "commits": 3,
                    "additions": 500,
                    "deletions": 200,
                    "changed_files": 10
                }
            }
        }
        
        self.commits = {
            "microsoft/vscode": [
                {
                    "sha": "abcdef1234567890",
                    "commit": {
                        "author": {
                            "name": "VOT Contributor",
                            "email": "contributor@vot.ai",
                            "date": "2025-03-14T05:00:00Z"
                        },
                        "message": "Add VOTai integration support"
                    },
                    "author": {
                        "login": "vot-contributor",
                        "id": 12345678
                    }
                },
                {
                    "sha": "bcdef1234567890a",
                    "commit": {
                        "author": {
                            "name": "VOT Contributor",
                            "email": "contributor@vot.ai",
                            "date": "2025-03-13T05:00:00Z"
                        },
                        "message": "Fix bugs in VOTai integration"
                    },
                    "author": {
                        "login": "vot-contributor",
                        "id": 12345678
                    }
                },
                {
                    "sha": "cdef1234567890ab",
                    "commit": {
                        "author": {
                            "name": "VOT Contributor",
                            "email": "contributor@vot.ai",
                            "date": "2025-03-12T05:00:00Z"
                        },
                        "message": "Initial VOTai integration"
                    },
                    "author": {
                        "login": "vot-contributor",
                        "id": 12345678
                    }
                }
            ]
        }
    
    def health_check(self):
        """Root route for health check."""
        try:
            return jsonify({
                "service": "Mock GitHub MCP Server",
                "status": "healthy",
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return jsonify({
                "service": "Mock GitHub MCP Server",
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            }), 500
    
    def api_root(self):
        """GitHub API root endpoint."""
        return jsonify({
            "current_user_url": "http://localhost:8000/user",
            "repository_url": "http://localhost:8000/repos/{owner}/{repo}",
            "repository_search_url": "http://localhost:8000/search/repositories?q={query}",
            "issue_search_url": "http://localhost:8000/search/issues?q={query}",
            "emojis_url": "http://localhost:8000/emojis",
            "events_url": "http://localhost:8000/events"
        })
    
    def get_repository(self, owner, repo):
        """Get a repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.repositories:
            return jsonify(self.repositories[repo_key])
        else:
            return jsonify({"message": "Repository not found"}), 404
    
    def get_commits(self, owner, repo):
        """Get commits for a repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.commits:
            # Handle pagination
            per_page = int(request.args.get('per_page', 30))
            page = int(request.args.get('page', 1))
            
            start = (page - 1) * per_page
            end = start + per_page
            
            return jsonify(self.commits[repo_key][start:end])
        else:
            return jsonify({"message": "Repository not found"}), 404
    
    def get_pull_request(self, owner, repo, pr_number):
        """Get a pull request."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.pull_requests and str(pr_number) in self.pull_requests[repo_key]:
            return jsonify(self.pull_requests[repo_key][str(pr_number)])
        else:
            return jsonify({"message": "Pull request not found"}), 404
    
    def check_connection(self):
        """Check if a connection to GitHub is active."""
        return jsonify({
            "active_connection": True,
            "connection_id": "mock-connection-id",
            "expires_at": time.time() + 3600
        })
    
    def get_required_parameters(self):
        """Get required parameters for GitHub connection."""
        return jsonify({
            "parameters": {
                "api_key": {
                    "type": "string",
                    "description": "GitHub Personal Access Token",
                    "required": True
                }
            }
        })
    
    def initiate_connection(self):
        """Initiate a connection to GitHub."""
        data = request.json or {}
        params = data.get('params', {})
        
        # Improved response format to match expected MCP response
        if 'parameters' in params and params.get('tool') == 'GitHub':
            return jsonify({
                "successful": True,
                "connection_id": "mock-connection-id",
                "expires_at": time.time() + 3600,
                "message": "GitHub connection established successfully"
            })
        else:
            return jsonify({
                "successful": False,
                "error": "Invalid parameters for GitHub connection",
                "status_code": 400
            })
    
    def get_agents(self):
        """Get list of available agents."""
        return jsonify({
            "agents": [
                {
                    "id": "dev-agent-id",
                    "name": "DevelopmentAgent",
                    "capabilities": ["github", "code_analysis"]
                }
            ]
        })
    
    def handle_agent_task(self):
        """Handle agent task submission."""
        data = request.json or {}
        task_type = data.get('type')
        task_id = data.get('task_id', 'mock-task-id')
        
        if task_type == 'analyze_repository':
            # Store task for polling
            self.tasks[task_id] = {
                "status": "completed",
                "result": {
                    "repository": data.get('repo'),
                    "analysis": {
                        "structure": {
                            "file_count": 1000,
                            "directories": 50,
                            "main_languages": ["TypeScript", "JavaScript", "CSS"]
                        },
                        "dependencies": {
                            "direct": 20,
                            "dev": 15,
                            "outdated": 5
                        },
                        "quality": {
                            "code_quality_score": 85,
                            "test_coverage": 72,
                            "issues": 10
                        }
                    }
                }
            }
        elif task_type == 'get_metrics':
            # Store metrics task
            self.tasks[task_id] = {
                "status": "completed",
                "result": {
                    "api_calls": 150,
                    "cache_hits": 75,
                    "cache_misses": 25,
                    "average_response_time": 0.32
                }
            }
        
        return jsonify({
            "task_id": task_id,
            "status": "submitted"
        })
    
    def get_task_result(self, task_id):
        """Get task result by ID."""
        task = self.tasks.get(task_id)
        if task:
            return jsonify(task)
        else:
            return jsonify({"status": "not_found"}), 404
    
    def run(self):
        """Run the server."""
        logger.info(f"Starting Mock GitHub MCP Server on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=self.debug)


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Run the Mock GitHub MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Initialize and run server
        server = MockGitHubServer(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    
    return 0


if __name__ == "__main__":
    exit(main()) 