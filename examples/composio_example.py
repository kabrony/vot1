#!/usr/bin/env python3
"""
Composio Integration Example

This script demonstrates how to use the Composio integration in VOT1.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the Composio integration
from vot1.integrations.composio import ComposioClient
from vot1.integrations.composio.utils import (
    check_composio_status,
    get_available_models,
    generate_with_model,
    create_text_embedding,
    get_daily_usage,
    format_usage_report
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_section(title: str) -> None:
    """Print a section title."""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def print_json(data: Dict[str, Any]) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2))

def check_connection() -> None:
    """Check the connection to Composio."""
    print_section("Checking Connection to Composio")
    
    status = check_composio_status()
    
    if status.get('connected', False):
        print("✅ Connected to Composio")
        print(f"  Version: {status.get('version', 'unknown')}")
        print(f"  Status: {status.get('status', 'unknown')}")
    else:
        print(f"❌ Failed to connect to Composio: {status.get('error', 'Unknown error')}")

def list_models() -> None:
    """List available models in Composio."""
    print_section("Available Models")
    
    models = get_available_models()
    
    if not models:
        print("No models available or error retrieving models.")
        return
        
    print(f"Found {len(models)} models:")
    for i, model in enumerate(models, 1):
        model_id = model.get("id", "unknown")
        model_name = model.get("name", "unknown")
        model_type = model.get("type", "unknown")
        
        print(f"{i}. {model_name} ({model_id})")
        print(f"   Type: {model_type}")
        print(f"   Context: {model.get('context_length', 'unknown')} tokens")
        print(f"   Description: {model.get('description', 'No description')}")
        print()

def generate_text() -> None:
    """Generate text using a model."""
    print_section("Text Generation")
    
    prompt = "Write a short poem about artificial intelligence and creativity."
    print(f"Prompt: {prompt}")
    print()
    
    text, metadata = generate_with_model(
        prompt=prompt,
        model_name=None,  # Use default model
        max_tokens=200,
        temperature=0.7
    )
    
    print("Generated Text:")
    print("--------------")
    print(text)
    print()
    
    print("Metadata:")
    print(f"  Model: {metadata.get('model', 'unknown')}")
    print(f"  Tokens: {metadata.get('usage', {}).get('total_tokens', 0)}")
    print(f"  Input Tokens: {metadata.get('usage', {}).get('prompt_tokens', 0)}")
    print(f"  Output Tokens: {metadata.get('usage', {}).get('completion_tokens', 0)}")

def create_embedding() -> None:
    """Create an embedding for text."""
    print_section("Text Embedding")
    
    text = "This is a sample text for creating an embedding vector."
    print(f"Text: {text}")
    print()
    
    embedding, metadata = create_text_embedding(
        text=text,
        model_name=None  # Use default embedding model
    )
    
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print()
    
    print("Metadata:")
    print(f"  Model: {metadata.get('model', 'unknown')}")
    print(f"  Tokens: {metadata.get('usage', {}).get('total_tokens', 0)}")

def check_usage() -> None:
    """Check usage information."""
    print_section("Usage Information")
    
    usage_data = get_daily_usage()
    
    if "error" in usage_data:
        print(f"Error retrieving usage data: {usage_data['error']}")
        return
        
    report = format_usage_report(usage_data)
    print(report)

def direct_client_usage() -> None:
    """Demonstrate direct usage of the ComposioClient."""
    print_section("Direct Client Usage")
    
    # Create client
    client = ComposioClient()
    
    # Check connection
    status = client.check_connection()
    print(f"Connected: {status['connected']}")
    
    # Get model info for a specific model
    models = client.list_models()
    if "models" in models and models["models"]:
        # Get the first model ID
        model_id = models["models"][0].get("id")
        
        if model_id:
            print(f"\nGetting info for model: {model_id}")
            model_info = client.get_model_info(model_id)
            print_json(model_info)

def main() -> None:
    """Main function to run the example."""
    print("Composio Integration Example")
    print("===========================")
    print("This example demonstrates how to use the Composio integration in VOT1.")
    
    # Check connection
    check_connection()
    
    # List models
    list_models()
    
    # Generate text
    generate_text()
    
    # Create embedding
    create_embedding()
    
    # Check usage
    check_usage()
    
    # Direct client usage
    direct_client_usage()
    
    print("\nExample completed.")

if __name__ == '__main__':
    main() 