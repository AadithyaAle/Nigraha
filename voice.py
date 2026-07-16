import subprocess
from rich.console import Console

console = Console()

def speak(text):
    """
    Native Linux text-to-speech using espeak.
    Bypasses pyttsx3 ctypes bugs in Python 3.13.
    """
    try:
        # Runs espeak directly in the background
        subprocess.run(
            ['espeak', '-ven+m3', '-s150', text], # -v is voice type, -s is speed
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        console.print("[dim red]Audio engine missing. Run: sudo apt install espeak[/dim red]")
    except Exception as e:
        pass # Fail silently so it doesn't crash the watchdog