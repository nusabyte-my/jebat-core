"use client";

import Link from "next/link";
import { useState } from "react";

const FEATURES = [
  { icon: "⚡", title: "30-Second Setup", desc: "One command deploys your entire AI workspace with skills, configuration, and IDE integration." },
  { icon: "🧠", title: "8 Local LLMs", desc: "Gemma 4, Qwen2.5 14B, Hermes3, Phi-3, Llama 3.1, Mistral, CodeLlama, TinyLlama — all running locally." },
  { icon: "💻", title: "IDE Integration", desc: "VS Code, Zed, Cursor, Claude Desktop, Gemini CLI — works with your favorite editor out of the box." },
  { icon: "📡", title: "Channel Setup", desc: "Telegram, Discord, WhatsApp, Slack — connect your AI agent to communication platforms." },
  { icon: "🔄", title: "Migration Tool", desc: "Automatic conversion from OpenClaw/Hermes setups with zero data loss and full backward compatibility." },
  { icon: "🔧", title: "Gateway Management", desc: "Start, stop, restart, and monitor your JEBAT Gateway with simple CLI commands." },
];

const CLI_COMMANDS = [
  { cmd: "npx jebat-agent --full", desc: "Full workspace setup with skills and IDE" },
  { cmd: "npx jebat-agent --quick", desc: "Quick setup (gateway only)" },
  { cmd: "npx jebat-agent --migrate", desc: "Migrate from OpenClaw/Hermes" },
  { cmd: "npx jebat-agent --ide vscode", desc: "VS Code / Cursor integration" },
  { cmd: "npx jebat-agent --ide zed", desc: "Zed editor integration" },
  { cmd: "npx jebat-agent --channel telegram", desc: "Telegram bot setup" },
  { cmd: "npx jebat-agent --channel discord", desc: "Discord bot setup" },
  { cmd: "npx jebat-gateway start", desc: "Start gateway server" },
  { cmd: "npx jebat-gateway status", desc: "Check gateway status" },
];

const MODELS = [
  { name: "Gemma 4", size: "9.6GB", desc: "Google's latest all-rounder", best: "Best overall" },
  { name: "Qwen2.5 14B", size: "9GB", desc: "Alibaba's coding powerhouse", best: "Coding & reasoning" },
  { name: "Hermes3", size: "4.7GB", desc: "NousResearch's reasoning model", best: "Complex reasoning" },
  { name: "Phi-3", size: "2.2GB", desc: "Microsoft's lightweight model", best: "Fast responses" },
  { name: "Llama 3.1 8B", size: "4.9GB", desc: "Meta's general purpose model", best: "General purpose" },
  { name: "Mistral", size: "4.4GB", desc: "Mistral AI's balanced model", best: "Balanced performance" },
  { name: "CodeLlama 7B", size: "3.8GB", desc: "Meta's code-focused model", best: "Code generation" },
  { name: "TinyLlama", size: "637MB", desc: "Ultra-lightweight testing", best: "Lightweight testing" },
];

