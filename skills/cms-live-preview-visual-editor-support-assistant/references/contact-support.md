# When to contact Contentstack Support

Symptoms whose cause sits outside the user's application. Recognising one of these early is worth
more than any fix, because the alternative is a long debugging session in code that was never the
problem.

For each, the job is to confirm the identifying evidence, say plainly that this is not something
they can fix in their own code, give the workaround if one exists, and tell them to open a ticket
with Contentstack Support.

## Provisioning and configuration, needs a support action

| Symptom | What it actually is |
|---|---|
| The Visual Experience or builder-mode option is absent from navigation | The plan or org flag was never enabled for that stack. |
| Custom Preview URLs or Open in New Tab are unavailable | Both are plan-gated. |

## Not Contentstack at all

| Symptom | What it actually is |
|---|---|
| A previously working `localhost` preview stops working, console shows a local network access error | Chrome's Local Network Access policy now blocks the app origin from framing localhost. Only the user can grant the permission, in the browser. |
| Preview pane blank, and the site sits behind platform password protection or third-party SSO | Those screens set `X-Frame-Options: DENY` on themselves. Contentstack cannot inject headers into a browser-originated iframe request. Workarounds, cheapest first: enable **Open in New Tab**, which renders the site outside the iframe so frame headers stop applying; otherwise disable protection on the preview deployment, put a bypass token in the Base URL, or front it with a server-side proxy that strips the header. |
| Ad slots, consent widgets, or other host-dependent third-party scripts misbehave in the pane | Those scripts key off the top-level origin, which is the Contentstack app inside an iframe. Expected, not a preview defect. |

## How to hand it over

State which category it falls into, quote the evidence that identifies it, and give the workaround
if there is one. Then tell the user to raise it with Contentstack Support — as a next step for them,
not as something happening behind the scenes. Nothing is routed anywhere on their behalf.


### Produce a handover note

Write the note below for the user to paste into the ticket. Fill it from what the protocol already
collected in steps 1–6; do not start a new round of questions to complete it. Leave a field as
"not checked" rather than guessing — an honest gap is more useful to the engineer than a filled-in
assumption. Keep it to the fields; a Support or Product Engineer wants the facts, not the narrative.

| Field | Value |
|---|---|
| Product | Live Preview / Visual Editor / Timeline |
| Stack API key | `<api_key>` |
| Environment / locale | `<environment>` / `<locale>` |
| Branch or alias | only if not `main` |
| Onboarding Check | exact card text shown, or "Setup Complete", or "card does not appear" |
| Framework | name and major version; App Router or Pages Router where relevant |
| Rendering mode | CSR / SSR / SSG / ISR / edge — for the affected route |
| Fetch layer | Delivery SDK / REST / GraphQL / BFF, middleware or proxy |
| SDK versions | `live-preview-utils x.y.z`, `delivery-sdk x.y.z` |
| Scope | one user or everyone; localhost, deployed or both; consistent or intermittent |
| Started after | new setup (never worked) / release / dependency bump / settings change / role change / nothing known |
| Failing request | `METHOD host/path → status` — URL redacted, no tokens |
| Console or server log | one-line excerpt, redacted |
| Ruled out | contracts verified and how, e.g. "tracker POST 200; `data-cslp` present; requests hit the preview host" |
| Suspected category | provisioning / plan gating / browser policy / other |
| Workaround applied | what, or "none" |

**Redact before sending.** Never include delivery tokens, preview tokens, management tokens, live
preview hashes, cookies, or auth headers. The stack API key and environment name are fine and are
what Support needs to find the stack.
