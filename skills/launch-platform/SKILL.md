---
name: launch-platform
description: "Advise developers on hosting and configuring sites on Contentstack Launch: framework support and build settings, Cloud Functions, Edge Functions, launch.json redirects, rewrites and cache priming, custom domains, CDN caching and cache revalidation, deploy hooks and CMS-triggered redeploys, environment variables, password protection, IP access control, log targets, monorepos, platform limits, and the Launch CLI and API. Use when developers ask how to deploy or configure a site on Launch, why a build or function fails, how caching or routing works on Launch, or what Launch supports. For syncing environment variables from .env.example, use launch-sync-environment-variables-from-env-example. For scripted deploy-and-monitor runs, use launch-trigger-and-monitor-launch-deployments."
allowed-tools: Read Grep Glob
---

# Launch Platform

Advise on hosting front-end sites on Contentstack Launch: frameworks and builds, Cloud and Edge Functions, `launch.json` routing, domains, CDN caching and revalidation, deploy triggers, environment variables, access control, logging, monorepos and limits.

## When to use

- Deploying or configuring a site on Launch, or checking whether Launch supports a framework or feature.
- A build, function or deployment that fails.
- Choosing between static, SSR, Cloud Functions and Edge Functions.
- Routing, redirects, caching and revalidation, deploy hooks, domains, password protection, IP filtering, log targets and monorepos.

Use another skill for:

- Syncing a Launch environment's variables from `.env.example` → `launch-sync-environment-variables-from-env-example`
- A scripted deploy-and-monitor run → `launch-trigger-and-monitor-launch-deployments`
- CMS webhooks that call a deploy hook or a revalidation receiver → `cms-webhooks`
- Delivery SDK code inside the app → `dx-delivery-sdk`
- The `csdx` CLI in general → `dx-cli`

## Before you answer

Find out the framework, rendering mode and package manager, whether the repo is a single app or a monorepo, any routing, caching or redirect requirements, how often content is published, and any error messages, build logs or deployment status.

## Instructions

1. Identify the framework, rendering mode and repo layout.
2. Check compatibility and limits first, and call out unsupported features before the user hits them.
3. Pick the compute layer (static, SSR, Cloud Function or Edge Function) and the routing approach.
4. Design caching and how content changes reach the site; prefer cache revalidation over full rebuilds for frequent content changes.
5. Cover domains, access control and logging when relevant.


### How a request is served

Requests hit the CDN edge first. Redirects in `launch.json` run, then rewrites, then the Edge Function, then the CDN cache lookup, then the origin (static files or the server-side runtime). A matching `launch.json` rule means the Edge Function does not run for that request.

### Frameworks and builds

Launch builds from GitHub or Bitbucket, or from an uploaded file. Framework presets include Next.js, Nuxt, Gatsby, Remix, Astro, Eleventy, SvelteKit, Qwik City, Jekyll, Angular, Analog and static HTML, plus custom or other for anything else. Vue is client-side only on Launch; use Nuxt for SSR. Configure the build command, output directory and, for SSR, the server command per environment. Supported runtime Node versions are 20.x, 22.x and 24.x. Use npm, yarn (node-modules mode) or bun; pnpm and Yarn Plug'n'Play are not supported. Builds time out after 60 minutes. Larger build machines are available by plan.

### Cloud Functions

Use Cloud Functions for Node.js API routes next to the front end. Put files in `/functions` at the project root; file names become routes, and `[param]` creates dynamic segments. The handler is `export default function handler(request, response)`. Defaults: 1,024 MB memory and a 30-second timeout, which Support can raise per organization. The file system is read-only except `/tmp`. Expect cold starts after inactivity. Cloud Functions cannot run from a monorepo sub-app.

### Edge Functions

Use Edge Functions for per-request logic at the CDN: redirects with logic, header changes, geo or A/B routing, auth gates and IP filtering. The entry point is `functions/[proxy].edge.js`. Code must be WinterCG-compatible: no Node APIs such as `fs`, `path` or `node:crypto`, or the deployment fails. Forward to the origin with `context.fetch()`. Limits: 128 MB memory, 1 MiB minified bundle and a 400 ms startup budget for global scope. Visitor geo headers are available on the request.

### launch.json

Place `launch.json` at the repository root (not in a monorepo sub-app). It holds `redirects`, `rewrites` and `cache.cachePriming.urls`. Rules run top to bottom, redirects before rewrites, and can add request or response headers. Sources are relative paths; escape `?` as `\?`; hash fragments are not supported. Keep the file under about 200 KB and move complex logic into an Edge Function. See [references/launch-json.md](references/launch-json.md).

### Caching and revalidation

