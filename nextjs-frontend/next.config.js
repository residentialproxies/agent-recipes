/** @type {import('next').NextConfig} */
const nextConfig = {
  // SSR mode (see `nextjs-frontend/STATIC_BUILD.md`).
  // Static export (`output: "export"`) is not compatible with this app’s
  // dynamic API-driven pages.
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
};

module.exports = nextConfig;
