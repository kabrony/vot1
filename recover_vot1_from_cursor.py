#!/usr/bin/env python3
"""
VOT1 Recovery Tool - Extracts VOT1 source code from Cursor editor history.

This script searches through Cursor editor history files to find and recover
VOT1 source code files. It identifies relevant Python files by searching for
key identifiers like "EnhancedClaudeClient" and organizes them into a
recovery directory with the original file structure.
"""

import os
import shutil
import subprocess
import re
import json
import sys
from pathlib import Path
from datetime import datetime
import argparse
import glob

# Configuration
CURSOR_HISTORY_DIR = os.path.expanduser("~/.cursor-server/data/User/History")
RECOVERY_DIR = os.path.expanduser("~/vot1_recovered")
CURRENT_VOT1_DIR = os.path.expanduser("~/vot1")

# Key identifiers that indicate VOT1 files
VOT1_IDENTIFIERS = [
    "EnhancedClaudeClient",
    "VOT1",
    "Village Of Thousands",
    "VillageOfThousands",
    "MemoryManager",
]

# Files we're particularly interested in
KEY_FILES = [
    "client.py",
    "memory.py",
    "dashboard/server.py",
    "dashboard/static/js/three-visualization.js",
    "dashboard/static/js/api.js",
    "dashboard/static/css/style.css",
    "dashboard/static/index.html",
]

def setup_recovery_dir():
    """Create recovery directory structure."""
    os.makedirs(RECOVERY_DIR, exist_ok=True)
    # Create key directories
    for dir_path in ["src/vot1", "src/vot1/dashboard", "src/vot1/dashboard/static", 
                     "src/vot1/dashboard/static/js", "src/vot1/dashboard/static/css"]:
        os.makedirs(os.path.join(RECOVERY_DIR, dir_path), exist_ok=True)
    
    print(f"Recovery directory set up at {RECOVERY_DIR}")

def find_vot1_files_in_cursor_history():
    """Find VOT1-related files in Cursor history."""
    vot1_files = []
    
    # Pattern for history file paths
    history_pattern = os.path.join(CURSOR_HISTORY_DIR, "*", "*.py")
    
    print(f"Searching for VOT1 files in Cursor history...")
    
    for file_path in glob.glob(history_pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Check if file contains any VOT1 identifier
                if any(identifier in content for identifier in VOT1_IDENTIFIERS):
                    # Get file metadata
                    file_info = {
                        'path': file_path,
                        'content': content,
                        'modified': os.path.getmtime(file_path),
                        'size': os.path.getsize(file_path),
                    }
                    
                    # Try to determine original filename
                    for key_file in KEY_FILES:
                        if key_file.split('/')[-1] in content.lower() and "class" in content and "def" in content:
                            file_info['likely_original'] = key_file
                            break
                    
                    vot1_files.append(file_info)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    print(f"Found {len(vot1_files)} potential VOT1 files in Cursor history")
    return vot1_files

def get_best_version_for_file(files, target_file):
    """Select the best version of a file from history based on completeness and recency."""
    candidates = []
    
    for file_info in files:
        if not file_info.get('likely_original'):
            continue
            
        if target_file in file_info['likely_original']:
            candidates.append(file_info)
    
    if not candidates:
        return None
    
    # Sort by file size (larger is likely more complete) and then by modified time (newer is better)
    candidates.sort(key=lambda x: (x['size'], x['modified']), reverse=True)
    return candidates[0]

def recover_vot1_files(vot1_files):
    """Recover VOT1 files from Cursor history."""
    recovered_files = []
    
    for key_file in KEY_FILES:
        best_version = get_best_version_for_file(vot1_files, key_file)
        
        if best_version:
            # Determine destination path
            dest_path = os.path.join(RECOVERY_DIR, "src/vot1", key_file)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Write recovered file
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(best_version['content'])
            
            print(f"Recovered {key_file} -> {dest_path}")
            recovered_files.append({
                'original_path': key_file,
                'recovery_path': dest_path,
                'source': best_version['path'],
                'size': best_version['size']
            })
    
    return recovered_files

def recover_unlabeled_files(vot1_files, recovered_files):
    """Try to recover files that didn't match our key file list."""
    recovered_paths = [info['source'] for info in recovered_files]
    unrecovered_count = 0
    
    # Process files we haven't already recovered
    for file_info in vot1_files:
        if file_info['path'] not in recovered_paths:
            # Try to determine what type of file it is
            content = file_info['content']
            
            # Check if it contains class definitions
            class_match = re.search(r'class\s+(\w+)', content)
            if class_match:
                class_name = class_match.group(1)
                dest_filename = f"{class_name.lower()}.py"
                
                # Special case for dashboard-related files
                if "dashboard" in content.lower() or "visualization" in content.lower():
                    dest_path = os.path.join(RECOVERY_DIR, "src/vot1/dashboard", dest_filename)
                else:
                    dest_path = os.path.join(RECOVERY_DIR, "src/vot1", dest_filename)
                
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Write recovered file
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Recovered unlabeled file -> {dest_path}")
                unrecovered_count += 1
    
    print(f"Recovered {unrecovered_count} additional files")

def generate_recovery_report(recovered_files):
    """Generate a report of the recovery process."""
    report_path = os.path.join(RECOVERY_DIR, "recovery_report.md")
    
    with open(report_path, 'w') as f:
        f.write("# VOT1 Code Recovery Report\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Recovered Files\n\n")
        f.write("| Original Path | Recovery Path | Source | Size |\n")
        f.write("|--------------|--------------|--------|------|\n")
        
        for file_info in recovered_files:
            f.write(f"| {file_info['original_path']} | {file_info['recovery_path']} | {os.path.basename(file_info['source'])} | {file_info['size']} bytes |\n")
    
    print(f"Recovery report generated at {report_path}")

def main():
    parser = argparse.ArgumentParser(description="VOT1 Code Recovery Tool")
    parser.add_argument("--no-report", action="store_true", help="Skip generating recovery report")
    args = parser.parse_args()
    
    # Set up recovery directory
    setup_recovery_dir()
    
    # Find VOT1 files in Cursor history
    vot1_files = find_vot1_files_in_cursor_history()
    
    # Recover key files
    recovered_files = recover_vot1_files(vot1_files)
    
    # Try to recover additional files
    recover_unlabeled_files(vot1_files, recovered_files)
    
    # Generate recovery report
    if not args.no_report and recovered_files:
        generate_recovery_report(recovered_files)
    
    print(f"\nRecovery process complete. Recovered files are in {RECOVERY_DIR}")
    print(f"To view the recovered files, run: ls -la {RECOVERY_DIR}/src/vot1")

if __name__ == "__main__":
    main() 