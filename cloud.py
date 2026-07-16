import time

from rich.console import Console

import history
from app_paths import LATEST_EVENT_FILE, atomic_write_json

console = Console()


def push_to_cloud():
    """
    Writes the latest event to a small local state file.
    The name is kept for backward compatibility with older imports.
    """
    data = history.load_history()
    if not data:
        return False

    try:
        atomic_write_json(
            LATEST_EVENT_FILE,
            {
                "synced_at": int(time.time()),
                "latest_event": data[-1],
            },
        )
        console.print("[dim]Latest event exported to local state.[/dim]")
        return True
    except Exception as exc:
        console.print(f"[dim red]State export skipped: {exc}[/dim red]")
        return False
