import type { Metadata } from "next";
export async function generateMetadata(): Promise<Metadata> {
  return { title: "Gelanggang Arena — LLM-to-LLM Multi-Agent Orchestration", description: "Watch AI models debate, collaborate, and compete. 5 orchestration modes from AutoGen, ChatDev 2.0, MAD Paradigm.", openGraph: { title: "Gelanggang Arena", description: "Watch AI models debate and collaborate in real-time.", type: "website", url: "https://jebat.online/gelanggang", siteName: "JEBAT AI Platform" }, twitter: { card: "summary_large_image", title: "Gelanggang Arena", description: "Watch AI models debate and collaborate." } };
}
export default function GelanggangLayout({ children }: { children: React.ReactNode }) { return <>{children}</>; }
