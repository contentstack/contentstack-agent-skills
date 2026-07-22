---
name: choose-connected-vs-freeform
description: "Decide whether a new page is a Connected (content-type-bound) or Freeform (one-off) template. **Connected is the default; Freeform is the very last resort.** Hands off to the matching build skill."
allowed-tools: Read Grep Glob
---

## When to use

Decide whether a new page is a Connected (content-type-bound) or Freeform (one-off) template. **Connected is the default; Freeform is the very last resort.** Hands off to the matching build skill.

Use at the start of authoring a new page, before any template is created. Phrases — "Connected or Freeform?", "what kind of template", "should this be a landing page". Emits a recommendation (Connected default; Freeform only when justified by the Three-AND rule) and the next skill to run. Do NOT use to actually build the template.

# Choose Connected vs Freeform Template

## Context

Studio offers two kinds of top-level compositions: **Connected templates** (bound 1:1 to a content type, so every entry of that CT renders through the same template at a derived URL) and **Freeform templates** (one-off pages assembled from any mix of sources — Pinned Queries, Additional Entry Data, Component Default Data — with no content-type binding).

**Default is Connected.** Connected scales with content (one template renders unlimited entries), auto-binds `template.*` against the connected entry, supports `{{entry.*}}` URL variables, gives authors a content-first workflow (edit the entry → page updates), and benefits from CT-level governance (validation, locales, variants, publishing workflows). **Most pages should be Connected**, including pages that only ever have one instance — model a single-entry content type rather than reaching for Freeform.

**Freeform is the very very very last resort.** Use it ONLY when **ALL THREE** are true:

1. **Short-lived** — the page has an expected end date (campaign, splash, takeover, time-boxed promo). Not a "one-off that lives forever."
2. **Owns ZERO content of its own** — no hero copy, no page-specific title, no subheading, no CTA text, no callouts, no closing message. **Literally no copy authored on the page.** Hero copy IS content; throwaway HTML is owned content in disguise. If you find yourself writing copy in JSX, you have a content field — model it as a single-entry CT → Connected.
3. **Visible content is 100% assembled by pinning / pulling from existing entries** — pinned entries from existing CTs, pinned queries, references into existing collections. The page is a *vitrine*, not a *source*.

If any one of those three is missing → **not Freeform.** Use Connected with the right CT shape (single-entry CT for one-off long-lived pages, multi-entry CT for repeating shapes including recurring campaigns, single-entry CT even for short-lived pages that own any copy).

Examples that do NOT qualify for Freeform (despite tempting at first glance):
- **"Black Friday 2026 landing"** — even if short-lived and references existing product entries, it has its own campaign hero copy, headlines, CTA text. Owned content → single-entry CT or generic `campaign` CT → Connected.
- **"Conference splash"** — has its own conference hero, dates copy, sponsor framing. Owned content → Connected.
- **"Marketing landing page"** — almost always has page-specific copy. Owned content → Connected.
- **Homepage / About / Contact / Pricing** — long-lived AND own their content → single-entry CT → Connected.

Genuine Freeform cases are rare and usually internal-tool-ish: a merchandiser dashboard pinning 12 products in a specific order, a monitoring vitrine of pinned analytics entries, an A/B test variant that's purely "pinned query, no other content, deleted next week" — pure assembly of existing entries with no surrounding copy.

## Task

1. Ask the user for `pageDescription`, `numberOfPagesOfThisShape`, and `hasContentTypeMatch` if not already provided.
2. Check for a URL-pattern hard constraint. If the user mentions a URL that needs entry-field variables (e.g. `/blog/{{entry.slug}}`, `/products/{{entry.handle}}`), force **Connected** — Freeform URL patterns only support `{{composition_uid}}` plus `{{environment}}` / `{{branch}}`; they cannot resolve `{{entry.*}}` or `{{content_type_uid}}`. (`{{locale}}` is accepted by the pattern engine but not recommended for either flavor — locale belongs in your routing layer + the SDK `locale` query option.)
3. Otherwise apply the decision tree in order. **Bias toward Connected at every branch**; only return Freeform after explicitly confirming ALL THREE Freeform conditions (Step 4 below).
   - (a) `numberOfPagesOfThisShape = many-with-CT-backing` (many pages, each maps to one entry of a single CT) → **Connected**. Canonical examples: blog posts, products, recipes, author profiles.
   - (b) `numberOfPagesOfThisShape = one` AND `hasContentTypeMatch = yes` (one-off page that maps cleanly to one entry of a CT) → **Connected** with a hard-coded URL. Cheaper than Freeform because Connected auto-binds template fields against the connected entry.
   - (c) `numberOfPagesOfThisShape = many` AND `hasContentTypeMatch = no` or `partial` → **propose Connected via a new or extended CT**. Ask: can a content type be created (or an existing one extended) to back these pages? If yes (which is usually the case), model the CT first → Connected.
   - (d) `numberOfPagesOfThisShape = one` AND `hasContentTypeMatch = no` → ask: does the page own any copy of its own (hero title, subheading, CTA, callouts)? If YES → **Connected** with a single-entry CT (typical for homepages, about, contact, pricing, campaign landing pages — they all own their copy). The page-specific copy IS content; model it. If NO (the page owns literally zero copy and purely assembles existing entries) → continue to Step 4 (Freeform candidate).

