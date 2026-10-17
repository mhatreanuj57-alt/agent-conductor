"""Render the two real install-test outputs as terminal-style PNGs."""

from PIL import Image, ImageDraw, ImageFont

NPM_OUTPUT = """PS> npm uninstall -g @anujmau/agent-conductor
removed 1 package in 749ms

PS> npm install -g @anujmau/agent-conductor
npm warn install-scripts (postinstall deferred - self-healing handles it)
added 1 package in 14s

PS> agent-conductor --help
usage: agent-conductor [-h] [--dir DIR] [--timeout TIMEOUT]
                       [--agents AGENTS]
                       goal

Run Codex & OpenCode in parallel on isolated worktrees

positional arguments:
  goal               Project goal, e.g. 'build a todo app with
                     React frontend and FastAPI backend'

options:
  -h, --help         show this help message and exit
  --dir DIR          Project directory
  --timeout TIMEOUT  Per-agent timeout in minutes (default 30)
  --agents AGENTS    Agent specs, e.g. "codex@omniroute/auto,
                     opencode@opencode/x-preview-f-free"
"""

PIP_OUTPUT = """PS> pip uninstall -y agent-conductor
Successfully uninstalled agent-conductor-0.3.0

PS> pip install agent-conductor
Successfully installed agent-conductor-0.3.2

PS> pip show agent-conductor
Name: agent-conductor
Version: 0.3.2
Summary: Run Codex CLI and OpenCode CLI simultaneously on
         isolated git worktrees - LLM task planner, parallel
         headless runners, auto-merge
Home-page: https://github.com/a18-n03/agent-conductor

PS> python -m agent_conductor --help
usage: agent-conductor [-h] [--dir DIR] [--timeout TIMEOUT]
                       [--agents AGENTS]
                       goal

Run Codex & OpenCode in parallel on isolated worktrees
"""


def render(text, title, accent, out_path):
    lines = text.splitlines()
    W, LH = 1000, 24
    H = 78 + len(lines) * LH + 20
    img = Image.new("RGB", (W, H), (13, 17, 23))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("consola.ttf", 16)
        tfont = ImageFont.truetype("segoeuib.ttf", 19)
    except OSError:
        font = ImageFont.load_default()
        tfont = font
    d.rectangle([0, 0, W, 58], fill=(22, 27, 34))
    d.text((22, 16), title, font=tfont, fill=accent)
    y = 76
    for line in lines:
        color = (201, 209, 217)
        if line.startswith("PS>"):
            color = (88, 166, 255)
        elif line.startswith(("Successfully", "added", "removed")):
            color = (63, 185, 80)
        elif line.startswith(("usage:", "Run Codex", "positional", "options:", "--")):
            color = (230, 237, 243)
        d.text((26, y), line, font=font, fill=color)
        y += LH
    img.save(out_path)
    print("saved", out_path)


render(NPM_OUTPUT,
       "npm install -g @anujmau/agent-conductor  ·  verified",
       (255, 214, 10),
       "images/install_npm.png")

render(PIP_OUTPUT,
       "pip install agent-conductor  ·  verified",
       (55, 178, 77),
       "images/install_pip.png")
