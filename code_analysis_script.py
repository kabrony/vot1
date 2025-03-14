#!/usr/bin/env python
"""
Code Analysis Script using VOT1 Development Assistant

This script analyzes the Python codebase to identify common patterns,
function sizes, file complexity metrics, and commonly used libraries.
"""

import os
import re
import json
import datetime
from pathlib import Path
from collections import Counter, defaultdict

# Import the Development Assistant
from src.vot1.dashboard.dev_assistant import DevelopmentAssistant

def analyze_function_patterns():
    """
    Analyze function patterns across the codebase.
    """
    print("Analyzing function patterns in Python codebase...")
    
    # Initialize the Development Assistant
    assistant = DevelopmentAssistant()
    
    # Get the codebase analysis for Python files
    analysis = assistant.analyze_codebase(file_extension='.py')
    
    if not analysis.get('success', False):
        print(f"Error analyzing codebase: {analysis.get('error', 'Unknown error')}")
        return
    
    print(f"Found {analysis['file_count']} Python files across {analysis['directory_count']} directories")
    print(f"Total Python code size: {analysis['total_size_formatted']}")
    print(f"Average file size: {analysis['average_file_size_formatted']}")
    
    # Analyze the 10 largest files
    print("\nLargest Python files:")
    for idx, file_info in enumerate(analysis['largest_files'], 1):
        print(f"  {idx}. {file_info['path']} ({file_info['size_formatted']})")
    
    # Analyze code patterns in the top files
    print("\nFunction Pattern Analysis:")
    pattern_analysis = analyze_top_files(analysis['largest_files'])
    
    # Analyze imports across the codebase
    print("\nImport Analysis:")
    import_analysis = analyze_imports(analysis['largest_files'])
    
    # Combined analysis results
    full_analysis = {
        "summary": {
            "timestamp": datetime.datetime.now().isoformat(),
            "file_count": analysis['file_count'],
            "directory_count": analysis['directory_count'],
            "total_size": analysis['total_size'],
            "total_size_formatted": analysis['total_size_formatted'],
            "average_file_size": analysis['average_file_size'],
            "average_file_size_formatted": analysis['average_file_size_formatted'],
        },
        "largest_files": analysis['largest_files'],
        "function_patterns": pattern_analysis,
        "import_analysis": import_analysis
    }
    
    # Export the analysis to a JSON file
    output_file = "code_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_analysis, f, indent=2)
    
    print(f"\nDetailed analysis exported to {output_file}")
    
    # Save analysis to memory
    analysis_summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "file_count": analysis['file_count'],
        "total_size": analysis['total_size'],
        "largest_files": [f['path'] for f in analysis['largest_files'][:5]],
        "pattern_summary": pattern_analysis['summary'] if 'summary' in pattern_analysis else {},
        "import_summary": import_analysis['summary'] if 'summary' in import_analysis else {}
    }
    
    save_result = assistant.save_memory('code_analysis', 'python_summary', analysis_summary)
    print(f"Analysis saved to memory: {save_result.get('success', False)}")