4. **Freeform last-resort check.** If — and only if — branch (d) led here with the user confirming the page owns no copy, run the three-AND rule. Re-confirm by asking explicitly:
   - (i) Does this page have an **expected end date**? (Campaign, splash, takeover — not "one-off that lives forever.")
   - (ii) Does the page own **ZERO content of its own**? No hero copy, no page-specific title, no subheading, no CTA text, no callouts, no closing message — literally nothing the page itself authors. (Hero copy IS content. Throwaway HTML IS content in disguise.)
   - (iii) Is the visible content **100% assembled from existing entries** — pinned entries, pinned queries, references into existing CTs?

   If the user confirms all three → **Freeform**. If even one answer wavers or is "yes, but a hero title" → flip back to **Connected** with a single-entry CT (or a `campaign` CT for recurring campaign shapes). Hero copy / page-specific copy means owned content; owned content means Connected.
4. Print the recommendation in this exact shape:
   ```
   Recommendation: <Connected | Freeform> template
   Rationale: <one sentence tying back to the inputs>
   Next skill: <build-connected-template | build-freeform-template>
   ```
5. If the recommendation is Freeform, append TWO reminder lines:
   - `Reconsider: did you rule out Connected via a single-entry CT or an extended CT? Freeform is the exception, not the default — re-check before proceeding.`
   - `Before running build-freeform-template, verify the project-level "Enable Freeform Feature" toggle is on (Studio → Settings → Configuration). Many teams keep it OFF deliberately to enforce the every-page-maps-to-a-CT discipline; if your project has it off, the right move is usually to leave it off and model a CT.`
6. Stop. Do not create the template yourself; the user (or the next skill invocation) runs the chosen build skill.

## Inputs needed from the user

- **pageDescription** — one sentence, free text. Used only for the rationale line.
- **numberOfPagesOfThisShape** — one of `one`, `many`, `many-with-CT-backing`.
- **hasContentTypeMatch** — one of `yes`, `no`, `partial`.

If the user volunteers a URL pattern in `pageDescription`, parse it for `{{entry.*}}` or `{{content_type_uid}}` and apply the hard constraint from step 2 before the decision tree.

## Acceptance

- Exactly one recommendation is printed (Connected OR Freeform — never both, never "it depends").
- The rationale references the user's actual inputs, not generic copy.
- The `Next skill` line names a real, runnable skill in the docs (`build-connected-template` or `build-freeform-template`).
- If the URL needs `{{entry.*}}`, the output is Connected and the rationale explicitly cites the Freeform URL-variable limitation.
- If the output is Freeform, the Enable Freeform Feature reminder is present.
- No template is created in Studio by this skill.

## Common pitfalls

| Pitfall | Why it bites | Right move |
|---|---|---|
| Recommending Freeform for "many blog posts" because the user said the word "landing" once | Freeform is 1:1 — each blog post would need its own template, exploding maintenance | If `many-with-CT-backing`, always Connected, regardless of stylistic words |
| Recommending Freeform when the URL contains `{{entry.slug}}` | Freeform URL patterns only resolve `{{composition_uid}}`, `{{environment}}`, `{{branch}}` — `{{entry.*}}` and `{{content_type_uid}}` will not interpolate | Force Connected the moment an entry-field variable appears |
| Treating "partial CT match" as automatic Freeform | A partial match often means the CT just needs one extra field; Connected is still right if the page shape repeats | Ask whether the CT can be extended before falling back to Freeform |
| Recommending Freeform without checking the project toggle | `Enable Freeform Feature` may be off at the project level; `build-freeform-template` will not see the option in the create-template modal | Always print the toggle reminder when the answer is Freeform |
| Choosing Freeform for a one-off page that maps to one entry | You lose Connected's auto-resolution of `template.*` bindings and have to wire Link Entry / Pinned Queries by hand | One-off + clean CT match → Connected with a hard-coded URL |
| Reaching for Freeform on a one-off page because "there's no obvious CT" | A single-entry CT (one CT, one entry) is almost always cheaper than Freeform for the homepage, about page, contact page, etc. Connected gives you auto-binding, locales, variants, and a content-first edit flow that Freeform doesn't | If the page has even one stable content shape, model it as a single-entry CT and go Connected |
| Treating Freeform as the default for "marketing / campaign" pages | The label "marketing page" doesn't decide the question — the data shape does. A "campaign" page that always has hero + promos + CTA can be a single-entry CT (Connected) | Ask what the *data* on the page looks like, not what the page is called. Connected wins whenever the shape repeats or stabilizes |
| Confusing Repeater iteration bindings with template bindings during the conversation | Inside a Repeater, fields bind as `repeater.<field>` (RepeaterBindingValue, discriminated by `repeaterUID`); at the template level they bind as `template.<field>` (TemplateBindingValue). This skill doesn't bind — it just chooses — but if the user asks "can I bind X?", route them to the matching build skill instead of guessing | Defer all binding shape questions to `build-connected-template` / `build-freeform-template` |
| Forgetting that references inside a Repeater always need a Condition Block | True for both single-CT and multi-CT reference fields — relevant when the user asks whether their repeater-of-refs page is feasible | Confirm feasibility, then hand off; the build skill handles the Condition Block step |
