---
title: Introduction
description: What Contentstack Agent Skills are, the problem they solve, and how the bundle is structured.
---

# Introduction

## What are agent skills?

An **agent skill** is a self-contained instruction set that teaches an AI coding assistant how to perform a specific task correctly. Each skill captures Contentstack's recommended approach to one area: data modeling, entry queries, asset delivery, Live Preview, Launch deployments, and so on, including the patterns to follow, the mistakes to avoid, and the safety rules to enforce.

Contentstack Agent Skills bundle **22 of these skills** into a single package you can install into the AI tool you already use. Once installed, your assistant automatically reaches for the right skill based on what you ask. You don't have to remember which file to open or paste documentation into your prompt.

## The problem they solve

AI coding assistants are capable but generic. Out of the box they tend to:

- Use outdated or invented SDK method names and chain orders.
- Mix up the Content Delivery API (CDA) and Content Management API (CMA).
- Suggest unsafe patterns: hardcoded tokens, management tokens in client code, reused Live Preview stacks.
- Over-model content, create deep reference chains, or miss localization and governance constraints.

Agent skills close that gap. They give the assistant Contentstack-specific knowledge and guardrails so its output is correct, production-ready, and safe by default.

## What's in the bundle

The 22 skills span five Contentstack product areas:

| Product | Skills |
| --- | --- |
| **CMS** | Assets · Branches & Aliases · Data Modeling · Entries · Environments & Publishing · Localization · Releases · Roles & Permissions · Taxonomy · Tokens & Authentication · Variants & Personalization · Webhooks · Workflows |
| **Developer Experience** | Delivery SDK · Contentstack Kickstart Next · Migrate JS→TS SDK · Live Preview & Visual Builder Support · Migration Companion |
| **Launch** | Sync env vars from `.env.example` · Trigger & Monitor Deployments |
| **Brand Kit** | Brand Kit Assistant |
| **Developer Hub** | Developer Hub App Architect |

See the full [skills reference](../skills/index.md) for a description of each.

## One source, five formats

Every skill is authored once as a `SKILL.md` file and packaged for five tools:

- **Claude Code**: installable plugin
- **Cursor**: rule files (`.mdc`)
- **Codex / OpenAI agents**: a markdown tree
- **Gemini CLI**: an extension manifest
- **[`skills` CLI](https://github.com/anthropics/skills)**: pulls any single skill on demand

You install only one. The bundle lives at [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills). The [supported tools](supported-tools.md) page explains what each format produces, and [how skills work](../how-it-works/architecture.md) explains how the formats stay in sync.

## Next steps

- New here? Start with the [Quickstart](../get-started/quickstart.md).
- Want the mental model first? Read [Concepts & terminology](concepts.md).
- Curious what's covered? Browse the [skills reference](../skills/index.md).
