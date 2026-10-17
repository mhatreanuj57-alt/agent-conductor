import os
import subprocess
import threading
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def build_command(agent_spec: str, prompt: str, worktree: Path) -> str:
    """Build the CLI command for a given agent specification."""
    prompt_escaped = (prompt.replace('"', "'")
                            .replace("\r", " ")
                            .replace("\n", " "))
    agent, _, model = agent_spec.partition("@")
    if agent == "codex":
        cmd = f'codex exec "{prompt_escaped}" -C "{worktree}" --skip-git-repo-check -s workspace-write'
        if model:
            if model.startswith("omniroute/"):
                short = model.split("/", 1)[1]
                cmd += f" -c model_provider=omniroute -c model={short}"
            else:
                cmd += f" -c model={model}"
        return cmd
    if agent == "opencode":
        cmd = f'opencode run "{prompt_escaped}" --dir "{worktree}"'
        if model:
            cmd += f' -m "{model}"'
        return cmd
    if agent == "claude":
        cmd = f'claude -p "{prompt_escaped}" --dangerously-skip-permissions'
        return cmd
    raise ValueError(
        f"Unknown agent: '{agent}'. Supported agents: codex, opencode, claude"
    )


def run_agent(
    agent_spec: str,
    task: dict,
    worktree: Path,
    log_path: Path,
    timeout_min: int = 30,
) -> dict:
    """Run a single agent in a worktree with timeout."""
    task = dict(task)
    task["prompt"] = (f"{task['prompt']}\n\nHARD REQUIREMENT: Your working directory is "
                      f"{worktree}. Create every file INSIDE this directory using relative "
                      f"paths. NEVER write outside it. Do not use absolute paths to other "
                      f"folders. Do not start long-running servers; just create the files.")
    cmd = build_command(agent_spec, task["prompt"], worktree)
    started = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"# {agent_spec} :: {task['name']}\n# {cmd}\n\n")
        log.flush()
        try:
            _, _, model = agent_spec.partition("@")
            env = os.environ.copy()
            if agent_spec.startswith("claude") and model:
                env["ANTHROPIC_MODEL"] = model
            process = subprocess.Popen(cmd, shell=True, stdout=log,
                                       stderr=subprocess.STDOUT, env=env,
                                       stdin=subprocess.DEVNULL, cwd=str(worktree))
            exit_code = process.wait(timeout=timeout_min * 60)
        except subprocess.TimeoutExpired:
            process.kill()
            log.write(f"\n[CONDUCTOR] TIMEOUT after {timeout_min} min\n")
            return {
                "agent": agent_spec,
                "task": task["name"],
                "status": "timeout",
                "minutes": round((time.time() - started) / 60, 1),
                "branch_worktree": str(worktree),
            }
    minutes = round((time.time() - started) / 60, 1)
    status = "done" if exit_code == 0 else f"exit {exit_code}"
    return {
        "agent": agent_spec,
        "task": task["name"],
        "status": status,
        "minutes": minutes,
        "worktree": str(worktree),
    }


def run_parallel(jobs: list, timeout_min: int = 30) -> list:
    """Run all agents in parallel threads."""
    results = [None] * len(jobs)
    threads = []

    def worker(idx: int, job: tuple) -> None:
        agent, task, worktree, log_path = job
        print(f"  [{agent}] started: {task['summary']}")
        results[idx] = run_agent(agent, task, worktree, log_path, timeout_min)
        print(f"  [{agent}] finished: {results[idx]['status']} in {results[idx]['minutes']} min")

    for i, job in enumerate(jobs):
        t = threading.Thread(target=worker, args=(i, job))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return results
