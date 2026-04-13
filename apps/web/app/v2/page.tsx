"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, useScroll, useTransform, useSpring, useInView, AnimatePresence } from "framer-motion";

// ─── Hooks ──────────────────────────────────────────────────────────────

function useMousePosition() {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const handler = (e: MouseEvent) => setPos({ x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight });
    window.addEventListener("mousemove", handler);
    return () => window.removeEventListener("mousemove", handler);
  }, []);
  return pos;
}

// ─── Section Wrapper ────────────────────────────────────────────────────

function Section({ children, className = "", id = "" }: { children: React.ReactNode; className?: string; id?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  return (
    <section ref={ref} id={id} className={`min-h-screen flex items-center justify-center relative ${className}`}>
      <motion.div
        initial={{ opacity: 0, y: 80 }}
        animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 80 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="w-full"
      >
        {children}
      </motion.div>
    </section>
  );
}

// ─── Floating Particles ─────────────────────────────────────────────────

function Particles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {Array.from({ length: 30 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full bg-cyan-400/20"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.6, 0.2],
          }}
          transition={{
            duration: 3 + Math.random() * 4,
            repeat: Infinity,
            delay: Math.random() * 3,
          }}
        />
      ))}
    </div>
  );
}

// ─── Navbar ─────────────────────────────────────────────────────────────

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const mouse = useMousePosition();
  
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrolled ? "bg-[#050505]/90 backdrop-blur-xl border-b border-white/5" : "bg-transparent"
      }`}
      style={{
        x: (mouse.x - 0.5) * -10,
      }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <a href="/" className="flex items-center gap-3 group">
          <motion.div
            className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 shadow-lg shadow-cyan-500/20"
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </motion.div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight">JEBAT</span>
            <span className="text-[10px] font-medium text-cyan-400/80 border border-cyan-400/20 rounded-full px-2 py-0.5">v3.0</span>
          </div>
        </a>
        <div className="hidden md:flex items-center gap-1 text-sm">
          {["Features", "Agents", "Security", "Chat", "Portal"].map(link => (
            <a key={link} href={`#${link.toLowerCase()}`} className="px-3 py-2 text-neutral-400 hover:text-white transition rounded-lg hover:bg-white/5">
              {link}
            </a>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <a href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 transition">
            Try Chat
          </a>
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-5 py-2 text-sm font-semibold text-black hover:from-cyan-300 hover:to-blue-400 transition shadow-lg shadow-cyan-500/20">
            Get Started
          </a>
        </div>
      </div>
    </motion.nav>
  );
}

// ─── Hero Section ───────────────────────────────────────────────────────

