"""
Development Assistant API

This module provides the API routes for the Development Assistant,
which integrates Claude 3.7's extended thinking with Perplexity research
and persistent memory to enhance the development workflow.
"""

import os
import sys
import json
import logging
from functools import wraps
from typing import Dict, Any, Optional
from pathlib import Path
from flask import Blueprint, jsonify, request, current_app

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create API blueprint
dev_assistant_api = Blueprint('dev_assistant_api', __name__, url_prefix='/api/dev-assistant')

# Helper function to get the development assistant instance
def get_dev_assistant():
    """Get or create the development assistant instance from the app context."""
    if not hasattr(current_app, 'dev_assistant'):
        try:
            # Import the development assistant module
            from ..utils.dev_assistant import init_dev_assistant
            
            # Get paths from config or use defaults
            project_root = current_app.config.get('PROJECT_ROOT', os.getcwd())
            memory_path = current_app.config.get('MEMORY_PATH', os.path.join(project_root, 'memory'))
            
            # Initialize development assistant
            current_app.dev_assistant = init_dev_assistant(project_root, memory_path)
            logger.info(f"Development Assistant initialized for project: {project_root}")
        except Exception as e:
            logger.error(f"Error initializing Development Assistant: {e}")
            current_app.dev_assistant = None
    
    return current_app.dev_assistant

def handle_errors(f):
    """Error handling decorator for API routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in Development Assistant API: {str(e)}")
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    return decorated_function

@dev_assistant_api.route('/status', methods=['GET'])
@handle_errors
def status():
    """Check the status and configuration of the Development Assistant."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'initialized': False,
            'error': 'Development Assistant could not be initialized',
            'config': {}
        })
    
    return jsonify({
        'initialized': True,
        'config': {
            'codebaseRoot': dev_assistant.project_root,
            'memoryPath': dev_assistant.memory.memory_path if dev_assistant.memory else None,
            'defaultResearchDepth': 'deep',
            'perplexityConnected': dev_assistant.researcher.connected if dev_assistant.researcher else False,
            'memoryEnabled': dev_assistant.memory is not None
        }
    })

@dev_assistant_api.route('/analyze', methods=['POST'])
@handle_errors
def analyze_codebase():
    """Analyze the codebase structure and dependencies."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    path = data.get('path')
    file_extension = data.get('file_extension', '.py')
    
    result = dev_assistant.analyze_codebase(path, file_extension)
    
    return jsonify(result)

@dev_assistant_api.route('/research', methods=['POST'])
@handle_errors
def research():
    """Perform research using Perplexity AI."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    query = data.get('query')
    
    if not query:
        return jsonify({
            'error': 'Query is required',
            'success': False
        }), 400
    
    depth = data.get('depth', 'deep')
    
    result = dev_assistant.research_topic(query, depth)
    
    return jsonify(result)

@dev_assistant_api.route('/generate', methods=['POST'])
@handle_errors
def generate_script():
    """Generate a script, document, or test based on description."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    description = data.get('description')
    script_type = data.get('script_type', 'python')
    template = data.get('template')
    
    if not description:
        return jsonify({
            'error': 'Description is required',
            'success': False
        }), 400
    
    result = dev_assistant.generate_script(description, script_type, template)
    
    return jsonify(result)

@dev_assistant_api.route('/troubleshoot', methods=['POST'])
@handle_errors
def troubleshoot():
    """Troubleshoot code issues."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    code = data.get('code')
    error_message = data.get('error_message')
    
    if not code:
        return jsonify({
            'error': 'Code is required',
            'success': False
        }), 400
    
    result = dev_assistant.troubleshoot_code(code, error_message)
    
    return jsonify(result)

@dev_assistant_api.route('/architecture', methods=['POST'])
@handle_errors
def analyze_architecture():
    """Analyze the project architecture and provide recommendations."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    result = dev_assistant.analyze_project_architecture()
    
    return jsonify(result)

@dev_assistant_api.route('/read-file', methods=['GET'])
@handle_errors
def read_file():
    """Read a file from the filesystem."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({
            'error': 'Path is required',
            'success': False
        }), 400
    
    try:
        # Resolve the path relative to the project root if not absolute
        if not os.path.isabs(path):
            dev_assistant = get_dev_assistant()
            if dev_assistant:
                project_root = dev_assistant.project_root
                path = os.path.join(project_root, path)
        
        # Check if the file exists
        if not os.path.exists(path) or not os.path.isfile(path):
            return jsonify({
                'error': f'File not found: {path}',
                'success': False
            }), 404
        
        # Read the file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'content': content,
            'path': path,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': f'Error reading file: {str(e)}',
            'success': False
        }), 500

@dev_assistant_api.route('/memory/list', methods=['GET'])
@handle_errors
def list_memory():
    """List memory categories or keys within a category."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    category = request.args.get('category')
    
    if category:
        keys = dev_assistant.memory.list_keys(category)
        return jsonify({
            'keys': keys,
            'category': category,
            'success': True
        })
    else:
        categories = dev_assistant.memory.list_categories()
        return jsonify({
            'categories': categories,
            'success': True
        })

@dev_assistant_api.route('/memory/get', methods=['GET'])
@handle_errors
def get_memory():
    """Get data from memory."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    category = request.args.get('category')
    key = request.args.get('key')
    
    if not category or not key:
        return jsonify({
            'error': 'Category and key are required',
            'success': False
        }), 400
    
    data = dev_assistant.memory.retrieve(category, key)
    
    return jsonify({
        'data': data,
        'category': category,
        'key': key,
        'success': data is not None
    })

@dev_assistant_api.route('/memory/save', methods=['POST'])
@handle_errors
def save_script():
    """Save a generated script to a file."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    script_key = data.get('script_key')
    file_path = data.get('file_path')
    
    if not script_key:
        return jsonify({
            'error': 'Script key is required',
            'success': False
        }), 400
    
    result = dev_assistant.save_script(script_key, file_path)
    
    return jsonify(result)

@dev_assistant_api.route('/memory/delete', methods=['POST'])
@handle_errors
def delete_memory():
    """Delete a memory entry."""
    dev_assistant = get_dev_assistant()
    
    if not dev_assistant:
        return jsonify({
            'error': 'Development Assistant not available',
            'success': False
        }), 500
    
    data = request.json
    category = data.get('category')
    key = data.get('key')
    
    if not category or not key:
        return jsonify({
            'error': 'Category and key are required',
            'success': False
        }), 400
    
    # Check if the memory manager has a delete method
    if hasattr(dev_assistant.memory, 'delete'):
        success = dev_assistant.memory.delete(category, key)
    else:
        # Basic delete implementation
        try:
            file_path = os.path.join(dev_assistant.memory.memory_path, category, f"{key}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                success = True
            else:
                success = False
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            success = False
    
    return jsonify({
        'success': success,
        'category': category,
        'key': key
    })

def init_dev_assistant_api(app):
    """Initialize the Development Assistant API routes."""
    app.register_blueprint(dev_assistant_api)
    logger.info("Development Assistant API routes initialized") 