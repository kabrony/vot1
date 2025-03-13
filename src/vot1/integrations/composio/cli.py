#!/usr/bin/env python3
"""
Composio CLI for VOT1

This module provides a command-line interface for interacting with Composio.
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Optional, Any

from .client import ComposioClient
from .utils import (
    check_composio_status,
    get_available_models,
    find_model_by_name,
    get_daily_usage,
    format_usage_report,
    generate_with_model,
    create_text_embedding
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the argument parser for the CLI.
    
    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description='Composio CLI for VOT1',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global options
    parser.add_argument('--mcp-url', help='Composio MCP URL')
    parser.add_argument('--api-key', help='Composio API key')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check Composio connection status')
    
    # Models command
    models_parser = subparsers.add_parser('models', help='List available models')
    models_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # Model info command
    model_info_parser = subparsers.add_parser('model-info', help='Get information about a specific model')
    model_info_parser.add_argument('model_name', help='Name or ID of the model')
    model_info_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate text with a model')
    generate_parser.add_argument('--model', help='Name or ID of the model to use')
    generate_parser.add_argument('--prompt', help='Prompt to generate from')
    generate_parser.add_argument('--prompt-file', help='File containing prompt to generate from')
    generate_parser.add_argument('--max-tokens', type=int, default=1000, help='Maximum number of tokens to generate')
    generate_parser.add_argument('--temperature', type=float, default=0.7, help='Temperature for generation')
    generate_parser.add_argument('--output-file', help='File to write output to')
    
    # Embedding command
    embedding_parser = subparsers.add_parser('embedding', help='Create an embedding for text')
    embedding_parser.add_argument('--model', help='Name or ID of the embedding model to use')
    embedding_parser.add_argument('--text', help='Text to create embedding for')
    embedding_parser.add_argument('--text-file', help='File containing text to create embedding for')
    embedding_parser.add_argument('--output-file', help='File to write embedding to')
    
    # Usage command
    usage_parser = subparsers.add_parser('usage', help='Get usage information')
    usage_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    return parser

def handle_status(args: argparse.Namespace) -> int:
    """
    Handle the status command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    client = ComposioClient(mcp_url=args.mcp_url, api_key=args.api_key)
    status = client.check_connection()
    
    if status.get('connected', False):
        print(f"✅ Connected to Composio")
        print(f"  Version: {status.get('version', 'unknown')}")
        print(f"  Status: {status.get('status', 'unknown')}")
        
        # Print available models if verbose
        if args.verbose and 'models' in status:
            print("\nAvailable models:")
            for model in status['models']:
                print(f"  - {model}")
                
        return 0
    else:
        print(f"❌ Failed to connect to Composio: {status.get('error', 'Unknown error')}")
        return 1

def handle_models(args: argparse.Namespace) -> int:
    """
    Handle the models command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    client = ComposioClient(mcp_url=args.mcp_url, api_key=args.api_key)
    response = client.list_models()
    
    if "error" in response:
        print(f"❌ Error listing models: {response['error']}")
        return 1
        
    models = response.get("models", [])
    
    if args.json:
        print(json.dumps(models, indent=2))
    else:
        print(f"Available models ({len(models)}):")
        for model in models:
            model_id = model.get("id", "unknown")
            model_name = model.get("name", "unknown")
            model_type = model.get("type", "unknown")
            
            print(f"  - {model_name} ({model_id})")
            if args.verbose:
                print(f"    Type: {model_type}")
                print(f"    Context: {model.get('context_length', 'unknown')} tokens")
                print(f"    Description: {model.get('description', 'No description')}")
                print()
    
    return 0

def handle_model_info(args: argparse.Namespace) -> int:
    """
    Handle the model-info command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    model = find_model_by_name(args.model_name)
    
    if not model:
        print(f"❌ Model '{args.model_name}' not found")
        return 1
        
    if args.json:
        print(json.dumps(model, indent=2))
    else:
        model_id = model.get("id", "unknown")
        model_name = model.get("name", "unknown")
        model_type = model.get("type", "unknown")
        
        print(f"Model: {model_name} ({model_id})")
        print(f"Type: {model_type}")
        print(f"Context Length: {model.get('context_length', 'unknown')} tokens")
        print(f"Description: {model.get('description', 'No description')}")
        
        # Print additional details if available
        if "capabilities" in model:
            print("\nCapabilities:")
            for capability in model["capabilities"]:
                print(f"  - {capability}")
                
        if "pricing" in model:
            print("\nPricing:")
            pricing = model["pricing"]
            print(f"  Input: ${pricing.get('input', 0)} per 1K tokens")
            print(f"  Output: ${pricing.get('output', 0)} per 1K tokens")
    
    return 0

