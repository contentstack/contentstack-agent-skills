---
title: Install for Codex / OpenAI agents
description: Use Contentstack Agent Skills with Codex or other OpenAI-style agents via the generated codex tree.
---

# Install for Codex / OpenAI agents

Codex and similar OpenAI-style agents use the generated **`codex/` markdown tree**. The entry point is `codex/AGENTS.md` (the router); each skill is a plain markdown file with frontmatter stripped.

## Install

Point your agent at the repository, **or** copy the `codex/` directory into your project:

Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

```
git clone https://github.com/contentstack/contentstack-agent-skills.git
cp -R contentstack-agent-skills/codex your-project/
```

Make sure your agent reads `codex/AGENTS.md` as its context/instructions entry point.

## What gets installed

- `codex/AGENTS.md`: the router, copied from `skills/CLAUDE.md` with link paths rewritten for the codex tree.
- `codex/<slug>/SKILL.md`: one markdown file per skill (body only, no YAML frontmatter).
- `codex/<slug>/references/` and `codex/<slug>/scripts/`: bundled assets, mirrored from the source skill.

The `codex/` tree is **generated** from `skills/` by `scripts/build-codex-skills.sh`. Don't edit it by hand. See [Architecture](../how-it-works/architecture.md).

## Verify

Ask your agent:

> Which Contentstack skills do you have available?

It should answer from the routing table in `codex/AGENTS.md`. See [Verify your setup](verify-setup.md).

## Use it

Ask Contentstack questions in natural language. The agent reads `AGENTS.md`, matches your request to a skill, then follows that skill's `SKILL.md`:

> Review this content model and tell me what to simplify.

routes to **Data Modeling Best Practices**.

## Update

Re-copy the `codex/` directory (or re-sync the repo) to get the latest version.

## Troubleshooting

- **The agent ignores the skills** → confirm it actually loads `codex/AGENTS.md` as instructions, and that the relative links to `codex/<slug>/SKILL.md` resolve from wherever you copied the tree.
- **A bundled script can't be found** → scripts self-locate relative to their own directory; invoke them by absolute path inside `codex/<slug>/scripts/`.
