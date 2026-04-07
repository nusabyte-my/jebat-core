import { mkdir, readFile, stat, readdir, writeFile } from "node:fs/promises";
import { join, resolve, relative, basename as pathBasename } from "node:path";
import { cwd } from "node:process";
import { DEFAULT_HOME, IDES, MODES, SCOPES } from "./constants.js";
import { detectIdes } from "./detect.js";
import { withPrompt, askText, chooseMany, chooseOne } from "./prompt.js";
import {
  ensureTarget,
  installHomeBundle,
  installMcpSnippet,
  installProjectContext,
  installWorkstationContext,
  readUniversalPrompt,
  workspaceRoot
} from "./install.js";
import {
  discoverAllSkills,
  searchSkills,
  parseSkillMarkdown,
  hashSkill,
  readSkillConfig,
  writeSkillConfig,
  readLockFile,
  writeLockFile,
  installSkill,
  removeSkill,
  verifySkill,
  createSkill,
  generateSkillMarkdown,
  LOCAL_SKILLS_DIR,
  PROJECT_SKILLS_DIR,
  CONFIG_PATH,
  LOCK_PATH,
} from "./skill-manager.js";
import { 
  countTokens, 
  estimateMessageTokens, 
  checkBudget, 
  getBudget,
  createBudgetTracker,
  MODEL_TOKEN_RATIOS,
  DEFAULT_BUDGETS
} from "./token-utils.js";
import { 
  compressContext, 
  compressSystemPrompt, 
  extractEssentialContext,
  COMPRESSION_LEVELS
} from "./context-compression.js";

/**
 * Strip common LLM output fluff to measure actual useful token count.
 */
function stripOutputFluff(text) {
  if (!text) return { text: "", originalLength: 0, cleanedLength: 0, fluffLinesRemoved: 0, originalTokens: 0, cleanedTokens: 0, savings: 0, reductionPercent: "0.0" };
  
  const fluffPatterns = [
    /^Sure!?\s*$/i,
    /^Certainly!?\s*$/i,
    /^Of course!?\s*$/i,
    /I[''](?:d| would) be happy to help/i,
    /I['']m happy to help/i,
    /^Happy to help/i,
    /Let me (?:help|assist|show|walk you through)/i,
    /I['']ll help you with that/i,
    /^Great question/i,
    /^Thanks for asking/i,
    /^Good point/i,
    /^Here['']s what/i,
    /^Here is what/i,
    /^Below is /i,
    /Based on the (?:context|information|code) (?:provided|given)/i,
    /From the (?:context|information|code) (?:provided|given)/i,
    /Now I['']ll (?:read|check|look at|analyze|review|create|build|update|install|deploy)/i,
    /I['']m going to (?:read|check|look at|analyze|review)/i,
    /I have (?:completed|finished|done|successfully)/i,
    /Let me know if you need anything else/i,
    /I hope this helps/i,
    /I hope this is helpful/i,
    /Please don['']t hesitate to/i,
    /Feel free to (?:ask|reach out|let me know)/i,
    /As an AI (?:language model|assistant)/i,
    /That['']s a (?:great|good|interesting) (?:question|point|idea)/i,
    /You['']re (?:right|correct)/i,
    /It['']s (?:important|worth noting|crucial) to (?:remember|note|understand)/i,
    /^Let me know if/i,
    /^Happy (?:to|coding|helping)/i,
    /Don['']t hesitate/i,
  ];
  
  const lines = text.split("\n");
  const cleaned = [];
  let fluffLinesRemoved = 0;
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    // Skip empty lines between content
    if (trimmed === "") {
      cleaned.push(line);
      continue;
    }
    
    let keep = true;
    for (const pattern of fluffPatterns) {
      if (pattern.test(trimmed)) {
        keep = false;
        fluffLinesRemoved++;
        break;
      }
    }
    
    if (keep) {
      cleaned.push(line);
    }
  }
  
  // Remove leading/trailing empty lines but preserve internal structure
  while (cleaned.length > 0 && cleaned[0].trim() === "") cleaned.shift();
  while (cleaned.length > 0 && cleaned[cleaned.length - 1].trim() === "") cleaned.pop();
  
  const result = cleaned.join("\n").replace(/\n{3,}/g, "\n\n").trim();
  
  return {
    text: result,
    originalLength: text.length,
    cleanedLength: result.length,
    fluffLinesRemoved,
    originalTokens: countTokens(text),
    cleanedTokens: countTokens(result),
    savings: countTokens(text) - countTokens(result),
    reductionPercent: ((countTokens(text) - countTokens(result)) / Math.max(countTokens(text), 1) * 100).toFixed(1)
  };
}

function printHeader() {
  console.log("\nJEBATCore CLI");
  console.log("Install JEBATCore as IDE context, local MCP, or both.\n");
}

