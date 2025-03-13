"""
GitHub Ecosystem Analysis API for VOT1 Dashboard

This module provides API endpoints for GitHub repository analysis using the VOT1 system with MCP hybrid automation.
"""

from flask import Blueprint, request, jsonify, current_app
from flask.views import MethodView
import asyncio
import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
import time

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scripts.github_ecosystem_analyzer import GitHubEcosystemAnalyzer
from scripts.github_update_automation import GitHubUpdateAutomation

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
github_ecosystem_bp = Blueprint('github_ecosystem', __name__)

class GitHubEcosystemAPI(MethodView):
    """API for GitHub Ecosystem Analysis and Automation"""
    
    def __init__(self):
        self.analyzer = None
        self.loop = None
        self.updater = None
    
    def _initialize_analyzer(self):
        """Initialize the GitHub ecosystem analyzer if not already initialized."""
        if self.analyzer is None:
            # Get configuration from the Flask app
            memory_manager = current_app.config.get('memory_manager')
            memory_path = memory_manager.storage_dir if memory_manager else "./memory"
            
            primary_model = current_app.config.get('MCP_HYBRID_PRIMARY_MODEL', 'claude-3-7-sonnet-20240620')
            secondary_model = current_app.config.get('MCP_HYBRID_SECONDARY_MODEL', 'claude-3-5-sonnet-20240620')
            use_extended_thinking = current_app.config.get('MCP_HYBRID_USE_EXTENDED_THINKING', True)
            max_thinking_tokens = current_app.config.get('MCP_HYBRID_MAX_THINKING_TOKENS', 8000)
            
            # Initialize the analyzer
            self.analyzer = GitHubEcosystemAnalyzer(
                primary_model=primary_model,
                secondary_model=secondary_model,
                use_extended_thinking=use_extended_thinking,
                max_thinking_tokens=max_thinking_tokens,
                memory_path=memory_path
            )
            
            # Get or create event loop
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
    
    def _initialize_updater(self):
        """Initialize the GitHub update automation if not already initialized."""
        if self.updater is None:
            # First ensure analyzer is initialized
            self._initialize_analyzer()
            
            # Initialize the updater with our existing analyzer
            self.updater = GitHubUpdateAutomation(
                analyzer=self.analyzer,
                auto_approve=False  # Default to not auto-approving PRs for safety
            )
    
    def handle_request(self):
        """Handle API requests."""
        data = request.get_json() or {}
        action = data.get('action') or request.args.get('action')
        
        if not action:
            return jsonify({
                'status': 'error',
                'message': 'Action is required'
            })
        
        # Status endpoint
        if action == 'status':
            return self._handle_status()
        
        # Repository analysis
        elif action == 'analyze_repository':
            return self._handle_analyze_repository(data)
        
        # Ecosystem analysis
        elif action == 'analyze_ecosystem':
            return self._handle_analyze_ecosystem(data)
        
        # Improvement plan
        elif action == 'generate_improvement_plan':
            return self._handle_generate_improvement_plan(data)
        
        # Repository updates
        elif action == 'update_repository':
            return self._handle_update_repository(data)
        
        # Get update status
        elif action == 'get_update_status':
            return self._handle_get_update_status(data)
        
        # Memory operations
        elif action == 'search_memory':
            return self._handle_search_memory(data)
        
        # Export report
        elif action == 'export_report':
            return self._handle_export_report(data)
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown action: {action}'
            })
    
    def _handle_status(self):
        """Handle status request."""
        return jsonify({
            'status': 'success',
            'message': 'GitHub Ecosystem API is operational',
            'capabilities': [
                'Repository analysis',
                'Ecosystem analysis',
                'Improvement planning',
                'Repository updates',
                'Report generation'
            ]
        })
    
    def get(self):
        """Handle GET requests."""
        try:
            action = request.args.get('action')
            
            if action == 'status':
                return jsonify({
                    'status': 'success',
                    'message': 'GitHub Ecosystem API is operational',
                    'capabilities': [
                        'Repository analysis',
                        'Ecosystem analysis',
                        'Improvement planning',
                        'Report generation'
                    ]
                })
            
            elif action == 'repositories':
                self._initialize_analyzer()
                return jsonify({
                    'status': 'success',
                    'repositories': list(self.analyzer.analyzed_repositories)
                })
            
            elif action == 'memories':
                limit = request.args.get('limit', 10, type=int)
                memory_manager = current_app.config.get('memory_manager')
                
                if not memory_manager:
                    return jsonify({
                        'status': 'error',
                        'message': 'Memory system not available'
                    }), 500
                
                # Search for GitHub-related memories
                memories = memory_manager.search_memories(
                    query="github_analysis OR github_ecosystem OR improvement_plan",
                    limit=limit,
                    memory_types=["github_analysis", "github_ecosystem_analysis", "improvement_plan", "ecosystem_improvement_plan"]
                )
                
                return jsonify({
                    'status': 'success',
                    'memories': memories
                })
            
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Unknown action requested'
                }), 400
                
        except Exception as e:
            logger.error(f"Error in GitHub Ecosystem API GET: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def post(self):
        """Handle POST requests for GitHub repository and ecosystem analysis."""
        try:
            self._initialize_analyzer()
            data = request.json
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No data provided'
                }), 400
            
            action = data.get('action')
            
            if action == 'analyze_repository':
                owner = data.get('owner')
                repo = data.get('repo')
                deep_analysis = data.get('deep_analysis', True)
                use_composio = data.get('use_composio', False)
                
                if not owner or not repo:
                    return jsonify({
                        'status': 'error',
                        'message': 'Repository owner and name are required'
                    }), 400
                
                # Run the analysis asynchronously
                result = self.loop.run_until_complete(
                    self.analyzer.analyze_repository(
                        owner, 
                        repo, 
                        deep_analysis,
                        use_composio=use_composio
                    )
                )
                
                # Ensure the repository is added to the analyzed repositories set
                if result.get('success', False) or 'memory_id' in result:
                    repo_key = f"{owner}/{repo}"
                    self.analyzer.analyzed_repositories.add(repo_key)
                    logger.info(f"Added {repo_key} to analyzed repositories")
                
                return jsonify({
                    'status': 'success',
                    'result': result
                })
            
            elif action == 'analyze_ecosystem':
                repos = data.get('repositories', [])
                deep_analysis = data.get('deep_analysis', True)
                
                if not repos or not isinstance(repos, list):
                    return jsonify({
                        'status': 'error',
                        'message': 'List of repositories is required'
                    }), 400
                
                # Run the ecosystem analysis asynchronously
                result = self.loop.run_until_complete(
                    self.analyzer.analyze_ecosystem(repos, deep_analysis)
                )
                
                return jsonify({
                    'status': 'success',
                    'result': result
                })
            
            elif action == 'generate_plan':
                owner = data.get('owner')
                repo = data.get('repo')
                ecosystem = data.get('ecosystem', False)
                use_composio = data.get('use_composio', False)
                
                if ecosystem:
                    # Generate ecosystem-wide improvement plan
                    result = self.loop.run_until_complete(
                        self.analyzer.generate_improvement_plan(ecosystem=True)
                    )
                else:
                    # Generate repository-specific improvement plan
                    if not owner or not repo:
                        return jsonify({
                            'status': 'error',
                            'message': 'Repository owner and name are required'
                        }), 400
                    
                    # First analyze the repository with Composio if requested
                    if use_composio:
                        self.loop.run_until_complete(
                            self.analyzer.analyze_repository(
                                owner, 
                                repo, 
                                deep_analysis=True,
                                use_composio=True
                            )
                        )
                        
                    # Then generate the improvement plan
                    result = self.loop.run_until_complete(
                        self.analyzer.generate_improvement_plan(owner, repo)
                    )
                
                return jsonify({
                    'status': 'success',
                    'result': result
                })
            
            elif action == 'export_report':
                owner = data.get('owner')
                repo = data.get('repo')
                ecosystem = data.get('ecosystem', False)
                format = data.get('format', 'markdown')
                output_path = data.get('output_path')
                
                if ecosystem:
                    # Export ecosystem report
                    result = self.loop.run_until_complete(
                        self.analyzer.export_analysis_report(
                            ecosystem=True,
                            format=format,
                            output_path=output_path
                        )
                    )
                else:
                    # Export repository report
                    if not owner or not repo:
                        return jsonify({
                            'status': 'error',
                            'message': 'Repository owner and name are required'
                        }), 400
                    
                    result = self.loop.run_until_complete(
                        self.analyzer.export_analysis_report(
                            owner=owner,
                            repo=repo,
                            ecosystem=False,
                            format=format,
                            output_path=output_path
                        )
                    )
                
                return jsonify({
                    'status': 'success',
                    'result': result
                })
            
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Unknown action requested'
                }), 400
                
        except Exception as e:
            logger.error(f"Error in GitHub Ecosystem API POST: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    def _handle_analyze_repository(self, data):
        """Handle repository analysis request."""
        self._initialize_analyzer()
        owner = data.get('owner')
        repo = data.get('repo')
        deep_analysis = data.get('deep_analysis', True)
        use_composio = data.get('use_composio', False)
        
        if not owner or not repo:
            return jsonify({
                'status': 'error',
                'message': 'Repository owner and name are required'
            })
        
        # Run the analysis asynchronously
        result = self.loop.run_until_complete(
            self.analyzer.analyze_repository(
                owner, 
                repo, 
                deep_analysis,
                use_composio=use_composio
            )
        )
        
        # Ensure the repository is added to the analyzed repositories set
        if result.get('success', False) or 'memory_id' in result:
            repo_key = f"{owner}/{repo}"
            self.analyzer.analyzed_repositories.add(repo_key)
            logger.info(f"Added {repo_key} to analyzed repositories")
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    def _handle_analyze_ecosystem(self, data):
        """Handle ecosystem analysis request."""
        self._initialize_analyzer()
        repos = data.get('repositories', [])
        deep_analysis = data.get('deep_analysis', True)
        
        if not repos or not isinstance(repos, list):
            return jsonify({
                'status': 'error',
                'message': 'List of repositories is required'
            })
        
        # Run the ecosystem analysis asynchronously
        result = self.loop.run_until_complete(
            self.analyzer.analyze_ecosystem(repos, deep_analysis)
        )
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    def _handle_generate_improvement_plan(self, data):
        """Handle improvement plan generation request."""
        self._initialize_analyzer()
        owner = data.get('owner')
        repo = data.get('repo')
        ecosystem = data.get('ecosystem', False)
        use_composio = data.get('use_composio', False)
        
        if ecosystem:
            # Generate ecosystem-wide improvement plan
            result = self.loop.run_until_complete(
                self.analyzer.generate_improvement_plan(ecosystem=True)
            )
        else:
            # Generate repository-specific improvement plan
            if not owner or not repo:
                return jsonify({
                    'status': 'error',
                    'message': 'Repository owner and name are required'
                })
            
            # First analyze the repository with Composio if requested
            if use_composio:
                self.loop.run_until_complete(
                    self.analyzer.analyze_repository(
                        owner, 
                        repo, 
                        deep_analysis=True,
                        use_composio=True
                    )
                )
                
            # Then generate the improvement plan
            result = self.loop.run_until_complete(
                self.analyzer.generate_improvement_plan(owner, repo)
            )
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    def _handle_update_repository(self, data):
        """Handle repository update request."""
        # Initialize the updater
        self._initialize_updater()
        
        # Extract parameters
        owner = data.get('owner')
        repo = data.get('repo')
        deep_analysis = data.get('deep_analysis', True)
        update_areas = data.get('update_areas', ['documentation', 'workflows', 'dependencies', 'code_quality'])
        max_updates = data.get('max_updates', 3)
        auto_approve = data.get('auto_approve', False)
        
        # Validate parameters
        if not owner or not repo:
            return jsonify({
                'status': 'error',
                'message': 'Repository owner and name are required'
            })
        
        # Set auto_approve setting (but don't persist it)
        self.updater.auto_approve = auto_approve
        
        try:
            # Run the update process
            result = self.loop.run_until_complete(
                self.updater.analyze_and_update(
                    owner=owner,
                    repo=repo,
                    deep_analysis=deep_analysis,
                    update_areas=update_areas,
                    max_updates=max_updates
                )
            )
            
            # Save the update result to memory
            if self.updater.memory_manager:
                update_record = {
                    'type': 'github_update',
                    'timestamp': time.time(),
                    'repository': f"{owner}/{repo}",
                    'update_areas': update_areas,
                    'max_updates': max_updates,
                    'result': result
                }
                self.updater.memory_manager.add(update_record)
            
            return jsonify({
                'status': 'success',
                'repository': f"{owner}/{repo}",
                'updates': result.get('updates_created', []),
                'analysis_completed': result.get('analysis_completed', False),
                'plan_generated': result.get('plan_generated', False),
                'message': f"Created {len(result.get('updates_created', []))} updates for {owner}/{repo}"
            })
            
        except Exception as e:
            current_app.logger.error(f"Error updating repository: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f"Error updating repository: {str(e)}"
            })
    
    def _handle_get_update_status(self, data):
        """Handle request to get update status."""
        # Initialize the updater
        self._initialize_updater()
        
        # Extract parameters
        owner = data.get('owner')
        repo = data.get('repo')
        
        # Validate parameters
        if not owner or not repo:
            return jsonify({
                'status': 'error',
                'message': 'Repository owner and name are required'
            })
        
        try:
            # Search memory for update records
            if self.updater.memory_manager:
                memory_records = self.updater.memory_manager.search(
                    query=f"github_update {owner}/{repo}",
                    n_results=5
                )
                
                updates = []
                for record in memory_records:
                    if record.get('type') == 'github_update' and record.get('repository') == f"{owner}/{repo}":
                        updates.append({
                            'timestamp': record.get('timestamp'),
                            'update_areas': record.get('update_areas', []),
                            'updates': record.get('result', {}).get('updates_created', [])
                        })
                
                return jsonify({
                    'status': 'success',
                    'repository': f"{owner}/{repo}",
                    'update_history': updates,
                    'message': f"Found {len(updates)} update records for {owner}/{repo}"
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Memory manager not available'
                })
                
        except Exception as e:
            current_app.logger.error(f"Error getting update status: {e}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': f"Error getting update status: {str(e)}"
            })

# Register the view
github_ecosystem_bp.add_url_rule('/api/github-ecosystem', view_func=GitHubEcosystemAPI.as_view('github_ecosystem_api')) 