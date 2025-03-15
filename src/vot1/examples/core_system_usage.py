#!/usr/bin/env python3
"""
VOT1 Core System Usage Example

This example demonstrates how to use the VOT1 components together effectively,
including the principles engine, memory system, composio integration,
blockchain components and feedback loop.

Usage:
    python -m src.vot1.examples.core_system_usage

This creates a working VOT1 system instance that processes a sample prompt
while enforcing core principles and utilizing memory.
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to path if needed
src_path = str(Path(__file__).parent.parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import VOT1 components
from vot1.core.principles import CorePrinciplesEngine
from vot1.memory import MemoryManager
from vot1.composio.client import ComposioClient
from vot1.composio.memory_bridge import ComposioMemoryBridge
from vot1.core.feedback_loop import FeedbackLoop
from vot1.blockchain.zk import ZKProofSystem
from vot1.blockchain.helius import HeliusClient
from vot1.blockchain.tokenomics import TokenomicsManager


class VOT1System:
    """
    Integrated VOT1 system that combines all core components.
    
    This class demonstrates how to effectively integrate:
    - Core Principles Engine
    - Memory Management
    - Composio Integration
    - Blockchain Components
    - Feedback Loop
    
    The system follows a modular design where components can be
    enabled/disabled based on configuration.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the VOT1 system with optional configuration.
        
        Args:
            config_path: Path to system configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.memory_manager = None
        self.principles_engine = None
        self.composio_client = None
        self.memory_bridge = None
        self.feedback_loop = None
        self.zk_system = None
        self.helius_client = None
        self.tokenomics = None
        
        logger.info("VOT1 System initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load system configuration"""
        # Default configuration
        default_config = {
            "memory": {
                "enabled": True,
                "memory_path": os.getenv("VOT1_MEMORY_PATH", "memory"),
                "vector_store": "faiss"
            },
            "principles": {
                "enabled": True,
                "enforce_principles": True
            },
            "composio": {
                "enabled": True,
                "api_key": os.getenv("COMPOSIO_API_KEY", ""),
                "mcp_url": os.getenv("COMPOSIO_MCP_URL", "https://api.composio.dev/v1"),
                "default_model": "claude-3-7-sonnet"
            },
            "blockchain": {
                "enabled": False,
                "helius_api_key": os.getenv("HELIUS_API_KEY", ""),
                "phantom_enabled": False
            },
            "feedback_loop": {
                "enabled": True,
                "evaluation_interval": 300  # 5 minutes
            }
        }
        
        # Load user configuration if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Update default config with user settings
                for section, settings in user_config.items():
                    if section in default_config:
                        default_config[section].update(settings)
                    else:
                        default_config[section] = settings
                
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
        
        # Debug: Print loaded configuration
        logger.info(f"Composio API Key: {default_config['composio']['api_key'][:5]}... (truncated)")
        logger.info(f"Composio MCP URL: {default_config['composio']['mcp_url']}")
        
        return default_config
    
    async def setup(self):
        """Set up and connect all VOT1 components"""
        logger.info("Setting up VOT1 system components...")
        
        # Set up memory manager
        if self.config["memory"]["enabled"]:
            await self._setup_memory()
        
        # Set up core principles engine
        if self.config["principles"]["enabled"]:
            await self._setup_principles()
        
        # Set up Composio client and memory bridge
        if self.config["composio"]["enabled"]:
            await self._setup_composio()
        
        # Set up blockchain components
        if self.config["blockchain"]["enabled"]:
            await self._setup_blockchain()
        
        # Set up feedback loop
        if self.config["feedback_loop"]["enabled"]:
            await self._setup_feedback_loop()
        
        logger.info("VOT1 system setup complete")
    
    async def _setup_memory(self):
        """Set up memory management"""
        memory_config = self.config["memory"]
        memory_path = memory_config["memory_path"]
        
        # Create memory system
        self.memory_manager = MemoryManager(
            memory_path=memory_path
        )
        
        logger.info(f"Memory manager initialized with path: {memory_path}")
    
    async def _setup_principles(self):
        """Set up core principles engine"""
        principles_config = self.config["principles"]
        
        # Initialize the principles engine
        self.principles_engine = CorePrinciplesEngine(
            enforce=principles_config.get("enforce_principles", True)
        )
        
        # Check if principles are already inscribed
        verification = self.principles_engine.verify_inscription()
        if not verification.get("verified", False):
            # Inscribe principles if not already inscribed
            inscription = self.principles_engine.inscribe_principles()
            logger.info(f"Core principles inscribed: {inscription.get('status')}")
        else:
            logger.info("Core principles already inscribed and verified")
        
        logger.info("Principles engine initialized")
    
    async def _setup_composio(self):
        """Set up Composio client and memory bridge"""
        composio_config = self.config["composio"]
        
        # Create Composio client
        self.composio_client = ComposioClient(
            api_key=composio_config.get("api_key", ""),
            mcp_url=composio_config.get("mcp_url", ""),
            default_model=composio_config.get("default_model", "claude-3-7-sonnet"),
            max_thinking_tokens=int(os.getenv("VOT1_MAX_THINKING_TOKENS", "120000"))
        )
        
        # Test connection
        connection_status = await self.composio_client.test_connection()
        if not connection_status:
            logger.warning("Composio connection test failed")
        else:
            logger.info("Composio connection successful")
        
        # Create memory bridge if memory manager is available
        if self.memory_manager:
            self.memory_bridge = ComposioMemoryBridge(
                memory_manager=self.memory_manager,
                composio_client=self.composio_client
            )
            logger.info("Composio memory bridge initialized")
        else:
            logger.warning("Cannot create memory bridge: Memory manager not available")
    
    async def _setup_blockchain(self):
        """Set up blockchain components"""
        blockchain_config = self.config["blockchain"]
        
        # Create ZK proof system
        self.zk_system = ZKProofSystem(
            memory_manager=self.memory_manager
        )
        logger.info("ZK proof system initialized")
        
        # Create Helius client if API key is available
        helius_api_key = blockchain_config.get("helius_api_key", "")
        if helius_api_key:
            self.helius_client = HeliusClient(
                api_key=helius_api_key,
                memory_manager=self.memory_manager
            )
            logger.info("Helius client initialized")
        
        # Create tokenomics manager
        self.tokenomics = TokenomicsManager(
            token_symbol="VOT",
            network="devnet",
            helius_client=self.helius_client
        )
        logger.info("Tokenomics manager initialized")
    
    async def _setup_feedback_loop(self):
        """Set up feedback loop"""
        feedback_config = self.config["feedback_loop"]
        
        # Create feedback loop
        self.feedback_loop = FeedbackLoop(
            memory_manager=self.memory_manager,
            principles_engine=self.principles_engine,
            composio_bridge=self.memory_bridge,
            evaluation_interval=feedback_config.get("evaluation_interval", 300)
        )
        
        # Apply to VOT1 system (self)
        result = await self.feedback_loop.apply_to_vot1_system(self)
        if result.get("status") == "applied":
            logger.info("Feedback loop applied successfully")
        else:
            logger.warning(f"Feedback loop application failed: {result.get('reason')}")
    
    async def process_prompt(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a user prompt with the VOT1 system
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            
        Returns:
            Dictionary with response data
        """
        logger.info(f"Processing prompt: {prompt[:50]}...")
        start_time = time.time()
        
        # Verify action against principles
        if self.principles_engine and self.config["principles"].get("enforce_principles", True):
            verification = self.principles_engine.verify_action(
                action_type="process_prompt",
                action_details={
                    "prompt": prompt,
                    "system": system,
                    "timestamp": time.time(),
                    "explanation": "Processing user query about VOT1 memory systems",
                    "performance_metrics": {
                        "start_time": start_time,
                        "max_tokens": int(os.getenv("VOT1_MAX_THINKING_TOKENS", "120000")),
                        "hybrid_mode": os.getenv("VOT1_ENABLE_HYBRID_MODE", "true").lower() == "true"
                    }
                }
            )
            
            if not verification.get("verified", True):
                logger.warning("Prompt processing violates core principles")
                result = {
                    "error": "Principles violation",
                    "details": verification,
                    "response": "Unable to process prompt due to principles violation"
                }
                
                if self.feedback_loop:
                    self.feedback_loop.log_interaction(
                        success=False,
                        response_time=time.time() - start_time,
                        principle_violations=len([v for v in verification.get("results", []) if not v.get("verified", True)])
                    )
                
                return result
        
        # Process with memory if available
        if self.memory_bridge:
            try:
                # Process with memory bridge
                response = await self.memory_bridge.process_with_memory(
                    prompt=prompt,
                    system=system,
                    store_response=True,
                    memory_limit=5,
                    thinking=True,
                    max_tokens=int(os.getenv("VOT1_MAX_TOKENS", "1024"))
                )
                
                # Handle response
                result = {
                    "success": True,
                    "response": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "memory_ids": response.get("memory_context", {}).get("memory_ids", []),
                    "processing_time": time.time() - start_time
                }
                
                # Record tokenomics reward for successful interaction
                if self.tokenomics:
                    await self.tokenomics.reward_agent_task(
                        agent_id="vot1_system",
                        task_description="Prompt processing",
                        quality_score=0.9,
                        complexity=1.0
                    )
                
                # Log successful interaction
                if self.feedback_loop:
                    self.feedback_loop.log_interaction(
                        success=True,
                        response_time=time.time() - start_time,
                        principle_violations=0,
                        memory_ops=len(result.get("memory_ids", [])),
                        model_calls=1
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Error processing prompt: {str(e)}")
                result = {
                    "error": "Processing error",
                    "details": str(e)
                }
                
                # Log failed interaction
                if self.feedback_loop:
                    self.feedback_loop.log_interaction(
                        success=False,
                        response_time=time.time() - start_time,
                        principle_violations=0
                    )
                
                return result
        
        # Fallback to direct Composio client if memory bridge is not available
        elif self.composio_client:
            try:
                response = await self.composio_client.process_request(
                    prompt=prompt,
                    system=system
                )
                
                return {
                    "success": True,
                    "response": response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "processing_time": time.time() - start_time
                }
                
            except Exception as e:
                logger.error(f"Error processing prompt with Composio: {str(e)}")
                return {
                    "error": "Composio processing error",
                    "details": str(e)
                }
        
        # No available processing method
        else:
            logger.error("No available method to process prompt")
            return {
                "error": "Configuration error",
                "details": "Neither memory bridge nor Composio client is available"
            }
    
    async def log_memory(self, content: str, memory_type: str = "general") -> Dict[str, Any]:
        """
        Log content to semantic memory
        
        Args:
            content: Memory content
            memory_type: Type of memory
            
        Returns:
            Dictionary with memory operation result
        """
        if not self.memory_manager:
            return {"error": "Memory manager not available"}
        
        try:
            # Add to semantic memory
            memory_id = self.memory_manager.add_semantic_memory(
                content=content,
                metadata={
                    "type": memory_type,
                    "timestamp": time.time()
                }
            )
            
            return {
                "success": True,
                "memory_id": memory_id
            }
            
        except Exception as e:
            logger.error(f"Error logging memory: {str(e)}")
            return {
                "error": "Memory operation failed",
                "details": str(e)
            }
    
    async def enforce_principles(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce core principles on an action
        
        Args:
            action_data: Action data to verify
            
        Returns:
            Verification result
        """
        if not self.principles_engine:
            return {"error": "Principles engine not available"}
        
        try:
            # Verify action against principles
            result = self.principles_engine.verify_action(
                action_type=action_data.get("action_type", "unknown"),
                action_details=action_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error enforcing principles: {str(e)}")
            return {
                "error": "Principles enforcement failed",
                "details": str(e)
            }
    
    async def shutdown(self):
        """Gracefully shut down VOT1 system"""
        logger.info("Shutting down VOT1 system...")
        
        # Stop feedback loop if running
        if self.feedback_loop and self.feedback_loop.is_running:
            await self.feedback_loop.stop()
            logger.info("Feedback loop stopped")
        
        # Close Composio client session
        if self.composio_client:
            await self.composio_client.close()
            logger.info("Closed Composio client session")
        
        logger.info("VOT1 system shutdown complete")


async def main():
    """Run VOT1 system example"""
    print("\n🌟 VOT1 System Example 🌟\n")
    print("Initializing VOT1 system components...\n")
    
    # Create and set up VOT1 system
    vot1 = VOT1System()
    await vot1.setup()
    
    # Process a sample prompt
    sample_prompt = """
    I'm interested in learning about advanced memory systems for AI. 
    Can you explain how VOT1's memory system works and its key features?
    """
    
    print("\n📝 Sample Prompt:")
    print(sample_prompt)
    print("\n⚙️ Processing...\n")
    
    # Process the prompt
    result = await vot1.process_prompt(
        prompt=sample_prompt,
        system="You are VOT1, an advanced AGI system with principles-guided operation and advanced memory capabilities."
    )
    
    # Display the result
    if result.get("success", False):
        print("✅ Response:")
        print(result["response"])
        print(f"\n⏱️ Processing Time: {result.get('processing_time', 0):.2f} seconds")
        if "memory_ids" in result:
            print(f"🧠 Memory Contexts Used: {len(result['memory_ids'])}")
    else:
        print("❌ Error:")
        print(result.get("error", "Unknown error"))
        print(result.get("details", ""))
    
    # Check system health via feedback loop
    if vot1.feedback_loop:
        print("\n🔍 System Health Check:")
        health = vot1.feedback_loop._calculate_system_health()
        print(f"Overall Health: {health['overall_health']}")
        if health['strengths']:
            print(f"Strengths: {', '.join(health['strengths'])}")
        if health['areas_of_concern']:
            print(f"Areas of Concern: {', '.join(health['areas_of_concern'])}")
    
    # Shutdown
    await vot1.shutdown()
    print("\n👋 VOT1 system shutdown complete")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 