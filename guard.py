import os
import json
import psutil
import subprocess
from rich.console import Console
import notifier

console = Console()
SETTINGS_FILE = "settings.json"
LOCKDOWN_FILE = "lockdown.mode" # <--- The trigger file

# GLOBAL CACHE
WARNED_CACHE = set()

def load_settings():
    """
    Loads settings but OVERRIDES them if Lockdown is active.
    """
    settings = {"mode": "manual", "whitelist": [], "enable_desktop_notifications": True}
    
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)

    # --- THE KILL SWITCH LOGIC ---
    # If the file exists, force mode to "automated" (Hunter-Killer)
    if os.path.exists(LOCKDOWN_FILE):
        settings["mode"] = "automated"
        
    return settings

def is_safe_system_process(proc):
    try:
        name = proc.info['name'].lower()
        kernel_prefixes = [
            "kworker", "rcu", "ksoftirqd", "migration", "idle_inject", 
            "cpuhp", "systemd", "kthread", "irq/", "mm_percpu_wq",
            "dbus", "wireplumber", "pipewire", "xorg", "wayland"
        ]
        if any(name.startswith(k) for k in kernel_prefixes): return True
        safe_apps = ["gnome", "snapd", "packagekit", "polkit", "accounts-daemon"]
        if any(s in name for s in safe_apps): return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True

def check_processes():
    settings = load_settings()
    whitelist = [p.lower() for p in settings.get("whitelist", [])]
    mode = settings.get("mode", "manual")
    rogues = []

    if mode == "manual": return []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            p_name = proc.info['name'].lower()
            if p_name in WARNED_CACHE: continue
            if p_name in whitelist: continue
            if is_safe_system_process(proc): continue
            
            # Note: In Lockdown mode, we don't cache because we want to kill repeatedly
            if mode != "automated":
                WARNED_CACHE.add(p_name)
                
            rogues.append(proc)
        except: continue
    return rogues

def enforce_rules(rogues):
    settings = load_settings()
    mode = settings.get("mode", "manual")
    
    for proc in rogues:
        try:
            p_name = proc.info['name']
            
            if mode == "automated":
                # STRICT MODE: Kill immediately
                if proc.is_running():
                    proc.kill()
                    msg = f"Terminated Hostile Process: {p_name}"
                    console.print(f"[bold red]⚔️  LOCKDOWN KILLED:[/bold red] {p_name}")
                    notifier.send_alert("Lockdown Action", msg, "critical")
                
            elif mode == "intended":
                # BALANCED MODE: Just Alert
                msg = f"Unknown process detected: {p_name}"
                console.print(f"[yellow]⚠️  Suspicious Process:[/yellow] {p_name}")
                # No double alert here, main.py handles it
        except: pass