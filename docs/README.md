---
title: Contentstack Agent Skills
description: "Documentation for the Contentstack agent skills bundle: Contentstack-aware instruction sets for Claude Code, claude.ai, Cursor, Codex, GitHub Copilot, Gemini, and the skills CLI."
---

# Contentstack Agent Skills

Contentstack Agent Skills are ready-to-use instruction sets that make your AI coding assistant Contentstack-aware. Install one bundle and your agent knows when and how to model content, query entries, handle assets, wire up Live Preview, write Delivery SDK code, automate Launch deployments, migrate from another CMS, and more, following Contentstack's own best practices and safety rules.

Every skill is written once in the open [Agent Skills](https://agentskills.io) format, which **Claude Code**, **claude.ai / Claude Cowork**, **Cursor**, **Codex**, **GitHub Copilot**, **Gemini CLI**, and the **`skills` CLI** all read natively. Install it in whichever tool fits your workflow.

## Documentation map

### Overview

- [Introduction](overview/introduction.md): what agent skills are and the problem they solve
- [Concepts & terminology](overview/concepts.md): skills, descriptions, references, scripts, manifests
- [Supported tools & compatibility](overview/supported-tools.md): every supported tool and how each one installs the bundle

### Get started

- [Quickstart](get-started/quickstart.md): install for your tool and run your first prompt in ~5 minutes
- [Install for Claude Code](get-started/install-claude-code.md)
- [Install for claude.ai and Claude Cowork](get-started/install-claude-ai.md)
- [Install for Cursor](get-started/install-cursor.md)
- [Install for Codex](get-started/install-codex.md)
- [Install for GitHub Copilot](get-started/install-copilot.md)
- [Install for Gemini CLI](get-started/install-gemini.md)
- [Use a single skill via the skills CLI](get-started/skills-cli.md)
- [Verify your setup](get-started/verify-setup.md)

### How skills work

- [Architecture](how-it-works/architecture.md): one source of truth and the per-tool manifests
- [How skill selection works](how-it-works/router.md): how a request is matched to a skill
- [Anatomy of a SKILL.md](how-it-works/skill-anatomy.md): the structure every skill follows
- [Security & safety model](how-it-works/security-model.md): secret handling and destructive-action gating

### Skills reference

- [All skills](skills/index.md): the full catalog, grouped by product

### Contributing

- [Add or edit a skill](contributing/add-or-edit-a-skill.md)
- [Authoring conventions](contributing/authoring-conventions.md)
- [Release & versioning](contributing/release-and-versioning.md)

## At a glance

|                          |                                                                                                                |
| ------------------------ | -------------------------------------------------------------------------------------------------------------- |
| **Skills included**      | 24 (see the [skill reference](skills/index.md))                                                                |
| **Products covered**     | CMS, Assets, Developer Experience, Studio, Launch, Brand Kit, Developer Hub                                    |
| **Supported tools**      | Claude Code, claude.ai / Cowork, Cursor, Codex, GitHub Copilot, Gemini CLI, `skills` CLI                       |
| **Source of truth**      | `skills/<slug>/SKILL.md`                                                                                       |
| **Repository**           | [github.com/contentstack/contentstack-agent-skills](https://github.com/contentstack/contentstack-agent-skills) |

## Learn more about Contentstack

- [contentstack.com/docs](https://www.contentstack.com/docs): full product documentation
- [developers.contentstack.com](https://developers.contentstack.com): SDKs, CLIs, and API references
- [contentstack.com/academy](https://www.contentstack.com/academy): training and learning paths
- [contentstack.com/explorer](https://www.contentstack.com/explorer): free sandbox accounts for testing
