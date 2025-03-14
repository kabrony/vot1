#!/usr/bin/env python3
"""
Local MCP Bridge Example Client

This script demonstrates how to use the Local MCP Bridge to call MCP functions.
"""

import os
import sys
import json
import time
import argparse
import requests
from typing import Dict, Any, Optional

def call_perplexity_search(host: str, port: int, query: str, api_key: Optional[str] = None):
    """
    Call the Perplexity AI search function.
    
    Args:
        host: Server host
        port: Server port
        query: Search query
        api_key: Optional Perplexity API key
    
    Returns:
        Search result
    """
    base_url = f"http://{host}:{port}"
    
    # Check connection to Perplexity
    print("Checking connection to Perplexity...")
    response = requests.get(f"{base_url}/api/check-connection/PERPLEXITY")
    data = response.json()
    
    # Connect if not already connected
    if not data.get("active_connection", False):
        print("Not connected to Perplexity. Initiating connection...")
        
        # Get required parameters
        response = requests.get(f"{base_url}/api/get-required-parameters/PERPLEXITY")
        params_data = response.json()
        
        if not params_data.get("successful", False):
            print(f"Error getting required parameters: {params_data.get('error')}")
            return None
        
        # Check if API key is required
        if "api_key" in params_data.get("parameters", []):
            if not api_key:
                print("Perplexity API key is required but not provided.")
                return None
            
            # Initiate connection
            print("Connecting to Perplexity...")
            response = requests.post(
                f"{base_url}/api/initiate-connection/PERPLEXITY",
                json={"api_key": api_key}
            )
            conn_data = response.json()
            
            if not conn_data.get("successful", False):
                print(f"Error connecting to Perplexity: {conn_data.get('error')}")
                return None
            
            print(f"Connected to Perplexity: {conn_data.get('message')}")
    
    # Call the Perplexity AI search function
    print(f"Calling Perplexity AI search with query: {query}")
    response = requests.post(
        f"{base_url}/api/call-function",
        json={
            "function_name": "mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH",
            "params": {
                "params": {
                    "systemContent": "You are a helpful research assistant.",
                    "userContent": query,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "return_citations": True
                }
            }
        }
    )
    
    # Process the response
    result = response.json()
    if not result.get("successful", False):
        print(f"Error calling Perplexity AI search: {result.get('error')}")
        return None
    
    return result


def call_github_search(host: str, port: int, query: str, github_token: Optional[str] = None):
    """
    Call the GitHub search repositories function.
    
    Args:
        host: Server host
        port: Server port
        query: Search query
        github_token: Optional GitHub API token
    
    Returns:
        Search result
    """
    base_url = f"http://{host}:{port}"
    
    # Check connection to GitHub
    print("Checking connection to GitHub...")
    response = requests.get(f"{base_url}/api/check-connection/GITHUB")
    data = response.json()
    
    # Connect if not already connected
    if not data.get("active_connection", False):
        print("Not connected to GitHub. Initiating connection...")
        
        # Get required parameters
        response = requests.get(f"{base_url}/api/get-required-parameters/GITHUB")
        params_data = response.json()
        
        if not params_data.get("successful", False):
            print(f"Error getting required parameters: {params_data.get('error')}")
            return None
        
        # Check if GitHub token is required
        required_params = params_data.get("parameters", [])
        if "github_token" in required_params or "token" in required_params:
            if not github_token:
                print("GitHub token is required but not provided.")
                return None
            
            # Initiate connection
            print("Connecting to GitHub...")
            response = requests.post(
                f"{base_url}/api/initiate-connection/GITHUB",
                json={"token": github_token}
            )
            conn_data = response.json()
            
            if not conn_data.get("successful", False):
                print(f"Error connecting to GitHub: {conn_data.get('error')}")
                return None
            
            print(f"Connected to GitHub: {conn_data.get('message')}")
    
    # Call the GitHub search repositories function
    print(f"Searching GitHub repositories with query: {query}")
    response = requests.post(
        f"{base_url}/api/call-function",
        json={
            "function_name": "mcp_GITHUB_SEARCH_REPOSITORIES",
            "params": {
                "params": {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5
                }
            }
        }
    )
    
    # Process the response
    result = response.json()
    if not result.get("successful", False):
        print(f"Error searching GitHub repositories: {result.get('error')}")
        return None
    
    return result


def call_firecrawl_scrape(host: str, port: int, url: str, firecrawl_key: Optional[str] = None):
    """
    Call the Firecrawl scrape function.
    
    Args:
        host: Server host
        port: Server port
        url: URL to scrape
        firecrawl_key: Optional Firecrawl API key
    
    Returns:
        Scrape result
    """
    base_url = f"http://{host}:{port}"
    
    # Check connection to Firecrawl
    print("Checking connection to Firecrawl...")
    response = requests.get(f"{base_url}/api/check-connection/FIRECRAWL")
    data = response.json()
    
    # Connect if not already connected
    if not data.get("active_connection", False):
        print("Not connected to Firecrawl. Initiating connection...")
        
        # Get required parameters
        response = requests.get(f"{base_url}/api/get-required-parameters/FIRECRAWL")
        params_data = response.json()
        
        if not params_data.get("successful", False):
            print(f"Error getting required parameters: {params_data.get('error')}")
            return None
        
        # Check if API key is required
        if "api_key" in params_data.get("parameters", []):
            if not firecrawl_key:
                print("Firecrawl API key is required but not provided.")
                return None
            
            # Initiate connection
            print("Connecting to Firecrawl...")
            response = requests.post(
                f"{base_url}/api/initiate-connection/FIRECRAWL",
                json={"api_key": firecrawl_key}
            )
            conn_data = response.json()
            
            if not conn_data.get("successful", False):
                print(f"Error connecting to Firecrawl: {conn_data.get('error')}")
                return None
            
            print(f"Connected to Firecrawl: {conn_data.get('message')}")
    
    # Call the Firecrawl scrape function
    print(f"Scraping URL with Firecrawl: {url}")
    response = requests.post(
        f"{base_url}/api/call-function",
        json={
            "function_name": "mcp_FIRECRAWL_FIRECRAWL_SCRAPE_EXTRACT_DATA_LLM",
            "params": {
                "params": {
                    "url": url,
                    "formats": ["text", "html"],
                    "onlyMainContent": True,
                    "jsonOptions": {
                        "prompt": "Extract the main content from this page"
                    }
                }
            }
        }
    )
    
    # Process the response
    result = response.json()
    if not result.get("successful", False):
        print(f"Error scraping URL: {result.get('error')}")
        return None
    
    return result


