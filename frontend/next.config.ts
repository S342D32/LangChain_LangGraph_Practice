import type { NextConfig } from "next";

const LANGGRAPH_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:2024";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/images/:path*",
        destination: `${LANGGRAPH_URL}/images/:path*`,
      },
    ];
  },
};

export default nextConfig;
