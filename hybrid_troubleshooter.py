#!/usr/bin/env python3
"""
Hybrid Troubleshooting Script

Combines Claude 3.7 Sonnet's hybrid reasoning with Perplexity's web search
to troubleshoot and fix VOT1 system issues.
"""

import os
import sys
import json
import asyncio
import logging
import re
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HybridTroubleshooter")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("dotenv module not found, using existing environment variables")
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip("'\"")
        logger.info("Environment variables manually loaded from .env file")
    except Exception as e:
        logger.warning(f"Failed to manually load .env file: {e}")

# Import required libraries
try:
    import anthropic
    from perplexipy import PerplexityClient
except ImportError:
    logger.error("Required libraries not installed. Please install with:")
    logger.error("pip install anthropic perplexipy")
    sys.exit(1)

class HybridTroubleshooter:
    """
    Hybrid troubleshooting system using Claude 3.7 and Perplexity.
    Combines Claude's hybrid reasoning with Perplexity's web search.
    """
    
    def __init__(self):
        """Initialize the troubleshooter."""
        # Initialize API keys
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.perplexity_api_key = os.environ.get("PERPLEXITY_API_KEY")
        
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        if not self.perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY not found in environment variables")
        
        # Initialize clients
        self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        self.perplexity_client = PerplexityClient(key=self.perplexity_api_key)
        
        # Set Claude model
        self.claude_model = os.environ.get("VOT1_PRIMARY_MODEL", "claude-3-7-sonnet-20240229")
        self.perplexity_model = os.environ.get("VOT1_SECONDARY_MODEL", "pplx-70b-online")
        
        # Create output directory
        os.makedirs("output/troubleshooting", exist_ok=True)
        
        logger.info(f"Initialized HybridTroubleshooter with Claude model: {self.claude_model}")
        logger.info(f"Perplexity model: {self.perplexity_model}")
    
    async def web_search(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search using Perplexity.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with search results
        """
        logger.info(f"Performing web search: {query}")
        
        try:
            # Call Perplexity API
            response = await self.perplexity_client.query(
                query,
                model=self.perplexity_model,
                streaming=False,
                store_in_memory=False
            )
            
            logger.info(f"Web search completed for: {query}")
            
            # Format response
            if isinstance(response, str):
                return {
                    "content": response,
                    "success": True
                }
            else:
                return {
                    "content": response.get("text", ""),
                    "citations": response.get("citations", []),
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    async def hybrid_analysis(
        self, 
        query: str, 
        context: Optional[str] = None, 
        search_web: bool = True
    ) -> Dict[str, Any]:
        """
        Perform hybrid analysis using Claude 3.7 Sonnet.
        
        Args:
            query: The analysis query
            context: Additional context for the analysis
            search_web: Whether to include web search results
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Performing hybrid analysis: {query}")
        
        try:
            # If web search is enabled, perform search and add to context
            web_results = None
            if search_web:
                web_results = await self.web_search(query)
                if web_results.get("success", False):
                    web_context = f"\n\nWEB SEARCH RESULTS:\n{web_results['content']}\n"
                    if context:
                        context = context + web_context
                    else:
                        context = web_context
            
            # Create Claude prompt
            system_message = """You are a hybrid troubleshooting system combining Claude 3.7 Sonnet's reasoning with web search.
            
Your task is to analyze technical issues thoroughly and provide detailed solutions.
You should:
1. Break down the problem into clear components
2. Analyze each component systematically
3. Identify root causes of issues
4. Suggest specific, actionable solutions with code examples
5. Explain your reasoning process step-by-step

Your output should be structured, practical, and technically precise.
"""
            
            full_prompt = f"QUERY: {query}\n\n"
            if context:
                full_prompt += f"CONTEXT:\n{context}\n\n"
            
            # Call Claude API with standard parameters
            logger.info(f"Calling Claude with model: {self.claude_model}")
            
            # Using max_tokens=4000 which is a reasonable limit
            try:
                response = await asyncio.wait_for(
                    self.claude_client.messages.create(
                        model=self.claude_model,
                        max_tokens=4000,
                        system=system_message,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ]
                    ),
                    timeout=120  # 2 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error("Claude API call timed out after 120 seconds")
                return {
                    "error": "Claude API call timed out",
                    "success": False
                }
            
            logger.info(f"Hybrid analysis completed for: {query}")
            
            # Extract content
            analysis_content = response.content[0].text if response.content else ""
            
            # Attempt to extract thinking content if available in the response
            thinking_content = None
            if hasattr(response, 'thinking'):
                thinking_content = response.thinking
            
            return {
                "analysis": analysis_content,
                "thinking": thinking_content,
                "web_results": web_results,
                "success": True
            }
                
        except Exception as e:
            logger.error(f"Error in hybrid analysis: {e}")
            import traceback
            error_details = traceback.format_exc()
            return {
                "error": str(e),
                "error_details": error_details,
                "success": False
            }
    
    async def fix_json_parsing(self, failed_json_path: str) -> Dict[str, Any]:
        """
        Fix JSON parsing errors in a file.
        
        Args:
            failed_json_path: Path to the failed JSON file
            
        Returns:
            Dictionary with fixed JSON
        """
        logger.info(f"Fixing JSON parsing errors in: {failed_json_path}")
        
        try:
            # Read the failed JSON file
            with open(failed_json_path, "r") as f:
                failed_json = f.read()
            
            # Create context with the failed JSON
            context = f"FAILED JSON CONTENT:\n```json\n{failed_json[:5000]}\n```\n"
            
            # Search for JSON parsing fixes
            web_results = await self.web_search("fix JSON parsing errors escaped quotes nodes array extra comma")
            if web_results.get("success", False):
                context += f"\nWEB SEARCH RESULTS ON JSON PARSING FIXES:\n{web_results['content']}\n"
            
            # Add specific error details from logs
            context += """
SPECIFIC ERROR DETAILS:
1. Error: "Expecting property name enclosed in double quotes: line 2 column 3 (char 4)"
2. Problematic line: "\"nodes\": ["
3. The failed JSON appears to have escaped quotes and possibly an extra comma after the opening bracket
"""
            
            # Perform hybrid analysis
            analysis_results = await self.hybrid_analysis(
                query="Fix the JSON parsing errors in this content and provide a corrected version",
                context=context,
                search_web=False  # Already included web search results
            )
            
            if not analysis_results.get("success", False):
                return analysis_results
            
            # Extract corrected JSON from analysis
            corrected_json = self._extract_json_from_text(analysis_results["analysis"])
            
            if not corrected_json:
                logger.warning("No corrected JSON found in analysis, applying manual fixes")
                corrected_json = self._apply_manual_json_fixes(failed_json)
            
            # Verify the corrected JSON
            try:
                parsed_json = json.loads(corrected_json)
                logger.info("Successfully parsed corrected JSON")
                
                # Save fixed JSON
                fixed_json_path = failed_json_path.replace("failed_json", "fixed_json")
                with open(fixed_json_path, "w") as f:
                    json.dump(parsed_json, f, indent=2)
                logger.info(f"Fixed JSON saved to: {fixed_json_path}")
                
                return {
                    "original_path": failed_json_path,
                    "fixed_path": fixed_json_path,
                    "fixed_json": parsed_json,
                    "success": True
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse corrected JSON: {e}")
                return {
                    "error": f"Failed to parse corrected JSON: {e}",
                    "success": False
                }
                
        except Exception as e:
            logger.error(f"Error fixing JSON parsing: {e}")
            import traceback
            error_details = traceback.format_exc()
            return {
                "error": str(e),
                "error_details": error_details,
                "success": False
            }
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON content from text."""
        # Look for JSON blocks
        json_pattern = r"```(?:json)?\s*({[\s\S]*?})```"
        matches = re.findall(json_pattern, text)
        
        if matches:
            return matches[0]
        
        # Try alternative pattern
        alt_pattern = r"{[\s\S]*\"nodes\"[\s\S]*\"edges\"[\s\S]*}"
        alt_matches = re.findall(alt_pattern, text)
        
        if alt_matches:
            return alt_matches[0]
        
        return None
    
    def _apply_manual_json_fixes(self, json_str: str) -> str:
        """Apply manual fixes to JSON string."""
        # Apply essential fixes to common JSON errors
        
        # Fix arrays with commas right after opening bracket
        json_str = re.sub(r'\[\s*,', '[', json_str)
        
        # Fix multiple escape characters
        json_str = re.sub(r'\\\\', '\\', json_str)
        
        # Fix escaped quotes
        json_str = re.sub(r'\\"', '"', json_str)
        json_str = re.sub(r'""', '"', json_str)
        
        # Fix trailing commas in objects and arrays
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Fix missing commas between objects
        json_str = re.sub(r'}(\s*){', r'},\1{', json_str)
        
        return json_str
    
    async def fix_memory_system(self, test_file_path: str) -> Dict[str, Any]:
        """
        Fix memory system initialization issues.
        
        Args:
            test_file_path: Path to the test file with issues
            
        Returns:
            Dictionary with fixes
        """
        logger.info(f"Fixing memory system initialization in: {test_file_path}")
        
        try:
            # Read the test file
            with open(test_file_path, "r") as f:
                test_file_content = f.read()
            
            # Create context with the test file content
            context = f"TEST FILE CONTENT:\n```python\n{test_file_content}\n```\n"
            
            # Add error details
            context += """
ERROR DETAILS:
1. Error: "ComposioMemoryBridge.__init__() got an unexpected keyword argument 'memory_path'"
2. The constructor parameters for ComposioMemoryBridge need to be fixed
3. Need to find correct constructor parameters for ComposioMemoryBridge
4. Need to create a mock ComposioClient for testing
"""
            
            # Search for memory bridge constructor info
            web_results = await self.web_search("ComposioMemoryBridge constructor parameters Python")
            if web_results.get("success", False):
                context += f"\nWEB SEARCH RESULTS ON MEMORY BRIDGE:\n{web_results['content']}\n"
            
            # Perform hybrid analysis
            analysis_results = await self.hybrid_analysis(
                query="Fix the memory system initialization issues in this test file",
                context=context,
                search_web=False  # Already included web search results
            )
            
            if not analysis_results.get("success", False):
                return analysis_results
            
            # Extract code fixes from analysis
            fixed_code = self._extract_code_from_text(analysis_results["analysis"])
            
            if not fixed_code:
                logger.warning("No fixed code found in analysis")
                return {
                    "error": "No fixed code found in analysis",
                    "success": False
                }
            
            # Save fixed code
            fixed_file_path = test_file_path.replace(".py", "_fixed.py")
            with open(fixed_file_path, "w") as f:
                f.write(fixed_code)
            logger.info(f"Fixed code saved to: {fixed_file_path}")
            
            return {
                "original_path": test_file_path,
                "fixed_path": fixed_file_path,
                "analysis": analysis_results["analysis"],
                "success": True
            }
                
        except Exception as e:
            logger.error(f"Error fixing memory system: {e}")
            import traceback
            error_details = traceback.format_exc()
            return {
                "error": str(e),
                "error_details": error_details,
                "success": False
            }
    
    def _extract_code_from_text(self, text: str) -> Optional[str]:
        """Extract code from text."""
        # Look for Python code blocks
        code_pattern = r"```(?:python)?\s*([\s\S]*?)```"
        matches = re.findall(code_pattern, text)
        
        if matches:
            # If there are multiple code blocks, choose the most relevant one
            # Look for a code block with ComposioMemoryBridge
            for match in matches:
                if "ComposioMemoryBridge" in match and "initialize_memory_system" in match:
                    return match
            
            # If no specific match found, return the largest code block
            return max(matches, key=len)
        
        return None

    async def update_test_kg_visualization(self, file_path: str) -> Dict[str, Any]:
        """
        Update the test_kg_visualization.py file to fix JSON parsing issues.
        
        Args:
            file_path: Path to the test_kg_visualization.py file
            
        Returns:
            Dictionary with fixes
        """
        logger.info(f"Updating test_kg_visualization.py: {file_path}")
        
        try:
            # Read the file
            with open(file_path, "r") as f:
                file_content = f.read()
            
            # Create context with the file content
            context = f"FILE CONTENT (relevant parts):\n```python\n{file_content[:1000]}\n...\n```\n"
            
            # Add specific requirements for JSON parsing fixes
            context += """
JSON PARSING ISSUES:
1. Need to add more robust JSON parsing for Claude responses
2. Specific error: "Expecting property name enclosed in double quotes: line 2 column 3 (char 4)"
3. Problematic line: "\"nodes\": ["
4. Need to fix arrays with commas right after opening bracket
5. Need to fix escaped quotes and other JSON formatting issues

SPECIFIC FIX NEEDED:
Add this regex pattern to fix arrays with commas after opening bracket:
```python
# Fix arrays with commas right after opening bracket
json_str = re.sub(r'\\[\\s*,', '[', json_str)
```

And improve error handling for malformed JSON.
"""
            
            # Search for JSON parsing fixes
            web_results = await self.web_search("fix JSON parsing Python regex common errors")
            if web_results.get("success", False):
                context += f"\nWEB SEARCH RESULTS ON JSON PARSING FIXES:\n{web_results['content']}\n"
            
            # Perform hybrid analysis
            analysis_results = await self.hybrid_analysis(
                query="Update the test_kg_visualization.py file to fix JSON parsing issues",
                context=context,
                search_web=False  # Already included web search results
            )
            
            if not analysis_results.get("success", False):
                return analysis_results
            
            # Extract code fixes from analysis
            json_parser_code = self._extract_json_parser_code(analysis_results["analysis"])
            
            if not json_parser_code:
                logger.warning("No JSON parser code found in analysis")
                return {
                    "error": "No JSON parser code found in analysis",
                    "success": False
                }
            
            # Create updated file content
            updated_content = self._update_json_parser_in_file(file_content, json_parser_code)
            
            # Save updated file
            updated_file_path = file_path.replace(".py", "_updated.py")
            with open(updated_file_path, "w") as f:
                f.write(updated_content)
            logger.info(f"Updated file saved to: {updated_file_path}")
            
            return {
                "original_path": file_path,
                "updated_path": updated_file_path,
                "analysis": analysis_results["analysis"],
                "success": True
            }
                
        except Exception as e:
            logger.error(f"Error updating test_kg_visualization.py: {e}")
            import traceback
            error_details = traceback.format_exc()
            return {
                "error": str(e),
                "error_details": error_details,
                "success": False
            }
    
    def _extract_json_parser_code(self, text: str) -> Optional[str]:
        """Extract JSON parser code from text."""
        # Look for JSON parsing code blocks
        parser_pattern = r"```(?:python)?\s*([\s\S]*?json_str[\s\S]*?)```"
        matches = re.findall(parser_pattern, text)
        
        if matches:
            return matches[0]
        
        return None
    
    def _update_json_parser_in_file(self, file_content: str, json_parser_code: str) -> str:
        """Update JSON parser in file content."""
        # Find JSON parsing section in file
        parser_section_pattern = r"(# Clean up the JSON string[\s\S]*?)try:[\s\S]*?graph_data = json\.loads\(json_str\)"
        parser_section_match = re.search(parser_section_pattern, file_content)
        
        if parser_section_match:
            # Replace the parser section with the improved code
            updated_content = file_content.replace(
                parser_section_match.group(0),
                f"{json_parser_code}\n            try:\n                graph_data = json.loads(json_str)"
            )
            return updated_content
        
        return file_content

async def main():
    """Run the troubleshooter."""
    try:
        logger.info("Starting hybrid troubleshooter")
        
        # Initialize troubleshooter
        troubleshooter = HybridTroubleshooter()
        
        # 1. Fix JSON parsing issues in the failed JSON file
        failed_json_path = "output/test_kg/failed_json_20250315_001539.json"
        if os.path.exists(failed_json_path):
            logger.info(f"Fixing JSON parsing issues in: {failed_json_path}")
            json_result = await troubleshooter.fix_json_parsing(failed_json_path)
            
            if json_result.get("success", False):
                logger.info(f"Successfully fixed JSON parsing issues: {json_result.get('fixed_path')}")
            else:
                logger.error(f"Failed to fix JSON parsing issues: {json_result.get('error')}")
        else:
            logger.warning(f"Failed JSON file not found: {failed_json_path}")
        
        # 2. Update test_kg_visualization.py with improved JSON parsing
        test_kg_path = "test_kg_visualization.py"
        if os.path.exists(test_kg_path):
            logger.info(f"Updating JSON parsing in: {test_kg_path}")
            update_result = await troubleshooter.update_test_kg_visualization(test_kg_path)
            
            if update_result.get("success", False):
                logger.info(f"Successfully updated JSON parsing: {update_result.get('updated_path')}")
            else:
                logger.error(f"Failed to update JSON parsing: {update_result.get('error')}")
        else:
            logger.warning(f"Test KG file not found: {test_kg_path}")
        
        # 3. Fix memory system initialization
        test_memory_path = "test_advanced_memory.py"
        if os.path.exists(test_memory_path):
            logger.info(f"Fixing memory system initialization in: {test_memory_path}")
            memory_result = await troubleshooter.fix_memory_system(test_memory_path)
            
            if memory_result.get("success", False):
                logger.info(f"Successfully fixed memory system: {memory_result.get('fixed_path')}")
            else:
                logger.error(f"Failed to fix memory system: {memory_result.get('error')}")
        else:
            logger.warning(f"Test memory file not found: {test_memory_path}")
        
        logger.info("Hybrid troubleshooter completed")
        
        print("\n========== TROUBLESHOOTING SUMMARY ==========")
        print("1. JSON Parsing Issues:")
        if 'json_result' in locals() and json_result.get("success", False):
            print("  ✅ Fixed JSON parsing issues")
            print(f"  📄 Fixed JSON saved to: {json_result.get('fixed_path')}")
        else:
            print("  ❌ Failed to fix JSON parsing issues")
        
        print("\n2. Test KG Visualization:")
        if 'update_result' in locals() and update_result.get("success", False):
            print("  ✅ Updated JSON parsing code")
            print(f"  📄 Updated file saved to: {update_result.get('updated_path')}")
        else:
            print("  ❌ Failed to update JSON parsing code")
        
        print("\n3. Memory System Initialization:")
        if 'memory_result' in locals() and memory_result.get("success", False):
            print("  ✅ Fixed memory system initialization")
            print(f"  📄 Fixed file saved to: {memory_result.get('fixed_path')}")
        else:
            print("  ❌ Failed to fix memory system initialization")
        
        print("\nNext steps:")
        print("1. Review and apply the generated fixes")
        print("2. Run the tests again to verify fixes")
        print("3. Make any additional manual adjustments as needed")
        print("==============================================")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 