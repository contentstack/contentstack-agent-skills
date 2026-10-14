---
name: deploy-studio-site
---

## When to use

Ship a Studio site to Contentstack Launch: Launch project and environments, production env vars, composition Deploy, Live Preview gating, region config, cache and 401 gotchas.

Use when deploying a Studio site, setting up Launch, configuring production env vars, wiring Live Preview only on the preview environment, or debugging "deployed but visitors see old content / blank page / a login screen / Live Preview chrome in production / 401 from Delivery API". Two layers ship independently: composition (Save+Deploy in canvas) and host (Launch environment variables + deployment).

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Deploy a Studio site

## Context

A Studio site ships in two independent layers, and both must be correct for the visitor URL to render the latest composition cleanly.

- **Composition Deploy**: publishes the composition record through Contentstack's publishing workflow (from the canvas to the target environment).
- **App host**: your React/Next app on Contentstack Launch that renders `<StudioComponent />` and reads from the Delivery SDK (via `sdk.fetchCompositionData` on the server when using SSR composition-by-URL). A Launch project holds environments; each Launch environment is one Git branch (or uploaded ZIP) with its own URL and variables, and is separate from the stack's environments.

**Tools.** Drive Launch through the Contentstack MCP's `launch` group (`GROUPS` includes `launch`, plus `CONTENTSTACK_ORGANIZATION_UID` and `CONTENTSTACK_LAUNCH_PROJECT_ID`; see [`install-contentstack-mcp`](install-contentstack-mcp.md)). It uses the same OAuth session. The Launch CLI (`csdx plugins:install @contentstack/cli-launch`) accepts only `csdx login`, which the user must run.

The Delivery Token, Preview Token, and Environment are configured per Launch environment: production must NOT carry a Preview Token (otherwise visitors see Live Preview overlays), and the preview environment SHOULD carry one (otherwise authors lose the live edit-and-see-it loop).

Goal state: visitor hits the production URL, gets the latest deployed composition rendered cleanly (no Studio chrome, no Live Preview overlays), and authors see real-time updates only in preview contexts.

## Task

### A. Host the app

1. **Confirm the build output type.** CSR (Vite/CRA, which produces static output) or SSR (Next/Remix). Pick the matching Launch framework preset (`NextJs`, `CSR`, …). Next.js on Launch needs App Router 13.4.6+ (Pages Router 12.2+).

2. **Create or reuse the Launch project** from a Git repository (GitHub, Bitbucket Cloud) or a ZIP upload, with the preset, build command and, for SSR, server command. The MCP will not start the `launch` group without a project ID (checked in 0.9.0), so create a **new** project in the Launch UI first (Git or ZIP upload), then set its uid as `CONTENTSTACK_LAUNCH_PROJECT_ID` and restart the MCP.

