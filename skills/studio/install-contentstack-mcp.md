---
name: install-contentstack-mcp
---

## When to use

Discover and verify the Contentstack MCP server before setup or provisioning API work. Prefer callable MCP operations. Install/configure the server when needed within the user's authorized scope. OAuth credentials and MCP execution are separate capabilities; `--auth` alone does not register tools in the current agent. See [`authenticate-cma`](authenticate-cma.md) for HTTP fallback credentials.

Run discovery on whole-project setup and API-provisioning flows, including when OAuth is already authenticated. Respect a prior decline. If tools are unavailable, record why and use supported OAuth HTTP operations where possible; do not claim MCP was used.

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Install Contentstack MCP: preferred API execution layer

> **MCP-first applies to supported callable operations.** For operations absent from the discovered tool schemas, a declined installation, an unsupported region, or a connection that cannot be recovered in this session, record the limitation and use the OAuth HTTP path. Never invent an MCP tool or assume a capability table from an older release is current.

## Discovery in the active host

1. Identify the host from the active tool surface. In Codex, search the available/deferred tool catalog for Contentstack tools. In Claude Code, use its MCP inventory. Do not use `claude mcp list` as evidence about Codex.
2. Inspect discovered tool schemas and run a read operation against the intended stack/region. Only a successful read establishes readiness. A saved OAuth file, CLI login success, or `CONTENTSTACK_MCP_READY` note alone does not.
3. If no tools are callable, inspect the current host's supported MCP configuration mechanism before registering the server. Resolve the final stack and region first. Use the host's documented restart/reconnect behavior; do not invent commands or edit another IDE's configuration.
4. After login or restart, repeat discovery and the read probe. Record supported operations and any remaining HTTP fallback reasons, without credentials.

The `claude mcp` commands below are Claude Code examples only. In other hosts, use their own configuration interface. CLI login commands shown with leading `!` use Claude's shell shortcut; omit `!` in an ordinary terminal.

## MCP-first credential boundary

For a whole-project Studio setup, run this discovery before asking the user to populate the app's `.env`:

1. Check the active host for callable Contentstack MCP tools.
2. If tools are unavailable, offer to register/configure the server using the host's documented mechanism, then ask the user to complete the interactive OAuth login if needed.
3. Run a read probe against the intended stack before claiming MCP readiness.
4. Use the discovered tool schemas to determine which values and operations MCP can supply.

MCP authentication and app runtime configuration are different. A successful MCP login does not write the app's `CONTENTSTACK_*` variables and does not prove that a Studio project is selected. The app still needs the runtime values required by [`install-studio`](install-studio.md), including the stack API key, delivery token, preview token, environment, locale mapping, and the selected Studio project's exact composition `contentTypeUid`.

Do not request every runtime value up front if MCP can discover or create it. Ask only for a stack API key when the MCP's registration has none ([`understand-contentstack-mcp`](understand-contentstack-mcp.md)), a Base URL/origin that belongs to the user's app, an explicit choice when multiple Studio projects exist, or any other value absent from the discovered tool/API responses. Never infer a Studio project, environment, locale mapping, or composition content type UID from the repository name or the default `compositions` convention.

The MCP server does not provide every Studio operation. At minimum, expect the Studio API project list/configuration (`/v1/projects`) and some token/Live Preview operations to require OAuth HTTP or the Studio UI. State that limitation and continue with the supported path; do not claim an MCP operation ran when no callable tool was discovered.

## What it does

Scope, and the things it deliberately does not cover, are in [`understand-contentstack-mcp`](understand-contentstack-mcp.md). Read that first if you are still deciding whether to install.

## Task

### Step 0: Region gate (run BEFORE anything else)

Do not offer the install, and do not run `--auth`, until the data center is settled. `DEFAULT_REGION` is `NA`, so "not set" silently means prod.

1. **Determine the DC**: [`analyze-project-fit`](analyze-project-fit.md) § 2b: Determine the data center. If that already ran this session, reuse its answer. Don't ask twice.

