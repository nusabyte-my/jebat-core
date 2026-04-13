"use client";

function AgentPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight">Jebat Agent</span>
                <span className="ml-2 text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
              </div>
            </a>
          </div>
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm text-neutral-400 hover:text-white transition flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
              Home
            </a>
            <a href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
              Try Chat
            </a>
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-5 py-2 text-sm font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
              npm: jebat-agent
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
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
              Unified AI Agent · OpenClaw + Hermes Combined
            </div>

            {/* Headline */}
            <h1 className="text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl leading-[1.05]">
              The Agent That{" "}
              <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">Controls</span>
              ,{" "}
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-500 bg-clip-text text-transparent">Captures</span>
              ,{" "}
              <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">Executes</span>
            </h1>

            {/* Subheadline */}
            <p className="max-w-3xl mx-auto text-lg md:text-xl leading-8 text-neutral-400">
              Jebat Agent unifies <strong className="text-white">OpenClaw's control plane</strong> and <strong className="text-white">Hermes' capture-first methodology</strong> into one powerful AI agent.
              <br className="hidden md:block"/>
              Setup in 30 seconds. Deploy local models. Connect channels. Own your AI.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition flex items-center gap-2 shadow-lg shadow-cyan-500/20">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
                Install via npm
                <svg className="w-4 h-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
              </a>
              <a href="#features" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white hover:bg-white/10 transition">
                Explore Features
              </a>
            </div>

            {/* Trust Stats */}
            <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
              {[
                { value: "8", label: "Local LLM Models", icon: "🤖" },
                { value: "5", label: "LLM Providers", icon: "🌐" },
                { value: "6", label: "IDE Integrations", icon: "💻" },
                { value: "30s", label: "Setup Time", icon: "⚡" },
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

      {/* What is Jebat Agent? */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">The Agent</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">Two Platforms. One Agent.</h2>
          <p className="max-w-3xl mx-auto text-neutral-400 text-lg">
            Jebat Agent combines the best of both OpenClaw and Hermes into a unified, powerful AI agent that does more than just chat.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2">
          {/* From OpenClaw */}
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-transparent p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">From OpenClaw</h3>
                <p className="text-xs text-cyan-400">Control Plane Heritage</p>
              </div>
            </div>
            <div className="space-y-4">
              {[
                { title: "Provider Routing", desc: "Route tasks across multiple LLM backends with automatic fallback chains" },
                { title: "Channel Surfaces", desc: "Connect Telegram, Discord, WhatsApp, Slack — all through one gateway" },
                { title: "Workstation Access", desc: "Manage CLI, VS Code, VPS, and remote surfaces from one interface" },
                { title: "Health Monitoring", desc: "Real-time posture assessment and system health tracking" },
              ].map((item, i) => (
                <div key={i} className="flex gap-3">
                  <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                  <div>
                    <p className="font-medium text-white text-sm">{item.title}</p>
                    <p className="text-xs text-neutral-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* From Hermes */}
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-purple-400/5 to-transparent p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-purple-400/10 border border-purple-400/20 flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a855f7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a10 10 0 10 10 10H12V2z"/>
                  <path d="M20.66 8A10 10 0 0014 2v6.66h6.66z" opacity="0.5"/>
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">From Hermes</h3>
                <p className="text-xs text-purple-400">Capture-First Methodology</p>
              </div>
            </div>
            <div className="space-y-4">
              {[
                { title: "Capture-First Workflow", desc: "Understand → Plan → Execute → Verify — structured thinking before action" },
                { title: "Direct Execution", desc: "Low fluff, implementation-first responses that get things done" },
                { title: "Multi-Agent Orchestration", desc: "Route work across multiple agents with intelligent delegation" },
                { title: "Context Awareness", desc: "Remember preferences, decisions, and context across every session" },
              ].map((item, i) => (
                <div key={i} className="flex gap-3">
                  <svg className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                  <div>
                    <p className="font-medium text-white text-sm">{item.title}</p>
                    <p className="text-xs text-neutral-400">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Capabilities</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">What Jebat Agent Can Do</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">More than just a chatbot — a complete AI operator for your workflow.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: "⚡",
              title: "30-Second Setup",
              desc: "One command configures your entire workspace with skills, IDE integration, and environment setup.",
              cmd: "npx jebat-agent --full",
            },
            {
              icon: "🤖",
              title: "8 Local LLM Models",
              desc: "Deploy Gemma 4, Qwen2.5 14B, Hermes3, Phi-3, Llama 3.1, Mistral, CodeLlama, and TinyLlama locally.",
              cmd: "npx jebat-agent --local-model qwen2.5",
            },
            {
              icon: "💻",
              title: "IDE Integration",
              desc: "Inject JEBAT context into VS Code, Zed, Cursor, Claude Desktop, Gemini CLI, and more.",
              cmd: "npx jebat-agent --ide vscode",
            },
            {
              icon: "📱",
              title: "Channel Setup",
              desc: "Connect Telegram, Discord, WhatsApp, or Slack with guided configuration wizards.",
              cmd: "npx jebat-agent --channel telegram",
            },
            {
              icon: "🔄",
              title: "Migration Tool",
              desc: "Automatically migrate from OpenClaw/Hermes. All configs, skills, and workspace converted seamlessly.",
              cmd: "npx jebat-agent --migrate",
            },
            {
              icon: "🔧",
              title: "Gateway Management",
              desc: "Control your gateway, check agent health, list skills, and deploy to VPS — all from CLI.",
              cmd: "npx jebat-gateway status",
            },
          ].map((feature, i) => (
            <div key={i} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="text-3xl mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-neutral-400 mb-4 leading-relaxed">{feature.desc}</p>
              <div className="rounded-lg bg-black/40 border border-white/5 p-3 font-mono text-xs text-cyan-300">{feature.cmd}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">How It Works</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">From Zero to Agent in 4 Steps</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">No complex configuration. No manual setup. Just one command.</p>
        </div>

        <div className="grid gap-8 md:grid-cols-4">
          {[
            { step: "1", title: "Install", desc: "Run `npx jebat-agent` from any terminal. No installation needed.", icon: "📦" },
            { step: "2", title: "Choose Mode", desc: "Quick setup for gateway, or full workspace with skills and IDE.", icon: "🎯" },
            { step: "3", title: "Configure", desc: "Connect channels, deploy local models, integrate your IDE.", icon: "⚙️" },
            { step: "4", title: "Start Working", desc: "Your agent is ready. Chat, orchestrate, deploy, build.", icon: "🚀" },
          ].map((item, i) => (
            <div key={i} className="relative">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400/20 to-blue-500/20 border border-cyan-400/20 mb-4">
                  <span className="text-2xl">{item.icon}</span>
                </div>
                <div className="text-xs font-medium text-cyan-400 mb-2">STEP {item.step}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">{item.desc}</p>
              </div>
              {i < 3 && (
                <div className="hidden md:block absolute top-8 -right-4 text-neutral-700">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7"/></svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CLI Commands */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-12">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">CLI Reference</span>
          <h2 className="text-3xl font-bold md:text-4xl mb-4">Every Command You Need</h2>
          <p className="max-w-2xl mx-auto text-neutral-400">Full reference for the jebat-agent CLI.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-black/20">
              <div className="w-3 h-3 rounded-full bg-red-400/60"/>
              <div className="w-3 h-3 rounded-full bg-amber-400/60"/>
              <div className="w-3 h-3 rounded-full bg-green-400/60"/>
              <span className="ml-2 text-xs text-neutral-500 font-mono">Setup Commands</span>
            </div>
            <div className="p-6 space-y-4">
              {[
                { cmd: "npx jebat-agent", desc: "Interactive setup wizard" },
                { cmd: "npx jebat-agent --quick", desc: "Quick setup (gateway only)" },
                { cmd: "npx jebat-agent --full", desc: "Full workspace + skills" },
                { cmd: "npx jebat-agent --ide vscode", desc: "VS Code / Cursor integration" },
                { cmd: "npx jebat-agent --channel telegram", desc: "Telegram bot setup" },
                { cmd: "npx jebat-agent --local-model qwen2.5", desc: "Deploy Qwen2.5 locally" },
                { cmd: "npx jebat-agent --migrate", desc: "Migrate from OpenClaw/Hermes" },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <code className="text-xs font-mono text-cyan-300 bg-black/30 rounded px-2 py-1 flex-shrink-0">{item.cmd}</code>
                  <span className="text-xs text-neutral-400 pt-1">{item.desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.02] overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-black/20">
              <div className="w-3 h-3 rounded-full bg-red-400/60"/>
              <div className="w-3 h-3 rounded-full bg-amber-400/60"/>
              <div className="w-3 h-3 rounded-full bg-green-400/60"/>
              <span className="ml-2 text-xs text-neutral-500 font-mono">Management Commands</span>
            </div>
            <div className="p-6 space-y-4">
              {[
                { cmd: "npx jebat-gateway start", desc: "Start gateway server" },
                { cmd: "npx jebat-gateway status", desc: "Check gateway status" },
                { cmd: "npx jebat-gateway restart", desc: "Restart gateway" },
                { cmd: "npx jebat-gateway logs", desc: "View gateway logs" },
                { cmd: "npx jebat-setup health", desc: "Check agent health" },
                { cmd: "npx jebat-setup skills", desc: "List available skills" },
                { cmd: "npx jebat-setup test", desc: "Test agent connectivity" },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <code className="text-xs font-mono text-purple-300 bg-black/30 rounded px-2 py-1 flex-shrink-0">{item.cmd}</code>
                  <span className="text-xs text-neutral-400 pt-1">{item.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Architecture</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">How Jebat Agent Works</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">A unified architecture that connects everything.</p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-8 md:p-12">
          <div className="grid gap-8 md:grid-cols-3">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400/20 to-blue-500/20 border border-cyan-400/20 mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Gateway Layer</h3>
              <p className="text-sm text-neutral-400 leading-relaxed">Routes requests across 5+ LLM providers with automatic fallback chains and load balancing.</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-400/20 to-pink-500/20 border border-purple-400/20 mb-4">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Agent Core</h3>
              <p className="text-sm text-neutral-400 leading-relaxed">Capture-first execution with multi-agent orchestration, memory, and context awareness.</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400/20 to-green-500/20 border border-emerald-400/20 mb-4">
                <span className="text-2xl">📱</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Channel Layer</h3>
              <p className="text-sm text-neutral-400 leading-relaxed">Connect Telegram, Discord, WhatsApp, Slack — all through one unified interface.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/5 to-transparent p-10 text-center md:p-16">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">Ready to Deploy Your Agent?</h2>
          <p className="mx-auto mb-8 max-w-lg text-neutral-400">One command. 30 seconds. Full AI operator ready to go.</p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-3.5 text-base font-semibold text-black transition hover:from-cyan-300 hover:to-blue-400 flex items-center gap-2 shadow-lg shadow-cyan-500/20">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
              npx jebat-agent
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </a>
            <a href="/chat" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              Try Chat Demo
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid gap-10 md:grid-cols-4">
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
                  <span className="text-lg font-bold">Jebat Agent</span>
                  <span className="ml-2 text-[10px] text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">v3.0.0</span>
                </div>
              </div>
              <p className="text-sm text-neutral-400 mb-6 max-w-sm leading-relaxed">
                The unified AI agent combining OpenClaw control plane and Hermes capture-first methodology. Built by <a href="https://nusabyte.my" className="text-cyan-300 hover:text-cyan-200 transition">NusaByte</a>.
              </p>
              <div className="flex flex-wrap gap-3 mb-6">
                {["Self-Hosted", "npm Package", "Open Source", "MIT License"].map((badge, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-neutral-400">{badge}</span>
                ))}
              </div>
              <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-neutral-300 transition hover:bg-white/10 hover:text-white">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"/></svg>
                View on npm
              </a>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Agent</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <a href="#features" className="block transition hover:text-white">Features</a>
                <a href="/chat" className="block transition hover:text-white">Chat Demo</a>
                <a href="https://www.npmjs.com/package/jebat-agent" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">npm Package</a>
                <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">GitHub</a>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <a href="/" className="block transition hover:text-white">← Home</a>
                <a href="/gelanggang" className="block transition hover:text-white">Gelanggang</a>
                <a href="/guides" className="block transition hover:text-white">Guides</a>
                <a href="/onboarding" className="block transition hover:text-white">Onboarding</a>
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-white/5">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-xs text-neutral-600">
                © 2026 <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">NusaByte</a>. All rights reserved.
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
    </main>
  );
}

export default AgentPage;
