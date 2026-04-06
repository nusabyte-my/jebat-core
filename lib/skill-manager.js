// JEBAT Skills Manager
// Handles skill installation, discovery, versioning, and lifecycle.
// Compatible with Anthropic SKILL.md format and skills.sh ecosystem.

import { readFile, writeFile, mkdir, readdir, stat, rm } from "node:fs/promises";
import { join, resolve, dirname } from "node:path";
import { cwd } from "node:process";
import { createHash } from "node:crypto";

// Skill registry — local + remote sources
const LOCAL_SKILLS_DIR = resolve(cwd(), "skills");
const PROJECT_SKILLS_DIR = resolve(cwd(), ".jebat", "skills");
const CONFIG_PATH = resolve(cwd(), "skills.json");
const LOCK_PATH = resolve(cwd(), "skills.lock");

// Remote skill registries
const REGISTRIES = {
  jebatcore: "https://github.com/nusabyte-my/jebat-core/skills",
  community: "https://github.com/anthropics/skills",
  vercel: "https://github.com/vercel-labs/skills",
};

// Default skill metadata
const DEFAULT_META = {
  author: "Unknown",
  version: "1.0.0",
  category: "general",
  tags: [],
  ide_support: ["vscode", "cursor", "zed", "claude"],
};

/**
 * Parse SKILL.md frontmatter and body.
 */
