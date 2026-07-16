# 🛡️ StackSentinel

**An Autonomous, Self-Healing Linux Infrastructure Agent powered by Amazon Nova.**

## 📑 Index

1. [Overview](https://www.google.com/search?q=%23-overview)
2. [Key Features](https://www.google.com/search?q=%23-key-features)
3. [Installation & Setup](https://www.google.com/search?q=%23-installation--setup)
4. [Usage Guide](https://www.google.com/search?q=%23-usage-guide)
5. [Full CLI Command Reference](https://www.google.com/search?q=%23-full-cli-command-reference)
6. [Teardown & Uninstallation](https://www.google.com/search?q=%23-teardown--uninstallation)
7. [License](https://www.google.com/search?q=%23-license)

## 🚀 Overview

System administrators cannot monitor terminal outputs 24/7. **StackSentinel** is a lightweight, edge-deployed AI watchdog that actively monitors Linux system logs, diagnoses critical hardware and software faults in real-time, and securely executes autonomous bash commands to heal the system before a total crash occurs.

Coupled with a mobile-responsive Command and Control (C2) dashboard, admins get live system telemetry and remote lockdown capabilities right from their phones.

## ✨ Key Features

* **🧠 LLM-Powered Remediation:** Integrates with AWS Bedrock (Amazon Nova) to diagnose raw system logs and generate precise bash fixes.
* **🛡️ Execution Safety Net:** A multi-layered guardrail system that intercepts AI-generated scripts to block destructive commands (like `rm -rf` or `mkfs`) and enforces 15-second execution timeouts.
* **🔒 Command Auditor:** An additional logic layer that cross-references suggested fixes against system security policies.
* **⚡ Crash-Proof IPC:** Engineered with atomic JSON file writes and global `0o666` permissions to ensure seamless communication between the Root Watchdog and the User-level C2 Dashboard.
* **🌐 Auto-Tunneling C2:** Integrated `pyngrok` support that automatically generates a public URL for your dashboard on startup.

## 💻 Installation & Setup

Developed and stress-tested on Ubuntu Linux. We provide an automated installation script that sets up the Python virtual environment and installs the StackSentinel global CLI tools.

**1. Clone & Navigate**

```bash
git clone https://github.com/AadithyaAle/StackSentinel.git
cd StackSentinel

```

**2. Run the Installer**

```bash
chmod +x install.sh uninstall.sh
./install.sh

```

**3. AWS Authentication**
Ensure you are logged into your secure AWS profile:

```bash
aws sso login --profile Stack-Sentinel

```

**4. Ngrok Authentication (For the Web UI)**
To use the automated public dashboard tunnel, you must link your free Ngrok account:

```bash
ngrok config add-authtoken YOUR_NGROK_TOKEN

```

## 🎮 Usage Guide

Thanks to the automated CLI setup, you can run StackSentinel from **any** terminal directory on your machine.

> [!IMPORTANT]
> **Environment Preservation:** To allow the AI to fix system-level issues while maintaining access to your AWS credentials, you must use the `-E` flag with `sudo`.

**Step 1: Start the Web Dashboard**
Open any terminal and run:

```bash
stacksentinel-ui

```

*The public Ngrok URL will be printed directly in your terminal so you can open it on your phone.*

**Mode A: Autonomous Healing (Recommended)**
To allow the AI to fix system-level issues while maintaining access to your AWS credentials, use the `-E` flag. This preserves your environment variables so the AI can "think" while having the power to "act."

```bash
sudo -E stacksentinel --watchdog

```

**Mode B: Standard/Read-Only Mode**
If you prefer not to grant root access, you can run the agent as a standard user.
*Note: The AI will still diagnose errors, but it may fail to execute fixes that require administrative permissions (like restarting services).*

```bash
stacksentinel --watchdog

```

**Step 3: Test the Auto-Healing (Simulation)**
To safely test the AI's execution capabilities, open a third terminal and inject a harmless missing-directory error into the log file: 

```bash
echo "CRITICAL: Backup service failed." >> /tmp/stacksentinel_dummy_log.txt

```

Watch your terminal or phone dashboard as the AI intercepts the log, consults Amazon Nova, audits the `mkdir` command for safety, and physically creates the directory on your machine. 

## 🧰 Full CLI Command Reference

StackSentinel is highly modular. You can use it as a passive monitor, an active guardian, or an interactive educational tool. 

| Command | Description |
| --- | --- |
| `stacksentinel "error"` | **Standard Mode:** Manually ask the AI to diagnose a specific error. |
| `sudo -E stacksentinel --watchdog` | **Active Defense:** Runs the continuous AFK protection and auto-healing loop. |
| `stacksentinel --watch` | **Passive Defense:** Monitors logs without executing fixes. |
| `stacksentinel --gym` | **Training:** Enter the interactive threat-response training simulator. |
| `stacksentinel --learn "error"` | **Professor Mode:** Explains Linux concepts before showing the fix. |
| `stacksentinel --teach` | **Feedback:** Provide manual corrections to the AI. |
| `stacksentinel --report` | **Analytics:** View the AI's success/failure performance score. |
| `stacksentinel --history` | **Audit Trail:** View a color-coded log of every command executed. |
| `stacksentinel --snapshot` | **Backups:** Create an instant JSON state backup of the system. |
| `stacksentinel --restore` | **Rollback:** Revert to a previous system snapshot. |
| `stacksentinel --set-baseline` | **Security:** Set a known-good configuration baseline. |
| `stacksentinel --audit` | **Security:** Check for unauthorized configuration drift. |

## 🗑️ Teardown & Uninstallation

To completely remove the StackSentinel CLI tools and isolated virtual environment from your system, simply run the included uninstaller: 

```bash
./uninstall.sh

```

 ## 🤝 Open Source


This project explores the intersection of AI inference and low-level systems engineering.


---

**License:** MIT




