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

Every skill uses the same sections in the same order, and `scripts/validate.mjs` enforces it. The full template is in [Skill template](../contributing/skill-template.md).

| Section | Required | What it captures |
| --- | --- | --- |
| **When to use** | Yes | The requests the skill handles, and which neighbouring skill to use instead for related topics. |
| **Before you answer** | No | What to find out or inspect first. |
| **Instructions** | Yes | A short numbered workflow, then the rules and facts under `###` subsections. |
| **MCP tools** | Yes | The Contentstack MCP tools that carry out the steps, or what to use when no tool covers the area. |
| **Output** | No | How answers should be shaped. |
| **Security** | Yes | Defaults, destructive-action gating, secret handling, env vars. |
| **References** | No | Bundled `references/` files and public docs. |
| **Examples** | No | Few-shot user/assistant pairs that calibrate behavior. |

The body doesn't restate the frontmatter description. Example prompts live in the [routing evals](../contributing/routing-evals.md), where they're tested.

## Advisory by default, MCP when asked

Skills explain and show code. When the Contentstack MCP server is connected and the user asks for the change, the agent uses the tools named in **MCP tools**: read tools freely, and write, publish, deploy or delete tools only after naming the target and getting confirmation.

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

Some skills end with worked **User → Assistant** pairs. These calibrate tone, format, and especially safety responses (for instance, how to refuse hardcoding a token, or how to gate a destructive action).

## Why the consistency matters

A predictable structure means:

- Agents can find the triggers, the rules, and the guardrails in the same place every time.
- Documentation pages map almost 1:1 to skill sections, so the [skills reference](../skills/index.md) is easy to keep in step with source.
- Authors have a template to follow. See [Authoring conventions](../contributing/authoring-conventions.md).
