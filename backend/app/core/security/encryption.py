"""
Encryption Module

Implements field-level encryption for PII and sensitive financial data
with key management and data classification.
"""

import os
import base64
import hashlib
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import redis.asyncio as redis

from app.core.config import settings


class EncryptionType(Enum):
    """Types of encryption"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    RSA_4096 = "rsa_4096"
    FERNET = "fernet"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class DataSensitivity(Enum):
    """Data sensitivity levels for encryption requirements"""
    PUBLIC = 0  # No encryption needed
    INTERNAL = 1  # Optional encryption
    CONFIDENTIAL = 2  # Encryption required
    RESTRICTED = 3  # Strong encryption required
    PII = 4  # Field-level encryption required
    FINANCIAL = 5  # Financial data encryption
    MNPI = 6  # Material Non-Public Information


class KeyManagement:
    """
    Secure key management system
    Implements key rotation, versioning, and secure storage
    """
    
    def __init__(self):
        self.master_key = None
        self.key_cache = {}
        self.redis_client = None
        self.key_rotation_interval = timedelta(days=90)
    
    async def initialize(self):
        """Initialize key management system"""
        
        # Initialize Redis for distributed key storage
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False  # Binary data for keys
        )
        
        # Load or generate master key
        await self.load_master_key()
    
    async def load_master_key(self):
        """Load or generate master encryption key"""
        
        # In production, this would be loaded from HSM or KMS
        master_key_env = os.environ.get("MASTER_ENCRYPTION_KEY")
        
        if master_key_env:
            self.master_key = base64.b64decode(master_key_env)
        else:
            # Generate new master key (only for development)
            self.master_key = os.urandom(32)
            print(f"Generated master key: {base64.b64encode(self.master_key).decode()}")
    
    def generate_data_key(self, key_id: str) -> bytes:
        """Generate a new data encryption key"""
        
        # Generate random key
        data_key = os.urandom(32)
        
        # Encrypt with master key
        encrypted_key = self.encrypt_key(data_key)
        
        # Store encrypted key
        self.store_key(key_id, encrypted_key)
        
        return data_key
    
    def encrypt_key(self, key: bytes) -> bytes:
        """Encrypt a data key with the master key"""
        
        # Use Fernet for key wrapping
        f = Fernet(base64.urlsafe_b64encode(self.master_key))
        return f.encrypt(key)
    
    def decrypt_key(self, encrypted_key: bytes) -> bytes:
        """Decrypt a data key with the master key"""
        
        f = Fernet(base64.urlsafe_b64encode(self.master_key))
        return f.decrypt(encrypted_key)
    
    async def store_key(self, key_id: str, encrypted_key: bytes):
        """Store encrypted key in secure storage"""
        
        key_metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "version": 1,
            "algorithm": "AES-256",
            "rotation_due": (datetime.utcnow() + self.key_rotation_interval).isoformat()
        }
        
        if self.redis_client:
            await self.redis_client.hset(
                f"encryption_key:{key_id}",
                mapping={
                    "key": encrypted_key,
                    "metadata": json.dumps(key_metadata)
                }
            )
        
        # Cache decrypted key
        self.key_cache[key_id] = self.decrypt_key(encrypted_key)
    
    async def get_key(self, key_id: str) -> Optional[bytes]:
        """Retrieve and decrypt a data key"""
        
        # Check cache first
        if key_id in self.key_cache:
            return self.key_cache[key_id]
        
        # Retrieve from storage
        if self.redis_client:
            key_data = await self.redis_client.hget(f"encryption_key:{key_id}", "key")
            
            if key_data:
                decrypted_key = self.decrypt_key(key_data)
                self.key_cache[key_id] = decrypted_key
                return decrypted_key
        
        return None
    
    async def rotate_key(self, key_id: str) -> bytes:
        """Rotate an encryption key"""
        
        # Generate new key
        new_key = self.generate_data_key(f"{key_id}_v{datetime.utcnow().timestamp()}")
        
        # Mark old key for re-encryption
        if self.redis_client:
            await self.redis_client.hset(
                f"encryption_key:{key_id}",
                "status",
                "rotating"
            )
        
        return new_key
    
    async def list_keys_for_rotation(self) -> List[str]:
        """List keys that need rotation"""
        
        keys_to_rotate = []
        
        if self.redis_client:
            # Scan all encryption keys
            cursor = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="encryption_key:*",
                    count=100
                )
                
                for key in keys:
                    metadata = await self.redis_client.hget(key, "metadata")
                    if metadata:
                        meta = json.loads(metadata)
                        rotation_due = datetime.fromisoformat(meta["rotation_due"])
                        
                        if rotation_due <= datetime.utcnow():
                            keys_to_rotate.append(key.replace("encryption_key:", ""))
                
                if cursor == 0:
                    break
        
        return keys_to_rotate


class DataClassifier:
    """
    Classify data sensitivity and determine encryption requirements
    """
    
    # PII field patterns
    PII_PATTERNS = {
        "ssn": r"^\d{3}-?\d{2}-?\d{4}$",
        "credit_card": r"^\d{13,19}$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^\+?1?\d{10,14}$",
        "driver_license": r"^[A-Z0-9]{5,20}$",
        "passport": r"^[A-Z0-9]{6,9}$",
        "bank_account": r"^\d{8,17}$"
    }
    
    # Field name indicators
    SENSITIVE_FIELD_NAMES = {
        "password", "passwd", "secret", "token", "api_key", "private_key",
        "ssn", "social_security", "tax_id", "ein",
        "credit_card", "card_number", "cvv", "cvc",
        "bank_account", "routing_number", "iban", "swift",
        "date_of_birth", "dob", "birthdate",
        "salary", "income", "net_worth", "balance",
        "medical", "health", "diagnosis", "prescription"
    }
    
    @classmethod
    def classify_field(cls, field_name: str, field_value: Any) -> DataSensitivity:
        """Classify a field's sensitivity level"""
        
        field_lower = field_name.lower()
        
        # Check field name
        for sensitive_name in cls.SENSITIVE_FIELD_NAMES:
            if sensitive_name in field_lower:
                if any(pii in field_lower for pii in ["ssn", "credit_card", "bank_account"]):
                    return DataSensitivity.PII
                elif any(fin in field_lower for fin in ["salary", "income", "balance", "net_worth"]):
                    return DataSensitivity.FINANCIAL
                else:
                    return DataSensitivity.RESTRICTED
        
        # Check field value patterns
        if isinstance(field_value, str):
            import re
            for pattern_name, pattern in cls.PII_PATTERNS.items():
                if re.match(pattern, field_value):
                    return DataSensitivity.PII
        
        # Check for financial data
        if isinstance(field_value, (int, float)) and field_value > 1000:
            if any(fin in field_lower for fin in ["amount", "value", "price", "cost"]):
                return DataSensitivity.FINANCIAL
        
        # Default classification
        if "internal" in field_lower:
            return DataSensitivity.INTERNAL
        elif "public" in field_lower:
            return DataSensitivity.PUBLIC
        else:
            return DataSensitivity.CONFIDENTIAL
    
    @classmethod
    def classify_document(cls, document: Dict[str, Any]) -> Dict[str, DataSensitivity]:
        """Classify all fields in a document"""
        
        classifications = {}
        
        for field_name, field_value in document.items():
            classifications[field_name] = cls.classify_field(field_name, field_value)
        
        return classifications
    
    @classmethod
    def get_required_encryption(cls, sensitivity: DataSensitivity) -> Optional[EncryptionType]:
        """Get required encryption type for sensitivity level"""
        
        if sensitivity == DataSensitivity.PUBLIC:
            return None
        elif sensitivity == DataSensitivity.INTERNAL:
            return EncryptionType.FERNET
        elif sensitivity in [DataSensitivity.CONFIDENTIAL, DataSensitivity.RESTRICTED]:
            return EncryptionType.AES_256_GCM
        elif sensitivity in [DataSensitivity.PII, DataSensitivity.FINANCIAL, DataSensitivity.MNPI]:
            return EncryptionType.AES_256_GCM
        
        return EncryptionType.AES_256_GCM


