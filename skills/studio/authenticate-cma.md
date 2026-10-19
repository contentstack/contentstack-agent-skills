---
name: authenticate-cma
---

## When to use

Canonical home for **how any Studio skill authenticates an API call**: CMA (`api.contentstack.io/v3`), the Studio API (`/v1/projects`), and the compositions service. Read it before writing a `curl`, a provisioning script, or any tooling that talks to Contentstack.

Phrases: "which token do I use", "OAuth instead of authtoken", "401 error_code 105", "422 Stack not found", "authtoken is not valid", "do I have to paste a token", "we're logged in with OAuth", "management token vs authtoken", "the MCP is authenticated, use that".

Do NOT use for: installing the MCP ([`install-contentstack-mcp`](install-contentstack-mcp.md)), or minting **delivery/preview** tokens, which are a different credential class entirely ([`enable-visual-experience`](enable-visual-experience.md)).

# Authenticating Contentstack API calls: OAuth first, session token last

Before reading a credential store for HTTP work, check the active host's callable tools per [`install-contentstack-mcp`](install-contentstack-mcp.md). Use read-verified MCP operations where supported. This skill resolves credentials for remaining HTTP operations; successful OAuth login does not establish MCP readiness. A missing readiness flag triggers discovery, not automatic HTTP fallback.

