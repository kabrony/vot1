#!/usr/bin/env python3
"""
GitHub Webhook Handler

This script demonstrates how to receive and process GitHub webhook events.
It sets up a simple Flask server that listens for webhook requests and
processes them based on the event type.

Usage:
    python webhook_handler.py --port 5000 --secret your_webhook_secret
"""

import os
import sys
import hashlib
import hmac
import json
import logging
import argparse
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("webhook_events.log")
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Secret for webhook validation
WEBHOOK_SECRET = None

def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verify that the webhook payload was sent from GitHub by validating the signature.
    
    Args:
        payload_body: The request body
        signature_header: The GitHub signature header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not WEBHOOK_SECRET or not signature_header:
        return False
        
    # The signature header starts with 'sha256='
    signature = signature_header.split('=')[1]
    
    # Create a hash using the webhook secret
    secret_bytes = WEBHOOK_SECRET.encode('utf-8')
    mac = hmac.new(secret_bytes, msg=payload_body, digestmod=hashlib.sha256)
    
    # Compare the hashes
    expected_signature = mac.hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def process_push_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a push event.
    
    Args:
        payload: The webhook payload
        
    Returns:
        Processing result
    """
    repo_name = payload.get('repository', {}).get('full_name', 'unknown')
    pusher = payload.get('pusher', {}).get('name', 'unknown')
    ref = payload.get('ref', 'unknown')
    
    logger.info(f"Push event to {repo_name} by {pusher} to {ref}")
    
    return {
        "status": "processed",
        "event_type": "push",
        "repository": repo_name,
        "pusher": pusher,
        "ref": ref
    }

def process_pull_request_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a pull request event.
    
    Args:
        payload: The webhook payload
        
    Returns:
        Processing result
    """
    repo_name = payload.get('repository', {}).get('full_name', 'unknown')
    pr_number = payload.get('number', 'unknown')
    action = payload.get('action', 'unknown')
    user = payload.get('pull_request', {}).get('user', {}).get('login', 'unknown')
    
    logger.info(f"Pull request #{pr_number} {action} on {repo_name} by {user}")
    
    return {
        "status": "processed",
        "event_type": "pull_request",
        "repository": repo_name,
        "number": pr_number,
        "action": action,
        "user": user
    }

def process_issues_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an issues event.
    
    Args:
        payload: The webhook payload
        
    Returns:
        Processing result
    """
    repo_name = payload.get('repository', {}).get('full_name', 'unknown')
    issue_number = payload.get('issue', {}).get('number', 'unknown')
    action = payload.get('action', 'unknown')
    user = payload.get('issue', {}).get('user', {}).get('login', 'unknown')
    
    logger.info(f"Issue #{issue_number} {action} on {repo_name} by {user}")
    
    return {
        "status": "processed",
        "event_type": "issues",
        "repository": repo_name,
        "number": issue_number,
        "action": action,
        "user": user
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook requests."""
    # Get the signature from the request
    signature_header = request.headers.get('X-Hub-Signature-256')
    
    # Get the event type
    event_type = request.headers.get('X-GitHub-Event')
    
    if not event_type:
        return jsonify({"status": "error", "message": "No event type specified"}), 400
        
    # Get the payload
    payload_body = request.get_data()
    if not verify_webhook_signature(payload_body, signature_header):
        return jsonify({"status": "error", "message": "Invalid signature"}), 401
        
    # Parse the payload
    payload = json.loads(payload_body.decode('utf-8'))
    
    # Process the event based on its type
    result = {"status": "received", "event_type": event_type}
    
    try:
        if event_type == 'push':
            result = process_push_event(payload)
        elif event_type == 'pull_request':
            result = process_pull_request_event(payload)
        elif event_type == 'issues':
            result = process_issues_event(payload)
        else:
            logger.info(f"Received unhandled event type: {event_type}")
            result = {"status": "skipped", "event_type": event_type}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
    return jsonify(result), 200

def main():
    """Parse arguments and start the webhook handler server."""
    parser = argparse.ArgumentParser(description="GitHub Webhook Handler")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--secret", help="Webhook secret for validation")
    
    args = parser.parse_args()
    
    # Set the webhook secret
    global WEBHOOK_SECRET
    WEBHOOK_SECRET = args.secret or os.environ.get("WEBHOOK_SECRET")
    
    if not WEBHOOK_SECRET:
        logger.warning("No webhook secret provided. Signature validation will fail.")
        
    # Start the server
    logger.info(f"Starting webhook handler on port {args.port}")
    app.run(host='0.0.0.0', port=args.port)

if __name__ == "__main__":
    main() 