"""
Firecrawl Integration for VOT1

This module provides integration with Firecrawl's web scraping and data extraction capabilities
through the Composio MCP interface.
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

class FirecrawlClient:
    """
    Client for interacting with Firecrawl through Composio MCP.
    """
    
    def __init__(self, mcp_url: Optional[str] = None):
        """
        Initialize the Firecrawl client.
        
        Args:
            mcp_url: Optional URL for the Firecrawl MCP endpoint.
                     If not provided, will use environment variable or config file.
        """
        self.mcp_url = mcp_url or self._get_mcp_url()
        self.api_key = os.environ.get("FIRECRAWL_API_KEY", "")
        
        # Validate configuration
        if not self.mcp_url:
            logger.warning("Firecrawl MCP URL not configured. Scraping functionality will be limited.")
    
    def _get_mcp_url(self) -> str:
        """
        Get the Firecrawl MCP URL from environment variables or config file.
        
        Returns:
            The MCP URL as a string.
        """
        # First check environment variable
        mcp_url = os.environ.get("FIRECRAWL_MCP_URL")
        if mcp_url:
            return mcp_url
            
        # Then check config file
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../../../config/mcp.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("mcpServers", {}).get("FIRECRAWL", {}).get("url", "")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            return ""
    
    def scrape_content(self, url: str, extract_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scrape content from a URL and optionally extract structured data.
        
        Args:
            url: The URL to scrape
            extract_data: Optional extraction configuration for structured data
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot scrape content: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "url": url}
            
        try:
            # Prepare the request payload
            payload = {
                "url": url
            }
            
            if extract_data:
                payload["extract_data"] = extract_data
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/scrape",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping content: {e}")
            return {
                "error": str(e),
                "url": url
            }
    
    def crawl_urls(self, start_url: str, max_pages: int = 10, 
                  include_patterns: Optional[List[str]] = None,
                  exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Crawl websites recursively starting from a URL.
        
        Args:
            start_url: The starting URL for crawling
            max_pages: Maximum number of pages to crawl
            include_patterns: List of URL patterns to include
            exclude_patterns: List of URL patterns to exclude
            
        Returns:
            Dictionary containing job ID and status
        """
        if not self.mcp_url:
            logger.error("Cannot crawl URLs: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "start_url": start_url}
            
        try:
            # Prepare the request payload
            payload = {
                "start_url": start_url,
                "max_pages": max_pages
            }
            
            if include_patterns:
                payload["include_patterns"] = include_patterns
                
            if exclude_patterns:
                payload["exclude_patterns"] = exclude_patterns
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/crawl",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error starting crawl: {e}")
            return {
                "error": str(e),
                "start_url": start_url
            }
    
    def extract_structured_data(self, url: str, extraction_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from a web page.
        
        Args:
            url: The URL to extract data from
            extraction_config: Configuration for data extraction
            
        Returns:
            Dictionary containing extracted data and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot extract data: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "url": url}
            
        try:
            # Prepare the request payload
            payload = {
                "url": url,
                "extraction_config": extraction_config
            }
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/extract",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error extracting data: {e}")
            return {
                "error": str(e),
                "url": url
            }
    
    def map_urls(self, urls: List[str], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map multiple URLs based on user options.
        
        Args:
            urls: List of URLs to map
            options: Optional mapping options
            
        Returns:
            Dictionary containing mapping results
        """
        if not self.mcp_url:
            logger.error("Cannot map URLs: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "urls": urls}
            
        try:
            # Prepare the request payload
            payload = {
                "urls": urls
            }
            
            if options:
                payload["options"] = options
                
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/map",
                json=payload,
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error mapping URLs: {e}")
            return {
                "error": str(e),
                "urls": urls
            }
    
    def get_crawl_job_status(self, job_uuid: str) -> Dict[str, Any]:
        """
        Get the status of a crawl job by its UUID.
        
        Args:
            job_uuid: The UUID of the crawl job
            
        Returns:
            Dictionary containing job status and metadata
        """
        if not self.mcp_url:
            logger.error("Cannot get job status: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "job_uuid": job_uuid}
            
        try:
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.get(
                f"{self.mcp_url}/job/{job_uuid}",
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting job status: {e}")
            return {
                "error": str(e),
                "job_uuid": job_uuid
            }
    
    def cancel_crawl_job(self, job_uuid: str) -> Dict[str, Any]:
        """
        Cancel a crawl job by its UUID.
        
        Args:
            job_uuid: The UUID of the crawl job to cancel
            
        Returns:
            Dictionary containing cancellation status
        """
        if not self.mcp_url:
            logger.error("Cannot cancel job: Firecrawl MCP URL not configured")
            return {"error": "Firecrawl MCP URL not configured", "job_uuid": job_uuid}
            
        try:
            # Add API key if available
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            # Make the request to the MCP endpoint
            response = requests.post(
                f"{self.mcp_url}/job/{job_uuid}/cancel",
                headers=headers
            )
            
            # Check for successful response
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error cancelling job: {e}")
            return {
                "error": str(e),
                "job_uuid": job_uuid
            }
    
    def wait_for_job_completion(self, job_uuid: str, timeout: int = 300, 
                               poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a job to complete, polling at regular intervals.
        
        Args:
            job_uuid: The UUID of the job to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Dictionary containing final job status
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_crawl_job_status(job_uuid)
            
            if "error" in status:
                return status
                
            job_status = status.get("status", "").lower()
            
            if job_status in ["completed", "failed", "cancelled"]:
                return status
                
            # Wait before checking again
            time.sleep(poll_interval)
            
        return {
            "error": "Timeout waiting for job completion",
            "job_uuid": job_uuid,
            "last_status": status
        }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    firecrawl = FirecrawlClient()
    
    # Example scrape
    result = firecrawl.scrape_content("https://example.com")
    print(json.dumps(result, indent=2))
    
    # Example crawl
    crawl_job = firecrawl.crawl_urls("https://example.com", max_pages=5)
    if "job_uuid" in crawl_job:
        # Wait for job completion
        final_status = firecrawl.wait_for_job_completion(crawl_job["job_uuid"])
        print(json.dumps(final_status, indent=2)) 