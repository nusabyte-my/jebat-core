#!/usr/bin/env node
// JEBAT npm wrapper — installs the Python package and runs the CLI.
// Agent-friendly: non-interactive, no prompts, clean exit codes, and a
// bootstrap URL that always serves plaintext (raw GitHub), with a fallback
// if the CDN/proxy ever returns HTML instead of the script.
//
// Usage: npx @nusabyte/jebat [command] [options]

import { spawnSync, spawn } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { platform } from 'os';
import https from 'https';
import os from 'os';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PACKAGE_NAME = 'jebat';
const JEBAT_VERSION = '8.2.0';

// Canonical bootstrap script. The raw GitHub URL ALWAYS serves the script as
// plaintext, so it is the reliable default for both humans and agents.
const INSTALL_SCRIPT_URL = 'https://raw.githubusercontent.com/nusabyte-my/jebat-core/main/install.sh';
// Fallback CDN URL (proxied). Only used if the primary fails or returns HTML.
const INSTALL_SCRIPT_URL_ALT = 'https://jebat.online/install.sh';

const IS_WIN = platform() === 'win32';
const PYTHON_CMD = process.env.JEBAT_PYTHON || (IS_WIN ? 'python.exe' : 'python3');

function log(msg) { console.error(`[jebat] ${msg}`); }
function error(msg) { console.error(`[jebat] ERROR: ${msg}`); process.exit(1); }

// ── helpers ───────────────────────────────────────────────────────────────
function hasCommand(cmd) {
  const r = spawnSync(IS_WIN ? 'where' : 'command', IS_WIN ? [cmd] : ['-v', cmd], { stdio: 'pipe' });
  return r.status === 0;
}

function findPython() {
  for (const c of [process.env.JEBAT_PYTHON, 'python3', 'python', 'py'].filter(Boolean)) {
    const r = spawnSync(c, ['--version'], { stdio: 'pipe' });
    if (r.status === 0) return c;
  }
  return null;
}

// Fetch a URL and return { ok, isHtml, body }
function fetchText(url) {
  return new Promise((resolve) => {
    const req = https.get(url, { timeout: 20000 }, (res) => {
      if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        return resolve(fetchText(res.headers.location));
      }
      if (!res.statusCode || res.statusCode >= 400) {
        res.resume();
        return resolve({ ok: false, isHtml: false, body: '' });
      }
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const body = Buffer.concat(chunks).toString('utf8');
        const isHtml = /^\s*<!DOCTYPE html/i.test(body) || /^\s*<html/i.test(body);
        resolve({ ok: true, isHtml, body });
      });
    });
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, isHtml: false, body: '' }); });
    req.on('error', () => resolve({ ok: false, isHtml: false, body: '' }));
  });
}

// Download the installer and run it with bash (--yes --quiet for agents/CI).
// Falls back to the alternate URL if the primary returns HTML or fails.
async function installJebat() {
  log('Bootstrapping JEBAT via the installer…');

  if (!hasCommand('bash')) {
    if (IS_WIN) {
      error('bash not found. On Windows, install Git for Windows (adds bash to PATH) or run inside WSL, then retry: npx @nusabyte/jebat repl');
    }
    error('bash not found. Install bash and retry: npx @nusabyte/jebat repl');
  }

  const tryUrl = async (url) => {
    const r = await fetchText(url);
    if (!r.ok) { warnOnce(`could not fetch ${url}`); return false; }
    if (r.isHtml) { warnOnce(`${url} returned HTML instead of a script; trying fallback.`); return false; }
    const tmp = resolve(os.tmpdir(), `jebat-install-${Date.now()}.sh`);
    fs.writeFileSync(tmp, r.body, { mode: 0o755 });
    const install = spawnSync('bash', [tmp, '--yes', '--quiet'], {
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    fs.unlinkSync(tmp);
    return install.status === 0;
  };

  if (await tryUrl(INSTALL_SCRIPT_URL)) return true;
  if (await tryUrl(INSTALL_SCRIPT_URL_ALT)) return true;
  error('Failed to download the JEBAT installer. See https://jebat.online/install.html');
  return false;
}

let _warned = false;
function warnOnce(msg) { if (!_warned) { _warned = true; console.error(`[jebat] ${msg}`); } }

function runJebat(args) {
  const pythonArgs = ['-m', 'jebat_cli_new', ...args];
  const isInteractive = args.includes('repl') || args.length === 0;

  if (isInteractive && process.stdin.isTTY) {
    const child = spawn(PYTHON_CMD, pythonArgs, {
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' },
    });
    child.on('error', (err) => error(`Failed to start JEBAT: ${err.message}`));
    child.on('exit', (code) => process.exit(code || 0));
    process.on('SIGINT', () => child.kill('SIGINT'));
    process.on('SIGTERM', () => child.kill('SIGTERM'));
  } else {
    const result = spawnSync(PYTHON_CMD, pythonArgs, {
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    process.exit(result.status || 0);
  }
}

function printHelp() {
  console.log(`JEBAT v${JEBAT_VERSION} — Sovereign Agent OS & Agent Workstation

Usage: npx jebat [command] [options]

Commands:
  repl              Start interactive REPL (default)
  chat <prompt>     One-shot chat with tool calling
  agent <prompt>    Run one-shot agent task
  code <prompt>     Generate code from description
  webui             Launch Stealth-Dark WebUI
  config show|set   Configuration management
  file read|write|patch|search|undo|tree  File operations
  tools list|inspect  List/inspect registered tools
  memory store|search|stats  Memory operations
  status            System status
  --version         Show version
  --help            Show this help

Examples:
  npx jebat repl
  npx jebat chat "Hello JEBAT"
  npx jebat agent "Audit all API endpoints in src/services"
  npx jebat code "Create a REST API"
  npx jebat webui

Installation:
  This wrapper installs the Python package automatically on first run.
  Requires: Python 3.11+ and pip. No sudo required.
  For AI agents / CI, the installer is fully non-interactive (--yes --quiet).

MCP:
  The npm launcher does not host an MCP server. From a full workspace checkout:
    python ./jebat-mcp --transport stdio
  See https://github.com/nusabyte-my/jebat-core/blob/main/MCP.md
`);
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h') || args.includes('help')) {
    printHelp();
    return;
  }
  if (args.includes('--version') || args.includes('-v')) {
    console.log(`JEBAT ${JEBAT_VERSION} (npm wrapper)`);
    return;
  }

  const py = findPython();
  if (!py) error('Python 3.11+ not found. Install it from https://python.org and retry.');

  const check = spawnSync(py, ['-c', 'import jebat_cli_new; print("OK")'], { stdio: 'pipe', encoding: 'utf-8' });

  if (check.status !== 0) {
    log('JEBAT not found. Installing…');
    const ok = await installJebat();
    if (!ok) process.exit(1);
    const recheck = spawnSync(py, ['-c', 'import jebat_cli_new; print("OK")'], { stdio: 'pipe', encoding: 'utf-8' });
    if (recheck.status !== 0) error('JEBAT install did not complete. Check the logs above.');
  } else {
    log('JEBAT already installed.');
  }

  runJebat(args);
}

main().catch((err) => error(`Unexpected error: ${err.message}`));
