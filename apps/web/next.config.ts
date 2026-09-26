import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // The web app imports the shared fixture from ../../contracts.
  turbopack: { root: path.resolve(__dirname, "../..") },
};

export default nextConfig;
