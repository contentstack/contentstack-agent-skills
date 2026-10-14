---
title: Contentstack Kickstart Next
description: Maintain Contentstack's Next.js kickstart with guidance for App Router structure, Contentstack setup, Live Preview, seeded content, environment variables, validation, and reviews.
---

# Contentstack Kickstart Next

**Slug:** `dx-kickstart-next` · **Product:** Developer Experience · **Type:** Builder and review guidance · **Ships references**

Helps agents build, review, debug, and extend Contentstack's `kickstart-next` repository or a close fork. It routes work into focused reference files for Next.js behavior, Contentstack delivery and preview setup, the seeded content model, local workflow, and PR review checks.

## When it triggers

When you ask about the Next.js kickstart app, App Router structure, Contentstack Delivery SDK setup, Live Preview or Visual Builder behavior, seeded stack alignment, environment variables, endpoint or image host configuration, package scripts, local setup, CI expectations, validation commands, or review checklists.

## What it covers

- **Next.js structure**: App Router routes, client/server boundaries, Tailwind, ESLint, TypeScript, image allowlists, and package scripts.
- **Contentstack integration**: centralized stack setup, Delivery SDK configuration, Live Preview initialization, Visual Builder edit tags, regions, hosts, and env vars.
- **Seed alignment**: `page` content type fields, modular blocks, asset shapes, CSLP `$` mappings, and renderer/type updates.
- **Workflow**: local setup, stack seeding, npm validation, docs updates, CODEOWNERS, dependency changes, and CI expectations.
- **Reviews**: blockers, major issues, minor nits, security checks, and pre-PR validation.

## Example prompts

- "Review my kickstart-next PR for Live Preview regressions."
- "Add a new modular block to the Next.js kickstart and keep Visual Builder working."
- "Why are my Contentstack images failing in next/image?"
- "Update the kickstart env vars for a dedicated Contentstack environment."
- "What should I run before opening a PR?"

## References

Ships focused reference files in `references/`:

- `next.md` for Next.js, TypeScript, Tailwind, images, and scripts.
- `contentstack.md` for Delivery SDK setup, preview, Visual Builder, regions, hosts, and env vars.
- `content-model.md` for seeded content type and field contracts.
- `workflow.md` for setup, validation, CI, docs, and dependency work.
- `review.md` for review severity and pre-PR checks.

## Safety notes

Never commits real Contentstack credentials. Uses `.env.example` and docs for placeholders, keeps runtime behavior grounded in the current checkout, and verifies scripts and CI workflows before claiming they exist.

## Related

- [Delivery SDK](dx-delivery-sdk.md) · [Live Preview & Visual Builder Support](cms-live-preview-visual-builder-support-assistant.md) · [Data Modeling Best Practices](cms-data-modeling-best-practices.md)
