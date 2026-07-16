import time
import random
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

import brain 

console = Console()

SCENARIOS = {
    "1": {
        "title": "Level 1: The Dependency Hell",
        "description": "You tried to install PyTorch, but now 'pip' commands fail with 'Externally Managed Environment'.",
        "error_log": "error: externally-managed-environment",
        "hint": "You might need to use a virtual environment.",
        "solution_keyword": "venv"
    },
    "2": {
        "title": "Level 2: The Black Screen",
        "description": "You updated your kernel and now your monitor is blank. You can only access the terminal.",
        "error_log": "NVRM: API mismatch: the client has the version 535.104, but this kernel module has the version 525.85.",
        "hint": "This looks like a driver version conflict.",
        "solution_keyword": "driver"
    }
}

def start_gym():
    console.clear()
    console.rule("[bold red]🥋 StackSentinel TRAINING GYM 🥋[/bold red]")
    console.print("[dim]Welcome, Cadet. Here you can practice fixing systems safely.[/dim]\n")
    console.print("[dim]Type 'exit' or 'quit' at any time to leave.[/dim]\n")

    console.print("[bold cyan]Select a Disaster Scenario:[/bold cyan]")
    for key, val in SCENARIOS.items():
        console.print(f"[{key}] {val['title']}")

    choice = Prompt.ask("Choose Level", choices=list(SCENARIOS.keys()), default="1")
    level = SCENARIOS[choice]

    # Display the Fake Disaster
    console.print(Panel(
        f"[bold red]SCENARIO ACTIVE:[/bold red] {level['title']}\n\n"
        f"{level['description']}\n\n"
        f"[yellow]System Log:[/yellow]\n{level['error_log']}",
        border_style="red"
    ))

    console.print("\n[bold green]Your Task:[/bold green] Ask the AI for a fix.")
    
    # Interactive Loop
    while True:
        user_query = Prompt.ask("[bold cyan]Describe the problem (or type 'exit')[/bold cyan]")
        
        # --- NEW: EXIT CONDITION ---
        if user_query.lower() in ["exit", "quit", "q"]:
            console.print("[yellow]Exiting Gym Mode. See you next time![/yellow]")
            break

        # 1. Call the Brain (Mock)
        fake_context = {"os": "Ubuntu Simulator", "logs": level['error_log']}
        
        with console.status("[bold purple]Consulting AI...[/bold purple]"):
            response = brain.ask_nova(fake_context, user_query, learning_mode=True)
            time.sleep(1.0)

        console.print(Panel(Markdown(response), title="AI Mentor", border_style="purple"))

        # 2. Check if they solved it
        if level['solution_keyword'] in user_query.lower():
             console.print(f"\n[bold green]🏆 SUCCESS![/bold green] You identified the issue.")
             console.print(f"[dim]The AI suggested the correct path based on your prompt.[/dim]")
             break
        else:
            console.print("[yellow]Not quite. Try describing the error log more specifically.[/yellow]")
            if Confirm.ask("Need a hint?"):
                console.print(f"[bold blue]HINT:[/bold blue] {level['hint']}")

    time.sleep(1)