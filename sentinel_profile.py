import os
import platform
import re
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from app_paths import PROFILE_FILE, atomic_write_json, read_json

console = Console()

LOG_FILES = [
    "/var/log/syslog",
    "/var/log/kern.log",
    "/var/log/dmesg",
    "/var/log/Xorg.0.log",
]

PATTERNS = {
    "NVIDIA_CRASH": r"NVRM: API mismatch|nvidia: module verification failed",
    "WIFI_DROP": r"wlan0: deauthenticating|iwlwifi.*Microcode SW error",
    "OOM_KILL": r"Out of memory: Kill process",
    "DISK_ERROR": r"I/O error|EXT4-fs error",
    "OVERHEAT": r"thermal|CPU temperature above threshold",
}


def scan_logs():
    """Reads recent system logs to find recurring patterns."""
    found_issues = []

    console.print("[dim]Reading system logs... (This may take a moment)[/dim]")

    for log_path in LOG_FILES:
        if not os.path.exists(log_path):
            continue

        try:
            result = subprocess.run(
                ["tail", "-n", "2000", log_path],
                capture_output=True,
                text=True,
                check=False,
            )
            log_content = result.stdout

            for issue_name, pattern in PATTERNS.items():
                if re.search(pattern, log_content, re.IGNORECASE):
                    if issue_name not in found_issues:
                        found_issues.append(issue_name)
                        console.print(f"[yellow]Found traces of: {issue_name}[/yellow]")
        except PermissionError:
            console.print(f"[red]Permission denied reading {log_path}. Try running with sudo.[/red]")
        except Exception:
            pass

    return found_issues


def create_profile():
    """Runs the onboarding wizard."""
    console.clear()
    console.rule("[bold cyan]StackSentinel: First Run Setup[/bold cyan]")
    console.print(
        Panel(
            "Welcome! To give you the best advice, I need to learn about this computer's history.\n"
            "I will scan your system logs for past errors (crashes, driver issues, etc).\n"
            "This data stays LOCAL on your machine.",
            title="🤖 Personalization",
            border_style="cyan",
        )
    )

    if not Confirm.ask("Do you want to run the System Health Scan?"):
        console.print("[dim]Skipping setup. I will run in 'Generic Mode'.[/dim]")
        save_profile([], "Generic User")
        return load_profile()

    user_role = "Developer"

    with console.status("[bold green]Analyzing System History...[/bold green]"):
        chronic_issues = scan_logs()

    save_profile(chronic_issues, user_role)

    console.print("\n[bold green]✅ Setup Complete![/bold green]")
    if chronic_issues:
        console.print(
            f"I have noted that this system struggles with: [red]{', '.join(chronic_issues)}[/red]"
        )
        console.print("I will keep this in mind when diagnosing future problems.")
    else:
        console.print("Your system logs look clean. Good job!")

    console.input("\n[dim]Press Enter to start StackSentinel...[/dim]")
    return load_profile()


def save_profile(issues, role):
    data = {
        "user_role": role,
        "chronic_issues": issues,
        "system_specs": platform.uname()._asdict(),
    }
    atomic_write_json(PROFILE_FILE, data)


def load_profile():
    return read_json(PROFILE_FILE, None)
