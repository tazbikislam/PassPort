from datetime import datetime
from typing import Dict, List, Tuple
from ..config import config

class PasswordAgeTracker:
    
    @staticmethod
    def get_password_age(created_date: datetime) -> Tuple[int, str]:
        age_days = (datetime.now() - created_date).days
        
        if age_days >= config.password_age_warning_days * 2:
            message = f"CRITICAL: This password is {age_days} days old!"
        elif age_days >= config.password_age_warning_days:
            message = f"WARNING: This password is {age_days} days old. Consider changing it."
        else:
            message = f"OK: Password age is {age_days} days."
        
        return age_days, message
    
    @staticmethod
    def check_all_passwords(passwords: Dict) -> List[Tuple[str, str]]:
        warnings = []
        for site, data in passwords.items():
            if 'created_date' in data:
                created = datetime.fromisoformat(data['created_date'])
                age_days, message = PasswordAgeTracker.get_password_age(created)
                if age_days >= config.password_age_warning_days:
                    warnings.append((site, message))
        return warnings