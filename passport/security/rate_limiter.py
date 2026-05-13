from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from ..config import config

@dataclass
class RateLimiter:
    attempts: Dict[str, List[datetime]] = field(default_factory=dict)
    
    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        now = datetime.now()
        cutoff = now - timedelta(minutes=config.lockout_minutes)
        
        if key not in self.attempts:
            self.attempts[key] = []
        
        self.attempts[key] = [t for t in self.attempts[key] if t > cutoff]
        
        if len(self.attempts[key]) >= config.max_login_attempts:
            time_until_reset = (self.attempts[key][0] + timedelta(minutes=config.lockout_minutes)) - now
            minutes_left = int(time_until_reset.total_seconds() / 60) + 1
            return True, minutes_left
        
        return False, 0
    
    def add_attempt(self, key: str):
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(datetime.now())
    
    def reset_attempts(self, key: str):
        if key in self.attempts:
            self.attempts[key] = []

rate_limiter = RateLimiter()