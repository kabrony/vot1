#!/usr/bin/env python3
"""
VOT1 Troubleshooter

This is the main troubleshooter script for the VOT1 system.
It provides a unified interface to troubleshoot and fix issues
with knowledge graphs, memory systems, and other components.
"""

import os
import sys
import json
import asyncio
import logging
import argparse
import importlib.util
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("vot1_troubleshooter.log")
    ]
)
logger = logging.getLogger("VOT1Troubleshooter")

# Check for required modules
required_modules = ["anthropic", "dotenv"]
missing_modules = []

for module in required_modules:
    if importlib.util.find_spec(module) is None:
        missing_modules.append(module)

if missing_modules:
    logger.error(f"Missing required modules: {', '.join(missing_modules)}")
    logger.error("Please install them with: pip install " + " ".join(missing_modules))
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("dotenv module not found, using existing environment variables")

# Import other troubleshooter modules
try:
    from hybrid_reasoning import HybridReasoning
except ImportError:
    logger.error("Could not import HybridReasoning. Make sure hybrid_reasoning.py is in the current directory.")
    sys.exit(1)

try:
    from json_fixer import JSONFixer
except ImportError:
    logger.error("Could not import JSONFixer. Make sure json_fixer.py is in the current directory.")
    sys.exit(1)

try:
    from memory_troubleshooter import MemorySystemTroubleshooter
except ImportError:
    logger.error("Could not import MemorySystemTroubleshooter. Make sure memory_troubleshooter.py is in the current directory.")
    sys.exit(1)

