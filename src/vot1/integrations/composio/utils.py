"""
Composio Utilities for VOT1

This module provides utility functions for working with Composio.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from .client import ComposioClient

# Configure logging
logger = logging.getLogger(__name__)

def get_client(mcp_url: Optional[str] = None, api_key: Optional[str] = None) -> ComposioClient:
    """
    Get a configured Composio client.
    
    Args:
        mcp_url: Optional URL for the Composio MCP endpoint.
        api_key: Optional API key for Composio.
        
    Returns:
        A configured ComposioClient instance.
    """
    return ComposioClient(mcp_url=mcp_url, api_key=api_key)

def check_composio_status() -> Dict[str, Any]:
    """
    Check the status of the Composio connection.
    
    Returns:
        Dictionary containing status information.
    """
    client = get_client()
    return client.check_connection()

def get_available_models() -> List[Dict[str, Any]]:
    """
    Get a list of available models from Composio.
    
    Returns:
        List of dictionaries containing model information.
    """
    client = get_client()
    response = client.list_models()
    
    if "error" in response:
        logger.error(f"Error getting models: {response['error']}")
        return []
        
    return response.get("models", [])

def find_model_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Find a model by name.
    
    Args:
        name: The name of the model to find.
        
    Returns:
        Dictionary containing model information, or None if not found.
    """
    models = get_available_models()
    
    for model in models:
        if model.get("name") == name or model.get("id") == name:
            return model
            
    return None

def get_daily_usage() -> Dict[str, Any]:
    """
    Get daily usage information for Composio.
    
    Returns:
        Dictionary containing usage information.
    """
    client = get_client()
    return client.get_usage()

def format_usage_report(usage_data: Dict[str, Any]) -> str:
    """
    Format usage data into a readable report.
    
    Args:
        usage_data: Dictionary containing usage information.
        
    Returns:
        Formatted usage report as a string.
    """
    if "error" in usage_data:
        return f"Error retrieving usage data: {usage_data['error']}"
        
    # Extract usage information
    daily_usage = usage_data.get("daily", {})
    monthly_usage = usage_data.get("monthly", {})
    
    # Format the report
    report = "Composio Usage Report\n"
    report += "=====================\n\n"
    
    # Daily usage
    report += "Daily Usage:\n"
    report += f"  Total Requests: {daily_usage.get('total_requests', 0)}\n"
    report += f"  Total Tokens: {daily_usage.get('total_tokens', 0)}\n"
    report += f"  Input Tokens: {daily_usage.get('input_tokens', 0)}\n"
    report += f"  Output Tokens: {daily_usage.get('output_tokens', 0)}\n\n"
    
    # Monthly usage
    report += "Monthly Usage:\n"
    report += f"  Total Requests: {monthly_usage.get('total_requests', 0)}\n"
    report += f"  Total Tokens: {monthly_usage.get('total_tokens', 0)}\n"
    report += f"  Input Tokens: {monthly_usage.get('input_tokens', 0)}\n"
    report += f"  Output Tokens: {monthly_usage.get('output_tokens', 0)}\n\n"
    
    # Model-specific usage
    model_usage = usage_data.get("models", {})
    if model_usage:
        report += "Model Usage:\n"
        for model_id, usage in model_usage.items():
            report += f"  {model_id}:\n"
            report += f"    Requests: {usage.get('requests', 0)}\n"
            report += f"    Total Tokens: {usage.get('total_tokens', 0)}\n"
            report += f"    Input Tokens: {usage.get('input_tokens', 0)}\n"
            report += f"    Output Tokens: {usage.get('output_tokens', 0)}\n"
    
    return report

def generate_with_model(prompt: str, model_name: Optional[str] = None, 
                        max_tokens: int = 1000, temperature: float = 0.7) -> Tuple[str, Dict[str, Any]]:
    """
    Generate text with a specified model.
    
    Args:
        prompt: The prompt to generate from.
        model_name: Optional name of the model to use.
        max_tokens: Maximum number of tokens to generate.
        temperature: Temperature for generation.
        
    Returns:
        Tuple containing the generated text and metadata.
    """
    client = get_client()
    
    # Find model ID if name is provided
    model_id = None
    if model_name:
        model = find_model_by_name(model_name)
        if model:
            model_id = model.get("id")
        else:
            logger.warning(f"Model '{model_name}' not found. Using default model.")
    
    # Generate text
    response = client.generate_text(
        prompt=prompt,
        model_id=model_id,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    if "error" in response:
        logger.error(f"Error generating text: {response['error']}")
        return f"Error: {response['error']}", response
        
    # Extract the generated text
    generated_text = response.get("text", "")
    
    return generated_text, response

def create_text_embedding(text: str, model_name: Optional[str] = None) -> Tuple[List[float], Dict[str, Any]]:
    """
    Create an embedding for text.
    
    Args:
        text: The text to create an embedding for.
        model_name: Optional name of the embedding model to use.
        
    Returns:
        Tuple containing the embedding vector and metadata.
    """
    client = get_client()
    
    # Find model ID if name is provided
    model_id = None
    if model_name:
        model = find_model_by_name(model_name)
        if model:
            model_id = model.get("id")
        else:
            logger.warning(f"Model '{model_name}' not found. Using default embedding model.")
    
    # Create embedding
    response = client.create_embedding(
        text=text,
        model_id=model_id
    )
    
    if "error" in response:
        logger.error(f"Error creating embedding: {response['error']}")
        return [], response
        
    # Extract the embedding
    embedding = response.get("embedding", [])
    
    return embedding, response 