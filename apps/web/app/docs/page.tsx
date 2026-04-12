const sections = [
  {
    title: "Memory System",
    body: "JEBAT uses a 5-layer memory stack: M0 sensory, M1 episodic, M2 semantic, M3 conceptual, and M4 procedural. Heat scoring governs retention, promotion, and decay.",
  },
  {
    title: "Skills",
    body: "Forty-plus JEBAT skills define memory, consolidation, orchestration, analysis, research, cybersecurity, hardening, and authorized pentesting workflows.",
  },
  {
    title: "Security",
    body: "Cybersecurity handles audit and detection, hardening applies defensive controls, and pentesting validates attack paths under explicit authorization.",
  },
  {
    title: "Platform",
    body: "The recommended stack is Next.js 14 + TypeScript + Tailwind + shadcn/ui with TimescaleDB and Redis behind JEBAT Gateway.",
  },
];

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-12 text-neutral-100 md:px-10">
      <div className="mx-auto max-w-5xl space-y-8">
        <div>
          <p className="mb-2 text-sm uppercase tracking-[0.25em] text-neutral-500">
            Documentation
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-white">
            JEBAT system docs
          </h1>
          <p className="mt-4 max-w-3xl text-neutral-300">
            Core documentation for the JEBAT platform. Explore the memory system, skills ecosystem, security workflows, and platform architecture.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {sections.map((section) => (
            <article
              key={section.title}
              className="rounded-2xl border border-white/10 bg-white/5 p-6"
            >
              <h2 className="mb-3 text-xl font-semibold text-white">
                {section.title}
              </h2>
              <p className="text-sm leading-7 text-neutral-300">{section.body}</p>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
