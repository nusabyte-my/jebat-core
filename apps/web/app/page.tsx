"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

// ─── Data ─────────────────────────────────────────────────────────────────────

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Security", href: "#security" },
  { label: "Gelanggang", href: "/gelanggang" },
  { label: "Architecture", href: "#architecture" },
  { label: "Skills", href: "#skills" },
];

const trustStats = [
  { value: "23+", label: "Specialist Agents", icon: "⚔️" },
  { value: "40+", label: "Optimized Skills", icon: "🗡️" },
  { value: "5", label: "LLM Providers", icon: "🌐" },
  { value: "100%", label: "Self-Hosted", icon: "🔒" },
];

const valuePillars = [
  {
    icon: "🧠",
    title: "Memory That Never Forgets",
    description: "5-layer cognitive architecture (M0–M4) with heat-based importance scoring. JEBAT remembers context, preferences, and decisions across every session — unlike stateless AI assistants.",
    features: ["Cross-session continuity", "Intelligent forgetting", "Semantic recall", "Vector search"],
  },
  {
    icon: "⚔️",
    title: "Agents That Collaborate",
    description: "23 specialist agents orchestrated by Panglima. Watch them debate, propose solutions, and reach consensus — all across different LLM providers in real-time.",
    features: ["Cross-provider LLM communication", "4 collaboration patterns", "Dynamic agent loading", "Shimmer notifications"],
  },
  {
    icon: "🛡️",
    title: "Security From Day One",
    description: "Autonomous security scanner on every startup. Three-tier cybersec assistant (Perisai, Pengawal, Serangan) with auto-fix for 6 vulnerability types.",
    features: ["IBM agentic-ai-cyberres integration", "18 MCP security tools", "GDPR/SOC2/ISO27001 compliance", "Audit logging"],
  },
];

const securityFeatures = [
  {
    icon: "🔍",
    title: "Autonomous Scanning",
    description: "Every JEBAT session begins with a full codebase security audit — secrets, CVEs, injection patterns, infrastructure misconfigs.",
    severity: "Always On",
  },
  {
    icon: "🔧",
    title: "Auto-Remediation",
    description: "Automatically fixes 6 vulnerability types (MD5→SHA256, eval removal, safe YAML, pickle, os.system, XSS) with backups before every change.",
    severity: "1-Click Fix",
  },
  {
    icon: "📋",
    title: "Compliance Reports",
    description: "Generate compliance reports for GDPR, SOC2, and ISO27001. Full audit trail with structured event logging and anomaly detection.",
    severity: "Enterprise Ready",
  },
  {
    icon: "🔒",
    title: "Zero-Trust Design",
    description: "7 built-in RBAC roles with 20+ granular permissions. Every API call, memory access, and config change is logged and auditable.",
    severity: "Role-Based",
  },
];

const collaborationPatterns = [
  {
    icon: "➡️",
    title: "Sequential",
    description: "Agent A → Agent B → Agent C, each building on previous results.",
    example: "Tukang writes code → Hulubalang audits → Penyemak validates",
  },
  {
    icon: "⚡",
    title: "Parallel",
    description: "All agents work simultaneously, results combined at the end.",
    example: "3 agents analyze the same codebase independently",
  },
  {
    icon: "🗳️",
    title: "Consensus",
    description: "All agents propose solutions, then vote. Majority wins.",
    example: "3 agents propose architectures → vote → 2 agree on microservices",
  },
  {
    icon: "⚔️",
    title: "Adversarial",
    description: "Two agents debate opposing positions. Third agent judges.",
    example: "Monolith vs Microservices debate → Panglima decides",
  },
];

