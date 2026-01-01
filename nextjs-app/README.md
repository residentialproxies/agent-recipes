# Agent Navigator - Next.js Frontend

Modern, production-ready frontend for Agent Navigator built with Next.js 14, TypeScript, and Tailwind CSS.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- FastAPI backend running (see main README.md)

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local and set your API URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

Visit `http://localhost:3000`

## 📁 Project Structure

```
nextjs-app/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Landing page
│   ├── globals.css          # Global styles
│   └── agents/
│       └── [id]/
│           └── page.tsx     # Agent detail page
├── components/              # React components
│   ├── ui/                  # Shadcn/UI base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── badge.tsx
│   ├── hero-section.tsx     # Landing hero
│   ├── ai-concierge.tsx     # AI recommendation UI
│   ├── agent-card.tsx       # Agent card component
│   └── agent-grid.tsx       # Agent grid layout
├── lib/                     # Utilities
│   ├── api.ts              # FastAPI client
│   └── utils.ts            # Helper functions
├── types/                   # TypeScript types
│   └── agent.ts            # Agent data models
└── public/                  # Static assets
```

## 🎨 Features

### 🏠 Landing Page

- **Hero Section**: Eye-catching gradient hero with stats
- **AI Concierge**: Interactive AI recommendation form
- **Trending Agents**: Grid of latest agents
- **Category Browser**: Quick navigation by category
- **Responsive Design**: Mobile-first, works on all devices

### 📄 Agent Detail Page

- **Comprehensive Info**: Full agent details
- **Metadata Display**: Frameworks, LLM providers, complexity
- **Quick Links**: Direct links to GitHub and README
- **Related Tags**: Categorized tags for discovery

### 🤖 AI Features

- **Real-time Recommendations**: Claude-powered agent selection
- **Natural Language Input**: Describe your needs in plain English
- **Cached Results**: Fast responses with API caching

## 🛠️ Technology Stack

| Layer         | Technology              |
| ------------- | ----------------------- |
| Framework     | Next.js 14 (App Router) |
| Language      | TypeScript              |
| Styling       | Tailwind CSS            |
| UI Components | Shadcn/UI + Radix UI    |
| Icons         | Lucide React            |
| API Client    | Fetch API with caching  |

## 🔧 Configuration

### Environment Variables

Create `.env.local`:

```bash
# Required: FastAPI backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: For client-side AI features
NEXT_PUBLIC_ANTHROPIC_API_KEY=sk-ant-xxx
```

### Next.js Config

The `next.config.js` includes:

- **Standalone output**: Optimized for Docker deployment
- **API Rewrites**: Proxy to FastAPI backend
- **Environment variables**: Injected at build time

## 📦 Build & Deploy

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
npm start
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL production
```

### Deploy to Cloudflare Pages

```bash
# Build
npm run build

# Deploy build output
# Note: Use the standalone output in .next/standalone/
```

## 🎯 Component Usage

### Hero Section

```tsx
import { HeroSection } from "@/components/hero-section";

<HeroSection />;
```

### AI Concierge

```tsx
import { AIConciergeCTA } from "@/components/ai-concierge";

<AIConciergeCTA />;
```

### Agent Grid

```tsx
import { AgentGrid } from "@/components/agent-grid";
import { getAgents } from "@/lib/api";

const { items } = await getAgents({ page_size: 12, sort: "-stars" });

<AgentGrid agents={items} />;
```

## 🔌 API Integration

The `lib/api.ts` client provides:

### Get Agents

```ts
const { agents, total } = await getAgents({
  q: "chatbot",
  category: "rag",
  complexity: "beginner",
  provider: "openai",
  page: 1,
  page_size: 10,
});
```

### Get Single Agent

```ts
const agent = await getAgent("agent-id");
```

### AI Recommendations

```ts
const recommendation = await getAIRecommendations(
  "I need to build a PDF chatbot",
);
```

## 🎨 Customization

### Colors

Edit `tailwind.config.ts` to change the color scheme:

```ts
colors: {
  primary: {
    DEFAULT: "hsl(262 83% 58%)", // Purple
    foreground: "hsl(210 40% 98%)",
  },
  // ... more colors
}
```

### Fonts

Change font in `app/layout.tsx`:

```ts
import { Inter } from "next/font/google";
// Change to any Google Font
```

## 📝 Development Guidelines

### Adding New Components

1. Create component in `components/`
2. Use TypeScript for props
3. Follow Shadcn/UI patterns
4. Add to exports if reusable

### Styling Best Practices

- Use Tailwind utility classes
- Leverage `cn()` helper for conditional styles
- Keep responsive design mobile-first
- Use CSS variables for theming

### Type Safety

- All API responses typed in `types/agent.ts`
- Use TypeScript strict mode
- No `any` types allowed

## 🐛 Troubleshooting

### API Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/v1/agents

# Verify env variable
echo $NEXT_PUBLIC_API_URL
```

### Build Errors

```bash
# Clear cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Type Errors

```bash
# Regenerate types
npm run build
```

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Shadcn/UI](https://ui.shadcn.com/)
- [Lucide Icons](https://lucide.dev/)

## 🤝 Contributing

1. Create feature branch
2. Make changes with types
3. Test locally
4. Submit PR with description

---

Built with ❤️ using Next.js 14 and Tailwind CSS
