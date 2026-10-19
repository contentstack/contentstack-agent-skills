---
title: Authoring conventions
description: "Conventions for writing Contentstack skills: structure, frontmatter, security, references, and examples."
---

# Authoring conventions

These conventions keep skills consistent, parseable by agents, and safe. Follow them when writing or editing any `skills/<slug>/SKILL.md`.

## Structure

Follow the section outline described in [Anatomy of a SKILL.md](../how-it-works/skill-anatomy.md): Description, When to Use, User Problem, Success Criteria, Expected Inputs/Outputs, Example User Requests, Workflow Summary, Instructions, Output Format, Tooling Notes, Security, Product Context, References, Examples.

Not every skill needs every section, but keep the order consistent so agents (and readers of the docs) find things in predictable places.

## Frontmatter

- `name` and `description` are required. `name` must equal the folder name (lowercase letters, digits, single hyphens, max 64 characters).
- The `description` says what the skill does and includes a "Use when…" sentence, max 1024 characters. It's the only text agents see before loading the skill, so it does the routing. See below.
- Set `allowed-tools` to the minimum needed. Advisory skills are almost always `Read Grep Glob` (read-only).
- Use `argument-hint` for action skills that take parameters.
- Use `disable-model-invocation: true` for skills that should run only when explicitly invoked (e.g. the Launch action skills).

## Write the description as the trigger

Agents choose a skill by matching your request against its description (see [How skill selection works](../how-it-works/router.md)). Make the "Use when…" clause list the concrete requests, tools, and terms a user would mention: "Delivery SDK", "Live Preview", "pagination", not "helps with content". Keep the **When to Use** section in the body consistent with it, and avoid overlap with neighboring skills' descriptions.

## Security is mandatory

Every skill must include a Security section covering the four pillars:

1. **Defaults**: standing safety rules.
2. **Destructive Actions**: advisory skills refuse mutations; action skills gate them behind confirmation.
3. **Secrets**. Never print, echo, infer, or store secrets; use placeholders.
4. **Environment Variables**: credentials via env vars with descriptive placeholder names.

Inherit the product's shared safety rules (see [Security & safety model](../how-it-works/security-model.md)) and add skill-specific ones.

## Default to read-only

Unless a skill genuinely needs to perform an external action, make it advisory and read-only. If it does perform actions, gate every destructive or production-facing step behind explicit confirmation, and prefer dry-run defaults.

## References, not assumptions

When a skill depends on precise API details, ship a `references/` file and instruct the agent to read it on demand. Don't bake volatile details into the body: point to the reference and mark anything that should be verified against live docs.

## Examples calibrate behavior

Include worked **User → Assistant** pairs, especially for:

- The core happy-path patterns.
- Edge cases and refusals (e.g. how to decline hardcoding a token, how to gate a delete).

Tag them (`few shot`, `edge case`) consistently with the rest of the bundle.

## Keep it concise and practical

Skills favor direct, actionable guidance over background theory. Lead with the recommendation; explain tradeoffs only when they change the decision.

## Validate before you push

Run `node scripts/validate.mjs`. It checks skill names, descriptions (including "Use when"), the `## Security` section and its four subsections, relative links under `skills/`, quoted frontmatter values in `skills/` and `docs/`, and that manifests parse with matching versions. CI runs it on pull requests to any branch, on pushes to `main` and `next`, and manually. See [Add or edit a skill](add-or-edit-a-skill.md) for the full list.
