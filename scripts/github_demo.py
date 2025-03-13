#!/usr/bin/env python3
"""
GitHub Automation Demo Script

This script demonstrates the enhanced GitHub automation system, including:
- UI dashboard with real-time operation tracking
- Memory optimization
- Webhook and workflow management
- Error handling and performance monitoring

Usage:
    python github_demo.py --owner <github-owner> --repo <github-repo> --token <github-token>
"""

import os
import sys
import time
import logging
import argparse
import asyncio
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.vot1.github_composio_bridge import GitHubComposioBridge
from src.vot1.memory import MemoryManager
from src.vot1.github_ui import GitHubOperationTracker, GitHubDashboard, create_dashboard
from src.vot1.vot_mcp import VotModelControlProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "logs/github_demo.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("github_demo")

class GitHubDemo:
    """Demo for the enhanced GitHub automation system."""
    
    def __init__(
        self,
        github_token: str,
        owner: str,
        repo: str,
        use_mcp: bool = False,
        mcp_url: Optional[str] = None,
        mcp_key: Optional[str] = None
    ):
        """
        Initialize the GitHub demo.
        
        Args:
            github_token: GitHub personal access token
            owner: GitHub repository owner
            repo: GitHub repository name
            use_mcp: Whether to use MCP for API calls
            mcp_url: URL for the MCP server
            mcp_key: API key for MCP authentication
        """
        self.github_token = github_token
        self.owner = owner
        self.repo = repo
        self.use_mcp = use_mcp
        self.mcp_url = mcp_url
        self.mcp_key = mcp_key
        
        # Initialize the dashboard
        self.dashboard_storage = os.path.join(project_root, "logs/github_operations")
        self.operation_tracker = GitHubOperationTracker(storage_path=self.dashboard_storage)
        self.dashboard = GitHubDashboard(
            operation_tracker=self.operation_tracker,
            output_dir=os.path.join(project_root, "reports/github")
        )
        
        # Initialize memory manager with optimization
        self.memory_path = os.path.join(project_root, "memory")
        self.memory_manager = MemoryManager(
            memory_path=self.memory_path,
            max_conversation_history=100,
            auto_cleanup_threshold=1000,
            compression_enabled=True
        )
        
        # Create MCP if needed
        self.mcp = None
        if use_mcp and mcp_url and mcp_key:
            self.mcp = VotModelControlProtocol(
                api_url=mcp_url,
                api_key=mcp_key
            )
        
        # Initialize GitHub bridge
        self.github_bridge = GitHubComposioBridge(
            github_token=github_token,
            model_name="claude-3-7-sonnet",
            mcp_url=mcp_url,
            mcp_key=mcp_key,
            use_mcp=use_mcp,
            cache_enabled=True
        )
        
        logger.info(f"Initialized GitHub Demo for {owner}/{repo}")
        
        # Register for operation updates
        self.github_bridge.register_progress_callback("demo", self._operation_updated)
    
    def _operation_updated(self, operation: Dict[str, Any]) -> None:
        """
        Handle operation updates from the GitHub bridge.
        
        Args:
            operation: Updated operation data
        """
        # Map GitHubComposioBridge operations to our operation tracker
        op_id = operation.get("id", "unknown")
        op_type = operation.get("type", "unknown")
        
        if operation.get("status") == "started":
            self.operation_tracker.start_operation(
                operation_id=op_id,
                operation_type=op_type,
                details=operation.get("details", {})
            )
        elif operation.get("status") == "completed":
            self.operation_tracker.complete_operation(
                operation_id=op_id,
                success=operation.get("success", False),
                error=operation.get("error"),
                result=operation.get("result")
            )
        else:
            self.operation_tracker.update_operation(
                operation_id=op_id,
                progress=operation.get("progress"),
                status=operation.get("status"),
                details=operation.get("details")
            )
    
    async def run_memory_optimization_demo(self) -> None:
        """Demonstrate memory optimization capabilities."""
        operation_id = str(uuid.uuid4())
        self.operation_tracker.start_operation(
            operation_id=operation_id,
            operation_type="memory_optimization",
            details={"description": "Demonstrating memory optimization"}
        )
        
        try:
            # Add some test memories
            logger.info("Adding test memories for optimization demo")
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=20,
                status="Adding test memories"
            )
            
            for i in range(10):
                self.memory_manager.add_semantic_memory(
                    content=f"Test memory {i} for GitHub automation demo",
                    metadata={"demo": True, "index": i}
                )
                await asyncio.sleep(0.1)  # Small delay for demonstration
            
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=50,
                status="Checking memory health"
            )
            
            # Check memory health
            health = await self.memory_manager.check_memory_health()
            logger.info(f"Memory health: {health}")
            
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=70,
                status="Optimizing memory"
            )
            
            # Run memory optimization
            optimization_result = await self.memory_manager.optimize_memory()
            logger.info(f"Memory optimization result: {optimization_result}")
            
            # Test advanced search
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=90,
                status="Testing advanced search"
            )
            
            search_results = await self.memory_manager.advanced_search(
                "GitHub automation",
                filters={"demo": True},
                limit=3,
                threshold=0.5
            )
            
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=True,
                result={
                    "health": health,
                    "optimization": optimization_result,
                    "search_results": len(search_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in memory optimization demo: {e}")
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=False,
                error=str(e)
            )
    
    async def run_github_connection_demo(self) -> None:
        """Demonstrate GitHub connection and API calls."""
        operation_id = str(uuid.uuid4())
        self.operation_tracker.start_operation(
            operation_id=operation_id,
            operation_type="github_connection",
            details={
                "description": "Testing GitHub API connection",
                "owner": self.owner,
                "repo": self.repo
            }
        )
        
        try:
            # Check connection
            logger.info("Checking GitHub connection")
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=30,
                status="Checking GitHub connection"
            )
            
            connection_result = await self.github_bridge.check_connection()
            
            if connection_result.get("github_connected"):
                self.operation_tracker.update_operation(
                    operation_id=operation_id,
                    progress=60,
                    status="Getting repository information"
                )
                
                # Get repository information
                repo_info = await self.github_bridge._make_github_api_request(
                    "GET", f"repos/{self.owner}/{self.repo}"
                )
                
                # Get performance metrics
                self.operation_tracker.update_operation(
                    operation_id=operation_id,
                    progress=90,
                    status="Getting performance metrics"
                )
                
                metrics = await self.github_bridge.get_performance_metrics()
                
                self.operation_tracker.complete_operation(
                    operation_id=operation_id,
                    success=True,
                    result={
                        "connection": connection_result,
                        "repository": {
                            "name": repo_info.get("name"),
                            "description": repo_info.get("description"),
                            "stars": repo_info.get("stargazers_count"),
                            "forks": repo_info.get("forks_count")
                        },
                        "metrics": metrics
                    }
                )
            else:
                self.operation_tracker.complete_operation(
                    operation_id=operation_id,
                    success=False,
                    error=f"Failed to connect to GitHub: {connection_result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.error(f"Error in GitHub connection demo: {e}")
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=False,
                error=str(e)
            )
    
    async def run_webhook_demo(self) -> None:
        """Demonstrate webhook management capabilities."""
        operation_id = str(uuid.uuid4())
        self.operation_tracker.start_operation(
            operation_id=operation_id,
            operation_type="webhook_management",
            details={
                "description": "Demonstrating webhook management",
                "owner": self.owner,
                "repo": self.repo
            }
        )
        
        try:
            # List existing webhooks
            logger.info(f"Listing webhooks for {self.owner}/{self.repo}")
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=20,
                status="Listing existing webhooks"
            )
            
            webhooks = await self.github_bridge.list_webhooks(self.owner, self.repo)
            
            # Create a test webhook if none exists
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=40,
                status="Creating test webhook"
            )
            
            webhook_url = "https://example.com/github/webhook"
            webhook_payload = {
                "url": webhook_url,
                "content_type": "json",
                "events": ["push", "pull_request"],
                "active": True
            }
            
            create_result = await self.github_bridge.create_webhook(
                self.owner, self.repo, webhook_payload
            )
            
            # List webhooks again to see the new one
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=70,
                status="Listing updated webhooks"
            )
            
            updated_webhooks = await self.github_bridge.list_webhooks(self.owner, self.repo)
            
            # Note: We don't actually delete the webhook in this demo to avoid
            # removing anything important from the user's repository
            
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=True,
                result={
                    "initial_webhooks": len(webhooks) if isinstance(webhooks, list) else 0,
                    "create_result": "success" if not create_result.get("error") else "error",
                    "updated_webhooks": len(updated_webhooks) if isinstance(updated_webhooks, list) else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Error in webhook demo: {e}")
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=False,
                error=str(e)
            )
    
    async def run_workflow_demo(self) -> None:
        """Demonstrate workflow management capabilities."""
        operation_id = str(uuid.uuid4())
        self.operation_tracker.start_operation(
            operation_id=operation_id,
            operation_type="workflow_management",
            details={
                "description": "Demonstrating workflow management",
                "owner": self.owner,
                "repo": self.repo
            }
        )
        
        try:
            # List workflows
            logger.info(f"Listing workflows for {self.owner}/{self.repo}")
            self.operation_tracker.update_operation(
                operation_id=operation_id,
                progress=30,
                status="Listing workflows"
            )
            
            workflows = await self.github_bridge.list_workflows(self.owner, self.repo)
            
            workflow_count = 0
            if isinstance(workflows, dict) and "workflows" in workflows:
                workflow_count = len(workflows["workflows"])
            
            # Get details of the first workflow if available
            workflow_details = None
            if workflow_count > 0:
                self.operation_tracker.update_operation(
                    operation_id=operation_id,
                    progress=60,
                    status="Getting workflow details"
                )
                
                first_workflow = workflows["workflows"][0]
                workflow_id = first_workflow.get("id")
                
                if workflow_id:
                    workflow_details = await self.github_bridge.get_workflow(
                        self.owner, self.repo, str(workflow_id)
                    )
            
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=True,
                result={
                    "workflow_count": workflow_count,
                    "workflow_details": workflow_details.get("name") if workflow_details else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error in workflow demo: {e}")
            self.operation_tracker.complete_operation(
                operation_id=operation_id,
                success=False,
                error=str(e)
            )
    
    async def run_demo(self) -> str:
        """
        Run the complete GitHub automation demo.
        
        Returns:
            Path to the generated dashboard HTML file
        """
        logger.info("Starting GitHub Automation Demo")
        
        try:
            # Run all demo components
            await self.run_memory_optimization_demo()
            await asyncio.sleep(1)  # Pause for UI update
            
            await self.run_github_connection_demo()
            await asyncio.sleep(1)  # Pause for UI update
            
            await self.run_webhook_demo()
            await asyncio.sleep(1)  # Pause for UI update
            
            await self.run_workflow_demo()
            
            # Generate final dashboard
            dashboard_path = self.dashboard.generate_dashboard()
            
            # Output performance metrics
            metrics = await self.github_bridge.get_performance_metrics()
            logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
            
            return dashboard_path
            
        except Exception as e:
            logger.error(f"Error running demo: {e}")
            return ""


async def main():
    """Run the GitHub automation demo."""
    parser = argparse.ArgumentParser(description="GitHub Automation Demo")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--owner", required=True, help="GitHub repository owner")
    parser.add_argument("--repo", required=True, help="GitHub repository name")
    parser.add_argument("--use-mcp", action="store_true", help="Use MCP for API calls")
    parser.add_argument("--mcp-url", help="URL for the MCP server")
    parser.add_argument("--mcp-key", help="API key for MCP authentication")
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = GitHubDemo(
        github_token=args.token,
        owner=args.owner,
        repo=args.repo,
        use_mcp=args.use_mcp,
        mcp_url=args.mcp_url,
        mcp_key=args.mcp_key
    )
    
    # Run the demo
    dashboard_path = await demo.run_demo()
    
    if dashboard_path:
        print(f"\nDemo completed successfully!")
        print(f"Dashboard available at: {dashboard_path}")
        print(f"Open the dashboard in your browser to view the results.")
    else:
        print(f"\nDemo encountered errors. Check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main()) 