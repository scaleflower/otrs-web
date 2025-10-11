"""
Encryption utilities for OTRS Web Application
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

def _get_key_from_secret(secret_key: str) -> bytes:
    """Derive encryption key from secret key"""
    # Convert secret key to bytes
    password = secret_key.encode()
    
    # Use a fixed salt for consistent key derivation
    # In production, you should use a random salt stored separately
    salt = b'otrs_web_fixed_salt_for_consistency'
    
    # Derive key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_data(data: str, secret_key: str) -> str:
    """
    Encrypt data using Fernet encryption
    
    Args:
        data: String data to encrypt
        secret_key: Secret key for encryption
        
    Returns:
        Encrypted data as string
    """
    if not data:
        return data
        
    key = _get_key_from_secret(secret_key)
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data: str, secret_key: str) -> str:
    """
    Decrypt data using Fernet encryption
    
    Args:
        encrypted_data: Encrypted data string
        secret_key: Secret key for decryption
        
    Returns:
        Decrypted data as string
    """
    if not encrypted_data:
        return encrypted_data
        
    key = _get_key_from_secret(secret_key)
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data.encode())
    return decrypted_data.decode()