"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  HiOutlineCpuChip,
  HiOutlineServerStack,
  HiOutlineUsers,
  HiOutlineShieldCheck,
  HiOutlineBolt,
  HiOutlineChatBubbleLeftRight,
  HiOutlineRocketLaunch,
  HiOutlineGlobeAlt,
  HiOutlineLockClosed,
  HiOutlineDocumentText,
  HiOutlineCommandLine,
  HiOutlineCube,
  HiOutlineCog6Tooth,
  HiOutlineCheckCircle,
  HiOutlineArrowRight,
  HiOutlinePlay,
  HiOutlineEye,
  HiOutlineSquares2X2,
  HiOutlineArrowPath,
  HiOutlineSignal,
  HiOutlineMagnifyingGlass,
  HiOutlineClipboardDocumentCheck,
  HiOutlineKey,
  HiOutlineBanknotes,
  HiOutlineChartBar,
  HiOutlineAcademicCap,
  HiOutlineBuildingOffice,
  HiOutlineCodeBracket,
  HiOutlineWrenchScrewdriver,
  HiOutlineQueueList,
  HiOutlineBookOpen,
} from "react-icons/hi2";

// ─── Data ───────────────────────────────────────────────────────────────

const SECTIONS = [
  "hero", "agent", "portal", "chat", "gelanggang", "security", "guides", "cta",
] as const;

type SectionId = (typeof SECTIONS)[number];

const SECTION_LABELS: Record<SectionId, string> = {
  hero: "Home",
  agent: "Agent",
  portal: "Portal",
  chat: "Chat",
  gelanggang: "Arena",
  security: "Security",
  guides: "Guides",
  cta: "Get Started",
};

const ICON_SIZE = "1.25rem";
const ICON_CLASS = "text-cyan-400 flex-shrink-0";

// ─── Background Animation ───────────────────────────────────────────────

function AgentNetworkBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Array<{ x: number; y: number; vx: number; vy: number; size: number; label: string }>>([]);
  const mouseRef = useRef({ x: -9999, y: -9999 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const labels = ["Panglima", "Tukang", "Hulubalang", "Pengawal", "Pawang", "Syahbandar", "Bendahara", "Hikmat", "Penganalisis", "Penyemak"];
    const nodes = labels.map((label) => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: 2 + Math.random() * 2,
      label,
    }));
    nodesRef.current = nodes;

    const handleMouse = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener("mousemove", handleMouse);

    let animId: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
        const dx = mouseRef.current.x - n.x;
        const dy = mouseRef.current.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          n.vx += dx * 0.00003;
          n.vy += dy * 0.00003;
        }
        n.vx *= 0.999;
        n.vy *= 0.999;
      });

      const connectionDist = 180;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < connectionDist) {
            const opacity = (1 - dist / connectionDist) * 0.12;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      nodes.forEach((n) => {
        const dx = mouseRef.current.x - n.x;
        const dy = mouseRef.current.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 250) {
          const opacity = (1 - dist / 250) * 0.25;
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(mouseRef.current.x, mouseRef.current.y);
          ctx.strokeStyle = `rgba(34, 211, 238, ${opacity})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });

      nodes.forEach((n) => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.5)";
        ctx.fill();
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size + 3, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.08)";
        ctx.fill();
      });

      animId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouse);
      cancelAnimationFrame(animId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ opacity: 0.5 }}
    />
  );
}

// ─── Section Wrapper ────────────────────────────────────────────────────

function SectionContent({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`w-full min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12 lg:py-8 overflow-y-auto ${className}`}>
      <div className="max-w-6xl mx-auto w-full relative z-10">
        {children}
      </div>
    </div>
  );
}

function SectionHeader({ badge, title, subtitle }: { badge: string; title: string; subtitle: string }) {
  return (
    <div className="text-center mb-10 lg:mb-16">
      <span className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">
        <span className="inline-flex h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"/>
        {badge}
      </span>
      <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-3 lg:mb-4">{title}</h2>
      <p className="max-w-2xl mx-auto text-neutral-400 text-base lg:text-lg leading-relaxed">{subtitle}</p>
    </div>
  );
}

// ─── Navbar ─────────────────────────────────────────────────────────────

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  const scrollTo = (id: string) => {
    setMobileOpen(false);
    const el = document.getElementById(`section-${id}`);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled ? "bg-[#050505]/90 backdrop-blur-xl border-b border-white/5" : "bg-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-3">
        <a href="/" className="flex items-center gap-2 lg:gap-3 group">
          <motion.div
            className="flex items-center justify-center w-7 h-7 lg:w-9 lg:h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20"
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            <HiOutlineCpuChip className="w-4 h-4 lg:w-5 lg:h-5 text-white" />
          </motion.div>
          <div className="flex items-center gap-1 lg:gap-2">
            <span className="text-base lg:text-lg font-bold tracking-tight">JEBAT</span>
            <span className="hidden sm:inline text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
          </div>
        </a>

        <div className="hidden xl:flex items-center gap-1">
          {SECTIONS.map((s) => (
            <button
              key={s}
              onClick={() => scrollTo(s)}
              className="px-3 py-2 text-xs lg:text-sm text-neutral-400 hover:text-white transition rounded-lg hover:bg-white/5"
            >
              {SECTION_LABELS[s]}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 lg:gap-3">
          <a href="/status" className="hidden sm:inline-flex items-center gap-1 lg:gap-2 rounded-full border border-white/10 bg-white/5 px-3 lg:px-4 py-1.5 lg:py-2 text-xs lg:text-sm text-white hover:bg-white/10 transition">
            <HiOutlineChartBar className="w-3.5 h-3.5" />
            Status
          </a>
          <a href="/chat" className="hidden sm:inline-flex items-center gap-1 lg:gap-2 rounded-full border border-white/10 bg-white/5 px-3 lg:px-4 py-1.5 lg:py-2 text-xs lg:text-sm text-white hover:bg-white/10 transition">
            <HiOutlineChatBubbleLeftRight className="w-3.5 h-3.5" />
            Try Chat
          </a>
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-3 lg:px-5 py-1.5 lg:py-2 text-xs lg:text-sm font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
            Get Started
          </a>
          <button className="xl:hidden text-white p-1" onClick={() => setMobileOpen(!mobileOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/> : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16"/>}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="xl:hidden bg-[#050505]/98 border-t border-white/5 px-4 sm:px-6 py-4 space-y-1"
        >
          {SECTIONS.map((s) => (
            <button
              key={s}
              onClick={() => scrollTo(s)}
              className="block w-full text-left px-3 py-2 text-sm text-neutral-400 hover:text-white transition rounded-lg hover:bg-white/5"
            >
              {SECTION_LABELS[s]}
            </button>
          ))}
        </motion.div>
      )}
    </motion.nav>
  );
}

// ─── Side Dots ──────────────────────────────────────────────────────────

function SideDots() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = SECTIONS.indexOf(entry.target.id.replace("section-", "") as SectionId);
            if (idx >= 0) setActive(idx);
          }
        });
      },
      { threshold: 0.5 }
    );

    SECTIONS.forEach((s) => {
      const el = document.getElementById(`section-${s}`);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    const el = document.getElementById(`section-${id}`);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="fixed right-3 sm:right-4 lg:right-6 top-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-2 sm:gap-3">
      {SECTIONS.map((s, i) => (
        <button
          key={s}
          onClick={() => scrollTo(s)}
          className="group flex flex-col items-center gap-1"
          title={SECTION_LABELS[s]}
        >
          <motion.div
            className={`rounded-full transition-all duration-300 ${
              active === i
                ? "bg-cyan-400 w-2 h-5 sm:w-2.5 sm:h-6"
                : "bg-neutral-600 w-2 h-2 sm:w-2.5 sm:h-2.5 group-hover:bg-neutral-400"
            }`}
          />
          <span className={`hidden lg:block text-[9px] transition-colors whitespace-nowrap ${active === i ? "text-cyan-400" : "text-neutral-600"}`}>
            {SECTION_LABELS[s]}
          </span>
        </button>
      ))}
    </div>
  );
}

// ─── SECTION: Hero ──────────────────────────────────────────────────────

function HeroSection() {
  const stats = [
    { value: "10", label: "Core Agents", icon: <HiOutlineCpuChip className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} /> },
    { value: "24", label: "Specialists", icon: <HiOutlineUsers className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} /> },
    { value: "5", label: "Orchestration", icon: <HiOutlineArrowPath className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} /> },
    { value: "100%", label: "Self-Hosted", icon: <HiOutlineLockClosed className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} /> },
  ];

  return (
    <SectionContent>
      <div className="text-center space-y-8 lg:space-y-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300"
        >
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
          Enterprise AI Platform &middot; Self-Hosted &middot; Zero Cloud Dependency
        </motion.div>

        <div className="max-w-5xl mx-auto">
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-4 lg:mb-6"
          >
            The AI Platform That{" "}
            <span className="block mt-1 sm:mt-2">
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent"
              >
                Remembers,
              </motion.span>{" "}
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.35 }}
                className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent"
              >
                Collaborates,
              </motion.span>{" "}
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.5 }}
                className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent"
              >
                Protects.
              </motion.span>
            </span>
          </motion.h1>
        </div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="max-w-3xl mx-auto text-base lg:text-lg text-neutral-400 leading-relaxed"
        >
          JEBAT is the enterprise-grade, self-hosted AI orchestration platform that combines{" "}
          <strong className="text-white">eternal memory</strong>,{" "}
          <strong className="text-white">multi-agent collaboration</strong>, and{" "}
          <strong className="text-white">military-grade security</strong> into one unified system.
          Deploy on your infrastructure. Own your data. No cloud dependency.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.7 }}
          className="flex flex-wrap justify-center gap-3 lg:gap-4"
        >
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 lg:px-8 py-3 lg:py-4 text-sm lg:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            <HiOutlineRocketLaunch className="w-5 h-5" />
            Deploy JEBAT
            <HiOutlineArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </a>
          <a href="/chat" className="rounded-full border border-white/15 px-6 lg:px-8 py-3 lg:py-4 text-sm lg:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
            <HiOutlineChatBubbleLeftRight className="w-5 h-5" />
            Try Live Chat
          </a>
          <a href="/portal" className="rounded-full border border-white/15 px-6 lg:px-8 py-3 lg:py-4 text-sm lg:text-base font-medium text-white hover:bg-white/10 transition flex items-center gap-2">
            <HiOutlineBuildingOffice className="w-5 h-5" />
            Enterprise Portal
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 max-w-4xl mx-auto pt-4"
        >
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05, borderColor: "rgba(34,211,238,0.3)" }}
              className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 lg:p-5"
            >
              <div className="mb-2">{stat.icon}</div>
              <div className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-xs text-neutral-500">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Platform ──────────────────────────────────────────────────

function PlatformSection() {
  const pillars = [
    {
      icon: <HiOutlineCpuChip className="w-6 h-6 lg:w-7 lg:h-7 text-white" />,
      title: "Jebat Agent",
      subtitle: "Your Unified AI Workspace",
      desc: "Deploy your entire AI workspace in 30 seconds. IDE integration, 8 local LLMs, channel setup, and migration from OpenClaw/Hermes — all automated.",
      features: ["30-second setup wizard", "8 local LLM deployment", "IDE integration (VS Code, Zed, Cursor)", "Channel setup (Telegram, Discord, WhatsApp)", "OpenClaw/Hermes migration"],
      gradient: "from-cyan-400 to-blue-500",
      cta: "View Agent Docs",
      link: "/agent",
    },
    {
      icon: <HiOutlineServerStack className="w-6 h-6 lg:w-7 lg:h-7 text-white" />,
      title: "Jebat Core",
      subtitle: "The Platform Backbone",
      desc: "5-layer cognitive memory, 40+ specialized skills, multi-agent orchestration, and the gateway that routes across 5 LLM providers with intelligent failover.",
      features: ["M0-M4 eternal memory system", "40+ optimized skills", "Multi-agent orchestration", "CyberSec scanning & hardening", "Gateway with provider routing"],
      gradient: "from-purple-400 to-pink-500",
      cta: "Explore Core",
      link: "/portal",
    },
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Platform Architecture"
        title="Two Pillars. One Platform."
        subtitle="JEBAT is built on two powerful components that work together seamlessly to deliver enterprise-grade AI capabilities."
      />
      <div className="grid gap-5 lg:gap-6 grid-cols-1 md:grid-cols-2 max-w-5xl mx-auto">
        {pillars.map((p, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.15 + i * 0.15 }}
            whileHover={{ y: -4 }}
            className="group relative rounded-2xl lg:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 lg:p-8 hover:border-cyan-400/20 transition-colors"
          >
            <div className="flex items-start justify-between mb-6">
              <div className={`w-12 h-12 lg:w-14 lg:h-14 rounded-xl lg:rounded-2xl bg-gradient-to-br ${p.gradient} flex items-center justify-center shadow-lg`}>
                {p.icon}
              </div>
              <span className={`rounded-full bg-gradient-to-r ${p.gradient} text-white px-3 py-1 text-xs font-medium`}>{p.title}</span>
            </div>
            <h3 className="text-xl lg:text-2xl font-bold mb-1 lg:mb-2">{p.title}</h3>
            <p className="text-sm lg:text-base text-cyan-400 mb-3 lg:mb-4">{p.subtitle}</p>
            <p className="text-sm lg:text-base text-neutral-400 leading-relaxed mb-6">{p.desc}</p>
            <div className="space-y-2 lg:space-y-3 mb-6">
              {p.features.map((f, j) => (
                <div key={j} className="flex items-start gap-3 text-sm text-neutral-300">
                  <HiOutlineCheckCircle className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                  {f}
                </div>
              ))}
            </div>
            <a href={p.link} className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${p.gradient} px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition`}>
              {p.cta} <HiOutlineArrowRight className="w-4 h-4" />
            </a>
          </motion.div>
        ))}
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Agents ────────────────────────────────────────────────────

