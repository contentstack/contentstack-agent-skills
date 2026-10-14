---
name: resolve-reference-depth
---

## When to use

Resolve a reference chain one hop at a time by declaring each hop's path, and stop at a human checkpoint the moment a path cannot be derived. Covers both mechanisms that must line up (the fetch's `include[]` and Studio's `data_sources.resolvedReferences`), why `include_all_depth` measured as inert, and what to ask for when the schema runs out of answers.

Use when a field behind a reference renders blank and the reference chain is more than one hop: a card that references an author who references an organization, a block whose reference points at an entry that itself references an asset group. Phrases: "reference inside a reference is empty", "nested reference not resolving", "the logo is inside a group inside a reference", "reference inside a modular block inside a group", "the field is buried four groups deep", "how deep can references go", "how many levels of reference does Contentstack support", "include_all_depth", "error_code 141", "include reference paths processing limit", "the data is two references deep". Do NOT use for a single-hop reference (bind it per [`build-section`](build-section.md)), for a reference that resolves to `[]` (that is absent content, not depth, see § Step 0), or to diagnose why one declared path is wrong (that is [`troubleshoot-data-binding`](troubleshoot-data-binding.md) rows on mis-terminated paths).

# Resolve a reference chain hop by hop, then ask

## Context

Three things decide whether a reference arrives, and they are not the same knob:

| Mechanism | Wire parameter | Ceiling |
|---|---|---|
| `data_sources.resolvedReferences` | becomes **`include[]`** on the bound-entry fetch | no depth cap. Every hop's path must be declared and correctly terminated |
| Field projection | **`only[<ref>][]`** | dropped automatically when the request URL would exceed ~15 000 chars |
| `include_all_depth` | one number, resolves everything to that depth | **5** org-wide, and lower per entry in practice |
| `include_reference` | explicit paths on the fetch | **3 levels** for a multi-content-type reference field |

**Which one the runtime actually uses matters more than the ceilings.** The SDK fetches bound page content with `include[]` + `only[]` and **no depth parameter at all**. References arrive because their path was declared, not because a number was raised. `include_all_depth` appears only on the fetch for composition/section entries.

`include_all_depth` was therefore **not** used as this skill's ladder, and when measured it turned out not to work at all (see § The ladder). **The fix is a declared path**, never a bigger number: the number is not in the production request to raise, and on the stack measured it changed nothing anywhere.

A chain fails if either the fetch never retrieved the entry or the composition never declared the path. Both present as the same thing downstream: a blank field.

## Why this matters

Digging deeper is neither free nor always correct. Each declared path multiplies the payload and consumes the per-request reference-path budget, and no amount of depth fixes an entry that is genuinely empty in the environment being served. Left to itself an agent will keep raising a number until the API rejects it (or, worse, until it does not) and report "resolved" when the request merely got wider and the field is still blank.

So when the schema stops answering, the next move is a question, not a retry. **Ask for the path or the entry. Bind exactly what comes back.** The checkpoint is the point of this skill.

## Reference for this skill

| Read this | For |
|---|---|
| [`understand-reference-depth`](understand-reference-depth.md) | What depth counts, and the two signals that it is finished |
| [`resolve-reference-depth-pitfalls`](resolve-reference-depth-pitfalls.md) | `error_code 141`, and what goes wrong walking depth. **Read before reporting done.** |

## Task

### Step 0: Classify before digging. Only the first of these five states is a depth problem

Read the raw value at the deepest point that did resolve:

| What you see | What it means | Response |
|---|---|---|
| `{ "uid": "…" }` and nothing else | Either the fetch never went deep enough, its path was never declared, **or the target entry is not published in this environment**, all three look identical | Run the **stub probe** below before spending a pass |
| **Every** reference in the response is a stub, all at once | The request URL overflowed. `only[]` is dropped first (a `[studio-sdk] Skipping only[] projections` warning). If `include[]` alone still overflows, the fetch 414s and falls back to no includes, so nothing resolves | Not a depth problem. Reduce the request: fewer declared paths, re-root, or split the fetch |
| `{ "uid": "…" }`, and fetching that uid directly returns no entry | The reference points at an entry that is not published (or not accessible) in this environment | **Not** a depth problem. No depth and no re-root will fill it. Report it unpublished; publishing it is the user's call, so never publish it yourself |
| `[]` | The reference field is genuinely empty for this entry in this environment | **Not** a depth problem. No depth will fill it. Say so and stop. Check the entry, the environment, and whether the target is published |
| Field absent entirely | The path was never requested, a declaration gap, not a depth gap | Declare the path (see [`author-composition-via-api`](author-composition-via-api.md) § Where a reference path must terminate), then re-run pass 1 |

**The stub probe.** A stub carries `_content_type_uid` and `uid`, so it costs one cheap request to find out which kind it is:

