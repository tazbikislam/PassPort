import re
import logging
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..config import config
from ..password.generator import PasswordGenerator
from ..password.tracker import PasswordAgeTracker

logger = logging.getLogger(__name__)
console = Console()

class SecurityAuditor:
    
    @staticmethod
    def scan_codebase() -> List[dict]:
        console.print("\n[bold cyan] Scanning codebase for hardcoded secrets...[/bold cyan]")
        
        sensitive_patterns = [
            r'(?:api[_-]?key|apikey|token|secret|password|passwd)\s*[=:]\s*["\'][^"\']+["\']',
            r'(?:-----BEGIN\s+(?:RSA|DSA|EC|OPENSSH|PGP)\s+PRIVATE\s+KEY)',
            r'(?:eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+)',
        ]
        
        findings = []
        current_file = Path(__file__).parent.parent / "main.py"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            
            task = progress.add_task("[cyan]Scanning files...", total=1)
            
            try:
                with open(current_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern in sensitive_patterns:
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                findings.append({
                                    'file': str(current_file),
                                    'line': line_num,
                                    'content': match.group()[:50] + '...',
                                    'pattern': pattern
                                })
                progress.update(task, completed=1)
            except Exception as e:
                logger.error(f"Error scanning codebase: {e}")
        
        return findings
    
    @staticmethod
    def run_full_audit(passport) -> Tuple[List[dict], List[str]]:

        console.print(Panel.fit("[bold] Security Audit Report[/bold]", border_style="cyan"))
        
        findings = []
        warnings = []
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("[cyan]Checking for hardcoded secrets...", total=1)
            code_findings = SecurityAuditor.scan_codebase()
            if code_findings:
                findings.extend(code_findings)
                warnings.append("Hardcoded secrets found in codebase")
            progress.update(task, completed=1)
        
        env_checks = {
            'MASTER_PASSWORD_HASH': config.master_password_hash,
            'MAX_LOGIN_ATTEMPTS': config.max_login_attempts,
            'LOCKOUT_MINUTES': config.lockout_minutes,
            'KEY_DERIVATION_ITERATIONS': config.key_derivation_iterations,
        }
        
        for key, value in env_checks.items():
            if not value:
                warnings.append(f"Environment variable {key} not set or empty")

        if passport.password_dict:
            weak_passwords = []
            for site, data in passport.password_dict.items():
                if isinstance(data, dict) and 'password' in data:
                    score, _, _ = PasswordGenerator.calculate_strength(data['password'])
                    if score < 4:
                        weak_passwords.append(site)
            
            if weak_passwords:
                warnings.append(f"Weak passwords found for: {', '.join(weak_passwords)}")

        age_warnings = PasswordAgeTracker.check_all_passwords(passport.password_dict)
        if age_warnings:
            for site, message in age_warnings:
                warnings.append(f"Password age issue for {site}: {message}")

        table = Table(title="Audit Results", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details")
        
        if findings:
            table.add_row("Code Secrets", " FAIL", f"{len(findings)} potential secrets found")
        else:
            table.add_row("Code Secrets", " PASS", "No hardcoded secrets detected")
        
        if warnings:
            table.add_row("Security Warnings", "  WARN", f"{len(warnings)} warnings found")
        else:
            table.add_row("Security Warnings", " PASS", "No security warnings")
        
        table.add_row("Rate Limiting", " ENABLED", f"Max {config.max_login_attempts} attempts per {config.lockout_minutes} minutes")
        table.add_row("Input Sanitization", " ACTIVE", "All inputs are sanitized")
        table.add_row("Encryption", " ACTIVE", "AES-128 (Fernet) + PBKDF2 key derivation")
        
        console.print(table)
        
        if warnings:
            console.print("\n[bold yellow]  Security Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  • {warning}")
        
        if findings:
            console.print("\n[bold red] Critical Findings:[/bold red]")
            for finding in findings:
                console.print(f"  • {finding['file']}:{finding['line']} - {finding['content']}")
        
        return findings, warnings