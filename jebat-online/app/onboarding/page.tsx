"use client";

import { useState } from "react";
import Link from "next/link";

const steps = [
  { id: 0, title: "Who", icon: "👤" },
  { id: 1, title: "Environment", icon: "💻" },
  { id: 2, title: "Experience", icon: "🔧" },
  { id: 3, title: "Needs", icon: "🎯" },
  { id: 4, title: "Setup", icon: "🚀" },
];

const roles = [
  { id: "developer", label: "Developer", emoji: "👨‍💻" },
  { id: "designer", label: "Designer", emoji: "🎨" },
  { id: "pentester", label: "Pentester / Security", emoji: "🛡️" },
  { id: "devops", label: "DevOps / Infra", emoji: "⚙️" },
  { id: "pm", label: "Project Manager", emoji: "📋" },
  { id: "student", label: "Student / Learner", emoji: "📚" },
  { id: "other", label: "Other", emoji: "🤷" },
];

const envs = [
  { id: "linux", label: "Linux", emoji: "🐧" },
  { id: "macos", label: "macOS", emoji: "🍎" },
  { id: "windows", label: "Windows", emoji: "🪟" },
  { id: "docker", label: "Docker", emoji: "🐳" },
  { id: "vps", label: "VPS / Cloud", emoji: "☁️" },
];

const editors = [
  { id: "vscode", label: "VS Code", emoji: "🔵" },
  { id: "cursor", label: "Cursor", emoji: "⚡" },
  { id: "zed", label: "Zed", emoji: "💎" },
  { id: "claude", label: "Claude Code", emoji: "🤖" },
  { id: "other", label: "Other", emoji: "✏️" },
];

const needs = [
  { id: "coding", label: "Code assistance & generation", emoji: "💻" },
  { id: "security", label: "Security auditing & pentesting", emoji: "🛡️" },
  { id: "memory", label: "AI that remembers context", emoji: "🧠" },
  { id: "agents", label: "Multi-agent task delegation", emoji: "⚔️" },
  { id: "deploy", label: "Deployment & infrastructure", emoji: "🚀" },
  { id: "research", label: "Research & documentation", emoji: "📖" },
  { id: "automation", label: "Automation & scripting", emoji: "⚡" },
  { id: "learning", label: "Learning & skill building", emoji: "📚" },
];

