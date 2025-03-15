#!/usr/bin/env python3
"""
Memory System Troubleshooter

This script helps diagnose and fix issues with the memory system
in the VOT1 project, focusing on the ComposioMemoryBridge error.
"""

import os
import sys
import re
import inspect
import asyncio
import logging
import importlib
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MemoryTroubleshooter")

# Output directory for reports
OUTPUT_DIR = "output/memory_fixes"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class MemorySystemTroubleshooter:
    """
    Diagnose and fix issues with the memory system.
    
    This class analyzes the ComposioMemoryBridge implementation and usages
    to identify and fix issues related to memory initialization.
    """
    
    def __init__(self):
        """Initialize the memory system troubleshooter."""
        logger.info("Initializing memory system troubleshooter")
        
        # Properties for tracking
        self.bridge_module_path = None
        self.bridge_signature = None
        self.bridge_uses = []
        self.issues_found = []
    
    def find_memory_bridge_module(self, search_dir="."):
        """
        Find the module that defines ComposioMemoryBridge.
        
        Args:
            search_dir: Directory to search
            
        Returns:
            Path to the module file
        """
        logger.info("Searching for ComposioMemoryBridge definition")
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for class definition
                    if "class ComposioMemoryBridge" in content:
                        logger.info(f"Found ComposioMemoryBridge definition in {file_path}")
                        self.bridge_module_path = file_path
                        
                        # Extract the class signature
                        matches = re.search(r"class\s+ComposioMemoryBridge\([^)]*\):\s*(?:(?:\"\"\"|\'\'\')[\s\S]*?(?:\"\"\"|\'\'\'))?\s*def\s+__init__\s*\(([^)]*)\)", content)
                        if matches:
                            self.bridge_signature = matches.group(1).strip()
                            logger.info(f"Found __init__ signature: {self.bridge_signature}")
                        
                        return file_path
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
        
        logger.warning("Could not find ComposioMemoryBridge definition")
        return None
    
    def find_memory_bridge_uses(self, search_dir="."):
        """
        Find files that use ComposioMemoryBridge.
        
        Args:
            search_dir: Directory to search
            
        Returns:
            List of files that use ComposioMemoryBridge
        """
        logger.info("Searching for ComposioMemoryBridge usage")
        
        uses = []
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if not file.endswith(".py"):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for import and usage
                    if "ComposioMemoryBridge" in content and file_path != self.bridge_module_path:
                        # Extract initialization calls
                        init_calls = []
                        pattern = r"ComposioMemoryBridge\s*\(([^)]*)\)"
                        for match in re.finditer(pattern, content):
                            init_calls.append(match.group(1).strip())
                        
                        if init_calls:
                            logger.info(f"Found ComposioMemoryBridge usage in {file_path}")
                            uses.append({
                                "file_path": file_path,
                                "init_calls": init_calls
                            })
                except Exception as e:
                    logger.warning(f"Error reading {file_path}: {e}")
        
        self.bridge_uses = uses
        logger.info(f"Found {len(uses)} files that use ComposioMemoryBridge")
        return uses
    
    def analyze_bridge_signature(self):
        """
        Analyze the bridge signature to understand required params.
        
        Returns:
            Dictionary with parameter analysis
        """
        if not self.bridge_signature:
            logger.warning("No bridge signature found to analyze")
            return None
        
        # Parse the signature
        params = self.bridge_signature.split(',')
        param_info = []
        
        for param in params:
            param = param.strip()
            if not param:
                continue
            
            # Handle default values
            if '=' in param:
                name, default = param.split('=', 1)
                name = name.strip()
                default = default.strip()
                required = False
            else:
                name = param
                default = None
                required = name != 'self'  # All non-self params without defaults are required
            
            # Strip type annotations if present
            if ':' in name:
                name = name.split(':', 1)[0].strip()
            
            param_info.append({
                "name": name,
                "default": default,
                "required": required
            })
        
        logger.info(f"Analyzed bridge signature: {len(param_info)} parameters")
        return param_info
    
    def analyze_init_calls(self):
        """
        Analyze initialization calls to find mismatches.
        
        Returns:
            List of issues found
        """
        if not self.bridge_signature or not self.bridge_uses:
            logger.warning("Missing bridge signature or uses to analyze")
            return []
        
        # Get proper parameters
        proper_params = self.analyze_bridge_signature()
        proper_param_names = {p["name"] for p in proper_params if p["name"] != 'self'}
        required_params = {p["name"] for p in proper_params if p["required"]}
        
        logger.info(f"Required parameters: {required_params}")
        logger.info(f"All valid parameters: {proper_param_names}")
        
        issues = []
        
        for use in self.bridge_uses:
            file_path = use["file_path"]
            
            for call_idx, init_call in enumerate(use["init_calls"]):
                # Extract parameter names and values
                call_params = {}
                
                # Handle positional and keyword arguments
                if init_call:
                    parts = init_call.split(',')
                    pos_idx = 0
                    
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        
                        if '=' in part:  # Keyword argument
                            k, v = part.split('=', 1)
                            call_params[k.strip()] = v.strip()
                        else:  # Positional argument
                            # Map to parameter name based on position
                            if pos_idx < len(proper_params) - 1:  # Skip self
                                param_name = proper_params[pos_idx + 1]["name"]
                                call_params[param_name] = part
                            pos_idx += 1
                
                # Check for invalid parameters
                invalid_params = set(call_params.keys()) - proper_param_names
                if invalid_params:
                    issue = {
                        "type": "invalid_parameters",
                        "file_path": file_path,
                        "call_index": call_idx,
                        "invalid_params": list(invalid_params),
                        "message": f"Invalid parameters in call: {invalid_params}"
                    }
                    issues.append(issue)
                    logger.warning(f"Invalid parameters in {file_path}: {invalid_params}")
                
                # Check for missing required parameters
                missing_required = required_params - set(call_params.keys())
                if missing_required:
                    issue = {
                        "type": "missing_required",
                        "file_path": file_path,
                        "call_index": call_idx,
                        "missing_params": list(missing_required),
                        "message": f"Missing required parameters in call: {missing_required}"
                    }
                    issues.append(issue)
                    logger.warning(f"Missing required parameters in {file_path}: {missing_required}")
        
        self.issues_found = issues
        logger.info(f"Found {len(issues)} issues in initialization calls")
        return issues
    
    def extract_memory_bridge_class(self):
        """
        Extract the ComposioMemoryBridge class definition.
        
        Returns:
            The class definition as a string
        """
        if not self.bridge_module_path:
            logger.warning("No bridge module path found")
            return None
        
        try:
            with open(self.bridge_module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the class definition
            class_match = re.search(r"class\s+ComposioMemoryBridge\([^)]*\):\s*(?:(?:\"\"\"|\'\'\')[\s\S]*?(?:\"\"\"|\'\'\'))?([\s\S]*?)(?:class|\Z)", content)
            if class_match:
                class_def = class_match.group(0)
                logger.info(f"Extracted ComposioMemoryBridge class definition ({len(class_def)} chars)")
                return class_def
            else:
                logger.warning("Could not extract ComposioMemoryBridge class definition")
                return None
        except Exception as e:
            logger.error(f"Error extracting bridge class: {e}")
            return None
    
    def generate_fix_suggestions(self):
        """
        Generate suggestions to fix the memory bridge issues.
        
        Returns:
            Dictionary with fix suggestions
        """
        if not self.issues_found:
            logger.info("No issues found, no fixes needed")
            return {
                "status": "no_issues",
                "message": "No issues found with ComposioMemoryBridge initialization"
            }
        
        # Group issues by file
        issues_by_file = {}
        for issue in self.issues_found:
            file_path = issue["file_path"]
            if file_path not in issues_by_file:
                issues_by_file[file_path] = []
            issues_by_file[file_path].append(issue)
        
        # Generate fix suggestions
        fixes = []
        
        for file_path, file_issues in issues_by_file.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Process each issue
                for issue in file_issues:
                    if issue["type"] == "invalid_parameters":
                        # Find the initialization call
                        pattern = r"ComposioMemoryBridge\s*\(([^)]*)\)"
                        matches = list(re.finditer(pattern, content))
                        
                        if issue["call_index"] < len(matches):
                            match = matches[issue["call_index"]]
                            current_call = match.group(0)
                            current_params = match.group(1)
                            
                            # Remove invalid parameters
                            invalid_params = issue["invalid_params"]
                            new_params = []
                            
                            for param in current_params.split(','):
                                param = param.strip()
                                if not param:
                                    continue
                                
                                # Check if this is an invalid parameter
                                is_invalid = False
                                for invalid in invalid_params:
                                    if param.startswith(f"{invalid}=") or param == invalid:
                                        is_invalid = True
                                        break
                                
                                if not is_invalid:
                                    new_params.append(param)
                            
                            # Create fixed call
                            fixed_call = f"ComposioMemoryBridge({', '.join(new_params)})"
                            
                            fixes.append({
                                "file_path": file_path,
                                "issue_type": "invalid_parameters",
                                "original": current_call,
                                "fixed": fixed_call,
                                "line_context": self._get_line_context(content, match.start())
                            })
            except Exception as e:
                logger.error(f"Error generating fix for {file_path}: {e}")
        
        # Prepare suggestion report
        bridge_class = self.extract_memory_bridge_class()
        param_analysis = self.analyze_bridge_signature()
        
        suggestions = {
            "status": "issues_found",
            "issues_count": len(self.issues_found),
            "bridge_module": self.bridge_module_path,
            "bridge_signature": self.bridge_signature,
            "parameter_analysis": param_analysis,
            "fixes": fixes,
            "bridge_class_snippet": bridge_class[:500] + "..." if bridge_class and len(bridge_class) > 500 else bridge_class
        }
        
        # Save suggestions to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        suggestion_file = os.path.join(OUTPUT_DIR, f"fix_suggestions_{timestamp}.txt")
        
        with open(suggestion_file, 'w', encoding='utf-8') as f:
            f.write("MEMORY BRIDGE FIX SUGGESTIONS\n")
            f.write("===========================\n\n")
            
            f.write(f"Issues found: {len(self.issues_found)}\n")
            f.write(f"Bridge module: {self.bridge_module_path}\n")
            f.write(f"Bridge signature: {self.bridge_signature}\n\n")
            
            f.write("Parameter analysis:\n")
            for param in param_analysis:
                required = "Required" if param["required"] else "Optional"
                default = f" (default: {param['default']})" if param["default"] else ""
                f.write(f"  - {param['name']}: {required}{default}\n")
            
            f.write("\nFix suggestions:\n")
            for fix in fixes:
                f.write(f"\nFile: {fix['file_path']}\n")
                f.write(f"Issue: {fix['issue_type']}\n")
                f.write(f"Context: {fix['line_context']}\n")
                f.write(f"Original: {fix['original']}\n")
                f.write(f"Fixed: {fix['fixed']}\n")
            
            f.write("\nBridge class snippet:\n")
            if bridge_class:
                f.write(bridge_class[:1000] + "..." if len(bridge_class) > 1000 else bridge_class)
        
        logger.info(f"Fix suggestions saved to {suggestion_file}")
        suggestions["suggestion_file"] = suggestion_file
        
        return suggestions
    
    def fix_memory_bridge_issues(self, auto_apply=False):
        """
        Apply fixes to files with memory bridge issues.
        
        Args:
            auto_apply: Whether to automatically apply fixes
            
        Returns:
            Dictionary with fix results
        """
        if not self.issues_found:
            logger.info("No issues found, no fixes needed")
            return {
                "status": "no_issues",
                "message": "No issues found with ComposioMemoryBridge initialization"
            }
        
        # Generate fix suggestions
        suggestions = self.generate_fix_suggestions()
        fixes = suggestions.get("fixes", [])
        
        if not fixes:
            logger.warning("No fixes generated")
            return {
                "status": "no_fixes",
                "message": "No fixes could be generated for the issues found"
            }
        
        # Apply fixes if requested
        if auto_apply:
            applied_fixes = []
            
            for fix in fixes:
                file_path = fix["file_path"]
                original = fix["original"]
                fixed = fix["fixed"]
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply the fix
                    new_content = content.replace(original, fixed)
                    
                    # Only save if changes were made
                    if new_content != content:
                        # Backup the original file
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_file = f"{file_path}.{timestamp}.bak"
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Write the fixed file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        applied_fixes.append({
                            "file_path": file_path,
                            "backup_file": backup_file,
                            "issue_type": fix["issue_type"]
                        })
                        
                        logger.info(f"Applied fix to {file_path}")
                except Exception as e:
                    logger.error(f"Error applying fix to {file_path}: {e}")
            
            return {
                "status": "fixes_applied",
                "applied_count": len(applied_fixes),
                "applied_fixes": applied_fixes,
                "suggestion_file": suggestions.get("suggestion_file")
            }
        else:
            return {
                "status": "fixes_suggested",
                "fixes_count": len(fixes),
                "suggestion_file": suggestions.get("suggestion_file"),
                "message": f"Generated {len(fixes)} fix suggestions. See {suggestions.get('suggestion_file')}"
            }
    
    def _get_line_context(self, content, position, context_lines=2):
        """Get line context around a position in the content."""
        lines = content[:position].split('\n')
        line_number = len(lines)
        
        start_line = max(0, line_number - context_lines)
        end_line = min(len(content.split('\n')), line_number + context_lines)
        
        context = []
        for i, line in enumerate(content.split('\n')[start_line:end_line], start=start_line + 1):
            prefix = ">>> " if i == line_number else "    "
            context.append(f"{prefix}{i}: {line}")
        
        return "\n".join(context)
    
    def create_dummy_composio_client(self):
        """
        Create a dummy ComposioClient to help with testing.
        
        Returns:
            Path to the created file
        """
        dummy_file = "dummy_composio_client.py"
        
        content = """#!/usr/bin/env python3
\"\"\"
Dummy Composio Client

This module provides a dummy implementation of ComposioClient
for testing purposes when the real client is not available.
\"\"\"

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DummyComposioClient:
    \"\"\"
    Dummy implementation of ComposioClient for testing.
    \"\"\"
    
    def __init__(self, api_key=None, api_url=None):
        \"\"\"Initialize the dummy client.\"\"\"
        self.api_key = api_key or "dummy_api_key"
        self.api_url = api_url or "https://dummy.composio.dev/api"
        logger.info("Initialized DummyComposioClient")
    
    async def get_memories(self, query=None, limit=10):
        \"\"\"Get dummy memories.\"\"\"
        logger.info(f"Getting dummy memories with query: {query}, limit: {limit}")
        return {
            "memories": [
                {
                    "id": "mem1",
                    "content": "This is a dummy memory",
                    "metadata": {"source": "dummy", "created_at": "2023-01-01"}
                }
            ],
            "total": 1
        }
    
    async def add_memory(self, content, metadata=None):
        \"\"\"Add a dummy memory.\"\"\"
        metadata = metadata or {}
        logger.info(f"Adding dummy memory: {content[:30]}...")
        return {
            "id": "new_mem_id",
            "content": content,
            "metadata": metadata
        }
    
    async def delete_memory(self, memory_id):
        \"\"\"Delete a dummy memory.\"\"\"
        logger.info(f"Deleting dummy memory: {memory_id}")
        return {"success": True, "id": memory_id}
    
    async def search_memories(self, query, limit=10):
        \"\"\"Search dummy memories.\"\"\"
        logger.info(f"Searching dummy memories with query: {query}, limit: {limit}")
        return {
            "matches": [
                {
                    "id": "mem1",
                    "content": "This is a dummy memory that matches: " + query,
                    "metadata": {"source": "dummy", "created_at": "2023-01-01"},
                    "score": 0.95
                }
            ],
            "total": 1
        }

# Also provide a memory bridge implementation that works with the dummy client
class DummyMemoryBridge:
    \"\"\"
    Dummy implementation of a memory bridge.
    \"\"\"
    
    def __init__(self, client=None, namespace="default"):
        \"\"\"Initialize the dummy memory bridge.\"\"\"
        self.client = client or DummyComposioClient()
        self.namespace = namespace
        logger.info(f"Initialized DummyMemoryBridge with namespace: {namespace}")
    
    async def store_memory(self, content, metadata=None):
        \"\"\"Store a memory.\"\"\"
        metadata = metadata or {}
        metadata["namespace"] = self.namespace
        return await self.client.add_memory(content, metadata)
    
    async def retrieve_memories(self, query=None, limit=10):
        \"\"\"Retrieve memories.\"\"\"
        result = await self.client.get_memories(query, limit)
        return result.get("memories", [])
    
    async def search_memories(self, query, limit=10):
        \"\"\"Search memories.\"\"\"
        result = await self.client.search_memories(query, limit)
        return result.get("matches", [])
    
    async def delete_memory(self, memory_id):
        \"\"\"Delete a memory.\"\"\"
        return await self.client.delete_memory(memory_id)
"""
        
        with open(dummy_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Created dummy Composio client at {dummy_file}")
        return dummy_file

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

async def main():
    """Main entry point for the script"""
    # Initialize the Memory Troubleshooter
    troubleshooter = MemorySystemTroubleshooter()
    
    # Example memory data with issues
    memory_data = {
        "conversations": [
            {
                "id": "conv1",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, how are you?"
                    },
                    {
                        "role": "assistant",
                        "content": "I'm doing well, thank you for asking!"
                    }
                ]
            },
            {
                "id": "conv2",
                "messages": [
                    {
                        "role": "user",
                        "content": "Can you help me with a problem?"
                    },
                    {
                        "role": "assistant"
                        # Missing content field
                    }
                ]
            }
        ],
        "knowledge_graph": {
            "nodes": [
                {
                    "id": "concept1",
                    "label": "AI Systems"
                },
                {
                    "id": "concept2",
                    "label": "Memory Management"
                }
            ],
            "edges": [
                {
                    "source": "concept1",
                    "target": "concept2",
                    "label": "includes"
                },
                {
                    "source": "concept3", # Reference to non-existent node
                    "target": "concept2",
                    "label": "relates to"
                }
            ]
        }
    }
    
    # Analyze memory issues
    print("Analyzing memory issues...")
    analysis = await troubleshooter.analyze_memory_issue(memory_data, "Missing content in messages and invalid node references")
    
    if analysis.get("success", False):
        print("✅ Memory analysis complete!")
        print(f"Analysis saved to: {analysis.get('analysis_file')}")
        
        # Print a summary of the analysis
        print("\nAnalysis Summary:")
        analysis_text = analysis.get("analysis", "")
        summary_lines = [line for line in analysis_text.split("\n") if line.strip().startswith("- ")][:5]
        for line in summary_lines:
            print(line)
    else:
        print(f"❌ Error analyzing memory: {analysis.get('error')}")
    
    # Repair memory
    print("\nRepairing memory...")
    repair = await troubleshooter.repair_memory(memory_data, analysis)
    
    if repair.get("success", False):
        print("✅ Memory repaired!")
        print(f"Repaired memory saved to: {repair.get('repaired_file')}")
    else:
        print(f"❌ Error repairing memory: {repair.get('error')}")
    
    print("\nMemory troubleshooting complete!") 