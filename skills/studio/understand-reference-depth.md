---
name: understand-reference-depth
---

## When to use

What reference depth actually counts, and the two signals that say it is finished. Read when you are unsure how deep to fetch, or why adding depth stopped helping. Depth counts reference hops; Groups and blocks are free, and stub count is not a progress bar.

Resolving it in practice is [`resolve-reference-depth`](resolve-reference-depth.md).

## The ladder

**`include_all_depth` cannot be trusted to do anything: measure it, never assume it.** On one stack measured, an entry on a five-hop chain returned byte-identical payloads at 1, 2, 3, 4, 5, 6 and 10: same bytes, same stubs, no error at any value, and no effect layered on top of declared paths. It may behave differently on the stack in front of you. **So probe it once (Step 2b) rather than either trusting it or writing it off.**

**What actually resolves a hop is a declared path, and every hop needs its own.** Same entry, same environment:

| Declared | Real stubs left | Bytes |
|---|---|---|
| nothing | 11 | 9,699 |
| hop 1 | 12 | 62,052 |
| hop 1 + hop 2 (`….author`) | 11 | 63,955 |
| hop 1 + hop 2 + `….category` | 10 | 64,405 |

One declared path buys exactly one hop. Nothing cascades.

So the ladder is not a depth counter. It is: **derive the path, declare it, and when the path cannot be derived, ask.**

| Pass | What you do | If data still missing |
|---|---|---|
| 1 | Declare every hop you can derive **from the schema**, then fetch once | **Continue automatically**: deriving costs one schema read |
| 2 | For each remaining stub, resolve its target CT and declare the next hop | **Continue** while each next hop is derivable, there is no depth number to stop at |
| 3 | A stub whose path you cannot derive: ambiguous multi-CT reference, a target you cannot see, or a chain that leaves this stack | **Ask the user.** Never guess, never re-root on your own |

**Ask only where the next step is unbounded or hard to undo.** Passes 1 and 2 are neither: the schema states the path, so deriving it is bounded work with one right answer, and stopping to ask spends the user's attention on something you can look up. Pass 3 is different. There is no schema answer left, so a guess is a guess. That is where the checkpoint belongs.

**Do not escalate depth as a substitute for asking.** Raising a number that the measurement above shows is inert, then reporting "resolved", is the exact failure this skill exists to prevent.

### Two signals that depth is finished

**A plateau.** When a pass returns exactly what the previous one did, the remaining stubs are not reachable by depth from this root. Measured: an entry held the same three unresolved paths at depths 2, 3 and 4 without moving.

A plateau has two causes and they need opposite responses: the chain continues past what the schema can derive (a Step 3 question), or the targets are not published in this environment (absent content, nothing to ask about). **Run the stub probe from Step 0 to tell them apart before prompting anyone.** In every measured case it was the second, and a prompt would have been the wrong move.

**`141`.** Same conclusion, reached by error rather than by plateau.

### Depth counts reference hops. Groups and blocks are free.

Nesting inside the same entry (groups, group-multiples, modular blocks, blocks within blocks) costs **no depth at all**. Only a hop into another entry does. This is the single most common reason a chain is diagnosed wrongly.

Measured on a real page entry. This path is nine segments and crosses two modular-block levels, two block uids and a group:

```
page_blocks . slider_block . cards . card_with_image . card . detail_blocks . info_card . partner_group . partner
    ↑MB          ↑block       ↑MB       ↑block        ↑REF      ↑MB           ↑block      ↑group       ↑REF
```

It contains exactly **two reference hops**, and it resolved completely at `include_all_depth: 2`, stub at 1, resolved at 2, unchanged at 3. Nine segments, depth two.

**So a value buried four groups deep inside an entry inside an entry is depth 2, not depth 6.** If it renders blank, no amount of extra depth will fix it, and raising the number only spends the path budget until it returns `141`.

The blank field in that situation is almost always the declared path instead: every group and block segment must appear in it, the block uid included, with reference-target CT uids dropped. Those four shapes and their exact terminations are canonical in [`author-composition-via-api`](author-composition-repeater-recipes.md#reference-path-termination): the path rules live there, the depth ladder lives here, and the two failures look identical from the outside.

**Count hops from the schema, not from the dots.** Walk the content type: each segment whose field is `data_type: "reference"` is one hop. Group, blocks and block-uid segments are zero. The hop count is the depth you need. The full segment list is the path you must declare.

### Stub count is not a progress bar

The number of unresolved references can **rise** while you are succeeding, because resolving one level exposes the stubs at the next. Measured on two entries: 39, then 34, then **45** across three passes, while resolved references went 72, then 111, then 140. And 11 rose to **12** on declaring a single hop that added 52KB of content.

So never report progress as "stubs went down", and never stop because they went up. Track the specific paths the binding actually needs, and report those by name.
