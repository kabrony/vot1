#!/usr/bin/env python3
"""
VOT1 Code Recovery Script

This script helps recover VOT1 code from Cursor history files and compares
it with the current version to identify differences.
"""

import os
import shutil
import glob
import difflib
import sys
from pathlib import Path
import argparse

# Define paths
CURSOR_HISTORY_DIR = os.path.expanduser('~/.cursor-server/data/User/History')
VOT1_RECOVERY_DIR = os.path.expanduser('~/vot1_recovered')
CURRENT_VOT1_DIR = os.path.expanduser('~/vot1')

def setup_recovery_dir():
    """Create the recovery directory if it doesn't exist."""
    os.makedirs(VOT1_RECOVERY_DIR, exist_ok=True)
    print(f"Recovery directory set up at: {VOT1_RECOVERY_DIR}")

def find_enhanced_claude_client_files():
    """Find all files containing EnhancedClaudeClient in Cursor history."""
    cmd = f"grep -l 'EnhancedClaudeClient' {CURSOR_HISTORY_DIR}/*/*.py"
    result = os.popen(cmd).read()
    files = result.strip().split('\n')
    return [f for f in files if f]  # Filter out any empty entries

def extract_oldest_files(files, n=3):
    """Extract the n oldest files by their directory names."""
    # Sort by directory name which may correlate with age
    sorted_files = sorted(files, key=lambda x: os.path.dirname(x))
    return sorted_files[:n]

def copy_file_to_recovery(file_path, dest_name=None):
    """Copy a file to the recovery directory with an optional new name."""
    if dest_name is None:
        dest_name = os.path.basename(os.path.dirname(file_path)) + '_' + os.path.basename(file_path)
    
    dest_path = os.path.join(VOT1_RECOVERY_DIR, dest_name)
    shutil.copy2(file_path, dest_path)
    print(f"Copied {file_path} to {dest_path}")
    return dest_path

def diff_files(file1, file2):
    """Generate a diff between two files."""
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        f1_lines = f1.readlines()
        f2_lines = f2.readlines()
    
    diff = difflib.unified_diff(
        f1_lines, f2_lines,
        fromfile=os.path.basename(file1),
        tofile=os.path.basename(file2),
        n=3
    )
    return ''.join(diff)

def search_for_vot1_files():
    """Search for all files that might be part of VOT1 in Cursor history."""
    cmd = f"grep -l 'vot1\\|VOT1' {CURSOR_HISTORY_DIR}/*/*.py | grep -v '__pycache__'"
    result = os.popen(cmd).read()
    files = result.strip().split('\n')
    return [f for f in files if f]

def recover_file(cursor_file, output_name):
    """Recover a file from Cursor history to the recovery directory."""
    dest_path = os.path.join(VOT1_RECOVERY_DIR, output_name)
    shutil.copy2(cursor_file, dest_path)
    print(f"Recovered {output_name} from {cursor_file}")
    return dest_path

def generate_recovery_report(recovered_files):
    """Generate a report of recovered files."""
    report_path = os.path.join(VOT1_RECOVERY_DIR, 'recovery_report.txt')
    with open(report_path, 'w') as f:
        f.write("VOT1 Recovery Report\n")
        f.write("===================\n\n")
        f.write(f"Recovery Time: {os.popen('date').read()}\n")
        f.write(f"Number of Files Recovered: {len(recovered_files)}\n\n")
        f.write("Recovered Files:\n")
        for i, file_path in enumerate(recovered_files, 1):
            f.write(f"{i}. {os.path.basename(file_path)}\n")
    
    print(f"Recovery report generated at {report_path}")

def main():
    parser = argparse.ArgumentParser(description="VOT1 Code Recovery Tool")
    parser.add_argument('--recover-all', action='store_true', help='Attempt to recover all VOT1 files')
    parser.add_argument('--compare', action='store_true', help='Compare recovered files with current files')
    args = parser.parse_args()
    
    # Ensure recovery directory exists
    setup_recovery_dir()
    
    recovered_files = []
    
    if args.recover_all:
        # Search for all potential VOT1 files
        vot1_files = search_for_vot1_files()
        print(f"Found {len(vot1_files)} potential VOT1 files in Cursor history")
        
        # Process each file
        for cursor_file in vot1_files:
            # Generate output name based on content
            with open(cursor_file, 'r') as f:
                content = f.read()
                
            # Try to determine what kind of file it is
            if 'class EnhancedClaudeClient' in content:
                output_name = 'client.py.recovered'
            elif 'class MemoryManager' in content:
                output_name = 'memory.py.recovered'
            elif 'class DashboardServer' in content:
                output_name = 'dashboard_server.py.recovered'
            else:
                # Use hash from directory name to make unique
                dir_hash = os.path.basename(os.path.dirname(cursor_file))
                output_name = f"vot1_unknown_{dir_hash}.py.recovered"
            
            recovered_file = recover_file(cursor_file, output_name)
            recovered_files.append(recovered_file)
    else:
        # Just recover the EnhancedClaudeClient files
        claude_files = find_enhanced_claude_client_files()
        print(f"Found {len(claude_files)} files containing EnhancedClaudeClient")
        
        # Extract a few of the oldest files based on directory naming
        oldest_files = extract_oldest_files(claude_files, 3)
        print(f"Selected {len(oldest_files)} oldest files for recovery")
        
        # Copy each file to recovery directory
        for i, file_path in enumerate(oldest_files):
            dest_name = f"client_{i+1}.py.recovered"
            recovered_file = copy_file_to_recovery(file_path, dest_name)
            recovered_files.append(recovered_file)
    
    # Generate report
    generate_recovery_report(recovered_files)
    
    # Compare with current files if requested
    if args.compare and os.path.exists(os.path.join(CURRENT_VOT1_DIR, 'src/vot1/client.py')):
        current_client = os.path.join(CURRENT_VOT1_DIR, 'src/vot1/client.py')
        
        # Find the client.py equivalent in recovered files
        client_recoveries = [f for f in recovered_files if 'client' in os.path.basename(f).lower()]
        
        if client_recoveries:
            # Use the first one for comparison
            diff_output = diff_files(current_client, client_recoveries[0])
            diff_path = os.path.join(VOT1_RECOVERY_DIR, 'client_diff.txt')
            
            with open(diff_path, 'w') as f:
                f.write(diff_output)
            
            print(f"Diff between current and recovered client.py saved to {diff_path}")
    
    print(f"\nRecovery complete! Files saved to {VOT1_RECOVERY_DIR}")
    print("To view recovered files, run: ls -la ~/vot1_recovered/")

if __name__ == "__main__":
    main() 