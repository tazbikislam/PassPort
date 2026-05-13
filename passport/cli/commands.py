import os
import time
import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

from ..config import config
from ..password.manager import PassPort
from ..password.generator import PasswordGenerator
from ..password.tracker import PasswordAgeTracker
from ..security.auditor import SecurityAuditor
from ..utils.animations import Animations

console = Console()
app = typer.Typer(
    name="passport",
    help=" PassPort - Passwords & Portability",
    add_completion=False,
)

def authenticate_passport(passport: PassPort) -> bool:
    """Helper function to authenticate master password"""
    if not passport.master_authenticated:
        console.print("[yellow]  Master authentication required to access vault[/yellow]")
        return passport.authenticate_master()
    return True

@app.command()
def init(
    key_file: str = typer.Option(config.default_key_file, help="Path to encryption key file"),
    password_file: str = typer.Option(config.default_password_file, help="Path to password file"),
):
    """Initialize PassPort with master password"""
    try:
        if os.path.exists(key_file) and os.path.exists(password_file):
            console.print("[yellow] PassPort is already initialized![/yellow]")
            if not questionary.confirm("Do you want to reinitialize? This will DELETE existing data!").ask():
                console.print("[yellow]Initialization cancelled.[/yellow]")
                return
        
        passport = PassPort()
        Animations.loading_spinner("Initializing PassPort", 0.5)
        
        console.print("[bold cyan] Setting up Master Password[/bold cyan]")
        console.print("[dim]This password will encrypt and protect your password vault[/dim]\n")
        
        master_password = questionary.password(
            "Enter master/encryption password:",
            validate=lambda x: len(x) >= 8 or "Password must be at least 8 characters"
        ).ask()
        
        confirm_password = questionary.password("Confirm master password:").ask()
        
        if master_password != confirm_password:
            console.print("[red] Passwords do not match![/red]")
            return
        
        passport.authenticate_master(master_password)
        
        console.print("[bold cyan] Generating encryption key...[/bold cyan]")
        passport.generate_key(key_file)
        
        console.print("[bold cyan] Creating password vault...[/bold cyan]")
        passport.create_password_file(password_file)
        
        success_panel = Panel(
            f"[bold green] PassPort initialized successfully![/bold green]\n\n"
            f" Key file: {key_file}\n"
            f" Vault: {password_file}\n"
            f"  Keep your master password safe!",
            title="Success",
            border_style="green"
        )
        console.print(success_panel)
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")
        raise typer.Exit(code=1)

