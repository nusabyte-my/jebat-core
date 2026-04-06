import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { BUNDLE_DIRS, BUNDLE_FILES, PROJECT_MAPPINGS } from "./constants.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function src(pathValue) {
  return join(ROOT, pathValue);
}

async function ensureDir(pathValue) {
  await mkdir(pathValue, { recursive: true });
}

function timestampToken() {
  return new Date().toISOString().replaceAll(":", "-");
}

async function backupPath(targetPath, options) {
  if (!existsSync(targetPath)) {
    return null;
  }
  const backupPathValue = `${targetPath}.bak-${timestampToken()}`;
  if (!options.dryRun) {
    await cp(targetPath, backupPathValue, { recursive: true, force: true });
  }
  options.backups.push(backupPathValue);
  return backupPathValue;
}

async function copyPath(fromRelative, toAbsolute, options) {
  await ensureDir(dirname(toAbsolute));
  await backupPath(toAbsolute, options);
  if (!options.dryRun) {
    await cp(src(fromRelative), toAbsolute, { recursive: true, force: true });
  }
  options.installed.push(toAbsolute);
}

async function writeText(pathValue, content, options) {
  await ensureDir(dirname(pathValue));
  await backupPath(pathValue, options);
  if (!options.dryRun) {
    await writeFile(pathValue, content, "utf8");
  }
  options.installed.push(pathValue);
}

function createOptions(options = {}) {
  return {
    dryRun: Boolean(options.dryRun),
    installed: [],
    backups: []
  };
}

export async function installHomeBundle(homeDir, options = {}) {
  const state = createOptions(options);
  const bundleRoot = join(homeDir, "bundle");
  const serverRoot = join(homeDir, "server");
  if (!state.dryRun) {
    await ensureDir(bundleRoot);
    await ensureDir(serverRoot);
  }

  for (const dir of BUNDLE_DIRS) {
    await copyPath(dir, join(bundleRoot, dir), state);
  }

  for (const file of BUNDLE_FILES) {
    await copyPath(file, join(bundleRoot, file), state);
  }

  await copyPath("lib/mcp-server.js", join(serverRoot, "mcp-server.js"), state);
  return { bundleRoot, serverRoot, installed: state.installed, backups: state.backups };
}

export async function installProjectContext(ideKey, targetDir, options = {}) {
  const state = createOptions(options);
  const mappings = PROJECT_MAPPINGS[ideKey] || [];
  for (const mapping of mappings) {
    const destination = join(targetDir, mapping.dest);
    await copyPath(mapping.src, destination, state);
  }
  return { installed: state.installed, backups: state.backups };
}

export async function installWorkstationContext(ideKey, homeDir, options = {}) {
  const state = createOptions(options);
  const snippetRoot = join(homeDir, "ide-snippets", ideKey, "extension");
  const mappings = PROJECT_MAPPINGS[ideKey] || [];
  for (const mapping of mappings) {
    const destination = join(snippetRoot, mapping.dest.replaceAll("/", "_"));
    await copyPath(mapping.src, destination, state);
  }
  const note = join(snippetRoot, "README.txt");
  await writeText(
    note,
    [
      `JEBATCore extension/context files for ${ideKey}.`,
      "These files were generated for workstation install.",
      "Copy or adapt them into your preferred global or project configuration flow."
    ].join("\n"),
    state
  );
  return { installed: state.installed, backups: state.backups };
}

export async function installMcpSnippet(ideKey, homeDir, bundleRoot, serverRoot, options = {}) {
  const state = createOptions(options);
  const snippetRoot = join(homeDir, "ide-snippets", ideKey, "mcp");
  const configPath = join(snippetRoot, "mcp-config.json");
  const readmePath = join(snippetRoot, "README.txt");
  const snippet = {
    mcpServers: {
      jebatcore: {
        command: "node",
        args: [join(serverRoot, "mcp-server.js"), "--bundle", bundleRoot]
      }
    }
  };
  await writeText(configPath, `${JSON.stringify(snippet, null, 2)}\n`, state);
  await writeText(
    readmePath,
    [
      `JEBATCore MCP snippet for ${ideKey}.`,
      "Import or paste this into the IDE or client MCP configuration that supports stdio servers.",
      `Server command: node ${join(serverRoot, "mcp-server.js")} --bundle ${bundleRoot}`
    ].join("\n"),
    state
  );
  return { installed: state.installed, backups: state.backups };
}

export async function readUniversalPrompt() {
  return readFile(src("adapters/jebat-universal-prompt.md"), "utf8");
}

export function workspaceRoot() {
  return ROOT;
}

export function ensureTarget(targetPath) {
  const resolved = resolve(targetPath);
  if (!existsSync(resolved)) {
    throw new Error(`Target path does not exist: ${resolved}`);
  }
  if (!statSync(resolved).isDirectory()) {
    throw new Error(`Target path is not a directory: ${resolved}`);
  }
  return resolved;
}