2. **Branch on the result:**

   | DC | What to set | Then |
   |---|---|---|
   | **Standard region**: one of the 7 | `--region <CODE>` or `CONTENTSTACK_REGION=<CODE>` (`NA`/`EU`/`AU`/`AZURE_NA`/`AZURE_EU`/`GCP_NA`/`GCP_EU`. `US`, `AWS_NA`, `AWS_EU`, `AWS_AU` also accepted) | Continue to Step 1 |
   | **Custom / private data center** (hosts supplied by Contentstack) | A valid region code **plus** base-URL overrides `CONTENTSTACK_CMA_BASE_URL=https://<your-cma-host>`, `CONTENTSTACK_CDA_BASE_URL=https://<your-cdn-host>` (add the other `*_BASE_URL` vars for tool groups you use). Set every host explicitly | **Not Step 1.** `--auth` offers the standard regions only and derives its authorize host from that pick, so it cannot mint a session here. Use raw `curl` with `$CS_AUTH`, or `csdx` with this DC's OAuth app credentials. See [`understand-contentstack-mcp`](understand-contentstack-mcp.md) § Custom / private data centers |
   | **Unknown / user unsure** | - | **STOP.** Print the block below. Do not install, do not run `--auth` |

   **Custom hosts are whatever Contentstack supplied to the user.** Use them verbatim. Never validate them against a list, never "correct" them to ones you've seen before, and never reuse hosts because they appeared in a previous session. The only fixed vocabulary is the 7 **region codes**.

3. **If the region can't be established, say this verbatim and stop:**

   > I can't set up the Contentstack MCP yet. I don't know which data center your stack is on, and the MCP defaults to **NA prod** when it isn't told. Authenticating now could point an OAuth session and every CMA write at the wrong data center, and the calls would succeed silently.
   >
   > Tell me one of these and I'll continue:
   > - the URL you open Contentstack at: `app.contentstack.com`, a regional host, or a custom host Contentstack supplied, or
   > - the region code directly: `NA`, `EU`, `AU`, `AZURE_NA`, `AZURE_EU`, `GCP_NA`, `GCP_EU`.
   >
   > For a custom / private data center, give me the hosts Contentstack supplied and I'll set `CONTENTSTACK_CMA_BASE_URL` / `CONTENTSTACK_CDA_BASE_URL` to them and check they resolve before logging in. A data-center name is not a region value: `--region <name>` makes the CLI exit with `Unknown region`.

