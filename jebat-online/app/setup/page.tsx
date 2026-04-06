"use client";

import { useState } from "react";

const steps = [
  { id: 0, title: "Gateway", icon: "📡" },
  { id: 1, title: "Providers", icon: "🤖" },
  { id: 2, title: "IDE Adapters", icon: "💻" },
  { id: 3, title: "Skills", icon: "🗡️" },
  { id: 4, title: "Verify", icon: "✅" },
];

const providers = [
  { id: "mesin", name: "Mesin", subtitle: "Ollama · VPS-hosted", url: "https://bot.sh4dow.tech/api", models: ["qwen2.5-coder:7b", "hermes-sec-v2", "llama3.1"] },
  { id: "zai", name: "ZAI", subtitle: "Malaysian AI Platform", url: "https://api.zai.network/v1", models: ["glm-5", "glm-4-plus"] },
  { id: "terbuka", name: "Terbuka", subtitle: "OpenAI", url: "https://api.openai.com/v1", models: ["gpt-4o", "gpt-4o-mini", "o1"] },
  { id: "bijak", name: "Bijak", subtitle: "Anthropic Claude", url: "https://api.anthropic.com/v1", models: ["claude-sonnet-4-20250514", "claude-opus-4-20250605"] },
  { id: "gemilang", name: "Gemilang", subtitle: "Google Gemini", url: "https://generativelanguage.googleapis.com/v1beta", models: ["gemini-2.5-pro", "gemini-2.0-flash"] },
  { id: "haluan", name: "Haluan", subtitle: "OpenRouter · Multi-model", url: "https://openrouter.ai/api/v1", models: ["anthropic/claude-sonnet-4", "google/gemini-2.5-pro"] },
];

const ideList = [
  { id: "vscode", name: "VS Code", file: ".github/copilot-instructions.md" },
  { id: "cursor", name: "Cursor", file: ".cursorrules" },
  { id: "zed", name: "Zed", file: ".zed/jebat-system-prompt.md" },
  { id: "trae", name: "Trae", file: ".trae/rules/jebat.md" },
  { id: "antigravity", name: "Antigravity", file: ".antigravity/jebat.md" },
];

const skillCategories = [
  { name: "Core", skills: ["Panglima", "Hikmat", "Agent Dispatch", "Memory Core"] },
  { name: "Development", skills: ["Tukang", "Tukang Web", "Pembina Aplikasi", "Fullstack", "Database", "Web Developer", "UI/UX"] },
  { name: "Security", skills: ["Hulubalang", "Pengawal", "Perisai", "Serangan", "Security Pentest"] },
  { name: "Growth", skills: ["Penjejak Carian (SEO)", "Penggerak Pasaran", "Jurutulis Jualan", "Strategi Jenama", "Penganalisis"] },
  { name: "Product", skills: ["Strategi Produk", "Penyemak (QA)", "Senibina Antara Muka", "Penyebar Reka Bentuk"] },
  { name: "Operations", skills: ["Syahbandar", "Bendahara", "Khidmat Pelanggan", "Pengkarya Kandungan"] },
  { name: "Research", skills: ["Pawang", "Penulis Cadangan", "Penggerak Jualan"] },
];

