# Contentstack guidance for kickstart-next

Use this when changing how `kickstart-next` talks to Contentstack, handles preview, resolves regions/hosts, or aligns with the seeded content model.

## Delivery and preview

- Keep stack configuration and fetching centralized in `lib/contentstack.ts`.
- Create the stack with `@contentstack/delivery-sdk`, using API key, delivery token, environment, region, optional custom delivery host, and `live_preview` options.
- Initialize Live Preview with `@contentstack/live-preview-utils` using builder mode, stack SDK/config, stack details, client URL params, and edit button settings.
- Query the `page` content type by URL when resolving pages. In `kickstart-next`, `getPage(url)` filters `url` with `QueryOperation.EQUALS` and returns the first `Page` entry.
- When preview mode is enabled, add editable tags with `contentstack.Utils.addEditableTags()` and preserve `$` attributes on entries, fields, and modular blocks.

## Preview versus production

- Preserve the split between production server rendering and preview client refreshes.
- `app/page.tsx` should fetch `getPage("/")` server-side before branching so both production and preview receive initial content.
- Preview should render `components/Preview.tsx`, initialize Live Preview client-side, subscribe to entry changes, and refetch the current path.

## Regions and hosts

- Prefer Contentstack endpoint helpers where already used by the repo. Current `kickstart-next` uses `getContentstackEndpoint(region, "", true)` from `@contentstack/utils`.
- Keep advanced host overrides documented and wired consistently:
  - Delivery host override: `NEXT_PUBLIC_CONTENTSTACK_CONTENT_DELIVERY` in `kickstart-next`.
  - Preview host override: `NEXT_PUBLIC_CONTENTSTACK_PREVIEW_HOST` in `kickstart-next`.
  - Application or Live Preview UI host override: `NEXT_PUBLIC_CONTENTSTACK_CONTENT_APPLICATION` in `kickstart-next`.
  - Image hostname override: `NEXT_PUBLIC_CONTENTSTACK_IMAGE_HOSTNAME` in `kickstart-next`.
- If a variable is supported in code but missing from `.env.example` or README setup docs, update the docs/example when touching that area.

## Environment variables

- Required for normal operation: `NEXT_PUBLIC_CONTENTSTACK_API_KEY`, `NEXT_PUBLIC_CONTENTSTACK_DELIVERY_TOKEN`, `NEXT_PUBLIC_CONTENTSTACK_ENVIRONMENT`, `NEXT_PUBLIC_CONTENTSTACK_REGION`.
- Required for preview mode: `NEXT_PUBLIC_CONTENTSTACK_PREVIEW=true` and `NEXT_PUBLIC_CONTENTSTACK_PREVIEW_TOKEN`.
- Advanced/dedicated-environment overrides: `NEXT_PUBLIC_CONTENTSTACK_CONTENT_DELIVERY`, `NEXT_PUBLIC_CONTENTSTACK_PREVIEW_HOST`, `NEXT_PUBLIC_CONTENTSTACK_CONTENT_APPLICATION`, `NEXT_PUBLIC_CONTENTSTACK_IMAGE_HOSTNAME`.
- Keep real tokens out of committed files. Use placeholder values in `.env.example`, README snippets, and docs.

## Seed alignment

- Assume the app is aligned to the `contentstack/kickstart-stack-seed` stack unless the repo says otherwise.
- For a compact schema map, read [content-model.md](content-model.md) before changing content type UIDs, field UIDs, modular blocks, TypeScript entry shapes, or renderer bindings.
- Changing content type UIDs, field UIDs, or modular block shapes requires matching updates to `lib/types.ts`, renderers, docs, and Live Preview bindings.
- Preserve the `Page` fields expected by the seed: `title`, `url`, `description`, `image`, `rich_text`, and `blocks`.
- Preserve modular block support for `block.title`, `block.copy`, `block.image`, `block.layout`, and `_metadata.uid` unless intentionally changing the seed contract.
- Keep CSLP shapes aligned with the fields rendered in components. `$` mappings are needed on entries, assets, and modular blocks for Visual Builder editing.

## Rendering safety

- Continue sanitizing rich text HTML with `isomorphic-dompurify` before `dangerouslySetInnerHTML`.
- Keep `VB_EmptyBlockParentClass` on empty modular block containers so Visual Builder can target empty block areas.