function AgentsSection() {
  const coreAgents = [
    { name: "Panglima", role: "Orchestration", model: "Claude 4", color: "cyan" },
    { name: "Tukang", role: "Development", model: "Qwen Coder", color: "purple" },
    { name: "Hulubalang", role: "Security Audit", model: "Hermes Sec", color: "red" },
    { name: "Pengawal", role: "CyberSec", model: "Hermes Sec", color: "orange" },
    { name: "Pawang", role: "Research", model: "Claude 4", color: "emerald" },
    { name: "Syahbandar", role: "Operations", model: "Qwen Coder", color: "blue" },
    { name: "Bendahara", role: "Database", model: "Qwen Coder", color: "indigo" },
    { name: "Hikmat", role: "Memory", model: "Claude 4", color: "pink" },
    { name: "Penganalisis", role: "Analytics", model: "Claude 4", color: "yellow" },
    { name: "Penyemak", role: "QA", model: "Claude 4", color: "teal" },
  ];

  const colorMap: Record<string, string> = {
    cyan: "from-cyan-400 to-blue-500", purple: "from-purple-400 to-pink-500", red: "from-red-400 to-rose-500",
    orange: "from-orange-400 to-amber-500", emerald: "from-emerald-400 to-teal-500", blue: "from-blue-400 to-indigo-500",
    indigo: "from-indigo-400 to-purple-500", pink: "from-pink-400 to-rose-500", yellow: "from-yellow-400 to-orange-500",
    teal: "from-teal-400 to-emerald-500",
  };

  const specialists = [
    "Tukang Web", "Pembina Aplikasi", "Khidmat Pelanggan", "Senibina UI/UX",
    "Penyebar Reka Bentuk", "Penasihat Keselamatan", "Juru Audit", "Penjaga Kualiti",
    "Perancang Strategik", "Analis Risiko", "Pemikir Kritis", "Pemeriksa Kualiti",
    "Pereka Grafik", "Penulis Kandungan", "Jurubahasa", "Penyusun Data",
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Agent Registry"
        title="34 AI Agents. One Platform."
        subtitle="10 core agents orchestrate 24 specialists — each with distinct roles, providers, and models optimized for enterprise tasks."
      />

      <div className="mb-10 lg:mb-14 max-w-5xl mx-auto">
        <div className="flex items-center gap-2 mb-4 lg:mb-6 justify-center">
          <HiOutlineCpuChip className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} />
          <h3 className="text-lg lg:text-xl font-semibold">10 Core Agents</h3>
        </div>
        <div className="grid gap-3 lg:gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
          {coreAgents.map((a, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.05 + i * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="group relative rounded-xl lg:rounded-2xl border border-white/10 bg-white/[0.02] p-4 lg:p-5 text-center hover:border-cyan-400/20 transition-colors"
            >
              <div className={`w-10 h-10 lg:w-12 lg:h-12 rounded-full bg-gradient-to-br ${colorMap[a.color]} mx-auto mb-2 lg:mb-3 flex items-center justify-center text-xs lg:text-sm font-bold text-white shadow-lg`}>
                {a.name.substring(0, 2).toUpperCase()}
              </div>
              <h4 className="text-xs lg:text-sm font-bold mb-0.5">{a.name}</h4>
              <p className="text-[9px] lg:text-[10px] text-neutral-500 mb-2">{a.role}</p>
              <span className="inline-block rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[8px] lg:text-[10px] text-neutral-400">{a.model}</span>
            </motion.div>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center gap-2 mb-4 lg:mb-6 justify-center">
          <HiOutlineUsers className={ICON_CLASS} style={{ fontSize: ICON_SIZE }} />
          <h3 className="text-lg lg:text-xl font-semibold">24 Specialist Agents</h3>
        </div>
        <div className="grid gap-2 lg:gap-3 grid-cols-3 sm:grid-cols-4 lg:grid-cols-8">
          {specialists.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.3 + i * 0.03 }}
              whileHover={{ scale: 1.05, borderColor: "rgba(34,211,238,0.3)" }}
              className="rounded-lg border border-white/5 bg-white/[0.02] p-2 lg:p-3 text-center text-[9px] lg:text-xs text-neutral-400 hover:border-cyan-400/20 transition-colors"
            >
              {s}
            </motion.div>
          ))}
        </div>
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Core Engine ───────────────────────────────────────────────

