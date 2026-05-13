import hashlib
import logging
from datetime import datetime
from typing import Optional, List
from ..security.sanitizer import InputSanitizer
from ..security.encryption import EncryptionManager
from ..security.rate_limiter import rate_limiter
from ..config import config
from rich.console import Console
import questionary

logger = logging.getLogger(__name__)
console = Console()

class PassPort:
    
    def __init__(self):
        self.encryption = EncryptionManager()
        self.password_file = None
        self.password_dict = {}
        self.master_authenticated = False
    
    def authenticate_master(self, master_password: str = None) -> bool:
        client_id = hashlib.sha256(str(id(self)).encode()).hexdigest()[:16]
        
        is_limited, minutes_left = rate_limiter.is_rate_limited(client_id)
        if is_limited:
            console.print(f"[bold red]Rate limited! Try again in {minutes_left} minutes.[/bold red]")
            return False
        
        if master_password is None:
            master_password = questionary.password("Enter master/encryption password:").ask()
            if not master_password:
                return False
        
        if config.master_password_hash:
            password_hash = hashlib.sha256(master_password.encode()).hexdigest()
            if password_hash != config.master_password_hash:
                rate_limiter.add_attempt(client_id)
                logger.warning(f"Failed master authentication attempt from {client_id}")
                console.print("[red] Invalid master password![/red]")
                return False
        
        rate_limiter.reset_attempts(client_id)
        self.master_authenticated = True
        
        logger.info("Master authentication successful")
        return True
    
    def generate_key(self, path: str = None) -> str:
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        if path is None:
            path = config.default_key_file
        
        return self.encryption.generate_key(path)
    
    def load_key(self, path: str = None):
        if path is None:
            path = config.default_key_file
        
        self.encryption.load_key(path)
    
    def create_password_file(self, path: str = None):
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        if path is None:
            path = config.default_password_file
        
        path = InputSanitizer.sanitize_string(path)
        self.password_file = path
        
        empty_data = {}
        self.encryption.save_passwords(empty_data, path)
        
        logger.info(f"Created new password file at {path}")
    
    def load_password_file(self, path: str = None):
        if path is None:
            path = config.default_password_file
        
        path = InputSanitizer.sanitize_string(path)
        self.password_file = path
        self.password_dict = self.encryption.load_passwords(path)
        logger.info(f"Loaded password file from {path}")
    
    def add_password(self, site: str, password: str):
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        site = InputSanitizer.validate_site_name(site)
        InputSanitizer.validate_password(password)
        
        self.password_dict[site] = {
            'password': password,
            'created_date': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
        
        self.encryption.save_passwords(self.password_dict, self.password_file)
        logger.info(f"Added password for {site}")
    
    def get_password(self, site: str) -> Optional[str]:
        """Retrieve a password"""
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        site = InputSanitizer.validate_site_name(site)
        data = self.password_dict.get(site)
        
        if isinstance(data, dict):
            return data.get('password')
        return None
    
    def list_sites(self) -> List[str]:
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        return list(self.password_dict.keys())
    
    def delete_password(self, site: str):
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        site = InputSanitizer.validate_site_name(site)
        
        if site in self.password_dict:
            del self.password_dict[site]
            self.encryption.save_passwords(self.password_dict, self.password_file)
            logger.info(f"Deleted password for {site}")
    
    def update_password(self, site: str, new_password: str):
        if not self.master_authenticated:
            raise PermissionError("Master authentication required")
        
        site = InputSanitizer.validate_site_name(site)
        InputSanitizer.validate_password(new_password)
        
        if site in self.password_dict:
            self.password_dict[site]['password'] = new_password
            self.password_dict[site]['last_modified'] = datetime.now().isoformat()
            self.encryption.save_passwords(self.password_dict, self.password_file)
            logger.info(f"Updated password for {site}")