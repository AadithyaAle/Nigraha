import json
import os
import shlex

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from rich.console import Console

console = Console()
DEFAULT_MODEL = os.environ.get("STACKSENTINEL_MODEL", "gpt-5.6-luna")
ALLOWED_COMMANDS = {
    "apt",
    "apt-get",
    "chmod",
    "chown",
    "cp",
    "git",
    "journalctl",
    "ls",
    "mkdir",
    "modprobe",
    "mv",
    "nmcli",
    "pip",
    "pip3",
    "python3",
    "sed",
    "systemctl",
    "touch",
    "ufw",
}
BLOCKED_SNIPPETS = (
    "rm -rf /",
    "mkfs",
    "dd if=/dev/zero",
    ":(){",
    "shutdown",
    "reboot",
    "poweroff",
    "chmod 777",
)


def ask_openai(system_context, user_problem, learning_mode=False, user_profile=None):
    """Calls the OpenAI Responses API with a compact Linux-fix prompt."""
    if OpenAI is None:
        console.print(
            "[dim yellow]The OpenAI package is not installed yet. Using offline fallback mode.[/dim yellow]"
        )
        return _mock_fallback(user_problem, learning_mode=learning_mode)

    if not os.environ.get("OPENAI_API_KEY"):
        console.print(
            "[dim yellow]OPENAI_API_KEY is not set. Using offline fallback mode.[/dim yellow]"
        )
        return _mock_fallback(user_problem, learning_mode=learning_mode)

    try:
        client = OpenAI()
        system_prompt = (
            "You are StackSentinel, a Linux repair assistant. "
            "Keep replies short, practical, and safe. "
            "Always return a brief explanation, one primary fix in a ```bash``` block, "
            "and an optional backup command in a separate ```bash``` block only when useful. "
            "Never suggest destructive commands, interactive prompts, or commands that need multiple shell operators."
        )
        system_prompt += f"\n\nSystem context:\n{json.dumps(system_context)}"
        if user_profile:
            system_prompt += f"\n\nUser profile:\n{json.dumps(user_profile)}"

        if learning_mode:
            system_prompt += (
                "\n\nEducational mode is enabled. Explain the reasoning slightly more clearly, "
                "but keep the command output format exactly the same."
            )

        response = client.responses.create(
            model=DEFAULT_MODEL,
            max_output_tokens=500,
            reasoning={"effort": "low"},
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_problem}],
                },
            ],
        )
        return response.output_text or _mock_fallback(
            user_problem, learning_mode=learning_mode
        )
    except Exception as exc:
        console.print(
            f"[dim red]⚠️ AI connection failed: {exc}. Using offline mode.[/dim red]"
        )
        return _mock_fallback(user_problem, learning_mode=learning_mode)


def _mock_fallback(problem, learning_mode=False):
    """Failsafe so the tool stays usable when no API key or network is available."""
    problem_lower = problem.lower()
    if "wifi" in problem_lower:
        prefix = "Offline educational diagnosis" if learning_mode else "Offline diagnosis"
        return (
            f"{prefix}: the Wi-Fi interface appears to be unavailable.\n\n"
            "Suggested Fix:\n```bash\nnmcli radio wifi on\n```"
        )
    return (
        "Offline diagnosis: I could not reach the API, so I am returning a safe placeholder.\n\n"
        "Suggested Fix:\n```bash\njournalctl -p err -n 50\n```"
    )


def audit_command(command):
    """A narrow allowlist for command execution."""
    command = (command or "").strip()
    lowered = command.lower()
    if not command:
        return "BLOCKED: Empty command"

    for snippet in BLOCKED_SNIPPETS:
        if snippet in lowered:
            return f"BLOCKED: Dangerous command detected ({snippet})"

    if any(token in command for token in ("&&", "||", ";", "|", ">", "<", "`", "$(")):
        return "BLOCKED: Shell chaining and redirection are not allowed"

    try:
        parts = shlex.split(command)
    except ValueError:
        return "BLOCKED: Command could not be parsed safely"

    if not parts:
        return "BLOCKED: Empty command"

    executable = parts[0].lower()
    if executable == "sudo":
        return "BLOCKED: sudo commands are not auto-approved"
    if executable not in ALLOWED_COMMANDS:
        return f"BLOCKED: Command '{executable}' is outside the safe allowlist"

    return "SAFE"