def analyze_top_files(largest_files, max_files=10):
    """
    Analyze patterns in the top files.
    
    Args:
        largest_files: List of largest file info dicts
        max_files: Maximum number of files to analyze
    
    Returns:
        Dict with pattern analysis results
    """
    function_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\)')
    class_pattern = re.compile(r'class\s+(\w+)(\(([^)]*)\))?:')
    comment_pattern = re.compile(r'^\s*#.*$', re.MULTILINE)
    docstring_pattern = re.compile(r'""".*?"""', re.DOTALL)
    
    function_counts = {}
    class_counts = {}
    function_names = []
    class_names = []
    docstring_ratio = []
    comment_ratio = []
    function_arg_counts = []
    total_lines = 0
    empty_lines = 0
    code_blocks = 0
    
    file_results = []
    
    for file_info in largest_files[:max_files]:
        file_path = Path(file_info['path'])
        
        if not file_path.exists():
            print(f"  - File not found: {file_path}")
            continue
        
        print(f"\n  Analyzing {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                total_lines += len(lines)
                
                # Count empty lines
                empty_line_count = sum(1 for line in lines if not line.strip())
                empty_lines += empty_line_count
                
                # Find functions
                functions = function_pattern.findall(content)
                function_counts[str(file_path)] = len(functions)
                function_names.extend([f[0] for f in functions])
                
                # Analyze function arguments
                for func in functions:
                    args = func[1].strip()
                    arg_count = len(args.split(',')) if args else 0
                    function_arg_counts.append(arg_count)
                
                # Find classes
                classes = class_pattern.findall(content)
                class_counts[str(file_path)] = len(classes)
                class_names.extend([c[0] for c in classes])
                
                # Count comments
                comments = comment_pattern.findall(content)
                comment_count = len(comments)
                
                # Count docstrings
                docstrings = docstring_pattern.findall(content)
                docstring_count = len(docstrings)
                
                # Calculate ratios
                if len(lines) > 0:
                    file_comment_ratio = comment_count / len(lines)
                    comment_ratio.append(file_comment_ratio)
                    
                    file_docstring_ratio = docstring_count / max(1, len(functions) + len(classes))
                    docstring_ratio.append(file_docstring_ratio)
                
                # Count code blocks (indentation levels > 1)
                indent_pattern = re.compile(r'^\s{4,}', re.MULTILINE)
                code_block_lines = indent_pattern.findall(content)
                code_blocks += len(code_block_lines)
                
                print(f"    - Lines: {len(lines)} (Empty: {empty_line_count}, {empty_line_count/len(lines)*100:.1f}%)")
                print(f"    - Functions: {len(functions)}")
                print(f"    - Classes: {len(classes)}")
                
                # Get some function names as examples
                if functions:
                    print(f"    - Function examples: {', '.join(f[0] for f in functions[:3])}")
                
                # Analyze complexity (simple metric: lines per function)
                if functions:
                    avg_lines = len(lines) / len(functions)
                    print(f"    - Avg lines per function: {avg_lines:.1f}")
                    print(f"    - Avg arguments per function: {sum(function_arg_counts[-len(functions):])/len(functions):.1f}")
                
                # Comment and docstring coverage
                print(f"    - Comment ratio: {file_comment_ratio*100:.1f}%")
                print(f"    - Docstring coverage: {file_docstring_ratio*100:.1f}%")
                
                # Save file analysis
                file_results.append({
                    "file_path": str(file_path),
                    "size": file_info['size'],
                    "size_formatted": file_info['size_formatted'],
                    "lines": len(lines),
                    "empty_lines": empty_line_count,
                    "empty_line_ratio": empty_line_count / len(lines),
                    "functions": len(functions),
                    "classes": len(classes),
                    "comments": comment_count,
                    "docstrings": docstring_count,
                    "comment_ratio": file_comment_ratio,
                    "docstring_ratio": file_docstring_ratio,
                    "lines_per_function": avg_lines if functions else 0,
                    "avg_args_per_function": sum(function_arg_counts[-len(functions):])/len(functions) if functions else 0,
                    "function_examples": [f[0] for f in functions[:3]],
                    "class_examples": [c[0] for c in classes[:3]]
                })
        
        except Exception as e:
            print(f"    - Error analyzing file: {e}")
    
    # Analyze function naming patterns
    most_common_prefixes = Counter([name.split('_')[0] for name in function_names]).most_common(5)
    prefix_stats = [{"prefix": prefix, "count": count} for prefix, count in most_common_prefixes]
    
    # Analyze average metrics
    avg_funcs_per_file = sum(function_counts.values()) / max(1, len(function_counts))
    avg_classes_per_file = sum(class_counts.values()) / max(1, len(class_counts))
    avg_comment_ratio = sum(comment_ratio) / max(1, len(comment_ratio))
    avg_docstring_ratio = sum(docstring_ratio) / max(1, len(docstring_ratio))
    avg_args_per_func = sum(function_arg_counts) / max(1, len(function_arg_counts))
    
    # Calculate empty line percentage
    empty_line_percentage = empty_lines / total_lines * 100 if total_lines > 0 else 0
    
    summary = {
        "total_functions": sum(function_counts.values()),
        "total_classes": sum(class_counts.values()),
        "avg_functions_per_file": avg_funcs_per_file,
        "avg_classes_per_file": avg_classes_per_file,
        "avg_comment_ratio": avg_comment_ratio,
        "avg_docstring_ratio": avg_docstring_ratio,
        "empty_line_percentage": empty_line_percentage,
        "avg_args_per_function": avg_args_per_func,
        "common_function_prefixes": prefix_stats
    }
    
    print("\n  Overall Pattern Summary:")
    print(f"    - Average functions per file: {avg_funcs_per_file:.1f}")
    print(f"    - Average classes per file: {avg_classes_per_file:.1f}")
    print(f"    - Average comment ratio: {avg_comment_ratio*100:.1f}%")
    print(f"    - Average docstring coverage: {avg_docstring_ratio*100:.1f}%")
    print(f"    - Empty line percentage: {empty_line_percentage:.1f}%")
    print(f"    - Average arguments per function: {avg_args_per_func:.1f}")
    print(f"    - Most common function prefixes: {', '.join([p['prefix'] for p in prefix_stats])}")
    
    return {
        "summary": summary,
        "file_results": file_results
    }

def analyze_imports(largest_files, max_files=15):
    """
    Analyze imports across the codebase.
    
    Args:
        largest_files: List of largest file info dicts
        max_files: Maximum number of files to analyze
    
    Returns:
        Dict with import analysis results
    """
    print("\n  Analyzing imports...")
    
    import_pattern = re.compile(r'^(?:from\s+([.\w]+)\s+)?import\s+([*\w, ]+)', re.MULTILINE)
    
    all_imports = []
    standard_lib_imports = []
    third_party_imports = []
    project_imports = []
    
    # Standard library modules (partial list)
    std_libs = {
        'os', 'sys', 're', 'math', 'random', 'datetime', 'time', 'json', 
        'csv', 'collections', 'functools', 'itertools', 'pathlib', 'logging',
        'subprocess', 'threading', 'multiprocessing', 'argparse', 'typing',
        'requests'
    }
    
    for file_info in largest_files[:max_files]:
        file_path = Path(file_info['path'])
        
        if not file_path.exists():
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find all imports
                imports = import_pattern.findall(content)
                for imp in imports:
                    from_module, imported_items = imp
                    
                    # Process multiple imports on one line (e.g., import os, sys)
                    for item in imported_items.split(','):
                        item = item.strip()
                        if not item:
                            continue
                        
                        # Construct full import name
                        if from_module:
                            import_name = f"{from_module}.{item}"
                            base_module = from_module.split('.')[0]
                        else:
                            import_name = item
                            base_module = item.split('.')[0]
                        
                        all_imports.append(import_name)
                        
                        # Categorize import
                        if base_module in std_libs:
                            standard_lib_imports.append(import_name)
                        elif base_module.startswith(('src', 'vot1')):
                            project_imports.append(import_name)
                        else:
                            third_party_imports.append(import_name)
        
        except Exception as e:
            print(f"    - Error analyzing imports in {file_path}: {e}")
    
    # Count most common imports
    most_common_imports = Counter(all_imports).most_common(10)
    most_common_std_libs = Counter(standard_lib_imports).most_common(5)
    most_common_third_party = Counter(third_party_imports).most_common(5)
    most_common_project = Counter(project_imports).most_common(5)
    
    # Convert to JSON-friendly format
    import_counts = [{"name": name, "count": count} for name, count in most_common_imports]
    std_lib_counts = [{"name": name, "count": count} for name, count in most_common_std_libs]
    third_party_counts = [{"name": name, "count": count} for name, count in most_common_third_party]
    project_counts = [{"name": name, "count": count} for name, count in most_common_project]
    
    # Print results
    print(f"    - Total distinct imports: {len(set(all_imports))}")
    print(f"    - Standard library imports: {len(set(standard_lib_imports))}")
    print(f"    - Third-party imports: {len(set(third_party_imports))}")
    print(f"    - Project-specific imports: {len(set(project_imports))}")
    
    print("\n    Most common imports:")
    for imp in import_counts:
        print(f"      - {imp['name']}: {imp['count']} occurrences")
    
    # Create summary
    summary = {
        "total_imports": len(all_imports),
        "distinct_imports": len(set(all_imports)),
        "standard_library_count": len(set(standard_lib_imports)),
        "third_party_count": len(set(third_party_imports)),
        "project_specific_count": len(set(project_imports))
    }
    
    return {
        "summary": summary,
        "most_common": import_counts,
        "standard_library": std_lib_counts,
        "third_party": third_party_counts,
        "project_specific": project_counts
    }

def main():
    """
    Main function to run the analysis.
    """
    print("VOT1 Code Pattern Analysis Tool")
    print("===============================")
    
    analyze_function_patterns()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main() 