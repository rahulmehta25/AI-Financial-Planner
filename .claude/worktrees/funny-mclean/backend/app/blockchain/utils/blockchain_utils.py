"""
Blockchain utilities for Ethereum interaction.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from web3 import Web3, AsyncWeb3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import logging

from ..config import get_blockchain_config, AUDIT_CONTRACT_ABI, COMPLIANCE_CONTRACT_ABI

logger = logging.getLogger(__name__)


class BlockchainUtils:
    """Utilities for blockchain interactions."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.w3 = None
        self.account = None
        self._initialize_web3()
        
    def _initialize_web3(self):
        """Initialize Web3 connection."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.config.ethereum_provider_url))
            
            # Add POA middleware for development networks
            if self.config.ethereum_network_id == 1337:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Initialize account if private key provided
            if self.config.ethereum_private_key:
                self.account = Account.from_key(self.config.ethereum_private_key)
                self.w3.eth.default_account = self.account.address
            
            logger.info(f"Connected to Ethereum network: {self.config.ethereum_network_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            raise
    
    def is_connected(self) -> bool:
        """Check if connected to Ethereum network."""
        try:
            return self.w3.isConnected()
        except:
            return False
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get information about the connected network."""
        try:
            chain_id = self.w3.eth.chain_id
            block_number = self.w3.eth.block_number
            gas_price = self.w3.eth.gas_price
            
            return {
                'chain_id': chain_id,
                'block_number': block_number,
                'gas_price': gas_price,
                'is_connected': self.is_connected(),
                'account_address': self.account.address if self.account else None
            }
            
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {}
    
    def get_contract(self, address: str, abi: List[Dict]) -> Any:
        """Get contract instance."""
        try:
            return self.w3.eth.contract(
                address=Web3.toChecksumAddress(address),
                abi=abi
            )
        except Exception as e:
            logger.error(f"Error getting contract: {e}")
            raise
    
    def get_audit_contract(self) -> Any:
        """Get audit contract instance."""
        if not self.config.audit_contract_address:
            raise ValueError("Audit contract address not configured")
        
        return self.get_contract(
            self.config.audit_contract_address,
            AUDIT_CONTRACT_ABI
        )
    
    def get_compliance_contract(self) -> Any:
        """Get compliance contract instance."""
        if not self.config.compliance_contract_address:
            raise ValueError("Compliance contract address not configured")
        
        return self.get_contract(
            self.config.compliance_contract_address,
            COMPLIANCE_CONTRACT_ABI
        )
    
    def send_transaction(
        self,
        contract_function: Any,
        value: int = 0,
        gas_limit: int = None
    ) -> str:
        """Send a transaction to the blockchain."""
        try:
            if not self.account:
                raise ValueError("No account configured for transactions")
            
            # Build transaction
            transaction = contract_function.buildTransaction({
                'from': self.account.address,
                'value': value,
                'gas': gas_limit or self.config.gas_limit,
                'gasPrice': self.config.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.config.ethereum_private_key
            )
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise
    
    def wait_for_transaction_receipt(
        self,
        tx_hash: str,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Wait for transaction receipt."""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=timeout
            )
            
            return {
                'transaction_hash': receipt.transactionHash.hex(),
                'block_number': receipt.blockNumber,
                'gas_used': receipt.gasUsed,
                'status': receipt.status,
                'logs': [dict(log) for log in receipt.logs]
            }
            
        except Exception as e:
            logger.error(f"Error waiting for transaction receipt: {e}")
            raise
    
    def call_contract_function(
        self,
        contract_function: Any,
        block_identifier: str = 'latest'
    ) -> Any:
        """Call a contract function (read-only)."""
        try:
            return contract_function.call(block_identifier=block_identifier)
        except Exception as e:
            logger.error(f"Error calling contract function: {e}")
            raise
    
    def get_event_logs(
        self,
        contract: Any,
        event_name: str,
        from_block: int = 0,
        to_block: str = 'latest',
        argument_filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Get event logs from contract."""
        try:
            event_filter = getattr(contract.events, event_name).createFilter(
                fromBlock=from_block,
                toBlock=to_block,
                argument_filters=argument_filters or {}
            )
            
            logs = event_filter.get_all_entries()
            
            return [
                {
                    'event': event_name,
                    'transaction_hash': log.transactionHash.hex(),
                    'block_number': log.blockNumber,
                    'args': dict(log.args),
                    'address': log.address
                }
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error getting event logs: {e}")
            return []
    
    def estimate_gas(self, contract_function: Any) -> int:
        """Estimate gas for a contract function call."""
        try:
            return contract_function.estimateGas({
                'from': self.account.address if self.account else None
            })
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return self.config.gas_limit
    
    def get_balance(self, address: str = None) -> int:
        """Get ETH balance for an address."""
        try:
            addr = address or (self.account.address if self.account else None)
            if not addr:
                raise ValueError("No address provided")
            
            return self.w3.eth.get_balance(Web3.toChecksumAddress(addr))
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    def wei_to_ether(self, wei_amount: int) -> float:
        """Convert Wei to Ether."""
        return Web3.fromWei(wei_amount, 'ether')
    
    def ether_to_wei(self, ether_amount: float) -> int:
        """Convert Ether to Wei."""
        return Web3.toWei(ether_amount, 'ether')
    
    def generate_account(self) -> Tuple[str, str]:
        """Generate a new Ethereum account."""
        try:
            account = Account.create()
            return account.address, account.privateKey.hex()
        except Exception as e:
            logger.error(f"Error generating account: {e}")
            raise
    
    def validate_address(self, address: str) -> bool:
        """Validate an Ethereum address."""
        try:
            return Web3.isAddress(address)
        except:
            return False
    
    def get_transaction_by_hash(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details by hash."""
        try:
            transaction = self.w3.eth.get_transaction(tx_hash)
            return {
                'hash': transaction.hash.hex(),
                'block_number': transaction.blockNumber,
                'from': transaction['from'],
                'to': transaction.to,
                'value': transaction.value,
                'gas': transaction.gas,
                'gas_price': transaction.gasPrice,
                'nonce': transaction.nonce
            }
        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return {}
    
    def get_block_info(self, block_identifier: int = 'latest') -> Dict[str, Any]:
        """Get block information."""
        try:
            block = self.w3.eth.get_block(block_identifier)
            return {
                'number': block.number,
                'hash': block.hash.hex(),
                'timestamp': block.timestamp,
                'transactions': len(block.transactions),
                'gas_used': block.gasUsed,
                'gas_limit': block.gasLimit,
                'miner': block.miner
            }
        except Exception as e:
            logger.error(f"Error getting block info: {e}")
            return {}
    
    def batch_call(self, calls: List[Tuple[Any, str]]) -> List[Any]:
        """Execute multiple contract calls in batch."""
        results = []
        for contract_function, description in calls:
            try:
                result = self.call_contract_function(contract_function)
                results.append({
                    'description': description,
                    'result': result,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'description': description,
                    'error': str(e),
                    'success': False
                })
        return results
    
    def deploy_contract(
        self,
        abi: List[Dict],
        bytecode: str,
        constructor_args: List[Any] = None
    ) -> Tuple[str, str]:
        """Deploy a new contract."""
        try:
            if not self.account:
                raise ValueError("No account configured for deployment")
            
            contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Build deployment transaction
            constructor = contract.constructor(*(constructor_args or []))
            transaction = constructor.buildTransaction({
                'from': self.account.address,
                'gas': self.config.gas_limit,
                'gasPrice': self.config.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address)
            })
            
            # Sign and send deployment transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction,
                private_key=self.config.ethereum_private_key
            )
            
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for deployment
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Contract deployed at: {receipt.contractAddress}")
            return receipt.contractAddress, tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error deploying contract: {e}")
            raise