function Hero() {
  const mouse = useMousePosition();
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 0.5], [0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <motion.section
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ y, opacity }}
    >
      {/* Mouse-following gradient */}
      <motion.div
        className="absolute pointer-events-none"
        style={{
          left: `${mouse.x * 100}%`,
          top: `${mouse.y * 100}%`,
          x: "-50%",
          y: "-50%",
          width: 600,
          height: 600,
          background: "radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)",
        }}
      />
      
      <Particles />
      
      {/* Grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_70%)]" />

      <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 md:pt-32 md:pb-24 text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-8"
        >
          <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>
          Self-Hosted · Enterprise-Ready · 100% Private
        </motion.div>

        {/* Headline with staggered animation */}
        <h1 className="text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl leading-[1.05] mb-6">
          {["The AI Platform That", "Remembers", "Collaborates", "Protects"].map((text, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 + i * 0.15, ease: [0.16, 1, 0.3, 1] }}
              className={`block ${
                i === 1 ? "bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent" :
                i === 2 ? "bg-gradient-to-r from-blue-400 via-purple-400 to-pink-500 bg-clip-text text-transparent" :
                i === 3 ? "bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent" :
                "text-white"
              } ${i === 0 ? "mb-2" : ""}`}
            >
              {text}
            </motion.span>
          ))}
        </h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="max-w-3xl mx-auto text-lg md:text-xl leading-8 text-neutral-400 mb-8"
        >
          JEBAT combines <strong className="text-white">eternal memory</strong>,{" "}
          <strong className="text-white">multi-agent orchestration</strong> across 8 local LLMs, and{" "}
          <strong className="text-white">enterprise security</strong> into one self-hosted platform.
          <br className="hidden md:block"/>
          Download, install, and own your AI — no cloud dependency.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1 }}
          className="flex flex-wrap justify-center gap-4"
        >
          <motion.a
            href="https://github.com/nusabyte-my/jebat-core"
            target="_blank"
            rel="noopener noreferrer"
            className="group rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
            Download JEBAT
            <svg className="w-4 h-4 transition group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
          </motion.a>
          <motion.a
            href="/chat"
            className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white flex items-center gap-2"
            whileHover={{ scale: 1.05, backgroundColor: "rgba(255,255,255,0.1)" }}
            whileTap={{ scale: 0.98 }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
            Try Chat Demo
          </motion.a>
        </motion.div>

        {/* Trust Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 1.2 }}
          className="pt-12 grid grid-cols-2 md:grid-cols-5 gap-6 max-w-4xl mx-auto"
        >
          {[
            { value: "10", label: "Core Agents", icon: "🤖" },
            { value: "24", label: "Specialists", icon: "⚡" },
            { value: "8", label: "Local LLMs", icon: "🧠" },
            { value: "5", label: "Orchestration Modes", icon: "🎭" },
            { value: "100%", label: "Self-Hosted", icon: "🔒" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              className="rounded-2xl border border-white/5 bg-white/[0.02] p-4"
              whileHover={{ borderColor: "rgba(34,211,238,0.3)", scale: 1.05 }}
            >
              <div className="text-2xl mb-2">{stat.icon}</div>
              <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{stat.value}</div>
              <div className="text-xs text-neutral-500">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          className="absolute bottom-8 left-1/2 -translate-x-1/2"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="flex flex-col items-center gap-2 text-neutral-500">
            <span className="text-xs">Scroll to explore</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}

// ─── Features Section ───────────────────────────────────────────────────

function Features() {
  const features = [
    { icon: "⚖️", title: "5 Orchestration Modes", desc: "Debate, Consensus, Sequential, Parallel, Hierarchical — research-backed multi-agent patterns", color: "from-cyan-400 to-blue-500" },
    { icon: "🤖", title: "10 Core Agents", desc: "Panglima, Tukang, Hulubalang, Pengawal, and more — each with specialized roles", color: "from-purple-400 to-pink-500" },
    { icon: "👥", title: "24 Specialists", desc: "From Tukang Web to Khidmat Pelanggan — domain-specific AI agents", color: "from-emerald-400 to-teal-500" },
    { icon: "🧠", title: "8 Local LLMs", desc: "Gemma 4, Qwen2.5, Hermes3, Phi-3 — run AI on your hardware, no cloud needed", color: "from-orange-400 to-red-500" },
    { icon: "📝", title: "Markdown Rendering", desc: "Tables, code blocks, headers, lists — beautiful AI responses with full formatting", color: "from-yellow-400 to-orange-500" },
    { icon: "👤", title: "User Onboarding", desc: "Personalized AI that remembers your name, role, and use cases", color: "from-pink-400 to-rose-500" },
  ];

  return (
    <Section id="features">
      <div className="mx-auto max-w-7xl px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Features</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">Everything You Need</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Enterprise-grade AI platform built for privacy and performance.</p>
        </motion.div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group relative rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-8"
              whileHover={{ y: -5, borderColor: "rgba(34,211,238,0.2)" }}
            >
              <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-6 text-2xl shadow-lg`}>
                {f.icon}
              </div>
              <h3 className="text-xl font-bold mb-3">{f.title}</h3>
              <p className="text-neutral-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </Section>
  );
}

// ─── Agents Section ─────────────────────────────────────────────────────

function Agents() {
  const agents = [
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

  return (
    <Section id="agents">
      <div className="mx-auto max-w-7xl px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block rounded-full border border-cyan-400/20 bg-cyan-400/5 px-4 py-1.5 text-sm text-cyan-300 mb-4">Core Agents</span>
          <h2 className="text-3xl font-bold md:text-5xl mb-4">10 Specialized Agents</h2>
          <p className="max-w-2xl mx-auto text-neutral-400 text-lg">Each agent has a distinct role, provider, and model optimized for their task.</p>
        </motion.div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          {agents.map((a, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="group relative rounded-2xl border border-white/10 bg-white/[0.02] p-6 text-center overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${colorMap[a.color]} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${colorMap[a.color]} mx-auto mb-4 flex items-center justify-center text-lg font-bold text-white shadow-lg`}>
                {a.name.substring(0, 2).toUpperCase()}
              </div>
              <h3 className="font-bold mb-1">{a.name}</h3>
              <p className="text-xs text-neutral-500 mb-2">{a.role}</p>
              <span className="inline-block rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-[10px] text-neutral-400">{a.model}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </Section>
  );
}

// ─── Security Section ───────────────────────────────────────────────────

function Security() {
  return (
    <Section id="security">
      <div className="mx-auto max-w-7xl px-6 py-20">
        <div className="grid gap-12 lg:grid-cols-2 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
          >
            <span className="inline-block rounded-full border border-red-400/20 bg-red-400/5 px-4 py-1.5 text-sm text-red-300 mb-4">Security</span>
            <h2 className="text-3xl font-bold md:text-5xl mb-6">Enterprise-Grade Protection</h2>
            <p className="text-neutral-400 text-lg mb-8">Built-in security from day one. No add-ons, no extra cost.</p>
            
            <div className="space-y-4">
              {[
                { icon: "🛡️", title: "Prompt Injection Defense", desc: "Automatic detection and blocking of malicious prompts" },
                { icon: "🔍", title: "Command Sanitization", desc: "All inputs validated and sanitized before execution" },
                { icon: "📋", title: "Complete Audit Trails", desc: "Every action logged for compliance and review" },
                { icon: "🔐", title: "Secrets Management", desc: "API keys and credentials never exposed" },
                { icon: "🏠", title: "100% Self-Hosted", desc: "Your data never leaves your infrastructure" },
              ].map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-start gap-4 p-4 rounded-xl border border-white/5 bg-white/[0.02]"
                >
                  <span className="text-2xl">{s.icon}</span>
                  <div>
                    <h3 className="font-semibold mb-1">{s.title}</h3>
                    <p className="text-sm text-neutral-500">{s.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.02] to-transparent p-8 aspect-square flex items-center justify-center">
              <div className="text-center">
                <div className="text-8xl mb-4">🔒</div>
                <h3 className="text-2xl font-bold mb-2">Zero Cloud Dependency</h3>
                <p className="text-neutral-400">Everything runs on your hardware</p>
                <div className="mt-6 grid grid-cols-2 gap-3">
                  {["Anthropic", "OpenAI", "Ollama", "Gemini", "ZAI", "Local"].map((p, i) => (
                    <div key={i} className="rounded-lg bg-white/5 border border-white/5 px-3 py-2 text-sm text-neutral-400">
                      {p}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </Section>
  );
}

// ─── CTA Section ────────────────────────────────────────────────────────

function CTA() {
  return (
    <Section>
      <div className="mx-auto max-w-7xl px-6 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="rounded-3xl border border-white/10 bg-gradient-to-br from-cyan-400/5 to-purple-400/5 p-12 md:p-20"
        >
          <h2 className="text-3xl font-bold md:text-5xl mb-6">Ready to Own Your AI?</h2>
          <p className="text-neutral-400 text-lg mb-8 max-w-2xl mx-auto">
            Download JEBAT today and experience the future of self-hosted AI. No subscriptions, no cloud dependency, no limits.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <motion.a
              href="https://github.com/nusabyte-my/jebat-core"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-8 py-4 text-base font-semibold text-black flex items-center gap-2 shadow-lg shadow-cyan-500/20"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.98 }}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              Download Now
            </motion.a>
            <motion.a
              href="/chat"
              className="rounded-full border border-white/15 px-8 py-4 text-base font-medium text-white flex items-center gap-2"
              whileHover={{ scale: 1.05, backgroundColor: "rgba(255,255,255,0.1)" }}
              whileTap={{ scale: 0.98 }}
            >
              Try Live Demo
            </motion.a>
          </div>
        </motion.div>
      </div>
    </Section>
  );
}

// ─── Footer ─────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="text-sm text-neutral-500">© 2026 NusaByte. Built with ❤️ in Malaysia.</span>
        </div>
        <div className="flex items-center gap-6 text-sm text-neutral-500">
          <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">GitHub</a>
          <a href="/chat" className="hover:text-white transition">Chat</a>
          <a href="/portal" className="hover:text-white transition">Portal</a>
        </div>
      </div>
    </footer>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────

export default function LandingV2() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-x-hidden">
      {/* Progress bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 to-blue-500 z-50 origin-left"
        style={{ scaleX }}
      />
      
      <Navbar />
      <Hero />
      <Features />
      <Agents />
      <Security />
      <CTA />
      <Footer />
    </div>
  );
}
