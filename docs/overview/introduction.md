---
title: Introduction
description: What Contentstack Agent Skills are, the problem they solve, and how the bundle is structured.
---

# Introduction

## What are agent skills?

An **agent skill** is a self-contained instruction set that teaches an AI coding assistant how to perform a specific task correctly. Each skill captures Contentstack's recommended approach to one area: data modeling, entry queries, asset delivery, Live Preview, Launch deployments, and so on, including the patterns to follow, the mistakes to avoid, and the safety rules to enforce.

Contentstack Agent Skills bundle **these skills** into a single package you can install into the AI tool you already use. Once installed, your assistant automatically reaches for the right skill based on what you ask. You don't have to remember which file to open or paste documentation into your prompt.

## The problem they solve

AI coding assistants are capable but generic. Out of the box they tend to:

- Use outdated or invented SDK method names and chain orders.
- Mix up the Content Delivery API (CDA) and Content Management API (CMA).
- Suggest unsafe patterns: hardcoded tokens, management tokens in client code, reused Live Preview stacks.
- Over-model content, create deep reference chains, or miss localization and governance constraints.

Agent skills close that gap. They give the assistant Contentstack-specific knowledge and guardrails so its output is correct, production-ready, and safe by default.

## What's in the bundle

The skills span seven Contentstack product areas:

| Product | Skills |
| --- | --- |
| **CMS** | Assets · Branches & Aliases · Data Modeling · Entries · Environments & Publishing · Localization · Releases · Roles & Permissions · Taxonomy · Tokens & Authentication · Variants & Personalization · Webhooks · Workflows |
| **Assets** | Asset Management |
| **Developer Experience** | Delivery SDK · Contentstack Kickstart Next · Migrate JS→TS SDK · Live Preview & Visual Editor Support · Migration Companion |
| **Studio** | Contentstack Studio |
| **Launch** | Sync env vars from `.env.example` · Trigger & Monitor Deployments |
| **Brand Kit** | Brand Kit Assistant |
| **Developer Hub** | Developer Hub App Architect |

See the full [skills reference](../skills/index.md) for a description of each.

## One source, every tool

Every skill is authored once as a `SKILL.md` file in the open [Agent Skills](https://agentskills.io) format. These tools read that format natively, so they all install the same files:

- **Claude Code**, **claude.ai**, and **Claude Cowork**: a plugin from the marketplace
- **Cursor**: a plugin added from the GitHub repository
- **Codex**: a plugin from the marketplace
- **GitHub Copilot**: a plugin for Copilot CLI or VS Code
- **Gemini CLI**: an extension
- **[`skills` CLI](https://github.com/vercel-labs/skills)**: pulls any single skill into almost any agent

You install only one. The bundle lives at [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). The [supported tools](supported-tools.md) page compares the install options, and [Architecture](../how-it-works/architecture.md) explains how one folder serves every tool.

## Next steps

- New here? Start with the [Quickstart](../get-started/quickstart.md).
- Want the mental model first? Read [Concepts & terminology](concepts.md).
- Curious what's covered? Browse the [skills reference](../skills/index.md).
