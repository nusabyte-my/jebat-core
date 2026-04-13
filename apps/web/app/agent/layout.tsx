import type { Metadata } from "next";
export async function generateMetadata(): Promise<Metadata> {
  return { title: "Jebat Agent — 30-Second AI Workspace Setup with 8 Local LLMs", description: "Deploy your AI workspace in 30 seconds. IDE integration, 8 local LLMs, channel setup, and migration.", openGraph: { title: "Jebat Agent — 30-Second AI Workspace Setup", description: "Deploy your AI workspace in 30 seconds with 8 local LLMs.", type: "website", url: "https://jebat.online/agent", siteName: "JEBAT AI Platform" }, twitter: { card: "summary_large_image", title: "Jebat Agent — 30-Second AI Workspace Setup", description: "Deploy your AI workspace in 30 seconds." } };
}
export default function AgentLayout({ children }: { children: React.ReactNode }) { return <>{children}</>; }
