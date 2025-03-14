#!/usr/bin/env python
"""
UI/UX Analysis Script using VOT1 Development Assistant

This script analyzes the UI/UX of the VOT1 Dashboard application,
examining HTML templates, CSS styling, and JavaScript functionality
to provide improvement recommendations.
"""

import os
import re
import json
import datetime
from pathlib import Path
from collections import Counter, defaultdict

# Import the Development Assistant
from src.vot1.dashboard.dev_assistant import DevelopmentAssistant

def analyze_ui_ux():
    """
    Analyze UI/UX elements across the codebase.
    """
    print("Analyzing UI/UX elements in the VOT1 Dashboard...")
    
    # Initialize the Development Assistant
    assistant = DevelopmentAssistant()
    
    # Get the codebase analysis for HTML, CSS, and JS files
    html_analysis = assistant.analyze_codebase(file_extension='.html')
    css_analysis = assistant.analyze_codebase(file_extension='.css')
    js_analysis = assistant.analyze_codebase(file_extension='.js')
    
    if not html_analysis.get('success', False) or not css_analysis.get('success', False) or not js_analysis.get('success', False):
        print(f"Error analyzing codebase: One or more file analyses failed")
        return
    
    print(f"Found {html_analysis['file_count']} HTML files across {html_analysis['directory_count']} directories")
    print(f"Found {css_analysis['file_count']} CSS files across {css_analysis['directory_count']} directories")
    print(f"Found {js_analysis['file_count']} JS files across {js_analysis['directory_count']} directories")
    
    # Analyze UI structure
    print("\nUI Structure Analysis:")
    ui_structure = analyze_ui_structure(html_analysis['largest_files'])
    
    # Analyze styling
    print("\nCSS Styling Analysis:")
    css_structure = analyze_css_styling(css_analysis['largest_files'])
    
    # Analyze JavaScript functionality
    print("\nJavaScript Functionality Analysis:")
    js_structure = analyze_js_functionality(js_analysis['largest_files'])
    
    # Generate improvement recommendations
    print("\nGenerating UI/UX Improvement Recommendations:")
    recommendations = generate_recommendations(ui_structure, css_structure, js_structure)
    
    # Combined analysis results
    full_analysis = {
        "summary": {
            "timestamp": datetime.datetime.now().isoformat(),
            "html_files": html_analysis['file_count'],
            "css_files": css_analysis['file_count'],
            "js_files": js_analysis['file_count'],
        },
        "ui_structure": ui_structure,
        "css_styling": css_structure,
        "js_functionality": js_structure,
        "recommendations": recommendations
    }
    
    # Export the analysis to a JSON file
    output_file = "ui_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_analysis, f, indent=2)
    
    print(f"\nDetailed analysis exported to {output_file}")
    
    # Save analysis to memory
    analysis_summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "html_files": html_analysis['file_count'],
        "css_files": css_analysis['file_count'],
        "js_files": js_analysis['file_count'],
        "recommendations": recommendations
    }
    
    save_result = assistant.save_memory('ui_analysis', 'ui_summary', analysis_summary)
    print(f"Analysis saved to memory: {save_result.get('success', False)}")

