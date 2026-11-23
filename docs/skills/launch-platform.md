---
title: Launch Platform
description: "Host and configure sites on Contentstack Launch: frameworks, Cloud and Edge Functions, launch.json, caching and revalidation, deploy triggers, domains, access control, logs and limits."
---

# Launch Platform

**Slug:** `launch-platform` · **Product:** Launch · **Type:** Advisory (acts through MCP tools on request)

Advises on getting a framework app building and serving on Launch, choosing between Cloud and Edge Functions, keeping content fresh without constant rebuilds, and staying inside platform limits.

## When it triggers

When you ask how to deploy or configure a site on Launch, why a build or function fails, how routing or caching works on Launch, or whether Launch supports a framework or feature.

## What it covers

- **Request flow**: `launch.json` redirects, then rewrites, then the Edge Function, then the CDN cache, then the origin.
- **Frameworks and builds**: presets (Next.js, Nuxt, Astro, Remix, SvelteKit, Gatsby, Angular and more), build and server commands, supported Node versions, npm/yarn/bun (no pnpm), 60-minute build limit.
- **Cloud Functions**: `/functions` file routing, handler shape, memory and timeout defaults, read-only file system.
- **Edge Functions**: `functions/[proxy].edge.js`, WinterCG-only APIs, memory, bundle and startup limits.
- **launch.json**: redirects, rewrites, header rules and cache priming. See the bundled reference.
- **Caching**: full purge on each live deployment, `Cache-Control`, and the revalidate-CDN-cache API by path, prefix, cache tag or hostname.
- **Deploy triggers**: deploy hooks, CMS-webhook redeploys, auto-deploy on push, rollback. Prefers revalidation over rebuilds for frequent publishing.
- **Environment variables, domains, password protection, IP control through Edge Functions, log targets over OTLP, monorepos.**
- **Limits and unsupported features**, in a bundled limits reference.

## Example prompts

- "How do I deploy my Next.js app to Launch?"
- "Should this middleware be an Edge Function or a Cloud Function?"
- "My site shows old content after I publish in the CMS."
- "Can I restrict my staging site to our office IPs?"
- "How do I send Launch logs to Datadog?"

## MCP tools

With the `launch` group of the Contentstack MCP server connected, the agent can read projects, environments, deployments and build or server logs (`get_an_environment`, `get_deployment`, `get_deployment_logs`, `get_server_logs`), and on request deploy, revalidate the CDN cache, update environments or manage deploy hooks (`create_deployment`, `revalidate_cdn_cache`, `update_an_environment`, `create_deploy_hook`). There are no tools for domains, log targets or rollback.

## Safety notes

Advisory by default. Uses MCP tools to change Launch only when asked, and names the project, environment and effect before any deployment, cache revalidation, environment update or delete, then waits for confirmation. Treats deploy hook URLs and tokens as secrets.

## Related

- [Launch: Sync environment variables](launch-sync-environment-variables-from-env-example.md) · [Launch: Trigger and monitor deployments](launch-trigger-and-monitor-launch-deployments.md) · [Webhooks](cms-webhooks.md)