function CoreSection() {
  const features = [
    { icon: <HiOutlineCog6Tooth className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "5-Layer Memory (M0-M4)", desc: "Eternal cognitive memory with heat-based retention, cross-session continuity, and intelligent forgetting." },
    { icon: <HiOutlineBolt className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "40+ Specialized Skills", desc: "Optimized skill templates for token efficiency, from code generation to security auditing." },
    { icon: <HiOutlineArrowPath className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Intelligent Routing", desc: "Gateway routes across 5 LLM providers with automatic failover, load balancing, and cost optimization." },
    { icon: <HiOutlineShieldCheck className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Enterprise Security", desc: "Prompt injection defense, command sanitization, complete audit trails, and secrets management." },
    { icon: <HiOutlineChartBar className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Performance Module", desc: "LRUCache (40-60% latency reduction), ConnectionPool (30% faster), RequestDeduplicator (30% cost savings)." },
    { icon: <HiOutlineGlobeAlt className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "5 LLM Providers", desc: "Anthropic, OpenAI, Gemini, Ollama (8 local models), and ZAI — all integrated with intelligent fallback." },
  ];

  const providers = [
    { name: "Anthropic", models: "Claude 4, Sonnet, Opus", gradient: "from-green-400 to-emerald-500" },
    { name: "OpenAI", models: "GPT-4o, GPT-4, 3.5", gradient: "from-blue-400 to-cyan-500" },
    { name: "Ollama", models: "8 Local Models", gradient: "from-purple-400 to-pink-500" },
    { name: "Gemini", models: "Pro, Flash", gradient: "from-yellow-400 to-orange-500" },
    { name: "ZAI", models: "Zhipu Models", gradient: "from-red-400 to-rose-500" },
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Core Engine"
        title="The Brain Behind JEBAT"
        subtitle="Jebat Core is the platform backbone — the multi-agent orchestration engine that powers the entire ecosystem."
      />
      <div className="space-y-8 lg:space-y-10">
        {/* Features Grid */}
        <div className="grid gap-4 lg:gap-5 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 + i * 0.08 }}
              className="flex items-start gap-4 p-5 rounded-xl border border-white/5 bg-white/[0.02] hover:border-cyan-400/20 transition-colors"
            >
              <div className="mt-0.5">{f.icon}</div>
              <div>
                <h3 className="font-semibold text-sm lg:text-base mb-1">{f.title}</h3>
                <p className="text-xs lg:text-sm text-neutral-500 leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Providers + Terminal Row */}
        <div className="grid gap-4 lg:gap-6 grid-cols-1 md:grid-cols-2">
          {/* Provider Network */}
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6">
            <div className="text-center mb-5">
              <div className="flex items-center justify-center gap-2 mb-2">
                <HiOutlineGlobeAlt className="w-5 h-5 text-cyan-400" />
                <h3 className="text-lg font-bold">Provider Network</h3>
              </div>
              <p className="text-sm text-neutral-400">Intelligent routing across 5 LLM backends</p>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {providers.map((p, i) => (
                <motion.div
                  key={i}
                  whileHover={{ scale: 1.05 }}
                  className="rounded-xl border border-white/10 bg-white/[0.02] p-3 text-center"
                >
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${p.gradient} mx-auto mb-2 flex items-center justify-center text-sm font-bold text-white`}>
                    {p.name.substring(0, 2).toUpperCase()}
                  </div>
                  <h4 className="text-xs font-semibold mb-1">{p.name}</h4>
                  <p className="text-[10px] text-neutral-500">{p.models}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Terminal */}
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6">
            <div className="flex items-center gap-2 mb-4">
              <HiOutlineCommandLine className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-bold">System Health</h3>
            </div>
            <div className="rounded-lg bg-black/30 border border-white/5 p-4 font-mono text-sm">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-cyan-400">$</span> <span className="text-white">npx jebat-core doctor</span>
              </div>
              <div className="text-neutral-500 space-y-2">
                <div className="flex items-center gap-2"><HiOutlineCheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" /> Memory system: 5-layer (M0-M4)</div>
                <div className="flex items-center gap-2"><HiOutlineCheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" /> Skills: 40+ installed</div>
                <div className="flex items-center gap-2"><HiOutlineCheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" /> Gateway: 5 providers connected</div>
                <div className="flex items-center gap-2 text-emerald-400 font-semibold"><HiOutlineCheckCircle className="w-4 h-4 flex-shrink-0" /> System healthy</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Orchestration ─────────────────────────────────────────────

function OrchestrationSection() {
  const modes = [
    { icon: <HiOutlineChatBubbleLeftRight className="w-6 h-6 lg:w-7 lg:h-7 text-white" />, title: "Multi-Agent Debate", desc: "Advocate vs Critic → Rebuttals → Confidence → Moderator conclusion. Research-backed MAD paradigm.", rounds: "4 Rounds", time: "~2-5 min", gradient: "from-cyan-400 to-blue-500" },
    { icon: <HiOutlineUsers className="w-6 h-6 lg:w-7 lg:h-7 text-white" />, title: "Consensus Building", desc: "Share perspectives → Find agreement → Final synthesized conclusion. Collaborative approach.", rounds: "3 Rounds", time: "~1.5-3 min", gradient: "from-emerald-400 to-teal-500" },
    { icon: <HiOutlineArrowPath className="w-6 h-6 lg:w-7 lg:h-7 text-white" />, title: "Sequential Chain", desc: "Model 1 starts → Model 2 builds → Model 1 refines. Linear knowledge building.", rounds: "3 Steps", time: "~1-2 min", gradient: "from-blue-400 to-indigo-500" },
    { icon: <HiOutlineBolt className="w-6 h-6 lg:w-7 lg:h-7 text-white" />, title: "Parallel Analysis", desc: "Both analyze independently → Comparison table with synthesis. Unbiased perspectives.", rounds: "2 Phases", time: "~1-2 min", gradient: "from-yellow-400 to-orange-500" },
    { icon: <HiOutlineBuildingOffice className="w-6 h-6 lg:w-7 lg:h-7 text-white" />, title: "Hierarchical Review", desc: "Senior delegates → Junior completes → Senior reviews. Quality control pattern.", rounds: "3 Steps", time: "~1.5-3 min", gradient: "from-purple-400 to-pink-500" },
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Orchestration Engine"
        title="5 Research-Backed Orchestration Modes"
        subtitle="Based on AutoGen, ChatDev 2.0, and MAD Paradigm papers. Choose the right pattern for your use case."
      />
      <div className="grid gap-4 lg:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
        {modes.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 + i * 0.1 }}
            whileHover={{ y: -4 }}
            className="group relative rounded-2xl lg:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 lg:p-8 hover:border-cyan-400/20 transition-colors"
          >
            <div className="flex items-start justify-between mb-4 lg:mb-6">
              <div className={`w-12 h-12 lg:w-14 lg:h-14 rounded-xl lg:rounded-2xl bg-gradient-to-br ${m.gradient} flex items-center justify-center shadow-lg`}>
                {m.icon}
              </div>
              <div className="text-right">
                <div className="text-[10px] lg:text-xs text-neutral-500">{m.rounds}</div>
                <div className="text-[10px] lg:text-xs text-neutral-600">{m.time}</div>
              </div>
            </div>
            <h3 className="text-lg lg:text-xl font-bold mb-2 lg:mb-3">{m.title}</h3>
            <p className="text-sm lg:text-base text-neutral-400 leading-relaxed">{m.desc}</p>
            <a href="/chat" className="mt-4 lg:mt-6 inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition text-xs lg:text-sm font-medium">
              Try in Chat <HiOutlineArrowRight className="w-3.5 h-3.5" />
            </a>
          </motion.div>
        ))}
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Why Choose Us ─────────────────────────────────────────────

function WhySection() {
  const reasons = [
    { icon: <HiOutlineLockClosed className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "100% Self-Hosted", desc: "Your data never leaves your infrastructure. No cloud, no third-party, no vendor lock-in. Complete sovereignty over your AI.", metric: "0 data breaches", stat: "Privacy-first" },
    { icon: <HiOutlineBolt className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "40-60% Faster", desc: "LRUCache, ConnectionPool, RequestDeduplicator, and SmartRouter — enterprise performance optimizations out of the box.", metric: "<2s local avg", stat: "Latency" },
    { icon: <HiOutlineCog6Tooth className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Eternal Memory", desc: "5-layer cognitive memory (M0-M4) with heat-based retention. JEBAT remembers across sessions — unlike ChatGPT or Claude.", metric: "M0-M4 layers", stat: "Memory" },
    { icon: <HiOutlineCpuChip className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "34 AI Agents", desc: "10 core agents orchestrate 24 specialists. From security audits to code review, research to customer service — all automated.", metric: "10 + 24", stat: "Agents" },
    { icon: <HiOutlineGlobeAlt className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "5 LLM Providers", desc: "Anthropic, OpenAI, Gemini, Ollama (8 local models), and ZAI. Intelligent routing with automatic failover.", metric: "5 backends", stat: "Providers" },
    { icon: <HiOutlineBanknotes className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Cost Effective", desc: "Run 8 local LLMs for free. Intelligent routing minimizes cloud API costs. No subscription fees, no per-token charges.", metric: "$0 local", stat: "Cost" },
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Why JEBAT"
        title="Why Enterprise Teams Choose JEBAT"
        subtitle="Built for organizations that demand privacy, performance, and control over their AI infrastructure."
      />
      <div className="grid gap-4 lg:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto">
        {reasons.map((r, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 + i * 0.1 }}
            whileHover={{ y: -4 }}
            className="group relative rounded-2xl lg:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 lg:p-8 hover:border-cyan-400/20 transition-colors"
          >
            <div className="flex items-start justify-between mb-4 lg:mb-6">
              <div className="mt-0.5">{r.icon}</div>
              <div className="text-right">
                <div className="text-lg lg:text-xl font-bold text-cyan-400">{r.metric}</div>
                <div className="text-[10px] lg:text-xs text-neutral-500">{r.stat}</div>
              </div>
            </div>
            <h3 className="text-lg lg:text-xl font-bold mb-2 lg:mb-3">{r.title}</h3>
            <p className="text-sm lg:text-base text-neutral-400 leading-relaxed">{r.desc}</p>
          </motion.div>
        ))}
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Live Chat ─────────────────────────────────────────────────

function ChatSection() {
  const features = [
    { icon: <HiOutlineChatBubbleLeftRight className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Real-Time AI Chat", desc: "Chat with 8 local LLMs or cloud providers. Markdown rendering with tables, code blocks, and headers." },
    { icon: <HiOutlineArrowPath className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "5 Orchestration Modes", desc: "Switch between Debate, Consensus, Sequential, Parallel, and Hierarchical modes directly in chat." },
    { icon: <HiOutlineUsers className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Personalized Experience", desc: "Onboarding flow remembers your name, role, and use cases. AI tailors responses to you." },
    { icon: <HiOutlineCog6Tooth className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Session Persistence", desc: "Conversations survive page refresh. Settings remembered. Last conversation auto-loads on return." },
    { icon: <HiOutlineBolt className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "Warm Model Button", desc: "Pre-load large models (9.6GB) before chatting. Smart retry logic handles model loading gracefully." },
    { icon: <HiOutlineKey className={ICON_CLASS} style={{ fontSize: "1.5rem" }} />, title: "BYOK Support", desc: "Bring Your Own Key for OpenAI and Anthropic. Or use 8 free local models — no API key needed." },
  ];

  return (
    <SectionContent>
      <SectionHeader
        badge="Live Demo"
        title="Experience JEBAT Chat"
        subtitle="Try our live chat interface with 8 local LLMs, 5 orchestration modes, and enterprise-grade features. No signup, no API key required."
      />
      <div className="space-y-8 lg:space-y-10">
        {/* Features Grid */}
        <div className="grid gap-4 lg:gap-5 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 + i * 0.08 }}
              className="flex items-start gap-4 p-5 rounded-xl border border-white/5 bg-white/[0.02] hover:border-cyan-400/20 transition-colors"
            >
              <div className="mt-0.5">{f.icon}</div>
              <div>
                <h3 className="font-semibold text-sm lg:text-base mb-1">{f.title}</h3>
                <p className="text-xs lg:text-sm text-neutral-500 leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Chat Mockup + CTA */}
        <div className="flex flex-col items-center gap-6">
          {/* Chat Mockup */}
          <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6">
            <div className="rounded-xl bg-black/40 border border-white/5 overflow-hidden">
              <div className="p-4 border-b border-white/5 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-xs font-bold text-white">AI</div>
                <div>
                  <div className="text-sm font-semibold">Jebat Chat</div>
                  <div className="flex items-center gap-1.5">
                    <span className="inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400"/>
                    <span className="text-[10px] text-emerald-400">Online · 8 models ready</span>
                  </div>
                </div>
              </div>
              <div className="p-4 space-y-4">
                <div className="flex justify-end">
                  <div className="rounded-2xl rounded-br-md bg-blue-600/20 border border-blue-500/20 px-4 py-3 max-w-[80%]">
                    <p className="text-sm">Compare Python vs JavaScript for backend development</p>
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="rounded-2xl rounded-bl-md bg-white/5 border border-white/10 px-4 py-3 max-w-[85%]">
                    <p className="text-sm mb-2 font-semibold">## Python vs JavaScript: Backend</p>
                    <div className="rounded-lg bg-black/30 p-3 mb-2 font-mono text-xs overflow-x-auto">
                      <div className="text-cyan-400">| Feature | Python | JavaScript |</div>
                      <div className="text-neutral-600">|---------|--------|------------|</div>
                      <div className="text-neutral-400">| Typing | Strong | Dynamic |</div>
                      <div className="text-neutral-400">| Async | asyncio | Native |</div>
                      <div className="text-neutral-400">| ML/AI | Excellent | Growing |</div>
                    </div>
                    <p className="text-xs text-neutral-400">Python excels in AI/ML ecosystems while JavaScript dominates full-stack development...</p>
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-white/5 flex items-center gap-2">
                <div className="flex-1 rounded-lg bg-white/5 border border-white/10 px-3 py-2 text-xs text-neutral-500">Message Jebat...</div>
                <button className="rounded-full bg-cyan-400/20 p-2">
                  <HiOutlineChatBubbleLeftRight className="w-4 h-4 text-cyan-400" />
                </button>
              </div>
            </div>
          </div>

          {/* CTA */}
          <a href="/chat" className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            <HiOutlinePlay className="w-5 h-5" />
            Launch Chat Interface
            <HiOutlineArrowRight className="w-4 h-4" />
          </a>
        </div>
      </div>
    </SectionContent>
  );
}

// ─── SECTION: CTA ───────────────────────────────────────────────────────

function CTASection() {
  return (
    <SectionContent>
      <div className="text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl lg:rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5 p-8 lg:p-12 max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 lg:w-20 lg:h-20 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20 mx-auto mb-4 lg:mb-6">
            <HiOutlineRocketLaunch className="w-8 h-8 lg:w-10 lg:h-10 text-white" />
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-4 lg:mb-6">Ready to Own Your AI?</h2>
          <p className="text-neutral-400 text-base lg:text-lg mb-8 max-w-2xl mx-auto leading-relaxed">
            Download JEBAT today and experience the future of self-hosted AI. No subscriptions, no cloud dependency, no limits. Deploy on your infrastructure in 30 seconds.
          </p>
          <div className="flex flex-wrap justify-center gap-3 lg:gap-4 mb-8">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 lg:px-8 py-3 lg:py-4 text-sm lg:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Deploy on GitHub
              <HiOutlineArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </a>
            <a href="/chat" className="rounded-full border border-white/15 px-6 lg:px-8 py-3 lg:py-4 text-sm lg:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              <HiOutlinePlay className="w-5 h-5" />
              Try Live Demo
            </a>
          </div>
          <div className="flex flex-wrap justify-center gap-4 lg:gap-6 text-xs lg:text-sm text-neutral-500">
            <span className="flex items-center gap-1.5">
              <HiOutlineCheckCircle className="w-4 h-4 text-emerald-400" />
              Free & Open Source
            </span>
            <span className="flex items-center gap-1.5">
              <HiOutlineCheckCircle className="w-4 h-4 text-emerald-400" />
              No Credit Card
            </span>
            <span className="flex items-center gap-1.5">
              <HiOutlineCheckCircle className="w-4 h-4 text-emerald-400" />
              30-Second Setup
            </span>
          </div>
        </motion.div>
      </div>
    </SectionContent>
  );
}

// ─── Feature CTA Section ────────────────────────────────────────────────

interface FeatureCardData {
  icon: React.ReactNode;
  title: string;
  desc: string;
}

function FeatureCTASection({
  agentName,
  agentRole,
  agentGradient,
  agentInitials,
  badge,
  title,
  subtitle,
  features,
  primaryCta,
  secondaryCta,
  primaryHref,
  secondaryHref,
  stats,
  themeColor,
}: {
  agentName: string;
  agentRole: string;
  agentGradient: string;
  agentInitials: string;
  badge: string;
  title: string;
  subtitle: string;
  features: FeatureCardData[];
  primaryCta: string;
  secondaryCta: string;
  primaryHref: string;
  secondaryHref: string;
  stats: { value: string; label: string }[];
  themeColor: string;
}) {
  return (
    <SectionContent>
      <div className="space-y-10 lg:space-y-12">
        {/* Agent Header */}
        <div className="text-center space-y-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className={`inline-flex items-center justify-center w-16 h-16 lg:w-20 lg:h-20 rounded-full bg-gradient-to-br ${agentGradient} shadow-lg mx-auto mb-4`}
          >
            <span className="text-2xl lg:text-3xl font-bold text-white">{agentInitials}</span>
          </motion.div>
          <div className="text-sm text-neutral-400">
            <span className={`font-semibold ${themeColor}`}>{agentName}</span> · {agentRole}
          </div>
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300">
            <span className="inline-flex h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"/>
            {badge}
          </span>
        </div>

        {/* Title & Subtitle */}
        <div className="text-center">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-4 lg:mb-6">{title}</h2>
          <p className="max-w-3xl mx-auto text-neutral-400 text-base lg:text-lg leading-relaxed">{subtitle}</p>
        </div>

        {/* Feature Cards */}
        <div className="grid gap-4 lg:gap-5 grid-cols-1 md:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 + i * 0.1 }}
              whileHover={{ y: -4 }}
              className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 hover:border-cyan-400/20 transition-colors"
            >
              <div className="mb-4">{f.icon}</div>
              <h3 className="font-semibold text-base mb-2">{f.title}</h3>
              <p className="text-sm text-neutral-500 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-wrap justify-center gap-3 lg:gap-4">
          <a href={primaryHref} className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            {primaryCta}
            <HiOutlineArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </a>
          <a href={secondaryHref} className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
            {secondaryCta}
            <HiOutlineArrowRight className="w-4 h-4" />
          </a>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap justify-center gap-6 lg:gap-10">
          {stats.map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-xl lg:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{s.value}</div>
              <div className="text-xs text-neutral-500">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </SectionContent>
  );
}

// ─── Updated Sections ───────────────────────────────────────────────────

function AgentCTASection() {
  return (
    <FeatureCTASection
      agentName="Tukang"
      agentRole="Development & Engineering"
      agentGradient="from-purple-400 to-pink-500"
      agentInitials="TK"
      badge="Jebat Agent"
      title="Deploy Your AI Workspace in 30 Seconds"
      subtitle="Jebat Agent — Setup wizard, IDE integration, 8 local LLMs, channel automation, and OpenClaw migration. Everything you need to run AI on your infrastructure."
      features={[
        { icon: <HiOutlineWrenchScrewdriver className="w-6 h-6 text-purple-400" />, title: "30-Second Setup", desc: "One command deploys your entire AI workspace with skills, config, and IDE integration." },
        { icon: <HiOutlineCodeBracket className="w-6 h-6 text-purple-400" />, title: "IDE Integration", desc: "VS Code, Zed, Cursor, Claude Desktop, Gemini CLI — works with your favorite editor." },
        { icon: <HiOutlineCpuChip className="w-6 h-6 text-purple-400" />, title: "8 Local LLMs", desc: "Gemma 4, Qwen2.5, Hermes3, Phi-3, Llama 3.1, Mistral, CodeLlama, TinyLlama." },
      ]}
      primaryCta="Deploy Now"
      secondaryCta="View on npm"
      primaryHref="/agent/"
      secondaryHref="https://www.npmjs.com/package/jebat-agent"
      stats={[
        { value: "30s", label: "Setup Time" },
        { value: "40+", label: "Skills" },
        { value: "8", label: "Local LLMs" },
      ]}
      themeColor="text-purple-400"
    />
  );
}

function PortalCTASection() {
  return (
    <FeatureCTASection
      agentName="Panglima"
      agentRole="Orchestration & Command"
      agentGradient="from-cyan-400 to-blue-500"
      agentInitials="PL"
      badge="Enterprise Portal"
      title="Real-Time AI Command Center"
      subtitle="Monitor all 34 agents, track usage analytics, measure performance metrics, and manage your AI team from a single dashboard."
      features={[
        { icon: <HiOutlineChartBar className="w-6 h-6 text-cyan-400" />, title: "Live Analytics", desc: "Real-time usage tracking, token consumption, response times, and cost analysis." },
        { icon: <HiOutlineUsers className="w-6 h-6 text-cyan-400" />, title: "Agent Monitoring", desc: "Status, health, and activity for all 10 core agents and 24 specialists." },
        { icon: <HiOutlineCog6Tooth className="w-6 h-6 text-cyan-400" />, title: "Performance Metrics", desc: "Latency, cache hit rates, throughput, and system health indicators." },
      ]}
      primaryCta="Open Portal"
      secondaryCta="Explore Features"
      primaryHref="/portal/"
      secondaryHref="/agent/"
      stats={[
        { value: "10", label: "Core Agents" },
        { value: "24", label: "Specialists" },
        { value: "Live", label: "Analytics" },
      ]}
      themeColor="text-cyan-400"
    />
  );
}

function ChatCTASection() {
  return (
    <FeatureCTASection
      agentName="Hikmat"
      agentRole="Memory & Knowledge"
      agentGradient="from-pink-400 to-rose-500"
      agentInitials="HK"
      badge="Live Chat"
      title="AI Chat That Remembers You"
      subtitle="5 orchestration modes, 8 local LLMs, markdown rendering with tables, session persistence, and personalized onboarding that adapts to your role."
      features={[
        { icon: <HiOutlineArrowPath className="w-6 h-6 text-pink-400" />, title: "5 Orchestration Modes", desc: "Debate, Consensus, Sequential, Parallel, Hierarchical — switch modes instantly." },
        { icon: <HiOutlineDocumentText className="w-6 h-6 text-pink-400" />, title: "Markdown Rendering", desc: "Tables, code blocks, headers, lists — beautiful AI responses with full formatting." },
        { icon: <HiOutlineCog6Tooth className="w-6 h-6 text-pink-400" />, title: "Session Persistence", desc: "Conversations survive refresh. Settings remembered. Last chat auto-loads." },
      ]}
      primaryCta="Start Chatting"
      secondaryCta="View Features"
      primaryHref="/chat/"
      secondaryHref="/portal/"
      stats={[
        { value: "5", label: "Modes" },
        { value: "8", label: "Local LLMs" },
        { value: "∞", label: "Memory" },
      ]}
      themeColor="text-pink-400"
    />
  );
}

function GelanggangCTASection() {
  return (
    <FeatureCTASection
      agentName="Penganalisis"
      agentRole="Analytics & Insights"
      agentGradient="from-yellow-400 to-orange-500"
      agentInitials="PA"
      badge="LLM Arena"
      title="Watch AI Models Compete in Real-Time"
      subtitle="Gelanggang — the LLM-to-LLM arena where models debate, collaborate, and compete. Research-backed orchestration patterns from AutoGen and MAD Paradigm."
      features={[
        { icon: <HiOutlineChatBubbleLeftRight className="w-6 h-6 text-yellow-400" />, title: "Live Debates", desc: "Watch models argue, rebut, and reach consensus in real-time conversations." },
        { icon: <HiOutlineChartBar className="w-6 h-6 text-yellow-400" />, title: "Model Comparison", desc: "Side-by-side analysis of different models on the same topic." },
        { icon: <HiOutlineBolt className="w-6 h-6 text-yellow-400" />, title: "Research-Backed", desc: "Based on AutoGen, ChatDev 2.0, and MAD Paradigm papers." },
      ]}
      primaryCta="Enter Arena"
      secondaryCta="Learn More"
      primaryHref="/gelanggang/"
      secondaryHref="/chat/"
      stats={[
        { value: "Live", label: "Debates" },
        { value: "8", label: "Models" },
        { value: "Real", label: "Time" },
      ]}
      themeColor="text-yellow-400"
    />
  );
}

function SecurityCTASection() {
  return (
    <FeatureCTASection
      agentName="Hulubalang"
      agentRole="Security Audit & Compliance"
      agentGradient="from-red-400 to-rose-500"
      agentInitials="HB"
      badge="CyberSec Suite"
      title="Military-Grade Security Infrastructure"
      subtitle="Four-layer security: Hulubalang (audit), Pengawal (defense), Perisai (hardening), Serangan (pentest). Prompt injection defense, command sanitization, and complete audit trails."
      features={[
        { icon: <HiOutlineShieldCheck className="w-6 h-6 text-red-400" />, title: "Injection Defense", desc: "Automatic detection and blocking of prompt injection attacks." },
        { icon: <HiOutlineClipboardDocumentCheck className="w-6 h-6 text-red-400" />, title: "Complete Audit Trails", desc: "Every action logged for compliance, review, and incident response." },
        { icon: <HiOutlineKey className="w-6 h-6 text-red-400" />, title: "Secrets Management", desc: "API keys and credentials never exposed. Encrypted storage and rotation." },
      ]}
      primaryCta="View Security"
      secondaryCta="CyberSec Suite"
      primaryHref="/security/"
      secondaryHref="/portal/"
      stats={[
        { value: "4", label: "Security Tools" },
        { value: "0", label: "Breaches" },
        { value: "100%", label: "Audit" },
      ]}
      themeColor="text-red-400"
    />
  );
}

function GuidesCTASection() {
  return (
    <FeatureCTASection
      agentName="Syahbandar"
      agentRole="Operations & Infrastructure"
      agentGradient="from-blue-400 to-indigo-500"
      agentInitials="SB"
      badge="Setup Guides"
      title="Step-by-Step Deployment Guides"
      subtitle="Comprehensive documentation for IDE integration, channel setup, model deployment, migration from OpenClaw/Hermes, and production hardening."
      features={[
        { icon: <HiOutlineBookOpen className="w-6 h-6 text-blue-400" />, title: "Step-by-Step Guides", desc: "Clear instructions for every setup scenario, from beginner to advanced." },
        { icon: <HiOutlineCommandLine className="w-6 h-6 text-blue-400" />, title: "CLI Commands", desc: "Copy-paste ready commands for quick setup and automation." },
        { icon: <HiOutlineArrowPath className="w-6 h-6 text-blue-400" />, title: "Migration Paths", desc: "Seamless migration from OpenClaw and Hermes with zero downtime." },
      ]}
      primaryCta="Read Guides"
      secondaryCta="Quick Start"
      primaryHref="/guides/"
      secondaryHref="https://github.com/nusabyte-my/jebat-core"
      stats={[
        { value: "10+", label: "Guides" },
        { value: "CLI", label: "Commands" },
        { value: "Zero", label: "Downtime" },
      ]}
      themeColor="text-blue-400"
    />
  );
}

// ─── Section Order ──────────────────────────────────────────────────────

const SECTION_COMPONENTS = [
  HeroSection, AgentCTASection, PortalCTASection, ChatCTASection,
  GelanggangCTASection, SecurityCTASection, GuidesCTASection, CTASection,
];

// ─── Main Page ──────────────────────────────────────────────────────────

export default function LandingV2() {
  return (
    <div className="h-screen w-screen bg-[#050505] text-white overflow-x-hidden">
      <AgentNetworkBackground />
      <Navbar />
      <SideDots />

      <div className="h-screen w-screen overflow-y-auto snap-y snap-mandatory scroll-smooth">
        {SECTIONS.map((sectionId, i) => {
          const Component = SECTION_COMPONENTS[i];
          return (
            <motion.section
              key={sectionId}
              id={`section-${sectionId}`}
              className="h-screen w-screen snap-start"
            >
              <Component />
            </motion.section>
          );
        })}
      </div>
    </div>
  );
}
