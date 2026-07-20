"""
Encryption Configuration for Data at Rest and in Transit

Implements field-level encryption, key management, and rotation.
"""

import os
import base64
import hashlib
import secrets
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import boto3


class EncryptionManager:
    """Comprehensive encryption management system"""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize encryption manager with master key"""
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = os.environ.get('MASTER_ENCRYPTION_KEY', '').encode()
        
        if not self.master_key:
            raise ValueError("Master encryption key not provided")
        
        # Derive encryption key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'stable_salt',  # In production, use a proper salt management
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        self.fernet = Fernet(key)
        
        # Initialize key rotation manager
        self.key_rotation_manager = KeyRotationManager()
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt a single field"""
        if not data:
            return data
        
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt a single field"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")
    
    def encrypt_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PII fields in a dictionary"""
        pii_fields = [
            'ssn', 'social_security_number', 'tax_id', 'driver_license',
            'passport_number', 'bank_account', 'credit_card', 'routing_number',
            'date_of_birth', 'dob', 'email', 'phone', 'address'
        ]
        
        encrypted_data = data.copy()
        
        for key, value in data.items():
            if any(pii_field in key.lower() for pii_field in pii_fields):
                if isinstance(value, str):
                    encrypted_data[key] = self.encrypt_field(value)
                elif isinstance(value, dict):
                    encrypted_data[key] = self.encrypt_pii(value)
        
        return encrypted_data
    
    def generate_data_key(self) -> Tuple[bytes, bytes]:
        """Generate a data encryption key"""
        data_key = Fernet.generate_key()
        encrypted_data_key = self.fernet.encrypt(data_key)
        return data_key, encrypted_data_key
    
    def envelope_encrypt(self, data: bytes) -> Dict[str, bytes]:
        """Encrypt data using envelope encryption"""
        # Generate data key
        data_key, encrypted_data_key = self.generate_data_key()
        
        # Encrypt data with data key
        f = Fernet(data_key)
        encrypted_data = f.encrypt(data)
        
        return {
            'encrypted_data': encrypted_data,
            'encrypted_data_key': encrypted_data_key
        }
    
    def envelope_decrypt(self, encrypted_payload: Dict[str, bytes]) -> bytes:
        """Decrypt data using envelope encryption"""
        # Decrypt data key
        data_key = self.fernet.decrypt(encrypted_payload['encrypted_data_key'])
        
        # Decrypt data with data key
        f = Fernet(data_key)
        return f.decrypt(encrypted_payload['encrypted_data'])


class KeyRotationManager:
    """Automated key rotation management"""
    
    def __init__(self):
        self.rotation_schedule = timedelta(days=90)  # Rotate every 90 days
        self.key_versions = {}
    
    def should_rotate(self, key_id: str, last_rotation: datetime) -> bool:
        """Check if key should be rotated"""
        return datetime.utcnow() - last_rotation > self.rotation_schedule
    
    def rotate_key(self, old_key: bytes) -> bytes:
        """Rotate encryption key"""
        # Generate new key
        new_key = Fernet.generate_key()
        
        # Store key version mapping
        key_version_id = secrets.token_hex(16)
        self.key_versions[key_version_id] = {
            'old_key': old_key,
            'new_key': new_key,
            'rotation_date': datetime.utcnow()
        }
        
        return new_key
    
    def re_encrypt_with_new_key(self, encrypted_data: bytes, old_key: bytes, new_key: bytes) -> bytes:
        """Re-encrypt data with new key"""
        # Decrypt with old key
        old_fernet = Fernet(old_key)
        decrypted = old_fernet.decrypt(encrypted_data)
        
        # Encrypt with new key
        new_fernet = Fernet(new_key)
        return new_fernet.encrypt(decrypted)


class HashiCorpVaultIntegration:
    """Integration with HashiCorp Vault for secret management"""
    
    def __init__(self, vault_url: str, vault_token: str, namespace: str = "financial-planner"):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.namespace = namespace
        
        # Initialize Vault client (using hvac library in production)
        # import hvac
        # self.client = hvac.Client(url=vault_url, token=vault_token, namespace=namespace)
    
    def store_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """Store secret in Vault"""
        # Implementation would use hvac client
        # self.client.secrets.kv.v2.create_or_update_secret(
        #     path=path,
        #     secret=secret
        # )
        return True
    
    def retrieve_secret(self, path: str) -> Dict[str, Any]:
        """Retrieve secret from Vault"""
        # Implementation would use hvac client
        # response = self.client.secrets.kv.v2.read_secret_version(path=path)
        # return response['data']['data']
        return {}
    
    def rotate_database_credentials(self, database_name: str) -> Dict[str, str]:
        """Rotate database credentials using Vault"""
        # Implementation would use Vault database secrets engine
        # self.client.secrets.database.rotate_root_credentials(name=database_name)
        # return self.client.secrets.database.generate_credentials(name=database_name)
        return {}
    
    def get_encryption_key(self, key_name: str) -> bytes:
        """Get encryption key from Vault transit engine"""
        # Implementation would use Vault transit engine
        # response = self.client.secrets.transit.read_key(name=key_name)
        # return response['data']['keys']['1']
        return b''
    
    def encrypt_with_vault(self, key_name: str, plaintext: str) -> str:
        """Encrypt data using Vault transit engine"""
        # Implementation would use Vault transit engine
        # response = self.client.secrets.transit.encrypt_data(
        #     name=key_name,
        #     plaintext=base64.b64encode(plaintext.encode()).decode()
        # )
        # return response['data']['ciphertext']
        return ""


class AWSKMSIntegration:
    """AWS KMS integration for key management"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.kms_client = boto3.client('kms', region_name=region)
        self.key_alias = 'alias/financial-planner-master'
    
    def create_master_key(self) -> str:
        """Create a new KMS master key"""
        response = self.kms_client.create_key(
            Description='Financial Planner Master Encryption Key',
            KeyUsage='ENCRYPT_DECRYPT',
            Origin='AWS_KMS',
            MultiRegion=True,
            Tags=[
                {'TagKey': 'Application', 'TagValue': 'FinancialPlanner'},
                {'TagKey': 'Environment', 'TagValue': 'Production'},
                {'TagKey': 'Compliance', 'TagValue': 'PCI-DSS,GDPR'}
            ]
        )
        
        key_id = response['KeyMetadata']['KeyId']
        
        # Create alias
        self.kms_client.create_alias(
            AliasName=self.key_alias,
            TargetKeyId=key_id
        )
        
        return key_id
    
    def encrypt_data(self, plaintext: bytes) -> Dict[str, Any]:
        """Encrypt data using KMS"""
        response = self.kms_client.encrypt(
            KeyId=self.key_alias,
            Plaintext=plaintext,
            EncryptionContext={
                'Application': 'FinancialPlanner',
                'Purpose': 'DataEncryption'
            }
        )
        
        return {
            'ciphertext': base64.b64encode(response['CiphertextBlob']).decode(),
            'key_id': response['KeyId']
        }
    
    def decrypt_data(self, ciphertext: str) -> bytes:
        """Decrypt data using KMS"""
        response = self.kms_client.decrypt(
            CiphertextBlob=base64.b64decode(ciphertext),
            EncryptionContext={
                'Application': 'FinancialPlanner',
                'Purpose': 'DataEncryption'
            }
        )
        
        return response['Plaintext']
    
    def generate_data_key(self) -> Dict[str, Any]:
        """Generate a data encryption key"""
        response = self.kms_client.generate_data_key(
            KeyId=self.key_alias,
            KeySpec='AES_256',
            EncryptionContext={
                'Application': 'FinancialPlanner',
                'Purpose': 'DataKeyGeneration'
            }
        )
        
        return {
            'plaintext_key': response['Plaintext'],
            'ciphertext_key': base64.b64encode(response['CiphertextBlob']).decode()
        }
    
    def rotate_key(self) -> None:
        """Enable automatic key rotation"""
        self.kms_client.enable_key_rotation(KeyId=self.key_alias)
    
    def create_grant(self, principal_arn: str, operations: list) -> str:
        """Create a grant for specific operations"""
        response = self.kms_client.create_grant(
            KeyId=self.key_alias,
            GranteePrincipal=principal_arn,
            Operations=operations,
            Constraints={
                'EncryptionContextSubset': {
                    'Application': 'FinancialPlanner'
                }
            }
        )
        
        return response['GrantId']


