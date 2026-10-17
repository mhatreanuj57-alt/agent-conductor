"""Render the real conductor report output as a terminal-style PNG."""

from PIL import Image, ImageDraw, ImageFont

OUTPUT = """  ┌─────────────────────────────────────────┐
  │  ⚡ AGENT CONDUCTOR                      │
  │  claude + opencode, working in parallel │
  └─────────────────────────────────────────┘

  [1/5] Planning with LLM...
        project: quote-card
        - claude@auto/best-coding frontend-quote-card
        - opencode@opencode/x-preview-f-free backend-flask-api

  [2/5] Preparing repo: projects/quote-card
  [3/5] Creating isolated worktrees...
        claude    -> .conductor/claude-frontend-quote-card
        opencode  -> .conductor/opencode-backend-flask-api

  [4/5] Launching agents in parallel (timeout 10 min each)...
  [claude@auto/best-coding] started: Static HTML quote card...
  [opencode@opencode/x-preview-f-free] started: Flask backend...
  [opencode@opencode/x-preview-f-free] finished: done in 2.5 min
  [claude@auto/best-coding] finished: done in 4.6 min

  [5/5] Committing agent work + merging to main...
        claude: committed 1 changed files
        opencode: committed 1 changed files

========================================================
  CONDUCTOR REPORT
========================================================
  [OK ] claude@auto/best-coding frontend-quote-card  done (4.6 min)
  [OK ] opencode@opencode/x-preview-f-free backend    done (2.5 min)
--------------------------------------------------------
  [OK ] merge conductor/claude-frontend-quote-card  merged
  [OK ] merge conductor/opencode-backend-flask-api  merged
--------------------------------------------------------
  recent commits:
    2d5c7d6 Merge branch 'conductor/opencode-backend-flask-api'
    b93a5d3 feat(opencode): backend-flask-api
    dfa53b8 feat(claude): frontend-quote-card
========================================================

  LIVE TEST: GET /api/quote
  -> {"author": "Lao Tzu",
      "quote": "The journey of a thousand miles begins with a single step."}
"""

W, H = 1180, 1030
img = Image.new("RGB", (W, H), (13, 17, 23))
d = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("consola.ttf", 17)
    title = ImageFont.truetype("segoeuib.ttf", 22)
except OSError:
    font = ImageFont.load_default()
    title = font

d.rectangle([0, 0, W, 64], fill=(22, 27, 34))
d.text((24, 18), "● ● ●   agent-conductor — real run: claude + opencode in parallel", font=title, fill=(88, 166, 255))

y = 88
for line in OUTPUT.splitlines():
    color = (48, 209, 88) if "[OK" in line else ((255, 214, 10) if "finished" in line or "started" in line else (201, 209, 217))
    if "CONDUCTOR REPORT" in line or line.startswith("  ┌") or "LIVE TEST" in line:
        color = (88, 166, 255)
    if '"author"' in line or '"quote"' in line:
        color = (255, 123, 114)
    d.text((28, y), line, font=font, fill=color)
    y += 24

img.save("images/report_terminal.png")
print("saved images/report_terminal.png")
