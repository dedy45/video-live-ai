# Dashboard Frontend Strategy

> **Status**: Active
> **Date**: 2026-03-07

## Decision

- **Framework**: Vite + Svelte (static build)
- **Build output**: `src/dashboard/frontend/dist/`
- **Served by**: FastAPI at `/dashboard`
- **No**: Next.js, NestJS, React, or any SPA framework with server-side rendering

## Why Svelte

| Factor | Svelte | Next.js |
|--------|--------|---------|
| Bundle size | ~10KB | ~200KB+ |
| Build step | Simple (vite build) | Complex (Node server) |
| Serving | Static files via FastAPI | Requires Node runtime |
| Learning curve | Low | Medium |
| Complexity | Minimal | Over-engineered for internal tool |

## Build Workflow

```bash
# Development
cd src/dashboard/frontend
npm install
npm run dev

# Production build
npm run build
# Output lands in dist/

# FastAPI serves dist/ at /dashboard
```

## Directory Structure

```
src/dashboard/frontend/
├── package.json
├── vite.config.ts
├── src/
│   ├── App.svelte
│   ├── main.ts
│   ├── lib/
│   │   ├── api.ts          # API client
│   │   ├── types.ts         # TypeScript types
│   │   └── stores.ts        # Svelte stores
│   └── components/
│       ├── Overview.svelte
│       ├── Readiness.svelte
│       ├── Engine.svelte
│       ├── Preview.svelte
│       ├── Stream.svelte
│       └── Diagnostics.svelte
├── dist/                    # Build output (gitignored)
└── index.html
```