function parseArgs(args) {
  const result = {
    command: args[0] || "install",
    ide: "",
    mode: "",
    scope: "",
    target: "",
    home: "",
    yes: false,
    dryRun: false,
    help: false,
    // Token command args
    text: "",
    file: "",
    model: "default",
    budget: "",
    level: "moderate",
    targetTokens: 0,
    output: "",
    // Design system args
    name: "",
    list: false,
    copy: false,
    // Icon search args
    query: "",
    listAll: false,
    // Skill manager args
    skillName: "",
    skillSource: "",
    skillDir: "",
    skillCategory: "",
    skillDescription: "",
    skillAuthor: "",
    skillTags: "",
    force: false
  };

  for (let index = 1; index < args.length; index += 1) {
    const token = args[index];
    const next = args[index + 1];
    if (token === "--ide") {
      result.ide = next || "";
      index += 1;
    } else if (token === "--mode") {
      result.mode = next || "";
      index += 1;
    } else if (token === "--scope") {
      result.scope = next || "";
      index += 1;
    } else if (token === "--target") {
      result.target = next || "";
      index += 1;
    } else if (token === "--home") {
      result.home = next || "";
      index += 1;
    } else if (token === "--yes") {
      result.yes = true;
    } else if (token === "--dry-run") {
      result.dryRun = true;
    } else if (token === "--help" || token === "-h") {
      result.help = true;
    } else if (token === "--text") {
      result.text = next || "";
      index += 1;
    } else if (token === "--file") {
      result.file = next || "";
      index += 1;
    } else if (token === "--model") {
      result.model = next || "default";
      index += 1;
    } else if (token === "--budget") {
      result.budget = next || "";
      index += 1;
    } else if (token === "--level") {
      result.level = next || "moderate";
      index += 1;
    } else if (token === "--target-tokens") {
      result.targetTokens = Number.parseInt(next || "0", 10);
      index += 1;
    } else if (token === "--output") {
      result.output = next || "";
      index += 1;
    } else if (token === "--name") {
      result.name = next || "";
      index += 1;
    } else if (token === "--list") {
      result.list = true;
    } else if (token === "--copy") {
      result.copy = true;
    } else if (token === "--query") {
      result.query = next || "";
      index += 1;
    } else if (token === "--list-all") {
      result.listAll = true;
    } else if (token === "--skill") {
      result.skillName = next || "";
      index += 1;
    } else if (token === "--source") {
      result.skillSource = next || "";
      index += 1;
    } else if (token === "--skill-dir") {
      result.skillDir = next || "";
      index += 1;
    } else if (token === "--category") {
      result.skillCategory = next || "";
      index += 1;
    } else if (token === "--description") {
      result.skillDescription = next || "";
      index += 1;
    } else if (token === "--author") {
      result.skillAuthor = next || "";
      index += 1;
    } else if (token === "--tags") {
      result.skillTags = next || "";
      index += 1;
    } else if (token === "--force") {
      result.force = true;
    }
  }

  return result;
}

function splitIdeArg(value) {
  return value ? value.split(",").map((item) => item.trim()).filter(Boolean) : [];
}

function suggestMode(selected) {
  if (selected.some((ide) => ["vscode", "cursor", "windsurf", "zed", "vscodium"].includes(ide))) {
    return "both";
  }
  return "extension";
}

function listKeys(collection) {
  return collection.map((item) => item.key);
}

function validateInstallConfig(config) {
  const validIdes = new Set(listKeys(IDES));
  const validModes = new Set(listKeys(MODES));
  const validScopes = new Set(listKeys(SCOPES));

  if (!config.selectedIdes.length) {
    throw new Error("No IDE selected. Use --ide or run interactively.");
  }
  for (const ide of config.selectedIdes) {
    if (!validIdes.has(ide)) {
      throw new Error(`Unsupported IDE: ${ide}`);
    }
  }
  if (!validModes.has(config.mode)) {
    throw new Error(`Unsupported mode: ${config.mode}`);
  }
  if (!validScopes.has(config.scope)) {
    throw new Error(`Unsupported scope: ${config.scope}`);
  }
  if (config.scope === "project" && !config.target) {
    throw new Error("Project scope requires --target.");
  }
}

function chooseDefaultIdes() {
  const detected = detectIdes().filter((ide) => ide.detected).map((ide) => ide.key);
  return detected.length ? detected : ["vscode"];
}

function defaultConfigFromFlags(parsed) {
  const selectedIdes = parsed.ide ? splitIdeArg(parsed.ide) : chooseDefaultIdes();
  const mode = parsed.mode || suggestMode(selectedIdes);
  const scope = parsed.scope || "workstation";
  const target = parsed.target || (scope === "project" ? cwd() : "");
  return { selectedIdes, mode, scope, target };
}

