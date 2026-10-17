import subprocess
from pathlib import Path

from .worktrees import git


def merge_all(project_dir: Path, branches: list) -> list:
    results = []
    for branch in branches:
        merge = subprocess.run(
            ["git", "-C", str(project_dir), "merge", branch, "--no-edit", "--allow-unrelated-histories"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if merge.returncode == 0:
            results.append({"branch": branch, "status": "merged"})
        else:
            conflict = "CONFLICT" in merge.stdout or "CONFLICT" in merge.stderr
            if conflict:
                subprocess.run(["git", "-C", str(project_dir), "merge", "--abort"],
                               capture_output=True, text=True)
                results.append({"branch": branch, "status": "conflict (aborted - merge manually)"})
            else:
                results.append({"branch": branch, "status": f"failed: {(merge.stderr or merge.stdout)[:120]}"})
    return results


def final_report(project_dir: Path, agent_results: list, merge_results: list):
    lines = ["", "=" * 56, "  CONDUCTOR REPORT", "=" * 56]
    for r in agent_results:
        icon = "OK " if r["status"] == "done" else "!! "
        lines.append(f"  [{icon}] {r['agent']:9s} {r['task']:20s} {r['status']} ({r['minutes']} min)")
    lines.append("-" * 56)
    for r in merge_results:
        icon = "OK " if r["status"] == "merged" else "!! "
        lines.append(f"  [{icon}] merge {r['branch']:35s} {r['status']}")
    log_status = subprocess.run(
        ["git", "-C", str(project_dir), "log", "--oneline", "-8"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    lines.append("-" * 56)
    lines.append("  recent commits:")
    lines.extend("    " + l for l in log_status.stdout.splitlines())
    lines.append("=" * 56)
    return "\n".join(lines)