```
GET /v3/content_types/<stub._content_type_uid>/entries
      ?environment=<env>&query={"uid":"<stub.uid>"}
```

If an entry comes back, the target exists and the stub is a depth or path problem. Continue the ladder. **If nothing comes back, the target is not published in this environment, and no amount of depth will ever resolve it.** Measured: an entry that plateaued at three unresolved paths across depths 2, 3 and 4 turned out to have all three pointing at unpublished targets, depth was never the fault, and each further pass would have cost payload for nothing.

Run the probe on one representative stub per distinct target content type, not per occurrence.

Never open a checkpoint for any row but the first. Offering to dig deeper for absent content sends the user to approve work that cannot succeed.

### Step 1: Derive every path you can, then fetch once

Walk the content type. Each segment whose field is `data_type: "reference"` is a hop. Group, blocks and block-uid segments are free. Declare **every** derivable hop in one request rather than one per pass, each costs a path, not a round trip.

Declare the same paths in the composition's `resolvedReferences`. A fetch that includes a path the composition never declared still renders blank, and the two failures are indistinguishable from outside.

**Use schema paths, not payload paths.** The payload carries array indices (`sections.1.resources.cards.0.reference_card.card_category.0.author.0`) and `include[]` takes the schema shape with the indices dropped: `sections.resources.cards.reference_card.card_category.author`. Copying the path out of the response is the most common way this silently declares nothing.

### Step 2: Walk the remaining stubs outward

For each stub still present, read its `_content_type_uid`, look that CT up, and declare the next hop. Repeat while the next hop is derivable. Stop when the stub set stops shrinking.

**There is no depth limit to stop at: the walk runs until the schema has nothing left to give.** It goes exactly as deep as the data does, which is why it needs no ceiling: measured across three entries it converged in a single round at 2, 2 and 3 hops, each time because nothing further was derivable rather than because a cap was hit. The only thing that can cut it short is the request budget, and that is answered by splitting (Step 2b.3), not by stopping.

**`_metadata` objects are not stubs.** They are uid-only and match every naive stub detector. Measured on one entry: 28 apparent stubs, of which **17 were `_metadata`**, a detector that counts them reports a chain as unresolved forever. Exclude them before deciding anything.

**Stub count is not a progress bar. It can rise while you are succeeding.** Declaring hop 1 above took the count from 11 to 12 while adding 52KB of resolved content, because resolving one hop exposes the stubs one hop further out.

### Step 2b: Exhaust the automated options before you ask

**Asking is the last resort, not the second one.** Three things are still free to try, and all three are bounded. Do them before Step 3.

**0. Declare the stub's own path before anything beyond it.** A stub at payload path `P` is resolved by declaring `P` itself, not by declaring the fields of the content type it points at. Declaring only the hops past a stub leaves the stub exactly as it was, and the pass looks like it accomplished nothing. Measured: on one entry this mistake held the count at 8 stubs and pushed 7 of them to the user as questions. Declaring each stub's own path first took the same entry to 1, and that survivor was unpublished: **0 questions**.

**1. Union over every candidate CT.** A reference field with several `reference_to` targets holds a different content type per entry, so the next hop differs per entry too. Walking only the CT this entry happens to hold under-declares for every other one. Declare the next hop for **every** candidate.

**2. Probe `include_all_depth` once, on this stack.** One A/B fetch, same paths, with and without it. Identical bytes and identical stub count means inert here. Spend nothing more on it. Anything different means it helps on this stack, so keep it. Measure. Never assume either way.

**3. Split the request when the budget bites.** Exhaustive expansion overruns the request long before it runs out of schema: measured, a full schema closure produced **153** candidate paths where the entry accepted **27**. So expand toward the paths that actually carry a stub, and when a set returns `141` or `414`, **split it across two fetches and merge** rather than giving up or asking.

**No entry is not zero stubs.** A fetch that returns `200` with an empty `entries` array reports zero stubs and zero bytes, identical to a fully resolved page. It means the content type has no entry in this environment, which is a Step 0 classification, not a success. Check an entry came back before reading any count.

**A failed request is not an empty result.** A `414` returns no body: zero stubs, zero bytes. Counting stubs alone reports it as total success. Check `r.ok` first. This is the single easiest way to conclude "nothing left to resolve" from a request that never ran.

Only when all three are exhausted, and stubs remain, continue to Step 3.

### Step 3: Re-probe, then ask. Do not guess, do not re-root unasked

When a stub's path cannot be derived, **ask the user**. This is the checkpoint, and it replaces the old "raise the depth / re-root" behavior.

**Re-run the Step 0 stub probe on each survivor first.** A stub that outlived every derivable path is more often unpublished than unreachable, and the two are byte-identical in the response. Fetch the stub's uid directly on the **delivery** API for the target environment:

- **`422`** (or `entry not found`) means the target is **not published in this environment**. That is absent content, not a path. Report it as such, and leave publishing to the user. Asking for an include path cannot fix it, and spends the user's attention on a wrong question.
- **`200`** means genuinely reachable but undeclared. This one is worth asking about.

