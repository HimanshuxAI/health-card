import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/identity/:path*", destination: "http://localhost:8001/:path*" },
      { source: "/api/records/:path*", destination: "http://localhost:8002/:path*" },
      { source: "/api/abdm/:path*", destination: "http://localhost:8003/:path*" },
      { source: "/api/nhcx/:path*", destination: "http://localhost:8004/:path*" },
      { source: "/api/sos/:path*", destination: "http://localhost:8005/:path*" },
    ];
  },
};

export default nextConfig;