@app.command()
def add():
    """Add a new password entry"""
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        if not os.path.exists(key_file) or not os.path.exists(password_file):
            console.print("[yellow]  PassPort not initialized![/yellow]")
            return
        
        passport = PassPort()
        passport.load_key(key_file)
        passport.load_password_file(password_file)
        
        if not authenticate_passport(passport):
            return
        
        site = questionary.text("Site/Service name:").ask()
        if not site:
            return
        
        use_generator = questionary.confirm("Generate strong password?").ask()
        
        if use_generator:
            length = questionary.text(
                "Password length",
                default="20",
                validate=lambda x: x.isdigit() and 8 <= int(x) <= 128
            ).ask()
            
            include_symbols = questionary.confirm("Include special characters?", default=True).ask()
            
            password = PasswordGenerator.generate_password(
                length=int(length),
                include_symbols=include_symbols
            )
            
            console.print(f"\n[bold cyan]Generated Password:[/bold cyan]")
            console.print(f"[green]{password}[/green]")
            PasswordGenerator.display_strength_meter(password)
            
            if not questionary.confirm("Use this password?").ask():
                password = questionary.password("Enter password manually:").ask()
        else:
            password = questionary.password("Enter password:").ask()
        
        if password:
            passport.add_password(site, password)
            console.print(f"[bold green] Password added for {site}[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def get():
    """Retrieve a password"""
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        if not os.path.exists(key_file) or not os.path.exists(password_file):
            console.print("[yellow]  PassPort not initialized![/yellow]")
            return
        
        passport = PassPort()
        passport.load_key(key_file)
        passport.load_password_file(password_file)
        
        if not authenticate_passport(passport):
            return
        
        site = questionary.text("Site/Service name:").ask()
        if not site:
            return
        
        password = passport.get_password(site)
        
        if password:
            show = questionary.confirm("Show password?").ask()
            if show:
                console.print(f"\n[bold cyan]Password for {site}:[/bold cyan]")
                console.print(f"[green]{password}[/green]")
            else:
                console.print(f"\n[bold cyan]Password for {site}:[/bold cyan]")
                console.print("[green]••••••••••••[/green]")
        else:
            console.print(f"[yellow]No password found for {site}[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def list():
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        if not os.path.exists(key_file) or not os.path.exists(password_file):
            console.print("[yellow]  PassPort not initialized![/yellow]")
            return
        
        passport = PassPort()
        passport.load_key(key_file)
        passport.load_password_file(password_file)
        
        if not authenticate_passport(passport):
            return
        
        sites = passport.list_sites()
        
        if sites:
            table = Table(title="[bold cyan] Stored Passwords[/bold cyan]")
            table.add_column("Site", style="cyan", no_wrap=True)
            table.add_column("Password Age", style="yellow")
            table.add_column("Status", style="bold")
            
            for site in sites:
                if isinstance(passport.password_dict[site], dict):
                    if 'created_date' in passport.password_dict[site]:
                        created = datetime.fromisoformat(passport.password_dict[site]['created_date'])
                        age_days, _ = PasswordAgeTracker.get_password_age(created)
                        
                        status = "[red]  Update[/red]" if age_days >= config.password_age_warning_days else "[green]✅ OK[/green]"
                        table.add_row(site, f"{age_days} days", status)
                    else:
                        table.add_row(site, "Unknown", "[dim]N/A[/dim]")
                else:
                    table.add_row(site, "Legacy", "[yellow]  Migrate[/yellow]")
            
            console.print(table)
        else:
            console.print("[yellow]No passwords stored yet[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def generate():
    """Generate a strong password"""
    try:
        length = questionary.text(
            "Password length:",
            default="20",
            validate=lambda x: x.isdigit() and 8 <= int(x) <= 128
        ).ask()
        
        include_symbols = questionary.confirm("Include special characters?", default=True).ask()
        
        with console.status("[bold green]Generating secure password...", spinner="dots"):
            time.sleep(0.5)
            password = PasswordGenerator.generate_password(
                length=int(length),
                include_symbols=include_symbols
            )
        
        password_panel = Panel(
            f"[bold cyan]{password}[/bold cyan]",
            title=" Generated Password",
            border_style="cyan"
        )
        console.print(password_panel)
        PasswordGenerator.display_strength_meter(password)
        
        if questionary.confirm("Copy to clipboard?").ask():
            import pyperclip
            pyperclip.copy(password)
            console.print("[green] Copied to clipboard![/green]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def audit():
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        passport = PassPort()
        
        if os.path.exists(key_file) and os.path.exists(password_file):
            passport.load_key(key_file)
            passport.load_password_file(password_file)
        
        console.print("[bold cyan] Running security audit...[/bold cyan]\n")
        SecurityAuditor.run_full_audit(passport)
        
        console.print("\n[bold cyan] Recommendations:[/bold cyan]")
        console.print("  • Set all environment variables in .env file")
        console.print("  • Use password ages to rotate old passwords")
        console.print("  • Enable 2FA for critical accounts")
        console.print("  • Regular backup of encrypted vault")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def delete():
    """Delete a password entry"""
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        if not os.path.exists(key_file) or not os.path.exists(password_file):
            console.print("[yellow]  PassPort not initialized![/yellow]")
            return
        
        passport = PassPort()
        passport.load_key(key_file)
        passport.load_password_file(password_file)
        
        if not authenticate_passport(passport):
            return
        
        site = questionary.text("Site/Service to delete:").ask()
        if not site:
            return
        
        if questionary.confirm(f"Are you sure you want to delete password for {site}?").ask():
            passport.delete_password(site)
            console.print(f"[green] Password deleted for {site}[/green]")
        else:
            console.print("[yellow]Deletion cancelled[/yellow]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.command()
def update():
    try:
        key_file = config.default_key_file
        password_file = config.default_password_file
        
        if not os.path.exists(key_file) or not os.path.exists(password_file):
            console.print("[yellow]⚠️  PassPort not initialized![/yellow]")
            return
        
        passport = PassPort()
        passport.load_key(key_file)
        passport.load_password_file(password_file)
        
        if not authenticate_passport(passport):
            return
        
        site = questionary.text("Site/Service to update:").ask()
        if not site or site not in passport.list_sites():
            console.print(f"[yellow]No password found for {site}[/yellow]")
            return
        
        use_generator = questionary.confirm("Generate new strong password?").ask()
        
        if use_generator:
            length = questionary.text("Password length", default="20").ask()
            include_symbols = questionary.confirm("Include special characters?", default=True).ask()
            new_password = PasswordGenerator.generate_password(
                length=int(length),
                include_symbols=include_symbols
            )
            console.print(f"\n[bold cyan]Generated Password:[/bold cyan]")
            console.print(f"[green]{new_password}[/green]")
            PasswordGenerator.display_strength_meter(new_password)
            
            if not questionary.confirm("Use this password?").ask():
                new_password = questionary.password("Enter password manually:").ask()
        else:
            new_password = questionary.password("Enter new password:").ask()
        
        if new_password:
            passport.update_password(site, new_password)
            console.print(f"[bold green] Password updated for {site}[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red] Error: {e}[/bold red]")

@app.callback()
def callback():
    console.print(Panel(
        "[bold cyan] PassPort - Passwords & Portability[/bold cyan]\n\n"
        "[dim]Encrypt, manage, and carry your passwords everywhere securely.[/dim]",
        border_style="cyan"
    ))