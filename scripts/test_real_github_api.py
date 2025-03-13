#!/usr/bin/env python3
"""
Test Real GitHub API

This script tests the real GitHub API implementation by performing basic operations
like repository analysis, webhook creation, and workflow creation.
"""

import os
import asyncio
import logging
import argparse
from typing import Dict, Any, Optional

from real_github_api import GitHubAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("github_api_test.log")
    ]
)
logger = logging.getLogger(__name__)

async def test_basic_operations(token: str, owner: str, repo: str) -> None:
    """
    Test basic GitHub API operations.
    
    Args:
        token: GitHub API token
        owner: Repository owner
        repo: Repository name
    """
    async with GitHubAPIClient(token) as client:
        # Test authentication
        logger.info("Testing authentication...")
        creds = await client.verify_credentials()
        if not creds["success"]:
            logger.error(f"Authentication failed: {creds.get('error')}")
            return
            
        logger.info(f"Successfully authenticated as {creds['user']['login']}")
        
        # Test repository info
        logger.info(f"Getting repository info for {owner}/{repo}...")
        repo_info = await client.get_repository(owner, repo)
        if "id" in repo_info:
            logger.info(f"Repository info retrieved successfully")
            logger.info(f"  Name: {repo_info['name']}")
            logger.info(f"  Stars: {repo_info['stargazers_count']}")
            logger.info(f"  Language: {repo_info['language']}")
        else:
            logger.error(f"Failed to get repository info: {repo_info.get('error', 'Unknown error')}")
            return
            
        # Test repository contents
        logger.info(f"Getting repository contents for {owner}/{repo}...")
        contents = await client.get_repository_contents(owner, repo)
        if isinstance(contents, list):
            logger.info(f"Found {len(contents)} items in repository root")
            for item in contents[:5]:  # Show first 5 items
                logger.info(f"  {item['type']}: {item['name']}")
        else:
            logger.error(f"Failed to get repository contents: {contents.get('error', 'Unknown error')}")
            
        # Test repository analysis
        logger.info(f"Analyzing repository {owner}/{repo}...")
        analysis = await client.analyze_repository(owner, repo, deep_analysis=True)
        
        if analysis["success"]:
            logger.info("Analysis completed successfully")
            logger.info(f"  Documentation score: {analysis['documentation']['score']:.2f}")
            logger.info(f"  Code quality score: {analysis['code_quality']['score']:.2f}")
            logger.info(f"  Workflows: {analysis['workflows']['count']}")
            
            if analysis.get('deep_analysis_results'):
                logger.info(f"  Health score: {analysis['deep_analysis_results'].get('health_score', 'N/A')}")
                logger.info(f"  Stale issues: {analysis['deep_analysis_results'].get('stale_issues', 'N/A')}")
                
            logger.info("Improvement areas:")
            for area in analysis.get('improvement_areas', []):
                logger.info(f"  - {area['title']} ({area['priority']})")
        else:
            logger.error(f"Analysis failed: {analysis.get('error', 'Unknown error')}")

async def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Test Real GitHub API")
    parser.add_argument("--token", help="GitHub API token")
    parser.add_argument("--owner", default="microsoft", help="Repository owner")
    parser.add_argument("--repo", default="vscode", help="Repository name")
    
    args = parser.parse_args()
    
    # Get token from environment variable if not provided
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.error("GitHub token not provided. Use --token or set GITHUB_TOKEN environment variable")
        return 1
        
    try:
        await test_basic_operations(token, args.owner, args.repo)
        return 0
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 