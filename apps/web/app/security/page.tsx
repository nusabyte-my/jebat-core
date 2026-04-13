"use client";

import Link from "next/link";
import { useState } from "react";

const SECURITY_TOOLS = [
  {
    icon: "🔍",
    name: "Hulubalang",
    role: "Security Audit & Compliance",
    desc: "Automated security assessments, compliance reporting (SOC2, ISO 27001, GDPR), risk analysis and scoring, and executive summary generation.",
    features: ["Compliance auditing", "Risk scoring", "Executive reports", "Session tracking"],
    gradient: "from-red-400 to-rose-500",
    initials: "HB",
  },
  {
    icon: "🛡️",
    name: "Pengawal",
    role: "CyberSec Defense & Scanning",
    desc: "Vulnerability scanning and detection, real-time threat monitoring, automated incident response, and network service discovery.",
    features: ["Vuln scanning", "Threat monitoring", "Incident response", "Service discovery"],
    gradient: "from-orange-400 to-amber-500",
    initials: "PG",
  },
  {
    icon: "🔒",
    name: "Perisai",
    role: "System Hardening & Compliance",
    desc: "Configuration audit and remediation, security baseline enforcement, access control verification, and patch management tracking.",
    features: ["Config auditing", "Baseline enforcement", "Access control", "Patch management"],
    gradient: "from-yellow-400 to-orange-500",
    initials: "PS",
  },
  {
    icon: "⚔️",
    name: "Serangan",
    role: "Penetration Testing & Red Team",
    desc: "Automated penetration testing, exploit simulation and validation, attack surface mapping, and red team operations.",
    features: ["Pen testing", "Exploit simulation", "Attack mapping", "Red team ops"],
    gradient: "from-purple-400 to-pink-500",
    initials: "SG",
  },
];

const CLI_COMMANDS = [
  { cmd: "npx jebat-security init", desc: "Initialize security workspace" },
  { cmd: "npx jebat-security audit <target>", desc: "Run Hulubalang security audit" },
  { cmd: "npx jebat-security scan <target>", desc: "Run Pengawal vulnerability scan" },
  { cmd: "npx jebat-security harden <target>", desc: "Run Perisai system hardening" },
  { cmd: "npx jebat-security pentest <target>", desc: "Run Serangan penetration test" },
  { cmd: "npx jebat-security report [session]", desc: "Generate security report" },
  { cmd: "npx jebat-security status", desc: "Check security system status" },
];

