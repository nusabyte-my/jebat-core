"use client";

import { motion } from "framer-motion";
import {
  HiOutlineShieldCheck,
  HiOutlineLockClosed,
  HiOutlineExclamationTriangle,
  HiOutlineDocumentMagnifyingGlass,
  HiOutlineFingerPrint,
  HiOutlineEye,
  HiOutlineArrowRight
} from "react-icons/hi2";

export default function V3Security() {
  const ALERTS = [
    { type: "CRITICAL", msg: "Unauthorized access attempt on M3 Conceptual Layer", time: "2m ago", status: "BLOCKED" },
    { type: "WARNING", msg: "Insecure tool binding detected in [Tukang]", time: "15m ago", status: "PATCHED" },
    { type: "INFO", msg: "Automatic PII mask applied to 1,204 records", time: "1h ago", status: "OK" },
  ];

  return (
    <main className="min-h-screen">
      {/* ─── Header: Security Sentinel ───────────────────────── */}
      <section className="pt-48 pb-20 border-b border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-10">
          <div className="space-y-4">
            <h2 className="text-xs font-bold text-red-500 uppercase tracking-[0.3em]">Security Sentinel</h2>
            <h1 className="text-4xl lg:text-6xl font-bold text-white tracking-tight">
              Hulubalang <br /> <span className="text-red-500">& Hardening</span>
            </h1>
          </div>
          <p className="text-slate-400 max-w-2xl text-lg font-sans">
            The defense matrix of the sovereign intelligence platform. Powered by the <span className="text-white font-bold">VPS .206 Mainframe</span>,
            the system continuously monitors and mitigates threats.
          </p>
          <div>
            <button className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-2xl font-bold text-xs transition shadow-lg shadow-red-600/20 flex items-center gap-2 uppercase tracking-widest">
              <HiOutlineShieldCheck className="text-sm" /> FULL SYSTEM AUDIT
            </button>
          </div>
        </div>
      </section>

      {/* ─── Vulnerability Map ───────────────────────── */}
      <section className="py-32">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
           <div className="relative z-10 space-y-8">
              <div className="flex items-center justify-between">
                 <h3 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
                    <HiOutlineDocumentMagnifyingGlass className="text-blue-500" />
                    Threat Surface Analysis
                 </h3>
                 <span className="text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20 uppercase tracking-widest shadow-sm">Hardened</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
                 <div className="space-y-6">
                    <div className="p-6 rounded-[24px] bg-slate-950 border border-slate-800 shadow-inner group">
                       <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Network Isolation</p>
                       <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500 text-xl group-hover:scale-110 transition-transform">
                             <HiOutlineLockClosed />
                          </div>
                          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                             <div className="h-full w-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]"></div>
                          </div>
                          <span className="text-xs font-bold text-white uppercase tracking-widest">Private</span>
                       </div>
                    </div>
                    <div className="p-6 rounded-[24px] bg-slate-950 border border-slate-800 shadow-inner group">
                       <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">PII Scrubbing</p>
                       <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 text-xl group-hover:scale-110 transition-transform">
                             <HiOutlineFingerPrint />
                          </div>
                          <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                             <div className="h-full w-[92%] bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
                          </div>
                          <span className="text-xs font-bold text-white uppercase tracking-widest">92%</span>
                       </div>
                    </div>
                 </div>
                 <div className="bg-slate-950 rounded-3xl p-6 border border-slate-800 flex items-center justify-center relative overflow-hidden shadow-inner">
                    <div className="text-center space-y-2 z-10">
                       <p className="text-5xl font-bold text-white tracking-tighter">0.0</p>
                       <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Critical Vulnerabilities</p>
                    </div>
                    <div className="absolute inset-0 bg-emerald-500/5 blur-[60px] pointer-events-none"></div>
                 </div>
              </div>
           </div>
        </div>

         {/* Live Alerts */}
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-white uppercase tracking-widest px-2">Live Sentinel Logs</h3>
            <div className="space-y-3">
              {ALERTS.map((alert, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  whileHover={{ x: 4, borderColor: "rgba(239, 68, 68, 0.4)" }}
                  className="p-5 rounded-[32px] bg-slate-900/50 border border-slate-800 flex items-center gap-4 group shadow-sm hover:border-red-500/30 transition-all"
                >
                  <div className={`w-2 h-2 rounded-full ${alert.type === 'CRITICAL' ? 'bg-red-500 animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]' : alert.type === 'WARNING' ? 'bg-amber-500' : 'bg-blue-500'}`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white truncate">{alert.msg}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">{alert.time}</span>
                      <span className={`text-[9px] font-bold px-2 py-0.5 rounded tracking-widest uppercase ${alert.status === 'BLOCKED' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-slate-800 text-slate-400'}`}>{alert.status}</span>
                    </div>
                  </div>
                  <HiOutlineEye className="text-slate-700 group-hover:text-red-400 transition-colors cursor-pointer" />
                </motion.div>
              ))}
            </div>
            <motion.div
              whileHover={{ y: -4 }}
              className="p-8 rounded-[32px] bg-red-600/5 border border-red-500/10 space-y-4 shadow-inner"
            >
              <HiOutlineExclamationTriangle className="text-3xl text-red-500" />
              <h4 className="text-white font-bold tracking-tight">Hardening Active</h4>
              <p className="text-slate-500 text-[10px] leading-relaxed uppercase font-bold tracking-widest">Hulubalang is enforcing kernel-level sandbox on all [Tukang] generated code.</p>
            </motion.div>
          </div>

        </div>
      </section>
    </main>
  );
}
