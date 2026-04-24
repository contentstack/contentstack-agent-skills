---
name: cms-releases
description: "Advise developers on using Contentstack Releases for coordinated, atomic content deployment. Cover release creation, item management, staged deployment, webhook storm prevention, and CI/CD integration."
allowed-tools: Read Grep Glob
---

# Releases

## Description

Advise developers on using Contentstack Releases for coordinated, atomic content deployment. Cover release creation, item management, staged deployment, webhook storm prevention, and CI/CD integration.

## When to Use

Use when developers ask about deploying multiple content changes together, campaign launches, coordinated content updates, release scheduling, or CI/CD content deployment.

## User Problem

Developers need to deploy related content changes atomically so campaigns, redesigns, or coordinated updates go live together without manual coordination errors.

## Success Criteria

Provides practical release workflow guidance.
Explains webhook storm risks and mitigation.
Shows CI/CD integration patterns when relevant.
Correctly states release limitations and constraints.

## Expected Inputs

- Deployment coordination requirements
- Number and type of content items
- CI/CD pipeline details
- Scheduling needs

## Expected Outputs

- Release workflow recommendations
- Webhook storm prevention guidance
- CI/CD integration patterns
- Limitation awareness

## Example User Requests

- How do I deploy a campaign with 50 entries at once?
- Can I schedule a release for a future date?
- My static site rebuilds hundreds of times per release deployment.
- How do I integrate releases with my CI/CD pipeline?
- What are the limits on releases?

## Workflow Summary

Understand the coordination requirements.
Recommend release creation and item grouping.
Advise staging validation before production.
Warn about webhook storms and receiver debouncing.
Cover CI/CD integration if applicable.
State release limitations and when not to use releases.

## Instructions

### Release workflow

Create a release with a descriptive name. Add all related entries and assets, including items from multiple content types and locales. Deploy to staging first, validate, then deploy to production. Specify which version of each entry to deploy when needed.

### Webhook storm

A release deployment triggers one webhook event per item. Warn users to debounce webhook receivers and inspect the source key in payloads when present. Refer to the Webhooks skill for receiver-specific handling.

### Limitations

Max 100 items per single API call when adding items to a release. Release titles max out at 50 characters. Updating release items to latest versions does not automatically add new references from updated entries. Releases are branch-specific.

### CI/CD integration

Use a pipeline that creates a release, adds changed items, deploys to staging, runs tests, then deploys to production on success. Combine with branches and aliases for automated content deployment.

### When not to use releases

Do not recommend releases for routine single-entry publishes. Use them when coordinated deployment across multiple content pieces is required.

## Output Format

Be concise and practical.
Emphasize the webhook storm gotcha when relevant.
Prefer bullets or short steps over long prose.
State limitations clearly when they affect the recommendation.

## Tooling Notes

Read-only advisory.
Do not create, deploy, or modify releases.
Use read-only tools only.

## Security

### Defaults

Never expose tokens or API keys.
Use environment variables for credentials in example code.
Do not suggest client-side access to management credentials.

### Destructive Actions

Do not perform or instruct destructive or irreversible release operations. This skill is advisory only and must not create, deploy, update, or delete releases.

### Secrets

Never reveal management tokens, API keys, or other secrets. If code is shown, use placeholders and environment variables only.

### Environment Variables

Use environment variables for all credentials in examples and integration guidance. Never hardcode secrets in sample code.

## Product Context

- - Product: CMS
- - Description: Contentstack headless CMS: content types, entries, assets, environments, publishing, workflows, webhooks, and the Content Management API (CMA).
- - Product safety rules: - Never expose management tokens or API keys.
- Always use environment variables for credentials.
- Route all CMA calls through server-side proxies in browser apps.
- Never hardcode stack API keys in client-side code.
- - Default tools: ["CMA API", "Content Types", "Entries", "Assets", "Workflows", "Webhooks", "Environments", "Releases", "Publish Queue"]
- - Default connectors: ["CMA Proxy", "Webhooks"]