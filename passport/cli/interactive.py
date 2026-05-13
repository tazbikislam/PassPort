import os
import sys
import questionary
from rich.console import Console
from rich.panel import Panel
from .commands import app as typer_app
from ..config import config

console = Console()

def check_vault_exists():
    key_file = config.default_key_file
    password_file = config.default_password_file
    return os.path.exists(key_file) and os.path.exists(password_file)

def interactive_main():

    if not check_vault_exists():
        console.print(Panel(
            "[bold yellow]  PassPort is not initialized![/bold yellow]\n\n"
            "You need to initialize PassPort before using it.\n"
            "This will create encryption keys and your password vault.",
            title="Setup Required",
            border_style="yellow"
        ))
        
        if questionary.confirm("Would you like to initialize now?").ask():
            sys.argv = ['passport', 'init']
            typer_app()
            return
        else:
            console.print("[red]Cannot proceed without initialization. Exiting...[/red]")
            return
    
    console.print(Panel(
        "[bold cyan] PassPort - Passwords & Portability[/bold cyan]\n"
        "[dim]Encrypt, manage, and carry your passwords everywhere securely.[/dim]",
        border_style="cyan"
    ))
    
    while True:
        try:
            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "1. List all passwords",
                    "2. Add new password",
                    "3. Get password",
                    "4. Update password",
                    "5. Delete password",
                    "6. Generate password",
                    "7. Security audit",
                    "8. Change master password",
                    "9. Exit"
                ]
            ).ask()
            
            if action == "9. Exit":
                console.print("[green] Goodbye! Stay secure! [/green]")
                break
            
            if action == "8. Change master password":
                from ..authentication.auth_manager import AuthManager
                auth_manager = AuthManager()
                auth_manager.is_authenticated = True
                auth_manager.change_master_password()
                input("\n[dim]Press Enter to continue...[/dim]")
                continue
            
            action_map = {
                "1. List all passwords": ["list"],
                "2. Add new password": ["add"],
                "3. Get password": ["get"],
                "4. Update password": ["update"],
                "5. Delete password": ["delete"],
                "6. Generate password": ["generate"],
                "7. Security audit": ["audit"],
            }
            
            if action in action_map:
                try:
                    command = action_map[action]
                    
                    if command[0] in ["add", "get", "update", "delete", "list"]:
                        if not check_vault_exists():
                            console.print("[yellow]  PassPort not initialized![/yellow]")
                            console.print("[dim]Please initialize first using option after restart[/dim]")
                            continue
                    
                    typer_app(command)
                    
                except SystemExit:
                    pass
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                
                input("\n[dim]Press Enter to continue...[/dim]")
            else:
                console.print(f"[yellow]Unknown option: {action}[/yellow]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow] Operation cancelled. Stay secure! [/yellow]")
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")