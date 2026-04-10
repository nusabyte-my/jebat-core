import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
  turbopack: {
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
