import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

import psutil
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

import auth
import brain
import cloud
import diagnose
import drift
import guard
import history
import hooks_engine
import notifier
import sentinel_profile as profiler
import snapshot
import voice
from app_paths import (
    DEFAULT_LOG_FILE,
    LOCKDOWN_FILE,
    STATUS_FILE,
    atomic_write_json,
    ensure_app_dirs,
)

console = Console()


def extract_commands(text):
    commands = {}
    backup_match = re.search(
        r"\*\*Backup Command:\*\*\s*```bash\s+(.*?)\s+```", text, re.DOTALL
    )
    if backup_match:
        commands["backup"] = backup_match.group(1).strip()

    fix_match = re.search(r"(?:Suggested Fix:|Fix:).*?```bash\s+(.*?)\s+```", text, re.DOTALL)
    if fix_match:
        commands["fix"] = fix_match.group(1).strip()
    elif "```bash" in text:
        all_matches = re.findall(r"```bash\s+(.*?)\s+```", text, re.DOTALL)
        if all_matches:
            commands["fix"] = all_matches[-1].strip()
    return commands


def broadcast_status(status, cpu, ram, last_log):
    try:
        atomic_write_json(
            STATUS_FILE,
            {
                "cpu": cpu,
                "ram": ram,
                "status": status,
                "last_log": last_log[:150],
            },
            mode=0o600,
        )
    except Exception:
        pass


def ensure_log_file(log_file):
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("--- Watchdog Log Started ---\n", encoding="utf-8")
    return path


def cleanup_status_file():
    if STATUS_FILE.exists():
        STATUS_FILE.unlink()


def start_watchdog_with_fallback(log_file=str(DEFAULT_LOG_FILE)):
    """Run watchdog and fall back to passive watching after an internal error.

    A watchdog failure must never leave the terminal full of a Python traceback
    or encourage the user to force-stop it.  The fallback performs no process
    actions and keeps the recent log visible.
    """
    try:
        start_watchdog_mode(log_file)
    except KeyboardInterrupt:
        cleanup_status_file()
        console.print("\n[yellow]Watchdog disarmed by user.[/yellow]")
    except Exception as exc:
        error_summary = f"{type(exc).__name__}: {exc}"
        broadcast_status("SAFE FALLBACK", 0, 0, error_summary)
        console.print(
            Panel(
                "Watchdog encountered an internal error and has been switched "
                "to passive log watching. No processes were stopped.\n\n"
                f"[bold]Error:[/bold] {error_summary}",
                title="Watchdog safe fallback",
                border_style="yellow",
            )
        )
        try:
            start_watch_mode(log_file)
        except KeyboardInterrupt:
            cleanup_status_file()
            console.print("\n[yellow]Passive watch stopped by user.[/yellow]")
        except Exception as fallback_error:
            fallback_summary = f"{type(fallback_error).__name__}: {fallback_error}"
            broadcast_status("STOPPED", 0, 0, fallback_summary)
            console.print(
                Panel(
                    f"Passive watch could not start.\n\n[bold]Error:[/bold] {fallback_summary}",
                    title="Watchdog stopped safely",
                    border_style="red",
                )
            )


def run_fix_command(command):
    result = subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    return result


def show_command_result(result):
    """Show captured stdout/stderr after a command has completed."""
    sections = []
    if result.stdout.strip():
        sections.append(f"STDOUT\n{result.stdout.strip()}")
    if result.stderr.strip():
        sections.append(f"STDERR\n{result.stderr.strip()}")

    output = "\n\n".join(sections) or "Command completed successfully with no terminal output."
    max_output_length = 6000
    if len(output) > max_output_length:
        output = (
            f"… output shortened; showing the last {max_output_length} characters …\n\n"
            f"{output[-max_output_length:]}"
        )

    succeeded = result.returncode == 0
    console.print(
        Panel(
            Text(output),
            title=(
                f"Command completed (exit code {result.returncode})"
                if succeeded
                else f"Command failed (exit code {result.returncode})"
            ),
            border_style="green" if succeeded else "red",
        )
    )