def get_server_status(host: str, port: int):
    """
    Get the server status.
    
    Args:
        host: Server host
        port: Server port
    
    Returns:
        Server status
    """
    base_url = f"http://{host}:{port}"
    
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            return data
        return {"successful": False, "error": f"HTTP error: {response.status_code}"}
    except Exception as e:
        return {"successful": False, "error": str(e)}


def display_metrics(host: str, port: int):
    """
    Display server metrics.
    
    Args:
        host: Server host
        port: Server port
    """
    base_url = f"http://{host}:{port}"
    
    try:
        response = requests.get(f"{base_url}/api/metrics")
        if response.status_code == 200:
            data = response.json()
            if data.get("successful", False):
                metrics = data.get("metrics", {})
                
                print("\n=== Server Metrics ===")
                print(f"API Calls: {metrics.get('api_calls', 0)}")
                print(f"API Errors: {metrics.get('api_errors', 0)}")
                error_rate = metrics.get('error_rate', 0) * 100
                print(f"Error Rate: {error_rate:.2f}%")
                print(f"Avg Response Time: {metrics.get('avg_response_time', 0):.3f} seconds")
                
                cache_stats = metrics.get('cache_stats')
                if cache_stats:
                    print("\n=== Cache Stats ===")
                    print(f"Hits: {cache_stats.get('hits', 0)}")
                    print(f"Misses: {cache_stats.get('misses', 0)}")
                    last_cleared = time.localtime(cache_stats.get('last_cleared', 0))
                    print(f"Last Cleared: {time.strftime('%Y-%m-%d %H:%M:%S', last_cleared)}")
            else:
                print(f"Error getting metrics: {data.get('error')}")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


def clear_cache(host: str, port: int):
    """
    Clear the server cache.
    
    Args:
        host: Server host
        port: Server port
    """
    base_url = f"http://{host}:{port}"
    
    try:
        response = requests.post(f"{base_url}/api/clear-cache")
        if response.status_code == 200:
            data = response.json()
            if data.get("successful", False):
                print("Cache cleared successfully")
                stats = data.get("stats", {})
                print(f"Entries before: {stats.get('entries_before', 0)}")
                print(f"Hits: {stats.get('hits', 0)}")
                print(f"Misses: {stats.get('misses', 0)}")
            else:
                print(f"Error clearing cache: {data.get('error')}")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Local MCP Bridge Example Client")
    
    # Server configuration
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=5678, help="Server port")
    
    # Service API keys
    parser.add_argument("--github-token", help="GitHub API token")
    parser.add_argument("--perplexity-key", help="Perplexity API key")
    parser.add_argument("--firecrawl-key", help="Firecrawl API key")
    
    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--status", action="store_true", help="Get server status")
    action_group.add_argument("--metrics", action="store_true", help="Get server metrics")
    action_group.add_argument("--clear-cache", action="store_true", help="Clear server cache")
    action_group.add_argument("--perplexity-search", help="Call Perplexity AI search with the given query")
    action_group.add_argument("--github-search", help="Search GitHub repositories with the given query")
    action_group.add_argument("--firecrawl-scrape", help="Scrape a URL with Firecrawl")
    
    args = parser.parse_args()
    
    # Check if the server is running
    status = get_server_status(args.host, args.port)
    if not status.get("successful", False):
        print(f"Error: Server not running or not accessible: {status.get('error')}")
        return 1
    
    print(f"Server is running (uptime: {status.get('uptime', 0):.1f}s)")
    
    # Perform the requested action
    if args.status:
        print("\n=== Server Status ===")
        print(f"Status: {status.get('status')}")
        print(f"Uptime: {status.get('uptime'):.1f} seconds")
        print("\nAvailable Services:")
        for service in status.get("available_services", []):
            print(f"- {service}")
        print("\nConnected Services:")
        for service in status.get("connected_services", []):
            print(f"- {service}")
    
    elif args.metrics:
        display_metrics(args.host, args.port)
    
    elif args.clear_cache:
        clear_cache(args.host, args.port)
    
    elif args.perplexity_search:
        result = call_perplexity_search(
            args.host, 
            args.port, 
            args.perplexity_search, 
            args.perplexity_key
        )
        if result:
            print("\n=== Perplexity AI Search Result ===")
            print(json.dumps(result, indent=2))
    
    elif args.github_search:
        result = call_github_search(
            args.host, 
            args.port, 
            args.github_search, 
            args.github_token
        )
        if result:
            print("\n=== GitHub Search Result ===")
            print(json.dumps(result, indent=2))
    
    elif args.firecrawl_scrape:
        result = call_firecrawl_scrape(
            args.host, 
            args.port, 
            args.firecrawl_scrape, 
            args.firecrawl_key
        )
        if result:
            print("\n=== Firecrawl Scrape Result ===")
            print(json.dumps(result, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 