class DatabaseEncryption:
    """Database-level encryption configuration"""
    
    @staticmethod
    def get_postgres_tde_config() -> str:
        """PostgreSQL Transparent Data Encryption configuration"""
        return """
-- Enable TDE for PostgreSQL (using pgcrypto extension)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encrypted tablespace
CREATE TABLESPACE encrypted_ts
  LOCATION '/var/lib/postgresql/encrypted'
  WITH (encryption_key_id = 'financial-planner-key');

-- Create tables with encrypted columns
CREATE TABLE users_encrypted (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    ssn_encrypted BYTEA,  -- Encrypted SSN
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) TABLESPACE encrypted_ts;

-- Function to encrypt PII
CREATE OR REPLACE FUNCTION encrypt_pii(plain_text TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(
        plain_text,
        current_setting('app.encryption_key')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrypt PII
CREATE OR REPLACE FUNCTION decrypt_pii(encrypted_data BYTEA)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        encrypted_data,
        current_setting('app.encryption_key')
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create view with automatic decryption for authorized users
CREATE VIEW users_decrypted AS
SELECT 
    id,
    email,
    decrypt_pii(ssn_encrypted) as ssn,
    created_at
FROM users_encrypted
WHERE pg_has_role(current_user, 'pii_reader', 'MEMBER');

-- Row-level security for encryption
ALTER TABLE users_encrypted ENABLE ROW LEVEL SECURITY;

CREATE POLICY encrypt_policy ON users_encrypted
    FOR ALL
    USING (pg_has_role(current_user, 'data_encryptor', 'MEMBER'));
"""
    
    @staticmethod
    def get_mysql_tde_config() -> str:
        """MySQL Transparent Data Encryption configuration"""
        return """
-- Enable keyring plugin for encryption
INSTALL PLUGIN keyring_file SONAME 'keyring_file.so';

-- Set keyring file location
SET GLOBAL keyring_file_data='/var/lib/mysql-keyring/keyring';

-- Create encrypted table
CREATE TABLE users_encrypted (
    id CHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    ssn_encrypted VARBINARY(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENCRYPTION='Y';

-- Create encryption functions
DELIMITER $$

CREATE FUNCTION encrypt_pii(plain_text VARCHAR(255))
RETURNS VARBINARY(255)
DETERMINISTIC
SQL SECURITY DEFINER
BEGIN
    RETURN AES_ENCRYPT(plain_text, @encryption_key);
END$$

CREATE FUNCTION decrypt_pii(encrypted_data VARBINARY(255))
RETURNS VARCHAR(255)
DETERMINISTIC
SQL SECURITY DEFINER
BEGIN
    RETURN AES_DECRYPT(encrypted_data, @encryption_key);
END$$

DELIMITER ;

-- Set up master key rotation
ALTER INSTANCE ROTATE INNODB MASTER KEY;
"""


class TLSConfiguration:
    """TLS/SSL configuration for data in transit"""
    
    @staticmethod
    def get_nginx_tls_config() -> str:
        """Nginx TLS configuration"""
        return """
# TLS Configuration
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
ssl_trusted_certificate /etc/nginx/ssl/chain.pem;

# TLS versions (only TLS 1.2 and 1.3)
ssl_protocols TLSv1.2 TLSv1.3;

# Cipher suites (strong ciphers only)
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# Prefer server ciphers
ssl_prefer_server_ciphers off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;

# SSL session cache
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Certificate pinning
add_header Public-Key-Pins 'pin-sha256="base64+primary=="; pin-sha256="base64+backup=="; max-age=5184000; includeSubDomains' always;
"""
    
    @staticmethod
    def get_application_tls_config() -> Dict[str, Any]:
        """Application-level TLS configuration"""
        return {
            "tls_version": "1.3",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256"
            ],
            "certificate_path": "/app/certs/server.crt",
            "private_key_path": "/app/certs/server.key",
            "ca_bundle_path": "/app/certs/ca-bundle.crt",
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
            "minimum_version": "TLSv1.2",
            "session_timeout": 86400,
            "session_cache_size": 10000
        }