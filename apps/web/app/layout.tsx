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
  title: "JEBAT AI Agent Platform — Multi-Agent Orchestration & Self-Hosted AI",
  description:
    "JEBAT is the enterprise AI agent platform with multi-agent orchestration, 10 core agents, 24 specialists, 5 orchestration modes, 8 local LLM models, and 5 providers (Anthropic, OpenAI, Gemini, Ollama, ZAI). 100% self-hosted, no cloud dependency. Built by NusaByte, Malaysia AI Platform.",
  keywords: [
    "JEBAT AI Agent Platform", "Multi-Agent Orchestration", "Self-Hosted AI",
    "Enterprise AI", "LLM Debate", "Local Models", "Ollama", "Malaysia AI Platform",
    "Anthropic Claude", "OpenAI", "Gemini", "ZAI", "ConfMAD", "LLM-as-Judge",
    "Prompt Injection Defense", "CyberSec AI", "NusaByte", "Privacy-First AI",
  ],
  openGraph: {
    title: "JEBAT — Self-Hosted Multi-Agent AI Platform",
    description: "10 core agents, 24 specialists, 8 local LLMs, 5 providers. 100% self-hosted enterprise AI.",
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
      <head>
        <meta name="theme-color" content="#050505"/>
        <meta name="apple-mobile-web-app-capable" content="yes"/>
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@graph": [
                {
                  "@type": "Organization",
                  "@id": "https://jebat.online#organization",
                  "name": "NusaByte",
                  "url": "https://nusabyte.my",
                  "logo": {
                    "@type": "ImageObject",
                    "url": "https://jebat.online/logo.png",
                  },
                  "sameAs": [
                    "https://github.com/nusabyte-my/jebat-core",
                    "https://github.com/nusabyte-my",
                  ],
                },
                {
                  "@type": "SoftwareApplication",
                  "@id": "https://jebat.online#software",
                  "name": "JEBAT AI Agent Platform",
                  "applicationCategory": "BusinessApplication",
                  "operatingSystem": "Linux, macOS, Windows",
                  "url": "https://jebat.online",
                  "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "MYR",
                  },
                  "featureList": [
                    "Multi-Agent Orchestration",
                    "Self-Hosted AI",
                    "8 Local LLM Models",
                    "5 LLM Providers",
                    "Enterprise Security",
                    "LLM-as-Judge Consensus",
                    "Confidence Scoring (ConfMAD)",
                    "Markdown Rendering",
                    "LRUCache Optimization",
                    "Customer Portal",
                  ],
                  "provider": { "@id": "https://jebat.online#organization" },
                },
              ],
            }),
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        {children}
        <script dangerouslySetInnerHTML={{
          __html: `
            if ('serviceWorker' in navigator) {
              window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').then((reg) => {
                  console.log('[PWA] Service Worker registered');
                }).catch((err) => {
                  console.log('[PWA] Service Worker registration failed:', err);
                });
              });
            }
          `
        }} />
      </body>
    </html>
  );
}
