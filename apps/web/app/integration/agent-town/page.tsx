"use client";

import Link from "next/link";

const steps = [
  {
    step: 1,
    title: "Install Agent Town",
    code: "npx @geezerrrr/agent-town",
    description: "Run Agent Town instantly with npx. No clone needed.",
  },
  {
    step: 2,
    title: "Start Your OpenClaw Gateway",
    code: "openclaw gateway start",
    description: "Agent Town connects to your local OpenClaw gateway. Make sure it's running on port 18789.",
  },
  {
    step: 3,
    title: "Connect to JEBAT Skills",
    code: "npx @nusabyte/jebat install",
    description: "Install JEBAT context into Agent Town's workspace. This bridges JEBAT's 23+ skills into the RPG world.",
  },
  {
    step: 4,
    title: "Walk Up & Assign",
    code: "Approach a worker → Press E → Type your task",
    description: "Workers now have access to JEBAT's memory, agent orchestration, and CyberSec skills. Watch them execute in real-time.",
  },
];

const workerRoles = [
  { role: "Tukang (Builder)", sprite: "🔧", skills: "fullstack, app-development, web-developer", description: "Builds features, writes code, deploys apps" },
  { role: "Hulubalang (Guard)", sprite: "🛡️", skills: "security-pentest, pengawal, perisai, serangan", description: "Security audits, vulnerability scanning, pentest reports" },
  { role: "Pawang (Researcher)", sprite: "🔍", skills: "research-docs, jebat-researcher, jebat-analyst", description: "Deep research, documentation, data analysis" },
  { role: "Syahbandar (Ops)", sprite: "⚙️", skills: "automation, database, agent-dispatch", description: "CI/CD, Docker, database migrations, automation" },
  { role: "Penganalisis (Analyst)", sprite: "📊", skills: "penganalisis-pm, product-strategy, brand-strategy", description: "Product analysis, KPI review, funnel analysis" },
  { role: "Senibina (Designer)", sprite: "🎨", skills: "ui-ux, design-system, penyebar-reka-bentuk", description: "UI/UX review, design systems, responsive design" },
];

export default function AgentTownIntegrationPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">🏘️</span>
            <span className="font-semibold tracking-tight">Agent Town × JEBAT</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://github.com/geezerrrr/agent-town" target="_blank" rel="noopener noreferrer" className="text-sm text-neutral-400 transition hover:text-white">Agent Town ↗</a>
            <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 py-12 space-y-16">
        {/* Hero */}
        <section className="text-center space-y-6">
          <div className="text-6xl">🏘️ ⚡ ⚔️</div>
          <h1 className="text-4xl font-bold md:text-5xl">
            <span className="text-amber-300">Agent Town</span> × <span className="gradient-text">JEBAT</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            Walk around a pixel-art office, assign tasks to AI workers face-to-face, and watch JEBAT's multi-agent system execute everything in real-time.
          </p>
        </section>

        {/* How It Works */}
        <section>
          <h2 className="text-2xl font-bold mb-8">How to Integrate</h2>
          <div className="space-y-8">
            {steps.map((s) => (
              <div key={s.step} className="flex gap-6">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-cyan-400/20 text-cyan-300 flex items-center justify-center font-bold text-lg">
                  {s.step}
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="text-lg font-semibold">{s.title}</h3>
                  <code className="block rounded-lg bg-black/40 border border-white/5 px-4 py-2 text-sm font-mono text-cyan-300">
                    {s.code}
                  </code>
                  <p className="text-sm text-neutral-400">{s.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Worker Roles */}
        <section>
          <h2 className="text-2xl font-bold mb-2">JEBAT Workers in Agent Town</h2>
          <p className="text-neutral-400 mb-8">Each worker in Agent Town maps to a JEBAT skill specialist. Walk up and assign tasks naturally.</p>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {workerRoles.map((w) => (
              <div key={w.role} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{w.sprite}</span>
                  <div>
                    <div className="font-semibold">{w.role}</div>
                    <div className="text-xs text-neutral-500">Active Skills</div>
                  </div>
                </div>
                <p className="text-sm text-neutral-400 mb-3">{w.description}</p>
                <div className="flex flex-wrap gap-1.5">
                  {w.skills.split(", ").map((s) => (
                    <span key={s} className="text-xs rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-neutral-400">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Architecture */}
        <section className="rounded-3xl border border-white/10 bg-white/[0.02] p-8">
          <h2 className="text-2xl font-bold mb-6">How They Connect</h2>
          <div className="font-mono text-sm space-y-2">
            {[
              { label: "You (Boss)", sub: "Walk up to workers, assign tasks", indent: 0 },
              { label: "Agent Town (Phaser 3 + React)", sub: "Pixel RPG world, WebSocket chat", indent: 0 },
              { label: "↓ Task assigned via WebSocket", sub: "", indent: 0 },
              { label: "OpenClaw Gateway (:18789)", sub: "Routes task to JEBAT agent", indent: 0 },
              { label: "JEBAT Agent", sub: "Loads relevant skills, memory context", indent: 2 },
              { label: "├─ Hikmat Memory", sub: "Loads M1-M4 context for continuity", indent: 4 },
              { label: "├─ Panglima", sub: "Decomposes task, spawns specialists", indent: 4 },
              { label: "├─ Tukang / Hulubalang / Pawang", sub: "Executes the work", indent: 4 },
              { label: "└─ Penyemak", sub: "Reviews output before returning", indent: 4 },
              { label: "↓ Result streamed back via WebSocket", sub: "", indent: 0 },
              { label: "Agent Town", sub: "Shows chat, tool calls, status bubbles in-game", indent: 0 },
            ].map((row, i) => (
              <div key={i} style={{ paddingLeft: row.indent ? `${row.indent}rem` : undefined }}>
                {row.sub ? (
                  <div>
                    <span className="text-cyan-300">{row.label}</span>
                    <span className="ml-2 text-neutral-500">{row.sub}</span>
                  </div>
                ) : (
                  <span className="text-neutral-500">{row.label}</span>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="text-center space-y-6">
          <h2 className="text-2xl font-bold">Ready to Try?</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="https://github.com/geezerrrr/agent-town" target="_blank" rel="noopener noreferrer" className="rounded-full border border-amber-400/30 px-8 py-3.5 text-base font-medium text-amber-300 transition hover:bg-amber-400/10">
              Agent Town GitHub →
            </a>
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Start JEBAT Onboarding →
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
