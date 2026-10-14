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
/plugin install contentstack-skills@contentstack-skills
```

→ [Full guide](install-claude-code.md)

### claude.ai and Claude Cowork

Go to **Customize → Plugins → Add marketplace** and enter `contentstack/contentstack-agent-skills`.

→ [Full guide](install-claude-ai.md)

### Cursor

Open **Settings → Plugins**, choose **Add from GitHub repository**, and enter `https://github.com/contentstack/contentstack-agent-skills`.

→ [Full guide](install-cursor.md)

### Codex

```
codex plugin marketplace add contentstack/contentstack-agent-skills
codex plugin add contentstack-skills@contentstack-skills
```

→ [Full guide](install-codex.md)

### GitHub Copilot

```
copilot plugin marketplace add contentstack/contentstack-agent-skills
copilot plugin install contentstack-skills@contentstack-skills
```

In VS Code, add the repo to `chat.plugins.marketplaces` instead.

→ [Full guide](install-copilot.md)

### Gemini CLI

```
gemini extensions install https://github.com/contentstack/contentstack-agent-skills
```

→ [Full guide](install-gemini.md)

### Single skill only

```
npx skills add contentstack/contentstack-agent-skills --skill dx-delivery-sdk
```

→ [Full guide](skills-cli.md)

## 2. Confirm the skills loaded

Ask your assistant _"Which Contentstack skills do you have available?"_ It should list skills from the bundle. If it doesn't, see [Verify your setup](verify-setup.md).

## 3. Run your first prompt

Ask a Contentstack question in natural language. The agent matches it to a skill's description and loads that skill automatically. Try one of these:

- _"Write a Contentstack Delivery SDK query in TypeScript for blog posts, including the author reference."_ → loads **Delivery SDK**
- _"Should product categories be a taxonomy, tags, or a referenced content type?"_ → loads **Taxonomy** / **Data Modeling**
- _"My Live Preview iframe is blank. What should I check?"_ → loads **Live Preview & Visual Editor Support**
- _"What token should I use to read published content from my frontend?"_ → loads **Tokens & Authentication**

You should get an answer that uses correct Contentstack patterns and follows the safety rules (for example, no hardcoded tokens).

## What's next

- Browse everything the bundle can do in the [skills reference](../skills/index.md).
- Understand how the agent picks a skill in [How skill selection works](../how-it-works/router.md).
