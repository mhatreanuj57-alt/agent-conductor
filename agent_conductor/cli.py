import argparse
import sys
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.cwd() / ".env")

from agent_conductor.merger import final_report, merge_all
from agent_conductor.planner import plan
from agent_conductor.runners import run_parallel
from agent_conductor.worktrees import (branch_ahead_of, cleanup_worktrees, commit_worktree_changes,
                           create_worktree, ensure_repo, harvest_strays)

__version__ = "0.3.3"

BANNER = """
  ┌─────────────────────────────────────┐
  │  ⚡ AGENT CONDUCTOR                  │
  │  codex + opencode, working in parallel  │
  └─────────────────────────────────────┘
"""


def main():
    parser = argparse.ArgumentParser(description="Run Codex & OpenCode in parallel on isolated worktrees")
    parser.add_argument("goal", nargs="?", help="Project goal, e.g. 'build a todo app with React frontend and FastAPI backend'")
    parser.add_argument("--dir", default=None, help="Project directory (default: ./projects/<name>)")
    parser.add_argument("--timeout", type=int, default=30, help="Per-agent timeout in minutes (default 30)")
    parser.add_argument("--agents", default="codex,opencode",
                        help="Agent specs comma-separated. Use name@model to override the model, "
                             "e.g. 'codex,opencode@opencode/glm-5'")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    
    if not args.goal:
        parser.error("the following arguments are required: goal")

    agent_specs = [a.strip() for a in args.agents.split(",") if a.strip()]

    print(BANNER)
    print("  [1/5] Planning with LLM...")
    if args.verbose:
        print(f"        Goal: {args.goal}")
        print(f"        Agents: {args.agents}")
        print(f"        Timeout: {args.timeout} min")
    try:
        plan_data = plan(args.goal, agents=agent_specs)
    except Exception as e:
        print(f"  ERROR: Planning failed: {e}")
        sys.exit(1)
    
    project = plan_data["project"]
    tasks = plan_data["tasks"]
    print(f"        project: {project}")
    for t in tasks:
        print(f"        - {t['agent']:9s} {t['name']}: {t['summary']}")
    
    if args.verbose:
        print(f"\n        Total tasks: {len(tasks)}")
        print(f"        Estimated agents: {len(agent_specs)}")
    
    if args.dry_run:
        print("\n  [DRY RUN] Plan generated. Use without --dry-run to execute.")
        return

    project_dir = Path(args.dir) if args.dir else Path.cwd() / "projects" / project
    print(f"\n  [2/5] Preparing repo: {project_dir}")
    ensure_repo(project_dir)

    print("  [3/5] Creating isolated worktrees...")
    jobs, branches, worktrees = [], [], {}
    for task in tasks:
        spec = task["agent"]
        short = spec.split("@")[0]
        wt = create_worktree(project_dir, short, task["name"])
        worktrees[short] = wt
        branches.append(f"conductor/{short}-{task['name']}")
        jobs.append((spec, task, wt, Path("logs") / f"{datetime.now():%Y%m%d-%H%M%S}-{short}.log"))
        print(f"        {spec:28s} -> {wt}")

    print(f"\n  [4/5] Launching agents in parallel (timeout {args.timeout} min each)...")
    agent_results = run_parallel(jobs, timeout_min=args.timeout)

    print("\n  [5/5] Committing agent work + merging to main...")
    ahead_counts = {}
    for spec, task, wt, _ in jobs:
        short = spec.split("@")[0]
        strays = harvest_strays(task, wt, [Path.cwd(), project_dir])
        for s in strays:
            print(f"        {short}: harvested stray output -> {s}")
        info = commit_worktree_changes(wt, short, task["name"])
        branch_name = f"conductor/{short}-{task['name']}"
        ahead_counts[branch_name] = branch_ahead_of(project_dir, branch_name)
        if info["committed"]:
            print(f"        {short}: committed {info['files']} changed files")
        else:
            print(f"        {short}: no file changes detected")
    merge_results = merge_all(project_dir, branches)
    for m in merge_results:
        if ahead_counts.get(m["branch"], 0) == 0 and m["status"] == "merged":
            m["status"] = "merged (empty branch - no commits)"
    cleanup_worktrees(project_dir)

    print(final_report(project_dir, agent_results, merge_results))
    print(f"\n  project: {project_dir}")
    print("  logs:    logs/ (full agent transcripts)")


if __name__ == "__main__":
    main()
