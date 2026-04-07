// ─── Enterprise Icon System for JEBAT ─────────────────────────────────────────
// SVG-based icons replacing emoji for professional appearance
// Usage: <AgentIcon name="panglima" size={24} color="#00E5FF" />

const ICON_PATHS: Record<string, string> = {
  // Core Agents
  panglima: "M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5", // Crown/sword
  tukang: "M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z", // Wrench
  hulubalang: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z", // Shield
  pawang: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7", // Search
  syahbandar: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z", // Gear
  bendahara: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4", // Database
  penyemak: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z", // Check circle
  hikmat: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z", // Lightbulb
  pengawal: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z", // Lock
  perisai: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z", // Shield check
  serangan: "M13 10V3L4 14h7v7l9-11h-7z", // Lightning
  penganalisis: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z", // Bar chart

  // SEO/Marketing Agents
  penjejak: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9", // Globe/SEO
  penggerak: "M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z", // Growth/Marketing
  jurutulis: "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z", // Copy/Content
  strategi: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z", // Strategy/Bulb

  // Platform Icons
  memory: "M4 7v10c0 2 3.582 4 8 4s8-2 8-4V7M4 7c0 2 3.582 4 8 4s8-2 8-4M4 7c0-2 3.582-4 8-4s8 2 8 4",
  agents: "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z",
  security: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z",
  thinking: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  gateway: "M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.858 15.355-5.858 21.213 0",
  mobile: "M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z",
  voice: "M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z",
  enterprise: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4",
  distributed: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9",
  geo: "M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z", // Location/GEO
  sem: "M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122", // SEM/Ads
  aem: "M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z", // AEM/Content
};

export function AgentIcon({
  name,
  size = 24,
  color = "currentColor",
  className = "",
}: {
  name: string;
  size?: number;
  color?: string;
  className?: string;
}) {
  const path = ICON_PATHS[name];
  if (!path) return null;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d={path} />
    </svg>
  );
}

// ─── Icon Map with Colors ─────────────────────────────────────────────────────

export const AGENT_ICONS: Record<string, { icon: string; color: string }> = {
  panglima: { icon: "panglima", color: "#00E5FF" },
  tukang: { icon: "tukang", color: "#3B82F6" },
  hulubalang: { icon: "hulubalang", color: "#EF4444" },
  pawang: { icon: "pawang", color: "#10B981" },
  syahbandar: { icon: "syahbandar", color: "#F59E0B" },
  bendahara: { icon: "bendahara", color: "#8B5CF6" },
  penyemak: { icon: "penyemak", color: "#EC4899" },
  hikmat: { icon: "hikmat", color: "#06B6D4" },
  pengawal: { icon: "pengawal", color: "#F97316" },
  perisai: { icon: "perisai", color: "#14B8A6" },
  serangan: { icon: "serangan", color: "#EF4444" },
  penganalisis: { icon: "penganalisis", color: "#A855F7" },
  penjejak: { icon: "penjejak", color: "#06B6D4" },
  penggerak: { icon: "penggerak", color: "#F59E0B" },
  jurutulis: { icon: "juritulis", color: "#EC4899" },
  strategi: { icon: "strategi", color: "#8B5CF6" },
  geo: { icon: "geo", color: "#10B981" },
  sem: { icon: "sem", color: "#F59E0B" },
  aem: { icon: "aem", color: "#3B82F6" },
};

// ─── Pixel Agent Component ────────────────────────────────────────────────────

export function PixelAgent({
  name,
  size = 64,
  color = "#00E5FF",
  animated = false,
}: {
  name: string;
  size?: number;
  color?: string;
  animated?: boolean;
}) {
  const icon = AGENT_ICONS[name];
  if (!icon) return null;

  const pixelSize = Math.max(4, Math.floor(size / 24));

  return (
    <div
      className={`relative inline-flex items-center justify-center ${animated ? "animate-bounce-slow" : ""}`}
      style={{ width: size, height: size }}
    >
      {/* Pixel grid background */}
      <div
        className="absolute inset-0 rounded-lg border"
        style={{
          borderColor: color + "20",
          backgroundColor: color + "08",
          backgroundImage: `linear-gradient(${color}10 1px, transparent 1px), linear-gradient(90deg, ${color}10 1px, transparent 1px)`,
          backgroundSize: `${pixelSize * 2}px ${pixelSize * 2}px`,
        }}
      />
      {/* Icon */}
      <div className="relative z-10">
        <AgentIcon name={icon.icon} size={size * 0.6} color={color} />
      </div>
      {/* Glow effect */}
      <div
        className="absolute inset-0 rounded-lg opacity-20 blur-md"
        style={{ backgroundColor: color }}
      />
    </div>
  );
}

// ─── Skill Tooltip Data ───────────────────────────────────────────────────────

