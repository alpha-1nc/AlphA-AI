/** @type {import('next').NextConfig} */
const nextConfig = {
  // API 리다이렉트 (백엔드로 프록시)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
