import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    max_login_attempts: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    lockout_minutes: int = int(os.getenv('LOCKOUT_MINUTES', '15'))
    password_age_warning_days: int = int(os.getenv('PASSWORD_AGE_WARNING_DAYS', '180'))
    max_input_length: int = int(os.getenv('MAX_INPUT_LENGTH', '256'))
    min_password_length: int = int(os.getenv('MIN_PASSWORD_LENGTH', '8'))
    max_password_length: int = int(os.getenv('MAX_PASSWORD_LENGTH', '128'))
    key_derivation_iterations: int = int(os.getenv('KEY_DERIVATION_ITERATIONS', '100000'))
    default_key_file: str = os.getenv('DEFAULT_KEY_FILE', 'passport.key')
    default_password_file: str = os.getenv('DEFAULT_PASSWORD_FILE', 'passwords.enc')
    master_password_hash: str = os.getenv('MASTER_PASSWORD_HASH', '')
    security_audit_enabled: bool = os.getenv('SECURITY_AUDIT_ENABLED', 'true').lower() == 'true'

config = Config()