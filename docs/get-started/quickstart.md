---
title: Quickstart
description: Install Contentstack Agent Skills for your tool and run your first Contentstack-aware prompt in about five minutes.
---

# Quickstart

Get your AI assistant Contentstack-aware in three steps.

## 1. Install the bundle

Pick your tool and run the install. Each link has the full guide; the commands below are the short version.

### Claude Code

```
/plugin marketplace add contentstack/contentstack-agent-skills
/plugin install contentstack-skills
```

→ [Full guide](install-claude-code.md)

### Cursor

Install from Cursor's plugin marketplace, **or** copy `cursor/rules/*.mdc` into your project's `.cursor/rules/` directory.

→ [Full guide](install-cursor.md)

### Codex / OpenAI agents

Point your agent at the repo or copy the `codex/` directory into your project. The entry point is `codex/AGENTS.md`.

Repository: [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills)

→ [Full guide](install-codex.md)

### Gemini CLI

```
gemini extensions install contentstack/contentstack-agent-skills
```

→ [Full guide](install-gemini.md)

### Single skill only

```
npx skills add contentstack/contentstack-agent-skills@dx-delivery-sdk
```

→ [Full guide](skills-cli.md)

## 2. Confirm the router loaded

For the full-bundle formats, the **router** decides which skill to apply. Confirm it's active before relying on it. See [Verify your setup](verify-setup.md). A quick check: ask your assistant _"Which Contentstack skills do you have available?"_ and it should list skills from the bundle.

## 3. Run your first prompt

Ask a Contentstack question in natural language. The agent routes to the matching skill automatically. Try one of these:

- _"Write a Contentstack Delivery SDK query in TypeScript for blog posts, including the author reference."_ → routes to **Delivery SDK**
- _"Should product categories be a taxonomy, tags, or a referenced content type?"_ → routes to **Taxonomy** / **Data Modeling**
- _"My Live Preview iframe is blank. What should I check?"_ → routes to **Live Preview & Visual Builder Support**
- _"What token should I use to read published content from my frontend?"_ → routes to **Tokens & Authentication**

You should get an answer that uses correct Contentstack patterns and follows the safety rules (for example, no hardcoded tokens).

## What's next

- Browse everything the bundle can do in the [skills reference](../skills/index.md).
- Understand how routing works in [The router](../how-it-works/router.md).
