/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use environment variable or default to backend container
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000';
    console.log('Next.js rewrites using API base URL:', apiBaseUrl);
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig; 