# Agent Conductor

![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
![Author: Anuj Mhatre](https://img.shields.io/badge/Author-Anuj%20Mhatre-orange)

## Why We Built This

Single AI agents are powerful but limited. Agent Conductor orchestrates multiple AI coding agents (Codex + OpenCode) in parallel on isolated git worktrees, then merges their results — enabling true parallel AI development.

## What It Does

- Plans project tasks using LLM and assigns to multiple agents
- Creates isolated git worktrees for each agent
- Runs Codex and OpenCode agents in parallel with configurable timeouts
- Harvests stray output files from agent work
- Commits and merges all agent work back to main
- Generates a final merge report

## How It Was Built

- **Orchestration:** Python CLI with argparse
- **Planning:** OpenAI-compatible LLM for task decomposition
- **Isolation:** Git worktrees for parallel agent work
- **Agents:** Codex CLI + OpenCode CLI integration
- **Merge:** Git merge with conflict detection

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="your-key"

# Run conductor
agent-conductor "build a todo app with React frontend and FastAPI backend"

# With custom settings
agent-conductor --timeout=60 --agents="codex,opencode@opencode/glm-5" "my project goal"
```

**Options:**
- `--dir`: Custom project directory
- `--timeout`: Per-agent timeout in minutes (default: 30)
- `--agents`: Comma-separated agent specs with optional model overrides

## Project Structure

```
agent-conductor/
├── agent_conductor/
│   ├── __init__.py      # Package init
│   ├── cli.py           # CLI entry point
│   ├── planner.py       # LLM-based task planning
│   ├── runners.py       # Parallel agent execution
│   ├── merger.py        # Git merge + reporting
│   └── worktrees.py     # Git worktree management
├── tui.py               # Terminal UI (alternative)
├── webui.py             # Web UI (alternative)
├── requirements.txt     # Dependencies
└── bin/                 # CLI scripts
```

## Test Results

Integration testing requires Codex/OpenCode CLI installed.

## License

MIT License - see [LICENSE](LICENSE) for details.
