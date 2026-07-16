import os
import tarfile
import time
from rich.console import Console
from rich.prompt import Prompt

console = Console()
BACKUP_DIR = "sentinel_backups"
CRITICAL_PATHS = [
    os.path.expanduser("~/.bashrc"),
    "settings.json",
    "sentinel_history.json"
]

def cleanup_old_snapshots(keep=5):
    """
    Prevents disk from filling up by deleting old backups.
    """
    if not os.path.exists(BACKUP_DIR): return
    snapshots = []
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".tar.gz"):
            snapshots.append(os.path.join(BACKUP_DIR, f))
    
    # Sort by time (oldest first)
    snapshots.sort(key=os.path.getmtime)
    
    while len(snapshots) > keep:
        oldest = snapshots.pop(0)
        try:
            os.remove(oldest)
            if os.path.exists(oldest + ".meta"): os.remove(oldest + ".meta")
            console.print(f"[dim yellow]🧹 Cleaned old snapshot: {os.path.basename(oldest)}[/dim yellow]")
        except OSError: pass

def create_snapshot(note="Manual Snapshot"):
    if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
    
    cleanup_old_snapshots() # Auto-clean before creating new

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"snapshot_{timestamp}.tar.gz"
    filepath = os.path.join(BACKUP_DIR, filename)

    console.print(f"[bold blue]📦 Creating Snapshot: {filename}...[/bold blue]")
    try:
        with tarfile.open(filepath, "w:gz") as tar:
            for path in CRITICAL_PATHS:
                if os.path.exists(path): 
                    tar.add(path)
        
        with open(filepath + ".meta", "w") as f: 
            f.write(note)
        console.print(f"[bold green]✅ Snapshot Saved![/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Backup Failed:[/bold red] {e}")
        return False

def list_snapshots():
    if not os.path.exists(BACKUP_DIR): return []
    snapshots = []
    for f in sorted(os.listdir(BACKUP_DIR)):
        if f.endswith(".tar.gz"):
            note = "Auto-Backup"
            if os.path.exists(os.path.join(BACKUP_DIR, f + ".meta")):
                with open(os.path.join(BACKUP_DIR, f + ".meta"), "r") as mf: note = mf.read().strip()
            snapshots.append({"file": f, "note": note})
    return snapshots

def restore_snapshot(filename):
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath): return False
    try:
        with tarfile.open(filepath, "r:gz") as tar:
            tar.extractall(path="/") 
        console.print("[bold green]✅ System Restored![/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Restore Failed:[/bold red] {e}")
        return False