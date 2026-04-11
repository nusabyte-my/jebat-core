#!/usr/bin/env node
/**
 * ⚔️ JEBAT CLI — jebat-core
 *
 * The LLM Ecosystem That Remembers Everything
 *
 * Usage:
 *   npx jebat-core setup          Full onboarding + integration setup
 *   npx jebat-core onboard        User onboarding wizard
 *   npx jebat-core chat           AI assistant chat (REPL)
 *   npx jebat-core install        Install JEBAT context to IDEs
 *   npx jebat-core detect         Detect installed IDEs
 *   npx jebat-core prompt         Print universal prompt
 *   npx jebat-core doctor         Workspace health check
 *   npx jebat-core status         Gateway + VPS + agents status
 *   npx jebat-core memory         Memory operations
 *   npx jebat-core agents         List registered agents
 *   npx jebat-core token-analyze  Count/analyze tokens
 *   npx jebat-core token-compress Compress context
 *   npx jebat-core skill-list     List installed skills
 *   npx jebat-core skill-search   Search skills catalog
 *   npx jebat-core skill-sync     Sync skills from VPS
 *   npx jebat-core skill-push     Push skills to VPS
 *   npx jebat-core design-system  Browse design systems
 *   npx jebat-core icon-search    Search tech icons
 *   npx jebat-core deploy         VPS deployment helper
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");
const readline = require("readline");
const http = require("http");
const https = require("https");

// ─── Constants ─────────────────────────────────────────────────────
const JEBAT_HOME = path.join(os.homedir(), ".jebat");
const JEBAT_CONFIG = path.join(JEBAT_HOME, "config.json");
const VPS_SKILLS_CACHE = path.join(JEBAT_HOME, "vps-skills");
const GATEWAY_URL = process.env.JEBAT_GATEWAY_URL || "http://localhost:18789";
const API_URL = process.env.JEBAT_API_URL || "http://localhost:8080";
const VPS_SKILLS_URL = "https://jebat.online/api/v1/skills";
const VPS_SKILLS_SSH = "root@72.62.254.65:/root/jebat-core/skills";
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

function warn(msg) {
  console.log(`⚠️  ${msg}`);
}

function success(msg) {
  console.log(`✅ ${msg}`);
}

function divider(label) {
  const line = "═".repeat(60);
  console.log(`\n${line}`);
  if (label) console.log(`  ${label}`);
  console.log(`${line}\n`);
}

function rl() {
  return readline.createInterface({ input: process.stdin, output: process.stdout });
}

function ask(question, defaultVal = "") {
  return new Promise((resolve) => {
    const iface = rl();
    const prompt = defaultVal ? `${question} [${defaultVal}]: ` : `${question}: `;
    iface.question(prompt, (answer) => {
      iface.close();
      resolve((answer || defaultVal).trim());
    });
  });
}

function askMultiLine(question) {
  return new Promise((resolve) => {
    const iface = rl();
    console.log(`${question} (end with empty line or Ctrl+C):`);
    const lines = [];
    iface.on("line", (line) => {
      if (line.trim() === "") {
        iface.close();
        resolve(lines.join("\n"));
        return;
      }
      lines.push(line);
    });
  });
}

function askChoice(question, choices, defaultIdx = 0) {
  return new Promise((resolve) => {
    const iface = rl();
    console.log(question);
    choices.forEach((c, i) => {
      const marker = i === defaultIdx ? " (default)" : "";
      console.log(`  ${i + 1}. ${c}${marker}`);
    });
    iface.question(`Choose [1-${choices.length}]: `, (answer) => {
      iface.close();
      const idx = parseInt(answer, 10) - 1;
      resolve(Number.isInteger(idx) && idx >= 0 && idx < choices.length ? choices[idx] : choices[defaultIdx]);
    });
  });
}

function askYesNo(question, defaultYes = true) {
  return new Promise((resolve) => {
    const iface = rl();
    const prompt = `${question} [${defaultYes ? "Y/n" : "y/N"}]: `;
    iface.question(prompt, (answer) => {
      iface.close();
      const v = answer.trim().toLowerCase();
      if (v === "") return resolve(defaultYes);
      resolve(v === "y" || v === "yes");
    });
  });
}

// ─── Config ─────────────────────────────────────────────────────────

function loadConfig() {
  if (fs.existsSync(JEBAT_CONFIG)) {
    try {
      return JSON.parse(fs.readFileSync(JEBAT_CONFIG, "utf8"));
    } catch {
      return {};
    }
  }
  return {};
}

function saveConfig(cfg) {
  if (!fs.existsSync(JEBAT_HOME)) fs.mkdirSync(JEBAT_HOME, { recursive: true });
  fs.writeFileSync(JEBAT_CONFIG, JSON.stringify(cfg, null, 2));
}

// ─── HTTP helpers ───────────────────────────────────────────────────

function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : http;
    mod.get(url, { timeout }, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => resolve({ status: res.statusCode, body: data }));
    }).on("error", reject).on("timeout", (req) => { req.destroy(); reject(new Error("timeout")); });
  });
}

function httpPostJson(url, body, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const mod = urlObj.protocol === "https:" ? https : http;
    const payload = JSON.stringify(body);
    const opts = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
      },
      timeout,
    };
    const req = mod.request(opts, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error("timeout")); });
    req.write(payload);
    req.end();
  });
}

// ─── Checks ─────────────────────────────────────────────────────────

function checkWorkspace() {
  const files = ["AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md"];
  const cwd = process.cwd();
  const found = [];
  const missing = [];
  for (const f of files) {
    if (fs.existsSync(path.join(cwd, f)) || fs.existsSync(path.join(cwd, "core", f))) {
      found.push(f);
    } else {
      missing.push(f);
    }
  }
  return { total: files.length, found: found.length, missing };
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

async function checkGateway(url) {
  try {
    const res = await httpGet(`${url}/health`, 3000);
    return res.status === 200;
  } catch {
    return false;
  }
}

async function checkAgents() {
  try {
    const res = await httpGet(`${API_URL}/api/v1/agents`, 5000);
    if (res.status === 200) {
      const data = typeof res.body === "string" ? JSON.parse(res.body) : res.body;
      return data;
    }
  } catch {
    // try gateway port too
    try {
      const res2 = await httpGet(`${GATEWAY_URL}/api/v1/agents`, 5000);
      if (res2.status === 200) {
        const data = typeof res2.body === "string" ? JSON.parse(res2.body) : res2.body;
        return data;
      }
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Fetch skills from VPS API or local directories.
 */
