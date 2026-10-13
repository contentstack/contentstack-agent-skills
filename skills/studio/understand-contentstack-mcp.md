---
name: understand-contentstack-mcp
---

## When to use

What the Contentstack MCP server does, and what it does not. Read before installing, to decide whether it fits the task. Installing it is [`install-contentstack-mcp`](install-contentstack-mcp.md).

## What it does: and does NOT do

Grounded in `contentstack.com/docs/agent-os/contentstack-mcp-server` **and verified against the CLI source** (`~/.npm/_npx/*/node_modules/@contentstack/mcp/dist/index.js`).

> **REGION GATE: establish the data center BEFORE `--auth`, never after.** Verified against the CLI (`@contentstack/mcp` 0.9.0, `dist/chunk-IJB7CYTF.js`). Two independent settings, and only one of them is prod-locked:
>
> - **Region**: `--region` / `CONTENTSTACK_REGION`, normalized through `REGION_ALIASES` to exactly 7 codes: `NA` (aliases `US`, `AWS_NA`), `EU` (`AWS_EU`), `AU` (`AWS_AU`), `AZURE_NA`, `AZURE_EU`, `GCP_NA`, `GCP_EU`. Anything else (including a non-prod environment name) **throws at startup**: `Unknown region "<value>". Provide a valid region via --region or CONTENTSTACK_REGION`.
> - **Hosts**: overridable per tool group via `ENDPOINT_OVERRIDE_ENV`: `CONTENTSTACK_CMA_BASE_URL`, `CONTENTSTACK_CDA_BASE_URL`, `CONTENTSTACK_PERSONALIZE_BASE_URL`, `CONTENTSTACK_LAUNCH_BASE_URL`, `CONTENTSTACK_AUTOMATIONS_BASE_URL`, `CONTENTSTACK_DEVELOPERHUB_BASE_URL`, `CONTENTSTACK_ANALYTICS_BASE_URL`, `CONTENTSTACK_BRANDKIT_API_BASE_URL`, `CONTENTSTACK_LYTICS_BASE_URL`. These **win over the region-derived endpoint**.
>
> **So non-prod API calls ARE reachable**: a valid region code (it only has to normalize) plus the base-URL overrides for your `<env>`. **But the OAuth login itself is not:** the authorize host is region-derived with no override, so `--auth` can't mint a token for a custom DC. Use a management token there, or `csdx`. See § [OAuth on a custom region](#oauth-on-a-custom-region).
>
> **Why this must gate the login.** `DEFAULT_REGION = "NA"`. With nothing set, the CLI silently authenticates and runs **against NA prod**, no prompt, no warning. On a non-prod project that means an OAuth session and CMA writes pointing at the wrong data center, and every call succeeds. Resolve the DC first (Step 0). Only then run `--auth`.

### `--auth` is an interactive TUI: only the browser login needs you

Runtime-verified against `@contentstack/mcp` 0.9.0. `--auth` is **not** a headless command. It opens an `inquirer` menu on the terminal:

```
? Select an action:      ❯ Authorization / Exit
? Authorization actions: ❯ Login / Reauthorize / Logout / Back
? Select your Contentstack region: ❯ <region>
```

…then opens a browser and waits for the OAuth callback on `http://localhost:8184`.

Without a TTY it dies immediately with **`Error: User force closed the prompt with 0 null`**. Piping input gets through the first menu and fails on the second, measured. And even with the menus driven, the browser login still needs a human.

**So drive the menus via a PTY ([`install-contentstack-mcp`](install-contentstack-mcp.md) Step 3) or hand the user the command, region included.** Never make them work out flags. In Claude Code, `!` runs it in the session so the output lands back in the conversation:

```
! CONTENTSTACK_REGION=<NA|EU|AU|AZURE_NA|AZURE_EU|GCP_NA|GCP_EU> npx @contentstack/mcp --auth
```

Then choose **Authorization**, then **Login**. The browser opens and you finish the login there. The region belongs **in the command**, because `--auth` bakes the data center into the stored session. Setting it afterwards does not move an existing token (§ REGION GATE).

**Never print the command without a resolved region.** `DEFAULT_REGION` is `NA`, so omitting it silently authenticates against NA prod.

### When to re-run it: the session can die mid-work

Three signatures mean the stored session is unusable and the command above is the fix:

| Signature | Cause |
|---|---|
| `401 error_code 105` "access token is invalid or expired or revoked", and a refresh isn't possible | access token past its hour, no usable refresh token |
| `400 {"message":["invalid refresh_token"]}` | the stored refresh token was **spent**: refresh tokens rotate, and something refreshed without writing the new pair back ([`authenticate-cma`](authenticate-cma.md) § Refresh tokens rotate) |
| the store file is absent | never authenticated on this machine |