export default function SecurityPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "tools" | "cli">("overview");

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-red-400 to-rose-600 shadow-lg shadow-red-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight">JEBAT</span>
              <span className="text-[10px] font-medium text-red-400/80 border border-red-400/20 rounded-full px-2 py-0.5">Security</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/v2" className="hidden sm:inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
              Home
            </Link>
            <Link href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              Try Chat
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-red-400 to-rose-500 px-5 py-2 text-sm font-semibold text-black hover:from-red-300 hover:to-rose-400 transition shadow-lg shadow-red-500/20">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-red-400/5 rounded-full blur-3xl"/>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-red-400/20 bg-red-400/5 px-4 py-1.5 text-sm text-red-300 mb-6">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            Four-Layer Security Suite · Enterprise-Grade · Zero Trust
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block">Military-Grade</span>
            <span className="block bg-gradient-to-r from-red-400 via-orange-400 to-yellow-400 bg-clip-text text-transparent">
              Security Infrastructure
            </span>
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed mb-8">
            Four specialized security agents — <strong className="text-white">Hulubalang</strong> (audit),{" "}
            <strong className="text-white">Pengawal</strong> (defense),{" "}
            <strong className="text-white">Perisai</strong> (hardening), and{" "}
            <strong className="text-white">Serangan</strong> (pentest) — working together to protect your infrastructure.
          </p>

          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-12">
            <a href="https://www.npmjs.com/package/jebat-security" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-red-400 to-rose-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-red-500/20 hover:from-red-300 hover:to-rose-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              Install Security CLI
            </a>
            <Link href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Chat Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: "4", label: "Security Layers", icon: "🛡️" },
              { value: "0", label: "Data Breaches", icon: "🔒" },
              { value: "100%", label: "Audit Coverage", icon: "📋" },
              { value: "24/7", label: "Monitoring", icon: "👁️" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-red-400 to-orange-500 bg-clip-text text-transparent">{stat.value}</div>
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
              { id: "overview", label: "Overview", icon: "📊" },
              { id: "tools", label: "Security Tools", icon: "🛠️" },
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
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-12 lg:space-y-16">
            {/* Architecture */}
            <div className="text-center">
              <h2 className="text-2xl md:text-3xl font-bold mb-4">Security Architecture</h2>
              <p className="text-neutral-400 max-w-2xl mx-auto mb-8">Four specialized agents working together to provide comprehensive security coverage for your infrastructure.</p>
              
              <div className="grid gap-4 md:gap-6 grid-cols-2 lg:grid-cols-4 max-w-5xl mx-auto">
                {SECURITY_TOOLS.map((tool, i) => (
                  <div key={i} className="group rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 text-center hover:border-red-400/20 transition-colors">
                    <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${tool.gradient} mx-auto mb-3 flex items-center justify-center text-lg font-bold text-white shadow-lg`}>
                      {tool.initials}
                    </div>
                    <h3 className="font-bold mb-1">{tool.name}</h3>
                    <p className="text-xs text-neutral-500 mb-3">{tool.role}</p>
                    <div className="space-y-1.5">
                      {tool.features.map((f, j) => (
                        <div key={j} className="text-[10px] text-neutral-400 bg-white/5 rounded px-2 py-1">{f}</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Features */}
            <div className="grid gap-6 md:gap-8 md:grid-cols-2 max-w-5xl mx-auto">
              {[
                { icon: "🔍", title: "Prompt Injection Defense", desc: "Automatic detection and blocking of malicious prompts before they reach your AI models." },
                { icon: "🔐", title: "Command Sanitization", desc: "All inputs validated and sanitized before execution. No injection attacks possible." },
                { icon: "📋", title: "Complete Audit Trails", desc: "Every action logged for compliance, review, and incident response. Full accountability." },
                { icon: "🏠", title: "100% Self-Hosted", desc: "Your data never leaves your infrastructure. No cloud, no third-party, no vendor lock-in." },
              ].map((f, i) => (
                <div key={i} className="flex items-start gap-4 p-5 rounded-xl border border-white/5 bg-white/[0.02]">
                  <span className="text-2xl flex-shrink-0">{f.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm md:text-base mb-1">{f.title}</h3>
                    <p className="text-xs md:text-sm text-neutral-500">{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tools Tab */}
        {activeTab === "tools" && (
          <div className="space-y-8 max-w-5xl mx-auto">
            {SECURITY_TOOLS.map((tool, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
                <div className="flex items-start gap-4 md:gap-6">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${tool.gradient} flex items-center justify-center shadow-lg flex-shrink-0`}>
                    <span className="text-2xl font-bold text-white">{tool.initials}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <h3 className="text-xl md:text-2xl font-bold">{tool.icon} {tool.name}</h3>
                      <span className="text-xs text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">{tool.role}</span>
                    </div>
                    <p className="text-sm md:text-base text-neutral-400 leading-relaxed mb-4">{tool.desc}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {tool.features.map((f, j) => (
                        <div key={j} className="flex items-center gap-2 text-xs text-neutral-300">
                          <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                          {f}
                        </div>
                      ))}
                    </div>
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
                <span className="text-red-400">📦</span> Installation
              </h3>
              <div className="space-y-3">
                <div className="rounded-lg bg-black/40 border border-white/5 p-4 font-mono text-sm">
                  <span className="text-red-400">$</span> <span className="text-white">npm install -g jebat-security</span>
                </div>
                <p className="text-sm text-neutral-500">Or run directly with npx — no installation needed.</p>
              </div>
            </div>

            {/* Commands */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <span className="text-red-400">⌘</span> CLI Commands
              </h3>
              <div className="space-y-3">
                {CLI_COMMANDS.map((c, i) => (
                  <div key={i} className="rounded-lg bg-black/30 border border-white/5 p-4">
                    <div className="flex items-start gap-3">
                      <code className="flex-1 text-sm text-cyan-400 font-mono">{c.cmd}</code>
                    </div>
                    <p className="text-xs text-neutral-500 mt-2">{c.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Security API */}
            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="text-red-400">🔌</span> Security API
              </h3>
              <div className="space-y-3">
                <div className="rounded-lg bg-black/40 border border-white/5 p-4 font-mono text-sm">
                  <div className="text-neutral-500 mb-2"># Create target</div>
                  <div><span className="text-red-400">$</span> <span className="text-white">curl -X POST http://localhost:8080/api/v1/security/targets</span></div>
                  <div className="text-neutral-500 mt-1">  -H "Content-Type: application/json"</div>
                  <div className="text-neutral-500">  -d &#123;"url": "https://target.com"&#125;</div>
                </div>
                <p className="text-sm text-neutral-500">Full API documentation at <a href="/security" className="text-red-400 hover:text-red-300 underline">/api/v1/security/*</a></p>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-red-400 to-rose-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <span className="text-sm text-neutral-500">© 2026 NusaByte · JEBAT Security Suite</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <Link href="/v2" className="hover:text-white transition">Home</Link>
            <Link href="/chat" className="hover:text-white transition">Chat</Link>
            <Link href="/portal" className="hover:text-white transition">Portal</Link>
            <a href="https://www.npmjs.com/package/jebat-security" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">npm</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
