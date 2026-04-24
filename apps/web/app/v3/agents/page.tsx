"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { 
  HiOutlineUsers, 
  HiOutlineUserCircle, 
  HiOutlineBolt,
  HiOutlineFingerPrint,
  HiOutlineArrowRight,
  HiOutlineCpuChip,
  HiOutlineCircleStack,
  HiOutlineShieldCheck
} from "react-icons/hi2";
import Link from "next/link";
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

const CORE_COMMAND = [
  { name: "HANG TUAH", role: "Lead Orchestrator", specialty: "Strategic Governance", desc: "The primary decision-maker. Coordinates all 34 agents and resolves cross-domain conflicts.", skills: ["Multi-Agent Orchestration", "Conflict Resolution", "Strategic Logic"], value: "Reduces operational friction by 60% through automated delegation." },
  { name: "HANG NADIM", role: "Primary Classifier", specialty: "High-Speed Routing", desc: "The gatekeeper. Analyzes incoming prompts and dispatches the most efficient execution path.", skills: ["Intent Classification", "Token Optimization", "Load Balancing"], value: "Prevents resource waste by ensuring the right agent handles the right task." },
  { name: "HANG KASTURI", role: "Infrastructure Lead", specialty: "Persistence & Stability", desc: "Ensures the PostgreSQL foundation and Redis caches are optimized for real-time response.", skills: ["Database Partitioning", "Edge Caching", "High Availability"], value: "Keeps enterprise-critical AI workloads stable under sustained load." },
  { name: "HANG LEKIR", role: "Intelligence Lead", specialty: "Advanced Research", desc: "Deep-dives into complex knowledge bases and cross-references multi-layer memory (M0-M4).", skills: ["Semantic Search", "Knowledge Extraction", "Memory Mapping"], value: "Transforms raw data into actionable enterprise intelligence." },
  { name: "HANG LEKIU", role: "Security Lead", specialty: "Defense & Hardening", desc: "Monitors the threat surface and enforces sandboxing controls for generated code.", skills: ["PII Scrubbing", "Sandbox Enforcement", "Injection Defense"], value: "Provides hardened security controls for sovereign AI deployments." }
];

export default function V3Agents() {
  const [hoveredSpecialist, setHoveredSpecialist] = useState<Specialist | null>(null);

  return (
    <main className="min-h-screen">
      <SpecialistModal
        specialist={hoveredSpecialist}
        isOpen={!!hoveredSpecialist}
        onClose={() => setHoveredSpecialist(null)}
      />

      {/* ─── Header: Agent Orchestration ────────────────────────────── */}
      <section className="pt-48 pb-20 border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-10">
          <div className="space-y-4">
            <h2 className="text-xs font-bold text-emerald-500 uppercase tracking-[0.3em]">Intelligence Matrix</h2>
            <h1 className="text-5xl lg:text-7xl font-bold text-white tracking-tight leading-[0.95]">
              The Swarm <br /> <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">Orchestration</span>
            </h1>
          </div>
          <p className="text-slate-400 max-w-3xl text-lg lg:text-xl font-sans leading-relaxed">
            JEBAT dispatches specialized execution paths led by the Five Warriors. Our orchestration model
            replaces a monolithic assistant with a governed multi-agent runtime.
          </p>
          <div className="flex flex-wrap gap-4">
             <div className="flex items-center gap-3 px-4 py-2 rounded-full border border-emerald-500/20 bg-emerald-500/5">
                <HiOutlineCpuChip className="text-emerald-500" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">Ollama Mainframe (.206)</span>
             </div>
             <div className="flex items-center gap-3 px-4 py-2 rounded-full border border-blue-500/20 bg-blue-500/5">
                <HiOutlineCircleStack className="text-blue-500" />
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">PostgreSQL Persistent</span>
             </div>
          </div>
        </div>
      </section>

      {/* ─── Core Command: The 5 Warriors ─────────────────────────────── */}
      <section className="py-32 space-y-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
          <div className="flex items-center justify-between">
             <div className="flex items-center gap-4">
                <HiOutlineFingerPrint className="text-2xl text-emerald-500" />
                <h3 className="text-xl font-bold text-white uppercase tracking-widest">Core Command (The Lineage)</h3>
             </div>
             <span className="text-[10px] font-bold text-slate-500 uppercase">Hover to reveal specialization</span>
          </div>
         
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
            {CORE_COMMAND.map((leader, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -10 }}
                className="group h-[420px] rounded-[40px] bg-slate-900/50 border border-slate-800/50 p-10 flex flex-col justify-between relative overflow-hidden shadow-2xl transition-all hover:border-emerald-500/30"
              >
                 <div className="space-y-6 group-hover:opacity-0 transition-all duration-300">
                    <div className="w-20 h-20 rounded-3xl bg-emerald-600/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 text-4xl font-bold">
                       {leader.name.charAt(5)}
                    </div>
                    <div>
                       <h4 className="text-3xl font-bold text-white">{leader.name}</h4>
                       <p className="text-emerald-500 font-bold text-xs uppercase tracking-widest mt-1">{leader.role}</p>
                    </div>
                    <p className="text-slate-400 text-sm leading-relaxed">{leader.desc}</p>
                 </div>

                 <div className="absolute inset-0 p-10 flex flex-col justify-center bg-slate-900 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-4 group-hover:translate-y-0">
                    <h4 className="text-white text-xl font-bold uppercase tracking-widest mb-6">Specialized Skillset</h4>
                    <div className="space-y-3 mb-10">
                       {leader.skills.map(s => (
                          <div key={s} className="flex items-center gap-2 text-white font-bold text-sm">
                             <HiOutlineBolt className="text-emerald-400" /> {s}
                          </div>
                       ))}
                    </div>
                    <div className="pt-6 border-t border-emerald-400/50">
                       <p className="text-[10px] text-emerald-100 font-bold uppercase tracking-widest mb-2">Enterprise Value</p>
                       <p className="text-white text-sm font-medium leading-relaxed italic">&ldquo;{leader.value}&rdquo;</p>
                    </div>
                 </div>
                 <div className="absolute bottom-0 right-0 -mr-10 -mb-10 w-48 h-48 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none"></div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Specialist Swarm Matrix ─────────────────────────────── */}
      <section className="py-32 space-y-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
          <div className="flex items-center gap-4">
            <HiOutlineUsers className="text-2xl text-emerald-500" />
            <h3 className="text-xl font-bold text-white uppercase tracking-widest">Specialist Swarm Matrix</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {SPECIALISTS_DATA.map((agent, i) => (
              <motion.div
                key={i}
                onMouseEnter={() => setHoveredSpecialist(agent)}
                onMouseLeave={() => setHoveredSpecialist(null)}
                whileHover={{ y: -4, borderColor: "rgba(16, 185, 129, 0.4)" }}
                className="p-6 rounded-[32px] bg-slate-900/50 border border-slate-800 hover:bg-slate-900 transition-all group shadow-xl cursor-pointer relative"
              >
                <div className={`w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-${agent.color}-400 mb-4 group-hover:scale-110 transition-transform shadow-inner`}>
                  <HiOutlineUserCircle className="text-xl" />
                </div>
                <h4 className="text-white font-bold text-sm">{agent.name}</h4>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tight mb-2">{agent.role}</p>
                <div className="flex items-center gap-2 text-[9px] font-bold text-emerald-500 uppercase tracking-tighter">
                  Skill Details <HiOutlineArrowRight className="group-hover:translate-x-1 transition-transform" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
