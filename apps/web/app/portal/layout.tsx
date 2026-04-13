import type { Metadata } from "next";
export async function generateMetadata(): Promise<Metadata> {
  return { title: "JEBAT Enterprise Portal — Agent Monitoring & Analytics", description: "Monitor 34 AI agents, track usage analytics, measure performance metrics. Real-time enterprise dashboard.", openGraph: { title: "JEBAT Enterprise Portal", description: "Monitor 34 AI agents with real-time analytics.", type: "website", url: "https://jebat.online/portal", siteName: "JEBAT AI Platform" }, twitter: { card: "summary_large_image", title: "JEBAT Enterprise Portal", description: "Monitor 34 AI agents with real-time analytics." } };
}
export default function PortalLayout({ children }: { children: React.ReactNode }) { return <>{children}</>; }
