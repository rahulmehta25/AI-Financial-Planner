"""
Blockchain configuration for audit system.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, validator


class BlockchainConfig(BaseSettings):
    """Configuration for blockchain services."""
    
    # Ethereum Configuration
    ethereum_provider_url: str = "http://localhost:8545"
    ethereum_network_id: int = 1337  # Local development
    ethereum_private_key: Optional[str] = None
    ethereum_account_address: Optional[str] = None
    gas_limit: int = 3000000
    gas_price: int = 20000000000  # 20 gwei
    
    # Smart Contract Addresses
    audit_contract_address: Optional[str] = None
    compliance_contract_address: Optional[str] = None
    
    # IPFS Configuration
    ipfs_api_url: str = "http://localhost:5001"
    ipfs_gateway_url: str = "http://localhost:8080"
    ipfs_timeout: int = 30
    
    # Security Settings
    encryption_algorithm: str = "AES-256-GCM"
    hash_algorithm: str = "SHA-256"
    signature_algorithm: str = "ECDSA"
    
    # Compliance Settings
    retention_period_years: int = 7
    audit_frequency_hours: int = 24
    compliance_standards: list = ["SOX", "GDPR", "PCI-DSS"]
    
    # Performance Settings
    batch_size: int = 100
    retry_attempts: int = 3
    cache_ttl_seconds: int = 3600
    
    class Config:
        env_prefix = "BLOCKCHAIN_"
        case_sensitive = False
        
    @validator('ethereum_private_key')
    def validate_private_key(cls, v):
        if v and not v.startswith('0x'):
            return f'0x{v}'
        return v
    
    @validator('ethereum_account_address')
    def validate_address(cls, v):
        if v and not v.startswith('0x'):
            return f'0x{v}'
        return v


# Global configuration instance
blockchain_config = BlockchainConfig()


def get_blockchain_config() -> BlockchainConfig:
    """Get blockchain configuration instance."""
    return blockchain_config


def update_config(**kwargs) -> None:
    """Update blockchain configuration."""
    global blockchain_config
    for key, value in kwargs.items():
        if hasattr(blockchain_config, key):
            setattr(blockchain_config, key, value)


# Contract ABI configurations
AUDIT_CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "eventId", "type": "string"},
            {"name": "userId", "type": "string"},
            {"name": "action", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "dataHash", "type": "bytes32"},
            {"name": "ipfsHash", "type": "string"}
        ],
        "name": "logAuditEvent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "eventId", "type": "string"}],
        "name": "getAuditEvent",
        "outputs": [
            {"name": "userId", "type": "string"},
            {"name": "action", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "dataHash", "type": "bytes32"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "blockNumber", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "userId", "type": "string"}],
        "name": "getUserAuditEvents",
        "outputs": [{"name": "", "type": "string[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "eventId", "type": "string"},
            {"name": "dataHash", "type": "bytes32"}
        ],
        "name": "verifyEventIntegrity",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

COMPLIANCE_CONTRACT_ABI = [
    {
        "inputs": [
            {"name": "planId", "type": "string"},
            {"name": "userId", "type": "string"},
            {"name": "planHash", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "ipfsHash", "type": "string"}
        ],
        "name": "createProofOfExistence",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "planId", "type": "string"}],
        "name": "getProofOfExistence",
        "outputs": [
            {"name": "userId", "type": "string"},
            {"name": "planHash", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "blockNumber", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "planId", "type": "string"},
            {"name": "planHash", "type": "bytes32"}
        ],
        "name": "verifyPlanIntegrity",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "complianceId", "type": "string"},
            {"name": "standard", "type": "string"},
            {"name": "evidenceHash", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"}
        ],
        "name": "recordComplianceProof",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]