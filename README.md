# 🛡️ StackSentinel

**An autonomous, self-healing Linux infrastructure agent — built with Codex and GPT‑5.6 for OpenAI Build Week.**

StackSentinel watches your system logs, diagnoses Linux problems with an LLM, and can safely repair them in real time — with an audit layer that blocks anything destructive before it ever touches your machine.

---

## 📑 Index

- [Overview](#-overview)
- [Built With Codex & GPT-5.6](#-built-with-codex--gpt-56)
- [Key Features](#-key-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Full CLI Command Reference](#-full-cli-command-reference)
- [Command Safety](#-command-safety)
- [Data Storage](#-data-storage)
- [Notes & Configuration](#-notes--configuration)
- [Uninstallation](#-uninstallation)
- [License](#-license)

---

## 🚀 Overview

System administrators can't watch a terminal 24/7. StackSentinel is a lightweight, locally-run AI watchdog for Linux that:

- Continuously monitors system logs for critical faults
- Diagnoses the root cause using the **OpenAI Responses API**
- Audits every AI-generated fix against a strict safety allowlist
- Executes the fix only if it passes that audit
- Surfaces live status through a local dashboard, with history, snapshots, and rollback built in

It's designed to act as a second pair of eyes on a box that would otherwise fail silently — catching problems like missing directories, broken services, or misconfigured permissions and repairing them before they cascade into an outage.

## 🧠 Built With Codex & GPT-5.6

This project was built for **OpenAI Build Week** using **Codex** as the primary development agent and **GPT‑5.6** as the diagnosis/reasoning model at runtime:

- **Codex** was used to scaffold the CLI command structure, the watchdog daemon loop, the command-auditor safety layer, and the local dashboard — significantly accelerating iteration on the audit/allowlist logic, which needed to be tight and well-tested before any AI-suggested command was allowed to execute.
- **GPT‑5.6**, called through the OpenAI Responses API, is the model StackSentinel talks to at runtime: it receives the raw log line, returns a diagnosis and a proposed shell fix, which is then independently re-checked by the local auditor before execution.
- Key design decisions Codex helped accelerate: separating "diagnosis" (LLM) from "authorization to execute" (deterministic local code), so the model never has unchecked shell access — the model proposes, the auditor disposes.

## ✨ Key Features

- 🧠 **LLM-Powered Diagnosis** — Uses the OpenAI Responses API (GPT‑5.6 by default) to read raw log output and propose a precise, minimal shell fix.
- 🛡️ **Execution Safety Net** — A multi-layered guardrail blocks shell chaining (`&&`, `;`, pipes, redirection), blocks `sudo` execution, blocks destructive patterns (`rm -rf /`, `mkfs`, `dd if=/dev/zero`, `shutdown`, `reboot`), and restricts execution to a small allowlist of known-safe Linux repair commands.
- 🔒 **Command Auditor** — An independent logic layer cross-checks every AI-suggested fix against system security policy before it's allowed to run, regardless of what the model returns.
- ✅ **Human-in-the-loop CLI** — Interactive commands still require explicit confirmation before anything executes.
- 📊 **History, Snapshots & Rollback** — Full audit trail of every command run, plus JSON state snapshots you can restore from and a configurable drift baseline you can audit against.
- 🌐 **Local Dashboard** — A lightweight web UI at `http://127.0.0.1:5000` for live status and lockdown control, no data leaves your machine.
- 🎓 **Training & Teaching Modes** — `--gym` for interactive threat-response practice, `--learn` for an explain-then-fix teaching mode, and `--teach` so you can give the system manual corrections.
- 🔌 **Recovery Hooks** — Simple keyword-triggered recovery scripts (e.g. a Wi-Fi reset hook) for common recurring problems.
- 🔊 **Optional Alerts** — Voice alerts via `espeak` and desktop notifications via `libnotify-bin`.
- 🛟 **Offline-Safe Fallback** — If `OPENAI_API_KEY` isn't set, StackSentinel falls back to a safe offline placeholder response instead of failing.

## ⚠️ Requirements

- Linux
- Python 3.10+
- `pip`
- `espeak` (optional — voice alerts)
- `libnotify-bin` (optional — desktop notifications)
- An `OPENAI_API_KEY` environment variable for live AI diagnosis

## 💻 Installation

**1. Clone the repository**

```bash
git clone https://github.com/AadithyaAle/Nigraha Nigraha
cd Nigraha
```

**2. Run the installer**

```bash
sudo ./install.sh
```

This script:
- Installs system packages via `apt` (including `espeak` and `libnotify-bin`)
- Installs the StackSentinel CLI globally via `pip`
- Marks the bundled recovery hooks as executable

> No manual `venv` setup and no manual `pip install -r requirements.txt` needed for the standard install path.

**3. Set your API key**

```bash
export OPENAI_API_KEY="your_api_key_here"
```

To persist it across sessions, add that line to your shell profile (e.g. `~/.bashrc`).

## 🎮 Quick Start

**Ask for a one-off diagnosis:**

```bash
stacksentinel "wifi keeps disconnecting after resume"
```

**Run in educational mode** (explains the concept before showing the fix):

```bash
stacksentinel --learn "python package install keeps failing"
```

**Start passive log watching** (diagnoses but doesn't execute anything):

```bash
stacksentinel --watch
```

**Start full autonomous watchdog mode** (diagnoses and auto-heals):

```bash
stacksentinel --watchdog
```

**Open the local dashboard:**

```bash
stacksentinel-ui
```

The dashboard stays local at `http://127.0.0.1:5000` — nothing is exposed publicly.

## 🧰 Full CLI Command Reference

| Command | Description |
|---|---|
| `stacksentinel "error"` | Standard mode: manually ask the AI to diagnose a specific error. |
| `stacksentinel --watchdog` | Active defense: continuous monitoring loop with automatic healing. |
| `stacksentinel --watch` | Passive defense: monitors logs and diagnoses without executing fixes. |
| `stacksentinel --learn "error"` | Professor mode: explains the underlying Linux concept before showing the fix. |
| `stacksentinel --gym` | Training: interactive threat-response training simulator. |
| `stacksentinel --teach` | Feedback: provide manual corrections to the AI. |
| `stacksentinel --report` | Analytics: view the AI's success/failure performance score. |
| `stacksentinel --history` | Audit trail: color-coded log of every command executed. |
| `stacksentinel --snapshot` | Backups: create an instant JSON state backup of the system. |
| `stacksentinel --restore` | Rollback: revert to a previous system snapshot. |
| `stacksentinel --set-baseline` | Security: set a known-good configuration baseline. |
| `stacksentinel --audit` | Security: check for unauthorized configuration drift. |
| `stacksentinel-ui` | Launches the local status/control dashboard. |

## 🔒 Command Safety

StackSentinel never blindly trusts model output. Every proposed fix passes through a deterministic auditor before it can run. It blocks:

- Shell chaining and composition — `&&`, `;`, pipes (`|`), and redirection (`>`, `>>`)
- `sudo` execution
- Destructive patterns — `rm -rf /`, `mkfs`, `dd if=/dev/zero`, `shutdown`, `reboot`
- Anything outside a small, explicit allowlist of basic Linux repair commands

Interactive CLI use additionally requires explicit human confirmation before any command executes.

## 🗂️ Data Storage

Runtime data lives outside the repo, at:

```
~/.local/share/stacksentinel/
```

This includes:
- Audit history
- System profile
- Drift baseline
- Restore snapshots
- Local state exported for the dashboard

Temporary live status and lockdown flags are kept in `/tmp`.

## 📝 Notes & Configuration

- If `OPENAI_API_KEY` is missing, StackSentinel falls back to a safe offline placeholder response rather than failing outright.
- The default model is `gpt-5.6-luna`. Override it with the `STACKSENTINEL_MODEL` environment variable.
- The built-in chaos generator writes to the same log location the watchdog reads, so you can safely simulate failures end-to-end.

## 🗑️ Uninstallation

```bash
./uninstall.sh
```

This removes the StackSentinel CLI tools and any installed environment from your system.

License: MIT
*Built for OpenAI Build Week — a project exploring what's possible when Codex and GPT‑5.6 build a self-healing system together.*
