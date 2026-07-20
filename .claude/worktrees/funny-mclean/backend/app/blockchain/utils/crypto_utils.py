"""
Cryptographic utilities for blockchain audit system.
"""

import hashlib
import hmac
import secrets
import base64
from typing import Tuple, Any, Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class CryptoUtils:
    """Cryptographic utilities for secure operations."""
    
    def __init__(self):
        self.backend = default_backend()
    
    def generate_hash(self, data: bytes, algorithm: str = "SHA-256") -> str:
        """
        Generate hash of data using specified algorithm.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (SHA-256, SHA-512, MD5)
            
        Returns:
            Hexadecimal hash string
        """
        try:
            if algorithm.upper() == "SHA-256":
                hash_obj = hashlib.sha256()
            elif algorithm.upper() == "SHA-512":
                hash_obj = hashlib.sha512()
            elif algorithm.upper() == "MD5":
                hash_obj = hashlib.md5()
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            hash_obj.update(data)
            return hash_obj.hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating hash: {e}")
            raise
    
    def generate_merkle_root(self, hashes: list) -> str:
        """
        Generate Merkle root hash from list of hashes.
        
        Args:
            hashes: List of hash strings
            
        Returns:
            Merkle root hash
        """
        if not hashes:
            return ""
        
        if len(hashes) == 1:
            return hashes[0]
        
        # Ensure even number of hashes
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        
        next_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            next_level.append(self.generate_hash(combined.encode()))
        
        return self.generate_merkle_root(next_level)
    
    def verify_merkle_proof(
        self, 
        leaf_hash: str, 
        proof: list, 
        root_hash: str
    ) -> bool:
        """
        Verify Merkle proof for a leaf hash.
        
        Args:
            leaf_hash: Hash of the leaf to verify
            proof: List of proof hashes
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid
        """
        current_hash = leaf_hash
        
        for proof_hash in proof:
            combined = current_hash + proof_hash
            current_hash = self.generate_hash(combined.encode())
        
        return current_hash == root_hash
    
    def generate_hmac(self, data: bytes, key: bytes) -> str:
        """
        Generate HMAC for data integrity verification.
        
        Args:
            data: Data to generate HMAC for
            key: Secret key
            
        Returns:
            HMAC hexadecimal string
        """
        return hmac.new(key, data, hashlib.sha256).hexdigest()
    
    def verify_hmac(self, data: bytes, key: bytes, expected_hmac: str) -> bool:
        """
        Verify HMAC for data integrity.
        
        Args:
            data: Original data
            key: Secret key
            expected_hmac: Expected HMAC value
            
        Returns:
            True if HMAC is valid
        """
        calculated_hmac = self.generate_hmac(data, key)
        return hmac.compare_digest(calculated_hmac, expected_hmac)
    
    def encrypt_data(self, data: bytes, key: bytes = None) -> Tuple[bytes, str]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Data to encrypt
            key: Optional encryption key (generated if not provided)
            
        Returns:
            Tuple of (encrypted_data, base64_key)
        """
        try:
            if key is None:
                key = secrets.token_bytes(32)  # 256-bit key
            
            # Generate random IV
            iv = secrets.token_bytes(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine IV, tag, and ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            
            # Return encrypted data and base64-encoded key
            return encrypted_data, base64.b64encode(key).decode()
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: bytes, key_b64: str) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            encrypted_data: Encrypted data (IV + tag + ciphertext)
            key_b64: Base64-encoded encryption key
            
        Returns:
            Decrypted data
        """
        try:
            key = base64.b64decode(key_b64)
            
            # Extract IV, tag, and ciphertext
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def generate_key_pair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair for asymmetric encryption.
        
        Args:
            key_size: RSA key size in bits
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=self.backend
            )
            
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            return private_pem, public_pem
            
        except Exception as e:
            logger.error(f"Error generating key pair: {e}")
            raise
    
    def rsa_encrypt(self, data: bytes, public_key_pem: bytes) -> bytes:
        """
        Encrypt data using RSA public key.
        
        Args:
            data: Data to encrypt
            public_key_pem: Public key in PEM format
            
        Returns:
            Encrypted data
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self.backend
            )
            
            encrypted_data = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error with RSA encryption: {e}")
            raise
    
    def rsa_decrypt(self, encrypted_data: bytes, private_key_pem: bytes) -> bytes:
        """
        Decrypt data using RSA private key.
        
        Args:
            encrypted_data: Encrypted data
            private_key_pem: Private key in PEM format
            
        Returns:
            Decrypted data
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=self.backend
            )
            
            decrypted_data = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error with RSA decryption: {e}")
            raise
    
    def sign_data(self, data: bytes, private_key_pem: bytes) -> bytes:
        """
        Sign data using RSA private key.
        
        Args:
            data: Data to sign
            private_key_pem: Private key in PEM format
            
        Returns:
            Digital signature
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
                backend=self.backend
            )
            
            signature = private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return signature
            
        except Exception as e:
            logger.error(f"Error signing data: {e}")
            raise
    
    def verify_signature(
        self, 
        data: bytes, 
        signature: bytes, 
        public_key_pem: bytes
    ) -> bool:
        """
        Verify digital signature using RSA public key.
        
        Args:
            data: Original data
            signature: Digital signature
            public_key_pem: Public key in PEM format
            
        Returns:
            True if signature is valid
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=self.backend
            )
            
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception:
            return False
    
    def derive_key(
        self, 
        password: str, 
        salt: bytes = None, 
        iterations: int = 100000
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password string
            salt: Optional salt (generated if not provided)
            iterations: Number of PBKDF2 iterations
            
        Returns:
            Tuple of (derived_key, salt)
        """
        try:
            if salt is None:
                salt = secrets.token_bytes(32)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=iterations,
                backend=self.backend
            )
            
            key = kdf.derive(password.encode())
            return key, salt
            
        except Exception as e:
            logger.error(f"Error deriving key: {e}")
            raise
    
    def generate_secure_random(self, length: int) -> bytes:
        """
        Generate cryptographically secure random bytes.
        
        Args:
            length: Number of bytes to generate
            
        Returns:
            Random bytes
        """
        return secrets.token_bytes(length)
    
    def constant_time_compare(self, a: str, b: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks.
        
        Args:
            a: First string
            b: Second string
            
        Returns:
            True if strings are equal
        """
        return hmac.compare_digest(a, b)
    
    def generate_checksum(self, data: bytes) -> str:
        """
        Generate checksum for data integrity verification.
        
        Args:
            data: Data to generate checksum for
            
        Returns:
            Checksum string
        """
        return self.generate_hash(data, "SHA-256")[:16]  # First 16 chars
    
    def verify_checksum(self, data: bytes, expected_checksum: str) -> bool:
        """
        Verify data checksum.
        
        Args:
            data: Original data
            expected_checksum: Expected checksum
            
        Returns:
            True if checksum is valid
        """
        calculated_checksum = self.generate_checksum(data)
        return self.constant_time_compare(calculated_checksum, expected_checksum)