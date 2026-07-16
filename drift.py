import json
import os
import psutil
import platform
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()
BASELINE_FILE = "system_baseline.json"

def get_current_state():
    # Simple audit metrics
    return {
        "kernel": platform.release(),
        "cpu_count": psutil.cpu_count(),
        "total_ram": psutil.virtual_memory().total,
        "disk_used": psutil.disk_usage('/').used,
        # Linux specific package count (approximate)
        "packages": len(os.popen('dpkg --get-selections').read().splitlines()) if platform.system() == "Linux" else 0
    }

def set_baseline():
    state = get_current_state()
    with open(BASELINE_FILE, "w") as f:
        json.dump(state, f, indent=4)
    console.print("[bold green]✅ Baseline Set![/bold green] This system state is now the 'Golden Standard'.")

def run_audit():
    if not os.path.exists(BASELINE_FILE):
        console.print("[yellow]No baseline found. Run --set-baseline first.[/yellow]")
        return

    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)
    
    current = get_current_state()
    issues = []

    table = Table(title="System Drift Audit")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="dim")
    table.add_column("Current", style="bold")
    table.add_column("Status")

    # Check RAM
    ram_gb_base = baseline['total_ram'] // (1024**3)
    ram_gb_curr = current['total_ram'] // (1024**3)
    
    if current['total_ram'] != baseline['total_ram']:
        status = "[red]HARDWARE CHANGE[/red]"
        issues.append("RAM mismatch")
    else:
        status = "[green]OK[/green]"
    table.add_row("Total RAM", f"{ram_gb_base} GB", f"{ram_gb_curr} GB", status)

    # Check Disk Usage
    disk_gb_base = baseline['disk_used'] // (1024**3)
    disk_gb_curr = current['disk_used'] // (1024**3)
    
    diff = current['disk_used'] - baseline['disk_used']
    percent_change = (diff / baseline['disk_used']) * 100 if baseline['disk_used'] > 0 else 0
    
    if percent_change > 10:
        status = f"[yellow]WARNING (+{int(percent_change)}%)[/yellow]"
        issues.append("High Disk Growth")
    else:
        status = "[green]Stable[/green]"
    table.add_row("Disk Usage", f"{disk_gb_base} GB", f"{disk_gb_curr} GB", status)

    # Check Packages
    pkg_diff = current['packages'] - baseline['packages']
    if pkg_diff != 0:
        status = f"[yellow]MODIFIED ({pkg_diff:+d})[/yellow]"
        issues.append("Software Environment Changed")
    else:
        status = "[green]Match[/green]"
    table.add_row("Installed Pkgs", str(baseline['packages']), str(current['packages']), status)

    console.print(table)
    
    if not issues:
        console.print(Panel("✅ [bold green]System is Compliant.[/bold green]", border_style="green"))
    else:
        console.print(Panel(f"⚠️ [bold yellow]Drift Detected:[/bold yellow] {', '.join(issues)}", border_style="yellow"))