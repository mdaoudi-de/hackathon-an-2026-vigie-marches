import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Serveur autonome minimal pour l'image Docker (copie .next/standalone).
  output: "standalone",
};

export default nextConfig;