Launch purges the whole CDN cache when a new deployment goes live. Set `Cache-Control` headers to control caching. To refresh content without rebuilding, call `POST /projects/{project_uid}/environments/{environment_uid}/revalidate-cdn-cache` with an exact path, a path prefix (`isPrefix: true`), cache tags (set `Cache-Tag` response headers first) or hostnames. Revalidation has a daily quota that depends on the plan; tell users to check theirs. Cache priming warms up to 50 URLs after each deployment. Next.js App Router ISR and `revalidateTag()` are not supported; use the revalidation API instead.

### Deploy triggers

A deploy hook is a per-environment URL that starts a deployment on POST; treat the URL as a secret. To redeploy on CMS publish, point a CMS webhook at the deploy hook. Every publish then triggers a full build, so for frequent publishing prefer revalidating the cache from a webhook receiver. `autoDeployOnPush` controls deploys on Git pushes. Rollback to an earlier deployment is available in the UI and API.

### Environment variables

Variables apply at build time and runtime. Limits: 128 per environment, and a total size cap that is much smaller when Cloud Functions are enabled. Use framework prefixes (such as `NEXT_PUBLIC_`) only for values safe in the browser.

### Domains and access control

Use a CNAME for subdomains and an A record for apex domains. TLS is automatic, and custom certificates can be uploaded. Custom domains depend on the plan, and the environment needs a live deployment first. Password protection (HTTP Basic Auth) is set per environment and applies without a redeploy. There is no built-in IP allowlist; filter on the visitor IP header in an Edge Function.

### Logs

Log targets forward server logs (SSR, Cloud and Edge Functions) and CDN traffic logs over OpenTelemetry (OTLP) to Datadog, CloudWatch, Splunk or any OTLP endpoint. One target per log type per environment. Batches that fail to send are not retried.

### Monorepos

Scope the build command and output directory to the app, for example with Turborepo filters or Nx project builds. Gatsby, Cloud Functions and `launch.json` are not supported from a sub-app.

### API and CLI

The Launch API uses regional hosts (`launch-api.contentstack.com`, `eu-launch-api.contentstack.com`, `au-launch-api.contentstack.com`, `azure-na-launch-api.contentstack.com`, `azure-eu-launch-api.contentstack.com`, `gcp-na-launch-api.contentstack.com`, `gcp-eu-launch-api.contentstack.com`). Authenticate with an OAuth bearer token (recommended) or `authtoken` plus `organization_uid`. The API is rate limited per organization. The `csdx launch` CLI commands cover deployments, logs, environment variables and local Cloud Function testing. Full limits are in [references/limits.md](references/limits.md).

## MCP tools

When the Contentstack MCP server is connected with the `launch` group, these tools act on Launch:

- Inspect: `get_all_projects`, `get_a_project`, `get_all_environments`, `get_an_environment`, `get_environments`, `get_all_deployments`, `get_deployment`, `get_latest_live_deployment`, `get_deployment_logs`, `get_server_logs`, `get_deploy_hooks`, `get_signed_download_url_deployment` (`launch`)
- Change: `create_a_project`, `update_a_project`, `create_an_environment`, `update_an_environment`, `create_deployment`, `revalidate_cdn_cache`, `create_deploy_hook`, `update_deploy_hook`, `trigger_deploy_hook`, `get_signed_upload_url_project`, `get_signed_upload_url_environment`, `get_signed_upload_url_deployment` (`launch`)
- Delete: `delete_a_project`, `delete_an_environment`, `delete_deploy_hook` (`launch`)

Use the read tools to check a real project's build settings, deployment status and logs before diagnosing. `update_an_environment` replaces build settings, variables and password protection together, so read the environment first and send the full object. There are no tools for domains, log targets or rollback; use the Launch UI or API.

## Output

Be concise and practical. Lead with the recommended approach, then config or code. Call out unsupported features and limits up front. Use placeholders for tokens and hostnames.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose authtokens, OAuth tokens, deploy hook URLs or environment secrets.
- Only use public framework prefixes for values that are safe in the browser.
- Use environment variables for credentials in examples.

### Destructive Actions

Before deleting projects, environments, deploy hooks or domains, deploying, rolling back, updating an environment or revalidating the cache, name the project, environment and effect (for example, a production deployment or a full cache purge) and wait for confirmation. Treat production environments as needing explicit confirmation every time.

### Secrets

Never print or echo secret values, deploy hook URLs or password-protection credentials. Use placeholders.

### Environment Variables

Use placeholder names such as `CONTENTSTACK_LAUNCH_OAUTH_TOKEN`. Keep secrets in Launch environment variables, never in the repo or `launch.json`.

## References

- [launch.json reference](references/launch-json.md): redirect, rewrite and cache-priming syntax with examples.
- [Launch limits](references/limits.md): build, function, routing, variable and delivery limits.
