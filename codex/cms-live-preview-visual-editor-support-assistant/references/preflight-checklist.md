# Preflight checklist

Run in order. Each step either passes or localises the problem to one contract. Stop at the first
failure and fix it before continuing, because a failure upstream makes every downstream check
meaningless.

## Before touching the application

1. **Get the Onboarding Check to appear.** It walks the contracts in order and names the first one
   that fails. Do not assume its default state: each product stores its own setting under
   Settings → Visual Experience, and an unset value resolves differently per product, so the toggle
   can read on while the card never appears. Save the setting explicitly for the product in use.
2. **Live Preview is enabled on the stack**, with a default preview environment set.
3. **A Preview Token exists**, generated against the Delivery Token the application already uses.
   A management token is not a substitute and must never reach client-side configuration.
4. **The environment has a Base URL**, and one for each locale being previewed. A missing Base URL
   presents as a greyed-out environment selector or "No environments available".
5. **The signed-in user's role can read everything the page uses.** Preview runs as that user and
   applies their full ACL — content types, entries, fields, locales, assets — so anything they
   cannot read comes back empty. Delivery uses a delivery token and applies none. Expect preview
   to differ per user, and make the site render missing data gracefully.

## Reachability

6. **The preview host is served over HTTPS** with a trusted certificate.
7. **`curl -I https://<preview-host>/<a-deep-route>`** returns no `X-Frame-Options`, and a CSP
   `frame-ancestors` that includes the Contentstack app origin. Test a deep route, not the site
   root, and confirm it holds after any redirect.
8. **Nothing sits in front of the site that cannot render in a frame**: platform password
   protection, an SSO screen setting `X-Frame-Options: DENY`, or basic auth.
9. **If previewing `http://localhost`**, confirm the browser is not blocking it. Chrome's Local
    Network Access policy blocks the app origin from framing localhost and only the user can grant
    the permission.

## Versions

10. **Live Preview Utils v3.0+ and Delivery SDK v3.20.3+** for Visual Editor. **v4.4.4+** if using
    `setPageContext()`.
11. **Exactly one copy of the preview SDK is loaded.** An npm install plus an ESM or CDN
    `<script type="module">` import of a different version produces behaviour differences that look
    like configuration bugs.

## Contract 1: init runs

12. **A `POST /live-preview/tracker` returns 2xx** when the preview panel loads. If it never fires,
    init did not run.
13. **`init()` runs on the client**, not in server-only code.
14. **The enable flag parses as a boolean in the deployed build.** A string `"false"` is truthy.
15. **`ssr` is set explicitly.** The automatic default keys off `stackSdk` and gets it wrong in both
    directions: a CSR app without `stackSdk` silently becomes SSR, and an SSG site with `ssr: true`
    produces blank screens rather than an error.
16. **`stackDetails: { apiKey, environment }` is passed explicitly.** Since v2 the SDK no longer
    derives the API key from the Stack object for edit tags.
17. **`mode: "builder"` is set if Visual Editor is the target.** Visual Editor's own onboarding check
    has a Verify Mode item that fails on `mode: "preview"`. Edit tags alone do not produce a canvas.

## Contract 2: edit tags reach the DOM

18. **A rendered field carries `data-cslp`**, formed as
    `<content_type_uid>.<entry_uid>.<locale>.<field_path>`.
19. **`addEditableTags(entry, contentTypeUid, true, locale)`** is called once on every fetched
    top-level entry. The third argument must be `true` for React and JSX. References resolved with
    `includeReference()` are rebased automatically; a separate call is only for hand-merged ones.
20. **`$` keys are spread onto leaves and containers.** Scalars: the element rendering the value.
    Multiple, reference and block fields: `entry.$.field` on the wrapper plus `entry.$["field__" + i]`
    per instance, and an empty one keeps the wrapper with `VB_EmptyBlockParentClass`. Enumerate from
    `Object.keys(entry.$)`, not from the JSX. See [edit-tags.md](edit-tags.md).
21. **Reference paths mirror the data shape.** References come back as arrays:
    `post.author[0].$?.name`, not `post.$?.author.name`.
22. **For GraphQL**, connection wrappers are flattened and `system { uid, content_type_uid }` is
    requested on every node, before `addEditableTags()` runs.

## Contract 3: the hash reaches the fetch

23. **Content requests hit a `*-preview.contentstack.com` host** during an active preview session.
    Seeing `cdn.contentstack.io` or `graphql.contentstack.com` here is the single most common setup
    failure, whatever the reported symptom was.
24. **Those requests carry `live_preview` and `preview_token` headers** and return 200.
25. **Every fetch path uses the initialized Stack instance.** A second instance, a hand-rolled
    wrapper, or a BFF that bypasses it will keep serving published content.
26. **The hash is never hardcoded or invented.** An unrecognised hash returns
    `error_code 382, Please create tracker before starting live preview session`.
27. **If the app proxies Contentstack through its own backend**, the hash is forwarded end to end.
28. **SSR only: the Stack instance is built per request.** A module-level instance leaks one
    editor's draft into other users' responses, including public traffic.
29. **Caching is bypassed for preview requests.** Any cache on the preview path serves published
    content after the host switch is already correct, and can serve preview output to real visitors.

## Behaviour

30. **Edit a field without saving.** The preview updates.
31. **Hover a tagged element in Visual Editor.** It highlights, and clicking focuses the matching
    field in the form panel.
32. **Open entries from several content types**, including a nested route and one with no `url`
    field. Each loads its own page.
33. **Navigate inside the preview pane.** Preview context survives the navigation.
34. **Load the public site in a normal browser tab.** No edit button, no `#cslp-tooltip` in the DOM,
    and no preview response served from cache.