async function interactiveInstall(parsed) {
  const detected = detectIdes();
  const selectedIdes = await withPrompt((rl) => chooseMany(rl, "Choose IDE(s)", detected));
  const suggested = suggestMode(selectedIdes);
  const mode = await withPrompt((rl) =>
    chooseOne(
      rl,
      `Choose install mode (suggested: ${suggested})`,
      MODES,
      suggested
    )
  );
  const scope = await withPrompt((rl) => chooseOne(rl, "Choose install scope", SCOPES, "workstation"));
  let target = "";
  if (scope === "project") {
    target = await withPrompt((rl) => askText(rl, "Project target path", cwd()));
  }
  return { selectedIdes, mode, scope, target };
}

async function performInstall({ selectedIdes, mode, scope, target, home, dryRun }) {
  const homeDir = resolve(home || DEFAULT_HOME);
  if (!dryRun) {
    await mkdir(homeDir, { recursive: true });
  }
  const bundleInstall = await installHomeBundle(homeDir, { dryRun });
  const { bundleRoot, serverRoot } = bundleInstall;

  const results = [];
  for (const ide of selectedIdes) {
    if (mode === "extension" || mode === "both") {
      if (scope === "project") {
        const resolvedTarget = ensureTarget(target || cwd());
        const entry = await installProjectContext(ide, resolvedTarget, { dryRun });
        results.push({ ide, kind: "extension", ...entry });
      } else {
        const entry = await installWorkstationContext(ide, homeDir, { dryRun });
        results.push({ ide, kind: "extension", ...entry });
      }
    }
    if (mode === "mcp" || mode === "both") {
      const entry = await installMcpSnippet(ide, homeDir, bundleRoot, serverRoot, { dryRun });
      results.push({ ide, kind: "mcp", ...entry });
    }
  }

  return { homeDir, bundleRoot, serverRoot, dryRun, bundleInstall, results };
}

function printInstallResult(result) {
  const verb = result.dryRun ? "Planned" : "Installed";
  console.log(`\n${verb} JEBATCore bundle in ${result.homeDir}\n`);
  if (result.bundleInstall.installed.length) {
    console.log("bundle");
    for (const file of result.bundleInstall.installed) {
      console.log(`  - ${file}`);
    }
  }
  for (const item of result.results) {
    console.log(`${item.ide} (${item.kind})`);
    for (const file of item.installed) {
      console.log(`  - ${file}`);
    }
    if (item.backups.length) {
      console.log("  backups");
      for (const file of item.backups) {
        console.log(`  - ${file}`);
      }
    }
  }
  if (result.bundleInstall.backups.length) {
    console.log("bundle backups");
    for (const file of result.bundleInstall.backups) {
      console.log(`  - ${file}`);
    }
  }
  console.log("\nTop 10 IDE targets:");
  IDES.forEach((ide, index) => {
    console.log(`  ${index + 1}. ${ide.name}`);
  });
  console.log("\nSuggestion:");
  console.log("  - Use `both` for VS Code, Cursor, Windsurf, Zed, or VSCodium.");
  console.log("  - Use `extension` first for JetBrains, Neovim, Sublime, Trae, or Antigravity.");
  console.log("  - MCP snippets are generated conservatively for manual import into each IDE/client config.");
}

function printDetect() {
  const detected = detectIdes();
  printHeader();
  detected.forEach((ide, index) => {
    const state = ide.detected ? "detected" : "not detected";
    console.log(`${index + 1}. ${ide.name} - ${state}`);
  });
}

async function printPrompt() {
  const prompt = await readUniversalPrompt();
  console.log(prompt);
}

async function printDoctor() {
  const homeDir = resolve(DEFAULT_HOME);
  printHeader();
  console.log(`Workspace root: ${workspaceRoot()}`);
  console.log(`JEBATCore home: ${homeDir}`);
  console.log("Recommended validation:");
  console.log("  powershell -NoProfile -ExecutionPolicy Bypass -File .\\validate-workspace.ps1");
}

async function analyzeTokens(parsed) {
  let text = parsed.text;
  
  if (parsed.file) {
    try {
      const filePath = resolve(parsed.file);
      text = await readFile(filePath, "utf8");
    } catch (error) {
      console.error(`Error reading file: ${error.message}`);
      return;
    }
  }
  
  if (!text) {
    console.log("Usage: jebatcore token-analyze --text \"your text\" OR --file path/to/file.txt [--model claude]");
    return;
  }
  
  const model = parsed.model;
  const tokens = countTokens(text, model);
  const chars = text.length;
  const words = text.split(/\s+/).filter(Boolean).length;
  const lines = text.split("\n").length;
  
  console.log("\nToken Analysis");
  console.log("═".repeat(50));
  console.log(`Model: ${MODEL_TOKEN_RATIOS[model]?.name || model}`);
  console.log(`Tokens: ${tokens.toLocaleString()}`);
  console.log(`Characters: ${chars.toLocaleString()}`);
  console.log(`Words: ${words.toLocaleString()}`);
  console.log(`Lines: ${lines.toLocaleString()}`);
  console.log(`Chars per token: ${(chars / Math.max(tokens, 1)).toFixed(2)}`);
  console.log(`Words per token: ${(words / Math.max(tokens, 1)).toFixed(2)}`);
  
  // Show budget context
  console.log("\nBudget Context");
  console.log("─".repeat(50));
  for (const [operation, budget] of Object.entries(DEFAULT_BUDGETS)) {
    const inputUtil = (tokens / budget.input * 100).toFixed(1);
    const bar = "█".repeat(Math.min(Math.floor(inputUtil / 5), 20)) + "░".repeat(20 - Math.min(Math.floor(inputUtil / 5), 20));
    console.log(`${operation.padEnd(20)} ${inputUtil}% ${bar} ${tokens.toLocaleString()}/${budget.input.toLocaleString()}`);
  }
  console.log();
}

