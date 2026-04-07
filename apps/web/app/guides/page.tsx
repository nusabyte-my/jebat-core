import Link from "next/link";

const guideCategories = [
  {
    id: "developers",
    icon: "🔧",
    title: "Developers",
    description: "Code assistance, debugging, testing, and deployment",
    pages: [
      { title: "Setup & Installation", description: "Clone, install dependencies, and start JEBAT on your local machine.", path: "/guides/setup" },
      { title: "IDE Integration", description: "Install JEBAT context into VS Code, Cursor, Zed, Trae, or Antigravity.", path: "/guides/ide-setup" },
      { title: "Code Review Workflow", description: "Use multi-agent code review — Tukang writes, Hulubalang audits, Penyemak validates.", path: "/guides/code-review" },
      { title: "Deployment Guide", description: "Deploy JEBAT to Docker, VPS, or production with Traefik and Let's Encrypt.", path: "/guides/deployment" },
    ],
  },
  {
    id: "security",
    icon: "🛡️",
    title: "Security Teams",
    description: "Vulnerability scanning, pentesting, and compliance",
    pages: [
      { title: "Security Scanning", description: "Run autonomous security scans on your codebase. Understand findings and auto-fix vulnerabilities.", path: "/guides/security-scan" },
      { title: "Pentesting Guide", description: "Use Serangan (offensive) agent for authorized penetration testing with proper authorization.", path: "/guides/pentesting" },
      { title: "Compliance Reports", description: "Generate GDPR, SOC2, and ISO27001 compliance reports from audit logs.", path: "/guides/compliance" },
      { title: "Incident Response", description: "Use JEBAT's incident response workflow — detect, investigate, contain, remediate.", path: "/guides/incident-response" },
    ],
  },
  {
    id: "operations",
    icon: "⚙️",
    title: "Operations & DevOps",
    description: "Infrastructure, CI/CD, monitoring, and automation",
    pages: [
      { title: "Docker Setup", description: "Start JEBAT with Docker Compose — API, WebUI, Redis, and database in one command.", path: "/guides/docker" },
      { title: "VPS Deployment", description: "Deploy to a VPS with Nginx, Traefik, and Let's Encrypt SSL for jebat.online.", path: "/guides/vps" },
      { title: "Monitoring Setup", description: "Configure Prometheus and Grafana for real-time JEBAT metrics and alerts.", path: "/guides/monitoring" },
      { title: "CI/CD Pipeline", description: "Set up GitHub Actions for automated testing, building, and deployment.", path: "/guides/cicd" },
    ],
  },
  {
    id: "research",
    icon: "🔍",
    title: "Researchers & Analysts",
    description: "Research workflows, data analysis, and documentation",
    pages: [
      { title: "Research Workflow", description: "Use Pawang (researcher) agent for deep investigation, synthesis, and documentation.", path: "/guides/research" },
      { title: "Data Analysis", description: "Use Penganalisis (analyst) agent for KPI review, funnel analysis, and experiments.", path: "/guides/analysis" },
      { title: "Documentation", description: "Generate structured documentation from code, architecture decisions, and API specs.", path: "/guides/documentation" },
    ],
  },
];

export default function GuidesPage() {
  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">📖</span>
            <span className="font-semibold tracking-tight">JEBAT Guides</span>
          </div>
          <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 py-12 space-y-12">
        {/* Hero */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl font-bold md:text-5xl gradient-text">Guides for Every Domain</h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-400">
            Step-by-step guides tailored to your role. Whether you're a developer, security analyst, DevOps engineer, or researcher — JEBAT has you covered.
          </p>
        </section>

        {/* Guide Categories */}
        {guideCategories.map((cat) => (
          <section key={cat.id}>
            <div className="flex items-center gap-3 mb-6">
              <span className="text-3xl">{cat.icon}</span>
              <div>
                <h2 className="text-2xl font-bold">{cat.title}</h2>
                <p className="text-sm text-neutral-400">{cat.description}</p>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {cat.pages.map((page) => (
                <Link key={page.path} href={page.path} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5 flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-cyan-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-1">{page.title}</h3>
                    <p className="text-sm text-neutral-400">{page.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        ))}

        {/* CTA */}
        <section className="text-center space-y-6 pt-8">
          <h2 className="text-2xl font-bold">Can't Find What You Need?</h2>
          <p className="text-neutral-400">Check our GitHub repository for additional documentation and community guides.</p>
          <div className="flex flex-wrap justify-center gap-4">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full border border-white/15 px-8 py-3.5 text-base font-medium text-white transition hover:bg-white/10">
              GitHub Repository
            </a>
            <a href="https://github.com/nusabyte-my/jebat-core/issues" target="_blank" rel="noopener noreferrer" className="rounded-full bg-cyan-400 px-8 py-3.5 text-base font-semibold text-black transition hover:bg-cyan-300">
              Request a Guide →
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
