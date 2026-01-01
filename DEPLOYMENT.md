# Deployment Guide

This project uses a split deployment architecture:

- **Frontend**: Cloudflare Pages (Next.js SSR/SSG + CDN)
- **Backend**: Railway/Render/Fly.io (FastAPI)

## Prerequisites

1. GitHub account with repository access
2. Cloudflare account with Pages enabled
3. Backend hosting account (Railway/Render/Fly.io)

## Security Notes

- NEVER commit `wrangler.toml`, `.env`, or any files containing secrets
- All sensitive data MUST be stored in GitHub Secrets
- The `wrangler.toml` file is in `.gitignore` to prevent account ID leakage

## GitHub Setup

### 1. Create Repository

```bash
# Already initialized locally, push to GitHub using provided credentials
git remote add origin https://github.com/residentialproxies/agent-recipes.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to: `Settings > Secrets and variables > Actions > New repository secret`

Add the following secrets:

| Secret Name             | Description               | Example Value                      |
| ----------------------- | ------------------------- | ---------------------------------- |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID     | `your-cloudflare-account-id`       |
| `CLOUDFLARE_API_TOKEN`  | Cloudflare API token      | `your-cloudflare-api-token`        |
| `API_BASE_URL`          | Backend API URL           | `https://your-backend.railway.app` |
| `ANTHROPIC_API_KEY`     | Claude API key (optional) | `sk-ant-...`                       |

## Frontend Deployment (Cloudflare Pages)

### Automatic Deployment (Recommended)

1. Push code to `main` branch
2. GitHub Actions automatically builds and deploys to Cloudflare Pages
3. Check deployment status in Actions tab

### Manual Deployment

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
cd nextjs-frontend
npm install
npm run build
wrangler pages deploy .next --project-name=agent-recipes
```

## Backend Deployment

Backend should be deployed to a separate service (Railway/Render/Fly.io) as documented in:
`/Volumes/SSD/skills/server-ops/vps/107.174.42.198/heavy-tasks/SYNC.md`

### Environment Variables for Backend

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
AI_DAILY_BUDGET_USD=5.0
INDEXER_WORKERS=20
CORS_ALLOW_ORIGINS=https://agent-recipes.pages.dev
```

## Deployment URLs

- **Frontend**: https://agent-recipes.pages.dev
- **Backend**: Configure in `API_BASE_URL` secret
- **Custom Domain**: Configure in Cloudflare Pages settings

## Troubleshooting

### Build Failures

Check GitHub Actions logs for detailed error messages:

```bash
# View workflow runs
gh run list

# View specific run
gh run view <run-id>
```

### Cloudflare Pages Issues

```bash
# Check deployment status
wrangler pages deployment list --project-name=agent-recipes

# View logs
wrangler pages deployment tail --project-name=agent-recipes
```

### Backend Connection Issues

1. Verify `API_BASE_URL` in GitHub Secrets
2. Check CORS configuration in backend
3. Ensure backend is deployed and accessible

## Post-Deployment Verification

1. Visit https://agent-recipes.pages.dev
2. Verify API connection to backend
3. Test search functionality
4. Check AI selector feature
5. Verify SEO meta tags and sitemap

## Monitoring

- **Frontend**: Cloudflare Analytics
- **Backend**: Service-specific monitoring (Railway/Render/Fly.io)
- **Errors**: Check GitHub Actions logs and Cloudflare Pages logs

## Security Checklist

- [ ] No secrets in code or config files
- [ ] All secrets stored in GitHub Secrets
- [ ] `wrangler.toml` is gitignored
- [ ] `.env` files are gitignored
- [ ] Git history clean (no exposed tokens)
- [ ] CORS properly configured
- [ ] API rate limiting enabled
- [ ] Input validation active