async function fetchVpsSkills() {
  try {
    const res = await httpGet(VPS_SKILLS_URL, 10000);
    if (res.status === 200) {
      const data = typeof res.body === "string" ? JSON.parse(res.body) : res.body;
      return { source: "vps-api", skills: data.skills || [] };
    }
  } catch {
    // Try local directories
  }

  const skillsDirs = [
    path.join(process.cwd(), "skills"),
    path.join(process.cwd(), "packages", "skills", "skills"),
    path.join(JEBAT_HOME, "bundle", "skills"),
    VPS_SKILLS_CACHE,
  ];
  let skillsDir = null;
  for (const dir of skillsDirs) {
    if (fs.existsSync(dir)) { skillsDir = dir; break; }
  }
  if (!skillsDir) return { source: "local", skills: [] };

  const skills = [];
  const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory() && !entry.name.startsWith(".")) {
      const skillMd = path.join(skillsDir, entry.name, "SKILL.md");
      let name = entry.name;
      let description = "";
      if (fs.existsSync(skillMd)) {
        const content = fs.readFileSync(skillMd, "utf8");
        const match = content.match(/name:\s*(.+)/);
        if (match) name = match[1].trim().replace(/['"]/g, "");
        const descMatch = content.match(/description:\s*(.+)/);
        if (descMatch) description = descMatch[1].trim().replace(/['"]/g, "");
      }
      skills.push({ name, description, source: "local" });
    }
  }
  return { source: "local", skills };
}

/**
 * Sync skills from VPS to local cache.
 */
async function cmdSkillSync() {
  divider("🔄  VPS Skills Sync");
  log(`Syncing from: ${VPS_SKILLS_URL}`, "🌐");

  try {
    const res = await httpGet(VPS_SKILLS_URL, 10000);
    if (res.status === 200) {
      const data = typeof res.body === "string" ? JSON.parse(res.body) : res.body;
      const skills = data.skills || [];

      if (skills.length === 0) {
        log("No skills found on VPS", "⚠️");
        return;
      }

      // Sync to local cache
      if (!fs.existsSync(VPS_SKILLS_CACHE)) fs.mkdirSync(VPS_SKILLS_CACHE, { recursive: true });

      for (const skill of skills) {
        const skillDir = path.join(VPS_SKILLS_CACHE, skill.name);
        if (!fs.existsSync(skillDir)) fs.mkdirSync(skillDir, { recursive: true });
        const skillMd = path.join(skillDir, "SKILL.md");
        if (!fs.existsSync(skillMd)) {
          const content = `---\nname: ${skill.name}\ndescription: ${skill.description || ""}\ncategory: ${skill.category || "general"}\nversion: ${skill.version || "1.0.0"}\n---\n\n# ${skill.name}\n\n${skill.description || ""}\n`;
          fs.writeFileSync(skillMd, content);
        }
      }

      success(`Synced ${skills.length} skills from VPS`);
      log(`Cached at: ${VPS_SKILLS_CACHE}`);
      return;
    }
  } catch {
    warn("VPS API unreachable");
  }

  // Fallback: rsync via SSH
  try {
    log("Falling back to SSH rsync...");
    if (!fs.existsSync(VPS_SKILLS_CACHE)) fs.mkdirSync(VPS_SKILLS_CACHE, { recursive: true });
    execSync(`rsync -avz --delete ${VPS_SKILLS_SSH}/ ${VPS_SKILLS_CACHE}/`, { stdio: "inherit", timeout: 30000 });
    success("Skills synced via SSH");
  } catch (e) {
    error(`SSH sync failed: ${e.message}`);
  }
}

/**
 * Push local skills to VPS.
 */
async function cmdSkillPush() {
  divider("📤  Push Skills to VPS");

  const skillsDirs = [
    path.join(process.cwd(), "skills"),
    path.join(process.cwd(), "packages", "skills", "skills"),
    path.join(JEBAT_HOME, "bundle", "skills"),
  ];
  let skillsDir = null;
  for (const dir of skillsDirs) {
    if (fs.existsSync(dir)) { skillsDir = dir; break; }
  }
  if (!skillsDir) {
    error("No skills directory found to push.");
    return;
  }

  log(`Pushing from: ${skillsDir}`, "📁");
  log(`To: ${VPS_SKILLS_SSH}`, "🌐");

  const doPush = await askYesNo("Continue?", true);
  if (!doPush) {
    log("Cancelled", "⚠️");
    return;
  }

  try {
    execSync(`rsync -avz ${skillsDir}/ ${VPS_SKILLS_SSH}/`, { stdio: "inherit", timeout: 30000 });
    success("Skills pushed to VPS");
  } catch (e) {
    error(`Push failed: ${e.message}`);
  }
}

// ─── Onboarding ─────────────────────────────────────────────────────

async function cmdOnboard() {
  divider("⚔️  JEBAT User Onboarding");

  const config = loadConfig();

  // Step 1: Who is the user
  log("Step 1 of 4 — Who are you?", "👤");
  const name = await ask("Your name or handle", config.userName || "");
  const role = await ask("Your role (e.g. developer, founder, designer)", config.userRole || "");

  // Step 2: What does the user want
  log("", "");
  log("Step 2 of 4 — What do you want JEBAT to help with?", "🎯");
  log("Common uses:");
  log("  1. Coding & development (building features, debugging)");
  log("  2. Research & analysis (comparing tools, investigating topics)");
  log("  3. Security review (pentesting, hardening, audit)");
  log("  4. Operations & deployment (CI/CD, Docker, infra)");
  log("  5. Content & growth (writing, SEO, marketing)");
  log("  6. All of the above (general assistant)");
  const useCase = await askChoice("Primary use case:", [
    "coding", "research", "security", "operations", "content", "general"
  ], 5);

  // Step 3: Working style preferences
  log("", "");
  log("Step 3 of 4 — How should JEBAT behave?", "⚙️");
  const style = await askChoice("Response style:", [
    "direct — short answers, no filler",
    "detailed — thorough explanations",
    "balanced — concise but complete"
  ], 0);

  const language = await ask("Preferred language (default: English)", config.language || "English");

  const confirmBeforeAction = await askYesNo("Confirm before making changes to files?", true);
  const useMemory = await askYesNo("Enable persistent memory (JEBAT remembers past work)?", true);

  // Step 4: Gateway / API
  log("", "");
  log("Step 4 of 4 — Gateway connection", "🔗");
  const gwUrl = await ask("Gateway URL", config.gatewayUrl || GATEWAY_URL);

  // Save
  config.userName = name || config.userName || "User";
  config.userRole = role || config.userRole || "";
  config.useCase = useCase;
  config.responseStyle = style;
  config.language = language || "English";
  config.confirmBeforeAction = confirmBeforeAction;
  config.useMemory = useMemory;
  config.gatewayUrl = gwUrl;
  config.onboardedAt = new Date().toISOString();

  saveConfig(config);

  // Generate USER.md if workspace exists
  const cwd = process.cwd();
  const userMdPath = path.join(cwd, "USER.md");
  if (!fs.existsSync(userMdPath) || await askYesNo("Overwrite USER.md in current workspace?", false)) {
    const userMd = `# USER.md — JEBAT User Profile

**Name**: ${config.userName}
**Role**: ${config.userRole || "Not specified"}
**Language**: ${config.language}

## Primary Use Case
${config.useCase}

## Working Style
- Response style: ${config.responseStyle}
- Confirm before changes: ${config.confirmBeforeAction ? "yes" : "no"}
- Persistent memory: ${config.useMemory ? "enabled" : "disabled"}

## Preferences
- JEBAT should be ${config.responseStyle.includes("direct") ? "direct and concise" : config.responseStyle.includes("detailed") ? "thorough and explanatory" : "balanced — concise but complete"}
- Gateway: ${config.gatewayUrl}
`;
    fs.writeFileSync(userMdPath, userMd);
    success("USER.md written to workspace");
  }

  divider("Onboarding Complete");
  log(`Welcome, ${config.userName}! JEBAT is configured for ${config.useCase}.`, "⚔️");
  log("");
  log("Next steps:");
  log("  1. npx jebat-core setup    — Full integration setup");
  log("  2. npx jebat-core install  — Install IDE context");
  log("  3. npx jebat-core status   — Check system health");
  log("");
}

// ─── Setup (full integration) ───────────────────────────────────────

async function cmdSetup() {
  divider("⚔️  JEBAT Setup Wizard");

  const config = loadConfig();

  // Step 0: Onboarding if not done
  if (!config.onboardedAt) {
    log("You haven't been onboarded yet. Let's fix that.", "📋");
    const doOnboard = await askYesNo("Run onboarding now?", true);
    if (doOnboard) {
      await cmdOnboard();
      // Reload config after onboarding
      Object.assign(config, loadConfig());
    } else {
      log("Skipping onboarding. You can run it later with: npx jebat-core onboard", "⚠️");
    }
  }

  // Step 1: Workspace health
  log("Step 1 — Workspace health", "📁");
  const ws = checkWorkspace();
  if (ws.found === ws.total) {
    success(`Core files: ${ws.found}/${ws.total}`);
  } else {
    warn(`Core files: ${ws.found}/${ws.total}`);
    ws.missing.forEach((f) => log(`  Missing: ${f}`));
  }

  // Step 2: Gateway
  log("", "");
  log("Step 2 — Gateway connection", "🔗");
  const gwUrl = config.gatewayUrl || GATEWAY_URL;
  const gwOk = await checkGateway(gwUrl);
  if (gwOk) {
    success(`Gateway online at ${gwUrl}`);
  } else {
    warn(`Gateway offline at ${gwUrl}`);
    log("  The gateway provides LLM routing and agent access.");
    log("  Start it with: python -m uvicorn apps.api.services.api.jebat_api:app --port 18789");
    const retryGw = await askYesNo("  Retry gateway check?", false);
    if (retryGw) {
      if (await checkGateway(gwUrl)) {
        success("Gateway is now online");
      } else {
        warn("Gateway still offline — you can continue setup without it");
      }
    }
  }

  // Step 3: Agents
  log("", "");
  log("Step 3 — Agent registry", "🤖");
  const agents = await checkAgents();
  if (agents && agents.total > 0) {
    success(`${agents.total} agents registered`);
    if (agents.agents) {
      agents.agents.slice(0, 5).forEach((a) => {
        log(`  • ${a.agent_name} (${a.agent_role}) — ${a.provider}/${a.model}`);
      });
      if (agents.agents.length > 5) log(`  ... and ${agents.agents.length - 5} more`);
    }
  } else {
    warn("Agents not available — gateway must be running for agent access");
    log("  Agents are registered when the API server starts.");
  }

  // Step 4: IDE detection + install
  log("", "");
  log("Step 4 — IDE integration", "💻");
  const ides = detectIDEs();
  if (ides.length > 0) {
    ides.forEach((ide) => success(`Detected: ${ide}`));
    const doInstall = await askYesNo("Install JEBAT context to detected IDEs?", true);
    if (doInstall) {
      await cmdInstallTargeted(ides);
    }
  } else {
    warn("No IDEs detected in home directory");
    log("  Checked: ~/.vscode, ~/.cursor, ~/.zed, ~/.trae");
    log("  You can still install to a project with: npx jebat-core install");
  }

  // Step 5: Skills
  log("", "");
  log("Step 5 — Skills", "🗡️");
  const skillsData = await fetchVpsSkills();
  if (skillsData.skills.length > 0) {
    success(`${skillsData.skills.length} skills available (${skillsData.source})`);
    skillsData.skills.slice(0, 8).forEach((s) => log(`  • ${s.name}${s.description ? ` — ${s.description.slice(0, 50)}` : ""}`));
    if (skillsData.skills.length > 8) log(`  ... and ${skillsData.skills.length - 8} more`);
  } else {
    warn("No skills found");
    log("  Push skills with: npx jebat-core skill-push");
  }

  // Summary
  divider("Setup Summary");
  log(`User: ${config.userName || "Not onboarded"}`, "👤");
  log(`Workspace: ${ws.found}/${ws.total} core files`, ws.found === ws.total ? "✅" : "⚠️");
  log(`Gateway: ${gwOk ? "online" : "offline"}`, gwOk ? "✅" : "⚠️");
  log(`Agents: ${agents && agents.total ? agents.total + " registered" : "unavailable"}`, agents && agents.total ? "✅" : "⚠️");
  log(`IDEs: ${ides.length > 0 ? ides.join(", ") : "none detected"}`, "💻");
  log(`Skills: ${skillsData.skills.length} available (${skillsData.source})`, "🗡️");
  log("");
  log("You're ready. Start chatting:", "⚔️");
  log("  npx jebat-core chat");
  log("");
}

// ─── Install ────────────────────────────────────────────────────────

async function cmdInstallTargeted(ideKeys) {
  const workspace = process.cwd();
  log("Installing JEBAT context...", "⚔️");

  const contextFile = path.join(__dirname, "..", "adapters", "jebat", "JEBAT-CONTEXT.md");
  let context = "";
  if (fs.existsSync(contextFile)) {
    context = fs.readFileSync(contextFile, "utf8");
  } else {
    context = buildDefaultContext();
  }

  let installed = 0;
  for (const ide of ideKeys) {
    const file = IDE_TARGETS[ide];
    if (!file) continue;
    const target = path.join(workspace, file);
    const dir = path.dirname(target);
    if (!fs.existsSync(dir)) {
      try { fs.mkdirSync(dir, { recursive: true }); }
      catch { warn(`${ide}: Cannot create ${dir}`); continue; }
    }
    fs.writeFileSync(target, context);
    success(`${ide}: ${file}`);
    installed++;
  }
  log("");
  success(`Installed to ${installed} IDE(s). Restart your IDE to activate.`);
}

function cmdInstall(targetDir) {
  const workspace = targetDir || process.cwd();
  divider("⚔️  JEBAT Install");

  const contextFile = path.join(__dirname, "..", "adapters", "jebat", "JEBAT-CONTEXT.md");
  let context = "";
  if (fs.existsSync(contextFile)) {
    context = fs.readFileSync(contextFile, "utf8");
  } else {
    context = buildDefaultContext();
  }

  let installed = 0;
  for (const [ide, file] of Object.entries(IDE_TARGETS)) {
    const target = path.join(workspace, file);
    const dir = path.dirname(target);
    if (!fs.existsSync(dir)) {
      try { fs.mkdirSync(dir, { recursive: true }); }
      catch { warn(`${ide}: Cannot create ${dir}`); continue; }
    }
    fs.writeFileSync(target, context);
    success(`${ide}: ${file}`);
    installed++;
  }

  log("");
  success(`Installed JEBAT context to ${installed} IDE(s). Restart your IDE to activate.`);
  log("");
  log("Next: npx jebat-core status  —  check system health");
}

function buildDefaultContext() {
  const config = loadConfig();
  const name = config.userName || "User";
  const role = config.userRole || "developer";
  const useCase = config.useCase || "general";
  const style = config.responseStyle || "direct — short answers, no filler";

  return `# JEBAT Context — ${new Date().toISOString()}

JEBAT is the primary AI operator for this workspace.
Named after Hang Jebat — loyal, sharp, decisive.

## User
- Name: ${name}
- Role: ${role}
- Use case: ${useCase}
- Style: ${style}

## Core Rules
- Direct answers, no filler
- Search memory before claiming ignorance
- Backup config before editing
- Confirm before SSH or external actions

## Skills
Panglima, Hikmat, Tukang, Hulubalang, Pawang, Syahbandar, and 20+ more specialists.

## Gateway
Jebat Gateway on port 18789 — multi-provider LLM routing.
`;
}

// ─── Doctor ─────────────────────────────────────────────────────────

async function cmdDoctor() {
  divider("🩺  JEBAT Doctor");

  // Config
  const config = loadConfig();
  log("Configuration:");
  if (config.onboardedAt) {
    success(`User: ${config.userName || "User"} (${config.userRole || "unknown"})`);
    success(`Use case: ${config.useCase || "general"}`);
    success(`Onboarded: ${new Date(config.onboardedAt).toLocaleDateString()}`);
  } else {
    warn("Not onboarded — run: npx jebat-core onboard");
  }
  log("");

  // Workspace
  log("Workspace:");
  const ws = checkWorkspace();
  log(`  Core files: ${ws.found}/${ws.total}`, ws.found === ws.total ? "✅" : "⚠️");
  if (ws.missing.length) ws.missing.forEach((f) => log(`    Missing: ${f}`));
  log("");

  // Gateway
  log("Gateway:");
  const gwUrl = config.gatewayUrl || GATEWAY_URL;
  const gwOk = await checkGateway(gwUrl);
  log(`  ${gwUrl}`, gwOk ? "✅" : "⚠️");
  log("");

  // Agents
  log("Agents:");
  const agents = await checkAgents();
  if (agents && agents.total > 0) {
    success(`${agents.total} agents registered`);
    if (agents.stats) {
      if (agents.stats.providers) {
        log(`  Providers: ${Object.entries(agents.stats.providers).map(([k, v]) => `${k}(${v})`).join(", ")}`);
      }
      if (agents.stats.roles) {
        log(`  Roles: ${Object.entries(agents.stats.roles).map(([k, v]) => `${k}(${v})`).join(", ")}`);
      }
    }
  } else {
    warn("Agents unavailable (gateway offline)");
  }
  log("");

  // Skills
  log("Skills:");
  const skillsData = await fetchVpsSkills();
  if (skillsData.skills.length > 0) {
    success(`${skillsData.skills.length} skills (${skillsData.source})`);
  } else {
    warn("No skills found");
  }
  log("");

  // JEBAT home
  log("JEBAT home:");
  if (!fs.existsSync(JEBAT_HOME)) {
    fs.mkdirSync(JEBAT_HOME, { recursive: true });
    success(`Created: ${JEBAT_HOME}`);
  } else {
    success(`${JEBAT_HOME}`);
  }
  log("");

  const healthy = ws.found === ws.total && gwOk;
  log(healthy ? "JEBAT is healthy." : "Some issues found — review warnings.", healthy ? "✅" : "⚠️");
  log("");
}

// ─── Status ─────────────────────────────────────────────────────────

async function cmdStatus() {
  divider("📡  JEBAT System Status");

  // Gateway
  const gwUrl = (loadConfig()).gatewayUrl || GATEWAY_URL;
  const gwOk = await checkGateway(gwUrl);
  log(`Gateway (${gwUrl})`, gwOk ? "✅ Online" : "❌ Offline");

  // Agents
  const agents = await checkAgents();
  if (agents && agents.total > 0) {
    log(`Agents: ${agents.total} registered`, "✅");
  } else {
    log("Agents: unavailable", "⚠️");
  }

  // VPS
  try {
    const res = await httpGet("https://jebat.online/api/v1/health", 5000);
    log("VPS (jebat.online)", res.status === 200 ? "✅ Healthy" : `⚠️ HTTP ${res.status}`);
  } catch {
    log("VPS (jebat.online)", "⚠️ Unreachable");
  }

  // WebUI
  try {
    const res = await httpGet("https://jebat.online/webui/", 5000);
    log("WebUI (/webui/)", res.status === 200 ? "✅ Healthy" : `⚠️ HTTP ${res.status}`);
  } catch {
    log("WebUI (/webui/)", "⚠️ Unreachable");
  }

  const pkg = require("../package.json");
  log(`CLI: jebat-core v${pkg.version}`, "✅");
  log("");
}

// ─── Chat (gateway proxy) ───────────────────────────────────────────

async function cmdChat() {
  const config = loadConfig();
  const gwUrl = config.gatewayUrl || GATEWAY_URL;

  divider("💬  JEBAT Chat");

  // Check gateway
  const gwOk = await checkGateway(gwUrl);
  if (!gwOk) {
    warn(`Gateway offline at ${gwUrl}`);
    log("");
    log("Start the gateway:");
    log("  cd apps/api && uvicorn services.api.jebat_api:app --port 18789");
    log("");

    // Offer offline chat mode
    const doOffline = await askYesNo("Continue in offline mode (no AI responses)?", false);
    if (!doOffline) {
      process.exit(0);
    }
  }

  const userName = config.userName || "User";
  log(`Hello, ${userName}. Type your message (or 'quit' to exit).`, "⚔️");
  log("");

  // Interactive REPL
  while (true) {
    const iface = rl();
    const msg = await new Promise((resolve) => {
      iface.question("> ", (answer) => { iface.close(); resolve(answer); });
    });

    if (!msg || msg.trim().toLowerCase() === "quit" || msg.trim().toLowerCase() === "exit") {
      log("Goodbye.", "⚔️");
      break;
    }

    if (!gwOk) {
      warn("Gateway offline — cannot send message");
      continue;
    }

    try {
      const res = await httpPostJson(`${gwUrl}/api/v1/chat/completions`, {
        model: "jebat-pro",
        messages: [{ role: "user", content: msg.trim() }],
      }, 60000);

      if (res.status === 200 && res.body.choices && res.body.choices[0]) {
        log("");
        log(res.body.choices[0].message.content);
        log("");
      } else {
        warn(`Gateway returned ${res.status}`);
        if (typeof res.body === "string") warn(res.body.slice(0, 200));
      }
    } catch (e) {
      warn(`Request failed: ${e.message}`);
    }
  }
}

// ─── Agents list ────────────────────────────────────────────────────

async function cmdAgents() {
  divider("🤖  JEBAT Agents");

  const agents = await checkAgents();
  if (!agents || !agents.total) {
    warn("No agents available — gateway must be running");
    log("");
    log("Start the API server:");
    log("  cd apps/api && uvicorn services.api.jebat_api:app --port 18789");
    log("");
    return;
  }

  success(`${agents.total} agents registered`);
  if (agents.stats) {
    log("");
    if (agents.stats.providers) {
      log("Providers:", "📊");
      Object.entries(agents.stats.providers).forEach(([k, v]) => log(`  ${k}: ${v}`));
    }
    if (agents.stats.roles) {
      log("Roles:", "📊");
      Object.entries(agents.stats.roles).forEach(([k, v]) => log(`  ${k}: ${v}`));
    }
  }

  if (agents.agents && agents.agents.length) {
    log("");
    log("Registered Agents:", "📋");
    for (const a of agents.agents) {
      log(`  • ${a.agent_name} (${a.agent_id})`);
      log(`    Role: ${a.agent_role} | Provider: ${a.provider} | Model: ${a.model}`);
      log(`    Capabilities: ${a.capabilities.join(", ")}`);
      log(`    Status: ${a.status}`);
      log("");
    }
  }
}

// ─── Skills ─────────────────────────────────────────────────────────

function cmdSkillList() {
  const skillsDirs = [
    path.join(process.cwd(), "skills"),
    path.join(process.cwd(), "packages", "skills", "skills"),
    path.join(JEBAT_HOME, "bundle", "skills"),
    VPS_SKILLS_CACHE,
  ];
  let skillsDir = null;
  for (const dir of skillsDirs) {
    if (fs.existsSync(dir)) { skillsDir = dir; break; }
  }
  if (!skillsDir) {
    error("No skills directory found. Run: npx jebat-core skill-sync");
  }

  divider("🗡️  Installed Skills");

  const categories = {
    "Core": ["panglima", "memory-core", "jebat-agent", "agent-dispatch"],
    "Development": ["fullstack", "web-developer", "app-development", "database", "ui-ux", "qa-validation"],
    "Security": ["security-pentest", "jebat-cybersecurity", "jebat-hardening", "jebat-pentesting"],
    "Growth": ["seo", "marketing", "copywriting", "brand-strategy", "content-creation"],
    "Product": ["product-strategy", "senibina-antara-muka", "design-system", "penyebar-reka-bentuk"],
    "Operations": ["automation", "customer-success", "proposal-writing", "sales-enablement"],
    "Research": ["research-docs", "jebat-researcher", "jebat-analyst"],
    "Memory": ["jebat-memory-skill", "jebat-consolidation-skill"],
    "Orchestration": ["jebat-agent-orchestrator"],
  };

  const installed = fs.readdirSync(skillsDir);
  for (const [cat, catSkills] of Object.entries(categories)) {
    log(`${cat}:`, "📂");
    catSkills.forEach((skill) => {
      const found = installed.some((f) => f.toLowerCase().includes(skill.toLowerCase()));
      log(`  ${found ? "✅" : "❌"} ${skill}`);
    });
    log("");
  }
}

// ─── Token ──────────────────────────────────────────────────────────

function cmdTokenAnalyze(text) {
  const chars = text.length;
  const tokens = Math.ceil(chars / 4);
  divider("🔢  Token Analysis");
  log(`Characters: ${chars.toLocaleString()}`);
  log(`Estimated tokens: ~${tokens.toLocaleString()}`);
  log(`Model context usage:`);
  log(`  GPT-4o: ~${(tokens * 1.1).toFixed(0)} tokens (with overhead)`);
  log(`  Claude: ~${(tokens * 1.05).toFixed(0)} tokens (with overhead)`);
  log("");
}

// ─── Help ───────────────────────────────────────────────────────────

function cmdHelp() {
  console.log(`
⚔️  JEBAT CLI — jebat-core
The LLM Ecosystem That Remembers Everything

Usage:
  npx jebat-core <command>

Setup & Onboarding:
  setup            Full onboarding + integration setup
  onboard          User onboarding wizard
  install [dir]    Install JEBAT context to IDEs
  detect           Detect installed IDEs

Operations:
  chat             AI assistant chat (REPL mode)
  status           Gateway + VPS + agents status
  doctor           Full health check
  agents           List registered agents
  memory           Memory operations (stats, search)

Skills:
  skill-list       List installed skills
  skill-search     Search skills catalog
  skill-sync       Sync skills from VPS
  skill-push       Push skills to VPS

Utilities:
  prompt           Print universal prompt
  token-analyze    Count/analyze tokens
  token-compress   Compress context
  design-system    Browse design systems
  icon-search      Search tech icons
  deploy           VPS deployment helper
  help             Show this help

Examples:
  npx jebat-core setup        # First time — full onboarding
  npx jebat-core onboard      # User profile setup
  npx jebat-core install      # IDE context files
  npx jebat-core chat         # Interactive chat
  npx jebat-core status       # System health
  npx jebat-core doctor       # Detailed diagnostics
  npx jebat-core agents       # See registered agents
  npx jebat-core skill-sync   # Fetch skills from VPS
  npx jebat-core skill-push   # Push skills to VPS
`);
}

// ─── Router ─────────────────────────────────────────────────────────

// ── Agent definitions ──
const AGENTS = [
  { id: "auto",          name: "Auto (Panglima orchestrates)",  role: "orchestrator" },
  { id: "panglima",      name: "Panglima (orchestration)",      role: "orchestration" },
  { id: "tukang",        name: "Tukang (development)",          role: "development" },
  { id: "hulubalang",    name: "Hulubalang (security)",         role: "security" },
  { id: "pawang",        name: "Pawang (research)",             role: "research" },
  { id: "syahbandar",    name: "Syahbandar (operations)",       role: "operations" },
  { id: "bendahara",     name: "Bendahara (database)",          role: "database" },
  { id: "hikmat",        name: "Hikmat (memory)",               role: "memory" },
  { id: "penganalisis",  name: "Penganalisis (analytics)",      role: "analytics" },
  { id: "penyemak",      name: "Penyemak (QA)",                 role: "qa" },
];

function saveAgentPreference(agentId) {
  const config = loadConfig();
  config.selectedAgent = agentId;
  saveConfig(config);
}

/**
 * Single readline interface for load prompt + multi-select agent picker.
 * Returns { loadJebat, agentIds: string[], agents: Agent[] } or null if declined.
 *
 * Behaviour:
 *   - Type agent number(s) separated by space (e.g. "2 4 7")
 *   - 1 = Auto (Panglima orchestrates)
 *   - Press Enter with no input → default = Auto
 *   - If Auto + others chosen → Auto wins (orchestrator mode)
 */
function promptLoadAndAgent() {
  return new Promise((resolve) => {
    const iface = readline.createInterface({ input: process.stdin, output: process.stdout });
    const lines = [];

    iface.on("line", (raw) => {
      lines.push(raw);
      processLine();
    });

    let phase = "load";
    const config = loadConfig();
    // Resolve previous selection to first agent id for default highlighting
    const savedRaw = config.selectedAgent || "auto";
    const firstSaved = savedRaw.split(",")[0];
    const prevIdx = AGENTS.findIndex((a) => a.id === firstSaved);
    const defaultAgentIdx = prevIdx >= 0 ? prevIdx : 0;

    process.stdout.write("\n⚔️  Do you want to load JEBAT? [Y/n]: ");

    function processLine() {
      if (phase === "load") {
        const v = (lines[lines.length - 1] || "").trim().toLowerCase();
        const yes = v === "" || v === "y" || v === "yes";
        if (!yes) {
          iface.close();
          resolve(null);
          return;
        }
        phase = "agent";
        log("Select your agent(s) — space-separate for multi-select, Enter = Auto", "🤖");
        AGENTS.forEach((a, i) => {
          const marker = i === defaultAgentIdx ? " (default)" : "";
          const check = i === 0 ? "  ✦ " : "    ";
          log(`${check}${i + 1}. ${a.name}${marker}`);
        });
        log("");
        process.stdout.write("Choose [1-10, space-separate, Enter=Auto]: ");
      } else if (phase === "agent") {
        const answer = (lines[lines.length - 1] || "").trim();

        // No input → use previous selection (or default auto)
        if (!answer) {
          if (savedRaw === "auto") {
            const chosen = AGENTS[0];
            iface.close();
            config.selectedAgent = chosen.id;
            saveConfig(config);
            resolve({ loadJebat: true, agentIds: ["auto"], agents: [chosen] });
          } else {
            const ids = savedRaw.split(",");
            const chosen = ids.map((id) => AGENTS.find((a) => a.id === id)).filter(Boolean);
            if (chosen.length === 0) {
              const fallback = AGENTS[0];
              iface.close();
              config.selectedAgent = fallback.id;
              saveConfig(config);
              resolve({ loadJebat: true, agentIds: ["auto"], agents: [fallback] });
            } else {
              iface.close();
              resolve({ loadJebat: true, agentIds: ids, agents: chosen });
            }
          }
          return;
        }

        // Parse space-separated numbers
        const nums = answer.split(/\s+/).map((n) => parseInt(n, 10) - 1).filter((n) => n >= 0 && n < AGENTS.length);
        if (nums.length === 0) {
          // Invalid input → use previous or fallback to auto
          if (savedRaw === "auto") {
            const chosen = AGENTS[0];
            iface.close();
            config.selectedAgent = chosen.id;
            saveConfig(config);
            resolve({ loadJebat: true, agentIds: ["auto"], agents: [chosen] });
          } else {
            const ids = savedRaw.split(",");
            const chosen = ids.map((id) => AGENTS.find((a) => a.id === id)).filter(Boolean);
            iface.close();
            if (chosen.length === 0) {
              const fallback = AGENTS[0];
              config.selectedAgent = fallback.id;
              saveConfig(config);
              resolve({ loadJebat: true, agentIds: ["auto"], agents: [fallback] });
            } else {
              resolve({ loadJebat: true, agentIds: ids, agents: chosen });
            }
          }
          return;
        }

        const chosen = nums.map((i) => AGENTS[i]);

        // If "auto" (index 0) is among selections, it overrides — just use auto
        const hasAuto = chosen.some((a) => a.id === "auto");
        if (hasAuto) {
          config.selectedAgent = "auto";
          saveConfig(config);
          resolve({ loadJebat: true, agentIds: ["auto"], agents: [AGENTS[0]] });
        } else {
          config.selectedAgent = chosen.map((a) => a.id).join(",");
          saveConfig(config);
          resolve({ loadJebat: true, agentIds: chosen.map((a) => a.id), agents: chosen });
        }
        iface.close();
      }
    }
  });
}

(async () => {
  // ── JEBAT Load + Agent Selection (single readline interface) ──
  const skipLoadCmds = ["token-analyze", "help", "--help", "-h"];
  const [cmd, ...args] = process.argv.slice(2);

  if (!skipLoadCmds.includes(cmd)) {
    const result = await promptLoadAndAgent();
    if (!result) {
      log("JEBAT not loaded. Run npx jebat-core again to load it later.", "⚠️");
      process.exit(0);
    }
    const names = result.agents.map((a) => a.name).join(", ");
    log(`Agents: ${names}`, "✅");
    console.log("");
  }

  switch (cmd) {
    case "setup":
      await cmdSetup();
      break;
    case "onboard":
      await cmdOnboard();
      break;
    case "install":
      cmdInstall(args[0]);
      break;
    case "detect":
      const ides = detectIDEs();
      log(`Detected IDEs: ${ides.length > 0 ? ides.join(", ") : "none"}`, "💻");
      break;
    case "doctor":
      await cmdDoctor();
      break;
    case "status":
      await cmdStatus();
      break;
    case "prompt":
      const promptFile = path.join(__dirname, "..", "adapters", "jebat", "jebat-universal-prompt.md");
      if (fs.existsSync(promptFile)) {
        console.log(fs.readFileSync(promptFile, "utf8"));
      } else {
        log("Universal prompt file not found", "⚠️");
      }
      break;
    case "chat":
      await cmdChat();
      break;
    case "agents":
      await cmdAgents();
      break;
    case "skill-list":
      cmdSkillList();
      break;
    case "skill-sync":
      await cmdSkillSync();
      break;
    case "skill-push":
      await cmdSkillPush();
      break;
    case "token-analyze":
      if (process.stdin.isTTY) {
        log("Usage: echo 'text' | npx jebat-core token-analyze", "📖");
      } else {
        let data = "";
        process.stdin.on("data", (chunk) => (data += chunk));
        process.stdin.on("end", () => cmdTokenAnalyze(data));
      }
      break;
    case "memory":
      log("Memory operations — local file view", "🧠");
      const memDir = path.join(process.cwd(), "memory");
      if (fs.existsSync(memDir)) {
        fs.readdirSync(memDir).filter((f) => f.endsWith(".md")).forEach((f) => log(`  ${f}`));
      } else {
        log("  No local memory directory", "⚠️");
      }
      break;
    case "design-system":
    case "icon-search":
      log("Browse the skills.sh catalog at:", "🎨");
      log("  https://skills.sh/");
      break;
    case "deploy":
      divider("🚀  VPS Deployment");
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
})();