def handle_generate(args: argparse.Namespace) -> int:
    """
    Handle the generate command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    # Get prompt from arguments or file
    prompt = args.prompt
    if args.prompt_file:
        try:
            with open(args.prompt_file, 'r') as f:
                prompt = f.read()
        except Exception as e:
            print(f"❌ Error reading prompt file: {e}")
            return 1
            
    if not prompt:
        print("❌ No prompt provided. Use --prompt or --prompt-file")
        return 1
        
    # Generate text
    generated_text, response = generate_with_model(
        prompt=prompt,
        model_name=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature
    )
    
    if "error" in response:
        print(f"❌ Error generating text: {response['error']}")
        return 1
        
    # Output the generated text
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                f.write(generated_text)
            print(f"✅ Generated text written to {args.output_file}")
        except Exception as e:
            print(f"❌ Error writing to output file: {e}")
            return 1
    else:
        print("\nGenerated Text:")
        print("---------------")
        print(generated_text)
        
    # Print metadata if verbose
    if args.verbose:
        print("\nMetadata:")
        print(f"  Model: {response.get('model', 'unknown')}")
        print(f"  Tokens: {response.get('usage', {}).get('total_tokens', 0)}")
        print(f"  Input Tokens: {response.get('usage', {}).get('prompt_tokens', 0)}")
        print(f"  Output Tokens: {response.get('usage', {}).get('completion_tokens', 0)}")
    
    return 0

def handle_embedding(args: argparse.Namespace) -> int:
    """
    Handle the embedding command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    # Get text from arguments or file
    text = args.text
    if args.text_file:
        try:
            with open(args.text_file, 'r') as f:
                text = f.read()
        except Exception as e:
            print(f"❌ Error reading text file: {e}")
            return 1
            
    if not text:
        print("❌ No text provided. Use --text or --text-file")
        return 1
        
    # Create embedding
    embedding, response = create_text_embedding(
        text=text,
        model_name=args.model
    )
    
    if "error" in response:
        print(f"❌ Error creating embedding: {response['error']}")
        return 1
        
    # Output the embedding
    if args.output_file:
        try:
            with open(args.output_file, 'w') as f:
                json.dump(embedding, f)
            print(f"✅ Embedding written to {args.output_file}")
        except Exception as e:
            print(f"❌ Error writing to output file: {e}")
            return 1
    else:
        print(f"\nEmbedding (dimension: {len(embedding)}):")
        print(f"First 5 values: {embedding[:5]}")
        
    # Print metadata if verbose
    if args.verbose:
        print("\nMetadata:")
        print(f"  Model: {response.get('model', 'unknown')}")
        print(f"  Tokens: {response.get('usage', {}).get('total_tokens', 0)}")
    
    return 0

def handle_usage(args: argparse.Namespace) -> int:
    """
    Handle the usage command.
    
    Args:
        args: Command-line arguments.
        
    Returns:
        Exit code.
    """
    usage_data = get_daily_usage()
    
    if "error" in usage_data:
        print(f"❌ Error getting usage data: {usage_data['error']}")
        return 1
        
    if args.json:
        print(json.dumps(usage_data, indent=2))
    else:
        report = format_usage_report(usage_data)
        print(report)
    
    return 0

def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code.
    """
    parser = setup_parser()
    args = parser.parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle commands
    if args.command == 'status':
        return handle_status(args)
    elif args.command == 'models':
        return handle_models(args)
    elif args.command == 'model-info':
        return handle_model_info(args)
    elif args.command == 'generate':
        return handle_generate(args)
    elif args.command == 'embedding':
        return handle_embedding(args)
    elif args.command == 'usage':
        return handle_usage(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main())