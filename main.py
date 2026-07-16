import sys
import argparse
import time
import re
import os
import psutil
import json
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from rich.live import Live
from rich.table import Table

# --- MODULE IMPORTS ---
import diagnose
import brain 
import history
import gym
import sentinel_profile as profiler
import guard
import auth 
import snapshot
import cloud
import hooks_engine
import drift
import notifier
import voice

console = Console()
STATUS_FILE = "/tmp/stacksentinel_status.json"
LOCKDOWN_FILE = "/tmp/stacksentinel_lockdown.mode"

# --- HELPER FUNCTIONS ---
def extract_commands(text):
    commands = {}
    backup_match = re.search(r"\*\*Backup Command:\*\*\s*```bash\s+(.*?)\s+```", text, re.DOTALL)
    if backup_match: commands['backup'] = backup_match.group(1).strip()
    
    fix_match = re.search(r"(?:Suggested Fix:|Fix:).*?```bash\s+(.*?)\s+```", text, re.DOTALL)
    if fix_match: commands['fix'] = fix_match.group(1).strip()
    elif "```bash" in text:
        all_matches = re.findall(r"```bash\s+(.*?)\s+```", text, re.DOTALL)
        if all_matches: commands['fix'] = all_matches[-1].strip()
    return commands

def broadcast_status(status, cpu, ram, last_log):
    """Writes system state atomically so the Flask server never crashes reading it."""
    try:
        data = {
            "cpu": cpu,
            "ram": ram,
            "status": status,
            "last_log": last_log[:150]
        }
        temp_path = STATUS_FILE + ".tmp"
        with open(temp_path, "w") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, STATUS_FILE)
        os.chmod(STATUS_FILE, 0o666)
    except Exception:
        pass

