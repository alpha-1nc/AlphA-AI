/** @type {import('next').NextConfig} */
const nextConfig = {
  // API 리다이렉트 (로컬 개발용 백엔드 프록시)
  // NEXT_PUBLIC_API_BASE가 설정되면 rewrites 비활성화
  async rewrites() {
    // Vercel 배포 시에는 NEXT_PUBLIC_API_BASE 사용하므로 프록시 불필요
    if (process.env.NEXT_PUBLIC_API_BASE) {
      return [];
    }
    // 로컬 개발: localhost:8000으로 프록시
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;

