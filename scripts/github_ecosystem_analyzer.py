#!/usr/bin/env python3
"""
GitHub Ecosystem Analyzer with MCP Hybrid Automation

This script provides advanced GitHub repository analysis using the VOT1 system with MCP hybrid automation.
It leverages the power of multiple Claude models for different analysis tasks:
- Claude 3.7 Sonnet with extended thinking for deep code analysis and architecture recommendations
- Claude 3.5 Sonnet for basic metrics and quick insights

Features:
1. Deep repository structure analysis
2. Advanced code quality assessment
3. Cross-repository ecosystem analysis
4. Actionable improvement recommendations
5. Memory integration for contextual awareness across repositories
"""

import os
import sys
import argparse
import logging
import json
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.vot_mcp import VotModelControlProtocol
from src.vot1.memory import MemoryManager
from src.vot1.github_app_bridge import GitHubAppBridge
from src.vot1.github_composio_bridge import GitHubComposioBridge
from scripts.mcp_hybrid_automation import McpHybridAutomation
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'github_ecosystem_analyzer.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class GitHubEcosystemAnalyzer:
    """
    Advanced GitHub ecosystem analysis with MCP hybrid automation.
    
    This class provides enhanced repository analysis capabilities by leveraging
    the MCP hybrid automation system with extended thinking for complex analysis tasks.
    """
    
    def __init__(
        self,
        primary_model: str = "claude-3-7-sonnet-20240620",
        secondary_model: str = "claude-3-5-sonnet-20240620",
        use_extended_thinking: bool = True,
        max_thinking_tokens: int = 8000,
        memory_path: Optional[str] = None,
        github_token: Optional[str] = None,
        composio_api_key: Optional[str] = None,
        default_owner: Optional[str] = None,
        default_repo: Optional[str] = None,
        use_composio: bool = False
    ):
        """
        Initialize the GitHub Ecosystem Analyzer.
        
        Args:
            primary_model: Model for complex analysis tasks
            secondary_model: Model for simpler analysis tasks
            use_extended_thinking: Whether to use extended thinking for deep analysis
            max_thinking_tokens: Maximum thinking tokens when extended thinking is enabled
            memory_path: Path to store memory data
            github_token: GitHub API token for authentication
            composio_api_key: Composio API key for enhanced GitHub integration
            default_owner: Default repository owner
            default_repo: Default repository name
            use_composio: Whether to use Composio for enhanced GitHub interaction
        """
        # Initialize memory
        self.memory_path = memory_path or os.environ.get('VOT1_MEMORY_PATH', os.path.join(os.getcwd(), 'memory'))
        os.makedirs(self.memory_path, exist_ok=True)
        self.memory_manager = MemoryManager(memory_path=self.memory_path)
        logger.info(f"Initialized memory manager at {self.memory_path}")
        
        # Initialize MCP hybrid automation
        self.mcp_automation = McpHybridAutomation(
            primary_model=primary_model,
            secondary_model=secondary_model,
            use_extended_thinking=use_extended_thinking,
            max_thinking_tokens=max_thinking_tokens,
            memory_manager=self.memory_manager
        )
        
        # Initialize GitHub bridge
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        
        if use_composio and composio_api_key:
            self.github_bridge = GitHubComposioBridge(
                mcp=self.mcp_automation.mcp,
                memory_manager=self.memory_manager,
                default_owner=default_owner,
                default_repo=default_repo,
                composio_api_key=composio_api_key,
                model_name=primary_model
            )
            logger.info("Using GitHubComposioBridge for enhanced repository analysis")
        else:
            self.github_bridge = GitHubAppBridge(
                mcp=self.mcp_automation.mcp,
                memory_manager=self.memory_manager,
                default_owner=default_owner,
                default_repo=default_repo
            )
            logger.info("Using GitHubAppBridge for repository analysis")
        
        self.analyzed_repositories = set()
        logger.info(f"GitHub Ecosystem Analyzer initialized with {primary_model}/{secondary_model}")
        if use_extended_thinking:
            logger.info(f"Extended thinking enabled with {max_thinking_tokens} tokens")
    
    async def analyze_repository(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        deep_analysis: bool = True,
        use_composio: bool = False
    ) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of a GitHub repository.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            deep_analysis: Whether to perform deep analysis with the primary model
            use_composio: Whether to use the Composio bridge for enhanced analysis
            
        Returns:
            Dictionary with repository analysis results
        """
        # Switch GitHub bridge if requested
        original_bridge = None
        if use_composio and not isinstance(self.github_bridge, GitHubComposioBridge):
            logger.info(f"Temporarily switching to GitHubComposioBridge for enhanced analysis")
            original_bridge = self.github_bridge
            composio_api_key = os.environ.get("COMPOSIO_API_KEY")
            self.github_bridge = GitHubComposioBridge(
                mcp=self.mcp_automation.mcp,
                memory_manager=self.memory_manager,
                default_owner=owner,
                default_repo=repo,
                composio_api_key=composio_api_key
            )
        
        owner = owner or self.github_bridge.default_owner
        repo = repo or self.github_bridge.default_repo
        
        if not owner or not repo:
            # Restore original bridge if needed
            if original_bridge:
                self.github_bridge = original_bridge
            return {"error": "Repository owner and name are required", "success": False}
        
        repo_key = f"{owner}/{repo}"
        logger.info(f"Analyzing repository: {repo_key} (deep_analysis={deep_analysis}, use_composio={use_composio})")
        
        try:
            # First, get basic repository analysis from the GitHub bridge
            repo_analysis = await self.github_bridge.analyze_repository(owner, repo, deep_analysis)
            
            # If deep analysis is requested, perform enhanced analysis with MCP primary model
            if deep_analysis:
                enhanced_analysis = await self._perform_enhanced_analysis(owner, repo, repo_analysis)
                repo_analysis["enhanced_analysis"] = enhanced_analysis
            
            # Store the repository in our analyzed set
            self.analyzed_repositories.add(repo_key)
            
            # Store the analysis in memory for future reference
            self._store_analysis_in_memory(owner, repo, repo_analysis)
            
            # Restore original bridge if needed
            if original_bridge:
                self.github_bridge = original_bridge
            
            return repo_analysis
        
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_key}: {e}")
            # Restore original bridge if needed
            if original_bridge:
                self.github_bridge = original_bridge
            return {
                "error": f"Analysis failed: {str(e)}",
                "success": False
            }
    
    async def _perform_enhanced_analysis(
        self,
        owner: str,
        repo: str,
        basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform enhanced analysis using the MCP primary model with extended thinking.
        
        Args:
            owner: Repository owner
            repo: Repository name
            basic_analysis: Basic analysis results from the GitHub bridge
            
        Returns:
            Enhanced analysis results
        """
        logger.info(f"Performing enhanced analysis for {owner}/{repo} with extended thinking")
        
        # Structure input for the model
        analysis_prompt = f"""
        Perform a deep analysis of the GitHub repository {owner}/{repo} based on the following data:
        
        {json.dumps(basic_analysis, indent=2)}
        
        Please provide comprehensive insights including:
        
        1. Architecture Assessment:
           - Evaluate the overall architecture of the repository
           - Identify architectural patterns and their effectiveness
           - Recommend architectural improvements
        
        2. Code Quality Deep Dive:
           - Analyze code quality beyond surface metrics
           - Identify potential technical debt areas
           - Suggest refactoring priorities
        
        3. Development Workflow Analysis:
           - Analyze commit patterns and developer workflows
           - Identify bottlenecks in the development process
           - Recommend workflow optimizations
        
        4. Documentation and Knowledge Management:
           - Evaluate documentation completeness and quality
           - Identify knowledge gaps
           - Recommend documentation improvements
        
        5. Future Development Roadmap:
           - Based on the analysis, recommend a prioritized roadmap for improvements
           - Suggest specific action items with expected impact
        
        Focus on providing actionable, strategic recommendations rather than surface-level observations.
        """
        
        # Use the primary model with extended thinking for this complex analysis
        result = self.mcp_automation.process_with_optimal_model(
            prompt=analysis_prompt,
            task_complexity="complex",  # Force using primary model
            system="You are an expert software architect and engineering lead performing a deep analysis of a GitHub repository. Your analysis should be comprehensive, insightful, and actionable.",
            max_tokens=4096,
            temperature=0.7,
            use_memory=True  # Use memory for context
        )
        
        # Extract content from result
        if isinstance(result, dict):
            analysis_text = result.get("content", "")
        else:
            analysis_text = result
        
        # Try to parse structured data if the response is in JSON format
        try:
            # Look for JSON within the text
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', analysis_text)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                # Return as structured text if not JSON
                return {
                    "analysis_text": analysis_text,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Could not parse enhanced analysis as JSON: {e}")
            return {
                "analysis_text": analysis_text,
                "timestamp": time.time()
            }
    
    def _store_analysis_in_memory(self, owner: str, repo: str, analysis: Dict[str, Any]) -> None:
        """
        Store repository analysis in memory for future reference.
        
        Args:
            owner: Repository owner
            repo: Repository name
            analysis: Analysis results
        """
        repo_key = f"{owner}/{repo}"
        try:
            # Create a summary of the analysis
            summary = f"Analysis of GitHub repository {repo_key}"
            if "description" in analysis:
                summary += f": {analysis['description']}"
            
            # Store the full analysis
            memory_id = self.memory_manager.add_semantic_memory(
                content=json.dumps(analysis, indent=2),
                metadata={
                    "type": "github_analysis",
                    "repository": repo_key,
                    "timestamp": time.time(),
                    "summary": summary
                }
            )
            logger.info(f"Stored analysis of {repo_key} in memory with ID: {memory_id}")
            
            # Store the memory ID in the analysis result for reference
            if isinstance(analysis, dict):
                analysis["memory_id"] = memory_id
            
        except Exception as e:
            logger.error(f"Error storing analysis in memory: {e}")
    
    async def analyze_ecosystem(
        self,
        repos: List[Dict[str, str]],
        deep_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze multiple repositories as an ecosystem.
        
        Args:
            repos: List of repositories to analyze, each with 'owner' and 'repo' keys
            deep_analysis: Whether to perform deep analysis on each repository
            
        Returns:
            Ecosystem analysis results
        """
        logger.info(f"Starting ecosystem analysis for {len(repos)} repositories")
        
        # Analyze each repository
        analyses = {}
        for repo_info in repos:
            owner = repo_info.get("owner")
            repo = repo_info.get("repo")
            if owner and repo:
                repo_key = f"{owner}/{repo}"
                analyses[repo_key] = await self.analyze_repository(owner, repo, deep_analysis)
                
                # Add a small delay to avoid rate limiting
                await asyncio.sleep(1)
        
        # Perform ecosystem-level analysis with the primary model
        ecosystem_analysis = await self._analyze_ecosystem_relationships(analyses)
        
        result = {
            "repository_analyses": analyses,
            "ecosystem_analysis": ecosystem_analysis,
            "timestamp": time.time(),
            "repositories_analyzed": len(analyses)
        }
        
        # Store ecosystem analysis in memory
        self._store_ecosystem_analysis_in_memory(result)
        
        return result
    
    async def _analyze_ecosystem_relationships(self, analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationships and patterns across multiple repositories.
        
        Args:
            analyses: Dictionary of repository analyses
            
        Returns:
            Ecosystem-level analysis
        """
        logger.info(f"Performing ecosystem-level analysis for {len(analyses)} repositories")
        
        # Structure the input for the model
        repo_summaries = {}
        for repo_key, analysis in analyses.items():
            # Extract key information for each repository
            summary = {
                "name": repo_key,
                "description": analysis.get("description", ""),
                "language": analysis.get("language", ""),
                "stars": analysis.get("stargazers_count", 0),
                "forks": analysis.get("forks_count", 0),
                "issues": analysis.get("open_issues_count", 0),
                "updated_at": analysis.get("updated_at", ""),
                "topics": analysis.get("topics", [])
            }
            repo_summaries[repo_key] = summary
        
        ecosystem_prompt = f"""
        Analyze the following GitHub repositories as an ecosystem:
        
        {json.dumps(repo_summaries, indent=2)}
        
        Please provide a comprehensive ecosystem analysis including:
        
        1. Common Patterns and Practices:
           - Identify common architectural patterns across repositories
           - Identify shared development practices
           - Highlight consistency or inconsistency in approaches
        
        2. Dependency and Relationship Analysis:
           - Identify potential dependencies between repositories
           - Analyze how these repositories might interact
           - Suggest integration improvements
        
        3. Knowledge and Technology Silos:
           - Identify specialized knowledge areas
           - Detect technology silos or fragmentation
           - Recommend knowledge sharing improvements
        
        4. Ecosystem Health Assessment:
           - Evaluate the overall health of the ecosystem
           - Identify systemic issues affecting multiple repositories
           - Recommend ecosystem-wide improvements
        
        5. Strategic Recommendations:
           - Provide strategic recommendations for the ecosystem
           - Suggest prioritized actions to improve the entire ecosystem
           - Recommend specific integration points or consolidation opportunities
        
        Focus on system-level insights rather than individual repository details.
        """
        
        # Use the primary model with extended thinking for this very complex analysis
        result = self.mcp_automation.process_with_optimal_model(
            prompt=ecosystem_prompt,
            task_complexity="complex",  # Force using primary model
            system="You are an expert software architect and engineering lead performing an ecosystem analysis of multiple GitHub repositories. Your analysis should focus on system-level patterns, relationships, and strategic recommendations.",
            max_tokens=4096,
            temperature=0.7,
            use_memory=True  # Use memory for context
        )
        
        # Extract content from result
        if isinstance(result, dict):
            analysis_text = result.get("content", "")
        else:
            analysis_text = result
        
        # Try to parse structured data if the response is in JSON format
        try:
            # Look for JSON within the text
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', analysis_text)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            else:
                # Return as structured text if not JSON
                return {
                    "analysis_text": analysis_text,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Could not parse ecosystem analysis as JSON: {e}")
            return {
                "analysis_text": analysis_text,
                "timestamp": time.time()
            }
    
    def _store_ecosystem_analysis_in_memory(self, ecosystem_analysis: Dict[str, Any]) -> None:
        """
        Store ecosystem analysis in memory for future reference.
        
        Args:
            ecosystem_analysis: Ecosystem analysis results
        """
        try:
            # Create a summary of the repositories analyzed
            repo_list = list(ecosystem_analysis.get("repository_analyses", {}).keys())
            summary = f"Ecosystem analysis of {len(repo_list)} GitHub repositories: {', '.join(repo_list[:5])}"
            if len(repo_list) > 5:
                summary += f" and {len(repo_list) - 5} more"
            
            # Store the full analysis
            self.memory_manager.add_semantic_memory(
                content=json.dumps(ecosystem_analysis, indent=2),
                metadata={
                    "type": "github_ecosystem_analysis",
                    "repositories": repo_list,
                    "timestamp": time.time(),
                    "summary": summary
                }
            )
            logger.info(f"Stored ecosystem analysis in memory")
            
        except Exception as e:
            logger.error(f"Error storing ecosystem analysis in memory: {e}")
    
    async def generate_improvement_plan(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ecosystem: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an improvement plan for a repository or ecosystem.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ecosystem: Whether to generate an ecosystem-wide improvement plan
            
        Returns:
            Dictionary with improvement plan
        """
        try:
            if ecosystem:
                # Generate ecosystem-wide improvement plan
                logger.info("Generating ecosystem improvement plan")
                return await self._generate_ecosystem_improvement_plan()
            else:
                # Generate repository-specific improvement plan
                owner = owner or self.github_bridge.default_owner
                repo = repo or self.github_bridge.default_repo
                
                if not owner or not repo:
                    return {"error": "Repository owner and name are required", "success": False}
                
                repo_key = f"{owner}/{repo}"
                logger.info(f"Generating detailed improvement plan for {repo_key}")
                
                # Automatically analyze the repository if we don't have previous analysis
                if repo_key not in self.analyzed_repositories:
                    logger.info(f"No previous analysis found for {repo_key}, running analysis first")
                    await self.analyze_repository(owner, repo, deep_analysis=True)
                
                return await self._generate_repository_improvement_plan(owner, repo)
                
        except Exception as e:
            logger.error(f"Error generating improvement plan: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def _generate_repository_improvement_plan(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Generate a detailed improvement plan for a single repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository improvement plan
        """
        repo_key = f"{owner}/{repo}"
        logger.info(f"Generating detailed improvement plan for {repo_key}")
        
        # Search for previous analysis in memory
        memories = self.memory_manager.search_memories(
            query=f"github_analysis {repo_key}",
            limit=1,
            memory_types=["github_analysis"]
        )
        
        # If no memories found, try searching by repository field
        if not memories:
            logger.info(f"No memories found with query 'github_analysis {repo_key}', trying metadata search")
            all_memories = self.memory_manager.search_memories(
                query="github_analysis",
                limit=10,
                memory_types=["github_analysis"]
            )
            
            # Filter memories by repository field
            memories = [
                memory for memory in all_memories 
                if memory.get("metadata", {}).get("repository") == repo_key
            ]
        
        analysis_data = {}
        if memories:
            # Extract the analysis data from memory
            try:
                memory_content = memories[0].get("content", "{}")
                analysis_data = json.loads(memory_content)
                logger.info(f"Found analysis data for {repo_key} in memory")
            except Exception as e:
                logger.warning(f"Could not parse memory content as JSON: {e}")
        
        if not analysis_data:
            return {
                "error": f"No analysis data found for {repo_key}",
                "success": False
            }
        
        # Generate improvement plan using the primary model
        improvement_prompt = f"""
        Generate a detailed, actionable improvement plan for the GitHub repository {repo_key} based on the following analysis:
        
        {json.dumps(analysis_data, indent=2)}
        
        The improvement plan should include:
        
        1. Executive Summary
           - Brief overview of the repository's current state
           - Key improvement areas and expected benefits
        
        2. Prioritized Improvement Actions
           - High-priority actions (immediate term)
           - Medium-priority actions (mid-term)
           - Low-priority actions (long-term)
        
        3. Implementation Details for Each Action
           - Detailed description of the action
           - Expected effort (story points or time estimate)
           - Technical approach and considerations
           - Expected outcome and success metrics
        
        4. Roadmap Timeline
           - Suggested implementation sequence
           - Dependencies between actions
           - Milestones and checkpoints
        
        5. Risk Assessment
           - Potential risks and challenges
           - Mitigation strategies
        
        The plan should be specific, actionable, and tailored to this repository's unique characteristics.
        """
        
        # Use the primary model with extended thinking for this complex task
        result = self.mcp_automation.process_with_optimal_model(
            prompt=improvement_prompt,
            task_complexity="complex",  # Force using primary model
            system="You are an expert software architect and engineering lead creating an improvement plan for a GitHub repository. Your plan should be comprehensive, specific, actionable, and realistic.",
            max_tokens=4096,
            temperature=0.7,
            use_memory=True  # Use memory for context
        )
        
        # Extract content from result
        if isinstance(result, dict):
            plan_text = result.get("content", "")
        else:
            plan_text = result
            
        # Store the improvement plan in memory
        self._store_improvement_plan_in_memory(owner, repo, plan_text)
            
        return {
            "repository": repo_key,
            "improvement_plan": plan_text,
            "timestamp": time.time(),
            "success": True
        }
    
    async def _generate_ecosystem_improvement_plan(self) -> Dict[str, Any]:
        """
        Generate a detailed improvement plan for the entire ecosystem.
        
        Returns:
            Ecosystem improvement plan
        """
        logger.info(f"Generating ecosystem improvement plan for {len(self.analyzed_repositories)} repositories")
        
        # Search for previous ecosystem analysis in memory
        memories = self.memory_manager.search_memories(
            query="github_ecosystem_analysis",
            limit=1,
            memory_types=["github_ecosystem_analysis"]
        )
        
        ecosystem_data = {}
        if memories:
            # Extract the ecosystem data from memory
            try:
                memory_content = memories[0].get("content", "{}")
                ecosystem_data = json.loads(memory_content)
            except Exception as e:
                logger.warning(f"Could not parse memory content as JSON: {e}")
        
        if not ecosystem_data:
            return {
                "error": "No ecosystem analysis data found",
                "success": False
            }
        
        # Generate ecosystem improvement plan using the primary model
        improvement_prompt = f"""
        Generate a comprehensive ecosystem improvement plan for the following GitHub repositories:
        
        {json.dumps(list(self.analyzed_repositories), indent=2)}
        
        Based on the ecosystem analysis:
        
        {json.dumps(ecosystem_data.get("ecosystem_analysis", {}), indent=2)}
        
        The ecosystem improvement plan should include:
        
        1. Executive Summary
           - Overview of the current ecosystem state
           - Key system-level improvement areas
        
        2. Cross-Repository Standardization
           - Code style and conventions
           - Architecture patterns
           - Documentation formats
           - Development workflows
        
        3. Integration and Dependency Management
           - Repository dependencies and interactions
           - API standardization
           - Shared libraries and utilities
        
        4. Knowledge Sharing and Documentation
           - Cross-repository documentation
           - Knowledge transfer mechanisms
           - Training and onboarding
        
        5. System-Level Improvements
           - Infrastructure and CI/CD
           - Monitoring and observability
           - Security practices
           - Performance optimizations
        
        6. Implementation Roadmap
           - Phased implementation approach
           - Key milestones and dependencies
           - Resource allocation recommendations
        
        7. Governance and Maintenance
           - Ownership and maintenance model
           - Decision-making processes
           - Long-term sustainability
        
        The plan should address system-level concerns rather than just individual repository improvements.
        """
        
        # Use the primary model with extended thinking for this complex task
        result = self.mcp_automation.process_with_optimal_model(
            prompt=improvement_prompt,
            task_complexity="complex",  # Force using primary model
            system="You are an expert software architect and engineering lead creating a system-level improvement plan for a GitHub repository ecosystem. Your plan should address cross-repository concerns, standardization, and system-level optimizations.",
            max_tokens=4096,
            temperature=0.7,
            use_memory=True  # Use memory for context
        )
        
        # Extract content from result
        if isinstance(result, dict):
            plan_text = result.get("content", "")
        else:
            plan_text = result
            
        # Store the ecosystem improvement plan in memory
        self._store_ecosystem_improvement_plan_in_memory(plan_text)
            
        return {
            "repositories": list(self.analyzed_repositories),
            "ecosystem_improvement_plan": plan_text,
            "timestamp": time.time(),
            "success": True
        }
    
    def _store_improvement_plan_in_memory(self, owner: str, repo: str, plan: str) -> None:
        """
        Store repository improvement plan in memory.
        
        Args:
            owner: Repository owner
            repo: Repository name
            plan: Improvement plan text
        """
        repo_key = f"{owner}/{repo}"
        try:
            self.memory_manager.add_semantic_memory(
                content=plan,
                metadata={
                    "type": "improvement_plan",
                    "repository": repo_key,
                    "timestamp": time.time(),
                    "summary": f"Improvement plan for GitHub repository {repo_key}"
                }
            )
            logger.info(f"Stored improvement plan for {repo_key} in memory")
            
        except Exception as e:
            logger.error(f"Error storing improvement plan in memory: {e}")
    
    def _store_ecosystem_improvement_plan_in_memory(self, plan: str) -> None:
        """
        Store ecosystem improvement plan in memory.
        
        Args:
            plan: Ecosystem improvement plan text
        """
        try:
            repo_list = list(self.analyzed_repositories)
            self.memory_manager.add_semantic_memory(
                content=plan,
                metadata={
                    "type": "ecosystem_improvement_plan",
                    "repositories": repo_list,
                    "timestamp": time.time(),
                    "summary": f"Ecosystem improvement plan for {len(repo_list)} GitHub repositories"
                }
            )
            logger.info(f"Stored ecosystem improvement plan in memory")
            
        except Exception as e:
            logger.error(f"Error storing ecosystem improvement plan in memory: {e}")
            
    async def export_analysis_report(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        ecosystem: bool = False,
        format: str = "markdown",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export analysis results as a formatted report.
        
        Args:
            owner: Repository owner or organization
            repo: Repository name
            ecosystem: Whether to export an ecosystem report
            format: Report format ('markdown', 'json', or 'html')
            output_path: Path to save the report
            
        Returns:
            Dictionary with export result information
        """
        if ecosystem:
            report_type = "ecosystem"
            report_content = await self._generate_ecosystem_report(format)
            filename = f"ecosystem_analysis_report"
        else:
            # Ensure we have owner and repo
            owner = owner or self.github_bridge.default_owner
            repo = repo or self.github_bridge.default_repo
            
            if not owner or not repo:
                return {"error": "Repository owner and name are required", "success": False}
            
            repo_key = f"{owner}/{repo}"
            report_type = "repository"
            report_content = await self._generate_repository_report(owner, repo, format)
            filename = f"{owner}_{repo}_analysis_report"
        
        # Determine file extension
        if format == "json":
            ext = "json"
        elif format == "html":
            ext = "html"
        else:  # default to markdown
            ext = "md"
            format = "markdown"
        
        # Save the report
        if output_path:
            os.makedirs(output_path, exist_ok=True)
            file_path = os.path.join(output_path, f"{filename}.{ext}")
        else:
            output_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, f"{filename}.{ext}")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Exported {report_type} report to {file_path}")
            
            return {
                "success": True,
                "report_type": report_type,
                "format": format,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error exporting {report_type} report: {e}")
            return {
                "error": f"Export failed: {str(e)}",
                "success": False
            }
    
    async def _generate_repository_report(self, owner: str, repo: str, format: str) -> str:
        """
        Generate a formatted report for a single repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            format: Report format
            
        Returns:
            Formatted report content
        """
        repo_key = f"{owner}/{repo}"
        
        # Search for previous analysis and improvement plan in memory
        analysis_memories = self.memory_manager.search_memories(
            query=f"github_analysis {repo_key}",
            limit=1,
            memory_types=["github_analysis"]
        )
        
        plan_memories = self.memory_manager.search_memories(
            query=f"improvement_plan {repo_key}",
            limit=1,
            memory_types=["improvement_plan"]
        )
        
        analysis_data = {}
        if analysis_memories:
            try:
                memory_content = analysis_memories[0].get("content", "{}")
                analysis_data = json.loads(memory_content)
            except Exception as e:
                logger.warning(f"Could not parse analysis memory content as JSON: {e}")
        
        improvement_plan = ""
        if plan_memories:
            improvement_plan = plan_memories[0].get("content", "")
        
        # Generate report using the secondary model (for efficiency)
        report_prompt = f"""
        Generate a comprehensive analysis report for the GitHub repository {repo_key}.
        
        Include the following information:
        
        1. Repository Overview
        2. Key Metrics and Statistics
        3. Code Quality Assessment
        4. Architecture Analysis
        5. Development Workflow Insights
        6. Improvement Recommendations
        
        Format the report in {format} format.
        
        Use the following data for the report:
        
        Analysis Data:
        {json.dumps(analysis_data, indent=2)}
        
        Improvement Plan:
        {improvement_plan}
        """
        
        # Use the secondary model for report generation
        result = self.mcp_automation.process_with_optimal_model(
            prompt=report_prompt,
            task_complexity="medium",  # Use secondary model
            system=f"You are an expert software analyst creating a {format} report about a GitHub repository. Your report should be well-structured, comprehensive, and visually appealing in {format} format.",
            max_tokens=3072,
            temperature=0.7,
            use_memory=True
        )
        
        # Extract content from result
        if isinstance(result, dict):
            report_content = result.get("content", "")
        else:
            report_content = result
        
        return report_content
    
    async def _generate_ecosystem_report(self, format: str) -> str:
        """
        Generate a formatted report for the repository ecosystem.
        
        Args:
            format: Report format
            
        Returns:
            Formatted report content
        """
        # Search for previous ecosystem analysis and improvement plan in memory
        eco_analysis_memories = self.memory_manager.search_memories(
            query="github_ecosystem_analysis",
            limit=1,
            memory_types=["github_ecosystem_analysis"]
        )
        
        eco_plan_memories = self.memory_manager.search_memories(
            query="ecosystem_improvement_plan",
            limit=1,
            memory_types=["ecosystem_improvement_plan"]
        )
        
        ecosystem_data = {}
        if eco_analysis_memories:
            try:
                memory_content = eco_analysis_memories[0].get("content", "{}")
                ecosystem_data = json.loads(memory_content)
            except Exception as e:
                logger.warning(f"Could not parse ecosystem analysis memory content as JSON: {e}")
        
        ecosystem_plan = ""
        if eco_plan_memories:
            ecosystem_plan = eco_plan_memories[0].get("content", "")
        
        # Generate report using the secondary model (for efficiency)
        report_prompt = f"""
        Generate a comprehensive ecosystem analysis report for the following GitHub repositories:
        
        {json.dumps(list(self.analyzed_repositories), indent=2)}
        
        Include the following information:
        
        1. Ecosystem Overview
        2. Repository Summaries
        3. Cross-Repository Patterns and Relationships
        4. System-Level Health Assessment
        5. Knowledge and Technology Distribution
        6. Strategic Improvement Recommendations
        
        Format the report in {format} format.
        
        Use the following data for the report:
        
        Ecosystem Analysis Data:
        {json.dumps(ecosystem_data, indent=2)}
        
        Ecosystem Improvement Plan:
        {ecosystem_plan}
        """
        
        # Use the secondary model for report generation
        result = self.mcp_automation.process_with_optimal_model(
            prompt=report_prompt,
            task_complexity="medium",  # Use secondary model
            system=f"You are an expert software ecosystem analyst creating a {format} report about multiple GitHub repositories. Your report should be well-structured, focus on system-level insights, and be visually appealing in {format} format.",
            max_tokens=3072,
            temperature=0.7,
            use_memory=True
        )
        
        # Extract content from result
        if isinstance(result, dict):
            report_content = result.get("content", "")
        else:
            report_content = result
        
        return report_content


async def main():
    """Run the GitHub Ecosystem Analyzer."""
    parser = argparse.ArgumentParser(description="GitHub Ecosystem Analyzer with MCP Hybrid Automation")
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--repos-file", help="JSON file containing multiple repositories to analyze")
    parser.add_argument("--deep-analysis", action="store_true", help="Perform deep analysis with the primary model")
    parser.add_argument("--ecosystem", action="store_true", help="Perform ecosystem analysis across repositories")
    parser.add_argument("--generate-plan", action="store_true", help="Generate improvement plan")
    parser.add_argument("--export-report", action="store_true", help="Export analysis report")
    parser.add_argument("--report-format", choices=["markdown", "json", "html"], default="markdown", help="Report format")
    parser.add_argument("--output-path", help="Path to save report")
    parser.add_argument("--memory-path", help="Path to memory storage")
    parser.add_argument("--use-composio", action="store_true", help="Use Composio for enhanced GitHub integration")
    parser.add_argument("--max-thinking-tokens", type=int, default=8000, help="Maximum thinking tokens")
    parser.add_argument("--disable-extended-thinking", action="store_true", help="Disable extended thinking for deep analysis")
    
    args = parser.parse_args()
    
    # Initialize the analyzer
    analyzer = GitHubEcosystemAnalyzer(
        use_extended_thinking=not args.disable_extended_thinking,
        max_thinking_tokens=args.max_thinking_tokens,
        memory_path=args.memory_path,
        default_owner=args.owner,
        default_repo=args.repo,
        use_composio=args.use_composio
    )
    
    result = None
    
    # Process based on arguments
    if args.repos_file and args.ecosystem:
        # Analyze multiple repositories as an ecosystem
        with open(args.repos_file, 'r') as f:
            repos = json.load(f)
        result = await analyzer.analyze_ecosystem(repos, args.deep_analysis)
    elif args.owner and args.repo:
        # Analyze a single repository
        result = await analyzer.analyze_repository(args.owner, args.repo, args.deep_analysis, args.use_composio)
    
    if result and args.generate_plan:
        if args.ecosystem:
            plan = await analyzer.generate_improvement_plan(ecosystem=True)
        else:
            plan = await analyzer.generate_improvement_plan(args.owner, args.repo, False)
        print(json.dumps(plan, indent=2))
    
    if result and args.export_report:
        if args.ecosystem:
            report = await analyzer.export_analysis_report(ecosystem=True, format=args.report_format, output_path=args.output_path)
        else:
            report = await analyzer.export_analysis_report(args.owner, args.repo, False, args.report_format, args.output_path)
        print(json.dumps(report, indent=2))
    
    # Print result summary if not already printed
    if result and not (args.generate_plan or args.export_report):
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 