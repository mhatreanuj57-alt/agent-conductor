import shutil
import subprocess
from pathlib import Path


def git(project_dir: Path, *args: str) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(project_dir), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ensure_repo(project_dir: Path) -> None:
    """Ensure the project directory is a git repo with a base commit."""
    project_dir.mkdir(parents=True, exist_ok=True)
    if not (project_dir / ".git").exists():
        git(project_dir, "init", "-b", "main")
    identity = subprocess.run(["git", "-C", str(project_dir), "config", "user.email"],
                              capture_output=True, text=True)
    if not identity.stdout.strip():
        subprocess.run(["git", "-C", str(project_dir), "config", "user.name", "Agent Conductor"],
                       capture_output=True, text=True)
        subprocess.run(["git", "-C", str(project_dir), "config", "user.email", "conductor@local"],
                       capture_output=True, text=True)
    status = git(project_dir, "status", "--porcelain")
    log = subprocess.run(["git", "-C", str(project_dir), "rev-parse", "--verify", "HEAD"],
                         capture_output=True, text=True)
    if status or log.returncode != 0:
        readme = project_dir / "PROJECT.md"
        if not readme.exists():
            readme.write_text("# Project\n\nCreated by Agent Conductor.\n", encoding="utf-8")
        git(project_dir, "add", "-A")
        commit = subprocess.run(["git", "-C", str(project_dir), "commit", "-m", "chore: base commit by conductor",
                                 "--allow-empty"], capture_output=True, text=True)
        if commit.returncode != 0 and "nothing to commit" not in commit.stdout + commit.stderr:
            raise RuntimeError(f"Base commit failed: {commit.stderr}")


def create_worktree(project_dir: Path, agent: str, task_name: str) -> Path:
    """Create an isolated git worktree for an agent."""
    branch = f"conductor/{agent}-{task_name}"
    wt_path = project_dir / ".conductor" / f"{agent}-{task_name}"
    if wt_path.exists():
        git(project_dir, "worktree", "remove", "--force", str(wt_path))
        git(project_dir, "branch", "-D", branch)
    git(project_dir, "worktree", "add", "-b", branch, str(wt_path))
    return wt_path


def harvest_strays(task: dict, worktree: Path, search_roots: list) -> list:
    moved = []
    for rel in task.get("paths", []):
        rel = rel.strip("/\\")
        if not rel:
            continue
        target = worktree / rel
        if target.exists():
            continue
        for root in search_roots:
            stray = Path(root) / rel
            if stray.exists() and stray.resolve() != target.resolve():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(stray), str(target))
                moved.append(str(target))
                break
    return moved


def commit_worktree_changes(worktree: Path, agent: str, task_name: str) -> dict:
    status = git(worktree, "status", "--porcelain")
    if not status.strip():
        return {"committed": False, "files": 0}
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", f"feat({agent}): {task_name}")
    files = len([l for l in status.splitlines() if l.strip()])
    return {"committed": True, "files": files}


def branch_ahead_of(project_dir: Path, branch: str) -> int:
    out = git(project_dir, "rev-list", "--count", f"main..{branch}")
    return int(out or 0)


def cleanup_worktrees(project_dir: Path):
    wt_root = project_dir / ".conductor"
    if wt_root.exists():
        for wt in wt_root.iterdir():
            subprocess.run(["git", "-C", str(project_dir), "worktree", "remove", "--force", str(wt)],
                           capture_output=True, text=True)
        subprocess.run(["git", "-C", str(project_dir), "worktree", "prune"], capture_output=True, text=True)
