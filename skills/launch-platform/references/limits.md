# Launch limits

Defaults can change and some depend on the plan. Check the current Launch documentation before relying on a number.

| Area | Limit |
| --- | --- |
| Build duration | 60 minutes, then the build fails |
| Node.js runtime | 20.x, 22.x, 24.x |
| Package managers | npm, yarn (node-modules mode), bun. Not pnpm or Yarn Plug'n'Play |
| Cloud Function memory | 1,024 MB |
| Cloud Function / SSR timeout | 30 seconds by default; can be raised per organization through Support |
| Writable file system | `/tmp` only, ephemeral |
| Edge Function memory | 128 MB |
| Edge Function bundle | 1 MiB minified |
| Edge Function startup | 400 ms for global scope |
| Request / response body | 5 MB |
| Environment variables | 128 per environment; total size is capped, and the cap is lower with Cloud Functions enabled |
| `launch.json` | Keep under about 200 KB; source and destination URLs up to 512 characters |
| Cache priming | 50 URLs per deployment |
| Cache revalidation | Daily quota depends on the plan |
| Custom domains | Plan-gated; needs a live deployment |
| Launch API | Rate limited per organization |

## Not supported

- Docker containers
- pnpm and Yarn Plug'n'Play
- Vue.js SSR (use Nuxt)
- Next.js App Router ISR and `revalidateTag()` (use the revalidation API)
- Cloud Functions, Gatsby and `launch.json` in a monorepo sub-app
- A built-in IP allowlist (use an Edge Function)
