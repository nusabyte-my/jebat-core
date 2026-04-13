"use client";

function PortalPage() {
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
                <span className="text-lg font-bold tracking-tight">JEBAT Portal</span>
                <span className="ml-2 text-[10px] font-medium text-emerald-400/80 border border-emerald-400/20 rounded-full px-2 py-0.5">Enterprise</span>
              </div>
            </a>
          </div>
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm text-neutral-400 hover:text-white transition flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
              Home
            </a>
            <a href="/agent" className="text-sm text-neutral-400 hover:text-white transition">Agent</a>
            <a href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
              Chat
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-emerald-400/5 rounded-full blur-3xl"/>
          <div className="absolute top-40 right-10 w-[400px] h-[400px] bg-cyan-500/5 rounded-full blur-3xl"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 md:pt-32 md:pb-24">
          <div className="text-center space-y-8 max-w-5xl mx-auto">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
              Enterprise Customer Portal
            </div>

            <h1 className="text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl leading-[1.05]">
              Manage Your{" "}
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-500 bg-clip-text text-transparent">AI Workforce</span>
            </h1>

            <p className="max-w-3xl mx-auto text-lg md:text-xl leading-8 text-neutral-400">
              Monitor agents, track usage, manage teams, and optimize your AI operations — all in one centralized dashboard.
            </p>

            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <a href="#agents" className="rounded-full bg-gradient-to-r from-emerald-400 to-cyan-500 px-8 py-4 text-base font-semibold text-black hover:from-emerald-300 hover:to-cyan-400 transition flex items-center gap-2 shadow-lg shadow-emerald-500/20">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                View Agents
              </a>
              <a href="#usage" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white hover:bg-white/10 transition">
                Usage Analytics
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Agent Status Overview */}
      <section id="agents" className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-4">Agent Status</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">Your AI Workforce</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">10 core agents + 24 specialists, all monitored and managed in real-time.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            { name: "Panglima", role: "Orchestration", provider: "Anthropic", model: "claude-sonnet-4", status: "online", icon: "🎯", color: "cyan" },
            { name: "Tukang", role: "Development", provider: "Ollama", model: "qwen2.5-coder:7b", status: "online", icon: "💻", color: "blue" },
            { name: "Hulubalang", role: "Security", provider: "Ollama", model: "hermes-sec-v2", status: "online", icon: "🛡️", color: "red" },
            { name: "Pengawal", role: "CyberSec", provider: "Ollama", model: "hermes-sec-v2", status: "online", icon: "🔒", color: "orange" },
            { name: "Pawang", role: "Research", provider: "Anthropic", model: "claude-sonnet-4", status: "online", icon: "🔍", color: "purple" },
            { name: "Syahbandar", role: "Operations", provider: "Ollama", model: "qwen2.5-coder:7b", status: "online", icon: "⚙️", color: "green" },
            { name: "Bendahara", role: "Database", provider: "Ollama", model: "qwen2.5-coder:7b", status: "online", icon: "🗄️", color: "yellow" },
            { name: "Hikmat", role: "Memory", provider: "Anthropic", model: "claude-sonnet-4", status: "online", icon: "🧠", color: "indigo" },
            { name: "Penganalisis", role: "Analytics", provider: "Anthropic", model: "claude-sonnet-4", status: "online", icon: "📊", color: "pink" },
            { name: "Penyemak", role: "QA", provider: "Anthropic", model: "claude-sonnet-4", status: "online", icon: "✅", color: "emerald" },
          ].map((agent, i) => (
            <div key={i} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="text-3xl">{agent.icon}</div>
                <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                  agent.status === "online" 
                    ? "bg-emerald-400/10 text-emerald-400 border border-emerald-400/20" 
                    : "bg-red-400/10 text-red-400 border border-red-400/20"
                }`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${agent.status === "online" ? "bg-emerald-400" : "bg-red-400"}`}/>
                  {agent.status === "online" ? "Online" : "Offline"}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{agent.name}</h3>
              <p className="text-sm text-neutral-400 mb-3">{agent.role}</p>
              <div className="space-y-2 text-xs text-neutral-500">
                <div className="flex justify-between">
                  <span>Provider</span>
                  <span className="text-neutral-300">{agent.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span>Model</span>
                  <span className="text-neutral-300 font-mono">{agent.model}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Specialist Agents */}
        <div className="mt-12">
          <h3 className="text-xl font-semibold text-white mb-6">Specialist Agents (24+)</h3>
          <div className="flex flex-wrap gap-3">
            {["Tukang Web", "Pembina Aplikasi", "Senibina Antara Muka", "Penyebar Reka Bentuk", "Pengkarya Kandungan", "Jurutulis Jualan", "Penjejak Carian", "Penggerak Pasaran", "Strategi Jenama", "Strategi Produk", "Khidmat Pelanggan", "Penulis Cadangan", "Penggerak Jualan"].map((agent, i) => (
              <span key={i} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-neutral-300 hover:border-cyan-400/30 hover:text-cyan-300 transition cursor-default">
                {agent}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Usage Analytics */}
      <section id="usage" className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Analytics</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">Usage Analytics</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Track performance, costs, and agent utilization.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Total Requests", value: "12,847", change: "+12%", icon: "📈", color: "emerald" },
            { label: "Avg Response Time", value: "2.1s", change: "-53%", icon: "⚡", color: "cyan" },
            { label: "Cache Hit Rate", value: "65%", change: "+65%", icon: "💾", color: "blue" },
            { label: "Cost This Month", value: "$247", change: "-30%", icon: "💰", color: "purple" },
          ].map((stat, i) => (
            <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl">{stat.icon}</span>
                <span className={`text-xs font-medium ${stat.change.startsWith("+") ? "text-emerald-400" : "text-cyan-400"}`}>
                  {stat.change}
                </span>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-sm text-neutral-400">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Performance Metrics */}
        <div className="mt-12 rounded-3xl border border-white/10 bg-white/[0.02] p-8">
          <h3 className="text-lg font-semibold text-white mb-6">Performance Metrics</h3>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              { label: "Uptime", value: "99.9%", target: "99.99%", progress: 99.9 },
              { label: "Throughput", value: "47 req/s", target: "100 req/s", progress: 47 },
              { label: "Error Rate", value: "0.05%", target: "<0.1%", progress: 95 },
            ].map((metric, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-neutral-400">{metric.label}</span>
                  <span className="text-white font-medium">{metric.value}</span>
                </div>
                <div className="w-full bg-white/5 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-emerald-400 to-cyan-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${metric.progress}%` }}
                  />
                </div>
                <div className="text-xs text-neutral-500 mt-1">Target: {metric.target}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Customer Features */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full border border-purple-400/20 bg-purple-400/5 px-4 py-1.5 text-sm text-purple-300 mb-4">Customer Portal</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">Enterprise Features</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Everything you need to manage your AI workforce.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: "👥",
              title: "Team Workspaces",
              desc: "Isolated agent pools per team with role-based access control and custom permissions.",
              status: "Coming Soon",
            },
            {
              icon: "🔐",
              title: "SSO Integration",
              desc: "SAML/OIDC support for enterprise single sign-on with Active Directory sync.",
              status: "Planned",
            },
            {
              icon: "📋",
              title: "Audit Trails",
              desc: "Complete agent activity logging with SOC2 and GDPR compliance reporting.",
              status: "In Development",
            },
            {
              icon: "🤖",
              title: "Khidmat Pelanggan",
              desc: "AI-powered 24/7 customer support agent with seamless human escalation.",
              status: "Coming Soon",
            },
            {
              icon: "📊",
              title: "Custom Reports",
              desc: "Export usage analytics, cost tracking, and performance metrics to PDF/CSV.",
              status: "Planned",
            },
            {
              icon: "🔌",
              title: "Webhooks & API",
              desc: "REST API v2 with webhook support for integrating with your existing systems.",
              status: "Planned",
            },
          ].map((feature, i) => (
            <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="flex items-start justify-between mb-4">
                <span className="text-2xl">{feature.icon}</span>
                <span className="text-xs font-medium text-neutral-500 bg-white/5 px-2 py-1 rounded-full">
                  {feature.status}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-neutral-400 leading-relaxed">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-emerald-400/20 bg-gradient-to-br from-emerald-400/5 to-transparent p-10 text-center md:p-16">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">Ready to Scale Your AI Operations?</h2>
          <p className="mx-auto mb-8 max-w-lg text-neutral-400">Get started with enterprise features, dedicated support, and custom integrations.</p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="mailto:enterprise@jebat.online" className="rounded-full bg-gradient-to-r from-emerald-400 to-cyan-500 px-8 py-3.5 text-base font-semibold text-black transition hover:from-emerald-300 hover:to-cyan-400 flex items-center gap-2 shadow-lg shadow-emerald-500/20">
              Contact Sales
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
            </a>
            <a href="/" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              Back to Home
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
                <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-600">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    <path d="M2 17l10 5 10-5"/>
                    <path d="M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <div>
                  <span className="text-lg font-bold">JEBAT Portal</span>
                  <span className="ml-2 text-[10px] text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">Enterprise</span>
                </div>
              </div>
              <p className="text-sm text-neutral-400 mb-6 max-w-sm leading-relaxed">
                Enterprise customer portal for managing AI agents, tracking usage, and optimizing operations. Built by <a href="https://nusabyte.my" className="text-emerald-300 hover:text-emerald-200 transition">NusaByte</a>.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Portal</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <a href="#agents" className="block transition hover:text-white">Agent Status</a>
                <a href="#usage" className="block transition hover:text-white">Usage Analytics</a>
                <a href="/chat" className="block transition hover:text-white">Chat Demo</a>
                <a href="/agent" className="block transition hover:text-white">Agent Info</a>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <a href="/" className="block transition hover:text-white">← Home</a>
                <a href="/gelanggang" className="block transition hover:text-white">Gelanggang</a>
                <a href="/guides" className="block transition hover:text-white">Guides</a>
                <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">GitHub</a>
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-white/5">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-xs text-neutral-600">
                © 2026 <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-emerald-300">NusaByte</a>. All rights reserved.
              </div>
              <div className="flex items-center gap-4 text-xs text-neutral-600">
                <span>Enterprise Ready</span>
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

export default PortalPage;
