# StackSentinel

StackSentinel is a local Linux troubleshooting assistant. It collects a small
system report, uses the OpenAI Responses API to suggest a safe repair command,
and lets you decide whether to run that command.

It also includes log monitoring, a local dashboard, system snapshots, and a
safe alert-only watchdog mode.

## Features

- Diagnose Linux problems from the terminal
- Review and approve suggested commands before interactive execution
- Display command output and errors after a command finishes
- Monitor StackSentinel's log in passive watch mode
- Use an alert-only watchdog with CPU, RAM, and process notifications
- View live CPU, RAM, status, and recent logs in a local dashboard
- Keep local history, snapshots, system profiles, and drift baselines
- Run simple bundled recovery hooks, such as Wi-Fi recovery

## Requirements

- Linux
- Python 3.10 or newer
- `pip`
- An OpenAI API key for online diagnosis

Optional desktop integrations:

- `espeak` for voice alerts
- `libnotify-bin` for desktop notifications

## Installation

Clone the repository and run the installer:

```bash
git clone https://github.com/AadithyaAle/Nigraha.git
cd Nigraha
sudo ./install.sh
```

The installer installs the required system packages, installs the
`stacksentinel` and `stacksentinel-ui` commands, and makes bundled hooks
executable. A virtual environment is not required for this installation path.

Set your OpenAI API key in the current terminal:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

To keep it across new terminals, add that command to your shell profile, such
as `~/.bashrc` or `~/.zshrc`.

## Usage

Ask StackSentinel to inspect a problem:

```bash
stacksentinel "Bluetooth is not connecting"
```

When a repair command is suggested, StackSentinel audits it and asks for your
approval. After it runs, it displays the command's standard output, error
output, and exit code.

Useful commands:

```bash
stacksentinel --help
stacksentinel --learn "why is my Wi-Fi disconnecting?"
stacksentinel --history
stacksentinel --report
stacksentinel --snapshot
stacksentinel --restore
stacksentinel --audit
stacksentinel --set-baseline
stacksentinel --gym
```

## Monitoring and Dashboard

Start passive log monitoring:

```bash
stacksentinel --watch
```

Start watchdog monitoring:

```bash
stacksentinel --watchdog
```

Watchdog is alert-only. It does not terminate processes, so it will not end
your desktop session. If an internal watchdog error occurs, it displays the
error and automatically falls back to passive log watching.

Start the dashboard:

```bash
stacksentinel-ui
```

Open <http://127.0.0.1:5000> in your browser. The dashboard stays local by
default and shows live CPU/RAM data plus recent StackSentinel log activity.

## Safety

StackSentinel does not run arbitrary model output. Its command audit blocks:

- `sudo` commands
- shell chaining, pipes, redirection, substitutions, and backticks
- destructive commands such as filesystem formatting, rebooting, or deleting
  the root filesystem
- executables outside its allowlist

Interactive diagnoses always require confirmation before a suggested command
runs. Watchdog actions are alert-only.

## Configuration and Data

Set a different OpenAI model if needed:

```bash
export STACKSENTINEL_MODEL="gpt-5.6-luna"
```

Without `OPENAI_API_KEY`, StackSentinel uses a safe offline placeholder
diagnosis instead of contacting the API.

Application data is stored outside the repository:

```text
~/.local/share/stacksentinel/
```

This includes history, profiles, snapshots, and drift data. Temporary
dashboard status files are stored in `/tmp`.

## Updating

From the repository directory:

```bash
git pull
sudo -H python3 -m pip install --force-reinstall --no-deps . --break-system-packages
```

## Uninstall

Run:

```bash
./uninstall.sh
```

This removes the global package. Your local data in
`~/.local/share/stacksentinel/` is kept unless you remove it yourself.

## License

StackSentinel is licensed under the [Apache License 2.0](LICENSE).

