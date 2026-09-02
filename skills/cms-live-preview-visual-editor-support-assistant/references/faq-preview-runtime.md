# Preview runtime FAQ

Content correctness once the integration is confirmed wired up: staleness, lost preview context,
caching, locale, variants, and Timeline.

If the integration itself is not confirmed, work the four setup contracts in SKILL.md first. A
fetch that never switched to the Preview Service produces most of the symptoms below and none of
the fixes here will help.

### variant-or-audience-switch-shows-base-entry
- **bucket**: preview-runtime
- **symptom**: Selecting a variant (or switching audience in Audience Preview) in Visual Experience keeps rendering the base entry. The side form shows the correct variant content, but the canvas does not. A manual browser refresh sometimes fixes it. Clicking into the element shows the correct variant value while the rendered page does not.
- **frameworks**: Next.js, React, framework-agnostic
- **rendering_modes**: CSR | SSR
- **root_cause**: Two distinct mechanisms. (1) Most common: the iframe's content requests are not reaching the Preview service at all (see `app-fetches-from-delivery-cdn-instead-of-preview-service` in `faq-setup.md`). Delivery returns the published base entry and has no knowledge of the variant selected in the UI — the side form looks right because the parent Contentstack UI fetches the entry separately over the Management service. (2) Refresh gap: on variant switch the site must re-fetch, and in CSR that only happens if `onEntryChange` is registered. Without it the canvas keeps its first render. In practice almost every report is one of these two — the Preview Service not configured, or `onEntryChange` missing — not a defect in variant resolution.
- **fix**:
  1. First confirm the preview path works at all: change a plain text field and check the canvas updates. If it does not, fix that first — the variant symptom is downstream of it.
  2. Do **not** try to pass the variant yourself. The Preview Service resolves the variant from the UI selection; no extra `variant` query param is needed. `include_applied_variants=true` only adds metadata to the response body.
  3. Confirm the Preview Service is actually configured: a preview token on the Stack's `live_preview` config, and content requests going to a `*-preview.contentstack.com` host during the session. This is the most common cause.
  4. Register `ContentstackLivePreview.onEntryChange(fetchFn)` and make `fetchFn` re-query through the preview-configured Stack. This is the second most common cause. Confirm `ssr` matches the route's actual rendering mode while you are there.
  5. Check the cache layer. If preview responses are cached under a key that ignores the `live_preview` hash, the base content is served no matter what. Bypass caching entirely for preview requests.
  6. Variants on referenced entries: the referenced content type must be linked to the variant group for its variant content to resolve in preview, and that reference field must be in the `includeReference()` / `referenceFieldPath` list used for the page.
  7. If a cache sits in front, it must not serve one variant's response for another. Do not key it by variant — bypass it for preview requests entirely.
- **verification**: Switch variants; the network tab should show a fresh request to the preview host, and the rendered canvas should change without a manual refresh.

---

### cached-response-serves-stale-preview
- **bucket**: preview-runtime
- **symptom**: Preview works on localhost but not on a deployed environment with identical code and config — the setup status can even show "Setup Completed" and every edit return `{"notice":"Live Preview entry updated successfully."}` while the rendered page never changes. Or preview stops updating and only recovers in an incognito window or after a hard reload.
- **frameworks**: Next.js, framework-agnostic
- **rendering_modes**: SSR | SSG/ISR | edge
- **root_cause**: A cache sits between the browser and the preview service. Whether or not its key includes the `live_preview` hash, preview requests get a stored payload instead of a live one. Seen with a customer CDN in front of the deployed environment, with an app-level fetch cache, and (on the Contentstack side) with stale JS bundles cached in the browser or CDN after a release. The Contentstack SDKs' own cache policies (`IGNORE_CACHE`, `CACHE_THEN_NETWORK`, `CACHE_ELSE_NETWORK`, `NETWORK_ELSE_CACHE`) do **not** switch themselves off for Live Preview — they cache regardless of the preview config.
- **fix**:
  1. Bypass every cache layer when a `live_preview` hash is present: no CDN caching of the preview host or the preview route, `cache: 'no-store'` on the fetch. If the app opted into SDK-level caching, also set `Policy.IGNORE_CACHE` in `cacheOptions` — but `cacheOptions` is optional and unset by default, so most apps have no SDK cache to disable and can skip this.
  2. Do not cache preview responses at all, under any key. The `live_preview` hash identifies the preview **session**, not the content version, so it stays the same across every edit in that session. Keying a cache on it means the first response is served for the rest of the session and the canvas silently stops updating. There is no cache key that makes preview responses safe to cache — use the preview parameters to *bypass* the cache, never to key it.
  3. Exclude the preview environment's base URL from the CDN entirely — the preview service cannot be cached at origin either, which is also why preview responses are measurably slower than CDN delivery (roughly 1s vs 100ms in one measured case). That gap is expected.