async function compressText(parsed) {
  let text = parsed.text;
  
  if (parsed.file) {
    try {
      const filePath = resolve(parsed.file);
      text = await readFile(filePath, "utf8");
    } catch (error) {
      console.error(`Error reading file: ${error.message}`);
      return;
    }
  }
  
  if (!text) {
    console.log("Usage: jebatcore token-compress --file path/to/file.txt [--level moderate] [--target-tokens 2000]");
    return;
  }
  
  const level = parsed.level;
  const targetTokens = parsed.targetTokens || null;
  const model = parsed.model;
  
  const result = compressContext(text, {
    level,
    targetTokens,
    model
  });
  
  console.log("\nCompression Result");
  console.log("═".repeat(50));
  console.log(`Level: ${level}`);
  console.log(`Original tokens: ${result.originalTokens.toLocaleString()}`);
  console.log(`Compressed tokens: ${result.compressedTokens.toLocaleString()}`);
  console.log(`Savings: ${result.savings.toLocaleString()} tokens (${(100 - parseFloat(result.compressionRatio)).toFixed(1)}% reduction)`);
  console.log(`Compression ratio: ${result.compressionRatio}`);
  
  if (parsed.output) {
    const outputPath = resolve(parsed.output);
    await require("node:fs/promises").writeFile(outputPath, result.text, "utf8");
    console.log(`\nOutput written to: ${outputPath}`);
  } else {
    console.log("\nCompressed Text");
    console.log("─".repeat(50));
    console.log(result.text);
  }
  console.log();
}

async function compressPrompt(parsed) {
  let text = parsed.text;
  
  if (parsed.file) {
    try {
      const filePath = resolve(parsed.file);
      text = await readFile(filePath, "utf8");
    } catch (error) {
      console.error(`Error reading file: ${error.message}`);
      return;
    }
  }
  
  if (!text) {
    console.log("Usage: jebatcore token-compress-prompt --file path/to/prompt.txt [--target-tokens 4000]");
    return;
  }
  
  const targetTokens = parsed.targetTokens || 4000;
  
  const result = compressSystemPrompt(text, targetTokens);
  
  console.log("\nSystem Prompt Compression");
  console.log("═".repeat(50));
  console.log(`Target tokens: ${targetTokens.toLocaleString()}`);
  console.log(`Original tokens: ${result.originalTokens.toLocaleString()}`);
  console.log(`Compressed tokens: ${result.compressedTokens.toLocaleString()}`);
  console.log(`Savings: ${result.savings.toLocaleString()} tokens (${(100 - parseFloat(result.compressionRatio)).toFixed(1)}% reduction)`);
  console.log(`Compression ratio: ${result.compressionRatio}`);
  
  if (parsed.output) {
    const outputPath = resolve(parsed.output);
    await require("node:fs/promises").writeFile(outputPath, result.text, "utf8");
    console.log(`\nOutput written to: ${outputPath}`);
  } else {
    console.log("\nCompressed Prompt");
    console.log("─".repeat(50));
    console.log(result.text);
  }
  console.log();
}

async function showBudgetInfo(parsed) {
  const budgetType = parsed.budget;
  
  if (budgetType) {
    const budget = DEFAULT_BUDGETS[budgetType];
    if (!budget) {
      console.log(`Unknown budget type: ${budgetType}`);
      console.log("\nAvailable budgets:");
      for (const key of Object.keys(DEFAULT_BUDGETS)) {
        console.log(`  ${key}`);
      }
      return;
    }
    
    console.log(`\nBudget: ${budgetType}`);
    console.log("═".repeat(50));
    console.log(`Input: ${budget.input.toLocaleString()} tokens`);
    console.log(`Output: ${budget.output.toLocaleString()} tokens`);
    console.log(`Total: ${(budget.input + budget.output).toLocaleString()} tokens`);
    
    // Show character equivalents for different models
    console.log("\nCharacter Equivalents");
    console.log("─".repeat(50));
    for (const [model, config] of Object.entries(MODEL_TOKEN_RATIOS)) {
      const inputChars = budget.input * config.charsPerToken;
      const outputChars = budget.output * config.charsPerToken;
      console.log(`${config.name.padEnd(12)} input: ~${inputChars.toLocaleString()} chars, output: ~${outputChars.toLocaleString()} chars`);
    }
    console.log();
  } else {
    console.log("\nDefault Token Budgets");
    console.log("═".repeat(50));
    console.log("Operation".padEnd(20) + "Input".padEnd(12) + "Output".padEnd(12) + "Total");
    console.log("─".repeat(50));
    for (const [key, budget] of Object.entries(DEFAULT_BUDGETS)) {
      const total = budget.input + budget.output;
      console.log(key.padEnd(20) + budget.input.toLocaleString().padEnd(12) + budget.output.toLocaleString().padEnd(12) + total.toLocaleString());
    }
    console.log("\nUsage: jebatcore token-budget --budget <operation>");
    console.log("Example: jebatcore token-budget --budget implementation");
    console.log();
  }
}

