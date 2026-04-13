"use client";

import Link from "next/link";
import { useState } from "react";

const AGENT_STATUS = [
  { name: "Panglima", role: "Orchestration", status: "online", model: "claude-sonnet-4" },
  { name: "Tukang", role: "Development", status: "online", model: "qwen2.5-coder:7b" },
  { name: "Hulubalang", role: "Security Audit", status: "online", model: "hermes-sec-v2" },
  { name: "Pengawal", role: "CyberSec Defense", status: "online", model: "hermes-sec-v2" },
  { name: "Pawang", role: "Research", status: "online", model: "claude-sonnet-4" },
  { name: "Syahbandar", role: "Operations", status: "online", model: "qwen2.5-coder:7b" },
  { name: "Bendahara", role: "Database", status: "online", model: "qwen2.5-coder:7b" },
  { name: "Hikmat", role: "Memory", status: "online", model: "claude-sonnet-4" },
  { name: "Penganalisis", role: "Analytics", status: "online", model: "claude-sonnet-4" },
  { name: "Penyemak", role: "QA", status: "online", model: "claude-sonnet-4" },
];

const USAGE_ANALYTICS = [
  { label: "Total Conversations", value: "1,247", change: "+12%", icon: "💬" },
  { label: "Avg Response Time", value: "2.1s", change: "-8%", icon: "⏱️" },
  { label: "Tokens Processed", value: "4.2M", change: "+24%", icon: "🔢" },
  { label: "Cache Hit Rate", value: "65%", change: "+5%", icon: "💾" },
  { label: "Active Sessions", value: "23", change: "+3", icon: "👥" },
  { label: "Uptime", value: "99.9%", change: "0%", icon: "📊" },
];

const PERFORMANCE_METRICS = [
  { label: "LLM Response Time", value: "1.8s", target: "<3s", status: "good" },
  { label: "Cache Latency", value: "0.2s", target: "<0.5s", status: "good" },
  { label: "Request Throughput", value: "47 req/s", target: "50 req/s", status: "warning" },
  { label: "Error Rate", value: "0.01%", target: "<0.1%", status: "good" },
  { label: "Memory Usage", value: "68%", target: "<80%", status: "good" },
  { label: "CPU Usage", value: "42%", target: "<70%", status: "good" },
];

export default function PortalPage() {
  const [activeTab, setActiveTab] = useState<"agents" | "usage" | "performance">("agents");

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 shadow-lg shadow-emerald-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight">Enterprise Portal</span>
              <span className="text-[10px] font-medium text-emerald-400/80 border border-emerald-400/20 rounded-full px-2 py-0.5">Live</span>
            </div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/v2" className="hidden sm:inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition">
              Home
            </Link>
            <Link href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
              Try Chat
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 px-5 py-2 text-sm font-semibold text-black hover:from-emerald-300 hover:to-teal-400 transition shadow-lg shadow-emerald-500/20">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-emerald-400/5 rounded-full blur-3xl"/>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-6">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            Real-Time Monitoring & Analytics
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block">Enterprise</span>
            <span className="block bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 bg-clip-text text-transparent">
              Customer Portal
            </span>
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed mb-8">
            Monitor all 34 AI agents, track usage analytics, measure performance metrics, and manage your AI team from a single dashboard.
          </p>

          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-12">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-emerald-500/20 hover:from-emerald-300 hover:to-teal-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Deploy Portal
            </a>
            <Link href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Chat Demo
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: "10", label: "Core Agents", icon: "🤖" },
              { value: "24", label: "Specialists", icon: "⚡" },
              { value: "Live", label: "Analytics", icon: "📊" },
              { value: "99.9%", label: "Uptime", icon: "⏱️" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">{stat.value}</div>
                <div className="text-xs text-neutral-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tab Navigation */}
      <section className="border-t border-white/5">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-1 bg-white/5 rounded-xl p-1 max-w-lg mx-auto">
            {([
              { id: "agents", label: "Agent Status", icon: "🤖" },
              { id: "usage", label: "Usage Analytics", icon: "📊" },
              { id: "performance", label: "Performance", icon: "⚡" },
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
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.icon}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Tab Content */}
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-20">
        {/* Agents Tab */}
        {activeTab === "agents" && (
          <div className="grid gap-3 md:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 max-w-6xl mx-auto">
            {AGENT_STATUS.map((a, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
                    {a.name.substring(0, 2).toUpperCase()}
                  </div>
                  <span className="inline-flex items-center gap-1.5">
                    <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
                    <span className="text-[10px] text-emerald-400">Online</span>
                  </span>
                </div>
                <h3 className="font-bold text-sm mb-0.5">{a.name}</h3>
                <p className="text-[10px] text-neutral-500 mb-2">{a.role}</p>
                <div className="text-[9px] text-neutral-600 font-mono bg-white/5 rounded px-2 py-1 text-center">{a.model}</div>
              </div>
            ))}
          </div>
        )}

        {/* Usage Tab */}
        {activeTab === "usage" && (
          <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
            {USAGE_ANALYTICS.map((m, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6">
                <div className="flex items-start justify-between mb-4">
                  <span className="text-3xl">{m.icon}</span>
                  <span className={`text-xs font-medium ${m.change.startsWith("+") ? "text-emerald-400" : m.change === "0%" ? "text-neutral-500" : "text-red-400"}`}>{m.change}</span>
                </div>
                <div className="text-2xl font-bold mb-1">{m.value}</div>
                <div className="text-xs text-neutral-500">{m.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === "performance" && (
          <div className="space-y-4 max-w-4xl mx-auto">
            {PERFORMANCE_METRICS.map((m, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-sm">{m.label}</h3>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-neutral-500">Target: {m.target}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${m.status === "good" ? "bg-emerald-400/10 text-emerald-400 border border-emerald-400/20" : "bg-yellow-400/10 text-yellow-400 border border-yellow-400/20"}`}>
                      {m.status === "good" ? "✓ Good" : "⚠ Warning"}
                    </span>
                  </div>
                </div>
                <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                  <div className={`h-full rounded-full ${m.status === "good" ? "bg-gradient-to-r from-emerald-400 to-teal-500" : "bg-gradient-to-r from-yellow-400 to-orange-500"}`} style={{ width: "70%" }}/>
                </div>
                <div className="text-lg font-bold mt-2">{m.value}</div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
            </div>
            <span className="text-sm text-neutral-500">© 2026 NusaByte · Enterprise Portal</span>
          </div>
          <div className="flex items-center gap-4 text-sm text-neutral-500">
            <Link href="/v2" className="hover:text-white transition">Home</Link>
            <Link href="/chat" className="hover:text-white transition">Chat</Link>
            <Link href="/security" className="hover:text-white transition">Security</Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
