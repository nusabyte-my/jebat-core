"use client";

import Link from "next/link";

const features = [
  {
    icon: "🧠",
    title: "Eternal Memory",
    description: "5-layer cognitive architecture (M0–M4) with heat-based importance scoring. JEBAT remembers what matters across every session.",
    details: ["Sensory → Episodic → Semantic → Conceptual → Procedural", "Automatic consolidation and intelligent forgetting", "Cross-linked semantic recall"],
  },
  {
    icon: "⚔️",
    title: "Multi-Agent Orchestration",
    description: "17 specialized agents — from Tukang (builder) to Hulubalang (security) — coordinated by Panglima, the capture-first operator.",
    details: ["Parallel specialist execution", "Council-style decision workflows", "Git worktree isolation for concurrent tasks"],
  },
  {
    icon: "🔥",
    title: "Ultra-Think Reasoning",
    description: "6 thinking modes optimized for every task: Fast, Deliberate, Deep, Strategic, Creative, and Critical.",
    details: ["Token-optimized context compression", "Progressive disclosure of reasoning chains", "Confidence scoring per response"],
  },
  {
    icon: "🛡️",
    title: "Pengawal — CyberSec Assistant",
    description: "Three-tier security: Perisai (defensive), Pengawal (monitoring), Serangan (authorized offensive).",
    details: ["Vulnerability scanning & threat modeling", "OWASP/CIS compliance auditing", "Automated pentest reporting"],
  },
  {
    icon: "📡",
    title: "Multi-Channel Gateway",
    description: "WhatsApp, Telegram, Discord, Slack, and REST API — meet users where they are, all through one gateway on port 18789.",
    details: ["OpenClaw-compatible protocol", "Session management & cron automation", "DM pairing for security"],
  },
  {
    icon: "🔌",
    title: "Dev Tool Integration",
    description: "VS Code, Cursor, Zed, Trae, Antigravity — JEBAT context injects directly into your IDE workflow.",
    details: ["One-click `npx @nusabyte/jebat install`", "Per-IDE optimized context files", "Command palette integration"],
  },
];

const skills = [
  "Panglima", "Hikmat", "Tukang", "Hulubalang", "Pawang", "Syahbandar",
  "Bendahara", "Penyemak", "Senibina Antara Muka", "Penyebar Reka Bentuk",
  "Pengkarya Kandungan", "Jurutulis Jualan", "Penjejak Carian", "Penggerak Pasaran",
  "Penganalisis", "Strategi Jenama", "Strategi Produk", "Khidmat Pelanggan",
  "Penulis Cadangan", "Penggerak Jualan", "Pengawal", "Perisai", "Serangan",
];

const roadmap = [
  { phase: "Phase 1", title: "Platform Foundation", status: "complete", items: ["Core identity & memory", "Hermes execution layer", "Skill architecture"] },
  { phase: "Phase 2", title: "Gateway & Dashboard", status: "complete", items: ["Onboarding wizard", "Provider configuration", "Live status dashboard"] },
  { phase: "Phase 3", title: "CLI & Dev Tools", status: "complete", items: ["NPX CLI rebrand", "AI Assistant CLI", "IDE adapter expansion"] },
  { phase: "Phase 4", title: "Skill Expansion", status: "in-progress", items: ["40+ skills from skills.sh", "Ralphex execution engine", "CCPM project manager"] },
  { phase: "Phase 5", title: "CyberSec Suite", status: "in-progress", items: ["Pengawal assistant", "Perisai defensive layer", "Serangan offensive layer"] },
  { phase: "Phase 6", title: "Production Ready", status: "planned", items: ["Docker Compose v2", "Authentication", "CI/CD pipeline"] },
];

function StatusDot({ status }: { status: string }) {
  const color = status === "complete" ? "bg-emerald-400" : status === "in-progress" ? "bg-cyan-400" : "bg-neutral-600";
  return <span className={`inline-flex h-2.5 w-2.5 rounded-full ${color} animate-pulse-glow`} />;
}

