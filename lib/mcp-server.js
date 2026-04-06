#!/usr/bin/env node
import { readFile, readdir, stat } from "node:fs/promises";
import { join, normalize, resolve, relative } from "node:path";
import { argv, stdin, stdout } from "node:process";
import { countTokens, optimizeForTokenBudget } from "./token-utils.js";
import { compressContext, extractEssentialContext } from "./context-compression.js";

function getArg(flag) {
  const index = argv.indexOf(flag);
  return index >= 0 ? argv[index + 1] : "";
}

const bundleRoot = resolve(getArg("--bundle") || process.cwd());

// Token optimization cache
const responseCache = new Map();
const MAX_CACHE_SIZE = 50;

function safePath(relativePath) {
  const resolved = resolve(bundleRoot, relativePath);
  if (!resolved.startsWith(bundleRoot)) {
    throw new Error("Path escapes bundle root.");
  }
  return resolved;
}

// Token-efficient response helpers
async function readAssetTokenEfficient(relativePath, options = {}) {
  const { maxTokens = 4000, compression = "moderate" } = options;
  const cacheKey = `asset:${relativePath}:${maxTokens}:${compression}`;
  
  if (responseCache.has(cacheKey)) {
    return responseCache.get(cacheKey);
  }
  
  const fullPath = safePath(normalize(relativePath));
  let text = await readFile(fullPath, "utf8");
  
  // Apply compression
  const result = compressContext(text, {
    level: compression,
    targetTokens: maxTokens
  });
  
  const response = {
    text: result.text,
    tokens: result.compressedTokens,
    originalTokens: result.originalTokens,
    savings: result.savings,
    compressionRatio: result.compressionRatio
  };
  
  // Cache result
  if (responseCache.size >= MAX_CACHE_SIZE) {
    const firstKey = responseCache.keys().next().value;
    responseCache.delete(firstKey);
  }
  responseCache.set(cacheKey, response);
  
  return response;
}

async function listAssetsTokenEfficient(category, pattern = "", maxTokens = 2000) {
  const cacheKey = `assets:${category}:${pattern}:${maxTokens}`;
  
  if (responseCache.has(cacheKey)) {
    return responseCache.get(cacheKey);
  }
  
  const map = {
    playbook: "vault/playbooks",
    template: "vault/templates",
    checklist: "vault/checklists",
    example: "vault/examples",
    skill: "skills"
  };
  
  const folder = map[category];
  if (!folder) {
    throw new Error(`Unsupported category: ${category}`);
  }
  
  const dir = safePath(folder);
  const entries = await readdir(dir, { withFileTypes: true });
  const items = entries
    .filter((entry) => entry.isFile() || entry.isDirectory())
    .map((entry) => ({
      path: join(folder, entry.name).replaceAll("\\", "/"),
      type: entry.isFile() ? "file" : "dir"
    }))
    .filter((item) => !pattern || item.path.toLowerCase().includes(pattern.toLowerCase()));
  
  // Format as concise list
  const text = items.map(item => `${item.type === "dir" ? "📁" : "📄"} ${item.path}`).join("\n");
  const tokens = countTokens(text);
  
  // Truncate if over budget
  let optimized = text;
  if (tokens > maxTokens) {
    const result = optimizeForTokenBudget(text, maxTokens);
    optimized = result.text;
  }
  
  const response = {
    text: optimized,
    count: items.length,
    tokens: countTokens(optimized),
    truncated: optimized !== text
  };
  
  if (responseCache.size >= MAX_CACHE_SIZE) {
    const firstKey = responseCache.keys().next().value;
    responseCache.delete(firstKey);
  }
  responseCache.set(cacheKey, response);
  
  return response;
}

async function getOperatingSystemTokenEfficient(maxTokens = 6000) {
  const cacheKey = `operating_system:${maxTokens}`;
  
  if (responseCache.has(cacheKey)) {
    return responseCache.get(cacheKey);
  }
  
  const text = await readFile(safePath("vault/OPERATING-SYSTEM.md"), "utf8");
  
  // Extract essential structure
  const result = extractEssentialContext(text, {
    keepHeadings: true,
    keepCodeExamples: false,
    keepLists: true,
    maxTokens
  });
  
  const response = {
    text: result.text,
    tokens: result.tokens,
    originalTokens: result.originalTokens,
    savings: result.savings,
    compressionRatio: result.compressionRatio
  };
  
  if (responseCache.size >= MAX_CACHE_SIZE) {
    const firstKey = responseCache.keys().next().value;
    responseCache.delete(firstKey);
  }
  responseCache.set(cacheKey, response);
  
  return response;
}

