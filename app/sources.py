"""一次情報のRSS/Atom監視先。追加・削除はこのリストだけで行えます。"""

SOURCES = [
    {"id": "aws", "name": "AWS", "url": "https://aws.amazon.com/about-aws/whats-new/recent/feed/", "topics": ["aws", "cloud", "serverless", "database"]},
    {"id": "react", "name": "React", "url": "https://react.dev/rss.xml", "topics": ["react", "frontend"]},
    {"id": "nextjs", "name": "Next.js", "url": "https://nextjs.org/feed.xml", "topics": ["next.js", "react", "frontend"]},
    {"id": "cloudflare", "name": "Cloudflare", "url": "https://blog.cloudflare.com/rss/", "topics": ["cloudflare", "edge", "security"]},
    {"id": "google-cloud", "name": "Google Cloud", "url": "https://cloud.google.com/release-notes/rss", "topics": ["google cloud", "cloud", "ai"]},
    {"id": "vite", "name": "Vite", "url": "https://github.com/vitejs/vite/releases.atom", "topics": ["vite", "frontend", "build tooling"]},
    {"id": "chrome-dev", "name": "Chrome for Developers", "url": "https://developer.chrome.com/static/blog/feed.xml", "topics": ["chrome", "web platform", "browser api", "css"]},
    {"id": "chrome-releases", "name": "Chrome Releases", "url": "https://chromereleases.googleblog.com/feeds/posts/default", "topics": ["chrome", "browser release", "security"]},
    {"id": "web-dev", "name": "web.dev", "url": "https://web.dev/static/blog/feed.xml", "topics": ["web platform", "css", "performance", "accessibility"]},
    {"id": "node", "name": "Node.js", "url": "https://nodejs.org/en/feed/blog.xml", "topics": ["node.js", "javascript", "runtime"]},
    {"id": "typescript", "name": "TypeScript", "url": "https://github.com/microsoft/TypeScript/releases.atom", "topics": ["typescript", "javascript", "tooling"]},
    {"id": "openai", "name": "OpenAI Developers", "url": "https://developers.openai.com/resources/updates/rss.xml", "topics": ["openai", "ai", "api"]},
]
