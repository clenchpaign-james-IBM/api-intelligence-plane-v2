"""
FIPS 140-3 Compliant Cryptography

This module provides cryptographic functions that comply with FedRAMP 140-3
requirements using NIST-approved algorithms.

Supported Algorithms:
- AES-256-GCM for symmetric encryption
- RSA-2048/4096 for asymmetric encryption
- SHA-256/SHA-384/SHA-512 for hashing
- HMAC-SHA-256/384/512 for message authentication
"""

import hashlib
import hmac
import secrets
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

from app.config import settings


class FIPSCrypto:
    """
    FIPS 140-3 compliant cryptographic operations.
    
    All algorithms used are NIST-approved and suitable for FedRAMP compliance.
    """
    
    # Key sizes (in bits)
    AES_KEY_SIZE = 256  # AES-256
    RSA_KEY_SIZE = 2048  # RSA-2048 minimum (can use 4096 for higher security)
    
    # Nonce/IV sizes (in bytes)
    GCM_NONCE_SIZE = 12  # 96 bits for GCM
    GCM_TAG_SIZE = 16    # 128 bits for authentication tag
    
    @staticmethod
    def generate_key(key_size: int = AES_KEY_SIZE) -> bytes:
        """
        Generate a cryptographically secure random key.
        
        Args:
            key_size: Key size in bits (default: 256 for AES-256)
            
        Returns:
            Random key bytes
        """
        return secrets.token_bytes(key_size // 8)
    
    @staticmethod
    def generate_nonce() -> bytes:
        """
        Generate a cryptographically secure random nonce for GCM.
        
        Returns:
            Random nonce bytes (12 bytes for GCM)
        """
        return secrets.token_bytes(FIPSCrypto.GCM_NONCE_SIZE)
    
    @staticmethod
    def encrypt_aes_gcm(
        plaintext: bytes,
        key: bytes,
        associated_data: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-GCM (AEAD cipher).
        
        AES-GCM provides both confidentiality and authenticity.
        
        Args:
            plaintext: Data to encrypt
            key: 256-bit encryption key
            associated_data: Optional additional authenticated data (AAD)
            
        Returns:
            Tuple of (nonce, ciphertext_with_tag)
            
        Raises:
            ValueError: If key size is invalid
        """
        if len(key) != FIPSCrypto.AES_KEY_SIZE // 8:
            raise ValueError(f"Key must be {FIPSCrypto.AES_KEY_SIZE} bits")
        
        # Generate random nonce
        nonce = FIPSCrypto.generate_nonce()
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key)
        
        # Encrypt and authenticate
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        
        return nonce, ciphertext
    
    @staticmethod
    def decrypt_aes_gcm(
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            ciphertext: Encrypted data with authentication tag
            key: 256-bit decryption key
            nonce: Nonce used during encryption
            associated_data: Optional AAD used during encryption
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If key or nonce size is invalid
            InvalidTag: If authentication fails (data tampered)
        """
        if len(key) != FIPSCrypto.AES_KEY_SIZE // 8:
            raise ValueError(f"Key must be {FIPSCrypto.AES_KEY_SIZE} bits")
        
        if len(nonce) != FIPSCrypto.GCM_NONCE_SIZE:
            raise ValueError(f"Nonce must be {FIPSCrypto.GCM_NONCE_SIZE} bytes")
        
        # Create AESGCM cipher
        aesgcm = AESGCM(key)
        
        # Decrypt and verify
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except InvalidTag:
            raise ValueError("Authentication failed - data may be tampered")
    
    @staticmethod
    def hash_sha256(data: bytes) -> bytes:
        """
        Compute SHA-256 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-256 hash (32 bytes)
        """
        return hashlib.sha256(data).digest()
    
    @staticmethod
    def hash_sha384(data: bytes) -> bytes:
        """
        Compute SHA-384 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-384 hash (48 bytes)
        """
        return hashlib.sha384(data).digest()
    
    @staticmethod
    def hash_sha512(data: bytes) -> bytes:
        """
        Compute SHA-512 hash.
        
        Args:
            data: Data to hash
            
        Returns:
            SHA-512 hash (64 bytes)
        """
        return hashlib.sha512(data).digest()
    
    @staticmethod
    def hmac_sha256(key: bytes, message: bytes) -> bytes:
        """
        Compute HMAC-SHA-256 for message authentication.
        
        Args:
            key: Secret key
            message: Message to authenticate
            
        Returns:
            HMAC-SHA-256 tag (32 bytes)
        """
        return hmac.new(key, message, hashlib.sha256).digest()
    
    @staticmethod
    def hmac_sha384(key: bytes, message: bytes) -> bytes:
        """
        Compute HMAC-SHA-384 for message authentication.
        
        Args:
            key: Secret key
            message: Message to authenticate
            
        Returns:
            HMAC-SHA-384 tag (48 bytes)
        """
        return hmac.new(key, message, hashlib.sha384).digest()
    
    @staticmethod
    def hmac_sha512(key: bytes, message: bytes) -> bytes:
        """
        Compute HMAC-SHA-512 for message authentication.
        
        Args:
            key: Secret key
            message: Message to authenticate
            
        Returns:
            HMAC-SHA-512 tag (64 bytes)
        """
        return hmac.new(key, message, hashlib.sha512).digest()
    
    @staticmethod
    def generate_rsa_keypair(
        key_size: int = RSA_KEY_SIZE,
    ) -> Tuple[bytes, bytes]:
        """
        Generate RSA key pair for asymmetric encryption.
        
        Args:
            key_size: Key size in bits (2048 or 4096)
            
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        if key_size not in [2048, 4096]:
            raise ValueError("RSA key size must be 2048 or 4096 bits")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend(),
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize public key
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        
        return private_pem, public_pem
    
    @staticmethod
    def encrypt_rsa_oaep(plaintext: bytes, public_key_pem: bytes) -> bytes:
        """
        Encrypt data using RSA-OAEP with SHA-256.
        
        Args:
            plaintext: Data to encrypt (max size depends on key size)
            public_key_pem: Public key in PEM format
            
        Returns:
            Encrypted ciphertext
        """
        # Load public key
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend(),
        )
        
        # Encrypt using OAEP with SHA-256
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        
        return ciphertext
    
    @staticmethod
    def decrypt_rsa_oaep(ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """
        Decrypt data using RSA-OAEP with SHA-256.
        
        Args:
            ciphertext: Encrypted data
            private_key_pem: Private key in PEM format
            
        Returns:
            Decrypted plaintext
        """
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend(),
        )
        
        # Decrypt using OAEP with SHA-256
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        
        return plaintext


# Convenience functions using application secret key
def encrypt_data(plaintext: bytes) -> Tuple[bytes, bytes]:
    """
    Encrypt data using application secret key.
    
    Args:
        plaintext: Data to encrypt
        
    Returns:
        Tuple of (nonce, ciphertext)
    """
    # Derive encryption key from secret key
    key = FIPSCrypto.hash_sha256(settings.SECRET_KEY.encode())
    return FIPSCrypto.encrypt_aes_gcm(plaintext, key)


def decrypt_data(ciphertext: bytes, nonce: bytes) -> bytes:
    """
    Decrypt data using application secret key.
    
    Args:
        ciphertext: Encrypted data
        nonce: Nonce used during encryption
        
    Returns:
        Decrypted plaintext
    """
    # Derive encryption key from secret key
    key = FIPSCrypto.hash_sha256(settings.SECRET_KEY.encode())
    return FIPSCrypto.decrypt_aes_gcm(ciphertext, key, nonce)


def hash_password(password: str) -> str:
    """
    Hash password using SHA-512 (for demonstration - use bcrypt/argon2 in production).
    
    Args:
        password: Plain text password
        
    Returns:
        Hex-encoded hash
    """
    return FIPSCrypto.hash_sha512(password.encode()).hex()


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        password: Plain text password
        password_hash: Hex-encoded hash
        
    Returns:
        True if password matches
    """
    computed_hash = hash_password(password)
    return hmac.compare_digest(computed_hash, password_hash)

# Made with Bob
