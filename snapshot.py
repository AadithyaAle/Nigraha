import os
import tarfile
import time
from pathlib import Path

from rich.console import Console

from app_paths import (
    BACKUP_DIR,
    BASELINE_FILE,
    HISTORY_FILE,
    PROFILE_FILE,
    SETTINGS_FILE,
    atomic_write_bytes,
    atomic_write_text,
)

console = Console()
SNAPSHOT_TARGETS = {
    "shell/bashrc": Path(os.path.expanduser("~/.bashrc")),
    "app/settings.json": SETTINGS_FILE,
    "app/sentinel_history.json": HISTORY_FILE,
    "app/system_profile.json": PROFILE_FILE,
    "app/system_baseline.json": BASELINE_FILE,
}


def cleanup_old_snapshots(keep=5):
    """Prevents disk from filling up by deleting old backups."""
    if not BACKUP_DIR.exists():
        return
    snapshots = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".tar.gz"):
            snapshots.append(os.path.join(BACKUP_DIR, filename))

    snapshots.sort(key=os.path.getmtime)

    while len(snapshots) > keep:
        oldest = snapshots.pop(0)
        try:
            os.remove(oldest)
            meta_path = oldest + ".meta"
            if os.path.exists(meta_path):
                os.remove(meta_path)
            console.print(
                f"[dim yellow]🧹 Cleaned old snapshot: {os.path.basename(oldest)}[/dim yellow]"
            )
        except OSError:
            pass


def create_snapshot(note="Manual Snapshot"):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"snapshot_{timestamp}.tar.gz"
    filepath = os.path.join(BACKUP_DIR, filename)

    console.print(f"[bold blue]📦 Creating Snapshot: {filename}...[/bold blue]")
    try:
        with tarfile.open(filepath, "w:gz") as archive:
            for archive_name, path in SNAPSHOT_TARGETS.items():
                if path.exists():
                    archive.add(path, arcname=archive_name)

        atomic_write_text(Path(filepath + ".meta"), note)
        cleanup_old_snapshots()
        console.print("[bold green]✅ Snapshot Saved![/bold green]")
        return True
    except Exception as exc:
        console.print(f"[bold red]❌ Backup Failed:[/bold red] {exc}")
        return False


def list_snapshots():
    if not BACKUP_DIR.exists():
        return []
    snapshots = []
    for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if filename.endswith(".tar.gz"):
            note = "Auto-Backup"
            meta_path = Path(BACKUP_DIR) / f"{filename}.meta"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as handle:
                    note = handle.read().strip() or note
            snapshots.append({"file": filename, "note": note})
    return snapshots


def restore_snapshot(filename):
    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        return False
    try:
        with tarfile.open(filepath, "r:gz") as archive:
            restored = 0
            for member in archive.getmembers():
                if not member.isfile() or member.name not in SNAPSHOT_TARGETS:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                atomic_write_bytes(SNAPSHOT_TARGETS[member.name], extracted.read())
                restored += 1
            if restored == 0:
                raise ValueError("No valid snapshot entries were found.")
        console.print("[bold green]✅ System Restored![/bold green]")
        return True
    except Exception as exc:
        console.print(f"[bold red]❌ Restore Failed:[/bold red] {exc}")
        return False
