"use client";

import Link from "next/link";
import { useState } from "react";

const ORCHESTRATION_MODES = [
  { icon: "⚖️", title: "Multi-Agent Debate", desc: "Advocate vs Critic → Rebuttals → Confidence → Moderator conclusion. Research-backed MAD paradigm.", rounds: "4 Rounds", time: "~2-5 min", gradient: "from-cyan-400 to-blue-500" },
  { icon: "🤝", title: "Consensus Building", desc: "Share perspectives → Find agreement → Final synthesized conclusion. Collaborative approach.", rounds: "3 Rounds", time: "~1.5-3 min", gradient: "from-emerald-400 to-teal-500" },
  { icon: "🔗", title: "Sequential Chain", desc: "Model 1 starts → Model 2 builds → Model 1 refines. Linear knowledge building.", rounds: "3 Steps", time: "~1-2 min", gradient: "from-blue-400 to-indigo-500" },
  { icon: "⚡", title: "Parallel Analysis", desc: "Both analyze independently → Comparison table with synthesis. Unbiased perspectives.", rounds: "2 Phases", time: "~1-2 min", gradient: "from-yellow-400 to-orange-500" },
  { icon: "🏛️", title: "Hierarchical Review", desc: "Senior delegates → Junior completes → Senior reviews. Quality control pattern.", rounds: "3 Steps", time: "~1.5-3 min", gradient: "from-purple-400 to-pink-500" },
];

const RESEARCH_SOURCES = [
  { name: "AutoGen", org: "Microsoft", desc: "Multi-agent conversation framework" },
  { name: "ChatDev 2.0", org: "OpenBMB", desc: "Virtual software company simulation" },
  { name: "MAD Paradigm", org: "Research", desc: "Multi-Agent Debate for consensus" },
  { name: "CrewAI", org: "Open Source", desc: "Role-playing agent collaboration" },
];

export default function GelanggangPage() {
  const [activeTab, setActiveTab] = useState<"modes" | "research">("modes");

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-600 shadow-lg shadow-amber-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight">Gelanggang Arena</span>
              <span className="text-[10px] font-medium text-amber-400/80 border border-amber-400/20 rounded-full px-2 py-0.5">Live</span>
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
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-5 py-2 text-sm font-semibold text-black hover:from-amber-300 hover:to-orange-400 transition shadow-lg shadow-amber-500/20">
              GitHub
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-amber-400/5 rounded-full blur-3xl"/>
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]"/>
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 md:pt-24 md:pb-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-400/5 px-4 py-1.5 text-sm text-amber-300 mb-6">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
            LLM-to-LLM Multi-Agent Arena
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
            <span className="block">Watch AI Models</span>
            <span className="block bg-gradient-to-r from-amber-400 via-orange-400 to-red-400 bg-clip-text text-transparent">
              Debate & Collaborate
            </span>
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed mb-8">
            Gelanggang — the LLM-to-LLM arena where models debate, collaborate, and compete in real-time. Research-backed orchestration patterns from AutoGen, ChatDev 2.0, and MAD Paradigm.
          </p>

          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-12">
            <Link href="/chat" className="rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-amber-500/20 hover:from-amber-300 hover:to-orange-400 transition">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              Enter Arena
            </Link>
            <Link href="/v2" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Learn More
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { value: "5", label: "Orchestration Modes", icon: "🎭" },
              { value: "8", label: "Local Models", icon: "🤖" },
              { value: "Live", label: "Debates", icon: "⚡" },
              { value: "Real", label: "Time", icon: "⏱️" },
            ].map((stat, i) => (
              <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">{stat.value}</div>
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
              { id: "modes", label: "Orchestration Modes", icon: "🎭" },
              { id: "research", label: "Research Sources", icon: "📚" },
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
        {/* Modes Tab */}
        {activeTab === "modes" && (
          <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
            {ORCHESTRATION_MODES.map((m, i) => (
              <div key={i} className="group rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 hover:border-amber-400/20 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${m.gradient} flex items-center justify-center text-xl shadow-lg`}>
                    {m.icon}
                  </div>
                  <div className="text-right">
                    <div className="text-[10px] text-neutral-500">{m.rounds}</div>
                    <div className="text-[10px] text-neutral-600">{m.time}</div>
                  </div>
                </div>
                <h3 className="text-lg font-bold mb-2">{m.title}</h3>
                <p className="text-sm text-neutral-500 leading-relaxed">{m.desc}</p>
                <Link href="/chat" className="mt-4 inline-flex items-center gap-2 text-amber-400 hover:text-amber-300 transition text-sm font-medium">
                  Try in Chat
                  <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
                </Link>
              </div>
            ))}
          </div>
        )}

        {/* Research Tab */}
        {activeTab === "research" && (
          <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2 max-w-4xl mx-auto">
            {RESEARCH_SOURCES.map((r, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-orange-600 flex items-center justify-center text-lg font-bold text-white shadow-lg">
                    {r.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg mb-1">{r.name}</h3>
                    <p className="text-xs text-amber-400 mb-2">{r.org}</p>
                    <p className="text-sm text-neutral-500">{r.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400 to-orange-600">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <span className="text-sm text-neutral-500">© 2026 NusaByte · Gelanggang Arena</span>
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
