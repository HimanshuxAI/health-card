import type { NextConfig } from "next";

// In Docker the API lives behind the gateway container; in local development
// each service runs on its own port. Both are supported through env vars.
const gateway = process.env.API_GATEWAY_URL;
const localPorts: Record<string, string> = {
  identity: "http://localhost:8001",
  records: "http://localhost:8002",
  abdm: "http://localhost:8003",
  nhcx: "http://localhost:8004",
  sos: "http://localhost:8005",
};

const nextConfig: NextConfig = {
  async rewrites() {
    return Object.entries(localPorts).map(([service, base]) => ({
      source: `/api/${service}/:path*`,
      destination: gateway ? `${gateway}/api/${service}/:path*` : `${base}/:path*`,
    }));
  },
};

export default nextConfig;
