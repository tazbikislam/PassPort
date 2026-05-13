import os
import json
import base64
import logging
from typing import Tuple, Dict
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..config import config

logger = logging.getLogger(__name__)

class EncryptionManager:
    
    def __init__(self):
        self.key = None
        self.fernet = None
    
    def derive_key(self, master_password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=config.key_derivation_iterations,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key, salt
    
    def generate_key(self, path: str = None) -> str:
        if path is None:
            path = config.default_key_file
        
        self.key = Fernet.generate_key()
        self.fernet = Fernet(self.key)
        
        with open(path, 'wb') as f:
            f.write(self.key)
        
        logger.info(f"Generated new encryption key at {path}")
        return path
    
    def load_key(self, path: str = None):
        if path is None:
            path = config.default_key_file
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Key file not found: {path}")
        
        with open(path, 'rb') as f:
            self.key = f.read()
        
        self.fernet = Fernet(self.key)
        logger.info(f"Loaded encryption key from {path}")
    
    def save_passwords(self, password_dict: Dict, password_file: str):
        if not self.fernet:
            raise ValueError("Encryption key not loaded. Call generate_key() or load_key() first")
        
        json_data = json.dumps(password_dict, indent=2).encode()
        encrypted_data = self.fernet.encrypt(json_data)
        
        with open(password_file, 'wb') as f:
            f.write(encrypted_data)
        
        logger.info(f"Saved encrypted passwords to {password_file}")
    
    def load_passwords(self, password_file: str) -> Dict:
        if not os.path.exists(password_file):
            raise FileNotFoundError(f"Password file not found: {password_file}")
        
        if not self.fernet:
            raise ValueError("Encryption key not loaded. Call generate_key() or load_key() first")
        
        try:
            with open(password_file, 'rb') as f:
                encrypted_data = f.read()
            
            if encrypted_data:
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            return {}
        except InvalidToken:
            raise ValueError("Invalid encryption key or corrupted password file")
        except Exception as e:
            logger.error(f"Error loading passwords: {e}")
            raise