class VOT1Troubleshooter:
    """
    Main troubleshooter for the VOT1 system.
    
    This class integrates the various troubleshooter components and
    provides a unified interface for fixing VOT1 issues.
    """
    
    def __init__(self):
        """Initialize the troubleshooter."""
        self.hybrid_reasoning = HybridReasoning()
        self.json_fixer = JSONFixer()
        self.memory_troubleshooter = MemorySystemTroubleshooter()
        
        logger.info("VOT1 Troubleshooter initialized")
    
    async def fix_knowledge_graph_json(self, directory="output/test_kg", pattern="*failed_json*.json"):
        """
        Fix malformed JSON in knowledge graph output files.
        
        Args:
            directory: Directory containing failed JSON files
            pattern: File name pattern to match
            
        Returns:
            Dictionary with fix results
        """
        logger.info(f"Fixing knowledge graph JSON in {directory} with pattern {pattern}")
        
        # Scan directory for failed JSON files and fix them
        fix_results = await self.json_fixer.scan_and_fix_directory(directory, pattern)
        
        # Summarize results
        files_processed = fix_results.get("files_processed", 0)
        files_fixed = fix_results.get("files_fixed", 0)
        
        print(f"\n📊 Knowledge Graph JSON Fix Summary:")
        print(f"  - Processed {files_processed} files")
        print(f"  - Fixed {files_fixed} files")
        
        if files_fixed > 0:
            print(f"  - Summary saved to: {fix_results.get('summary_file', 'unknown')}")
        
        return fix_results
    
    async def fix_memory_bridge_issues(self, auto_apply=False):
        """
        Fix issues with the memory bridge.
        
        Args:
            auto_apply: Whether to automatically apply fixes
            
        Returns:
            Dictionary with fix results
        """
        logger.info("Fixing memory bridge issues")
        
        # Find the memory bridge module
        bridge_module = self.memory_troubleshooter.find_memory_bridge_module()
        
        if not bridge_module:
            print("\n⚠️ Could not find ComposioMemoryBridge module.")
            
            # Ask if we should create a dummy implementation
            print("Would you like to create a dummy ComposioClient and DummyMemoryBridge for testing? (yes/no)")
            create_dummy = input().lower().strip()
            
            if create_dummy in ('y', 'yes'):
                dummy_file = self.memory_troubleshooter.create_dummy_composio_client()
                print(f"✅ Created dummy implementation at: {dummy_file}")
                return {
                    "status": "dummy_created",
                    "dummy_file": dummy_file
                }
            else:
                return {
                    "status": "no_module",
                    "message": "ComposioMemoryBridge module not found"
                }
        
        # Find uses of the memory bridge
        self.memory_troubleshooter.find_memory_bridge_uses()
        
        # Analyze bridge signature
        param_info = self.memory_troubleshooter.analyze_bridge_signature()
        
        # Analyze initialization calls
        issues = self.memory_troubleshooter.analyze_init_calls()
        
        # Generate/apply fix suggestions
        fix_results = self.memory_troubleshooter.fix_memory_bridge_issues(auto_apply=auto_apply)
        
        # Summarize results
        print("\n📊 Memory Bridge Fix Summary:")
        
        if param_info:
            print("\n  Parameters found in ComposioMemoryBridge:")
            for param in param_info:
                required = "Required" if param["required"] else "Optional"
                default = f" (default: {param['default']})" if param["default"] else ""
                print(f"    - {param['name']}: {required}{default}")
        
        if issues:
            print(f"\n  Found {len(issues)} issues in memory bridge initialization calls")
            
            for i, issue in enumerate(issues, 1):
                print(f"\n  Issue {i}:")
                print(f"    - Type: {issue['type']}")
                print(f"    - File: {issue['file_path']}")
                
                if issue['type'] == 'invalid_parameters':
                    print(f"    - Invalid parameters: {', '.join(issue['invalid_params'])}")
                elif issue['type'] == 'missing_required':
                    print(f"    - Missing required: {', '.join(issue['missing_params'])}")
            
            if fix_results.get("status") == "fixes_applied":
                print(f"\n  ✅ Applied {fix_results.get('applied_count', 0)} fixes")
                print(f"  📄 Report saved to: {fix_results.get('suggestion_file', 'unknown')}")
            elif fix_results.get("status") == "fixes_suggested":
                print(f"\n  ⚠️ Generated {fix_results.get('fixes_count', 0)} fix suggestions")
                print(f"  📄 Suggestions saved to: {fix_results.get('suggestion_file', 'unknown')}")
                
                if not auto_apply:
                    print("\n  To apply these fixes, run:")
                    print("    python vot1_troubleshooter.py --fix-memory --apply")
        else:
            print("  ✅ No issues found with memory bridge initialization")
        
        return fix_results
    
    async def analyze_issues_with_hybrid_reasoning(self, problem_description):
        """
        Analyze issues using Claude's hybrid reasoning.
        
        Args:
            problem_description: Description of the problem to analyze
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Analyzing issues with hybrid reasoning")
        
        # Use hybrid reasoning to analyze the problem
        result = await self.hybrid_reasoning.solve_problem(
            problem=problem_description,
            domain="programming"
        )
        
        if result.get("success", False):
            print("\n📊 Hybrid Reasoning Analysis:")
            print(f"  - Problem analyzed: {problem_description[:50]}...")
            print(f"  - Solution saved to: {result.get('output_file', 'unknown')}")
            
            # Print a preview of the solution
            solution = result.get("solution", "")
            preview_lines = solution.split("\n")[:5]
            preview = "\n".join(preview_lines)
            
            print("\nSolution preview:")
            print(f"{preview}")
            
            if len(solution.split("\n")) > 5:
                print("... (see full solution in the output file)")
        else:
            print("\n❌ Error analyzing problem with hybrid reasoning:")
            print(f"  - Error: {result.get('error', 'Unknown error')}")
        
        return result
    
    async def run_interactive_troubleshooter(self):
        """
        Run the troubleshooter in interactive mode.
        
        This function presents a menu of options and guides the user
        through the troubleshooting process.
        """
        print("\n===============================")
        print("  VOT1 Interactive Troubleshooter")
        print("===============================\n")
        
        print("This troubleshooter will help you fix issues with the VOT1 system.")
        print("Please select one of the following options:\n")
        
        while True:
            print("\n1. Fix malformed JSON in knowledge graph output files")
            print("2. Fix memory bridge initialization issues")
            print("3. Analyze issues with hybrid reasoning")
            print("4. Run all troubleshooting tools")
            print("5. Exit\n")
            
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                directory = input("\nEnter directory with failed JSON files (default: output/test_kg): ").strip()
                if not directory:
                    directory = "output/test_kg"
                
                pattern = input("Enter file pattern (default: *failed_json*.json): ").strip()
                if not pattern:
                    pattern = "*failed_json*.json"
                
                await self.fix_knowledge_graph_json(directory, pattern)
            
            elif choice == '2':
                apply_fixes = input("\nAutomatically apply fixes? (yes/no, default: no): ").strip().lower()
                auto_apply = apply_fixes in ('y', 'yes')
                
                await self.fix_memory_bridge_issues(auto_apply)
            
            elif choice == '3':
                print("\nPlease describe the issue you're experiencing:")
                problem_lines = []
                
                print("(Enter your description, finish with a blank line)")
                while True:
                    line = input()
                    if not line:
                        break
                    problem_lines.append(line)
                
                if problem_lines:
                    problem_description = "\n".join(problem_lines)
                    await self.analyze_issues_with_hybrid_reasoning(problem_description)
                else:
                    print("No problem description provided.")
            
            elif choice == '4':
                print("\nRunning all troubleshooting tools...")
                
                # Fix knowledge graph JSON
                await self.fix_knowledge_graph_json()
                
                # Fix memory bridge issues (without auto-applying)
                await self.fix_memory_bridge_issues(auto_apply=False)
                
                # Ask for problem description for hybrid reasoning
                print("\nPlease describe any other issues you're experiencing:")
                print("(Enter your description, finish with a blank line)")
                
                problem_lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    problem_lines.append(line)
                
                if problem_lines:
                    problem_description = "\n".join(problem_lines)
                    await self.analyze_issues_with_hybrid_reasoning(problem_description)
            
            elif choice == '5':
                print("\nExiting troubleshooter. Goodbye!")
                break
            
            else:
                print("\nInvalid choice. Please enter a number between 1 and 5.")
            
            print("\nPress Enter to continue...")
            input()
    
    async def run_cli_mode(self, args):
        """
        Run the troubleshooter in command-line mode.
        
        Args:
            args: Command-line arguments
            
        Returns:
            0 on success, non-zero on error
        """
        # Track if any errors occurred
        had_errors = False
        
        # Fix knowledge graph JSON if requested
        if args.fix_json:
            result = await self.fix_knowledge_graph_json(
                directory=args.json_dir,
                pattern=args.json_pattern
            )
            had_errors = had_errors or not result.get("success", False)
        
        # Fix memory bridge issues if requested
        if args.fix_memory:
            result = await self.fix_memory_bridge_issues(auto_apply=args.apply)
            had_errors = had_errors or result.get("status") not in ("no_issues", "fixes_applied", "dummy_created")
        
        # Analyze issues with hybrid reasoning if requested
        if args.analyze:
            if args.problem_file:
                try:
                    with open(args.problem_file, 'r') as f:
                        problem_description = f.read()
                except Exception as e:
                    logger.error(f"Error reading problem file: {e}")
                    problem_description = f"Error reading problem file: {e}"
                    had_errors = True
            else:
                problem_description = args.problem
            
            result = await self.analyze_issues_with_hybrid_reasoning(problem_description)
            had_errors = had_errors or not result.get("success", False)
        
        return 1 if had_errors else 0

async def main():
    """Run the VOT1 troubleshooter."""
    parser = argparse.ArgumentParser(description="VOT1 Troubleshooter")
    
    # Mode selection
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    # JSON fixing options
    parser.add_argument("--fix-json", action="store_true", help="Fix malformed JSON in knowledge graph output files")
    parser.add_argument("--json-dir", default="output/test_kg", help="Directory containing failed JSON files")
    parser.add_argument("--json-pattern", default="*failed_json*.json", help="File name pattern to match")
    
    # Memory bridge fixing options
    parser.add_argument("--fix-memory", action="store_true", help="Fix memory bridge initialization issues")
    parser.add_argument("--apply", action="store_true", help="Automatically apply fixes")
    
    # Hybrid reasoning options
    parser.add_argument("--analyze", action="store_true", help="Analyze issues with hybrid reasoning")
    parser.add_argument("--problem", default="", help="Problem description")
    parser.add_argument("--problem-file", help="File containing problem description")
    
    args = parser.parse_args()
    
    # Create troubleshooter
    troubleshooter = VOT1Troubleshooter()
    
    # Run in interactive mode if requested or if no specific actions were specified
    if args.interactive or not (args.fix_json or args.fix_memory or args.analyze):
        await troubleshooter.run_interactive_troubleshooter()
        return 0
    else:
        return await troubleshooter.run_cli_mode(args)

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 