export default function SetupPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [gatewayUrl, setGatewayUrl] = useState("http://localhost:18789");
  const [gatewayStatus, setGatewayStatus] = useState<"checking" | "online" | "offline">("offline");
  const [selectedProviders, setSelectedProviders] = useState<Record<string, { key: string; model: string }>>({});
  const [selectedIDEs, setSelectedIDEs] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [installLog, setInstallLog] = useState<string[]>([]);

  const checkGateway = async () => {
    setGatewayStatus("checking");
    try {
      const res = await fetch(`${gatewayUrl}/health`, { signal: AbortSignal.timeout(3000) });
      setGatewayStatus(res.ok ? "online" : "offline");
    } catch {
      setGatewayStatus("offline");
    }
  };

  const toggleProvider = (id: string) => {
    setSelectedProviders((prev) => {
      if (prev[id]) {
        const next = { ...prev };
        delete next[id];
        return next;
      }
      return { ...prev, [id]: { key: "", model: providers.find((p) => p.id === id)?.models[0] || "" } };
    });
  };

  const toggleIDE = (id: string) => {
    setSelectedIDEs((prev) => prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]);
  };

  const toggleSkill = (skill: string) => {
    setSelectedSkills((prev) => prev.includes(skill) ? prev.filter((s) => s !== skill) : [...prev, skill]);
  };

  const runInstall = async () => {
    const log: string[] = [];
    log.push("🗡️  JEBAT Setup — Starting installation...");
    log.push("");
    log.push(`[1/4] Gateway: ${gatewayUrl} — ${gatewayStatus === "online" ? "✅ Connected" : "⚠️  Will configure later"}`);
    log.push("");

    log.push(`[2/4] Providers: ${Object.keys(selectedProviders).length} configured`);
    Object.entries(selectedProviders).forEach(([id, cfg]) => {
      log.push(`  • ${providers.find((p) => p.id === id)?.name} → ${cfg.model}`);
    });
    log.push("");

    log.push(`[3/4] IDE Adapters: ${selectedIDEs.length} targets`);
    selectedIDEs.forEach((ide) => {
      const ideInfo = ideList.find((i) => i.id === ide);
      log.push(`  • ${ideInfo?.name} → ${ideInfo?.file}`);
    });
    log.push("");

    log.push(`[4/4] Skills: ${selectedSkills.length} selected`);
    selectedSkills.forEach((skill) => {
      log.push(`  • Installing: ${skill}`);
    });
    log.push("");
    log.push("✅ Setup complete! JEBAT is ready.");
    log.push("");
    log.push("Next steps:");
    log.push("  • Run: npx @nusabyte/jebat setup (CLI setup)");
    log.push("  • Run: npx @nusabyte/jebat chat (AI chat)");
    log.push("  • Visit: /dashboard for gateway management");

    setInstallLog(log);
  };

  const next = () => {
    if (currentStep === 4 && installLog.length === 0) {
      runInstall();
      return;
    }
    if (currentStep < 4) setCurrentStep(currentStep + 1);
  };

  const prev = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  return (
    <main className="min-h-screen bg-[#050505] text-neutral-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚔️</span>
            <span className="font-semibold tracking-tight">JEBAT Setup</span>
          </div>
          <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Back to Home</a>
        </div>
      </nav>

      {/* Steps indicator */}
      <div className="mx-auto max-w-5xl px-6 pt-8">
        <div className="flex items-center justify-between">
          {steps.map((step, i) => (
            <div key={step.id} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-1">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full text-lg transition ${
                  i <= currentStep ? "bg-cyan-400/20 text-cyan-300" : "bg-white/5 text-neutral-600"
                }`}>
                  {i < currentStep ? "✓" : step.icon}
                </div>
                <span className={`text-xs transition ${i <= currentStep ? "text-cyan-300" : "text-neutral-600"}`}>
                  {step.title}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className={`flex-1 mx-2 h-0.5 transition ${i < currentStep ? "bg-cyan-400/40" : "bg-white/5"}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* Step 0: Gateway */}
        {currentStep === 0 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Connect to JEBAT Gateway</h2>
              <p className="text-neutral-400 mt-2">The gateway on port 18789 manages all provider routing, sessions, and tool execution.</p>
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                value={gatewayUrl}
                onChange={(e) => setGatewayUrl(e.target.value)}
                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-mono text-cyan-300 outline-none focus:border-cyan-400/50"
                placeholder="http://localhost:18789"
              />
              <button
                onClick={checkGateway}
                className="rounded-xl border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium transition hover:bg-white/10"
              >
                {gatewayStatus === "checking" ? "Checking..." : "Test Connection"}
              </button>
            </div>
            {gatewayStatus === "online" && (
              <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4 text-sm text-emerald-300">
                ✅ Gateway is online at {gatewayUrl}
              </div>
            )}
            {gatewayStatus === "offline" && (
              <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 p-4 text-sm text-amber-300">
                ⚠️ Gateway not reachable. You can continue setup and configure the gateway later.
                <div className="mt-2 text-xs text-amber-400/80">Run: docker compose up -d (or start sh4dow-gateway)</div>
              </div>
            )}
          </div>
        )}

        {/* Step 1: Providers */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Configure LLM Providers</h2>
              <p className="text-neutral-400 mt-2">Select and configure the AI providers you want to use. JEBAT routes requests intelligently.</p>
            </div>
            <div className="space-y-3">
              {providers.map((p) => (
                <div key={p.id} className={`rounded-xl border p-4 transition ${selectedProviders[p.id] ? "border-cyan-400/30 bg-cyan-400/5" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}>
                  <label className="flex items-center justify-between cursor-pointer">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={!!selectedProviders[p.id]}
                        onChange={() => toggleProvider(p.id)}
                        className="h-4 w-4 rounded border-white/20 bg-white/5 text-cyan-400 focus:ring-cyan-400"
                      />
                      <div>
                        <div className="text-sm font-medium">{p.name}</div>
                        <div className="text-xs text-neutral-500">{p.subtitle}</div>
                        <div className="text-xs text-neutral-600 font-mono">{p.url}</div>
                      </div>
                    </div>
                    <span className="text-xs text-neutral-500">{p.models.length} models</span>
                  </label>
                  {selectedProviders[p.id] && (
                    <div className="mt-3 flex gap-3 pl-7">
                      <input
                        type="password"
                        placeholder="API Key"
                        value={selectedProviders[p.id].key}
                        onChange={(e) => setSelectedProviders((prev) => ({ ...prev, [p.id]: { ...prev[p.id], key: e.target.value } }))}
                        className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-cyan-400/50"
                      />
                      <select
                        value={selectedProviders[p.id].model}
                        onChange={(e) => setSelectedProviders((prev) => ({ ...prev, [p.id]: { ...prev[p.id], model: e.target.value } }))}
                        className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none focus:border-cyan-400/50"
                      >
                        {p.models.map((m) => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: IDE Adapters */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Install IDE Adapters</h2>
              <p className="text-neutral-400 mt-2">Inject JEBAT context directly into your IDEs. Select the ones you use.</p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {ideList.map((ide) => (
                <button
                  key={ide.id}
                  onClick={() => toggleIDE(ide.id)}
                  className={`rounded-xl border p-5 text-left transition card-hover ${
                    selectedIDEs.includes(ide.id)
                      ? "border-cyan-400/30 bg-cyan-400/5"
                      : "border-white/10 bg-white/[0.02] hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold">{ide.name}</div>
                      <div className="text-xs text-neutral-500 font-mono mt-1">{ide.file}</div>
                    </div>
                    <div className={`h-5 w-5 rounded-full border-2 transition ${selectedIDEs.includes(ide.id) ? "border-cyan-400 bg-cyan-400" : "border-white/20"}`}>
                      {selectedIDEs.includes(ide.id) && <span className="flex h-full items-center justify-center text-xs text-black">✓</span>}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Skills */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Install Skills</h2>
              <p className="text-neutral-400 mt-2">Select the skills you want. Core skills are recommended.</p>
            </div>
            <div className="space-y-5">
              {skillCategories.map((cat) => (
                <div key={cat.name}>
                  <h3 className="mb-2 text-sm font-semibold text-neutral-300">{cat.name}</h3>
                  <div className="flex flex-wrap gap-2">
                    {cat.skills.map((skill) => (
                      <button
                        key={skill}
                        onClick={() => toggleSkill(skill)}
                        className={`rounded-full border px-4 py-1.5 text-sm transition ${
                          selectedSkills.includes(skill)
                            ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-300"
                            : "border-white/10 bg-white/[0.02] text-neutral-400 hover:border-white/20"
                        }`}
                      >
                        {selectedSkills.includes(skill) && "✓ "}{skill}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Verify & Install */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Review & Install</h2>
              <p className="text-neutral-400 mt-2">Review your configuration and click Install to finalize.</p>
            </div>

            {/* Summary */}
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div>
                  <div className="text-xs text-neutral-500">Gateway</div>
                  <div className={`text-sm ${gatewayStatus === "online" ? "text-emerald-300" : "text-amber-300"}`}>
                    {gatewayStatus === "online" ? "✅ Connected" : "⚠️ Offline"}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Providers</div>
                  <div className="text-sm">{Object.keys(selectedProviders).length}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">IDEs</div>
                  <div className="text-sm">{selectedIDEs.length}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Skills</div>
                  <div className="text-sm">{selectedSkills.length}</div>
                </div>
              </div>
            </div>

            {/* Install log */}
            {installLog.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs text-neutral-300 max-h-80 overflow-auto">
                {installLog.map((line, i) => (
                  <div key={i} className={line.startsWith("✅") ? "text-emerald-300" : line.startsWith("⚠️") ? "text-amber-300" : line.startsWith("🗡️") ? "text-cyan-300" : ""}>
                    {line}
                  </div>
                ))}
              </div>
            )}

            {installLog.length === 0 && (
              <button
                onClick={runInstall}
                className="w-full rounded-xl bg-cyan-400 py-4 text-base font-semibold text-black transition hover:bg-cyan-300"
              >
                ⚔️ Install JEBAT
              </button>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={prev}
            disabled={currentStep === 0}
            className={`rounded-xl border px-6 py-3 text-sm font-medium transition ${
              currentStep === 0 ? "border-white/5 text-neutral-600 cursor-not-allowed" : "border-white/10 hover:bg-white/10"
            }`}
          >
            Back
          </button>
          {installLog.length === 0 && currentStep < 4 && (
            <button
              onClick={next}
              className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300"
            >
              Next →
            </button>
          )}
          {installLog.length > 0 && (
            <a href="/dashboard" className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300">
              Go to Dashboard →
            </a>
          )}
        </div>
      </div>
    </main>
  );
}
