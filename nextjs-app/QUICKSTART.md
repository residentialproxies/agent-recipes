# 🚀 Quick Start Guide

## Prerequisites Check

```bash
# Check Node.js version (need 18+)
node --version

# Check if FastAPI backend is running
curl http://localhost:8000/v1/agents
```

## Installation (3 steps)

### 1. Install Dependencies

```bash
cd nextjs-app
npm install
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.local.example .env.local

# Edit `.env.local` and set:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### 3. Start Development Server

```bash
npm run dev
```

Visit **http://localhost:3000** 🎉

## What You'll See

### Homepage (`/`)

- **Hero Section** with gradient background
- **AI Concierge** - Try typing: "I need a PDF chatbot"
- **Trending Agents** grid (12 cards)
- **Category Browser**

### Agent Detail (`/agents/[id]`)

- Full agent information
- Frameworks & LLM providers
- Direct GitHub links

## Common Issues

### "Cannot connect to API"

**Solution**: Start FastAPI backend first

```bash
cd ..  # Back to project root
uvicorn src.api:app --reload --port 8000
```

### "Module not found"

**Solution**: Reinstall dependencies

```bash
rm -rf node_modules package-lock.json
npm install
```

### Port 3000 already in use

**Solution**: Use different port

```bash
PORT=3001 npm run dev
```

## Next Steps

1. ✅ Explore the UI
2. ✅ Test AI Concierge with different queries
3. ✅ Check agent detail pages
4. ✅ Customize colors in `tailwind.config.ts`
5. ✅ Deploy to Vercel (see README.md)

## Production Build

```bash
# Build
npm run build

# Start production server
npm start
```

## Quick Commands

| Command         | Description             |
| --------------- | ----------------------- |
| `npm run dev`   | Start dev server        |
| `npm run build` | Build for production    |
| `npm start`     | Start production server |
| `npm run lint`  | Run ESLint              |

---

**Need help?** Check the full README.md or open an issue on GitHub.
