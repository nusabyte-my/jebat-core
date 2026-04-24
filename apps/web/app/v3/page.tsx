"use client";

import { motion } from "framer-motion";
import { 
  HiOutlineCpuChip, 
  HiOutlineServerStack, 
  HiOutlineShieldCheck, 
  HiOutlineBolt, 
  HiOutlineChatBubbleLeftRight,
  HiOutlineChartBar,
  HiOutlineCommandLine,
  HiOutlineCube,
  HiOutlineArrowRight
} from "react-icons/hi2";
import Link from "next/link";

export default function V3Dashboard() {
  return (
    <main className="max-w-[1600px] mx-auto p-6 lg:p-10 space-y-8">
      {/* ─── Header: Strategic Overview ─────────────────────────────── */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <HiOutlineCpuChip className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold font-heading tracking-tight text-white">
              JEBAT <span className="text-blue-500">v3</span> COMMAND
            </h1>
          </div>
          <p className="text-slate-400 text-sm pl-13">Sovereign Agent Orchestration Engine</p>
        </div>

        <div className="flex items-center gap-4 bg-slate-900/50 p-2 rounded-2xl border border-slate-800">
          <div className="px-4 py-2 text-center">
            <div className="text-xs text-slate-500 uppercase tracking-widest font-bold">Mainframe</div>
            <div className="flex items-center gap-2 justify-center mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
              <span className="text-sm font-semibold text-emerald-400">VPS .206</span>
            </div>
          </div>
          <div className="w-px h-8 bg-slate-800"></div>
          <div className="px-4 py-2 text-center">
            <div className="text-xs text-slate-500 uppercase tracking-widest font-bold">Agents</div>
            <div className="text-sm font-semibold text-white mt-1">34 DEPLOYED</div>
          </div>
          <div className="w-px h-8 bg-slate-800"></div>
          <div className="px-4 py-2 text-center">
            <div className="text-xs text-slate-500 uppercase tracking-widest font-bold">Memory</div>
            <div className="text-sm font-semibold text-blue-400 mt-1">92% HEAT (M4)</div>
          </div>
        </div>
      </header>

      {/* ─── Bento Grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 auto-rows-[180px]">
        
        {/* Card: Primary Action (Chat) - Large */}
        <Link href="/v3/chat" className="contents">
          <motion.div 
            whileHover={{ y: -4, borderColor: "rgba(59, 130, 246, 0.4)" }}
            className="md:col-span-2 md:row-span-2 rounded-3xl bg-gradient-to-br from-blue-600 to-blue-800 p-8 flex flex-col justify-between group cursor-pointer relative overflow-hidden border border-transparent shadow-2xl shadow-blue-900/20"
          >
            <div className="relative z-10">
              <div className="w-12 h-12 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center mb-6 shadow-inner">
                <HiOutlineChatBubbleLeftRight className="w-7 h-7 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Engage the Swarm</h2>
              <p className="text-blue-100/90 max-w-sm font-medium leading-relaxed">
                Initiate multi-agent reasoning, code generation, or complex research tasks through the unified chat interface. Powered by Jebat.cpp.
              </p>
            </div>
            
            <div className="flex items-center gap-3 text-white font-bold group-hover:gap-5 transition-all mt-4 uppercase tracking-widest text-[11px]">
              <span>Initialize Command Link</span>
              <HiOutlineArrowRight className="w-4 h-4" />
            </div>

            {/* Abstract Deco */}
            <div className="absolute top-0 right-0 -mr-10 -mt-10 w-64 h-64 bg-white/5 rounded-full blur-3xl pointer-events-none"></div>
          </motion.div>
        </Link>

        {/* Card: Ultra-Loop Status */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between shadow-xl relative overflow-hidden group"
        >
          <div className="flex justify-between items-start relative z-10">
            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shadow-inner">
              <HiOutlineBolt className="w-5 h-5 text-blue-400 group-hover:animate-pulse" />
            </div>
            <div className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Ultra-Loop™</div>
          </div>
          <div className="relative z-10">
            <div className="text-3xl font-bold text-white">0.4s</div>
            <p className="text-xs text-slate-500 mt-1">Perception Cycle Interval</p>
          </div>
          <button className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-[10px] font-bold uppercase tracking-widest transition text-white relative z-10">
            Override Frequency
          </button>
          <div className="absolute bottom-0 left-0 right-0 h-1/2 bg-gradient-to-t from-blue-500/5 to-transparent pointer-events-none"></div>
        </motion.div>

        {/* Card: Security Status */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between shadow-xl relative group overflow-hidden"
        >
          <div className="flex justify-between items-start relative z-10">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <HiOutlineShieldCheck className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
          </div>
          <div className="relative z-10">
            <div className="text-xl font-bold text-white">Hulubalang Active</div>
            <p className="text-xs text-slate-500 mt-1">Kernel-level sandboxing</p>
          </div>
          <div className="flex gap-2 relative z-10">
            <div className="h-1 flex-1 bg-emerald-500 rounded-full shadow-[0_0_4px_rgba(16,185,129,0.5)]"></div>
            <div className="h-1 flex-1 bg-emerald-500 rounded-full shadow-[0_0_4px_rgba(16,185,129,0.5)]"></div>
            <div className="h-1 flex-1 bg-emerald-500/20 rounded-full"></div>
          </div>
          <div className="absolute bottom-0 right-0 w-32 h-32 bg-emerald-500/5 blur-2xl rounded-full pointer-events-none group-hover:bg-emerald-500/10 transition-colors"></div>
        </motion.div>

        {/* Card: Memory Stats - Wide */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="md:col-span-2 rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col md:flex-row gap-6 shadow-xl relative overflow-hidden group"
        >
          <div className="flex-1 flex flex-col justify-between relative z-10">
            <div>
              <h3 className="text-lg font-bold text-white">PostgreSQL Consolidation</h3>
              <p className="text-xs text-slate-500 mt-1">Automatic transfer from M0 Sensory to M4 Procedural layers.</p>
            </div>
            <div className="flex items-end gap-1 h-12">
              {[40, 70, 45, 90, 65, 80, 50, 60, 85, 95].map((h, i) => (
                <div key={i} className="flex-1 bg-blue-500/10 rounded-t-sm relative">
                  <div 
                    className="absolute bottom-0 left-0 right-0 bg-blue-500 transition-all shadow-[0_0_8px_rgba(59,130,246,0.3)]" 
                    style={{ height: `${h}%` }}
                  ></div>
                </div>
              ))}
            </div>
          </div>
          <div className="w-px bg-slate-800 hidden md:block relative z-10"></div>
          <div className="w-full md:w-32 flex flex-col justify-center space-y-4 relative z-10">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">5</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Layers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-white">124k</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Records</div>
            </div>
          </div>
          <div className="absolute inset-0 bg-gradient-to-r from-transparent to-blue-500/5 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity"></div>
        </motion.div>

        {/* Card: Performance (Metrics) */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between shadow-xl"
        >
          <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center shadow-inner">
            <HiOutlineChartBar className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">14.2ms</div>
            <p className="text-xs text-slate-500 mt-1">Cross-Agent Latency</p>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-purple-400 uppercase tracking-widest">
            <HiOutlineBolt /> Redis Edge Sync
          </div>
        </motion.div>

        {/* Card: Core System (CLI) */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-950 border border-slate-800 p-5 font-mono text-[11px] relative overflow-hidden group shadow-inner"
        >
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-red-500"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-slate-600 ml-2">jebat --system-check</span>
          </div>
          <div className="space-y-1.5 text-slate-400">
            <p className="text-blue-400">[CORE] Initializing Jebat.cpp...</p>
            <p className="text-emerald-500">[OK] VPS .206 Mainframe Linked</p>
            <p className="text-emerald-500">[OK] Orchestrator Swarm Live</p>
            <p className="text-purple-400">[INFO] BYOK Vault Secured</p>
            <p className="animate-pulse">_</p>
          </div>
          {/* Overlay mask */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none"></div>
        </motion.div>

        {/* Card: Analytics Summary (Small) */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between shadow-xl"
        >
           <div className="flex items-center gap-2">
            <HiOutlineCube className="w-5 h-5 text-blue-400" />
            <span className="text-xs font-bold text-white tracking-widest uppercase">Resources</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-tighter">
              <span className="text-slate-500">Compute (GPU)</span>
              <span className="text-white">82%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="w-[82%] h-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></div>
            </div>
            <div className="flex justify-between text-[10px] font-bold uppercase tracking-tighter">
              <span className="text-slate-500">Memory (RAM)</span>
              <span className="text-white">42 GB</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="w-[65%] h-full bg-purple-500"></div>
            </div>
          </div>
        </motion.div>

        {/* Card: External Integrations */}
        <motion.div 
          whileHover={{ y: -4 }}
          className="rounded-3xl bg-slate-900 border border-slate-800 p-6 flex flex-col justify-between shadow-xl"
        >
          <div className="flex items-center gap-2">
            <HiOutlineServerStack className="w-5 h-5 text-slate-400" />
            <span className="text-xs font-bold text-white uppercase tracking-widest">Sovereignty</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Jebat.cpp', 'Llama 3.1', 'Qwen 2.5', 'PostgreSQL'].map(p => (
              <span key={p} className="px-2 py-1 bg-slate-800 rounded-md text-[9px] font-bold text-slate-300 border border-slate-700 uppercase tracking-tighter shadow-sm">{p}</span>
            ))}
          </div>
          <div className="text-[9px] text-blue-400 font-bold flex items-center gap-1 cursor-pointer hover:text-blue-300 transition-colors tracking-widest uppercase mt-2">
            MANAGE CLOUD BYOK <HiOutlineArrowRight />
          </div>
        </motion.div>

      </div>

      {/* ─── Footer: Global System Status ─────────────────────────────── */}
      <footer className="flex flex-col md:flex-row items-center justify-between gap-6 pt-10 text-slate-500 text-[10px] uppercase tracking-widest font-bold">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></span>
            LATENCY: 14.2MS
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            VPS .206 CONNECTED
          </div>
        </div>
        <div>
          &copy; 2026 NUSABYTE &middot; MALAYSIA &middot; JEBAT-CORE v2.0.0
        </div>
      </footer>
    </main>
  );
}
