"""
Codebase Analysis Script

This script uses the CodeAnalysis class from the Development Assistant
to analyze the codebase and check for potential issues.
"""

import os
import sys
import json
import logging
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def import_code_analysis():
    """Import the CodeAnalysis class from the dev_assistant module."""
    try:
        # Find the dev_assistant.py file
        for root, dirs, files in os.walk('.'):
            if 'dev_assistant.py' in files:
                dev_assistant_path = os.path.join(root, 'dev_assistant.py')
                logger.info(f"Found dev_assistant.py at {dev_assistant_path}")
                
                # Load the module from file
                spec = importlib.util.spec_from_file_location("dev_assistant", dev_assistant_path)
                dev_assistant = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(dev_assistant)
                
                # Get the CodeAnalysis class
                return dev_assistant.CodeAnalysis
        
        logger.error("Could not find dev_assistant.py")
        return None
    except Exception as e:
        logger.error(f"Error importing CodeAnalysis: {e}")
        return None

def analyze_directory(directory, file_extension='.py'):
    """Analyze a directory using the CodeAnalysis class."""
    CodeAnalysis = import_code_analysis()
    if not CodeAnalysis:
        logger.error("Cannot proceed without CodeAnalysis class")
        return None
    
    try:
        logger.info(f"Analyzing directory: {directory} with extension {file_extension}")
        results = CodeAnalysis.scan_directory(directory, file_extension)
        
        if not results:
            logger.warning(f"No {file_extension} files found in {directory}")
            return None
        
        # Calculate and add summary statistics
        total_files = len(results)
        total_lines = sum(file_analysis.get('total_lines', 0) for file_analysis in results)
        blank_lines = sum(file_analysis.get('blank_lines', 0) for file_analysis in results)
        comment_lines = sum(file_analysis.get('comment_lines', 0) for file_analysis in results)
        code_lines = sum(file_analysis.get('code_lines', 0) for file_analysis in results)
        total_classes = sum(len(file_analysis.get('classes', [])) for file_analysis in results)
        total_functions = sum(len(file_analysis.get('functions', [])) for file_analysis in results)
        
        # Combine all imports and count unique ones
        all_imports = []
        for file_analysis in results:
            all_imports.extend(file_analysis.get('imports', []))
        unique_imports = list(set(all_imports))
        
        summary = {
            'total_files': total_files,
            'total_lines': total_lines,
            'total_blank_lines': blank_lines,
            'total_comment_lines': comment_lines,
            'total_code_lines': code_lines,
            'total_classes': total_classes,
            'total_functions': total_functions,
            'unique_import_count': len(unique_imports),
            'unique_imports': unique_imports,
            'files': results
        }
        
        return summary
    except Exception as e:
        logger.error(f"Error analyzing directory {directory}: {e}")
        return None

def find_potential_bugs(analysis_result):
    """
    Check for potential bugs or issues in the analysis result.
    """
    if not analysis_result:
        return []
    
    potential_issues = []
    
    # Check for imports that might cause circular dependencies
    import_counts = {}
    for file_analysis in analysis_result['files']:
        file_path = file_analysis.get('file_path', '')
        imports = file_analysis.get('imports', [])
        
        for imp in imports:
            if imp not in import_counts:
                import_counts[imp] = []
            import_counts[imp].append(file_path)
    
    # Look for modules that import each other
    for file_analysis in analysis_result['files']:
        file_path = file_analysis.get('file_path', '')
        file_module = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        
        for imp in file_analysis.get('imports', []):
            for importing_file in import_counts.get(file_module, []):
                potential_issues.append({
                    'type': 'circular_import',
                    'file1': file_path,
                    'file2': importing_file,
                    'message': f"Potential circular import between {file_path} and {importing_file}"
                })
    
    # Check for excessively large files
    for file_analysis in analysis_result['files']:
        file_path = file_analysis.get('file_path', '')
        line_count = file_analysis.get('total_lines', 0)
        
        if line_count > 500:
            potential_issues.append({
                'type': 'large_file',
                'file': file_path,
                'line_count': line_count,
                'message': f"File {file_path} is very large ({line_count} lines). Consider refactoring."
            })
    
    # Check for files with high class/function counts
    for file_analysis in analysis_result['files']:
        file_path = file_analysis.get('file_path', '')
        class_count = len(file_analysis.get('classes', []))
        function_count = len(file_analysis.get('functions', []))
        
        if class_count > 5:
            potential_issues.append({
                'type': 'high_class_count',
                'file': file_path,
                'class_count': class_count,
                'message': f"File {file_path} has {class_count} classes. Consider splitting it up."
            })
        
        if function_count > 20:
            potential_issues.append({
                'type': 'high_function_count',
                'file': file_path,
                'function_count': function_count,
                'message': f"File {file_path} has {function_count} functions. Consider refactoring."
            })
    
    return potential_issues

def main():
    """Main function to analyze the codebase."""
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = 'src/vot1/dashboard'
    
    if len(sys.argv) > 2:
        file_extension = sys.argv[2]
    else:
        file_extension = '.py'
    
    # Run the analysis
    analysis_result = analyze_directory(target_dir, file_extension)
    
    if analysis_result:
        # Find potential issues
        issues = find_potential_bugs(analysis_result)
        
        # Add issues to the result
        analysis_result['potential_issues'] = issues
        
        # Print summary
        print("\n=== CODEBASE ANALYSIS SUMMARY ===")
        print(f"Files analyzed: {analysis_result['total_files']}")
        print(f"Total lines: {analysis_result['total_lines']} ({analysis_result['total_code_lines']} code, "
              f"{analysis_result['total_comment_lines']} comments, {analysis_result['total_blank_lines']} blank)")
        print(f"Classes: {analysis_result['total_classes']}")
        print(f"Functions: {analysis_result['total_functions']}")
        print(f"Unique imports: {analysis_result['unique_import_count']}")
        
        if issues:
            print("\n=== POTENTIAL ISSUES ===")
            for issue in issues:
                print(f"- {issue['message']}")
        else:
            print("\nNo potential issues found!")
        
        # Write detailed results to a JSON file
        with open('analysis_result.json', 'w') as f:
            json.dump(analysis_result, f, indent=2)
        print(f"\nDetailed analysis saved to analysis_result.json")
    else:
        print("Analysis failed. See logs for details.")

if __name__ == "__main__":
    main() 