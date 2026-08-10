---
title: Install for Cursor
description: Install Contentstack Agent Skills in Cursor via the plugin marketplace or by copying rule files.
---

# Install for Cursor

Cursor uses **rule files**. The bundle ships a generated `cursor/rules/` tree: one always-on router rule plus one rule per skill.

## Option A: Plugin marketplace

Install Contentstack Agent Skills from Cursor's plugin marketplace. This wires up the rules for you.

## Option B: Copy the rule files

Copy the rule files into your project:

```
git clone https://github.com/contentstack/contentstack-agent-skills.git
cp contentstack-agent-skills/cursor/rules/*.mdc your-project/.cursor/rules/
```

This is the best option when you want the skills committed to a specific repository so every contributor gets them.

## What gets installed

- `cursor/rules/00-router.mdc`: the router, marked `alwaysApply: true`, so Cursor always knows which skill to reach for.
- `cursor/rules/NN-<slug>.mdc`: one rule per skill (for example `05-cms-entries.mdc`, `17-dx-delivery-sdk.mdc`).

These files are **generated** from `skills/`. Don't edit them by hand. See [Architecture](../how-it-works/architecture.md).

## Verify

Open the Cursor chat and ask:

> Which Contentstack skills do you have available?

The `00-router.mdc` rule is always applied, so Cursor should answer from the routing table. See [Verify your setup](verify-setup.md) for more.

## Use it

Ask Contentstack questions normally:

> How do I set up Contentstack Live Preview for SSR in Next.js?

Cursor consults the router and applies the matching skill (here, **Live Preview & Visual Builder Support**).

## Update

If you installed via the marketplace, update through it. If you copied the files, re-copy `cursor/rules/*.mdc` from the latest bundle.

## Troubleshooting

- **Rules don't seem to apply** → confirm the `.mdc` files are in `.cursor/rules/` at the project root and that `00-router.mdc` retains its `alwaysApply: true` frontmatter.
- **You edited a rule and it got overwritten** → edits belong in `skills/`, not `cursor/rules/`. The generated tree is rebuilt from source. See [Add or edit a skill](../contributing/add-or-edit-a-skill.md).
