# Contentstack skill router

Use the table below to route a user request to the right skill. Each row maps a typical user intent to a skill's canonical `SKILL.md`.

| When the user asks… | Skill |
|----------------------|-------|
| Use when designing, reviewing, or refactoring Contentstack content models before creating or changing schemas. | [Contentstack Data Modeling Best Practices](./cms-data-modeling-best-practices/SKILL.md) |
| Use this skill when a user is implementing or debugging Contentstack Live Preview or Visual Builder, including blank preview panels, stale or published-only preview, lost preview context after navigation, shared SSR state, cache contamination, or edit-tag mapping failures. Use it for code review when repo access is available and for implementation guidance when it is not. | [Live Preview and Visual Builder Support Assistant](./cms-live-preview-visual-builder-support-assistant/SKILL.md) |
| Use when developers ask about fetching entries, building CDA queries, handling localization, publishing workflows, versioning behavior, bulk operations, or entry-related performance issues. | [Entries](./cms-entries/SKILL.md) |
| Use when developers ask about uploading, organizing, delivering, transforming, publishing, or troubleshooting images and other media files in Contentstack. | [Contentstack Assets](./cms-assets/SKILL.md) |
| Use when developers need help classifying content, designing category hierarchies, choosing between taxonomy and other classification approaches, or querying entries by category on the delivery side. | [Contentstack Taxonomy](./cms-taxonomy/SKILL.md) |
| Use when developers ask about workflow stage design, approval processes, publish rules, self-approval prevention, transition restrictions, or automation triggered by workflow changes. | [Workflows & Publish Rules](./cms-workflows/SKILL.md) |
| Use when developers ask about environment setup, publishing behavior, delivery or preview tokens, the Sync API, scheduling, or CDN and caching configuration in Contentstack. | [Contentstack Environments & Publishing](./cms-environments-publishing/SKILL.md) |
| Use when developers ask about languages, fallback chains, localizing entries, non-localizable fields, or multi-locale publishing. Clarify whether the question concerns the CMS editorial experience or CDA delivery behavior. | [Contentstack Localization](./cms-localization/SKILL.md) |
| Use when developers ask about branches, aliases, CI/CD integration with Contentstack, deployment strategies, or branch-specific vs global module behavior. | [Branches & Aliases](./cms-branches-aliases/SKILL.md) |
| Use when developers ask about user permissions, role design, team management, token capabilities, access control, or automation access in Contentstack. | [Roles & Permissions](./cms-roles-permissions/SKILL.md) |
| Use when developers ask about deploying multiple content changes together, campaign launches, coordinated content updates, release scheduling, or CI/CD content deployment. | [Releases](./cms-releases/SKILL.md) |
| Use when developers ask about authentication, token types, API keys, rate limits, SSO integration, or credential security. | [Tokens & Authentication](./cms-tokens-authentication/SKILL.md) |
| Use when developers need help setting up webhooks, choosing event channels, handling webhook payloads, verifying signatures, debugging delivery issues, or integrating Contentstack with external systems such as site rebuilds, search indexes, Slack, or CI/CD. | [Contentstack Webhooks](./cms-webhooks/SKILL.md) |
| Use when a Launch environment must match the keys defined in a local `.env.example` file. | [Sync Launch environment variables from .env.example](./launch-sync-environment-variables-from-env-example/SKILL.md) |
| Use when you need to automate Launch deployments for a known project and environment, monitor progress, and surface failure diagnostics. This is appropriate for CI/CD or operator workflows that need a deterministic deploy status check and log-based troubleshooting. | [Trigger and Monitor Launch Deployments](./launch-trigger-and-monitor-launch-deployments/SKILL.md) |
| Use when developers ask about content personalization, A/B testing, audience segmentation, variant creation, or integrating Personalize with the CMS. | [Variants & Personalization](./cms-variants-personalization/SKILL.md) |
| Use when a user needs help designing or building a Contentstack Developer Hub or Marketplace app. | [Developer Hub App Architect](./developer-hub-app-architect/SKILL.md) |
