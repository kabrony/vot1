#!/usr/bin/env python3
"""
Dashboard Runner Script
Runs the unified dashboard application with Supabase integration.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run the unified dashboard application')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    # Check if Supabase is enabled
    supabase_enabled = os.environ.get('SUPABASE_ENABLED', 'false').lower() == 'true'
    if supabase_enabled:
        logger.info("Supabase integration is enabled")
        
        # Check if Supabase URL and key are set
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase URL or key not set. Check your .env file.")
    else:
        logger.info("Supabase integration is disabled")
    
    try:
        # Import the dashboard application
        from dashboard import DashboardApp
        
        # Create and run the dashboard application
        dashboard = DashboardApp(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        # Open browser if not disabled
        if not args.no_browser:
            import webbrowser
            url = f"http://{'localhost' if args.host == '0.0.0.0' else args.host}:{args.port}"
            webbrowser.open(url)
        
        # Run the dashboard application
        dashboard.start(open_browser=not args.no_browser)
        
        return 0
    except Exception as e:
        logger.error(f"Failed to run dashboard application: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 