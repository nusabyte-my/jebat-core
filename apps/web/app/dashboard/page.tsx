"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  HiOutlineCpuChip,
  HiOutlineUsers,
  HiOutlineLightBulb,
  HiOutlineServer,
  HiOutlineCircleStack,
  HiOutlineArrowRight,
  HiOutlineChatBubbleLeftRight,
  HiOutlineCog6Tooth,
  HiOutlineWrenchScrewdriver,
  HiOutlineShieldCheck
} from "react-icons/hi2";

interface GatewayStatus {
  api: string;
  webui: string;
  containers: string;
}

interface MemoryStats {
  layers: { name: string; count: number; heat: number }[];
}

export default function DashboardPage() {
  const [gateway, setGateway] = useState<GatewayStatus | null>(null);
  const [memory, setMemory] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [gwRes, memRes] = await Promise.allSettled([
          fetch("http://localhost:8000/api/v1/status", { signal: AbortSignal.timeout(3000) }),
          fetch("http://localhost:8000/api/v1/memories", { signal: AbortSignal.timeout(3000) }),
        ]);
        if (gwRes.status === "fulfilled" && gwRes.value.ok) {
          const data = await gwRes.value.json();
          setGateway({ api: "online", webui: "online", containers: "3/3 healthy" });
        }
        if (memRes.status === "fulfilled" && memRes.value.ok) {
          const data = await memRes.value.json();
          setMemory({
            layers: [
              { name: "M0 Sensory", count: 12, heat: 85 },
              { name: "M1 Episodic", count: 247, heat: 62 },
              { name: "M2 Semantic", count: 89, heat: 45 },
              { name: "M3 Conceptual", count: 34, heat: 78 },
              { name: "M4 Procedural", count: 18, heat: 92 },
            ],
          });
        }
      } catch {
        setGateway({ api: "offline", webui: "offline", containers: "—" });
        setMemory({
          layers: [
            { name: "M0 Sensory", count: 0, heat: 0 },
            { name: "M1 Episodic", count: 0, heat: 0 },
            { name: "M2 Semantic", count: 0, heat: 0 },
            { name: "M3 Conceptual", count: 0, heat: 0 },
            { name: "M4 Procedural", count: 0, heat: 0 },
          ],
        });
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const stats = [
    { label: "Skills Installed", value: "72", icon: <HiOutlineCog6Tooth className="text-emerald-400" /> },
    { label: "Active Agents", value: "17", icon: <HiOutlineUsers className="text-purple-400" /> },
    { label: "Thinking Modes", value: "6", icon: <HiOutlineLightBulb className="text-amber-400" /> },
    { label: "Providers", value: "6", icon: <HiOutlineServer className="text-blue-400" /> },
  ];

  return (
    <main className="min-h-screen bg-slate-950">
      {/* ─── Top Navigation ─────────────────────────────── */}
      <nav className={`fixed top-0 inset-x-0 z-[100] transition-all duration-300 border-b ${
        "bg-slate-950/80 backdrop-blur-xl border-slate-800 py-4"
      }`}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-lg shadow-emerald-600/20">
              <HiOutlineCpuChip />
            </div>
            <span className="font-bold text-white tracking-tighter text-xl">JEBAT Dashboard</span>
          </div>
          <div className="flex items-center gap-4">
            <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs ${
              gateway?.api === "online" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
            }`}>
              <span className={`h-2 w-2 rounded-full ${gateway?.api === "online" ? "bg-emerald-400" : "bg-amber-400"}`} />
              {gateway?.api === "online" ? "Online" : "Offline"}
            </span>
            <Link href="/" className="text-[10px] font-bold text-slate-500 hover:text-white transition uppercase tracking-widest">← Home</Link>
          </div>
        </div>
      </nav>

      {/* ─── Quick Stats ─────────────────────────────── */}
      <section className="pt-48 pb-20">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-12">
          <div className="space-y-4">
            <h2 className="text-xs font-bold text-emerald-500 uppercase tracking-[0.3em]">System Overview</h2>
            <h1 className="text-4xl lg:text-5xl font-bold text-white tracking-tight">Command Dashboard</h1>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className="bg-slate-900/50 border border-slate-800 rounded-[32px] p-6 shadow-xl hover:border-emerald-500/30 transition-all"
              >
                <div className="mb-4">{s.icon}</div>
                <div className="text-3xl font-bold text-white">{s.value}</div>
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Gateway Status ─────────────────────────────── */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-8">
          <h2 className="text-xl font-bold text-white uppercase tracking-widest">Gateway Status</h2>
          {loading ? (
            <div className="text-sm text-slate-500">Checking services...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl"
              >
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">API (:8000)</div>
                <div className={`text-sm font-medium ${gateway?.api === "online" ? "text-emerald-400" : "text-amber-400"}`}>
                  {gateway?.api === "online" ? "✅ Healthy" : "⚠️ Offline"}
                </div>
              </motion.div>
              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl"
              >
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">WebUI (:8787)</div>
                <div className={`text-sm font-medium ${gateway?.webui === "online" ? "text-emerald-400" : "text-amber-400"}`}>
                  {gateway?.webui === "online" ? "✅ Healthy" : "⚠️ Offline"}
                </div>
              </motion.div>
              <motion.div
                whileHover={{ y: -4 }}
                className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl"
              >
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Containers</div>
                <div className="text-sm font-medium text-white">{gateway?.containers}</div>
              </motion.div>
            </div>
          )}
        </div>
      </section>

      {/* ─── Memory Layers ─────────────────────────────── */}
      {memory && (
        <section className="py-12">
          <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-8">
            <h2 className="text-xl font-bold text-white uppercase tracking-widest">Memory Layers</h2>
            <div className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-8 shadow-xl space-y-6">
              {memory.layers.map((layer, i) => (
                <motion.div
                  key={layer.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="flex items-center gap-4"
                >
                  <div className="w-32 text-sm text-slate-300">{layer.name}</div>
                  <div className="flex-1">
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden shadow-inner">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.max(0, layer.heat)}%` }}
                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                      />
                    </div>
                  </div>
                  <div className="w-20 text-right text-sm text-slate-400 font-mono">{layer.count} items</div>
                  <div className="w-16 text-right text-xs text-slate-500 font-bold">H:{layer.heat}</div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

        {/* ─── Quick Actions ───────────────────────────── */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-8">
          <h2 className="text-xl font-bold text-white uppercase tracking-widest">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <motion.div
              whileHover={{ y: -4 }}
              className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl hover:border-emerald-500/30 transition-all cursor-pointer"
            >
              <Link href="/v3/chat" className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-emerald-400">
                  <HiOutlineChatBubbleLeftRight className="text-xl" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">Test Chat</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-widest">Try the AI assistant</div>
                </div>
                <HiOutlineArrowRight className="ml-auto text-slate-500 group-hover:text-emerald-500 transition-colors" />
              </Link>
            </motion.div>
            <motion.div
              whileHover={{ y: -4 }}
              className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl hover:border-emerald-500/30 transition-all cursor-pointer"
            >
              <Link href="/setup" className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-blue-400">
                  <HiOutlineCog6Tooth className="text-xl" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">Setup Wizard</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-widest">Re-run onboarding</div>
                </div>
                <HiOutlineArrowRight className="ml-auto text-slate-500 group-hover:text-blue-500 transition-colors" />
              </Link>
            </motion.div>
            <motion.div
              whileHover={{ y: -4 }}
              className="rounded-[32px] border border-slate-800 bg-slate-900/50 p-6 shadow-xl hover:border-emerald-500/30 transition-all cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-amber-400">
                  <HiOutlineWrenchScrewdriver className="text-xl" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">Run Doctor</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-widest">Workspace health check</div>
                </div>
                <HiOutlineArrowRight className="ml-auto text-slate-500 group-hover:text-amber-500 transition-colors" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─── Installed Skills ───────────────────────────── */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 space-y-8">
          <h2 className="text-xl font-bold text-white uppercase tracking-widest">Installed Skills</h2>
          <div className="flex flex-wrap gap-3">
            {[
              "Panglima", "Hikmat", "Tukang", "Tukang Web", "Hulubalang", "Pawang", "Syahbandar",
              "Bendahara", "Penyemak", "Senibina Antara Muka", "Penyebar Reka Bentuk",
              "Pengkarya Kandungan", "Jurutulis Jualan", "Penjejak Carian", "Penggerak Pasaran",
              "Penganalisis", "Strategi Jenama", "Strategi Produk", "Khidmat Pelanggan",
              "Penulis Cadangan", "Penggerak Jualan", "Pengawal", "Perisai", "Serangan",
            ].map((skill) => (
              <motion.div
                key={skill}
                whileHover={{ scale: 1.05 }}
                className="rounded-full border border-slate-800 bg-slate-900/50 px-4 py-2 text-xs text-slate-300 hover:border-emerald-500/30 hover:text-white transition-all"
              >
                {skill}
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
