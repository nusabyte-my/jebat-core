"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";

// ─── Sections Data ──────────────────────────────────────────────────────

const SECTIONS = [
  {
    id: "hero",
    title: "The AI Platform That",
    highlights: [
      { text: "Remembers", gradient: "from-cyan-400 to-blue-500" },
      { text: "Collaborates", gradient: "from-blue-400 to-purple-500" },
      { text: "Protects", gradient: "from-purple-400 to-pink-500" },
    ],
    subtitle: "JEBAT combines eternal memory, multi-agent orchestration across 8 local LLMs, and enterprise security into one self-hosted platform.",
    badge: "Self-Hosted · Enterprise-Ready · 100% Private",
    stats: [
      { value: "10", label: "Core Agents", icon: "🤖" },
      { value: "24", label: "Specialists", icon: "⚡" },
      { value: "8", label: "Local LLMs", icon: "🧠" },
      { value: "5", label: "Orchestration", icon: "🎭" },
      { value: "100%", label: "Self-Hosted", icon: "🔒" },
    ],
  },
  {
    id: "features",
    title: "Everything You Need",
    subtitle: "Enterprise-grade AI platform built for privacy and performance.",
    badge: "Features",
    features: [
      { icon: "⚖️", title: "5 Orchestration Modes", desc: "Debate, Consensus, Sequential, Parallel, Hierarchical — research-backed multi-agent patterns", color: "from-cyan-400 to-blue-500" },
      { icon: "🤖", title: "10 Core Agents", desc: "Panglima, Tukang, Hulubalang, Pengawal, and more — each with specialized roles", color: "from-purple-400 to-pink-500" },
      { icon: "👥", title: "24 Specialists", desc: "From Tukang Web to Khidmat Pelanggan — domain-specific AI agents", color: "from-emerald-400 to-teal-500" },
      { icon: "🧠", title: "8 Local LLMs", desc: "Gemma 4, Qwen2.5, Hermes3, Phi-3 — run AI on your hardware, no cloud needed", color: "from-orange-400 to-red-500" },
      { icon: "📝", title: "Markdown Rendering", desc: "Tables, code blocks, headers, lists — beautiful AI responses with full formatting", color: "from-yellow-400 to-orange-500" },
      { icon: "👤", title: "User Onboarding", desc: "Personalized AI that remembers your name, role, and use cases", color: "from-pink-400 to-rose-500" },
    ],
  },
  {
    id: "agents",
    title: "10 Specialized Agents",
    subtitle: "Each agent has a distinct role, provider, and model optimized for their task.",
    badge: "Core Agents",
    agents: [
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
    ],
  },
  {
    id: "security",
    title: "Enterprise-Grade Protection",
    subtitle: "Built-in security from day one. No add-ons, no extra cost.",
    badge: "Security",
    features: [
      { icon: "🛡️", title: "Prompt Injection Defense", desc: "Automatic detection and blocking of malicious prompts" },
      { icon: "🔍", title: "Command Sanitization", desc: "All inputs validated and sanitized before execution" },
      { icon: "📋", title: "Complete Audit Trails", desc: "Every action logged for compliance and review" },
      { icon: "🔐", title: "Secrets Management", desc: "API keys and credentials never exposed" },
      { icon: "🏠", title: "100% Self-Hosted", desc: "Your data never leaves your infrastructure" },
    ],
  },
  {
    id: "cta",
    title: "Ready to Own Your AI?",
    subtitle: "Download JEBAT today and experience the future of self-hosted AI. No subscriptions, no cloud dependency, no limits.",
  },
];

const COLOR_MAP: Record<string, string> = {
  cyan: "from-cyan-400 to-blue-500",
  purple: "from-purple-400 to-pink-500",
  red: "from-red-400 to-rose-500",
  orange: "from-orange-400 to-amber-500",
  emerald: "from-emerald-400 to-teal-500",
  blue: "from-blue-400 to-indigo-500",
  indigo: "from-indigo-400 to-purple-500",
  pink: "from-pink-400 to-rose-500",
  yellow: "from-yellow-400 to-orange-500",
  teal: "from-teal-400 to-emerald-500",
};