/**
 * Strip common fluff patterns from LLM output to save output tokens.
 * Removes greetings, sign-offs, restatements, and sycophantic content.
 */
function stripOutputFluff(text) {
  if (!text) return text;
  
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
        break;
      }
    }
    
    if (keep) {
      cleaned.push(line);
    }
  }
  
  // Remove leading/trailing empty lines
  while (cleaned.length > 0 && cleaned[0].trim() === "") cleaned.shift();
  while (cleaned.length > 0 && cleaned[cleaned.length - 1].trim() === "") cleaned.pop();
  
  return cleaned.join("\n").replace(/\n{3,}/g, "\n\n").trim();
}

// Cache management tool
function clearCache() {
  const size = responseCache.size;
  responseCache.clear();
  return { cleared: size };
}

function getCacheStats() {
  return {
    size: responseCache.size,
    maxSize: MAX_CACHE_SIZE,
    utilization: (responseCache.size / MAX_CACHE_SIZE * 100).toFixed(1) + "%"
  };
}

async function listCategory(relativePath) {
  const dir = safePath(relativePath);
  const entries = await readdir(dir, { withFileTypes: true });
  return entries.filter((entry) => entry.isFile()).map((entry) => join(relativePath, entry.name).replaceAll("\\", "/"));
}

async function operatingSystemSummary() {
  return readFile(safePath("vault/OPERATING-SYSTEM.md"), "utf8");
}

async function readAsset(relativePath) {
  return readFile(safePath(normalize(relativePath)), "utf8");
}

async function findAssets(category, pattern = "") {
  const map = {
    playbook: "vault/playbooks",
    template: "vault/templates",
    checklist: "vault/checklists",
    example: "vault/examples",
    skill: "skills"
  };
  const folder = map[category];
  if (!folder) {
    throw new Error(`Unsupported category: ${category}`);
  }
  const dir = safePath(folder);
  const entries = await readdir(dir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() || entry.isDirectory())
    .map((entry) => join(folder, entry.name).replaceAll("\\", "/"))
    .filter((item) => !pattern || item.toLowerCase().includes(pattern.toLowerCase()));
}

const tools = [
  {
    name: "operating_system",
    description: "Read the top-level JEBAT operating-system index.",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "operating_system_efficient",
    description: "Read operating-system index with token optimization (returns token count and compression stats).",
    inputSchema: {
      type: "object",
      properties: {
        maxTokens: { type: "number", description: "Maximum tokens to return (default: 6000)" }
      }
    }
  },
  {
    name: "find_assets",
    description: "List playbooks, templates, checklists, examples, or skills by category.",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string" },
        pattern: { type: "string" }
      },
      required: ["category"]
    }
  },
  {
    name: "find_assets_efficient",
    description: "List assets with token optimization (returns concise list with token count).",
    inputSchema: {
      type: "object",
      properties: {
        category: { type: "string" },
        pattern: { type: "string" },
        maxTokens: { type: "number", description: "Maximum tokens for response (default: 2000)" }
      },
      required: ["category"]
    }
  },
  {
    name: "read_asset",
    description: "Read a specific asset relative to the installed JEBAT bundle.",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string" }
      },
      required: ["path"]
    }
  },
  {
    name: "read_asset_efficient",
    description: "Read asset with token optimization (applies compression to fit token budget).",
    inputSchema: {
      type: "object",
      properties: {
        path: { type: "string" },
        maxTokens: { type: "number", description: "Maximum tokens (default: 4000)" },
        compression: { type: "string", enum: ["minimal", "moderate", "aggressive"], description: "Compression level (default: moderate)" }
      },
      required: ["path"]
    }
  },
  {
    name: "token_stats",
    description: "Get token usage statistics for a text string.",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string" },
        model: { type: "string", description: "Model type for token estimation (default: default)" }
      },
      required: ["text"]
    }
  },
  {
    name: "cache_stats",
    description: "Get MCP server cache statistics (size, utilization).",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "cache_clear",
    description: "Clear MCP server response cache.",
    inputSchema: { type: "object", properties: {} }
  }
];

