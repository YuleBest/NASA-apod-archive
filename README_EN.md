# 🌌 NASA APOD Archive (English Version)

A modern, high-performance web application for browsing NASA's **Astronomy Picture of the Day (APOD)**. Built with Vue 3, Vite, and optimized for smooth browsing with local data caching.

### ✨ Features

- **Daily Updates**: Automatically fetches and tracks the latest astronomical wonders.
- **Modern UI**: Clean, premium design with starry background and glassmorphism effects.
- **Performance Optimized**:
  - Local JSON database for instant browsing.
  - Aggressive caching strategies via Cloudflare Pages.
  - Smooth loading animations and transitions to prevent layout shifts (CLS).
- **Responsive Design**: Optimized for mobile, tablet, and desktop viewing.
- **Dynamic SEO**: Dynamic meta tags and Open Graph support for social sharing.
- **Automatic Sync**: Python-based automation script for data synchronization.

### 🚀 Tech Stack

- **Frontend**: Vue 3, Vite, Vue Router, Unhead (SEO)
- **Styling**: Vanilla CSS (Modern CSS variables & Grid)
- **Deployment**: Optimized for Cloudflare Pages (\_redirects & \_headers configured)
- **Automation**: Python script for NASA API data orchestration

### 🛠️ Local Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build
```