def analyze_ui_structure(html_files):
    """
    Analyze the UI structure by examining HTML files.
    
    Args:
        html_files: List of HTML file info dicts
    
    Returns:
        Dict with UI structure analysis results
    """
    print("  Analyzing UI structure from HTML files...")
    
    # Patterns to look for
    responsive_pattern = re.compile(r'class=["\'].*?(container|row|col|d-flex|flex|grid|md-|lg-|sm-|responsive|media).*?["\']')
    accessibility_patterns = {
        'alt_tags': re.compile(r'<img[^>]*alt=["\'](.*?)["\']'),
        'aria_labels': re.compile(r'aria-label=["\'](.*?)["\']'),
        'aria_attributes': re.compile(r'aria-[a-z]+'),
        'semantic_elements': re.compile(r'<(header|nav|main|article|section|aside|footer)')
    }
    form_elements = re.compile(r'<(input|select|textarea|button|label|form)')
    
    # Results structure
    results = {
        'templates': [],
        'responsive_elements_count': 0,
        'accessibility': {
            'alt_tags_count': 0,
            'aria_attributes_count': 0,
            'semantic_elements_count': 0
        },
        'form_elements_count': 0,
        'themes': [],
        'navigation_types': [],
        'summary': {}
    }
    
    total_templates = 0
    
    for file_info in html_files:
        file_path = Path(file_info['path'])
        
        if not file_path.exists():
            print(f"  - File not found: {file_path}")
            continue
        
        print(f"\n  Analyzing {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check if it's a template or base layout
                is_template = 'templates' in str(file_path)
                if is_template:
                    total_templates += 1
                
                is_base = 'base' in file_path.name
                template_type = 'base' if is_base else 'page'
                
                # Check for themes
                theme = 'standard'
                if 'cyberpunk' in file_path.name or 'cyberpunk' in content:
                    theme = 'cyberpunk'
                
                # Check for responsive elements
                responsive_elements = responsive_pattern.findall(content)
                
                # Check for accessibility elements
                alt_tags = accessibility_patterns['alt_tags'].findall(content)
                aria_attributes = accessibility_patterns['aria_attributes'].findall(content)
                semantic_elements = accessibility_patterns['semantic_elements'].findall(content)
                
                # Count form elements
                form_elements_found = form_elements.findall(content)
                
                # Check navigation type
                navigation_type = 'unknown'
                if 'navbar' in content and 'navbar-nav' in content:
                    navigation_type = 'bootstrap-navbar'
                elif '<nav' in content:
                    navigation_type = 'standard-nav'
                
                # Add to results
                results['responsive_elements_count'] += len(responsive_elements)
                results['accessibility']['alt_tags_count'] += len(alt_tags)
                results['accessibility']['aria_attributes_count'] += len(aria_attributes)
                results['accessibility']['semantic_elements_count'] += len(semantic_elements)
                results['form_elements_count'] += len(form_elements_found)
                
                if theme not in results['themes']:
                    results['themes'].append(theme)
                
                if navigation_type not in results['navigation_types']:
                    results['navigation_types'].append(navigation_type)
                
                # Add template info
                if is_template:
                    template_info = {
                        'path': str(file_path),
                        'type': template_type,
                        'theme': theme,
                        'responsive_elements': len(responsive_elements),
                        'accessibility_score': len(alt_tags) + len(aria_attributes) + len(semantic_elements),
                        'form_elements': len(form_elements_found)
                    }
                    results['templates'].append(template_info)
                
                print(f"    - Type: {'Template' if is_template else 'Static HTML'} ({template_type})")
                print(f"    - Theme: {theme}")
                print(f"    - Responsive Elements: {len(responsive_elements)}")
                print(f"    - Accessibility Elements: {len(alt_tags) + len(aria_attributes) + len(semantic_elements)}")
                print(f"    - Form Elements: {len(form_elements_found)}")
        
        except Exception as e:
            print(f"    - Error analyzing file: {e}")
    
    # Calculate summary statistics
    results['summary'] = {
        'total_templates': total_templates,
        'responsive_score': results['responsive_elements_count'] / max(1, total_templates),
        'accessibility_score': (results['accessibility']['alt_tags_count'] + 
                              results['accessibility']['aria_attributes_count'] + 
                              results['accessibility']['semantic_elements_count']) / max(1, total_templates),
        'themes_count': len(results['themes']),
        'navigation_types_count': len(results['navigation_types'])
    }
    
    print("\n  UI Structure Summary:")
    print(f"    - Total Templates: {total_templates}")
    print(f"    - Responsive Score: {results['summary']['responsive_score']:.1f}")
    print(f"    - Accessibility Score: {results['summary']['accessibility_score']:.1f}")
    print(f"    - Themes: {', '.join(results['themes'])}")
    print(f"    - Navigation Types: {', '.join(results['navigation_types'])}")
    
    return results

def analyze_css_styling(css_files):
    """
    Analyze CSS styling across the codebase.
    
    Args:
        css_files: List of CSS file info dicts
    
    Returns:
        Dict with CSS styling analysis results
    """
    print("  Analyzing CSS styling...")
    
    # Patterns to look for
    color_var_pattern = re.compile(r'--[a-zA-Z0-9_-]+(-color|-bg|-border|-text|\b):\s*(#[a-fA-F0-9]{3,8}|rgba?\(.*?\))')
    media_query_pattern = re.compile(r'@media\s*\([^)]+\)')
    flexbox_grid_pattern = re.compile(r'(display\s*:\s*(flex|grid)|flex-[a-z]+|grid-[a-z]+)')
    animation_pattern = re.compile(r'(animation|transition|@keyframes)')
    
    # Results structure
    results = {
        'color_variables': [],
        'media_queries_count': 0,
        'responsive_techniques': {
            'flexbox_count': 0,
            'grid_count': 0
        },
        'animations_count': 0,
        'themes': [],
        'summary': {}
    }
    
    total_css_files = 0
    
    for file_info in css_files:
        file_path = Path(file_info['path'])
        
        if not file_path.exists():
            print(f"  - File not found: {file_path}")
            continue
        
        print(f"\n  Analyzing {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                total_css_files += 1
                
                # Check for theme
                theme = 'standard'
                if 'cyberpunk' in file_path.name:
                    theme = 'cyberpunk'
                
                # Find color variables
                color_vars = color_var_pattern.findall(content)
                
                # Find media queries
                media_queries = media_query_pattern.findall(content)
                
                # Find flexbox/grid usage
                flexbox_grid = flexbox_grid_pattern.findall(content)
                flexbox_count = sum(1 for item in flexbox_grid if 'flex' in item[0])
                grid_count = sum(1 for item in flexbox_grid if 'grid' in item[0])
                
                # Find animations
                animations = animation_pattern.findall(content)
                
                # Add to results
                for var in color_vars:
                    var_name = var[0].strip()
                    var_value = var[1].strip()
                    results['color_variables'].append({'name': var_name, 'value': var_value})
                
                results['media_queries_count'] += len(media_queries)
                results['responsive_techniques']['flexbox_count'] += flexbox_count
                results['responsive_techniques']['grid_count'] += grid_count
                results['animations_count'] += len(animations)
                
                if theme not in results['themes']:
                    results['themes'].append(theme)
                
                print(f"    - Theme: {theme}")
                print(f"    - Color Variables: {len(color_vars)}")
                print(f"    - Media Queries: {len(media_queries)}")
                print(f"    - Flexbox Usage: {flexbox_count}")
                print(f"    - Grid Usage: {grid_count}")
                print(f"    - Animations: {len(animations)}")
        
        except Exception as e:
            print(f"    - Error analyzing file: {e}")
    
    # Calculate summary statistics
    results['summary'] = {
        'total_css_files': total_css_files,
        'color_variables_count': len(results['color_variables']),
        'responsive_score': results['media_queries_count'] / max(1, total_css_files),
        'modern_layout_score': (results['responsive_techniques']['flexbox_count'] + 
                              results['responsive_techniques']['grid_count']) / max(1, total_css_files),
        'animation_score': results['animations_count'] / max(1, total_css_files),
        'themes_count': len(results['themes'])
    }
    
    print("\n  CSS Styling Summary:")
    print(f"    - Total CSS Files: {total_css_files}")
    print(f"    - Color Variables: {len(results['color_variables'])}")
    print(f"    - Responsive Score: {results['summary']['responsive_score']:.1f}")
    print(f"    - Modern Layout Score: {results['summary']['modern_layout_score']:.1f}")
    print(f"    - Animation Score: {results['summary']['animation_score']:.1f}")
    print(f"    - Themes: {', '.join(results['themes'])}")
    
    return results

def analyze_js_functionality(js_files):
    """
    Analyze JavaScript functionality across the codebase.
    
    Args:
        js_files: List of JS file info dicts
    
    Returns:
        Dict with JS functionality analysis results
    """
    print("  Analyzing JavaScript functionality...")
    
    # Patterns to look for
    event_listener_pattern = re.compile(r'addEventListener\(["\']([^"\']+)["\']')
    fetch_pattern = re.compile(r'fetch\(')
    async_pattern = re.compile(r'(async\s+function|await\s+)')
    dom_manipulation_pattern = re.compile(r'(document\.getElement|document\.query|appendChild|innerHTML|textContent|createElement)')
    module_pattern = re.compile(r'(import\s+|export\s+)')
    
    # Results structure
    results = {
        'event_listeners': [],
        'fetch_api_count': 0,
        'async_await_count': 0,
        'dom_manipulation_count': 0,
        'module_usage_count': 0,
        'features': [],
        'summary': {}
    }
    
    total_js_files = 0
    
    for file_info in js_files:
        file_path = Path(file_info['path'])
        
        if not file_path.exists():
            print(f"  - File not found: {file_path}")
            continue
        
        print(f"\n  Analyzing {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                total_js_files += 1
                
                # Identify file purpose
                feature = 'unknown'
                if 'wallet' in file_path.name:
                    feature = 'wallet'
                elif 'chart' in file_path.name:
                    feature = 'chart'
                elif 'visualization' in file_path.name:
                    feature = 'visualization'
                elif 'api' in file_path.name:
                    feature = 'api'
                elif 'chat' in file_path.name:
                    feature = 'chat'
                elif 'dashboard' in file_path.name:
                    feature = 'dashboard'
                
                # Find event listeners
                event_listeners = event_listener_pattern.findall(content)
                
                # Find fetch API usage
                fetch_api = fetch_pattern.findall(content)
                
                # Find async/await usage
                async_await = async_pattern.findall(content)
                
                # Find DOM manipulation
                dom_manipulation = dom_manipulation_pattern.findall(content)
                
                # Find module usage
                module_usage = module_pattern.findall(content)
                
                # Add to results
                for event in event_listeners:
                    if event not in results['event_listeners']:
                        results['event_listeners'].append(event)
                
                results['fetch_api_count'] += len(fetch_api)
                results['async_await_count'] += len(async_await)
                results['dom_manipulation_count'] += len(dom_manipulation)
                results['module_usage_count'] += len(module_usage)
                
                if feature not in results['features']:
                    results['features'].append(feature)
                
                print(f"    - Feature: {feature}")
                print(f"    - Event Listeners: {len(event_listeners)}")
                print(f"    - Fetch API Usage: {len(fetch_api)}")
                print(f"    - Async/Await Usage: {len(async_await)}")
                print(f"    - DOM Manipulation: {len(dom_manipulation)}")
                print(f"    - Module Pattern Usage: {len(module_usage)}")
        
        except Exception as e:
            print(f"    - Error analyzing file: {e}")
    
    # Calculate summary statistics
    results['summary'] = {
        'total_js_files': total_js_files,
        'event_listeners_count': len(results['event_listeners']),
        'modern_js_score': (results['fetch_api_count'] + results['async_await_count'] + results['module_usage_count']) / max(1, total_js_files),
        'interactivity_score': (len(results['event_listeners']) + results['dom_manipulation_count']) / max(1, total_js_files),
        'features_count': len(results['features'])
    }
    
    print("\n  JavaScript Functionality Summary:")
    print(f"    - Total JS Files: {total_js_files}")
    print(f"    - Unique Event Listeners: {len(results['event_listeners'])}")
    print(f"    - Modern JS Score: {results['summary']['modern_js_score']:.1f}")
    print(f"    - Interactivity Score: {results['summary']['interactivity_score']:.1f}")
    print(f"    - Features: {', '.join(results['features'])}")
    
    return results

def generate_recommendations(ui_structure, css_styling, js_functionality):
    """
    Generate UI/UX improvement recommendations based on analysis.
    
    Args:
        ui_structure: Results from UI structure analysis
        css_styling: Results from CSS styling analysis
        js_functionality: Results from JS functionality analysis
    
    Returns:
        List of recommendation objects
    """
    recommendations = []
    
    # Check for theme consistency
    if len(ui_structure['themes']) > 1 and 'standard' in ui_structure['themes'] and 'cyberpunk' in ui_structure['themes']:
        recommendations.append({
            'category': 'Design Consistency',
            'title': 'Consolidate UI Themes',
            'description': 'The application uses both standard and cyberpunk themes. Consider consolidating to a single theme or implementing a proper theme switching mechanism.',
            'impact': 'high',
            'effort': 'medium'
        })
    
    # Check for responsive design
    if ui_structure['summary']['responsive_score'] < 5:
        recommendations.append({
            'category': 'Responsive Design',
            'title': 'Enhance Responsive Design',
            'description': 'Add more responsive design elements to ensure better mobile compatibility. Consider using more Bootstrap grid classes or CSS flexbox/grid.',
            'impact': 'high',
            'effort': 'medium'
        })
    
    # Check for accessibility
    if ui_structure['summary']['accessibility_score'] < 5:
        recommendations.append({
            'category': 'Accessibility',
            'title': 'Improve Accessibility',
            'description': 'Add more accessibility features such as ARIA attributes, alt tags, and semantic HTML elements to make the application more accessible.',
            'impact': 'high',
            'effort': 'medium'
        })
    
    # Check for CSS variable usage
    if css_styling['summary']['color_variables_count'] < 10:
        recommendations.append({
            'category': 'CSS Architecture',
            'title': 'Enhance CSS Variable Usage',
            'description': 'Implement more CSS variables for colors, spacing, and typography to improve theme consistency and maintainability.',
            'impact': 'medium',
            'effort': 'low'
        })
    
    # Check for modern JS usage
    if js_functionality['summary']['modern_js_score'] < 3:
        recommendations.append({
            'category': 'JavaScript Modernization',
            'title': 'Modernize JavaScript Code',
            'description': 'Adopt more modern JavaScript patterns like Fetch API, async/await, and ES modules to improve code maintainability and performance.',
            'impact': 'medium',
            'effort': 'high'
        })
    
    # Check for dark mode
    dark_mode_detected = any('dark' in var['name'] for var in css_styling['color_variables'])
    if not dark_mode_detected:
        recommendations.append({
            'category': 'User Experience',
            'title': 'Implement Dark Mode',
            'description': 'Add a proper dark mode option that users can toggle. This improves user experience in low-light environments and is a popular feature.',
            'impact': 'medium',
            'effort': 'medium'
        })
    
    # Check for animation usage
    if css_styling['summary']['animation_score'] < 2:
        recommendations.append({
            'category': 'Visual Design',
            'title': 'Add Subtle Animations',
            'description': 'Incorporate subtle animations and transitions to enhance user experience and provide visual feedback for interactions.',
            'impact': 'low',
            'effort': 'low'
        })
    
    # Check wallet integration
    wallet_feature_present = 'wallet' in js_functionality['features']
    if wallet_feature_present:
        recommendations.append({
            'category': 'Feature Enhancement',
            'title': 'Enhance Wallet Integration',
            'description': 'Improve the wallet integration with visual transaction history, balance graphs, and better error handling for failed connections.',
            'impact': 'high',
            'effort': 'medium'
        })
    
    # Suggest design system
    recommendations.append({
        'category': 'Design System',
        'title': 'Implement Design System',
        'description': 'Develop a comprehensive design system with component library, style guide, and usage documentation to ensure consistency across the application.',
        'impact': 'high',
        'effort': 'high'
    })
    
    # Mobile optimization
    recommendations.append({
        'category': 'Mobile Experience',
        'title': 'Optimize for Mobile Devices',
        'description': 'Enhance the mobile experience with touch-friendly controls, appropriate sizing, and possibly a Progressive Web App (PWA) implementation.',
        'impact': 'high',
        'effort': 'medium'
    })
    
    print(f"\n  Generated {len(recommendations)} UI/UX improvement recommendations")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec['title']} ({rec['impact']} impact, {rec['effort']} effort)")
    
    return recommendations

def main():
    """
    Main function to run the analysis.
    """
    print("VOT1 UI/UX Analysis Tool")
    print("========================")
    
    analyze_ui_ux()
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main() 