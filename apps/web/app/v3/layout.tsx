"use client";

import Header from "./components/Header";

export default function V3Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-[#0F172A] text-slate-200 min-h-screen flex flex-col font-sans">
      <Header />
      <div className="pt-20 flex-1 flex flex-col">
        {children}
      </div>
    </div>
  );
}
