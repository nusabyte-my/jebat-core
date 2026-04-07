"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

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
    description: "23 specialized agents — from Tukang (builder) to Hulubalang (security) — coordinated by Panglima, the capture-first operator.",
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
    icon: "🔒",
    title: "Autonomous Security Scanner",
    description: "Adapted from IBM's agentic-ai-cyberres. Runs on every session startup — scans the entire codebase for secrets, CVEs, injection patterns, and infrastructure misconfigs.",
    details: ["Secret & credential detection across all files", "Dependency vulnerability audit (npm + pip)", "18 MCP security tools catalog from awesome-cybersecurity-agentic-ai", "Auto-generated scan reports in security/scan-reports/"],
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
  {
    icon: "🏘️",
    title: "Agent Town",
    description: "Pixel-art RPG world where you walk up to AI workers and assign tasks face-to-face. Built on OpenClaw, integrates with JEBAT's multi-agent system.",
    details: ["Phaser 3 + React HUD", "Real-time task tracking in-game", "Worker autonomy with JEBAT skills"],
  },
];

const integrations = [
  {
    icon: "🏘️",
    title: "Agent Town",
    description: "Pixel-art RPG world where you walk up to AI workers and assign tasks face-to-face. Built on OpenClaw, integrates with JEBAT's multi-agent system.",
    link: "https://github.com/geezerrrr/agent-town",
    action: "Learn Integration",
    actionLink: "/integration/agent-town",
  },
  {
    icon: "🧩",
    title: "OpenClaw Gateway",
    description: "Plug your existing OpenClaw gateway into JEBAT's skill system, memory layers, and agent orchestration seamlessly.",
    link: "#",
    action: "Setup Guide",
    actionLink: "/setup",
  },
  {
    icon: "🤖",
    title: "Custom Agents",
    description: "Bring your own agents. JEBAT's adapter system accepts any AI agent that can communicate via REST API or WebSocket.",
    link: "#",
    action: "Build Your Agent",
    actionLink: "/integration/custom-agent",
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
  { phase: "Q2 2026", title: "Infrastructure & Polish", status: "complete", items: ["Monitoring dashboard", "Docker deployment", "CI/CD pipeline", "WhatsApp + Discord channel stubs"] },
  { phase: "Q3 2026", title: "Web UI, API & Scale", status: "complete", items: ["Next.js 16 web app (9 pages)", "REST API v1 (FastAPI)", "Python + JS SDKs", "Multi-tenancy support"] },
  { phase: "Q4 2026", title: "Advanced Features & AI", status: "in-progress", items: ["Plugin system", "Dynamic agent loading + shimmer", "Autonomous security scanner + auto-fix", "Knowledge graph (planned)"] },
  { phase: "Q1 2027", title: "Mobile & Voice", status: "planned", items: ["iOS + Android app (Flutter)", "Voice commands (STT/TTS)", "ElevenLabs TTS integration", "Whisper speech recognition"] },
  { phase: "Q2 2027", title: "Enterprise Features", status: "planned", items: ["SSO integration (OAuth2/SAML)", "Advanced RBAC", "Audit logging", "GDPR + SOC2 compliance"] },
  { phase: "Q3 2027", title: "Distributed System", status: "planned", items: ["Multi-instance sync", "Distributed memory", "Federated learning", "Edge computing support"] },
];

const cyberQuotes = [
  "\"The only truly secure system is one that is powered off.\" — Gene Spafford",
  "\"In cybersecurity, the weakest link is always the human element.\" — Kevin Mitnick",
  "\"Pentesting is not about breaking in. It's about proving that someone can.\" — Anonymous",
  "\"The best defense is a good offense — test before they do.\" — Anonymous",
  "\"Hackers are breaking into systems faster than you're patching them.\" — Anonymous",
  "\"Security is not a product, but a process.\" — Bruce Schneier",
  "\"There are two types of companies: those that have been hacked, and those that don't know it yet.\" — Anonymous",
  "\"A pentester's job is to find vulnerabilities before the bad guys do.\" — Anonymous",
  "\"Trust, but verify. Then verify again.\" — JEBAT Security Principle",
  "\"The firewall is useless if the user opens the door.\" — Anonymous",
  "\"Your network is only as secure as your weakest password.\" — Anonymous",
  "\"Red team finds the cracks. Blue team patches them. Purple team wins.\" — Anonymous",
  "\"Privacy is not something that I'm merely entitled to, it's a fundamental human right.\" — Edward Snowden",
  "\"The great question of the 21st century is: will the internet set us free, or enslave us?\" — Anonymous",
  "\"Hackers are breaking the rules. It's time defenders start rewriting them.\" — Anonymous",
  "\"The quieter you become, the more you are able to hear.\" — Kali Linux Motto",
  "\"Information wants to be free. Privacy demands it be protected.\" — Anonymous",
  "\"A system is only as good as the people who maintain it.\" — JEBAT Principle",
  "\"Attack surfaces multiply. Defenders must automate or drown.\" — Anonymous",
  "\"The best time to secure your system was yesterday. The second best time is now.\" — Anonymous",
  "\"Every line of code is a liability. Every vulnerability is a lesson.\" — Anonymous",
  "\"You can't secure what you can't see. Visibility is the foundation of security.\" — Anonymous",
  "\"The attacker only needs to be right once. The defender must be right every time.\" — Bruce Schneier",
  "\"Security is a journey, not a destination.\" — Anonymous",
  "\"Patching is cheaper than breach notification.\" — Anonymous",
  "\"If you think technology can solve your security problems, you don't understand the problems.\" — Bruce Schneier",
  "\"Ethical hacking is the art of thinking like a criminal to protect like a guardian.\" — Anonymous",
  "\"The cost of prevention is always less than the cost of cure.\" — JEBAT Principle",
  "\"Zero trust doesn't mean zero faith. It means verify everything.\" — Anonymous",
  "\"A vulnerability disclosed is a vulnerability half-fixed.\" — Anonymous",
  "\"The most dangerous vulnerability is the one you don't know exists.\" — Anonymous",
  "\"Encryption is the lock on the door of the digital age.\" — Anonymous",
  "\"Social engineering will always beat technical security.\" — Kevin Mitnick",
  "\"The difference between a hacker and a pentester is permission.\" — Anonymous",
  "\"Security through obscurity is not security. It's hope.\" — Anonymous",
  "\"Logs don't lie. People do. Monitor everything.\" — Anonymous",
  "\"The best firewall rule is the one you don't need.\" — Anonymous",
  "\"A secure system is a tested system.\" — JEBAT Principle",
  "\"Don't patch the symptom. Fix the root cause.\" — Anonymous",
  "\"Every breach is a failure of imagination by the defenders.\" — Anonymous",
  "\"Threat modeling is thinking about tomorrow's attacks today.\" — Anonymous",
  "\"The most secure password is the one you never type.\" — Anonymous",
  "\"Compliance is not security. Security is not compliance.\" — Anonymous",
  "\"An untested backup is a lie you tell yourself.\" — Anonymous",
  "\"The cloud is just someone else's computer. Secure accordingly.\" — Anonymous",
  "\"Defense in depth means the attacker has to win every time. You only need to win once.\" — Anonymous",
  "\"Automate everything that can be automated. Humans make mistakes under pressure.\" — Anonymous",
  "\"The best incident response plan is the one you practice.\" — Anonymous",
  "\"Never trust input. Always validate. Always sanitize.\" — JEBAT Principle",
  "\"A pentest report without remediation is just a horror story.\" — Anonymous",
];

function StatusDot({ status }: { status: string }) {
  const color = status === "complete" ? "bg-emerald-400" : status === "in-progress" ? "bg-cyan-400" : "bg-neutral-600";
  return <span className={`inline-flex h-2.5 w-2.5 rounded-full ${color} animate-pulse-glow`} />;
}

export default function Home() {
  const [quote, setQuote] = useState(cyberQuotes[0]);

  useEffect(() => {
    const randomIndex = Math.floor(Math.random() * cyberQuotes.length);
    setQuote(cyberQuotes[randomIndex]);
  }, []);

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
            <a href="#integrations" className="transition hover:text-white">Integrations</a>
            <a href="#skills" className="transition hover:text-white">Skills</a>
            <a href="#roadmap" className="transition hover:text-white">Roadmap</a>
            <Link href="/demo" className="rounded-full border border-cyan-400/30 px-4 py-2 text-cyan-300 transition hover:bg-cyan-400/10">
              Try Demo
            </Link>
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-4 py-2 text-black font-medium transition hover:bg-cyan-300">
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
            JEBATCore v2.0 — Now with Pengawal CyberSec & Agent Town
          </div>
          <h1 className="max-w-4xl text-5xl font-bold tracking-tight md:text-7xl">
            The LLM Ecosystem That{" "}
            <span className="gradient-text">Remembers Everything</span>
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-neutral-400">
            Eternal memory. Multi-agent orchestration. 6 thinking modes. CyberSec assistant.
            Self-hosted, privacy-first. Built by NusaByte for developers who need a buddy, not an assistant.
          </p>
          <div className="flex flex-wrap justify-center gap-4 pt-4">
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Let's Build Together →
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
              ["23+", "Specialist Agents"],
              ["40+", "Optimized Skills"],
              ["9", "Pages Deployed"],
              ["87%", "Roadmap Complete"],
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

      {/* Integrations */}
      <section id="integrations" className="mx-auto max-w-7xl px-6 py-16">
        <h2 className="mb-2 text-center text-3xl font-bold md:text-4xl">Integrations</h2>
        <p className="mx-auto mb-12 max-w-xl text-center text-neutral-400">Plug JEBAT into your existing tools. Bring your agents, connect your gateway, play in the world.</p>
        <div className="grid gap-5 md:grid-cols-3">
          {integrations.map((item) => (
            <article key={item.title} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6 flex flex-col">
              <div className="mb-3 text-3xl">{item.icon}</div>
              <h3 className="mb-2 text-xl font-semibold text-white">{item.title}</h3>
              <p className="mb-4 text-sm leading-7 text-neutral-400 flex-1">{item.description}</p>
              <div className="flex gap-3 mt-auto">
                {item.link !== "#" && (
                  <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-sm text-cyan-300 underline underline-offset-4 transition hover:text-cyan-200">
                    View Project
                  </a>
                )}
                <Link href={item.actionLink} className="text-sm text-cyan-300 underline underline-offset-4 transition hover:text-cyan-200">
                  {item.action}
                </Link>
              </div>
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
                { label: "├─ Agent Orchestrator", sub: "23 specialists · Council workflows", indent: 2 },
                { label: "├─ Serangan Autonomous", sub: "Codebase scanner · IBM agentic-ai-cyberres · 18 MCP tools", indent: 2 },
                { label: "├─ Pengawal (CyberSec)", sub: "Perisai · Pengawal · Serangan", indent: 2 },
                { label: "└─ Agent Town", sub: "Pixel-art RPG task assignment world", indent: 2 },
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
                ["AI/ML", "Ollama · OpenAI · Anthropic · Google Gemini · OpenRouter · ZAI"],
                ["DevOps", "Docker Compose · Nginx · Let's Encrypt"],
                ["CLI", "Node.js (jebat) · Python (jebat_dev) · Rich UI"],
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
        <h2 className="mb-2 text-center text-3xl font-bold">Optimized & Enhanced Skills</h2>
        <p className="mx-auto mb-4 max-w-xl text-center text-neutral-400">
          Every skill has been optimized for token efficiency, enhanced with real-world patterns from skills.sh, and adapted for the JEBAT ecosystem.
        </p>
        <p className="mx-auto mb-10 text-center text-sm text-cyan-300">
          Owner: <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="underline underline-offset-4 transition hover:text-cyan-200">humm1ngb1rd — nusabyte.my</a>
        </p>
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
            Tell us about yourself, your environment, and what you need. We'll set things up for you.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Start Onboarding →
            </Link>
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
            <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="transition hover:text-white">nusabyte.my</a>
            <Link href="/demo" className="transition hover:text-white">Demo</Link>
            <Link href="/onboarding" className="transition hover:text-white">Onboarding</Link>
          </div>
        </div>
        <div className="border-t border-white/5">
          <div className="mx-auto max-w-7xl px-6 py-6 text-center">
            <div className="text-xs text-neutral-600">
              Owner: <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">humm1ngb1rd — nusabyte.my</a>
              {" "}· Created by <a href="https://nusabyte.my" target="_blank" rel="noopener noreferrer" className="text-neutral-400 transition hover:text-cyan-300">NusaByte</a>
            </div>
            <div className="mt-2 text-xs text-neutral-700 italic max-w-2xl mx-auto">
              {quote}
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