const skillCategories = [
  { name: "Core", skills: ["Panglima", "Hikmat", "Agent Dispatch"], color: "cyan" },
  { name: "Engineering", skills: ["Tukang", "Tukang Web", "Pembina Aplikasi", "Bendahara"], color: "blue" },
  { name: "Security", skills: ["Hulubalang", "Pengawal", "Perisai", "Serangan"], color: "red" },
  { name: "Intelligence", skills: ["Pawang", "Penganalisis", "Penyemak"], color: "green" },
  { name: "Operations", skills: ["Syahbandar", "Khidmat Pelanggan"], color: "amber" },
  { name: "Growth", skills: ["Penjejak Carian", "Penggerak Pasaran", "Jurutulis Jualan", "Strategi Jenama"], color: "purple" },
  { name: "Product", skills: ["Strategi Produk", "Senibina Antara Muka", "Penyebar Reka Bentuk"], color: "pink" },
  { name: "Content", skills: ["Pengkarya Kandungan", "Penulis Cadangan", "Penggerak Jualan"], color: "orange" },
];

const cyberQuotes = [
  "\"The only truly secure system is one that is powered off.\" — Gene Spafford",
  "\"In cybersecurity, the weakest link is always the human element.\" — Kevin Mitnick",
  "\"The attacker only needs to be right once. The defender must be right every time.\" — Bruce Schneier",
  "\"Security is not a product, but a process.\" — Bruce Schneier",
  "\"Trust, but verify. Then verify again.\" — JEBAT Security Principle",
  "\"Zero trust doesn't mean zero faith. It means verify everything.\" — Anonymous",
  "\"Social engineering will always beat technical security.\" — Kevin Mitnick",
  "\"The cost of prevention is always less than the cost of cure.\" — JEBAT Principle",
  "\"Never trust input. Always validate. Always sanitize.\" — JEBAT Principle",
  "\"A pentest report without remediation is just a horror story.\" — Anonymous",
];

// ─── Components ───────────────────────────────────────────────────────────────

function StatusDot({ status }: { status: string }) {
  const color = status === "complete" ? "bg-emerald-400" : status === "in-progress" ? "bg-cyan-400" : "bg-neutral-600";
  return <span className={`inline-flex h-2.5 w-2.5 rounded-full ${color}`} />;
}

