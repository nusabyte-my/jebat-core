"use client";

export function AgentShimmer({ agents, visible }: { agents: string[]; visible: boolean }) {
  if (!visible) return null;

  const agentIcons: Record<string, string> = {
    panglima: "⚔️", tukang: "🔧", "tukang-web": "🌐", hulubalang: "🛡️",
    pawang: "🔍", syahbandar: "⚙️", bendahara: "💾", penyemak: "✅",
    "senibina-antara-muka": "🎨", "penyebar-reka-bentuk": "📐",
    "pengkarya-kandungan": "📝", "juritulis-jualan": "✍️",
    "penjejak-carian": "🔎", "penggerak-pasaran": "📣",
    penganalisis: "📊", "strategi-jenama": "💎", "strategi-produk": "🎯",
    "khidmat-pelanggan": "🤝", "penulis-cadangan": "📋",
    "penggerak-jualan": "💼", pengawal: "🔒", perisai: "🛡️",
    serangan: "⚡", hikmat: "🧠", "memory-core": "💭",
  };

  return (
    <div className="flex items-center gap-3 py-2 animate-fade-in">
      {agents.map((agent) => (
        <div key={agent} className="flex items-center gap-1.5">
          <div className="relative">
            <span className="text-lg animate-pulse">{agentIcons[agent] || "🤖"}</span>
            <div className="absolute inset-0 rounded-full bg-cyan-400/20 animate-ping" />
          </div>
          <span className="text-xs text-cyan-300/80 font-medium capitalize">
            {agent.replace(/-/g, " ")}
          </span>
        </div>
      ))}
      {agents.length === 0 && (
        <div className="flex items-center gap-1.5">
          <div className="relative">
            <span className="text-lg animate-pulse">🤖</span>
            <div className="absolute inset-0 rounded-full bg-cyan-400/20 animate-ping" />
          </div>
          <span className="text-xs text-cyan-300/80 font-medium">Loading agent...</span>
        </div>
      )}
    </div>
  );
}
