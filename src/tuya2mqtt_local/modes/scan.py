import subprocess
import sys
from typing import Sequence

from rich.console import Console

console = Console()


def scan_mode(args: Sequence[str] = ()):
    """Run tinytuya scan."""
    console.print("[bold blue]Starting TinyTuya scan...[/bold blue]")

    try:
        cmd = [sys.executable, "-m", "tinytuya", "scan", *args]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running TinyTuya scan: {e}[/red]")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
