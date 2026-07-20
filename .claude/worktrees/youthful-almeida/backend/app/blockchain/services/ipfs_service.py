"""
IPFS service for distributed document storage and retrieval.
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import aiohttp
import aiofiles
from pathlib import Path
import logging

from ..config import get_blockchain_config
from ..utils.crypto_utils import CryptoUtils

logger = logging.getLogger(__name__)


class IPFSService:
    """Service for interacting with IPFS (InterPlanetary File System)."""
    
    def __init__(self):
        self.config = get_blockchain_config()
        self.api_url = self.config.ipfs_api_url
        self.gateway_url = self.config.ipfs_gateway_url
        self.timeout = self.config.ipfs_timeout
        self.crypto_utils = CryptoUtils()
        
    async def add_file(
        self, 
        file_content: bytes, 
        filename: str = None,
        encrypt: bool = True,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, str]:
        """
        Add a file to IPFS with optional encryption.
        
        Args:
            file_content: The file content as bytes
            filename: Optional filename
            encrypt: Whether to encrypt the content before storing
            metadata: Optional metadata to include
            
        Returns:
            Dictionary with IPFS hash, encryption key (if encrypted), and metadata
        """
        try:
            # Prepare content
            content_to_store = file_content
            encryption_key = None
            
            if encrypt:
                content_to_store, encryption_key = self.crypto_utils.encrypt_data(file_content)
            
            # Create multipart form data
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                content_to_store,
                filename=filename or f'document_{datetime.now().isoformat()}'
            )
            
            # Add to IPFS
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/add", data=form_data) as response:
                    if response.status != 200:
                        raise Exception(f"IPFS add failed: {response.status}")
                    
                    result = await response.json()
                    ipfs_hash = result['Hash']
            
            # Store metadata if provided
            metadata_hash = None
            if metadata:
                metadata['timestamp'] = datetime.now().isoformat()
                metadata['filename'] = filename
                metadata['encrypted'] = encrypt
                metadata['size'] = len(file_content)
                metadata['content_hash'] = hashlib.sha256(file_content).hexdigest()
                
                metadata_hash = await self._store_metadata(metadata)
            
            logger.info(f"File stored in IPFS with hash: {ipfs_hash}")
            
            return {
                'ipfs_hash': ipfs_hash,
                'encryption_key': encryption_key,
                'metadata_hash': metadata_hash,
                'size': len(content_to_store),
                'encrypted': encrypt
            }
            
        except Exception as e:
            logger.error(f"Error adding file to IPFS: {e}")
            raise
    
    async def get_file(
        self, 
        ipfs_hash: str, 
        encryption_key: str = None,
        save_to_path: str = None
    ) -> bytes:
        """
        Retrieve a file from IPFS with optional decryption.
        
        Args:
            ipfs_hash: The IPFS hash of the file
            encryption_key: Optional encryption key for decryption
            save_to_path: Optional path to save the file
            
        Returns:
            The file content as bytes
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(f"{self.gateway_url}/ipfs/{ipfs_hash}") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS get failed: {response.status}")
                    
                    content = await response.read()
            
            # Decrypt if encryption key provided
            if encryption_key:
                content = self.crypto_utils.decrypt_data(content, encryption_key)
            
            # Save to file if path provided
            if save_to_path:
                async with aiofiles.open(save_to_path, 'wb') as f:
                    await f.write(content)
            
            logger.info(f"File retrieved from IPFS: {ipfs_hash}")
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving file from IPFS: {e}")
            raise
    
    async def add_json(
        self, 
        data: Dict[str, Any], 
        encrypt: bool = True
    ) -> Dict[str, str]:
        """
        Add JSON data to IPFS.
        
        Args:
            data: The data to store as JSON
            encrypt: Whether to encrypt the data
            
        Returns:
            Dictionary with IPFS hash and encryption key (if encrypted)
        """
        json_content = json.dumps(data, indent=2, default=str).encode('utf-8')
        return await self.add_file(
            json_content, 
            filename=f"data_{datetime.now().isoformat()}.json",
            encrypt=encrypt,
            metadata={'type': 'json', 'content_type': 'application/json'}
        )
    
    async def get_json(
        self, 
        ipfs_hash: str, 
        encryption_key: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve JSON data from IPFS.
        
        Args:
            ipfs_hash: The IPFS hash of the JSON data
            encryption_key: Optional encryption key for decryption
            
        Returns:
            The JSON data as a dictionary
        """
        content = await self.get_file(ipfs_hash, encryption_key)
        return json.loads(content.decode('utf-8'))
    
    async def pin_file(self, ipfs_hash: str) -> bool:
        """
        Pin a file in IPFS to prevent garbage collection.
        
        Args:
            ipfs_hash: The IPFS hash to pin
            
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/pin/add?arg={ipfs_hash}") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS pin failed: {response.status}")
                    
                    logger.info(f"File pinned in IPFS: {ipfs_hash}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error pinning file in IPFS: {e}")
            return False
    
    async def unpin_file(self, ipfs_hash: str) -> bool:
        """
        Unpin a file in IPFS.
        
        Args:
            ipfs_hash: The IPFS hash to unpin
            
        Returns:
            True if successful
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/pin/rm?arg={ipfs_hash}") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS unpin failed: {response.status}")
                    
                    logger.info(f"File unpinned in IPFS: {ipfs_hash}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error unpinning file in IPFS: {e}")
            return False
    
    async def get_file_stats(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Get statistics for a file in IPFS.
        
        Args:
            ipfs_hash: The IPFS hash to get stats for
            
        Returns:
            Dictionary with file statistics
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/object/stat?arg={ipfs_hash}") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS stat failed: {response.status}")
                    
                    stats = await response.json()
                    return {
                        'hash': ipfs_hash,
                        'size': stats.get('CumulativeSize', 0),
                        'block_size': stats.get('BlockSize', 0),
                        'links': stats.get('NumLinks', 0),
                        'data_size': stats.get('DataSize', 0)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting file stats from IPFS: {e}")
            raise
    
    async def list_pinned_files(self) -> List[str]:
        """
        List all pinned files in IPFS.
        
        Returns:
            List of IPFS hashes that are pinned
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/pin/ls") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS pin list failed: {response.status}")
                    
                    result = await response.json()
                    return list(result.get('Keys', {}).keys())
                    
        except Exception as e:
            logger.error(f"Error listing pinned files in IPFS: {e}")
            return []
    
    async def _store_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Store metadata as a separate IPFS file.
        
        Args:
            metadata: The metadata to store
            
        Returns:
            IPFS hash of the metadata
        """
        result = await self.add_json(metadata, encrypt=False)
        await self.pin_file(result['ipfs_hash'])
        return result['ipfs_hash']
    
    async def verify_file_integrity(
        self, 
        ipfs_hash: str, 
        expected_hash: str
    ) -> bool:
        """
        Verify the integrity of a file in IPFS.
        
        Args:
            ipfs_hash: The IPFS hash of the file
            expected_hash: The expected SHA-256 hash
            
        Returns:
            True if the file integrity is verified
        """
        try:
            content = await self.get_file(ipfs_hash)
            actual_hash = hashlib.sha256(content).hexdigest()
            return actual_hash == expected_hash
            
        except Exception as e:
            logger.error(f"Error verifying file integrity: {e}")
            return False
    
    async def batch_add_files(
        self, 
        files: List[Tuple[bytes, str]], 
        encrypt: bool = True
    ) -> List[Dict[str, str]]:
        """
        Add multiple files to IPFS in batch.
        
        Args:
            files: List of tuples (content, filename)
            encrypt: Whether to encrypt the files
            
        Returns:
            List of results for each file
        """
        tasks = []
        for content, filename in files:
            task = self.add_file(content, filename, encrypt)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    async def get_node_info(self) -> Dict[str, Any]:
        """
        Get information about the IPFS node.
        
        Returns:
            Dictionary with node information
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(f"{self.api_url}/api/v0/id") as response:
                    if response.status != 200:
                        raise Exception(f"IPFS node info failed: {response.status}")
                    
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Error getting IPFS node info: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """
        Check if IPFS is accessible.
        
        Returns:
            True if IPFS is accessible
        """
        try:
            await self.get_node_info()
            return True
        except:
            return False