import type { Metadata } from "next";

const meta = {
  title: "JEBAT Security Dashboard — CyberSec Suite & Penetration Testing",
  desc: "Four-layer security suite: Hulubalang (audit), Pengawal (defense), Perisai (hardening), Serangan (pentest). Military-grade self-hosted AI security.",
};

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: meta.title,
    description: meta.desc,
    openGraph: { title: meta.title, description: meta.desc, type: "website", url: "https://jebat.online/security", siteName: "JEBAT AI Platform" },
    twitter: { card: "summary_large_image", title: meta.title, description: meta.desc },
  };
}

export default function SecurityLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
