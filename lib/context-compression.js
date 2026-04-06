/**
 * Context compression module for optimizing prompts and system messages.
 * Reduces token usage while preserving critical information.
 */

import { countTokens } from "./token-utils.js";

/**
 * Compression strategies for different use cases.
 */
const COMPRESSION_LEVELS = {
  minimal: { removeWhitespace: true, shortenPaths: false, abbreviate: false, target: 0.95 },
  moderate: { removeWhitespace: true, shortenPaths: true, abbreviate: true, target: 0.75 },
  aggressive: { removeWhitespace: true, shortenPaths: true, abbreviate: true, target: 0.50 }
};

/**
 * Common abbreviations for context compression.
 */
const ABBREVIATIONS = {
  "operating system": "OS",
  "configuration": "config",
  "directory": "dir",
  "environment": "env",
  "implementation": "impl",
  "documentation": "docs",
  "development": "dev",
  "production": "prod",
  "development environment": "dev env",
  "production environment": "prod env",
  "application programming interface": "API",
  "command line interface": "CLI",
  "graphical user interface": "GUI",
  "integrated development environment": "IDE",
  "large language model": "LLM",
  "model context protocol": "MCP"
};

/**
 * Remove redundant whitespace and normalize text.
 */
function normalizeWhitespace(text) {
  return text
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n") // Max 2 consecutive newlines
    .replace(/[ \t]+$/gm, "") // Trailing whitespace
    .replace(/^([ \t]+)/gm, (match) => {
      // Preserve markdown indentation (2 or 4 spaces)
      const spaces = match.length;
      if (spaces >= 4) return "    ";
      if (spaces >= 2) return "  ";
      return "";
    })
    .trim();
}

/**
 * Shorten file paths while preserving readability.
 */
function shortenPaths(text) {
  return text.replace(/(?:[A-Z]:\\|\/)[\w\\/-]+/g, (path) => {
    const parts = path.replace(/[\\/]+/g, "/").split("/");
    if (parts.length <= 3) return path;
    return `.../${parts.slice(-3).join("/")}`;
  });
}

/**
 * Apply abbreviations to text.
 */
function applyAbbreviations(text) {
  let result = text;
  for (const [full, abbrev] of Object.entries(ABBREVIATIONS)) {
    const regex = new RegExp(`\\b${full}\\b`, "gi");
    result = result.replace(regex, abbrev);
  }
  return result;
}

/**
 * Remove verbose but non-essential content from markdown.
 */
function compressMarkdown(text, level) {
  if (level === "minimal") return text;
  
  const lines = text.split("\n");
  const compressed = [];
  let inCodeBlock = false;
  let skipNext = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Preserve code blocks
    if (line.trim().startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      compressed.push(line);
      continue;
    }
    
    if (inCodeBlock) {
      compressed.push(line);
      continue;
    }
    
    // Skip examples in aggressive mode
    if (level === "aggressive" && (
      line.toLowerCase().includes("example:") ||
      line.toLowerCase().includes("for example") ||
      line.toLowerCase().includes("e.g.,")
    )) {
      skipNext = true;
      continue;
    }
    
    // Skip verbose explanations
    if (level === "aggressive" && (
      line.startsWith("> ") || // Blockquotes
      line.toLowerCase().includes("note:") ||
      line.toLowerCase().includes("important:")
    )) {
      continue;
    }
    
    // Compress list items
    if (line.match(/^[-*]\s+/) && level === "aggressive") {
      compressed.push(line.replace(/^[-*]\s+/, "• "));
      continue;
    }
    
    compressed.push(line);
  }
  
  return compressed.join("\n");
}

/**
 * Compress text using multiple strategies.
 */
export function compressContext(text, options = {}) {
  const {
    level = "moderate",
    preserveCodeBlocks = true,
    preserveHeaders = true,
    targetTokens = null,
    model = "default"
  } = options;
  
  const config = COMPRESSION_LEVELS[level] || COMPRESSION_LEVELS.moderate;
  const originalTokens = countTokens(text, model);
  
  let result = text;
  
  // Step 1: Normalize whitespace (always)
  result = normalizeWhitespace(result);
  
  // Step 2: Apply abbreviations
  if (config.abbreviate) {
    result = applyAbbreviations(result);
  }
  
  // Step 3: Shorten paths
  if (config.shortenPaths) {
    result = shortenPaths(result);
  }
  
  // Step 4: Compress markdown
  if (level !== "minimal") {
    result = compressMarkdown(result, level);
  }
  
  // Step 5: Trim to target tokens if specified
  if (targetTokens) {
    const currentTokens = countTokens(result, model);
    if (currentTokens > targetTokens) {
      const ratio = currentTokens / targetTokens;
      const maxChars = Math.floor(result.length / ratio);
      result = result.substring(0, maxChars);
      
      // Find good break point
      const lastBreak = Math.max(
        result.lastIndexOf("\n\n"),
        result.lastIndexOf(".\n"),
        result.lastIndexOf("\n")
      );
      
      if (lastBreak > maxChars * 0.7) {
        result = result.substring(0, lastBreak);
      }
      
      result += "\n\n[context compressed for token efficiency]";
    }
  }
  
  const compressedTokens = countTokens(result, model);
  const savings = originalTokens - compressedTokens;
  
  return {
    text: result,
    originalTokens,
    compressedTokens,
    savings,
    compressionRatio: (compressedTokens / originalTokens * 100).toFixed(1) + "%",
    level
  };
}

