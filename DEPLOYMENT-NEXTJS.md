# Next.js Frontend Deployment Guide

This guide covers deploying the Next.js frontend from `/nextjs-app` to production.

## 📋 Pre-Deployment Checklist

- [ ] FastAPI backend is deployed and accessible
- [ ] Backend URL is noted (e.g., `https://api.example.com`)
- [ ] Node.js 18+ installed
- [ ] Project builds successfully locally

## 🚀 Deployment Options

### Option 1: Vercel (Recommended)

**Pros**: Zero-config, auto-scaling, edge CDN, free tier
**Best for**: Quick deployment, global distribution

#### Steps:

1. **Install Vercel CLI**

```bash
npm i -g vercel
```

2. **Deploy**

```bash
cd nextjs-app
vercel
```

3. **Set Environment Variables**

```bash
# Production
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-backend-url.com

# Recommended for SSR: private server-side base URL (not exposed to the browser)
vercel env add API_URL production
# Enter: https://your-backend-url.com

# Preview
vercel env add NEXT_PUBLIC_API_URL preview
vercel env add API_URL preview
```

4. **Deploy Production**

```bash
vercel --prod
```

**Custom Domain**: `vercel domains add yourdomain.com`

---

### Option 2: Cloudflare Pages

**Pros**: Global CDN, free tier, DDoS protection
**Best for**: Static export builds (no SSR)

#### Steps:

1. **Build Project**

```bash
cd nextjs-app
NEXT_OUTPUT=export npm run build
```

2. **Deploy via Wrangler**

```bash
# Install Wrangler
npm i -g wrangler

# Login
wrangler login

# Deploy
wrangler pages deploy out --project-name agent-navigator
```

3. **Set Environment Variables**

- Go to Cloudflare Dashboard → Pages → agent-navigator → Settings
- Add: `NEXT_PUBLIC_API_URL = https://your-backend.com`

**Note**:

- Cloudflare Pages does not run Next.js SSR by default. Use `NEXT_OUTPUT=export` for static export.
- In static export mode, Next.js rewrites are not applied; serve `/api/*` via a reverse proxy/CDN rule, or configure the frontend to call the backend origin directly.

---

### Option 3: Docker + Railway/Fly.io

**Pros**: Full control, works with any host
**Best for**: Self-hosting, custom infrastructure

#### Dockerfile

Create `nextjs-app/Dockerfile`:

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

#### Deploy to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize
cd nextjs-app
railway init

# Add environment variable
railway variables set NEXT_PUBLIC_API_URL=https://your-backend.com

# Deploy
railway up
```

#### Deploy to Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Initialize
cd nextjs-app
flyctl launch

# Set secret
flyctl secrets set NEXT_PUBLIC_API_URL=https://your-backend.com

# Deploy
flyctl deploy
```

---

### Option 4: AWS Amplify

**Pros**: AWS integration, managed hosting
**Best for**: AWS ecosystem users

#### Steps:

1. **Push to Git** (GitHub/GitLab/Bitbucket)

2. **AWS Amplify Console**
   - New app → Connect repository
   - Branch: `main`
   - Build settings:
     ```yaml
     version: 1
     frontend:
       phases:
         preBuild:
           commands:
             - cd nextjs-app
             - npm ci
         build:
           commands:
             - npm run build
       artifacts:
         baseDirectory: nextjs-app/.next
         files:
           - "**/*"
       cache:
         paths:
           - nextjs-app/node_modules/**/*
     ```

3. **Environment Variables**
   - Add: `NEXT_PUBLIC_API_URL`

4. **Deploy**: Auto-deploys on git push

---

## 🔧 Environment Variables

### Required

```bash
NEXT_PUBLIC_API_URL=https://your-backend.com
API_URL=https://your-backend.com
```

### Optional

```bash
# If you want client-side AI (not recommended, expose API key)
NEXT_PUBLIC_ANTHROPIC_API_KEY=sk-ant-xxx

# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

---

## 🧪 Testing Production Build Locally

```bash
cd nextjs-app

# Build
npm run build

# Start
npm start

# Visit http://localhost:3000
```

---

## 📊 Performance Optimization

### 1. Enable Compression

Vercel/Cloudflare: **Enabled by default**

For custom servers, add to `next.config.js`:

```js
module.exports = {
  compress: true,
};
```

### 2. Image Optimization

Add to `next.config.js`:

```js
module.exports = {
  images: {
    domains: ["github.com", "avatars.githubusercontent.com"],
    formats: ["image/avif", "image/webp"],
  },
};
```

### 3. Analytics

Add Vercel Analytics:

```bash
npm i @vercel/analytics
```

In `app/layout.tsx`:

```tsx
import { Analytics } from "@vercel/analytics/react";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

---

## 🔒 Security

### 1. Environment Variables

**Never commit** `.env.local` to git (already in `.gitignore`)

### 2. API Security

Since `NEXT_PUBLIC_*` variables are exposed to the browser:

- ✅ Use for public URLs only
- ❌ Never put API keys in `NEXT_PUBLIC_*`
- ✅ Proxy sensitive APIs through backend

### 3. CORS

Configure FastAPI backend to allow your frontend domain:

```python
# src/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📈 Monitoring

### Vercel

Built-in analytics at: https://vercel.com/[project]/analytics

### Custom Monitoring

Add Sentry:

```bash
npm i @sentry/nextjs
```

Configure in `sentry.client.config.ts`

---

## 🐛 Troubleshooting

### Build fails on Vercel

**Check**:

- `package.json` engines field
- Node version in Vercel settings
- Build logs for missing dependencies

### API calls failing in production

**Check**:

- `NEXT_PUBLIC_API_URL` is set correctly
- Backend CORS allows frontend domain
- Backend is accessible from the internet

### Static pages not updating

**Solution**: Revalidate cache

```bash
vercel --prod --force
```

Or set shorter revalidate in `page.tsx`:

```tsx
export const revalidate = 600; // 10 minutes
```

---

## 📚 Resources

- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)
- [Vercel Documentation](https://vercel.com/docs)
- [Cloudflare Pages](https://developers.cloudflare.com/pages)

---

**Need help?** Open an issue on GitHub or check the main DEPLOYMENT.md