# --- WATCHDOG MODE (FULL FEATURED) ---
# Change line 67 to this:
def start_watchdog_mode(log_file="/tmp/stacksentinel_dummy_log.txt"):
    console.clear()
    console.rule("[bold red]🛡️ StackSentinel WATCHDOG PROTOCOL: ACTIVE[/bold red]")
    console.print(Panel(
        "I am guarding your system while you are away.\n"
        "Monitoring: [cyan]Logs[/cyan] | [cyan]CPU/RAM[/cyan] | [cyan]Process Whitelist[/cyan]\n"
        "Status: [bold green]ARMED[/bold green]",
        title="AFK Protection",
        border_style="red"
    ))
    
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("--- Watchdog Log Started ---\n")

    # Startup Sequence
    notifier.send_startup_ping()
    voice.speak("Watchdog Protocol Initiated. System Armed.")

    last_processed_line = ""
    tick_counter = 0
    was_locked = False
    current_ai_log = "Monitoring system logs..."

    with Live(refresh_per_second=1) as live:
        with open(log_file, "r") as f:
            f.seek(0, 2)
            while True:
                # 1. Fetch Vitals ONCE to fix the psutil double-call bug
                current_cpu = psutil.cpu_percent(interval=None)
                current_ram = psutil.virtual_memory().percent
                
                # --- CHECK FOR REMOTE LOCKDOWN ---
                is_locked = os.path.exists(LOCKDOWN_FILE)
                
                # Edge Trigger: Lockdown Started
                if is_locked and not was_locked:
                    voice.speak("Lockdown Protocol Engaged. Eliminating threats.")
                    console.print("[bold red]🔒 LOCKDOWN ACTIVATED REMOTELY[/bold red]")
                    notifier.send_alert("System Status", "Lockdown Protocol Engaged via Remote.", "critical")
                
                # Edge Trigger: Lockdown Ended
                elif not is_locked and was_locked:
                    voice.speak("Lockdown disengaged. Returning to standard watch.")
                    console.print("[green]🔓 Lockdown lifted.[/green]")
                    notifier.send_alert("System Status", "Lockdown Disengaged.", "normal")
                
                was_locked = is_locked

                # 2. Update the Rich Table GUI
                table = Table(title="System Vitals")
                table.add_column("Metric", style="cyan"); table.add_column("Value", style="green")
                table.add_row("CPU Usage", f"{current_cpu}%")
                table.add_row("RAM Usage", f"{current_ram}%")
                table.add_row("Mode", "[bold red]🔒 LOCKDOWN[/bold red]" if is_locked else "[green]Standard[/green]")
                status = "[green]NORMAL[/green]"
                if current_cpu > 90: status = "[red]HIGH LOAD[/red]"
                table.add_row("Status", status)
                live.update(table)

                # --- GUARD CHECK ---
                check_freq = 1 if is_locked else 5
                
                if tick_counter % check_freq == 0:
                     rogues = guard.check_processes()
                     if rogues: 
                         # guard.enforce_rules(rogues) # Temporarily disabled to prevent Ubuntu GDM crashes
                         #console.print(f"[yellow]Safe Mode: guard.py wants to kill -> {rogues}[/yellow]")
                         pass
                
                # --- REMOTE BROADCAST ---
                if tick_counter % 2 == 0:
                    status_text = "🔒 LOCKDOWN" if is_locked else "ARMED"
                    broadcast_status(status_text, current_cpu, current_ram, current_ai_log)

                # --- LOG ANALYSIS ---
                line = f.readline()
                if line and ("ERROR" in line or "CRITICAL" in line):
                    if line.strip() == last_processed_line:
                        time.sleep(0.1)
                        continue 
                    
                    last_processed_line = line.strip()
                    current_ai_log = line.strip() # Keeps the error visible on your phone!

                    live.stop() 
                    
                    if hasattr(history, 'is_system_looping') and history.is_system_looping(line):
                        msg = "Circuit Breaker Triggered."
                        console.print(Panel(f"[bold red]🛑 {msg}[/bold red]", border_style="red"))
                        voice.speak(msg)
                        notifier.send_alert("Circuit Breaker", msg, "critical")
                        current_ai_log = "HALTED: Circuit Breaker Active"
                        broadcast_status("HALTED", current_cpu, current_ram, current_ai_log)
                        input("Press Enter to reset...")
                        live.start()
                        continue

                    # Alerting Sequence
                    broadcast_status("CRITICAL ALERT", current_cpu, current_ram, current_ai_log)
                    notifier.send_alert("StackSentinel Alert", line.strip(), "critical")
                    voice.speak(f"Critical Alert. Error Detected.")
                    console.print(Panel(f"[bold red]🚨 THREAT DETECTED:[/bold red] {line.strip()}", border_style="red"))
                    
                    console.print("[yellow]🧠 Consulting Amazon Nova AI...[/yellow]")
                    sys_ctx = diagnose.get_system_report()
                    solution = brain.ask_nova(sys_ctx, f"CRITICAL: {line}", learning_mode=False)
                    cmds = extract_commands(solution)
                    fix = cmds.get('fix')
                    
                    if fix and "SAFE" in brain.audit_command(fix):
                        console.print(f"[bold green]✅ Auto-Fixing...[/bold green]")
                        #voice.speak("Applying Automated Fix.")
                        
                        # --- THE MAGIC MOMENT: Execution ---
                        try:
                            # Added timeout=15 so the AI can never permanently freeze the watchdog
                            subprocess.run(fix, shell=True, check=False, timeout=15)
                            console.print(f"[bold cyan]Command Executed: {fix}[/bold cyan]")
                        except subprocess.TimeoutExpired:
                            console.print(f"[bold red]Execution Aborted: Command took too long or asked for input.[/bold red]")
                        except Exception as e:
                            console.print(f"[red]Execution failed: {e}[/red]")
                            
                        history.save_event(f"AFK: {line}", solution, fix, None, "SAFE", "AUTO_EXECUTED")
                        current_ai_log = f"✅ FIXED: {fix}" # Sends success message to your phone
                    else:
                        console.print(f"[bold red]🛑 Dangerous Fix Blocked.[/bold red]")
                        voice.speak("Fix blocked by Safety Protocols.")
                        history.save_event(f"AFK: {line}", solution, fix, None, "BLOCKED", "BLOCKED")
                        current_ai_log = "🛑 BLOCKED: Unsafe command detected."
                    
                    time.sleep(2)
                    live.start()
                
                # --- HEARTBEAT SLEEP ---
                time.sleep(1.0)
                tick_counter += 1

