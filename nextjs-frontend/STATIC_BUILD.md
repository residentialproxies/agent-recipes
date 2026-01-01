# Static Build Configuration

The current Next.js app uses Server-Side Rendering (SSR) with dynamic API calls to the FastAPI backend. This configuration is NOT compatible with Cloudflare Pages static export.

## Options:

### Option 1: Deploy to Cloudflare Workers/Pages with SSR (Recommended)

Use `@cloudflare/next-on-pages` adapter to deploy the full SSR app to Cloudflare Workers.

```bash
npm install --save-dev @cloudflare/next-on-pages
```

Update `next.config.js`:

```js
const { setupDevPlatform } = require("@cloudflare/next-on-pages/next-dev");

if (process.env.NODE_ENV === "development") {
  setupDevPlatform();
}

module.exports = {
  // No output: "export" - SSR mode
};
```

### Option 2: Create a Static Landing Page

Build a simple static HTML landing page that links to the backend API docs and provides project information.

### Option 3: Use Vercel/Netlify for SSR

Deploy the Next.js app to a platform that supports SSR natively (Vercel, Netlify, etc.) and use Cloudflare Pages for the static SEO site only.

## Current Workaround:

We'll create a simple static landing page for Cloudflare Pages deployment.
