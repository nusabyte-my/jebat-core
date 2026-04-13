import type { Metadata } from "next";

export function generatePageMetadata(
  title: string,
  description: string,
  path: string = "",
  keywords: string[] = []
): Metadata {
  const fullTitle = title.includes("JEBAT") ? title : `${title} | JEBAT AI Platform`;
  return {
    title: fullTitle,
    description,
    keywords: ["JEBAT", "AI Platform", "Multi-Agent", "Self-Hosted AI", ...keywords],
    openGraph: {
      title: fullTitle,
      description,
      type: "website",
      url: `https://jebat.online${path}`,
      siteName: "JEBAT AI Platform",
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description,
    },
  };
}