**Default assumption: there is no session `authtoken`, and none is coming.** The user authenticates once via OAuth (the MCP's `--auth`, or `csdx auth:login --oauth`) and every skill runs on that. A skill whose only documented path is `-H "authtoken: <paste-one>"` is broken for the normal case: it stops the run to demand a credential the user was never going to produce.

## The credential ladder: verified from the CLI's own resolver

Not inferred. This is `feature-status/build-auth-headers.js` in `@contentstack/cli-utilities`, the resolver every `csdx` command runs through, plus `http-client/oauth-decorator.js`:

| Priority | Credential | Headers it sends | Scope pairing |
|---|---|---|---|
| 1 | **Management token** | `Authorization: <token>` (**no `Bearer` prefix**, that is the API contract) | + `api_key` (stack-scoped) |
| 2 | **OAuth access token** | `authorization: Bearer <access_token>` | + `organization_uid` |
| 3 | **Session authtoken** | `authtoken: <token>` | + `organization_uid` |
| 4 | **Session authtoken** | `authtoken: <token>` | + `api_key` |

`oauth-decorator.js` confirms the same split at the transport layer: `authorisationType === 'OAUTH'` produces `authorization: Bearer …`, and `'BASIC'` produces `authtoken: …`. **So the whole CMA surface that `csdx` drives (content types, entries, assets, publish, export/import) is reached with OAuth Bearer every day.** OAuth is the CLI's preferred rung, above the session token, not a fallback.

## The `$CS_AUTH` convention: what every snippet in this pack uses

Resolve auth **once**, then every call is credential-agnostic:

```bash
# Pick the first that applies. Never prompt for a session authtoken before OAuth has been tried.
CS_AUTH="authorization: Bearer $CS_OAUTH_ACCESS_TOKEN"   # 1. OAuth  (+ CS_SCOPE below)
# CS_AUTH="Authorization: $CS_MANAGEMENT_TOKEN"          # 2. management token — NO "Bearer"
# CS_AUTH="authtoken: $CS_AUTHTOKEN"                     # 3. session token — last resort only

CS_SCOPE="organization_uid: $CS_ORG_UID"   # org-scoped calls (Studio /v1/projects, OAuth generally)
# CS_SCOPE="api_key: $CS_API_KEY"          # stack-scoped calls (CMA v3 content operations)

curl -s -H "$CS_AUTH" -H "$CS_SCOPE" "https://api.contentstack.io/v3/content_types?limit=100"
```

Stack-scoped CMA content calls take `api_key`. Org-scoped calls take `organization_uid`. **Sending `api_key` where the endpoint wants the org is the `422 error_code 21` "Stack not found" signature**: the auth was accepted, the scope was wrong. That error means "fix the scope header", not "OAuth is unsupported here".

## OAuth access tokens expire: refresh before concluding anything

`csdx` calls `compareOAuthExpiry()` **before every single request** and silently refreshes via the stored refresh token. A raw `curl` does none of that. So a token that worked an hour ago returns **401** now, and the 401 is indistinguishable from "this endpoint rejects OAuth".

**Never conclude an endpoint doesn't support OAuth from one 401.** Refresh first, then retry. Only a fresh token's failure is evidence about the endpoint.

**`error_code 39` does not mean "switch credential class".** The compositions service accepts OAuth Bearer. `39` means no credential arrived at all. See the matrix row below.

### The numbers, and the refresh call

| | Value | Source |
|---|---|---|
| Access-token lifetime | **59 minutes** from issue | `csdx` OAuth handler: `oauthDate + 59 * 60 * 1000` |
| Checked | before **every** request | `compareOAuthExpiry()` |
| Refresh endpoint | `POST {developerHub}/token` | `@contentstack/mcp`, `@contentstack/management` OAuth handler |
| Refresh body | **form-encoded**: `grant_type=refresh_token&client_id=…&refresh_token=…&redirect_uri=…` | `@contentstack/mcp` |
| `client_id`, `redirect_uri` | The MCP's public app defaults: `cGQZujH3Y_oYkf59`, `http://localhost:8184`. Env `CONTENTSTACK_OAUTH_CLIENT_ID` / `CONTENTSTACK_OAUTH_REDIRECT_URI` override them. Not secrets. Other MCP version: read them from its installed `dist` | `@contentstack/mcp` 0.9.0 constructor |
| Returns | `access_token`, `refresh_token`, `expires_in` | same |

### Refresh tokens rotate: so "read-only" credential sharing is impossible

`POST /token` **invalidates the refresh token you present** and issues a new one. That single fact kills the obvious-looking design:

> "I'll read another tool's stored session but never write to it, so I can't corrupt anything."

The moment that consumer refreshes, the pair still sitting in the other tool's store is **dead**. That tool's next refresh returns `400 {"message":["invalid_refresh_token"]}`, and the user has to log in again, caused by the consumer that was trying to be careful.

Measured exactly that way: an in-memory-only refresh succeeded once, and every later process failed against the now-stale store.

**Sharing a rotating credential means owning its rotation.** Either persist the new pair back to the store you read it from (atomically, preserving the other fields) or don't refresh that credential at all and tell the user to re-authenticate. There is no third option.

A `400 invalid_refresh_token` therefore means "something refreshed and didn't write back", not "your login expired".

**Recovering from it needs a human.** `npx @contentstack/mcp --auth` is an interactive TUI plus a browser login. No agent can complete it. Hand the user the command with the region already filled in. See [`install-contentstack-mcp`](install-contentstack-mcp.md) § `--auth` is an interactive TUI.

**The body is `application/x-www-form-urlencoded`, and `redirect_uri` is required.** A JSON body is rejected. This is easy to get wrong from the SDK's TypeScript alone: an implementation that sends JSON without `redirect_uri` fails on the first live expiry.

**Anything that runs longer than an hour must handle this.** Seeding 80 sections, backfilling thumbnails, uploading assets: all cross the boundary, and the failure lands mid-run with half the work done.

Two ways to survive it:

- **Re-mint before the run**: `csdx auth:login --oauth`, re-export the token. Fine for a short run. A coin-flip for a long one.
- **Refresh in-process**: hold the refresh token and `client_id`, refresh when stale, and retry once on a 401. Refresh tokens rotate, so after each refresh **write the new pair back** to the store it came from (atomically, keeping every other field).

**A bare `curl` in a loop has neither.** If a snippet in this pack is going to run more than a few minutes, drive it from a script that refreshes. Don't paste a token into a shell loop and hope.

## Failure signatures: what each response actually means

| Response | Cause | Fix |
|---|---|---|
| `401` `error_code 105` "authtoken is not valid" | OAuth token sent in the **`authtoken:`** header | OAuth goes in `authorization: Bearer`. Wrong header, not a wrong token |
| `401` after previously working | Expired OAuth access token, no refresh | Refresh the token, retry. Not an endpoint limitation |
| `401` `error_code 39` (compositions) / `48` (registered components) "Missing Contentstack auth token" | **Neither** credential reached the service: no `authtoken` and no `authorization: Bearer`. Both styles are accepted, so this does not mean "OAuth was refused" | Send one credential. Check the `Bearer ` prefix is present: a bare `authorization` value is read as a management token and never relayed |
| `401` "not logged in" | **Management token** sent as `authtoken:` | Management token goes in `Authorization:` **without** `Bearer`, paired with `api_key` |
| `422` `error_code 21` "Stack not found" | Auth accepted, scope header wrong or the app token can't resolve the stack | Pair OAuth with `organization_uid`. For stack-scoped calls send `api_key` |
| `403` `error_code 316` "You don't have the permission to do this operation" | The `api_key` belongs to a **different org** than the OAuth session. Auth was fine. Measured: same token, `200` on one stack, `403` on another | Re-auth against the owning org, or use an `api_key` from the token's org. `GET /v3/stacks` + `organization_uid` lists what it can reach |
| `200` + the change didn't apply | Wrong envelope or wrong key, **not an auth problem** | See [`enable-visual-experience`](enable-visual-experience.md): `PUT /v3/stacks` returns "Stack updated successfully" while ignoring an unrecognized payload |

That last row is the most expensive one in this table, because it looks like success.

## Which credential each service takes

| Service | OAuth Bearer | Session authtoken | Management token |
|---|---|---|---|
| CMA v3: content types, entries, assets, publish | **Yes**, verified, the path every `csdx` command uses | **Yes** | **Yes** (stack-scoped) |
| CMA v3: `/v3/stacks/settings` (Live Preview toggle) | **Yes**, verified for read AND write: `POST` returned `201` and the re-read showed `enabled: true` | **Yes**, verified | Untested |
| CMA v3: `/v3/stacks/delivery_tokens` (incl. `?create_with_preview_token=true`) | **Yes**, verified for read AND write: `POST` returned `201` with a 26-char `preview_token`, `DELETE` `200`. See [`provision-studio-project`](provision-studio-project.md) step 6 | **Yes**, verified | Untested |
| CMA v3: `POST /v3/environments` | **Yes**, verified, `201` | **Yes** | **Yes** |
| CMA v3: `GET /v3/stacks` (org-scoped) | **Yes**, verified: `200` with OAuth Bearer + `organization_uid` | **Yes** | - |
| Studio API: `/v1/projects` | **Yes**, verified: `GET` returns `200` + the project list with `organization_uid` | **Yes** | **No**, `401` "not logged in" |
| Compositions service (`/v1/projects/{uid}/compositions`) | **Yes**: the service forwards Bearer to the CMA | **Yes**, also accepted | **No** |
| Registered components (`/v1/projects/{uid}/registered-components`) | **Yes**: forwards Bearer to the component service | **Yes**, also accepted | **No** |

**"Untested" means nobody has measured that combination. "No" means measured and refused.** For an untested row: attempt OAuth, read the response, and record what you observe. Never pre-emptively downgrade to a session token because a row says untested. Treat "this endpoint doesn't do OAuth" as a claim to verify, not assume.

**Reads and writes both measured**, on a throwaway stack: `POST /v3/environments` returned `201`, `POST /v3/stacks/settings` returned `201` with the re-read confirming `enabled: true`, `POST /v3/stacks/delivery_tokens?create_with_preview_token=true` returned `201` carrying a 26-character `preview_token`, and `DELETE` returned `200`. OAuth Bearer covers the write surface, not just reads.

**And the failures along the way were all `422`, never `401`/`403`**: which is the useful part. A `422` means the credential authenticated and authorized, and the request was then rejected on **content**. Two real payload rules surfaced that way:

| Rejected payload | Response | Rule |
|---|---|---|
| `{stack_settings:{live_preview:{enabled:true}}}` | `422` `150`, `errors["settings.live_preview"]`: "You must activate the enable button and provide default URL and environment" | `enabled` alone is not enough: `default-env` (an environment **uid**) is required, so the environment must exist first |
| delivery-token `scope` with only an `environment` entry | `422` `141` "Delivery Token creation failed. Please try again.", real cause in `errors["scope.branch_or_alias"]` | add `{"module":"branch","branches":["main"],"acl":{"read":true}}` | <!-- style-lint: allow -->

Both are documented in [`enable-visual-experience`](enable-visual-experience.md) § Do it by API. **Read the payload from there rather than reconstructing it**: the top-level error messages are generic and the actionable detail hides in `errors`.

### Compositions and registered components take OAuth Bearer

OAuth-first applies to the entire pack, with no carve-out: the compositions and registered-components services accept `authorization: Bearer <access>` and forward whichever credential you presented:

```
authtoken: <session token>          -> forwarded as  authtoken: <session token>
authorization: Bearer <access>      -> forwarded as  authorization: Bearer <access>
```

Three rules apply:

- **The `Bearer ` prefix is mandatory.** Upstream reads a bare `authorization` value as a management token, so dropping the prefix fails as the wrong credential kind. A non-`Bearer` value is deliberately never relayed: the service does not pass on stack-scoped credentials it did not issue.
- **Send one credential, not two.** If both headers arrive, the authenticated principal picks the winner. Sending both and hoping is how a caller ends up authenticated as somebody else.
- **`39` and `48` mean "no credential at all".** Neither is evidence that OAuth was refused. Refreshing doesn't help, but sending a credential does.

Prefer attempting OAuth and reading the response over trusting a claim that it can't work.

### `403 error_code 316` is the org trap, not an auth failure

Measured: the same OAuth token returned `200` on one stack and `403` on another in the same run.

```
GET /v3/content_types   stack in the token's org      -> 200
GET /v3/content_types   stack in a DIFFERENT org      -> 403 error_code 316
                                                          "You don't have the permission to do this operation."
```

**OAuth sessions are org-scoped.** The MCP and `csdx` capture one org at login. An `api_key` from any other org returns `403 / 316`: the credential is perfectly valid, it just doesn't reach that stack. Confirmed twice, the second time with a **freshly refreshed** token in the same run: `200` listing stacks in the token's own org, `403 / 316` for both a stack and a stack-list in a different org. A fresh token failing on one org and succeeding on another is proof the problem is scope, not the credential. Reading this as "OAuth doesn't work" and escalating to a session token is the wrong move. The fix is to authenticate against the owning org, or use the right `api_key`. Confirm which org you're on with `GET /v3/stacks` + `organization_uid`, which lists exactly the stacks the token can reach.

### Probe: re-run this when you change org, environment or data center

```bash
# Read-only. Safe on any stack. Prints status codes only, never the token.
for ep in "content_types?limit=1" "stacks/settings" "delivery_tokens?limit=1"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' \
    -H "authorization: Bearer $CS_OAUTH_ACCESS_TOKEN" -H "api_key: $CS_API_KEY" \
    "https://api.contentstack.io/v3/$ep")
  echo "GET /v3/$ep -> $code"
done
```

`200` on all three means the writes authenticate too: same credential, same service. A `403 / 316` means the `api_key` is outside the token's org, **not** that OAuth failed. Anything else: check the signature table above before blaming OAuth.

## Where the credential actually lives: three separate stores

This is what makes "we're on OAuth" ambiguous in practice. The same login flow writes to a different place depending on who ran it:

| Who authenticated | Store | Read by |
|---|---|---|
| `csdx auth:login --oauth` | `~/Library/Preferences/@contentstack/…` (macOS) | `csdx` commands |
| `npx @contentstack/mcp --auth` | `~/Library/Application Support/ContentstackMCP/oauth-config.json` (`%LOCALAPPDATA%` on Windows, `~/.config` elsewhere) | the MCP server's tool calls |
| an env var you exported | `CS_OAUTH_ACCESS_TOKEN` | scripts and `curl` |

**Same OAuth flow, same credential class, three different homes, and none of them reads the others.** So "I authenticated the MCP" historically did not mean a script or a `curl` was authenticated.

A script closes that gap by preferring the env var, then falling back to **reading the MCP's store**, so one `--auth` covers scripts too. **Ask the user before reading or refreshing that stored session**: it is their credential, and refreshing it rotates the refresh token, which can sign the MCP server out (its next refresh fails with `400 invalid_refresh_token`) unless the new pair is written back. Refreshing means **writing the new pair back** to that file (atomic, other fields kept). The MCP's stored config also carries `organization_uid`, which is why org-scoped calls need no extra env var. Its `stack_api_key` is empty, which is why the stack key is still the one thing you supply.

**If the host blocks reading that file**, the login is fine: don't send the user to `--auth`. Say what was blocked and offer: approve the read, an allow rule `Read(<that path>/**)`, or `export CS_OAUTH_ACCESS_TOKEN`. Meanwhile use the MCP's tools where they cover the task.

The MCP refreshes on its own schedule: `token_issued_at + expires_in` (3600s), refreshed within **5 minutes** of expiry. Match that margin in your script, so neither hands out a token the other would have rotated.

## Why a session authtoken is the last rung, not a convenience

A session `authtoken` is a **full user-session credential**: every org, every stack, every permission that user holds, valid until the session ends. It isn't a scoped grant. Pasting one into a shell, a script or a `.env` leaves copies in shell history, process lists and logs.

So: attempt OAuth, read the actual response, and escalate only on an observed failure with a fresh token. If you do end up using one, scope it to the single call and discard it: never persist it, never echo it, never commit it.

## Acceptance

- [ ] No skill run asked the user for a session `authtoken` before OAuth was attempted and observed to fail **with a freshly refreshed token**.
- [ ] Every call pairs its credential with the right scope header: `organization_uid` for org-scoped, `api_key` for stack-scoped.
- [ ] A management token, if used, is sent as `Authorization: <token>` with **no** `Bearer` prefix.
- [ ] Any 401/422 was matched against the signature table before being reported as "OAuth isn't supported here".
- [ ] No session token was written to a file, an env var that outlives the call, or a commit.

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Reading another tool's OAuth store and refreshing "read-only" | Refresh tokens rotate: the refresh spends the stored one, so that tool's next refresh fails with `400 invalid_refresh_token` and the user must re-authenticate | Write the new pair back atomically, or don't refresh a credential you don't own |
| A long run on a token minted at the start | Access tokens last **59 minutes**. A seeding or backfill run crosses that and 401s with half the work done, and the 401 reads as an endpoint limitation | Refresh in-process and write the rotated pair back, or re-mint immediately before a short run |
| Hardcoding `-H "authtoken: …"` in a skill's snippet | The user authenticated with OAuth and has no session token: the run stops to demand a credential that isn't coming | Use the `$CS_AUTH` convention. Resolve auth once at the top |
| Prefixing a management token with `Bearer` | `401`. The API contract for management tokens is the bare token in `Authorization:` | No prefix. Only OAuth uses `Bearer` |
| Reading one `401` as "this endpoint rejects OAuth" | Access tokens expire and raw `curl` never refreshes. `csdx` refreshes before every call | Refresh, retry, and only then record a capability limit |
| Pairing OAuth with `api_key` on an org-scoped call | `422 error_code 21` "Stack not found": reads as a missing stack, is actually a wrong scope header | OAuth + `organization_uid` for org-scoped endpoints |
| Treating a `200` as proof the write landed | `PUT /v3/stacks` accepts an unrecognized envelope and reports success | Re-read the resource and assert the field changed |
| Asking for an authtoken "just in case" up front | Spreads a full-session credential for a run that would have worked on OAuth | Ask only after a fresh-token failure, and say which call failed and how |

## See also

- [`install-contentstack-mcp`](install-contentstack-mcp.md): how the OAuth session is established, and custom / private data-center constraints
- [`provision-studio-project`](provision-studio-project.md) § step 10: the `/v1/projects` ladder, applied
- [`enable-visual-experience`](enable-visual-experience.md): the stack-settings and preview-token writes, and the `200`-but-ignored trap
- [`complete-the-build`](complete-the-build.md): the audits that run over these endpoints