class FieldEncryption:
    """
    Field-level encryption for sensitive data
    """
    
    def __init__(self, key_manager: KeyManagement):
        self.key_manager = key_manager
        self.classifier = DataClassifier()
    
    def encrypt_field_aes_gcm(self, data: bytes, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """Encrypt data using AES-256-GCM"""
        
        # Generate nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return ciphertext, nonce, encryptor.tag
    
    def decrypt_field_aes_gcm(
        self,
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        tag: bytes
    ) -> bytes:
        """Decrypt data using AES-256-GCM"""
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def encrypt_field_fernet(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using Fernet (simplified encryption)"""
        
        # Ensure key is 32 bytes
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.encrypt(data)
    
    def decrypt_field_fernet(self, ciphertext: bytes, key: bytes) -> bytes:
        """Decrypt data using Fernet"""
        
        if len(key) != 32:
            key = hashlib.sha256(key).digest()
        
        f = Fernet(base64.urlsafe_b64encode(key))
        return f.decrypt(ciphertext)
    
    async def encrypt_value(
        self,
        value: Any,
        field_name: str,
        encryption_type: Optional[EncryptionType] = None
    ) -> Dict[str, Any]:
        """Encrypt a single value"""
        
        # Determine encryption requirements
        if not encryption_type:
            sensitivity = self.classifier.classify_field(field_name, value)
            encryption_type = self.classifier.get_required_encryption(sensitivity)
        
        if not encryption_type:
            return {"encrypted": False, "value": value}
        
        # Convert value to bytes
        if isinstance(value, str):
            data = value.encode()
        elif isinstance(value, (int, float)):
            data = str(value).encode()
        else:
            data = json.dumps(value).encode()
        
        # Get or generate encryption key
        key_id = f"field_{field_name}"
        key = await self.key_manager.get_key(key_id)
        
        if not key:
            key = self.key_manager.generate_data_key(key_id)
        
        # Encrypt based on type
        if encryption_type == EncryptionType.AES_256_GCM:
            ciphertext, nonce, tag = self.encrypt_field_aes_gcm(data, key)
            
            return {
                "encrypted": True,
                "algorithm": encryption_type.value,
                "key_id": key_id,
                "ciphertext": base64.b64encode(ciphertext).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "tag": base64.b64encode(tag).decode()
            }
        
        elif encryption_type == EncryptionType.FERNET:
            ciphertext = self.encrypt_field_fernet(data, key)
            
            return {
                "encrypted": True,
                "algorithm": encryption_type.value,
                "key_id": key_id,
                "ciphertext": base64.b64encode(ciphertext).decode()
            }
        
        return {"encrypted": False, "value": value}
    
    async def decrypt_value(self, encrypted_data: Dict[str, Any]) -> Any:
        """Decrypt an encrypted value"""
        
        if not encrypted_data.get("encrypted"):
            return encrypted_data.get("value")
        
        # Get decryption key
        key_id = encrypted_data.get("key_id")
        key = await self.key_manager.get_key(key_id)
        
        if not key:
            raise ValueError(f"Decryption key not found: {key_id}")
        
        algorithm = encrypted_data.get("algorithm")
        
        if algorithm == EncryptionType.AES_256_GCM.value:
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            tag = base64.b64decode(encrypted_data["tag"])
            
            plaintext = self.decrypt_field_aes_gcm(ciphertext, key, nonce, tag)
        
        elif algorithm == EncryptionType.FERNET.value:
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            plaintext = self.decrypt_field_fernet(ciphertext, key)
        
        else:
            raise ValueError(f"Unknown encryption algorithm: {algorithm}")
        
        # Convert back to original type
        try:
            return json.loads(plaintext.decode())
        except:
            return plaintext.decode()
    
    async def encrypt_document(
        self,
        document: Dict[str, Any],
        field_policies: Optional[Dict[str, EncryptionType]] = None
    ) -> Dict[str, Any]:
        """Encrypt sensitive fields in a document"""
        
        encrypted_doc = {}
        
        for field_name, field_value in document.items():
            # Check if field should be encrypted
            if field_policies and field_name in field_policies:
                encryption_type = field_policies[field_name]
            else:
                sensitivity = self.classifier.classify_field(field_name, field_value)
                encryption_type = self.classifier.get_required_encryption(sensitivity)
            
            if encryption_type:
                encrypted_doc[field_name] = await self.encrypt_value(
                    field_value,
                    field_name,
                    encryption_type
                )
            else:
                encrypted_doc[field_name] = field_value
        
        return encrypted_doc
    
    async def decrypt_document(self, encrypted_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt all encrypted fields in a document"""
        
        decrypted_doc = {}
        
        for field_name, field_value in encrypted_doc.items():
            if isinstance(field_value, dict) and field_value.get("encrypted"):
                decrypted_doc[field_name] = await self.decrypt_value(field_value)
            else:
                decrypted_doc[field_name] = field_value
        
        return decrypted_doc


class EncryptionManager:
    """
    Central encryption manager coordinating all encryption operations
    """
    
    def __init__(self):
        self.key_manager = KeyManagement()
        self.field_encryption = None
        self.audit_log = []
    
    async def initialize(self):
        """Initialize encryption system"""
        
        await self.key_manager.initialize()
        self.field_encryption = FieldEncryption(self.key_manager)
    
    async def encrypt_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt all PII fields in data"""
        
        # Identify PII fields
        classifications = DataClassifier.classify_document(data)
        
        # Build encryption policy
        field_policies = {}
        for field_name, sensitivity in classifications.items():
            if sensitivity in [DataSensitivity.PII, DataSensitivity.FINANCIAL]:
                field_policies[field_name] = EncryptionType.AES_256_GCM
        
        # Encrypt document
        encrypted = await self.field_encryption.encrypt_document(data, field_policies)
        
        # Log encryption operation
        self.audit_log.append({
            "operation": "encrypt_pii",
            "timestamp": datetime.utcnow().isoformat(),
            "fields_encrypted": list(field_policies.keys())
        })
        
        return encrypted
    
    async def decrypt_pii(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields in data"""
        
        decrypted = await self.field_encryption.decrypt_document(encrypted_data)
        
        # Log decryption operation
        self.audit_log.append({
            "operation": "decrypt_pii",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return decrypted
    
    async def rotate_encryption_keys(self) -> List[str]:
        """Rotate all encryption keys that are due"""
        
        keys_to_rotate = await self.key_manager.list_keys_for_rotation()
        rotated_keys = []
        
        for key_id in keys_to_rotate:
            new_key = await self.key_manager.rotate_key(key_id)
            rotated_keys.append(key_id)
            
            # TODO: Re-encrypt data with new key
        
        self.audit_log.append({
            "operation": "key_rotation",
            "timestamp": datetime.utcnow().isoformat(),
            "keys_rotated": len(rotated_keys)
        })
        
        return rotated_keys
    
    def generate_encryption_report(self) -> Dict[str, Any]:
        """Generate encryption status report"""
        
        return {
            "encryption_enabled": True,
            "algorithms_supported": [e.value for e in EncryptionType],
            "key_rotation_interval": self.key_manager.key_rotation_interval.days,
            "cached_keys": len(self.key_manager.key_cache),
            "audit_entries": len(self.audit_log),
            "last_key_rotation": None  # Would track actual rotation
        }