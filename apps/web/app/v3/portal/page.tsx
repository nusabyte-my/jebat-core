"use client";

import { motion } from "framer-motion";
import { useState } from "react";
import Link from "next/link";
import {
  HiOutlineUsers,
  HiOutlineChartBar,
  HiOutlineBolt,
  HiOutlineServerStack,
  HiOutlineArrowLeft,
  HiOutlineGlobeAlt,
  HiOutlineSignal,
  HiOutlineCpuChip
} from "react-icons/hi2";

const AGENT_STATUS = [
  { name: "Panglima", role: "Orchestration", status: "online", model: "jebat-cpp-multi", color: "blue" },
  { name: "Tukang", role: "Development", status: "online", model: "qwen2.5-coder", color: "purple" },
  { name: "Hulubalang", role: "Security", status: "online", model: "llama3.1:70b", color: "red" },
  { name: "Hikmat", role: "Memory", status: "online", model: "jebat-cpp-multi", color: "pink" },
  { name: "Penganalisis", role: "Analytics", status: "online", model: "llama3.1:70b", color: "emerald" },
];

export default function V3Portal() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <main className="min-h-screen">
      {/* ─── Top Navigation ─────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-[100] bg-slate-950/80 backdrop-blur-xl border-b border-slate-800 py-4">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
          <Link href="/v3" className="flex items-center gap-2 text-slate-400 hover:text-white transition group">
            <HiOutlineArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-xs font-bold uppercase tracking-widest">Back to Command</span>
          </Link>
          <div className="flex gap-2">
            {['overview', 'agents', 'analytics', 'infrastructure'].map((t) => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-tighter transition-all ${
                  activeTab === t ? "bg-emerald-600 text-white shadow-lg shadow-emerald-500/20" : "bg-slate-900 text-slate-500 hover:bg-slate-800"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* ─── Header: Sovereign Telemetry ─────────────────────────────── */}
      <section className="pt-48 pb-20 border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-10">
          <div className="space-y-4">
            <h2 className="text-xs font-bold text-emerald-500 uppercase tracking-[0.3em]">Sovereign Telemetry</h2>
            <h1 className="text-4xl lg:text-6xl font-bold text-white tracking-tight">
              Enterprise <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">Telemetry</span>
            </h1>
          </div>
          <p className="text-slate-400 max-w-2xl text-lg">
            Real-time diagnostics across all 34 agents, memory layers, and LLM engines.
            Currently monitoring the <span className="text-white font-bold">VPS .206 Mainframe</span>.
          </p>
        </div>
      </section>

      {/* ─── Grid: Top Analytics ─────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: "Processed Tokens", value: "14.2M", change: "+24% (Local)", icon: <HiOutlineBolt className="text-emerald-400" /> },
            { label: "VPS .206 Latency", value: "14.2ms", change: "OPTIMIZED", icon: <HiOutlineSignal className="text-emerald-400" /> },
            { label: "Active Swarms", value: "12", change: "PEAK LOAD", icon: <HiOutlineUsers className="text-purple-400" /> },
            { label: "Jebat.cpp Cores", value: "8", change: "ACTIVE", icon: <HiOutlineCpuChip className="text-orange-400" /> },
          ].map((stat, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -4 }}
              className="bg-slate-900/50 border border-slate-800 p-6 rounded-[32px] flex items-center justify-between shadow-xl hover:border-emerald-500/30 transition-all"
            >
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</p>
                <h3 className="text-3xl font-bold text-white">{stat.value}</h3>
                <p className={`text-[10px] font-bold ${stat.change === 'OPTIMIZED' || stat.change === 'ACTIVE' ? "text-emerald-500" : "text-blue-400"}`}>{stat.change}</p>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center text-xl shadow-inner">
                {stat.icon}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* ─── Grid: Main Portal Content ─────────────────────────────── */}
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-24">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Agent Grid - Wide */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">Active Core Engines</h2>
              <Link href="/v3/agents" className="text-[10px] font-bold text-emerald-500 hover:underline">VIEW ALL 34 AGENTS</Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {AGENT_STATUS.map((agent, i) => (
                <motion.div
                  key={i}
                  whileHover={{ x: 4 }}
                  className="bg-slate-900/50 border border-slate-800 p-4 rounded-[24px] flex items-center gap-4 group shadow-md hover:border-emerald-500/30 transition-all"
                >
                  <div
                    className={`w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-lg font-bold text-white border-b-2 shadow-inner`}
                    style={{ borderColor: `var(--color-specialist-${agent.color})` }}
                  >
                    {agent.name.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-white text-sm">{agent.name}</h4>
                    <p className="text-[10px] font-bold text-slate-500 uppercase tracking-tight">{agent.role}</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 justify-end">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_4px_rgba(16,185,129,0.8)]"></span>
                      <span className="text-[9px] font-bold text-emerald-500 uppercase tracking-widest">Local</span>
                    </div>
                    <p className="text-[9px] text-emerald-400 font-mono mt-1 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">{agent.model}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Infrastructure Sidebar */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-[32px] p-8 space-y-8 shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-emerald-500/5 blur-[80px] pointer-events-none"></div>
            <div className="relative z-10 space-y-1">
              <h2 className="text-xl font-bold text-white">Mainframe Load</h2>
              <p className="text-xs text-emerald-400 font-mono uppercase font-bold tracking-widest">Node: VPS .206 (Private)</p>
            </div>

            <div className="relative z-10 space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest">
                  <span className="text-slate-400">Compute (Ollama/Jebat.cpp)</span>
                  <span className="text-white">82.4%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "82.4%" }}
                    className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                  ></motion.div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest">
                  <span className="text-slate-400">Memory (RAM)</span>
                  <span className="text-white">24.2 / 32 GB</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "75%" }}
                    className="h-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"
                  ></motion.div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-bold uppercase tracking-widest">
                  <span className="text-slate-400">PostgreSQL (Storage)</span>
                  <span className="text-white">42%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "42%" }}
                    className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                  ></motion.div>
                </div>
              </div>
            </div>

            <div className="relative z-10 pt-6 border-t border-slate-800">
              <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 shadow-inner">
                <HiOutlineServerStack className="w-6 h-6 text-emerald-500" />
                <div className="flex-1">
                  <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">Primary Engine</p>
                  <p className="text-xs font-bold text-white mt-0.5">Jebat.cpp Multi-LM</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
