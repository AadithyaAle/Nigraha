import hashlib
import json
import os
import getpass
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
SECRET_FILE = "secret.json"

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def set_password():
    console.print(Panel("🆕 [bold green]First Run: Setup Security[/bold green]\nCreate a password to lock your Sentinel.", border_style="green"))
    while True:
        p1 = getpass.getpass("Enter New Password: ")
        p2 = getpass.getpass("Confirm Password: ")
        if p1 == p2 and p1.strip():
            with open(SECRET_FILE, "w") as f:
                json.dump({"hash": get_password_hash(p1)}, f)
            console.print("[bold green]✅ Password Set![/bold green]")
            return
        console.print("[red]Passwords do not match. Try again.[/red]")

def verify_access():
    if not os.path.exists(SECRET_FILE):
        set_password()
        return True

    with open(SECRET_FILE, "r") as f:
        stored_hash = json.load(f)["hash"]

    console.print("[bold yellow]🔒 Security Check Required[/bold yellow]")
    attempt = getpass.getpass("Enter Admin Password: ")
    
    if get_password_hash(attempt) == stored_hash:
        console.print("[green]🔓 Access Granted[/green]")
        return True
    else:
        console.print("[bold red]⛔ ACCESS DENIED[/bold red]")
        return False