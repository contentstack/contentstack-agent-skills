# Symptom index

Find the reported symptom, go to the entry. Symptoms are worded the way users report them, not the
way the underlying cause would be described.

Setup entries come first because an unmet setup contract produces a large share of what gets
reported as behavioural. If the integration has never fully worked, work the four contracts in
SKILL.md before reading anything below.


## Setup and first integration

| Symptom | Entry |
|---|---|
| Live Preview / Visual Editor loads the site fine, but edits made in the entry form or the right-hand panel nev… | [app-fetches-from-delivery-cdn-instead-of-preview-service](faq-setup.md#app-fetches-from-delivery-cdn-instead-of-preview-service) |
| The Live Preview / Visual Editor pane is blank or shows "`<your-host>` refused to connect" | [iframe-blocked-by-x-frame-options-or-csp-frame-ancestors](faq-setup.md#iframe-blocked-by-x-frame-options-or-csp-frame-ancestors) |
| Preview API requests fail with `{"error_message":"Please create tracker before starting live preview session",… | [error-382-create-tracker-before-starting-live-preview-session](faq-setup.md#error-382-create-tracker-before-starting-live-preview-session) |
| Nothing on the page is inline-editable: no hover highlight, no edit button, no field toolbar | [edit-tags-not-generated-or-not-spread](faq-setup.md#edit-tags-not-generated-or-not-spread) |
| Live Preview opens the site's home page or a "Page Not Found" instead of the entry being edited | [preview-url-does-not-resolve-to-the-app-route](faq-setup.md#preview-url-does-not-resolve-to-the-app-route) |
| Visual Editor features silently do nothing on an otherwise working Live Preview setup; or a version bump break… | [sdk-version-below-visual-editor-minimum-or-breaking-major-upgrade](faq-setup.md#sdk-version-below-visual-editor-minimum-or-breaking-major-upgrade) |
| The Live Preview environment selector is greyed out or shows "No environments available"; preview loads the wr… | [environment-base-url-misconfigured-or-missing-for-a-locale](faq-setup.md#environment-base-url-misconfigured-or-missing-for-a-locale) |
| The Live Preview "Edit" pencil button appears on the normal production or UAT site for ordinary visitors, or t… | [edit-button-rendered-outside-a-live-preview-session](faq-setup.md#edit-button-rendered-outside-a-live-preview-session) |
| `Access to fetch at 'https://<region>-rest-preview.contentstack.com/v3/...' from origin '<site origin>' has be… | [cors-blocked-on-preview-api-requests](faq-setup.md#cors-blocked-on-preview-api-requests) |
| Two opposite failures from the same mistake | [ssr-stack-instance-shared-or-duplicated](faq-setup.md#ssr-stack-instance-shared-or-duplicated) |
| In a Next.js App Router project, Live Preview never activates: no hash in the URL, no SSR-mode detection, edit… | [nextjs-app-router-init-must-run-in-a-client-component](faq-setup.md#nextjs-app-router-init-must-run-in-a-client-component) |
| "Preview Service Not Enabled" shows in the preview panel on a setup that otherwise works | [legacy-management-token-setup-not-migrated-to-preview-token](faq-setup.md#legacy-management-token-setup-not-migrated-to-preview-token) |
| Preview opens for pages that already exist on the main branch but never shows updates, and any page that exist… | [branch-or-alias-mismatch-between-app-token-and-entry](faq-setup.md#branch-or-alias-mismatch-between-app-token-and-entry) |
| Live Preview never activates or the preview panel reports the service is not enabled, even though the stack se… | [wrong-region-hosts-in-sdk-and-preview-config](faq-setup.md#wrong-region-hosts-in-sdk-and-preview-config) |
| Start Editing / the Edit button opens Visual Editor or the entry editor with `locale=en-us` even though the st… | [locale-defaults-to-en-us-in-init](faq-setup.md#locale-defaults-to-en-us-in-init) |
| The floating "Start Editing" button appears in the bottom-right corner of the site on every environment once `… | [start-editing-button-cannot-be-hidden-in-editor-mode](faq-setup.md#start-editing-button-cannot-be-hidden-in-editor-mode) |
| A "Preview Service Not Enabled" popup appeared for teams that had not changed anything, then disappeared days… | [onboarding-check-card-not-visible-or-appears-unexpectedly](faq-setup.md#onboarding-check-card-not-visible-or-appears-unexpectedly) |
| The "Visual Experience" / builder-mode option does not appear in the Contentstack navigation at all, so the te… | [visual-experience-navigation-missing-for-the-stack](faq-setup.md#visual-experience-navigation-missing-for-the-stack) |
| The site renders in the preview pane but behaves as if logged out, or without personalization, locale or curre… | [third-party-cookies-blocked-inside-the-preview-iframe](faq-setup.md#third-party-cookies-blocked-inside-the-preview-iframe) |
| A previously working local Live Preview setup breaks with `Access to fetch at 'http://localhost:5173/' from or… | [chrome-local-network-access-blocks-preview-of-localhost](faq-setup.md#chrome-local-network-access-blocks-preview-of-localhost) |
| `data-cslp` attributes in the DOM contain `undefined` where the entry uid should be | [cslp-tags-contain-the-literal-string-undefined](faq-setup.md#cslp-tags-contain-the-literal-string-undefined) |
| Live Preview on a statically generated site is unreliable or simply shows build-time content: blank or black s… | [ssg-preview-needs-csr-mode](faq-setup.md#ssg-preview-needs-csr-mode) |

## Preview runtime

| Symptom | Entry |
|---|---|
| Selecting a variant (or switching audience in Audience Preview) in Visual Experience keeps rendering the base… | [variant-or-audience-switch-shows-base-entry](faq-preview-runtime.md#variant-or-audience-switch-shows-base-entry) |
| Preview works on localhost but not on a deployed environment with identical code and config — the setup status… | [cached-response-serves-stale-preview](faq-preview-runtime.md#cached-response-serves-stale-preview) |
| A page that renders fine in the entry editor and on the live site comes back blank in Visual Experience for a… | [locale-fallback-blank-or-wrong-locale-in-preview](faq-preview-runtime.md#locale-fallback-blank-or-wrong-locale-in-preview) |
| Edits only appear after manually reloading the preview | [csr-edits-need-manual-refresh](faq-preview-runtime.md#csr-edits-need-manual-refresh) |
| Preview works on the entry's own URL, but navigating within the site inside the preview panel breaks it — "Pag… | [spa-client-navigation-loses-preview-context](faq-preview-runtime.md#spa-client-navigation-loses-preview-context) |
| `ContentstackLivePreview.hash` logs as an empty string, so the code that gates on it never switches to the pre… | [hash-empty-outside-the-preview-iframe](faq-preview-runtime.md#hash-empty-outside-the-preview-iframe) |
| The very first `onEntryChange` fetch after opening the preview returns published data even though the entry wa… | [stale-first-fetch-when-editing-a-referenced-entry](faq-preview-runtime.md#stale-first-fetch-when-editing-a-referenced-entry) |
| Live Preview works for top-level fields but an edit to an entry that is referenced inside another entry does n… | [legacy-management-token-preview-breaks-on-references](faq-preview-runtime.md#legacy-management-token-preview-breaks-on-references) |
| One user sees an empty or partly empty page in Live Preview / Visual Editor while colleagues on the same stack… | [preview-renders-empty-for-a-restricted-user](faq-preview-runtime.md#preview-renders-empty-for-a-restricted-user) |
| Ad slots, consent widgets, or other host-dependent third-party scripts intermittently fail to render inside Li… | [third-party-scripts-misbehave-inside-the-preview-iframe](faq-preview-runtime.md#third-party-scripts-misbehave-inside-the-preview-iframe) |

## Visual Editor

| Symptom | Entry |
|---|---|
| Edit tags on fields that come from a referenced entry do nothing when clicked | [cslp-not-rebased-to-referenced-entry](faq-visual-editor.md#cslp-not-rebased-to-referenced-entry) |
| Visual Editor will not initialize for any non-fallback locale on an older stack, while Live Preview works | [locale-case-mismatch-lowercased-cslp](faq-visual-editor.md#locale-case-mismatch-lowercased-cslp) |
| An empty rich text field renders with zero height in preview mode, so there is nothing to click and the author… | [empty-fields-are-not-clickable-on-the-canvas](faq-visual-editor.md#empty-fields-are-not-clickable-on-the-canvas) |
| A page or component with an empty modular-block / multiple field shows no "+ Add Component" affordance, so aut… | [empty-block-add-button-not-appearing-or-failing](faq-visual-editor.md#empty-block-add-button-not-appearing-or-failing) |
| With GraphQL, edit tags are generated but Visual Editor cannot resolve them | [graphql-connection-wrappers-break-cslp](faq-visual-editor.md#graphql-connection-wrappers-break-cslp) |
| Interactive components stop working inside the editor canvas: carousel arrows, tab strips, accordions, dropdow… | [canvas-swallows-site-click-events](faq-visual-editor.md#canvas-swallows-site-click-events) |
| Variant content renders on the canvas but Highlight Variant outlines nothing and audience mode shows no variant fields | [highlight-variant-or-audience-mode-does-nothing](faq-visual-editor.md#highlight-variant-or-audience-mode-does-nothing) |

## Timeline

| Symptom | Entry |
|---|---|
| Timeline preview shows the wrong point in time — either the current version regardless of the date picked, or… | [timeline-preview-timestamp-ignored-or-dropped](faq-timeline.md#timeline-preview-timestamp-ignored-or-dropped) |
| Timeline Compare Website renders both versions but highlights no differences between them. | [timeline-compare-highlights-no-differences](faq-timeline.md#timeline-compare-highlights-no-differences) |
