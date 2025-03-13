#!/usr/bin/env python3
"""
Configure Branch Protection Rules

This script allows you to programmatically configure branch protection rules (rulesets)
on GitHub repositories. It provides a way to protect important branches by setting up
rules that enforce requirements for pushes, pull requests, and more.
"""

import os
import sys
import argparse
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional

import aiohttp
from aiohttp import ClientSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubAPI:
    """GitHub API client for repository branch protection."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, session: Optional[ClientSession] = None):
        """Initialize with a GitHub token."""
        self.token = token
        self.session = session
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
            
    async def _make_request(self, method: str, endpoint: str, params=None, data=None, preview_headers=None) -> Dict[str, Any]:
        """Make an API request to GitHub."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            self._is_external_session = False
            
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VOT1-GitHub-Integration",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # Add preview headers if needed
        if preview_headers:
            for key, value in preview_headers.items():
                headers[key] = value
        
        try:
            async with self.session.request(
                method, url, headers=headers, params=params, 
                json=data, raise_for_status=False
            ) as response:
                if response.status in (200, 201, 204):
                    try:
                        return {"success": True, "data": await response.json()}
                    except:
                        return {"success": True, "data": await response.text() or "Success"}
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return {"success": False, "error": error_text, "status": response.status}
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {str(e)}")
            return {"success": False, "error": f"Connection error: {str(e)}"}
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        logger.info("Getting user information")
        endpoint = "/user"
        result = await self._make_request("GET", endpoint)
        
        if result["success"]:
            return result["data"]
        else:
            logger.error(f"Could not get user info: {result.get('error')}")
            return {}

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
    
    async def get_repository_branch_protection_rules(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get branch protection rules for a repository."""
        logger.info(f"Getting branch protection rules for {owner}/{repo}")
        
        # Get branch protection rules directly
        rules_endpoint = f"/repos/{owner}/{repo}/rulesets"
        params = {
            "per_page": 100,
            "includes_parents": "false",
            "targets": "branch"
        }
        
        preview_headers = {
            "Accept": "application/vnd.github.v3+json,application/vnd.github.ruleset-preview+json"
        }
        
        rules_result = await self._make_request(
            "GET", 
            rules_endpoint,
            params=params,
            preview_headers=preview_headers
        )
        
        if rules_result["success"]:
            if isinstance(rules_result["data"], list):
                return rules_result["data"]
            else:
                logger.error(f"Unexpected response format: {rules_result['data']}")
                return []
        else:
            logger.error(f"Could not get branch protection rules: {rules_result.get('error')}")
            logger.info("This may be normal for repositories that don't have any branch protection rules yet.")
            return []
    
    async def create_branch_protection_rule(
        self, 
        owner: str, 
        repo: str, 
        ruleset_name: str,
        target_branches: List[str],
        enforcement_status: str = "active",
        rules: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a branch protection rule (ruleset).
        
        Args:
            owner: Repository owner
            repo: Repository name
            ruleset_name: Name of the ruleset
            target_branches: List of branch patterns to protect (e.g., ["main", "release/*"])
            enforcement_status: "active", "evaluate", or "disabled"
            rules: Dictionary of rules to apply
        """
        logger.info(f"Creating branch protection ruleset '{ruleset_name}' for {owner}/{repo}")
        
        if rules is None:
            # Default rules for strong branch protection - as array format required by GitHub API
            rules = [
                {
                    "type": "pull_request",
                    "parameters": {
                        "dismiss_stale_reviews_on_push": True,
                        "require_code_owner_review": False,
                        "require_last_push_approval": False,
                        "required_approving_review_count": 1,
                        "required_review_thread_resolution": True
                    }
                },
                {
                    "type": "required_status_checks",
                    "parameters": {
                        "strict_required_status_checks_policy": True,
                        "required_status_checks": [
                            {"context": "ci/github-actions"}
                        ]
                    }
                },
                {
                    "type": "non_fast_forward",
                    "parameters": {}
                },
                {
                    "type": "deletion",
                    "parameters": {}
                }
            ]
        
        # Define the payload
        rules_payload = {
            "name": ruleset_name,
            "target": "branch",
            "enforcement": enforcement_status,
            "conditions": {
                "ref_name": {
                    "include": target_branches,
                    "exclude": []
                }
            },
            "rules": rules
        }
        
        # Log the payload for debugging
        logger.info(f"Request payload: {json.dumps(rules_payload, indent=2)}")
        
        # Create the ruleset
        endpoint = f"/repos/{owner}/{repo}/rulesets"
        preview_headers = {
            "Accept": "application/vnd.github.v3+json,application/vnd.github.ruleset-preview+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        result = await self._make_request(
            "POST", 
            endpoint, 
            data=rules_payload,
            preview_headers=preview_headers
        )
        
        if result["success"]:
            logger.info(f"Successfully created ruleset '{ruleset_name}'")
            return {"success": True, "ruleset": result["data"]}
        else:
            logger.error(f"Failed to create ruleset: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
    
    async def update_branch_protection_rule(
        self, 
        owner: str, 
        repo: str,
        ruleset_id: int,
        ruleset_name: str = None,
        target_branches: List[str] = None,
        enforcement_status: str = None,
        rules: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing branch protection rule (ruleset).
        
        Args:
            owner: Repository owner
            repo: Repository name
            ruleset_id: ID of the ruleset to update
            ruleset_name: New name for the ruleset (optional)
            target_branches: New list of branch patterns (optional)
            enforcement_status: New enforcement status (optional)
            rules: New rules to apply (optional) - must be in array format
        """
        logger.info(f"Updating branch protection ruleset ID {ruleset_id} for {owner}/{repo}")
        
        # Get current ruleset first
        get_endpoint = f"/repos/{owner}/{repo}/rulesets/{ruleset_id}"
        preview_headers = {
            "Accept": "application/vnd.github.v3+json,application/vnd.github.ruleset-preview+json"
        }
        
        current_result = await self._make_request(
            "GET", 
            get_endpoint,
            preview_headers=preview_headers
        )
        
        if not current_result["success"]:
            logger.error(f"Could not get current ruleset: {current_result.get('error')}")
            return {"success": False, "error": current_result.get("error")}
        
        current_ruleset = current_result["data"]
        
        # Prepare update payload, using current values as defaults
        update_payload = {
            "name": ruleset_name or current_ruleset.get("name"),
            "target": "branch",  # Currently only branch rulesets are supported
            "enforcement": enforcement_status or current_ruleset.get("enforcement", "active"),
        }
        
        # Update conditions if target_branches provided
        if target_branches:
            update_payload["conditions"] = {
                "ref_name": {
                    "include": target_branches,
                    "exclude": current_ruleset.get("conditions", {}).get("ref_name", {}).get("exclude", [])
                }
            }
        
        # Update rules if provided - must be array format
        if rules:
            update_payload["rules"] = rules
        
        # Update the ruleset
        endpoint = f"/repos/{owner}/{repo}/rulesets/{ruleset_id}"
        result = await self._make_request(
            "PUT", 
            endpoint, 
            data=update_payload,
            preview_headers=preview_headers
        )
        
        if result["success"]:
            logger.info(f"Successfully updated ruleset ID {ruleset_id}")
            return {"success": True, "ruleset": result["data"]}
        else:
            logger.error(f"Failed to update ruleset: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
    
    async def delete_branch_protection_rule(self, owner: str, repo: str, ruleset_id: int) -> Dict[str, Any]:
        """Delete a branch protection rule (ruleset)."""
        logger.info(f"Deleting branch protection ruleset ID {ruleset_id} from {owner}/{repo}")
        
        endpoint = f"/repos/{owner}/{repo}/rulesets/{ruleset_id}"
        preview_headers = {
            "Accept": "application/vnd.github.v3+json,application/vnd.github.ruleset-preview+json"
        }
        
        result = await self._make_request(
            "DELETE", 
            endpoint,
            preview_headers=preview_headers
        )
        
        if result["success"]:
            logger.info(f"Successfully deleted ruleset ID {ruleset_id}")
            return {"success": True}
        else:
            logger.error(f"Failed to delete ruleset: {result.get('error')}")
            return {"success": False, "error": result.get("error")}

async def configure_branch_protection(
    owner: str, 
    repo: str, 
    token: str,
    ruleset_name: str,
    branches: List[str],
    enforcement: str,
    required_checks: List[str] = None,
    require_approvals: bool = True,
    approval_count: int = 1,
    prevent_force_push: bool = True,
    prevent_deletion: bool = True,
    require_linear_history: bool = False
) -> Dict[str, Any]:
    """Configure branch protection rules for a repository."""
    async with GitHubAPI(token) as github:
        # Verify that we can connect to the API
        user_info = await github.get_user_info()
        if not user_info:
            return {"success": False, "error": "Could not authenticate with GitHub API"}
        
        logger.info(f"Authenticated as {user_info.get('login')}")
        
        # Get existing rules to avoid duplicates
        existing_rules = await github.get_repository_branch_protection_rules(owner, repo)
        
        # Check if a ruleset with this name already exists
        existing_ruleset = None
        for rule in existing_rules:
            if rule.get("name") == ruleset_name:
                existing_ruleset = rule
                break
        
        # Create custom rules based on arguments - in array format required by GitHub API
        rules = []
        
        # Add PR review rule if enabled
        if require_approvals:
            rules.append({
                "type": "pull_request",
                "parameters": {
                    "dismiss_stale_reviews_on_push": True,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": approval_count,
                    "required_review_thread_resolution": True
                }
            })
        
        # Add status checks rule if checks are provided
        if required_checks:
            status_checks_rule = {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": []
                }
            }
            
            for check in required_checks:
                status_checks_rule["parameters"]["required_status_checks"].append({"context": check})
            
            rules.append(status_checks_rule)
        
        # Linear history is not supported in the current API as a separate rule type
        # Keeping the parameter for backward compatibility
        
        # Add force push prevention if enabled
        if prevent_force_push:
            rules.append({
                "type": "non_fast_forward",
                "parameters": {}
            })
        
        # Add deletion prevention if enabled
        if prevent_deletion:
            rules.append({
                "type": "deletion",
                "parameters": {}
            })
        
        # Format branch patterns - add leading 'refs/heads/' if not already present
        formatted_branches = []
        for branch in branches:
            if not branch.startswith("refs/heads/"):
                formatted_branches.append(f"refs/heads/{branch}")
            else:
                formatted_branches.append(branch)
        
        # If ruleset exists, update it
        if existing_ruleset:
            logger.info(f"Updating existing ruleset '{ruleset_name}'")
            result = await github.update_branch_protection_rule(
                owner=owner,
                repo=repo,
                ruleset_id=existing_ruleset.get("id"),
                ruleset_name=ruleset_name,
                target_branches=formatted_branches,
                enforcement_status=enforcement,
                rules=rules
            )
        else:
            # Create new ruleset
            logger.info(f"Creating new ruleset '{ruleset_name}'")
            result = await github.create_branch_protection_rule(
                owner=owner,
                repo=repo,
                ruleset_name=ruleset_name,
                target_branches=formatted_branches,
                enforcement_status=enforcement,
                rules=rules
            )
        
        return result

async def list_branch_protection_rules(owner: str, repo: str, token: str) -> Dict[str, Any]:
    """List all branch protection rules for a repository."""
    async with GitHubAPI(token) as github:
        # Verify that we can connect to the API
        user_info = await github.get_user_info()
        if not user_info:
            return {"success": False, "error": "Could not authenticate with GitHub API"}
        
        logger.info(f"Authenticated as {user_info.get('login')}")
        
        # Get rules
        rules = await github.get_repository_branch_protection_rules(owner, repo)
        
        if rules:
            # Format rule display
            formatted_rules = []
            for rule in rules:
                rule_info = {
                    "id": rule.get("id"),
                    "name": rule.get("name"),
                    "enforcement": rule.get("enforcement"),
                    "target_branches": rule.get("conditions", {}).get("ref_name", {}).get("include", []),
                    "created_at": rule.get("created_at"),
                    "updated_at": rule.get("updated_at")
                }
                formatted_rules.append(rule_info)
            
            return {"success": True, "rules": formatted_rules}
        else:
            return {"success": True, "rules": []}

async def delete_rule(owner: str, repo: str, token: str, ruleset_id: int) -> Dict[str, Any]:
    """Delete a branch protection rule by ID."""
    async with GitHubAPI(token) as github:
        # Verify that we can connect to the API
        user_info = await github.get_user_info()
        if not user_info:
            return {"success": False, "error": "Could not authenticate with GitHub API"}
        
        logger.info(f"Authenticated as {user_info.get('login')}")
        
        # Delete the rule
        result = await github.delete_branch_protection_rule(owner, repo, ruleset_id)
        return result

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Configure GitHub branch protection rules")
    
    # Required arguments
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all branch protection rules")
    
    # Create/update command
    create_parser = subparsers.add_parser("create", help="Create or update a branch protection rule")
    create_parser.add_argument("--name", required=True, help="Name of the ruleset")
    create_parser.add_argument("--branches", required=True, help="Comma-separated list of branch patterns to protect")
    create_parser.add_argument("--enforcement", choices=["active", "evaluate", "disabled"], default="active",
                             help="Enforcement status of the ruleset")
    create_parser.add_argument("--required-checks", help="Comma-separated list of required status checks")
    create_parser.add_argument("--require-approvals", action="store_true", default=True,
                             help="Require pull request reviews before merging")
    create_parser.add_argument("--approval-count", type=int, default=1,
                             help="Number of required approving reviews")
    create_parser.add_argument("--prevent-force-push", action="store_true", default=True,
                             help="Prevent force pushes")
    create_parser.add_argument("--prevent-deletion", action="store_true", default=True,
                             help="Prevent branch deletion")
    create_parser.add_argument("--require-linear-history", action="store_true", default=False,
                             help="Require linear history")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a branch protection rule")
    delete_parser.add_argument("--id", type=int, required=True, help="ID of the ruleset to delete")
    
    return parser.parse_args()

async def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Get GitHub token from environment
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("No GitHub token found. Set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    # Execute command
    if args.command == "list":
        result = await list_branch_protection_rules(args.owner, args.repo, token)
        if result["success"]:
            rules = result["rules"]
            if rules:
                logger.info(f"Found {len(rules)} branch protection rules:")
                for rule in rules:
                    logger.info(f"ID: {rule['id']}")
                    logger.info(f"  Name: {rule['name']}")
                    logger.info(f"  Enforcement: {rule['enforcement']}")
                    logger.info(f"  Branches: {', '.join(rule['target_branches'])}")
                    logger.info(f"  Created: {rule['created_at']}")
                    logger.info(f"  Updated: {rule['updated_at']}")
                    logger.info("---")
            else:
                logger.info("No branch protection rules found.")
        else:
            logger.error(f"Failed to list rules: {result.get('error')}")
    
    elif args.command == "create":
        # Parse branch patterns and required checks
        branches = [b.strip() for b in args.branches.split(",")]
        required_checks = None
        if args.required_checks:
            required_checks = [c.strip() for c in args.required_checks.split(",")]
        
        result = await configure_branch_protection(
            owner=args.owner,
            repo=args.repo,
            token=token,
            ruleset_name=args.name,
            branches=branches,
            enforcement=args.enforcement,
            required_checks=required_checks,
            require_approvals=args.require_approvals,
            approval_count=args.approval_count,
            prevent_force_push=args.prevent_force_push,
            prevent_deletion=args.prevent_deletion,
            require_linear_history=args.require_linear_history
        )
        
        if result["success"]:
            logger.info(f"Successfully configured branch protection ruleset")
            
            # Display ruleset info
            if "ruleset" in result:
                ruleset = result["ruleset"]
                logger.info(f"Ruleset ID: {ruleset.get('id')}")
                logger.info(f"Name: {ruleset.get('name')}")
                logger.info(f"Enforcement: {ruleset.get('enforcement')}")
                target_branches = ruleset.get('conditions', {}).get('ref_name', {}).get('include', [])
                logger.info(f"Protected branches: {', '.join(target_branches)}")
        else:
            logger.error(f"Failed to configure branch protection: {result.get('error')}")
    
    elif args.command == "delete":
        result = await delete_rule(args.owner, args.repo, token, args.id)
        if result["success"]:
            logger.info(f"Successfully deleted ruleset with ID {args.id}")
        else:
            logger.error(f"Failed to delete ruleset: {result.get('error')}")
    
    else:
        logger.error("No command specified. Use --help for usage information.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 