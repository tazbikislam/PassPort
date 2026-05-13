import re
import string
import secrets
from typing import Tuple
from rich.console import Console

console = Console()

class PasswordGenerator:
    
    @staticmethod
    def calculate_strength(password: str) -> Tuple[int, str, str]:
        score = 0
        
        length = len(password)
        if length >= 16:
            score += 3
        elif length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        
        if re.search(r'[a-z]', password) and re.search(r'[A-Z]', password):
            score += 2
        elif re.search(r'[a-zA-Z]', password):
            score += 1
        
        if re.search(r'\d', password):
            score += 1
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 2
        
        if length > 20:
            score += 1
        
        if score >= 8:
            return score, "Very Strong", "green"
        elif score >= 6:
                return score, "Strong", "bright_green"
        elif score >= 4:
            return score, "Moderate", "yellow"
        elif score >= 2:
            return score, "Weak", "orange"
        else:
            return score, "Very Weak", "red"
    
    @staticmethod
    def generate_password(length: int = 20, include_symbols: bool = True) -> str:
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits
        if include_symbols:
            alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                (not include_symbols or any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))):
                return password
    
    @staticmethod
    def display_strength_meter(password: str):
        """Display visual password strength meter"""
        score, label, color = PasswordGenerator.calculate_strength(password)
        
        bar_length = 20
        filled = int((score / 10) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        style = f"[{color}]"
        console.print(f"\nPassword Strength: {style}{label}[/{color}]")
        console.print(f"[{color}]{bar}[/{color}] {score}/10\n")