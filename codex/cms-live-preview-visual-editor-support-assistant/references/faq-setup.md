# Setup FAQ

Setup and first-integration failures, ordered by how often they come up in practice. Each entry
gives the symptom as users actually report it, the mechanism behind it, the fix, and a
verification step.

Read this after localising the problem to one of the four contracts in the parent skill. The
contract tells you which section to read; this file tells you what to do.

### app-fetches-from-delivery-cdn-instead-of-preview-service
- **bucket**: setup
- **symptom**: Live Preview / Visual Editor loads the site fine, but edits made in the entry form or the right-hand panel never appear in the preview. Content only changes after the entry is published. The Onboarding Check gets past the site-loading and SDK gates and then stops on **Preview Service Not Enabled**. Variant selection in Visual Editor also shows the base entry.
- **frameworks**: Next.js (Pages + App Router), React, Angular, Gatsby, Vue/Nuxt, Java/Spring, framework-agnostic REST/GraphQL clients
- **rendering_modes**: any
- **root_cause**: The site is still calling the Content Delivery host (`cdn.contentstack.io` / `graphql.contentstack.com`) for its content. The `live_preview` hash reaches the page in the URL, but nothing in the fetch layer switches host + headers to the Preview Service, so the API returns published content. Most common with hand-rolled fetch wrappers, a BFF/middleware layer, GraphQL clients, or a separate fetch helper that bypasses the initialized Delivery SDK instance.
- **fix**:
  1. Generate a Preview Token against the Delivery Token you already use (Settings → Tokens → your Delivery Token → Preview Token), and enable Live Preview on the stack with a default preview environment.
  2. If you use the Contentstack Delivery SDK: pass the same initialized Stack instance to every content fetch, and give it `live_preview: { enable: true, preview_token: <TOKEN>, host: <region preview host> }`. Do not create a second Stack instance just for `ContentstackLivePreview.init()`.
  3. If you fetch over raw REST/GraphQL: branch on the hash before every request.
     ```js
     // SSR: read it off the request. CSR: use ContentstackLivePreview.hash
     const livePreviewHash = request.query.live_preview;
     if (livePreviewHash) {
       headers.append("live_preview", livePreviewHash);
       headers.append("preview_token", CONTENTSTACK_PREVIEW_TOKEN);
       url.hostname = LIVE_PREVIEW_HOST; // e.g. rest-preview.contentstack.com
     } else {
       url.hostname = CONTENTSTACK_CDN_HOST; // e.g. cdn.contentstack.io
     }
     ```
     For GraphQL the equivalent is swapping `graphql.contentstack.com` → `graphql-preview.contentstack.com` and adding the same two headers.
  4. Bypass any cache layer for preview requests. Do not try to fix it with a smarter cache key: the hash is stable for the whole preview session, so any cache on this path serves the first response for the rest of it.
- **verification**: Open the entry in Live Preview, then in DevTools → Network confirm requests go to the `*-preview.contentstack.com` host, carry `preview_token` and `live_preview` headers, and return 200. Edit a field without saving; the preview must update. The Onboarding Check should reach **Setup Complete**.

---

