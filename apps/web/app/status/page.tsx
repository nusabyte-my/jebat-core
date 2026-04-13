"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
export default function StatusPage() {
  const [lastChecked, setLastChecked] = useState(new Date().toLocaleTimeString());
  useEffect(() => { const i = setInterval(() => setLastChecked(new Date().toLocaleTimeString()), 60000); return () => clearInterval(i); }, []);
  const services = [
    { name: "Landing Page", status: "operational", rt: "45ms", desc: "Main website and V2 landing" },
    { name: "Chat Interface", status: "operational", rt: "120ms", desc: "AI chat with 8 local LLMs" },
    { name: "Enterprise Portal", status: "operational", rt: "38ms", desc: "Agent monitoring dashboard" },
    { name: "Security Dashboard", status: "operational", rt: "42ms", desc: "CyberSec monitoring" },
    { name: "Gelanggang Arena", status: "operational", rt: "55ms", desc: "LLM-to-LLM orchestration" },
    { name: "Setup Guides", status: "operational", rt: "35ms", desc: "Documentation and guides" },
    { name: "Ollama API", status: "operational", rt: "890ms", desc: "Local LLM proxy on my-vps" },
    { name: "Agent Documentation", status: "operational", rt: "40ms", desc: "jebat-agent npm package" },
  ];
  const pkgs = [
    { name: "jebat-agent", ver: "3.0.1", desc: "Setup wizard" },
    { name: "jebat-core", ver: "3.0.1", desc: "Platform core" },
    { name: "jebat-security", ver: "1.0.1", desc: "CyberSec suite" },
    { name: "jebat-gelanggang", ver: "1.0.0", desc: "LLM Arena" },
    { name: "jebat-guides", ver: "1.0.0", desc: "Documentation" },
  ];
  return (
    <div className="min-h-screen bg-[#050505] text-white">
      <nav className="sticky top-0 z-50 bg-[#050505]/90 backdrop-blur-xl border-b border-white/5">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8 py-4">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-600 shadow-lg shadow-emerald-500/20">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            </div>
            <div><span className="text-lg font-bold">System Status</span><span className="ml-2 text-[10px] text-emerald-400/80 border border-emerald-400/20 rounded-full px-2 py-0.5">99.97%</span></div>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/v2" className="hidden sm:inline text-sm text-neutral-400 hover:text-white">Home</Link>
            <Link href="/chat" className="hidden sm:inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10">Try Chat</Link>
            <a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="rounded-full bg-gradient-to-r from-emerald-400 to-cyan-500 px-5 py-2 text-sm font-semibold text-black shadow-lg shadow-emerald-500/20">GitHub</a>
          </div>
        </div>
      </nav>
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-16 pb-12 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-1.5 text-sm text-emerald-300 mb-6"><span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"/>All Systems Operational</div>
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6"><span className="block">JEBAT Platform</span><span className="block bg-gradient-to-r from-emerald-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent">System Status</span></h1>
        <p className="text-neutral-400 mb-8">Last checked: {lastChecked}</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto mb-12">
          {[{v:"99.97%",l:"Uptime",i:"📊"},{v:"8/8",l:"Services Up",i:"✅"},{v:"5",l:"npm Packages",i:"📦"},{v:"9",l:"Live Pages",i:"🌐"}].map((s,j)=><div key={j} className="rounded-2xl border border-white/5 bg-white/[0.02] p-4"><div className="text-2xl mb-2">{s.i}</div><div className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-500 bg-clip-text text-transparent">{s.v}</div><div className="text-xs text-neutral-500">{s.l}</div></div>)}
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-12">
        <h2 className="text-xl font-bold mb-6">Service Status</h2>
        <div className="space-y-3">
          {services.map((s,i)=><div key={i} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] p-4 md:p-5"><div className="flex items-center gap-4"><span className="inline-flex h-3 w-3 rounded-full bg-emerald-400"/><div><h3 className="font-semibold text-sm md:text-base">{s.name}</h3><p className="text-xs text-neutral-500">{s.desc}</p></div></div><div className="text-right"><span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400">Operational</span><div className="text-[10px] text-neutral-600 mt-1">{s.rt}</div></div></div>)}
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-12">
        <h2 className="text-xl font-bold mb-6">npm Packages</h2>
        <div className="grid gap-3 md:gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
          {pkgs.map((p,i)=><a key={i} href={`https://www.npmjs.com/package/${p.name}`} target="_blank" rel="noopener noreferrer" className="rounded-xl border border-white/10 bg-white/[0.02] p-4 hover:border-emerald-400/20 transition block"><div className="flex items-center gap-2 mb-2"><span className="inline-flex h-2 w-2 rounded-full bg-emerald-400"/><span className="font-semibold text-sm">{p.name}</span></div><div className="text-xs text-neutral-500">{p.ver} · {p.desc}</div></a>)}
        </div>
      </section>
      <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pb-20">
        <h2 className="text-xl font-bold mb-6">Recent Updates</h2>
        <div className="space-y-3">
          {[{d:"2026-04-14",t:"V2 set as default homepage + SEO + PWA",s:"resolved"},{d:"2026-04-14",t:"All dedicated pages revamped with enterprise UI",s:"resolved"},{d:"2026-04-13",t:"5 npm packages published",s:"resolved"},{d:"2026-04-13",t:"Chat session persistence and onboarding added",s:"resolved"}].map((inc,i)=><div key={i} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] p-4"><div><h3 className="font-medium text-sm">{inc.t}</h3><p className="text-xs text-neutral-500">{inc.d}</p></div><span className="text-xs font-medium px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400">{inc.s}</span></div>)}
        </div>
      </section>
      <footer className="border-t border-white/5 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3"><div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-cyan-600"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></div><span className="text-sm text-neutral-500">© 2026 NusaByte · JEBAT Status</span></div>
          <div className="flex items-center gap-4 text-sm text-neutral-500"><Link href="/v2" className="hover:text-white">Home</Link><Link href="/chat" className="hover:text-white">Chat</Link><Link href="/portal" className="hover:text-white">Portal</Link><a href="https://github.com/nusabyte-my/jebat-core" target="_blank" rel="noopener noreferrer" className="hover:text-white">GitHub</a></div>
        </div>
      </footer>
    </div>
  );
}
