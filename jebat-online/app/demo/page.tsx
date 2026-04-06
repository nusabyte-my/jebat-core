"use client";

import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  tokens?: number;
}

const thinkingModes = [
  { id: "fast", label: "Fast", color: "text-green-300" },
  { id: "deliberate", label: "Deliberate", color: "text-cyan-300" },
  { id: "deep", label: "Deep", color: "text-blue-300" },
  { id: "strategic", label: "Strategic", color: "text-purple-300" },
  { id: "creative", label: "Creative", color: "text-pink-300" },
  { id: "critical", label: "Critical", color: "text-red-300" },
];

const demoProviders = [
  { id: "ollama", name: "Ollama" },
  { id: "zai", name: "ZAI" },
  { id: "openai", name: "OpenAI" },
  { id: "anthropic", name: "Anthropic" },
  { id: "gemini", name: "Google Gemini" },
  { id: "openrouter", name: "OpenRouter" },
];

const sampleMessages: Record<string, string> = {
  fast: "Fast response mode — quick answers for simple questions.",
  deliberate: "I'll think through this step by step. Let me analyze the problem systematically, considering trade-offs and edge cases before providing a recommendation.",
  deep: "Let me go deep on this. First, I'll examine the underlying assumptions. Second, I'll trace the causal chain. Third, I'll model the second-order effects. Here's what emerges...",
  strategic: "Looking at this strategically: short-term we optimize for velocity, mid-term for maintainability, long-term for optionality. The move that serves all three is...",
  creative: "What if we flipped the problem entirely? Instead of building X, what if we made Y so compelling that X becomes unnecessary? Here's a lateral take...",
  critical: "Let me stress-test this assumption. The weak point I see is the dependency on Z — if that fails, the whole chain collapses. Here's the failure mode analysis...",
};

export default function DemoPage() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "⚔️ I'm JEBAT — your LLM operator with eternal memory. Ask me anything, and try different thinking modes. I remember everything across this session.", tokens: 0 },
  ]);
  const [input, setInput] = useState("");
  const [selectedMode, setSelectedMode] = useState("deliberate");
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [isThinking, setIsThinking] = useState(false);
  const [tokenCount, setTokenCount] = useState(0);
  const [memoryDemo, setMemoryDemo] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isThinking) return;

    const userMsg: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);

    // Simulate thinking delay
    const delay = selectedMode === "fast" ? 500 : selectedMode === "deep" ? 2500 : selectedMode === "strategic" ? 2000 : 1200;

    setTimeout(() => {
      const mode = thinkingModes.find((m) => m.id === selectedMode);
      const thinkingText = sampleMessages[selectedMode] || "Processing your request...";
      const estimatedTokens = Math.floor(input.length / 4) + Math.floor(thinkingText.length / 4);

      const assistantMsg: Message = {
        role: "assistant",
        content: thinkingText,
        thinking: mode ? `${mode.label} mode — ${selectedProvider} provider` : undefined,
        tokens: estimatedTokens,
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setTokenCount((prev) => prev + estimatedTokens);
      setIsThinking(false);
    }, delay);
  };

  const testMemory = () => {
    const memoryMsg: Message = {
      role: "assistant",
      content: "🧠 Memory demo: I'll remember that you prefer dark mode and Python for backend development. Next time you ask about stack preferences, I'll recall this.\n\n**M1 Episodic stored:** User preference — dark mode, Python backend\n**Heat score:** 85 (high relevance)\n**Layer:** M1 → will consolidate to M2 if accessed 3+ times",
      tokens: 45,
    };
    setMessages((prev) => [...prev, memoryMsg]);
    setTokenCount((prev) => prev + 45);
    setMemoryDemo(true);
  };

  const skills = [
    { name: "Panglima", desc: "Orchestration", emoji: "⚔️" },
    { name: "Hulubalang", desc: "Security", emoji: "🛡️" },
    { name: "Tukang", desc: "Development", emoji: "🔧" },
    { name: "Pawang", desc: "Research", emoji: "🔍" },
    { name: "Syahbandar", desc: "Operations", emoji: "⚙️" },
  ];

  const testSkill = (skill: string) => {
    const skillMsg: Message = {
      role: "assistant",
      content: `🗡️ **${skill} activated**\n\nLoading skill context...\n✓ SKILL.md loaded\n✓ References loaded\n✓ Tool definitions loaded\n\nReady for ${skill.toLowerCase()}-specific tasks. What would you like me to do?`,
      tokens: 30,
    };
    setMessages((prev) => [...prev, skillMsg]);
    setTokenCount((prev) => prev + 30);
  };

  return (
    <main className="h-screen bg-[#050505] text-neutral-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl px-4 py-3">
        <div className="mx-auto max-w-5xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚔️</span>
            <div>
              <div className="text-sm font-semibold">JEBAT Live Demo</div>
              <div className="text-xs text-neutral-500">Try thinking modes, memory, and skills</div>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-neutral-500">
            <span>{tokenCount.toLocaleString()} tokens</span>
            <a href="/" className="transition hover:text-white">← Home</a>
          </div>
        </div>
      </header>

      {/* Controls bar */}
      <div className="border-b border-white/5 bg-black/20 px-4 py-2">
        <div className="mx-auto max-w-5xl flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-neutral-500">Think:</span>
            {thinkingModes.map((m) => (
              <button
                key={m.id}
                onClick={() => setSelectedMode(m.id)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
                  selectedMode === m.id ? "bg-cyan-400/15 text-cyan-300" : "text-neutral-500 hover:text-neutral-300"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-neutral-500">Provider:</span>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="rounded-md border border-white/10 bg-black/30 px-2 py-1 text-xs text-neutral-300 outline-none"
            >
              {demoProviders.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <div className="flex-1" />
          <button onClick={testMemory} className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-400 hover:text-white transition">
            🧠 Test Memory
          </button>
          {skills.map((s) => (
            <button key={s.name} onClick={() => testSkill(s.name)} className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-400 hover:text-white transition">
              {s.emoji} {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-2xl rounded-2xl px-5 py-3.5 ${
                msg.role === "user"
                  ? "bg-cyan-400/10 text-cyan-100 border border-cyan-400/20"
                  : "bg-white/[0.03] border border-white/10"
              }`}>
                {msg.thinking && (
                  <div className="mb-2 flex items-center gap-2">
                    <span className="inline-flex h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    <span className="text-xs text-cyan-400/70 font-mono">{msg.thinking}</span>
                  </div>
                )}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                {msg.tokens !== undefined && msg.tokens > 0 && (
                  <div className="mt-2 text-xs text-neutral-600 font-mono">~{msg.tokens} tokens</div>
                )}
              </div>
            </div>
          ))}
          {isThinking && (
            <div className="flex justify-start">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-xs text-neutral-500 font-mono">
                    {thinkingModes.find((m) => m.id === selectedMode)?.label} thinking...
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-white/5 bg-[#050505]/80 backdrop-blur-xl px-4 py-4">
        <div className="mx-auto max-w-5xl flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask JEBAT anything... (Enter to send)"
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none focus:border-cyan-400/50 placeholder:text-neutral-600"
          />
          <button
            onClick={sendMessage}
            disabled={isThinking || !input.trim()}
            className={`rounded-xl px-6 py-3 text-sm font-medium transition ${
              isThinking || !input.trim()
                ? "bg-white/5 text-neutral-600 cursor-not-allowed"
                : "bg-cyan-400 text-black hover:bg-cyan-300"
            }`}
          >
            Send ⚔️
          </button>
        </div>
      </div>
    </main>
  );
}
