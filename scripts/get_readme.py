#!/usr/bin/env python3
"""
Fetch repository README content
"""

import os
import sys
import asyncio
import aiohttp
import base64
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def get_readme(owner, repo, token):
    """Fetch README content from a GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "VOT1-GitHub-Integration"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            else:
                error_text = await response.text()
                logger.error(f"Error {response.status}: {error_text}")
                return None

async def main():
    owner = "kabrony"
    repo = "vot1"
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        logger.error("No GitHub token found. Set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
        
    readme_content = await get_readme(owner, repo, token)
    if readme_content:
        print("\n===== README CONTENT =====\n")
        print(readme_content)
        print("\n==========================\n")
    else:
        logger.error("Failed to fetch README content.")

if __name__ == "__main__":
    asyncio.run(main()) 