#!/usr/bin/env python3
"""
JSON Fixer with Claude 3.7 Sonnet

This script provides tools to fix malformed JSON using Claude 3.7 Sonnet's
hybrid reasoning capabilities. It's particularly useful for repairing JSON
from knowledge graph visualization responses.
"""

import os
import sys
import json
import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JSONFixer")

# Import required libraries
try:
    import anthropic
except ImportError:
    logger.error("Anthropic not installed. Install with: pip install anthropic")
    sys.exit(1)

class JSONFixer:
    """
    Fix malformed JSON using Claude 3.7 Sonnet.
    
    This class provides methods to analyze and repair JSON that has syntax
    errors, particularly focusing on JSON generated for knowledge graphs.
    """
    
    def __init__(self, model: str = None, output_dir: str = None):
        """
        Initialize the JSON Fixer.
        
        Args:
            model: Claude model to use
            output_dir: Directory to save outputs
        """
        # Load environment variables from .env file
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
        
        # Configure Claude API
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.claude_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        self.claude_model = model or os.environ.get("VOT1_PRIMARY_MODEL", "claude-3-7-sonnet-20240219")
        
        # Create output directory
        self.output_dir = output_dir or os.path.join("output", "json_fixer")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Common JSON error patterns
        self.error_patterns = {
            "extra_comma_after_bracket": r'\[\s*,',
            "missing_comma_between_items": r'}\s*{',
            "trailing_comma": r',\s*[}\]]',
            "unescaped_quote": r'(?<!\\)"(?![\s,:}\]])',
        }
        
        logger.info(f"Initialized JSONFixer with Claude model: {self.claude_model}")
    
    def analyze_json_error(self, error_msg: str, json_str: str) -> Dict[str, Any]:
        """
        Analyze a JSON error and return information about it.
        
        Args:
            error_msg: The error message from the JSON parser
            json_str: The malformed JSON string
            
        Returns:
            Dictionary with error analysis
        """
        error_info = {
            "error_message": error_msg,
            "detected_issues": []
        }
        
        # Extract error position
        position_match = re.search(r"line (\d+) column (\d+) \(char (\d+)\)", error_msg)
        if position_match:
            line_num = int(position_match.group(1))
            col_num = int(position_match.group(2))
            char_pos = int(position_match.group(3))
            
            error_info["line"] = line_num
            error_info["column"] = col_num
            error_info["char_position"] = char_pos
            
            # Get the problematic line
            lines = json_str.split('\n')
            if 0 <= line_num - 1 < len(lines):
                error_info["problematic_line"] = lines[line_num - 1]
                
                # Add context (lines before and after)
                context_lines = []
                for i in range(max(0, line_num - 3), min(len(lines), line_num + 2)):
                    prefix = ">>> " if i == line_num - 1 else "    "
                    context_lines.append(f"{prefix}{i+1}: {lines[i]}")
                error_info["context"] = "\n".join(context_lines)
        
        # Check for known error patterns
        for pattern_name, pattern in self.error_patterns.items():
            if re.search(pattern, json_str):
                error_info["detected_issues"].append(pattern_name)
        
        # Look for bracket balance issues
        opening_counts = json_str.count('{') + json_str.count('[')
        closing_counts = json_str.count('}') + json_str.count(']')
        
        if opening_counts > closing_counts:
            error_info["detected_issues"].append("missing_closing_brackets")
            error_info["bracket_imbalance"] = opening_counts - closing_counts
        elif closing_counts > opening_counts:
            error_info["detected_issues"].append("unexpected_closing_brackets")
            error_info["bracket_imbalance"] = closing_counts - opening_counts
        
        return error_info
    
    def apply_quick_fixes(self, json_str: str) -> Dict[str, Any]:
        """
        Apply quick fixes to common JSON syntax errors.
        
        Args:
            json_str: The malformed JSON string
            
        Returns:
            Dictionary with fix results
        """
        try:
            # Make a copy of the original string
            fixed_json = json_str
            
            # Remove extra commas after opening brackets
            fixed_json = re.sub(r'\[\s*,', '[', fixed_json)
            
            # Remove trailing commas in arrays
            fixed_json = re.sub(r',\s*\]', ']', fixed_json)
            
            # Remove trailing commas in objects
            fixed_json = re.sub(r',\s*\}', '}', fixed_json)
            
            # Add missing commas between object entries
            fixed_json = re.sub(r'"\s*\n\s*"', '",\n"', fixed_json)
            
            # Validate the fixed JSON
            try:
                json.loads(fixed_json)
                is_valid = True
            except json.JSONDecodeError as e:
                is_valid = False
                error = str(e)
            
            # Create result
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result = {
                "original_json": json_str,
                "fixed_json_str": fixed_json,
                "is_valid": is_valid,
                "timestamp": datetime.now().isoformat()
            }
            
            if not is_valid:
                result["error"] = error
            
            # Save original and fixed JSON
            original_file = os.path.join(self.output_dir, f"original_{timestamp}.json")
            with open(original_file, "w") as f:
                f.write(json_str)
            
            fixed_file = os.path.join(self.output_dir, f"rule_fixed_{timestamp}.json")
            with open(fixed_file, "w") as f:
                f.write(fixed_json)
            
            result["original_file"] = original_file
            result["fixed_file"] = fixed_file
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying quick fixes: {e}")
            import traceback
            return {
                "error": str(e),
                "error_details": traceback.format_exc(),
                "original_json": json_str,
                "is_valid": False
            }
    
    def extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON from markdown code blocks.
        
        Args:
            text: Text potentially containing markdown JSON code blocks
            
        Returns:
            Extracted JSON string or original if no code blocks found
        """
        # Find JSON code blocks
        json_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)```', text)
        
        if json_blocks:
            # Return the largest code block (most likely to be complete)
            return max(json_blocks, key=len).strip()
        
        # No code blocks found, look for JSON-like structure
        json_like = re.search(r'(\{[\s\S]*\})', text)
        if json_like:
            return json_like.group(1).strip()
        
        # Return original as fallback
        return text
    
    async def fix_with_claude(self, json_str: str, error_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Use Claude 3.7 Sonnet to fix malformed JSON.
        
        Args:
            json_str: The malformed JSON string
            error_info: Optional error analysis info
            
        Returns:
            Dictionary with fix results
        """
        try:
            # Create prompt with detailed instructions
            prompt = """I need help fixing malformed JSON. Please correct the syntax errors and return ONLY valid JSON without any additional text, explanations, or markdown.

Here's the malformed JSON:
```
{json_str}
```
""".format(json_str=json_str)
            
            if error_info:
                prompt += """
Error message: {error_message}

Problematic context:
{context}

Detected issues: {issues}
""".format(
                    error_message=error_info.get("error_message", "Unknown error"),
                    context=error_info.get("context", ""),
                    issues=", ".join(error_info.get("detected_issues", ["Unknown"]))
                )
            
            # System message focusing on JSON fixing
            system_message = """You are Claude 3.7 Sonnet, an expert in fixing malformed JSON.
            
Your task is to repair the provided JSON by:
1. Identifying syntax errors (missing commas, extra commas, unclosed brackets, etc.)
2. Fixing the structure while preserving as much of the original content as possible
3. ONLY returning the fixed, valid JSON without any explanations or markdown

Rules:
- Return ONLY the fixed JSON, nothing else
- Do not add explanations or comments about the fixes
- Do not wrap your response in code blocks or markdown
- Ensure the JSON is properly formatted and valid
- Preserve the original data structure (nodes, edges, etc.)

The response should be ONLY the fixed JSON that can be directly parsed by JSON.parse() or json.loads().
"""
            
            # Make API call with Claude
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4000,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract the fixed JSON
            fixed_json_str = response.content[0].text if response.content else ""
            fixed_json_str = self.extract_json_from_markdown(fixed_json_str)
            
            # Validate by parsing it
            try:
                fixed_json = json.loads(fixed_json_str)
                is_valid = True
            except json.JSONDecodeError as e:
                fixed_json = None
                is_valid = False
                fix_error = str(e)
            
            # Create result
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result = {
                "original_json": json_str,
                "fixed_json_str": fixed_json_str,
                "is_valid": is_valid,
                "timestamp": datetime.now().isoformat(),
                "model": self.claude_model,
                "success": is_valid
            }
            
            if not is_valid:
                result["fix_error"] = fix_error
            
            # Save original and fixed JSON
            original_file = os.path.join(self.output_dir, f"original_{timestamp}.json")
            with open(original_file, "w") as f:
                f.write(json_str)
            
            fixed_file = os.path.join(self.output_dir, f"fixed_{timestamp}.json")
            with open(fixed_file, "w") as f:
                f.write(fixed_json_str)
            
            result["original_file"] = original_file
            result["fixed_file"] = fixed_file
            
            return result
            
        except Exception as e:
            logger.error(f"Error fixing JSON with Claude: {e}")
            import traceback
            return {
                "error": str(e),
                "error_details": traceback.format_exc(),
                "original_json": json_str,
                "success": False
            }
    
    async def fix_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        Fix a JSON file that contains malformed JSON.
        
        Args:
            file_path: Path to the file with malformed JSON
            
        Returns:
            Dictionary with fix results
        """
        try:
            # Read the file
            with open(file_path, 'r') as f:
                json_str = f.read()
            
            # Try to parse it first
            try:
                json.loads(json_str)
                logger.info(f"File {file_path} already contains valid JSON")
                return {
                    "file_path": file_path,
                    "is_valid": True,
                    "message": "File already contains valid JSON",
                    "success": True
                }
            except json.JSONDecodeError as e:
                # Analyze the error
                error_info = self.analyze_json_error(str(e), json_str)
                
                # Try quick fixes first
                quick_fixed = self.apply_quick_fixes(json_str)
                
                try:
                    json.loads(quick_fixed)
                    # Quick fix worked
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    fixed_file = os.path.join(self.output_dir, f"quick_fixed_{timestamp}.json")
                    with open(fixed_file, 'w') as f:
                        f.write(quick_fixed)
                    
                    logger.info(f"Quick fix successful for {file_path}")
                    return {
                        "file_path": file_path,
                        "fixed_file": fixed_file,
                        "is_valid": True,
                        "method": "quick_fix",
                        "error_info": error_info,
                        "success": True
                    }
                except json.JSONDecodeError:
                    # Quick fix didn't work, use Claude
                    logger.info(f"Quick fix failed for {file_path}, trying Claude")
                    return await self.fix_with_claude(json_str, error_info)
        
        except Exception as e:
            logger.error(f"Error fixing JSON file: {e}")
            import traceback
            return {
                "error": str(e),
                "error_details": traceback.format_exc(),
                "file_path": file_path,
                "success": False
            }
    
    async def scan_and_fix_directory(self, directory: str, pattern: str = "*failed_json*.json") -> Dict[str, Any]:
        """
        Scan a directory for failed JSON files and fix them.
        
        Args:
            directory: Directory to scan
            pattern: Glob pattern to match files
            
        Returns:
            Dictionary with fix results for all files
        """
        try:
            # Find all matching files
            all_files = list(Path(directory).glob(pattern))
            
            if not all_files:
                logger.warning(f"No files matching pattern {pattern} found in {directory}")
                return {
                    "directory": directory,
                    "pattern": pattern,
                    "message": "No matching files found",
                    "success": True,
                    "files_processed": 0
                }
            
            # Process each file
            results = {}
            for file_path in all_files:
                logger.info(f"Processing file: {file_path}")
                file_result = await self.fix_json_file(str(file_path))
                results[str(file_path)] = file_result
            
            # Create summary
            success_count = sum(1 for r in results.values() if r.get("success", False))
            
            summary = {
                "directory": directory,
                "pattern": pattern,
                "files_processed": len(results),
                "files_fixed": success_count,
                "success_rate": f"{success_count}/{len(results)}",
                "results": results,
                "success": True
            }
            
            # Save summary
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_file = os.path.join(self.output_dir, f"fix_summary_{timestamp}.json")
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            summary["summary_file"] = summary_file
            return summary
        
        except Exception as e:
            logger.error(f"Error scanning and fixing directory: {e}")
            import traceback
            return {
                "error": str(e),
                "error_details": traceback.format_exc(),
                "directory": directory,
                "pattern": pattern,
                "success": False
            }

async def main():
    """Main entry point for the script"""
    # Initialize the JSON Fixer
    fixer = JSONFixer()
    
    # Example corrupted JSON
    corrupted_json = """{
      "nodes": [,
        {
          "id": "concept1",
          "label": "Concept 1",
          "type": "primary"
        },
        {
          "id": "concept2",
          "label": "Concept 2"
          "type": "secondary"
        }
      ],
      "edges": [
        {
          "source": "concept1",
          "target": "concept2",
          "label": "relates to"
        },
      ]
    }"""
    
    # Analyze issues
    print("Analyzing JSON issues...")
    try:
        json.loads(corrupted_json)
        print("JSON is valid (unexpected)")
        analysis = {"success": False, "error": "No error found"}
    except json.JSONDecodeError as e:
        print(f"JSON error (expected): {e}")
        # Analyze the error
        analysis = fixer.analyze_json_error(str(e), corrupted_json)
    
    if analysis and "detected_issues" in analysis:
        print("✅ Issues identified:")
        for i, issue in enumerate(analysis.get("detected_issues", []), 1):
            print(f"  {i}. {issue}")
    else:
        print(f"❌ Error analyzing JSON: {analysis.get('error') if analysis else 'Unknown error'}")
    
    # Fix with rule-based approach
    print("\nFixing with rule-based approach...")
    rule_result = fixer.apply_quick_fixes(corrupted_json)
    
    if rule_result.get("is_valid", False):
        print("✅ JSON fixed with rules!")
        print(f"Fixed JSON: {rule_result.get('fixed_json_str')}")
    else:
        print(f"❌ Error fixing with rules: {rule_result.get('error')}")
    
    # Fix with Claude
    print("\nFixing with Claude...")
    claude_result = await fixer.fix_with_claude(corrupted_json, analysis)
    
    if claude_result.get("is_valid", False):
        print("✅ JSON fixed with Claude!")
        print(f"Fixed JSON saved to: {claude_result.get('fixed_file')}")
    else:
        print(f"❌ Error fixing with Claude: {claude_result.get('error')}")
    
    print("\nJSON Fixing complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 