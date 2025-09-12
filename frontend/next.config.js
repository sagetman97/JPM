/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // Use environment variable or default to backend container
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:8000';
    const chatbotUrl = process.env.NEXT_PUBLIC_CHATBOT_URL || 'http://chatbot:8001';
    console.log('Next.js rewrites using API base URL:', apiBaseUrl);
    console.log('Next.js rewrites using Chatbot URL:', chatbotUrl);
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
      {
        source: '/chatbot-api/:path*',
        destination: `${chatbotUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig; 