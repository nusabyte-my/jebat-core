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
    <>
      <a href="/" className="fixed top-4 left-4 z-50 text-sm text-neutral-400 hover:text-white transition flex items-center gap-1 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full border border-white/10">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
        Home
      </a>
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
    </>
  );
}
