import logging
import json
import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create API blueprint
mcp_api_bp = Blueprint('mcp_api', __name__, url_prefix='/api/mcp')

def handle_errors(f):
    """Error handling decorator for API routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in MCP API: {str(e)}")
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    return decorated_function

@mcp_api_bp.route('/perplexity/check-connection', methods=['GET'])
@handle_errors
def check_perplexity_connection():
    """Check if a connection to Perplexity AI exists"""
    try:
        # Check active connection directly with MCP tools
        # This function should be imported from your MCP tools library
        from mcp_tools import call_mcp_function
        
        response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_CHECK_ACTIVE_CONNECTION", {
            "params": {"tool": "PERPLEXITYAI"}
        })
        
        # Parse and return response data
        response_data = response.get('data', {})
        active_connection = response_data.get('active_connection', False)
        connection_details = response_data.get('connection_details', None)
        
        return jsonify({
            'active_connection': active_connection,
            'connection_details': connection_details,
            'successful': True
        })
    except Exception as e:
        logger.error(f"Error checking Perplexity connection: {str(e)}")
        return jsonify({
            'active_connection': False,
            'error': str(e),
            'successful': False
        })

@mcp_api_bp.route('/firecrawl/check-connection', methods=['GET'])
@handle_errors
def check_firecrawl_connection():
    """Check if a connection to Firecrawl exists"""
    try:
        # Check active connection directly with MCP tools
        from mcp_tools import call_mcp_function
        
        response = call_mcp_function("mcp_FIRECRAWL_FIRECRAWL_CHECK_ACTIVE_CONNECTION", {
            "params": {"tool": "FIRECRAWL"}
        })
        
        # Parse and return response data
        response_data = response.get('data', {})
        active_connection = response_data.get('active_connection', False)
        connection_details = response_data.get('connection_details', None)
        
        return jsonify({
            'active_connection': active_connection,
            'connection_details': connection_details,
            'successful': True
        })
    except Exception as e:
        logger.error(f"Error checking Firecrawl connection: {str(e)}")
        return jsonify({
            'active_connection': False,
            'error': str(e),
            'successful': False
        })

@mcp_api_bp.route('/perplexity/connect', methods=['POST'])
@handle_errors
def connect_perplexity():
    """Connect to Perplexity AI"""
    try:
        # Connect to Perplexity directly with MCP tools
        from mcp_tools import call_mcp_function
        
        # First get required parameters
        params_response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_GET_REQUIRED_PARAMETERS", {
            "params": {"tool": "PERPLEXITYAI"}
        })
        
        # Initialize connection
        response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_INITIATE_CONNECTION", {
            "params": {
                "tool": "PERPLEXITYAI",
                "parameters": {} # Default connector usually doesn't need parameters
            }
        })
        
        # Parse and return response data
        response_data = response.get('data', {})
        connection_id = response_data.get('connection_id')
        
        return jsonify({
            'connection_id': connection_id,
            'status': 'connected',
            'successful': True
        })
    except Exception as e:
        logger.error(f"Error connecting to Perplexity: {str(e)}")
        return jsonify({
            'error': str(e),
            'successful': False
        })

@mcp_api_bp.route('/firecrawl/connect', methods=['POST'])
@handle_errors
def connect_firecrawl():
    """Connect to Firecrawl with an API key"""
    # Get API key from request
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({
            'error': 'API key is required',
            'successful': False
        }), 400
    
    try:
        # Connect to Firecrawl directly with MCP tools
        from mcp_tools import call_mcp_function
        
        # Initialize connection with API key
        response = call_mcp_function("mcp_FIRECRAWL_FIRECRAWL_INITIATE_CONNECTION", {
            "params": {
                "tool": "FIRECRAWL",
                "parameters": {
                    "api_key": api_key
                }
            }
        })
        
        # Parse and return response data
        response_data = response.get('data', {})
        connection_id = response_data.get('connection_id')
        
        return jsonify({
            'connection_id': connection_id,
            'status': 'connected',
            'successful': True
        })
    except Exception as e:
        logger.error(f"Error connecting to Firecrawl: {str(e)}")
        return jsonify({
            'error': str(e),
            'successful': False
        })

@mcp_api_bp.route('/perplexity/search', methods=['POST'])
@handle_errors
def perplexity_search():
    """Perform a search using Perplexity AI"""
    # Check for active connection first (you may skip this if performance is critical)
    connection_check = check_perplexity_connection()
    connection_data = json.loads(connection_check.data)
    
    if not connection_data.get('active_connection'):
        return jsonify({
            'error': 'No active connection to Perplexity AI',
            'successful': False
        }), 400
    
    # Get query and options from request
    data = request.json
    query = data.get('query')
    options = data.get('options', {})
    
    if not query:
        return jsonify({
            'error': 'Query is required',
            'successful': False
        }), 400
    
    try:
        # Use MCP to call Perplexity
        from mcp_tools import call_mcp_function
        
        # Prepare parameters
        system_prompt = options.get('systemPrompt', "You are a research assistant. Provide thorough, accurate information with relevant details, examples, and context.")
        
        response = call_mcp_function("mcp_PERPLEXITY_PERPLEXITYAI_PERPLEXITY_AI_SEARCH", {
            "params": {
                "model": options.get('model', 'pplx-70b-online'),
                "systemContent": system_prompt,
                "userContent": query,
                "temperature": options.get('temperature', 0.7),
                "max_tokens": options.get('max_tokens', 2000),
                "return_citations": options.get('returnCitations', True),
            }
        })
        
        # Extract the content from the response
        response_data = response.get('content', [])
        content_text = ""
        
        # Parse the text content from the response
        for item in response_data:
            if item.get('type') == 'text':
                content_text += item.get('text', '')
        
        # Try to parse it as JSON if possible
        try:
            parsed_content = json.loads(content_text)
            return jsonify({
                'content': parsed_content.get('completion', ''),
                'citations': parsed_content.get('citations', []),
                'model': options.get('model', 'pplx-70b-online'),
                'successful': True
            })
        except:
            # If not valid JSON, return the raw text
            return jsonify({
                'content': content_text,
                'citations': [],
                'model': options.get('model', 'pplx-70b-online'),
                'successful': True
            })
            
    except Exception as e:
        logger.error(f"Error performing Perplexity search: {str(e)}")
        return jsonify({
            'error': str(e),
            'successful': False
        })

@mcp_api_bp.route('/firecrawl/crawl', methods=['POST'])
@handle_errors
def firecrawl_crawl():
    """Crawl a website using Firecrawl"""
    # Check for active connection first (you may skip this if performance is critical)
    connection_check = check_firecrawl_connection()
    connection_data = json.loads(connection_check.data)
    
    if not connection_data.get('active_connection'):
        return jsonify({
            'error': 'No active connection to Firecrawl',
            'successful': False
        }), 400
    
    # Get URL and options from request
    data = request.json
    url = data.get('url')
    options = data.get('options', {})
    
    if not url:
        return jsonify({
            'error': 'URL is required',
            'successful': False
        }), 400
    
    try:
        # Use MCP to call Firecrawl
        from mcp_tools import call_mcp_function
        
        # Prepare parameters with defaults
        params = {
            "url": url,
            "limit": options.get('limit', 10),
            "maxDepth": options.get('maxDepth', 2),
            "allowExternalLinks": options.get('allowExternalLinks', False),
        }
        
        # Add scrape options if provided
        if 'scrapeOptions' in options:
            scrape_options = options['scrapeOptions']
            if 'formats' in scrape_options:
                params["scrapeOptions_formats"] = scrape_options['formats']
            if 'onlyMainContent' in scrape_options:
                params["scrapeOptions_onlyMainContent"] = scrape_options['onlyMainContent']
        
        # Call the Firecrawl API
        response = call_mcp_function("mcp_FIRECRAWL_FIRECRAWL_CRAWL_URLS", {
            "params": params
        })
        
        # Process the response
        crawl_id = response.get('data', {}).get('id')
        
        # Get job status (may need polling in real implementation)
        status_response = call_mcp_function("mcp_FIRECRAWL_FIRECRAWL_CRAWL_JOB_STATUS", {
            "params": {
                "id": crawl_id
            }
        })
        
        status_data = status_response.get('data', {})
        
        return jsonify({
            'id': crawl_id,
            'status': status_data.get('status', 'unknown'),
            'url': url,
            'pages_crawled': len(status_data.get('pages', [])),
            'results': status_data.get('pages', []),
            'successful': True
        })
    except Exception as e:
        logger.error(f"Error crawling website: {str(e)}")
        return jsonify({
            'error': str(e),
            'successful': False
        })

def init_mcp_api(app):
    """Initialize the MCP API routes"""
    app.register_blueprint(mcp_api_bp)
    logger.info("MCP API routes initialized") 