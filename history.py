import json
import os
import re
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from app_paths import HISTORY_FILE, atomic_write_json

LOG_FILE = HISTORY_FILE
console = Console()


def save_event(problem, solution, fix_cmd, backup_cmd, auditor_status, status):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "problem": problem,
        "ai_diagnosis": solution,
        "proposed_fix": fix_cmd,
        "backup_command": backup_cmd,
        "auditor_verdict": auditor_status,
        "final_status": status,
        "user_feedback": None,
    }
    history = load_history()
    history.append(entry)
    atomic_write_json(LOG_FILE, history)


def load_history():
    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, ValueError):
        console.print("[bold red]⚠️  Warning: History file is corrupted.[/bold red]")
        backup_name = LOG_FILE.with_suffix(LOG_FILE.suffix + ".corrupted")
        os.rename(LOG_FILE, backup_name)
        console.print(f"[dim]Moved corrupted file to {backup_name}. Starting fresh.[/dim]")
        return []


def _problem_fingerprint(problem):
    normalized = re.sub(r"\[[^\]]+\]", "", problem.lower())
    normalized = re.sub(r"\d+", "#", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def check_recurrence(current_problem):
    data = load_history()
    for entry in reversed(data):
        words_a = set(current_problem.lower().split())
        words_b = set(entry.get("problem", "").lower().split())
        if len(words_a) == 0:
            continue
        if len(words_a.intersection(words_b)) / len(words_a) > 0.4:
            return entry
    return None


def is_system_looping(problem, limit=3, window_minutes=5):
    """
    Circuit Breaker: Checks if we are repeatedly trying to fix the same error.
    """
    data = load_history()
    recent_fixes = 0
    now = datetime.now()
    current_fingerprint = _problem_fingerprint(problem)

    for entry in reversed(data):
        timestamp = entry.get("timestamp")
        if not timestamp:
            continue
        entry_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        if (now - entry_time).total_seconds() > (window_minutes * 60):
            break

        if current_fingerprint == _problem_fingerprint(entry.get("problem", "")):
            if entry.get("final_status") in ["AUTO_EXECUTED", "EXECUTED"]:
                recent_fixes += 1

    return recent_fixes >= limit


def generate_report():
    data = load_history()
    if not data:
        return {
            "total": 0,
            "accuracy": 0,
            "health": "Unknown",
            "blocked": 0,
            "user_corrections": 0,
        }

    total = len(data)
    successful = len(
        [
            entry
            for entry in data
            if entry.get("final_status")
            in ["EXECUTED", "USER_CORRECTED", "AUTO_EXECUTED"]
        ]
    )
    blocked = len([entry for entry in data if entry.get("final_status") == "BLOCKED"])
    corrected = len([entry for entry in data if entry.get("user_feedback")])
    accuracy = int((successful / total) * 100) if total > 0 else 0
    health = "Stable"
    if blocked > 3:
        health = "Critical (High Security Blocks)"
    return {
        "total": total,
        "accuracy": accuracy,
        "health": health,
        "blocked": blocked,
        "user_corrections": corrected,
    }


def view_history():
    data = load_history()
    if not data:
        console.print("[yellow]No logs found.[/yellow]")
        return
    table = Table(title="Audit Log")
    table.add_column("ID", style="cyan")
    table.add_column("Date")
    table.add_column("Problem")
    table.add_column("Status")
    for idx, entry in enumerate(data[-10:]):
        problem = entry.get("problem", "Unknown")
        table.add_row(
            str(idx),
            entry.get("timestamp", "Unknown"),
            problem[:30] + "...",
            entry.get("final_status", "Unknown"),
        )
    console.print(table)


def enter_teach_mode():
    view_history()
    choice = Prompt.ask("Enter ID to correct (or 'q')", default="q")
    if choice == "q":
        return
    try:
        data = load_history()
        idx = int(choice)
        real_idx = len(data) - 10 + idx if len(data) > 10 else idx
        entry = data[real_idx]

        console.print(
            Panel(
                f"Problem: {entry['problem']}\nCMD: {entry['proposed_fix']}",
                title="Current",
            )
        )
        console.print("1. Fix Command")
        if Prompt.ask("Choose", choices=["1"], default="1") == "1":
            entry["user_feedback"] = Prompt.ask("Enter CORRECT command")
            entry["final_status"] = "USER_CORRECTED"
            atomic_write_json(LOG_FILE, data)
            console.print("[green]Saved![/green]")
    except Exception:
        console.print("[red]Error editing.[/red]")
