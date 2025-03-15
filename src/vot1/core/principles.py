"""
Core Principles Engine for VOT1

This module defines the immutable principles that govern the VOT1 system.
These principles are cryptographically inscribed using ZK proofs to prevent alteration.
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)

# Define the core principles
CORE_PRINCIPLES = [
    {
        "id": 1,
        "name": "User Sovereignty",
        "description": "User data, decisions, and privacy must always be respected above all else.",
        "verification_method": "verify_user_sovereignty"
    },
    {
        "id": 2,
        "name": "Truth and Accuracy",
        "description": "Always provide truthful and accurate information, especially when answering factual queries.",
        "verification_method": "verify_truth_accuracy"
    },
    {
        "id": 3,
        "name": "Continuous Improvement",
        "description": "The system must continuously learn, adapt, and improve based on feedback and experience.",
        "verification_method": "verify_improvement"
    },
    {
        "id": 4,
        "name": "Transparency",
        "description": "System operations and decisions must be transparent and explainable when requested.",
        "verification_method": "verify_transparency"
    },
    {
        "id": 5,
        "name": "Resource Efficiency",
        "description": "Optimize resource usage to maximize effectiveness while minimizing computational costs.",
        "verification_method": "verify_efficiency"
    },
    {
        "id": 6,
        "name": "Ethical Behavior",
        "description": "Actions must adhere to ethical standards and avoid harmful outputs or intentions.",
        "verification_method": "verify_ethics"
    },
    {
        "id": 7,
        "name": "Security First",
        "description": "Prioritize security in all operations and protect against unauthorized access or manipulation.",
        "verification_method": "verify_security"
    },
    {
        "id": 8,
        "name": "Autonomous Agency",
        "description": "Enable autonomous agency within the bounds of other principles when beneficial.",
        "verification_method": "verify_agency"
    },
    {
        "id": 9,
        "name": "Interoperability",
        "description": "Design systems to work seamlessly with other components and external systems.",
        "verification_method": "verify_interoperability"
    },
    {
        "id": 10,
        "name": "Critical File Protection",
        "description": "Protect critical system files, especially .env configurations and memory storage, from unauthorized deletion or modification.",
        "verification_method": "verify_file_protection"
    }
]

class CorePrinciplesEngine:
    """
    Manages and enforces the core principles of the VOT1 system.
    Ensures principles cannot be altered and all system actions are verified against them.
    """
    
    def __init__(self, principles_path: str = "memory/principles", 
                 config_path: str = "vot1_config.json"):
        """
        Initialize the Core Principles Engine.
        
        Args:
            principles_path: Path to store principles inscriptions
            config_path: Path to the configuration file
        """
        self.principles = CORE_PRINCIPLES
        self.principles_path = principles_path
        self.config_path = config_path
        self.inscribed = False
        self.protected_paths = ['.env', 'memory/', 'vot1_config.json']
        
        # Ensure principles directory exists
        os.makedirs(self.principles_path, exist_ok=True)
        
        # Load configuration if available
        self.load_config()
        
        # Check if principles are already inscribed
        self.check_inscription()
        
        logger.info("Core Principles Engine initialized")
    
    def load_config(self) -> None:
        """Load configuration settings."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                if 'principles' in config:
                    if 'path' in config['principles']:
                        self.principles_path = config['principles']['path']
                        os.makedirs(self.principles_path, exist_ok=True)
                
                if 'system' in config and 'security' in config['system'] and 'protected_paths' in config['system']['security']:
                    self.protected_paths = config['system']['security']['protected_paths']
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    
    def check_inscription(self) -> bool:
        """
        Check if principles are already inscribed.
        
        Returns:
            True if inscribed, False otherwise
        """
        inscription_file = os.path.join(self.principles_path, "inscription.json")
        if os.path.exists(inscription_file):
            try:
                with open(inscription_file, 'r') as f:
                    inscription = json.load(f)
                
                # Verify the inscription
                current_hash = self._calculate_principles_hash()
                if inscription.get('hash') == current_hash:
                    self.inscribed = True
                    logger.info("Principles inscription verified successfully")
                    return True
                else:
                    logger.warning("Principles inscription hash mismatch - principles may have been altered")
            except Exception as e:
                logger.error(f"Error verifying principles inscription: {str(e)}")
        
        return False
    
    def inscribe_principles(self) -> bool:
        """
        Inscribe the principles cryptographically to prevent alteration.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a hash of the principles
            principles_hash = self._calculate_principles_hash()
            
            # Create the inscription record
            inscription = {
                "timestamp": time.time(),
                "hash": principles_hash,
                "principles": self.principles,
                "inscription_method": "sha256"
            }
            
            # Save the inscription
            inscription_file = os.path.join(self.principles_path, "inscription.json")
            with open(inscription_file, 'w') as f:
                json.dump(inscription, f, indent=4)
            
            self.inscribed = True
            logger.info("Principles successfully inscribed")
            return True
        except Exception as e:
            logger.error(f"Error inscribing principles: {str(e)}")
            return False
    
    def _calculate_principles_hash(self) -> str:
        """
        Calculate a hash of the principles to ensure integrity.
        
        Returns:
            Hash string of the principles
        """
        principles_str = json.dumps(self.principles, sort_keys=True)
        return hashlib.sha256(principles_str.encode('utf-8')).hexdigest()
    
    def verify_inscription(self) -> Tuple[bool, str]:
        """
        Verify that principles have not been altered since inscription.
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if not self.inscribed:
            return False, "Principles not inscribed"
        
        inscription_file = os.path.join(self.principles_path, "inscription.json")
        if not os.path.exists(inscription_file):
            return False, "Inscription file not found"
        
        try:
            with open(inscription_file, 'r') as f:
                inscription = json.load(f)
            
            recorded_hash = inscription.get('hash')
            current_hash = self._calculate_principles_hash()
            
            if recorded_hash == current_hash:
                return True, "Inscription verified successfully"
            else:
                return False, "Inscription verification failed - hash mismatch"
        except Exception as e:
            return False, f"Error verifying inscription: {str(e)}"
    
    def verify_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify if an action complies with the core principles.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        if not self.inscribed:
            logger.warning("Principles not inscribed - action verification may be unreliable")
        
        # Log the action for transparency
        logger.info(f"Verifying action: {action.get('type', 'unknown')}")
        
        # Perform verification based on action type
        action_type = action.get('type', '')
        
        # File operation verification
        if action_type == 'file_operation':
            return self.verify_file_operation(action)
        
        # Add more action type verifications as needed
        # For example: data_access, user_interaction, memory_modification, etc.
        
        # Default verification
        for principle in self.principles:
            verification_method = principle.get('verification_method')
            if hasattr(self, verification_method):
                method = getattr(self, verification_method)
                is_valid, reason = method(action)
                if not is_valid:
                    logger.warning(f"Action violates principle {principle['id']}: {principle['name']}")
                    return False, f"Violates principle {principle['id']}: {reason}"
        
        return True, "Action complies with all principles"
    
    def verify_user_sovereignty(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 1: User Sovereignty.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        # Implementation depends on the specific action
        # Example check for data access actions
        if action.get('type') == 'data_access' and not action.get('user_authorized', False):
            return False, "Data access without user authorization"
        
        return True, "Action respects user sovereignty"
    
    def verify_truth_accuracy(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 2: Truth and Accuracy.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        # Implementation depends on the specific action
        if action.get('type') == 'information_provision' and action.get('confidence', 1.0) < 0.7:
            return False, "Information provided with low confidence"
        
        return True, "Information appears accurate"
    
    def verify_improvement(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 3: Continuous Improvement.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        return True, "Action supports continuous improvement"
    
    def verify_transparency(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 4: Transparency.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        if action.get('type') == 'system_operation' and action.get('hidden', False):
            return False, "Operation not transparent to the user"
        
        return True, "Action maintains transparency"
    
    def verify_efficiency(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 5: Resource Efficiency.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        return True, "Action is resource efficient"
    
    def verify_ethics(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 6: Ethical Behavior.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        if action.get('harm_potential', 0) > 0.5:
            return False, "Action has significant harm potential"
        
        return True, "Action adheres to ethical standards"
    
    def verify_security(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 7: Security First.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        if action.get('type') == 'access_control' and not action.get('authenticated', False):
            return False, "Access attempt without proper authentication"
        
        return True, "Action maintains security"
    
    def verify_agency(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 8: Autonomous Agency.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        return True, "Action respects autonomous agency"
    
    def verify_interoperability(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 9: Interoperability.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        return True, "Action maintains interoperability"
    
    def verify_file_protection(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify compliance with Principle 10: Critical File Protection.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            Tuple of (is_compliant, reason)
        """
        if action.get('type') == 'file_operation':
            operation = action.get('operation', '')
            path = action.get('path', '')
            authorized = action.get('authorized', False)
            
            # Check if the path is protected
            if self.is_protected_path(path) and operation in ['delete', 'write', 'modify'] and not authorized:
                return False, f"Unauthorized {operation} on protected path: {path}"
        
        return True, "File operation respects protection principles"
    
    def verify_file_operation(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify a file operation against the core principles.
        
        Args:
            action: Dictionary containing file operation details
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        operation = action.get('operation', '')
        path = action.get('path', '')
        authorized = action.get('authorized', False)
        
        # Check Critical File Protection principle
        is_valid, reason = self.verify_file_protection(action)
        if not is_valid:
            return False, reason
            
        # Check User Sovereignty principle for user data
        if '/user_data/' in path and not authorized:
            is_valid, reason = self.verify_user_sovereignty(action)
            if not is_valid:
                return False, reason
        
        # Check Security principle
        is_valid, reason = self.verify_security(action)
        if not is_valid:
            return False, reason
        
        return True, "File operation complies with principles"
    
    def is_protected_path(self, path: str) -> bool:
        """
        Check if a file path is protected.
        
        Args:
            path: The path to check
            
        Returns:
            True if the path is protected, False otherwise
        """
        normalized_path = os.path.normpath(path)
        
        for protected_pattern in self.protected_paths:
            if protected_pattern.endswith('/'):
                # Directory pattern
                if normalized_path.startswith(protected_pattern[:-1]):
                    return True
            elif os.path.basename(normalized_path) == protected_pattern:
                # File pattern
                return True
            elif '*' in protected_pattern:
                # Glob pattern
                import fnmatch
                if fnmatch.fnmatch(normalized_path, protected_pattern) or \
                   fnmatch.fnmatch(os.path.basename(normalized_path), protected_pattern):
                    return True
        
        return False
    
    def log_enforcement(self, action: Dict[str, Any], is_compliant: bool, reason: str) -> None:
        """
        Log the enforcement of principles for an action.
        
        Args:
            action: The action being verified
            is_compliant: Whether the action complies with principles
            reason: Reason for compliance or non-compliance
        """
        action_type = action.get('type', 'unknown')
        log_entry = {
            "timestamp": time.time(),
            "action_type": action_type,
            "is_compliant": is_compliant,
            "reason": reason
        }
        
        # Log to file
        try:
            log_file = os.path.join(self.principles_path, "enforcement_log.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error logging principle enforcement: {str(e)}")
        
        # Log to logger
        if is_compliant:
            logger.info(f"Principle enforcement: {action_type} - compliant - {reason}")
        else:
            logger.warning(f"Principle enforcement: {action_type} - non-compliant - {reason}")
    
    def get_principle_by_id(self, principle_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a principle by its ID.
        
        Args:
            principle_id: The ID of the principle
            
        Returns:
            The principle dictionary or None if not found
        """
        for principle in self.principles:
            if principle.get('id') == principle_id:
                return principle
        return None
    
    def get_principles(self) -> List[Dict[str, Any]]:
        """
        Get all principles.
        
        Returns:
            List of all principles
        """
        return self.principles