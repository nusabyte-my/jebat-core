import { homedir } from "node:os";
import { join } from "node:path";

export const IDES = [
  { key: "vscode", name: "VS Code", recommendedMode: "both" },
  { key: "cursor", name: "Cursor", recommendedMode: "both" },
  { key: "windsurf", name: "Windsurf", recommendedMode: "both" },
  { key: "zed", name: "Zed", recommendedMode: "both" },
  { key: "jetbrains", name: "JetBrains IDEs", recommendedMode: "extension" },
  { key: "neovim", name: "Neovim", recommendedMode: "extension" },
  { key: "sublime", name: "Sublime Text", recommendedMode: "extension" },
  { key: "vscodium", name: "VSCodium", recommendedMode: "both" },
  { key: "trae", name: "Trae", recommendedMode: "extension" },
  { key: "antigravity", name: "Antigravity", recommendedMode: "extension" }
];

export const MODES = [
  { key: "extension", name: "Extension / Context Files" },
  { key: "mcp", name: "MCP Server" },
  { key: "both", name: "Both" }
];

export const SCOPES = [
  { key: "workstation", name: "Workstation (recommended)" },
  { key: "project", name: "Project" }
];

export const DEFAULT_HOME = process.env.JEBATCORE_HOME || join(homedir(), ".jebatcore");

export const BUNDLE_DIRS = [
  "vault",
  "skills"
];

export const BUNDLE_FILES = [
  "AGENTS.md",
  "IDENTITY.md",
  "MEMORY.md",
  "ORCHESTRA.md",
  "SOUL.md",
  "TOOLS.md",
  "USER.md",
  "adapters/jebat-universal-prompt.md",
  "adapters/generic/JEBAT.md"
];

export const PROJECT_MAPPINGS = {
  vscode: [{ src: "adapters/vscode/copilot-instructions.md", dest: ".github/copilot-instructions.md" }],
  cursor: [{ src: "adapters/cursor/.cursorrules", dest: ".cursorrules" }],
  windsurf: [{ src: "adapters/generic/JEBAT.md", dest: ".windsurf/jebat-context.md" }],
  zed: [{ src: "adapters/zed/system-prompt.md", dest: ".zed/jebat-system-prompt.md" }],
  jetbrains: [{ src: "adapters/generic/JEBAT.md", dest: ".idea/jebat-context.md" }],
  neovim: [{ src: "adapters/generic/JEBAT.md", dest: ".nvim/jebat-context.md" }],
  sublime: [{ src: "adapters/generic/JEBAT.md", dest: ".sublime/jebat-context.md" }],
  vscodium: [{ src: "adapters/vscode/copilot-instructions.md", dest: ".github/copilot-instructions.md" }],
  trae: [{ src: "adapters/generic/JEBAT.md", dest: ".trae/jebat-context.md" }],
  antigravity: [{ src: "adapters/generic/JEBAT.md", dest: ".antigravity/jebat-context.md" }]
};
