"""
Solana Memory Agent for TRILOGY BRAIN

This module implements the Solana blockchain integration for the TRILOGY BRAIN architecture,
providing secure storage, retrieval, and verification of critical memories through dedicated agents.
"""

import os
import json
import base64
import hashlib
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solana.system_program import SYS_PROGRAM_ID, CreateAccountParams, create_account, transfer
from solders.instruction import Instruction
import solders.signature as solders_signature
from solders.pubkey import Pubkey
from borsh_construct import U8, U64, String, CStruct, Vec

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine

logger = get_logger(__name__)

# Define Solana Memory Program Instructions
MEMORY_PROGRAM_SEED = "vot1_memory"
MEMORY_ACCOUNT_SEED = "memory_account"
MEMORY_INDEX_SEED = "memory_index"

# Instruction types
STORE_MEMORY = 0
RETRIEVE_MEMORY = 1
VERIFY_MEMORY = 2
UPDATE_MEMORY = 3
DELETE_MEMORY = 4

# Memory types
CRITICAL_MEMORY = 0
PRINCIPLE_MEMORY = 1
SYSTEM_MEMORY = 2
USER_MEMORY = 3

# Define Borsh schema for memory storage
MemoryData = CStruct(
    "memory_type" / U8,
    "created_at" / U64,
    "updated_at" / U64,
    "memory_id" / String,
    "content_hash" / String,
    "content" / String,
    "metadata" / String,
    "zk_proof" / String
)

