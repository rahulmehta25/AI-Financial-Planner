/** @type {import('next').NextConfig} */
const exporting = process.env.AIFP_EXPORT === "1";

const nextConfig = {
  reactStrictMode: true,
  ...(exporting ? { output: "export", images: { unoptimized: true } } : {}),
};

export default nextConfig;