async function analyzeOutputFluff(parsed) {
  let text = parsed.text;
  
  if (parsed.file) {
    try {
      const filePath = resolve(parsed.file);
      text = await readFile(filePath, "utf8");
    } catch (error) {
      console.error(`Error reading file: ${error.message}`);
      return;
    }
  }
  
  if (!text) {
    console.log("Usage: jebatcore output-fluff --text \"LLM response\" OR --file response.txt");
    return;
  }
  
  const result = stripOutputFluff(text);
  
  console.log("\nOutput Fluff Analysis");
  console.log("═".repeat(50));
  console.log(`Original tokens: ${result.originalTokens.toLocaleString()}`);
  console.log(`Clean tokens: ${result.cleanedTokens.toLocaleString()}`);
  console.log(`Fluff tokens: ${result.savings.toLocaleString()} (${result.reductionPercent}% reduction)`);
  console.log(`Fluff lines removed: ${result.fluffLinesRemoved}`);
  
  if (parsed.output) {
    const outputPath = resolve(parsed.output);
    await require("node:fs/promises").writeFile(outputPath, result.text, "utf8");
    console.log(`\nCleaned output written to: ${outputPath}`);
  } else {
    console.log("\nCleaned Output");
    console.log("─".repeat(50));
    console.log(result.text);
  }
  console.log();
}

async function showDesignSystem(parsed) {
  const designSystemsDir = resolve(workspaceRoot(), "vault", "design-systems");
  
  if (parsed.list) {
    console.log("\nAvailable Design Systems");
    console.log("═".repeat(50));
    const entries = await readdir(designSystemsDir, { withFileTypes: true });
    for (const entry of entries.filter(e => e.isFile() && e.name.endsWith(".md"))) {
      const name = entry.name.replace(".md", "");
      const content = await readFile(join(designSystemsDir, entry.name), "utf8");
      const firstLine = content.split("\n")[0].replace("# Design System: ", "");
      console.log(`  ${name.padEnd(12)} ${firstLine}`);
    }
    console.log("\nUsage: jebatcore design-system --name <system>");
    console.log("Example: jebatcore design-system --name vercel");
    console.log();
    return;
  }
  
  if (parsed.name) {
    const filePath = join(designSystemsDir, `${parsed.name}.md`);
    try {
      const content = await readFile(filePath, "utf8");
      console.log(`\nDesign System: ${parsed.name.toUpperCase()}`);
      console.log("═".repeat(50));
      console.log(content);
      console.log();
    } catch {
      console.log(`Design system "${parsed.name}" not found.`);
      console.log("Available: vercel, cursor, supabase");
      console.log("Use --list to see all available systems.");
    }
    return;
  }
  
  // Default: show summary
  console.log("\nDesign Systems Library");
  console.log("═".repeat(50));
  console.log("Design systems from awesome-design-md collection.");
  console.log("Drop a DESIGN.md into your project root for AI agents.");
  console.log("\nLocal systems:");
  const entries = await readdir(designSystemsDir, { withFileTypes: true });
  for (const entry of entries.filter(e => e.isFile() && e.name.endsWith(".md"))) {
    console.log(`  • ${entry.name.replace(".md", "")}`);
  }
  console.log("\nUsage: jebatcore design-system --list");
  console.log("       jebatcore design-system --name vercel");
  console.log();
}