export function parseSkillMarkdown(content) {
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) {
    return null;
  }

  const frontmatter = frontmatterMatch[1];
  const body = content.slice(frontmatterMatch[0].length).trim();

  const meta = { ...DEFAULT_META };
  const lines = frontmatter.split("\n");
  let currentKey = null;
  let currentArray = null;

  for (const line of lines) {
    // Check for YAML list item
    const itemMatch = line.match(/^\s+-\s+(.*)/);
    if (itemMatch && currentKey) {
      if (!currentArray) currentArray = [];
      currentArray.push(itemMatch[1].trim().replace(/^['"]|['"]$/g, ""));
      meta[currentKey] = currentArray;
      continue;
    }

    // Check for key: value
    const colonIndex = line.indexOf(":");
    if (colonIndex === -1) continue;
    const key = line.slice(0, colonIndex).trim();
    let value = line.slice(colonIndex + 1).trim();

    // Check for bracket array
    if (value.startsWith("[")) {
      try {
        value = JSON.parse(value.replace(/'/g, '"'));
      } catch {
        value = value.replace(/[[\]]/g, "").split(",").map(s => s.trim().replace(/^['"]|['"]$/g, ""));
      }
    }

    // Empty value means start of YAML list
    if (value === "") {
      currentKey = key;
      currentArray = [];
      meta[key] = [];
      continue;
    }

    currentKey = key;
    currentArray = null;
    meta[key] = value;
  }

  return { meta, body };
}

/**
 * Generate SKILL.md content from metadata and body.
 */
export function generateSkillMarkdown(meta, body) {
  let frontmatter = "---\n";
  for (const [key, value] of Object.entries(meta)) {
    if (Array.isArray(value)) {
      frontmatter += `${key}: [${value.map(v => `"${v}"`).join(", ")}]\n`;
    } else {
      frontmatter += `${key}: ${value}\n`;
    }
  }
  frontmatter += "---\n\n";
  return frontmatter + body;
}

/**
 * Compute skill fingerprint for lock file.
 */
export function hashSkill(content) {
  return createHash("sha256").update(content).digest("hex").slice(0, 16);
}

/**
 * Discover all available skills in a directory.
 */
export async function discoverSkills(dir) {
  const skills = [];
  
  try {
    const entries = await readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      if (entry.name.startsWith("_")) continue; // Skip internal dirs
      
      if (entry.isDirectory()) {
        const skillPath = join(dir, entry.name, "SKILL.md");
        try {
          const content = await readFile(skillPath, "utf8");
          const parsed = parseSkillMarkdown(content);
          if (parsed) {
            skills.push({
              id: entry.name,
              path: skillPath,
              ...parsed,
              content,
              hash: hashSkill(content),
            });
          }
        } catch {
          // No SKILL.md in this directory, skip
        }
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return skills;
}

/**
 * Discover all skills across all known locations.
 */
export async function discoverAllSkills() {
  const locations = [
    { source: "local", dir: LOCAL_SKILLS_DIR },
    { source: "project", dir: PROJECT_SKILLS_DIR },
  ];
  
  const allSkills = [];
  for (const loc of locations) {
    const skills = await discoverSkills(loc.dir);
    allSkills.push(...skills.map(s => ({ ...s, source: loc.source })));
  }
  
  return allSkills;
}

/**
 * Search skills by query (name, description, tags, category).
 */
export async function searchSkills(query) {
  const skills = await discoverAllSkills();
  const q = query.toLowerCase();
  
  return skills.filter(skill => {
    const searchable = [
      skill.meta.name || "",
      skill.meta.description || "",
      skill.meta.category || "",
      ...(skill.meta.tags || []),
      skill.id,
    ].join(" ").toLowerCase();
    
    return searchable.includes(q);
  });
}

/**
 * Read skill configuration from skills.json.
 */
export async function readSkillConfig() {
  try {
    const content = await readFile(CONFIG_PATH, "utf8");
    return JSON.parse(content);
  } catch {
    return { skills: {}, registries: [] };
  }
}

/**
 * Write skill configuration to skills.json.
 */
export async function writeSkillConfig(config) {
  await writeFile(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n", "utf8");
}

/**
 * Read lock file.
 */
export async function readLockFile() {
  try {
    const content = await readFile(LOCK_PATH, "utf8");
    const skills = {};
    for (const line of content.split("\n")) {
      if (!line || line.startsWith("#")) continue;
      const [name, hash, source] = line.split("|").map(s => s.trim());
      if (name && hash) {
        skills[name] = { hash, source: source || "local" };
      }
    }
    return skills;
  } catch {
    return {};
  }
}

/**
 * Write lock file.
 */
export async function writeLockFile(skills) {
  let content = "# JEBAT Skills Lock\n";
  content += "# Format: skill-name | sha256 | source\n";
  content += "# Auto-generated. Do not edit manually.\n\n";
  
  for (const [name, info] of Object.entries(skills).sort()) {
    content += `${name} | ${info.hash} | ${info.source || "local"}\n`;
  }
  
  await writeFile(LOCK_PATH, content, "utf8");
}

/**
 * Install a skill from a local path or git URL.
 */
export async function installSkill(source, options = {}) {
  const { targetDir = PROJECT_SKILLS_DIR, name } = options;
  
  await mkdir(targetDir, { recursive: true });
  
  // Local path installation
  const sourcePath = resolve(source);
  const skillDir = join(targetDir, name || basename(sourcePath));
  
  try {
    // Check for SKILL.md
    const skillMdPath = join(sourcePath, "SKILL.md");
    const content = await readFile(skillMdPath, "utf8");
    const parsed = parseSkillMarkdown(content);
    
    if (!parsed) {
      throw new Error("Invalid SKILL.md format. Requires YAML frontmatter with name and description.");
    }
    
    const skillName = parsed.meta.name || name || basename(sourcePath);
    const destDir = join(targetDir, skillName);
    
    // Copy skill files
    await copyDir(sourcePath, destDir);
    
    // Update lock file
    const lock = await readLockFile();
    lock[skillName] = {
      hash: hashSkill(content),
      source: sourcePath,
      installedAt: new Date().toISOString(),
    };
    await writeLockFile(lock);
    
    return {
      name: skillName,
      path: destDir,
      meta: parsed.meta,
      installed: true,
    };
  } catch (error) {
    throw new Error(`Failed to install skill from ${source}: ${error.message}`);
  }
}

/**
 * Remove an installed skill.
 */
export async function removeSkill(name, targetDir = PROJECT_SKILLS_DIR) {
  const skillPath = join(targetDir, name);
  
  try {
    await stat(skillPath);
  } catch {
    throw new Error(`Skill "${name}" not found in ${targetDir}`);
  }
  
  await rm(skillPath, { recursive: true, force: true });
  
  // Update lock file
  const lock = await readLockFile();
  delete lock[name];
  await writeLockFile(lock);
  
  return { name, removed: true };
}

/**
 * Verify skill integrity against lock file.
 */
export async function verifySkill(name, targetDir = PROJECT_SKILLS_DIR) {
  const skillPath = join(targetDir, name, "SKILL.md");
  const lock = await readLockFile();
  
  try {
    const content = await readFile(skillPath, "utf8");
    const currentHash = hashSkill(content);
    const lockedHash = lock[name]?.hash;
    
    if (!lockedHash) {
      return { name, verified: false, reason: "not in lock file" };
    }
    
    if (currentHash !== lockedHash) {
      return { name, verified: false, reason: "hash mismatch", expected: lockedHash, actual: currentHash };
    }
    
    return { name, verified: true };
  } catch {
    return { name, verified: false, reason: "SKILL.md not found" };
  }
}

/**
 * Create a new skill from template.
 */
export async function createSkill(name, options = {}) {
  const { category = "general", dir = LOCAL_SKILLS_DIR } = options;
  const skillDir = join(dir, name);
  
  await mkdir(skillDir, { recursive: true });
  
  const meta = {
    name,
    description: options.description || `Skill for ${name} tasks.`,
    category,
    tags: options.tags || [name],
    ide_support: ["vscode", "cursor", "zed", "claude"],
    author: options.author || "JEBATCore / NusaByte",
    version: "1.0.0",
  };
  
  const body = `# ${name.charAt(0).toUpperCase() + name.slice(1)} Skill

## Instructions
[Add step-by-step instructions for this skill]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
`;
  
  const content = generateSkillMarkdown(meta, body);
  await writeFile(join(skillDir, "SKILL.md"), content, "utf8");
  
  return { name, path: skillDir, meta };
}

// Helper: copy directory recursively
async function copyDir(src, dest) {
  await mkdir(dest, { recursive: true });
  const entries = await readdir(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    
    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      const content = await readFile(srcPath);
      await writeFile(destPath, content);
    }
  }
}

// Helper: get basename from path
function basename(path) {
  return path.split(/[\\/]/).pop();
}

export {
  LOCAL_SKILLS_DIR,
  PROJECT_SKILLS_DIR,
  CONFIG_PATH,
  LOCK_PATH,
  REGISTRIES,
};
