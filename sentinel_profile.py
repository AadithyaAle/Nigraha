import os
import re
import json
import platform
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()
PROFILE_FILE = "system_profile.json"

# Common Linux Log Locations
LOG_FILES = [
    "/var/log/syslog",
    "/var/log/kern.log",
    "/var/log/dmesg",
    "/var/log/Xorg.0.log"
]

# Regex patterns for common "Chronic Issues"
PATTERNS = {
    "NVIDIA_CRASH": r"NVRM: API mismatch|nvidia: module verification failed",
    "WIFI_DROP": r"wlan0: deauthenticating|iwlwifi.*Microcode SW error",
    "OOM_KILL": r"Out of memory: Kill process",
    "DISK_ERROR": r"I/O error|EXT4-fs error",
    "OVERHEAT": r"thermal|CPU temperature above threshold"
}

def scan_logs():
    """
    Reads the last 5000 lines of system logs to find recurring patterns.
    Returns a dictionary of found issues.
    """
    found_issues = []
    
    console.print("[dim]Reading system logs... (This may take a moment)[/dim]")

    for log_path in LOG_FILES:
        if not os.path.exists(log_path):
            continue
            
        try:
            # We use 'tail' to avoid reading massive files entirely
            # Read last 2000 lines
            cmd = ["tail", "-n", "2000", log_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            log_content = result.stdout
            
            for issue_name, pattern in PATTERNS.items():
                if re.search(pattern, log_content, re.IGNORECASE):
                    if issue_name not in found_issues:
                        found_issues.append(issue_name)
                        console.print(f"[yellow]Found traces of: {issue_name}[/yellow]")
        except PermissionError:
            console.print(f"[red]Permission denied reading {log_path}. Try running with sudo.[/red]")
        except Exception as e:
            pass

    return found_issues

def create_profile():
    """
    Runs the onboarding wizard.
    """
    console.clear()
    console.rule("[bold cyan]StackSentinel: First Run Setup[/bold cyan]")
    console.print(Panel(
        "Welcome! To give you the best advice, I need to learn about this computer's history.\n"
        "I will scan your system logs for past errors (crashes, driver issues, etc).\n"
        "This data stays LOCAL on your machine.",
        title="🤖 Personalization",
        border_style="cyan"
    ))

    if not Confirm.ask("Do you want to run the System Health Scan?"):
        console.print("[dim]Skipping setup. I will run in 'Generic Mode'.[/dim]")
        save_profile([], "Generic User")
        return

    # 1. Get User Info
    user_role = "Developer" # Default
    
    # 2. Scan Logs
    with console.status("[bold green]Analyzing System History...[/bold green]"):
        chronic_issues = scan_logs()

    # 3. Save
    save_profile(chronic_issues, user_role)
    
    console.print("\n[bold green]✅ Setup Complete![/bold green]")
    if chronic_issues:
        console.print(f"I have noted that this system struggles with: [red]{', '.join(chronic_issues)}[/red]")
        console.print("I will keep this in mind when diagnosing future problems.")
    else:
        console.print("Your system logs look clean. Good job!")
    
    console.input("\n[dim]Press Enter to start StackSentinel...[/dim]")

def save_profile(issues, role):
    data = {
        "user_role": role,
        "chronic_issues": issues,
        "system_specs": platform.uname()._asdict()
    }
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return None
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)