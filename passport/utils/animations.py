import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

console = Console()

class Animations:
    
    @staticmethod
    def loading_spinner(message: str, duration: float = 1.0):
       
        with console.status(f"[bold green]{message}...", spinner="dots"):
            time.sleep(duration)
    
    @staticmethod
    def progress_bar(total: int, description: str = "Processing"):

        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        )