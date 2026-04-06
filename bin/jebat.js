#!/usr/bin/env node
/**
 * ⚔️ JEBAT CLI — @nusabyte/jebat
 *
 * The LLM Ecosystem That Remembers Everything
 *
 * Usage:
 *   npx @nusabyte/jebat setup        Interactive setup wizard
 *   npx @nusabyte/jebat chat         AI assistant chat (REPL)
 *   npx @nusabyte/jebat install      Install JEBAT context to IDEs
 *   npx @nusabyte/jebat detect       Detect installed IDEs
 *   npx @nusabyte/jebat prompt       Print universal prompt
 *   npx @nusabyte/jebat doctor       Workspace health check
 *   npx @nusabyte/jebat status       Gateway + VPS status
 *   npx @nusabyte/jebat memory       Memory operations
 *   npx @nusabyte/jebat token-analyze  Count/analyze tokens
 *   npx @nusabyte/jebat token-compress Compress context
 *   npx @nusabyte/jebat skill-list   List installed skills
 *   npx @nusabyte/jebat skill-search Search skills catalog
 *   npx @nusabyte/jebat design-system  Browse design systems
 *   npx @nusabyte/jebat icon-search  Search tech icons
 *   npx @nusabyte/jebat deploy       VPS deployment helper
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

// ─── Constants ─────────────────────────────────────────────────────
const JEBAT_HOME = path.join(os.homedir(), ".jebat");
const GATEWAY_URL = process.env.JEBAT_GATEWAY_URL || "http://localhost:18789";
const IDE_TARGETS = {
  vscode: ".github/copilot-instructions.md",
  cursor: ".cursorrules",
  zed: ".zed/jebat-system-prompt.md",
  trae: ".trae/rules/jebat.md",
  antigravity: ".antigravity/jebat.md",
};

// ─── Helpers ────────────────────────────────────────────────────────
function log(msg, emoji = "") {
  const prefix = emoji ? `${emoji} ` : "";
  console.log(`${prefix}${msg}`);
}

function error(msg) {
  console.error(`❌ ${msg}`);
  process.exit(1);
}

function checkWorkspace() {
  const files = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"];
  const cwd = process.cwd();
  const found = files.filter((f) => fs.existsSync(path.join(cwd, f)));
  return { total: files.length, found: found.length, missing: files.filter((f) => !fs.existsSync(path.join(cwd, f))) };
}

function detectIDEs() {
  const home = os.homedir();
  const detected = [];
  if (fs.existsSync(path.join(home, ".vscode"))) detected.push("vscode");
  if (fs.existsSync(path.join(home, ".cursor"))) detected.push("cursor");
  if (fs.existsSync(path.join(home, ".zed"))) detected.push("zed");
  if (fs.existsSync(path.join(home, ".trae"))) detected.push("trae");
  return detected;
}

function checkGateway(url) {
  try {
    execSync(`curl -s -o /dev/null -w "%{http_code}" --max-time 3 ${url}/health`, { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

// ─── Commands ───────────────────────────────────────────────────────

function cmdSetup() {
  log("JEBAT Setup Wizard", "⚔️");
  log("");
  log("Step 1: Check workspace health...");
  const ws = checkWorkspace();
  log(`  Found ${ws.found}/${ws.total} core files`, ws.found === ws.total ? "✅" : "⚠️");
  if (ws.missing.length > 0) {
    ws.missing.forEach((f) => log(`    Missing: ${f}`, "  "));
  }

  log("");
  log("Step 2: Check gateway...");
  const gw = checkGateway(GATEWAY_URL);
  log(`  Gateway at ${GATEWAY_URL}: ${gw ? "✅ Online" : "⚠️ Offline"}`, gw ? "✅" : "⚠️");

  log("");
  log("Step 3: Detect IDEs...");
  const ides = detectIDEs();
  if (ides.length > 0) {
    ides.forEach((ide) => log(`  Found: ${ide}`, "✅"));
  } else {
    log("  No IDEs detected", "⚠️");
  }

  log("");
  log("Step 4: Install JEBAT context to IDEs?", "💻");
  log("  Run: npx @nusabyte/jebat install");

  log("");
  log("Step 5: Install skills?", "🗡️");
  log("  Run: npx @nusabyte/jebat skill-list");

  log("");
  log("Setup checklist complete! Use 'npx @nusabyte/jebat chat' to start chatting.", "⚔️");
}

function cmdInstall(targetDir) {
  const workspace = targetDir || process.cwd();
  log("Installing JEBAT context to IDEs...", "⚔️");
  log("");

  const contextFile = path.join(__dirname, "..", "adapters", "jebat", "JEBAT-CONTEXT.md");
  let context = "";
  if (fs.existsSync(contextFile)) {
    context = fs.readFileSync(contextFile, "utf8");
  } else {
    context = `# JEBAT Context — ${new Date().toISOString()}\n\nJEBAT is the primary AI operator for this workspace.\nNamed after Hang Jebat — loyal, sharp, decisive.\n\n## Core Rules\n- Direct answers, no filler\n- Search memory before claiming ignorance\n- Backup config before editing\n- Confirm before SSH or external actions\n\n## Skills\nPanglima, Hikmat, Tukang, Hulubalang, Pawang, Syahbandar, and 20+ more specialists.\n\n## Gateway\nSh4dow Gateway on port 18789 — multi-provider LLM routing.\n`;
  }

  let installed = 0;
  for (const [ide, file] of Object.entries(IDE_TARGETS)) {
    const target = path.join(workspace, file);
    const dir = path.dirname(target);
    if (!fs.existsSync(dir)) {
      try {
        fs.mkdirSync(dir, { recursive: true });
      } catch {
        log(`  ${ide}: Cannot create ${dir}`, "⚠️");
        continue;
      }
    }
    fs.writeFileSync(target, context);
    log(`  ${ide}: ${file}`, "✅");
    installed++;
  }

  log("");
  log(`Installed JEBAT context to ${installed} IDE(s). Restart your IDE to activate.`, "⚔️");
}

function cmdDoctor() {
  log("JEBAT Doctor — Workspace Health Check", "🩺");
  log("");

  // Workspace
  const ws = checkWorkspace();
  log(`Core files: ${ws.found}/${ws.total}`, ws.found === ws.total ? "✅" : "⚠️");

  // Gateway
  const gw = checkGateway(GATEWAY_URL);
  log(`Gateway: ${GATEWAY_URL}`, gw ? "✅" : "⚠️");

  // Skills
  const skillsDir = path.join(process.cwd(), "skills");
  if (fs.existsSync(skillsDir)) {
    const skills = fs.readdirSync(skillsDir).filter((f) => fs.statSync(path.join(skillsDir, f)).isDirectory());
    log(`Skills: ${skills.length} installed`, "✅");
  } else {
    log("Skills directory not found", "⚠️");
  }

  // Memory
  const memDir = path.join(process.cwd(), "memory");
  if (fs.existsSync(memDir)) {
    const memFiles = fs.readdirSync(memDir).filter((f) => f.endsWith(".md"));
    log(`Memory: ${memFiles} daily files`, "✅");
  } else {
    log("Memory directory not found", "⚠️");
  }

  // JEBAT home
  if (!fs.existsSync(JEBAT_HOME)) {
    fs.mkdirSync(JEBAT_HOME, { recursive: true });
    log(`Created: ${JEBAT_HOME}`, "✅");
  } else {
    log(`JEBAT home: ${JEBAT_HOME}`, "✅");
  }

  log("");
  const allGood = ws.found === ws.total && gw;
  log(allGood ? "All checks passed. JEBAT is healthy." : "Some checks failed. Review warnings above.", allGood ? "✅" : "⚠️");
}

function cmdStatus() {
  log("JEBAT System Status", "📡");
  log("");

  // Gateway
  const gw = checkGateway(GATEWAY_URL);
  log(`Gateway (${GATEWAY_URL})`, gw ? "✅ Online" : "❌ Offline");

  // VPS
  try {
    const code = execSync(`curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://jebat.online/api/v1/health 2>/dev/null || echo "000"`, { encoding: "utf8" }).trim();
    log("VPS (jebat.online)", code === "200" ? "✅ Healthy" : `⚠️ HTTP ${code}`);
  } catch {
    log("VPS (jebat.online)", "⚠️ Unreachable");
  }

  // WebUI
  try {
    const code = execSync(`curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://jebat.online/webui/ 2>/dev/null || echo "000"`, { encoding: "utf8" }).trim();
    log("WebUI (/webui/)", code === "200" ? "✅ Healthy" : `⚠️ HTTP ${code}`);
  } catch {
    log("WebUI (/webui/)", "⚠️ Unreachable");
  }

  log("");
  log(`NPM: @nusabyte/jebat v${require("../package.json").version}`, "✅");
}

function cmdSkillList() {
  const skillsDir = path.join(process.cwd(), "skills");
  if (!fs.existsSync(skillsDir)) {
    error("No skills directory found. Run: npx @nusabyte/jebat install");
  }

  log("Installed Skills", "🗡️");
  log("");

  const categories = {
    "Core": ["panglima", "memory-core", "hermes-agent", "agent-dispatch"],
    "Development": ["fullstack", "web-developer", "app-development", "database", "ui-ux", "qa-validation"],
    "Security": ["security-pentest", "jebat-cybersecurity", "jebat-hardening", "jebat-pentesting"],
    "Growth": ["seo", "marketing", "copywriting", "brand-strategy", "content-creation"],
    "Product": ["product-strategy", "senibina-antara-muka", "design-system", "penyebar-reka-bentuk"],
    "Operations": ["automation", "customer-success", "proposal-writing", "sales-enablement"],
    "Research": ["research-docs", "jebat-researcher", "jebat-analyst"],
    "Memory": ["jebat-memory-skill", "jebat-consolidation-skill"],
    "Orchestration": ["jebat-agent-orchestrator"],
  };

  for (const [cat, catSkills] of Object.entries(categories)) {
    log(`${cat}:`, "📂");
    const installed = fs.readdirSync(skillsDir);
    catSkills.forEach((skill) => {
      const found = installed.some((f) => f.toLowerCase().includes(skill.toLowerCase()));
      log(`  ${found ? "✅" : "❌"} ${skill}`);
    });
    log("");
  }
}

function cmdTokenAnalyze(text) {
  // Rough estimation: ~4 chars per token for English
  const chars = text.length;
  const tokens = Math.ceil(chars / 4);
  log(`Token Analysis`, "🔢");
  log(`Characters: ${chars.toLocaleString()}`);
  log(`Estimated tokens: ~${tokens.toLocaleString()}`);
  log(`Model context usage:`);
  log(`  GPT-4o: ~${(tokens * 1.1).toFixed(0)} tokens (with overhead)`);
  log(`  Claude: ~${(tokens * 1.05).toFixed(0)} tokens (with overhead)`);
}

function cmdHelp() {
  console.log(`
⚔️  JEBAT CLI — @nusabyte/jebat
The LLM Ecosystem That Remembers Everything

Usage:
  npx @nusabyte/jebat <command>

Commands:
  setup            Interactive setup wizard
  chat             AI assistant chat (REPL mode)
  install [dir]    Install JEBAT context to IDEs
  detect           Detect installed IDEs
  prompt           Print universal prompt
  doctor           Workspace health check
  status           Gateway + VPS status
  memory           Memory operations (stats, search)
  token-analyze    Count/analyze tokens
  token-compress   Compress context
  skill-list       List installed skills
  skill-search     Search skills catalog
  design-system    Browse design systems
  icon-search      Search tech icons
  deploy           VPS deployment helper
  help             Show this help

Examples:
  npx @nusabyte/jebat setup
  npx @nusabyte/jebat chat
  npx @nusabyte/jebat install
  npx @nusabyte/jebat doctor
  npx @nusabyte/jebat status
  echo "some text" | npx @nusabyte/jebat token-analyze
`);
}

// ─── Router ─────────────────────────────────────────────────────────

const [cmd, ...args] = process.argv.slice(2);

switch (cmd) {
  case "setup":
    cmdSetup();
    break;
  case "install":
    cmdInstall(args[0]);
    break;
  case "detect":
    const ides = detectIDEs();
    log(`Detected IDEs: ${ides.length > 0 ? ides.join(", ") : "none"}`, "💻");
    break;
  case "doctor":
    cmdDoctor();
    break;
  case "status":
    cmdStatus();
    break;
  case "prompt":
    const promptFile = path.join(__dirname, "..", "adapters", "jebat", "jebat-universal-prompt.md");
    if (fs.existsSync(promptFile)) {
      console.log(fs.readFileSync(promptFile, "utf8"));
    } else {
      log("Universal prompt file not found", "⚠️");
    }
    break;
  case "skill-list":
    cmdSkillList();
    break;
  case "token-analyze":
    if (process.stdin.isTTY) {
      log("Usage: echo 'text' | npx @nusabyte/jebat token-analyze", "📖");
    } else {
      let data = "";
      process.stdin.on("data", (chunk) => (data += chunk));
      process.stdin.on("end", () => cmdTokenAnalyze(data));
    }
    break;
  case "memory":
    log("Memory operations — coming in next update", "🧠");
    log("  Local memory files exist:", "📂");
    const memDir = path.join(process.cwd(), "memory");
    if (fs.existsSync(memDir)) {
      fs.readdirSync(memDir).filter((f) => f.endsWith(".md")).forEach((f) => log(`    ${f}`));
    }
    break;
  case "chat":
    log("Chat mode — requires gateway connection.", "💬");
    log("  Ensure gateway is running on port 18789");
    log("  Run: npx @nusabyte/jebat status");
    log("  For full interactive chat, see: /demo in the web UI");
    break;
  case "design-system":
  case "icon-search":
    log("Browse the skills.sh catalog at:", "🎨");
    log("  https://skills.sh/");
    break;
  case "deploy":
    log("VPS Deployment Helper", "🚀");
    log("");
    log("Target: root@72.62.254.65");
    log("Source: /root/jebat-core/");
    log("Nginx: /etc/nginx/sites-enabled/jebat.online");
    log("");
    log("To deploy:");
    log("  1. ssh root@72.62.254.65");
    log("  2. cd /root/jebat-core && git pull");
    log("  3. docker compose -f deploy/vps/docker-compose.prod.yml up -d");
    log("  4. docker ps — verify containers");
    break;
  case "help":
  case undefined:
  case "--help":
  case "-h":
    cmdHelp();
    break;
  default:
    log(`Unknown command: ${cmd}`, "❌");
    cmdHelp();
    process.exit(1);
}