function SectionHeading({ badge, title, subtitle }: { badge: string; title: string; subtitle: string }) {
  return (
    <div className="text-center mb-12">
      <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">
        {badge}
      </span>
      <h2 className="text-3xl font-bold md:text-4xl mb-4">{title}</h2>
      <p className="max-w-2xl mx-auto text-neutral-400">{subtitle}</p>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Home() {
  const [quote, setQuote] = useState(cyberQuotes[0]);
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    setQuote(cyberQuotes[Math.floor(Math.random() * cyberQuotes.length)]);
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100 overflow-x-hidden">
      {/* ─── Nav ─────────────────────────────────────────────────────── */}
      <nav className={`sticky top-0 z-50 transition-all duration-300 ${scrollY > 50 ? "bg-[#050505]/95 backdrop-blur-xl border-b border-white/5" : "bg-transparent"}`}>
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚔️</span>
            <span className="text-lg font-semibold tracking-tight">JEBAT</span>
            <span className="hidden md:inline-block text-xs text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">v2.0</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm text-neutral-400">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href} className="transition hover:text-white">{link.label}</a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hidden sm:inline-block text-sm text-neutral-400 transition hover:text-white">
              GitHub
            </a>
            <Link href="/gelanggang" className="rounded-full border border-cyan-400/30 px-4 py-2 text-sm text-cyan-300 transition hover:bg-cyan-400/10">
              Gelanggang
            </Link>
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-4 py-2 text-sm font-medium text-black transition hover:bg-cyan-300">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* ─── Hero ────────────────────────────────────────────────────── */}
      <section className="relative">
        {/* Background effects */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-cyan-400/5 rounded-full blur-3xl" />
          <div className="absolute top-20 right-10 w-[400px] h-[400px] bg-red-400/3 rounded-full blur-3xl" />
          <div className="absolute top-40 left-10 w-[300px] h-[300px] bg-green-400/3 rounded-full blur-3xl" />
          {/* Grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]" />
        </div>

        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 md:pt-32 md:pb-24">
          <div className="text-center space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Self-Hosted · Enterprise-Ready · 100% Private
            </div>

            {/* Headline */}
            <h1 className="max-w-5xl mx-auto text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl leading-[1.1]">
              The AI Platform That{" "}
              <span className="gradient-text">Remembers</span>,{" "}
              <span className="gradient-text">Collaborates</span>,{" "}
              <span className="gradient-text">Protects</span>
            </h1>

            {/* Subheadline */}
            <p className="max-w-3xl mx-auto text-lg md:text-xl leading-8 text-neutral-400">
              JEBAT combines eternal memory, multi-agent orchestration across 5 LLM providers, and autonomous cybersecurity scanning into one self-hosted platform. Built by <a href="https://nusabyte.my" className="text-cyan-300 hover:text-cyan-200 transition">NusaByte</a> for teams who need an AI operator — not just a chatbot.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap justify-center gap-4 pt-4">
              <Link href="/onboarding" className="group rounded-full bg-cyan-400 px-8 py-4 text-base font-semibold text-black transition hover:bg-cyan-300 flex items-center gap-2">
                Start Building
                <svg className="w-4 h-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
              </Link>
              <Link href="/gelanggang" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white transition hover:bg-white/10 flex items-center gap-2">
                🏛️ Watch Gelanggang
              </Link>
              <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white transition hover:bg-white/10">
                ⭐ Star on GitHub
              </a>
            </div>

            {/* Trust Stats */}
            <div className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
              {trustStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                  <div className="text-xl mb-1">{stat.icon}</div>
                  <div className="text-2xl font-bold gradient-text">{stat.value}</div>
                  <div className="text-xs text-neutral-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Value Pillars ───────────────────────────────────────────── */}
      <section id="features" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHeading
          badge="Core Capabilities"
          title="Why Teams Choose JEBAT"
          subtitle="Three pillars that make JEBAT fundamentally different from stateless AI assistants."
        />
        <div className="grid gap-6 md:grid-cols-3">
          {valuePillars.map((pillar) => (
            <div key={pillar.title} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="text-3xl mb-4">{pillar.icon}</div>
              <h3 className="text-xl font-semibold text-white mb-3">{pillar.title}</h3>
              <p className="text-sm leading-7 text-neutral-400 mb-4">{pillar.description}</p>
              <div className="space-y-2">
                {pillar.features.map((f) => (
                  <div key={f} className="flex items-center gap-2 text-sm text-neutral-500">
                    <svg className="w-4 h-4 text-cyan-400/60 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    {f}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Gelanggang Panglima Demo ────────────────────────────────── */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-cyan-400/10 bg-gradient-to-br from-cyan-400/5 via-transparent to-transparent p-8 md:p-12">
          <div className="grid gap-8 lg:grid-cols-2 items-center">
            <div className="space-y-6">
              <span className="text-4xl">🏛️</span>
              <h2 className="text-3xl font-bold md:text-4xl">
                <span className="text-amber-300">Gelanggang Panglima</span>
              </h2>
              <p className="text-neutral-400 leading-7">
                Watch AI agents from OpenAI, Anthropic, Gemini, Ollama, and ZAI communicate, debate, and collaborate in real-time. Choose from 4 collaboration patterns — Sequential, Parallel, Consensus, or Adversarial.
              </p>
              <div className="flex flex-wrap gap-3">
                {["OpenAI", "Anthropic", "Gemini", "Ollama", "ZAI"].map((p) => (
                  <span key={p} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-300">{p}</span>
                ))}
              </div>
              <Link href="/gelanggang" className="inline-flex items-center gap-2 rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300">
                Try Live Demo →
              </Link>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/40 p-6 font-mono text-sm space-y-3">
              <div className="flex items-center gap-2 text-neutral-500 text-xs mb-4">
                <div className="w-3 h-3 rounded-full bg-red-400/60" />
                <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                <div className="w-3 h-3 rounded-full bg-green-400/60" />
                <span className="ml-2">Gelanggang — Live Session</span>
              </div>
              {[
                { agent: "Tukang (OpenAI)", text: "I've built the auth API with JWT and rate limiting.", color: "#3B82F6" },
                { agent: "Hulubalang (Anthropic)", text: "🔴 CRITICAL — SQL injection vulnerability found.", color: "#EF4444" },
                { agent: "Penyemak (ZAI)", text: "✅ 75% production-ready. 5 test gaps identified.", color: "#8B5CF6" },
                { agent: "Panglima (Anthropic)", text: "⚔️ VERDICT: Proceed with 3 critical fixes.", color: "#00E5FF" },
              ].map((msg, i) => (
                <div key={i} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: msg.color }} />
                    <span className="text-xs" style={{ color: msg.color }}>{msg.agent}</span>
                  </div>
                  <div className="text-xs text-neutral-300">{msg.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Security Section ────────────────────────────────────────── */}
      <section id="security" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHeading
          badge="Enterprise Security"
          title="Security From Day One"
          subtitle="Autonomous scanning, auto-remediation, and compliance reporting — built into every JEBAT session."
        />
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {securityFeatures.map((feature) => (
            <div key={feature.title} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{feature.icon}</span>
                <span className="text-xs rounded-full border border-red-400/20 bg-red-400/5 px-2 py-0.5 text-red-300">{feature.severity}</span>
              </div>
              <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-neutral-400 leading-6">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Collaboration Patterns */}
        <div className="mt-16">
          <h3 className="text-2xl font-bold text-center mb-8">Cross-Provider Collaboration Patterns</h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {collaborationPatterns.map((p) => (
              <div key={p.title} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="text-2xl mb-2">{p.icon}</div>
                <h4 className="font-semibold text-white mb-1">{p.title}</h4>
                <p className="text-xs text-neutral-400 mb-3">{p.description}</p>
                <div className="rounded bg-black/30 px-3 py-2 text-xs text-neutral-300">{p.example}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Architecture ────────────────────────────────────────────── */}
      <section id="architecture" className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-8 md:p-12">
          <h2 className="text-3xl font-bold text-center mb-10">Platform Architecture</h2>
          <div className="grid gap-8 lg:grid-cols-2">
            <div className="space-y-3 font-mono text-sm">
              {[
                { label: "Channels", sub: "WhatsApp · Telegram · Discord · Slack · REST API", indent: 0 },
                { label: "jebat-gateway (:18789)", sub: "Sessions · Cron · Tool routing", indent: 0 },
                { label: "JEBAT Core", sub: "", indent: 0 },
                { label: "├─ Memory (M0-M4)", sub: "Heat scoring · Vector search", indent: 2 },
                { label: "├─ Ultra-Think", sub: "6 reasoning modes", indent: 2 },
                { label: "├─ Ultra-Loop", sub: "5-phase continuous processing", indent: 2 },
                { label: "├─ Agent Orchestrator", sub: "23 specialists", indent: 2 },
                { label: "├─ Serangan Autonomous", sub: "IBM agentic-ai-cyberres · 18 MCP tools", indent: 2 },
                { label: "├─ Pengawal (CyberSec)", sub: "Perisai · Pengawal · Serangan", indent: 2 },
                { label: "├─ Prompt Enhancer", sub: "6-stage optimization pipeline", indent: 2 },
                { label: "└─ Gelanggang Panglima", sub: "LLM-to-LLM cross-provider arena", indent: 2 },
                { label: "Storage", sub: "PostgreSQL/TimescaleDB · Redis · SQLite + Chroma", indent: 0 },
              ].map((row, i) => (
                <div key={i} style={{ paddingLeft: row.indent ? `${row.indent}rem` : undefined }}>
                  {row.sub ? (
                    <div>
                      <span className="text-cyan-300">{row.label}</span>
                      <span className="ml-2 text-neutral-500">{row.sub}</span>
                    </div>
                  ) : (
                    <span className="font-semibold text-white">{row.label}</span>
                  )}
                </div>
              ))}
            </div>
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-white">Tech Stack</h3>
              {[
                ["Frontend", "Next.js 16 · React 19 · TypeScript · Tailwind v4"],
                ["Backend", "Python 3.11+ · FastAPI · Uvicorn"],
                ["Database", "PostgreSQL/TimescaleDB · Redis 7 · Chroma"],
                ["AI/ML", "OpenAI · Anthropic · Gemini · Ollama · ZAI"],
                ["DevOps", "Docker Compose · Nginx · Let's Encrypt"],
                ["Mobile", "Flutter (iOS + Android scaffold)"],
              ].map(([name, tools]) => (
                <div key={name}>
                  <div className="text-sm font-medium text-neutral-300">{name}</div>
                  <div className="text-sm text-neutral-500">{tools}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── Skills Ecosystem ────────────────────────────────────────── */}
      <section id="skills" className="mx-auto max-w-7xl px-6 py-20">
        <SectionHeading
          badge="Skills Ecosystem"
          title="23 Optimized & Enhanced Skills"
          subtitle="Every skill optimized for token efficiency, enhanced with real-world patterns from skills.sh, and adapted for the JEBAT ecosystem."
        />
        <div className="space-y-6">
          {skillCategories.map((cat) => (
            <div key={cat.name}>
              <h3 className="text-sm font-semibold text-neutral-300 mb-3">{cat.name}</h3>
              <div className="flex flex-wrap gap-2">
                {cat.skills.map((skill) => (
                  <span key={skill} className="rounded-full border border-white/10 bg-white/[0.02] px-4 py-2 text-sm text-neutral-300 transition hover:border-cyan-400/30 hover:text-cyan-300 cursor-default">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Roadmap ─────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <SectionHeading
          badge="Roadmap"
          title="100% Features Shipped"
          subtitle="All planned quarters complete. From infrastructure to distributed systems — JEBAT is production-ready."
        />
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {[
            { phase: "Q2 2026", title: "Infrastructure & Polish", status: "complete", items: ["Monitoring dashboard", "Docker deployment", "CI/CD pipeline", "WhatsApp + Discord stubs"] },
            { phase: "Q3 2026", title: "Web UI, API & Scale", status: "complete", items: ["Next.js 16 web app (9 pages)", "REST API v1 (FastAPI)", "Python + JS SDKs", "Multi-tenancy"] },
            { phase: "Q4 2026", title: "Advanced Features & AI", status: "complete", items: ["Plugin system", "Dynamic agent loading", "Security scanner + auto-fix", "Knowledge Graph (Neo4j)"] },
            { phase: "Q1 2027", title: "Mobile & Voice", status: "complete", items: ["Flutter app (iOS + Android)", "Whisper STT integration", "ElevenLabs TTS", "50 cyber quotes"] },
            { phase: "Q2 2027", title: "Enterprise Features", status: "complete", items: ["Advanced RBAC (7 roles)", "Audit logging (GDPR/SOC2)", "Compliance reports", "Enterprise README"] },
            { phase: "Q3 2027", title: "Distributed System", status: "complete", items: ["Multi-instance sync", "Federated learning", "Event-driven sync", "Heartbeat monitoring"] },
          ].map((r) => (
            <div key={r.phase} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="mb-3 flex items-center gap-2">
                <StatusDot status={r.status} />
                <span className="text-xs uppercase tracking-widest text-neutral-500">{r.phase}</span>
              </div>
              <h3 className="mb-3 text-lg font-semibold text-white">{r.title}</h3>
              <ul className="space-y-2">
                {r.items.map((item) => (
                  <li key={item} className="flex items-start gap-2 text-sm text-neutral-400">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-neutral-600" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ─── CTA ─────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/5 to-transparent p-10 text-center md:p-16">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">Ready to Build with JEBAT?</h2>
          <p className="mx-auto mb-8 max-w-lg text-neutral-400">
            Tell us about yourself, your environment, and what you need. We'll set things up for you.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Start Onboarding →
            </Link>
            <Link href="/gelanggang" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              🏛️ Watch Gelanggang
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Footer ──────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5">
        {/* Main footer */}
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="grid gap-10 md:grid-cols-5">
            {/* Brand column */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">⚔️</span>
                <div>
                  <span className="text-lg font-semibold">JEBAT</span>
                  <span className="ml-2 text-xs text-neutral-500 border border-white/10 rounded-full px-2 py-0.5">v2.0.0</span>
                </div>
              </div>
              <p className="text-sm text-neutral-400 mb-6 max-w-sm leading-relaxed">
                The self-hosted AI platform that remembers, collaborates, and protects. Built by <a href="https://nusabyte.my" className="text-cyan-300 hover:text-cyan-200 transition">NusaByte</a> for teams who need an AI operator — not just a chatbot.
              </p>
              {/* Trust badges */}
              <div className="flex flex-wrap gap-3 mb-6">
                {[
                  { icon: "🔒", label: "Self-Hosted" },
                  { icon: "✅", label: "SOC2 Ready" },
                  { icon: "🛡️", label: "GDPR Compliant" },
                  { icon: "⭐", label: "MIT License" },
                ].map((badge) => (
                  <span key={badge.label} className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-neutral-400">
                    <span>{badge.icon}</span>
                    {badge.label}
                  </span>
                ))}
              </div>
              {/* GitHub star CTA */}
              <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-neutral-300 transition hover:bg-white/10 hover:text-white">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
                <span>Star on GitHub</span>
                <span className="text-xs text-neutral-500">— helps others find JEBAT</span>
              </a>
            </div>
            {/* Platform */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Platform</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <a href="#features" className="block transition hover:text-white">Features</a>
                <a href="#security" className="block transition hover:text-white">Security</a>
                <a href="#architecture" className="block transition hover:text-white">Architecture</a>
                <a href="#skills" className="block transition hover:text-white">Skills</a>
                <Link href="/gelanggang" className="block transition hover:text-white">Gelanggang Demo</Link>
              </div>
            </div>
            {/* Resources */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Resources</h4>
              <div className="space-y-3 text-sm text-neutral-500">
                <Link href="/demo" className="block transition hover:text-white">Chat Demo</Link>
                <Link href="/onboarding" className="block transition hover:text-white">Onboarding</Link>
                <Link href="/setup" className="block transition hover:text-white">Setup Guide</Link>
                <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">Documentation</a>
                <a href="https://github.com/nusabyte-my/jebat-core/issues" target="_blank" rel="noopener noreferrer" className="block transition hover:text-white">Report Issues</a>
              </div>
            </div>
            {/* Company */}
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
        {/* Bottom bar */}
        <div className="border-t border-white/5">
          <div className="mx-auto max-w-7xl px-6 py-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="text-xs text-neutral-600">
                © {new Date().getFullYear()} <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">NusaByte</a>. 
                Owner: <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">humm1ngb1rd</a>. 
                All rights reserved.
              </div>
              <div className="text-xs text-neutral-700 italic max-w-md text-center">
                {quote}
              </div>
              <div className="flex items-center gap-4 text-xs text-neutral-600">
                <a href="https://github.com/nusabyte-my/jebat-core/blob/main/LICENSE" target="_blank" rel="noopener noreferrer" className="transition hover:text-white">MIT License</a>
                <span>·</span>
                <span>Built with ❤️ in Malaysia</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
