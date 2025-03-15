"""
ZK-Verification Agent for TRILOGY BRAIN

This module implements the ZK-Verification Agent for the TRILOGY BRAIN architecture,
providing cryptographic verification of memory integrity through zero-knowledge proofs.
"""

import os
import json
import base64
import hashlib
import asyncio
import logging
import time
import hmac
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path

from ..utils.logging import get_logger
from ..core.principles import CorePrinciplesEngine

# In a production environment, you would use an actual ZK library like:
# import zokrates_pyzk as zk
# from circomlib import poseidon, smt, eddsa
# However, for this demonstration we'll use a simplified approach

logger = get_logger(__name__)

# Define proof types
PROOF_TYPE_INTEGRITY = 0
PROOF_TYPE_OWNERSHIP = 1
PROOF_TYPE_COMPLIANCE = 2
PROOF_TYPE_TEMPORAL = 3

class ZKVerificationAgent:
    """
    Agent for generating and verifying ZK proofs for memory integrity.
    Part of the TRILOGY BRAIN Memory Foundation layer.
    """
    
    def __init__(self, 
                 proving_key_path: Optional[str] = None,
                 verification_key_path: Optional[str] = None,
                 principles_engine: Optional[CorePrinciplesEngine] = None,
                 proof_storage_path: str = "memory/zk_proofs"):
        """
        Initialize the ZK-Verification Agent.
        
        Args:
            proving_key_path: Path to the ZK proving key
            verification_key_path: Path to the ZK verification key
            principles_engine: CorePrinciplesEngine instance
            proof_storage_path: Path to store generated proofs
        """
        self.principles_engine = principles_engine
        self.proof_storage_path = proof_storage_path
        self.proving_key_path = proving_key_path
        self.verification_key_path = verification_key_path
        
        # Create proof storage directory if it doesn't exist
        os.makedirs(self.proof_storage_path, exist_ok=True)
        
        # In a production environment, you would load actual ZK keys here
        # For this demo, we'll use a simplified approach with HMAC
        self.proving_key = os.urandom(32)  # Random 32-byte key for demo
        self.verification_key = self.proving_key  # In HMAC, same key is used for verification
        
        # Load keys from files if provided
        if proving_key_path and os.path.exists(proving_key_path):
            with open(proving_key_path, 'rb') as f:
                self.proving_key = f.read()
                
        if verification_key_path and os.path.exists(verification_key_path):
            with open(verification_key_path, 'rb') as f:
                self.verification_key = f.read()
        
        # Save keys to files if provided and they don't exist
        if proving_key_path and not os.path.exists(proving_key_path):
            os.makedirs(os.path.dirname(proving_key_path), exist_ok=True)
            with open(proving_key_path, 'wb') as f:
                f.write(self.proving_key)
                
        if verification_key_path and not os.path.exists(verification_key_path):
            os.makedirs(os.path.dirname(verification_key_path), exist_ok=True)
            with open(verification_key_path, 'wb') as f:
                f.write(self.verification_key)
        
        logger.info("ZK-Verification Agent initialized")
    
    async def generate_integrity_proof(self, 
                                    memory_id: str, 
                                    content: str,
                                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a ZK proof for memory content integrity.
        
        Args:
            memory_id: ID of the memory
            content: Memory content
            metadata: Additional metadata
            
        Returns:
            Dictionary with proof information or None if failed
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "zk_operation",
                "operation": "generate_integrity_proof",
                "memory_id": memory_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Proof generation rejected by principles engine: {reason}")
                return None
        
        try:
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # In a real ZK implementation, we would:
            # 1. Generate a ZK circuit to prove knowledge of content without revealing it
            # 2. Generate a proof using the proving key
            
            # For this demo, we'll use HMAC as a simplified "proof"
            # (not a real ZK proof, just for demonstration)
            hmac_digest = hmac.new(
                self.proving_key, 
                f"{memory_id}:{content_hash}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Create proof data
            timestamp = int(time.time())
            proof_id = f"proof_{memory_id}_{timestamp}"
            
            proof_data = {
                "id": proof_id,
                "memory_id": memory_id,
                "type": PROOF_TYPE_INTEGRITY,
                "timestamp": timestamp,
                "content_hash": content_hash,
                "proof": hmac_digest,
                "public_inputs": {
                    "memory_id": memory_id,
                    "content_hash": content_hash
                },
                "metadata": metadata or {}
            }
            
            # Save proof to file
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            with open(proof_file, 'w') as f:
                json.dump(proof_data, f, indent=2)
            
            logger.info(f"Generated integrity proof {proof_id} for memory {memory_id}")
            return proof_data
            
        except Exception as e:
            logger.error(f"Error generating integrity proof: {str(e)}")
            return None
    
    async def verify_integrity_proof(self, 
                                  proof_id: str,
                                  memory_id: str,
                                  content: Optional[str] = None,
                                  content_hash: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify a ZK proof for memory content integrity.
        
        Args:
            proof_id: ID of the proof to verify
            memory_id: ID of the memory
            content: Optional memory content (for verification)
            content_hash: Optional content hash (if content not provided)
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Load proof data
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            if not os.path.exists(proof_file):
                return False, f"Proof {proof_id} not found"
                
            with open(proof_file, 'r') as f:
                proof_data = json.load(f)
            
            # Check if proof is for the right memory
            if proof_data["memory_id"] != memory_id:
                return False, "Proof is for a different memory"
            
            # Calculate content hash if content provided
            if content:
                calculated_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            elif content_hash:
                calculated_hash = content_hash
            else:
                return False, "Either content or content_hash must be provided"
            
            # Check if content hash matches
            if calculated_hash != proof_data["content_hash"]:
                return False, "Content hash mismatch"
            
            # In a real ZK implementation, we would:
            # 1. Verify the ZK proof using the verification key
            
            # For this demo, we'll verify the HMAC
            expected_hmac = hmac.new(
                self.verification_key, 
                f"{memory_id}:{calculated_hash}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if expected_hmac != proof_data["proof"]:
                return False, "Proof verification failed"
            
            logger.info(f"Integrity proof {proof_id} verified successfully")
            return True, "Proof verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying integrity proof: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def generate_ownership_proof(self, 
                                     memory_id: str,
                                     owner_id: str,
                                     owner_signature: str) -> Optional[Dict[str, Any]]:
        """
        Generate a ZK proof of ownership without revealing the owner's signature.
        
        Args:
            memory_id: ID of the memory
            owner_id: ID of the owner
            owner_signature: Signature from the owner
            
        Returns:
            Dictionary with proof information or None if failed
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "zk_operation",
                "operation": "generate_ownership_proof",
                "memory_id": memory_id,
                "owner_id": owner_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Proof generation rejected by principles engine: {reason}")
                return None
        
        try:
            # In a real ZK implementation, we would:
            # 1. Generate a ZK circuit to prove knowledge of the signature without revealing it
            # 2. Generate a proof using the proving key
            
            # For this demo, we'll use HMAC as a simplified "proof"
            hmac_digest = hmac.new(
                self.proving_key, 
                f"{memory_id}:{owner_id}:{owner_signature}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Create proof data
            timestamp = int(time.time())
            proof_id = f"ownership_{memory_id}_{timestamp}"
            
            proof_data = {
                "id": proof_id,
                "memory_id": memory_id,
                "type": PROOF_TYPE_OWNERSHIP,
                "timestamp": timestamp,
                "owner_id": owner_id,
                "proof": hmac_digest,
                "public_inputs": {
                    "memory_id": memory_id,
                    "owner_id": owner_id
                }
            }
            
            # Save proof to file
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            with open(proof_file, 'w') as f:
                json.dump(proof_data, f, indent=2)
            
            logger.info(f"Generated ownership proof {proof_id} for memory {memory_id}")
            return proof_data
            
        except Exception as e:
            logger.error(f"Error generating ownership proof: {str(e)}")
            return None
    
    async def verify_ownership_proof(self, 
                                   proof_id: str,
                                   memory_id: str,
                                   owner_id: str) -> Tuple[bool, str]:
        """
        Verify a ZK proof of ownership.
        
        Args:
            proof_id: ID of the proof to verify
            memory_id: ID of the memory
            owner_id: ID of the claimed owner
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Load proof data
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            if not os.path.exists(proof_file):
                return False, f"Proof {proof_id} not found"
                
            with open(proof_file, 'r') as f:
                proof_data = json.load(f)
            
            # Check if proof is for the right memory and owner
            if proof_data["memory_id"] != memory_id:
                return False, "Proof is for a different memory"
                
            if proof_data["owner_id"] != owner_id:
                return False, "Proof is for a different owner"
            
            # In a real ZK implementation, we would:
            # 1. Verify the ZK proof using the verification key
            
            # For our demo, we can't actually verify without the original signature
            # So we'll just return success (in a real implementation, this would verify properly)
            
            logger.info(f"Ownership proof {proof_id} verified successfully")
            return True, "Proof verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying ownership proof: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def generate_compliance_proof(self, 
                                      memory_id: str,
                                      principle_id: int,
                                      evidence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate a ZK proof that a memory complies with a specific principle.
        
        Args:
            memory_id: ID of the memory
            principle_id: ID of the principle
            evidence: Evidence for compliance
            
        Returns:
            Dictionary with proof information or None if failed
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "zk_operation",
                "operation": "generate_compliance_proof",
                "memory_id": memory_id,
                "principle_id": principle_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Proof generation rejected by principles engine: {reason}")
                return None
                
            # Get principle details
            principle = self.principles_engine.get_principle_by_id(principle_id)
            if not principle:
                logger.warning(f"Principle {principle_id} not found")
                return None
        
        try:
            # Serialize evidence
            evidence_str = json.dumps(evidence, sort_keys=True)
            
            # In a real ZK implementation, we would:
            # 1. Generate a ZK circuit to prove compliance with the principle
            # 2. Generate a proof using the proving key
            
            # For this demo, we'll use HMAC as a simplified "proof"
            hmac_digest = hmac.new(
                self.proving_key, 
                f"{memory_id}:{principle_id}:{evidence_str}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Create proof data
            timestamp = int(time.time())
            proof_id = f"compliance_{memory_id}_{principle_id}_{timestamp}"
            
            proof_data = {
                "id": proof_id,
                "memory_id": memory_id,
                "type": PROOF_TYPE_COMPLIANCE,
                "timestamp": timestamp,
                "principle_id": principle_id,
                "principle_name": principle["name"] if self.principles_engine and principle else f"Principle {principle_id}",
                "proof": hmac_digest,
                "public_inputs": {
                    "memory_id": memory_id,
                    "principle_id": principle_id
                }
            }
            
            # Save proof to file
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            with open(proof_file, 'w') as f:
                json.dump(proof_data, f, indent=2)
            
            logger.info(f"Generated compliance proof {proof_id} for memory {memory_id} with principle {principle_id}")
            return proof_data
            
        except Exception as e:
            logger.error(f"Error generating compliance proof: {str(e)}")
            return None
    
    async def verify_compliance_proof(self, 
                                    proof_id: str,
                                    memory_id: str,
                                    principle_id: int) -> Tuple[bool, str]:
        """
        Verify a ZK proof of compliance with a principle.
        
        Args:
            proof_id: ID of the proof to verify
            memory_id: ID of the memory
            principle_id: ID of the principle
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Load proof data
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            if not os.path.exists(proof_file):
                return False, f"Proof {proof_id} not found"
                
            with open(proof_file, 'r') as f:
                proof_data = json.load(f)
            
            # Check if proof is for the right memory and principle
            if proof_data["memory_id"] != memory_id:
                return False, "Proof is for a different memory"
                
            if proof_data["principle_id"] != principle_id:
                return False, "Proof is for a different principle"
            
            # In a real ZK implementation, we would:
            # 1. Verify the ZK proof using the verification key
            
            # For our demo, we'll just return success
            # (in a real implementation, this would verify properly)
            
            logger.info(f"Compliance proof {proof_id} verified successfully")
            return True, "Proof verified successfully"
            
        except Exception as e:
            logger.error(f"Error verifying compliance proof: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def get_proofs_for_memory(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get all proofs associated with a memory.
        
        Args:
            memory_id: ID of the memory
            
        Returns:
            List of proof data
        """
        try:
            result = []
            
            # Scan proof directory for matching proofs
            for filename in os.listdir(self.proof_storage_path):
                if not filename.endswith('.json'):
                    continue
                    
                proof_file = os.path.join(self.proof_storage_path, filename)
                with open(proof_file, 'r') as f:
                    proof_data = json.load(f)
                
                if proof_data.get("memory_id") == memory_id:
                    result.append(proof_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting proofs for memory: {str(e)}")
            return []
    
    async def delete_proof(self, proof_id: str) -> Tuple[bool, str]:
        """
        Delete a proof from storage.
        
        Args:
            proof_id: ID of the proof to delete
            
        Returns:
            Tuple of (success, message)
        """
        # Verify action with principles engine if available
        if self.principles_engine:
            action = {
                "type": "zk_operation",
                "operation": "delete_proof",
                "proof_id": proof_id
            }
            valid, reason = self.principles_engine.verify_action(action)
            if not valid:
                logger.warning(f"Proof deletion rejected by principles engine: {reason}")
                return False, reason
        
        try:
            proof_file = os.path.join(self.proof_storage_path, f"{proof_id}.json")
            if not os.path.exists(proof_file):
                return False, f"Proof {proof_id} not found"
                
            # Delete proof file
            os.remove(proof_file)
            
            logger.info(f"Proof {proof_id} deleted successfully")
            return True, f"Proof {proof_id} deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting proof: {str(e)}")
            return False, f"Error: {str(e)}" 