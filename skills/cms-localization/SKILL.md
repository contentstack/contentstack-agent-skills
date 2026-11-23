---
name: cms-localization
description: "Advise developers on Contentstack localization: language setup, fallback chains, localized vs unlocalized entries, non-localizable fields, and multi-locale publishing. Use when developers ask about languages, fallback chains, localizing entries, non-localizable fields, or multi-locale publishing. Clarify whether the question concerns the CMS editorial experience or CDA delivery behavior. For translation apps such as Trados or Smartling, use marketplace-apps."
allowed-tools: Read Grep Glob
---

# Contentstack Localization

Advise on multilingual content: the master language, fallback chains, localized vs unlocalized entries, non-localizable fields, CDA locale queries and multi-locale publishing.

## When to use

- Setting up languages and fallback chains.
- Localized vs unlocalized entries, and Unlocalize.
- Deciding which fields are non-localizable.
- Querying locales on the CDA and publishing in several locales.

Use another skill for:

- Translation and localization apps from the Marketplace → `marketplace-apps`
- Localizing taxonomy terms → `cms-taxonomy`
- Locale-aware queries in SDK code → `dx-delivery-sdk`
- Modeling which content is shared across locales → `cms-data-modeling-best-practices`

## Before you answer

Find out the target languages and markets, the fallback requirements, the translation workflow, which content is shared across locales, and whether the question is about the CMS editorial experience or CDA delivery behavior. If that last point is unclear, ask.

## Instructions

1. Confirm the target locales and markets, and whether the question is about CMS or CDA behavior.
2. Explain the master language constraints and design the fallback chain.
3. Recommend which fields stay non-localizable.
4. Describe localized vs unlocalized entry behavior and its editorial impact.
5. Give CDA locale query guidance and a multi-locale publishing strategy.

### Master language

State upfront that the master language is permanent, set at stack creation, and ends every fallback chain.

### Fallback chain design

Each language can have one fallback language. Inheritance is a chain such as `fr-ca` -> `fr-fr` -> `en-us` (master). Warn that changing fallback relationships later affects existing content inheritance.

### Localized vs unlocalized entries

A localized entry is an independent copy with its own version history, publishing status and workflow state. An unlocalized entry inherits from its fallback chain. Localizing is reversible: Unlocalize removes the locale's own content and the entry goes back to inheriting from its fallback, or from the master language if the fallback has no content. Unlocalized and deleted entries can be restored from Trash within 14 days.

### Non-localizable fields

Recommend marking structural or shared data as non-localizable, such as SKUs, prices, dates, coordinates, boolean flags, shared assets and identifiers. Keep human-readable text fields localizable.

### CDA locale queries

Tell developers to pass `locale` explicitly in CDA requests. Use `include_fallback=true` when they want the fallback chain to apply; without it, only the exact locale is checked.

### Multi-locale publishing

Editors can publish multiple locale versions from the master language entry, subject to plan limits. Only the latest version of each localized entry is published, and localized entry versions can be deleted only from the master language entry's delete modal.

## MCP tools

When the Contentstack MCP server is connected, these tools act on the stack (local server group in brackets):

- Inspect: `get_all_languages` (`cma`); `get_all_entries_cdn`, `get_a_single_entry_cdn` with `locale` and `include_fallback` (`cda`, to see what each locale serves)
- Change: `localize_an_entry`, `publish_an_entry` (several locales at once) (`cma`)
- Remove: `unlocalize_an_entry` (`cma`)

There are no tools to add languages or change fallback chains; do that in the stack's language settings or with the CMA.

## Output

State whether the answer covers the editorial UI or CDA behavior. Lead with the recommendation, and show the fallback chain or the query inline.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks for the change.
- Never expose secrets, tokens, or API keys in output or logs.
- Always use environment variables for credentials, and never hardcode secrets in scripts, examples, or instructions.
- Route CMA calls through server-side proxies in browser apps, and never hardcode stack API keys in client-side code.
- Do not claim access to tools or connectors that are not explicitly available.
- Clearly separate verified facts from assumptions.

### Destructive Actions

- Before localizing, unlocalizing or publishing, list the entry, locales and environments affected and wait for explicit confirmation. Unlocalize removes the locale's own content.
- Never auto-execute delete, overwrite, or publish operations.

### Secrets

- Treat all tokens, passwords, and API keys as sensitive.
- Never echo or log secret values.
- Mask secrets in any output shown to users.
- Use environment variables exclusively for credential storage.

### Environment Variables

- Document every required environment variable.
- Provide example values without real credentials.
- Validate presence of required env vars before execution.
- Never use default fallback values for secrets.