// ─── Components ─────────────────────────────────────────────────────────

function Navbar({ activeSection, onNavigate }: { activeSection: number; onNavigate: (i: number) => void }) {
  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/80 backdrop-blur-xl border-b border-white/5"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 md:px-6 py-3">
        <a href="/" className="flex items-center gap-2 md:gap-3">
          <div className="flex items-center justify-center w-7 h-7 md:w-9 md:h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="flex items-center gap-1 md:gap-2">
            <span className="text-base md:text-lg font-bold tracking-tight">JEBAT</span>
            <span className="hidden sm:inline text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
          </div>
        </a>

        {/* Desktop nav dots */}
        <div className="hidden md:flex items-center gap-1">
          {SECTIONS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => onNavigate(i)}
              className={`px-3 py-2 text-sm transition rounded-lg ${
                activeSection === i ? "text-white bg-white/10" : "text-neutral-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {s.id.charAt(0).toUpperCase() + s.id.slice(1)}
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

function SlideIndicator({ activeSection, onNavigate }: { activeSection: number; onNavigate: (i: number) => void }) {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-[#050505]/80 backdrop-blur-xl border border-white/10 rounded-full px-4 py-2">
      {SECTIONS.map((s, i) => (
        <button
          key={s.id}
          onClick={() => onNavigate(i)}
          className="group flex items-center gap-2"
        >
          <div
            className={`w-2 h-2 md:w-2.5 md:h-2.5 rounded-full transition-all duration-300 ${
              activeSection === i
                ? "bg-cyan-400 w-6 md:w-8"
                : "bg-neutral-600 group-hover:bg-neutral-400"
            }`}
          />
          <span className={`hidden md:block text-[10px] transition-colors ${activeSection === i ? "text-cyan-400" : "text-neutral-500"}`}>
            {s.id}
          </span>
        </button>
      ))}
    </div>
  );
}

function SwipeHint() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const t = setTimeout(() => setVisible(false), 4000);
    return () => clearTimeout(t);
  }, []);
  if (!visible) return null;
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 z-10 flex flex-col items-center gap-2 text-neutral-500"
    >
      <motion.div
        animate={{ x: [0, 8, 0] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/></svg>
      </motion.div>
      <span className="text-xs">Swipe or scroll</span>
    </motion.div>
  );
}

// ─── Section Components ─────────────────────────────────────────────────

function HeroSection() {
  const section = SECTIONS[0];
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-20 md:py-0">
      <div className="max-w-5xl mx-auto text-center space-y-8">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300"
        >
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
          {section.badge}
        </motion.div>

        {/* Headline */}
        <div>
          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-4"
          >
            {section.title}
          </motion.h1>
          <div className="flex flex-wrap justify-center gap-x-3 gap-y-2">
            {(section.highlights || []).map((h, i) => (
              <motion.span
                key={i}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5 + i * 0.15 }}
                className={`text-3xl md:text-5xl lg:text-6xl font-bold bg-gradient-to-r ${h.gradient} bg-clip-text text-transparent`}
              >
                {h.text}
              </motion.span>
            ))}
          </div>
        </div>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="max-w-2xl mx-auto text-base md:text-lg text-neutral-400 leading-relaxed"
        >
          {section.subtitle}
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="flex flex-wrap justify-center gap-3 md:gap-4"
        >
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            Download JEBAT
          </a>
          <a href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
            Try Chat Demo
          </a>
          <a href="/gelanggang" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white hover:bg-white/10 transition">
            🏛️ Watch Gelanggang
          </a>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 max-w-3xl mx-auto pt-4"
        >
          {(section.stats || []).map((stat, i) => (
            <div key={i} className="rounded-2xl border border-white/5 bg-white/[0.02] p-3 md:p-4">
              <div className="text-xl md:text-2xl mb-1">{stat.icon}</div>
              <div className="text-xl md:text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-[10px] md:text-xs text-neutral-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}

function FeaturesSection() {
  const section = SECTIONS[1];
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-16 md:py-0">
      <div className="max-w-7xl mx-auto w-full">
        <div className="text-center mb-10 md:mb-14">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">{section.badge}</span>
          <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">{section.title}</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">{section.subtitle}</p>
        </div>
        <div className="grid gap-4 md:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {(section.features || []).map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              whileHover={{ y: -4, borderColor: "rgba(34,211,238,0.3)" }}
              className="group relative rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8"
            >
              <div className={`w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-gradient-to-br ${(f as any).color || ''} flex items-center justify-center mb-4 md:mb-6 text-xl md:text-2xl shadow-lg`}>
                {f.icon}
              </div>
              <h3 className="text-lg md:text-xl font-bold mb-2 md:mb-3">{f.title}</h3>
              <p className="text-sm md:text-base text-neutral-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AgentsSection() {
  const section = SECTIONS[2];
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-16 md:py-0 overflow-y-auto">
      <div className="max-w-7xl mx-auto w-full">
        <div className="text-center mb-10 md:mb-14">
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">{section.badge}</span>
          <h2 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">{section.title}</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-base md:text-lg">{section.subtitle}</p>
        </div>
        <div className="grid gap-3 md:gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          {(section.agents || []).map((a, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="group relative rounded-xl md:rounded-2xl border border-white/10 bg-white/[0.02] p-4 md:p-6 text-center"
            >
              <div className={`w-10 h-10 md:w-14 md:h-14 rounded-full bg-gradient-to-br ${COLOR_MAP[a.color]} mx-auto mb-3 md:mb-4 flex items-center justify-center text-sm md:text-lg font-bold text-white shadow-lg`}>
                {a.name.substring(0, 2).toUpperCase()}
              </div>
              <h3 className="text-sm md:text-base font-bold mb-1">{a.name}</h3>
              <p className="text-[10px] md:text-xs text-neutral-500 mb-2">{a.role}</p>
              <span className="inline-block rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[9px] md:text-[10px] text-neutral-400">{a.model}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SecuritySection() {
  const section = SECTIONS[3];
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-16 md:py-0 overflow-y-auto">
      <div className="max-w-7xl mx-auto w-full">
        <div className="grid gap-8 md:gap-12 lg:grid-cols-2 items-center">
          <div>
            <span className="inline-block rounded-full border border-red-400/20 bg-red-400/5 px-4 py-1.5 text-sm text-red-300 mb-4">{section.badge}</span>
            <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6">{section.title}</h2>
            <p className="text-neutral-400 text-base md:text-lg mb-6 md:mb-8">{section.subtitle}</p>
            <div className="space-y-3 md:space-y-4">
              {(section.features || []).map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex items-start gap-3 md:gap-4 p-3 md:p-4 rounded-xl border border-white/5 bg-white/[0.02]"
                >
                  <span className="text-xl md:text-2xl flex-shrink-0">{s.icon}</span>
                  <div>
                    <h3 className="font-semibold text-sm md:text-base mb-0.5 md:mb-1">{s.title}</h3>
                    <p className="text-xs md:text-sm text-neutral-500">{s.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-6 md:p-8">
            <div className="text-center">
              <div className="text-5xl md:text-7xl mb-4">🔒</div>
              <h3 className="text-xl md:text-2xl font-bold mb-2">Zero Cloud Dependency</h3>
              <p className="text-sm md:text-base text-neutral-400 mb-6">Everything runs on your hardware</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 md:gap-3">
                {["Anthropic", "OpenAI", "Ollama", "Gemini", "ZAI", "Local"].map((p, i) => (
                  <div key={i} className="rounded-lg bg-white/5 border border-white/5 px-3 py-2 text-xs md:text-sm text-neutral-400 text-center">
                    {p}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CTASection() {
  const section = SECTIONS[4];
  return (
    <div className="w-full h-full flex items-center justify-center px-4 md:px-8 py-16 md:py-0">
      <div className="max-w-4xl mx-auto w-full text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl md:rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5 p-8 md:p-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold mb-4 md:mb-6">{section.title}</h2>
          <p className="text-neutral-400 text-base md:text-lg mb-8 max-w-2xl mx-auto">{section.subtitle}</p>
          <div className="flex flex-wrap justify-center gap-3 md:gap-4">
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Download Now
            </a>
            <a href="/chat" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Try Live Demo
            </a>
            <a href="/portal" className="rounded-full border border-white/15 px-6 md:px-8 py-3 md:py-4 text-sm md:text-base font-medium text-white flex items-center gap-2 hover:bg-white/10 transition">
              Enterprise Portal
            </a>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

const SECTION_COMPONENTS = [HeroSection, FeaturesSection, AgentsSection, SecuritySection, CTASection];

// ─── Main Page ──────────────────────────────────────────────────────────

export default function LandingV2() {
  const [active, setActive] = useState(0);
  const [direction, setDirection] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 300, damping: 30 });

  const goTo = useCallback((index: number) => {
    if (index < 0 || index >= SECTIONS.length) return;
    setDirection(index > active ? 1 : -1);
    setActive(index);
    x.set(0);
  }, [active, x]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown") goTo(active + 1);
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") goTo(active - 1);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [active, goTo]);

  // Wheel navigation
  useEffect(() => {
    let wheelTimeout: NodeJS.Timeout;
    const handler = (e: WheelEvent) => {
      clearTimeout(wheelTimeout);
      wheelTimeout = setTimeout(() => {
        if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
          if (e.deltaX > 30) goTo(active + 1);
          else if (e.deltaX < -30) goTo(active - 1);
        } else {
          if (e.deltaY > 30) goTo(active + 1);
          else if (e.deltaY < -30) goTo(active - 1);
        }
      }, 50);
    };
    window.addEventListener("wheel", handler, { passive: true });
    return () => {
      window.removeEventListener("wheel", handler);
      clearTimeout(wheelTimeout);
    };
  }, [active, goTo]);

  const SectionComponent = SECTION_COMPONENTS[active];

  return (
    <div className="h-screen w-screen bg-[#050505] text-white overflow-hidden select-none" ref={containerRef}>
      <Navbar activeSection={active} onNavigate={goTo} />
      <SlideIndicator activeSection={active} onNavigate={goTo} />
      
      {/* Main swipeable area */}
      <motion.div
        className="h-full w-full"
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.15}
        onDragStart={() => setIsDragging(true)}
        onDragEnd={(e, info) => {
          setIsDragging(false);
          const threshold = window.innerWidth * 0.15;
          if (info.offset.x < -threshold) goTo(active + 1);
          else if (info.offset.x > threshold) goTo(active - 1);
          else x.set(0);
        }}
        style={{ x: springX }}
        animate={{ x: isDragging ? undefined : 0 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      >
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={active}
            custom={direction}
            initial={{ opacity: 0, x: direction * 60 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -60 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="h-full w-full"
          >
            <SectionComponent />
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* Swipe hint (auto-hides) */}
      {active < SECTIONS.length - 1 && <SwipeHint />}

      {/* Section number */}
      <div className="fixed top-20 right-4 md:right-8 z-40 text-neutral-600 text-xs md:text-sm font-mono">
        <span className="text-white font-bold">{String(active + 1).padStart(2, "0")}</span>
        <span> / {String(SECTIONS.length).padStart(2, "0")}</span>
      </div>
    </div>
  );
}
