"use client";

import Link from "next/link";
import { useState } from "react";

const GUIDES = [
  { icon: "📦", title: "Quick Setup", desc: "Get JEBAT running in 30 seconds with npx jebat-agent --full", path: "/guides/setup", category: "Getting Started" },
  { icon: "💻", title: "IDE Integration", desc: "VS Code, Zed, Cursor, Claude Desktop, Gemini CLI setup guides", path: "/guides/setup", category: "Development" },
  { icon: "🤖", title: "Local LLM Deployment", desc: "Deploy 8 local models with Ollama on your hardware", path: "/guides/setup", category: "Models" },
  { icon: "📡", title: "Channel Setup", desc: "Telegram, Discord, WhatsApp, Slack bot configuration", path: "/guides/setup", category: "Channels" },
  { icon: "🔄", title: "Migration Guide", desc: "Migrate from OpenClaw/Hermes with zero data loss", path: "/guides/setup", category: "Migration" },
  { icon: "🔒", title: "Security Hardening", desc: "Production security best practices and configuration", path: "/security", category: "Security" },
  { icon: "🐳", title: "Docker Setup", desc: "Deploy JEBAT with Docker Compose — API, WebUI, Redis, database", path: "/guides/setup", category: "DevOps" },
  { icon: "🖥️", title: "VPS Deployment", desc: "Deploy to VPS with Nginx, Traefik, and Let's Encrypt SSL", path: "/guides/setup", category: "DevOps" },
  { icon: "📊", title: "Monitoring Setup", desc: "Configure Prometheus and Grafana for real-time JEBAT metrics", path: "/guides/setup", category: "Operations" },
];

const CLI_COMMANDS = [
  { cmd: "npx jebat-agent --full", desc: "Full workspace setup with skills and IDE" },
  { cmd: "npx jebat-agent --quick", desc: "Quick setup (gateway only)" },
  { cmd: "npx jebat-agent --ide vscode", desc: "VS Code / Cursor integration" },
  { cmd: "npx jebat-agent --ide zed", desc: "Zed editor integration" },
  { cmd: "npx jebat-agent --channel telegram", desc: "Telegram bot setup" },
  { cmd: "npx jebat-agent --channel discord", desc: "Discord bot setup" },
  { cmd: "npx jebat-agent --migrate", desc: "Migrate from OpenClaw/Hermes" },
  { cmd: "npx jebat-gateway start", desc: "Start gateway server" },
  { cmd: "npx jebat-gateway status", desc: "Check gateway status" },
  { cmd: "npx jebat-setup health", desc: "Check agent health" },
];

export default function GuidesPage() {
  const [activeTab, setActiveTab] = useState<"guides" | "cli">("guides");

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-600 shadow-lg shadow-blue-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight">JEBAT Guides</span>
              <span className="text-[10px] font-medium text-blue-400/80 border border-blue-400/20 rounded-full px-2 py-0.5">Docs</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/v2" className="hidden sm:inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
              Home
            </Link>
            <Link href="/status" className="hidden sm:inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
              Status
            </Link>
            <Link href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              Try Chat
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-blue-400 to-indigo-500 px-5 py-2 text-sm font-semibold text-black hover:from-blue-300 hover:to-indigo-400 transition shadow-lg shadow-blue-500/20">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-blue-400/5 rounded-full blur-3xl"/>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-400/5 px-4 py-1.5 text-sm text-blue-300 mb-6">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            Setup & Deployment Documentation
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block">Step-by-Step</span>
            <span className="block bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Setup Guides
            </span>
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed mb-8">
            Comprehensive documentation for IDE integration, channel setup, model deployment, migration from OpenClaw/Hermes, and production hardening.
          </p>

          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-12">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-blue-400 to-indigo-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-blue-500/20 hover:from-blue-300 hover:to-indigo-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              View on GitHub
            </a>
            <Link href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Chat Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: "10+", label: "Guides", icon: "📚" },
              { value: "CLI", label: "Commands", icon: "⌘" },
              { value: "Zero", label: "Downtime", icon: "⏱️" },
              { value: "30s", label: "Setup", icon: "⚡" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">{stat.value}</div>
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
              { id: "guides", label: "All Guides", icon: "📚" },
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
        {/* Guides Tab */}
        {activeTab === "guides" && (
          <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
            {GUIDES.map((g, i) => (
              <a key={i} href={g.path} className="group rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 hover:border-blue-400/20 transition-colors block">
                <div className="flex items-start justify-between mb-4">
                  <span className="text-3xl">{g.icon}</span>
                  <span className="text-[10px] text-neutral-500 bg-white/5 border border-white/10 rounded-full px-2 py-0.5">{g.category}</span>
                </div>
                <h3 className="font-bold text-lg mb-2 group-hover:text-blue-400 transition-colors">{g.title}</h3>
                <p className="text-sm text-neutral-500 leading-relaxed">{g.desc}</p>
                <div className="mt-4 flex items-center gap-2 text-blue-400 text-sm font-medium">
                  Read Guide
                  <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
                </div>
              </a>
            ))}
          </div>
        )}

        {/* CLI Tab */}
        {activeTab === "cli" && (
          <div className="space-y-8 max-w-4xl mx-auto">
            {/* Install */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="text-blue-400">📦</span> Installation
              </h3>
              <div className="space-y-3">
                <div className="rounded-lg bg-black/40 border border-white/5 p-4 font-mono text-sm">
                  <span className="text-blue-400">$</span> <span className="text-white">npm install -g jebat-agent</span>
                </div>
                <p className="text-sm text-neutral-500">Or run directly with npx — no installation needed.</p>
              </div>
            </div>

            {/* Commands */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <span className="text-blue-400">⌘</span> CLI Commands
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
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-blue-400 to-indigo-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <span className="text-sm text-neutral-500">© 2026 NusaByte · JEBAT Guides</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <Link href="/v2" className="hover:text-white transition">Home</Link>
            <Link href="/chat" className="hover:text-white transition">Chat</Link>
            <Link href="/portal" className="hover:text-white transition">Portal</Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