/**
 * Compress system prompt for token efficiency.
 * Preserves critical instructions while removing verbosity.
 */
export function compressSystemPrompt(systemPrompt, targetTokens = null) {
  // Remove redundant phrasing
  let compressed = systemPrompt
    .replace(/Please note that/gi, "Note:")
    .replace(/It is important to remember/gi, "Remember:")
    .replace(/You should always/gi, "Always")
    .replace(/You must never/gi, "Never")
    .replace(/Make sure to/gi, "Ensure:")
    .replace(/In order to/gi, "To")
    .replace(/Due to the fact that/gi, "Because")
    .replace(/At this point in time/gi, "Now")
    .replace(/In the event that/gi, "If");
  
  // Remove filler sentences
  const fillerPatterns = [
    /^.*feel free to.*$/gim,
    /^.*don't hesitate to.*$/gim,
    /^.*let me know if.*$/gim,
    /^.*I hope this helps.*$/gim,
    /^.*As an AI.*$/gim
  ];
  
  for (const pattern of fillerPatterns) {
    compressed = compressed.replace(pattern, "");
  }
  
  // Clean up extra newlines
  compressed = compressed.replace(/\n{3,}/g, "\n\n").trim();
  
  const originalTokens = countTokens(systemPrompt);
  const compressedTokens = countTokens(compressed);
  
  // Further compress if still over target
  if (targetTokens && compressedTokens > targetTokens) {
    const result = compressContext(compressed, {
      level: "aggressive",
      targetTokens,
      preserveCodeBlocks: true,
      preserveHeaders: true
    });
    
    return {
      text: result.text,
      originalTokens,
      compressedTokens: result.compressedTokens,
      savings: originalTokens - result.compressedTokens,
      compressionRatio: (result.compressedTokens / originalTokens * 100).toFixed(1) + "%"
    };
  }
  
  return {
    text: compressed,
    originalTokens,
    compressedTokens,
    savings: originalTokens - compressedTokens,
    compressionRatio: (compressedTokens / originalTokens * 100).toFixed(1) + "%"
  };
}

/**
 * Extract only essential information from context.
 * Strips examples, explanations, and verbose descriptions.
 */
export function extractEssentialContext(text, options = {}) {
  const {
    keepHeadings = true,
    keepCodeExamples = false,
    keepLists = true,
    maxTokens = 2000
  } = options;
  
  const lines = text.split("\n");
  const essential = [];
  let inCodeBlock = false;
  let tokenCount = 0;
  
  for (const line of lines) {
    // Track code blocks
    if (line.trim().startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      if (keepCodeExamples) {
        essential.push(line);
      }
      continue;
    }
    
    if (inCodeBlock) {
      if (keepCodeExamples) {
        essential.push(line);
      }
      continue;
    }
    
    // Keep headings
    if (keepHeadings && line.match(/^#{1,6}\s+/)) {
      essential.push(line);
      continue;
    }
    
    // Keep list items
    if (keepLists && line.match(/^[-*]\s+/)) {
      essential.push(line);
      continue;
    }
    
    // Keep short, directive sentences
    if (line.length < 100 && line.match(/^(Never|Always|Ensure|Use|Check|Verify|Do not)/i)) {
      essential.push(line);
      continue;
    }
    
    // Skip long explanations
    if (line.length > 150) {
      continue;
    }
    
    // Keep other lines if under token budget
    const tempText = essential.join("\n") + "\n" + line;
    const tempTokens = countTokens(tempText);
    
    if (tempTokens <= maxTokens) {
      essential.push(line);
    } else {
      break;
    }
  }
  
  const result = essential.join("\n");
  const resultTokens = countTokens(result);
  
  return {
    text: result,
    tokens: resultTokens,
    originalTokens: countTokens(text),
    savings: countTokens(text) - resultTokens,
    compressionRatio: (resultTokens / countTokens(text) * 100).toFixed(1) + "%"
  };
}

export { COMPRESSION_LEVELS, ABBREVIATIONS };
