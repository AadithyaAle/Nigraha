import json
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

LOG_FILE = "sentinel_history.json"
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
        "user_feedback": None 
    }
    history = load_history()
    history.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=4)

def load_history():
    if not os.path.exists(LOG_FILE):
        return []
    
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        # EDGE CASE: Corrupted History File
        console.print("[bold red]⚠️  Warning: History file is corrupted.[/bold red]")
        backup_name = LOG_FILE + ".corrupted"
        os.rename(LOG_FILE, backup_name)
        console.print(f"[dim]Moved corrupted file to {backup_name}. Starting fresh.[/dim]")
        return []

def check_recurrence(current_problem):
    data = load_history()
    for entry in reversed(data):
        words_a = set(current_problem.lower().split())
        words_b = set(entry["problem"].lower().split())
        if len(words_a) == 0: continue
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

    for entry in reversed(data):
        entry_time = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
        if (now - entry_time).total_seconds() > (window_minutes * 60):
            break
        
        # Check if it's the same problem and we tried to fix it
        if problem.lower()[:20] in entry["problem"].lower():
            if entry["final_status"] in ["AUTO_EXECUTED", "EXECUTED"]:
                recent_fixes += 1

    return recent_fixes >= limit

def generate_report():
    data = load_history()
    if not data: return {"total": 0, "accuracy": 0, "health": "Unknown", "blocked": 0, "user_corrections": 0}
    
    total = len(data)
    successful = len([e for e in data if e["final_status"] in ["EXECUTED", "USER_CORRECTED", "AUTO_EXECUTED"]])
    blocked = len([e for e in data if e["final_status"] == "BLOCKED"])
    corrected = len([e for e in data if e.get("user_feedback")])
    accuracy = int((successful / total) * 100) if total > 0 else 0
    health = "Stable"
    if blocked > 3: health = "Critical (High Security Blocks)"
    return {"total": total, "accuracy": accuracy, "health": health, "blocked": blocked, "user_corrections": corrected}

def view_history():
    data = load_history()
    if not data:
        console.print("[yellow]No logs found.[/yellow]")
        return
    table = Table(title="Audit Log")
    table.add_column("ID", style="cyan"); table.add_column("Date"); table.add_column("Problem"); table.add_column("Status")
    for idx, entry in enumerate(data[-10:]):
        table.add_row(str(idx), entry["timestamp"], entry["problem"][:30]+"...", entry["final_status"])
    console.print(table)

def enter_teach_mode():
    view_history()
    choice = Prompt.ask("Enter ID to correct (or 'q')", default="q")
    if choice == 'q': return
    try:
        data = load_history()
        # Adjust index logic for robustness
        idx = int(choice)
        real_idx = len(data) - 10 + idx if len(data) > 10 else idx
        entry = data[real_idx]
        
        console.print(Panel(f"Problem: {entry['problem']}\nCMD: {entry['proposed_fix']}", title="Current"))
        console.print("1. Fix Command\n2. Fix Description")
        if Prompt.ask("Choose") == "1":
            entry["user_feedback"] = Prompt.ask("Enter CORRECT command")
            entry["final_status"] = "USER_CORRECTED"
            with open(LOG_FILE, "w") as f: json.dump(data, f, indent=4)
            console.print("[green]Saved![/green]")
    except:
        console.print("[red]Error editing.[/red]")