export default function Home() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">⚔️</span>
            <span className="text-lg font-semibold tracking-tight">JEBAT</span>
          </div>
          <div className="hidden items-center gap-6 text-sm text-neutral-400 md:flex">
            <a href="#features" className="transition hover:text-white">Features</a>
            <a href="#skills" className="transition hover:text-white">Skills</a>
            <a href="#roadmap" className="transition hover:text-white">Roadmap</a>
            <a href="#architecture" className="transition hover:text-white">Architecture</a>
            <Link href="/demo" className="rounded-full border border-cyan-400/30 px-4 py-2 text-cyan-300 transition hover:bg-cyan-400/10">
              Try Demo
            </Link>
            <Link href="/setup" className="rounded-full bg-cyan-400 px-4 py-2 text-black font-medium transition hover:bg-cyan-300">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-7xl px-6 pt-20 pb-16 md:pt-32 md:pb-24">
        <div className="flex flex-col items-center gap-8 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300">
            <span className="inline-flex h-2 w-2 rounded-full bg-cyan-400 animate-pulse-glow" />
            JEBATCore v2.0 — Now with Pengawal CyberSec
          </div>
          <h1 className="max-w-4xl text-5xl font-bold tracking-tight md:text-7xl">
            The LLM Ecosystem That{" "}
            <span className="gradient-text">Remembers Everything</span>
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-neutral-400">
            Eternal memory. Multi-agent orchestration. 6 thinking modes. CyberSec assistant.
            Self-hosted, privacy-first. Built by NusaByte for developers who need an operator, not a yes-man.
          </p>
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <Link href="/setup" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Setup JEBAT →
            </Link>
            <Link href="/demo" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              Live Demo
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              GitHub
            </a>
          </div>

          {/* Quick stats */}
          <div className="mt-8 grid grid-cols-2 gap-6 md:grid-cols-4">
            {[
              ["17+", "Specialist Agents"],
              ["72+", "Skills Installed"],
              ["6", "Thinking Modes"],
              ["5", "Memory Layers"],
            ].map(([num, label]) => (
              <div key={label} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4">
                <div className="text-2xl font-bold gradient-text">{num}</div>
                <div className="text-sm text-neutral-500">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-7xl px-6 py-16">
        <h2 className="mb-2 text-center text-3xl font-bold md:text-4xl">Everything You Need</h2>
        <p className="mx-auto mb-12 max-w-xl text-center text-neutral-400">A complete development ecosystem — from memory to security to deployment.</p>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <article key={f.title} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="mb-3 text-3xl">{f.icon}</div>
              <h3 className="mb-2 text-xl font-semibold text-white">{f.title}</h3>
              <p className="mb-4 text-sm leading-7 text-neutral-400">{f.description}</p>
              <ul className="space-y-2">
                {f.details.map((d) => (
                  <li key={d} className="flex items-start gap-2 text-sm text-neutral-500">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400/60" />
                    {d}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="mx-auto max-w-7xl px-6 py-16">
        <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-8 md:p-12">
          <h2 className="mb-8 text-center text-3xl font-bold">Architecture</h2>
          <div className="grid gap-8 lg:grid-cols-2">
            {/* Visual diagram */}
            <div className="space-y-3 font-mono text-sm">
              {[
                { label: "Channels", sub: "WhatsApp · Telegram · Discord · Slack · REST API", indent: 0 },
                { label: "Gateway (port 18789)", sub: "Sessions · Cron · Tool routing · Multi-tenant", indent: 0 },
                { label: "JEBAT Core", sub: "", indent: 0 },
                { label: "├─ Memory (M0-M4)", sub: "Heat scoring · Consolidation · Vector search", indent: 2 },
                { label: "├─ Ultra-Think", sub: "6 reasoning modes · Token optimization", indent: 2 },
                { label: "├─ Ultra-Loop", sub: "5-phase continuous processing", indent: 2 },
                { label: "├─ Agent Orchestrator", sub: "17 specialists · Council workflows", indent: 2 },
                { label: "├─ Pengawal (CyberSec)", sub: "Perisai · Pengawal · Serangan", indent: 2 },
                { label: "└─ Sentinel", sub: "Autonomous security monitoring", indent: 2 },
                { label: "Storage", sub: "PostgreSQL/TimescaleDB · Redis · SQLite (Chroma)", indent: 0 },
              ].map((row, i) => (
                <div key={i} className="flex items-start gap-2" style={{ paddingLeft: row.indent ? `${row.indent}rem` : undefined }}>
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

            {/* Tech stack */}
            <div className="space-y-6">
              <h3 className="text-xl font-semibold text-white">Stack</h3>
              {[
                ["Frontend", "Next.js 16 · React 19 · TypeScript · Tailwind v4 · shadcn/ui"],
                ["Backend", "Python 3.11+ · FastAPI · Uvicorn · Pydantic"],
                ["Database", "PostgreSQL/TimescaleDB · Redis 7 · SQLite + Chroma"],
                ["AI/ML", "Mesin (Ollama VPS) · Terbuka (OpenAI) · Bijak (Anthropic) · Gemilang (Gemini) · Haluan (OpenRouter) · ZAI"],
                ["DevOps", "Docker Compose · Traefik · Prometheus · Grafana · Nginx"],
                ["CLI", "Node.js (jebatcore) · Python (jebat_dev) · Rich UI"],
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

      {/* Skills */}
      <section id="skills" className="mx-auto max-w-7xl px-6 py-16">
        <h2 className="mb-2 text-center text-3xl font-bold">72+ Skills Installed</h2>
        <p className="mx-auto mb-10 max-w-xl text-center text-neutral-400">From Panglima (orchestration) to Serangan (offensive security) — every specialist, one platform.</p>
        <div className="flex flex-wrap justify-center gap-3">
          {skills.map((s) => (
            <span key={s} className="rounded-full border border-white/10 bg-white/[0.02] px-4 py-2 text-sm text-neutral-300 transition hover:border-cyan-400/30 hover:text-cyan-300 cursor-default">
              {s}
            </span>
          ))}
        </div>
      </section>

      {/* Roadmap */}
      <section id="roadmap" className="mx-auto max-w-7xl px-6 py-16">
        <h2 className="mb-10 text-center text-3xl font-bold">Roadmap</h2>
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {roadmap.map((r) => (
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

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="rounded-3xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/5 to-transparent p-10 text-center md:p-16">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">Ready to Build with JEBAT?</h2>
          <p className="mx-auto mb-8 max-w-lg text-neutral-400">
            One command to start. One dashboard to configure. One platform for everything.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <code className="rounded-xl border border-white/10 bg-black/40 px-6 py-3 text-sm font-mono text-cyan-300">
              npx @nusabyte/jebat setup
            </code>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚔️</span>
            <div>
              <div className="text-sm font-semibold">JEBAT by NusaByte</div>
              <div className="text-xs text-neutral-500">Because warriors remember everything that matters.</div>
            </div>
          </div>
          <div className="flex gap-6 text-sm text-neutral-500">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="transition hover:text-white">GitHub</a>
            <a href="https://jebat.online" className="transition hover:text-white">jebat.online</a>
            <Link href="/demo" className="transition hover:text-white">Demo</Link>
            <Link href="/setup" className="transition hover:text-white">Setup</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