export const SKILL_INFO: Record<string, { description: string; provider?: string; useCase: string }> = {
  Panglima: { description: "Capture-first orchestration. Routes tasks to the right specialist, manages consensus workflows, and makes final decisions.", useCase: "Complex multi-domain tasks" },
  Hikmat: { description: "Memory engine with 5-layer cognitive architecture (M0-M4). Heat-based importance scoring, vector search, and cross-session continuity.", useCase: "Cross-session memory & recall" },
  "Agent Dispatch": { description: "Multi-domain routing, sequencing, and verification planning. Determines minimum useful skill set for any task.", useCase: "Task routing & verification" },
  Tukang: { description: "Full-stack development specialist. Writes, debugs, tests, and deploys code across React, Next.js, Python, and more.", useCase: "Code generation & debugging" },
  "Tukang Web": { description: "Browser-facing frontend implementation. Specializes in UI components, responsive design, and user interactions.", useCase: "Frontend development" },
  "Pembina Aplikasi": { description: "Cross-layer application delivery. Connects frontend, backend, database, and infrastructure into cohesive systems.", useCase: "Full application delivery" },
  Hulubalang: { description: "Security, pentesting, CTF, and hardening specialist. Identifies vulnerabilities and provides remediation guidance.", useCase: "Security audits & pentesting" },
  Pengawal: { description: "Three-tier cybersecurity assistant: Perisai (defensive), Pengawal (monitoring), Serangan (authorized offensive).", useCase: "Enterprise security operations" },
  Perisai: { description: "Defensive security specialist. Vulnerability scanning, threat modeling (STRIDE/DREAD), OWASP/CIS compliance auditing.", useCase: "Vulnerability assessment" },
  Serangan: { description: "Authorized offensive security. Reconnaissance, exploit chain generation, pentest reporting with proper authorization gates.", useCase: "Authorized penetration testing" },
  Pawang: { description: "Investigation, research, and structured documentation. Deep web research, synthesis, and report generation.", useCase: "Research & investigation" },
  Penganalisis: { description: "KPI review, funnel analysis, experiments, and reporting. Product analytics with PM specialist agent integration.", useCase: "Data analysis & reporting" },
  Syahbandar: { description: "Cron, CI/CD, Docker, webhooks, and automation scripts. Infrastructure management and deployment orchestration.", useCase: "DevOps & automation" },
  Bendahara: { description: "PostgreSQL, Redis, migrations, and optimization. Database schema design and performance tuning.", useCase: "Database management" },
  Penyemak: { description: "QA, regression checks, and acceptance validation. Code review, testing, and quality gate enforcement.", useCase: "Quality assurance" },
  "Senibina Antara Muka": { description: "UI/UX, responsive flows, and usability. Pixel-perfect design implementation and user experience optimization.", useCase: "UI/UX design" },
  "Penyebar Reka Bentuk": { description: "Design systems, tokens, component libraries, and DESIGN.md execution. Consistent design language across the platform.", useCase: "Design system management" },
  "Penjejak Carian": { description: "SEO and discoverability specialist. Meta optimization, structured data, keyword research, and Google placement improvement.", useCase: "SEO optimization" },
  "Penggerak Pasaran": { description: "Positioning, offers, campaigns, and funnels. Growth marketing with SEM and content strategy integration.", useCase: "Marketing & growth" },
  "Jurutulis Jualan": { description: "Conversion copy and landing messaging. Persuasive content for landing pages, CTAs, and sales materials.", useCase: "Copywriting & content" },
  "Strategi Jenama": { description: "Positioning, message architecture, and voice discipline. Brand consistency across all touchpoints.", useCase: "Brand strategy" },
  "Strategi Produk": { description: "Feature framing, scope cuts, acceptance criteria, and roadmap tradeoffs. Product management with RICE/Kano prioritization.", useCase: "Product strategy" },
  "Khidmat Pelanggan": { description: "Onboarding, support workflows, FAQ systems, and retention feedback. Customer success optimization.", useCase: "Customer success" },
  "Penulis Cadangan": { description: "Client proposals, scoped offers, and SOW structure. Commercial document generation with proper scoping.", useCase: "Proposals & SOWs" },
  "Penggerak Jualan": { description: "One-pagers, objection handling, outbound support, and sales collateral. Sales enablement content.", useCase: "Sales enablement" },
  "Pengkarya Kandungan": { description: "Editorial and campaign content systems. Content planning, creation workflows, and distribution strategy.", useCase: "Content management" },
};

// ─── Feature Icons ────────────────────────────────────────────────────────────

export const FEATURE_ICONS: Record<string, string> = {
  memory: "memory",
  agents: "agents",
  security: "security",
  thinking: "thinking",
  gateway: "gateway",
  mobile: "mobile",
  voice: "voice",
  enterprise: "enterprise",
  distributed: "distributed",
};
