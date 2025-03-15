"""
Research script for Model Control Protocol (MCP) tools for AGI with Composio integration

This script uses direct API calls to research MCP technologies for AGI development,
focusing on Composio integration capabilities.
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional

# Import the PerplexiPy library
try:
    from perplexipy import PerplexityClient
except ImportError:
    print("Please install PerplexiPy with: pip install PerplexiPy")
    sys.exit(1)

# Import the Anthropic library
try:
    import anthropic
except ImportError:
    print("Please install Anthropic with: pip install anthropic")
    sys.exit(1)

class SimpleResearcher:
    """
    A simple researcher that uses Perplexity and Claude to research MCP for AGI
    """
    
    def __init__(self):
        """Initialize the researcher with API keys from environment variables"""
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")
        
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
        # Initialize clients - modified to use correct initialization parameters
        self.perplexity_client = PerplexityClient(key=self.perplexity_api_key)
        self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        
        print("SimpleResearcher initialized successfully")
    
    async def research_mcp_for_agi(self, topic: str = "Model Control Protocol (MCP) tools for AGI with Composio integration"):
        """
        Research MCP for AGI with Composio integration
        
        Args:
            topic: Research topic
            
        Returns:
            Dictionary with research results
        """
        print(f"\n[INFO] Researching: {topic}")
        print("-" * 80)
        
        # Step 1: Perform initial research with Perplexity
        print("\n[INFO] Conducting initial research with Perplexity...")
        
        research_results = self.perplexity_client.query(
            f"""Provide comprehensive research on {topic}. 
            Focus on:
            1. What is Model Control Protocol (MCP) and its role in AGI development
            2. How Composio tools integrate with MCP
            3. Current best practices for MCP implementation
            4. Benefits of MCP for agent systems
            5. Future directions for MCP in AGI
            
            Include specific examples and technical details where possible.
            """
        )
        
        print("\n[INFO] Initial research completed")
        print("-" * 80)
        print(research_results)
        print("-" * 80)
        
        # Step 2: Follow-up with more specific questions
        print("\n[INFO] Conducting follow-up research on specific aspects...")
        
        followup_questions = [
            "What are the key components of an MCP implementation for AGI systems?",
            "How does Composio's tool ecosystem integrate with Model Control Protocol?",
            "What security considerations are important when implementing MCP for AGI?"
        ]
        
        followup_results = {}
        
        for question in followup_questions:
            print(f"\n[INFO] Researching: {question}")
            result = self.perplexity_client.query(question)
            followup_results[question] = result
            print(f"\n--- Result for: {question} ---")
            print(result)
            print("-" * 80)
        
        # Step 3: Analyze with Claude
        print("\n[INFO] Analyzing research with Claude 3.7 Sonnet...")
        
        # Prepare research summary for Claude
        research_summary = f"Research on {topic}:\n\n{research_results}\n\n"
        for question, result in followup_results.items():
            research_summary += f"Follow-up on '{question}':\n{result}\n\n"
        
        claude_prompt = f"""Analyze the following research on {topic}:

{research_summary}

Please provide:
1. A critical analysis of Model Control Protocol for AGI systems
2. Specific advantages of integrating Composio tools with MCP
3. Technical implementation recommendations
4. Current limitations and challenges
5. Future implications for AGI development

Be thorough but precise in your analysis.
"""
        
        message = self.anthropic_client.messages.create(
            model="claude-3-7-sonnet-20240620",
            max_tokens=4000,
            system="You are a technical expert in AI systems, specifically in Model Control Protocol (MCP) and AGI architectures.",
            messages=[
                {"role": "user", "content": claude_prompt}
            ]
        )
        
        analysis = message.content[0].text
        
        print("\n[INFO] Analysis completed")
        print("-" * 80)
        print(analysis)
        print("-" * 80)
        
        # Compile and return results
        results = {
            "topic": topic,
            "initial_research": research_results,
            "followup_research": followup_results,
            "analysis": analysis
        }
        
        # Save results to file
        filename = "mcp_composio_research_results.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[SUCCESS] Research results saved to {filename}")
        
        return results

async def main():
    """Run the research script"""
    try:
        researcher = SimpleResearcher()
        results = await researcher.research_mcp_for_agi()
        
        print("\n[SUCCESS] Research completed successfully")
        print(f"Saved results to: mcp_composio_research_results.json")
        
    except Exception as e:
        print(f"\n[ERROR] Research failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the research
    asyncio.run(main()) 