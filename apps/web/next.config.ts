import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output keeps the production Docker image small — it only
  // needs the traced server bundle plus node_modules it actually uses.
  output: "standalone",
};

export default nextConfig;