def start_watchdog_mode(log_file=str(DEFAULT_LOG_FILE)):
    ensure_app_dirs()
    console.clear()
    console.rule("[bold red]🛡️ StackSentinel WATCHDOG PROTOCOL: ACTIVE[/bold red]")
    console.print(
        Panel(
            "I am guarding your system while you are away.\n"
            "Monitoring: [cyan]Logs[/cyan] | [cyan]CPU/RAM[/cyan] | [cyan]Process Guard[/cyan]\n"
            "Status: [bold green]ARMED[/bold green]",
            title="AFK Protection",
            border_style="red",
        )
    )

    log_path = ensure_log_file(log_file)
    notifier.send_startup_ping()
    voice.speak("Watchdog protocol initiated. System armed.")

    last_processed_line = ""
    tick_counter = 0
    was_locked = False
    current_ai_log = "Monitoring system logs..."

    with Live(refresh_per_second=1) as live:
        with open(log_path, "r", encoding="utf-8") as handle:
            handle.seek(0, os.SEEK_END)
            while True:
                current_cpu = psutil.cpu_percent(interval=None)
                current_ram = psutil.virtual_memory().percent
                is_locked = LOCKDOWN_FILE.exists()

                if is_locked and not was_locked:
                    voice.speak("Lockdown protocol engaged. Alerts are elevated.")
                    console.print("[bold red]🔒 LOCKDOWN ACTIVATED: alert-only mode[/bold red]")
                    notifier.send_alert(
                        "System Status",
                        "Lockdown engaged. StackSentinel will alert but will not terminate processes.",
                        "critical",
                    )
                elif not is_locked and was_locked:
                    voice.speak("Lockdown disengaged. Returning to standard watch.")
                    console.print("[green]🔓 Lockdown lifted.[/green]")
                    notifier.send_alert("System Status", "Lockdown disengaged.", "normal")

                was_locked = is_locked

                table = Table(title="System Vitals")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("CPU Usage", f"{current_cpu}%")
                table.add_row("RAM Usage", f"{current_ram}%")
                table.add_row(
                    "Mode",
                    "[bold red]🔒 LOCKDOWN[/bold red]" if is_locked else "[green]Standard[/green]",
                )
                status = "[green]NORMAL[/green]"
                if current_cpu > 90:
                    status = "[red]HIGH LOAD[/red]"
                table.add_row("Status", status)
                live.update(table)

                check_freq = 1 if is_locked else 5
                if tick_counter % check_freq == 0:
                    rogues = guard.check_processes()
                    if rogues:
                        guard.enforce_rules(rogues)

                if tick_counter % 2 == 0:
                    status_text = "🔒 LOCKDOWN" if is_locked else "ARMED"
                    broadcast_status(status_text, current_cpu, current_ram, current_ai_log)

                line = handle.readline()
                if line and ("ERROR" in line or "CRITICAL" in line):
                    stripped = line.strip()
                    if stripped == last_processed_line:
                        time.sleep(0.1)
                        continue

                    last_processed_line = stripped
                    current_ai_log = stripped
                    live.stop()

                    if history.is_system_looping(stripped):
                        msg = "Circuit breaker triggered."
                        console.print(Panel(f"[bold red]🛑 {msg}[/bold red]", border_style="red"))
                        voice.speak(msg)
                        notifier.send_alert("Circuit Breaker", msg, "critical")
                        current_ai_log = "HALTED: Circuit breaker active"
                        broadcast_status("HALTED", current_cpu, current_ram, current_ai_log)
                        input("Press Enter to reset...")
                        live.start()
                        continue

                    broadcast_status("CRITICAL ALERT", current_cpu, current_ram, current_ai_log)
                    notifier.send_alert("StackSentinel Alert", stripped, "critical")
                    voice.speak("Critical alert. Error detected.")
                    console.print(
                        Panel(
                            f"[bold red]🚨 THREAT DETECTED:[/bold red] {stripped}",
                            border_style="red",
                        )
                    )

                    console.print("[yellow]🧠 Consulting OpenAI diagnosis...[/yellow]")
                    sys_ctx = diagnose.get_system_report()
                    solution = brain.ask_openai(sys_ctx, f"CRITICAL: {stripped}")
                    cmds = extract_commands(solution)
                    fix = cmds.get("fix")

                    if fix and brain.audit_command(fix) == "SAFE":
                        console.print("[bold green]✅ Auto-fixing...[/bold green]")
                        try:
                            result = run_fix_command(fix)
                            if result.returncode == 0:
                                console.print(f"[bold cyan]Command Executed: {fix}[/bold cyan]")
                                show_command_result(result)
                                history_status = "AUTO_EXECUTED"
                                current_ai_log = f"✅ FIXED: {fix}"
                            else:
                                show_command_result(result)
                                history_status = "FAILED"
                                current_ai_log = f"❌ FAILED: {fix}"
                        except subprocess.TimeoutExpired:
                            console.print(
                                "[bold red]Execution aborted: command took too long or asked for input.[/bold red]"
                            )
                            history_status = "TIMEOUT"
                            current_ai_log = "❌ FAILED: Command timed out."

                        history.save_event(
                            f"AFK: {stripped}",
                            solution,
                            fix,
                            cmds.get("backup"),
                            "SAFE",
                            history_status,
                        )
                    else:
                        console.print("[bold red]🛑 Dangerous fix blocked.[/bold red]")
                        voice.speak("Fix blocked by safety protocols.")
                        history.save_event(
                            f"AFK: {stripped}",
                            solution,
                            fix,
                            cmds.get("backup"),
                            "BLOCKED",
                            "BLOCKED",
                        )
                        current_ai_log = "🛑 BLOCKED: Unsafe command detected."

                    time.sleep(2)
                    live.start()

                time.sleep(1.0)
                tick_counter += 1


