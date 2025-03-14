#!/usr/bin/env python3
"""
VOT1 GitHub Composio Bridge

This module serves as a bridge between the VOT1 system and GitHub, using the Composio
integration to enable autonomous repository interactions with enhanced capabilities.
It provides functionality for working with repositories, issues, pull requests,
and other GitHub features through Composio's direct GitHub integration.

Key features:
1. Repository analysis and metrics with enhanced depth
2. Automated issue and PR creation/management
3. Code review comment automation
4. Repository improvement tracking
5. Integration with both Claude and Perplexity models via Composio
"""

import os
import sys
import logging
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
import aiohttp
import uuid

# Import Composio libraries
try:
    from composio_openai import ComposioToolSet, App, Action
    from openai import OpenAI
    COMPOSIO_AVAILABLE = True
except ImportError:
    COMPOSIO_AVAILABLE = False
    logging.warning("Composio libraries not found. Install with 'pip install composio-openai openai'")

# Import VOT1 components
from src.vot1.github_app_bridge import GitHubAppBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubComposioBridge(GitHubAppBridge):
    """
    Bridge between VOT1 and GitHub using Composio integration.
    
    This bridge enables autonomous GitHub repository interactions,
    with advanced AI-powered analysis and updates via Composio integration.
    """
    
    def __init__(
        self,
        github_token: str,
        composio_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model_name: str = "claude-3-7-sonnet",
        mcp_url: Optional[str] = None,
        mcp_key: Optional[str] = None,
        cache_enabled: bool = True,
        use_mcp: bool = False,
        **kwargs
    ):
        """
        Initialize the GitHub Composio Bridge.
        
        Args:
            github_token: GitHub personal access token
            composio_api_key: Composio API key for AI integration
            openai_api_key: OpenAI API key (alternative to Composio)
            model_name: LLM model to use
            mcp_url: URL for the Model Control Protocol server
            mcp_key: API key for MCP authentication
            cache_enabled: Whether to cache API responses
            use_mcp: Whether to use MCP for API calls
        """
        super().__init__(github_token, **kwargs)
        
        self.composio_api_key = composio_api_key
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.mcp_url = mcp_url
        self.mcp_key = mcp_key
        self.use_mcp = use_mcp
        
        # Cached GitHub data to reduce API calls
        self.cache_enabled = cache_enabled
        self.cache = {} if cache_enabled else None
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.cache_stats = {"hits": 0, "misses": 0, "last_cleared": time.time()}
        
        # Performance monitoring
        self.performance_metrics = {
            "api_calls": 0,
            "api_errors": 0,
            "response_times": [],
            "start_time": time.time()
        }
        
        # UI components for progress reporting
        self.progress_callbacks = {}
        self.active_operations = {}
        
        logger.info(f"Initialized GitHubComposioBridge with model {model_name}")
        if self.use_mcp:
            logger.info(f"Using MCP integration at {self.mcp_url}")
    
    async def check_connection(self) -> Dict[str, bool]:
        """
        Check connections to GitHub API and Composio.
        
        Returns:
            Dictionary with connection status
        """
        start_time = time.time()
        result = {
            "github_connected": False,
            "composio_connected": False,
            "mcp_connected": False,
            "response_time_ms": 0
        }
        
        try:
            # Check GitHub connection
            user = await self.get_user()
            if user and "login" in user:
                result["github_connected"] = True
                result["github_user"] = user["login"]
            
            # Check Composio connection if available
            if self.composio_api_key:
                # Simple check - in production would call Composio API endpoint
                result["composio_connected"] = True
            
            # Check MCP connection if enabled
            if self.use_mcp and self.mcp_url:
                mcp_health = await self._check_mcp_health()
                result["mcp_connected"] = mcp_health.get("status") == "ok"
                result["mcp_health"] = mcp_health
            
        except Exception as e:
            logger.error(f"Error checking connections: {e}")
            result["error"] = str(e)
        
        # Calculate response time
        result["response_time_ms"] = int((time.time() - start_time) * 1000)
        self.performance_metrics["response_times"].append(result["response_time_ms"])
        
        return result
    
    async def _check_mcp_health(self) -> Dict[str, Any]:
        """Check MCP server health."""
        if not self.mcp_url:
            return {"status": "unavailable", "reason": "MCP URL not configured"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_url}/health", 
                    headers={"Authorization": f"Bearer {self.mcp_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "ok", "details": data}
                    else:
                        return {
                            "status": "error", 
                            "status_code": response.status,
                            "reason": await response.text()
                        }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def star_repository(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Star a GitHub repository using Composio GitHub tools.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            
        Returns:
            Dictionary with star operation results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        if not self.has_composio:
            # Fall back to parent implementation
            return await super().star_repository(owner, repo)
            
        try:
            # Create a task to star the repository
            task = f"Star the GitHub repository {owner}/{repo}"
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for tool calling
                tools=self.github_tools,
                messages=[
                    {"role": "system", "content": "You are a GitHub automation assistant. Perform the requested GitHub operations precisely."},
                    {"role": "user", "content": task},
                ],
            )
            
            # Process the response
            result = self.composio_toolset.handle_tool_calls(response)
            
            # Check if the operation was successful
            success = "successfully" in result.lower() and "error" not in result.lower()
            
            # Store in memory if successful
            if success and self.memory_manager:
                memory_content = f"""
                Starred GitHub Repository:
                Repository: {owner}/{repo}
                Method: Composio GitHub Integration
                """
                
                metadata = {
                    "type": "github_repository_starred",
                    "owner": owner,
                    "repo": repo,
                    "timestamp": time.time()
                }
                
                self.memory_manager.add_semantic_memory(
                    content=memory_content,
                    metadata=metadata
                )
            
            return {
                "success": success,
                "message": result,
                "repository": f"{owner}/{repo}"
            }
        except Exception as e:
            logger.error(f"Error starring repository: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def analyze_repository(self, owner: Optional[str] = None, repo: Optional[str] = None, deep_analysis: bool = False) -> Dict[str, Any]:
        """
        Analyze a GitHub repository to gather metrics and insights using Composio.
        
        This enhanced implementation provides deeper insights into code quality,
        repository structure, and overall health compared to the MCP version.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            deep_analysis: Whether to perform a more thorough analysis
            
        Returns:
            Dictionary with repository analysis results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        if not self.has_composio:
            # Fall back to parent implementation
            return await super().analyze_repository(owner, repo, deep_analysis)
        
        try:
            logger.info(f"Starting Composio-powered repository analysis for {owner}/{repo} (deep_analysis={deep_analysis})")
            
            # Create a comprehensive analysis task
            analysis_task = f"""
            Perform a comprehensive analysis of the GitHub repository {owner}/{repo}.
            
            Please provide detailed information about:
            1. Repository metadata (stars, forks, watchers, etc.)
            2. Code quality issues and potential improvements
            3. Recent pull requests and their status
            4. Recent commits and activity metrics
            5. Repository structure and organization
            6. Documentation completeness and quality
            7. Community health indicators
            
            Structure your response as a detailed JSON object with clear sections for each aspect.
            Focus especially on actionable improvements and quality metrics.
            
            If deep analysis is requested, include more detailed code quality assessment.
            Deep analysis requested: {deep_analysis}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for tool calling
                tools=self.github_tools,
                messages=[
                    {"role": "system", "content": "You are a GitHub repository analysis expert. Provide detailed, accurate, and comprehensive analysis of repositories."},
                    {"role": "user", "content": analysis_task},
                ],
            )
            
            # Process the response
            result = self.composio_toolset.handle_tool_calls(response)
            
            # Parse the structured result
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'```json\n([\s\S]*?)\n```', result)
                
                if json_match:
                    analysis_result = json.loads(json_match.group(1))
                else:
                    # Try to parse the entire response as JSON
                    analysis_result = json.loads(result)
            except Exception as json_err:
                logger.warning(f"Failed to parse structured analysis. Treating response as raw text: {json_err}")
                # If JSON parsing fails, create a structured object with the raw text
                analysis_result = {
                    "repository": {"name": f"{owner}/{repo}"},
                    "raw_analysis": result,
                    "error": "Failed to parse structured analysis"
                }
            
            # Add success flag
            analysis_result["success"] = True
            
            # Store analysis in memory
            if self.memory_manager:
                memory_content = f"""
                Repository Analysis for {owner}/{repo} (via Composio)
                
                Analysis Result:
                {json.dumps(analysis_result, indent=2)}
                """
                
                metadata = {
                    "type": "github_repository_analysis_composio",
                    "owner": owner,
                    "repo": repo,
                    "timestamp": time.time(),
                    "deep_analysis": deep_analysis
                }
                
                analysis_memory = self.memory_manager.add_semantic_memory(
                    content=memory_content,
                    metadata=metadata
                )
                logger.info(f"Repository analysis stored in memory: {analysis_memory.id}")
            
            return analysis_result
        except Exception as e:
            logger.error(f"Error analyzing repository {owner}/{repo} with Composio: {e}")
            
            # Fall back to parent implementation if Composio fails
            logger.info("Falling back to MCP implementation for repository analysis")
            return await super().analyze_repository(owner, repo, deep_analysis)
    
    async def run_autonomous_improvement_cycle(
        self,
        components: List[str] = None,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        max_improvements: int = 3,
        create_prs: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete autonomous improvement cycle for the repository using Composio.
        
        This enhanced method provides more sophisticated repository analysis
        and better improvement suggestions compared to the MCP version.
        
        Args:
            components: List of component paths to improve (if None, will detect automatically)
            owner: Repository owner or organization
            repo: Repository name
            max_improvements: Maximum number of improvements to make
            create_prs: Whether to create PRs for the improvements
            
        Returns:
            Dictionary with improvement results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        if not self.has_composio:
            # Fall back to parent implementation
            return await super().run_autonomous_improvement_cycle(components, owner, repo, max_improvements, create_prs)
        
        try:
            logger.info(f"Starting Composio-powered autonomous improvement cycle for {owner}/{repo}")
            
            # Step 1: Analyze the repository
            analysis_result = await self.analyze_repository(owner, repo, deep_analysis=True)
            
            if not analysis_result.get("success", False):
                return {"error": "Repository analysis failed", "success": False}
            
            # Step 2: Identify components to improve if not provided
            if not components:
                # Create a task to identify components to improve
                components_task = f"""
                Based on the repository analysis of {owner}/{repo}, identify {max_improvements} components 
                that would benefit most from improvements.
                
                Focus on components that:
                1. Have code quality issues
                2. Are central to the repository's functionality
                3. Have high complexity or technical debt
                4. Lack proper documentation or tests
                
                Return a JSON array of file paths relative to the repository root.
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # Using GPT-4o for tool calling
                    tools=self.github_tools,
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying code components that need improvement. Return specific file paths that would benefit from improvement."},
                        {"role": "user", "content": components_task},
                    ],
                )
                
                # Process the response
                result = self.composio_toolset.handle_tool_calls(response)
                
                # Try to extract components from the result
                try:
                    # Try to find a JSON array in the response
                    import re
                    json_match = re.search(r'\[.*\]', result, re.DOTALL)
                    
                    if json_match:
                        components = json.loads(json_match.group(0))
                    else:
                        # Fallback: parse the entire text as JSON if possible
                        components = json.loads(result)
                    
                    # Ensure components is a list of strings
                    if not isinstance(components, list) or not all(isinstance(c, str) for c in components):
                        raise ValueError("Invalid components format")
                except Exception as json_err:
                    logger.error(f"Error parsing components from Composio response: {json_err}")
                    # Fallback to MCP implementation
                    components = await self._identify_improvement_candidates(
                        analysis_result,
                        owner,
                        repo,
                        max_candidates=max_improvements
                    )
                
                if not components:
                    return {
                        "message": "No components identified for improvement",
                        "success": True,
                        "improvements": []
                    }
            
            # Step 3: Generate improvements for each component
            improvements = []
            
            for component_path in components[:max_improvements]:
                logger.info(f"Generating improvement for component: {component_path}")
                
                # For each component, create a detailed improvement plan
                improvement_task = f"""
                Generate detailed improvements for the component: {component_path} in repository {owner}/{repo}.
                
                Please analyze:
                1. Code quality issues
                2. Architectural concerns
                3. Documentation gaps
                4. Testing needs
                5. Performance optimizations
                
                Provide specific, actionable recommendations with code examples where appropriate.
                Structure your response as a detailed, professional GitHub issue.
                """
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",  # Using GPT-4o for tool calling
                    tools=self.github_tools,
                    messages=[
                        {"role": "system", "content": "You are an expert software engineer specializing in code improvement. Generate detailed, actionable improvement plans."},
                        {"role": "user", "content": improvement_task},
                    ],
                )
                
                # Process the response to get the improvement plan
                improvement_plan = self.composio_toolset.handle_tool_calls(response)
                
                # Create an issue with the improvement plan
                issue_title = f"Improvement Plan for {component_path}"
                issue_body = improvement_plan
                
                # Create the issue
                issue_creation_task = f"""
                Create a GitHub issue in repository {owner}/{repo} with the following:
                Title: {issue_title}
                Body: 
                {issue_body}
                
                Labels: improvement, autonomous-feedback
                """
                
                try:
                    issue_response = self.openai_client.chat.completions.create(
                        model="gpt-4o",  # Using GPT-4o for tool calling
                        tools=self.github_tools,
                        messages=[
                            {"role": "system", "content": "You are a GitHub automation assistant. Create issues with the exact content provided."},
                            {"role": "user", "content": issue_creation_task},
                        ],
                    )
                    
                    # Process the response
                    issue_result = self.composio_toolset.handle_tool_calls(issue_response)
                    
                    # Check if issue creation was successful
                    if "created" in issue_result.lower() and "error" not in issue_result.lower():
                        # Try to extract issue number from the response
                        import re
                        issue_number_match = re.search(r'#(\d+)', issue_result)
                        issue_number = int(issue_number_match.group(1)) if issue_number_match else None
                        
                        improvements.append({
                            "component": component_path,
                            "issue": {
                                "title": issue_title,
                                "body": issue_body,
                                "number": issue_number,
                                "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}" if issue_number else None
                            },
                            "pr": None
                        })
                    else:
                        logger.error(f"Error creating issue for {component_path}: {issue_result}")
                except Exception as issue_err:
                    logger.error(f"Error creating issue for {component_path}: {issue_err}")
            
            return {
                "success": True,
                "components_analyzed": len(components),
                "improvements": improvements
            }
            
        except Exception as e:
            logger.error(f"Error in Composio autonomous improvement cycle for {owner}/{repo}: {e}")
            
            # Fall back to parent implementation
            logger.info("Falling back to MCP implementation for autonomous improvement cycle")
            return await super().run_autonomous_improvement_cycle(components, owner, repo, max_improvements, create_prs)
    
    async def generate_health_check_report(
        self, 
        owner: Optional[str] = None, 
        repo: Optional[str] = None,
        create_issue: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive health check report for the repository using Composio.
        
        This enhanced method provides deeper health assessment and more
        detailed improvement recommendations compared to the MCP version.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            create_issue: Whether to create an issue with the report
            
        Returns:
            Dictionary with health check results
        """
        owner = owner or self.default_owner
        repo = repo or self.default_repo
        
        if not owner or not repo:
            return {"error": "Repository owner and name are required", "success": False}
        
        if not self.has_composio:
            # Fall back to parent implementation
            return await super().generate_health_check_report(owner, repo, create_issue)
        
        try:
            logger.info(f"Generating Composio-powered health check report for {owner}/{repo}")
            
            # Create a task to generate a comprehensive health report
            health_report_task = f"""
            Generate a comprehensive health check report for the GitHub repository {owner}/{repo}.
            
            Include detailed assessment of:
            1. Code quality and maintainability
            2. Documentation completeness and clarity
            3. Test coverage and quality
            4. Community engagement and contributions
            5. Project activity and maintenance status
            6. Security practices and vulnerabilities
            7. Overall repository health score (0-1 scale)
            
            Provide specific, actionable recommendations for improvement in each area.
            Structure your report in a professional format suitable for a GitHub issue.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o for tool calling
                tools=self.github_tools,
                messages=[
                    {"role": "system", "content": "You are an expert at repository health assessment. Generate comprehensive, actionable health reports for GitHub repositories."},
                    {"role": "user", "content": health_report_task},
                ],
            )
            
            # Process the response
            health_report = self.composio_toolset.handle_tool_calls(response)
            
            # Try to extract structured health scores from the report
            try:
                # Look for scores in the report
                import re
                
                # Look for overall health score
                overall_score_match = re.search(r'overall[\s\w]+score:?\s*(0\.\d+|1\.0|1)', health_report, re.IGNORECASE)
                overall_score = float(overall_score_match.group(1)) if overall_score_match else 0.5
                
                # Look for documentation score
                doc_score_match = re.search(r'documentation[\s\w]+score:?\s*(0\.\d+|1\.0|1)', health_report, re.IGNORECASE)
                documentation_score = float(doc_score_match.group(1)) if doc_score_match else 0.5
                
                # Look for activity score
                activity_score_match = re.search(r'activity[\s\w]+score:?\s*(0\.\d+|1\.0|1)', health_report, re.IGNORECASE)
                activity_score = float(activity_score_match.group(1)) if activity_score_match else 0.5
                
                # Look for community score
                community_score_match = re.search(r'community[\s\w]+score:?\s*(0\.\d+|1\.0|1)', health_report, re.IGNORECASE)
                community_score = float(community_score_match.group(1)) if community_score_match else 0.5
                
                # Extract improvement suggestions using regex
                improvements_section_match = re.search(r'recommendations?:?([\s\S]+?)(?:\n#|\n$)', health_report, re.IGNORECASE)
                improvements_text = improvements_section_match.group(1) if improvements_section_match else ""
                
                # Parse bullet points as improvement suggestions
                improvements = []
                suggestion_matches = re.finditer(r'[*-]\s*([^\n]+)', improvements_text)
                for i, match in enumerate(suggestion_matches):
                    suggestion_text = match.group(1).strip()
                    # Categorize suggestions based on keywords
                    category = "general"
                    priority = "medium"
                    
                    if any(kw in suggestion_text.lower() for kw in ["document", "readme", "wiki", "comment"]):
                        category = "documentation"
                    elif any(kw in suggestion_text.lower() for kw in ["test", "coverage", "assert"]):
                        category = "testing"
                    elif any(kw in suggestion_text.lower() for kw in ["security", "vulnerability", "auth"]):
                        category = "security"
                        priority = "high"
                    elif any(kw in suggestion_text.lower() for kw in ["community", "contributor", "issue template"]):
                        category = "community"
                    elif any(kw in suggestion_text.lower() for kw in ["code quality", "refactor", "clean"]):
                        category = "code quality"
                    
                    improvements.append({
                        "category": category,
                        "priority": priority,
                        "suggestion": suggestion_text
                    })
            except Exception as parse_err:
                logger.warning(f"Error parsing structured data from health report: {parse_err}")
                # Use default values
                overall_score = 0.5
                documentation_score = 0.5
                activity_score = 0.5
                community_score = 0.5
                improvements = []
            
            # Create report object
            report = {
                "repository": f"{owner}/{repo}",
                "timestamp": time.time(),
                "health_score": overall_score,
                "documentation_score": documentation_score,
                "activity_score": activity_score,
                "community_score": community_score,
                "improvement_suggestions": improvements,
                "raw_report": health_report
            }
            
            # Create issue if requested
            issue = None
            if create_issue:
                issue_title = f"Repository Health Check: {overall_score:.2f}/1.00"
                issue_body = health_report
                
                # Create the issue
                issue_creation_task = f"""
                Create a GitHub issue in repository {owner}/{repo} with the following:
                Title: {issue_title}
                Body: 
                {issue_body}
                
                Labels: health-check, documentation
                """
                
                try:
                    issue_response = self.openai_client.chat.completions.create(
                        model="gpt-4o",  # Using GPT-4o for tool calling
                        tools=self.github_tools,
                        messages=[
                            {"role": "system", "content": "You are a GitHub automation assistant. Create issues with the exact content provided."},
                            {"role": "user", "content": issue_creation_task},
                        ],
                    )
                    
                    # Process the response
                    issue_result = self.composio_toolset.handle_tool_calls(issue_response)
                    
                    # Check if issue creation was successful
                    if "created" in issue_result.lower() and "error" not in issue_result.lower():
                        # Try to extract issue number from the response
                        import re
                        issue_number_match = re.search(r'#(\d+)', issue_result)
                        issue_number = int(issue_number_match.group(1)) if issue_number_match else None
                        
                        issue = {
                            "title": issue_title,
                            "body": issue_body,
                            "number": issue_number,
                            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_number}" if issue_number else None
                        }
                        report["issue"] = issue
                    else:
                        logger.error(f"Error creating health check issue: {issue_result}")
                except Exception as issue_err:
                    logger.error(f"Error creating health check issue: {issue_err}")
            
            return {
                "success": True,
                "health_check": report,
                "issue": issue
            }
        except Exception as e:
            logger.error(f"Error generating Composio health check report for {owner}/{repo}: {e}")
            
            # Fall back to parent implementation
            logger.info("Falling back to MCP implementation for health check report")
            return await super().generate_health_check_report(owner, repo, create_issue)

    async def create_webhook(
        self, 
        owner: str, 
        repo: str, 
        webhook_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a webhook for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            webhook_payload: Webhook configuration payload
            
        Returns:
            Webhook creation response
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "create_webhook", {
            "owner": owner,
            "repo": repo,
            "action": "Creating webhook"
        })
        
        try:
            logger.info(f"Creating webhook for {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/hooks"
            
            # Validate webhook payload
            required_fields = ["url", "content_type"]
            for field in required_fields:
                if field not in webhook_payload:
                    error_msg = f"Missing required field in webhook payload: {field}"
                    logger.error(error_msg)
                    self._end_operation(operation_id, success=False, error=error_msg)
                    return {"error": error_msg}
            
            # Ensure events is present (default to push if not)
            if "events" not in webhook_payload:
                webhook_payload["events"] = ["push"]
            
            if "config" not in webhook_payload:
                webhook_payload = {
                    "config": {
                        "url": webhook_payload["url"],
                        "content_type": webhook_payload.get("content_type", "json"),
                        "secret": webhook_payload.get("secret", ""),
                        "insecure_ssl": webhook_payload.get("insecure_ssl", "0")
                    },
                    "events": webhook_payload["events"],
                    "active": webhook_payload.get("active", True)
                }
            
            # Update progress
            self._update_operation(operation_id, progress=50, 
                                  status="Submitting webhook creation request")
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("POST", url, webhook_payload)
            else:
                response = await self.github.post(url, data=webhook_payload)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            if "error" in response:
                logger.error(f"Error creating webhook: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            self._end_operation(operation_id, success=True, result=response)
            logger.info(f"Successfully created webhook for {owner}/{repo}")
            return response
            
        except Exception as e:
            error_msg = f"Exception creating webhook: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    async def list_webhooks(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        List all webhooks for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of webhooks
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "list_webhooks", {
            "owner": owner,
            "repo": repo,
            "action": "Fetching webhooks"
        })
        
        try:
            logger.info(f"Listing webhooks for {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/hooks"
            
            # Check cache first if enabled
            cache_key = f"webhooks_{owner}_{repo}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self._end_operation(operation_id, success=True, result=cached_data)
                return cached_data
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("GET", url)
            else:
                response = await self.github.get(url)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            if "error" in response:
                logger.error(f"Error listing webhooks: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            # Cache the results if caching is enabled
            self._add_to_cache(cache_key, response)
            
            webhook_count = len(response) if isinstance(response, list) else 0
            logger.info(f"Retrieved {webhook_count} webhooks for {owner}/{repo}")
            
            self._end_operation(operation_id, success=True, result=response)
            return response
            
        except Exception as e:
            error_msg = f"Exception listing webhooks: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    async def delete_webhook(self, owner: str, repo: str, webhook_id: int) -> Dict[str, Any]:
        """
        Delete a webhook from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            webhook_id: ID of the webhook to delete
            
        Returns:
            Empty dictionary on success, error object on failure
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "delete_webhook", {
            "owner": owner,
            "repo": repo,
            "webhook_id": webhook_id,
            "action": "Deleting webhook"
        })
        
        try:
            logger.info(f"Deleting webhook {webhook_id} from {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/hooks/{webhook_id}"
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("DELETE", url)
            else:
                response = await self.github.delete(url)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            # Clear cache since it's now outdated
            cache_key = f"webhooks_{owner}_{repo}"
            self._remove_from_cache(cache_key)
            
            if "error" in response:
                logger.error(f"Error deleting webhook: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            logger.info(f"Successfully deleted webhook {webhook_id} from {owner}/{repo}")
            self._end_operation(operation_id, success=True)
            
            # Return empty dict on success (GitHub returns 204 No Content)
            return {}
            
        except Exception as e:
            error_msg = f"Exception deleting webhook: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    async def list_workflows(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        List GitHub Actions workflows for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dictionary with workflows information
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "list_workflows", {
            "owner": owner,
            "repo": repo,
            "action": "Fetching workflows"
        })
        
        try:
            logger.info(f"Listing workflows for {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/actions/workflows"
            
            # Check cache first if enabled
            cache_key = f"workflows_{owner}_{repo}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self._end_operation(operation_id, success=True, result=cached_data)
                return cached_data
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("GET", url)
            else:
                response = await self.github.get(url)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            if "error" in response:
                logger.error(f"Error listing workflows: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            # Cache the results if caching is enabled
            self._add_to_cache(cache_key, response)
            
            workflow_count = len(response.get("workflows", [])) if isinstance(response, dict) else 0
            logger.info(f"Retrieved {workflow_count} workflows for {owner}/{repo}")
            
            self._end_operation(operation_id, success=True, result=response)
            return response
            
        except Exception as e:
            error_msg = f"Exception listing workflows: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    async def get_workflow(self, owner: str, repo: str, workflow_id: str) -> Dict[str, Any]:
        """
        Get a specific GitHub Actions workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or file name
            
        Returns:
            Dictionary with workflow information
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "get_workflow", {
            "owner": owner,
            "repo": repo,
            "workflow_id": workflow_id,
            "action": "Fetching workflow details"
        })
        
        try:
            logger.info(f"Getting workflow {workflow_id} for {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}"
            
            # Check cache first if enabled
            cache_key = f"workflow_{owner}_{repo}_{workflow_id}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                self._end_operation(operation_id, success=True, result=cached_data)
                return cached_data
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("GET", url)
            else:
                response = await self.github.get(url)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            if "error" in response:
                logger.error(f"Error getting workflow: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            # Cache the results if caching is enabled
            self._add_to_cache(cache_key, response)
            
            logger.info(f"Successfully retrieved workflow {workflow_id} for {owner}/{repo}")
            
            self._end_operation(operation_id, success=True, result=response)
            return response
            
        except Exception as e:
            error_msg = f"Exception getting workflow: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    async def dispatch_workflow(
        self, 
        owner: str, 
        repo: str, 
        workflow_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger a GitHub Actions workflow.
        
        Args:
            owner: Repository owner
            repo: Repository name
            workflow_id: Workflow ID or file name
            payload: Dispatch payload with ref and inputs
            
        Returns:
            Dictionary with dispatch result
        """
        operation_id = str(uuid.uuid4())
        self._start_operation(operation_id, "dispatch_workflow", {
            "owner": owner,
            "repo": repo,
            "workflow_id": workflow_id,
            "action": "Triggering workflow"
        })
        
        try:
            logger.info(f"Dispatching workflow {workflow_id} for {owner}/{repo}")
            
            url = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
            
            # Validate payload
            if "ref" not in payload:
                error_msg = "Missing required 'ref' field in workflow dispatch payload"
                logger.error(error_msg)
                self._end_operation(operation_id, success=False, error=error_msg)
                return {"error": error_msg}
            
            # Make the API call
            if self.use_mcp:
                response = await self._make_github_api_request("POST", url, payload)
            else:
                response = await self.github.post(url, data=payload)
            
            # Update performance metrics
            self.performance_metrics["api_calls"] += 1
            
            # GitHub returns 204 No Content on success, so an empty response is expected
            if response and "error" in response:
                logger.error(f"Error dispatching workflow: {response['error']}")
                self.performance_metrics["api_errors"] += 1
                self._end_operation(operation_id, success=False, error=response["error"])
                return response
            
            logger.info(f"Successfully dispatched workflow {workflow_id} for {owner}/{repo}")
            
            self._end_operation(operation_id, success=True)
            return {"success": True, "message": f"Workflow {workflow_id} dispatched"}
            
        except Exception as e:
            error_msg = f"Exception dispatching workflow: {str(e)}"
            logger.error(error_msg)
            self.performance_metrics["api_errors"] += 1
            self._end_operation(operation_id, success=False, error=error_msg)
            return {"error": error_msg}
    
    # UI/UX and Progress Reporting Methods
    def register_progress_callback(self, callback_id: str, callback_fn: Callable) -> None:
        """
        Register a callback function to receive progress updates.
        
        Args:
            callback_id: Unique identifier for the callback
            callback_fn: Function to call with progress updates
        """
        self.progress_callbacks[callback_id] = callback_fn
        logger.debug(f"Registered progress callback: {callback_id}")
    
    def unregister_progress_callback(self, callback_id: str) -> None:
        """Remove a progress callback by its ID."""
        if callback_id in self.progress_callbacks:
            del self.progress_callbacks[callback_id]
            logger.debug(f"Unregistered progress callback: {callback_id}")
    
    def _start_operation(
        self, 
        operation_id: str, 
        operation_type: str, 
        details: Dict[str, Any]
    ) -> None:
        """
        Start tracking an operation for progress reporting.
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (e.g., "create_webhook")
            details: Operation details
        """
        self.active_operations[operation_id] = {
            "id": operation_id,
            "type": operation_type,
            "details": details,
            "start_time": time.time(),
            "progress": 0,
            "status": "started",
            "success": None,
            "error": None,
            "result": None
        }
        
        # Notify callbacks
        self._notify_progress(operation_id)
    
    def _update_operation(
        self, 
        operation_id: str, 
        progress: Optional[int] = None, 
        status: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update an operation's progress status.
        
        Args:
            operation_id: Unique identifier for the operation
            progress: Progress percentage (0-100)
            status: Status message
            details: Updated operation details
        """
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        if progress is not None:
            operation["progress"] = progress
        
        if status is not None:
            operation["status"] = status
        
        if details is not None:
            operation["details"].update(details)
        
        # Notify callbacks
        self._notify_progress(operation_id)
    
    def _end_operation(
        self, 
        operation_id: str, 
        success: bool, 
        error: Optional[str] = None,
        result: Optional[Any] = None
    ) -> None:
        """
        Mark an operation as complete.
        
        Args:
            operation_id: Unique identifier for the operation
            success: Whether the operation succeeded
            error: Error message if failed
            result: Operation result data
        """
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        operation["progress"] = 100
        operation["status"] = "completed" if success else "failed"
        operation["success"] = success
        operation["end_time"] = time.time()
        operation["duration"] = operation["end_time"] - operation["start_time"]
        
        if error:
            operation["error"] = error
        
        if result:
            operation["result"] = result
        
        # Notify callbacks
        self._notify_progress(operation_id)
        
        # Clean up completed operations after 5 minutes
        asyncio.create_task(self._cleanup_operation(operation_id))
    
    async def _cleanup_operation(self, operation_id: str) -> None:
        """Remove completed operation after delay."""
        await asyncio.sleep(300)  # 5 minutes
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]
    
    def _notify_progress(self, operation_id: str) -> None:
        """Notify all registered callbacks of operation progress."""
        if operation_id not in self.active_operations:
            return
        
        operation = self.active_operations[operation_id]
        
        for callback_id, callback_fn in self.progress_callbacks.items():
            try:
                callback_fn(operation)
            except Exception as e:
                logger.error(f"Error in progress callback {callback_id}: {e}")
    
    # Cache Management
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and is not expired."""
        if not self.cache_enabled or not self.cache:
            return None
        
        cache_entry = self.cache.get(key)
        if not cache_entry:
            self.cache_stats["misses"] += 1
            return None
        
        # Check if cache entry is expired
        if time.time() - cache_entry["timestamp"] > self.cache_ttl:
            # Expired
            self.cache_stats["misses"] += 1
            return None
        
        # Valid cache hit
        self.cache_stats["hits"] += 1
        return cache_entry["data"]
    
    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add or update cache entry."""
        if not self.cache_enabled or not self.cache:
            return
        
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
    
    def _remove_from_cache(self, key: str) -> None:
        """Remove entry from cache."""
        if not self.cache_enabled or not self.cache or key not in self.cache:
            return
        
        del self.cache[key]
    
    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear the entire cache.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.cache_enabled or not self.cache:
            return {"status": "cache_disabled"}
        
        cache_size = len(self.cache)
        self.cache.clear()
        self.cache_stats["last_cleared"] = time.time()
        
        return {
            "status": "cleared",
            "entries_removed": cache_size,
            "stats": self.cache_stats
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the bridge.
        
        Returns:
            Dictionary with performance statistics
        """
        # Calculate average response time
        avg_response_time = 0
        if self.performance_metrics["response_times"]:
            avg_response_time = sum(self.performance_metrics["response_times"]) / len(self.performance_metrics["response_times"])
        
        # Calculate error rate
        error_rate = 0
        if self.performance_metrics["api_calls"] > 0:
            error_rate = (self.performance_metrics["api_errors"] / self.performance_metrics["api_calls"]) * 100
        
        uptime = time.time() - self.performance_metrics["start_time"]
        
        metrics = {
            "api_calls": self.performance_metrics["api_calls"],
            "api_errors": self.performance_metrics["api_errors"],
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "uptime_seconds": round(uptime, 2),
            "active_operations": len(self.active_operations),
            "cache_stats": self.cache_stats if self.cache_enabled else {"status": "disabled"}
        }
        
        return metrics
    
    async def _make_github_api_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GitHub API request using MCP or direct API call.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            API response or error object
        """
        start_time = time.time()
        
        try:
            if self.use_mcp and self.mcp_url and self.mcp_key:
                # Use MCP for the request
                payload = {
                    "request": {
                        "method": method,
                        "url": f"https://api.github.com/{endpoint}",
                        "headers": {
                            "Authorization": f"Bearer {self.github_token}",
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28"
                        }
                    }
                }
                
                if data:
                    payload["request"]["data"] = data
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.mcp_url}/github/api",
                        headers={"Authorization": f"Bearer {self.mcp_key}"},
                        json=payload
                    ) as response:
                        response_time = int((time.time() - start_time) * 1000)
                        self.performance_metrics["response_times"].append(response_time)
                        
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.error(f"MCP GitHub API error: {response.status} - {error_text}")
                            return {"error": f"HTTP {response.status}: {error_text}"}
                        
                        return await response.json()
            else:
                # Make direct API call
                if method == "GET":
                    response = await self.github.get(endpoint)
                elif method == "POST":
                    response = await self.github.post(endpoint, data=data)
                elif method == "PUT":
                    response = await self.github.put(endpoint, data=data)
                elif method == "DELETE":
                    response = await self.github.delete(endpoint)
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
                
                response_time = int((time.time() - start_time) * 1000)
                self.performance_metrics["response_times"].append(response_time)
                
                return response
                
        except Exception as e:
            logger.error(f"Error making GitHub API request: {e}")
            return {"error": str(e)}


async def main():
    """Main function to demonstrate GitHub Composio Bridge usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 GitHub Composio Integration Bridge")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # check-connection command
    subparsers.add_parser("check-connection", help="Check GitHub connection status")
    
    # analyze-repo command
    analyze_repo_parser = subparsers.add_parser("analyze-repo", help="Analyze a GitHub repository")
    analyze_repo_parser.add_argument("--owner", help="Repository owner or organization")
    analyze_repo_parser.add_argument("--repo", help="Repository name")
    analyze_repo_parser.add_argument("--deep", action="store_true", help="Perform deep analysis")
    
    # health-check command
    health_check_parser = subparsers.add_parser("health-check", help="Generate repository health check report")
    health_check_parser.add_argument("--owner", help="Repository owner or organization")
    health_check_parser.add_argument("--repo", help="Repository name")
    health_check_parser.add_argument("--create-issue", action="store_true", help="Create an issue with the report")
    
    # star-repo command
    star_repo_parser = subparsers.add_parser("star-repo", help="Star a GitHub repository")
    star_repo_parser.add_argument("--owner", help="Repository owner or organization")
    star_repo_parser.add_argument("--repo", help="Repository name")
    
    # autonomous-cycle command
    cycle_parser = subparsers.add_parser("autonomous-cycle", help="Run autonomous improvement cycle")
    cycle_parser.add_argument("--owner", help="Repository owner or organization")
    cycle_parser.add_argument("--repo", help="Repository name")
    cycle_parser.add_argument("--components", nargs="+", help="Components to improve")
    cycle_parser.add_argument("--max", type=int, default=3, help="Maximum number of improvements")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize components
    from src.vot1.vot_mcp import VotModelControlProtocol
    from src.vot1.memory import MemoryManager
    from src.vot1.code_analyzer import create_analyzer
    from src.vot1.development_feedback_bridge import DevelopmentFeedbackBridge
    
    mcp = VotModelControlProtocol()
    memory_manager = MemoryManager()
    code_analyzer = create_analyzer(mcp=mcp)
    feedback_bridge = DevelopmentFeedbackBridge(mcp=mcp, code_analyzer=code_analyzer)
    
    # Create GitHub Composio bridge
    github_bridge = GitHubComposioBridge(
        mcp=mcp,
        memory_manager=memory_manager,
        code_analyzer=code_analyzer,
        feedback_bridge=feedback_bridge,
        default_owner=args.owner if hasattr(args, 'owner') else None,
        default_repo=args.repo if hasattr(args, 'repo') else None
    )
    
    # Execute command
    if args.command == "check-connection":
        is_connected = await github_bridge.check_connection()
        print(f"GitHub connection active: {is_connected}")
    
    elif args.command == "analyze-repo":
        result = await github_bridge.analyze_repository(
            args.owner, 
            args.repo, 
            deep_analysis=args.deep
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "health-check":
        result = await github_bridge.generate_health_check_report(
            args.owner,
            args.repo,
            create_issue=args.create_issue
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "star-repo":
        result = await github_bridge.star_repository(args.owner, args.repo)
        print(json.dumps(result, indent=2))
    
    elif args.command == "autonomous-cycle":
        result = await github_bridge.run_autonomous_improvement_cycle(
            components=args.components,
            owner=args.owner,
            repo=args.repo,
            max_improvements=args.max
        )
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main()) 