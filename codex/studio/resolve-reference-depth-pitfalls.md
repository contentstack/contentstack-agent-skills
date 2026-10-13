---
name: resolve-reference-depth-pitfalls
---

## When to use

Diagnostics for reference resolution: `error_code 141` and what it always means, plus the pitfall table for walking depth. Read when a fetch fails or a stub will not resolve.

Part of the reference-depth set. Start at [`resolve-reference-depth`](resolve-reference-depth.md).

## `error_code 141`: always the same cause, never "go deeper"

`141` means the request asked for more reference paths than it is allowed to carry.

**It is a request-size limit, not a path count. Do not plan around "100 paths".** Measured on one stack, the same entry accepted **27** declared paths and returned `141` at **28**, with the request URL at ~2.5KB. Paths on that entry ranged from 23 to 372 characters, so the count at which it breaks moves with how long your paths are: a few deeply-nested paths exhaust it as fast as many shallow ones. Past that, an even longer request stops returning `141` and starts returning **`414`**, a transport failure with an empty body, which is easy to misread as "resolved nothing".

**Always check `r.ok` before reading a response.** A `414` and a genuinely empty result look identical if you only count stubs.

The fix is the same in every case: **ask for fewer paths.**

- **Split**: run two or more fetches, each carrying part of the path set, and merge.
- **Narrow**: declare only the chains the binding actually needs, not the schema's full closure.
- **Re-root**: fetch the deepest resolved entry as a new root so the request carries only the sub-chain. Unbounded, so it needs the user (Step 3).

What is never the fix is raising a depth number. A `141` does not become a success one level deeper.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Treating `[]` as "not deep enough" | No depth fills genuinely empty content. The user approves passes that cannot succeed | Classify per Step 0 first. Report absent content as absent |
| Tuning `include_all_depth` to fix a page | The bound-entry fetch carries `include[]` and `only[]` and no depth parameter, the number being raised is not in that request | Use depth to diagnose. Fix by declaring the path, which becomes `include[]` |
| Trusting `include_all_depth` to resolve anything | Measured inert on a real stack: identical bytes at 1 to 6 and 10, no error, and no effect on top of declared paths | Declare a path per hop. Re-measure before relying on the parameter |
| Answering a `141` by raising the depth | `141` means too many reference paths. One more level asks for strictly more | Narrow the declared set, or ask which paths actually matter |
| Reading a falling stub count as progress | Resolving one level exposes the stubs one hop further out, and `_metadata` objects inflate the count, measured 17 of 28 | Exclude `_metadata`. Track the paths the binding needs, by name |
| Deepening the fetch but not declaring the path | The entry is fetched and the field still renders blank, so the fix looks like it failed | Advance both mechanisms in the same pass |
| Prompting per stub, or per section | Spends the user's attention on decisions the schema already answers | Declare every derivable hop, then ask once, for everything still stuck |
| Raising depth because the value is deeply nested in groups or blocks | Same-entry nesting costs no depth. The number climbs until `141` while the real fault is an undeclared or mis-terminated path | Count reference hops from the schema. Fix the path, not the depth |
| Reading an unpublished target as "not deep enough" | An unresolvable stub and a too-shallow stub are byte-identical. Digging and re-rooting both fail forever | Probe the stub's uid directly. No entry returned means publish state, not depth |
| Declaring hops past a stub instead of the stub's own path | The stub is resolved by its own path. Declaring the target CT's fields leaves it untouched and the pass looks like a no-op | Declare `P` first, then anything beyond `P` |
| Reading an empty `entries` array as a resolved page | Zero stubs and zero bytes look identical to full success | Confirm an entry came back before counting anything |
| Reading a `414` as "nothing to resolve" | The response has no body, so stub and byte counts are both zero, indistinguishable from success unless `r.ok` is checked | Check `r.ok` first. On `414` split the path set and retry |
| Declaring the schema's full closure | Expansion overruns the request long before the schema runs out, measured 153 candidate paths against a 27-path ceiling | Expand toward paths that carry a real stub. Split when the budget bites |
| Expanding only the CT this entry happens to hold | A multi-target reference holds a different CT per entry, so the next hop is under-declared for every other entry | Union the next hop over every `reference_to` candidate |
| Asking the user about a stub that is merely unpublished | The survivor of every derivable path looks like a missing path, but probes `422` with `publish_details: (NONE)`. Measured, the only stub reaching Step 3 was this | Re-run the stub probe before prompting. Report `422` as absent content |
| Guessing a path, or re-rooting, instead of asking | A guessed path silently declares nothing, and a re-root has no natural end, both look like progress and produce a blank field | At an underivable path, stop and ask for path / entry / depth (Step 3) |
| Digging silently in automation | The job passes, the page is blank, and nothing recorded which path was missing | Declare derivable hops, then stop and report in the Step 3 format |
