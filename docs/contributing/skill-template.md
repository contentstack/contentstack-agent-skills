---
title: Skill template
description: "The section outline every SKILL.md follows, with a copyable template. scripts/validate.mjs enforces it."
---

# Skill template

Every `skills/<slug>/SKILL.md` uses the same sections in the same order. `node scripts/validate.mjs` fails a skill that has a section outside this list, misses a required one, or puts them out of order.

| Section | Required | What goes in it |
| --- | --- | --- |
| `## When to use` | Yes | The requests the skill handles, then **Use another skill for:** with the neighbouring skills and what they own. |
| `## Before you answer` | No | What to find out or inspect first: IDs, framework, region, the user's goal. |
| `## Instructions` | Yes | A short numbered workflow, then `###` subsections with the rules and facts. Long or volatile detail goes in `references/`. |
| `## MCP tools` | Yes | Which Contentstack MCP tools carry out the steps, grouped as inspect, change and delete, with the local server group in brackets. If no tool covers the area, say so and name the API, CLI or UI to use instead. |
| `## Output` | No | How to shape the answer. |
| `## Security` | Yes | `### Defaults`, `### Destructive Actions`, `### Secrets`, `### Environment Variables`. |
| `## References` | No | Bundled `references/` files and public docs URLs. |
| `## Examples` | No | Worked User → Assistant pairs, mostly for refusals and confirmation gates. |

Keep the rest out of the body:

- **Don't restate the description.** The frontmatter `description` does the routing; the body starts with a one- or two-sentence scope statement under the title.
- **Example prompts belong in [routing evals](routing-evals.md)**, where they're tested, not in the skill.
- **Product context and safety rules go in Security.** Don't repeat a separate product block.

## MCP pairing

The skills are advisory by default: they explain and show code. When the Contentstack MCP server (the local `@contentstack/mcp` server or MCP Profile Hub) is connected and the user asks for the change, the agent can make it with the tools listed under `## MCP tools`. The rules:

- Read tools can run freely to ground an answer in the user's real stack.
- Before any create, update, publish, deploy or delete, the agent names the target (stack, branch, environment, entries) and waits for confirmation.
- Tool names are the local server's, from `https://mcp.contentstack.com/<group>/tools`. Profile Hub profiles expose a chosen subset, so the agent uses what its client lists.

`allowed-tools` in the frontmatter pre-approves tools; it doesn't block MCP tools, which still follow the client's permission settings.

## Template

````markdown
---
name: <slug>
description: "<What the skill does, with the product terms users say>. Use when <concrete requests>. For <neighbouring topic>, use <other-skill>."
allowed-tools: Read Grep Glob
---

# <Title>

<One or two sentences: what this skill covers.>

## When to use

- <Request the skill handles>
- <Request the skill handles>

Use another skill for:

- <Topic> → `<other-skill>`

## Before you answer

<What to ask or inspect first.>

## Instructions

1. <Step>
2. <Step>

### <Rule group>

<Rules and facts.>

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `<tool>` (`<group>`)
- Change: `<tool>` (`<group>`)
- Delete: `<tool>` (`<group>`)

## Output

<How to shape the answer.>

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.

### Destructive Actions

<What needs confirmation, and what to say before asking.>

### Secrets

Never print, echo or store tokens, API keys or secrets. Use placeholders.

### Environment Variables

<Variable names to use in examples.>

## References

- <Public docs URL>
````
