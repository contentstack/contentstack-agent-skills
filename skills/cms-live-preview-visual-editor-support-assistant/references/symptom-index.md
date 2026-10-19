# Symptom index

Find the reported symptom, go to the entry. Symptoms are worded the way users report them, not the
way the underlying cause would be described.

Integration entries come first because an unmet contract produces a large share of what gets
reported as behavioural. If the integration has never fully worked, work the four contracts in
SKILL.md before reading anything below.

## Integration

| Symptom | Entry |
|---|---|
| Live Preview / Visual Editor loads the site fine, but edits made in the entry form or the right-hand panel never appear in the preview | [app-fetches-from-delivery-cdn-instead-of-preview-service](faq-integration.md#app-fetches-from-delivery-cdn-instead-of-preview-service) |
| The Live Preview / Visual Editor pane is blank or shows "`<your-host>` refused to connect" | [iframe-blocked-by-x-frame-options-or-csp-frame-ancestors](faq-integration.md#iframe-blocked-by-x-frame-options-or-csp-frame-ancestors) |
| Preview API requests fail with `{"error_message":"Please create tracker before starting live preview session","error_code":382,"status":400}` | [error-382-create-tracker-before-starting-live-preview-session](faq-integration.md#error-382-create-tracker-before-starting-live-preview-session) |
| Nothing on the page is inline-editable: no hover highlight, no edit button, no field toolbar | [edit-tags-not-generated-or-not-spread](faq-integration.md#edit-tags-not-generated-or-not-spread) |
| Live Preview opens the site's home page or a "Page Not Found" instead of the entry being edited | [preview-url-does-not-resolve-to-the-app-route](faq-integration.md#preview-url-does-not-resolve-to-the-app-route) |
| Live Preview opens the home page or the wrong page; the entry path is glued onto the last query parameter of the Base URL | [base-url-query-string-corrupts-preview-url](faq-integration.md#base-url-query-string-corrupts-preview-url) |
| Visual Editor features silently do nothing on an otherwise working Live Preview setup; or a version bump breaks a previously working integration: `setConfigFromParams` is no longer callable, `ReferenceError: window is not defined` in server code, the Edit button suddenly renders in production, or `Live_Preview_SDK: To use edit tags, you must provide the stack API key` | [sdk-version-below-visual-editor-minimum-or-breaking-major-upgrade](faq-integration.md#sdk-version-below-visual-editor-minimum-or-breaking-major-upgrade) |
| The Live Preview environment selector is greyed out or shows "No environments available"; preview loads the wrong path or the site root | [environment-base-url-misconfigured-or-missing-for-a-locale](faq-integration.md#environment-base-url-misconfigured-or-missing-for-a-locale) |
| The Live Preview "Edit" pencil button appears on the normal production or UAT site for ordinary visitors, or the `#cslp-tooltip` button element is injected into `document.body` on production even when not visible | [edit-button-rendered-outside-a-live-preview-session](faq-integration.md#edit-button-rendered-outside-a-live-preview-session) |
| `Access to fetch at 'https://<region>-rest-preview.contentstack.com/v3/...' from origin '<site origin>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource`, frequently alongside a `401 (Unauthorized)` on the same request | [cors-blocked-on-preview-api-requests](faq-integration.md#cors-blocked-on-preview-api-requests) |
| Two opposite failures from the same mistake | [ssr-stack-instance-shared-or-duplicated](faq-integration.md#ssr-stack-instance-shared-or-duplicated) |
| In a Next.js App Router project, Live Preview never activates: no hash in the URL, no SSR-mode detection, edit tags render but do nothing, or nothing at all happens when the entry is edited | [nextjs-app-router-init-must-run-in-a-client-component](faq-integration.md#nextjs-app-router-init-must-run-in-a-client-component) |
| "Preview Service Not Enabled" shows in the preview panel on a setup that otherwise works | [legacy-management-token-setup-not-migrated-to-preview-token](faq-integration.md#legacy-management-token-setup-not-migrated-to-preview-token) |
| Preview opens for pages that already exist on the main branch but never shows updates, and any page that exists only on the working branch 404s | [branch-or-alias-mismatch-between-app-token-and-entry](faq-integration.md#branch-or-alias-mismatch-between-app-token-and-entry) |
| Live Preview never activates or the preview panel reports the service is not enabled, even though the stack settings look correct | [wrong-region-hosts-in-sdk-and-preview-config](faq-integration.md#wrong-region-hosts-in-sdk-and-preview-config) |
| Start Editing / the Edit button opens Visual Editor or the entry editor with `locale=en-us` even though the stack has no `en-us` language, producing a 404 or a "Language not found" toast | [locale-defaults-to-en-us-in-init](faq-integration.md#locale-defaults-to-en-us-in-init) |
| The floating "Start Editing" button appears in the bottom-right corner of the site on every environment once `mode: "builder"` is set, including production. Setting `editButton.enable: false` removes the per-field Edit button but not this one. | [start-editing-button-cannot-be-hidden-in-editor-mode](faq-integration.md#start-editing-button-cannot-be-hidden-in-editor-mode) |
| A "Preview Service Not Enabled" popup appeared for teams that had not changed anything, then disappeared days later on its own | [onboarding-check-card-not-visible-or-appears-unexpectedly](faq-integration.md#onboarding-check-card-not-visible-or-appears-unexpectedly) |
| The "Visual Experience" / builder-mode option does not appear in the Contentstack navigation at all, so the team cannot open the builder and assumes their integration is wrong | [visual-experience-navigation-missing-for-the-stack](faq-integration.md#visual-experience-navigation-missing-for-the-stack) |
| The site renders in the preview pane but behaves as if logged out, or without personalization, locale or currency preferences | [third-party-cookies-blocked-inside-the-preview-iframe](faq-integration.md#third-party-cookies-blocked-inside-the-preview-iframe) |
| A previously working local Live Preview setup breaks with `Access to fetch at 'http://localhost:5173/' from origin 'https://<region>-app.contentstack.com' has been blocked by CORS policy: Permission was denied for this request to access the 'unknown' address space`. Chrome only; Safari unaffected. Downgrading the SDK does not help. | [chrome-local-network-access-blocks-preview-of-localhost](faq-integration.md#chrome-local-network-access-blocks-preview-of-localhost) |
| `data-cslp` attributes in the DOM contain `undefined` where the entry uid should be | [cslp-tags-contain-the-literal-string-undefined](faq-integration.md#cslp-tags-contain-the-literal-string-undefined) |
| Live Preview on a statically generated site is unreliable or simply shows build-time content: blank or black screens, flicker, an auth prompt on reload, or edits that never appear no matter what | [ssg-preview-needs-csr-mode](faq-integration.md#ssg-preview-needs-csr-mode) |

## Preview runtime

| Symptom | Entry |
|---|---|
| Selecting a variant (or switching audience in Audience Preview) in Visual Experience keeps rendering the base entry | [variant-or-audience-switch-shows-base-entry](faq-preview-runtime.md#variant-or-audience-switch-shows-base-entry) |
| Preview works on localhost but not on a deployed environment with identical code and config — the setup status can even show "Setup Complete" and edits go through in the entry form while the rendered page never changes | [cached-response-serves-stale-preview](faq-preview-runtime.md#cached-response-serves-stale-preview) |
| A page that renders fine in the entry editor and on the live site comes back blank in Visual Experience for a non-master locale | [locale-fallback-blank-or-wrong-locale-in-preview](faq-preview-runtime.md#locale-fallback-blank-or-wrong-locale-in-preview) |
| Edits only appear after manually reloading the preview | [csr-edits-need-manual-refresh](faq-preview-runtime.md#csr-edits-need-manual-refresh) |
| Preview works on the entry's own URL, but navigating within the site inside the preview panel breaks it — "Page Not Found", "You are currently previewing a different webpage", or edits silently stop applying | [spa-client-navigation-loses-preview-context](faq-preview-runtime.md#spa-client-navigation-loses-preview-context) |
| `ContentstackLivePreview.hash` logs as an empty string, so the code that gates on it never switches to the preview host | [hash-empty-outside-the-preview-iframe](faq-preview-runtime.md#hash-empty-outside-the-preview-iframe) |
| Live Preview works for top-level fields but an edit to an entry that is referenced inside another entry does not update | [legacy-management-token-preview-breaks-on-references](faq-preview-runtime.md#legacy-management-token-preview-breaks-on-references) |
| One user sees an empty or partly empty page in Live Preview / Visual Editor while colleagues on the same stack see it fully, and the published site is fine for everybody | [preview-renders-empty-for-a-restricted-user](faq-preview-runtime.md#preview-renders-empty-for-a-restricted-user) |
| Ad slots, consent widgets, or other host-dependent third-party scripts intermittently fail to render inside Live Preview while working on the live site | [third-party-scripts-misbehave-inside-the-preview-iframe](faq-preview-runtime.md#third-party-scripts-misbehave-inside-the-preview-iframe) |

## Visual Editor

| Symptom | Entry |
|---|---|
| Edit tags on fields that come from a referenced entry do nothing when clicked | [cslp-not-rebased-to-referenced-entry](faq-visual-editor.md#cslp-not-rebased-to-referenced-entry) |
| Visual Editor will not initialize for any non-fallback locale on an older stack, while Live Preview works | [locale-case-mismatch-lowercased-cslp](faq-visual-editor.md#locale-case-mismatch-lowercased-cslp) |
| An empty rich text field renders with zero height in preview mode, so there is nothing to click and the author cannot start editing it from the canvas | [empty-fields-are-not-clickable-on-the-canvas](faq-visual-editor.md#empty-fields-are-not-clickable-on-the-canvas) |
| A page or component with an empty modular-block / multiple field shows no "Add <field display name>" affordance, so authors have to go to the form panel to add the first block | [empty-block-add-button-not-appearing-or-failing](faq-visual-editor.md#empty-block-add-button-not-appearing-or-failing) |
| With GraphQL, edit tags are generated but Visual Editor cannot resolve them | [graphql-connection-wrappers-break-cslp](faq-visual-editor.md#graphql-connection-wrappers-break-cslp) |
| Interactive components stop working inside the editor canvas: carousel arrows, tab strips, accordions, dropdowns and links do nothing when clicked, while the same page works normally outside the editor | [canvas-swallows-site-click-events](faq-visual-editor.md#canvas-swallows-site-click-events) |
| Variant content renders on the canvas but Highlight Variant outlines nothing and audience mode shows no variant fields | [highlight-variant-or-audience-mode-does-nothing](faq-visual-editor.md#highlight-variant-or-audience-mode-does-nothing) |

## Timeline

| Symptom | Entry |
|---|---|
| Timeline preview shows the wrong point in time — either the current version regardless of the date picked, or version 1 of the entry for every timestamp | [timeline-preview-timestamp-ignored-or-dropped](faq-timeline.md#timeline-preview-timestamp-ignored-or-dropped) |
| Timeline Compare Website renders both versions but highlights no differences between them. | [timeline-compare-highlights-no-differences](faq-timeline.md#timeline-compare-highlights-no-differences) |
