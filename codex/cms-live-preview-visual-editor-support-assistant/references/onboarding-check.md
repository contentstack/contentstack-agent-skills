# The Onboarding Check

Each Visual Experience product runs its own setup check when its panel opens. There are **three**,
with different gates, different minimum SDK versions, and different surfaces. Confirm the product
before reading anything below.

**Ask for a screenshot before anything else.** The first failing item localises the problem to one
gate and proves every earlier gate passed.

## The chain property

All three checks evaluate their gates in order and stop at the first failure. Read the **first**
failing item. Items after it never ran and carry no information.

So "Preview Service Not Enabled" proves the site was reachable, the SDK initialised, and its version
is supported. Do not re-ask about those. The inverse holds too: a check stuck on its first gate says
nothing about the SDK, because the SDK gate never ran.

## Live Preview

One card, showing the gate under test while checking and the first failure when one fails.

| # | Card while checking | Card on failure | What the failure means |
|---|---|---|---|
| 1 | Website Loading | **Could Not Connect to Website** | A `no-cors` `HEAD` request to the preview URL failed at the network level: a wrong or unreachable Base URL, DNS, connection refused, an untrusted certificate (open the URL in its own tab, accept the warning, reload the pane), a non-localhost `http://` host (mixed content), or the browser blocking localhost. Frame headers and auth screens do **not** fail this gate, because a `no-cors` request succeeds on any HTTP response. |
| 2 | Verifying Live Preview SDK | **Live Preview SDK Not Initialized** | No init handshake arrived within about 12 seconds. Either the frame rendered nothing (`X-Frame-Options`, CSP `frame-ancestors`, a password, auth or SSO screen) or the page loaded and `init()` never ran on the client: server-only placement, `enable` not truthy in the deployed build, the init module tree-shaken out, or init running late. |
| 3 | Verifying Live Preview SDK | **Outdated Live Preview SDK Version** | The handshake reported a version below 1.4.0, or an unparseable one. Upgrade Live Preview Utils. |
| 4 | Verifying Preview Service | **Preview Service Not Enabled** | Site and SDK are fine, but content is not coming from the Preview Service. The fetch layer never switched host and headers. The most common failure. |
| 5 | — | **Default Environment Not Set** | Integration fine. The stack has no default preview environment. |
| — | — | **Setup Complete** | All gates passed. |

To tell the two gate-2 causes apart, look at the pane: blank or a browser error page means frame
headers or an auth screen; the site visibly rendered means `init()`.

Body text worth quoting back: gate 1 reads "Ensure the website is live and accessible via Contentstack
origins." Gate 4 reads "Please enable the Preview Service for a seamless live preview experience."

## Visual Editor

Its own check, not Live Preview's. A small status card runs first, its header naming the gate under
test: "Live Preview SDK", "Live Preview SDK Init Mode", "API Key / Preview Token", then "All Set!".
If a gate is still incomplete 18 seconds after the last change, a full-pane **"Set Up Visual Editor"**
overlay replaces it. If the environment gate fails, the overlay appears at once. Ask for the overlay
screenshot.

Overlay items, verbatim:

| # | Overlay item | Passes when |
|---|---|---|
| 1 | Configure the environment | both sub-checks pass |
| 1a | Validate the Default Environment | the `environment` in the preview URL exists on the stack |
| 1b | Validate the Base URL | that environment has a Base URL for the current locale, and its **origin equals the previewed page's origin** |
| 2 | Install the Latest Live Preview SDK | Live Preview Utils major version is 3 or higher |
| 3 | Verify Mode for Live Preview | `init()` was called with `mode: "builder"`. `mode: "preview"` fails here |
| 4 | Validate the Preview Token / API Key | after items 1 to 3 pass and the handshake arrives, a content request reaches the REST or GraphQL Preview Service. Polled 5 times over about 18 seconds |

Two consequences:

- **Visual Editor needs three things.** Working Live Preview, edit tags, and `mode: "builder"`. A setup
  copied from a Live Preview guide has `mode: "preview"` and fails item 3 with everything else green.
- **Item 1b is origin-exact.** `https://www.example.com` against a page on `https://example.com`, or
  `http` against `https`, fails while the frame still renders.

## Timeline

Its own check, three items. A small status card runs first ("Default Environment", "Live Preview
SDK", "Preview Token", then "All Set!", which hides after about two seconds). If an item is still
unchecked ten seconds after the last status change, or one second after when no environment resolves,
a full-pane **"Set Up Timeline"** overlay lists the items under "Get Started", each with a filled or
empty circle.

| # | Overlay item | Passes when | Empty circle means |
|---|---|---|---|
| 1 | Configure the environment | an environment resolves: `environment` on the Timeline URL, else the stack's default preview environment | none on the URL and no default set |
| 2 | Install the latest Live Preview SDK | item 1 passed and the `init()` handshake reached Timeline with major version 2 or higher | `init()` never ran in the frame, or SDK 1.x |
| 3 | Generate and use Preview Token | item 2 passed and a content request reached the Preview Service within about nine seconds | the site fetched from the delivery CDN, or fetched nothing in time |

A slow site can show item 3 empty on a correct setup. Have the user reopen the panel on a warm cache
before believing it.

"Configure" opens the stack's Live Preview settings page. The footer links to the Set Up Timeline
documentation.

## Minimum SDK versions differ

| Product | The check fails below |
|---|---|
| Live Preview | 1.4.0 |
| Timeline | major version 2 |
| Visual Editor | major version 3 |

So an SDK can pass Live Preview's check and fail Visual Editor's.

## What the checks do not cover

"Setup Complete" with a broken experience is a real and informative combination. None of the three
checks looks at:

- **Edit tags.** Nothing inspects `data-cslp`. Setup Complete with nothing editable is edit-tag
  generation, every time.
- **Preview URL resolution.** The site loading is not the right entry loading.
- **Locale, variants and Timeline timestamps.**
- **Caching.** A cache can serve published content while every gate passes.
- **Roles.** The check runs as the signed-in user but reports no permission gaps.

## When the check does not appear

Absence is not a pass. Rule out:

- **Live Preview:** no default environment is set and none is remembered locally for the locale.
- **Visual Editor:** the check already completed for this user and preview URL, or every gate passed.
- **Dismissed.** Each product stores a per-stack dismissal in the user's browser storage. It
  persists until site data is cleared, whatever the dismissal dialog says about "next login".
- **Turned off in stack settings.**

The stack settings disagree on what an unset value means:

| Product | Setting | Unset resolves to |
|---|---|---|
| Live Preview | `live_preview.lp-onboarding-setup-visible` | hidden |
| Timeline | `timeline.onboarding-setup-visible` | visible |
| Visual Editor | `visual_builder.onboarding-setup-visible` | visible if the stack has no `visual_builder` settings at all; **hidden** if it has them without this key |

The settings screen shows every one of these as **on** when unset, so the toggle can read on while
the check never appears. The fix is one action: open Settings → Visual Experience and Save without
changing anything. That writes an explicit value for all three.

If the check then appears for colleagues but not the reporter, the reporter dismissed it. No stack
save clears that; they clear site data for the app origin or use another browser profile.

If the user cannot produce the check, verify the four contracts in SKILL.md by hand.
