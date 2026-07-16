from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

APP_NAME = "stacksentinel"
REPO_ROOT = Path(__file__).resolve().parent
APP_HOME = Path(
    os.environ.get(
        "STACKSENTINEL_HOME",
        Path.home() / ".local" / "share" / APP_NAME,
    )
).expanduser()
STATE_DIR = APP_HOME / "state"
BACKUP_DIR = APP_HOME / "snapshots"

HISTORY_FILE = APP_HOME / "sentinel_history.json"
SETTINGS_FILE = APP_HOME / "settings.json"
SECRET_FILE = APP_HOME / "secret.json"
PROFILE_FILE = APP_HOME / "system_profile.json"
BASELINE_FILE = APP_HOME / "system_baseline.json"
LATEST_EVENT_FILE = STATE_DIR / "latest_event.json"
DEFAULT_LOG_FILE = APP_HOME / "system_log.txt"

STATUS_FILE = Path("/tmp/stacksentinel_status.json")
LOCKDOWN_FILE = Path("/tmp/stacksentinel_lockdown.mode")
HOOKS_DIR = REPO_ROOT / "hooks"


def ensure_app_dirs() -> None:
    APP_HOME.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def atomic_write_text(path: Path, text: str, mode: int = 0o600) -> None:
    ensure_app_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, mode)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_bytes(path: Path, payload: bytes, mode: int = 0o600) -> None:
    ensure_app_dirs()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        os.chmod(path, mode)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_json(path: Path, data: Any, mode: int = 0o600) -> None:
    atomic_write_text(path, json.dumps(data, indent=4), mode=mode)


def read_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default
