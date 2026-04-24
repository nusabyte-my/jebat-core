"use client";

import { motion } from "framer-motion";
import { 
  HiOutlineCpuChip, 
  HiOutlineServerStack, 
  HiOutlineShieldCheck, 
  HiOutlineBolt, 
  HiOutlineCube,
  HiOutlineArrowRight,
  HiOutlineLockClosed,
  HiOutlineGlobeAlt,
  HiOutlineCommandLine,
  HiOutlineAcademicCap,
  HiOutlineScale,
  HiOutlineUsers,
  HiOutlineArrowPath,
  HiOutlineEye,
  HiOutlineFingerPrint,
  HiOutlineUserCircle,
  HiOutlineCircleStack
} from "react-icons/hi2";
import Link from "next/link";
import { useState, useEffect } from "react";
import { SpecialistModal, Specialist } from "../components/SpecialistModal";

const SPECIALISTS_DATA: Specialist[] = [
  { 
    name: "Tukang", 
    role: "Development", 
    color: "purple", 
    skill: "Fullstack Engineering",
    details: ["Next.js Optimization", "Python API Design", "Rust Core Integration", "CI/CD Orchestration"],
    metrics: [{ label: "Accuracy", val: "98.4%" }, { label: "Latency", val: "1.2s" }, { label: "Trust", val: "High" }]
  },
  { 
    name: "Hulubalang", 
    role: "Sec-Audit", 
    color: "red", 
    skill: "Vulnerability Scanning",
    details: ["Pentest Automation", "Vulnerability Research", "Threat Modeling", "Kernel Hardening"],
    metrics: [{ label: "Threat Detection", val: "99.9%" }, { label: "Response", val: "0.2s" }, { label: "Level", val: "Military" }]
  },
  { 
    name: "Hikmat", 
    role: "Memory", 
    color: "pink", 
    skill: "Context Retention",
    details: ["5-Layer Consolidation", "Vector Search Opt", "Semantic Mapping", "Eternal Retention"],
    metrics: [{ label: "Recall Speed", val: "42ms" }, { label: "Consistency", val: "100%" }, { label: "Layers", val: "M0-M4" }]
  },
  { 
    name: "Bendahara", 
    role: "Database", 
    color: "orange", 
    skill: "Schema Management",
    details: ["PostgreSQL Partitioning", "Redis Edge Sync", "ACID Verification", "Data Provenance"],
    metrics: [{ label: "Transaction", val: "ACID" }, { label: "Uptime", val: "99.99%" }, { label: "Scaling", val: "Auto" }]
  },
  { 
    name: "Pawang", 
    role: "Research", 
    color: "emerald", 
    skill: "Web Extraction",
    details: ["Real-time Discovery", "Deep Web Crawling", "Source Verification", "Synthesis Engine"],
    metrics: [{ label: "Coverage", val: "Global" }, { label: "Truth Score", val: "96%" }, { label: "Depth", val: "Full" }]
  },
  { 
    name: "Syahbandar", 
    role: "Operations", 
    color: "cyan", 
    skill: "Docker & CI/CD",
    details: ["Container Swarm", "Node Auto-scaling", "Health Checks", "Traffic Routing"],
    metrics: [{ label: "Efficiency", val: "94%" }, { label: "Stability", val: "Peak" }, { label: "Nodes", val: "Managed" }]
  },
  { 
    name: "Penganalisis", 
    role: "Analytics", 
    color: "teal", 
    skill: "Token Usage Monitoring",
    details: ["Cost Projection", "Performance Profiling", "Bottle-neck ID", "Consensus Audit"],
    metrics: [{ label: "Granularity", val: "Per-Token" }, { label: "Insights", val: "Live" }, { label: "Value", val: "High" }]
  },
  { 
    name: "Penyemak", 
    role: "Verification", 
    color: "amber", 
    skill: "QA Logic Testing",
    details: ["Chain-of-Thought Audit", "Cross-model Verification", "Edge Case Detection", "Consensus Build"],
    metrics: [{ label: "Reliability", val: "99.9%" }, { label: "Coverage", val: "100%" }, { label: "Pass Rate", val: "Opt" }]
  },
];

