import os
import re
import hashlib
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Optional, Dict
from getpass import getpass

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import config
from ..security.rate_limiter import rate_limiter
from ..password.generator import PasswordGenerator

logger = logging.getLogger(__name__)
console = Console()

class AuthManager:    
    def __init__(self):
        self.auth_file = Path.home() / '.passport_auth.json'
        self.master_password = None
        self.is_authenticated = False
        
    def is_first_run(self) -> bool:
        return not self.auth_file.exists()
    
    def validate_master_password_strength(self, password: str) -> Tuple[bool, str]:
        try:
            if not password:
                return False, "Password cannot be empty"
            
            if len(password) < 16:
                return False, "Master password must be at least 16 characters long"
            
            if len(password) > 128:
                return False, "Master password must not exceed 128 characters"
            
            common_patterns = [
                r'password', r'123456', r'qwerty', r'admin',
                r'letmein', r'welcome', r'monkey', r'dragon',
                r'master', r'passport', r'login'
            ]
            
            for pattern in common_patterns:
                if re.search(pattern, password, re.IGNORECASE):
                    return False, f"Password contains common pattern: '{pattern}'"
            
            has_lower = bool(re.search(r'[a-z]', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_digit = bool(re.search(r'\d', password))
            has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
            
            missing = []
            if not has_lower:
                missing.append("lowercase letter")
            if not has_upper:
                missing.append("uppercase letter")
            if not has_digit:
                missing.append("digit")
            if not has_special:
                missing.append("special character")
            
            if missing:
                return False, f"Password must contain: {', '.join(missing)}"
            
            score, label, _ = PasswordGenerator.calculate_strength(password)
            if score < 7:
                return False, f"Password is too weak ({label}). Please use a stronger password"
            
            return True, "Password meets strength requirements"
            
        except Exception as e:
            logger.error(f"Password validation error: {e}")
            return False, f"Error validating password: {str(e)}"
    
    def setup_master_password(self) -> bool:
        console.print(Panel(
            "[bold cyan] Welcome to PassPort - Initial Setup[/bold cyan]\n\n"
            "[yellow]This appears to be your first time using PassPort.[/yellow]\n"
            "You need to create a strong master password.\n\n"
            "[bold]Requirements for master password:[/bold]\n"
            "• At least 16 characters long\n"
            "• Must contain uppercase, lowercase, digit, and special character\n"
            "• Should not contain common words or patterns\n"
            "• [red]IMPORTANT: Remember this password! It cannot be recovered![/red]",
            border_style="cyan"
        ))
        
        while True:
            try:
                console.print("\n[bold]Enter a strong master password:[/bold]")
                password = getpass("")
                
                if not password:
                    console.print("[red]❌ Password cannot be empty![/red]")
                    continue
                
                is_valid, message = self.validate_master_password_strength(password)
                if not is_valid:
                    console.print(f"[red] {message}[/red]")
                    continue
                
                score, label, color = PasswordGenerator.calculate_strength(password)
                console.print(f"[{color}]Password Strength: {label} ({score}/10)[/{color}]")
                
                console.print("\n[bold]Confirm master password:[/bold]")
                confirm_password = getpass("")
                
                if not confirm_password:
                    console.print("[red] Confirmation cannot be empty![/red]")
                    continue
                
                if password != confirm_password:
                    console.print("[red] Passwords do not match![/red]")
                    continue
                
                if self._save_password_hash(password):
                    self.master_password = password
                    self.is_authenticated = True
                    
                    console.print(Panel(
                        "[bold green] Master password set successfully![/bold green]\n\n"
                        "[yellow]  IMPORTANT: Store your master password safely![/yellow]\n"
                        "• Write it down and keep it in a secure location\n"
                        "• You will need this password every time you use PassPort",
                        border_style="green"
                    ))
                    return True
                else:
                    console.print("[red] Failed to save master password[/red]")
                    return False
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Setup cancelled by user[/yellow]")
                return False
            except Exception as e:
                console.print(f"[red] Error during setup: {e}[/red]")
                logger.error(f"Setup error: {e}")
                return False
    
    def authenticate(self) -> bool:
        """
        Authenticate user with master password
        Returns True if authenticated, False otherwise
        """
        try:
            if self.is_first_run():
                return self.setup_master_password()
            
            stored_hash = self._load_password_hash()
            if not stored_hash:
                console.print("[red] Authentication data corrupted. Please reinstall.[/red]")
                console.print("[yellow]Removing corrupted auth file...[/yellow]")
                self.auth_file.unlink(missing_ok=True)
                return self.setup_master_password()
            
            client_ip = "local"
            
            max_attempts = config.max_login_attempts
            attempts = 0
            
            console.print(Panel(
                "[bold cyan] PassPort - Master Password Authentication[/bold cyan]\n"
                "[dim]Enter your master password to unlock the vault[/dim]",
                border_style="cyan"
            ))
            
            while attempts < max_attempts:
                try:
                    is_limited, minutes_left = rate_limiter.is_rate_limited(client_ip)
                    if is_limited:
                        console.print(f"[bold red]Too many attempts! Try again in {minutes_left} minutes.[/bold red]")
                        return False
                    
                    console.print(f"\n[bold]Master Password (attempt {attempts + 1}/{max_attempts}):[/bold]")
                    password = getpass("")
                    
                    if not password:
                        console.print("[red] Password cannot be empty![/red]")
                        continue
                    
                    # Verify password
                    if self._verify_password(password, stored_hash):
                        rate_limiter.reset_attempts(client_ip)
                        self.master_password = password
                        self.is_authenticated = True
                        
                        with console.status("[bold green]Unlocking vault...", spinner="dots"):
                            import time
                            time.sleep(0.5)
                        
                        console.print("[bold green] Authentication successful![/bold green]\n")
                        return True
                    
                    attempts += 1
                    rate_limiter.add_attempt(client_ip)
                    
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        console.print(f"[red] Incorrect password! {remaining} attempts remaining.[/red]")
                    
                    if attempts >= 3:
                        console.print("[yellow]  Hint: Make sure Caps Lock is off and check your keyboard layout[/yellow]")
                        
                except KeyboardInterrupt:
                    console.print("\n[yellow]Authentication cancelled[/yellow]")
                    return False
            
            console.print("[bold red] Maximum attempts reached. Account temporarily locked.[/bold red]")
            return False
            
        except Exception as e:
            console.print(f"[red] Authentication error: {e}[/red]")
            logger.error(f"Authentication error: {e}")
            return False
    
    def _save_password_hash(self, password: str) -> bool:
        try:
            salt = os.urandom(32)
            
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000,  
                dklen=32
            )
            
            auth_data = {
                'salt': salt.hex(),
                'hash': password_hash.hex(),
                'created_date': datetime.now().isoformat(),
                'iterations': 100000,
                'version': '1.0'
            }
            
            self.auth_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
            
            try:
                import stat
                os.chmod(self.auth_file, stat.S_IRUSR | stat.S_IWUSR)  # 600
            except:
                pass  
            
            logger.info("Master password hash saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save password hash: {e}")
            return False
    
    def _load_password_hash(self) -> Optional[Dict]:
        try:
            if not self.auth_file.exists():
                return None
            
            with open(self.auth_file, 'r') as f:
                auth_data = json.load(f)
            
            required_keys = ['salt', 'hash', 'iterations']
            if not all(key in auth_data for key in required_keys):
                logger.error("Invalid auth data structure")
                return None
            
            return auth_data
            
        except Exception as e:
            logger.error(f"Failed to load password hash: {e}")
            return None
    
    def _verify_password(self, password: str, stored_data: Dict) -> bool:
        """
        Verify password against stored hash
        Returns True if password matches, False otherwise
        """
        try:
            salt = bytes.fromhex(stored_data['salt'])
            stored_hash = bytes.fromhex(stored_data['hash'])
            iterations = stored_data.get('iterations', 100000)
            
            password_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                iterations,
                dklen=32
            )
            
            import hmac
            return hmac.compare_digest(password_hash, stored_hash)
            
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def change_master_password(self) -> bool:
        if not self.is_authenticated:
            console.print("[red] Must be authenticated to change password[/red]")
            return False
        
        console.print(Panel(
            "[bold cyan] Change Master Password[/bold cyan]",
            border_style="cyan"
        ))
        
        console.print("[bold]Enter current master password:[/bold]")
        current_password = getpass("")
        
        stored_data = self._load_password_hash()
        if not stored_data or not self._verify_password(current_password, stored_data):
            console.print("[red] Current password is incorrect[/red]")
            return False
        
        while True:
            console.print("\n[bold]Enter new master password:[/bold]")
            new_password = getpass("")
            
            is_valid, message = self.validate_master_password_strength(new_password)
            if not is_valid:
                console.print(f"[red] {message}[/red]")
                continue
            
            console.print("[bold]Confirm new master password:[/bold]")
            confirm_password = getpass("")
            
            if new_password != confirm_password:
                console.print("[red] Passwords do not match[/red]")
                continue
            
            if self._save_password_hash(new_password):
                self.master_password = new_password
                console.print("[green] Master password changed successfully![/green]")
                return True
            else:
                console.print("[red] Failed to save new password[/red]")
                return False
    
    def get_master_password(self) -> Optional[str]:
        if not self.is_authenticated:
            return None
        return self.master_password
    
    def logout(self):
        self.master_password = None
        self.is_authenticated = False
        console.print("[yellow] Logged out successfully[/yellow]")