import getpass
import os

import psutil
from rich.console import Console

import notifier
from app_paths import LOCKDOWN_FILE, SETTINGS_FILE, read_json

console = Console()
WARNED_CACHE = set()


def load_settings():
    """Loads settings and escalates to automated mode when lockdown is active."""
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

            if mode != "automated":
                WARNED_CACHE.add(process_name)

            rogues.append(proc)
        except Exception:
            continue
    return rogues


def enforce_rules(rogues):
    settings = load_settings()
    mode = settings.get("mode", "manual")

    for proc in rogues:
        try:
            process_name = proc.info["name"]

            if mode == "automated":
                if proc.is_running():
                    proc.terminate()
                    msg = f"Terminated Hostile Process: {process_name}"
                    console.print(f"[bold red]⚔️  LOCKDOWN KILLED:[/bold red] {process_name}")
                    notifier.send_alert("Lockdown Action", msg, "critical")

            elif mode == "intended":
                msg = f"Unknown process detected: {process_name}"
                console.print(f"[yellow]⚠️  Suspicious Process:[/yellow] {process_name}")
                notifier.send_alert("Guard Alert", msg, "normal")
        except Exception:
            pass