const experienceLevels = [
  { id: "beginner", label: "Beginner — Just getting started" },
  { id: "intermediate", label: "Intermediate — Comfortable with basics" },
  { id: "advanced", label: "Advanced — Ship things regularly" },
  { id: "expert", label: "Expert — I build the tools others use" },
];

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [profile, setProfile] = useState({
    role: "",
    name: "",
    experience: "",
    environments: [] as string[],
    editors: [] as string[],
    needs: [] as string[],
    description: "",
  });
  const [setupLog, setSetupLog] = useState<string[]>([]);

  const toggle = (field: string, value: string) => {
    setProfile((prev) => {
      const arr = prev[field as keyof typeof prev] as string[];
      return { ...prev, [field]: arr.includes(value) ? arr.filter((v: string) => v !== value) : [...arr, value] };
    });
  };

  const runSetup = () => {
    const log: string[] = [];
    log.push("⚔️  JEBAT Onboarding — Setting up your workspace...\n");
    log.push(`👤 Role: ${roles.find(r => r.id === profile.role)?.label || profile.role}`);
    log.push(`💻 Experience: ${experienceLevels.find(e => e.id === profile.experience)?.label || profile.experience}`);
    log.push(`💻 Environments: ${profile.environments.join(", ")}`);
    log.push(`✏️ Editors: ${profile.editors.join(", ")}`);
    log.push(`🎯 Needs: ${profile.needs.map(n => needs.find(ne => ne.id === n)?.label || n).join(", ")}`);
    if (profile.description) log.push(`📝 Description: ${profile.description}`);
    log.push("");
    log.push("[1/3] Installing IDE adapters...");
    profile.editors.forEach((e) => log.push(`  ✅ ${editors.find(ed => ed.id === e)?.label || e} context installed`));
    log.push("");
    log.push("[2/3] Configuring skills for your needs...");
    if (profile.needs.includes("security")) log.push("  ✅ Hulubalang + Pengawal + Perisai + Serangan activated");
    if (profile.needs.includes("coding")) log.push("  ✅ Tukang + Tukang Web + Pembina Aplikasi activated");
    if (profile.needs.includes("memory")) log.push("  ✅ Hikmat memory engine initialized");
    if (profile.needs.includes("agents")) log.push("  ✅ Panglima orchestration configured");
    if (profile.needs.includes("deploy")) log.push("  ✅ Syahbandar + Bendahara activated");
    if (profile.needs.includes("research")) log.push("  ✅ Pawang researcher configured");
    if (profile.needs.includes("automation")) log.push("  ✅ Syahbandar automation activated");
    if (profile.needs.includes("learning")) log.push("  ✅ All skills set to learning mode");
    log.push("");
    log.push("[3/3] Connecting to gateway...");
    log.push("  ✅ jebat-gateway on port 18789 ready");
    log.push("");
    log.push("✅ You're all set! JEBAT knows you now.");
    log.push("");
    log.push("Next: Try the demo, explore skills, or start chatting.");

    setSetupLog(log);
  };

  const next = () => {
    if (currentStep === 4 && setupLog.length === 0) {
      runSetup();
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
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚔️</span>
            <span className="font-semibold tracking-tight">JEBAT — Let's Get to Know You</span>
          </div>
          <a href="/" className="text-sm text-neutral-400 transition hover:text-white">← Home</a>
        </div>
      </nav>

      {/* Steps indicator */}
      <div className="mx-auto max-w-3xl px-6 pt-8">
        <div className="flex items-center justify-between">
          {steps.map((step, i) => (
            <div key={step.id} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-1">
                <div className={`flex h-10 w-10 items-center justify-center rounded-full text-lg transition ${i <= currentStep ? "bg-cyan-400/20 text-cyan-300" : "bg-white/5 text-neutral-600"}`}>
                  {i < currentStep ? "✓" : step.icon}
                </div>
                <span className={`text-xs transition ${i <= currentStep ? "text-cyan-300" : "text-neutral-600"}`}>{step.title}</span>
              </div>
              {i < steps.length - 1 && (
                <div className={`flex-1 mx-2 h-0.5 transition ${i < currentStep ? "bg-cyan-400/40" : "bg-white/5"}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="mx-auto max-w-3xl px-6 py-8 space-y-6">
        {/* Step 0: Who */}
        {currentStep === 0 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Who are you?</h2>
              <p className="text-neutral-400 mt-2">Tell us your role so JEBAT can tailor the experience.</p>
            </div>
            <input
              type="text"
              placeholder="What should we call you? (optional)"
              value={profile.name}
              onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none focus:border-cyan-400/50 placeholder:text-neutral-600"
            />
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
              {roles.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setProfile((p) => ({ ...p, role: r.id }))}
                  className={`rounded-xl border p-4 text-left transition card-hover ${profile.role === r.id ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}
                >
                  <div className="text-2xl mb-1">{r.emoji}</div>
                  <div className="text-sm font-medium">{r.label}</div>
                </button>
              ))}
            </div>
            <textarea
              placeholder="Anything else we should know about you? (optional)"
              value={profile.description}
              onChange={(e) => setProfile((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none focus:border-cyan-400/50 placeholder:text-neutral-600 resize-none"
            />
          </div>
        )}

        {/* Step 1: Environment */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Your environment</h2>
              <p className="text-neutral-400 mt-2">Where do you work? Select all that apply.</p>
            </div>
            <div>
              <div className="text-sm font-medium text-neutral-300 mb-3">Operating System / Platform</div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                {envs.map((e) => (
                  <button
                    key={e.id}
                    onClick={() => toggle("environments", e.id)}
                    className={`rounded-xl border p-4 text-left transition card-hover ${profile.environments.includes(e.id) ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}
                  >
                    <div className="text-2xl mb-1">{e.emoji}</div>
                    <div className="text-sm font-medium">{e.label}</div>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-neutral-300 mb-3">Code Editor / IDE</div>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                {editors.map((e) => (
                  <button
                    key={e.id}
                    onClick={() => toggle("editors", e.id)}
                    className={`rounded-xl border p-4 text-left transition card-hover ${profile.editors.includes(e.id) ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}
                  >
                    <div className="text-2xl mb-1">{e.emoji}</div>
                    <div className="text-sm font-medium">{e.label}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Experience */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Your experience level</h2>
              <p className="text-neutral-400 mt-2">Be honest — JEBAT adjusts complexity based on this.</p>
            </div>
            <div className="space-y-3">
              {experienceLevels.map((e) => (
                <button
                  key={e.id}
                  onClick={() => setProfile((p) => ({ ...p, experience: e.id }))}
                  className={`w-full rounded-xl border p-4 text-left transition card-hover ${profile.experience === e.id ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}
                >
                  <div className="text-sm font-medium">{e.label}</div>
                </button>
              ))}
            </div>
            <div>
              <div className="text-sm font-medium text-neutral-300 mb-3">What have you built or worked on recently?</div>
              <textarea
                placeholder="e.g. A Next.js dashboard, a Python API, a pentest report..."
                value={profile.description}
                onChange={(e) => setProfile((p) => ({ ...p, description: e.target.value }))}
                rows={4}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm outline-none focus:border-cyan-400/50 placeholder:text-neutral-600 resize-none"
              />
            </div>
          </div>
        )}

        {/* Step 3: Needs */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">What do you need JEBAT for?</h2>
              <p className="text-neutral-400 mt-2">Select all that apply. JEBAT will activate the right skills.</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {needs.map((n) => (
                <button
                  key={n.id}
                  onClick={() => toggle("needs", n.id)}
                  className={`rounded-xl border p-4 text-left transition card-hover ${profile.needs.includes(n.id) ? "border-cyan-400/30 bg-cyan-400/10" : "border-white/10 bg-white/[0.02] hover:border-white/20"}`}
                >
                  <div className="text-2xl mb-1">{n.emoji}</div>
                  <div className="text-sm font-medium">{n.label}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Setup & Summary */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold">Ready to set up</h2>
              <p className="text-neutral-400 mt-2">Here's what JEBAT knows about you. Click to install.</p>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-neutral-500">Role</div>
                  <div className="text-sm">{roles.find(r => r.id === profile.role)?.label || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Experience</div>
                  <div className="text-sm">{experienceLevels.find(e => e.id === profile.experience)?.label || "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Environments</div>
                  <div className="text-sm">{profile.environments.length > 0 ? profile.environments.join(", ") : "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-neutral-500">Editors</div>
                  <div className="text-sm">{profile.editors.length > 0 ? profile.editors.join(", ") : "—"}</div>
                </div>
              </div>
              <div>
                <div className="text-xs text-neutral-500">Needs</div>
                <div className="flex flex-wrap gap-2 mt-1">
                  {profile.needs.map(n => (
                    <span key={n} className="rounded-full border border-cyan-400/20 bg-cyan-400/5 px-3 py-1 text-xs text-cyan-300">
                      {needs.find(ne => ne.id === n)?.emoji} {needs.find(ne => ne.id === n)?.label}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {setupLog.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-black/40 p-4 font-mono text-xs text-neutral-300 max-h-80 overflow-auto">
                {setupLog.map((line, i) => (
                  <div key={i} className={line.startsWith("✅") ? "text-emerald-300" : line.startsWith("⚔️") ? "text-cyan-300" : ""}>
                    {line}
                  </div>
                ))}
              </div>
            )}

            {setupLog.length === 0 && (
              <button
                onClick={runSetup}
                className="w-full rounded-xl bg-cyan-400 py-4 text-base font-semibold text-black transition hover:bg-cyan-300"
              >
                ⚔️ Set Up JEBAT
              </button>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={prev}
            disabled={currentStep === 0}
            className={`rounded-xl border px-6 py-3 text-sm font-medium transition ${currentStep === 0 ? "border-white/5 text-neutral-600 cursor-not-allowed" : "border-white/10 hover:bg-white/10"}`}
          >
            Back
          </button>
          {setupLog.length === 0 && currentStep < 4 && (
            <button onClick={next} className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300">
              Next →
            </button>
          )}
          {setupLog.length > 0 && (
            <div className="flex gap-3">
              <Link href="/demo" className="rounded-xl border border-white/10 px-6 py-3 text-sm font-medium transition hover:bg-white/10">Try Demo</Link>
              <Link href="/dashboard" className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300">Go to Dashboard →</Link>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
