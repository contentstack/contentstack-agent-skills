---
name: troubleshoot
---

## When to use

Symptom router: classify a Studio failure (canvas, binding, URL resolution, SSR, fresh-setup) and route to the ONE specialist diagnostic skill. Don't load every diagnostic. Route first.

Use as the FIRST step whenever Studio isn't working. Phrases: "Studio broken", "help debug Studio", "canvas blank", "composition not rendering", "binding wrong". Routes to the right specialist. Do NOT use to verify a fresh install (use `verify-setup`). Do NOT skip and invoke specialists directly when the symptom is ambiguous. Let the router classify first.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Troubleshoot Studio: symptom router

## Why route first

Studio has five distinct failure surfaces, each with its own specialist diagnostic. Loading all five wastes ~10K tokens and lets the wrong specialist mis-diagnose. This skill is the lean classifier: read it, match the symptom to ONE specialist, load that one.

## Classify the symptom

Match the user's complaint against the most specific row. **Load only the matching specialist.** Symptoms ordered by frequency.

| Symptom (verbatim or close paraphrase) | Failure surface | Load this specialist |
|---|---|---|
| Canvas is **blank** / shows the wrong page / "Component Loading Error" / iframe never finishes loading / "SDK Not Initialized" popup / preview entry won't update / authentication failed | **Canvas iframe**: the editor's render surface inside Studio | [`troubleshoot-canvas`](troubleshoot-canvas.md) |
| Component **renders but the bound value is wrong, empty, or shows the literal path** (`{{entry.title}}`) / binding chip looks correct but rendered output is stale / Repeater iterates wrong field / Condition Block doesn't disambiguate | **Data binding**: the value resolution path | [`troubleshoot-data-binding`](troubleshoot-data-binding.md) |
| **Live-site URL** resolves to the wrong composition / two templates match the same URL non-deterministically / `/blog/post-1` 404s on the visitor site / `*` wildcard pattern stopped matching / `:slug` comes back literal | **URL resolution**: pattern matching at the SDK level | [`troubleshoot-composition-resolution`](troubleshoot-composition-resolution.md) |
| **Server-side render fails**: "Attempted to call Page() from the server" / "Element type is invalid" / `useData()` warning / "is registered as lazy but hasn't been loaded yet" / "Component with type 'X' is not registered" from the server bundle / hydration mismatch around composition trees | **SSR / RSC**: server render path | [`troubleshoot-ssr-rendering`](troubleshoot-ssr-rendering.md) |
| **Fresh install just done, does it actually work end-to-end?** ("I just ran install-studio, how do I verify it's wired?") / regression check ("worked yesterday, what broke?") | **Layered smoke test** (not symptom diagnosis) | [`verify-setup`](verify-setup.md) |

## When the symptom doesn't clearly match a row

Two paths:

1. **Ask the user one clarifying question**: "Is the failure on the canvas inside Studio, on the live site, or during a build / SSR step?" That maps to canvas / URL resolution / SSR respectively. If the answer is "the value renders but is wrong", route to data binding.

2. **Default to canvas-test pre-flight.** If the user is unsure where the failure is, [`troubleshoot-canvas`](troubleshoot-canvas.md) leads with a section-test pre-flight that rules out 80% of misdirections before reading any symptom row. Run that, then route based on what the pre-flight finds.

## What this skill does NOT do

- Does NOT execute the diagnostic. That's the specialist's job. This skill ends after routing.
- Does NOT cover authoring-quality issues ("the layout looks wrong", "this Section needs different styling"). Those are design / build issues. Route to [`build-section`](build-section.md) or [`design-section-from-jsx`](design-section-from-jsx.md).
- Does NOT replace [`verify-setup`](verify-setup.md) for fresh-install smoke testing. That's its own intent, not a symptom.

## Acceptance

Skill succeeds when:
- [ ] The user's symptom was matched to exactly ONE specialist row (no "load all five").
- [ ] The specialist was invoked / linked.
- [ ] If the symptom didn't match, a clarifying question was asked OR the canvas-test pre-flight was run.