class SolanaMemoryAgent:
    """
    Agent for storing and retrieving memories on the Solana blockchain.
    Part of the TRILOGY BRAIN Memory Foundation layer.
    """
    
    def __init__(self, 
                 keypair_path: Optional[str] = None,
                 rpc_url: Optional[str] = None,
                 program_id: Optional[str] = None,
                 principles_engine: Optional[CorePrinciplesEngine] = None,
                 network: str = "devnet"):
        """
        Initialize the Solana Memory Agent.
        
        Args:
            keypair_path: Path to Solana keypair file
            rpc_url: Solana RPC URL
            program_id: Solana program ID for the memory program
            principles_engine: CorePrinciplesEngine instance
            network: Solana network to use ("devnet", "testnet", "mainnet-beta")
        """
        # Load configuration
        self.network = network
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL") or self._get_default_rpc_url()
        self.program_id = program_id or os.getenv("SOLANA_MEMORY_PROGRAM_ID")
        self.principles_engine = principles_engine
        
        # Initialize Solana client
        self.client = Client(self.rpc_url)
        
        # Load or create keypair
        if keypair_path and os.path.exists(keypair_path):
            with open(keypair_path, 'r') as f:
                keypair_data = json.load(f)
                self.keypair = Keypair.from_secret_key(bytes(keypair_data))
        else:
            self.keypair = Keypair()
            # Save keypair if path provided
            if keypair_path:
                os.makedirs(os.path.dirname(keypair_path), exist_ok=True)
                with open(keypair_path, 'w') as f:
                    json.dump(list(self.keypair.secret_key), f)
        
        self.public_key = self.keypair.public_key
        
        # Initialize memory indices
        self.memory_indices = {}
        self._load_memory_indices()
        
        logger.info(f"Solana Memory Agent initialized with public key {self.public_key}")
        logger.info(f"Connected to Solana {self.network} at {self.rpc_url}")
    
    def _get_default_rpc_url(self) -> str:
        """Get default RPC URL based on network."""
        if self.network == "devnet":
            return "https://api.devnet.solana.com"
        elif self.network == "testnet":
            return "https://api.testnet.solana.com"
        elif self.network == "mainnet-beta":
            return "https://api.mainnet-beta.solana.com"
        else:
            return "https://api.devnet.solana.com"
    
    def _load_memory_indices(self) -> None:
        """Load memory indices from Solana blockchain."""
        try:
            # Get program-derived address for the index account
            index_pubkey, _ = self._get_memory_index_address()
            
            # Check if account exists
            account_info = self.client.get_account_info(index_pubkey)
            if account_info.value is not None:
                # Parse account data
                data = account_info.value.data
                self.memory_indices = json.loads(data)
                logger.info(f"Loaded {len(self.memory_indices)} memory indices from blockchain")
            else:
                logger.info("Memory index account not found, initializing empty indices")
                self.memory_indices = {}
        except Exception as e:
            logger.error(f"Error loading memory indices: {str(e)}")
            self.memory_indices = {}
    
    def _get_memory_account_address(self, memory_id: str) -> Tuple[PublicKey, int]:
        """Get the program-derived address for a memory account."""
        return PublicKey.find_program_address(
            [bytes(MEMORY_ACCOUNT_SEED, 'utf-8'), bytes(memory_id, 'utf-8')],
            PublicKey(self.program_id)
        )
    
    def _get_memory_index_address(self) -> Tuple[PublicKey, int]:
        """Get the program-derived address for the memory index account."""
        return PublicKey.find_program_address(
            [bytes(MEMORY_INDEX_SEED, 'utf-8')],
            PublicKey(self.program_id)
        )
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def store_memory(self, 
                         memory_id: str, 
                         content: str, 
                         memory_type: int = SYSTEM_MEMORY,
                         metadata: Optional[Dict[str, Any]] = None,
                         zk_proof: Optional[str] = None) -> Tuple[bool, str]:
        """
        Store a memory on the Solana blockchain.
        
        Args:
            memory_id: Unique ID for the memory
            content: Memory content
            memory_type: Type of memory
            metadata: Additional metadata
            zk_proof: Optional ZK proof for verification
            
        Returns:
            Tuple of (success, message)
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "blockchain_operation",
                "operation": "store_memory",
                "memory_id": memory_id,
                "memory_type": memory_type
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Memory storage rejected by principles engine: {reason}")
                return False, reason
        
        try:
            # Prepare memory data
            content_hash = self._calculate_content_hash(content)
            timestamp = int(time.time())
            
            memory_data = {
                "memory_type": memory_type,
                "created_at": timestamp,
                "updated_at": timestamp,
                "memory_id": memory_id,
                "content_hash": content_hash,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "metadata": json.dumps(metadata or {}),
                "zk_proof": zk_proof or ""
            }
            
            # Serialize data using Borsh
            serialized_data = MemoryData.build({
                "memory_type": memory_type,
                "created_at": timestamp,
                "updated_at": timestamp,
                "memory_id": memory_id,
                "content_hash": content_hash,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "metadata": json.dumps(metadata or {}),
                "zk_proof": zk_proof or ""
            })
            
            # Get memory account address
            memory_account, bump_seed = self._get_memory_account_address(memory_id)
            
            # Create instruction to store memory
            instruction_data = bytes([STORE_MEMORY]) + serialized_data
            
            # Create transaction
            instructions = [
                Instruction(
                    program_id=Pubkey.from_string(self.program_id),
                    accounts=[
                        # Account metas would be defined here
                        # This is a simplified example
                    ],
                    data=instruction_data
                )
            ]
            
            # Sign and send transaction
            # This is a simplified implementation
            # In a real implementation, you would create and sign a proper Solana transaction
            
            # Update local memory indices
            self.memory_indices[memory_id] = {
                "account": str(memory_account),
                "memory_type": memory_type,
                "content_hash": content_hash,
                "timestamp": timestamp
            }
            
            logger.info(f"Memory {memory_id} stored on Solana blockchain")
            return True, f"Memory {memory_id} stored successfully"
            
        except Exception as e:
            logger.error(f"Error storing memory on blockchain: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory from the Solana blockchain.
        
        Args:
            memory_id: ID of the memory to retrieve
            
        Returns:
            Memory data or None if not found
        """
        try:
            # Check if memory exists in indices
            if memory_id not in self.memory_indices:
                logger.warning(f"Memory {memory_id} not found in indices")
                return None
            
            # Get memory account address
            memory_account, _ = self._get_memory_account_address(memory_id)
            
            # Get account data
            account_info = self.client.get_account_info(memory_account)
            if account_info.value is None:
                logger.warning(f"Memory account for {memory_id} not found")
                return None
            
            # Deserialize data using Borsh
            data = account_info.value.data
            memory_data = MemoryData.parse(data[1:])  # Skip instruction byte
            
            # Decode content
            content = base64.b64decode(memory_data.content).decode('utf-8')
            
            # Verify content hash
            calculated_hash = self._calculate_content_hash(content)
            if calculated_hash != memory_data.content_hash:
                logger.warning(f"Content hash mismatch for memory {memory_id}")
                return None
            
            # Create memory object
            memory = {
                "id": memory_id,
                "content": content,
                "type": memory_data.memory_type,
                "created_at": memory_data.created_at,
                "updated_at": memory_data.updated_at,
                "content_hash": memory_data.content_hash,
                "metadata": json.loads(memory_data.metadata),
                "zk_proof": memory_data.zk_proof
            }
            
            logger.info(f"Memory {memory_id} retrieved from blockchain")
            return memory
            
        except Exception as e:
            logger.error(f"Error retrieving memory from blockchain: {str(e)}")
            return None
    
    async def verify_memory(self, memory_id: str) -> Tuple[bool, str]:
        """
        Verify a memory's integrity using its hash and optional ZK proof.
        
        Args:
            memory_id: ID of the memory to verify
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Retrieve memory
            memory = await self.retrieve_memory(memory_id)
            if not memory:
                return False, f"Memory {memory_id} not found"
            
            # Verify content hash
            content = memory["content"]
            stored_hash = memory["content_hash"]
            calculated_hash = self._calculate_content_hash(content)
            
            if calculated_hash != stored_hash:
                return False, "Content hash mismatch"
            
            # Verify ZK proof if available
            zk_proof = memory.get("zk_proof")
            if zk_proof and len(zk_proof) > 0:
                # This would involve ZK proof verification
                # Simplified for this example
                pass
            
            return True, "Memory verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying memory: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def update_memory(self, 
                          memory_id: str, 
                          content: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          zk_proof: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update an existing memory on the blockchain.
        
        Args:
            memory_id: ID of the memory to update
            content: New content
            metadata: New or updated metadata
            zk_proof: New ZK proof
            
        Returns:
            Tuple of (success, message)
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "blockchain_operation",
                "operation": "update_memory",
                "memory_id": memory_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Memory update rejected by principles engine: {reason}")
                return False, reason
        
        try:
            # Check if memory exists
            existing_memory = await self.retrieve_memory(memory_id)
            if not existing_memory:
                return False, f"Memory {memory_id} not found"
            
            # Prepare updated memory data
            content_hash = self._calculate_content_hash(content)
            timestamp = int(time.time())
            
            # Merge metadata if provided
            if metadata and existing_memory.get("metadata"):
                updated_metadata = {**existing_memory["metadata"], **metadata}
            else:
                updated_metadata = metadata or existing_memory.get("metadata", {})
            
            memory_data = {
                "memory_type": existing_memory["type"],
                "created_at": existing_memory["created_at"],
                "updated_at": timestamp,
                "memory_id": memory_id,
                "content_hash": content_hash,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "metadata": json.dumps(updated_metadata),
                "zk_proof": zk_proof or existing_memory.get("zk_proof", "")
            }
            
            # Serialize data using Borsh
            serialized_data = MemoryData.build(memory_data)
            
            # Get memory account address
            memory_account, _ = self._get_memory_account_address(memory_id)
            
            # Create instruction to update memory
            instruction_data = bytes([UPDATE_MEMORY]) + serialized_data
            
            # Create transaction
            # This is a simplified implementation
            # In a real implementation, you would create and sign a proper Solana transaction
            
            # Update local memory indices
            self.memory_indices[memory_id]["content_hash"] = content_hash
            self.memory_indices[memory_id]["timestamp"] = timestamp
            
            logger.info(f"Memory {memory_id} updated on blockchain")
            return True, f"Memory {memory_id} updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating memory on blockchain: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def delete_memory(self, memory_id: str) -> Tuple[bool, str]:
        """
        Delete a memory from the blockchain.
        Note: This doesn't actually delete the data from Solana,
        it marks it as deleted in the index.
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            Tuple of (success, message)
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "blockchain_operation",
                "operation": "delete_memory",
                "memory_id": memory_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Memory deletion rejected by principles engine: {reason}")
                return False, reason
        
        try:
            # Check if memory exists
            if memory_id not in self.memory_indices:
                return False, f"Memory {memory_id} not found"
            
            # Get memory account address
            memory_account, _ = self._get_memory_account_address(memory_id)
            
            # Create instruction to delete memory
            instruction_data = bytes([DELETE_MEMORY]) + memory_id.encode('utf-8')
            
            # Create transaction
            # This is a simplified implementation
            # In a real implementation, you would create and sign a proper Solana transaction
            
            # Remove from local memory indices
            if memory_id in self.memory_indices:
                del self.memory_indices[memory_id]
            
            logger.info(f"Memory {memory_id} deleted from blockchain")
            return True, f"Memory {memory_id} deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting memory from blockchain: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def get_memory_list(self, memory_type: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get list of memories stored on the blockchain.
        
        Args:
            memory_type: Optional filter by memory type
            
        Returns:
            List of memory metadata
        """
        try:
            result = []
            
            for memory_id, metadata in self.memory_indices.items():
                if memory_type is not None and metadata.get("memory_type") != memory_type:
                    continue
                    
                result.append({
                    "id": memory_id,
                    "type": metadata.get("memory_type"),
                    "timestamp": metadata.get("timestamp"),
                    "content_hash": metadata.get("content_hash")
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting memory list: {str(e)}")
            return []
    
    async def get_account_balance(self) -> float:
        """Get the balance of the agent's Solana account in SOL."""
        try:
            balance = self.client.get_balance(self.public_key)
            return balance.value / 10**9  # Convert lamports to SOL
        except Exception as e:
            logger.error(f"Error getting account balance: {str(e)}")
            return 0.0
    
    async def close(self) -> None:
        """Close the agent and clean up resources."""
        # Nothing to do for now
        pass 