import os
import subprocess
from rich.console import Console

console = Console()
HOOKS_DIR = "hooks"

def check_and_run_hooks(error_message):
    """
    Scans the hooks/ directory.
    If a filename matches a word in the error_message, execute it.
    """
    if not os.path.exists(HOOKS_DIR):
        return False

    executed = False
    error_words = set(error_message.lower().split())

    for script in os.listdir(HOOKS_DIR):
        # Example: script "wifi_fix.sh" -> keyword "wifi"
        keyword = script.split('_')[0].lower()
        
        if keyword in error_words:
            script_path = os.path.join(HOOKS_DIR, script)
            
            console.print(f"[bold magenta]⚡ Hook Detected:[/bold magenta] found custom script for '{keyword}'")
            console.print(f"Executing: [dim]{script_path}[/dim]")
            
            try:
                # Run the script
                result = subprocess.run([f"./{script_path}"], shell=True, capture_output=True, text=True)
                console.print(f"[green]Output:[/green]\n{result.stdout}")
                if result.stderr:
                    console.print(f"[red]Error:[/red]\n{result.stderr}")
                executed = True
            except Exception as e:
                console.print(f"[red]Hook Failed:[/red] {e}")

    return executed