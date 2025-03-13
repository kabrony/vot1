#!/usr/bin/env python3
"""
VOT1 Feedback Loop Runner

This script starts the feedback loop for continuous system improvement.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.core.feedback_loop import get_feedback_loop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'feedback_loop.log'), mode='a')
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='VOT1 Feedback Loop Runner')
    
    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run the feedback loop once and exit'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        help='Override the feedback loop interval (in seconds)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show the current status of the feedback loop and exit'
    )
    
    parser.add_argument(
        '--history',
        action='store_true',
        help='Show the history of feedback loop results and exit'
    )
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Get the feedback loop instance
    feedback_loop = get_feedback_loop()
    
    # Override interval if specified
    if args.interval:
        os.environ['FEEDBACK_LOOP_INTERVAL'] = str(args.interval)
        logger.info(f"Overriding feedback loop interval to {args.interval} seconds")
    
    # Show status if requested
    if args.status:
        status = feedback_loop.get_status()
        print("\nFeedback Loop Status:")
        print(f"  Enabled: {status['enabled']}")
        print(f"  Running: {status['running']}")
        print(f"  Interval: {status['interval']} seconds")
        print(f"  Last Run: {status['last_run_time'] or 'Never'}")
        print(f"  Endpoints: {status['endpoints_count']}")
        print(f"  Notification Channels: {', '.join(status['notification_channels'])}")
        print(f"  Results History: {status['results_history_count']} entries")
        return
    
    # Show history if requested
    if args.history:
        history = feedback_loop.get_results_history()
        print("\nFeedback Loop History:")
        
        if not history:
            print("  No history available")
            return
        
        for i, cycle in enumerate(history):
            print(f"\nCycle {i+1} - {cycle.get('timestamp', 'Unknown time')}")
            
            endpoints = cycle.get('endpoints', [])
            success_count = sum(1 for e in endpoints if e.get('success', False))
            failure_count = len(endpoints) - success_count
            
            print(f"  Executed {len(endpoints)} endpoints: {success_count} succeeded, {failure_count} failed")
            
            if failure_count > 0:
                print("  Failed endpoints:")
                for endpoint in endpoints:
                    if not endpoint.get('success', False):
                        print(f"    - {endpoint.get('name', 'unknown')}: {endpoint.get('error', 'Unknown error')}")
        
        return
    
    # Run once if requested
    if args.run_once:
        logger.info("Running feedback loop once")
        result = feedback_loop.run_now()
        
        endpoints = result.get('endpoints', [])
        success_count = sum(1 for e in endpoints if e.get('success', False))
        failure_count = len(endpoints) - success_count
        
        logger.info(f"Feedback loop completed: {success_count} succeeded, {failure_count} failed")
        return
    
    # Start the feedback loop
    if not feedback_loop.is_enabled():
        logger.warning("Feedback loop is disabled. Enable it in the configuration or environment variables.")
        return
    
    logger.info("Starting feedback loop")
    feedback_loop.start()
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping feedback loop")
        feedback_loop.stop()
        logger.info("Feedback loop stopped")

if __name__ == '__main__':
    main() 