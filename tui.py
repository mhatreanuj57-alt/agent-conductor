"""Agent Conductor - Terminal UI (no browser needed).

Run:  python tui.py
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from rich import box
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from rich.console import Console, Group  # noqa: E402

console = Console()

BANNER = r"""
   ┌──────────────────────────────────────────────┐
   │   ⚡  A G E N T   C O N D U C T O R          │
   │   codex · opencode · claude — in parallel    │
   └──────────────────────────────────────────────┘"""

DEFAULT_A1 = "codex@omniroute/auto"
DEFAULT_A2 = "opencode@opencode/x-preview-f-free"


def ask(prompt: str, default: str) -> str:
    val = console.input(f"  [cyan]{prompt}[/cyan] [dim]({default})[/dim]: ").strip()
    return val or default


def build_layout(output_lines, status_line):
    tail = output_lines[-28:] if output_lines else ["waiting for output..."]
    log_text = Text("\n".join(tail), style="white")
    log_text.truncate(max_width=110, max_lines=28)
    log_panel = Panel(log_text, title="live output", border_style="blue", box=box.ROUNDED)
    header = Panel(status_line, border_style="green", box=box.ROUNDED)
    return Group(header, log_panel)


def run(goal, agents, timeout):
    cmd = [sys.executable, "-m", "agent_conductor.cli", goal,
           "--agents", agents, "--timeout", str(timeout)]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace",
                            stdin=subprocess.DEVNULL)
    lines = []

    def status_line():
        return Text(f" ⚡ running  ·  {agents}  ·  {len(lines)} lines", style="bold green")

    with Live(build_layout(lines, status_line()), console=console,
              refresh_per_second=4) as live:
        for line in proc.stdout:
            lines.append(line.rstrip())
            live.update(build_layout(lines, status_line()))
    proc.wait()
    return lines, proc.returncode


def main():
    print(BANNER)
    print()
    goal = ask("project goal", "build a joke app: static HTML frontend, FastAPI backend")
    a1 = ask("agent 1", DEFAULT_A1)
    a2 = ask("agent 2", DEFAULT_A2)
    timeout = int(ask("timeout (min)", "15"))
    agents = f"{a1},{a2}"

    print()
    console.rule("[bold green]launching agents", style="green")
    lines, code = run(goal, agents, timeout)

    console.print()
    for line in lines[-30:]:
        style = "bold green" if "[OK" in line else ("yellow" if "started" in line or "finished" in line else "white")
        if "CONDUCTOR REPORT" in line:
            style = "bold cyan"
        console.print(line, style=style)

    if code == 0:
        console.print("\n [bold green]✔ run complete[/bold green] — check projects/ for the merged app\n")
    else:
        console.print(f"\n [bold red]✗ exited with code {code}[/bold red] — see logs/\n")


if __name__ == "__main__":
    main()
