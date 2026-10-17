#!/usr/bin/env node
/* One-time setup: find python, create a venv, install python deps + this package. */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const pkgRoot = path.join(__dirname, "..");
const venv = path.join(pkgRoot, ".venv");

function findPython() {
  const candidates = process.platform === "win32"
    ? ["python", "py -3"]
    : ["python3", "python"];
  for (const c of candidates) {
    try {
      execSync(`${c} --version`, { stdio: "pipe" });
      return c;
    } catch (e) { /* try next */ }
  }
  console.error("agent-conductor: Python 3.10+ is required but was not found.");
  console.error("Install it from https://python.org and re-run: npm install -g agent-conductor");
  process.exit(1);
}

function run(cmd) {
  execSync(cmd, { stdio: "inherit", cwd: pkgRoot });
}

const python = findPython();
const isWin = process.platform === "win32";
const venvPython = isWin ? path.join(venv, "Scripts", "python.exe") : path.join(venv, "bin", "python");

if (!fs.existsSync(venvPython)) {
  console.log("agent-conductor: creating virtual environment...");
  run(`${python} -m venv "${venv}"`);
}

console.log("agent-conductor: installing dependencies...");
run(`"${venvPython}" -m pip install --quiet --disable-pip-version-check python-dotenv openai rich fastapi uvicorn`);
console.log("agent-conductor: ready ✔  (run: agent-conductor --help)");
