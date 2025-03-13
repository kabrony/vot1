#!/usr/bin/env python3
"""
MCP Code Analysis Automation

This script provides automated code analysis using the Model Control Protocol (MCP)
with a hybrid model approach, optimizing for both performance and cost.
"""

import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.vot_mcp import VotModelControlProtocol
from src.vot1.code_analyzer import CodeAnalyzer
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
        logging.FileHandler(os.path.join('logs', 'mcp_code_analysis.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class McpCodeAnalyzer:
    """
    Code analyzer using MCP with hybrid model approach.
    
    This class provides automated code analysis using MCP with hybrid model selection
    based on task complexity.
    """
    
    def __init__(
        self,
        mcp_automation: Optional[McpHybridAutomation] = None,
        use_extended_thinking: bool = True,
        max_thinking_tokens: int = 8000
    ):
        """
        Initialize the MCP code analyzer.
        
        Args:
            mcp_automation: Optional existing MCP automation instance
            use_extended_thinking: Whether to enable extended thinking for complex tasks
            max_thinking_tokens: Maximum thinking tokens when extended thinking is enabled
        """
        # Use provided MCP automation or create a new one
        self.mcp_automation = mcp_automation or McpHybridAutomation(
            use_extended_thinking=use_extended_thinking,
            max_thinking_tokens=max_thinking_tokens
        )
        
        # Initialize code analyzer
        self.code_analyzer = CodeAnalyzer(mcp=self.mcp_automation.mcp)
        
        logger.info("MCP Code Analyzer initialized")
    
    def analyze_file(
        self,
        file_path: str,
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single file using MCP.
        
        Args:
            file_path: Path to the file to analyze
            analysis_types: Types of analysis to perform (None for all)
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing file: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Perform analysis
            return self.code_analyzer.analyze_code(
                content=content,
                file_path=file_path,
                analysis_types=analysis_types
            )
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                "error": str(e),
                "issues": []
            }
    
    def analyze_directory(
        self,
        directory: str,
        extensions: List[str] = ['.py', '.js', '.html', '.css'],
        include_subdirs: bool = True,
        exclude_dirs: Optional[List[str]] = None,
        analysis_types: Optional[List[str]] = None,
        max_files: Optional[int] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all files in a directory using MCP.
        
        Args:
            directory: Directory to analyze
            extensions: File extensions to include
            include_subdirs: Whether to include subdirectories
            exclude_dirs: Directories to exclude
            analysis_types: Types of analysis to perform (None for all)
            max_files: Maximum number of files to analyze
            output_file: Optional file to save results to
            
        Returns:
            Analysis results by file path
        """
        logger.info(f"Analyzing directory: {directory}")
        logger.info(f"Extensions: {extensions}")
        logger.info(f"Include subdirectories: {include_subdirs}")
        if exclude_dirs:
            logger.info(f"Excluding directories: {exclude_dirs}")
        if max_files:
            logger.info(f"Maximum files: {max_files}")
        
        # Default exclude directories
        exclude_dirs = exclude_dirs or ['.git', '__pycache__', 'node_modules', 'venv', '.venv']
        
        # Find files to analyze
        files_to_analyze = self._find_files(
            directory=directory,
            extensions=extensions,
            include_subdirs=include_subdirs,
            exclude_dirs=exclude_dirs,
            max_files=max_files
        )
        
        logger.info(f"Found {len(files_to_analyze)} files to analyze")
        
        # Analyze each file
        results = {}
        for i, file_path in enumerate(files_to_analyze):
            logger.info(f"Analyzing file {i+1}/{len(files_to_analyze)}: {file_path}")
            
            # Analyze file
            file_results = self.analyze_file(
                file_path=file_path,
                analysis_types=analysis_types
            )
            
            # Store results
            results[file_path] = file_results
            
            # Log results
            issue_count = len(file_results.get("issues", []))
            logger.info(f"Found {issue_count} issues in {file_path}")
        
        # Save results if output file specified
        if output_file:
            self._save_results(results, output_file)
        
        return results
    
    def _find_files(
        self,
        directory: str,
        extensions: List[str],
        include_subdirs: bool,
        exclude_dirs: List[str],
        max_files: Optional[int] = None
    ) -> List[str]:
        """Find files to analyze in the directory."""
        files = []
        
        # Normalize extensions to include dot
        normalized_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        
        # Convert exclude_dirs to absolute paths
        base_dir = os.path.abspath(directory)
        absolute_exclude_dirs = [os.path.join(base_dir, d) for d in exclude_dirs]
        
        # Walk directory
        for root, dirs, filenames in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in absolute_exclude_dirs 
                      and d not in exclude_dirs]
            
            # Skip subdirectories if not included
            if not include_subdirs and root != directory:
                continue
            
            # Add files with matching extensions
            for filename in filenames:
                if any(filename.endswith(ext) for ext in normalized_extensions):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
            
            # Break if max files reached
            if max_files and len(files) >= max_files:
                files = files[:max_files]
                break
        
        return files
    
    def _save_results(self, results: Dict[str, Dict[str, Any]], output_file: str) -> None:
        """Save analysis results to a file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved analysis results to {output_file}")
    
    def generate_summary(
        self,
        results: Dict[str, Dict[str, Any]],
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate a summary of analysis results using MCP.
        
        Args:
            results: Analysis results by file path
            output_file: Optional file to save summary to
            
        Returns:
            Summary text
        """
        logger.info("Generating summary of analysis results")
        
        # Prepare analysis data
        file_count = len(results)
        issue_count = sum(len(file_result.get("issues", [])) for file_result in results.values())
        
        # Count issues by type and severity
        issue_types = {}
        severities = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for file_path, file_result in results.items():
            for issue in file_result.get("issues", []):
                # Count by type
                issue_type = issue.get("type", "unknown")
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1
                
                # Count by severity
                severity = issue.get("severity", "info").lower()
                if severity in severities:
                    severities[severity] += 1
        
        # Generate summary prompt
        summary_prompt = f"""
        Generate a comprehensive summary of the code analysis results.
        
        Analysis overview:
        - Files analyzed: {file_count}
        - Total issues found: {issue_count}
        - Issues by severity:
          - Critical: {severities['critical']}
          - High: {severities['high']}
          - Medium: {severities['medium']}
          - Low: {severities['low']}
          - Info: {severities['info']}
        - Issues by type:
        {json.dumps(issue_types, indent=2)}
        
        Please provide:
        1. A concise executive summary of the findings
        2. Key areas of concern prioritized by severity and frequency
        3. General recommendations for improvement
        4. Strengths identified in the codebase
        
        Format the summary in markdown for readability.
        """
        
        # Use MCP to generate summary
        response = self.mcp_automation.process_with_optimal_model(
            prompt=summary_prompt,
            task_complexity="high",  # Use primary model for summary
            system="You are an expert code reviewer providing a summary of code analysis results. Your summary is clear, actionable, and focuses on the most important findings.",
            max_tokens=4096
        )
        
        summary = response.get("content", "Error generating summary")
        
        # Save summary if output file specified
        if output_file:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Save summary
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            logger.info(f"Saved summary to {output_file}")
        
        return summary

def main():
    """Main function to handle command-line arguments and run code analysis."""
    parser = argparse.ArgumentParser(description="VOT1 MCP Code Analysis Automation")
    
    parser.add_argument("directory", help="Directory to analyze")
    parser.add_argument("--extensions", nargs="+", default=['.py', '.js', '.html', '.css'],
                      help="File extensions to analyze")
    parser.add_argument("--exclude-dirs", nargs="+", 
                      default=['.git', '__pycache__', 'node_modules', 'venv', '.venv'],
                      help="Directories to exclude")
    parser.add_argument("--no-subdirs", action="store_true",
                      help="Do not include subdirectories")
    parser.add_argument("--max-files", type=int, default=None,
                      help="Maximum number of files to analyze")
    parser.add_argument("--output", type=str, default=None,
                      help="File to save analysis results to")
    parser.add_argument("--summary", type=str, default=None,
                      help="File to save analysis summary to")
    parser.add_argument("--no-extended-thinking", action="store_true",
                      help="Disable extended thinking mode")
    parser.add_argument("--thinking-tokens", type=int, default=8000,
                      help="Maximum thinking tokens when extended thinking is enabled")
    
    args = parser.parse_args()
    
    # Initialize MCP code analyzer
    analyzer = McpCodeAnalyzer(
        use_extended_thinking=not args.no_extended_thinking,
        max_thinking_tokens=args.thinking_tokens
    )
    
    # Run analysis
    results = analyzer.analyze_directory(
        directory=args.directory,
        extensions=args.extensions,
        include_subdirs=not args.no_subdirs,
        exclude_dirs=args.exclude_dirs,
        max_files=args.max_files,
        output_file=args.output
    )
    
    # Generate and print summary
    if args.summary or args.output:
        summary = analyzer.generate_summary(
            results=results,
            output_file=args.summary
        )
        if not args.summary:
            print(summary)
    else:
        # Print results overview
        print(f"Analysis complete. Found {len(results)} files.")
        total_issues = sum(len(file_result.get('issues', [])) for file_result in results.values())
        print(f"Total issues found: {total_issues}")
        
        # Print issues by file
        for file_path, file_result in results.items():
            issues = file_result.get('issues', [])
            if issues:
                print(f"\n{file_path}: {len(issues)} issues")
                for issue in issues[:5]:  # Limit to first 5 issues for display
                    print(f"- [{issue.get('severity', 'unknown').upper()}] {issue.get('type')}: {issue.get('message')}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more issues")

if __name__ == "__main__":
    main() 