function writeMessage(message) {
  const json = JSON.stringify(message);
  stdout.write(`Content-Length: ${Buffer.byteLength(json, "utf8")}\r\n\r\n${json}`);
}

async function handleRequest(message) {
  const { id, method, params = {} } = message;

  if (method === "initialize") {
    writeMessage({
      jsonrpc: "2.0",
      id,
      result: {
        protocolVersion: "2024-11-05",
        capabilities: { tools: {} },
        serverInfo: { name: "jebatcore", version: "0.1.0" }
      }
    });
    return;
  }

  if (method === "tools/list") {
    writeMessage({ jsonrpc: "2.0", id, result: { tools } });
    return;
  }

  if (method === "tools/call") {
    try {
      let text = "";
      let metadata = null;
      
      if (params.name === "operating_system") {
        text = await operatingSystemSummary();
      } else if (params.name === "operating_system_efficient") {
        const maxTokens = params.arguments?.maxTokens || 6000;
        const result = await getOperatingSystemTokenEfficient(maxTokens);
        text = result.text;
        metadata = result;
      } else if (params.name === "find_assets") {
        const results = await findAssets(params.arguments?.category, params.arguments?.pattern || "");
        text = results.join("\n");
      } else if (params.name === "find_assets_efficient") {
        const maxTokens = params.arguments?.maxTokens || 2000;
        const result = await listAssetsTokenEfficient(
          params.arguments?.category,
          params.arguments?.pattern || "",
          maxTokens
        );
        text = result.text;
        metadata = { count: result.count, tokens: result.tokens, truncated: result.truncated };
      } else if (params.name === "read_asset") {
        text = await readAsset(params.arguments?.path || "");
      } else if (params.name === "read_asset_efficient") {
        const maxTokens = params.arguments?.maxTokens || 4000;
        const compression = params.arguments?.compression || "moderate";
        const result = await readAssetTokenEfficient(params.arguments?.path || "", { maxTokens, compression });
        text = result.text;
        metadata = result;
      } else if (params.name === "token_stats") {
        const model = params.arguments?.model || "default";
        const tokens = countTokens(params.arguments?.text || "", model);
        text = `Token count: ${tokens}\nModel: ${model}\nEstimated characters (4 chars/token): ${tokens * 4}`;
        metadata = { tokens, model };
      } else if (params.name === "cache_stats") {
        const stats = getCacheStats();
        text = `Cache size: ${stats.size}/${stats.maxSize} (${stats.utilization})`;
        metadata = stats;
      } else if (params.name === "cache_clear") {
        const result = clearCache();
        text = `Cache cleared: ${result.cleared} entries removed`;
        metadata = result;
      } else {
        throw new Error(`Unknown tool: ${params.name}`);
      }
      
      // Apply output fluff stripping to reduce token waste
      text = stripOutputFluff(text);
      
      const response = {
        jsonrpc: "2.0",
        id,
        result: {
          content: [{ type: "text", text }]
        }
      };
      
      // Include metadata if available
      if (metadata) {
        response.result.metadata = metadata;
      }
      
      writeMessage(response);
    } catch (error) {
      writeMessage({
        jsonrpc: "2.0",
        id,
        error: { code: -32000, message: String(error.message || error) }
      });
    }
  }
}

let buffer = "";
stdin.setEncoding("utf8");
stdin.on("data", async (chunk) => {
  buffer += chunk;
  while (true) {
    const headerEnd = buffer.indexOf("\r\n\r\n");
    if (headerEnd < 0) break;
    const header = buffer.slice(0, headerEnd);
    const match = header.match(/Content-Length:\s*(\d+)/i);
    if (!match) {
      buffer = "";
      break;
    }
    const length = Number.parseInt(match[1], 10);
    const bodyStart = headerEnd + 4;
    if (buffer.length < bodyStart + length) break;
    const body = buffer.slice(bodyStart, bodyStart + length);
    buffer = buffer.slice(bodyStart + length);
    const message = JSON.parse(body);
    if (message.method === "notifications/initialized") {
      continue;
    }
    await handleRequest(message);
  }
});
