"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";

// ─── Data ───────────────────────────────────────────────────────────────

const SECTIONS = [
  "hero", "platform", "agents", "core", "orchestration", "why", "chat", "cta",
] as const;

type SectionId = (typeof SECTIONS)[number];

const SECTION_LABELS: Record<SectionId, string> = {
  hero: "Home",
  platform: "Platform",
  agents: "Agents",
  core: "Core Engine",
  orchestration: "Orchestration",
  why: "Why JEBAT",
  chat: "Live Demo",
  cta: "Get Started",
};

// ─── Background Animation ───────────────────────────────────────────────

function AgentNetworkBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Array<{ x: number; y: number; vx: number; vy: number; size: number; label: string }>>([]);
  const mouseRef = useRef({ x: 0, y: 0 });

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
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      size: 2 + Math.random() * 3,
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

      // Update nodes
      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;

        // Mouse attraction
        const dx = mouseRef.current.x - n.x;
        const dy = mouseRef.current.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          n.vx += dx * 0.00005;
          n.vy += dy * 0.00005;
        }

        // Damping
        n.vx *= 0.999;
        n.vy *= 0.999;
      });

      // Draw connections
      const connectionDist = 180;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < connectionDist) {
            const opacity = (1 - dist / connectionDist) * 0.15;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = `rgba(59, 130, 246, ${opacity})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      // Draw mouse connections
      nodes.forEach((n) => {
        const dx = mouseRef.current.x - n.x;
        const dy = mouseRef.current.y - n.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 250) {
          const opacity = (1 - dist / 250) * 0.3;
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(mouseRef.current.x, mouseRef.current.y);
          ctx.strokeStyle = `rgba(34, 211, 238, ${opacity})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });

      // Draw nodes
      nodes.forEach((n) => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.6)";
        ctx.fill();

        // Glow
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.size + 4, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(59, 130, 246, 0.1)";
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
      style={{ opacity: 0.6 }}
    />
  );
}

// ─── Section Wrapper ────────────────────────────────────────────────────

function SectionContent({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-16 md:py-0 overflow-y-auto">
      <div className="max-w-7xl mx-auto w-full relative z-10">
        {children}
      </div>
    </div>
  );
}

// ─── Navbar ─────────────────────────────────────────────────────────────

