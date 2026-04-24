import type { Metadata } from "next";
import "./globals.css";
import ServiceWorkerRegistration from "./components/ServiceWorkerRegistration";

export const metadata: Metadata = {
  metadataBase: new URL("https://jebat.online"),
  title: "JEBAT | Sovereign AI Control Plane",
  description:
    "JEBAT is a sovereign AI control plane for governed agents, model routing, private memory, and operator workflows across self-hosted, VPC, and private infrastructure deployments.",
  keywords: [
    "JEBAT",
    "Sovereign AI",
    "AI control plane",
    "Private AI infrastructure",
    "Multi-agent orchestration",
    "Self-hosted AI",
    "Operator console",
    "NusaByte",
  ],
  openGraph: {
    title: "JEBAT | Sovereign AI Control Plane",
    description:
      "Private AI infrastructure for teams that need governed automation, self-hosted model routing, and operator-grade control surfaces.",
    type: "website",
    url: "https://jebat.online",
    siteName: "JEBAT",
  },
  twitter: {
    card: "summary",
    title: "JEBAT | Sovereign AI Control Plane",
    description:
      "Private AI infrastructure for governed agents, model routing, memory, and operator workflows.",
  },
  icons: {
    icon: "/favicon.svg",
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
      className="h-full antialiased"
      suppressHydrationWarning
      data-scroll-behavior="smooth"
    >
      <head>
        <meta name="theme-color" content="#020617"/>
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
                    "url": "https://jebat.online/favicon.svg",
                  },
                  "sameAs": [
                    "https://github.com/nusabyte-my/jebat-core",
                    "https://github.com/nusabyte-my",
                  ],
                },
                {
                  "@type": "SoftwareApplication",
                  "@id": "https://jebat.online#software",
                  "name": "JEBAT Control Plane",
                  "applicationCategory": "BusinessApplication",
                  "operatingSystem": "Linux, macOS, Windows",
                  "url": "https://jebat.online",
                  "featureList": [
                    "Governed multi-agent orchestration",
                    "Private model routing and failover",
                    "Operator WebUI and CLI control surfaces",
                    "Persistent memory and runtime context",
                    "Security-oriented control and audit posture",
                    "Self-hosted and private infrastructure deployment",
                  ],
                  "provider": { "@id": "https://jebat.online#organization" },
                },
              ],
            }),
          }}
        />
      </head>
      <body className="min-h-full flex flex-col">
        <ServiceWorkerRegistration />
        {children}
      </body>
    </html>
  );
}
