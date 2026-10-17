"""Render the real counter-app run as 2 terminal-style screenshots."""

from PIL import Image, ImageDraw, ImageFont

RUN_OUTPUT = """  ┌──────────────────────────────────────────────┐
  │  ⚡ AGENT CONDUCTOR                           │
  │  codex · opencode · claude — in parallel     │
  └──────────────────────────────────────────────┘

  [1/5] Planning with LLM...
        project: tiny-counter-app
        - opencode@x-preview-f-free frontend-counter-ui
        - opencode@x-preview-f-free backend-node-server

  [2/5] Preparing repo: projects/tiny-counter-app
  [3/5] Creating isolated worktrees...
        opencode -> .conductor/opencode-frontend-counter-ui
        opencode -> .conductor/opencode-backend-node-server

  [4/5] Launching agents in parallel (timeout 8 min each)...
  [opencode] started: Create index.html with counter display
  [opencode] started: Create Node server.js (serves frontend)
"""

REPORT_OUTPUT = """  [opencode] finished: done in 0.5 min
  [opencode] finished: done in 0.7 min

  [5/5] Committing agent work + merging to main...
        opencode: committed 1 changed files
        opencode: committed 1 changed files

========================================================
  CONDUCTOR REPORT
========================================================
  [OK ] opencode  frontend-counter-ui   done (0.5 min)
  [OK ] opencode  backend-node-server   done (0.7 min)
--------------------------------------------------------
  [OK ] merge conductor/opencode-frontend-counter-ui  merged
  [OK ] merge conductor/opencode-backend-node-server  merged
--------------------------------------------------------
  recent commits:
    aa5dddf Merge branch 'conductor/opencode-backend-node-server'
    a719740 feat(opencode): frontend-counter-ui
    8d64ad5 feat(opencode): backend-node-server

  LIVE TEST (merged app):
  $ node backend/server.js
  POST /api/increment -> {"count": 1}   ✓ working
"""


def render(text, title, accent, out_path, H_extra=20):
    lines = text.splitlines()
    W, LH = 1080, 24
    H = 78 + len(lines) * LH + H_extra
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
        if "started" in line:
            color = (255, 214, 10)
        if "finished" in line or "[OK" in line:
            color = (63, 185, 80)
        if "CONDUCTOR REPORT" in line or "AGENT CONDUCTOR" in line:
            color = (88, 166, 255)
        if "LIVE TEST" in line or '"count"' in line:
            color = (255, 123, 114)
        d.text((26, y), line, font=font, fill=color)
        y += LH
    img.save(out_path)
    print("saved", out_path)


render(RUN_OUTPUT,
       "agent-conductor · live run — two agents launched in parallel",
       (88, 166, 255),
       "images/run_live.png")

render(REPORT_OUTPUT,
       "agent-conductor · report + live test of merged app",
       (63, 185, 80),
       "images/run_report.png")
