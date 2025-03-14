import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def update_mcp_config():
    """Update the MCP configuration file with internal tools."""
    # Locate the config file
    config_path = os.path.join("src", "vot1", "local_mcp", "config", "mcp.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # Default configuration with internal tools
    default_config = {
        "mcpServers": {
            "GITHUB": {
                "url": "https://mcp.github.anthropic.com/v1"
            },
            "PERPLEXITY": {
                "url": "https://mcp.perplexity.anthropic.com/v1"
            },
            "FIRECRAWL": {
                "url": "https://mcp.firecrawl.anthropic.com/v1"
            },
            "FIGMA": {
                "url": "https://mcp.figma.anthropic.com/v1"
            },
            "COMPOSIO": {
                "url": "https://mcp.composio.dev/v1"
            },
            "LOCAL": {
                "url": "http://localhost:5678/api"
            }
        },
        "internalTools": {
            "memory": {
                "functions": [
                    {
                        "name": "store_memory",
                        "description": "Store a memory in the system",
                        "parameters": {
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "description": "Key to identify the memory"
                                },
                                "value": {
                                    "type": "object",
                                    "description": "Value to store"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "Tags to classify the memory"
                                }
                            },
                            "required": ["key", "value"]
                        }
                    },
                    {
                        "name": "retrieve_memory",
                        "description": "Retrieve a memory from the system",
                        "parameters": {
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "description": "Key of the memory to retrieve"
                                }
                            },
                            "required": ["key"]
                        }
                    },
                    {
                        "name": "search_memories",
                        "description": "Search memories by tags",
                        "parameters": {
                            "properties": {
                                "tags": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "Tags to search for"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return"
                                }
                            },
                            "required": ["tags"]
                        }
                    }
                ]
            },
            "agent": {
                "functions": [
                    {
                        "name": "list_agents",
                        "description": "List all available agents",
                        "parameters": {
                            "properties": {}
                        }
                    },
                    {
                        "name": "send_task",
                        "description": "Send a task to an agent",
                        "parameters": {
                            "properties": {
                                "agent_id": {
                                    "type": "string",
                                    "description": "ID of the agent to send the task to"
                                },
                                "task_type": {
                                    "type": "string",
                                    "description": "Type of task to send",
                                    "enum": ["query", "analyze_repo", "scrape_url", "process_search_results", "memory", "call_function"]
                                },
                                "task_data": {
                                    "type": "object",
                                    "description": "Task data"
                                }
                            },
                            "required": ["agent_id", "task_type", "task_data"]
                        }
                    }
                ]
            },
            "perplexity": {
                "functions": [
                    {
                        "name": "search",
                        "description": "Search the web using Perplexity AI",
                        "parameters": {
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "temperature": {
                                    "type": "number",
                                    "description": "Temperature for generation",
                                    "default": 0.7
                                },
                                "max_tokens": {
                                    "type": "integer",
                                    "description": "Maximum number of tokens to generate",
                                    "default": 1000
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            },
            "github": {
                "functions": [
                    {
                        "name": "search_repos",
                        "description": "Search GitHub repositories",
                        "parameters": {
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query"
                                },
                                "sort": {
                                    "type": "string",
                                    "description": "Sort field",
                                    "enum": ["stars", "forks", "updated"],
                                    "default": "stars"
                                },
                                "order": {
                                    "type": "string",
                                    "description": "Sort order",
                                    "enum": ["asc", "desc"],
                                    "default": "desc"
                                },
                                "per_page": {
                                    "type": "integer",
                                    "description": "Results per page",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    }
                ]
            }
        }
    }
    
    # If the config file exists, update it; otherwise, create it
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
                
            # Update the existing config
            if "internalTools" not in existing_config:
                existing_config["internalTools"] = default_config["internalTools"]
            else:
                # Merge internal tools
                for tool_name, tool_config in default_config["internalTools"].items():
                    if tool_name not in existing_config["internalTools"]:
                        existing_config["internalTools"][tool_name] = tool_config
            
            # Add LOCAL server if not present
            if "LOCAL" not in existing_config.get("mcpServers", {}):
                existing_config.setdefault("mcpServers", {})["LOCAL"] = default_config["mcpServers"]["LOCAL"]
                
            # Write the updated config
            with open(config_path, 'w') as f:
                json.dump(existing_config, f, indent=2)
            
            logger.info(f"Updated MCP configuration at {config_path}")
            return True
                
        except Exception as e:
            logger.error(f"Error updating MCP configuration: {e}")
            
            # If there was an error, create a new config file
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created new MCP configuration at {config_path}")
            return True
    else:
        # Create a new config file
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created new MCP configuration at {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating MCP configuration: {e}")
            return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    update_mcp_config() 