export default function V3Landing() {
  const [scrolled, setScrolled] = useState(false);
  const [hoveredSpecialist, setHoveredSpecialist] = useState<Specialist | null>(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <main className="min-h-screen">
      <SpecialistModal 
        specialist={hoveredSpecialist} 
        isOpen={!!hoveredSpecialist} 
        onClose={() => setHoveredSpecialist(null)} 
      />
      
      {/* ─── Top Navigation ─────────────────────────────── */}
      <nav className={`fixed top-0 inset-x-0 z-[100] transition-all duration-300 border-b ${
        scrolled ? "bg-slate-950/80 backdrop-blur-xl border-slate-800 py-4" : "bg-transparent border-transparent py-6"
      }`}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-600/20">
                <HiOutlineCpuChip />
             </div>
             <span className="font-bold text-white tracking-tighter text-xl">JEBAT.ONLINE</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-[10px] font-bold uppercase tracking-widest text-slate-400">
             <Link href="/v3" className="hover:text-blue-500 transition">Command</Link>
             <Link href="/v3/portal" className="hover:text-blue-500 transition">Portal</Link>
             <Link href="/v3/chat" className="hover:text-blue-500 transition">Unified Chat</Link>
             <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" className="hover:text-blue-500 transition">Source</a>
          </div>
          <Link href="/v3" className="px-5 py-2 bg-white text-blue-600 rounded-xl text-[10px] font-bold uppercase tracking-tighter hover:bg-blue-50 transition-colors shadow-xl">
             Launch App
          </Link>
        </div>
      </nav>

      {/* ─── Hero: The Vision ─────────────────────────────── */}
      <section className="relative pt-48 pb-20 overflow-hidden border-b border-slate-800/50">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none"></div>
        
        <div className="max-w-7xl mx-auto px-6 lg:px-8 text-center space-y-10 relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-blue-500/20 bg-blue-500/5 backdrop-blur-md"
          >
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">Enterprise AI Infrastructure powered by VPS .206</span>
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-6xl lg:text-[100px] font-bold tracking-tight text-white font-heading leading-[0.95]"
          >
            Orchestrate the <br />
            <span className="bg-gradient-to-r from-blue-400 via-blue-600 to-emerald-400 bg-clip-text text-transparent">
              Autonomous Future
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-slate-400 text-lg lg:text-xl max-w-3xl mx-auto leading-relaxed"
          >
            JEBAT is a private AI platform built for sovereign data control. 
            Deploy a multi-agent runtime with persistent memory on your own infrastructure.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-wrap justify-center gap-4"
          >
            <Link href="/v3" className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-bold transition-all shadow-lg shadow-blue-600/20 flex items-center gap-3 group">
              LAUNCH COMMAND <HiOutlineArrowRight className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" className="px-8 py-4 bg-slate-900 hover:bg-slate-800 text-white border border-slate-800 rounded-2xl font-bold transition-all flex items-center gap-3">
              <HiOutlineCommandLine className="text-blue-400" /> VIEW SOURCE
            </a>
          </motion.div>
        </div>
      </section>

      {/* ─── Core Infrastructure: The 6 Pillars ─────────────────────────────── */}
      <section className="py-32 bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-20">
          <div className="text-center space-y-4">
            <h2 className="text-xs font-bold text-blue-500 uppercase tracking-[0.3em]">Core Infrastructure</h2>
            <p className="text-4xl lg:text-5xl font-bold text-white tracking-tight">Engineered for the 0.1%</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { 
                icon: <HiOutlineBolt />, 
                title: "Eternal Memory", 
                desc: "5-layer (M0-M4) memory architecture with heat-based consolidation for multi-year context preservation.",
                color: "blue"
              },
              { 
                icon: <HiOutlineAcademicCap />, 
                title: "Ultra-Think™", 
                desc: "6 reasoning modes including Strategic and Critical, delivering verified consensus through multi-agent chains.",
                color: "emerald"
              },
              { 
                icon: <HiOutlineUsers />, 
                title: "Swarm Intelligence", 
                desc: "A massive matrix of 34 specialized agents. Panglima coordinates while specialists execute domain-specific tasks.",
                color: "purple"
              },
              { 
                icon: <HiOutlineArrowPath />, 
                title: "Ultra-Loop™", 
                desc: "Perpetual execution cycles. The system continuously perceives, reflects, and optimizes in the background.",
                color: "cyan"
              },
              { 
                icon: <HiOutlineShieldCheck />, 
                title: "Sentinel Security", 
                desc: "Military-grade hardening. Automated PII masking, air-gap compatibility, and exhaustive audit trails.",
                color: "red"
              },
              { 
                icon: <HiOutlineLockClosed />, 
                title: "Data Sovereignty", 
                desc: "Absolute ownership. Primary reasoning powered by local Ollama instances on private VPS .206 mainframe.",
                color: "orange"
              }
            ].map((p, i) => (
              <motion.div 
                key={i}
                whileHover={{ y: -8 }}
                className="p-8 rounded-[40px] bg-slate-900/50 border border-slate-800/50 group hover:border-blue-500/30 hover:bg-slate-900 transition-all shadow-sm"
              >
                <div className={`w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center text-2xl text-${p.color}-500 mb-8 group-hover:scale-110 transition-transform`}>
                  {p.icon}
                </div>
                <h3 className="text-xl font-bold text-white mb-4">{p.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{p.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Swarm Matrix: The 34 Specialists ─────────────────────────────── */}
      <section className="py-24 border-y border-slate-800/50 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-16">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4 max-w-2xl">
               <h2 className="text-xs font-bold text-purple-500 uppercase tracking-[0.3em]">Agent Roles</h2>
               <p className="text-4xl lg:text-5xl font-bold text-white tracking-tight">The Orchestration Swarm</p>
               <p className="text-slate-400 leading-relaxed">
                  JEBAT dispatches specialized agents for every domain. Hover over a specialist to view detailed skillsets 
                  optimized for the <span className="text-white font-bold underline decoration-blue-500/50">VPS .206 Mainframe</span>.
               </p>
            </div>
            <div className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800 flex items-center gap-4 shadow-2xl shadow-purple-500/5">
               <div className="text-2xl font-bold text-white">34</div>
               <div className="text-[10px] font-bold text-slate-500 uppercase leading-tight">Verified <br /> Specialist Roles</div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-6 text-center">
            {SPECIALISTS_DATA.map((agent, i) => (
              <motion.div 
                key={i}
                onMouseEnter={() => setHoveredSpecialist(agent)}
                onMouseLeave={() => setHoveredSpecialist(null)}
                whileHover={{ scale: 1.02, borderColor: "rgba(59, 130, 246, 0.4)" }}
                className="p-6 rounded-[32px] bg-slate-900/30 border border-slate-800/50 hover:bg-slate-800/50 transition-all cursor-pointer relative shadow-xl"
              >
                <div className={`w-10 h-10 rounded-xl bg-slate-800 mx-auto mb-4 flex items-center justify-center text-lg font-bold text-${agent.color}-400 shadow-lg`}>
                   <HiOutlineUserCircle />
                </div>
                <h4 className="text-sm font-bold text-white uppercase tracking-tighter">{agent.name}</h4>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">{agent.role}</p>
                <div className="mt-4 flex items-center justify-center gap-2 text-[9px] font-bold text-blue-500 uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-opacity">
                   SKILL MATRIX <HiOutlineArrowRight />
                </div>
              </motion.div>
            ))}
          </div>
          <div className="text-center">
             <Link href="/v3/agents" className="text-[10px] font-bold text-slate-500 hover:text-white transition-colors uppercase tracking-[0.3em]">View full 34-agent hierarchy</Link>
          </div>
        </div>
      </section>

      {/* ─── Infrastructure Sovereignty ─────────────────────────────── */}
      <section className="py-24 relative overflow-hidden bg-slate-950">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col lg:flex-row items-center gap-20">
          <div className="flex-1 space-y-8 relative z-10">
             <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tight">Data Sovereignty <br /> by Design</h2>
             <p className="text-slate-400 text-lg leading-relaxed font-sans">
                Primary reasoning is executed on the <span className="text-white font-bold">VPS .206 Ollama Mainframe</span>. Your data remains in the private perimeter.
             </p>
             <div className="space-y-6">
                <div className="flex gap-4 p-6 rounded-[24px] bg-slate-900 border border-slate-800 shadow-xl">
                   <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 text-xl">
                      <HiOutlineGlobeAlt />
                   </div>
                   <div>
                      <h4 className="font-bold text-white mb-1">Local-First Execution</h4>
                      <p className="text-xs text-slate-500 leading-relaxed">Hardware-accelerated inference on VPS .206 using Ollama backend.</p>
                   </div>
                </div>
                <div className="flex gap-4 p-6 rounded-[24px] bg-slate-900 border border-slate-800 shadow-xl">
                   <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 text-xl">
                      <HiOutlineScale />
                   </div>
                   <div>
                      <h4 className="font-bold text-white mb-1">Persistent Storage</h4>
                      <p className="text-xs text-slate-500 leading-relaxed">PostgreSQL foundation ensures data durability and cross-agent memory consistency.</p>
                   </div>
                </div>
             </div>
          </div>

          <div className="flex-1 relative w-full flex justify-center">
             <div className="relative w-80 h-80 lg:w-96 lg:h-96">
                <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-[100px] animate-pulse"></div>
                <div className="absolute inset-4 border border-blue-500/20 rounded-full"></div>
                <div className="absolute inset-16 border border-blue-500/40 rounded-full"></div>
                
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 bg-blue-600 rounded-[32px] shadow-2xl flex flex-col items-center justify-center text-white border border-white/20">
                   <span className="text-xs font-bold uppercase tracking-tighter mb-1">VPS</span>
                   <span className="text-xl font-bold">.206</span>
                </div>

                <div className="absolute top-0 left-1/2 -translate-x-1/2 -mt-4 p-2 bg-slate-900 rounded-lg border border-slate-800 text-[9px] font-bold text-white shadow-xl uppercase tracking-widest">Ollama Mainframe</div>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 -mb-4 p-2 bg-slate-900 rounded-lg border border-slate-800 text-[9px] font-bold text-white shadow-xl uppercase tracking-widest">PostgreSQL persistent</div>
                <div className="absolute left-0 top-1/2 -translate-y-1/2 -ml-12 p-2 bg-slate-900 rounded-lg border border-slate-800 text-[9px] font-bold text-white shadow-xl uppercase tracking-widest">Redis Cache</div>
                <div className="absolute right-0 top-1/2 -translate-y-1/2 -mr-12 p-2 bg-slate-900 rounded-lg border border-slate-800 text-[9px] font-bold text-white shadow-xl uppercase tracking-widest">Memory Layers</div>
             </div>
          </div>
        </div>
      </section>

      {/* ─── Product Showcase: Ultra-Think ─────────────────────────────── */}
      <section className="py-32 overflow-hidden border-t border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex flex-col lg:flex-row items-center gap-16">
            <div className="flex-1 space-y-8">
              <div className="space-y-4">
                <div className="inline-block px-3 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Advanced Reasoning</div>
                <h2 className="text-4xl lg:text-6xl font-bold text-white tracking-tighter font-heading leading-tight">Ultra-Think™ Engine</h2>
                <p className="text-slate-400 text-lg leading-relaxed font-sans">
                  Go beyond simple prompts. JEBAT&apos;s Ultra-Think module implements 6 distinct reasoning modes utilizing <span className="text-white font-bold">Parallel VPS Inference</span>.
                </p>
              </div>

              <div className="space-y-4">
                {[
                  { label: "Chain-of-Thought (CoT)", val: "100%", color: "emerald" },
                  { label: "Multi-Agent Consensus", val: "Verified", color: "blue" },
                  { label: "Context Window Utility", val: "Optimized", color: "purple" }
                ].map((stat, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between text-xs font-bold uppercase tracking-tighter text-slate-500 font-heading">
                      <span>{stat.label}</span>
                      <span className={`text-${stat.color}-400`}>{stat.val}</span>
                    </div>
                    <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden shadow-inner">
                      <div className={`h-full bg-${stat.color}-500 w-full opacity-30 shadow-[0_0_8px_rgba(var(--tw-color-${stat.color}-500),0.5)]`}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex-1 relative">
              <div className="w-full aspect-square max-w-md mx-auto rounded-[56px] bg-gradient-to-br from-blue-600/50 to-emerald-600/50 p-[1px] shadow-3xl">
                 <div className="w-full h-full rounded-[56px] bg-slate-950 p-10 flex flex-col justify-between relative overflow-hidden">
                    <div className="space-y-4 font-mono text-[11px] leading-relaxed">
                       <p className="text-blue-500 flex items-center gap-2 underline underline-offset-4 decoration-blue-500/30 font-bold"><HiOutlineCommandLine /> jebat --think &quot;Architect VPS redundancy&quot;</p>
                       <p className="text-slate-500 mt-6 animate-pulse">› [Hang Tuah] Dispatching specialists...</p>
                       <p className="text-emerald-500">› [Tukang] Optimizing Ollama config on .206...</p>
                       <p className="text-purple-500">› [Bendahara] Verifying PG schema sync...</p>
                       <div className="pt-6 border-t border-slate-800 mt-4">
                          <p className="text-white font-bold uppercase tracking-widest text-[9px]">Swarm Decision:</p>
                          <p className="text-white text-xs mt-2 font-medium leading-relaxed italic">&ldquo;Implement automated failover between VPS .206 and primary GPU cluster.&rdquo;</p>
                       </div>
                    </div>
                    <div className="h-32 bg-gradient-to-t from-emerald-500/10 to-transparent absolute bottom-0 left-0 right-0 pointer-events-none"></div>
                 </div>
              </div>
              <div className="absolute -top-6 -right-6 p-6 rounded-[32px] bg-slate-900 border border-slate-800 shadow-2xl backdrop-blur-xl">
                 <HiOutlineAcademicCap className="text-4xl text-blue-500 mb-2" />
                 <p className="text-[10px] font-bold text-white uppercase tracking-widest">Reasoning V3.0</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Trust & Deployment ─────────────────────────────── */}
      <section className="py-24 bg-blue-600 relative overflow-hidden shadow-inner">
         <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:20px_20px]"></div>
         
         <div className="max-w-4xl mx-auto px-6 text-center relative z-10 space-y-12">
            <h2 className="text-5xl lg:text-7xl font-bold text-white tracking-tight font-heading leading-tight italic">Deploy to Production <br /> in 30 Seconds</h2>
            <p className="text-blue-100 text-lg lg:text-xl font-sans opacity-90 max-w-2xl mx-auto leading-relaxed">
              Connect your private <span className="text-white font-bold">VPS .206 Mainframe</span> in seconds. One command. Full sovereignty.
            </p>
            <div className="bg-black/30 backdrop-blur-xl rounded-[32px] p-8 font-mono text-white text-sm lg:text-2xl inline-block border border-white/10 shadow-3xl group hover:scale-[1.02] transition-transform cursor-copy">
               <span className="text-emerald-400 mr-4 font-bold">$</span> npx jebat-agent setup <span className="text-blue-300">--mainframe=.206</span>
            </div>
            <div className="pt-8">
              <Link href="/v3/portal" className="px-12 py-6 bg-white text-blue-600 hover:bg-blue-50 rounded-[28px] font-bold transition-all shadow-3xl flex items-center gap-4 mx-auto w-fit text-lg group uppercase tracking-widest">
                ACCESS THE PORTAL <HiOutlineArrowRight className="group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
         </div>
      </section>

      {/* ─── Footer ─────────────────────────────── */}
      <footer className="py-24 border-t border-slate-800 bg-slate-950">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 grid grid-cols-1 md:grid-cols-4 gap-16">
          <div className="col-span-1 md:col-span-2 space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-xl">
                <HiOutlineCpuChip />
              </div>
              <span className="font-bold text-white tracking-tighter text-2xl font-heading uppercase">JEBAT.ONLINE</span>
            </div>
            <p className="text-slate-500 text-sm max-w-sm leading-relaxed font-medium italic">
              &ldquo;The last AI platform you will ever need.&rdquo; 
              Empowering enterprise with sovereign agent intelligence and private mainframe orchestration.
            </p>
            <div className="flex items-center gap-4 bg-slate-900/50 p-3 rounded-xl border border-slate-800 w-fit">
               <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">Ollama Mainframe .206 ACTIVE</span>
            </div>
          </div>
          <div className="space-y-6">
             <h4 className="text-xs font-bold text-white uppercase tracking-widest border-l-2 border-blue-500 pl-4">Platform</h4>
             <ul className="text-[11px] font-bold text-slate-500 space-y-4 uppercase tracking-tighter">
                <li><Link href="/v3" className="hover:text-blue-500 transition">Command Center</Link></li>
                <li><Link href="/v3/portal" className="hover:text-blue-500 transition">Enterprise Portal</Link></li>
                <li><Link href="/v3/chat" className="hover:text-blue-500 transition">Unified Chat</Link></li>
                <li><Link href="/v3/security" className="hover:text-blue-500 transition">Security Audit</Link></li>
             </ul>
          </div>
          <div className="space-y-6">
             <h4 className="text-xs font-bold text-white uppercase tracking-widest border-l-2 border-emerald-500 pl-4">Engineering</h4>
             <ul className="text-[11px] font-bold text-slate-500 space-y-4 uppercase tracking-tighter">
                <li><a href="#" className="hover:text-emerald-500 transition">Sovereignty Model</a></li>
                <li><a href="#" className="hover:text-emerald-500 transition">Memory Layers</a></li>
                <li><a href="#" className="hover:text-emerald-500 transition">Swarm Protocols</a></li>
                <li><a href="https://github.com/nusabyte-my/jebat-core" target="_blank" className="hover:text-emerald-500 transition">PostgreSQL Sync</a></li>
             </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 pt-24 text-center text-slate-600 text-[10px] uppercase tracking-widest font-bold border-t border-slate-900 mt-20">
           &copy; 2026 NUSABYTE &middot; ALL RIGHTS RESERVED &middot; OPTIMIZED FOR VPS .206 &middot; MALAYSIA
        </div>
      </footer>
    </main>
  );
}