### iframe-blocked-by-x-frame-options-or-csp-frame-ancestors
- **bucket**: setup
- **symptom**: The Live Preview / Visual Editor pane is blank or shows "`<your-host>` refused to connect". Console shows `Refused to display '<url>' in a frame because it set 'X-Frame-Options' to 'sameorigin'` (or `deny`), or a `frame-ancestors` CSP violation. Frequently paired with a `401` on a `HEAD`/`GET` of the site root. Works on localhost, fails on the deployed dev/QA/staging host.
- **frameworks**: framework-agnostic (server / CDN / hosting-platform header config)
- **rendering_modes**: any
- **root_cause**: Contentstack renders the site inside an iframe on the app origin. Any `X-Frame-Options: SAMEORIGIN|DENY` or a CSP `frame-ancestors` directive that does not include the Contentstack app origin makes the browser refuse the frame before the page can run. Platform-level deployment protection (for example a hosting provider's password protection) adds `X-Frame-Options: DENY` to the password screen itself, so even the auth prompt cannot render.
- **fix**:
  1. Remove `X-Frame-Options` for the preview host and use CSP instead: `Content-Security-Policy: frame-ancestors 'self' https://*.contentstack.com https://*.contentstack.io;` (`X-Frame-Options` has no allowlist syntax; a bare `SAMEORIGIN` always wins).
  2. Apply the header on every route, not just the site root. A route that redirects to a different hostname than the configured Base URL will also fail.
  3. If the deployment sits behind platform password protection, note that no header or query parameter can be injected into a browser-originated iframe request from Contentstack. Options: disable protection on the preview deployment, use a bypass token embedded in the Base URL, put a server-side proxy in front that injects the header, or use Live Preview → Open in New Tab (a plan-gated feature that renders outside the iframe).
  4. Third-party SSO screens that themselves set `X-Frame-Options: DENY` cannot render in the iframe at all. Use Open in New Tab, which renders the preview outside the iframe so those screens can load.
- **verification**: `curl -I https://<preview-host>/<some-deep-route>` and confirm no `X-Frame-Options` and a `frame-ancestors` value that includes the Contentstack app origin. Reload Live Preview; the pane should render.

---

### error-382-create-tracker-before-starting-live-preview-session
- **bucket**: setup
- **symptom**: Preview API requests fail with
  `{"error_message":"Please create tracker before starting live preview session","error_code":382,"status":400}`
  (a sibling variant is `{"error_message":"Please provide live preview hash in request","error_code":382}`). Often appears the moment `mode: "builder"` is set, or when the site is opened directly rather than from inside the Contentstack preview pane. Sometimes reproduces for one developer and not another on "identical" setups.
- **frameworks**: Next.js, React, framework-agnostic REST/GraphQL clients
- **rendering_modes**: CSR, SSR
- **root_cause**: The `live_preview` hash sent on the request has no matching tracker document. Contentstack creates that tracker with a `POST /live-preview/tracker` when the preview session starts inside the CMS. The error means either (a) the app sent a hardcoded, stale, or hand-invented hash, (b) the app sent `live_preview=true` or an empty value instead of the real hash, or (c) the request was made outside any preview session (the site opened directly, or a custom preview tool that has no way to obtain a hash).
- **fix**:
  1. Never hardcode or invent a hash. Read it from `?live_preview=` on the request (SSR) or from `ContentstackLivePreview.hash` (CSR), and skip the preview host entirely when it is absent.
  2. Confirm the tracker call fires: in DevTools → Network, look for `POST /live-preview/tracker` returning 2xx when the preview pane loads. If it never fires, the SDK did not initialize (check `enable`, the `.env` value actually parsing as `true`, and that `init()` runs on the client).
  3. If the app proxies Contentstack through its own backend, forward the hash end to end. The front end must pass the hash it received to the backend, and the backend must put it in the `live_preview` header.
  4. Building a preview tool entirely outside Contentstack is not supported with a Preview Token alone; the hash originates in the CMS session. Use a dedicated publishing environment for an internal preview tool instead.
- **verification**: With the entry open in Live Preview, the network log shows a successful tracker POST followed by preview reads returning 200 with the same hash value.

---

### edit-tags-not-generated-or-not-spread
- **bucket**: setup
- **symptom**: Nothing on the page is inline-editable: no hover highlight, no edit button, no field toolbar. Clicking the canvas does nothing, or selects the wrong (parent) element. `entry.$` / `post.$` is `undefined` in the app, or `data-cslp` renders as literal text instead of an attribute. Live Preview auto-refresh often still works, which makes it look like a Visual Editor bug.
- **frameworks**: React, Next.js, Vue, Angular, Gatsby, Blazor/.NET, jQuery
- **rendering_modes**: any
- **root_cause**: Tags need two independent things and teams usually do only one: `addEditableTags()` must run on every fetched entry, **and** the generated `$` attributes must be spread onto the DOM elements that render each field. `mode: "builder"` does not generate tags, but it is still required: Visual Editor's Verify Mode gate fails on `mode: "preview"`, so tags alone do not produce a canvas. Four ways this goes wrong: the call is missing entirely (commonly commented out during a migration); `tagsAsObject` is `false` or omitted, producing a `data-cslp` string React cannot spread; the content type **title** is passed instead of its **uid**; or the call is correct but nothing spreads the result into the markup.
- **fix**:
  1. Call it on every entry right after fetching, including referenced entries: `addEditableTags(entry, contentTypeUid, true, locale)`. The third argument must be `true` for React and JSX.
  2. Pass the content type **uid**, not its display title.
  3. Spread onto the element that renders the value: `<h1 {...post.$?.title}>{post.title}</h1>`.
  4. Mirror the data path exactly. References come back as arrays, so it is `post.author[0].$?.name`, not `post.$?.author.name`.
  5. Tag the leaf element that holds the value, one `data-cslp` per element. Tagging a wrapper group instead of the field makes Visual Editor select the wrong field.
  6. Check nothing strips them at build time: `cleanCslpOnProduction: true` removes `data-cslp` from the DOM, and `PURGE_PREVIEW_SDK=true` no-ops the whole SDK.
  7. For GraphQL, the response shape itself breaks tag paths — see `graphql-connection-wrappers-break-cslp` in `faq-visual-editor.md` for the normalizer that has to run before `addEditableTags()`.
  8. If you only want auto-refresh and not in-context editing, use `mode: "preview"` rather than `mode: "builder"` with no tags.
- **verification**: In DevTools on the previewed page, `document.querySelectorAll('[data-cslp]').length` must be greater than 0, and a rendered field must carry `data-cslp="<content_type_uid>.<entry_uid>.<locale>.<field_path>"`. Hovering it in the canvas should highlight it, and clicking should focus the matching field in the form panel.

---

### preview-url-does-not-resolve-to-the-app-route
- **bucket**: setup
- **symptom**: Live Preview opens the site's home page or a "Page Not Found" instead of the entry being edited. Navigating inside the preview 404s. Sometimes the pane says "You are currently previewing a different webpage". Affects entries whose real URL is nested, taxonomy-driven, multi-tenant, or has no `url` field at all.
- **frameworks**: Next.js, React, framework-agnostic
- **rendering_modes**: any
- **root_cause**: By default the preview URL is `environment Base URL` + the entry's `url` field. That only works when app routing maps 1:1 to the `url` field. Nested paths, custom route prefixes, several content types with different URL shapes, multiple sites served from one stack, or a URL stored in a custom text field instead of the built-in `url` field all break the concatenation.
- **fix**:
  1. Configure **Custom Preview URLs** (Settings → Visual Experience → Preview URL) with pattern placeholders such as `/blog/{{entry.category}}/{{entry.slug}}`, plus Base URL aliases when several hostnames map to one stack. This is the feature that decouples preview from `Base URL + entry.url`; it is plan-gated and has to be enabled on the account.
  2. With Custom Preview URLs enabled, tell the editor which entry each page is by calling `setPageContext({ entryUid, contentTypeUid })` on every page (Live Preview Utils v4.4.4+). Fallbacks: the `window.__CS_PAGE_CONTEXT__` global, or `<meta name="contentstack:entry-uid">` and `<meta name="contentstack:content-type-uid">`. **This only has an effect when Custom Preview URLs is configured and enabled on the plan.** Without it the editor resolves by URL alone and the call is silently ignored — it does not error, so a missing feature flag looks like `setPageContext` not working.
  3. Do not narrow the environment Base URL to one content type's prefix (for example `.../inspiration/articles/`) — that fixes one content type and breaks all others.
  4. Verify the entry's `url` field actually corresponds to a route the app serves, and that the route renders the content type you expect.
- **verification**: Open entries from several content types (root page, nested page, no-URL page). Each should load its own page in the preview pane, and the URL bar in the pane should show the real route.

---

### sdk-version-below-visual-editor-minimum-or-breaking-major-upgrade
- **bucket**: setup
- **symptom**: Visual Editor features silently do nothing on an otherwise working Live Preview setup; or a version bump breaks a previously working integration — `setConfigFromParams` disappears, `ReferenceError: window is not defined` in server code, the Edit button suddenly renders in production, or `Live_Preview_SDK: To use edit tags, you must provide the stack API key`.
- **frameworks**: Next.js, React, Gatsby, Angular
- **rendering_modes**: any
- **root_cause**: Feature availability is version-gated and majors carry breaking changes that were not always documented. Pinned-old dependency policies (auto-update disabled) leave teams on v1.x where the required callbacks do not exist. The v2 → v3 jump removed `setConfigFromParams` (its replacement reads `window`, which throws in SSR) and made `stackDetails.apiKey` mandatory for edit tags.
- **fix**:
  1. Meet the minimums: Live Preview Utils **v3.0+** and Delivery SDK **v3.20.3+** for Visual Editor; **v4.4.4+** if you use `setPageContext()`.
  2. Pass `stackDetails: { apiKey, environment }` explicitly in `init()` — v2+ no longer derives the API key from the Stack object for edit tags.
  3. In SSR, stop calling `setConfigFromParams`. Read the query parameters from the request and apply them with `livePreviewQuery()` instead of relying on any SDK helper that touches `window`.
  4. Pin one delivery method for the SDK. Mixing an npm install with an ESM/CDN `<script type="module">` import of a different version produces version-specific behaviour differences (for example the Edit button appearing after a CDN bump).
  5. Read the SDK release notes before a major bump rather than the setup docs alone.
- **verification**: `npm ls @contentstack/live-preview-utils @contentstack/delivery-sdk` (or `contentstack`) shows versions at or above the minimums, and only one copy of the preview SDK is loaded in the page.

---

### environment-base-url-misconfigured-or-missing-for-a-locale
- **bucket**: setup
- **symptom**: The Live Preview environment selector is greyed out or shows "No environments available"; preview loads the wrong path or the site root; a specific locale cannot be previewed at all while others work; the preview pane keeps showing the previous environment's URL after switching.
- **frameworks**: framework-agnostic (stack configuration)
- **rendering_modes**: any
- **root_cause**: Live Preview builds the iframe URL from the environment's Base URL for the entry's locale. If any environment is missing a Base URL for that locale, the whole selector can be disabled for the locale. A Base URL missing its locale segment (for example `https://host` instead of `https://host/en`) resolves to the wrong page. A Base URL without a scheme (`localhost:3001` instead of `http://localhost:3001`) silently fails. Locales with no configured Base URL are not supported in Visual Editor at all.
- **fix**:
  1. Settings → Environments: set a Base URL for **every** environment/locale pair you intend to preview, including the locale path segment where the app uses one.
  2. Always include the scheme (`http://` or `https://`).
  3. For a locale that only exists via fallback, either add a Base URL that resolves fallback content (and add `include_fallback=true` on your queries) or accept that Visual Editor cannot render it.
  4. Environment publish permissions affect which Base URLs a role can select; a restricted user can still preview by typing the correct Base URL into the Live Preview URL bar.
  5. If **only one user** sees "No environments available" while colleagues do not, it is not the Base URL — that user's role has no read permission on any environment. See `preview-renders-empty-for-a-restricted-user` in `faq-preview-runtime.md`.
- **verification**: For each locale, open the Live Preview environment dropdown — every environment should be selectable and the resolved URL should load the correct localized page.

---

### edit-button-rendered-outside-a-live-preview-session
- **bucket**: setup
- **symptom**: The Live Preview "Edit" pencil button appears on the normal production or UAT site for ordinary visitors, or the `#cslp-tooltip` button element is injected into `document.body` on production even when not visible (usually caught in an accessibility audit). Sometimes intermittent, correlating with client-side route changes rather than fresh page loads.
- **frameworks**: Next.js (App Router especially), React
- **rendering_modes**: CSR, SSR
- **root_cause**: With `editButton.enable: true`, the SDK gates the button on `enable` + `inIframe()` + the `cslp-buttons` query parameter. It never checks the `live_preview` hash or any active-session signal, so a normally loaded page with the SDK initialized renders the button by design. Teams that gate `init()` on a server-read hash also get bitten by App Router soft navigation, which does not re-run that server-side gate while the SDK's button instance persists across route changes.
- **fix**:
  1. Add `editButton: { enable: true, exclude: ['outsideLivePreviewPortal'] }`. Outside the iframe `inIframe()` is false, so the button will not render, while Live Preview inside the pane keeps working.
  2. If Live Preview is not used on production at all, strip it from the production build: `cleanCslpOnProduction: true` removes `data-cslp` from the DOM, and the `PURGE_PREVIEW_SDK=true` build flag no-ops the SDK entirely.
  3. Do not rely on a server-side hash check alone in an App Router app; soft navigation will not re-evaluate it.
- **verification**: Load the production URL in a normal tab with DevTools open. `document.getElementById('cslp-tooltip')` should be absent, and no `data-cslp` attributes should be present if `cleanCslpOnProduction` is set.

---

### cors-blocked-on-preview-api-requests
- **bucket**: setup
- **symptom**: `Access to fetch at 'https://<region>-rest-preview.contentstack.com/v3/...' from origin '<site origin>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource`, frequently alongside a `401 (Unauthorized)` on the same request. Works on localhost, fails on the deployed dev/staging host.
- **frameworks**: Gatsby, Angular, Next.js, React
- **rendering_modes**: CSR mainly
- **root_cause**: Two distinct problems that surface as one console message. (1) The site's own Content Security Policy (`connect-src` / `default-src`) does not allow calls to Contentstack hosts, which most frameworks restrict by default in production but not in local dev. (2) The preview request is genuinely rejected (bad or wrong-type token), and the error response carries no CORS headers, so the browser reports it as a CORS failure instead of a 401. There is no per-stack "CORS allowlist" on the Contentstack side to add origins to.
- **fix**:
  1. Widen the site's CSP to the whole Contentstack domain rather than individual hosts. Listing only `app.contentstack.com` and `rest-preview.contentstack.com` has repeatedly been insufficient; `https://*.contentstack.com` (and `https://*.contentstack.io` where delivery/asset hosts are used) is what worked.
  2. Fix the 401 separately: confirm you are sending a valid **Preview Token** (not a Delivery Token, not a Management Token) in the `preview_token` header, and regenerate it if in doubt. Resolve the CSP first, or the server error stays masked.
  3. Recheck env vars after a stack migration or API key change — a stale API key produces the same 401-behind-CORS shape.
- **verification**: `curl` the same preview URL with the same headers from a terminal. A 200 proves the token is valid and the remaining problem is browser-side CSP. In the browser, the request should complete with `Access-Control-Allow-Origin` present.

---

### ssr-stack-instance-shared-or-duplicated
- **bucket**: setup
- **symptom**: Two opposite failures from the same mistake. **(A) Hash never arrives:** `init()` succeeds and `ContentstackLivePreview.hash` is populated on the client, but server-rendered pages still return published content. Deterministic, and only the author notices. **(B) Preview state leaks out:** intermittent, user-dependent wrong content, and the **production** site failing with `The Live Preview tracker is invalid or no longer exists. Create a new tracker to continue.` (error_code 382) or `The requested tracker was created for the 'dev' branch. Access using the 'main' branch is not allowed.`; preview stalling after a while; `TypeError: Cannot read properties of undefined (reading 'uid')` after idle hours in production; two editors seeing each other's content; personalization on the public site stopping resolving per visitor because a cached preview render is being served instead. This one reaches real visitors.
- **frameworks**: Next.js (App Router and Pages Router), Express/Node, Nuxt
- **rendering_modes**: SSR | edge
- **root_cause**: In SSR the SDK does not fetch content. It puts `?live_preview=<hash>&content_type_uid=...&entry_uid=...` on the URL and reloads, and preview state lives **on the Stack instance**. Failure (A) is having two instances: a long-lived "default" Stack for page queries plus a second Stack passed only to `init()`, so the hash never lands on the instance that queries. Failure (B) is having one module-level instance shared across requests: once any request puts it into preview mode, unrelated requests inherit it, and ordinary delivery traffic starts hitting the preview service with a hash that has expired (the tracker lasts about a day; the session hash rotates roughly every 30 minutes) or belongs to another branch. Under concurrency requests can also overwrite each other's config mid-flight.
- **fix**:
  1. Create a fresh Delivery SDK instance **per request**. Do not share a module-level Stack, and pass the instance down through request-scoped context rather than importing a singleton. This one change fixes both failures.
  2. Read the hash off the incoming request each time and apply it to that instance: `stack.livePreviewQuery({ live_preview: hash, contentTypeUid, entryUid })`.
  3. Call `livePreviewQuery(...)` **unconditionally** per request, with empty values when there is no hash. Calling it only when a hash exists leaves the previous request's hash in place.
  4. Run every query that should show drafts on that instance. A query on an un-hashed instance returns published content.
  5. Drop any separate "live preview only" Stack. `init()` does not need a Stack in SSR.
  6. Never reuse a hash captured in a preview session on a normal page load, and never hardcode or persist one. Keep the branch consistent: a tracker created against one branch cannot be used against another.
  7. Ignore `No ack listener found` / `NO_REQUEST_LISTENER_FOUND` here. Routine postMessage chatter that appears on working setups; it does not affect SSR content.
- **verification**: Log the hash on the server per request and confirm it is non-empty and changes per session, and that preview requests hit the preview host. Editing a field without saving should change the SSR output on reload. Then load the production URL directly on a cold server and confirm requests go to the CDN host with no `live_preview` header, and that mixed preview / non-preview traffic does not contaminate either side.

---

### nextjs-app-router-init-must-run-in-a-client-component
- **bucket**: setup
- **symptom**: In a Next.js App Router project, Live Preview never activates: no hash in the URL, no SSR-mode detection, edit tags render but do nothing, or nothing at all happens when the entry is edited. The same code works in a Pages Router project.
- **frameworks**: Next.js App Router
- **rendering_modes**: SSR, CSR
- **root_cause**: `ContentstackLivePreview.init()` has to run in the browser. In App Router, code placed in a server component or in the root layout module body never executes client-side, so the SDK never installs its postMessage listeners and never advertises SSR mode.
- **fix**:
  1. Create a dedicated client component and call `init()` from an effect:
     ```tsx
     "use client";
     import ContentstackLivePreview from "@contentstack/live-preview-utils";
     import { useEffect } from "react";
     export default function LivePreviewClient() {
       useEffect(() => { ContentstackLivePreview.init({ /* ... */ }); }, []);
       return null;
     }
     ```
  2. Render that component from the root layout.
  3. On the server side, read `live_preview`, `content_type_uid`, and `entry_uid` from `searchParams` (or from request headers set in middleware) and apply them with `livePreviewQuery()` per request. Do not expect the client SDK to hand the hash to server code.
  4. Keep the SDK init code in its own module so re-renders do not reset the configuration.
- **verification**: With the entry open in Live Preview, the iframe URL contains `?live_preview=...`, the console reports SSR mode where applicable, and the server sees the hash on each request.

---

### legacy-management-token-setup-not-migrated-to-preview-token
- **bucket**: setup
- **symptom**: "Preview Service Not Enabled" shows in the preview panel on a setup that otherwise works. Or a setup copied from older docs / an older starter app passes a `management_token` to `live_preview` and fails with 401/422 after tokens were rotated.
- **frameworks**: Next.js, Gatsby, React, framework-agnostic
- **rendering_modes**: any
- **root_cause**: The original Live Preview implementation read drafts through the CMA using a read-only Management Token. That was replaced by the Preview Service and a read-only Preview Token issued against a Delivery Token. Applications left on the legacy path still work but are flagged, and older starter apps / source plugins shipped `management_token` in the `live_preview` config long after the docs switched to `preview_token`.
- **fix**:
  1. Generate a Preview Token on the Delivery Token you already use.
  2. Replace `live_preview.management_token` with `live_preview.preview_token` and point `live_preview.host` at the region's `*-rest-preview.contentstack.com`.
  3. Update any framework source plugin to a version whose build output actually reads `preview_token` (some releases had source and build output disagreeing).
  4. Remove the Management Token from client-side code entirely. Stack API Key, Delivery Token, and Preview Token are read-only and safe to ship to the browser; a Management Token has write access and is not.
- **verification**: No Management Token appears in any client bundle or preview request; the "Preview Service Not Enabled" card is gone and the Onboarding Check reaches Setup Complete.

---

### branch-or-alias-mismatch-between-app-token-and-entry
- **bucket**: setup
- **symptom**: Preview opens for pages that already exist on the main branch but never shows updates, and any page that exists only on the working branch 404s. Or: `error_code: 901, "Access denied. You have insufficient permissions to perform operation on this branch"`.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: Two misalignments. The deployed preview site is pinned to one branch (often a production replica on `main`) while the author edits on another. Or the Delivery/Preview Token scope does not include the branch or alias being previewed, which surfaces as the 901. Aliases themselves resolve to their target branch correctly, so an alias in the URL is not a cause.
- **fix**:
  1. Make the branch the app queries match the branch the entry is edited on — either configure a per-branch preview deployment or read the branch from the preview request and pass it as the `branch` header.
  2. Extend the Delivery Token scope to include every branch **and** alias you preview against. Adding a branch to the scope after the fact is what cleared the 901.
  3. Aliases are fine to use in preview URLs. If you scope a token to an alias, confirm the alias points at the branch you think it does, since repointing an alias silently changes what preview reads.
- **verification**: Edit an entry that exists only on the non-main branch; it should load and update in the preview. Preview requests should carry the expected `branch` header and return 200.

---

### wrong-region-hosts-in-sdk-and-preview-config
- **bucket**: setup
- **symptom**: Live Preview never activates or the preview panel reports the service is not enabled, even though the stack settings look correct. Requests in the network tab go to the default North America hosts while the stack lives in another region.
- **frameworks**: Next.js, Angular, React
- **rendering_modes**: any
- **root_cause**: Region is not inferred. Each of the delivery host, preview host, API host, and app host has a region-specific name, and the SDK defaults to the AWS NA set. A stack in EU / Azure / GCP that is left on the defaults gets rejected or served from the wrong region.
- **fix**:
  1. Set every host explicitly and consistently for the stack's region. All four move together:
     - delivery: `cdn.contentstack.io` → e.g. `eu-cdn.contentstack.com`, `azure-na-cdn.contentstack.com`, `gcp-eu-cdn.contentstack.com`
     - preview: `rest-preview.contentstack.com` → e.g. `eu-rest-preview.contentstack.com`, `azure-na-rest-preview.contentstack.com`, `gcp-eu-rest-preview.contentstack.com`
     - GraphQL preview: `graphql-preview.contentstack.com` → the region-prefixed equivalent
     - app host (`clientUrlParams.host`): `app.contentstack.com` → e.g. `eu-app.contentstack.com`, `gcp-na-app.contentstack.com`
  2. Use the SDK's `region` option where available rather than hand-writing hosts, and make sure a hardcoded `host` does not override it.
  3. Re-check every host after a stack migration; the API key changes too.
- **verification**: In DevTools → Network, every Contentstack request goes to a host carrying the correct region prefix, and returns 200.

---

### locale-defaults-to-en-us-in-init
- **bucket**: setup
- **symptom**: Start Editing / the Edit button opens Visual Editor or the entry editor with `locale=en-us` even though the stack has no `en-us` language, producing a 404 or a "Language not found" toast. Works on one deployment and not another with identical code.
- **frameworks**: React, Angular, framework-agnostic
- **rendering_modes**: any
- **root_cause**: When `stackDetails.locale` is not set in `init()`, the SDK tries to infer the locale by finding an element with `data-cslp` in the DOM and reading the locale out of it. If no tagged element is present at that moment, it falls back to `en-us`. That fallback is invalid on stacks whose master language is something else, and it explains why the same code behaves differently on two deployments (one happens to have tagged content in the DOM, the other does not).
- **fix**:
  1. Set the locale explicitly:
     `ContentstackLivePreview.init({ stackDetails: { apiKey, environment, locale: '<your-locale>' } })`.
  2. Also pass the locale to `addEditableTags(entry, contentTypeUid, true, locale)` so the generated `data-cslp` carries the right locale.
  3. Do not add a dummy `en-us` language to the stack as a workaround.
- **verification**: Click an edit tag; the URL that opens should carry your real locale, and the entry should load without a "Language not found" error.

---

### start-editing-button-cannot-be-hidden-in-editor-mode
- **bucket**: setup
- **symptom**: The floating "Start Editing" button appears in the bottom-right corner of the site on every environment once `mode: "builder"` is set, including production. Setting `editButton.enable: false` removes the per-field edit tags but not this button.
- **frameworks**: React, Next.js, Gatsby
- **rendering_modes**: any
- **root_cause**: "Start Editing" is a separate control from the per-field edit tags. It is enabled implicitly by `mode: "builder"` and has its own config key, which was not obvious from the setup docs. `editButton` governs only the field-level tags.
- **fix**:
  1. Disable it explicitly:
     ```js
     ContentstackLivePreview.init({
       mode: "builder",
       editInVisualBuilderButton: { enable: false },
     });
     ```
  2. Better for production builds: do not initialize the SDK there at all, or use `PURGE_PREVIEW_SDK=true` / `cleanCslpOnProduction: true`.
- **verification**: Load the production URL; no floating Start Editing button. Load the preview environment; the button is present when you want it.

---

### onboarding-check-card-not-visible-or-appears-unexpectedly
- **bucket**: setup
- **symptom**: A "Preview Service Not Enabled" popup appeared for teams that had not changed anything, then disappeared days later on its own. Conversely, other teams never see the status card at all when they want to diagnose a failing integration.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: Each product keeps its own stack setting, and they do not agree on what "unset" means. Timeline treats an unset value as visible. Live Preview treats an unset value as hidden. Visual Editor depends on whether its settings object exists at all. Meanwhile the Visual Experience settings screen renders the toggle as on whenever the value is unset, so a stack that never explicitly saved the setting can show the toggle on while Live Preview behaves as though it is off. Separately, the checks run asynchronously with a timeout, so the card can appear briefly on a correctly configured site whose first preview fetch is slow, then clear itself once the request lands.
- **fix**:
  1. Open Settings → Visual Experience and click Save without changing anything. The form always submits all three products' visibility keys, and an unset value arrives in the form as on, so a single save writes an explicit `true` for Live Preview, Visual Editor and Timeline at once. That removes the unset ambiguity and makes all three agree.
  2. Check the setting for the product actually being used. Live Preview, Visual Editor and Timeline each have their own, under Settings → Visual Experience.
  3. Read the one step the card shows. The gates run as an ordered chain that stops at the first failure, so the card names a single gate — that is the configuration gap, and every gate before it has already passed.
  4. If it still does not appear for one user but does for others, that user dismissed it. The suppression is stored per stack in their browser, and no stack-level save clears it — they need to clear site data for the app origin, or use another browser profile.
  5. If the card flashes then clears on a working site, no action is needed — the first preview request simply arrived after the check timeout.
- **verification**: Open an entry in the product in question and confirm the status card appears. If it does not appear after saving the setting explicitly, it is being suppressed locally rather than by the stack setting.

---

### visual-experience-navigation-missing-for-the-stack
- **bucket**: setup
- **symptom**: The "Visual Experience" / builder-mode option does not appear in the Contentstack navigation at all, so the team cannot open the builder and assumes their integration is wrong.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: Entirely CMS-side. Three things gate the navigation entry: plan entitlement, organization-level enablement, and the stack's own Live Preview setting. **Nothing in the application affects it.** If the nav entry is absent, stop looking at the site: no SDK version, `init()` option, edit tag or fetch change can make it appear. Only the third of those is visible to the customer — plan entitlement and org enablement cannot be checked from the CMS UI.
- **fix**:
  1. Have the user check the one thing they can see: Live Preview enabled on the stack, under Settings → Visual Experience.
  2. If that is on and the navigation entry is still missing, stop there and contact Contentstack Support. Whether the plan includes Visual Editor, and whether it is enabled for the organization, are not things the user can verify or change, so do not send them looking.
- **verification**: The Visual Experience option appears in the entry's navigation. Only once it opens is there any point looking at the integration itself.

---

### third-party-cookies-blocked-inside-the-preview-iframe
- **bucket**: setup
- **symptom**: The site renders in the preview pane but behaves as if logged out, or without personalization, locale or currency preferences. Anything driven by the site's own cookies is lost.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: Inside the preview iframe the site is a third-party context relative to the Contentstack app origin, and browsers block third-party cookies by default. Only cookies set with `SameSite=None; Secure` survive, and that attribute deliberately weakens the protection that stops a cookie being sent from other sites.
- **fix**:
  1. **Start by asking whether the cookie matters here at all.** Preview is for reviewing content, not for exercising session state. Most sites do not need their cookies to render the page an author is checking, and the right outcome is usually that the site degrades gracefully in the iframe rather than that the cookie policy changes.
  2. If the content genuinely cannot render without it, prefer an alternative to loosening cookies: drive the preference from a query parameter or header the preview URL can carry, or give preview a dedicated path that does not depend on the cookie.
  3. Only if neither works, set `SameSite=None; Secure` — **and only on the preview deployment, never on production**. Scope it to the preview host so the production site keeps its stricter policy. Do not apply it site-wide to make preview convenient.
  4. Cookie-gated content needs a preview-specific auth path regardless. The iframe cannot inherit the parent's session.
- **verification**: The page renders in the intended state inside the preview iframe, and the production site's cookies still carry their original `SameSite` policy. Confirm the second part explicitly — this is the step most likely to be applied too broadly.

---

### chrome-local-network-access-blocks-preview-of-localhost
- **bucket**: setup
- **symptom**: A previously working local Live Preview setup breaks with
  `Access to fetch at 'http://localhost:5173/' from origin 'https://<region>-app.contentstack.com' has been blocked by CORS policy: Permission was denied for this request to access the 'unknown' address space`.
  Chrome only; Safari unaffected. Downgrading the SDK does not help.
- **frameworks**: framework-agnostic (Vite, Next.js dev servers)
- **rendering_modes**: any
- **root_cause**: Chrome's Local Network Access / Private Network Access restriction. A public HTTPS origin (the Contentstack app) reaching a private or loopback address (`localhost`) now requires an explicit browser permission. Nothing changed in the SDK or in Contentstack.
- **fix**:
  1. Accept the Chrome "Local network access" permission prompt for the Contentstack app origin, or enable it manually in Chrome → Site settings for that origin.
  2. If you would rather not ask every author to grant it, preview against a deployed HTTPS host instead of `localhost`.
- **verification**: Reload Live Preview in Chrome; the `OPTIONS`/`GET` to the local dev server succeeds and the iframe renders.

---

### cslp-tags-contain-the-literal-string-undefined
- **bucket**: setup
- **symptom**: `data-cslp` attributes in the DOM contain `undefined` where the entry uid should be. Inline editing does not work and edit mapping silently fails on those elements.
- **frameworks**: Next.js
- **rendering_modes**: SSR
- **root_cause**: `addEditableTags()` was called once with an array or collection of entries rather than with a single entry object. It reads `uid` off the object it is handed; an array has no `uid`, so every generated tag interpolates `undefined`.
- **fix**:
  1. Loop the result set and call the helper per entry:
     ```
     for (const entry of result) {
       addEditableTags(entry, contentTypeUid, true, entry.locale);
     }
     ```
  2. Pass each entry's own content type uid, not the page's, when the collection mixes content types.
  3. Confirm the object you pass actually has a `uid` property; if your fetch layer strips system fields, restore them first.
- **verification**: Search the rendered HTML for `cslp` and confirm no attribute value contains `undefined`.

---

### ssg-preview-needs-csr-mode
- **bucket**: setup
- **symptom**: Live Preview on a statically generated site is unreliable or simply shows build-time content: blank or black screens, flicker, an auth prompt on reload, or edits that never appear no matter what. The hash is on the URL and never reaches the fetch.
- **frameworks**: Next.js, Gatsby, Astro, framework-agnostic
- **rendering_modes**: SSG/ISR
- **root_cause**: Two halves of the same mistake. A prerendered page cannot read query parameters at request time, so the `live_preview` hash can never reach a build-time data fetch — static output is published-only content by definition. And in SSR mode the SDK reloads the page after every edit, which on a static site just re-serves the same prerendered HTML. SSG is supported, but only in CSR mode.
- **fix**:
  1. Initialize with `ssr: false`. Edits then fire an `onEntryChange` callback instead of a page reload.
  2. Pass `stackSdk` in the init config. It is mandatory in CSR mode, and it is also what the SDK uses to default `ssr`, so omitting it silently selects SSR behaviour.
  3. Implement `onEntryChange`: subscribe on the client, refetch the entry, update the UI. No rebuild is needed.
  4. Remove any `Stack.livePreviewQuery()` call from middleware. It is SSR-only and must not run on a static route.
  5. If the site mixes static and server-rendered routes, make the mode conditional per route rather than per app.
  6. If a route must stay server-rendered, make only the preview path dynamic: detect `live_preview` in `searchParams` and force that request dynamic. Do not combine a whole-route cache directive with a page that needs `searchParams` — split the condition at the fetch, not the route.
- **verification**: Edit a field. The preview updates in place with no page reload, no flicker and no auth prompt, and the network tab shows a request to the preview host carrying the unsaved value.
