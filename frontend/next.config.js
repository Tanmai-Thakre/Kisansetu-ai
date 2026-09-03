/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",           // required for Docker standalone build
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // Disable SWC transforms on older Node/Windows to avoid build failures
  experimental: {
    forceSwcTransforms: false,
  },
};

module.exports = nextConfig;
