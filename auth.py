import base64
import getpass
import hashlib
import hmac
import secrets

from rich.console import Console
from rich.panel import Panel

from app_paths import SECRET_FILE, atomic_write_json, read_json

console = Console()
PBKDF2_ROUNDS = 200_000


def get_password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)


def set_password():
    console.print(
        Panel(
            "🆕 [bold green]First Run: Setup Security[/bold green]\nCreate a password to lock your Sentinel.",
            border_style="green",
        )
    )
    while True:
        p1 = getpass.getpass("Enter New Password: ")
        p2 = getpass.getpass("Confirm Password: ")
        if p1 == p2 and p1.strip():
            salt = secrets.token_bytes(16)
            atomic_write_json(
                SECRET_FILE,
                {
                    "salt": base64.b64encode(salt).decode("utf-8"),
                    "hash": base64.b64encode(get_password_hash(p1, salt)).decode(
                        "utf-8"
                    ),
                },
            )
            console.print("[bold green]✅ Password Set![/bold green]")
            return
        console.print("[red]Passwords do not match. Try again.[/red]")


def verify_access():
    stored = read_json(SECRET_FILE, None)
    if not stored or "salt" not in stored or "hash" not in stored:
        set_password()
        return True

    console.print("[bold yellow]🔒 Security Check Required[/bold yellow]")
    attempt = getpass.getpass("Enter Admin Password: ")
    salt = base64.b64decode(stored["salt"])
    stored_hash = base64.b64decode(stored["hash"])

    if hmac.compare_digest(get_password_hash(attempt, salt), stored_hash):
        console.print("[green]🔓 Access Granted[/green]")
        return True

    console.print("[bold red]⛔ ACCESS DENIED[/bold red]")
    return False
