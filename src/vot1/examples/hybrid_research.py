"""
VOTai Hybrid Research Example

This example demonstrates how to use the VOTai system for hybrid research
using Claude 3.7 Sonnet's hybrid thinking and Perplexity's deep web research.
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
grandparent_dir = os.path.dirname(parent_dir)
if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)

# Modified imports to use direct relative paths
from vot1.initialize import initialize_system
from vot1.utils.branding import format_status, format_result_block
from vot1.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class HybridResearcher:
    """
    Hybrid Researcher that combines Claude's hybrid thinking with Perplexity's web research.
    
    This demonstrates how to:
    1. Use the Perplexity client for deep web research
    2. Provide that research to Claude for hybrid thinking
    3. Get a comprehensive analysis with relevant memory integration
    """
    
    def __init__(self):
        """Initialize the Hybrid Researcher (system will be initialized lazily)"""
        self.system = None
        self.memory_bridge = None
        self.claude_client = None
        self.perplexity_client = None
    
    async def initialize(self):
        """Initialize the VOTai system and required components"""
        # Initialize the system (this will set up logging)
        self.system = await initialize_system()
        
        # Get required components
        self.memory_bridge = await self.system.get_memory_bridge()
        self.claude_client = await self.system.get_claude_client()
        self.perplexity_client = await self.system.get_perplexity_client()
        
        logger.info(format_status("success", "Hybrid Researcher initialized"))
    
    async def research_and_analyze(
        self,
        topic: str,
        depth: str = "standard",
        focus: Optional[str] = None,
        with_hybrid_thinking: bool = True,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Perform hybrid research and analysis on a topic.
        
        This method:
        1. Conducts deep web research using Perplexity
        2. Stores research results in memory
        3. Uses Claude's hybrid thinking to analyze the research
        4. Returns combined results
        
        Args:
            topic: Research topic
            depth: Research depth ("brief", "standard", "deep")
            focus: Optional focus area
            with_hybrid_thinking: Whether to use hybrid thinking
            max_iterations: Maximum hybrid thinking iterations
            
        Returns:
            Dictionary with research and analysis results
        """
        if not self.system:
            await self.initialize()
        
        logger.info(format_status("info", f"Starting hybrid research on: {topic}"))
        
        # Print status update
        print(f"\n{format_status('info', f'Researching topic: {topic}')}")
        if focus:
            print(f"Focus: {focus}")
        print(f"Depth: {depth}")
        print(f"Using hybrid thinking: {'Yes' if with_hybrid_thinking else 'No'}")
        print("\n" + "=" * 80 + "\n")
        
        # Step 1: Perform web research with Perplexity
        print(format_status("info", "Conducting web research with Perplexity..."))
        
        try:
            # Print progress updates during streaming
            print("\nResearch progress:")
            current_status = ""
            research_results = {}
            
            # Define stream handler to show progress
            async def stream_handler(event_type, content):
                nonlocal current_status
                if event_type == "status":
                    current_status = content
                    print(f"\n{format_status('info', content)}")
                elif event_type == "content":
                    print(".", end="", flush=True)
                elif event_type == "error":
                    print(f"\n{format_status('error', content)}")
                    
            # Conduct the research
            research_results = await self.perplexity_client.research(
                topic=topic,
                max_queries=3 if depth == "deep" else 2,
                depth=depth,
                focus=focus,
                streaming=True,
                stream_handler=stream_handler
            )
            
            print("\n\n" + "=" * 80 + "\n")
            print(format_status("success", "Web research completed"))
            
            # Print research summary
            print("\n" + format_result_block(
                title="Research Summary",
                content=research_results["summary"],
                status="info"
            ))
            
            # Step 2: Use Claude's hybrid thinking for analysis if requested
            if with_hybrid_thinking:
                print(format_status("info", "Analyzing research results with Claude's hybrid thinking..."))
                
                # Prepare prompt for Claude
                analysis_prompt = f"""Analyze the following research on "{topic}":

{research_results["summary"]}

Please provide:
1. A critical analysis of the key findings
2. Connections between different aspects of the research
3. Potential implications or applications
4. Areas that require further research
5. Your own insights based on the information provided

Be thorough but concise in your analysis.
"""
                
                # Use hybrid thinking
                thinking_results = await self.memory_bridge.hybrid_thinking(
                    prompt=analysis_prompt,
                    max_iterations=max_iterations,
                    max_thinking_tokens=8000,
                    memory_types=["perplexity_response", "research_session", "citation"]
                )
                
                print("\n" + format_result_block(
                    title="Analysis Results",
                    content=thinking_results["response"],
                    status="success"
                ))
                
                # Include thinking process in results
                research_results["analysis"] = thinking_results["response"]
                research_results["thinking_process"] = thinking_results["thinking"]
                research_results["iterations"] = thinking_results["iterations"]
            
            # Return combined results
            return research_results
            
        except Exception as e:
            logger.error(f"Error in hybrid research: {str(e)}")
            print(f"\n{format_status('error', f'Research error: {str(e)}')}")
            return {
                "error": str(e),
                "topic": topic
            }

async def main():
    """Run the example"""
    # Create researcher
    researcher = HybridResearcher()
    
    # Get research topic from command line or use default
    import argparse
    parser = argparse.ArgumentParser(description="VOTai Hybrid Research Example")
    parser.add_argument("--topic", default="Advances in quantum computing in 2024", help="Research topic")
    parser.add_argument("--focus", help="Research focus area")
    parser.add_argument("--depth", default="standard", choices=["brief", "standard", "deep"], help="Research depth")
    parser.add_argument("--no-hybrid", action="store_true", help="Disable hybrid thinking")
    args = parser.parse_args()
    
    # Perform research
    results = await researcher.research_and_analyze(
        topic=args.topic,
        depth=args.depth,
        focus=args.focus,
        with_hybrid_thinking=not args.no_hybrid
    )
    
    # Final status
    if "error" not in results:
        citation_count = len(results.get("citations", []))
        query_count = len(results.get("queries", []))
        print(f"\n{format_status('success', 'Research completed successfully')}")
        print(f"Queries: {query_count}, Citations: {citation_count}")
        
        # Save results to file if desired
        save = input("\nSave results to file? (y/n): ").lower().strip() == "y"
        if save:
            import json
            from datetime import datetime
            
            # Create sanitized filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            topic_filename = "".join(c if c.isalnum() else "_" for c in args.topic)[:30]
            filename = f"research_{topic_filename}_{timestamp}.json"
            
            with open(filename, "w") as f:
                json.dump(results, f, indent=2)
                
            print(f"{format_status('success', f'Results saved to {filename}')}")
    else:
        print(f"\n{format_status('error', 'Research failed')}")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 