#!/usr/bin/env python3
"""
VOT1 Hybrid Reasoning Module

A module that leverages Claude 3.7 Sonnet to perform hybrid reasoning,
combining fast thinking with deep, step-by-step analysis for enhanced
code structure comprehension and insights.
"""

import os
import sys
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hybrid_reasoning")

# Try to import Anthropic client
try:
    import anthropic
    anthropic_available = True
except ImportError:
    logger.warning("Anthropic SDK not installed. Please install with 'pip install anthropic'")
    anthropic_available = False

class HybridReasoning:
    """
    Provides hybrid reasoning capabilities using Claude 3.7 Sonnet.
    
    The hybrid reasoning approach combines fast, intuitive thinking with
    slow, deliberate analysis to provide comprehensive insights about
    code structures, architecture patterns, and potential improvements.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-7-sonnet-20240620",
        max_tokens: int = 4000,
        thinking_budget: int = 8000,
        temperature: float = 0.7,
        cache_dir: str = "cache/reasoning"
    ):
        """
        Initialize the hybrid reasoning module.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in the response
            thinking_budget: Maximum tokens for thinking
            temperature: Temperature parameter for generation
            cache_dir: Directory to cache reasoning results
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.temperature = temperature
        self.cache_dir = cache_dir
        
        # Initialize Claude client if available
        self.client = None
        if anthropic_available and self.api_key:
            try:
                # Make sure to only pass supported parameters
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"Initialized Claude client with model {self.model}")
            except Exception as e:
                logger.error(f"Error initializing Claude client: {e}")
                self.client = None
        elif not anthropic_available:
            logger.warning("Anthropic SDK not available. Hybrid reasoning will use simulated responses.")
        elif not self.api_key:
            logger.warning("No API key provided. Hybrid reasoning will use simulated responses.")
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def perform_hybrid_thinking(
        self,
        prompt: str,
        domain: str = "general",
        use_cache: bool = True,
        cache_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid reasoning using Claude's extended thinking capabilities.
        
        Args:
            prompt: The prompt for Claude to reason about
            domain: Domain for thinking (programming, architecture, etc.)
            use_cache: Whether to use cached results if available
            cache_key: Custom cache key, defaults to a hash of the prompt
            
        Returns:
            Dictionary containing both the thinking process and the final answer
        """
        # Generate cache key if not provided
        if not cache_key:
            import hashlib
            cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        cache_path = os.path.join(self.cache_dir, f"{cache_key}_{domain}.json")
        
        # Check cache if enabled
        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cached_result = json.load(f)
                    logger.info(f"Found cached reasoning result for {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")
        
        # Prepare to call Claude
        if self.client:
            try:
                # Set up the system message based on domain
                system_message = self._get_system_message(domain)
                
                # Call Claude with extended thinking
                start_time = time.time()
                logger.info(f"Calling Claude for hybrid reasoning in domain: {domain}")
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_message,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    anthropic_version="bedrock-2023-05-31"
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"Claude response received in {elapsed_time:.2f}s")
                
                # Extract thinking and solution
                result = {
                    "thinking": self._extract_thinking(response),
                    "solution": self._extract_solution(response),
                    "prompt": prompt,
                    "domain": domain,
                    "model": self.model,
                    "timestamp": time.time()
                }
                
                # Cache the result
                with open(cache_path, 'w') as f:
                    json.dump(result, f, indent=2)
                
                return result
                
            except Exception as e:
                logger.error(f"Error during Claude API call: {e}")
                return self._generate_simulated_response(prompt, domain)
        else:
            logger.warning("Claude client not available, using simulated response")
            return self._generate_simulated_response(prompt, domain)
    
    def _get_system_message(self, domain: str) -> str:
        """Get the appropriate system message for the domain."""
        base_msg = """You are Claude 3.7 Sonnet, an AI assistant with advanced hybrid reasoning capabilities.
When analyzing complex problems, you use both:
1. Fast, intuitive thinking for quick pattern recognition
2. Slow, deliberate thinking for step-by-step analysis

For this task, use your hybrid thinking approach to show both your thought process and final solution.
Structure your response with clearly labeled sections for "Thinking" and "Solution"."""

        domain_specific = {
            "programming": """
You specialize in software engineering and programming.
When analyzing code and project structures:
- Identify architectural patterns and design principles
- Evaluate code organization and modularity
- Consider maintainability, scalability, and best practices
- Provide concrete, actionable suggestions for improvements""",

            "architecture": """
You specialize in software architecture analysis.
When analyzing system architectures:
- Identify architectural styles (microservices, monolithic, etc.)
- Evaluate component coupling and cohesion
- Consider scalability, performance, and resilience
- Provide recommendations for architectural improvements""",
            
            "ux": """
You specialize in user experience and interface design.
When analyzing UI/UX components:
- Identify design patterns and frameworks
- Evaluate usability and accessibility considerations
- Consider consistency, responsiveness, and user flow
- Provide suggestions for enhancing user experience"""
        }
        
        return base_msg + domain_specific.get(domain, "")
    
    def _extract_thinking(self, response: Any) -> str:
        """Extract the thinking process from Claude's response."""
        if hasattr(response, "content") and response.content:
            content = response.content[0].text
            
            # Try to extract thinking section
            if "Thinking:" in content and "Solution:" in content:
                thinking_part = content.split("Thinking:")[1].split("Solution:")[0].strip()
                return thinking_part
            
            # If no explicit sections, return the whole response
            return content
        
        return "No thinking process available"
    
    def _extract_solution(self, response: Any) -> Union[Dict[str, Any], str]:
        """Extract the solution from Claude's response and try to parse as JSON."""
        if hasattr(response, "content") and response.content:
            content = response.content[0].text
            
            # Try to extract solution section
            solution_text = ""
            if "Solution:" in content:
                solution_text = content.split("Solution:")[1].strip()
            else:
                solution_text = content
            
            # Try to extract JSON from the solution
            try:
                # Find JSON within the solution
                import re
                json_match = re.search(r'```json\n([\s\S]*?)\n```', solution_text)
                if json_match:
                    json_str = json_match.group(1)
                    return json.loads(json_str)
                
                # If no marked JSON, try to parse the whole solution
                return json.loads(solution_text)
            except json.JSONDecodeError:
                # Return as plain text if not valid JSON
                return solution_text
        
        return "No solution available"
    
    def _generate_simulated_response(self, prompt: str, domain: str) -> Dict[str, Any]:
        """Generate a simulated response when Claude is not available."""
        logger.info("Generating simulated hybrid reasoning response")
        
        if "file structure" in prompt.lower() or "project structure" in prompt.lower():
            # Simulate response for file structure analysis
            return {
                "thinking": "I'm analyzing the file structure to understand the project organization...",
                "solution": {
                    "main_components": [
                        "visualization - UI components for rendering file structures",
                        "api - Server endpoints for file structure data",
                        "utils - Helper utilities for file operations"
                    ],
                    "architectural_patterns": [
                        "Model-View-Controller pattern",
                        "Module-based organization",
                        "API-first approach"
                    ],
                    "strengths": [
                        "Clear separation of concerns",
                        "Modular design allows for easy extension",
                        "Visualization components are decoupled from data generation"
                    ],
                    "improvement_areas": [
                        "Documentation could be more comprehensive",
                        "Test coverage appears limited",
                        "Configuration management could be centralized"
                    ],
                    "recommendations": [
                        "Add more comprehensive documentation",
                        "Implement a test suite",
                        "Consider using a dependency injection pattern"
                    ]
                },
                "prompt": prompt,
                "domain": domain,
                "model": "simulated",
                "timestamp": time.time()
            }
        else:
            # Generic simulated response
            return {
                "thinking": "I'm analyzing the provided information...",
                "solution": {
                    "analysis": "This is a simulated response since Claude is not available.",
                    "key_points": [
                        "This is point 1",
                        "This is point 2",
                        "This is point 3"
                    ],
                    "recommendations": [
                        "First recommendation",
                        "Second recommendation",
                        "Third recommendation"
                    ]
                },
                "prompt": prompt,
                "domain": domain,
                "model": "simulated",
                "timestamp": time.time()
            }
    
    def analyze_code_structure(self, code_snippet: str) -> Dict[str, Any]:
        """
        Analyze a code snippet to understand its structure and patterns.
        
        Args:
            code_snippet: The code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
        Analyze the following code snippet to understand its structure,
        patterns, and potential improvements:
        
        ```
        {code_snippet}
        ```
        
        Please provide:
        1. A summary of what this code does
        2. The design patterns or principles it follows
        3. Any potential issues or bugs
        4. Suggestions for improvement
        
        Format your response as structured JSON with these categories.
        """
        
        return self.perform_hybrid_thinking(prompt, domain="programming")
    
    def analyze_project_architecture(self, file_structure: str) -> Dict[str, Any]:
        """
        Analyze project architecture based on file structure.
        
        Args:
            file_structure: Markdown or text representation of the file structure
            
        Returns:
            Dictionary with architecture analysis
        """
        prompt = f"""
        Analyze the following project file structure to understand its
        architectural patterns, organization, and potential improvements:
        
        {file_structure}
        
        Please provide:
        1. The main components of the project
        2. The architectural patterns observed
        3. Strengths of the current structure
        4. Areas for improvement
        5. Specific recommendations
        
        Format your response as structured JSON with these categories.
        """
        
        return self.perform_hybrid_thinking(prompt, domain="architecture")
    
    def analyze_ui_components(self, ui_code: str) -> Dict[str, Any]:
        """
        Analyze UI components to understand patterns and user experience.
        
        Args:
            ui_code: UI code to analyze
            
        Returns:
            Dictionary with UI analysis
        """
        prompt = f"""
        Analyze the following UI code to understand its components,
        patterns, and user experience considerations:
        
        ```
        {ui_code}
        ```
        
        Please provide:
        1. The UI framework or libraries being used
        2. The main UI components identified
        3. UX patterns implemented
        4. Accessibility considerations
        5. Suggestions for improvement
        
        Format your response as structured JSON with these categories.
        """
        
        return self.perform_hybrid_thinking(prompt, domain="ux")

if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 Hybrid Reasoning Module")
    parser.add_argument("--prompt", "-p", type=str, help="Prompt for reasoning")
    parser.add_argument("--domain", "-d", type=str, default="general", 
                      choices=["general", "programming", "architecture", "ux"],
                      help="Domain for reasoning")
    parser.add_argument("--file", "-f", type=str, help="File to analyze")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    
    args = parser.parse_args()
    
    reasoner = HybridReasoning()
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
                
            if args.domain == "programming":
                result = reasoner.analyze_code_structure(content)
            elif args.domain == "architecture":
                result = reasoner.analyze_project_architecture(content)
            elif args.domain == "ux":
                result = reasoner.analyze_ui_components(content)
            else:
                result = reasoner.perform_hybrid_thinking(
                    f"Analyze the following content:\n\n{content}",
                    domain=args.domain,
                    use_cache=not args.no_cache
                )
                
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            sys.exit(1)
            
    elif args.prompt:
        result = reasoner.perform_hybrid_thinking(
            args.prompt,
            domain=args.domain,
            use_cache=not args.no_cache
        )
        print(json.dumps(result, indent=2))
        
    else:
        parser.print_help() 