- **verification**: Compare response headers on the preview request for cache hits. Reproduce in a private window; if the private window works and the normal one does not, it is a cache.

---

### locale-fallback-blank-or-wrong-locale-in-preview
- **bucket**: preview-runtime
- **symptom**: A page that renders fine in the entry editor and on the live site comes back blank in Visual Experience for a non-master locale. Or preview opens with a locale that does not exist in the stack (e.g. `en-us` on a stack that only has `fr-fr`) and 404s. Or one modular block referencing another entry renders empty in an unlocalized locale.
- **frameworks**: framework-agnostic
- **rendering_modes**: CSR | SSR | SSG/ISR
- **root_cause**: The Delivery API falls back to the master locale automatically; the Preview service does not. If the request to the preview service omits `include_fallback=true` (REST) or `fallback_locale: true` (GraphQL), an unlocalized entry — including an unlocalized *referenced* entry inside a modular block — returns nothing and the page renders empty. Separately, Visual Experience needs a base URL configured per locale in the environment; a locale with no base URL cannot load an iframe, and the preview URL falls back to a default locale that may not exist in the stack.
- **fix**:
  1. Add `include_fallback=true` (REST) / `fallback_locale: true` (GraphQL) to every preview fetch, and to nested reference includes.
  2. Configure a base URL for every locale you want to author in, under the environment's Live Preview settings. A missing URL for one locale can disable the whole environment selector for that locale.
  3. If a shared/common locale has no public market URL, create a preview-only route for it — it does not need to be publicly reachable, only loadable in the iframe.
  4. If you need 404s for unlocalized entries outside preview but fallback inside preview, branch on the presence of the `live_preview` hash rather than turning fallback on globally.
- **verification**: Open the locale in Visual Experience; the entry renders with master-locale content. Check the preview request URL contains the fallback parameter.

---

### csr-edits-need-manual-refresh
- **bucket**: preview-runtime
- **symptom**: Edits only appear after manually reloading the preview. Or the preview flashes/reloads but keeps the old values. Or after navigating to a second page inside the preview, editing an entry refetches and re-renders the *first* page instead.
- **frameworks**: React, Next.js, Angular, Nuxt, Express
- **rendering_modes**: CSR | SSR
- **root_cause**: Three variants. (a) `onEntryChange` is never registered, or is registered but its callback fetches from the delivery path. (b) `ssr` does not match the route. With `ssr: true` the page is reloaded on change, so the fresh hash arrives on a new server request; with `ssr: false` the SDK calls `onChange()` instead and expects the app to refetch. Set the wrong one and neither path runs: an SSR route with `ssr: false` waits for a refetch the app never does, and a CSR route with `ssr: true` waits for a reload that does not repopulate client state. (c) Stale closure: `onEntryChange` is registered once in an effect with `[]` dependencies, but the fetch callback closed over the pathname captured at mount, so after a client-side route change it refetches the original path.
- **fix**:
  1. CSR: `ContentstackLivePreview.onEntryChange(fetchContent)` where `fetchContent` re-queries through the preview-configured Stack. Use `onEntryChange(fn, { skipInitialRender: true })` — equivalent to the older `onLiveEdit` — if you do not want the initial call.
  2. Read the current route inside the callback (from a ref or `window.location.pathname`), never from a value captured at mount.
  3. SSR: set `ssr: true`. The page is then reloaded on change and picks up the new hash on the server request. You do not need to add a `router.refresh()` or any manual re-render.
  4. Do not call `stack.livePreviewQuery()` on the client in CSR mode. The SDK owns the hash there; a manual call that resets `live_preview: ""` when the browser URL lacks the params will clobber it and the refetch silently returns published content.
- **verification**: Type into a field; the canvas updates without touching the browser. Navigate to a second page inside the preview and edit again — the second page should update, not the first.

---

