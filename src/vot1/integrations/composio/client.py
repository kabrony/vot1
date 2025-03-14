"""
Composio Client for VOT1

This module provides a client for interacting with the Composio API.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

class ComposioClient:
    """Client for interacting with the Composio API"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Composio client
        
        Args:
            api_key: Composio API key (defaults to COMPOSIO_API_KEY environment variable)
            base_url: Composio API base URL (defaults to COMPOSIO_MCP_URL environment variable)
        """
        self.api_key = api_key or os.environ.get('COMPOSIO_API_KEY')
        self.base_url = base_url or os.environ.get('COMPOSIO_MCP_URL')
        
        if not self.base_url:
            raise ValueError("Composio base URL not provided and COMPOSIO_MCP_URL environment variable not set")
        
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        # Set up session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Add API key to headers if available
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def check_connection(self) -> Dict[str, Any]:
        """
        Check the connection to the Composio API
        
        Returns:
            Dict containing connection status and version information
        """
        try:
            # Try to get models as a simple connection test
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            
            # Get version information if available
            version = "unknown"
            try:
                version_response = self.session.get(f"{self.base_url}/version")
                if version_response.status_code == 200:
                    version_data = version_response.json()
                    version = version_data.get('version', 'unknown')
            except Exception as e:
                logger.warning(f"Failed to get Composio version: {e}")
            
            return {
                "connected": True,
                "version": version
            }
        except Exception as e:
            logger.error(f"Failed to connect to Composio API: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all available models
        
        Returns:
            Dict containing list of models
        """
        try:
            response = self.session.get(f"{self.base_url}/models")
            response.raise_for_status()
            data = response.json()
            
            # Process models to ensure consistent format
            models = data.get('data', [])
            processed_models = []
            
            for model in models:
                processed_model = {
                    'id': model.get('id'),
                    'name': model.get('name', model.get('id')),
                    'type': model.get('type', 'unknown'),
                    'context_length': model.get('context_length', model.get('max_tokens', 0)),
                    'description': model.get('description', '')
                }
                processed_models.append(processed_model)
            
            return {
                'models': processed_models
            }
        except Exception as e:
            logger.error(f"Failed to list Composio models: {e}")
            return {
                'error': str(e)
            }
    
    def generate_text(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate text using a Composio model
        
        Args:
            prompt: The prompt to generate text from
            model_id: ID of the model to use (optional)
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling (0.0 to 1.0)
            stop_sequences: List of sequences that will stop generation
            
        Returns:
            Dict containing generated text and metadata
        """
        try:
            payload = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature
            }
            
            if model_id:
                payload['model'] = model_id
                
            if stop_sequences:
                payload['stop'] = stop_sequences
            
            response = self.session.post(f"{self.base_url}/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Process response to ensure consistent format
            result = {
                'text': data.get('choices', [{}])[0].get('text', ''),
                'model': data.get('model', model_id or 'unknown')
            }
            
            # Add usage information if available
            if 'usage' in data:
                result['usage'] = {
                    'prompt_tokens': data['usage'].get('prompt_tokens', 0),
                    'completion_tokens': data['usage'].get('completion_tokens', 0),
                    'total_tokens': data['usage'].get('total_tokens', 0)
                }
            
            return result
        except Exception as e:
            logger.error(f"Failed to generate text: {e}")
            return {
                'error': str(e)
            }
    
    def create_embedding(
        self,
        text: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an embedding for the given text
        
        Args:
            text: The text to create an embedding for
            model_id: ID of the model to use (optional)
            
        Returns:
            Dict containing the embedding and metadata
        """
        try:
            payload = {
                'input': text
            }
            
            if model_id:
                payload['model'] = model_id
            
            response = self.session.post(f"{self.base_url}/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Process response to ensure consistent format
            result = {
                'embedding': data.get('data', [{}])[0].get('embedding', []),
                'model': data.get('model', model_id or 'unknown')
            }
            
            # Add usage information if available
            if 'usage' in data:
                result['usage'] = {
                    'prompt_tokens': data['usage'].get('prompt_tokens', 0),
                    'total_tokens': data['usage'].get('total_tokens', 0)
                }
            
            return result
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return {
                'error': str(e)
            }
    
    def get_usage(self) -> Dict[str, Any]:
        """
        Get usage statistics for the Composio account
        
        Returns:
            Dict containing usage statistics
        """
        try:
            response = self.session.get(f"{self.base_url}/usage")
            response.raise_for_status()
            data = response.json()
            
            # Process response to ensure consistent format
            result = {
                'daily': {
                    'total_requests': data.get('daily', {}).get('requests', 0),
                    'total_tokens': data.get('daily', {}).get('tokens', 0),
                    'input_tokens': data.get('daily', {}).get('input_tokens', 0),
                    'output_tokens': data.get('daily', {}).get('output_tokens', 0)
                },
                'monthly': {
                    'total_requests': data.get('monthly', {}).get('requests', 0),
                    'total_tokens': data.get('monthly', {}).get('tokens', 0),
                    'input_tokens': data.get('monthly', {}).get('input_tokens', 0),
                    'output_tokens': data.get('monthly', {}).get('output_tokens', 0)
                }
            }
            
            # Add model-specific usage if available
            if 'models' in data:
                result['models'] = {}
                for model_id, usage in data['models'].items():
                    result['models'][model_id] = {
                        'requests': usage.get('requests', 0),
                        'total_tokens': usage.get('tokens', 0),
                        'input_tokens': usage.get('input_tokens', 0),
                        'output_tokens': usage.get('output_tokens', 0)
                    }
            
            return result
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {
                'error': str(e)
            }
    
    def import_openapi_spec(
        self,
        spec_file_path: str,
        auth_file_path: Optional[str] = None,
        tool_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Import an OpenAPI specification to create a tool
        
        Args:
            spec_file_path: Path to the OpenAPI specification file
            auth_file_path: Path to the authentication configuration file (optional)
            tool_name: Custom name for the tool (optional)
            description: Custom description for the tool (optional)
            tags: List of tags for the tool (optional)
            
        Returns:
            Dict containing the created tool information
        """
        try:
            # Read the spec file
            with open(spec_file_path, 'r') as f:
                spec_content = f.read()
            
            # Read the auth file if provided
            auth_content = None
            if auth_file_path:
                with open(auth_file_path, 'r') as f:
                    auth_content = f.read()
            
            # Prepare multipart form data
            files = {
                'spec': ('spec.yaml', spec_content, 'application/yaml')
            }
            
            if auth_content:
                files['auth'] = ('auth.yaml', auth_content, 'application/yaml')
            
            # Prepare metadata
            data = {}
            if tool_name:
                data['name'] = tool_name
            if description:
                data['description'] = description
            if tags:
                data['tags'] = json.dumps(tags)
            
            response = self.session.post(
                f"{self.base_url}/tools/import",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                'tool': result
            }
        except Exception as e:
            logger.error(f"Failed to import OpenAPI spec: {e}")
            return {
                'error': str(e)
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all available tools
        
        Returns:
            Dict containing list of tools
        """
        try:
            response = self.session.get(f"{self.base_url}/tools")
            response.raise_for_status()
            data = response.json()
            
            return {
                'tools': data.get('tools', [])
            }
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return {
                'error': str(e)
            }
    
    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Get details for a specific tool
        
        Args:
            tool_id: ID of the tool to get
            
        Returns:
            Dict containing tool details
        """
        try:
            response = self.session.get(f"{self.base_url}/tools/{tool_id}")
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logger.error(f"Failed to get tool details: {e}")
            return {
                'error': str(e)
            }
    
    def delete_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool
        
        Args:
            tool_id: ID of the tool to delete
            
        Returns:
            Dict containing result of the operation
        """
        try:
            response = self.session.delete(f"{self.base_url}/tools/{tool_id}")
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'message': data.get('message', 'Tool deleted successfully')
            }
        except Exception as e:
            logger.error(f"Failed to delete tool: {e}")
            return {
                'error': str(e)
            }
    
    def execute_tool_action(
        self,
        tool_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an action on a tool
        
        Args:
            tool_id: ID of the tool
            action: Name of the action to execute
            parameters: Parameters for the action
            
        Returns:
            Dict containing the result of the action
        """
        try:
            payload = {
                'action': action,
                'parameters': parameters
            }
            
            response = self.session.post(
                f"{self.base_url}/tools/{tool_id}/execute",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                'result': data.get('result', {})
            }
        except Exception as e:
            logger.error(f"Failed to execute tool action: {e}")
            return {
                'error': str(e)
            }

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    composio = ComposioClient()
    
    # Check connection
    status = composio.check_connection()
    print(json.dumps(status, indent=2))
    
    # List models
    models = composio.list_models()
    print(json.dumps(models, indent=2)) 