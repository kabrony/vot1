#!/usr/bin/env python3
"""
Test script for Claude 3.7 Sonnet hybrid thinking capabilities

This script demonstrates the advanced hybrid thinking capabilities
of Claude 3.7 Sonnet for research and analysis applications.
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, Any, Optional

import anthropic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ClaudeHybridTest")

# Claude 3.7 Sonnet model
CLAUDE_MODEL = "claude-3-7-sonnet-20250219"

class ClaudeHybridThinker:
    """Test helper for Claude 3.7 Sonnet's hybrid thinking capabilities."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key."""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("No Anthropic API key provided")
            
        # Initialize the Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info(f"Initialized Claude client with model: {CLAUDE_MODEL}")
        
        # Initialize feedback storage
        self.feedback_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "thinking_captured": 0,
            "average_thinking_length": 0,
            "average_response_time": 0
        }
    
    async def perform_hybrid_thinking(
        self, 
        topic: str, 
        context: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid thinking on a topic with Claude 3.7 Sonnet.
        
        Args:
            topic: Topic to think about
            context: Additional context
            output_file: Optional file to save results
            
        Returns:
            Dictionary with thinking results
        """
        # System prompt that encourages deep hybrid thinking
        system_prompt = """You are Claude 3.7 Sonnet, an AI assistant with exceptional hybrid thinking capabilities.
        
For this task, engage in a thorough, structured thinking process before concluding:
1. Break down the problem into clear components
2. Consider multiple perspectives, approaches, and frameworks
3. Identify potential challenges, contradictions or limitations
4. Synthesize information from various domains and sources
5. Connect concepts in novel, insightful ways
6. Draw on your knowledge across relevant domains
7. Use step-by-step reasoning to reach well-supported conclusions

Your hybrid thinking should be comprehensive, creative, rigorous and detail-oriented.
First explore multiple angles deeply, then provide a well-reasoned, coherent synthesis.
"""
        
        # User prompt with topic and context
        user_prompt = f"""I need to deeply understand the topic: "{topic}"

{context if context else ""}

Please use your hybrid thinking capabilities to analyze this topic thoroughly, exploring multiple perspectives, integrating relevant knowledge, and developing a comprehensive understanding.
"""
        
        try:
            logger.info(f"Starting hybrid thinking on: {topic}")
            start_time = time.time()
            
            # Increment request counter
            self.performance_metrics["total_requests"] += 1
            
            # Call Claude API with hybrid thinking
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Update metrics
            self.performance_metrics["successful_requests"] += 1
            self.performance_metrics["average_response_time"] = (
                (self.performance_metrics["average_response_time"] * 
                 (self.performance_metrics["successful_requests"] - 1) + 
                 response_time) / self.performance_metrics["successful_requests"]
            )
            
            # Extract thinking content if available
            thinking_content = None
            if hasattr(response, 'usage') and hasattr(response.usage, 'thinking_content'):
                thinking_content = response.usage.thinking_content
                logger.info(f"Successfully captured {len(thinking_content)} characters of hybrid thinking")
                
                # Update thinking metrics
                self.performance_metrics["thinking_captured"] += 1
                self.performance_metrics["average_thinking_length"] = (
                    (self.performance_metrics["average_thinking_length"] * 
                     (self.performance_metrics["thinking_captured"] - 1) + 
                     len(thinking_content)) / self.performance_metrics["thinking_captured"]
                )
            elif hasattr(response, 'usage') and hasattr(response.usage, 'thinking_tokens'):
                thinking_tokens = response.usage.thinking_tokens
                logger.info(f"Used {thinking_tokens} thinking tokens, but content not accessible")
            
            # Get response content
            response_content = response.content[0].text
            
            # Record feedback
            feedback = {
                "timestamp": time.time(),
                "topic": topic,
                "response_time": response_time,
                "thinking_captured": thinking_content is not None,
                "thinking_length": len(thinking_content) if thinking_content else 0,
                "response_length": len(response_content)
            }
            self.feedback_history.append(feedback)
            
            # Prepare results
            results = {
                "topic": topic,
                "hybrid_thinking": thinking_content,
                "response": response_content,
                "model": CLAUDE_MODEL,
                "success": True,
                "response_time": response_time,
                "metrics": {
                    "thinking_captured": thinking_content is not None,
                    "thinking_length": len(thinking_content) if thinking_content else 0,
                    "response_length": len(response_content)
                }
            }
            
            # Save to file if requested
            if output_file:
                os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Saved hybrid thinking results to: {output_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during hybrid thinking: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e), "success": False}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a performance report based on feedback history.
        
        Returns:
            Dictionary with performance metrics
        """
        # Clone current metrics
        report = dict(self.performance_metrics)
        
        # Add derived metrics
        if self.performance_metrics["total_requests"] > 0:
            report["success_rate"] = (self.performance_metrics["successful_requests"] / 
                                      self.performance_metrics["total_requests"])
        
        if self.performance_metrics["successful_requests"] > 0:
            report["thinking_capture_rate"] = (self.performance_metrics["thinking_captured"] / 
                                              self.performance_metrics["successful_requests"])
        
        # Add feedback history stats
        if self.feedback_history:
            # Find fastest and slowest responses
            response_times = [f["response_time"] for f in self.feedback_history]
            report["fastest_response"] = min(response_times)
            report["slowest_response"] = max(response_times)
            
            # Add recent feedback entries
            report["recent_feedback"] = self.feedback_history[-5:] if len(self.feedback_history) > 5 else self.feedback_history
        
        return report

async def main():
    """Run hybrid thinking test."""
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("No ANTHROPIC_API_KEY environment variable found")
        return
    
    # Sample research topics with contexts
    research_topics = [
        {
            "topic": "Claude 3.7 Sonnet hybrid thinking capabilities",
            "context": """Focus on understanding how Claude 3.7 Sonnet's hybrid thinking works, including:
- The technical mechanisms behind hybrid thinking
- How it improves reasoning and analysis
- Applications in research and problem-solving
- Comparing hybrid thinking to traditional AI reasoning
- Future directions and potential improvements""",
            "output_file": "output/hybrid_thinking_claude37.json"
        }
    ]
    
    # Create thinker
    thinker = ClaudeHybridThinker(api_key)
    
    # Process each topic
    for research in research_topics:
        logger.info(f"Processing topic: {research['topic']}")
        results = await thinker.perform_hybrid_thinking(
            topic=research["topic"],
            context=research["context"],
            output_file=research["output_file"]
        )
        
        # Print summary
        if results.get("success"):
            logger.info(f"Successfully completed hybrid thinking on: {research['topic']}")
            if results.get("hybrid_thinking"):
                thinking_preview = results["hybrid_thinking"][:100] + "..." if len(results["hybrid_thinking"]) > 100 else results["hybrid_thinking"]
                logger.info(f"Hybrid thinking preview: {thinking_preview}")
        else:
            logger.error(f"Failed to complete hybrid thinking: {results.get('error')}")
    
    # Generate and print performance report
    performance_report = thinker.get_performance_report()
    logger.info("=" * 40)
    logger.info("Performance Report:")
    for key, value in performance_report.items():
        if key != "recent_feedback":  # Skip printing the detailed feedback entries
            logger.info(f"  {key}: {value}")
    logger.info("=" * 40)
    
    # Save performance report
    try:
        with open("output/performance_report.json", "w") as f:
            json.dump(performance_report, f, indent=2)
        logger.info("Performance report saved to output/performance_report.json")
    except Exception as e:
        logger.error(f"Error saving performance report: {e}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 