# Timeline FAQ

Timeline previews an entry at a point in time. It shares the Live Preview SDK and the same preview
host, but it is a distinct product: it has its own Onboarding Check with three gates rather than
five (see [onboarding-check.md](onboarding-check.md)), and it carries a `preview_timestamp` alongside the usual
`live_preview` hash.

If plain Live Preview does not work, fix that first — everything here assumes the preview path is
already good.

### timeline-preview-timestamp-ignored-or-dropped
- **bucket**: preview-runtime
- **symptom**: Timeline preview shows the wrong point in time — either the current version regardless of the date picked, or version 1 of the entry for every timestamp. Reference-field changes that render correctly on the live site, in Live Preview, and in Visual Editor do not show in Timeline. Clicking an internal link inside Timeline preview loses the timestamp and the page reloads twice.
- **frameworks**: Next.js, React, framework-agnostic
- **rendering_modes**: CSR | SSR
- **root_cause**: Timeline adds `preview_timestamp` to the iframe URL alongside the `live_preview` hash, and the site must forward **both** to the preview service. Common failures: (a) the app only forwards the hash; (b) the app calls `stack.livePreviewQuery()` manually on the client and passes the hash without `preview_timestamp`, overwriting what the SDK had; (c) client-side internal navigation rewrites the iframe URL and drops the query params, so the next render has no timestamp (the double reload is Timeline re-injecting it); (d) a Timeline tracker is a different tracker type than a Visual Editor tracker, so a hash captured from one context does not work in the other.
- **fix**:
  1. On the server, read `preview_timestamp` from the request URL on every request and pass it with the hash: `stack.livePreviewQuery({ live_preview: hash, preview_timestamp: ts, content_type_uid, entry_uid })`.
  2. On the client, prefer letting the SDK read the params from `document.location` — do not call `livePreviewQuery()` yourself. If you must, always include `preview_timestamp` next to the hash.
  3. Preserve `live_preview` and `preview_timestamp` across client-side route changes, or force a full navigation inside preview. Use Timeline's URL navigation box rather than in-page link clicks when demoing.
  4. Do not reuse a hash across contexts. A Timeline hash comes from the Timeline preview page's tracker call; a Visual Editor hash comes from Visual Editor.
  5. Append the params correctly when the base URL already carries a query string, rather than overwriting the existing one.
- **verification**: Pick a future scheduled-publish marker; the request to the preview host should carry both headers and the response `_version` should match the version expected at that timestamp.

---

### timeline-compare-highlights-no-differences
- **bucket**: visual-editor
- **symptom**: Timeline **Compare Website** renders both versions but highlights no differences between them.
- **frameworks**: framework-agnostic
- **rendering_modes**: any
- **root_cause**: Highlight Differences works by matching changed fields to DOM elements through their `data-cslp` attributes. It needs live edit tags enabled on the site **and** a `data-cslp` physically present on the element that renders the changed field. Where the tag coverage is thin, or the specific field that changed carries no tag, the diff has nothing to attach the highlight to and the comparison looks empty even though both versions rendered.
- **fix**:
  1. Confirm live edit tags are enabled and rendered — see `edit-tags-not-generated-or-not-spread` in `faq-setup.md`.
  2. In the Timeline iframe, run
     `[...document.querySelectorAll('[data-cslp]')].map(el => ({tag: el.tagName, cslp: el.getAttribute('data-cslp')}))`
     and confirm the **specific field you changed** appears in that list.
  3. If the changed field has no tag, add it and retest.
- **verification**: Change one plain text field in a release, open Timeline → Compare Website, and confirm that element is highlighted.
