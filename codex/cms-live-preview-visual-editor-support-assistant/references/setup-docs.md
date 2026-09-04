# Setup: the documentation is the source of truth

For setup, follow the official Contentstack documentation. Do not reconstruct setup steps from
memory and do not invent a procedure. Identify the framework and rendering mode, open the matching
page, and follow it.

The rest of this skill exists for when the documented setup has been followed and something still
does not work. That is a different job, and it is where the mined failure catalogue earns its keep.

## Pick the page

Establish framework and rendering mode first, then route.

### Start here regardless

- [Set Up Live Preview for your Website](https://www.contentstack.com/docs/developers/set-up-live-preview/set-up-live-preview-for-your-website) — the setup hub
- [How Live Preview Works](https://www.contentstack.com/docs/developers/set-up-live-preview/how-live-preview-works) — the model to reason from
- [How Live Preview Works with SDK](https://www.contentstack.com/docs/headless-cms/how-live-preview-works-with-sdk) — how `ssr` is resolved and how the hash travels

### By framework and mode

| Framework and mode | Page |
|---|---|
| Next.js App Router, CSR | [Live Preview Implementation for Next.js CSR App Router](https://www.contentstack.com/docs/developers/set-up-live-preview/live-preview-implementation-for-nextjs-csr-app-router) |
| Next.js App Router, SSR | [Live Preview Implementation for Next.js SSR App Router](https://www.contentstack.com/docs/developers/set-up-live-preview/live-preview-implementation-for-nextjs-ssr-app-router) |
| React, CSR | [Live Preview Implementation for ReactJS CSR Website](https://www.contentstack.com/docs/developers/set-up-live-preview/live-preview-implementation-for-reactjs-csr-website) |
| Any framework, SSG | [Set Up Live Preview for Static-Site Generator (SSG)](https://www.contentstack.com/docs/developers/set-up-live-preview/set-up-live-preview-for-static-site-generator-ssg) — runs in CSR mode, `ssr: false` |
| Any framework, SSR over REST | [Set Up Live Preview with REST for Server-Side Rendering](https://www.contentstack.com/docs/developers/set-up-live-preview/set-up-live-preview-with-rest-for-server-side-rendering) |

### Visual Editor, on top of a working Live Preview

Visual Editor is not a separate integration. It is Live Preview plus edit tags plus `mode: "builder"`
in `init()`, so Live Preview must work first, and a setup copied from a Live Preview guide will still
fail Visual Editor's Verify Mode gate until the mode is changed from `"preview"`.

- [Set Up Visual Builder for Your Website](https://www.contentstack.com/docs/developers/set-up-visual-builder/set-up-visual-builder-for-your-website)
- [Set Up Visual Editor for Your Website](https://www.contentstack.com/docs/developers/set-up-visual-editor/set-up-visual-editor-for-your-website)
- [Set Up Live Edit Tags for Entries with REST](https://www.contentstack.com/docs/developers/set-up-live-preview/set-up-live-edit-tags-for-entries-with-rest) — the `addEditableTags()` reference

### Starters

[Kickstart Next.js](https://www.contentstack.com/docs/developers/kickstarts/next) and its siblings
are working references. When a user's setup disagrees with a kickstart, the kickstart is right.

## What the documentation will not settle

These come up constantly and are not answered by any setup page. Say so plainly rather than
guessing, and reach for `rendering-modes.md` and `faq-setup.md`.

- **Next.js Pages Router.** Supported, but has no dedicated page. Use the SSR-over-REST page for
  `getServerSideProps` and the SSG page for `getStaticProps`; the contracts are identical.
- **ISR and framework cache or draft modes.** SSG *is* documented (see the table above). ISR is
  not. Caching must be off for preview routes, and integrating with a framework's own
  cache-invalidation or draft feature is out of scope.
- **Edge runtimes.** No coverage anywhere. Untested rather than unsupported. Say that.
- **GraphQL with edit tags.** Connection wrappers break `data-cslp` paths and need a
  customer-side response normalizer. By design; see `graphql-connection-wrappers-break-cslp` in
  `faq-visual-editor.md`.
- **Frameworks with a starter but no support history.** A starter existing is not evidence the
  combination is proven.

## Two things worth stating before a user starts

**Version minimums.** Live Preview Utils v3.0+ and Delivery SDK v3.20.3+ for Visual Editor, and
Live Preview Utils v4.4.4+ for `setPageContext()`. Load exactly one copy of the preview SDK; mixing
an npm install with an ESM or CDN import of a different version produces behaviour that looks like
a configuration bug.

**`addEditableTags()` mutates and returns nothing.** It updates the entry passed as its first
argument in place. Assigning its result gives you `undefined`, which is a common first-timer
mistake. For React and JSX, `tagsAsObject` must be `true`; it defaults to `false`, which produces a
string that React cannot spread.
