"""Minimalist web UI for Agent Conductor.

Run:  uvicorn webui:app --port 8600
Open: http://localhost:8600
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from pydantic import BaseModel

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

app = FastAPI(title="Agent Conductor UI")

_state = {"proc": None, "output": [], "running": False, "started": None}


class RunRequest(BaseModel):
    goal: str
    agents: str = "codex@omniroute/auto,opencode@opencode/x-preview-f-free"
    timeout: int = 15


def _reader(proc):
    try:
        for line in proc.stdout:
            _state["output"].append(line.rstrip("\n"))
    except Exception:
        pass
    proc.wait()
    _state["output"].append(f"\n[EXIT code {proc.returncode}]")
    _state["running"] = False


@app.post("/api/run")
def run(req: RunRequest):
    if _state["running"]:
        return {"error": "a run is already in progress"}
    _state["output"] = []
    _state["running"] = True
    _state["started"] = time.strftime("%H:%M:%S")
    cmd = [sys.executable, "-m", "agent_conductor.cli", req.goal,
           "--agents", req.agents, "--timeout", str(req.timeout)]
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace",
                            stdin=subprocess.DEVNULL)
    _state["proc"] = proc
    threading.Thread(target=_reader, args=(proc,), daemon=True).start()
    return {"started": True}


@app.get("/api/status")
def status():
    return {"running": _state["running"], "started": _state["started"],
            "lines": _state["output"][-400:]}


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!doctype html>
<html><head><meta charset="utf-8"><title>Agent Conductor</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
*{box-sizing:border-box;margin:0}
body{background:#0d1117;color:#c9d1d9;font-family:Inter,sans-serif;min-height:100vh;
     display:flex;flex-direction:column;align-items:center;padding:40px 20px}
h1{font-size:1.6rem;font-weight:800;color:#e6edf3;letter-spacing:-.5px}
h1 span{color:#58a6ff}
.sub{color:#8b949e;font-size:.85rem;margin:6px 0 26px}
.card{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:22px;width:100%;max-width:860px}
label{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#8b949e;display:block;margin:14px 0 6px}
textarea,input{width:100%;background:#0d1117;border:1px solid #30363d;border-radius:8px;
               color:#e6edf3;padding:11px 14px;font-size:.92rem;font-family:inherit}
textarea{resize:vertical;min-height:64px}
input:focus,textarea:focus{outline:none;border-color:#58a6ff}
.row{display:flex;gap:12px}.row>div{flex:1}
button{margin-top:18px;width:100%;background:#238636;color:#fff;border:none;border-radius:8px;
       padding:13px;font-size:1rem;font-weight:600;cursor:pointer;font-family:inherit}
button:hover{background:#2ea043}
button:disabled{background:#21262d;color:#6e7681;cursor:not-allowed}
.term{margin-top:22px;background:#0d1117;border:1px solid #30363d;border-radius:12px;
      padding:18px;font-family:'JetBrains Mono',monospace;font-size:.8rem;line-height:1.55;
      white-space:pre-wrap;word-break:break-all;height:420px;overflow-y:auto;display:none}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#3fb950;margin-right:8px;
     animation:pulse 1.2s infinite}
@keyframes pulse{50%{opacity:.3}}
.badge{font-size:.7rem;color:#8b949e;margin-top:10px}
</style></head><body>
<h1>⚡ Agent <span>Conductor</span></h1>
<div class="sub">Codex · OpenCode · Claude — working in parallel on isolated worktrees</div>
<div class="card">
  <label>Project goal</label>
  <textarea id="goal">build a joke app: static HTML frontend, FastAPI backend</textarea>
  <div class="row">
    <div><label>Agent 1</label><input id="a1" value="codex@omniroute/auto"></div>
    <div><label>Agent 2</label><input id="a2" value="opencode@opencode/x-preview-f-free"></div>
  </div>
  <div class="row">
    <div><label>Timeout (min)</label><input id="to" type="number" value="15"></div>
  </div>
  <button id="run" onclick="startRun()">▶ &nbsp;Run Conductor</button>
  <div class="term" id="term"></div>
  <div class="badge" id="badge"></div>
</div>
<script>
let polling=null;
async function startRun(){
  const goal=document.getElementById('goal').value.trim();
  if(!goal) return;
  const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({goal,agents:document.getElementById('a1').value+','+document.getElementById('a2').value,
                         timeout:+document.getElementById('to').value})});
  const j=await r.json();
  if(j.error){alert(j.error);return;}
  document.getElementById('run').disabled=true;
  document.getElementById('run').innerHTML='<span class="dot"></span>Running — agents launched in parallel';
  const term=document.getElementById('term');term.style.display='block';term.textContent='';
  polling=setInterval(poll,1500);
}
async function poll(){
  const r=await fetch('/api/status');const j=await r.json();
  const term=document.getElementById('term');
  const fresh=j.lines.join('\\n');
  if(term.dataset.n!==fresh.length+''){term.textContent=fresh;term.scrollTop=term.scrollHeight;term.dataset.n=fresh.length+'';}
  document.getElementById('badge').textContent='run started '+j.started+' · '+j.lines.length+' lines';
  if(!j.running){clearInterval(polling);polling=null;
    const b=document.getElementById('run');b.disabled=false;b.innerHTML='▶ &nbsp;Run Conductor';}
}
</script></body></html>"""
