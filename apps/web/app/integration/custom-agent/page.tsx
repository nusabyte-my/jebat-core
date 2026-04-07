"use client";

import Link from "next/link";

const steps = [
  {
    step: 1,
    title: "Create Your Agent",
    description: "Any AI agent that can communicate via REST API or WebSocket works. Python, Node.js, Go — doesn't matter.",
    code: "from fastapi import FastAPI\napp = FastAPI()\n\n@app.post('/chat')\nasync def chat(message: str):\n    return {'response': process(message)}",
  },
  {
    step: 2,
    title: "Register with JEBAT Gateway",
    description: "Point your agent to the jebat-gateway on port 18789. Register as a worker with a role and skill set.",
    code: "POST /gateway/register\n{\n  \"name\": \"my-agent\",\n  \"role\": \"tukang\",\n  \"skills\": [\"fullstack\", \"database\"],\n  \"endpoint\": \"http://localhost:3001/chat\"\n}",
  },
  {
    step: 3,
    title: "JEBAT Routes Work to You",
    description: "When a task matches your skills, Panglima (the orchestrator) sends it your way. You execute and stream results back.",
    code: "POST /gateway/task\n{\n  \"task\": \"Build a user CRUD API\",\n  \"context\": {...memory...},\n  \"thinking_mode\": \"deliberate\"\n}",
  },
  {
    step: 4,
    title: "Results Flow Back",
    description: "Your results are streamed back through the gateway to wherever the user is — web UI, CLI, IDE, or Agent Town.",
    code: "// Stream tool calls and results\nws.send(JSON.stringify({\n  type: 'tool_use',\n  tool: 'run_code',\n  status: 'completed',\n  result: '200 OK'\n}))",
  },
];

const adapters = [
  { name: "REST API", desc: "Any HTTP endpoint", complexity: "Easy" },
  { name: "WebSocket", desc: "Real-time streaming", complexity: "Medium" },
  { name: "MCP Protocol", desc: "Model Context Protocol", complexity: "Medium" },
  { name: "OpenAI Compatible", desc: "Chat completions format", complexity: "Easy" },
];

export default function CustomAgentIntegrationPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">🤖</span>
            <span className="font-semibold tracking-tight">Custom Agent Integration</span>
          </div>
          <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
        </div>
      </nav>

      <div className="mx-auto max-w-5xl px-6 py-12 space-y-16">
        {/* Hero */}
        <section className="text-center space-y-6">
          <div className="text-6xl">🤖 ⚡ ⚔️</div>
          <h1 className="text-4xl font-bold md:text-5xl">
            Bring <span className="gradient-text">Your Own Agent</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            JEBAT's adapter system accepts any AI agent. Connect your custom agent to our memory, skills, and orchestration system.
          </p>
        </section>

        {/* Steps */}
        <section>
          <h2 className="text-2xl font-bold mb-8">Integration Steps</h2>
          <div className="space-y-8">
            {steps.map((s) => (
              <div key={s.step} className="flex gap-6">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-cyan-400/20 text-cyan-300 flex items-center justify-center font-bold text-lg">
                  {s.step}
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="text-lg font-semibold">{s.title}</h3>
                  <p className="text-sm text-neutral-400">{s.description}</p>
                  <pre className="rounded-lg bg-black/40 border border-white/5 px-4 py-3 text-xs font-mono text-cyan-300 overflow-x-auto whitespace-pre">
                    {s.code}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Adapters */}
        <section>
          <h2 className="text-2xl font-bold mb-2">Supported Protocols</h2>
          <p className="text-neutral-400 mb-8">Pick whichever your agent already supports.</p>
          <div className="grid gap-4 md:grid-cols-2">
            {adapters.map((a) => (
              <div key={a.name} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold">{a.name}</h3>
                  <span className={`text-xs rounded-full px-2 py-1 ${a.complexity === "Easy" ? "bg-emerald-400/10 text-emerald-300" : "bg-amber-400/10 text-amber-300"}`}>
                    {a.complexity}
                  </span>
                </div>
                <p className="text-sm text-neutral-400">{a.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="text-center space-y-6">
          <h2 className="text-2xl font-bold">Ready to Connect?</h2>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/onboarding" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Start Onboarding →
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
