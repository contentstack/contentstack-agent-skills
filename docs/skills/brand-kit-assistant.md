---
title: Brand Kit Assistant
description: The entry point for Contentstack Brand Kit, concepts, setup, governance, Voice Profiles, Knowledge Vault, on-brand AI generation, and API-task routing.
---

# Brand Kit Assistant

**Slug:** `brand-kit-assistant` · **Product:** Brand Kit · **Type:** Advisory + API routing · **Ships references**

The primary entry point for Contentstack Brand Kit. It explains how Brand Kit, Voice Profiles, and Knowledge Vault fit together, guides setup and governance, routes API-specific tasks to the right capability, and enforces brand and safety rules before presenting anything as ready.

## When it triggers

When you ask about Brand Kit, Voice Profiles, Knowledge Vault, brand voice, tone, style rules, on-brand AI generation, setup, governance, or API usage.

## What it covers

- **Concepts**: a Brand Kit container, one or more Voice Profiles (how content should sound), and a Knowledge Vault (brand facts and source material) used to ground AI generation.
- **Setup**: creating a Brand Kit from a website or file upload, and mapping content to a Voice Profile vs Knowledge Vault.
- **On-brand generation**: use a Voice Profile for tone/style plus Knowledge Vault for factual grounding, then validate output against brand guidelines before publishing.
- **Knowledge Vault behavior**: it's vector-based semantic storage. It does **not** return original files or PDFs; keep source documents in your DAM/document system.
- **API guidance**: Brand Kit Management API (Brand Kits, Voice Profiles), Knowledge Vault API (ingest, update, delete, search, chunk retrieval), Generative AI API (content generation). Respects the 10 req/s per-organization rate limit and region-specific base URLs.

## References

Ships scoped API references: `references/brand-kit-management-api-reference.md` and `references/knowledge-vault-api-reference-skill.md`, read on demand for specific operations.

## Example prompts

- "What is Contentstack Brand Kit and what can I use it for?"
- "How do I create a Brand Kit from our website?"
- "Update this Voice Profile to match our brand voice."
- "How do I make AI-generated content stay on-brand?"
- "Can I get the original files back from Knowledge Vault?"

## Safety notes

Never exposes Brand Kit API tokens, authtokens, or decrypted credentials. Acknowledges secrets at a high level without echoing them. Requires explicit confirmation and a confirmed UID before destructive actions (delete, unpublish, overwrite). Validates generated content against brand guidelines before calling it ready and won't override brand rules without approval. Asks for missing identifiers, auth, region, or source content rather than guessing.

## Related

- [Tokens & Authentication](cms-tokens-authentication.md) · [Security & safety model](../how-it-works/security-model.md)
