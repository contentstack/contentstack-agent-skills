# The Onboarding Check

Every visual experience product ships a setup check that runs automatically when the preview panel
opens and reports its result in a small floating status card. It is the highest-yield thing to ask
about, because it has already run the diagnosis the user is asking you to do.

**Always ask for a screenshot of this card before asking anything else.** The step name on it
localises the problem to one gate, and because of how the check is structured, it also tells you
everything that already passed.

## The property that makes it powerful

The gates are evaluated as a single ordered chain, and it stops at the first failure. Only one
step is ever shown.

So a card reading "Preview Service Not Enabled" is not just one fact. It proves the website loaded
in the frame, the SDK initialised, and the SDK version is supported. Three contracts are already
ruled out. Do not re-ask about them.

The inverse also holds. A card stuck on the first gate tells you nothing about any later gate,
because none of them ran. Do not theorise about the SDK when the site never loaded.

## Live Preview and Visual Editor

Five gates, in this order.

| # | Card while checking | Card on failure | What the failure means |
|---|---|---|---|
| 1 | Website Loading | **Could Not Connect to Website** | The site never rendered in the frame. Frame headers (`X-Frame-Options`, CSP `frame-ancestors`), an auth gate or password protection, a wrong or unreachable Base URL, HTTP or an untrusted certificate, or the browser blocking localhost. Nothing after this ran. |
| 2 | Verifying Live Preview SDK | **Live Preview SDK Not Initialized** | The frame loaded but no init handshake arrived. `init()` is in server-only code, the enable flag did not parse as a boolean in the deployed build, the init module was tree-shaken out, or init runs after the check window. |
| 3 | Verifying Live Preview SDK | **Outdated Live Preview SDK Version** | The handshake arrived from a version below the supported minimum. Upgrade Live Preview Utils. |
| 4 | Verifying Preview Service | **Preview Service Not Enabled** | The SDK is fine and the site is fine, but content is not coming from the Preview Service. This is the fetch layer never switching host and headers, which is the most common failure of all. |
| 5 | — | **Default Environment Not Set** | Everything works. Setup is recorded as complete. The stack simply has no default preview environment, set in stack settings. |
| — | — | **Setup Complete** | All gates passed. |

The exact body text is worth quoting back to users, because they often paraphrase it into
something ambiguous. Gate 1 reads "Ensure the website is live and accessible via Contentstack
origins." Gate 4 reads "Please enable the Preview Service for a seamless live preview experience."

## Timeline

Timeline runs its own check with three gates, not the five above. Do not map one onto the other.

| # | Card | On failure | Meaning |
|---|---|---|---|
| 1 | Default Environment | Set default environment | No default environment configured |
| 2 | Live Preview SDK | Use updated SDK | SDK version below the supported minimum |
| 3 | Preview Token | Use preview token | Requests are not using the Preview Service |

**Timeline's check has a fixed delay before it declares failure.** A site slower than that window
produces a failure card even though the setup is correct. If a Timeline user reports a failing gate
on a site you know is slow, have them re-open the panel on a warm cache before believing the card.

## What the check does not cover

This is where the check earns its keep as a diagnostic, and where people over-trust it. "Setup
Complete" and a broken experience is a real and informative combination.

The check verifies reachability, the SDK handshake, SDK version, and that the Preview Service is in
use. It does not look at any of the following:

- **Edit tags.** Nothing in the chain inspects `data-cslp`. If the card says Setup Complete and
  nothing on the canvas is editable, the answer is edit-tag generation, every time. This is the
  single most useful inference the check supports.
- **Preview URL resolution.** The site loading is not the same as the correct entry loading. A card
  reading Setup Complete on the wrong page is a routing problem.
- **Locale, variants, and Timeline timestamps.**
- **Caching.** Any cache on the preview path can serve published content while every gate passes.
- **Roles.** The check runs as the signed-in user but does not report permission gaps, which is why
  a role problem looks like "works for everyone except one person" rather than a failed gate.

## When the card does not appear at all

Absence is not a pass. Before treating a missing card as "the check succeeded", rule out:

- No default environment is set and none is remembered locally for that locale, in which case the
  overlay is deliberately not shown.
- The user, or someone on their team, dismissed it. The preference persists per stack.
- The stack setting suppresses it.

**Do not reason about the default.** Each product keeps its own stack setting, and they disagree on
what an unset value means:

| Product | Setting | Unset resolves to |
|---|---|---|
| Timeline | `timeline.onboarding-setup-visible` | visible |
| Live Preview | `live_preview.lp-onboarding-setup-visible` | hidden |
| Visual Editor | `visual_builder.onboarding-setup-visible` | depends on whether the settings object exists |

The Visual Experience settings screen renders every one of these as **on** when unset, so a stack
that never explicitly saved the setting can show the toggle on while the card never appears.

The fix is one action: open Settings → Visual Experience and Save, without changing anything. That
form submits all three products' keys together and an unset value arrives as on, so one save writes
an explicit value for all three and they stop disagreeing.

If it then appears for colleagues but not for the reporter, they dismissed it. That suppression
lives per stack in their own browser storage and no stack-level save clears it.

If the user cannot produce the card, fall back to the four contracts in SKILL.md and verify them by
hand.

## How to ask for it

Ask for the screenshot rather than the wording. Users paraphrase the step name into a different
one, and since each name maps to a specific gate, a paraphrase can send you down the wrong branch.

If they cannot screenshot it, ask for the exact step name and body text as displayed, and confirm
which product they are in, because Live Preview and Timeline share a visual style but not a set of
gates.