Measured on one real chain: Steps 1 to 2 took 8 stubs down to 1, and that survivor probed `422` with `publish_details: (NONE)`. Every stub that reached Step 3 in that run was absent content, asking about any of them would have been wrong.

Cross-check on the management API if you need certainty: it ignores publish state, so a `200` there plus a `422` on delivery is conclusive.

Only for the survivors that probe `200`, ask as a numbered choice over **reference fields**. A
binding targets a CT field, never an entry, so the question is which reference field to declare
next. List the reference fields on the stub's CT and let the user pick:

```
Can't resolve this binding. Which reference field do I declare next?

  Prop         : <the prop that is blank>
  Payload path : <blocks>.1.<block>.<list>.0.<ref_field>.0
  Stub CT      : <target_content_type>
  Declared     : <ref_field>  (toggled on, still a stub)

  1. <target_content_type>.<ref_a>   -> <ref_a's target CT>
  2. <target_content_type>.<ref_b>   -> <ref_b's target CT>
  3. None of these — give me the include path, or a depth
  4. Leave this prop unbound          noted, I move on
```

**Every option declares the reference field itself before anything past it**, per 2b.0: picking
`1` declares `<ref_field>.<ref_a>`, the hop and its parent, not `<ref_a>` alone. Show each
field's target CT so the user can spot which holds the value, and mark declared ones so a pick
cannot repeat a pass.

Number choices across the whole report so several props are answered `1, 3, 4` in one line.
Keep option 4 — a prop with no content behind it is a real answer, and the only other exit is
to invent a path.

Then act on the choice and **resume the walk from there**. A picked field is declared with its
parent hop, then Step 2 runs again from the level it opens — a new level often makes the next
hops derivable, and re-asking for what the walk could derive wastes the checkpoint. A supplied
path goes straight into `include[]` and `resolvedReferences`. Speculate past nothing: resume,
and return to the user only if it stubs again.

### Step 4: Non-interactive runs

With no human to ask (CI, a seed pipeline, a scripted provisioner) do not guess and do not dig. Silent digging in automation is how a job passes while the page is still blank.

- declare every **derivable** hop (Steps 1 to 2). That part needs no human
- perform **zero** guesses and **zero** re-roots
- stop at the first stub that would need Step 3, and report it in the Step 3 format so a human can answer it later

A caller may configure more. What automation must never do is treat "no human present" as permission to keep going.

## Acceptance

- [ ] Every unresolved path was classified per Step 0 (including the stub probe) before anything deeper was proposed.
- [ ] Required hops were counted from the schema, not from path segments. Group and block nesting adds none.
- [ ] `include[]` used **schema** paths with array indices stripped, not paths copied out of the payload.
- [ ] `_metadata` objects were excluded before any stub was counted or reported.
- [ ] Every derivable hop was declared without prompting. The first prompt came only at a path that could not be derived.
- [ ] Each stub's own path was declared before any hop beyond it.
- [ ] An empty `entries` array was classified as "no entry in this environment", never counted as zero stubs.
- [ ] Every candidate CT of a multi-target reference was expanded, not only the one this entry held.
- [ ] `include_all_depth` was A/B probed once on this stack rather than assumed inert or assumed working.
- [ ] A `141`/`414` was answered by splitting or narrowing the path set, never by asking the user or by raising a depth.
- [ ] `r.ok` was checked before any response was counted. A `414` was never read as "nothing left to resolve".
- [ ] Each surviving stub was re-probed on the delivery API before any prompt, `422` reported as unpublished/absent, only `200` escalated to the user.
- [ ] That prompt named the field, the payload path, the target CT, the stub uid and what was already tried, and offered path / entry / depth as the three ways to answer.
- [ ] What the user supplied was bound exactly as given: no extra levels, no unrequested re-root.
- [ ] One report covering every unresolved path, not one per section or per stub.
- [ ] A non-interactive run declared derivable hops, then stopped at the first path needing a human, zero guesses, zero re-roots.
- [ ] The fix landed as a declared `resolvedReferences` path (`include[]`), never as a raised depth number.
- [ ] `include_all_depth` was not credited with a fix unless re-measured on that stack. It measured inert on the one tested.
- [ ] The final report names each path as resolved, absent (`[]`), or still unresolved, never "resolved" for a path that merely stopped erroring.

## See also

- [`troubleshoot-data-binding`](troubleshoot-data-binding.md): why one declared path resolves empty (mis-terminated paths, block-uid segments)
- [`author-composition-via-api`](author-composition-via-api.md) § Where a reference path must terminate: the four path shapes and where each one ends
- [`build-section`](build-section.md): binding a single-hop reference
- [`understand-linked-schemas`](understand-linked-schemas.md): how a Section's scope decides which references are addressable at all