function Navbar({ activeSection, onNavigate }: { activeSection: number; onNavigate: (i: number) => void }) {
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/70 backdrop-blur-xl border-b border-white/5"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 md:px-6 py-3">
        <a href="/" className="flex items-center gap-2 md:gap-3 group">
          <motion.div
            className="flex items-center justify-center w-7 h-7 md:w-9 md:h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20"
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </motion.div>
          <div className="flex items-center gap-1 md:gap-2">
            <span className="text-base md:text-lg font-bold tracking-tight">JEBAT</span>
            <span className="hidden sm:inline text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
          </div>
        </a>

        <div className="hidden lg:flex items-center gap-1">
          {SECTIONS.map((s, i) => (
            <button
              key={s}
              onClick={() => onNavigate(i)}
              className={`px-3 py-2 text-xs md:text-sm transition rounded-lg ${
                activeSection === i ? "text-white bg-white/10" : "text-neutral-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {SECTION_LABELS[s]}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          <a href="/chat" className="hidden sm:inline-flex items-center gap-1 md:gap-2 rounded-full border border-white/10 bg-white/5 px-3 md:px-4 py-1.5 md:py-2 text-xs md:text-sm text-white hover:bg-white/10 transition">
            Try Chat
          </a>
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-3 md:px-5 py-1.5 md:py-2 text-xs md:text-sm font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
            Get Started
          </a>
        </div>
      </div>
    </motion.nav>
  );
}

// ─── Slide Navigation ───────────────────────────────────────────────────

function SlideIndicator({ activeSection, onNavigate }: { activeSection: number; onNavigate: (i: number) => void }) {
  return (
    <div className="fixed right-4 md:right-6 top-1/2 -translate-y-1/2 z-50 flex flex-col items-center gap-3">
      {SECTIONS.map((s, i) => (
        <button
          key={s}
          onClick={() => onNavigate(i)}
          className="group flex flex-col items-center gap-1"
        >
          <motion.div
            className={`w-2 h-2 md:w-2.5 md:h-2.5 rounded-full transition-all duration-300 ${
              activeSection === i
                ? "bg-cyan-400 scale-125"
                : "bg-neutral-600 group-hover:bg-neutral-400"
            }`}
            whileHover={{ scale: 1.5 }}
          />
          <span className={`hidden xl:block text-[9px] transition-colors ${activeSection === i ? "text-cyan-400" : "text-neutral-600"} whitespace-nowrap`}>
            {SECTION_LABELS[s]}
          </span>
        </button>
      ))}
    </div>
  );
}

function SectionCounter({ active }: { active: number }) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-[#050505]/80 backdrop-blur-xl border border-white/10 rounded-full px-4 py-2">
      {SECTIONS.map((s, i) => (
        <button
          key={s}
          onClick={() => {
            // Scroll to section
            const el = document.getElementById(`section-${s}`);
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          className="group flex items-center gap-1"
        >
          <motion.div
            className={`w-2 h-2 md:w-2.5 md:h-2.5 rounded-full transition-all duration-300 ${
              active === i
                ? "bg-cyan-400 w-6 md:w-8"
                : "bg-neutral-600 group-hover:bg-neutral-400"
            }`}
          />
          <span className={`hidden md:block text-[10px] transition-colors ${active === i ? "text-cyan-400" : "text-neutral-500"}`}>
            {SECTION_LABELS[s]}
          </span>
        </button>
      ))}
    </div>
  );
}

// ─── SECTION: Hero ──────────────────────────────────────────────────────

function HeroSection() {
  return (
    <SectionContent>
      <div className="text-center space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300"
        >
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
          Enterprise AI Platform · Self-Hosted · Zero Cloud Dependency
        </motion.div>

        <div>
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-4"
          >
            The AI Platform That{" "}
            <span className="block">
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.6 }}
                className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent"
              >
                Remembers,
              </motion.span>{" "}
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.75 }}
                className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent"
              >
                Collaborates,
              </motion.span>{" "}
              <motion.span
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 }}
                className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent"
              >
                Protects.
              </motion.span>
            </span>
          </motion.h1>
        </div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="max-w-3xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed"
        >
          JEBAT is the enterprise-grade, self-hosted AI orchestration platform that combines{" "}
          <strong className="text-white">eternal memory</strong>,{" "}
          <strong className="text-white">multi-agent collaboration</strong>, and{" "}
          <strong className="text-white">military-grade security</strong> into one unified system.
          Deploy on your infrastructure. Own your data. No cloud dependency.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="flex flex-wrap justify-center gap-3 md:gap-4"
        >
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            Deploy JEBAT
          </a>
          <a href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
            Try Live Chat
          </a>
          <a href="/portal" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white hover:bg-white/10 transition">
            Enterprise Portal
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-3xl mx-auto pt-4"
        >
          {[
            { value: "10", label: "Core Agents", icon: "🤖" },
            { value: "24", label: "Specialists", icon: "⚡" },
            { value: "5", label: "Orchestration Modes", icon: "🎭" },
            { value: "100%", label: "Self-Hosted", icon: "🔒" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              whileHover={{ scale: 1.05, borderColor: "rgba(34,211,238,0.3)" }}
              className="rounded-2xl border border-white/5 bg-white/[0.02] p-3 md:p-4"
            >
              <div className="text-xl md:text-2xl mb-1">{stat.icon}</div>
              <div className="text-xl md:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-[10px] md:text-xs text-neutral-500">{stat.label}</div>
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
      icon: "🤖",
      title: "Jebat Agent",
      subtitle: "Your Unified AI Workspace",
      desc: "Deploy your entire AI workspace in 30 seconds. IDE integration, 8 local LLMs, channel setup, and migration from OpenClaw/Hermes — all automated.",
      features: ["30-second setup wizard", "8 local LLM deployment", "IDE integration (VS Code, Zed, Cursor)", "Channel setup (Telegram, Discord, WhatsApp)", "OpenClaw/Hermes migration"],
      color: "from-cyan-400 to-blue-500",
      cta: "View Agent Docs",
      link: "/agent",
    },
    {
      icon: "🏗️",
      title: "Jebat Core",
      subtitle: "The Platform Backbone",
      desc: "5-layer cognitive memory, 40+ specialized skills, multi-agent orchestration, and the gateway that routes across 5 LLM providers with intelligent failover.",
      features: ["M0-M4 eternal memory system", "40+ optimized skills", "Multi-agent orchestration", "CyberSec scanning & hardening", "Gateway with provider routing"],
      color: "from-purple-400 to-pink-500",
      cta: "Explore Core",
      link: "/portal",
    },
  ];

  return (
    <SectionContent>
      <div className="text-center mb-10 md:mb-14">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Platform Architecture</span>
        <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">Two Pillars. One Platform.</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">JEBAT is built on two powerful components that work together seamlessly to deliver enterprise-grade AI capabilities.</p>
      </div>
      <div className="grid gap-6 md:gap-8 grid-cols-1 md:grid-cols-2">
        {pillars.map((p, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.15 }}
            whileHover={{ y: -4, borderColor: "rgba(34,211,238,0.2)" }}
            className="group relative rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8"
          >
            <div className="absolute top-4 md:top-6 right-4 md:right-6">
              <span className={`rounded-full bg-gradient-to-r ${p.color} text-white px-3 py-1 text-xs font-medium`}>{p.title}</span>
            </div>
            <div className={`w-12 h-12 md:w-14 md:h-14 rounded-xl md:rounded-2xl bg-gradient-to-br ${p.color} flex items-center justify-center mb-4 md:mb-6 text-2xl md:text-3xl shadow-lg`}>
              {p.icon}
            </div>
            <h3 className="text-xl md:text-2xl font-bold mb-1 md:mb-2">{p.title}</h3>
            <p className="text-sm md:text-base text-cyan-400 mb-3 md:mb-4">{p.subtitle}</p>
            <p className="text-sm md:text-base text-neutral-400 leading-relaxed mb-4 md:mb-6">{p.desc}</p>
            <div className="space-y-2 md:space-y-3 mb-6">
              {p.features.map((f, j) => (
                <div key={j} className="flex items-start gap-2 md:gap-3 text-xs md:text-sm text-neutral-300">
                  <svg className="w-4 h-4 md:w-5 md:h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
                  {f}
                </div>
              ))}
            </div>
            <a href={p.link} className={`inline-flex items-center gap-2 rounded-full bg-gradient-to-r ${p.color} px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition`}>
              {p.cta} →
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
    { name: "Panglima", role: "Orchestration & Command", model: "Claude 4", desc: "Directs all agents, manages workflows", color: "cyan" },
    { name: "Tukang", role: "Development & Engineering", model: "Qwen Coder", desc: "Builds, codes, and engineers solutions", color: "purple" },
    { name: "Hulubalang", role: "Security Audit & Compliance", model: "Hermes Sec", desc: "Audits, scans, and ensures compliance", color: "red" },
    { name: "Pengawal", role: "CyberSec & Threat Defense", model: "Hermes Sec", desc: "Defends against cyber threats", color: "orange" },
    { name: "Pawang", role: "Research & Intelligence", model: "Claude 4", desc: "Deep research and market intelligence", color: "emerald" },
    { name: "Syahbandar", role: "Operations & Infrastructure", model: "Qwen Coder", desc: "Manages ops, CI/CD, and deployment", color: "blue" },
    { name: "Bendahara", role: "Database & Data Management", model: "Qwen Coder", desc: "Manages databases and data pipelines", color: "indigo" },
    { name: "Hikmat", role: "Memory & Knowledge", model: "Claude 4", desc: "5-layer eternal memory system", color: "pink" },
    { name: "Penganalisis", role: "Analytics & Insights", model: "Claude 4", desc: "Business analytics and reporting", color: "yellow" },
    { name: "Penyemak", role: "QA & Code Review", model: "Claude 4", desc: "Quality assurance and code review", color: "teal" },
  ];

  const colorMap: Record<string, string> = {
    cyan: "from-cyan-400 to-blue-500", purple: "from-purple-400 to-pink-500", red: "from-red-400 to-rose-500",
    orange: "from-orange-400 to-amber-500", emerald: "from-emerald-400 to-teal-500", blue: "from-blue-400 to-indigo-500",
    indigo: "from-indigo-400 to-purple-500", pink: "from-pink-400 to-rose-500", yellow: "from-yellow-400 to-orange-500",
    teal: "from-teal-400 to-emerald-500",
  };

  const specialists = [
    "Tukang Web", "Pembina Aplikasi", "Khidmat Pelanggan", "Senibina Antara Muka",
    "Penyebar Reka Bentuk", "Penasihat Keselamatan", "Juru Audit", "Penjaga Kualiti",
    "Perancang Strategik", "Analis Risiko", "Pemikir Kritis", "Pemeriksa Kualiti",
    "Pereka Grafik", "Penulis Kandungan", "Jurubahasa", "Penyusun Data",
  ];

  return (
    <SectionContent>
      <div className="text-center mb-10 md:mb-14">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Agent Registry</span>
        <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">34 AI Agents. One Platform.</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">10 core agents orchestrate 24 specialists — each with distinct roles, providers, and models optimized for enterprise tasks.</p>
      </div>

      {/* Core Agents */}
      <div className="mb-10 md:mb-14">
        <h3 className="text-lg md:text-xl font-semibold mb-4 md:mb-6 text-center">10 Core Agents</h3>
        <div className="grid gap-3 md:gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-5">
          {coreAgents.map((a, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="group relative rounded-xl md:rounded-2xl border border-white/10 bg-white/[0.02] p-4 md:p-5 text-center"
            >
              <div className={`w-10 h-10 md:w-12 md:h-12 rounded-full bg-gradient-to-br ${colorMap[a.color]} mx-auto mb-2 md:mb-3 flex items-center justify-center text-xs md:text-sm font-bold text-white shadow-lg`}>
                {a.name.substring(0, 2).toUpperCase()}
              </div>
              <h4 className="text-xs md:text-sm font-bold mb-0.5">{a.name}</h4>
              <p className="text-[9px] md:text-[10px] text-neutral-500 mb-1">{a.role}</p>
              <p className="text-[8px] md:text-[9px] text-neutral-600 mb-2 hidden md:block">{a.desc}</p>
              <span className="inline-block rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[8px] md:text-[10px] text-neutral-400">{a.model}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Specialists */}
      <div>
        <h3 className="text-lg md:text-xl font-semibold mb-4 md:mb-6 text-center">24 Specialist Agents</h3>
        <div className="grid gap-2 md:gap-3 grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
          {specialists.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 + i * 0.03 }}
              whileHover={{ scale: 1.05, borderColor: "rgba(34,211,238,0.3)" }}
              className="rounded-lg border border-white/5 bg-white/[0.02] p-2 md:p-3 text-center text-[9px] md:text-xs text-neutral-400"
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
    { icon: "🧠", title: "5-Layer Memory (M0-M4)", desc: "Eternal cognitive memory with heat-based retention, cross-session continuity, and intelligent forgetting." },
    { icon: "⚡", title: "40+ Specialized Skills", desc: "Optimized skill templates for token efficiency, from code generation to security auditing." },
    { icon: "🔄", title: "Intelligent Routing", desc: "Gateway routes across 5 LLM providers with automatic failover, load balancing, and cost optimization." },
    { icon: "🔐", title: "Enterprise Security", desc: "Prompt injection defense, command sanitization, complete audit trails, and secrets management." },
    { icon: "📊", title: "Performance Module", desc: "LRUCache (40-60% latency reduction), ConnectionPool (30% faster), RequestDeduplicator (30% cost savings)." },
    { icon: "🌐", title: "5 LLM Providers", desc: "Anthropic, OpenAI, Gemini, Ollama (8 local models), and ZAI — all integrated with intelligent fallback." },
  ];

  return (
    <SectionContent>
      <div className="grid gap-8 md:gap-12 lg:grid-cols-2 items-center">
        <div>
          <span className="inline-block rounded-full border border-purple-400/20 bg-purple-400/5 px-4 py-1.5 text-sm text-purple-300 mb-4">Core Engine</span>
          <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6">The Brain Behind JEBAT</h2>
          <p className="text-neutral-400 text-base md:text-lg mb-8 leading-relaxed">
            Jebat Core is the platform backbone — the multi-agent orchestration engine that powers the entire ecosystem. It manages memory, routes requests, enforces security, and coordinates 34 agents seamlessly.
          </p>
          <div className="space-y-3 md:space-y-4">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className="flex items-start gap-3 md:gap-4 p-3 md:p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:border-purple-400/20 transition"
              >
                <span className="text-xl md:text-2xl flex-shrink-0">{f.icon}</span>
                <div>
                  <h3 className="font-semibold text-sm md:text-base mb-0.5 md:mb-1">{f.title}</h3>
                  <p className="text-xs md:text-sm text-neutral-500">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
        <div className="rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
          <div className="text-center mb-6">
            <h3 className="text-xl md:text-2xl font-bold mb-2">Provider Network</h3>
            <p className="text-sm text-neutral-400">Intelligent routing across 5 LLM backends</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4 mb-6">
            {[
              { name: "Anthropic", models: "Claude 4, Sonnet, Opus", color: "from-green-400 to-emerald-500" },
              { name: "OpenAI", models: "GPT-4o, GPT-4, 3.5", color: "from-blue-400 to-cyan-500" },
              { name: "Ollama", models: "8 Local Models", color: "from-purple-400 to-pink-500" },
              { name: "Gemini", models: "Pro, Flash", color: "from-yellow-400 to-orange-500" },
              { name: "ZAI", models: "Zhipu Models", color: "from-red-400 to-rose-500" },
            ].map((p, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.05 }}
                className="rounded-xl border border-white/10 bg-white/[0.02] p-3 md:p-4 text-center"
              >
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${p.color} mx-auto mb-2 flex items-center justify-center text-sm font-bold text-white`}>
                  {p.name.substring(0, 2).toUpperCase()}
                </div>
                <h4 className="text-xs md:text-sm font-semibold mb-1">{p.name}</h4>
                <p className="text-[9px] md:text-[10px] text-neutral-500">{p.models}</p>
              </motion.div>
            ))}
          </div>
          <div className="rounded-lg bg-black/30 border border-white/5 p-3 md:p-4 font-mono text-xs md:text-sm">
            <span className="text-cyan-400">$</span> <span className="text-white">npx jebat-core doctor</span>
            <div className="text-neutral-500 mt-2">✓ Memory system: 5-layer (M0-M4)</div>
            <div className="text-neutral-500">✓ Skills: 40+ installed</div>
            <div className="text-neutral-500">✓ Gateway: 5 providers connected</div>
            <div className="text-emerald-400">✓ System healthy</div>
          </div>
        </div>
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Orchestration ─────────────────────────────────────────────

function OrchestrationSection() {
  const modes = [
    { icon: "⚖️", title: "Multi-Agent Debate", desc: "Advocate vs Critic → Rebuttals → Confidence → Moderator conclusion. Research-backed MAD paradigm.", rounds: "4 Rounds", time: "~2-5 min", color: "from-cyan-400 to-blue-500" },
    { icon: "🤝", title: "Consensus Building", desc: "Share perspectives → Find agreement → Final synthesized conclusion. Collaborative approach.", rounds: "3 Rounds", time: "~1.5-3 min", color: "from-emerald-400 to-teal-500" },
    { icon: "🔗", title: "Sequential Chain", desc: "Model 1 starts → Model 2 builds → Model 1 refines. Linear knowledge building.", rounds: "3 Steps", time: "~1-2 min", color: "from-blue-400 to-indigo-500" },
    { icon: "⚡", title: "Parallel Analysis", desc: "Both analyze independently → Comparison table with synthesis. Unbiased perspectives.", rounds: "2 Phases", time: "~1-2 min", color: "from-yellow-400 to-orange-500" },
    { icon: "🏛️", title: "Hierarchical Review", desc: "Senior delegates → Junior completes → Senior reviews. Quality control pattern.", rounds: "3 Steps", time: "~1.5-3 min", color: "from-purple-400 to-pink-500" },
  ];

  return (
    <SectionContent>
      <div className="text-center mb-10 md:mb-14">
        <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Orchestration Engine</span>
        <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">5 Research-Backed Orchestration Modes</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">Based on AutoGen, ChatDev 2.0, and MAD Paradigm papers. Choose the right pattern for your use case.</p>
      </div>
      <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
        {modes.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.1 }}
            whileHover={{ y: -4, borderColor: "rgba(34,211,238,0.2)" }}
            className="group relative rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8"
          >
            <div className="flex items-start justify-between mb-4 md:mb-6">
              <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-gradient-to-br ${m.color} flex items-center justify-center text-xl md:text-2xl shadow-lg`}>
                {m.icon}
              </div>
              <div className="text-right">
                <div className="text-[10px] md:text-xs text-neutral-500">{m.rounds}</div>
                <div className="text-[10px] md:text-xs text-neutral-600">{m.time}</div>
              </div>
            </div>
            <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3">{m.title}</h3>
            <p className="text-sm md:text-base text-neutral-400 leading-relaxed">{m.desc}</p>
            <a href="/chat" className="mt-4 md:mt-6 inline-flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition text-xs md:text-sm font-medium">
              Try in Chat →
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
    { icon: "🔒", title: "100% Self-Hosted", desc: "Your data never leaves your infrastructure. No cloud, no third-party, no vendor lock-in. Complete sovereignty over your AI.", metric: "0 data breaches", stat: "Privacy-first" },
    { icon: "⚡", title: "40-60% Faster Responses", desc: "LRUCache, ConnectionPool, RequestDeduplicator, and SmartRouter — enterprise performance optimizations out of the box.", metric: "<2s local avg", stat: "Latency" },
    { icon: "🧠", title: "Eternal Memory", desc: "5-layer cognitive memory (M0-M4) with heat-based retention. JEBAT remembers conversations across sessions — unlike ChatGPT or Claude.", metric: "M0-M4 layers", stat: "Memory" },
    { icon: "🤖", title: "34 AI Agents", desc: "10 core agents orchestrate 24 specialists. From security audits to code review, research to customer service — all automated.", metric: "10 + 24", stat: "Agents" },
    { icon: "🌐", title: "5 LLM Providers", desc: "Anthropic, OpenAI, Gemini, Ollama (8 local models), and ZAI. Intelligent routing with automatic failover.", metric: "5 backends", stat: "Providers" },
    { icon: "💰", title: "Cost Effective", desc: "Run 8 local LLMs for free. Intelligent routing minimizes cloud API costs. No subscription fees, no per-token charges.", metric: "$0 local", stat: "Cost" },
  ];

  return (
    <SectionContent>
      <div className="text-center mb-10 md:mb-14">
        <span className="inline-block rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-4">Why JEBAT</span>
        <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">Why Enterprise Teams Choose JEBAT</h2>
        <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">Built for organizations that demand privacy, performance, and control over their AI infrastructure.</p>
      </div>
      <div className="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {reasons.map((r, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.1 }}
            whileHover={{ y: -4, borderColor: "rgba(34,211,238,0.2)" }}
            className="group relative rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8"
          >
            <div className="flex items-start justify-between mb-4 md:mb-6">
              <span className="text-2xl md:text-3xl">{r.icon}</span>
              <div className="text-right">
                <div className="text-lg md:text-xl font-bold text-cyan-400">{r.metric}</div>
                <div className="text-[10px] md:text-xs text-neutral-500">{r.stat}</div>
              </div>
            </div>
            <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3">{r.title}</h3>
            <p className="text-sm md:text-base text-neutral-400 leading-relaxed">{r.desc}</p>
          </motion.div>
        ))}
      </div>
    </SectionContent>
  );
}

// ─── SECTION: Live Chat ─────────────────────────────────────────────────

function ChatSection() {
  const features = [
    { icon: "💬", title: "Real-Time AI Chat", desc: "Chat with 8 local LLMs or cloud providers. Markdown rendering with tables, code blocks, and headers." },
    { icon: "🎭", title: "5 Orchestration Modes", desc: "Switch between Debate, Consensus, Sequential, Parallel, and Hierarchical modes directly in chat." },
    { icon: "👤", title: "Personalized Experience", desc: "Onboarding flow remembers your name, role, and use cases. AI tailors responses to you." },
    { icon: "💾", title: "Session Persistence", desc: "Conversations survive page refresh. Settings remembered. Last conversation auto-loads on return." },
    { icon: "⚡", title: "Warm Model Button", desc: "Pre-load large models (9.6GB) before chatting. Smart retry logic handles model loading gracefully." },
    { icon: "🔐", title: "BYOK Support", desc: "Bring Your Own Key for OpenAI and Anthropic. Or use 8 free local models — no API key needed." },
  ];

  return (
    <SectionContent>
      <div className="grid gap-8 md:gap-12 lg:grid-cols-2 items-center">
        <div>
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Live Demo</span>
          <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6">Experience JEBAT Chat</h2>
          <p className="text-neutral-400 text-base md:text-lg mb-8 leading-relaxed">
            Try our live chat interface with 8 local LLMs, 5 orchestration modes, and enterprise-grade features. No signup, no API key required.
          </p>
          <div className="space-y-3 md:space-y-4 mb-8">
            {features.map((f, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className="flex items-start gap-3 md:gap-4 p-3 md:p-4 rounded-xl border border-white/5 bg-white/[0.02]"
              >
                <span className="text-xl md:text-2xl flex-shrink-0">{f.icon}</span>
                <div>
                  <h3 className="font-semibold text-sm md:text-base mb-0.5 md:mb-1">{f.title}</h3>
                  <p className="text-xs md:text-sm text-neutral-500">{f.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
          <a href="/chat" className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
            Launch Chat Interface →
          </a>
        </div>
        <div className="rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
          <div className="rounded-xl bg-black/40 border border-white/5 overflow-hidden">
            {/* Chat mockup */}
            <div className="p-3 md:p-4 border-b border-white/5 flex items-center gap-2 md:gap-3">
              <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-[10px] md:text-xs font-bold text-white">AI</div>
              <div>
                <div className="text-xs md:text-sm font-semibold">Jebat Chat</div>
                <div className="text-[9px] md:text-[10px] text-emerald-400">● Online · 8 models ready</div>
              </div>
            </div>
            <div className="p-3 md:p-4 space-y-3 md:space-y-4">
              <div className="flex justify-end">
                <div className="rounded-2xl rounded-br-md bg-blue-600/20 border border-blue-500/20 px-3 md:px-4 py-2 md:py-3 max-w-[80%]">
                  <p className="text-xs md:text-sm">Compare Python vs JavaScript for backend development</p>
                </div>
              </div>
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-md bg-white/5 border border-white/10 px-3 md:px-4 py-2 md:py-3 max-w-[85%]">
                  <p className="text-xs md:text-sm mb-2">## Python vs JavaScript: Backend Comparison</p>
                  <div className="rounded-lg bg-black/30 p-2 md:p-3 mb-2 font-mono text-[10px] md:text-xs overflow-x-auto">
                    <div className="text-cyan-400">| Feature | Python | JavaScript |</div>
                    <div className="text-neutral-500">|---------|--------|------------|</div>
                    <div className="text-neutral-400">| Typing | Strong | Dynamic |</div>
                    <div className="text-neutral-400">| Async | asyncio | Native |</div>
                    <div className="text-neutral-400">| ML/AI | Excellent | Growing |</div>
                  </div>
                  <p className="text-xs text-neutral-400">Python excels in AI/ML ecosystems while JavaScript dominates full-stack development...</p>
                </div>
              </div>
            </div>
            <div className="p-3 md:p-4 border-t border-white/5 flex items-center gap-2">
              <input readOnly placeholder="Message Jebat..." className="flex-1 bg-transparent text-xs md:text-sm text-neutral-400 outline-none" />
              <button className="rounded-full bg-cyan-400/20 p-1.5 md:p-2">
                <svg className="w-3 h-3 md:w-4 md:h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg>
              </button>
            </div>
          </div>
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
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5 p-8 md:p-16"
        >
          <div className="text-5xl md:text-7xl mb-4 md:mb-6">⚔️</div>
          <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6">Ready to Own Your AI?</h2>
          <p className="text-neutral-400 text-base md:text-lg mb-8 max-w-2xl mx-auto leading-relaxed">
            Download JEBAT today and experience the future of self-hosted AI. No subscriptions, no cloud dependency, no limits. Deploy on your infrastructure in 30 seconds.
          </p>
          <div className="flex flex-wrap justify-center gap-3 md:gap-4 mb-8">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20 hover:from-cyan-300 hover:to-blue-400 transition">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Deploy on GitHub
            </a>
            <a href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Live Demo
            </a>
          </div>
          <div className="flex flex-wrap justify-center gap-4 md:gap-6 text-xs md:text-sm text-neutral-500">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
              Free & Open Source
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
              No Credit Card
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7"/></svg>
              30-Second Setup
            </span>
          </div>
        </motion.div>
      </div>
    </SectionContent>
  );
}

const SECTION_COMPONENTS = [
  HeroSection, PlatformSection, AgentsSection, CoreSection,
  OrchestrationSection, WhySection, ChatSection, CTASection,
];

// ─── Main Page ──────────────────────────────────────────────────────────

export default function LandingV2() {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div className="h-screen w-screen bg-[#050505] text-white overflow-x-hidden" ref={containerRef}>
      <AgentNetworkBackground />
      <Navbar activeSection={0} onNavigate={() => {}} />
      <SlideIndicator activeSection={0} onNavigate={() => {}} />

      <div className="h-screen w-screen overflow-y-auto snap-y snap-mandatory scroll-smooth">
        {SECTIONS.map((sectionId, i) => {
          const Component = SECTION_COMPONENTS[i];
          return (
            <motion.div
              key={sectionId}
              id={`section-${sectionId}`}
              className="h-screen w-screen snap-start flex items-center justify-center"
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 0.6 }}
            >
              <Component />
            </motion.div>
          );
        })}
      </div>

      <SectionCounter active={0} />
    </div>
  );
}
