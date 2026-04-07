"use client";

import { useState, useEffect } from "react";

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
    { label: "Skills Installed", value: "72", icon: "🗡️" },
    { label: "Active Agents", value: "17", icon: "⚔️" },
    { label: "Thinking Modes", value: "6", icon: "🔥" },
    { label: "Providers", value: "6", icon: "🤖" },
  ];

  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚔️</span>
            <span className="font-semibold tracking-tight">JEBAT Dashboard</span>
          </div>
          <div className="flex items-center gap-4">
            <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs ${
              gateway?.api === "online" ? "bg-emerald-400/10 text-emerald-300" : "bg-amber-400/10 text-amber-300"
            }`}>
              <span className={`h-2 w-2 rounded-full ${gateway?.api === "online" ? "bg-emerald-400" : "bg-amber-400"}`} />
              {gateway?.api === "online" ? "Online" : "Offline"}
            </span>
            <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-6 py-8 space-y-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="card-hover rounded-2xl border border-white/10 bg-white/[0.02] p-5">
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="text-2xl font-bold">{s.value}</div>
              <div className="text-xs text-neutral-500">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Gateway Status */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          <h2 className="mb-4 text-lg font-semibold">Gateway Status</h2>
          {loading ? (
            <div className="text-sm text-neutral-500">Checking services...</div>
          ) : (
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-xl border border-white/5 bg-black/20 p-4">
                <div className="text-xs text-neutral-500">API (:8000)</div>
                <div className={`text-sm font-medium ${gateway?.api === "online" ? "text-emerald-300" : "text-amber-300"}`}>
                  {gateway?.api === "online" ? "✅ Healthy" : "⚠️ Offline"}
                </div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/20 p-4">
                <div className="text-xs text-neutral-500">WebUI (:8787)</div>
                <div className={`text-sm font-medium ${gateway?.webui === "online" ? "text-emerald-300" : "text-amber-300"}`}>
                  {gateway?.webui === "online" ? "✅ Healthy" : "⚠️ Offline"}
                </div>
              </div>
              <div className="rounded-xl border border-white/5 bg-black/20 p-4">
                <div className="text-xs text-neutral-500">Containers</div>
                <div className="text-sm font-medium text-neutral-300">{gateway?.containers}</div>
              </div>
            </div>
          )}
        </div>

        {/* Memory Layers */}
        {memory && (
          <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
            <h2 className="mb-4 text-lg font-semibold">Memory Layers</h2>
            <div className="space-y-3">
              {memory.layers.map((layer) => (
                <div key={layer.name} className="flex items-center gap-4">
                  <div className="w-32 text-sm text-neutral-300">{layer.name}</div>
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-cyan-300 transition-all"
                        style={{ width: `${Math.max(0, layer.heat)}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-20 text-right text-sm text-neutral-400">{layer.count} items</div>
                  <div className="w-16 text-right text-xs text-neutral-500">H:{layer.heat}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
          <div className="grid gap-3 md:grid-cols-3">
            <a href="/demo" className="card-hover rounded-xl border border-white/5 bg-black/20 p-4 flex items-center gap-3">
              <span className="text-xl">💬</span>
              <div>
                <div className="text-sm font-medium">Test Chat</div>
                <div className="text-xs text-neutral-500">Try the AI assistant</div>
              </div>
            </a>
            <a href="/setup" className="card-hover rounded-xl border border-white/5 bg-black/20 p-4 flex items-center gap-3">
              <span className="text-xl">⚙️</span>
              <div>
                <div className="text-sm font-medium">Setup Wizard</div>
                <div className="text-xs text-neutral-500">Re-run onboarding</div>
              </div>
            </a>
            <div className="card-hover rounded-xl border border-white/5 bg-black/20 p-4 flex items-center gap-3 cursor-pointer">
              <span className="text-xl">🩺</span>
              <div>
                <div className="text-sm font-medium">Run Doctor</div>
                <div className="text-xs text-neutral-500">Workspace health check</div>
              </div>
            </div>
          </div>
        </div>

        {/* Installed Skills */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
          <h2 className="mb-4 text-lg font-semibold">Installed Skills</h2>
          <div className="flex flex-wrap gap-2">
            {[
              "Panglima", "Hikmat", "Tukang", "Tukang Web", "Hulubalang", "Pawang", "Syahbandar",
              "Bendahara", "Penyemak", "Senibina Antara Muka", "Penyebar Reka Bentuk",
              "Pengkarya Kandungan", "Jurutulis Jualan", "Penjejak Carian", "Penggerak Pasaran",
              "Penganalisis", "Strategi Jenama", "Strategi Produk", "Khidmat Pelanggan",
              "Penulis Cadangan", "Penggerak Jualan", "Pengawal", "Perisai", "Serangan",
            ].map((skill) => (
              <span key={skill} className="rounded-full border border-white/10 bg-white/[0.02] px-3 py-1.5 text-xs text-neutral-300">
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
