"""
Setup script for blockchain audit system.
"""

import asyncio
import json
from typing import Dict, Any
import logging

from .utils.blockchain_utils import BlockchainUtils
from .services.ipfs_service import IPFSService
from .config import get_blockchain_config, update_config

logger = logging.getLogger(__name__)


class BlockchainSetup:
    """Setup and initialization for blockchain audit system."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.blockchain_utils = None
        self.ipfs_service = None
        
    async def initialize_system(self) -> Dict[str, Any]:
        """
        Initialize the complete blockchain audit system.
        
        Returns:
            Dictionary with initialization results
        """
        results = {
            "blockchain": {"status": "pending", "details": {}},
            "ipfs": {"status": "pending", "details": {}},
            "contracts": {"status": "pending", "details": {}},
            "overall_status": "pending"
        }
        
        try:
            # Initialize blockchain connection
            logger.info("Initializing blockchain connection...")
            blockchain_result = await self._initialize_blockchain()
            results["blockchain"] = blockchain_result
            
            # Initialize IPFS
            logger.info("Initializing IPFS connection...")
            ipfs_result = await self._initialize_ipfs()
            results["ipfs"] = ipfs_result
            
            # Deploy or verify contracts
            if blockchain_result["status"] == "success":
                logger.info("Setting up smart contracts...")
                contracts_result = await self._setup_contracts()
                results["contracts"] = contracts_result
            
            # Determine overall status
            all_success = all(
                result["status"] == "success" 
                for result in [blockchain_result, ipfs_result, results["contracts"]]
            )
            results["overall_status"] = "success" if all_success else "partial"
            
            logger.info(f"Blockchain audit system initialization: {results['overall_status']}")
            return results
            
        except Exception as e:
            logger.error(f"Error initializing blockchain system: {e}")
            results["overall_status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _initialize_blockchain(self) -> Dict[str, Any]:
        """Initialize blockchain connection."""
        try:
            self.blockchain_utils = BlockchainUtils()
            
            if not self.blockchain_utils.is_connected():
                return {
                    "status": "failed",
                    "error": "Unable to connect to Ethereum network",
                    "details": {}
                }
            
            network_info = self.blockchain_utils.get_network_info()
            
            # Check account balance if account is configured
            balance = 0
            if self.blockchain_utils.account:
                balance = self.blockchain_utils.get_balance()
                balance_eth = self.blockchain_utils.wei_to_ether(balance)
                
                if balance_eth < 0.1:  # Minimum ETH for transactions
                    logger.warning(f"Low account balance: {balance_eth} ETH")
            
            return {
                "status": "success",
                "details": {
                    "network_info": network_info,
                    "account_balance_wei": balance,
                    "account_balance_eth": self.blockchain_utils.wei_to_ether(balance) if balance else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Blockchain initialization failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
    
    async def _initialize_ipfs(self) -> Dict[str, Any]:
        """Initialize IPFS connection."""
        try:
            self.ipfs_service = IPFSService()
            
            is_connected = await self.ipfs_service.check_connection()
            
            if not is_connected:
                return {
                    "status": "failed",
                    "error": "Unable to connect to IPFS",
                    "details": {}
                }
            
            node_info = await self.ipfs_service.get_node_info()
            
            return {
                "status": "success",
                "details": {
                    "node_info": node_info,
                    "api_url": self.ipfs_service.api_url,
                    "gateway_url": self.ipfs_service.gateway_url
                }
            }
            
        except Exception as e:
            logger.error(f"IPFS initialization failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
    
    async def _setup_contracts(self) -> Dict[str, Any]:
        """Setup smart contracts."""
        try:
            results = {"audit_contract": {}, "compliance_contract": {}}
            
            # Check if contracts are already deployed
            if self.config.audit_contract_address:
                try:
                    contract = self.blockchain_utils.get_audit_contract()
                    # Test contract by calling a read function
                    total_events = self.blockchain_utils.call_contract_function(
                        contract.functions.getTotalEventCount()
                    )
                    results["audit_contract"] = {
                        "status": "existing",
                        "address": self.config.audit_contract_address,
                        "total_events": total_events
                    }
                except Exception as e:
                    logger.warning(f"Existing audit contract not accessible: {e}")
                    results["audit_contract"] = {"status": "needs_deployment"}
            else:
                results["audit_contract"] = {"status": "needs_deployment"}
            
            if self.config.compliance_contract_address:
                try:
                    contract = self.blockchain_utils.get_compliance_contract()
                    # Test contract by calling a read function
                    total_proofs = self.blockchain_utils.call_contract_function(
                        contract.functions.getTotalProofCount()
                    )
                    results["compliance_contract"] = {
                        "status": "existing",
                        "address": self.config.compliance_contract_address,
                        "total_proofs": total_proofs
                    }
                except Exception as e:
                    logger.warning(f"Existing compliance contract not accessible: {e}")
                    results["compliance_contract"] = {"status": "needs_deployment"}
            else:
                results["compliance_contract"] = {"status": "needs_deployment"}
            
            # Deploy contracts if needed
            if results["audit_contract"]["status"] == "needs_deployment":
                logger.info("Audit contract needs deployment - skipping for now")
                results["audit_contract"]["status"] = "deployment_required"
            
            if results["compliance_contract"]["status"] == "needs_deployment":
                logger.info("Compliance contract needs deployment - skipping for now")
                results["compliance_contract"]["status"] = "deployment_required"
            
            return {
                "status": "success",
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Contract setup failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
    
    async def deploy_contracts(self) -> Dict[str, Any]:
        """
        Deploy smart contracts to the blockchain.
        Note: This requires compiled contract bytecode.
        """
        try:
            if not self.blockchain_utils:
                raise Exception("Blockchain not initialized")
            
            # This would require actual contract compilation and bytecode
            # For now, return a placeholder response
            return {
                "status": "not_implemented",
                "message": "Contract deployment requires compiled bytecode",
                "instructions": [
                    "1. Compile contracts using Hardhat or Truffle",
                    "2. Deploy contracts to your Ethereum network", 
                    "3. Update configuration with contract addresses"
                ]
            }
            
        except Exception as e:
            logger.error(f"Contract deployment failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def verify_system_health(self) -> Dict[str, Any]:
        """Verify the health of all system components."""
        try:
            health_check = {
                "timestamp": "2024-01-01T10:00:00Z",  # Use actual timestamp
                "components": {},
                "overall_health": "healthy"
            }
            
            # Check blockchain
            if self.blockchain_utils:
                blockchain_connected = self.blockchain_utils.is_connected()
                health_check["components"]["blockchain"] = {
                    "status": "healthy" if blockchain_connected else "unhealthy",
                    "connected": blockchain_connected
                }
                if blockchain_connected:
                    network_info = self.blockchain_utils.get_network_info()
                    health_check["components"]["blockchain"]["network_info"] = network_info
            else:
                health_check["components"]["blockchain"] = {"status": "not_initialized"}
            
            # Check IPFS
            if self.ipfs_service:
                ipfs_connected = await self.ipfs_service.check_connection()
                health_check["components"]["ipfs"] = {
                    "status": "healthy" if ipfs_connected else "unhealthy",
                    "connected": ipfs_connected
                }
            else:
                health_check["components"]["ipfs"] = {"status": "not_initialized"}
            
            # Determine overall health
            unhealthy_components = [
                name for name, info in health_check["components"].items()
                if info["status"] != "healthy"
            ]
            
            if unhealthy_components:
                health_check["overall_health"] = "degraded"
                health_check["issues"] = unhealthy_components
            
            return health_check
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": "2024-01-01T10:00:00Z",
                "overall_health": "unhealthy",
                "error": str(e)
            }
    
    def generate_config_template(self) -> str:
        """Generate configuration template."""
        template = """
        # Blockchain Audit System Configuration Template
        
        # Ethereum Configuration
        BLOCKCHAIN_ETHEREUM_PROVIDER_URL=http://localhost:8545
        BLOCKCHAIN_ETHEREUM_NETWORK_ID=1337
        BLOCKCHAIN_ETHEREUM_PRIVATE_KEY=0x...
        BLOCKCHAIN_ETHEREUM_ACCOUNT_ADDRESS=0x...
        BLOCKCHAIN_GAS_LIMIT=3000000
        BLOCKCHAIN_GAS_PRICE=20000000000
        
        # Smart Contract Addresses (set after deployment)
        BLOCKCHAIN_AUDIT_CONTRACT_ADDRESS=0x...
        BLOCKCHAIN_COMPLIANCE_CONTRACT_ADDRESS=0x...
        
        # IPFS Configuration
        BLOCKCHAIN_IPFS_API_URL=http://localhost:5001
        BLOCKCHAIN_IPFS_GATEWAY_URL=http://localhost:8080
        BLOCKCHAIN_IPFS_TIMEOUT=30
        
        # Security Settings
        BLOCKCHAIN_ENCRYPTION_ALGORITHM=AES-256-GCM
        BLOCKCHAIN_HASH_ALGORITHM=SHA-256
        BLOCKCHAIN_SIGNATURE_ALGORITHM=ECDSA
        
        # Compliance Settings
        BLOCKCHAIN_RETENTION_PERIOD_YEARS=7
        BLOCKCHAIN_AUDIT_FREQUENCY_HOURS=24
        
        # Performance Settings
        BLOCKCHAIN_BATCH_SIZE=100
        BLOCKCHAIN_RETRY_ATTEMPTS=3
        BLOCKCHAIN_CACHE_TTL_SECONDS=3600
        """
        
        return template


async def main():
    """Main setup function."""
    setup = BlockchainSetup()
    
    print("🔗 Initializing Blockchain Audit System...")
    results = await setup.initialize_system()
    
    print(f"\n📊 Initialization Results:")
    print(f"Overall Status: {results['overall_status']}")
    print(f"Blockchain: {results['blockchain']['status']}")
    print(f"IPFS: {results['ipfs']['status']}")
    print(f"Contracts: {results['contracts']['status']}")
    
    if results['overall_status'] != 'success':
        print(f"\n⚠️  Issues found:")
        for component, info in results.items():
            if isinstance(info, dict) and info.get('status') != 'success':
                print(f"  - {component}: {info.get('error', 'Unknown error')}")
    
    print(f"\n🔍 System Health Check:")
    health = await setup.verify_system_health()
    print(f"Overall Health: {health['overall_health']}")
    
    if health['overall_health'] != 'healthy':
        print(f"Issues: {health.get('issues', [])}")


if __name__ == "__main__":
    asyncio.run(main())