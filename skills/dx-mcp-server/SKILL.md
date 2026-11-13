---
name: dx-mcp-server
description: "Help developers connect AI agents to Contentstack over the Model Context Protocol, with either the local @contentstack/mcp stdio server or the hosted MCP Profile Hub. Cover choosing between them, npx setup, API groups (GROUPS), OAuth and token auth, required IDs per group, client configuration for Claude Code, Claude Desktop, claude.ai, Cursor, Codex and ChatGPT, Profile Hub profiles, connector URLs and URL parameters, Automate automations and Agent OS agents as tools, execution history, the Tool Definitions API, and safe least-privilege setups. Use when developers ask how to give an AI assistant access to Contentstack, set up or debug the Contentstack MCP server or MCP Profile Hub, pick tool groups or profiles, fix MCP auth or missing tools, or build their own MCP integration. Pairs with the other Contentstack skills, which supply the product knowledge the tools need. For the csdx CLI, use dx-cli."
allowed-tools: Read Grep Glob
---

# Contentstack MCP

Help developers give AI agents access to Contentstack through MCP. Contentstack offers two options: the local `@contentstack/mcp` server, which runs on the developer's machine over stdio, and MCP Profile Hub, a hosted server reached over Streamable HTTP that exposes curated tool profiles.

## When to use

- Connecting an AI assistant to Contentstack to read or change content, deploy with Launch, query Personalize, Brand Kit, Lytics, Analytics or Automate, or run automations and agents.
- Choosing between the local server and MCP Profile Hub, and picking tool groups or profiles.
- MCP setup failures: no tools appear, auth fails, or the wrong stack or region is used.
- Building your own MCP integration on Contentstack's tool definitions.

Use another skill for:

- The `csdx` CLI → `dx-cli`
- What to do with the tools once connected: the product skill for the area, such as `cms-entries`, `cms-branches-aliases`, `launch-platform`, `personalize` or `automations`
- Token types and auth outside MCP → `cms-tokens-authentication`
- Installing Marketplace apps (MCP Profile Hub is one) → `marketplace-apps`
- MCP setup inside a Studio project → `studio`

## Before you answer

Find out the MCP client (Claude Code, Claude Desktop, claude.ai, Cursor, Codex, ChatGPT, VS Code or another), the products and tasks the agent needs, the region, stack API key, branch and any project IDs, and whether the setup is personal or shared by a team. The agent should see the right tools for the job, act on the right stack and branch with the user's own permissions, and not load hundreds of tools or leak tokens.

## Instructions

1. Choose between the local server and Profile Hub.
2. Pick the smallest set of groups, tools or profile.
3. Configure the client and authenticate.
4. Set stack, branch and project context.
5. Verify with a read-only prompt.


### Choose local server or Profile Hub

- **Local `@contentstack/mcp` server:** runs with `npx` on the developer's machine over stdio. Best for individual development, quick starts, scripted setups, management-token use, and dedicated infrastructure with custom endpoints. Tool selection is per group.
- **MCP Profile Hub:** hosted by Contentstack at `https://mcp-profile-hub.contentstack.com/api/mcp`, reached over Streamable HTTP, so nothing is installed and it also works in web clients such as claude.ai and ChatGPT. Profiles expose only the tools you pick, connections are configured once in the app, sign-in is OAuth, every call runs with the user's Contentstack roles, and calls are logged in an Executions view. Best for teams, non-developers and governed access. It can also expose your Automate automations and Agent OS agents as tools.

When unsure, recommend Profile Hub for shared or team use and the local server for a single developer working in a repository.

### Local server: setup

Run it with `npx -y @contentstack/mcp`; no install is needed. Pick groups with `GROUPS` or `--groups` (comma-separated): `cma`, `cma-extended`, `cda`, `analytics`, `automations`, `brandkit`, `launch`, `developerhub`, `lytics`, `personalize`, or `all`. The default is `cma`. Load `cma-extended` (audit logs, version history, workflow and publish rule inspection, folder and global field writes) only when needed, because every group adds tool definitions to each request.

Auth and required IDs:

