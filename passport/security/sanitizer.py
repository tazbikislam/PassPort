import re
import logging
from ..config import config

logger = logging.getLogger(__name__)

class InputSanitizer:
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = None) -> str:
        if max_length is None:
            max_length = config.max_input_length
        
        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")
        
        sanitized = value.replace('\x00', '').strip()
        
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bINSERT\b', r'\bUPDATE\b',
            r"\\x[0-9a-fA-F]{2}", r'\"', r'\'\s*OR\s*\''
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Potential malicious input detected: {pattern}")
                raise ValueError("Invalid input detected")
        
        return sanitized
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """Validate password strength"""
        if len(password) < config.min_password_length:
            raise ValueError(f"Password must be at least {config.min_password_length} characters")
        
        if len(password) > config.max_password_length:
            raise ValueError(f"Password must not exceed {config.max_password_length} characters")
        
        return True
    
    @staticmethod
    def validate_site_name(site: str) -> str:
        """Validate and sanitize site name"""
        sanitized = InputSanitizer.sanitize_string(site, 100)
        
        if not re.match(r'^[a-zA-Z0-9._-]+$', sanitized):
            raise ValueError("Site name can only contain letters, numbers, dots, dashes, and underscores")
        
        return sanitized