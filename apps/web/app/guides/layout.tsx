import type { Metadata } from "next";
export async function generateMetadata(): Promise<Metadata> {
  return { title: "JEBAT Setup Guides — IDE Integration, Models, Channels, Migration", description: "Step-by-step guides for IDE integration, channel setup, model deployment, migration, and production hardening.", openGraph: { title: "JEBAT Setup Guides", description: "Comprehensive setup documentation for JEBAT.", type: "website", url: "https://jebat.online/guides", siteName: "JEBAT AI Platform" }, twitter: { card: "summary_large_image", title: "JEBAT Setup Guides", description: "Step-by-step setup documentation." } };
}
export default function GuidesLayout({ children }: { children: React.ReactNode }) { return <>{children}</>; }
