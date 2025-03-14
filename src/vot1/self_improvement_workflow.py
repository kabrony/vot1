#!/usr/bin/env python3
"""
VOT1 Self-Improvement Workflow

This module implements an advanced self-improvement workflow for the VOT1 system,
enabling agents to enhance the THREE.js visualization and improve their own code.
The workflow leverages OWL reasoning, enhanced memory management, and integrates with
the latest AI models including Claude 3.7 Sonnet and Perplexity.

Key features:
1. OWL reasoning integration for semantic understanding of code
2. Memory-enhanced agent capabilities
3. THREE.js visualization improvement pipeline
4. Self-improvement of agent code
5. GitHub integration for version control
6. Hybrid AI model approach (Claude 3.7 + Perplexity)
"""

import os
import json
import logging
import time
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import VOT1 modules
try:
    from vot1.vot_mcp import VotModelControlProtocol
    from vot1.memory import MemoryManager, VectorStore
    from vot1.owl_reasoning import OWLReasoningEngine
    from vot1.perplexity_client import PerplexityClient
except ImportError as e:
    logger.error(f"Failed to import VOT1 modules: {e}")
    logger.error("Please ensure VOT1 is properly installed")
    sys.exit(1)


class SelfImprovementWorkflow:
    """
    Orchestrates self-improvement workflows for VOT1 agents.
    
    This class provides capabilities for agents to analyze, enhance, and improve
    their own code, particularly focusing on the THREE.js visualization module
    and other core components.
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        owl_engine: Optional[OWLReasoningEngine] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        github_owner: Optional[str] = None,
        vector_model: str = "sentence-transformers/all-mpnet-base-v2",
        max_thinking_tokens: int = 4096,
        use_perplexity: bool = True,
        workspace_dir: Optional[str] = None
    ):
        """
        Initialize the self-improvement workflow.
        
        Args:
            memory_manager: Memory manager instance or None to create a new one
            owl_engine: OWL reasoning engine or None to create a new one
            github_token: GitHub API token for repository integration
            github_repo: GitHub repository name
            github_owner: GitHub repository owner
            vector_model: Model name for vector embeddings
            max_thinking_tokens: Maximum tokens to use for thinking stream
            use_perplexity: Whether to use Perplexity for web searches
            workspace_dir: Directory containing the codebase
        """
        # Set up workspace directory
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        logger.info(f"Using workspace directory: {self.workspace_dir}")
        
        # Initialize memory management
        if memory_manager is None:
            vector_store = VectorStore(
                model_name=vector_model,
                storage_path=str(self.workspace_dir / "memory" / "vector_store.db")
            )
            self.memory_manager = MemoryManager(
                vector_store=vector_store,
                memory_path=str(self.workspace_dir / "memory")
            )
            logger.info("Initialized new memory manager")
        else:
            self.memory_manager = memory_manager
            logger.info("Using provided memory manager")
        
        # Initialize OWL reasoning engine
        if owl_engine is None:
            ontology_path = str(self.workspace_dir / "owl" / "vot1_ontology.owl")
            self.owl_engine = OWLReasoningEngine(
                ontology_path=ontology_path,
                memory_manager=self.memory_manager,
                embedding_model=vector_model
            )
            logger.info(f"Initialized new OWL reasoning engine with ontology: {ontology_path}")
        else:
            self.owl_engine = owl_engine
            logger.info("Using provided OWL reasoning engine")
        
        # Set up GitHub integration
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.github_repo = github_repo or os.environ.get("GITHUB_REPO")
        self.github_owner = github_owner or os.environ.get("GITHUB_OWNER")
        self.github_enabled = bool(self.github_token and self.github_repo and self.github_owner)
        
        if self.github_enabled:
            logger.info(f"GitHub integration enabled for {self.github_owner}/{self.github_repo}")
        else:
            logger.warning("GitHub integration not configured or missing credentials")
        
        # Initialize MCP for multiple AI models
        tools = self._create_tool_definitions()
        self.mcp = VotModelControlProtocol(
            primary_provider=VotModelControlProtocol.PROVIDER_ANTHROPIC,
            primary_model="claude-3-7-sonnet-20240620",  # Latest Sonnet model
            secondary_provider=VotModelControlProtocol.PROVIDER_PERPLEXITY,
            secondary_model="pplx-70b-online",  # Latest Perplexity model
            tools=tools,
            memory_manager=self.memory_manager,
            execution_mode=VotModelControlProtocol.MODE_STREAMING,
            config={
                "max_thinking_tokens": max_thinking_tokens,
                "use_hybrid_approach": True,
                "enable_web_search": use_perplexity
            }
        )
        logger.info(f"Initialized VotModelControlProtocol with max thinking tokens: {max_thinking_tokens}")
        
        # Register tool handlers
        self._register_tool_handlers()
    
    def _create_tool_definitions(self) -> List[Dict[str, Any]]:
        """Create tool definitions for the MCP."""
        return [
            {
                "name": "search_codebase",
                "description": "Search the VOT1 codebase for specific patterns or functionality",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "file_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "File types to search (.py, .js, etc.)"
                    }
                }
            },
            {
                "name": "analyze_code",
                "description": "Analyze a section of code to understand its structure and functionality",
                "parameters": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to analyze"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line number"
                    }
                }
            },
            {
                "name": "modify_code",
                "description": "Modify code to implement improvements",
                "parameters": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to modify"
                    },
                    "code_changes": {
                        "type": "string",
                        "description": "New code to replace the specified section"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line number"
                    }
                }
            },
            {
                "name": "commit_changes",
                "description": "Commit changes to GitHub",
                "parameters": {
                    "commit_message": {
                        "type": "string",
                        "description": "Commit message"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to commit"
                    }
                }
            }
        ]
    
    def _register_tool_handlers(self):
        """Register handlers for MCP tools."""
        self.mcp.register_tool("search_codebase", self._handle_search_codebase)
        self.mcp.register_tool("analyze_code", self._handle_analyze_code)
        self.mcp.register_tool("modify_code", self._handle_modify_code)
        self.mcp.register_tool("commit_changes", self._handle_commit_changes)
    
    def _handle_search_codebase(self, query: str, file_types: List[str]) -> Dict[str, Any]:
        """
        Handle the search_codebase tool.
        
        Args:
            query: Search query
            file_types: List of file extensions to search
        
        Returns:
            Dictionary with search results
        """
        # Implementation of codebase search
        import subprocess
        
        results = []
        extensions = ' '.join([f'--include="*.{ext.lstrip(".")}"' for ext in file_types])
        
        try:
            cmd = f'grep -r {extensions} -n "{query}" {self.workspace_dir}'
            output = subprocess.check_output(cmd, shell=True, text=True)
            
            for line in output.strip().split('\n'):
                if line:
                    file_path, line_num, content = line.split(':', 2)
                    results.append({
                        "file": file_path,
                        "line": int(line_num),
                        "content": content.strip()
                    })
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except subprocess.CalledProcessError:
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": "No matches found or search error"
            }
    
    def _handle_analyze_code(self, file_path: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        Handle the analyze_code tool.
        
        Args:
            file_path: Path to the file to analyze
            start_line: Starting line number
            end_line: Ending line number
        
        Returns:
            Dictionary with code analysis
        """
        full_path = self.workspace_dir / file_path
        
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            # Adjust line numbers (0-indexed in list)
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            code_section = ''.join(lines[start_idx:end_idx])
            
            # Use OWL reasoning to analyze code semantics
            analysis_context = {
                "code": code_section,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line
            }
            
            reasoning_result = self.owl_engine.reason(
                query="Analyze this code section for structure and functionality",
                context=[json.dumps(analysis_context)]
            )
            
            # Store the analysis in memory for future reference
            self.memory_manager.add_semantic_memory(
                content=f"Code analysis for {file_path}:{start_line}-{end_line}",
                metadata={
                    "type": "code_analysis",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "analysis": reasoning_result
                }
            )
            
            return {
                "success": True,
                "code": code_section,
                "analysis": reasoning_result,
                "file_info": {
                    "path": file_path,
                    "total_lines": len(lines),
                    "analyzed_lines": end_line - start_line + 1
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_modify_code(self, file_path: str, code_changes: str, start_line: int, end_line: int) -> Dict[str, Any]:
        """
        Handle the modify_code tool.
        
        Args:
            file_path: Path to the file to modify
            code_changes: New code to replace the specified section
            start_line: Starting line number
            end_line: Ending line number
        
        Returns:
            Dictionary with modification results
        """
        full_path = self.workspace_dir / file_path
        
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
            
            # Create backup
            backup_path = f"{full_path}.bak"
            with open(backup_path, 'w') as f:
                f.writelines(lines)
            
            # Adjust line numbers (0-indexed in list)
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)
            
            # Replace the code section
            new_lines = lines[:start_idx] + [code_changes] + lines[end_idx:]
            
            with open(full_path, 'w') as f:
                f.writelines(new_lines)
            
            logger.info(f"Modified code in {file_path} from line {start_line} to {end_line}")
            
            # Store the modification in memory
            self.memory_manager.add_semantic_memory(
                content=f"Code modification in {file_path}:{start_line}-{end_line}",
                metadata={
                    "type": "code_modification",
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "previous_code": ''.join(lines[start_idx:end_idx]),
                    "new_code": code_changes
                }
            )
            
            return {
                "success": True,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "backup_created": backup_path
            }
        except Exception as e:
            logger.error(f"Error modifying code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_commit_changes(self, commit_message: str, files: List[str]) -> Dict[str, Any]:
        """
        Handle the commit_changes tool.
        
        Args:
            commit_message: Commit message
            files: List of file paths to commit
        
        Returns:
            Dictionary with commit results
        """
        if not self.github_enabled:
            return {
                "success": False,
                "error": "GitHub integration not enabled"
            }
        
        try:
            import subprocess
            
            # Verify all files exist
            for file in files:
                if not (self.workspace_dir / file).exists():
                    return {
                        "success": False,
                        "error": f"File not found: {file}"
                    }
            
            # Add files to git
            add_cmd = f"git -C {self.workspace_dir} add {' '.join(files)}"
            subprocess.run(add_cmd, shell=True, check=True)
            
            # Commit files
            commit_cmd = f'git -C {self.workspace_dir} commit -m "{commit_message}"'
            subprocess.run(commit_cmd, shell=True, check=True)
            
            # Push to GitHub
            push_cmd = f"git -C {self.workspace_dir} push origin main"
            subprocess.run(push_cmd, shell=True, check=True)
            
            logger.info(f"Committed and pushed changes to GitHub: {commit_message}")
            
            return {
                "success": True,
                "commit_message": commit_message,
                "files": files,
                "repository": f"{self.github_owner}/{self.github_repo}"
            }
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def improve_three_js_visualization(self) -> Dict[str, Any]:
        """
        Improve the THREE.js visualization based on current system analysis.
        
        Returns:
            Dictionary with improvement results
        """
        logger.info("Starting THREE.js visualization improvement workflow")
        
        # Step 1: Analyze current visualization code
        three_js_path = "src/vot1/dashboard/static/js/three-visualization.js"
        
        # First, use MCP to gather requirements and analyze current implementation
        analysis_prompt = """
        Analyze the current THREE.js visualization and create a plan for improvement:
        
        1. Evaluate the current implementation, identifying strengths and weaknesses
        2. Consider advanced THREE.js features that could enhance the visualization:
           - Improved particle systems and effects
           - Enhanced cyberpunk aesthetic with neon colors and glowing edges
           - More intuitive node interaction and navigation
           - Performance optimization for handling larger memory graphs
        3. Develop a clear, step-by-step improvement plan
        4. Consider modular architecture to make future improvements easier
        
        Focus on creating a visually striking, cyberpunk-themed interface that effectively
        represents the VOT1 memory system.
        """
        
        analysis_result = await self.mcp.process_request_async(
            prompt=analysis_prompt,
            system="You are an expert THREE.js developer focused on creating advanced data visualizations with a cyberpunk aesthetic.",
            temperature=0.7,
            max_tokens=2048,
            context={"task": "visualization_improvement"}
        )
        
        # Step 2: Generate improvement plan
        improvement_plan = analysis_result.get("content", "")
        
        logger.info("Generated improvement plan for THREE.js visualization")
        
        # Step 3: Execute the improvement plan using the MCP to modify the code
        # This is a simplified version - actual implementation would involve multiple
        # targeted improvements to specific sections of the code
        
        # Let's use the MCP to generate improved code for the aesthetic aspects
        aesthetic_prompt = """
        Based on the improvement plan, rewrite the following aspects of the THREE.js visualization:
        
        1. Color scheme and visual styling (update the 'config' object)
        2. Particle system for background effects
        3. Node and link rendering with cyberpunk aesthetic
        
        Make sure to maintain all current functionality while enhancing the visual appeal
        with a strong cyberpunk theme featuring neon colors, glowing edges, and futuristic effects.
        """
        
        aesthetic_improvements = await self.mcp.process_request_async(
            prompt=aesthetic_prompt,
            system="You are an expert THREE.js developer specializing in advanced visual effects and cyberpunk design aesthetics.",
            temperature=0.7,
            max_tokens=2048,
            context={"task": "visualization_aesthetic_improvement"}
        )
        
        # Step 4: Apply the improvements
        # In a real implementation, this would involve parsing the MCP response
        # and applying specific changes to the code
        
        # For demonstration, we'll log the results
        logger.info("Generated aesthetic improvements for THREE.js visualization")
        
        # Return improvement summary
        return {
            "success": True,
            "analysis": analysis_result,
            "improvements": aesthetic_improvements,
            "visualization_path": three_js_path
        }
    
    async def enhance_memory_system(self) -> Dict[str, Any]:
        """
        Enhance the memory system with improved vector search and integration.
        
        Returns:
            Dictionary with enhancement results
        """
        logger.info("Starting memory system enhancement workflow")
        
        # Step 1: Analyze current memory implementation
        memory_path = "src/vot1/memory.py"
        
        # Generate improvement proposals using MCP
        memory_prompt = """
        Analyze the current VOT1 memory system and propose enhancements focused on:
        
        1. Improved vector embedding models for better semantic search
        2. Enhanced context retrieval algorithms
        3. Memory consolidation and summarization capabilities
        4. Integration with OWL reasoning for semantic memory enhancement
        5. Optimization for handling larger knowledge bases
        
        Provide specific, implementable improvements that build on the current architecture.
        """
        
        memory_analysis = await self.mcp.process_request_async(
            prompt=memory_prompt,
            system="You are an expert in vector databases, semantic search, and memory systems for large language models.",
            temperature=0.7,
            max_tokens=2048,
            context={"task": "memory_system_enhancement"}
        )
        
        # Log the memory enhancement proposals
        logger.info("Generated memory system enhancement proposals")
        
        # Return enhancement summary
        return {
            "success": True,
            "analysis": memory_analysis,
            "memory_path": memory_path
        }
    
    async def integrate_owl_reasoning(self) -> Dict[str, Any]:
        """
        Enhance OWL reasoning integration throughout the system.
        
        Returns:
            Dictionary with integration results
        """
        logger.info("Starting OWL reasoning integration workflow")
        
        # Step 1: Analyze current OWL implementation
        owl_path = "src/vot1/owl_reasoning.py"
        
        # Generate integration proposals using MCP
        owl_prompt = """
        Analyze the current VOT1 OWL reasoning implementation and propose enhancements focused on:
        
        1. Deeper integration with the memory system
        2. Enhanced semantic reasoning capabilities
        3. Support for uncertainty and probabilistic reasoning
        4. Improved ontology management and evolution
        5. Performance optimization for larger knowledge graphs
        
        Provide specific, implementable improvements that build on the current architecture.
        """
        
        owl_analysis = await self.mcp.process_request_async(
            prompt=owl_prompt,
            system="You are an expert in semantic web technologies, OWL ontologies, and reasoning systems.",
            temperature=0.7,
            max_tokens=2048,
            context={"task": "owl_reasoning_enhancement"}
        )
        
        # Log the OWL enhancement proposals
        logger.info("Generated OWL reasoning enhancement proposals")
        
        # Return enhancement summary
        return {
            "success": True,
            "analysis": owl_analysis,
            "owl_path": owl_path
        }
    
    async def create_self_improvement_agent(self) -> Dict[str, Any]:
        """
        Create an agent capable of improving its own code.
        
        Returns:
            Dictionary with agent creation results
        """
        logger.info("Starting self-improvement agent creation workflow")
        
        # Generate agent design using MCP
        agent_prompt = """
        Design a self-improving agent system for VOT1 that can:
        
        1. Analyze its own code and identify areas for improvement
        2. Generate and implement targeted enhancements
        3. Evaluate the impact of changes through automated testing
        4. Learn from successful and unsuccessful modification attempts
        5. Maintain a safety framework to prevent harmful changes
        
        Provide a detailed architecture and implementation approach.
        """
        
        agent_design = await self.mcp.process_request_async(
            prompt=agent_prompt,
            system="You are an expert in recursive self-improvement systems, agent architectures, and AI safety.",
            temperature=0.7,
            max_tokens=4096,  # Using more tokens for this complex task
            context={"task": "self_improvement_agent_design"}
        )
        
        # Log the agent design
        logger.info("Generated self-improvement agent design")
        
        # Return design summary
        return {
            "success": True,
            "design": agent_design
        }
    
    async def run_full_workflow(self) -> Dict[str, Any]:
        """
        Run the complete self-improvement workflow.
        
        Returns:
            Dictionary with workflow results
        """
        results = {}
        
        try:
            # Step 1: Integrate OWL reasoning
            logger.info("Step 1: Integrating OWL reasoning")
            results["owl_integration"] = await self.integrate_owl_reasoning()
            
            # Step 2: Enhance memory system
            logger.info("Step 2: Enhancing memory system")
            results["memory_enhancement"] = await self.enhance_memory_system()
            
            # Step 3: Improve THREE.js visualization
            logger.info("Step 3: Improving THREE.js visualization")
            results["three_js_improvement"] = await self.improve_three_js_visualization()
            
            # Step 4: Create self-improvement agent
            logger.info("Step 4: Creating self-improvement agent")
            results["self_improvement_agent"] = await self.create_self_improvement_agent()
            
            # Step 5: Commit changes to GitHub if enabled
            if self.github_enabled:
                logger.info("Step 5: Committing changes to GitHub")
                commit_result = self._handle_commit_changes(
                    commit_message="VOT1 Self-Improvement: Enhanced OWL, Memory, and Visualization",
                    files=[
                        "src/vot1/owl_reasoning.py",
                        "src/vot1/memory.py",
                        "src/vot1/dashboard/static/js/three-visualization.js",
                        "src/vot1/self_improvement_workflow.py"
                    ]
                )
                results["github_commit"] = commit_result
            
            logger.info("Self-improvement workflow completed successfully")
            results["success"] = True
            return results
        
        except Exception as e:
            logger.error(f"Error during self-improvement workflow: {e}")
            results["success"] = False
            results["error"] = str(e)
            return results


async def main():
    """Main function to run the self-improvement workflow."""
    parser = argparse.ArgumentParser(description="Run VOT1 self-improvement workflow")
    
    parser.add_argument("--memory-path", type=str, default="memory",
                      help="Path to the memory storage directory")
    parser.add_argument("--owl-path", type=str, default="owl/vot1_ontology.owl",
                      help="Path to the OWL ontology file")
    parser.add_argument("--github-token", type=str,
                      help="GitHub API token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--github-repo", type=str,
                      help="GitHub repository name (or set GITHUB_REPO env var)")
    parser.add_argument("--github-owner", type=str,
                      help="GitHub repository owner (or set GITHUB_OWNER env var)")
    parser.add_argument("--max-thinking-tokens", type=int, default=4096,
                      help="Maximum tokens to use for thinking stream")
    parser.add_argument("--no-perplexity", action="store_true",
                      help="Disable Perplexity integration")
    parser.add_argument("--workflow", type=str, choices=["all", "owl", "memory", "three-js", "agent"],
                      default="all", help="Which workflow to run")
    
    args = parser.parse_args()
    
    # Create the workflow instance
    workflow = SelfImprovementWorkflow(
        github_token=args.github_token,
        github_repo=args.github_repo,
        github_owner=args.github_owner,
        max_thinking_tokens=args.max_thinking_tokens,
        use_perplexity=not args.no_perplexity
    )
    
    # Run the selected workflow
    if args.workflow == "all":
        results = await workflow.run_full_workflow()
    elif args.workflow == "owl":
        results = await workflow.integrate_owl_reasoning()
    elif args.workflow == "memory":
        results = await workflow.enhance_memory_system()
    elif args.workflow == "three-js":
        results = await workflow.improve_three_js_visualization()
    elif args.workflow == "agent":
        results = await workflow.create_self_improvement_agent()
    
    # Print results summary
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 