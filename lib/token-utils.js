/**
 * Token utilities for counting, estimation, and budget tracking.
 * Provides token-aware operations for all LLM interactions.
 */

// Approximate token ratios for different models
const MODEL_TOKEN_RATIOS = {
  gpt4: { charsPerToken: 4.0, name: "GPT-4" },
  gpt35: { charsPerToken: 3.5, name: "GPT-3.5" },
  claude: { charsPerToken: 3.7, name: "Claude" },
  gemini: { charsPerToken: 4.2, name: "Gemini" },
  llama: { charsPerToken: 3.8, name: "Llama" },
  mistral: { charsPerToken: 3.9, name: "Mistral" },
  default: { charsPerToken: 4.0, name: "Default" }
};

// Default token budgets for different operation types
const DEFAULT_BUDGETS = {
  casualChat: { input: 2000, output: 500 },
  quickFact: { input: 1500, output: 300 },
  codeReview: { input: 8000, output: 1000 },
  implementation: { input: 12000, output: 2000 },
  research: { input: 10000, output: 1500 },
  memorySearch: { input: 4000, output: 800 },
  planning: { input: 6000, output: 1500 },
  verification: { input: 5000, output: 1000 }
};

/**
 * Count tokens in text using character-based estimation.
 * More accurate for English text than simple word counting.
 */
export function countTokens(text, model = "default") {
  if (!text) return 0;
  const ratio = MODEL_TOKEN_RATIOS[model] || MODEL_TOKEN_RATIOS.default;
  
  // More accurate estimation: count words + punctuation + special chars
  const words = text.split(/\s+/).filter(Boolean).length;
  const avgWordChars = text.replace(/\s+/g, "").length / Math.max(words, 1);
  
  // Base estimation
  let tokens = Math.ceil(text.length / ratio.charsPerToken);
  
  // Adjustment for very short or very long texts
  if (text.length < 100) {
    tokens = Math.max(tokens, words * 1.3); // Short texts have overhead
  }
  
  return Math.ceil(tokens);
}

/**
 * Estimate token count for a message with system prompt + context.
 */
export function estimateMessageTokens(systemPrompt, userMessage, context = "") {
  const systemTokens = countTokens(systemPrompt);
  const userTokens = countTokens(userMessage);
  const contextTokens = countTokens(context);
  
  // Message formatting overhead (~4 tokens per message)
  const overhead = 4;
  
  return {
    system: systemTokens,
    user: userTokens,
    context: contextTokens,
    overhead,
    total: systemTokens + userTokens + contextTokens + overhead
  };
}

/**
 * Check if text exceeds token budget.
 */
export function checkBudget(text, maxTokens, model = "default") {
  const tokens = countTokens(text, model);
  return {
    within: tokens <= maxTokens,
    used: tokens,
    limit: maxTokens,
    remaining: Math.max(0, maxTokens - tokens),
    utilization: (tokens / maxTokens * 100).toFixed(1) + "%"
  };
}

/**
 * Calculate token cost for multi-part message.
 */
export function calculateTokenCost(parts, model = "default") {
  const costs = {};
  let total = 0;
  
  for (const [key, text] of Object.entries(parts)) {
    const tokens = countTokens(text, model);
    costs[key] = tokens;
    total += tokens;
  }
  
  return { costs, total };
}

/**
 * Get recommended token budget for operation type.
 */
export function getBudget(operationType) {
  return DEFAULT_BUDGETS[operationType] || DEFAULT_BUDGETS.casualChat;
}

/**
 * Create a token budget tracker for a session.
 */
export function createBudgetTracker(budgets = DEFAULT_BUDGETS) {
  const usage = {};
  const startTime = Date.now();
  
  return {
    record(operationType, inputTokens, outputTokens) {
      if (!usage[operationType]) {
        usage[operationType] = { input: 0, output: 0, calls: 0 };
      }
      usage[operationType].input += inputTokens;
      usage[operationType].output += outputTokens;
      usage[operationType].calls += 1;
    },
    
    getUsage(operationType) {
      const budget = budgets[operationType];
      const used = usage[operationType] || { input: 0, output: 0, calls: 0 };
      
      return {
        operation: operationType,
        budget: budget || { input: "unlimited", output: "unlimited" },
        used,
        remaining: budget ? {
          input: Math.max(0, budget.input - used.input),
          output: Math.max(0, budget.output - used.output)
        } : "unlimited",
        utilization: budget ? {
          input: (used.input / budget.input * 100).toFixed(1) + "%",
          output: (used.output / budget.output * 100).toFixed(1) + "%"
        } : "unlimited"
      };
    },
    
    getSummary() {
      const totalInput = Object.values(usage).reduce((sum, u) => sum + u.input, 0);
      const totalOutput = Object.values(usage).reduce((sum, u) => sum + u.output, 0);
      const totalCalls = Object.values(usage).reduce((sum, u) => sum + u.calls, 0);
      const duration = Math.floor((Date.now() - startTime) / 1000);
      
      return {
        operations: Object.keys(usage).length,
        totalCalls,
        totalTokens: { input: totalInput, output: totalOutput, combined: totalInput + totalOutput },
        duration: `${Math.floor(duration / 60)}m ${duration % 60}s`,
        averageTokensPerCall: totalCalls > 0 ? Math.round((totalInput + totalOutput) / totalCalls) : 0
      };
    },
    
    export() {
      return {
        usage,
        budgets,
        summary: this.getSummary()
      };
    }
  };
}

/**
 * Optimize text to fit within token budget by smart truncation.
 * Preserves structure and key information.
 */
export function optimizeForTokenBudget(text, targetTokens, model = "default") {
  const currentTokens = countTokens(text, model);
  
  if (currentTokens <= targetTokens) {
    return { text, tokens: currentTokens, optimized: false };
  }
  
  const ratio = MODEL_TOKEN_RATIOS[model] || MODEL_TOKEN_RATIOS.default;
  const maxChars = Math.floor(targetTokens * ratio.charsPerTokens);
  
  if (text.length <= maxChars) {
    return { text, tokens: currentTokens, optimized: false };
  }
  
  // Smart truncation: preserve complete paragraphs
  const truncated = text.substring(0, maxChars);
  const lastParagraphEnd = Math.max(
    truncated.lastIndexOf("\n\n"),
    truncated.lastIndexOf("\n"),
    truncated.lastIndexOf(". ")
  );
  
  const optimized = lastParagraphEnd > maxChars * 0.5
    ? truncated.substring(0, lastParagraphEnd) + "\n\n[... truncated for token efficiency]"
    : truncated + "\n\n[... truncated for token efficiency]";
  
  const optimizedTokens = countTokens(optimized, model);
  
  return {
    text: optimized,
    tokens: optimizedTokens,
    originalTokens: currentTokens,
    savings: currentTokens - optimizedTokens,
    optimized: true
  };
}

export { MODEL_TOKEN_RATIOS, DEFAULT_BUDGETS };
