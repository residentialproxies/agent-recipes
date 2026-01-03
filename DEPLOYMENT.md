# Deployment Guide

This project supports two deployment styles:

- **VPS (one-click / repeatable)**: Docker Compose + `nginx-proxy` (recommended if you control a server)
- **Split hosting**: Cloudflare Pages (frontend) + managed backend (Railway/Render/Fly.io)

## VPS Deployment (One-Click)

### Requirements (VPS)

- Docker + Docker Compose
- An existing `nginx-proxy` + `letsencrypt-nginx-proxy-companion` setup
- The external network used by the proxy (default: `nginx-proxy_default`)

### Configure secrets on the VPS (once)

Create `$(VPS_PATH)/.env.production` (gitignored) with at least:

```bash
ANTHROPIC_API_KEY=...
GITHUB_TOKEN=...
AI_DAILY_BUDGET_USD=5.0

# CORS allowlist must match your frontend origins
CORS_ALLOW_ORIGINS=https://agentrecipes.com,https://www.agentrecipes.com

# nginx-proxy integration
PROXY_NETWORK_NAME=nginx-proxy_default
FRONTEND_VIRTUAL_HOST=agentrecipes.com,www.agentrecipes.com
API_VIRTUAL_HOST=api.agentrecipes.com
LETSENCRYPT_EMAIL=admin@example.com
```

### Deploy from your laptop (repeatable)

```bash
make deploy \
  VPS_SSH=root@107.174.42.198 \
  VPS_PATH=/opt/docker-projects/heavy-tasks/agent-recipes \
  PROD_SITE_URL=https://agentrecipes.com \
  PROD_API_URL=https://api.agentrecipes.com
```

Or:

```bash
VPS_SSH=root@107.174.42.198 VPS_PATH=/opt/docker-projects/heavy-tasks/agent-recipes ./scripts/deploy-vps.sh
```

This will:

- Build the Next.js static export with `NEXT_PUBLIC_SITE_URL` (canonical + sitemap)
- `rsync` backend code + `docker-compose.prod.yml` to the VPS
- `rsync` `nextjs-app/out/` to `frontend-dist/`
- Run `scripts/vps/release.sh` (Compose up + health waits)

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
| `SITE_URL`              | Frontend canonical URL    | `https://agent-recipes.pages.dev`  |
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

# Build static export
cd nextjs-app
npm ci
NEXT_OUTPUT=export NEXT_PUBLIC_SITE_URL=https://agent-recipes.pages.dev NEXT_PUBLIC_API_URL=https://your-backend.example.com npm run build

# Deploy static export output
wrangler pages deploy out --project-name=agent-recipes
```

## Backend Deployment

For split hosting, deploy the FastAPI backend to a managed service (Railway/Render/Fly.io).

### Environment Variables for Backend

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
AI_DAILY_BUDGET_USD=5.0
INDEXER_WORKERS=20
CORS_ALLOW_ORIGINS=https://agent-recipes.pages.dev,https://agentrecipes.com,https://www.agentrecipes.com
```

## Deployment URLs

- **Frontend**: Configure via Cloudflare Pages (example: https://agent-recipes.pages.dev)
- **Backend**: Configure in `API_BASE_URL` secret (used as `NEXT_PUBLIC_API_URL` during the build)
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