### spa-client-navigation-loses-preview-context
- **bucket**: preview-runtime
- **symptom**: Preview works on the entry's own URL, but navigating within the site inside the preview panel breaks it — "Page Not Found", "You are currently previewing a different webpage", or edits silently stop applying. The address bar in the preview panel briefly shows an internal route that does not match the entry's `url` before settling back. Back button and refresh behave inconsistently.
- **frameworks**: React (react-router), Next.js App Router, framework-agnostic
- **rendering_modes**: CSR | SSR
- **root_cause**: The SDK keeps the preview params on the URL by one mechanism only: a click listener that finds the clicked `<a>` and rewrites its `href` to include `live_preview` before the browser follows it. It does not patch the History API, so any navigation that does not go through a real anchor href — `router.push()`, `useNavigate()`, `history.pushState` — carries no params and the preview context is lost. Framework `<Link>` components are the common trap: they render an `<a>`, so the href is rewritten, but the router calls `preventDefault()` and pushes its own URL, so the rewrite is never used. Separately, if the app's routing does not map 1:1 to the entry's `url` field, the preview URL that Contentstack constructs (environment base URL + entry `url`) points at a route that does not exist. App Router soft navigation also does not re-run server-side hash gating.
- **fix**:
  1. Preserve `live_preview`, `content_type_uid`, `entry_uid`, and `preview_timestamp` in the URL across programmatic navigations, or trigger a hard navigation inside the preview.
  2. For routes that cannot be derived from the entry `url` field, enable **Custom Preview URLs** and then call `setPageContext({ entryUid, contentTypeUid })` on each page (Live Preview Utils v4.4.4+). The call only takes effect when Custom Preview URLs is configured and enabled on the plan; otherwise it is silently ignored and the editor keeps resolving by URL.
  3. For non-trivial URL structures, configure **Custom Preview URLs** in Settings → Visual Experience → Preview URL with placeholders (e.g. `/blog/{{entry.category}}/{{entry.slug}}`) and base URL aliases.
  4. Confirm every route allows iframe embedding, not just the root — an `X-Frame-Options` or CSP `frame-ancestors` header, or a hard redirect to a different host, on a deep route will break navigation inside the panel.
- **verification**: Click through the site's own nav inside the preview panel; the URL keeps its preview params and edits still apply on the new page.

---

### hash-empty-outside-the-preview-iframe
- **bucket**: preview-runtime
- **symptom**: `ContentstackLivePreview.hash` logs as an empty string, so the code that gates on it never switches to the preview host. Or an external tool calling the preview API directly gets `Please provide live preview hash in request` (error_code 382).
- **frameworks**: framework-agnostic
- **rendering_modes**: CSR | SSR
- **root_cause**: The hash identifies a temporary preview session created by the Contentstack application. It only exists when the page is loaded inside the Live Preview / Visual Experience context (via the URL param the parent injects, or via the postMessage handshake). Outside that context there is no session and the hash is legitimately empty. There is no public way to mint one from your own code.
- **fix**:
  1. Treat an empty hash as "not in preview" and fall back to the delivery host. This is the correct branch, not a bug.
  2. If the hash is empty *while inside* the preview panel, the postMessage handshake did not complete: check that the page is actually in the iframe, that `clientUrlParams.host` points at the right region's application host, that `init()` runs client-side (in a `"use client"` component for App Router), and that the SDK version is current.
  3. SSR: do not rely on `ContentstackLivePreview.hash` on the server. Read `live_preview` from the request query string instead.
  4. For an internal tool that needs draft data outside a browser preview session, the hash cannot be generated externally — that use case is not supported over the public preview API.
- **verification**: Log the hash from inside the preview panel and from a normal tab. It should be populated in the first and empty in the second.

---

### stale-first-fetch-when-editing-a-referenced-entry
- **bucket**: preview-runtime
- **symptom**: The very first `onEntryChange` fetch after opening the preview returns published data even though the entry was already modified. Every subsequent keystroke-triggered fetch returns the correct draft data.
- **frameworks**: Next.js (Pages Router), GraphQL
- **rendering_modes**: CSR (on an SSG/ISR site)
- **root_cause**: Service-side. It reproduced only when the entry being edited is a **referenced** entry and the site fetches the **parent** entry through a reference connection — the first preview response did not yet include the referenced entry's draft state.
- **fix**:
  1. Confirm the shape: are you editing a child/referenced entry while the page queries the parent through a reference connection? If so this is the known case and was fixed service-side.
  2. Confirm the first request really is going to the preview host (the Onboarding Check reports this too) before assuming this issue — a first request to the delivery host looks identical from the outside.
  3. Update to a current Live Preview Utils version.
- **verification**: Modify a referenced entry, open the preview fresh, and confirm the draft value is present on the first render with no keystroke.

---

