#!/usr/bin/env node

/**
 * jebatcore CLI — thin wrapper that bootstraps Python JEBAT if needed.
 *
 * This is what `npx jebat` or `npx jebatcore` runs. It:
 * 1. Checks if Python + jebat package is installed
 * 2. If not, installs them via pip
 * 3. Forwards all args to the real `jebat` Python CLI
 *
 * This mirrors the pattern used by Hermes Agent's npm package.
 */

const { spawn, execSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");

// ── Configuration ──────────────────────────────────────────────────────────

const JEBAT_PYTHON_PKG = "jebat";
const JEBAT_MIN_PYTHON = "3.10";
const PIP_INSTALL_ARGS = ["pip", "install", "--upgrade", JEBAT_PYTHON_PKG];

// ── Helpers ────────────────────────────────────────────────────────────────

function findPython() {
  // Try python3 first, then python, then py (Windows)
  const candidates = ["python3", "python", "py"];
  for (const cmd of candidates) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: "utf8", stdio: "pipe" });
      const match = version.match(/Python (\d+\.\d+)/);
      if (match && parseFloat(match[1]) >= parseFloat(JEBAT_MIN_PYTHON)) {
        return cmd;
      }
    } catch {
      continue;
    }
  }
  return null;
}

function isJebatInstalled(pythonCmd) {
  try {
    execSync(`${pythonCmd} -c "import jebat"`, { encoding: "utf8", stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

function installJebat(pythonCmd) {
  console.log(`[jebatcore] Installing JEBAT Python package via pip...`);
  try {
    execSync(`${pythonCmd} ${PIP_INSTALL_ARGS.join(" ")}`, {
      encoding: "utf8",
      stdio: "inherit",
    });
    console.log(`[jebatcore] JEBAT installed successfully.`);
    return true;
  } catch (err) {
    console.error(`[jebatcore] Failed to install JEBAT: ${err.message}`);
    console.error(`[jebatcore] Try manually: ${pythonCmd} pip install ${JEBAT_PYTHON_PKG}`);
    return false;
  }
}

// ── Main ────────────────────────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);

  // Special: if user runs 'jebatcore mcp-client', use the Node.js MCP client
  if (args[0] === "mcp-client") {
    const { JebatMCPClient } = require("./mcp-client");
    const transport = args[1] || "stdio";
    const mcpUrl = process.env.JEBAT_MCP_URL || "http://127.0.0.1:8100/mcp";
    const client = new JebatMCPClient({ transport, url: mcpUrl });

    client.connect().then(async (info) => {
      console.log("[jebatcore] Connected to JEBAT MCP server:", JSON.stringify(info, null, 2));
      const tools = await client.listTools();
      console.log("[jebatcore] Available tools:", tools.tools.map(t => t.name).join(", "));
      console.log("[jebatcore] MCP bridge running. Press Ctrl+C to disconnect.");
      // Keep alive — SIGINT handler prevents Node from exiting
      process.on("SIGINT", () => {
        console.log("[jebatcore] Disconnecting...");
        client.disconnect().catch(() => {});
        setTimeout(() => process.exit(0), 1000);
      });
      // Keep the process alive by setting a periodic heartbeat
      setInterval(() => {}, 60000);
    }).catch(err => {
      console.error("[jebatcore] MCP connection error:", err.message);
      process.exit(1);
    });
    return;
  }

  // Standard: bootstrap Python JEBAT and forward all args
  const pythonCmd = findPython();
  if (!pythonCmd) {
    console.error(`[jebatcore] Python ${JEBAT_MIN_PYTHON}+ not found. Install Python first.`);
    console.error(`[jebatcore] Download: https://python.org/downloads/`);
    process.exit(1);
  }

  if (!isJebatInstalled(pythonCmd)) {
    const success = installJebat(pythonCmd);
    if (!success) process.exit(1);
  }

  // Forward all args to the real jebat Python CLI
  const child = spawn(pythonCmd, ["-m", "jebat.cli.jebat_cli", ...args], {
    stdio: "inherit",
    env: { ...process.env },
  });

  child.on("exit", (code) => process.exit(code || 0));
  child.on("error", (err) => {
    console.error(`[jebatcore] Error running JEBAT: ${err.message}`);
    process.exit(1);
  });
}

main();