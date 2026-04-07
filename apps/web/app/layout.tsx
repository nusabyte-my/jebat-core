import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "JEBAT — The LLM Ecosystem That Remembers Everything",
  description:
    "Eternal memory. Multi-agent orchestration. 6 thinking modes. CyberSec assistant. Self-hosted, privacy-first. Built by NusaByte.",
  keywords: [
    "JEBAT", "AI assistant", "LLM", "memory", "agent orchestration",
    "cybersecurity", "self-hosted", "NusaByte", "OpenClaw", "Pengawal",
  ],
  openGraph: {
    title: "JEBAT — AI Ecosystem",
    description: "The LLM Ecosystem That Remembers Everything",
    type: "website",
    url: "https://jebat.online",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