export default function AgentPage() {
  const [activeTab, setActiveTab] = useState<"features" | "models" | "cli">("features");

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-purple-400 to-pink-600 shadow-lg shadow-purple-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight">Jebat Agent</span>
              <span className="text-[10px] font-medium text-purple-400/80 border border-purple-400/20 rounded-full px-2 py-0.5">v3.0</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/v2" className="hidden sm:inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
              Home
            </Link>
            <Link href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              Try Chat
            </Link>
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-purple-400 to-pink-500 px-5 py-2 text-sm font-semibold text-black hover:from-purple-300 hover:to-pink-400 transition shadow-lg shadow-purple-500/20">
              npm: jebat-agent
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-purple-400/5 rounded-full blur-3xl"/>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-purple-400/20 bg-purple-400/5 px-4 py-1.5 text-sm text-purple-300 mb-6">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            Unified AI Agent · OpenClaw + Hermes Combined
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block">The Agent That</span>
            <span className="block bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
              Controls, Deploys, Integrates
            </span>
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed mb-8">
            Jebat Agent combines the OpenClaw control plane and Hermes capture-first methodology into one powerful, self-hosted platform. Deploy your entire AI workspace in 30 seconds.
          </p>

          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-12">
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-purple-400 to-pink-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-purple-500/20 hover:from-purple-300 hover:to-pink-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Install jebat-agent
            </a>
            <Link href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Chat Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: "30s", label: "Setup Time", icon: "⚡" },
              { value: "8", label: "Local LLMs", icon: "🧠" },
              { value: "40+", label: "Skills", icon: "📦" },
              { value: "5", label: "IDE Support", icon: "💻" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">{stat.value}</div>
                <div className="text-xs text-neutral-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tab Navigation */}
      <section className="border-t border-white/5">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 max-w-md mx-auto">
            {([
              { id: "features", label: "Features", icon: "✨" },
              { id: "models", label: "Local Models", icon: "🤖" },
              { id: "cli", label: "CLI Commands", icon: "⌘" },
            ] as const).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  activeTab === tab.id
                    ? "bg-white/10 text-white"
                    : "text-neutral-400 hover:text-white hover:bg-white/5"
                }`}
              >
                <span className="mr-1.5">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Tab Content */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-20">
        {/* Features Tab */}
        {activeTab === "features" && (
          <div className="space-y-12 lg:space-y-16">
            <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
              {FEATURES.map((f, i) => (
                <div key={i} className="group rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 text-center hover:border-purple-400/20 transition-colors">
                  <div className="text-4xl mb-4">{f.icon}</div>
                  <h3 className="font-bold text-lg mb-2">{f.title}</h3>
                  <p className="text-sm text-neutral-500 leading-relaxed">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Models Tab */}
        {activeTab === "models" && (
          <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 max-w-6xl mx-auto">
            {MODELS.map((m, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 hover:border-purple-400/20 transition-colors">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 mx-auto mb-4 flex items-center justify-center text-sm font-bold text-white shadow-lg">
                  {m.name.substring(0, 2).toUpperCase()}
                </div>
                <h3 className="font-bold text-center mb-1">{m.name}</h3>
                <p className="text-xs text-neutral-500 text-center mb-3">{m.desc}</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">Size</span>
                    <span className="text-white font-mono">{m.size}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-neutral-400">Best For</span>
                    <span className="text-purple-400">{m.best}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* CLI Tab */}
        {activeTab === "cli" && (
          <div className="space-y-8 max-w-4xl mx-auto">
            {/* Install */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="text-purple-400">📦</span> Installation
              </h3>
              <div className="rounded-lg bg-black/40 border border-white/5 p-4 font-mono text-sm">
                <span className="text-purple-400">$</span> <span className="text-white">npm install -g jebat-agent</span>
              </div>
              <p className="text-sm text-neutral-500 mt-3">Or run directly with npx — no installation needed.</p>
            </div>

            {/* Commands */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <span className="text-purple-400">⌘</span> CLI Commands
              </h3>
              <div className="space-y-3">
                {CLI_COMMANDS.map((c, i) => (
                  <div key={i} className="rounded-lg bg-black/30 border border-white/5 p-4">
                    <code className="text-sm text-cyan-400 font-mono">{c.cmd}</code>
                    <p className="text-xs text-neutral-500 mt-2">{c.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Directory Structure */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="text-purple-400">📁</span> Workspace Structure
              </h3>
              <div className="rounded-lg bg-black/30 border border-white/5 p-4 font-mono text-sm">
                <div className="text-neutral-500">~/.jebat/</div>
                <div className="text-neutral-400 pl-4">├── jebat-gateway.json</div>
                <div className="text-neutral-400 pl-4">├── .env</div>
                <div className="text-neutral-400 pl-4">└── workspace/</div>
                <div className="text-neutral-400 pl-8">├── IDENTITY.md</div>
                <div className="text-neutral-400 pl-8">├── SOUL.md</div>
                <div className="text-neutral-400 pl-8">├── TOOLS.md</div>
                <div className="text-neutral-400 pl-8">├── USER.md</div>
                <div className="text-neutral-400 pl-8">└── skills/</div>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-purple-400 to-pink-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <span className="text-sm text-neutral-500">© 2026 NusaByte · JEBAT Agent</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <Link href="/v2" className="hover:text-white transition">Home</Link>
            <Link href="/chat" className="hover:text-white transition">Chat</Link>
            <Link href="/portal" className="hover:text-white transition">Portal</Link>
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">npm</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
