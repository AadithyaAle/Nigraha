# StackSentinel

StackSentinel is a local Linux repair assistant that watches logs, suggests safe shell fixes, and can optionally auto-respond to recurring problems. It now uses the OpenAI Responses API for diagnosis.

## What It Does

- Monitors a log file in watch or watchdog mode
- Diagnoses Linux issues with OpenAI
- Audits generated commands before they can run
- Stores history, snapshots, drift baselines, and profile data outside the repo
- Offers a lightweight local dashboard for status and lockdown control
- Supports simple keyword-based recovery hooks such as Wi-Fi reset scripts

## Requirements

- Linux
- Python 3.10+
- `pip`
- `espeak` for optional voice alerts
- An `OPENAI_API_KEY` environment variable for live AI diagnosis

## Install

Clone the repo and run:

```bash
git clone <your-repo-url> NIgraha
cd NIgraha
sudo ./install.sh
```

That script:

- installs system packages with `apt`
- installs StackSentinel globally with `pip`
- marks the bundled hooks executable

You do not need to manually create a `venv`, and you do not need to run `pip install -r requirements.txt` yourself for the normal install path.

Then set your API key:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

If you want that to persist, add it to your shell profile such as `~/.bashrc`.

## Quick Start

Ask for a diagnosis:

```bash
stacksentinel "wifi keeps disconnecting after resume"
```

Run in educational mode:

```bash
stacksentinel --learn "python package install keeps failing"
```

Start passive log watching:

```bash
stacksentinel --watch
```

Start full watchdog mode:

```bash
stacksentinel --watchdog
```

Open the local dashboard:

```bash
stacksentinel-ui
```

By default the dashboard stays local at `http://127.0.0.1:5000`.

## Command Safety

StackSentinel does not blindly trust model output. It blocks:

- shell chaining such as `&&`, `;`, pipes, and redirection
- `sudo` execution
- destructive patterns such as `rm -rf /`, `mkfs`, `dd if=/dev/zero`, `shutdown`, and `reboot`
- commands outside a small allowlist used for basic Linux repair tasks

For interactive CLI use, commands still require confirmation before they run.

## Data Storage

Runtime data is stored in:

```text
~/.local/share/stacksentinel/
```

That includes:

- audit history
- system profile
- drift baseline
- restore snapshots
- local state exported for the dashboard

Temporary live status and lockdown flags are kept in `/tmp`.

## Common Commands

```bash
stacksentinel --history
stacksentinel --report
stacksentinel --teach
stacksentinel --snapshot
stacksentinel --restore
stacksentinel --set-baseline
stacksentinel --audit
stacksentinel --gym
```

## Notes

- If `OPENAI_API_KEY` is missing, StackSentinel falls back to a safe offline placeholder response.
- The default model is `gpt-5.6-luna`. You can override it with `STACKSENTINEL_MODEL`.
- The built-in chaos generator writes to the same log location the watchdog reads.

## Uninstall

```bash
./uninstall.sh
```
