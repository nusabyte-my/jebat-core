"use client";

import { motion, AnimatePresence } from "framer-motion";
import { HiOutlineBolt, HiOutlineXMark, HiOutlineShieldCheck, HiOutlineCpuChip } from "react-icons/hi2";

export interface Specialist {
  name: string;
  role: string;
  color: string;
  skill: string;
  details: string[];
  metrics: { label: string; val: string }[];
}

// Using HEX codes directly to prevent lab() resolution and allow proper string manipulation
const COLOR_MAP: Record<string, string> = {
  purple: "#A855F7",
  red: "#EF4444",
  pink: "#EC4899",
  orange: "#F97316",
  emerald: "#10B981",
  cyan: "#06B6D4",
  teal: "#14B8A6",
  amber: "#F59E0B",
  blue: "#3B82F6",
};

export function SpecialistModal({ specialist, isOpen, onClose }: { specialist: Specialist | null, isOpen: boolean, onClose: () => void }) {
  if (!specialist) return null;

  const activeColor = COLOR_MAP[specialist.color] || "#3B82F6";

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 pointer-events-none">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-slate-950/60 backdrop-blur-md"
          />
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative w-full max-w-xl bg-slate-900 border border-slate-800 rounded-[40px] shadow-3xl overflow-hidden pointer-events-auto"
          >
            <div 
              className="h-2 w-full" 
              style={{ backgroundColor: activeColor, boxShadow: `0 0 20px ${activeColor}` }}
            ></div>
            
            <button 
              onClick={onClose}
              className="absolute top-6 right-6 w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
            >
              <HiOutlineXMark className="text-xl" />
            </button>

            <div className="p-10 space-y-8">
              <div className="flex items-center gap-6">
                 <div 
                   className="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center text-3xl shadow-inner"
                   style={{ color: activeColor }}
                 >
                    {specialist.name.charAt(0)}
                 </div>
                 <div>
                    <h3 className="text-3xl font-bold text-white tracking-tight">{specialist.name}</h3>
                    <p className="text-slate-500 font-bold uppercase tracking-widest text-xs mt-1">{specialist.role}</p>
                 </div>
              </div>

              <div className="space-y-4">
                 <p className="text-sm font-bold text-slate-400 uppercase tracking-widest border-l-2 border-blue-500 pl-4">Core Specialist Skillset</p>
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {specialist.details.map((s, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800">
                         <HiOutlineBolt style={{ color: activeColor }} />
                         <span className="text-xs font-bold text-slate-300 uppercase tracking-tighter">{s}</span>
                      </div>
                    ))}
                 </div>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-6 border-t border-slate-800">
                 {specialist.metrics.map((m, i) => (
                    <div key={i} className="text-center">
                       <p className="text-[10px] font-bold text-slate-600 uppercase mb-1">{m.label}</p>
                       <p className="text-lg font-bold" style={{ color: activeColor }}>{m.val}</p>
                    </div>
                 ))}
              </div>

              <div className="pt-4">
                 <div className="p-4 rounded-2xl bg-blue-600/5 border border-blue-500/10 flex items-center gap-4">
                    <HiOutlineCpuChip className="text-blue-500 text-xl" />
                    <p className="text-[10px] font-medium text-slate-400 leading-relaxed uppercase">
                      Currently optimized for <span className="text-white font-bold">VPS .206 Ollama Mainframe</span> for 0.4ms cross-agent latency.
                    </p>
                 </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
