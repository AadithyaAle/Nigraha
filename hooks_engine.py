import os
import subprocess

from rich.console import Console

from app_paths import HOOKS_DIR

console = Console()


def check_and_run_hooks(error_message):
    """
    Scans the hooks/ directory.
    If a filename matches a word in the error_message, execute it.
    """
    if not HOOKS_DIR.exists():
        return {"executed": False, "success": False}

    error_words = set(error_message.lower().split())

    for script in os.listdir(HOOKS_DIR):
        keyword = script.split("_")[0].lower()
        if keyword not in error_words:
            continue

        script_path = HOOKS_DIR / script
        console.print(
            f"[bold magenta]⚡ Hook Detected:[/bold magenta] found custom script for '{keyword}'"
        )
        console.print(f"Executing: [dim]{script_path}[/dim]")

        if not os.access(script_path, os.X_OK):
            console.print(
                f"[yellow]Skipped hook without execute permission: {script_path}[/yellow]"
            )
            continue

        try:
            result = subprocess.run(
                [str(script_path)],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            console.print(f"[green]Output:[/green]\n{result.stdout}")
            if result.stderr:
                console.print(f"[red]Error:[/red]\n{result.stderr}")
            return {
                "executed": True,
                "success": result.returncode == 0,
                "script": script,
                "returncode": result.returncode,
            }
        except Exception as exc:
            console.print(f"[red]Hook Failed:[/red] {exc}")
            return {"executed": True, "success": False, "script": script}

    return {"executed": False, "success": False}