**`403 error_code 316` is NOT one of them.** That is a valid credential pointed at a stack outside its org. Re-authenticating changes nothing unless you deliberately switch org. Check with `GET /v3/stacks` + `organization_uid` first.

**Replaces the `authtoken`.** `npx @contentstack/mcp --auth` opens a browser OAuth login, then saves the tokens locally and reuses them automatically on every later run.

**Its OAuth session is reusable outside the MCP.** `--auth` writes `~/Library/Application Support/ContentstackMCP/oauth-config.json` (`%LOCALAPPDATA%\ContentstackMCP` on Windows, `~/.config/ContentstackMCP` elsewhere) holding `access_token`, `refresh_token`, `expires_in` (3600), `token_issued_at` and `organization_uid`. Scripts can read it instead of demanding an exported token. Scripts that refresh it must write the rotated pair back. The MCP refreshes within **5 minutes** of expiry. Anything sharing the store should use the same margin. See [`authenticate-cma`](authenticate-cma.md) § Where the credential actually lives.

**Auto-captures `organization_uid` + region.** The OAuth token stores the **org** (your login's default org) and the region, no need to ask for `org_id`. (This corrects the docs' "can't discover" claim: org IS captured. Only the stack isn't.)

**Runs CMA ops as tools** (77 CMA + 22 CMA-extended): `create_a_content_type`, `update_content_type`, `get_all_content_types`, `create_a_global_field`, `update_a_global_field`, `create_an_entry`, `update_an_entry`, `publish_an_entry`, `get_all_entries`, `get_all_environments`, `create_an_environment`, `get_all_assets`, `publish_an_asset`. Covers most of `provision-studio-stack`, the CT-create in `provision-studio-project`, and entry create/publish in `author-composition-via-api`. **Note: asset upload has NO tool** (only get/publish/update/delete of existing assets). Creating a new asset from a binary stays raw multipart `POST /v3/assets`.

**Does NOT auto-capture the stack `api_key`.** The token's `stack_api_key` is empty, no `list_stacks` tool. Before asking, read `CONTENTSTACK_API_KEY` from the MCP's registration (this project's `mcpServers.contentstack.env` in `~/.claude.json`), else [`install-playwright-mcp`](install-playwright-mcp.md) Step 5b's `CS_RECENT_STACK_API_KEY`. Found one: ask "Use stack `<key>`, or give another key?" None: ask for it. It MUST belong to the OAuth'd org (Step 5 new-vs-existing / 403-recovery loop).

**Studio API (`/v1/projects`): OAuth FIRST, session authtoken only as fallback.** The MCP has no tool for it, so this is raw HTTP either way. But **attempt OAuth before asking anyone for a session token**, in this order:

1. **OAuth `Authorization: Bearer <access_token>`**: the token `--auth` already stored. Works for `/v1/projects` read+write on environments where the Studio API accepts app tokens (confirmed on a non-prod data center after COMS-1710). **Always try this first.**
2. **`csdx --oauth`**: the CLI's own OAuth session, same credential class, no pasting.
3. **Create the project in the Studio UI**: zero tokens, and it onboards the stack too. Often the fastest answer for a one-off.
4. **Session authtoken, last resort only.** Fall back only after observing one of these exact rejections:
   - `authtoken: <oauth-token>` returns **401 `error_code 105`** "authtoken is not valid"
   - `Authorization: Bearer <oauth-token>` returns **422 `error_code 21`** "Stack not found" (auth accepted, stack unresolvable via the app-token path)
   - a management token as `authtoken:` returns **401** "not logged in"

> **Why the ordering matters: a session authtoken is a full user session credential.** It carries the whole logged-in identity, not a scoped grant: every org, every stack, every permission that user holds. Pasting one into a shell, a script, or an env file spreads it into history, logs and process lists, and it stays valid until that session ends. Treat it as a break-glass credential: **prefer OAuth, don't ask for a session token before OAuth has actually failed, never persist it, never echo it, never commit it.** If you must use one, scope it to the single call and discard it.

**Capability varies by environment and is still rolling out**: some non-prod data centers accept OAuth Bearer for `/v1/projects`. A fresh NA prod stack was observed rejecting it. So don't hardcode either assumption: attempt OAuth, branch on the signatures above. See [`provision-studio-project`](provision-studio-project.md) step 10.

**No delivery/preview-token tool, no stack-create, no Live-Preview-enable tool.** All stay raw HTTP (`provision-studio-project` steps 3, 5, and stack-create).

> **The split:** Contentstack MCP = auth (incl. org) + CMA execution, **prod only**. Playwright MCP = stack-key discovery from the UI. Raw HTTP = Studio API + tokens + LP-enable + stack-create. Non-prod works through the MCP too, via base-URL overrides (Step 0). No single tool does all of it.

<a id="non-prod-auth-path"></a>

### Non-prod data centers: the one clear path

The MCP's OAuth login is unreachable here because its authorize host cannot be overridden. API calls can still use explicit host overrides, so choose the fixed fallback per operation below:

| Operation | Non-prod path | Notes |
|---|---|---|
| **CMA**: content types, entries, assets, publish | Raw `curl` against the non-prod CMA host with `-H "$CS_AUTH"`: **OAuth Bearer by default**. A session `authtoken` only as the last rung ([`authenticate-cma`](authenticate-cma.md)) | **Use `curl`, not Python.** `urllib`/`requests` fail with `SSLCertVerificationError`, the non-prod chain isn't in Python's CA store. `curl` reads the system keychain. See [`author-composition-via-api`](author-composition-via-api.md) § Common pitfalls |
| **Studio API**: `/v1/projects` register/configure | `csdx` with OAuth, or raw `curl` with a session authtoken against **`<env>-composable-studio-api.<non-prod-domain>`** (prod is `composable-studio-api.contentstack.com` + regional variants, see [`install-studio`](install-studio.md) § host table) | **Superseded:** an earlier version of this row said prod rejects OAuth Bearer. Runtime-verified since: `GET /v1/projects` on `composable-studio-api.contentstack.com` with `Authorization: Bearer <oauth>` + `organization_uid` returns **200** with the project list, and a non-prod data center accepts read+write on current builds. **OAuth is the first rung on prod too**. See [`authenticate-cma`](authenticate-cma.md). Still branch on the response rather than assuming, and pair Bearer with `organization_uid`, never a stack `api_key` |
| **`csdx` against a non-prod DC** | Set the custom region, then pass the DC's own OAuth app credentials as env vars, see § OAuth on a custom region below | The built-in app ids are per-DC, runtime-confirmed on a non-prod data center, where csdx's own default id fails the authorize step with **"App with id `<id>` not found"** |
| **Stack API key discovery** | Playwright MCP against the non-prod web app, or ask the user | No CLI/MCP path |
| **Anything the MCP would have done** | The equivalent raw-`curl` step in the owning skill | Every provisioning skill keeps a full curl fallback. Nothing is MCP-only |

<a id="oauth-on-a-custom-region"></a>

#### OAuth on a custom region: three things must line up, and two of them you supply

OAuth apps are **registered per data center**. Ids from one data center do not exist on another. So authorizing against a custom region needs all three of:

| # | What | Prod | Custom region |
|---|---|---|---|
| 1 | **Authorize UI host** | Derived from the region automatically | Must be that DC's UI host, e.g. `https://<env>-app.<non-prod-domain>` |
| 2 | **OAuth app id** | Built in / fetched automatically | **User supplies it**: it's registered on that DC only |
| 3 | **OAuth client id** | Built in / fetched automatically | **User supplies it** |

**Never guess, reuse, or hardcode ids.** They are per-DC, they rotate, and they belong in the user's environment. **Always read them from env vars the user sets. Never write a concrete id into a skill, script, config, or commit.** Ask the user for their DC's values. The failure is unambiguous when the id is wrong: the authorize page returns **"App with id `<id>` not found"** (runtime-confirmed on a non-prod data center using csdx's own built-in default).

**`csdx` works, because it lets you set all three.** The region config supplies the UI host. The app credentials come from env:

```bash
OAUTH_APP_ID=<dc-app-id> \
OAUTH_CLIENT_ID=<dc-client-id> \
OAUTH_APP_REDIRECT_URL=http://localhost:8184 \
csdx auth:login --oauth
```

**The MCP: blocked on (1) at v0.9.0.** It exposes `CONTENTSTACK_OAUTH_APP_ID`, `CONTENTSTACK_OAUTH_CLIENT_ID` and `CONTENTSTACK_OAUTH_REDIRECT_URI` (note the different names from csdx), so items 2 and 3 are settable, but `applyRegion()` hardcodes `oauthBaseUrl = OAUTH_URLS[region].uiHost`, built from the 7 prod regions with **no env override**. Custom-region app credentials therefore get sent to a prod authorize endpoint, where that app doesn't exist. **So `--auth` cannot mint a token for a custom region**, and the `*_BASE_URL` overrides don't help: they redirect API calls, not the login.

Two ways to use the MCP on a custom region anyway:

- **Management token instead of OAuth**: CMA accepts `--management-token` / `CONTENTSTACK_MANAGEMENT_TOKEN` in place of `--auth`. Combine with `CONTENTSTACK_CMA_BASE_URL` / `CDA_BASE_URL` for the DC. This is the working path today.
- **Skip the MCP** for that work and use `csdx` (OAuth, as above) or raw `curl`.

**Worth filing upstream:** every other piece is already overridable. One `CONTENTSTACK_OAUTH_UI_HOST` (or letting the region accept a custom endpoint set) would make the MCP work on non-prod.

**Decide the host before the first call.** Switching a half-provisioned flow from prod to non-prod means re-checking auth on every step: the token types, the working header, and the SSL behavior all differ.
