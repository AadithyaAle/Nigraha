import getpass
import os

import psutil
from rich.console import Console

import notifier
from app_paths import LOCKDOWN_FILE, SETTINGS_FILE, read_json

console = Console()
WARNED_CACHE = set()


def load_settings():
    """Load process-alert settings.

    Lockdown is intentionally alert-only.  A desktop session contains many
    user-owned helper processes, so terminating unknown user processes can
    end the graphical session and log the user out.
    """
    settings = {"mode": "manual", "whitelist": [], "enable_desktop_notifications": True}
    settings.update(read_json(SETTINGS_FILE, {}))
    if LOCKDOWN_FILE.exists():
        settings["mode"] = "automated"
    return settings


def is_safe_system_process(proc):
    try:
        name = proc.info["name"].lower()
        kernel_prefixes = [
            "kworker",
            "rcu",
            "ksoftirqd",
            "migration",
            "idle_inject",
            "cpuhp",
            "systemd",
            "kthread",
            "irq/",
            "mm_percpu_wq",
            "dbus",
            "wireplumber",
            "pipewire",
            "xorg",
            "wayland",
        ]
        if any(name.startswith(prefix) for prefix in kernel_prefixes):
            return True
        safe_apps = [
            "gnome",
            "snapd",
            "packagekit",
            "polkit",
            "accounts-daemon",
            "code",
            "codex",
        ]
        if any(app in name for app in safe_apps):
            return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
        return True


def check_processes():
    settings = load_settings()
    whitelist = [proc.lower() for proc in settings.get("whitelist", [])]
    mode = settings.get("mode", "manual")
    rogues = []
    current_user = getpass.getuser()
    protected_pids = {os.getpid(), os.getppid()}

    if mode == "manual":
        return []

    for proc in psutil.process_iter(["pid", "name", "username"]):
        try:
            process_name = (proc.info.get("name") or "").lower()
            if not process_name or proc.pid in protected_pids:
                continue
            if proc.info.get("username") != current_user:
                continue
            if process_name in WARNED_CACHE:
                continue
            if process_name in whitelist:
                continue
            if is_safe_system_process(proc):
                continue

            # Alert once per process name; lockdown must not flood desktop
            # notifications every watchdog tick.
            WARNED_CACHE.add(process_name)

            rogues.append(proc)
        except Exception:
            continue
    return rogues


def enforce_rules(rogues):
    """Report unknown processes without modifying the user's system.

    This function used to terminate every non-whitelisted user process while
    in automated mode.  That policy was too broad and could kill session
    components such as a panel, window manager helper, or shell.
    """
    for proc in rogues:
        try:
            process_name = proc.info["name"]
            msg = f"Unknown user process detected: {process_name} (PID {proc.pid})"
            console.print(f"[yellow]⚠️  Process alert:[/yellow] {process_name} (PID {proc.pid})")
            notifier.send_alert("StackSentinel process alert", msg, "normal")
        except Exception:
            pass