3b. **Region vocabularies differ between tools. Don't copy one into the other blindly.** Runtime-verified:

   | Tool | Accepts | Rejects |
   |---|---|---|
   | **Contentstack MCP** | `NA`, `US`, `AWS_NA`, `AWS-NA`. `normalizeRegion` uppercases and converts `-` to `_`, so all four resolve to `NA` | a custom data-center name becomes `undefined` and the CLI exits |
   | **`csdx` Studio plugin** | **`AWS-NA` only**: its map is keyed with the hyphenated prefix | `NA`, which fails with "Region not configured" |
   | **`csdx` core** | both `NA` and `AWS-NA` (identical hosts) | - |

   So **`AWS-NA` is the one value that satisfies all three.** Set that and neither tool complains. See [`configure-studio` § Select the Studio project](configure-studio.md#select-the-studio-project) for the plugin side.

   **`--auth` is interactive.** `login()` calls `selectRegion()` unconditionally (an inquirer prompt with no flag or env bypass) then opens a browser. It needs a TTY and a browser, so you cannot run it for the user: hand them the command (Step 3).

4. **Verify the host BEFORE triggering the login.** A confirmed answer is not a correct answer. A prefix from another environment, or a typo, produces a hostname that doesn't exist. Probe it unauthenticated. You are testing that the host resolves and a Contentstack API answers, not that you have access:

   ```bash
   # Custom DC: the CMA host Contentstack supplied. Standard region: the region's CMA host.
   curl -sS -o /dev/null -w "%{http_code}\n" --max-time 10 \
     "https://<your-cma-host>/v3/environments"
   ```

   | Result | Meaning | Action |
   |---|---|---|
   | `401` / `412` | Host exists and Contentstack is answering, it's rejecting you for missing auth, which is exactly right at this stage | Host is good; resume the Step 0 branch you picked |
   | `000` / DNS or connection error | **That host does not exist.** Almost always a wrong or mistyped host | Do NOT log in. Tell the user the exact hostname you tried, say it didn't resolve, and ask them to confirm the host from their Contentstack URL |
   | `200` | Unexpected without auth; note and continue | Same |

   Only after this probe passes do you install, and on a standard region hand the user `--auth`. Confirming the region then authenticating against a nonexistent host wastes an OAuth round-trip and, worse, silently falls back to prod for anything you forgot to override.

5. **Record the resolved region + any overrides** and reuse them in the `claude mcp add` config (Step 4). The same values must be present there, not only in your shell. An override that lives only in your shell means the MCP server process starts with prod defaults.

### Step 1: Check if already installed — in THIS host, not by reflex

Run § Discovery in the active host first. The command below is the **Claude Code** form only:

```bash
claude mcp list | grep -i contentstack
```

In Codex or any other host, that command is not the inventory and its absence is not evidence: search the active tool catalog for Contentstack tools instead. Treating an empty `claude mcp list` as "not installed" on a non-Claude host is how an already-connected server gets re-offered and reconfigured.

If Contentstack tools are present in whichever inventory applies, perform the read probe from the discovery section. Skip installation only after readiness is established, and skip **Step 2 entirely** — its offer is written for a host where nothing is installed.

### Step 2: Offer (don't push) — only when discovery found nothing callable

Tell the user verbatim:

> The Contentstack MCP isn't installed. It's optional: provisioning works via curl, and `csdx auth:login --oauth` gives the same OAuth credential either way, so declining doesn't mean pasting a token. If you do install it (~2 min), you log in once via browser OAuth, and CMA steps (create CTs, entries, assets, publish) run as tool calls instead of curl. One heads-up: your login captures the org automatically, but you still supply the **stack API key** once. (This offer is for the standard regions; custom / private data-center logins go through `csdx`.) Registering a Studio project (`/v1/projects`) has no MCP tool. I'll try your OAuth token there first and only ask for anything else if the API rejects it. Want me to install it? <!-- style-lint: allow -->

- **Yes**: go to Step 3.
- **No / not now**: reply `Got it — I'll use curl for provisioning this session, authenticating with your OAuth token (csdx auth:login --oauth if it isn't set up yet).` Stop. Do not re-prompt this session.
- **Tell me more**: expand the "What it does" section, then re-ask.

### Step 3: Authenticate (OAuth)

`--auth` walks **three arrow-key TTY menus in sequence** (`Select an action → Authorization`, then `Authorization actions → Login`, then `Select your Contentstack region → <region>`) and THEN prints the OAuth URL + calls `open()` to launch the browser. There is **no org-picker menu**: the org comes from your Contentstack login's default org. To target a different org, **switch your active org in the Contentstack web UI before logging in**. This is the ONLY way. (`CONTENTSTACK_ORGANIZATION_UID` does NOT help: the MCP takes the org from the OAuth token, not that env var, so it has no effect on CMA auth.)

**The user runs it in their own terminal.** It needs a TTY and a browser, so you cannot run it for them. Hand them the command with the resolved region **in** it (the `!` prefix gives a real TTY in Claude Code; omit it in an ordinary terminal):

```
! CONTENTSTACK_REGION=<resolved-region> npx @contentstack/mcp --auth
```
They arrow through Authorization, then Login, then their region, and log in. The CLI's `localhost:8184` callback finishes it (`Authentication completed successfully`). Wait for them to confirm.

Either way, tokens are saved locally and auto-reused. The region + org are stored in the session.

> **After authentication: select the Studio project before doing project-scoped work.** An org usually has several, and the wrong one fails silently (empty compositions list, empty Sections panel). See [`configure-studio` § Select the Studio project](configure-studio.md#select-the-studio-project). List them, confirm which when there's one, ask when there are several, and check the project's connected stack matches the app's.

### Step 3c: Tokens last 59 minutes. Check expiry before diagnosing any auth failure.

**Runtime-verified.** `--auth` stores `expires_in: 3600`; treat the access token as valid for **59 minutes** (tooling refreshes a minute early). A token from an earlier session is therefore almost always dead, and the failure does not say so:

| What you see | What it actually means |
|---|---|
| **401** `error_code 105`, "The provided access token is invalid or expired or revoked" | Usually just **expired**. Reads exactly like a wrong credential or wrong header, which is the trap |
| **403** on the CMA with a fresh token | Token is fine. That **stack is outside the OAuth'd org**. Different problem, different fix: switch the active org and re-auth, or use a stack in this org |
| **200** | Working. OAuth `Bearer` **is** valid for the CMA, verified with a fresh token |

**Check expiry FIRST, before concluding anything about headers, schemes or scopes.** This reads the MCP's stored session, so **ask the user first**. The snippet prints only the expiry, never the token:

```bash
node -e '
const os=require("os"),p=require("path"),fs=require("fs");
const f=p.join(os.homedir(),"Library/Application Support/ContentstackMCP/oauth-config.json"); // macOS
const c=JSON.parse(fs.readFileSync(f,"utf8"));
const expiresAt=c.token_issued_at+c.expires_in*1000;
console.log(Date.now()>expiresAt
  ? "EXPIRED "+Math.round((Date.now()-expiresAt)/60000)+" min ago — re-run --auth"
  : "valid for "+Math.round((expiresAt-Date.now())/60000)+" more min");'
```

Config location: `~/Library/Application Support/ContentstackMCP/oauth-config.json` (macOS), `~/.config/ContentstackMCP/` (Linux), `%LOCALAPPDATA%\ContentstackMCP\` (Windows).

**On expiry, say so plainly and re-authenticate. Don't debug the wrong layer.** Tell the user verbatim:

> Your Contentstack session expired. The MCP's access token only lasts 59 minutes, and yours was issued earlier. Nothing is misconfigured. I'll re-run the login. You'll just need to complete the browser step.

Then hand them the Step 3 command again. A `refresh_token` is stored alongside the access token, but a raw `curl` won't use it. Re-running `--auth` is the reliable path.

**This is the single most misleading failure in the whole flow.** An expired token produced a 401 that looked like "OAuth doesn't work for the CMA", a wrong conclusion that survived until the expiry was checked. **Any 401 on a Contentstack API: check the clock before you touch the credential.**

### Step 4: Register the MCP server

**claude-code CLI:**
```bash
claude mcp add contentstack -e GROUPS=cma,cma-extended -e CONTENTSTACK_REGION=<resolved-region> -- npx -y @contentstack/mcp
```

`<resolved-region>` is the Step 0 region (`NA` for prod NA, etc.). **Pin it explicitly, see the callout below.** Omitting it lets a stray ambient value crash the server.

**Claude Desktop / Cursor / VS Code (JSON config):**
```json
{
  "mcpServers": {
    "contentstack": {
      "command": "npx",
      "args": ["-y", "@contentstack/mcp"],
      "env": { "GROUPS": "cma,cma-extended", "CONTENTSTACK_REGION": "<resolved-region>" }
    }
  }
}
```
Config locations: Claude Desktop (macOS) `~/Library/Application Support/Claude/claude_desktop_config.json` · Cursor `~/.cursor/mcp.json` · VS Code extension MCP panel. Restart the IDE / `claude` session so the server registers.

> `GROUPS=cma,cma-extended` enables the write tools the provisioning skills need. Add `cda` only if a skill needs published-content reads. Do NOT set a `CONTENTSTACK_MANAGEMENT_TOKEN` when using OAuth. The stored session is the credential.

> **Pin `CONTENTSTACK_REGION` in the add config: the MCP inherits your shell environment.** The stdio server inherits the ambient env. If you're in a repo whose `.env` (or your shell) sets `CONTENTSTACK_REGION` to a non-standard value (a custom data-center name), the server reads THAT instead of your OAuth region and **throws `Unknown region "<x>"` at startup**, so `claude mcp list` shows `✘ Failed to connect — Connection closed` even though your OAuth session is valid and you never passed a bad region. This is the single most common "the MCP won't connect" cause on a machine that also runs an app against a custom / private data center. `-e CONTENTSTACK_REGION=<resolved-region>` (CLI) or the `env` block (JSON) overrides the stray value. Diagnose via the connection log: `~/Library/Caches/claude-cli-nodejs/<project-path>/mcp-logs-contentstack/`. The newest `.jsonl` prints the exact `Server stderr: Error: Unknown region …`. Pin `CONTENTSTACK_API_KEY` the same way for the same reason once the target stack is resolved (Step 5).

### Step 5: Choose the target stack (a loop of new-or-existing, then permission, then recover)

The MCP operates on ONE stack (`CONTENTSTACK_API_KEY`), which **MUST belong to the OAuth'd org** (Step 3's captured `organization_uid`). A key from another org fails the smoke test (Step 6). Run this loop. It exits only when an existing key is supplied OR a new stack is created successfully.

**Q1, ask after EVERY org selection** (first login AND after any "new org" re-auth below): "Create a new stack, or choose an existing stack?"

- **Choose existing stack**: the user supplies an `api_key` (from [`install-playwright-mcp`](install-playwright-mcp.md) Step 5b `CS_RECENT_STACK_API_KEY`, or pasted). Confirm it's in the OAuth'd org, then **go to "Set the key" (loop exit).**

- **Create a new stack**: the MCP has **no stack-create tool**, so use raw CMA `POST /v3/stacks` (header `organization_uid: <org>`, auth = OAuth access_token as `Bearer`; a session authtoken only per the [`authenticate-cma`](authenticate-cma.md) ladder (a freshly refreshed OAuth token observed to fail, risk explained, user agreed). Body `{ stack: { name, master_locale: "en-us" } }`). Confirm name + org first (real mutation). **Always attempt it: the create IS the permission check.** Branch on the response:
  - **HTTP 201**: capture `api_key`, then **go to "Set the key" (loop exit).**
  - **HTTP 403, `error_code 316`, `"You don't have the permission to do this operation."`** (verified): the user lacks stack-create rights in this org. Do NOT crash. **Q2 (ask: "No permission to create here) choose an existing stack, or a different org?"** (only these two. Admin-rights is an out-of-band footnote):
    - **Choose existing stack**: the user pastes `api_key`, then **go to "Set the key" (loop exit).**
    - **Choose different org**: **re-run Step 3, the browser re-opens.** Before logging in, the user switches their **active org** (Contentstack top-left switcher) to one where they can create (there's no in-flow org-picker, the login captures the active org). New org captured, so **loop back to Q1** (re-ask new-vs-existing for the new org). Repeat until exit.

**Set the key** (loop exit): the server was registered keyless in Step 4, and **`claude mcp add` errors if the name already exists**, so **remove, then re-add** with the key (CLI), or edit the `env` block directly (JSON config), then restart and go to Step 6:

```bash
claude mcp remove contentstack
claude mcp add contentstack -e GROUPS=cma,cma-extended -e CONTENTSTACK_REGION=<resolved-region> -e CONTENTSTACK_API_KEY=<blt...> -- npx -y @contentstack/mcp
```

For multi-stack work in one session, repeat this remove-then-re-add when switching stacks.

> **Why a restart is needed, and how to have only ONE.** The stack is bound to `CONTENTSTACK_API_KEY` **at server-process start**. There is **no hot-reload** (changing the env on a running process has no effect), **no per-call stack override** (the tools take `branch`, not an `api_key`, verified), and **no `claude mcp reconnect/restart`** subcommand (only add/remove/list/get/login/logout). So changing the target stack ALWAYS requires the server to respawn = one session restart. This is a Claude Code + MCP limitation, not something this skill can auto-fix. **To keep it to exactly one restart: finish the Step 5 loop and resolve the FINAL stack BEFORE the restart, then register + restart once, never re-register mid-build.** Switching to a different stack later is one restart each. If you genuinely cannot restart (long continuous flow), **provision via raw `curl` + the OAuth Bearer token instead**: no MCP, no restart, at the cost of not using the MCP tools.

### Step 6: Smoke test

After a **session restart** (so the MCP's tools load into the agent's toolset), call a read tool: `get_all_content_types` (or `get_all_environments`) against the configured stack. Pass = returns real CT/env data.

**Fail mode: `MCP error -32603: … Cannot read properties of undefined (reading 'data')`.** The server crashed on an undefined CMA response (no clean 401/403). Most often a **stale OAuth token, so re-auth (Step 3) for a fresh one** (the actual fix in testing). Otherwise the stack is in the wrong org/region, or is on a custom / private data center. See the `-32603` and wrong-org rows in Common pitfalls for the full triage.

Note `claude mcp list` showing `✔ Connected` only means the server process started. It does NOT confirm CMA calls work. The tool call is the real test.

### Step 7: Write the session flag

Record an in-conversation note downstream skills read. Get the org by reading `organization_uid` from the stored session (`~/Library/Application Support/ContentstackMCP/oauth-config.json`): **ask the user before reading it**, extract only that field, and never print the token. **Use the exact flag names the provisioning skills + the Playwright hook already consume** (`CS_RECENT_STACK_API_KEY`, `CS_ACTIVE_ORG`). A differently-named key is never read:
```
CONTENTSTACK_MCP_READY=true
CS_MCP_REGION=<region picked in --auth>
CS_ACTIVE_ORG=<organization_uid from the OAuth token>
CS_RECENT_STACK_API_KEY=<blt...>
```
Downstream skills check `CONTENTSTACK_MCP_READY` and read `CS_RECENT_STACK_API_KEY`. If absent they fall back to curl authenticated with the **same OAuth token**, not to a pasted session token.

### Step 8: Tell the user what's now automated

Print:
```
✅ Contentstack MCP installed + authenticated.

Runs as tool calls now (no curl, no pasted authtoken):
  • provision-studio-stack       — global fields, CTs, entries, asset dedupe + publish
  • provision-studio-project     — compositions CT create + environment create
  • author-composition-via-api   — entry create/update + publish

STILL raw HTTP (not in MCP scope) — same OAuth credential, sent as `Authorization: Bearer`:
  • provision-studio-project     — /v1/projects (Studio API), delivery+preview token, enable Live Preview, stack-create
  • provision-studio-stack       — asset binary UPLOAD (no MCP tool) + the CDA verify (delivery-host read)
  • stack API key                — you supply once (org is auto-captured by the login; MCP can't enumerate stacks)
  • anything on a custom / private data center — raw HTTP with explicit hosts; MCP OAuth login is unavailable
```

## Inputs needed from the user

1. `ide`: picks the config path.
2. `region`: the DC the stack lives in (drives the Step 3 region-menu selection). Must be one of the 7 standard regions.
3. `stackApiKey`: the target stack (in the OAuth'd org). From Playwright MCP's `CS_RECENT_STACK_API_KEY` or pasted once. Org is NOT an input. It's auto-captured by the login.
4. `existing vs new stack`: Step 5 branch.

## Acceptance

- [ ] Target stack confirmed on a **standard region** (not a custom / private data center) BEFORE offering.
- [ ] User offered the recommendation in non-pushy framing, with the standard-regions-only + "you supply the stack key" caveats stated.
- [ ] If declined: no further prompts this session.
- [ ] If accepted: `claude mcp list` shows `contentstack`. `--auth` completed (browser OAuth, region selected, org auto-captured).
- [ ] Stack key resolved (existing pasted, or new stack created) AND it belongs to the OAuth'd org.
- [ ] Smoke test (`get_all_content_types` / `get_all_environments`) returns real data, NOT just `✔ Connected`. On the `-32603 …'data'` crash, re-auth for a fresh token and retry.
- [ ] Session note written: `CONTENTSTACK_MCP_READY=true`, region, org, stack API key.
- [ ] User told which provisioning steps run as tools vs stay raw HTTP.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Passing `--region <name>` (a custom data-center name as a region) | Not a region value. `normalizeRegion` returns undefined and the CLI exits with `Unknown region` | Pass a **valid** region code and set the hosts explicitly: `CONTENTSTACK_CMA_BASE_URL` / `CONTENTSTACK_CDA_BASE_URL` -> the CMA / CDN hosts Contentstack supplied |
| Diagnosing a 401 as a wrong credential when the token has simply **expired** | Access tokens live **59 minutes**. The 401 text (`error_code 105`, "invalid or expired or revoked") gives no hint which. Sends you off testing headers and schemes that were never wrong | Check `token_issued_at + expires_in` first (Step 3c). If expired, tell the user the session expired and re-run `--auth` |
| Reading a **403** as an expired token | A fresh token returning 403 means the stack is outside the OAuth'd org, not an auth-lifetime problem | Switch the active org in the web UI and re-auth, or target a stack in the current org |
| Running `--auth` before the DC is settled | `DEFAULT_REGION` is `NA`, so an unset region silently authenticates against **NA prod**. The OAuth session and every CMA write land in the wrong data center and succeed | Run Step 0 first. Never `--auth` on an unknown DC |
| Region right, hosts left at defaults on a custom / private data center | Region alone cannot reach it: the map only produces standard-region endpoints | Set the `*_BASE_URL` override for every tool group you use, not just CMA |
| Smoke test crashes: `-32603 … Cannot read properties of undefined (reading 'data')` | Server got an undefined CMA response and didn't surface the real 401/403 | **Re-auth for a fresh token first** (the actual fix in testing). Else: stack not in the OAuth'd org, wrong region, or custom / private data-center stack |
| Expecting to paste `org_id` | The OAuth token auto-captures `organization_uid`, asking for it is redundant | Read it from the token. Only the **stack** key is a manual input |
| Stack `api_key` from a different org than the login | CMA can't read it, which produces the `-32603` crash above | Use a key in the OAuth'd org. Or re-auth into the owning org (switch default org first, there's no org-picker in `--auth`) |
| `POST /v3/stacks` (new-stack) returns **HTTP 403, `error_code 316`** `"You don't have the permission to do this operation."` | The user lacks stack-create rights in that org (verified against a real no-permission org) | Show the clear message (Step 5): get rights / switch org (re-auth) / use existing. Don't crash or retry blindly |
| Assuming it provisions the Studio project | `/v1/projects` (Studio API) is out of scope. Only CMA + related | Keep `provision-studio-project` steps 3/5/9 (LP-enable, tokens, project register) on raw HTTP |
| Asking for a session authtoken **before** trying OAuth on `/v1/projects` | A session authtoken is the whole user session, every org and stack, and often isn't needed: OAuth `Bearer` works for `/v1/projects` where the Studio API accepts app tokens | Send `Authorization: Bearer <oauth-token>` with the right scope header (`organization_uid` / `api_key`). Escalate only if that still fails with a **freshly refreshed** token. A 401 from sending OAuth in the `authtoken:` header, or a 422 "Stack not found", is a request bug, not grounds to escalate. Even then prefer `csdx auth:login --oauth` or the Studio UI, and explain the risk before asking for a session token |
| Sending the OAuth token as an `authtoken:` header | Wrong header for that credential class: 401 `error_code 105` | OAuth goes in `Authorization: Bearer`. `authtoken:` is only for session tokens |
| Expecting a delivery/preview-token tool | None exists ("requires manual setup") | Create tokens via raw CMA `POST /v3/stacks/delivery_tokens` (both env + branch scope) |
| Setting a management token alongside OAuth | Ambiguous credential. May target the wrong stack/region | With OAuth, omit `CONTENTSTACK_MANAGEMENT_TOKEN`. The stored session is the credential |
| `GROUPS` too narrow (`cma` only) | Some skills need CMA-extended (workflows/versions) | Register with `GROUPS=cma,cma-extended` |
| `--auth` dies instantly: `Error: User force closed the prompt with 0 null` | Run in a shell with **no TTY**. The arrow-key menus can't read input | Hand the user `! CONTENTSTACK_REGION=<resolved-region> npx @contentstack/mcp --auth` to run in their own terminal (Step 3) |
| MCP installed but not restarted | Tools don't appear. Skills silently fall back to curl | Restart the `claude` session / IDE after `claude mcp add`. MCP tool schemas load at session start |
| Assuming CMA works because `claude mcp list` shows `✔ Connected` | "Connected" only means the server process started, not that CMA calls succeed | Confirm with an actual read tool (Step 6), not the connection status |
| Session flag lost to context compaction | Downstream skill re-prompts for authtoken mid-flow | Re-run the Step 6 smoke test when a provisioning skill starts rather than trusting the flag indefinitely |

## See also

- [`install-playwright-mcp`](install-playwright-mcp.md): discovers `org_id` + stack API key from the UI. The complement this MCP can't do.
- [`provision-studio-project`](provision-studio-project.md): CT-create + env-create route through MCP. `/v1/projects` + tokens stay raw HTTP.
- [`provision-studio-stack`](provision-studio-stack.md): CTs, entries, assets, publish all route through MCP tools.
- [`author-composition-via-api`](author-composition-via-api.md): entry create + publish via MCP. The `ui`/`data_sources` shape is unchanged.
- Reference: `@contentstack/mcp` on npm · `contentstack.com/docs/agent-os/contentstack-mcp-server`.
