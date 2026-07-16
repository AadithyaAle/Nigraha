import platform
import shutil
import subprocess

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app_paths import BASELINE_FILE, atomic_write_json, read_json

console = Console()


def _package_count():
    if platform.system() != "Linux":
        return 0
    package_commands = (
        ["dpkg-query", "-f", ".", "-W"],
        ["rpm", "-qa"],
        ["pacman", "-Q"],
    )
    for cmd in package_commands:
        if not shutil.which(cmd[0]):
            continue
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return len(result.stdout.splitlines()) or len(result.stdout)
    return 0


def get_current_state():
    return {
        "kernel": platform.release(),
        "cpu_count": psutil.cpu_count(),
        "total_ram": psutil.virtual_memory().total,
        "disk_used": psutil.disk_usage("/").used,
        "packages": _package_count(),
    }


def set_baseline():
    state = get_current_state()
    atomic_write_json(BASELINE_FILE, state)
    console.print(
        "[bold green]✅ Baseline Set![/bold green] This system state is now the 'Golden Standard'."
    )


def run_audit():
    baseline = read_json(BASELINE_FILE, None)
    if not baseline:
        console.print("[yellow]No baseline found. Run --set-baseline first.[/yellow]")
        return

    current = get_current_state()
    issues = []

    table = Table(title="System Drift Audit")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="dim")
    table.add_column("Current", style="bold")
    table.add_column("Status")

    if current["kernel"] != baseline.get("kernel"):
        status = "[yellow]CHANGED[/yellow]"
        issues.append("Kernel changed")
    else:
        status = "[green]OK[/green]"
    table.add_row("Kernel", baseline.get("kernel", "Unknown"), current["kernel"], status)

    if current["cpu_count"] != baseline.get("cpu_count"):
        status = "[yellow]CHANGED[/yellow]"
        issues.append("CPU count changed")
    else:
        status = "[green]OK[/green]"
    table.add_row(
        "CPU Count",
        str(baseline.get("cpu_count", 0)),
        str(current["cpu_count"]),
        status,
    )

    ram_gb_base = baseline.get("total_ram", 0) // (1024**3)
    ram_gb_curr = current["total_ram"] // (1024**3)
    if current["total_ram"] != baseline.get("total_ram"):
        status = "[red]HARDWARE CHANGE[/red]"
        issues.append("RAM mismatch")
    else:
        status = "[green]OK[/green]"
    table.add_row("Total RAM", f"{ram_gb_base} GB", f"{ram_gb_curr} GB", status)

    disk_gb_base = baseline.get("disk_used", 0) // (1024**3)
    disk_gb_curr = current["disk_used"] // (1024**3)
    diff = current["disk_used"] - baseline.get("disk_used", 0)
    baseline_disk = baseline.get("disk_used", 0)
    percent_change = (diff / baseline_disk) * 100 if baseline_disk > 0 else 0
    if abs(percent_change) > 10:
        status = f"[yellow]WARNING ({percent_change:+.0f}%)[/yellow]"
        issues.append("Disk usage changed materially")
    else:
        status = "[green]Stable[/green]"
    table.add_row("Disk Usage", f"{disk_gb_base} GB", f"{disk_gb_curr} GB", status)

    pkg_diff = current["packages"] - baseline.get("packages", 0)
    if pkg_diff != 0:
        status = f"[yellow]MODIFIED ({pkg_diff:+d})[/yellow]"
        issues.append("Software environment changed")
    else:
        status = "[green]Match[/green]"
    table.add_row(
        "Installed Pkgs",
        str(baseline.get("packages", 0)),
        str(current["packages"]),
        status,
    )

    console.print(table)

    if not issues:
        console.print(Panel("✅ [bold green]System is Compliant.[/bold green]", border_style="green"))
    else:
        console.print(
            Panel(
                f"⚠️ [bold yellow]Drift Detected:[/bold yellow] {', '.join(issues)}",
                border_style="yellow",
            )
        )
