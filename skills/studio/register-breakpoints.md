---
name: register-breakpoints
---

## When to use

Register default/tablet/mobile breakpoints at SDK boot and verify the canvas breakpoint switcher renders.

Use when wiring responsive viewports into a Studio host app, e.g. "add tablet/mobile breakpoints", "the breakpoint switcher is missing from my canvas toolbar", or validating a breakpoint config against `BreakpointInput`. Run AFTER `install-studio` and `setup-section-preview`. The switcher only appears once the canvas mounts and the registry has at least two breakpoints.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Register Breakpoints (default + tablet + mobile)

## Context

Studio's canvas can preview a composition at multiple viewport sizes. The host app declares those viewports once at bootstrap by calling `registerBreakpoints` from `@contentstack/studio-react`. The first entry is always the `default` breakpoint (no `query` key). Subsequent entries carry a raw CSS media query string plus a `previewSize` used to resize the canvas iframe.

The shape comes from `@contentstack/studio-registry` (`breakpoint-registry.type.ts`):

```ts
interface Breakpoint {
  id: string;
  displayName: string;
  query: string;                         // raw CSS media query
  previewSize: { width: number; height: number };
}
// Input tuple: first entry MUST be the default and MUST NOT carry `query`.
type BreakpointInput = [DefaultBreakpoint, ...PreProcessedBreakpoint[]];
```

The registry tracks unique `id`s and unique `displayName`s. Duplicates throw. The call must run **before** any `<StudioCanvas />` mounts, so it belongs in the same bootstrap module as `registerComponent` / `registerDesignTokens` (commonly `src/studio/bootstrap.ts` or wherever your app shell already imports `@/lib/contentstack`).

## Task

1. **Locate the bootstrap module: by content, not by path.** `grep -rln "registerComponent" src app lib 2>/dev/null` (path lists produce false negatives on `src/app`, route groups, and locale segments). Typical homes are ( `src/studio/bootstrap.ts`, `src/studio/registerComponents.ts`, or whatever the project pulls in from `@/lib/contentstack`). If none exists, create `src/studio/bootstrap.ts` and import it from the app shell (`app/layout.tsx`, `src/main.tsx`, `app/root.tsx`, etc.) for its side effects.

2. **Add the import** at the top of that file:

   ```ts
   import { registerBreakpoints } from "@contentstack/studio-react";
   ```

3. **Call `registerBreakpoints` before any canvas surface renders.** Use the user-provided values. The structure must be:

   ```ts
   registerBreakpoints([
     {
       id: "default",                              // required literal
       displayName: "<defaultDisplayName>",
       // NO `query` key on default — registry throws if present
       previewSize: { width: <defaultWidth>, height: <defaultHeight> },
     },
     {
       id: "tablet",
       displayName: "Tablet",
       query: "<tabletQuery>",
       previewSize: { width: <tabletWidth>, height: <tabletHeight> },
     },
     {
       id: "mobile",
       displayName: "Mobile",
       query: "<mobileQuery>",
       previewSize: { width: <mobileWidth>, height: <mobileHeight> },
     },
   ]);
   ```

4. **Confirm uniqueness.** Every `id` and every `displayName` in the array must be unique. The registry maintains a `uniqueNames` set and throws `Duplicate breakpoint name '<id>'` on conflict.

5. **Restart the dev server.** Studio reads the registry once at boot. HMR updates may not re-register. A clean restart is the only reliable way to pick up a new array.

6. **Verify in the canvas.** Open a composition in Studio canvas and walk through the verification checks below.

## Inputs needed from the user

In this order. Defaults above are sensible if the user is unsure. Keep going with them unless they explicitly want different values.

1. `defaultDisplayName`: label shown on the desktop switcher button
2. `defaultWidth` / `defaultHeight`: canvas iframe size when "default" is active
3. `tabletQuery`: CSS media query string (e.g. `(max-width: 1024px)`)
4. `tabletWidth` / `tabletHeight`: preview iframe size at tablet
5. `mobileQuery`: CSS media query string (e.g. `(max-width: 640px)`)
6. `mobileWidth` / `mobileHeight`: preview iframe size at mobile

Pick representative device widths inside each media-query range. A `(max-width: 640px)` rule with a 1024-wide `previewSize` will mislead the author.

## Acceptance

This skill succeeds only when ALL of the following hold. If any fails, surface the failure and stop.

- [ ] `registerBreakpoints` is imported from `@contentstack/studio-react` in the bootstrap module
- [ ] The call runs at module load (no lazy wrapping in a component effect)
- [ ] First entry has `id: "default"` and NO `query` key (the doc example showing `query: ""` is wrong. Omit the key entirely: the registry rewrites it to `"*"` internally)
- [ ] Every `id` and `displayName` is unique
- [ ] Each non-default entry has both `query` and `previewSize`
- [ ] Canvas toolbar renders three buttons with the configured `displayName`s
- [ ] Clicking each switcher resizes the canvas iframe to the matching `previewSize`
- [ ] Opening the Design panel on any component shows breakpoint-scoped overrides. Switching the breakpoint changes the active slot
- [ ] A canvas iframe screenshot at each breakpoint (not just an a11y snapshot: iframe contents are opaque to it) shows the composition reflowing as expected

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| `query` set on default | Throws `Default breakpoint should not have a query` | Omit the key entirely |
| First entry not `id: "default"` | Throws `First breakpoint must be default` | Put the default entry first |
| Missing `previewSize` or `query` on non-default entries | Throws `Breakpoint '<field>' is required` | Provide both for every non-default entry |
| Switcher not visible | `registerBreakpoints` ran after canvas mount, or never ran | Move it into the same boot path as `registerComponent`, before rendering |
| `previewSize` mismatched to query range | Canvas frame misrepresents the device | Pick a representative width inside the media-query range |
| Mobile styles bleeding into desktop | Base styles were set while on the Mobile breakpoint | Design `default` first, then override downward |

## See also

- `install-studio` and `setup-section-preview` for the prerequisite setup.
- `troubleshoot-canvas` if the switcher never appears even after a clean restart.