| Group | Auth | Also needs |
| --- | --- | --- |
| `cma`, `cma-extended` | OAuth, or a management token | `CONTENTSTACK_API_KEY` |
| `cda` | Delivery token | `CONTENTSTACK_API_KEY`, `CONTENTSTACK_DELIVERY_TOKEN` |
| `analytics`, `automations` | OAuth | — |
| `brandkit` | OAuth | `CONTENTSTACK_BRAND_KIT_ID` |
| `launch` | OAuth | `CONTENTSTACK_LAUNCH_PROJECT_ID`, `CONTENTSTACK_ORGANIZATION_UID` |
| `developerhub` | OAuth | `CONTENTSTACK_API_KEY` |
| `lytics` | Lytics access token | `LYTICS_ACCESS_TOKEN` |
| `personalize` | OAuth | `CONTENTSTACK_PERSONALIZE_PROJECT_ID` |

Run `npx @contentstack/mcp --auth` once to sign in with OAuth. It saves the session and region locally. A management token (`CONTENTSTACK_MANAGEMENT_TOKEN`) works only for `cma` and `cma-extended`, and then `CONTENTSTACK_REGION` must be set (`NA`, `EU`, `AU`, `AZURE_NA`, `AZURE_EU`, `GCP_NA`, `GCP_EU`). Optional defaults: `CONTENTSTACK_ENVIRONMENT`, `CONTENTSTACK_BRANCH` (default `main`) and `CONTENTSTACK_LOCALE`. Since 0.9.0 the server enriches tool schemas with live stack data (content types, environments, locales, branches); set `CONTENTSTACK_MCP_ENRICH_TOOLS=false` to turn it off. Dedicated infrastructure can override hosts with `CONTENTSTACK_*_BASE_URL` variables. Every value can also be passed as a CLI flag (`--stack-api-key`, `--groups` and so on) for clients without environment variable support.

Client configuration:

- **Claude Code:** `claude mcp add contentstack --env GROUPS=cma --env CONTENTSTACK_API_KEY=<key> -- npx -y @contentstack/mcp`
- **Claude Desktop:** add an `mcpServers` entry to `claude_desktop_config.json` with `"command": "npx"`, `"args": ["-y", "@contentstack/mcp"]` and an `env` block, then restart.
- **Cursor:** the same `mcpServers` entry in `~/.cursor/mcp.json`.
- Any other stdio MCP client uses the same `npx` command.

### Profile Hub: setup

1. Open **MCP Profile Hub** from the App Switcher, or install the Marketplace app (needs a role that can install apps).
2. Use a ready-made system profile (for example `cms` or `launch`), or create a profile: **+ New Profile**, name it, **Browse catalog**, and pick tools from the **Contentstack APIs**, **Automations** or **AI agents** tabs (up to 200 tools per profile).
3. In **Configure**, choose a stack (required) and any Launch, Personalize, Brand Kit, Automate or Lytics connections the tools need.
4. In **Installation**, copy the connector URL or the client snippet: `https://mcp-profile-hub.contentstack.com/api/mcp?profile_id=<PROFILE_ID>&org_uid=<ORG_UID>`.

Connecting clients:

- **Claude Code:** `claude mcp add --transport http <name> "<connector URL>"`. Quote the URL. Add `--scope user` to make it available in every project, then run `/mcp` to sign in.
- **claude.ai and Claude Desktop:** **Add to Claude** in the Installation step, or add a custom connector with the URL. On some Claude plans only admins can add custom connectors.
- **Claude Desktop without connectors, and other stdio-only clients:** wrap the URL with `mcp-remote` through `npx`, using the snippet from the Installation step (it pins the version). Needs Node.js.
- **Cursor:** **Add to Cursor**, or `{"mcpServers": {"<name>": {"url": "<connector URL>"}}}` in `.cursor/mcp.json`.
- **Codex:** a `[mcp_servers.<name>]` block with `url = "<connector URL>"` in `~/.codex/config.toml`.
- **ChatGPT:** add a custom connector with the URL, if the ChatGPT plan supports custom connectors.

Don't add Authorization headers or bearer tokens: they block the OAuth handshake. The client opens a browser sign-in on first use.

URL parameters override the profile's saved context for one connection: `stack_api_key`, `branch`, `environment`, `locale`, `launch_project_uid`, `personalize_project_uid`, `brandkit_project_uid`, `automation_project_uid`, and `timeout` (milliseconds; default 60,000, max 120,000). An invalid project UID fails the connection; an invalid stack, branch, environment, locale or timeout falls back to the saved value. Lytics has no URL parameter.

