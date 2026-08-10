# Next.js guidance for kickstart-next

Use this when changing the Next.js app, route structure, rendering behavior, images, TypeScript, ESLint, Tailwind, or package scripts.

## App structure

- `app/layout.tsx` is the root layout and imports `app/globals.css`.
- `app/page.tsx` is the home route. It calls `getPage("/")`, then renders `components/Preview.tsx` when preview is enabled or `components/Page.tsx` otherwise.
- `components/Preview.tsx` is a Client Component. Keep `"use client"` at the top if it uses hooks or `@contentstack/live-preview-utils` subscriptions.
- `components/Page.tsx` renders Contentstack fields and is imported elsewhere as `Page`, even though its internal function name may differ.
- `lib/contentstack.ts` owns Contentstack stack setup, `isPreview`, `initLivePreview()`, and `getPage(url)`.
- `lib/types.ts` owns TypeScript shapes for Contentstack entries, assets, modular blocks, and CSLP `$` mappings.

## Client/server boundaries

- Fetch initial page data in the route/server component where possible.
- Use `Preview` only for Live Preview client behavior: initialize preview, subscribe to `ContentstackLivePreview.onEntryChange`, refetch with `getPage(path)`, and unsubscribe on cleanup.
- Do not move browser-only preview utilities into server-only execution paths.

## Images and rich text

- Use `next/image` for Contentstack images.
- Keep allowed image hosts in `next.config.mjs` under `images.remotePatterns`.
- Default image hosts are `images.contentstack.io` and `*-images.contentstack.com`; `NEXT_PUBLIC_CONTENTSTACK_IMAGE_HOSTNAME` can override with a single hostname for custom environments.
- Sanitize rich text with `isomorphic-dompurify` before using `dangerouslySetInnerHTML`.

## Styling

- The project uses Tailwind CSS 4 via `@tailwindcss/postcss` in `postcss.config.mjs`.
- `app/globals.css` imports Tailwind with `@import "tailwindcss"` and includes base compatibility styles for Tailwind v4 border defaults.
- Keep the kickstart visually simple and example-friendly. Avoid adding a design system unless the user explicitly asks for one.

## TypeScript and linting

- `tsconfig.json` uses `strict: true`, `noEmit: true`, `moduleResolution: "bundler"`, and the `@/*` path alias.
- `eslint.config.mjs` composes Next core web vitals and TypeScript presets.
- `@typescript-eslint/no-explicit-any` is off in the current config, but prefer precise Contentstack types when practical.

## Package scripts

- Current scripts are usually `dev`, `build`, `start`, and `lint`. Verify `package.json` before telling the user a script exists.
- There is typically no `typecheck` script; if one is absent, say that type checking is covered by `next build` rather than claiming a separate command ran.