def start_watch_mode(log_file=str(DEFAULT_LOG_FILE)):
    ensure_app_dirs()
    console.clear()
    console.rule("[bold blue]StackSentinel: WATCH MODE ACTIVE[/bold blue]")
    log_path = ensure_log_file(log_file)
    with open(log_path, "r", encoding="utf-8") as handle:
        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                console.print(f"[dim]{line.strip()}[/dim]")
            time.sleep(0.5)


def cli_entry_point():
    parser = argparse.ArgumentParser()
    parser.add_argument("problem", type=str, nargs="?", help="Describe your problem")
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--learn", action="store_true", help="Enable educational mode")
    parser.add_argument("--history", action="store_true", help="View audit logs")
    parser.add_argument("--gym", action="store_true", help="Enter training simulator")
    parser.add_argument("--watch", action="store_true", help="Monitor logs")
    parser.add_argument("--watchdog", action="store_true", help="AFK protection mode")
    parser.add_argument("--report", action="store_true", help="Show performance score")
    parser.add_argument("--teach", action="store_true", help="Correct AI mistakes")
    parser.add_argument("--snapshot", action="store_true", help="Create restore point")
    parser.add_argument("--restore", action="store_true", help="Restore from snapshot")
    parser.add_argument("--audit", action="store_true", help="Check for system drift")
    parser.add_argument("--set-baseline", action="store_true", help="Set drift baseline")
    args = parser.parse_args()

    if args.image:
        console.print("[yellow]Image diagnosis is not implemented yet.[/yellow]")

    if args.watchdog or args.teach or args.history or args.report or args.restore or args.set_baseline:
        if not auth.verify_access():
            return

    if args.snapshot:
        note = Prompt.ask("Enter a note", default="Manual Backup")
        snapshot.create_snapshot(note)
        return

    if args.restore:
        backups = snapshot.list_snapshots()
        if not backups:
            return
        table = Table(title="Restore Points")
        table.add_column("ID", style="cyan")
        table.add_column("File")
        table.add_column("Note")
        for idx, backup in enumerate(backups):
            table.add_row(str(idx), backup["file"], backup["note"])
        console.print(table)
        choice = Prompt.ask("ID to restore (or 'q')", default="q")
        if choice == "q":
            return
        try:
            snapshot.restore_snapshot(backups[int(choice)]["file"])
        except Exception:
            console.print("[red]Invalid ID[/red]")
        return

    if args.watchdog:
        start_watchdog_with_fallback()
        return
    if args.watch:
        start_watch_mode()
        return
    if args.report:
        console.print(history.generate_report())
        return
    if args.teach:
        history.enter_teach_mode()
        return
    if args.gym:
        import gym

        gym.start_gym()
        return
    if args.history:
        history.view_history()
        return
    if args.set_baseline:
        drift.set_baseline()
        return
    if args.audit:
        drift.run_audit()
        return

    if not args.problem:
        console.print("[red]Please provide a problem or flag.[/red]")
        return

    hook_result = hooks_engine.check_and_run_hooks(args.problem)
    if hook_result.get("executed"):
        if hook_result.get("success") and Confirm.ask("Did that hook fix it?", default=True):
            history.save_event(
                args.problem,
                f"Hook executed: {hook_result.get('script')}",
                hook_result.get("script"),
                None,
                "SAFE",
                "HOOK_EXECUTED",
            )
            return
        console.print("[yellow]Continuing with AI diagnosis.[/yellow]")

    profile = profiler.load_profile() or profiler.create_profile()
    last = history.check_recurrence(args.problem)
    if last and last.get("user_feedback") and Confirm.ask(
        f"Use trusted fix: {last['user_feedback']}?", default=True
    ):
        audit = brain.audit_command(last["user_feedback"])
        if audit == "SAFE":
            result = run_fix_command(last["user_feedback"])
            status = "EXECUTED" if result.returncode == 0 else "FAILED"
            history.save_event(
                args.problem,
                "Trusted fix reused from history.",
                last["user_feedback"],
                None,
                "SAFE",
                status,
            )
            show_command_result(result)
            return
        console.print(f"[red]{audit}[/red]")

    with console.status("[bold purple]Consulting OpenAI diagnosis...[/bold purple]"):
        ctx = diagnose.get_system_report()
        sol = brain.ask_openai(ctx, args.problem, learning_mode=args.learn, user_profile=profile)

    if args.learn:
        console.print(Panel(Markdown(sol), title="Professor Mode"))
        if not Confirm.ask("Show direct fix recommendation?", default=True):
            history.save_event(args.problem, sol, None, None, "N/A", "LEARN_ONLY")
            return
        sol = brain.ask_openai(ctx, args.problem, learning_mode=False, user_profile=profile)

    console.print(Panel(Markdown(sol), title="Diagnosis"))
    cmds = extract_commands(sol)
    status = "NO_ACTION"
    auditor = "N/A"

    if cmds.get("fix"):
        audit = brain.audit_command(cmds["fix"])
        auditor = "SAFE" if audit == "SAFE" else "WARNING"
        if auditor == "SAFE":
            console.print("[bold green]✅ Auditor approved[/bold green]")
            if Confirm.ask("Run this plan?", default=False):
                if cmds.get("backup"):
                    console.print(f"[blue]Backup command available:[/blue] {cmds['backup']}")
                try:
                    result = run_fix_command(cmds["fix"])
                    if result.returncode == 0:
                        show_command_result(result)
                        status = "EXECUTED"
                    else:
                        show_command_result(result)
                        status = "FAILED"
                except subprocess.TimeoutExpired:
                    console.print(
                        "[bold red]Execution aborted: command took too long or asked for input.[/bold red]"
                    )
                    status = "TIMEOUT"
            else:
                status = "SKIPPED"
        else:
            console.print(Panel(f"[bold red]BLOCKED[/bold red] {audit}", border_style="red"))
            status = "BLOCKED"

    history.save_event(args.problem, sol, cmds.get("fix"), cmds.get("backup"), auditor, status)
    with console.status("[bold blue]Saving latest event...[/bold blue]"):
        cloud.push_to_cloud()


if __name__ == "__main__":
    try:
        cli_entry_point()
    except KeyboardInterrupt:
        print("\n🛑 StackSentinel disarmed. Shutting down gracefully...")
        cleanup_status_file()
        sys.exit(0)