Things to know:

- An unpublished or empty profile connects but shows no tools.
- After editing a profile, the URL stays the same, but clients keep the old tool list until they reconnect.
- A profile never grants more than the user's Contentstack roles allow; calls beyond them fail.
- Automations appear as tools only when they have an HTTP trigger and are active; agents only when published with an HTTP trigger.
- Executions shows each call's input, result, timing and errors, and identifies the client, not the person. Use the organization audit log for user-level attribution.
- Tool lists for products the organization's plan doesn't include may not be offered.

### Least privilege and safety

- Start read-only. Add write, publish, delete or deploy tools only when the task needs them, and prefer a dedicated profile per job.
- Point agents at a development branch or stack first, and keep production publishing behind a separate profile or explicit confirmation.
- Keep management tokens out of shared configuration files and repositories; prefer OAuth.
- Before an agent deletes content types, global fields, assets, folders or branches, or deploys a release, ask it to state the target and wait for confirmation.

### Build your own

The local server's tool definitions are published at `https://mcp.contentstack.com/<group>/tools` (for example `/cda/tools`). Each definition includes a JSON Schema for the inputs and a mapper describing the HTTP request to build. The endpoints hold no credentials; callers bring their own tokens. Region hosts come from `https://artifacts.contentstack.com/regions.json`.

### Pair MCP with these skills

MCP gives the agent actions; the other Contentstack skills give it the product knowledge to use them well. For example, `cms-data-modeling-best-practices` before creating content types, `cms-branches-aliases` before merges, and `cms-webhooks` or `cms-releases` before publishing at scale.

## MCP tools

This skill is about the MCP server itself. Tools per local server group, as published at `https://mcp.contentstack.com/<group>/tools`:

| Group | Tools | Covers |
| --- | --- | --- |
| `cma` | 78 | Entries, content types, assets, branches, aliases and merges, releases, taxonomies, environments, variants, publishing |
| `cma-extended` | 22 | Audit logs, version history, global field and asset folder writes, workflow, publish rule and publish queue inspection |
| `cda` | 4 | Published entries and assets |
| `analytics` | 8 | Usage, device, URL, status code, cache and SDK analytics |
| `automations` | 9 | Automation projects, automations, triggering and activating |
| `brandkit` | 12 | Knowledge Vault, Voice Profiles, generative AI |
| `launch` | 27 | Projects, environments, deployments, logs, deploy hooks, cache revalidation |
| `developerhub` | 12 | Apps, OAuth, installations |
| `lytics` | 10 | Audiences, fields, user profiles, content classification |
| `personalize` | 24 | Attributes, audiences, experiences, events, analytics |

No group covers webhooks, roles, users, tokens, workflows (beyond reading them), publish rules (beyond reading them), labels or extensions; point users to the CMA or the UI for those. Profile Hub draws on the same catalog plus Automate automations and Agent OS agents, but a profile exposes only the tools chosen for it, so use the names the client lists.

## Output

Lead with the recommendation, then the exact configuration for the user's client, then the groups, profile or tools to enable, the auth steps, and the verification prompt (for example "List the content types in my stack"). Use placeholders for keys and IDs.

## Security

### Defaults

- Advisory by default. Do not edit the user's MCP configuration files or call Contentstack tools on their behalf unless asked.
- Prefer OAuth over tokens, and Profile Hub for shared access.
- Enable the fewest groups or tools that do the job.
- Keep production writes behind confirmation.

### Destructive Actions

Write tools can delete entries, content types, assets, branches and environments, publish to production, and deploy. Before enabling them, explain which tools are destructive and recommend a non-production target. Before the agent runs one, it names the target and waits for confirmation.

### Secrets

Never echo management, delivery or Lytics tokens or API keys. A connector URL that contains `apikey` also contains the stack API key, so share such URLs with care.

### Environment Variables

Keep tokens in environment variables or the client's secret storage, not in committed config files.

## References

- https://www.contentstack.com/docs/developers/contentstack-mcp-server
- https://www.contentstack.com/docs/developers/mcp-profile-hub
- https://www.contentstack.com/docs/developers/mcp-profile-hub-connect-a-client-to-profile-hub
- https://www.contentstack.com/docs/developers/mcp-profile-hub-url-parameters
- https://github.com/contentstack/mcp