async function searchIcons(parsed) {
  const iconCatalog = resolve(workspaceRoot(), "vault", "references", "developer-icons.md");
  
  try {
    const content = await readFile(iconCatalog, "utf8");
    
    if (parsed.listAll) {
      console.log("\nDeveloper Icons Catalog");
      console.log("═".repeat(50));
      console.log("Source: https://github.com/xandemon/developer-icons");
      console.log("100+ tech logos for UI/UX output enhancement\n");
      
      // Extract all icon names from the markdown tables
      const iconLines = content.split("\n").filter(line => line.includes("| `icon:") || line.match(/^\| [A-Z].*svg`/));
      const icons = [];
      for (const line of iconLines) {
        const match = line.match(/^\| (.+?) \|/);
        if (match) icons.push(match[1].trim());
      }
      
      // Group by category
      let currentCategory = "";
      const lines = content.split("\n");
      for (const line of lines) {
        if (line.startsWith("### ")) {
          currentCategory = line.replace("### ", "");
          console.log(`\n${currentCategory}`);
          console.log("─".repeat(30));
        } else if (line.match(/^\| icon:/) || (line.includes("|") && !line.includes("---") && !line.startsWith("| Icon"))) {
          const parts = line.split("|").filter(Boolean).map(s => s.trim());
          if (parts.length >= 2 && !parts[0].includes("Icon Name")) {
            console.log(`  ${parts[0]}`);
          }
        }
      }
      console.log();
      return;
    }
    
    if (parsed.query) {
      const query = parsed.query.toLowerCase();
      const matchingLines = content.split("\n").filter(line => line.toLowerCase().includes(query));
      
      console.log(`\nIcon Search: "${parsed.query}"`);
      console.log("═".repeat(50));
      
      let found = false;
      const lines = content.split("\n");
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].toLowerCase().includes(query) && lines[i].includes("|")) {
          const parts = lines[i].split("|").filter(Boolean).map(s => s.trim());
          if (parts.length >= 2 && !parts[0].includes("Icon Name")) {
            console.log(`  icon:${parts[0]}`);
            found = true;
          }
        }
      }
      
      if (!found) {
        console.log(`No icons matching "${parsed.query}"`);
        console.log("Use --list-all to see all available icons.");
      }
      console.log();
      return;
    }
    
    // Default: show search hint
    console.log("\nDeveloper Icons");
    console.log("═".repeat(50));
    console.log("100+ tech logos for UI/UX output enhancement");
    console.log("\nUsage: jebatcore icon-search --query <name>");
    console.log("       jebatcore icon-search --list-all");
    console.log("\nExamples:");
    console.log("  jebatcore icon-search --query react");
    console.log("  jebatcore icon-search --query node");
    console.log("  jebatcore icon-search --query database");
    console.log();
  } catch {
    console.log("Icon catalog not found.");
    console.log("Check: vault/references/developer-icons.md");
  }
}

// ═══════════════════════════════════════════════════
// Skill Manager CLI Commands
// ═══════════════════════════════════════════════════

async function listSkills(parsed) {
  const skills = await discoverAllSkills();
  const lock = await readLockFile();
  
  console.log("\nInstalled Skills");
  console.log("═".repeat(70));
  console.log("Skill".padEnd(22) + "Category".padEnd(16) + "Version".padEnd(10) + "Source".padEnd(10) + "Locked");
  console.log("─".repeat(70));
  
  for (const skill of skills.sort((a, b) => a.id.localeCompare(b.id))) {
    const locked = lock[skill.id] ? "✓" : "✗";
    console.log(
      skill.id.padEnd(22) +
      (skill.meta.category || "general").padEnd(16) +
      (skill.meta.version || "1.0.0").padEnd(10) +
      skill.source.padEnd(10) +
      locked
    );
  }
  
  console.log(`\nTotal: ${skills.length} skills`);
  console.log("Locked: " + Object.keys(lock).length + " | Unlocked: " + (skills.length - Object.keys(lock).length));
  console.log("\nUsage: jebatcore skill --skill <name>");
  console.log("       jebatcore skill-search --query <term>");
  console.log("       jebatcore skill-create --skill <name> --description \"...\"");
  console.log();
}

async function showSkill(parsed) {
  if (!parsed.skillName) {
    console.log("Usage: jebatcore skill --skill <name>");
    console.log("Use jebatcore skill-list to see available skills.");
    return;
  }
  
  const skills = await discoverAllSkills();
  const skill = skills.find(s => s.id === parsed.skillName);
  
  if (!skill) {
    console.log(`Skill "${parsed.skillName}" not found.`);
    console.log("Use jebatcore skill-list to see available skills.");
    return;
  }
  
  // Verify against lock
  const lock = await readLockFile();
  const verified = lock[skill.id]?.hash === skill.hash;
  
  console.log(`\nSkill: ${skill.id}`);
  console.log("═".repeat(50));
  console.log(`Description: ${skill.meta.description}`);
  console.log(`Category: ${skill.meta.category}`);
  console.log(`Version: ${skill.meta.version}`);
  console.log(`Author: ${skill.meta.author}`);
  console.log(`Tags: ${(skill.meta.tags || []).join(", ")}`);
  console.log(`IDE Support: ${(skill.meta.ide_support || []).join(", ")}`);
  console.log(`Source: ${skill.source}`);
  console.log(`Path: ${skill.path}`);
  console.log(`Integrity: ${verified ? "✓ Verified" : "✗ Modified"}`);
  console.log("\n" + "─".repeat(50));
  console.log(skill.body);
  console.log();
}

async function searchSkill(parsed) {
  if (!parsed.query && !parsed.skillCategory) {
    console.log("Usage: jebatcore skill-search --query <term>");
    console.log("       jebatcore skill-search --category <category>");
    return;
  }
  
  const query = parsed.query || parsed.skillCategory;
  const results = await searchSkills(query);
  
  console.log(`\nSkill Search: "${query}"`);
  console.log("═".repeat(70));
  
  if (results.length === 0) {
    console.log("No skills found.");
    console.log("Use jebatcore skill-create to author a new skill.");
    console.log();
    return;
  }
  
  console.log("Skill".padEnd(22) + "Category".padEnd(16) + "Description");
  console.log("─".repeat(70));
  
  for (const skill of results) {
    const desc = (skill.meta.description || "").slice(0, 40);
    console.log(
      skill.id.padEnd(22) +
      (skill.meta.category || "general").padEnd(16) +
      desc
    );
  }
  
  console.log(`\nFound: ${results.length} skill(s)`);
  console.log("Use jebatcore skill --skill <name> to view full content.");
  console.log();
}

async function createSkillCmd(parsed) {
  if (!parsed.skillName) {
    console.log("Usage: jebatcore skill-create --skill <name> --description \"...\"");
    console.log("Optional: --category, --author, --tags");
    return;
  }
  
  const result = await createSkill(parsed.skillName, {
    category: parsed.skillCategory || "general",
    description: parsed.skillDescription,
    author: parsed.skillAuthor || "JEBATCore / NusaByte",
    tags: parsed.skillTags ? parsed.skillTags.split(",").map(t => t.trim()) : [parsed.skillName],
  });
  
  console.log(`\nSkill Created: ${result.name}`);
  console.log("═".repeat(50));
  console.log(`Path: ${result.path}`);
  console.log(`Category: ${result.meta.category}`);
  console.log(`Description: ${result.meta.description}`);
  console.log("\nEdit SKILL.md to add instructions, examples, and guidelines.");
  console.log();
}

async function installSkillCmd(parsed) {
  if (!parsed.skillSource) {
    console.log("Usage: jebatcore skill-install --source <path-or-url> --skill <name>");
    console.log("Optional: --skill-dir <target-directory>");
    return;
  }
  
  try {
    const result = await installSkill(parsed.skillSource, {
      name: parsed.skillName,
      targetDir: parsed.skillDir ? resolve(parsed.skillDir) : PROJECT_SKILLS_DIR,
    });
    
    console.log(`\nSkill Installed: ${result.name}`);
    console.log("═".repeat(50));
    console.log(`Path: ${result.path}`);
    console.log(`Version: ${result.meta.version}`);
    console.log(`Description: ${result.meta.description}`);
    console.log("\nSkill hash recorded in skills.lock for integrity verification.");
    console.log();
  } catch (error) {
    console.error(`Install failed: ${error.message}`);
  }
}

async function removeSkillCmd(parsed) {
  if (!parsed.skillName) {
    console.log("Usage: jebatcore skill-remove --skill <name> [--force]");
    return;
  }
  
  if (!parsed.force) {
    console.log(`Remove skill "${parsed.skillName}"? Use --force to confirm.`);
    return;
  }
  
  try {
    const result = await removeSkill(parsed.skillName);
    console.log(`\nSkill Removed: ${result.name}`);
    console.log("Lock file updated.");
    console.log();
  } catch (error) {
    console.error(`Remove failed: ${error.message}`);
  }
}

async function verifySkills(parsed) {
  const skills = await discoverAllSkills();
  const lock = await readLockFile();
  
  console.log("\nSkill Integrity Verification");
  console.log("═".repeat(50));
  
  let verified = 0;
  let modified = 0;
  let untracked = 0;
  
  for (const skill of skills.sort((a, b) => a.id.localeCompare(b.id))) {
    // skill.path is full path to SKILL.md; extract the skills root dir
    const parts = skill.path.split(/[\\/]/);
    const skillsIdx = parts.findIndex(p => p === "skills");
    const rootDir = skillsIdx >= 0 ? parts.slice(0, skillsIdx + 1).join("/") : LOCAL_SKILLS_DIR;
    const result = await verifySkill(skill.id, resolve(rootDir));
    const icon = result.verified ? "✓" : "✗";
    const status = result.verified ? "OK" : (result.reason === "not in lock file" ? "untracked" : result.reason);
    
    console.log(`  ${icon} ${skill.id.padEnd(20)} ${status}`);
    
    if (result.verified) verified++;
    else if (result.reason === "not in lock file") untracked++;
    else modified++;
  }
  
  console.log(`\nSummary: ${verified} verified, ${modified} modified, ${untracked} untracked`);
  
  if (modified > 0) {
    console.log("\nTo update lock file with current hashes, run:");
    console.log("  jebatcore skill-lock-update");
  }
  console.log();
}

function printHelp() {
  printHeader();
  console.log("Commands:");
  console.log("  jebatcore install [--ide vscode,cursor] [--mode extension|mcp|both] [--scope workstation|project] [--target PATH] [--home PATH] [--yes] [--dry-run]");
  console.log("  jebatcore detect");
  console.log("  jebatcore prompt");
  console.log("  jebatcore doctor");
  console.log("  jebatcore token-analyze --text \"text\" OR --file path.txt [--model claude]");
  console.log("  jebatcore token-compress --file path.txt [--level moderate|aggressive|minimal] [--target-tokens 2000]");
  console.log("  jebatcore token-compress-prompt --file prompt.txt [--target-tokens 4000]");
  console.log("  jebatcore token-budget [--budget operation]");
  console.log("  jebatcore output-fluff --text \"LLM response\" OR --file response.txt");
  console.log("  jebatcore design-system [--name vercel|cursor|supabase] [--list] [--copy]");
  console.log("  jebatcore icon-search [--query react] [--list-all]");
  console.log("  jebatcore skill-list");
  console.log("  jebatcore skill --skill <name>");
  console.log("  jebatcore skill-search --query <term>");
  console.log("  jebatcore skill-create --skill <name> --description \"...\"");
  console.log("  jebatcore skill-install --source <path> --skill <name>");
  console.log("  jebatcore skill-remove --skill <name> --force");
  console.log("  jebatcore skill-verify");
  console.log("");
  console.log("Examples:");
  console.log("  npx jebatcore install");
  console.log("  npx jebatcore install --ide vscode,cursor --mode both --scope workstation --yes");
  console.log("  bunx jebatcore install --ide zed --mode mcp --scope project --target . --home ~/.jebatcore --dry-run");
  console.log("  npx jebatcore token-analyze --file AGENTS.md --model claude");
  console.log("  npx jebatcore token-compress --file system-prompt.txt --level aggressive --target-tokens 3000");
  console.log("  npx jebatcore token-budget --budget implementation");
  console.log("  npx jebatcore output-fluff --file llm-response.txt");
  console.log("  npx jebatcore design-system --list");
  console.log("  npx jebatcore design-system --name vercel");
  console.log("  npx jebatcore icon-search --query react");
  console.log("  npx jebatcore skill-list");
  console.log("  npx jebatcore skill --skill panglima");
  console.log("  npx jebatcore skill-search --query react");
  console.log("  npx jebatcore skill-create --skill my-api --description \"REST API patterns\"");
  console.log("  npx jebatcore skill-verify");
}

export async function runCli(args) {
  const parsed = parseArgs(args);

  if (parsed.help || parsed.command === "help") {
    printHelp();
    return;
  }

  if (parsed.command === "detect") {
    printDetect();
    return;
  }

  if (parsed.command === "prompt") {
    await printPrompt();
    return;
  }

  if (parsed.command === "doctor") {
    await printDoctor();
    return;
  }

  // Token optimization commands
  if (parsed.command === "token-analyze") {
    await analyzeTokens(parsed);
    return;
  }

  if (parsed.command === "token-compress") {
    await compressText(parsed);
    return;
  }

  if (parsed.command === "token-compress-prompt") {
    await compressPrompt(parsed);
    return;
  }

  if (parsed.command === "token-budget") {
    await showBudgetInfo(parsed);
    return;
  }

  if (parsed.command === "output-fluff") {
    await analyzeOutputFluff(parsed);
    return;
  }

  // Design system commands
  if (parsed.command === "design-system") {
    await showDesignSystem(parsed);
    return;
  }

  if (parsed.command === "icon-search") {
    await searchIcons(parsed);
    return;
  }

  // Skill manager commands
  if (parsed.command === "skill-list") {
    await listSkills(parsed);
    return;
  }

  if (parsed.command === "skill") {
    await showSkill(parsed);
    return;
  }

  if (parsed.command === "skill-search") {
    await searchSkill(parsed);
    return;
  }

  if (parsed.command === "skill-create") {
    await createSkillCmd(parsed);
    return;
  }

  if (parsed.command === "skill-install") {
    await installSkillCmd(parsed);
    return;
  }

  if (parsed.command === "skill-remove") {
    await removeSkillCmd(parsed);
    return;
  }

  if (parsed.command === "skill-verify") {
    await verifySkills(parsed);
    return;
  }

  printHeader();
  let installConfig;
  if (parsed.yes) {
    installConfig = defaultConfigFromFlags(parsed);
  } else if (!parsed.ide || !parsed.mode || !parsed.scope) {
    installConfig = await interactiveInstall(parsed);
  } else {
    installConfig = defaultConfigFromFlags(parsed);
  }
  validateInstallConfig(installConfig);
  const result = await performInstall({ ...installConfig, home: parsed.home, dryRun: parsed.dryRun });
  printInstallResult(result);
}
