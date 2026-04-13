"use client";

import { useState } from "react";

// ─── Components ──────────────────────────────────────────────────────────

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  if (typeof window !== "undefined") {
    window.addEventListener("scroll", () => setScrolled(window.scrollY > 20));
  }

  return (
    <nav className={`sticky top-0 z-50 transition-all duration-300 ${scrolled ? "bg-[#050505]/95 backdrop-blur-xl border-b border-white/5" : "bg-transparent"}`}>
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="/" className="flex items-center gap-3 hover:opacity-80 transition">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div>
            <span className="text-lg font-bold tracking-tight">JEBAT</span>
            <span className="ml-2 text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
          </div>
        </a>

        <div className="hidden md:flex items-center gap-1 text-sm">
          {[
            { href: "#platform", label: "Platform" },
            { href: "#agents-registry", label: "Agents" },
            { href: "#specialists", label: "Specialists" },
            { href: "#features", label: "Features" },
            { href: "#chat", label: "Chat" },
            { href: "#security", label: "Security" },
            { href: "/gelanggang", label: "Gelanggang" },
            { href: "/portal", label: "Portal" },
          ].map(link => (
            <a key={link.href} href={link.href} className="px-3 py-2 text-neutral-400 hover:text-white transition rounded-lg hover:bg-white/5">
              {link.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hidden sm:flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            GitHub
          </a>
          <a href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
            Try Chat
          </a>
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-5 py-2 text-sm font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
            Get Started
          </a>
          <button className="md:hidden text-white" onClick={() => setMobileOpen(!mobileOpen)}>
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/> : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16"/>}
            </svg>
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-[#050505]/98 border-t border-white/5 px-6 py-4 space-y-2">
          {["#platform", "#agents-registry", "#specialists", "#features", "#agent", "#core", "#chat", "#security"].map(href => (
            <a key={href} href={href} className="block py-2 text-neutral-400 hover:text-white transition" onClick={() => setMobileOpen(false)}>
              {href.replace("#", "").replace("-", " ").split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
            </a>
          ))}
          <a href="/gelanggang" className="block py-2 text-neutral-400 hover:text-white transition" onClick={() => setMobileOpen(false)}>Gelanggang</a>
          <a href="/portal" className="block py-2 text-neutral-400 hover:text-white transition" onClick={() => setMobileOpen(false)}>Portal</a>
        </div>
      )}
    </nav>
  );
}

function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-cyan-400/5 rounded-full blur-3xl"/>
        <div className="absolute top-40 right-10 w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-3xl"/>
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
      </div>

      <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 md:pt-32 md:pb-24">
        <div className="text-center space-y-8 max-w-5xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            Self-Hosted · Enterprise-Ready · 100% Private
          </div>

          {/* Headline */}
          <h1 className="text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl leading-[1.05]">
            The AI Platform That{" "}
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">Remembers</span>,{" "}
            <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-500 bg-clip-text text-transparent">Collaborates</span>,{" "}
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">Protects</span>
          </h1>

          {/* Subheadline */}
          <p className="max-w-3xl mx-auto text-lg md:text-xl leading-8 text-neutral-400">
            JEBAT combines <strong className="text-white">eternal memory</strong>,{" "}
            <strong className="text-white">multi-agent orchestration</strong> across 8 local LLMs, and{" "}
            <strong className="text-white">enterprise security</strong> into one self-hosted platform.
            <br className="hidden md:block"/>
            Download, install, and own your AI — no cloud dependency.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition flex items-center gap-2 shadow-lg shadow-cyan-500/20">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Download JEBAT
              <svg className="w-4 h-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </a>
            <a href="/chat" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white hover:bg-white/10 transition flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
              Try Chat Demo
            </a>
            <a href="/gelanggang" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white hover:bg-white/10 transition flex items-center gap-2">
              🏛️ Watch Gelanggang
            </a>
          </div>

          {/* Trust Stats */}
          <div className="pt-12 grid grid-cols-2 md:grid-cols-5 gap-4 max-w-4xl mx-auto">
            {[
              { value: "10", label: "Core Agents", icon: "🤖" },
              { value: "24", label: "Specialists", icon: "👥" },
              { value: "8", label: "Local LLMs", icon: "⚡" },
              { value: "5", label: "LLM Providers", icon: "🌐" },
              { value: "100%", label: "Self-Hosted", icon: "🔒" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 hover:border-cyan-400/20 transition">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{stat.value}</div>
                <div className="text-xs text-neutral-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function PlatformSection() {
  return (
    <section id="platform" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Platform Overview</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">Two Pillars. One Platform.</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">JEBAT is built on two powerful components that work together seamlessly.</p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Jebat Agent Card */}
        <div className="group relative rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-transparent p-8 hover:border-cyan-400/30 transition-all duration-300">
          <div className="absolute top-6 right-6">
            <span className="rounded-full bg-cyan-400/10 text-cyan-400 px-3 py-1 text-xs font-medium border border-cyan-400/20">Agent</span>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center mb-6 shadow-lg shadow-cyan-500/20">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h3 className="text-2xl font-bold mb-3">Jebat Agent</h3>
          <p className="text-neutral-400 mb-6 leading-relaxed">
            The unified AI agent combining OpenClaw control plane and Hermes capture-first methodology.
            Setup your entire workspace in 30 seconds with one command.
          </p>
          <div className="space-y-3 mb-6">
            {["30-second setup wizard", "IDE integration (VS Code, Zed, Cursor)", "Channel setup (Telegram, Discord, WhatsApp)", "Local model deployment (8 models)", "Migration from OpenClaw/Hermes"].map((f, i) => (
              <div key={i} className="flex items-start gap-3 text-sm text-neutral-300">
                <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                {f}
              </div>
            ))}
          </div>
          <div className="rounded-xl bg-black/40 border border-white/5 p-4 font-mono text-sm">
            <span className="text-cyan-400">$</span> <span className="text-white">npx jebat-agent --full</span>
          </div>
          <div className="flex flex-wrap gap-3 mt-6">
            <a href="/agent" className="inline-flex items-center gap-2 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 px-4 py-2 text-sm font-medium hover:bg-cyan-400/20 transition">
              Learn More →
            </a>
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/10 text-neutral-300 px-4 py-2 text-sm hover:bg-white/5 transition">
              npm →
            </a>
          </div>
        </div>

        {/* Jebat Core Card */}
        <div className="group relative rounded-3xl border border-white/10 bg-gradient-to-br from-purple-400/5 to-transparent p-8 hover:border-purple-400/30 transition-all duration-300">
          <div className="absolute top-6 right-6">
            <span className="rounded-full bg-purple-400/10 text-purple-400 px-3 py-1 text-xs font-medium border border-purple-400/20">Core</span>
          </div>
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-400 to-pink-600 flex items-center justify-center mb-6 shadow-lg shadow-purple-500/20">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
            </svg>
          </div>
          <h3 className="text-2xl font-bold mb-3">Jebat Core</h3>
          <p className="text-neutral-400 mb-6 leading-relaxed">
            The platform backbone — IDE context injection, MCP server, memory system, skill registry,
            and the gateway that routes everything.
          </p>
          <div className="space-y-3 mb-6">
            {["5-layer cognitive memory (M0-M4)", "40+ specialized skills", "Multi-agent orchestration", "CyberSec scanning & hardening", "Gateway with provider routing"].map((f, i) => (
              <div key={i} className="flex items-start gap-3 text-sm text-neutral-300">
                <svg className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                {f}
              </div>
            ))}
          </div>
          <div className="rounded-xl bg-black/40 border border-white/5 p-4 font-mono text-sm">
            <span className="text-purple-400">$</span> <span className="text-white">npx jebat-core doctor</span>
          </div>
          <div className="flex flex-wrap gap-3 mt-6">
            <a href="/portal" className="inline-flex items-center gap-2 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 px-4 py-2 text-sm font-medium hover:bg-purple-400/20 transition">
              Enterprise Portal →
            </a>
            <a href="https://www.npmjs.com/package/jebat-core" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-full border border-white/10 text-neutral-300 px-4 py-2 text-sm hover:bg-white/5 transition">
              npm →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function AgentsRegistry() {
  const coreAgents = [
    { name: "Panglima", role: "Orchestration & Command", provider: "Anthropic", model: "claude-sonnet-4", color: "cyan", icon: "⚔️", desc: "The commander — routes tasks, manages specialists, orchestrates workflows" },
    { name: "Tukang", role: "Development & Implementation", provider: "Ollama", model: "qwen2.5-coder", color: "blue", icon: "🔨", desc: "The builder — writes code, implements features, fixes bugs" },
    { name: "Hulubalang", role: "Security Audit & Pentest", provider: "Ollama", model: "hermes-sec-v2", color: "red", icon: "🛡️", desc: "The guardian — security reviews, penetration testing, vulnerability analysis" },
    { name: "Pengawal", role: "CyberSec Defense", provider: "Ollama", model: "hermes-sec-v2", color: "orange", icon: "🔰", desc: "The defender — real-time threat detection, security monitoring, incident response" },
    { name: "Pawang", role: "Research & Investigation", provider: "Anthropic", model: "claude-sonnet-4", color: "purple", icon: "🔮", desc: "The researcher — deep investigation, documentation, comparative analysis" },
    { name: "Syahbandar", role: "Operations & Automation", provider: "Ollama", model: "qwen2.5-coder", color: "green", icon: "⚙️", desc: "The operator — CI/CD, automation, deployments, system administration" },
    { name: "Bendahara", role: "Database & Schema", provider: "Ollama", model: "qwen2.5-coder", color: "yellow", icon: "🗄️", desc: "The treasurer — database design, SQL migrations, query optimization" },
    { name: "Hikmat", role: "Memory & Context", provider: "Anthropic", model: "claude-sonnet-4", color: "pink", icon: "🧠", desc: "The wise — 5-layer eternal memory (M0-M4), cross-session continuity" },
    { name: "Penganalisis", role: "Analytics & KPI Review", provider: "Anthropic", model: "claude-sonnet-4", color: "indigo", icon: "📊", desc: "The analyst — KPI tracking, funnel analysis, experiments, reporting" },
    { name: "Penyemak", role: "QA & Validation", provider: "Anthropic", model: "claude-sonnet-4", color: "emerald", icon: "✅", desc: "The inspector — testing, verification, regression review, release confidence" },
  ];

  const colorMap: Record<string, string> = {
    cyan: "from-cyan-400/10 to-cyan-600/5 border-cyan-400/20",
    blue: "from-blue-400/10 to-blue-600/5 border-blue-400/20",
    red: "from-red-400/10 to-red-600/5 border-red-400/20",
    orange: "from-orange-400/10 to-orange-600/5 border-orange-400/20",
    purple: "from-purple-400/10 to-purple-600/5 border-purple-400/20",
    green: "from-green-400/10 to-green-600/5 border-green-400/20",
    yellow: "from-yellow-400/10 to-yellow-600/5 border-yellow-400/20",
    pink: "from-pink-400/10 to-pink-600/5 border-pink-400/20",
    indigo: "from-indigo-400/10 to-indigo-600/5 border-indigo-400/20",
    emerald: "from-emerald-400/10 to-emerald-600/5 border-emerald-400/20",
  };

  const badgeMap: Record<string, string> = {
    cyan: "bg-cyan-400/10 text-cyan-400 border-cyan-400/20",
    blue: "bg-blue-400/10 text-blue-400 border-blue-400/20",
    red: "bg-red-400/10 text-red-400 border-red-400/20",
    orange: "bg-orange-400/10 text-orange-400 border-orange-400/20",
    purple: "bg-purple-400/10 text-purple-400 border-purple-400/20",
    green: "bg-green-400/10 text-green-400 border-green-400/20",
    yellow: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
    pink: "bg-pink-400/10 text-pink-400 border-pink-400/20",
    indigo: "bg-indigo-400/10 text-indigo-400 border-indigo-400/20",
    emerald: "bg-emerald-400/10 text-emerald-400 border-emerald-400/20",
  };

  return (
    <section id="agents-registry" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Core Agents Registry</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">10 Core Agents. One Platform.</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Each agent has a specialized role, provider, and model — orchestrated by Panglima for maximum effectiveness.</p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {coreAgents.map((agent, i) => (
          <div key={i} className={`group relative rounded-2xl border bg-gradient-to-br ${colorMap[agent.color]} p-6 hover:scale-[1.02] transition-all duration-300`}>
            <div className="flex items-start justify-between mb-3">
              <div className="text-3xl">{agent.icon}</div>
              <span className={`rounded-full ${badgeMap[agent.color]} px-2.5 py-0.5 text-xs font-medium border`}>
                {agent.provider}
              </span>
            </div>
            <h3 className="text-xl font-bold text-white mb-1">{agent.name}</h3>
            <p className="text-xs text-cyan-400 font-mono mb-2">{agent.model}</p>
            <p className="text-sm text-neutral-400 mb-3 leading-relaxed">{agent.desc}</p>
            <div className="text-xs text-neutral-500 uppercase tracking-wider">{agent.role}</div>
          </div>
        ))}
      </div>

      <div className="text-center mt-10">
        <a href="#specialists" className="inline-flex items-center gap-2 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 px-6 py-3 text-sm font-medium hover:bg-cyan-400/20 transition">
          View All 24 Specialists Below ↓
        </a>
      </div>
    </section>
  );
}

function SpecialistsGrid() {
  const specialists = [
    { name: "Tukang Web", role: "Browser UI & Frontend", category: "Delivery", icon: "🌐" },
    { name: "Pembina Aplikasi", role: "Cross-Layer App Delivery", category: "Delivery", icon: "📱" },
    { name: "Khidmat Pelanggan", role: "Onboarding & Support", category: "Growth", icon: "💬" },
    { name: "Senibina Antara Muka", role: "UI/UX & Responsive Design", category: "Design", icon: "🎨" },
    { name: "Penyebar Reka Bentuk", role: "Design Systems & Tokens", category: "Design", icon: "✨" },
    { name: "Pengkarya Kandungan", role: "Content Systems & Scripts", category: "Growth", icon: "📝" },
    { name: "Jurutulis Jualan", role: "Copywriting & CTA Framing", category: "Growth", icon: "✍️" },
    { name: "Penjejak Carian", role: "SEO & Metadata", category: "Growth", icon: "🔍" },
    { name: "Penggerak Pasaran", role: "Marketing & Campaigns", category: "Growth", icon: "📣" },
    { name: "Strategi Jenama", role: "Positioning & Brand Voice", category: "Strategy", icon: "🏷️" },
    { name: "Strategi Produk", role: "Feature Framing & Roadmap", category: "Strategy", icon: "🎯" },
    { name: "Penulis Cadangan", role: "Proposals & SOWs", category: "Strategy", icon: "📄" },
    { name: "Penggerak Jualan", role: "Sales Collateral & One-Pagers", category: "Strategy", icon: "💼" },
    { name: "Perisai", role: "Security Hardening", category: "Security", icon: "🛡️" },
    { name: "Serangan", role: "Penetration Testing", category: "Security", icon: "⚔️" },
    { name: "Hulubalang", role: "Security Audit & Pentest", category: "Security", icon: "🔒" },
    { name: "Pengawal", role: "CyberSec Defense", category: "Security", icon: "🔰" },
    { name: "Tukang", role: "Full-Stack Development", category: "Delivery", icon: "🔨" },
    { name: "Bendahara", role: "Database & Migrations", category: "Delivery", icon: "🗄️" },
    { name: "Syahbandar", role: "Ops, CI/CD & Deploy", category: "Delivery", icon: "⚙️" },
    { name: "Penyemak", role: "QA & Validation", category: "Quality", icon: "✅" },
    { name: "Pawang", role: "Research & Docs", category: "Knowledge", icon: "🔮" },
    { name: "Penganalisis", role: "KPI & Funnel Analysis", category: "Quality", icon: "📊" },
    { name: "Hikmat", role: "Memory Consolidation", category: "Knowledge", icon: "🧠" },
  ];

  const categoryColors: Record<string, string> = {
    Delivery: "border-cyan-400/20 bg-cyan-400/5 text-cyan-400",
    Security: "border-red-400/20 bg-red-400/5 text-red-400",
    Growth: "border-purple-400/20 bg-purple-400/5 text-purple-400",
    Strategy: "border-amber-400/20 bg-amber-400/5 text-amber-400",
    Quality: "border-green-400/20 bg-green-400/5 text-green-400",
    Design: "border-pink-400/20 bg-pink-400/5 text-pink-400",
    Knowledge: "border-indigo-400/20 bg-indigo-400/5 text-indigo-400",
  };

  return (
    <section id="specialists" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-purple-400/20 bg-purple-400/5 px-4 py-1.5 text-sm text-purple-300 mb-4">Specialist Agents</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">24 Specialist Agents</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Domain experts spawned on-demand for specialized tasks across delivery, security, growth, strategy, and quality.</p>
      </div>

      {/* Category Legend */}
      <div className="flex flex-wrap justify-center gap-3 mb-10">
        {Object.entries(categoryColors).map(([cat, cls]) => (
          <span key={cat} className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${cls}`}>
            {cat}
          </span>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {specialists.map((s, i) => (
          <div key={i} className="group flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-cyan-400/20 hover:bg-white/[0.04] transition-all duration-200">
            <div className="text-xl flex-shrink-0">{s.icon}</div>
            <div className="min-w-0">
              <h4 className="text-sm font-semibold text-white truncate">{s.name}</h4>
              <p className="text-xs text-neutral-500">{s.role}</p>
              <span className={`inline-block mt-1 rounded-full border px-2 py-0.5 text-[10px] font-medium ${categoryColors[s.category]}`}>
                {s.category}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center mt-10">
        <a href="#features" className="inline-flex items-center gap-2 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 px-6 py-3 text-sm font-medium hover:bg-purple-400/20 transition">
          Explore All Features ↓
        </a>
      </div>
    </section>
  );
}

function FeaturesSection() {
  const orchestrationModes = [
    { name: "Multi-Agent Debate", desc: "Multiple agents argue positions, LLM-as-Judge reaches consensus", icon: "🗣️" },
    { name: "Consensus Building", desc: "Agents converge on shared understanding through structured rounds", icon: "🤝" },
    { name: "Sequential Chain", desc: "Step-by-step pipeline: research → implement → verify → deploy", icon: "🔗" },
    { name: "Parallel Analysis", desc: "Independent workers investigate simultaneously for speed", icon: "⚡" },
    { name: "Hierarchical Review", desc: "Multi-level review with escalating authority and scope", icon: "📋" },
  ];

  const llmModels = [
    { name: "Gemma 4", provider: "Google", icon: "💎" },
    { name: "Qwen2.5:14B", provider: "Alibaba", icon: "🔷" },
    { name: "Hermes3", provider: "NousResearch", icon: "🔥" },
    { name: "Phi-3", provider: "Microsoft", icon: "🧩" },
    { name: "Llama 3.1:8B", provider: "Meta", icon: "🦙" },
    { name: "Mistral", provider: "Mistral AI", icon: "💨" },
    { name: "CodeLlama:7B", provider: "Meta", icon: "🐪" },
    { name: "TinyLlama", provider: "TinyLlama", icon: "🔹" },
  ];

  const llmProviders = [
    { name: "Anthropic", models: "Claude Sonnet 4", icon: "🟠" },
    { name: "OpenAI", models: "GPT-4o, o1, o3", icon: "🔵" },
    { name: "Gemini", models: "Gemini 2.5 Pro", icon: "🟣" },
    { name: "Ollama", models: "8 Local Models", icon: "🦙" },
    { name: "ZAI", models: "Zhipu GLM", icon: "🔶" },
  ];

  return (
    <section id="features" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-4">New Features</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">Platform Features</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Every component built for performance, security, and developer experience.</p>
      </div>

      {/* Orchestration Modes */}
      <div className="mb-16">
        <h3 className="text-2xl font-bold mb-6 text-center">5 Orchestration Modes</h3>
        <div className="grid gap-4 md:grid-cols-5">
          {orchestrationModes.map((mode, i) => (
            <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-5 text-center hover:border-cyan-400/20 transition">
              <div className="text-2xl mb-2">{mode.icon}</div>
              <h4 className="text-sm font-semibold text-white mb-1">{mode.name}</h4>
              <p className="text-xs text-neutral-500">{mode.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* LLM Models & Providers */}
      <div className="grid gap-10 lg:grid-cols-2 mb-16">
        {/* Local Models */}
        <div>
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-cyan-400">8</span> Local LLM Models
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {llmModels.map((m, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-white/5 bg-black/20 p-3 hover:border-cyan-400/20 transition">
                <span className="text-lg">{m.icon}</span>
                <div>
                  <div className="text-sm font-medium text-white">{m.name}</div>
                  <div className="text-xs text-neutral-500">{m.provider}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Providers */}
        <div>
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-purple-400">5</span> LLM Providers
          </h3>
          <div className="space-y-3">
            {llmProviders.map((p, i) => (
              <div key={i} className="flex items-center gap-4 rounded-lg border border-white/5 bg-black/20 p-4 hover:border-purple-400/20 transition">
                <span className="text-xl">{p.icon}</span>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-white">{p.name}</div>
                  <div className="text-xs text-neutral-500">{p.models}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Grid */}
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {[
          {
            icon: "📝",
            title: "Markdown Rendering",
            desc: "Full tables, code blocks with syntax highlighting, headers, lists, and inline formatting in all AI responses.",
            color: "cyan",
          },
          {
            icon: "✨",
            title: "Shimmer Animations",
            desc: "Smooth shimmer loading states while AI thinks — beautiful, not frustrating. Know when work is happening.",
            color: "purple",
          },
          {
            icon: "🎯",
            title: "Confidence Scoring (ConfMAD)",
            desc: "Every response includes confidence metrics using ConfMAD paradigm. Know when the AI is certain or uncertain.",
            color: "emerald",
          },
          {
            icon: "⚖️",
            title: "LLM-as-Judge Consensus",
            desc: "A designated judge model evaluates competing agent outputs and reaches consensus for higher accuracy.",
            color: "amber",
          },
          {
            icon: "🔄",
            title: "Retry Logic",
            desc: "Automatic retry with exponential backoff for model loading failures. Resilient by default.",
            color: "blue",
          },
          {
            icon: "⚡",
            title: "LRUCache Optimization",
            desc: "Intelligent caching reduces response latency by 40-60%. Frequently accessed results served instantly.",
            color: "green",
          },
        ].map((f, i) => (
          <div key={i} className="rounded-xl border border-white/10 bg-white/[0.02] p-6 hover:border-cyan-400/20 transition">
            <div className="text-2xl mb-3">{f.icon}</div>
            <h4 className="text-base font-semibold text-white mb-2">{f.title}</h4>
            <p className="text-sm text-neutral-400 leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Customer Portal CTA */}
      <div className="mt-12 rounded-2xl border border-white/10 bg-gradient-to-r from-cyan-400/5 to-purple-400/5 p-8 text-center">
        <h3 className="text-xl font-bold mb-2">Customer Portal</h3>
        <p className="text-neutral-400 mb-4 max-w-xl mx-auto">Self-service portal for customers with usage analytics, billing, and support — all self-hosted.</p>
        <a href="/portal" className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 text-black px-6 py-3 text-sm font-semibold hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
          Open Customer Portal →
        </a>
      </div>
    </section>
  );
}

function AgentSection() {
  return (
    <section id="agent" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Jebat Agent</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">One Command. Full Setup.</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Configure your IDE, connect channels, deploy local models — all in 30 seconds.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {[
          {
            icon: "⚡",
            title: "Quick Setup",
            desc: "Interactive wizard or one-liner. Full workspace with skills and config in seconds.",
            cmd: "npx jebat-agent --quick",
          },
          {
            icon: "💻",
            title: "IDE Integration",
            desc: "Inject JEBAT context into VS Code, Zed, Cursor, Claude Desktop, or Gemini CLI.",
            cmd: "npx jebat-agent --ide vscode",
          },
          {
            icon: "📱",
            title: "Channel Setup",
            desc: "Connect Telegram, Discord, WhatsApp, or Slack with guided configuration.",
            cmd: "npx jebat-agent --channel telegram",
          },
          {
            icon: "🤖",
            title: "Local Models",
            desc: "Deploy Qwen2.5, Gemma 4, Phi-3, Hermes3 via Ollama or AirLLM on your VPS.",
            cmd: "npx jebat-agent --local-model qwen2.5",
          },
          {
            icon: "🔄",
            title: "Migration",
            desc: "Migrate from OpenClaw/Hermes automatically. Configs, skills, workspace — all converted.",
            cmd: "npx jebat-agent --migrate",
          },
          {
            icon: "🔧",
            title: "Management",
            desc: "Gateway control, agent health checks, skill listing, and deployment helpers.",
            cmd: "npx jebat-gateway status",
          },
        ].map((item, i) => (
          <div key={i} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
            <div className="text-3xl mb-4">{item.icon}</div>
            <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
            <p className="text-sm text-neutral-400 mb-4 leading-relaxed">{item.desc}</p>
            <div className="rounded-lg bg-black/40 border border-white/5 p-3 font-mono text-xs text-cyan-300">{item.cmd}</div>
          </div>
        ))}
      </div>

      <div className="text-center mt-10">
        <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-full bg-cyan-400/10 border border-cyan-400/20 text-cyan-400 px-6 py-3 text-sm font-medium hover:bg-cyan-400/20 transition">
          Get Started on GitHub →
        </a>
      </div>
    </section>
  );
}

function CoreSection() {
  return (
    <section id="core" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-purple-400/20 bg-purple-400/5 px-4 py-1.5 text-sm text-purple-300 mb-4">Jebat Core</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">The Platform Backbone</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Memory, skills, agents, security — everything that makes JEBAT intelligent.</p>
      </div>

      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        {[
          { title: "Eternal Memory", desc: "5-layer cognitive stack (M0-M4) with heat-based retention. Cross-session continuity.", icon: "🧠" },
          { title: "Skill Registry", desc: "40+ specialized skills optimized for token efficiency and real-world patterns.", icon: "🛠️" },
          { title: "Agent Orchestration", desc: "Multi-agent routing with 5 modes: Debate, Consensus, Sequential, Parallel, Hierarchical.", icon: "🎭" },
          { title: "CyberSec Suite", desc: "Hulubalang (audit), Pengawal (defense), Perisai (hardening), Serangan (pentest).", icon: "🛡️" },
          { title: "Gateway Router", desc: "Provider routing across 5 LLM backends with fallback chains and load balancing.", icon: "🌐" },
          { title: "IDE Context", desc: "Inject JEBAT into any editor. VS Code, Cursor, Zed, JetBrains, Neovim, and more.", icon: "📝" },
          { title: "LRUCache", desc: "Intelligent caching reduces response latency by 40-60% for frequently accessed results.", icon: "⚡" },
          { title: "Confidence Scoring", desc: "ConfMAD paradigm provides confidence metrics on every AI response.", icon: "🎯" },
          { title: "LLM-as-Judge", desc: "Designated judge model evaluates competing outputs for consensus-driven accuracy.", icon: "⚖️" },
        ].map((item, i) => (
          <div key={i} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
            <div className="text-3xl mb-4">{item.icon}</div>
            <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
            <p className="text-sm text-neutral-400 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      <div className="text-center mt-10">
        <a href="/portal" className="inline-flex items-center gap-2 rounded-full bg-purple-400/10 border border-purple-400/20 text-purple-400 px-6 py-3 text-sm font-medium hover:bg-purple-400/20 transition">
          Explore Enterprise Portal →
        </a>
      </div>
    </section>
  );
}

function ChatSection() {
  return (
    <section id="chat" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-4">Live Chat</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">Chat with Your Agents</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Manus/Kimi-style interface with LLM-to-LLM debates, BYOK support, and local models.</p>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Chat Preview */}
        <div className="rounded-3xl border border-white/10 bg-[#0a0a0a] overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-black/20">
            <div className="w-3 h-3 rounded-full bg-red-400/60"/>
            <div className="w-3 h-3 rounded-full bg-amber-400/60"/>
            <div className="w-3 h-3 rounded-full bg-green-400/60"/>
            <span className="ml-2 text-xs text-neutral-500 font-mono">jebat.chat</span>
          </div>
          <div className="p-6 space-y-4 min-h-[400px]">
            {/* User message */}
            <div className="flex justify-end">
              <div className="rounded-2xl bg-blue-600 text-white px-4 py-3 max-w-[80%] text-sm">
                Explain how multi-agent orchestration works in JEBAT
              </div>
            </div>
            {/* AI message */}
            <div className="flex justify-start">
              <div className="rounded-2xl bg-[#1f1f1f] text-neutral-200 px-4 py-3 max-w-[85%] text-sm leading-relaxed">
                <p className="mb-2">JEBAT's Gelanggang system connects multiple agents across different LLM providers:</p>
                <ol className="list-decimal list-inside space-y-1 text-neutral-400">
                  <li><strong className="text-white">Panglima</strong> — Orchestrator (routes tasks)</li>
                  <li><strong className="text-white">Tukang</strong> — Builder (implements solutions)</li>
                  <li><strong className="text-white">Hulubalang</strong> — Guardian (security review)</li>
                  <li><strong className="text-white">Penyemak</strong> — QA (validates output)</li>
                </ol>
              </div>
            </div>
            {/* LLM-to-LLM indicator */}
            <div className="flex justify-center">
              <span className="text-xs text-purple-400 bg-purple-400/10 border border-purple-400/20 rounded-full px-3 py-1">
                🤖 Qwen2.5 → Hermes3 discussion
              </span>
            </div>
            {/* LLM 1 */}
            <div className="flex justify-start">
              <div className="rounded-2xl bg-[#1f1f1f] border-l-2 border-purple-500 text-neutral-200 px-4 py-3 max-w-[85%] text-sm">
                <p className="text-xs text-purple-400 mb-1 font-medium">Qwen2.5 14B</p>
                The key advantage is cross-provider diversity. Each agent can use a different model, providing diverse perspectives.
              </div>
            </div>
            {/* LLM 2 */}
            <div className="flex justify-start">
              <div className="rounded-2xl bg-[#1f1f1f] border-l-2 border-cyan-500 text-neutral-200 px-4 py-3 max-w-[85%] text-sm">
                <p className="text-xs text-cyan-400 mb-1 font-medium">Hermes3 8B</p>
                Agreed. Plus the memory layer (M0-M4) ensures context persists across the entire conversation chain.
              </div>
            </div>
          </div>
          {/* Input */}
          <div className="p-4 border-t border-white/5 bg-[#0a0a0a]">
            <div className="flex gap-3">
              <input className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-cyan-400/50" placeholder="Message Jebat..." readOnly/>
              <button className="bg-cyan-500 hover:bg-cyan-400 text-black rounded-xl px-4 py-3 transition">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
              </button>
            </div>
          </div>
        </div>

        {/* Chat Features */}
        <div className="space-y-6">
          {[
            {
              icon: "🤖",
              title: "LLM-to-LLM Chat",
              desc: "Watch two AI models debate any topic. Great for idea exploration and getting multiple perspectives automatically.",
            },
            {
              icon: "🔑",
              title: "BYOK Support",
              desc: "Bring Your Own Key — use GPT-4o, Claude, or any OpenAI-compatible model alongside local models.",
            },
            {
              icon: "🌐",
              title: "8 Local Models",
              desc: "Gemma 4, Qwen2.5 14B, Hermes3, Phi-3, Llama 3.1, Mistral, CodeLlama, and TinyLlama — all running locally.",
            },
            {
              icon: "🧠",
              title: "Memory Context",
              desc: "Chat with full conversation history. JEBAT remembers preferences, decisions, and context across sessions.",
            },
          ].map((feature, i) => (
            <div key={i} className="flex gap-4 p-5 rounded-2xl border border-white/10 bg-white/[0.02] hover:border-cyan-400/20 transition">
              <div className="text-2xl flex-shrink-0">{feature.icon}</div>
              <div>
                <h4 className="font-semibold text-white mb-1">{feature.title}</h4>
                <p className="text-sm text-neutral-400 leading-relaxed">{feature.desc}</p>
              </div>
            </div>
          ))}
          <a href="/chat" className="block rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-5 text-center hover:bg-cyan-400/10 transition">
            <span className="text-cyan-400 font-medium">Try the full chat experience →</span>
          </a>
        </div>
      </div>

      <div className="text-center mt-10">
        <a href="/chat" className="inline-flex items-center gap-2 rounded-full bg-emerald-400/10 border border-emerald-400/20 text-emerald-400 px-6 py-3 text-sm font-medium hover:bg-emerald-400/20 transition">
          Launch Chat Interface →
        </a>
      </div>
    </section>
  );
}

function SecuritySection() {
  return (
    <section id="security" className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-16">
        <span className="inline-block rounded-full border border-red-400/20 bg-red-400/5 px-4 py-1.5 text-sm text-red-300 mb-4">Security</span>
        <h2 className="text-3xl font-bold md:text-5xl mb-4">Enterprise-Grade Security</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Zero-trust architecture with prompt injection defense, command sanitization, and complete audit trails. 100% self-hosted — no cloud dependency.</p>
      </div>

      {/* Core Security Features */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-12">
        {[
          { title: "Prompt Injection Defense", desc: "Input sanitization, context isolation, pattern detection, adversarial testing", color: "red", icon: "🛡️" },
          { title: "Command Sanitization", desc: "Whitelist-only execution, argument escaping, timeout enforcement, shell safety", color: "orange", icon: "🔒" },
          { title: "Complete Audit Trails", desc: "Tamper-evident operation logs, JSON format, immutable history, full traceability", color: "yellow", icon: "📋" },
          { title: "Secrets Management", desc: "Secure token handling, credential masking, auto-rotation, vault integration", color: "green", icon: "🔑" },
        ].map((item, i) => (
          <div key={i} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6 text-center">
            <div className="text-4xl mb-4">{item.icon}</div>
            <h3 className="font-semibold text-white mb-2">{item.title}</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>

      {/* CyberSec Suite */}
      <div className="mb-12">
        <h3 className="text-xl font-bold mb-6 text-center">CyberSec Suite — 4 Security Agents</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { name: "Hulubalang", role: "Security Audit & Pentest", desc: "Vulnerability scanning, pentesting, security review with structured findings", icon: "⚔️" },
            { name: "Pengawal", role: "CyberSec Defense", desc: "Real-time threat detection, security monitoring, incident response protocols", icon: "🔰" },
            { name: "Perisai", role: "Security Hardening", desc: "System hardening, configuration audit, attack surface reduction", icon: "🛡️" },
            { name: "Serangan", role: "Penetration Testing", desc: "Offensive security, red-team simulations, exploit analysis", icon: "🗡️" },
          ].map((agent, i) => (
            <div key={i} className="rounded-xl border border-red-400/10 bg-red-400/[0.02] p-5 text-center hover:border-red-400/30 transition">
              <div className="text-2xl mb-2">{agent.icon}</div>
              <h4 className="text-sm font-semibold text-white mb-1">{agent.name}</h4>
              <p className="text-xs text-red-400 mb-2">{agent.role}</p>
              <p className="text-xs text-neutral-500">{agent.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Self-Hosted Badge */}
      <div className="rounded-2xl border border-emerald-400/20 bg-gradient-to-r from-emerald-400/5 to-cyan-400/5 p-8 text-center">
        <div className="text-4xl mb-3">🔒</div>
        <h3 className="text-xl font-bold mb-2">100% Self-Hosted. No Cloud Dependency.</h3>
        <p className="text-neutral-400 max-w-2xl mx-auto mb-6">
          Every model runs locally. Every byte of data stays on your infrastructure. No telemetry, no data exfiltration, no vendor lock-in.
          Complete sovereignty over your AI operations.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {["No Cloud API Calls Required", "No Data Leaves Your Server", "No Vendor Lock-In", "No Telemetry", "SOC2 Ready", "GDPR Compliant"].map((badge, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-xs text-emerald-400">
              ✓ {badge}
            </span>
          ))}
        </div>
      </div>

      <div className="text-center mt-10">
        <a href="#features" className="inline-flex items-center gap-2 rounded-full bg-red-400/10 border border-red-400/20 text-red-400 px-6 py-3 text-sm font-medium hover:bg-red-400/20 transition">
          See All Security Features ↓
        </a>
      </div>
    </section>
  );
}

function CLIDemo() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-20">
      <div className="text-center mb-12">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">npm CLI</span>
        <h2 className="text-3xl font-bold md:text-4xl mb-4">Try from Your Terminal</h2>
        <p className="max-w-2xl mx-auto text-neutral-400">Two packages. Zero installation. Start in seconds.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* jebat-agent terminal */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-black/20">
            <div className="w-3 h-3 rounded-full bg-red-400/60"/>
            <div className="w-3 h-3 rounded-full bg-amber-400/60"/>
            <div className="w-3 h-3 rounded-full bg-green-400/60"/>
            <span className="ml-2 text-xs text-neutral-500 font-mono">jebat-agent</span>
          </div>
          <div className="p-6 space-y-4">
            <details className="group rounded-lg border border-white/5 bg-black/20">
              <summary className="cursor-pointer px-4 py-3 text-sm font-mono text-cyan-300 hover:text-cyan-200 transition flex items-center justify-between">
                <span>$ npx jebat-agent --help</span>
                <svg className="w-4 h-4 text-neutral-500 transition group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
              </summary>
              <pre className="px-4 pb-4 text-xs text-neutral-400 whitespace-pre-wrap font-mono leading-relaxed border-t border-white/5 pt-3">
{`jebat-agent v1.0.3

USAGE:
  npx jebat-agent [options]

OPTIONS:
  --quick          Quick setup (gateway only)
  --full           Full setup (workspace + skills)
  --ide <ide>      IDE integration
  --channel <ch>   Channel setup
  --local-model <m> Setup local model
  --migrate        Migrate from OpenClaw/Hermes`}
              </pre>
            </details>
            <details className="group rounded-lg border border-white/5 bg-black/20">
              <summary className="cursor-pointer px-4 py-3 text-sm font-mono text-cyan-300 hover:text-cyan-200 transition flex items-center justify-between">
                <span>$ npx jebat-agent --full</span>
                <svg className="w-4 h-4 text-neutral-500 transition group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
              </summary>
              <pre className="px-4 pb-4 text-xs text-neutral-400 whitespace-pre-wrap font-mono leading-relaxed border-t border-white/5 pt-3">
{`🚀 Setting up Jebat...

1/5 Creating directory structure...
   ✓ Created ~/.jebat

2/5 Generating gateway config...
   ✓ Gateway config generated

3/5 Setting up workspace and skills...
   ✓ Workspace and skills configured

4/5 Creating environment file...
   ✓ Environment file created

5/5 Validating setup...
   ✓ Validation passed

✅ Jebat setup complete!`}
              </pre>
            </details>
          </div>
        </div>

        {/* jebat-core terminal */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-black/20">
            <div className="w-3 h-3 rounded-full bg-red-400/60"/>
            <div className="w-3 h-3 rounded-full bg-amber-400/60"/>
            <div className="w-3 h-3 rounded-full bg-green-400/60"/>
            <span className="ml-2 text-xs text-neutral-500 font-mono">jebat-core</span>
          </div>
          <div className="p-6 space-y-4">
            <details className="group rounded-lg border border-white/5 bg-black/20">
              <summary className="cursor-pointer px-4 py-3 text-sm font-mono text-purple-300 hover:text-purple-200 transition flex items-center justify-between">
                <span>$ npx jebat-core doctor</span>
                <svg className="w-4 h-4 text-neutral-500 transition group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
              </summary>
              <pre className="px-4 pb-4 text-xs text-neutral-400 whitespace-pre-wrap font-mono leading-relaxed border-t border-white/5 pt-3">
{`🩺 JEBAT Doctor — Workspace Health Check

✅ Core files: 5/5
✅ Gateway: http://localhost:18789
✅ Skills directory found (40+ skills)
✅ Memory: 4 daily files
✅ JEBAT home: ~/.jebat

✅ All checks passed. JEBAT is healthy.`}
              </pre>
            </details>
            <details className="group rounded-lg border border-white/5 bg-black/20">
              <summary className="cursor-pointer px-4 py-3 text-sm font-mono text-purple-300 hover:text-purple-200 transition flex items-center justify-between">
                <span>$ npx jebat-core status</span>
                <svg className="w-4 h-4 text-neutral-500 transition group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/></svg>
              </summary>
              <pre className="px-4 pb-4 text-xs text-neutral-400 whitespace-pre-wrap font-mono leading-relaxed border-t border-white/5 pt-3">
{`📡 JEBAT System Status

✅ Online Gateway (http://localhost:18789)
✅ Healthy VPS (jebat.online)
✅ Healthy WebUI (/webui/)
✅ Ollama Server (8 models)

✅ npm: jebat-core@3.0.0`}
              </pre>
            </details>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/5">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-10 md:grid-cols-5">
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div>
                <span className="text-lg font-bold">JEBAT</span>
                <span className="ml-2 text-[10px] text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">v3.0.0</span>
              </div>
            </div>
            <p className="text-sm text-neutral-400 mb-6 max-w-sm leading-relaxed">
              The self-hosted AI platform that remembers, collaborates, and protects.
              Built by <a href="https://nusabyte.my" className="text-cyan-300 hover:text-cyan-200 transition">NusaByte</a> for teams who need an AI operator — not just a chatbot.
            </p>
            <div className="flex flex-wrap gap-3 mb-6">
              {["Self-Hosted", "SOC2 Ready", "GDPR Compliant", "MIT License"].map((badge, i) => (
                <span key={i} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-neutral-400">
                  {badge}
                </span>
              ))}
            </div>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-neutral-300 transition hover:bg-white/10 hover:text-white">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              <span>Star on GitHub</span>
            </a>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
            <div className="space-y-3 text-sm text-neutral-500">
              <a href="#agents-registry" className="block transition hover:text-white">Core Agents</a>
              <a href="#specialists" className="block transition hover:text-white">Specialists</a>
              <a href="#features" className="block transition hover:text-white">Features</a>
              <a href="#agent" className="block transition hover:text-white">Jebat Agent</a>
              <a href="#core" className="block transition hover:text-white">Jebat Core</a>
              <a href="#chat" className="block transition hover:text-white">Chat Interface</a>
              <a href="#security" className="block transition hover:text-white">Security</a>
              <a href="/gelanggang" className="block transition hover:text-white">Gelanggang Demo</a>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Resources</h4>
            <div className="space-y-3 text-sm text-neutral-500">
              <a href="/portal" className="block transition hover:text-white">Customer Portal</a>
              <a href="/guides" className="block transition hover:text-white">Guides</a>
              <a href="/onboarding" className="block transition hover:text-white">Onboarding</a>
              <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">Documentation</a>
              <a href="https://github.com/nusabyte-my/jebat-core/issues" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">Report Issues</a>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Company</h4>
            <div className="space-y-3 text-sm text-neutral-500">
              <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">nusabyte.my</a>
              <a href="https://github.com/nusabyte-my" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">GitHub Organization</a>
              <a href="https://jebat.online" className="block transition hover:text-white">jebat.online</a>
            </div>
          </div>
        </div>
      </div>
      <div className="border-t border-white/5">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-xs text-neutral-600">
              © 2026 <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">NusaByte</a>.
              Owner: <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">humm1ngb1rd</a>.
              All rights reserved.
            </div>
            <div className="flex items-center gap-4 text-xs text-neutral-600">
              <a href="https://github.com/nusabyte-my/jebat-core/blob/main/LICENSE" target="_blank" rel="noopener noreferrer" className="transition hover:text-white">MIT License</a>
              <span>·</span>
              <span>Built in Malaysia</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100 overflow-x-hidden">
      <Navbar />
      <HeroSection />
      <PlatformSection />
      <AgentsRegistry />
      <SpecialistsGrid />
      <FeaturesSection />
      <AgentSection />
      <CoreSection />
      <ChatSection />
      <SecuritySection />
      <CLIDemo />
      <Footer />
    </main>
  );
}
