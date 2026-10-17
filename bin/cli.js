#!/usr/bin/env node
/* Launcher: runs the bundled python package with the venv interpreter,
   from the USER'S current directory (so .env + projects/ live there). */

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const isWin = process.platform === "win32";
const venvPython = isWin
  ? path.join(__dirname, "..", ".venv", "Scripts", "python.exe")
  : path.join(__dirname, "..", ".venv", "bin", "python");

if (!fs.existsSync(venvPython)) {
  console.log("agent-conductor: first run - setting up python venv (one time, ~30s)...");
  const { execSync } = require("child_process");
  try {
    execSync(`node "${path.join(__dirname, "setup.js")}"`, { stdio: "inherit" });
  } catch (e) {
    console.error("agent-conductor: setup failed. Is Python 3.10+ installed?");
    process.exit(1);
  }
}

const args = process.argv.slice(2);
const child = spawn(venvPython, ["-m", "agent_conductor", ...args], {
  cwd: process.cwd(),
  stdio: "inherit",
  env: { ...process.env, PYTHONPATH: path.join(__dirname, "..") },
});

child.on("exit", (code) => process.exit(code ?? 0));
