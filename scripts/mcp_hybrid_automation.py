#!/usr/bin/env python3
"""
MCP Hybrid Model Automation Script

This script provides a foundation for using the Model Control Protocol (MCP) with 
a hybrid model approach that optimizes for both cost and performance by using:
- Claude 3.7 Sonnet with extended thinking for complex tasks
- Claude 3.5 Sonnet for simpler tasks
"""

import os
import sys
import argparse
import logging
import json
from typing import Dict, Any, Optional, List, Union
import time

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vot1.vot_mcp import VotModelControlProtocol
from src.vot1.memory import MemoryManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'mcp_automation.log'), mode='a')
    ]
)
logger = logging.getLogger(__name__)

class McpHybridAutomation:
    """
    Provides automation for MCP with hybrid model approach.
    
    This class manages the use of multiple models through MCP, optimizing for both
    cost and performance by using different models for different types of tasks.
    """
    
    # Constants for models
    SONNET_MODEL = "claude-3-7-sonnet-20240620"
    THIN_MODEL = "claude-3-5-sonnet-20240620"
    
    def __init__(
        self,
        primary_model: str = SONNET_MODEL,
        secondary_model: str = THIN_MODEL,
        use_extended_thinking: bool = False,
        max_thinking_tokens: int = 5000,
        memory_manager = None
    ):
        """
        Initialize the MCP hybrid automation.
        
        Args:
            primary_model: Model to use for complex tasks
            secondary_model: Model to use for simple tasks
            use_extended_thinking: Whether to enable extended thinking for the primary model
            max_thinking_tokens: Maximum thinking tokens when extended thinking is enabled
            memory_manager: Optional memory manager for context
        """
        self.primary_model = primary_model
        self.secondary_model = secondary_model
        self.use_extended_thinking = use_extended_thinking
        self.max_thinking_tokens = max_thinking_tokens if use_extended_thinking else 0
        
        # Set up memory manager
        self.memory_manager = memory_manager
        if self.memory_manager is None:
            try:
                memory_path = os.environ.get('VOT1_MEMORY_PATH', os.path.join(os.getcwd(), 'memory'))
                # Create memory directory if it doesn't exist
                os.makedirs(memory_path, exist_ok=True)
                self.memory_manager = MemoryManager(memory_path=memory_path)
                logger.info(f"Created memory manager at {memory_path}")
            except Exception as e:
                logger.warning(f"Failed to create memory manager: {e}")
                self.memory_manager = None
        
        # Setup MCP client
        self.mcp = self._setup_mcp()
        
        logger.info(f"MCP Hybrid Automation initialized")
        logger.info(f"Primary model: {self.primary_model}")
        logger.info(f"Secondary model: {self.secondary_model}")
        logger.info(f"Extended thinking: {'Enabled' if self.use_extended_thinking else 'Disabled'}")
        if self.use_extended_thinking:
            logger.info(f"Max thinking tokens: {self.max_thinking_tokens}")
    
    def _setup_mcp(self) -> VotModelControlProtocol:
        """Set up the MCP client with hybrid model configuration."""
        config = {
            "max_thinking_tokens": self.max_thinking_tokens
        }
        
        # Initialize MCP with primary and secondary models
        mcp = VotModelControlProtocol(
            primary_provider=VotModelControlProtocol.PROVIDER_ANTHROPIC,
            primary_model=self.primary_model,
            secondary_provider=VotModelControlProtocol.PROVIDER_ANTHROPIC,
            secondary_model=self.secondary_model,
            memory_manager=self.memory_manager,
            config=config
        )
        
        return mcp
    
    def get_memory_context(self, prompt: str, max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories for the given prompt.
        
        Args:
            prompt: The prompt to retrieve context for
            max_memories: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memories with their metadata
        """
        if not self.memory_manager:
            return []
        
        try:
            memories = self.memory_manager.search(prompt, limit=max_memories)
            if not memories:
                return []
            
            context = []
            for memory in memories:
                context.append({
                    "id": memory.get("id", "unknown"),
                    "content": memory.get("content", ""),
                    "metadata": memory.get("metadata", {})
                })
            
            return context
        except Exception as e:
            logger.error(f"Error retrieving memory context: {e}")
            return []
    
    def process_with_optimal_model(
        self,
        prompt: str,
        task_complexity: str = "auto",
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        use_memory: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """
        Process a request using the optimal model based on task complexity.
        
        Args:
            prompt: The input prompt to process
            task_complexity: Complexity level ("simple", "medium", "complex", or "auto")
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            use_memory: Whether to retrieve and use memory context
            
        Returns:
            Response from the model
        """
        # Determine which model to use based on task complexity
        if task_complexity == "auto":
            # TODO: Implement automatic complexity detection
            model = self.secondary_model
        elif task_complexity == "simple" or task_complexity == "medium":
            model = self.secondary_model
            logger.info(f"Using secondary model ({self.secondary_model}) for {task_complexity} task")
        else:  # "complex" or unknown
            model = self.primary_model
            logger.info(f"Using primary model ({self.primary_model}) for {task_complexity} task")
        
        # Retrieve relevant context from memory if available
        memory_context = []
        context = None
        if use_memory and self.memory_manager:
            memory_context = self.get_memory_context(prompt)
            if memory_context:
                logger.info(f"Retrieved {len(memory_context)} relevant memories")
                # Create context dictionary for the MCP
                context = {
                    "memories": memory_context
                }
        
        # Prepare system prompt with memory context if available
        enhanced_system = system
        if memory_context and system:
            memory_content = "\n\nHere are some relevant memories that may be helpful:\n\n"
            for i, memory in enumerate(memory_context):
                memory_content += f"Memory #{i+1}:\n{memory['content']}\n\n"
            enhanced_system = system + memory_content
        elif memory_context:
            memory_content = "Here are some relevant memories that may be helpful:\n\n"
            for i, memory in enumerate(memory_context):
                memory_content += f"Memory #{i+1}:\n{memory['content']}\n\n"
            enhanced_system = memory_content
        
        # Process with MCP
        try:
            # Process request with appropriate model
            response = self.mcp.process_request(
                prompt=prompt,
                system=enhanced_system,
                temperature=temperature,
                max_tokens=max_tokens or 1024,
                context=context
            )
            
            # Store the interaction in memory if memory manager is available
            if self.memory_manager:
                try:
                    # Store user prompt
                    self.memory_manager.add_conversation_memory(
                        role="user",
                        content=prompt,
                        metadata={"timestamp": time.time()}
                    )
                    
                    # Store assistant response
                    response_content = response.get("content", "") if isinstance(response, dict) else response
                    self.memory_manager.add_conversation_memory(
                        role="assistant",
                        content=response_content,
                        metadata={
                            "timestamp": time.time(),
                            "model": model,
                            "complexity": task_complexity
                        }
                    )
                except Exception as e:
                    logger.error(f"Error storing conversation in memory: {e}")
            
            return response
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {"content": f"Error: {str(e)}"}
    
    def batch_process(
        self,
        prompts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple prompts in batch, optimizing for cost and performance.
        
        Args:
            prompts: List of dictionaries containing prompt data
                Each dict should have:
                - 'prompt': The prompt text
                - 'task_complexity': Optional complexity ('low', 'high', 'auto')
                - 'system': Optional system prompt
                - 'context': Optional additional context
                - 'max_tokens': Optional max tokens to generate
                - 'temperature': Optional sampling temperature
                
        Returns:
            List of response data from the models
        """
        results = []
        
        for i, prompt_data in enumerate(prompts):
            logger.info(f"Processing batch item {i+1}/{len(prompts)}")
            
            # Extract parameters
            prompt = prompt_data['prompt']
            task_complexity = prompt_data.get('task_complexity', 'auto')
            system = prompt_data.get('system')
            context = prompt_data.get('context')
            max_tokens = prompt_data.get('max_tokens')
            temperature = prompt_data.get('temperature', 0.7)
            
            # Process with optimal model
            result = self.process_with_optimal_model(
                prompt=prompt,
                task_complexity=task_complexity,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            results.append(result)
        
        return results
    
    def save_response_to_file(
        self,
        response: Dict[str, Any],
        file_path: str,
        include_metadata: bool = True
    ) -> None:
        """
        Save a model response to a file.
        
        Args:
            response: Model response data
            file_path: Path to save the response to
            include_metadata: Whether to include metadata in the saved file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Prepare data to save
        if include_metadata:
            data_to_save = response
        else:
            # Only save the content
            data_to_save = {"content": response.get("content", "")}
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=2)
        
        logger.info(f"Saved response to {file_path}")

def main():
    """Main function to handle command-line arguments and process requests."""
    parser = argparse.ArgumentParser(description="VOT1 MCP Hybrid Model Automation")
    
    parser.add_argument("--prompt", type=str, help="Prompt to process")
    parser.add_argument("--prompt-file", type=str, help="File containing the prompt")
    parser.add_argument("--system", type=str, help="Optional system prompt")
    parser.add_argument("--complexity", choices=["low", "high", "auto"], default="auto",
                       help="Task complexity (determines model selection)")
    parser.add_argument("--extended-thinking", action="store_true", 
                       help="Enable extended thinking mode")
    parser.add_argument("--thinking-tokens", type=int, default=5000,
                       help="Maximum thinking tokens when extended thinking is enabled")
    parser.add_argument("--output", type=str, help="File to save the response to")
    parser.add_argument("--primary-model", type=str, default=McpHybridAutomation.SONNET_MODEL,
                       help="Primary model to use")
    parser.add_argument("--secondary-model", type=str, default=McpHybridAutomation.THIN_MODEL,
                       help="Secondary model to use")
    
    args = parser.parse_args()
    
    # Get prompt
    prompt = args.prompt
    if args.prompt_file:
        try:
            with open(args.prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        except Exception as e:
            logger.error(f"Error reading prompt file: {e}")
            sys.exit(1)
    
    if not prompt:
        logger.error("No prompt provided. Use --prompt or --prompt-file.")
        sys.exit(1)
    
    # Setup MCP hybrid automation
    automation = McpHybridAutomation(
        primary_model=args.primary_model,
        secondary_model=args.secondary_model,
        use_extended_thinking=args.extended_thinking,
        max_thinking_tokens=args.thinking_tokens
    )
    
    # Process the request
    result = automation.process_with_optimal_model(
        prompt=prompt,
        task_complexity=args.complexity,
        system=args.system
    )
    
    # Save or print the response
    if args.output:
        automation.save_response_to_file(result, args.output)
    else:
        print(f"Response: {result['content']}")

if __name__ == "__main__":
    main() 