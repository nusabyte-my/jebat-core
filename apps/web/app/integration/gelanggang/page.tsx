"use client";

import Link from "next/link";

const steps = [
  {
    step: 1,
    title: "Enter the Gelanggang",
    code: "npx @nusabyte/jebat gelanggang",
    description: "Launch Gelanggang Panglima — the LLM-to-LLM orchestration arena. No setup needed.",
  },
  {
    step: 2,
    title: "Register Your Agents",
    code: "npx @nusabyte/jebat agent-register",
    description: "Agents from all providers (OpenAI, Anthropic, Gemini, Ollama, ZAI) register with the Gelanggang.",
  },
  {
    step: 3,
    title: "Choose a Collaboration Pattern",
    code: "sequential | parallel | consensus | adversarial",
    description: "Select how agents interact — build on each other, work simultaneously, vote, or debate.",
  },
  {
    step: 4,
    title: "Watch LLM-to-LLM Communication",
    code: "OpenAI's Tukang → Anthropic's Hulubalang → Gemini's Penyemak",
    description: "Agents communicate across providers using the standardized JEBAT protocol. Watch them debate, propose, and decide.",
  },
];

const workerRoles = [
  { role: "Tukang (Builder)", sprite: "🔧", skills: "fullstack, app-development, web-developer", description: "Writes code, builds features, deploys apps", provider: "OpenAI" },
  { role: "Hulubalang (Guard)", sprite: "🛡️", skills: "security-pentest, pengawal, perisai, serangan", description: "Security audits, vulnerability scanning, pentest reports", provider: "Anthropic" },
  { role: "Pawang (Researcher)", sprite: "🔍", skills: "research-docs, jebat-researcher, jebat-analyst", description: "Deep research, documentation, data analysis", provider: "Gemini" },
  { role: "Syahbandar (Ops)", sprite: "⚙️", skills: "automation, database, agent-dispatch", description: "CI/CD, Docker, database migrations, automation", provider: "Ollama" },
  { role: "Penganalisis (Analyst)", sprite: "📊", skills: "penganalisis-pm, product-strategy, brand-strategy", description: "Product analysis, KPI review, funnel analysis", provider: "ZAI" },
  { role: "Penyemak (QA)", sprite: "✅", skills: "qa-validation, testing, code-review", description: "Code review, testing, validation, acceptance", provider: "Anthropic" },
];

export default function GelanggangIntegrationPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">🏛️</span>
            <span className="font-semibold tracking-tight">Gelanggang Panglima × JEBAT</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/gelanggang" className="text-sm text-cyan-300 transition hover:text-cyan-200">Live Demo ↗</Link>
            <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 py-12 space-y-16">
        {/* Hero */}
        <section className="text-center space-y-6">
          <div className="text-6xl">🏛️ ⚡ ⚔️</div>
          <h1 className="text-4xl font-bold md:text-5xl">
            <span className="text-amber-300">Gelanggang Panglima</span> — LLM-to-LLM Arena
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            Watch AI agents from different providers (OpenAI, Anthropic, Gemini, Ollama, ZAI) communicate, collaborate, and debate — all orchestrated by Panglima in the Gelanggang.
          </p>
        </section>

        {/* How It Works */}
        <section>
          <h2 className="text-2xl font-bold mb-8">How Gelanggang Works</h2>
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
          <h2 className="text-2xl font-bold mb-2">Agents in the Gelanggang</h2>
          <p className="text-neutral-400 mb-8">Each agent connects to its LLM provider and communicates using the JEBAT protocol. Manually assign tasks — or let Panglima orchestrate.</p>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {workerRoles.map((w) => (
              <div key={w.role} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{w.sprite}</span>
                  <div>
                    <div className="font-semibold">{w.role}</div>
                    <div className="text-xs text-neutral-500">{w.provider}</div>
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
          <h2 className="text-2xl font-bold mb-6">Cross-Provider Communication Flow</h2>
          <div className="font-mono text-sm space-y-2">
            {[
              { label: "You (Panglima)", sub: "Assign task, choose pattern", indent: 0 },
              { label: "↓ Task assigned to Gelanggang", sub: "", indent: 0 },
              { label: "JEBAT Protocol Layer", sub: "Standardized message format", indent: 0 },
              { label: "├─ OpenAI Bridge", sub: "Tukang (gpt-4o) receives task", indent: 2 },
              { label: "├─ Anthropic Bridge", sub: "Hulubalang (claude-sonnet-4) reviews", indent: 2 },
              { label: "├─ Gemini Bridge", sub: "Pawang (gemini-2.5-pro) researches", indent: 2 },
              { label: "├─ Ollama Bridge", sub: "Syahbandar (qwen2.5-coder) deploys", indent: 2 },
              { label: "└─ ZAI Bridge", sub: "Penganalisis (glm-5) analyzes", indent: 2 },
              { label: "↓ Results aggregated", sub: "", indent: 0 },
              { label: "Gelanggang", sub: "Shows conversation, proposals, verdicts", indent: 0 },
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

        {/* Collaboration Patterns */}
        <section>
          <h2 className="text-2xl font-bold mb-2">Collaboration Patterns</h2>
          <p className="text-neutral-400 mb-8">Choose how agents work together in the Gelanggang.</p>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              {
                pattern: "Sequential",
                emoji: "➡️",
                desc: "Agent A → Agent B → Agent C. Each builds on the previous agent's work.",
                example: "Tukang writes code → Hulubalang audits → Penyemak validates",
                color: "#3B82F6",
              },
              {
                pattern: "Parallel",
                emoji: "⚡",
                desc: "All agents work simultaneously on the same task. Results combined at the end.",
                example: "Hulubalang + Pawang + Penyemak all analyze the same codebase independently",
                color: "#10B981",
              },
              {
                pattern: "Consensus",
                emoji: "🗳️",
                desc: "All agents propose solutions, then vote. Majority wins.",
                example: "3 agents propose architectures → all vote → 2 agree on microservices",
                color: "#F59E0B",
              },
              {
                pattern: "Adversarial",
                emoji: "⚔️",
                desc: "Two agents debate opposing positions. Third agent judges the winner.",
                example: "Tukang proposes monolith vs Syahbandar proposes microservices → Panglima judges",
                color: "#EF4444",
              },
            ].map((p) => (
              <div key={p.pattern} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-3xl">{p.emoji}</span>
                  <h3 className="font-semibold text-lg">{p.pattern}</h3>
                </div>
                <p className="text-sm text-neutral-400 mb-3">{p.desc}</p>
                <div className="rounded-lg bg-black/30 px-3 py-2 text-xs text-neutral-300">
                  {p.example}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="text-center space-y-6">
          <h2 className="text-2xl font-bold">Ready to Enter the Gelanggang?</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/gelanggang" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              🏛️ Try Live Demo →
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              View Source
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
