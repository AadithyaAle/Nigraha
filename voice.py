import subprocess

from rich.console import Console

console = Console()


def speak(text):
    """
    Native Linux text-to-speech using espeak.
    Bypasses pyttsx3 ctypes bugs in Python 3.13.
    """
    try:
        subprocess.Popen(
            ["espeak", "-ven+m3", "-s150", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        console.print("[dim red]Audio engine missing. Run: sudo apt install espeak[/dim red]")
    except Exception:
        pass
