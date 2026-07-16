import shutil
import subprocess


def _send_notification(title: str, message: str) -> None:
    if not shutil.which("notify-send"):
        return

    try:
        subprocess.Popen(
            ["notify-send", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def send_alert(title: str, message: str, level: str = "normal") -> None:
    del level
    _send_notification(title, message)


def send_startup_ping() -> None:
    _send_notification("StackSentinel", "Watchdog armed and monitoring.")