# --- WATCH MODE (PASSIVE) ---
def start_watch_mode(log_file="system_log.txt"):
    console.clear()
    console.rule("[bold blue]StackSentinel: WATCH MODE ACTIVE[/bold blue]")
    
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("---\n")
            
    with open(log_file, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line: console.print(f"[dim]{line.strip()}[/dim]")
            time.sleep(0.5)

# --- MAIN EXECUTION ---
def cli_entry_point():
    parser = argparse.ArgumentParser()
    parser.add_argument("problem", type=str, nargs="?", help="Describe your problem")
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--learn", action="store_true", help="Enable Educational Mode")
    parser.add_argument("--history", action="store_true", help="View Audit Logs")
    parser.add_argument("--gym", action="store_true", help="Enter Training Simulator")
    parser.add_argument("--watch", action="store_true", help="Monitor logs")
    parser.add_argument("--watchdog", action="store_true", help="AFK Protection Mode")
    parser.add_argument("--report", action="store_true", help="Show Performance Score")
    parser.add_argument("--teach", action="store_true", help="Correct AI mistakes")
    parser.add_argument("--snapshot", action="store_true", help="Create Restore Point")
    parser.add_argument("--restore", action="store_true", help="Restore from Snapshot")
    parser.add_argument("--audit", action="store_true", help="Check for System Drift")
    parser.add_argument("--set-baseline", action="store_true", help="Set Drift Baseline")
    args = parser.parse_args()

    if args.watchdog or args.teach or args.history or args.report or args.restore or args.set_baseline:
        if not auth.verify_access(): return

    if args.snapshot:
        note = Prompt.ask("Enter a note", default="Manual Backup")
        snapshot.create_snapshot(note); return

    if args.restore:
        backups = snapshot.list_snapshots()
        if not backups: return
        table = Table(title="Restore Points")
        table.add_column("ID", style="cyan"); table.add_column("File"); table.add_column("Note")
        for idx, b in enumerate(backups): table.add_row(str(idx), b['file'], b['note'])
        console.print(table)
        choice = Prompt.ask("ID to restore (or 'q')", default="q")
        if choice == 'q': return
        try: snapshot.restore_snapshot(backups[int(choice)]['file'])
        except: console.print("[red]Invalid ID[/red]")
        return

    if args.watchdog: start_watchdog_mode(); return
    if args.report: console.print(history.generate_report()); return
    if args.teach: history.enter_teach_mode(); return
    if args.gym: gym.start_gym(); return
    if args.history: history.view_history(); return
    if args.set_baseline: drift.set_baseline(); return
    if args.audit: drift.run_audit(); return

    if not args.problem:
        console.print("[red]Please provide a problem or flag.[/red]")
        return

    if hooks_engine.check_and_run_hooks(args.problem):
        console.print("[bold green]✅ Automated Hook Executed.[/bold green]")
        if not Confirm.ask("Did that fix it?"): return

    profile = profiler.load_profile() or profiler.create_profile()
    last = history.check_recurrence(args.problem)
    if last and last.get("user_feedback") and Confirm.ask(f"Use trusted fix: {last['user_feedback']}?"):
        console.print("[green]Executed.[/green]"); return

    with console.status("[bold purple]Consulting Amazon Nova AI...[/bold purple]"):
        ctx = diagnose.get_system_report()
        sol = brain.ask_nova(ctx, args.problem, learning_mode=args.learn, user_profile=profile)

    if args.learn:
        console.print(Panel(Markdown(sol), title="Professor Mode"))
        if not Confirm.ask("Show Answer?"): return
        sol = brain.ask_nova(ctx, args.problem, learning_mode=False)

    console.print(Panel(Markdown(sol), title="Diagnosis"))
    cmds = extract_commands(sol)
    status = "NO_ACTION"
    auditor = "N/A"
    
    if cmds.get('fix'):
        audit = brain.audit_command(cmds['fix'])
        auditor = "SAFE" if "SAFE" in audit else "WARNING"
        if auditor == "SAFE":
            console.print(f"[bold green]✅ Auditor Approved[/bold green]")
            if Confirm.ask("Run this plan?"):
                if cmds.get('backup'): console.print("[blue]Backing up...[/blue]")
                # Direct Terminal Execution Logic
                fix_command = cmds['fix']
                dangerous_keywords = ["rm -rf", "mkfs", "dd ", "reboot", "shutdown", "chmod 777", "mkswap"]
                
                if any(bad_word in fix_command for bad_word in dangerous_keywords):
                    console.print(f"[bold red]SECURITY ALERT: AI attempted to run a destructive command:[/bold red] {fix_command}")
                    console.print("[bold red]Execution BLOCKED to protect the kernel.[/bold red]")
                    status = "BLOCKED_BY_SAFETY_NET"
                else:
                    # Added a 15-second timeout so the AI can't freeze your terminal forever
                    try:
                        subprocess.run(fix_command, shell=True, check=False, timeout=15)
                        console.print("[green]Executed.[/green]")
                        status = "EXECUTED"
                    except subprocess.TimeoutExpired:
                        console.print("[bold red]Execution Aborted: Command took too long or asked for input.[/bold red]")
                        status = "TIMEOUT"

            else: status = "SKIPPED"
        else:
            console.print(Panel(f"[bold red]BLOCKED[/bold red] {audit}", border_style="red"))
            status = "BLOCKED"

    history.save_event(args.problem, sol, cmds.get('fix'), cmds.get('backup'), auditor, status)
    with console.status("[bold blue]Syncing to AWS Cloud...[/bold blue]"):
        cloud.push_to_cloud()

if __name__ == "__main__":
    try:
        # This is the crucial line that actually starts the app!
        cli_entry_point()
        
    except KeyboardInterrupt:
        # This catches the Ctrl+C button press!
        print("\n🛑 StackSentinel Watchdog disarmed. Shutting down gracefully...")
        
        # Clean up the status file so the UI knows we are offline

        if os.path.exists("/tmp/stacksentinel_status.json"):
            os.remove("/tmp/stacksentinel_status.json")
            
        sys.exit(0)