3. **Set production env vars** on the Launch production environment (Environments, Settings, Env. Variables, or `update_an_environment`). Same names as `.env.local` (see `install-studio`). Pick the prefix matching the framework (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`, `PUBLIC_`, or plain `process.env` for Remix):
   - `<PREFIX>_CONTENTSTACK_API_KEY`: stack API key (`blt…`)
   - `<PREFIX>_CONTENTSTACK_DELIVERY_TOKEN`: `cs…`, scoped to the **production environment + branch**
   - `<PREFIX>_CONTENTSTACK_ENVIRONMENT`: `<prodEnvironment>` (e.g. `production`)
   - `<PREFIX>_CONTENTSTACK_DEFAULT_LOCALE`: e.g. `en-us`
   - `<PREFIX>_CONTENTSTACK_PREVIEW_TOKEN`: **omit on the production deploy**, set only on preview deploys
   - SSR composition-by-URL ONLY (server-only, no `PUBLIC` prefix): `STUDIO_COMPOSITION_CT_UID`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_ENVIRONMENT`, `CONTENTSTACK_BRANCH`. See `configure-csr-vs-ssr`.

4. **Two Launch environments**:
   - **Production**: auto-deploy on commits off, `environment=<prodEnvironment>`, no preview token, Live Preview `enable: false`. **Turn off Contentstack Authentication** (on by default): it puts a login screen in front of every visitor.
   - **Preview**: auto-deploy on, `environment=<previewEnvironment>`, preview token set, Live Preview `enable: true`. Point that stack environment's Base URL at this Launch URL so Studio's canvas and preview load the deployed app ([`configure-studio`](configure-studio.md)).

5. **Gate Live Preview import and init** on the preview token. First run `grep -rn 'from "@contentstack/live-preview-utils"' src app lib`: every hit is a static import that shows the Edit button in production, however `init` is gated. Replace it with this (see `install-live-preview`):
   ```ts
   const previewToken = process.env.NEXT_PUBLIC_CONTENTSTACK_PREVIEW_TOKEN;
   const apiKey = process.env.NEXT_PUBLIC_CONTENTSTACK_API_KEY!;
   const environment = process.env.NEXT_PUBLIC_CONTENTSTACK_ENVIRONMENT!;

   if (previewToken) {
     import("@contentstack/live-preview-utils").then(({ default: ContentstackLivePreview }) =>
       ContentstackLivePreview.init({
         ssr: false,
         enable: Boolean(previewToken),
         stackDetails: { apiKey, environment },
         editButton: { enable: Boolean(previewToken) },
       }));
   }
   ```
   Why: `live-preview-utils` (4.5.3) draws its Edit button on **import**, even when `init` never runs. Remove its re-export too.

6. **Non-US regions.** Set the Live Preview `host` to the regional preview host (e.g. `eu-rest-preview.contentstack.com`) and the Delivery SDK `region` to match. Regional CDN hosts: `eu-cdn.contentstack.com`, `azure-na-cdn.contentstack.com`, `azure-eu-cdn.contentstack.com`, `gcp-na-cdn.contentstack.com`, `au-cdn.contentstack.com`. **Custom / private data center (hosts supplied by Contentstack)**: there is no `region` shortcut, so set every host explicitly. See [`install-studio`](install-studio.md) § Custom / private data center. Establish which data center you're on first via [`analyze-project-fit`](analyze-project-fit.md) § 2b (determine the data center).

7. **Deploy**: push to the production environment's branch, or redeploy it (`create_deployment`; a ZIP project uploads first). Read the build log (`get_deployment_logs`) for the expected `<PREFIX>_*` injection. Launch applies variable changes only to new deployments, and `NEXT_PUBLIC_*` (and equivalents) are inlined at build time: redeploy after every variable change.

8. **Caching (Next.js).** Launch does not support ISR revalidation, `revalidatePath`/`revalidateTag` or the App Router Data Cache. Opt pages out with `dynamic = 'force-dynamic'` or `revalidate = 0`, set `Cache-Control` headers in `next.config`, and after publishing purge with `revalidate_cdn_cache` (every redeploy also purges). Statically built pages need a deploy hook registered as a Contentstack webhook on publish.

### B. Deploy the composition

9. **Save** in the canvas. Save persists the draft. Deploy publishes whatever was last saved.

10. **Preview** in the canvas with Live Preview, switching the Preview Entry across a few real entries (for linked templates) to confirm bindings resolve. Repeater iteration bindings use `repeater.<field>`. Verify each iteration renders the expected entry data.

11. **Click Deploy** in the canvas toolbar (right cluster, next to Save). The Deploy modal opens: pick the target environments, decide "Send with References" vs "Send without References", confirm. The modal title says "Deploy Template" even for Sections. That's a label quirk, not a bug.

12. **Publish connected entries to the same environment.** For linked templates, the template can deploy fine but the page renders blank if the connected entry isn't published to `<prodEnvironment>`. Publish each connected entry to the target environment.

13. **Wait for publishing workflow.** If the stack has approvals or scheduling configured, the deploy is queued, not immediate. Check the Contentstack publish queue.

## Inputs needed from the user

In this order. Stop and ask if any required value is missing.

1. `framework`: picks the Launch preset and the env-var prefix
2. `launchProject`: an existing Launch project, or create one from a Git repo + branch or a ZIP upload
3. `prodEnvironment`: Contentstack environment name for the production Launch environment
4. `previewEnvironment`: Contentstack environment name for the preview Launch environment (optional, skip if not using one)
5. `region`: defaults to `us`
6. `ssrCompositionByUrl`: yes/no, controls whether server-only env vars are required

If the user doesn't know an environment name, send them to `app.contentstack.com`, where they open the stack, go to Settings, and open Environments.

## Acceptance

This skill succeeds only when ALL of the following are true. If any fails, do not claim success. Surface the failure and stop.

- [ ] The Launch production environment has `<PREFIX>_CONTENTSTACK_ENVIRONMENT` set to `<prodEnvironment>`, **no** preview token, and Contentstack Authentication off
- [ ] The Launch preview environment (if configured) has `<PREFIX>_CONTENTSTACK_PREVIEW_TOKEN` set and `environment=<previewEnvironment>`
- [ ] The live deployment was built after the last variable change
- [ ] `live-preview-utils` is imported only when the preview token is present, and `enable` / `editButton.enable` are gated on it
- [ ] If SSR composition-by-URL: server-only `STUDIO_COMPOSITION_CT_UID`, `CONTENTSTACK_DELIVERY_TOKEN`, `CONTENTSTACK_ENVIRONMENT`, `CONTENTSTACK_BRANCH` are set
- [ ] Region/host pair matches the stack's region (non-US only)
- [ ] Composition is Saved and Deployed to `<prodEnvironment>` via the canvas Deploy modal
- [ ] All connected entries for linked templates are published to `<prodEnvironment>`
- [ ] Visitor URL opened in an incognito session renders the composition with no Studio chrome, no Live Preview edit buttons
- [ ] In DevTools, the Network tab shows Delivery API calls hitting `cdn.contentstack.io` (or the regional CDN), not the preview host
- [ ] The preview environment (if configured) updates live on entry edit without reload

## Common pitfalls

| Symptom | Cause | Fix |
| --- | --- | --- |
| Deployed but visitors see old content | Launch CDN cache, or a statically built page | `force-dynamic` / `revalidate = 0` with `Cache-Control`, purge with `revalidate_cdn_cache`; static pages need a deploy hook on publish. `revalidatePath`/`revalidateTag` do nothing on Launch |
| Visitors get a Contentstack login screen | Contentstack Authentication is on by default per Launch environment | Turn it off on the production environment |
| Page renders blank post-deploy | Connected entry not published to target env | Publish the entry to `<prodEnvironment>` |
| Visitors see draft content after someone previewed | A server with a preview token keeps the last request's preview hash on its shared stack | No preview token on production. On a preview deployment, clear the hash per request: [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md) |
| Visitors see Live Preview edit buttons / overlays | `enable: true` unconditional in prod build, or `live-preview-utils` imported statically (it draws the button on import) | Import it only when the preview token exists (step 5) |
| Preview environment doesn't update live | `onEntryChange` not wired to refetch, or preview token mismatch | Run `verify-setup`. Verify token matches the one in Contentstack |
| `region` / `host` mismatch error | Non-US stack with US defaults | Set Delivery SDK `region` and Live Preview `host` to the region |
| Deploy "succeeded" but composition didn't change | Pending approval / scheduled publish | Check Contentstack publish queue |
| Build fails, or a changed variable has no effect | Launch applies variables only to new deployments, and `<PREFIX>_*` are inlined at build time | Set vars on the Launch environment, then redeploy. No single quotes in values |
| Delivery token returns 401 in production | Token scoped to wrong environment or branch | Generate a token scoped to the prod environment + branch. Rotate in the Launch environment's variables, then redeploy |
| Search engines don't index the site | The default `*.contentstackapps.com` domain is served `noindex` | Add a custom domain to the production environment |
| SSR composition-by-URL 500s | Missing server-only `STUDIO_COMPOSITION_CT_UID` / `CONTENTSTACK_BRANCH` | Add the server-only vars (see `configure-csr-vs-ssr`) |

## See also

- [`configure-csr-vs-ssr`](configure-csr-vs-ssr.md): SSR composition-by-URL and its server-only variables
- [`install-live-preview`](install-live-preview.md): gating Live Preview to preview deploys
- [`configure-studio`](configure-studio.md): pointing the stack environment's Base URL at the preview deploy
- [`verify-setup`](verify-setup.md): end-to-end checks after a deploy