### legacy-management-token-preview-breaks-on-references
- **bucket**: preview-runtime
- **symptom**: Live Preview works for top-level fields but an edit to an entry that is referenced inside another entry does not update. Setup status reports "Preview Service Not Enabled" even though Live Preview is on for the stack. Migrating to preview tokens returns `401 Unauthorized` on the first attempt.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: The older Live Preview implementation authenticated with a read-only Management Token against the CMA host. On that path the reference-resolution optimizations of the Preview service are not available, so edits inside references do not propagate. "Preview Service Not Enabled" is exactly this: the site is still fetching draft data over CMA rather than the Preview service.
- **fix**:
  1. Migrate to the Preview Service: generate a Preview Token tied to your Delivery Token and replace `management_token` with `preview_token` in `live_preview`, and point `host` at the region's preview host.
  2. Remove the CMA host override and any `setHost` calls left over from the old setup.
  3. If preview requests 401 after the swap, confirm the Preview Token is tied to the Delivery Token you are actually using and that the token is sent as the `preview_token` header (not `authorization`).
  4. Minimum versions for Visual Editor: Live Preview Utils v3.0+, Delivery SDK v3.20.3+ (v4.4.4+ of Live Preview Utils if you use `setPageContext`).
- **verification**: Setup status stops reporting "Preview Service Not Enabled"; edits to a referenced entry appear in the parent page's preview.

---

### preview-renders-empty-for-a-restricted-user
- **bucket**: preview-runtime
- **symptom**: One user sees an empty or partly empty page in Live Preview / Visual Editor while colleagues on the same stack see it fully, and the published site is fine for everybody. Missing pieces can be a region, a single field, an image, or a referenced entry. Related shapes: the environment dropdown reads "No environments available" for that user alone (the role has no read permission on any environment, so there is nothing to preview against), or preview logs show `422 "The Content Type '<uid>' was not found."` for their request only.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: **By design.** Preview runs as the signed-in user and applies that user's full ACL — content types, entries, fields, locales and assets alike. Anything the user cannot read comes back empty rather than as an error the site can see. Delivery behaves differently because it uses a delivery token and applies no ACL at all, which is why the published page looks fine. So the same page legitimately renders differently for two users, and that is not a defect. A role granting read on *entries* but not on the *content type* produces the confusing case where the entry opens in the editor but preview returns 422 for it.
- **fix**:
  1. **Handle missing data in the site's rendering.** This is the durable fix. Preview can return an absent field, an empty reference array, a null asset or an unresolved locale for a perfectly valid reason, so components must degrade instead of throwing or rendering a blank region. A site that assumes every field is present will look broken for every restricted user.
  2. Reproduce as the reporting user. This never shows up on an admin session, so testing as an admin proves nothing.
  3. If the user *should* have had access, pull the role with `GET /v3/stacks/roles/{role_uid}` and compare it against what the page actually reads: content types (including referenced ones), the specific fields, the locale, the asset folders, and read access to the preview environment.
  4. Grant read on the content type itself, not only on its entries. Granting entry access alone leaves the 422 in place.
  5. Do not work around it by granting broader edit rights. Read access on the environment and the content types is the correct fix.
  6. After changing the role, have the user sign out and back in before retesting. Role changes do not always apply to an existing session.
  7. **Everyone** seeing "No environments available", not just one user, is a different problem: a missing Base URL — see `environment-base-url-misconfigured-or-missing-for-a-locale` in `faq-setup.md`.
- **verification**: The restricted user's preview renders without gaps or errors, showing graceful fallbacks where access is limited; no `422 Content Type ... not found` in their preview requests. The environment dropdown lists the preview environment for their role.

---

### third-party-scripts-misbehave-inside-the-preview-iframe
- **bucket**: preview-runtime
- **symptom**: Ad slots, consent widgets, or other host-dependent third-party scripts intermittently fail to render inside Live Preview while working on the live site. Preview pages become unusable for pre-flight QA of those integrations.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: The preview renders inside a cross-origin iframe. Third-party scripts whose targeting or delivery logic depends on the top-level host, referrer, or first-party storage see the iframe context instead of the real site and behave differently. Not a Contentstack request failure: the calls fire and fail at the third party's delivery stage. This is inherent to rendering the site in an iframe and there is no product-side fix for it.
- **fix**:
  1. Where the third party allows it, add the Contentstack app origin to its allowed-referrer or allowed-domain configuration.
  2. Use **Open in New Tab**, which renders the preview outside the iframe so the third party sees the real host. This is an existing feature, not something to request.
  3. Where neither is possible, exclude those third-party scripts when the preview parameters are present, so authors preview content without them rather than with a broken version of them.
- **verification**: Use Open in New Tab rather than the preview panel and confirm the third-party content renders. That difference confirms the iframe context is the trigger.

---
