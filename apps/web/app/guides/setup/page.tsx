import Link from "next/link";

const steps = [
  {
    step: 1,
    title: "Prerequisites",
    description: "Ensure you have the following installed on your system:",
    commands: [
      { label: "Node.js ≥ 18", command: "node --version" },
      { label: "Python ≥ 3.11", command: "python3 --version" },
      { label: "Git ≥ 2.40", command: "git --version" },
      { label: "Docker (optional)", command: "docker --version" },
    ],
  },
  {
    step: 2,
    title: "Clone the Repository",
    description: "Get the full JEBAT codebase with all agents, skills, and infrastructure configs.",
    commands: [
      { label: "Clone", command: "git clone https://github.com/nusabyte-my/jebat-core.git" },
      { label: "Enter", command: "cd jebat-core" },
    ],
  },
  {
    step: 3,
    title: "Install Dependencies",
    description: "Install both frontend (Next.js) and backend (FastAPI) dependencies.",
    commands: [
      { label: "Frontend", command: "cd apps/web && npm install && cd ../.." },
      { label: "Backend", command: "cd apps/api && pip install -r requirements.txt && cd ../.." },
    ],
  },
  {
    step: 4,
    title: "Configure Environment",
    description: "Copy the environment template and configure your LLM provider keys.",
    commands: [
      { label: "Copy env", command: "cp infra/docker/.env.example .env" },
      { label: "Edit", command: "nano .env  # Add your API keys" },
    ],
  },
  {
    step: 5,
    title: "Start the Backend API",
    description: "Start FastAPI on port 8000 with memory, agents, and security scanning.",
    commands: [
      { label: "Start API", command: "cd apps/api && python -m services.api.jebat_api &" },
      { label: "Verify", command: "curl http://localhost:8000/api/v1/health" },
    ],
  },
  {
    step: 6,
    title: "Start the Frontend",
    description: "Start Next.js dev server on localhost:3000 with hot reload.",
    commands: [
      { label: "Start frontend", command: "cd apps/web && npm run dev" },
      { label: "Open", command: "open http://localhost:3000" },
    ],
  },
  {
    step: 7,
    title: "Install to Your IDE",
    description: "Inject JEBAT context into your IDE for AI-assisted development.",
    commands: [
      { label: "VS Code", command: "npx github:nusabyte-my/jebat-core install" },
      { label: "Verify", command: "cat .github/copilot-instructions.md" },
    ],
  },
];

export default function SetupGuide() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">📖</span>
            <span className="font-semibold tracking-tight">Setup & Installation Guide</span>
          </div>
          <Link href="/guides" className="text-sm text-neutral-400 transition hover:text-white">← All Guides</Link>
        </div>
      </nav>

      <div className="mx-auto max-w-4xl px-6 py-12 space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300">
            For Developers
          </span>
          <h1 className="text-3xl font-bold md:text-4xl">Setup & Installation</h1>
          <p className="text-neutral-400 text-lg">Get JEBAT running on your local machine in 7 steps. Estimated time: 5-10 minutes.</p>
        </div>

        {/* Steps */}
        <div className="space-y-6">
          {steps.map((step) => (
            <div key={step.step} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-cyan-400/20 text-cyan-300 flex items-center justify-center font-bold text-lg">
                  {step.step}
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-white mb-2">{step.title}</h2>
                  <p className="text-sm text-neutral-400 mb-4">{step.description}</p>
                  <div className="space-y-2">
                    {step.commands.map((cmd) => (
                      <div key={cmd.label}>
                        <div className="text-xs text-neutral-500 mb-1">{cmd.label}</div>
                        <div className="rounded-lg bg-black/40 border border-white/5 px-4 py-3">
                          <pre className="text-sm font-mono text-cyan-300 whitespace-pre-wrap">{cmd.command}</pre>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Verification */}
        <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-6">
          <h2 className="text-xl font-semibold text-emerald-300 mb-4">✅ Verify Installation</h2>
          <p className="text-sm text-neutral-400 mb-4">Run these checks to confirm everything is working:</p>
          <div className="space-y-3">
            {[
              { label: "API Health", command: "curl http://localhost:8000/api/v1/health", expected: '{"healthy":true,"database":true,"redis":true}' },
              { label: "Frontend", command: "open http://localhost:3000", expected: "JEBAT landing page loads" },
              { label: "IDE Context", command: "cat .github/copilot-instructions.md", expected: "JEBAT context file exists" },
            ].map((check) => (
              <div key={check.label}>
                <div className="text-xs text-neutral-500 mb-1">{check.label}</div>
                <div className="rounded-lg bg-black/40 border border-white/5 px-4 py-2">
                  <pre className="text-xs font-mono text-cyan-300">{check.command}</pre>
                </div>
                <div className="text-xs text-emerald-400/60 mt-1">Expected: {check.expected}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Next Steps */}
        <div className="flex flex-wrap gap-4 pt-4">
          <Link href="/guides/ide-setup" className="rounded-full bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300">
            Next: IDE Integration →
          </Link>
          <Link href="/guides" className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition hover:bg-white/10">
            All Guides
          </Link>
        </div>
      </div>
    </main>
  );
}
