"""
Helius.dev API Client for VOT1

This module provides integration with Helius.dev for advanced Solana blockchain capabilities,
including transaction history, NFT data, and RPC services.
"""

import os
import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
import aiohttp

from . import config

# Configure logging
logger = logging.getLogger(__name__)

class HeliusClient:
    """
    Helius.dev API client for Solana blockchain integration
    
    This class provides methods for:
    - Querying transaction history
    - Retrieving NFT metadata
    - Enhanced RPC capabilities
    - DAS (Digital Asset Standard) integration
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        rpc_url: Optional[str] = None,
        network: Optional[str] = None
    ):
        """
        Initialize the Helius.dev API client
        
        Args:
            api_key: Helius API key
            api_url: Helius API base URL
            rpc_url: Helius RPC URL
            network: Solana network to use
        """
        self.api_key = api_key or config.get("helius_api_key") or os.getenv("HELIUS_API_KEY")
        self.api_url = api_url or config.get("helius_api_url", "https://api.helius.xyz/v0")
        self.rpc_url = rpc_url or config.get("helius_rpc_url", "https://rpc.helius.xyz")
        self.network = network or config.get("network", "mainnet-beta")
        self._session = None
        
        if not self.api_key:
            logger.warning("Helius API key not provided. API functionality will be limited.")
        
        logger.info(f"HeliusClient initialized for network: {self.network}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
        return self._session
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get SOL balance for a wallet address
        
        Args:
            address: Wallet address to check
            
        Returns:
            Dict with balance information
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            # Prepare JSON-RPC request
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            async with session.post(
                f"{self.rpc_url}?api-key={self.api_key}",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        balance_lamports = result["result"]["value"]
                        balance_sol = balance_lamports / 1_000_000_000  # Convert lamports to SOL
                        
                        return {
                            "address": address,
                            "balance": {
                                "sol": balance_sol,
                                "lamports": balance_lamports
                            },
                            "network": self.network
                        }
                    else:
                        return {"error": "Invalid response from Helius RPC", "details": result}
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius RPC: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error getting balance from Helius: {str(e)}")
            return {"error": f"Error getting balance: {str(e)}"}
    
    async def get_transaction_history(self, address: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get transaction history for a wallet address
        
        Args:
            address: Wallet address to check
            limit: Maximum number of transactions to return
            
        Returns:
            Dict with transaction information
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            # Using the Helius getSignaturesForAddress endpoint
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [address, {"limit": limit}]
            }
            
            async with session.post(
                f"{self.rpc_url}?api-key={self.api_key}",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if "result" in result:
                        transactions = result["result"]
                        
                        return {
                            "address": address,
                            "transactions": transactions,
                            "count": len(transactions),
                            "network": self.network
                        }
                    else:
                        return {"error": "Invalid response from Helius RPC", "details": result}
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius RPC: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error getting transaction history from Helius: {str(e)}")
            return {"error": f"Error getting transaction history: {str(e)}"}
    
    async def get_nft_metadata(self, mint_address: str) -> Dict[str, Any]:
        """
        Get NFT metadata for a mint address
        
        Args:
            mint_address: NFT mint address
            
        Returns:
            Dict with NFT metadata
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            endpoint = f"{self.api_url}/nfts?api-key={self.api_key}"
            payload = {"mintAccounts": [mint_address]}
            
            async with session.post(
                endpoint,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return {
                            "mint_address": mint_address,
                            "metadata": result[0],
                            "network": self.network
                        }
                    else:
                        return {"error": "NFT not found or invalid response", "details": result}
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius API: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error getting NFT metadata from Helius: {str(e)}")
            return {"error": f"Error getting NFT metadata: {str(e)}"}
    
    async def get_token_balances(self, address: str) -> Dict[str, Any]:
        """
        Get token balances for a wallet address
        
        Args:
            address: Wallet address to check
            
        Returns:
            Dict with token balances
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            # Using the Helius getTokenAccountsByOwner endpoint
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            }
            
            async with session.post(
                f"{self.rpc_url}?api-key={self.api_key}",
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if "result" in result and "value" in result["result"]:
                        token_accounts = result["result"]["value"]
                        tokens = []
                        
                        for account in token_accounts:
                            if "account" in account and "data" in account["account"]:
                                parsed_data = account["account"]["data"]["parsed"]
                                if "info" in parsed_data:
                                    tokens.append({
                                        "mint": parsed_data["info"]["mint"],
                                        "owner": parsed_data["info"]["owner"],
                                        "amount": parsed_data["info"]["tokenAmount"]["amount"],
                                        "decimals": parsed_data["info"]["tokenAmount"]["decimals"],
                                        "uiAmount": parsed_data["info"]["tokenAmount"]["uiAmount"]
                                    })
                        
                        return {
                            "address": address,
                            "tokens": tokens,
                            "count": len(tokens),
                            "network": self.network
                        }
                    else:
                        return {"error": "Invalid response from Helius RPC", "details": result}
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius RPC: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error getting token balances from Helius: {str(e)}")
            return {"error": f"Error getting token balances: {str(e)}"}
    
    async def integrate_with_vot1_memory(self, memory_manager, address: str) -> Dict[str, Any]:
        """
        Integrate blockchain data with VOT1 memory system
        
        This method queries various blockchain data for an address and
        stores it in the VOT1 memory system for autonomous agent use.
        
        Args:
            memory_manager: VOT1 memory manager instance
            address: Wallet address to query
            
        Returns:
            Dict with integration status
        """
        if not memory_manager:
            return {"error": "Memory manager not provided"}
        
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        try:
            # Collect blockchain data
            balance_result = await self.get_balance(address)
            tx_result = await self.get_transaction_history(address, limit=5)
            token_result = await self.get_token_balances(address)
            
            # Create memory entry with all blockchain data
            blockchain_data = {
                "address": address,
                "network": self.network,
                "timestamp": int(time.time()),
                "balance": balance_result.get("balance", {}),
                "recent_transactions": tx_result.get("transactions", []),
                "tokens": token_result.get("tokens", [])
            }
            
            # Store in memory manager
            memory_content = f"Blockchain data for address {address} on {self.network} network"
            memory_metadata = {
                "type": "blockchain_data",
                "source": "helius",
                "address": address,
                "network": self.network,
                "timestamp": int(time.time())
            }
            
            memory_id = memory_manager.add_semantic_memory(
                content=memory_content,
                metadata=memory_metadata
            )
            
            # Store detailed blockchain data as a separate JSON file in the memory directory
            if hasattr(memory_manager, 'semantic_memory_path'):
                blockchain_file = os.path.join(
                    memory_manager.semantic_memory_path,
                    f"blockchain_{address}_{int(time.time())}.json"
                )
                
                with open(blockchain_file, 'w') as f:
                    json.dump(blockchain_data, f, indent=2)
                
                logger.info(f"Blockchain data stored in file: {blockchain_file}")
            
            return {
                "status": "integrated",
                "memory_id": memory_id,
                "blockchain_data": blockchain_data
            }
            
        except Exception as e:
            logger.error(f"Error integrating blockchain data with memory: {str(e)}")
            return {"error": f"Integration error: {str(e)}"}
    
    async def webhook_setup(self, callback_url: str, event_types: List[str]) -> Dict[str, Any]:
        """
        Set up Helius webhook for real-time blockchain events
        
        Args:
            callback_url: URL to receive webhook events
            event_types: List of event types to subscribe to
            
        Returns:
            Dict with webhook setup status
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            # Using the Helius webhook API
            endpoint = f"{self.api_url}/webhooks?api-key={self.api_key}"
            
            payload = {
                "webhookURL": callback_url,
                "transactionTypes": event_types,
                "accountAddresses": [],  # This would be populated with addresses to monitor
                "webhook": {
                    "includeMetadata": True,
                    "includeTokenBalances": True
                }
            }
            
            async with session.post(
                endpoint,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "webhook_created",
                        "webhook_id": result.get("webhookID"),
                        "event_types": event_types,
                        "callback_url": callback_url
                    }
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius API: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error setting up Helius webhook: {str(e)}")
            return {"error": f"Webhook setup error: {str(e)}"}
            
    # Helper method to get enriched transaction data
    async def get_enriched_transaction(self, signature: str) -> Dict[str, Any]:
        """
        Get enriched transaction data for a transaction signature
        
        Args:
            signature: Transaction signature
            
        Returns:
            Dict with enriched transaction data
        """
        if not self.api_key:
            return {"error": "Helius API key not provided"}
        
        session = await self._get_session()
        
        try:
            endpoint = f"{self.api_url}/transactions?api-key={self.api_key}"
            payload = {"transactions": [signature]}
            
            async with session.post(
                endpoint,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return {
                            "signature": signature,
                            "transaction": result[0],
                            "network": self.network
                        }
                    else:
                        return {"error": "Transaction not found or invalid response", "details": result}
                else:
                    text = await response.text()
                    return {"error": f"Error from Helius API: {response.status}", "details": text}
                    
        except Exception as e:
            logger.error(f"Error getting enriched transaction from Helius: {str(e)}")
            return {"error": f"Error getting transaction data: {str(e)}"} 