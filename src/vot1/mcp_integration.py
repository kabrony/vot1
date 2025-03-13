"""
VOT1 Model Context Protocol (MCP) Integration

This module provides integration with the Model Context Protocol (MCP) for
advanced AI capabilities, tool usage, and multi-model coordination.
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/mcp_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MCPIntegration:
    """
    Integrates VOT1 with the Model Context Protocol (MCP) for enhanced
    AI capabilities, tool usage, and multi-model coordination.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MCP integration with configuration.
        
        Args:
            config_path: Path to MCP configuration file (JSON)
        """
        self.config = self._load_config(config_path)
        self.api_key = self.config.get("api_key") or os.environ.get("MCP_API_KEY")
        self.base_url = self.config.get("base_url") or "https://api.modelcontextprotocol.ai/v1"
        self.session = requests.Session()
        
        if not self.api_key:
            logger.warning("No MCP API key provided. Integration will be limited.")
        else:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        
        self.available_models = self._get_available_models()
        logger.info(f"MCP integration initialized with {len(self.available_models)} available models")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "api_key": None,
            "base_url": "https://api.modelcontextprotocol.ai/v1",
            "default_model": "claude-3-5-sonnet",
            "request_timeout": 120,  # seconds
            "max_retries": 3,
            "retry_delay": 1.0,  # seconds
            "tools": {
                "enabled": True,
                "default_tools": ["web_search", "code_execution", "data_analysis"]
            },
            "logging": {
                "request_logging": True,
                "response_logging": True,
                "token_logging": False
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    for key, value in user_config.items():
                        if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                            # Merge nested dictionaries
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Loaded MCP configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading MCP configuration from {config_path}: {str(e)}")
                logger.info("Using default MCP configuration")
        else:
            logger.info("Using default MCP configuration")
            
        return default_config
    
    def _get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models from the MCP API."""
        if not self.api_key:
            logger.warning("No API key provided. Cannot get available models.")
            return []
        
        try:
            response = self._make_request("GET", "/models")
            if response.status_code == 200:
                models = response.json().get("data", [])
                logger.info(f"Retrieved {len(models)} available models from MCP API")
                return models
            else:
                logger.error(f"Failed to get available models: {response.status_code} {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error retrieving available models: {str(e)}")
            return []
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                    params: Dict[str, Any] = None, files: Dict[str, Any] = None,
                    retry_count: int = 0) -> requests.Response:
        """
        Make a request to the MCP API with error handling and retries.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request payload
            params: URL parameters
            files: Files to upload
            retry_count: Current retry count
            
        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Log the request if configured
            if self.config["logging"]["request_logging"]:
                log_data = data.copy() if data else {}
                if not self.config["logging"]["token_logging"] and "api_key" in log_data:
                    log_data["api_key"] = "***"
                logger.info(f"MCP API Request: {method} {url} {params} {log_data}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                files=files,
                timeout=self.config["request_timeout"]
            )
            
            # Log the response if configured
            if self.config["logging"]["response_logging"]:
                logger.info(f"MCP API Response: {response.status_code} {response.text[:200]}...")
            
            # Handle rate limiting with exponential backoff
            if response.status_code == 429 and retry_count < self.config["max_retries"]:
                retry_delay = self.config["retry_delay"] * (2 ** retry_count)
                logger.warning(f"Rate limited by MCP API. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                return self._make_request(method, endpoint, data, params, files, retry_count + 1)
            
            return response
            
        except requests.RequestException as e:
            if retry_count < self.config["max_retries"]:
                retry_delay = self.config["retry_delay"] * (2 ** retry_count)
                logger.warning(f"Request error: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                return self._make_request(method, endpoint, data, params, files, retry_count + 1)
            else:
                logger.error(f"Max retries exceeded for request to {url}: {str(e)}")
                raise
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: ID of the model
            
        Returns:
            Model information dictionary
        """
        for model in self.available_models:
            if model.get("id") == model_id:
                return model
        
        try:
            response = self._make_request("GET", f"/models/{model_id}")
            if response.status_code == 200:
                model_info = response.json()
                logger.info(f"Retrieved information for model: {model_id}")
                return model_info
            else:
                logger.error(f"Failed to get model info for {model_id}: {response.status_code} {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error retrieving model info for {model_id}: {str(e)}")
            return {}
    
    def complete(self, prompt: str, model_id: Optional[str] = None,
                max_tokens: int = 1000, temperature: float = 0.7,
                tools: Optional[List[Dict[str, Any]]] = None,
                tool_choice: Optional[str] = None,
                stop_sequences: Optional[List[str]] = None,
                stream: bool = False) -> Dict[str, Any]:
        """
        Generate a completion using the MCP API.
        
        Args:
            prompt: Text prompt for the model
            model_id: ID of the model to use (defaults to configuration)
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            tools: List of tools to make available to the model
            tool_choice: How the model should use tools ("auto", "required", None)
            stop_sequences: Sequences that will stop generation
            stream: Whether to stream the response
            
        Returns:
            Completion response dictionary
        """
        model = model_id or self.config["default_model"]
        
        # Set up tools if enabled in config
        if self.config["tools"]["enabled"] and tools is None:
            tools = self._get_default_tools()
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
            
        if tool_choice:
            payload["tool_choice"] = tool_choice
            
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        try:
            if stream:
                return self._stream_completion(payload)
            else:
                response = self._make_request("POST", "/chat/completions", data=payload)
                if response.status_code == 200:
                    completion = response.json()
                    logger.info(f"Generated completion with model {model} ({len(completion['choices'][0]['message']['content'])} chars)")
                    return completion
                else:
                    logger.error(f"Failed to generate completion: {response.status_code} {response.text}")
                    return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            return {"error": str(e)}
    
    def _stream_completion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stream a completion from the MCP API.
        
        Args:
            payload: Request payload
            
        Returns:
            Aggregated completion response
        """
        try:
            response = self._make_request("POST", "/chat/completions", data=payload)
            response.raise_for_status()
            
            # Initialize aggregated response
            aggregated_response = {
                "id": None,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": payload["model"],
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": ""},
                    "finish_reason": None
                }]
            }
            
            # Process the streaming response
            for line in response.iter_lines():
                if line:
                    if line.startswith(b"data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == b"[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            
                            # Store the ID from the first chunk
                            if aggregated_response["id"] is None:
                                aggregated_response["id"] = chunk.get("id")
                            
                            # Extract and append content
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                aggregated_response["choices"][0]["message"]["content"] += content
                            
                            # Update finish reason if present
                            finish_reason = chunk.get("choices", [{}])[0].get("finish_reason")
                            if finish_reason:
                                aggregated_response["choices"][0]["finish_reason"] = finish_reason
                                
                            # Yield the chunk for real-time processing if needed
                            yield chunk
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming response chunk: {data}")
            
            # Return the aggregated response
            return aggregated_response
            
        except Exception as e:
            logger.error(f"Error streaming completion: {str(e)}")
            return {"error": str(e)}
    
    def _get_default_tools(self) -> List[Dict[str, Any]]:
        """Get the default tools configuration from settings."""
        tools = []
        
        for tool_name in self.config["tools"]["default_tools"]:
            if tool_name == "web_search":
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                })
            elif tool_name == "code_execution":
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "execute_code",
                        "description": "Execute code in a sandbox environment",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "language": {
                                    "type": "string",
                                    "description": "The programming language",
                                    "enum": ["python", "javascript", "bash"]
                                },
                                "code": {
                                    "type": "string",
                                    "description": "The code to execute"
                                }
                            },
                            "required": ["language", "code"]
                        }
                    }
                })
            elif tool_name == "data_analysis":
                tools.append({
                    "type": "function",
                    "function": {
                        "name": "analyze_data",
                        "description": "Analyze data from various sources",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "data_source": {
                                    "type": "string",
                                    "description": "URL or path to data source"
                                },
                                "analysis_type": {
                                    "type": "string",
                                    "description": "Type of analysis to perform",
                                    "enum": ["summary", "statistical", "trend", "comparison"]
                                }
                            },
                            "required": ["data_source", "analysis_type"]
                        }
                    }
                })
                
        return tools
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool through the MCP API.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        payload = {
            "tool": tool_name,
            "parameters": parameters
        }
        
        try:
            response = self._make_request("POST", "/tools/execute", data=payload)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Executed tool {tool_name} successfully")
                return result
            else:
                logger.error(f"Failed to execute tool {tool_name}: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {"error": str(e)}
    
    def create_assistant(self, name: str, description: str, model_id: Optional[str] = None,
                        tools: Optional[List[Dict[str, Any]]] = None,
                        instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new assistant using the MCP API.
        
        Args:
            name: Name of the assistant
            description: Description of the assistant
            model_id: ID of the model to use
            tools: List of tools to make available to the assistant
            instructions: Instructions for the assistant
            
        Returns:
            Assistant creation response
        """
        model = model_id or self.config["default_model"]
        
        payload = {
            "name": name,
            "description": description,
            "model": model
        }
        
        if tools:
            payload["tools"] = tools
            
        if instructions:
            payload["instructions"] = instructions
        
        try:
            response = self._make_request("POST", "/assistants", data=payload)
            if response.status_code == 201:
                assistant = response.json()
                logger.info(f"Created assistant {name} with ID {assistant['id']}")
                return assistant
            else:
                logger.error(f"Failed to create assistant: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error creating assistant: {str(e)}")
            return {"error": str(e)}
    
    def create_thread(self, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create a new thread using the MCP API.
        
        Args:
            messages: Initial messages for the thread
            
        Returns:
            Thread creation response
        """
        payload = {}
        if messages:
            payload["messages"] = messages
        
        try:
            response = self._make_request("POST", "/threads", data=payload)
            if response.status_code == 201:
                thread = response.json()
                logger.info(f"Created thread with ID {thread['id']}")
                return thread
            else:
                logger.error(f"Failed to create thread: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error creating thread: {str(e)}")
            return {"error": str(e)}
    
    def add_message_to_thread(self, thread_id: str, content: str, role: str = "user",
                            attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Add a message to a thread using the MCP API.
        
        Args:
            thread_id: ID of the thread
            content: Content of the message
            role: Role of the message sender (usually "user")
            attachments: List of attachments
            
        Returns:
            Message creation response
        """
        payload = {
            "role": role,
            "content": content
        }
        
        if attachments:
            payload["attachments"] = attachments
        
        try:
            response = self._make_request("POST", f"/threads/{thread_id}/messages", data=payload)
            if response.status_code == 201:
                message = response.json()
                logger.info(f"Added message to thread {thread_id}")
                return message
            else:
                logger.error(f"Failed to add message to thread: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error adding message to thread: {str(e)}")
            return {"error": str(e)}
    
    def run_assistant(self, assistant_id: str, thread_id: str,
                    instructions: Optional[str] = None,
                    tools: Optional[List[Dict[str, Any]]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run an assistant on a thread using the MCP API.
        
        Args:
            assistant_id: ID of the assistant
            thread_id: ID of the thread
            instructions: Additional instructions for this run
            tools: Tools to override the assistant's configured tools
            metadata: Additional metadata for the run
            
        Returns:
            Run creation response
        """
        payload = {
            "assistant_id": assistant_id
        }
        
        if instructions:
            payload["instructions"] = instructions
            
        if tools:
            payload["tools"] = tools
            
        if metadata:
            payload["metadata"] = metadata
        
        try:
            response = self._make_request("POST", f"/threads/{thread_id}/runs", data=payload)
            if response.status_code == 201:
                run = response.json()
                logger.info(f"Started run {run['id']} for assistant {assistant_id} on thread {thread_id}")
                return run
            else:
                logger.error(f"Failed to run assistant: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error running assistant: {str(e)}")
            return {"error": str(e)}
    
    def get_run_status(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Get the status of a run using the MCP API.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            
        Returns:
            Run status response
        """
        try:
            response = self._make_request("GET", f"/threads/{thread_id}/runs/{run_id}")
            if response.status_code == 200:
                run = response.json()
                logger.info(f"Retrieved status for run {run_id}: {run['status']}")
                return run
            else:
                logger.error(f"Failed to get run status: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error getting run status: {str(e)}")
            return {"error": str(e)}
    
    def list_messages(self, thread_id: str, limit: int = 10, 
                    order: str = "desc") -> Dict[str, Any]:
        """
        List messages in a thread using the MCP API.
        
        Args:
            thread_id: ID of the thread
            limit: Maximum number of messages to return
            order: Order of messages ("asc" or "desc")
            
        Returns:
            List of messages
        """
        params = {
            "limit": limit,
            "order": order
        }
        
        try:
            response = self._make_request("GET", f"/threads/{thread_id}/messages", params=params)
            if response.status_code == 200:
                messages = response.json()
                logger.info(f"Retrieved {len(messages['data'])} messages from thread {thread_id}")
                return messages
            else:
                logger.error(f"Failed to list messages: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error listing messages: {str(e)}")
            return {"error": str(e)}
    
    def upload_file(self, file_path: str, purpose: str = "assistants") -> Dict[str, Any]:
        """
        Upload a file using the MCP API.
        
        Args:
            file_path: Path to the file
            purpose: Purpose of the file
            
        Returns:
            File upload response
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, "rb") as f:
                files = {
                    "file": (os.path.basename(file_path), f)
                }
                
                data = {
                    "purpose": purpose
                }
                
                response = self._make_request("POST", "/files", files=files, data=data)
                
                if response.status_code == 201:
                    file_obj = response.json()
                    logger.info(f"Uploaded file {file_path} with ID {file_obj['id']}")
                    return file_obj
                else:
                    logger.error(f"Failed to upload file: {response.status_code} {response.text}")
                    return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return {"error": str(e)}
    
    def cancel_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """
        Cancel a run using the MCP API.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            
        Returns:
            Run cancellation response
        """
        try:
            response = self._make_request("POST", f"/threads/{thread_id}/runs/{run_id}/cancel")
            if response.status_code == 200:
                run = response.json()
                logger.info(f"Cancelled run {run_id}")
                return run
            else:
                logger.error(f"Failed to cancel run: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error cancelling run: {str(e)}")
            return {"error": str(e)}
    
    def get_messages_in_run(self, thread_id: str, run_id: str, force_wait: bool = True,
                          polling_interval: float = 1.0, max_wait_time: float = 600.0) -> List[Dict[str, Any]]:
        """
        Get all messages generated during a run, waiting for the run to complete if necessary.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run
            force_wait: Whether to wait for the run to complete
            polling_interval: Time between polls when waiting
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            List of messages
        """
        if force_wait:
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                run_status = self.get_run_status(thread_id, run_id)
                status = run_status.get("status")
                
                if status in ["completed", "failed", "cancelled", "expired"]:
                    break
                    
                logger.info(f"Run {run_id} is {status}, waiting...")
                time.sleep(polling_interval)
                
            if time.time() - start_time >= max_wait_time:
                logger.warning(f"Timed out waiting for run {run_id} to complete")
                
        # Get messages from the thread
        messages_response = self.list_messages(thread_id)
        if "error" in messages_response:
            return []
            
        return messages_response.get("data", [])
    
    def conversation(self, messages: List[Dict[str, str]], model_id: Optional[str] = None,
                   max_tokens: int = 1000, temperature: float = 0.7,
                   tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Have a conversation with a model using the MCP API.
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            model_id: ID of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            tools: List of tools to make available to the model
            
        Returns:
            Conversation response
        """
        model = model_id or self.config["default_model"]
        
        # Set up tools if enabled in config
        if self.config["tools"]["enabled"] and tools is None:
            tools = self._get_default_tools()
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = tools
        
        try:
            response = self._make_request("POST", "/chat/completions", data=payload)
            if response.status_code == 200:
                completion = response.json()
                logger.info(f"Generated conversation response with model {model}")
                return completion
            else:
                logger.error(f"Failed to generate conversation response: {response.status_code} {response.text}")
                return {"error": response.text, "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Error generating conversation response: {str(e)}")
            return {"error": str(e)}

# Create a convenience function to get an MCP integration instance
def get_mcp_integration(config_path: Optional[str] = None) -> MCPIntegration:
    """
    Get a configured MCP integration instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configured MCPIntegration instance
    """
    return MCPIntegration(config_path)

# Example usage when run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VOT1 MCP Integration")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--prompt", help="Prompt to send to the model")
    parser.add_argument("--model", help="Model to use")
    args = parser.parse_args()
    
    if args.prompt:
        mcp = MCPIntegration(args.config)
        response = mcp.complete(
            prompt=args.prompt,
            model_id=args.model
        )
        
        if "error" in response:
            print(f"Error: {response['error']}")
        else:
            print(response["choices"][0]["message"]["content"]) 