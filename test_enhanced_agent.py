#!/usr/bin/env python3
"""
Test script for the Enhanced Research Agent.
Tests the new features including knowledge graph construction and THREE.js visualization.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded from .env file")
except ImportError:
    print("dotenv module not found, using existing environment variables")
    # Manually load .env file
    try:
        with open(".env", "r") as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        print("Environment variables manually loaded from .env file")
    except Exception as e:
        print(f"Failed to manually load .env file: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestEnhancedAgent")

# Now we can safely import the agent
from enhanced_research_agent import AdvancedResearchAgent

async def test_basic_functionality(agent: AdvancedResearchAgent) -> Dict[str, Any]:
    """Test basic agent functionality."""
    logger.info("Testing basic functionality...")
    
    if not agent.claude_client:
        logger.error("Claude client not initialized")
        return {"error": "Claude client not initialized"}
    
    try:
        # Simple Claude test
        response = agent.claude_client.messages.create(
            model=agent.claude_model,
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello, please respond with 'Connection successful!'"}
            ]
        )
        
        logger.info(f"Claude response: {response.content[0].text}")
        return {
            "success": True,
            "claude_response": response.content[0].text,
            "model": agent.claude_model
        }
        
    except Exception as e:
        logger.error(f"Error testing basic functionality: {e}")
        return {"error": str(e)}

async def test_research_with_visualization() -> Dict[str, Any]:
    """Test research with knowledge graph and visualization capabilities."""
    logger.info("Initializing Enhanced Research Agent...")
    
    # Get API keys from environment variables
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
    github_token = os.environ.get("GITHUB_TOKEN")
    
    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return {"error": "Missing ANTHROPIC_API_KEY"}
    
    if not perplexity_api_key:
        logger.warning("PERPLEXITY_API_KEY not found in environment variables. Web research will be unavailable.")
    
    # Initialize the agent with explicit API keys
    agent = AdvancedResearchAgent(
        anthropic_api_key=anthropic_api_key,
        perplexity_api_key=perplexity_api_key,
        github_token=github_token,
        output_dir="output/test_results"
    )
    
    # First, test basic functionality
    basic_test = await test_basic_functionality(agent)
    if "error" in basic_test:
        logger.error(f"Basic functionality test failed: {basic_test['error']}")
        return basic_test
    
    logger.info("Basic functionality test passed")
    
    # Now run a simple test with knowledge graph but without web research
    # to avoid API rate limits
    test_topic = "THREE.js force-directed graph visualization techniques"
    
    logger.info(f"Testing knowledge graph generation for: {test_topic}")
    
    # Create mock research results to avoid API calls
    mock_research = {
        "primary_research": "Force-directed graphs in THREE.js use physics simulations to layout nodes. Key aspects include performance optimization, edge bundling, and interactive features.",
        "followup_research": {
            "What libraries are commonly used?": "Popular libraries for force-directed graphs in THREE.js include force-graph, 3d-force-graph, and THREE-forcegraph. These provide high-level abstractions over raw THREE.js.",
            "How can performance be optimized?": "Performance can be optimized by using WebGL for rendering, implementing level-of-detail techniques, using web workers for physics calculations, and spatial partitioning for large graphs."
        }
    }
    
    try:
        # Test knowledge graph construction directly
        logger.info("Testing knowledge graph construction...")
        graph_results = await agent.construct_knowledge_graph(
            topic=test_topic,
            research_results=mock_research,
            graph_type="threejs"
        )
        
        if "error" in graph_results:
            logger.error(f"Knowledge graph construction failed: {graph_results['error']}")
            return {"error": graph_results["error"], "stage": "knowledge_graph"}
        
        logger.info(f"Knowledge graph generated with {len(graph_results['knowledge_graph'].get('nodes', []))} nodes")
        
        # Save knowledge graph to file for inspection
        os.makedirs("output", exist_ok=True)
        with open("output/knowledge_graph_test.json", "w") as f:
            json.dump(graph_results["knowledge_graph"], f, indent=2)
        logger.info("Knowledge graph saved to output/knowledge_graph_test.json")
        
        # Test THREE.js visualization code generation
        logger.info("Testing THREE.js visualization code generation...")
        viz_results = await agent.generate_threejs_visualization(
            knowledge_graph=graph_results["knowledge_graph"],
            visualization_options={
                "backgroundColor": "#111133",
                "useForceDirectedLayout": True,
                "colorByGroup": True
            }
        )
        
        if "error" in viz_results:
            logger.error(f"THREE.js visualization generation failed: {viz_results['error']}")
            return {"error": viz_results["error"], "stage": "visualization"}
        
        # Save HTML file for visualization
        viz_html = viz_results["visualization"].get("html", "")
        if viz_html:
            os.makedirs("output/visualization", exist_ok=True)
            with open("output/visualization/test_visualization.html", "w") as f:
                f.write(viz_html)
            logger.info("Visualization HTML saved to output/visualization/test_visualization.html")
        
        logger.info("Test completed successfully")
        return {
            "success": True,
            "knowledge_graph_nodes": len(graph_results["knowledge_graph"].get("nodes", [])),
            "visualization_generated": bool(viz_html)
        }
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

async def main():
    """Run all tests."""
    try:
        result = await test_research_with_visualization()
        
        if "error" in result:
            logger.error(f"Test failed: {result['error']}")
            if "stage" in result:
                logger.error(f"Failed at stage: {result['stage']}")
        else:
            logger.info("All tests completed successfully")
            logger.info(f"Test results: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 