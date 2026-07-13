#!/usr/bin/env node
// JEBAT npm wrapper - installs Python package and runs CLI
// Usage: npx jebat [args...] or bunx jebat [args...]

import { spawnSync, spawn } from 'child_process';
import { existsSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PACKAGE_NAME = 'jebat';
const PYTHON_CMD = process.platform === 'win32' ? 'python.exe' : 'python3';

function log(msg) {
  console.error(`[jebat] ${msg}`);
}

function error(msg) {
  console.error(`[jebat] ERROR: ${msg}`);
  process.exit(1);
}

function checkPython() {
  try {
    const result = spawnSync(PYTHON_CMD, ['--version'], { stdio: 'pipe' });
    if (result.status !== 0) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

function checkPip() {
  try {
    const result = spawnSync(PYTHON_CMD, ['-m', 'pip', '--version'], { stdio: 'pipe' });
    return result.status === 0;
  } catch {
    return false;
  }
}

function installJebat() {
  log('Bootstrapping JEBAT via the installer...');
  const installer = spawnSync('bash', ['-c', 'curl -fsSL https://jebat.online/install.sh | bash'], {
    stdio: 'inherit',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });
  if (installer.status !== 0) {
    error('Failed to bootstrap JEBAT. See https://jebat.online/install.sh');
  }
  log('JEBAT bootstrapped successfully!');
}

function runJebat(args) {
  const pythonArgs = ['-m', 'jebat_cli_new', ...args];
  
  // Use spawn for interactive mode (REPL)
  const isInteractive = args.includes('repl') || args.length === 0;
  
  if (isInteractive && process.stdin.isTTY) {
    // Interactive mode - use spawn with stdio inherit
    const child = spawn(PYTHON_CMD, pythonArgs, {
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' }
    });
    
    child.on('error', (err) => {
      error(`Failed to start JEBAT: ${err.message}`);
    });
    
    child.on('exit', (code) => {
      process.exit(code || 0);
    });
    
    // Handle signals
    process.on('SIGINT', () => child.kill('SIGINT'));
    process.on('SIGTERM', () => child.kill('SIGTERM'));
  } else {
    // Non-interactive mode - use spawnSync
    const result = spawnSync(PYTHON_CMD, pythonArgs, {
      stdio: 'inherit',
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
    });
    process.exit(result.status || 0);
  }
}

async function main() {
  const args = process.argv.slice(2);
  
  // Handle special flags
  if (args.includes('--help') || args.includes('-h') || args.includes('help')) {
    console.log(`JEBAT v8.2.0 — Sovereign Agent OS & Agent Workstation
    
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
  npx jebat agent "Analyze this codebase"
  npx jebat code "Create a REST API"
  npx jebat webui
  npx jebat config show

Installation:
  This wrapper installs the Python package automatically on first run.
  Requires: Python 3.11+ and pip

Remote Ollama:
  JEBAT uses https://jebat.online/ollama as the default endpoint.
  Models: qwen2.5-coder:7b, qwen2.5:14b (CPU inference on AMD EPYC)
`);
    return;
  }
  
  if (args.includes('--version') || args.includes('-v')) {
    console.log('JEBAT 8.2.0 (npm wrapper)');
    return;
  }
  
  // Check Python
  if (!checkPython()) {
    error('Python 3.11+ not found. Please install Python from https://python.org');
  }
  
  // Check pip
  if (!checkPip()) {
    error('pip not found. Please install pip (usually comes with Python).');
  }
  
  // Check if jebat is installed
  const checkResult = spawnSync(PYTHON_CMD, ['-c', 'import jebat_cli_new; print("OK")'], { 
    stdio: 'pipe', 
    encoding: 'utf-8'
  });
  
  if (checkResult.status !== 0) {
    log('JEBAT not found. Installing...');
    installJebat();
  } else {
    log(`JEBAT installed`);
  }
  
  // Run JEBAT
  runJebat(args);
}

main().catch(err => {
  error(`Unexpected error: ${err.message}`);
});