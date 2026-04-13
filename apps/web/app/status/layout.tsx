import type { Metadata } from "next";
export async function generateMetadata(): Promise<Metadata> {
  return { title: "JEBAT System Status — Service Monitoring & Uptime", description: "Real-time monitoring of all JEBAT services. 99.97% uptime, 8 services online, 5 npm packages, 9 live pages.", openGraph: { title: "JEBAT System Status", description: "Real-time service monitoring dashboard.", type: "website", url: "https://jebat.online/status", siteName: "JEBAT AI Platform" }, twitter: { card: "summary_large_image", title: "JEBAT System Status", description: "Real-time service monitoring." } };
}
export default function StatusLayout({ children }: { children: React.ReactNode }) { return <>{children}</>; }
