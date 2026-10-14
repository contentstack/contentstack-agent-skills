---
title: Anatomy of a SKILL.md
description: The structure every Contentstack skill follows, section by section.
---

# Anatomy of a SKILL.md

Every skill centers on a `SKILL.md` file at `skills/<slug>/SKILL.md`, optionally with `references/`, `scripts/` or, as in `studio`, sibling guide files next to it. Skills share a consistent structure so agents can parse them reliably and authors can write them predictably.

## Frontmatter

YAML at the top of the file configures how the skill is loaded. This follows the [Agent Skills](https://agentskills.io) format, so every supported tool reads it as-is:

```yaml
---
name: dx-delivery-sdk
description: "Help agents write correct, production-ready TypeScript using @contentstack/delivery-sdk…"
allowed-tools: Read Grep Glob
---
```

`name` and `description` are required. Common keys:

| Key | Purpose |
| --- | --- |
| `name` | The skill's identifier. Must equal the folder name: lowercase letters, digits and hyphens, max 64 characters. |
| `description` | What the skill does plus "Use when…" triggers, max 1024 characters. The only text agents see before loading the skill, so it drives selection. |
| `allowed-tools` | Restricts which tools the agent may use (most advisory skills are `Read Grep Glob`: read-only). |
| `argument-hint` | Hints expected arguments for action skills (e.g. `[project_uid] [environment_uid]`). |
| `disable-model-invocation` | Marks a skill that should only run when explicitly invoked, never picked automatically (used by the Launch action skills). |
| `context` / `agent` | Execution hints (e.g. `context: fork`, `agent: general-purpose` or `agent: plan`). |

Every tool installs the file unchanged, frontmatter included. See [How skill selection works](router.md) for how the description is used.

## Body sections

The Markdown body follows a repeatable outline. Not every skill uses every section, but most include:

| Section | What it captures |
| --- | --- |
| **Description** | What the skill does. |
| **When to Use** | The user intents that should activate it, expanding on the description's "Use when…". |
| **User Problem** | The underlying need the skill addresses. |
| **Success Criteria** | What a correct answer looks like. |
| **Expected Inputs** | What the agent should gather (UIDs, locale, framework, etc.). |
| **Expected Outputs** | The deliverables (code, recommendations, checklists). |
| **Example User Requests** | Representative prompts the skill handles. |
| **Workflow Summary** | The step-by-step approach. |
| **Instructions** | The detailed rules and decision logic: the core of the skill. |
| **Output Format** | How answers should be shaped. |
| **Tooling Notes** | Which tools/SDKs to prefer; read-only vs action behavior. |
| **Security** | Defaults, destructive-action gating, secret handling, env vars. |
| **Product Context** | The product area and its shared safety rules. |
| **References** | Bundled `references/` files to read on demand. |
| **Examples** | Few-shot user/assistant pairs that calibrate behavior. |

## Instructions: two styles

The **Instructions** section appears in two forms across the bundle:

- **Prose with subheadings**: narrative rules grouped under headings (e.g. Delivery SDK, Webhooks).
- **Structured JSON blocks**: an array of `{ "heading", "content" }` objects (e.g. Assets, Branches & Aliases, Environments & Publishing, Localization). These render as discrete rule cards.

Both are valid; they encode the same kind of guidance.

## References

When a skill needs authoritative detail beyond the body, it ships `references/` files and points to them:

```
### [Delivery SDK Spec](references/delivery-sdk-spec.md) (product doc, required)
- Source: Official Docs (…)
- Summary: …
- Read: references/delivery-sdk-spec.md
```

The agent reads these **on demand**, only when the task actually needs them, to keep context lean.

## Examples (few-shot)

Many skills end with worked **User → Assistant** pairs, often tagged `few shot` or `edge case`. These calibrate tone, format, and especially safety responses (for instance, how to refuse hardcoding a token, or how to gate a destructive action).

## Why the consistency matters

A predictable structure means:

- Agents can find the triggers, the rules, and the guardrails in the same place every time.
- Documentation pages map almost 1:1 to skill sections, so the [skills reference](../skills/index.md) is easy to keep in step with source.
- Authors have a template to follow. See [Authoring conventions](../contributing/authoring-conventions.md).
