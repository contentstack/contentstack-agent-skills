---
title: Routing evals
description: "How the evals/ suite checks that each prompt loads the right skill, and how to run and extend it."
---

# Routing evals

A skill only helps if the agent loads it. With more than 30 skills, descriptions compete with each other, and a vague one quietly sends questions to the wrong skill. The `evals/` folder holds prompts that must load a given skill, run with `claude plugin eval` (Claude Code 2.1 or later).

## How a case works

Each case is a folder named `routing-<skill>-<n>`:

```
evals/routing-cms-assets-1/
├── prompt.md                      # the user's question
└── graders/
    ├── loads-cms-assets.md        # passes when the agent calls Skill with cms-assets
    └── skips-asset-management.md  # passes when it doesn't load the neighbour
```

`prompt.md` has the case `name`, `tags: [routing, <skill>]`, and low `max_turns` and `timeout_seconds`, because the routing decision happens on the first turn. The graders are `tool_used` checks on the `Skill` tool. A `skips-` grader (`min: 0`, `max: 0`) guards against a neighbouring skill that covers similar ground, such as `cms-assets` and `asset-management`, or `personalize` and `cms-variants-personalization`.

Every skill that agents can pick automatically has at least two cases. The two Launch action skills have none, because `disable-model-invocation: true` means they only run when invoked by name.

## Run them

```bash
# One skill
claude plugin eval . --ablation none --case 'routing-cms-taxonomy-*' --runs 1 --trust-plugin --no-publish

# Everything, three runs per case
claude plugin eval . --tag routing --ablation none --runs 3 -j 6 --trust-plugin --no-publish
```

- `--ablation none` is required. The default also runs a baseline without the plugin, which doubles the cost, and it doesn't score `Skill` graders.
- Each run is a real Claude session and costs roughly $0.10–0.15, so the full suite is a few dollars per run per case.
- Results go to `evals/results/` (gitignored), with an HTML report.

In CI, `.github/workflows/routing-evals.yml` runs every case once on pull requests that change `skills/` or `evals/`, and three times when started by hand. It needs an `ANTHROPIC_API_KEY` repository secret and skips itself without one.

## When a case fails

A failing case usually means a description lost a routing cue or a neighbour's description grew to cover the same request. Fix the descriptions, not the prompt:

- Put the terms users actually say in the `description`.
- Add a "For X, use Y." cue to the skill that wins wrongly.
- Rerun just that skill's cases with `--case`.

## Add cases

When you add a skill, add at least two `routing-<skill>-<n>` folders: one plain request, and one phrased close to a neighbouring skill with a `skips-<neighbour>` grader. Write prompts the way users ask, not in the description's words.
