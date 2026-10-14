---
name: enable-visual-experience
---

## When to use

Enable Live Preview + Visual Experience at the stack level: prerequisite before any Studio / Live Preview / Visual Editor work. Without it, app installs silently fail.

Use as the FIRST step before `install-studio`, `install-live-preview`, `configure-studio`, or any Studio setup skill. Phrases: "enable Live Preview", "set up Visual Experience", "canvas is blank", "preview events not arriving". Also when `verify-setup` reports Layer 2 failing or `troubleshoot-canvas` finds canvas blank with no preview events. Not doable from CLI: click-through in the Contentstack web app, gates downstream skills.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Enable Visual Experience + Live Preview at the stack level

## Why this skill exists

Studio, Live Preview, and Visual Editor share **one stack-level checkbox**: `Stack → Settings → Visual Experience → General → Live Preview → Enable Live Preview`. When unchecked, every downstream piece works locally and then **silently fails**:

- The preview channel doesn't exist. Preview Tokens resolve to nothing
- The Studio canvas can't fetch content via the preview environment
- Visual Editor's inline editing doesn't render
- The `Preview URL` sub-tab is locked with: "Custom Preview URL Unavailable: You don't have permission to use a Custom Preview URL because Live Preview is disabled in the General settings."
- The top-nav `Visual Experience` link (which appears at the route `/visual-editor` when Live Preview is on) doesn't exist

> **Side effect verified live:** enabling Live Preview + clicking Save adds a top-level **`Visual Experience`** link to the main stack navigation (between Content Models and Publish Queue). Disabling + Save removes it. This is a useful sanity-check signal: if the top-nav link is missing after Step 1, the save didn't actually persist.

## Do it by API: this is automatable {#api-path}

> **Auth: OAuth first.** Snippets here write `-H "$CS_AUTH"`, resolved once per run. **Assume there is no session `authtoken`**: the user authenticates with OAuth (MCP `--auth` / `csdx auth:login --oauth`) and never pastes one. Resolution order, scope headers (`organization_uid` vs `api_key`), the expiry/refresh rule and the 401/422 signature table: [`authenticate-cma`](authenticate-cma.md). `<stack>`: MCP-registration key ([`understand-contentstack-mcp`](understand-contentstack-mcp.md)), user-confirmed.

Both the Live Preview toggle and the preview token are scriptable. Prefer this path. Fall back to the UI walkthrough when no CMA credential resolves (OAuth first; a session `authtoken` only as the last rung per [`authenticate-cma`](authenticate-cma.md), never as the reason to skip the API path).

**This changes stack settings: confirm first.** Tell the user which stack and environment, show the current `live_preview` block from the read, state the change, and get approval before the write.

### 1. Enable Live Preview: `POST /v3/stacks/settings`

Read first, merge the flag into the existing settings with `jq`, write the whole object back:

```bash
# requires: CS_AUTH (see authenticate-cma), STACK_API_KEY, CMA_HOST, ENV_UID, jq
SETTINGS="$(mktemp)"; trap 'rm -f "$SETTINGS"' EXIT

curl -s -H "api_key: $STACK_API_KEY" -H "$CS_AUTH" \
  "https://$CMA_HOST/v3/stacks/settings" > "$SETTINGS"      # → { "stack_settings": { … } }
jq '.stack_settings.live_preview' "$SETTINGS"                # show the before state; confirm with the user

jq --arg env "$ENV_UID" '{stack_settings: (.stack_settings
      | .live_preview = ((.live_preview // {}) + {enabled: true, "default-env": $env,
                          "default-url": (.live_preview["default-url"] // "")}))}' \
  "$SETTINGS" \
| curl -s -X POST -H "api_key: $STACK_API_KEY" -H "$CS_AUTH" \
    -H "Content-Type: application/json" \
    "https://$CMA_HOST/v3/stacks/settings" --data-binary @-
# → 201 Created, and it persists
```

**Send the FULL `stack_settings` object** with only the flag changed. Siblings (`visual_builder`, `discrete_variables`, `timeline`, `entries`, `stack_variables`) must survive the write, so read-modify-write rather than posting `live_preview` alone.

`default-env` takes an **environment uid**, so Step 2 below is settable in the same call.

### 2. Mint the delivery token and its preview token in one call

```bash
curl -s -X POST -H "api_key: <stack>" -H "$CS_AUTH" \
  -H "Content-Type: application/json" \
  "https://<cma-host>/v3/stacks/delivery_tokens?create_with_preview_token=true" \
  -d '{"token":{"name":"studio","description":"Studio + Live Preview","scope":[
        {"module":"environment","environments":["<env-name>"],"acl":{"read":true}},
        {"module":"branch","branches":["main"],"acl":{"read":true}}]}}'
# → 201, response.token.preview_token  (≈26 chars, "cs…")
```

Read one back later with `GET /v3/stacks/delivery_tokens/<uid>?include_preview_token=true`.

| Trap | What you see | Fix |
| --- | --- | --- |
| `PUT /v3/stacks {stack:{settings:{live_preview:{enable:true}}}}` | **200 OK, "Stack updated successfully."** and the setting does NOT persist: wrong endpoint, wrong envelope (`stack.settings` vs `stack_settings`), wrong key (`enable` vs `enabled`) | Use `POST /v3/stacks/settings` with the `stack_settings` envelope and `enabled` |
| `create_with_preview_token` placed in the request **body** | Token created, `preview_token` silently absent | It is a **query param** |
| Token creation on a branch-enabled stack without a branch scope | `error_code 141`, "Delivery Token creation failed. Please try again.". The real reason hides in `errors["scope.branch_or_alias"]` | Add `{"module":"branch","branches":["main"],"acl":{"read":true}}` to `scope` | <!-- style-lint: allow -->
| Reading LP state from `GET /v3/stacks?include_settings=true` and finding `{}` | That is genuinely "off": the field is readable, so **verify instead of asking the user** | - |

**Attempt OAuth Bearer first and branch on the response** ([`authenticate-cma`](authenticate-cma.md) § Which credential each service takes carries the probe). Whether a stack-scoped **management token** is accepted for the settings write is untested. If it 401s, fall back to the UI steps.

**Method note worth keeping:** this was believed impossible for two sessions because the wrong endpoint answered `200`. It was settled by opening the Network tab in DevTools while a human ticked the checkbox. When a CMA operation looks impossible, capture what the product's own UI calls before writing it off.

### After an API write, reload the UI before trusting your eyes

An already-open **Visual Experience** tab under **Settings** does NOT reflect a settings write made by API: the SPA holds the state it loaded with. Verified live: the API read said `enabled: true` while the open tab still showed the checkbox unchecked. A reload showed it checked, with the Default Preview Environment populated and the **`Visual Experience`** top-nav link present.

So confirm an API-driven enable in this order:

1. **Read it back**: call `GET /v3/stacks/settings` and read `stack_settings.live_preview.enabled`. This is the source of truth and it is instant.
2. Only then look at the UI, and **reload the page first**. A stale tab is the single most likely reason a working write looks broken.

The top-nav link is the cheapest human-visible signal: it appears when Live Preview is on, whether it was switched on by API or by checkbox, and disappears when it is off.

## Fallback: the UI walkthrough

Use this when the API path 401s with a **freshly refreshed** token (an expired OAuth token 401s identically, refresh before concluding anything), or no credential resolves at all. It is also what a human follows to verify what the API did.

## Task

**Run the [API path](#api-path) first, then route.** Do not walk a human through work you have already done. That is the failure this routing exists to prevent.

| Step | Covered by the API path? | What to do |
| --- | --- | --- |
| 1. Enable Live Preview | Yes, `POST /v3/stacks/settings` | **SKIP the walkthrough.** Confirm by read-back: `live_preview.enabled === true`. Do not ask for a "done" |
| 2. Default Preview Environment | Yes, the same call with `default-env: <env-uid>` | **SKIP.** Confirm `live_preview["default-env"]` is non-empty |
| 3. Custom Preview URL | No, not API-settable (untested) | **Walk the human through it**, the only step that still needs one |
| 4. Preview Token | Yes, `POST …/delivery_tokens?create_with_preview_token=true` | **SKIP.** Confirm `token.preview_token` came back |
| 5: Summary | - | Always print it, stating which steps were done by API and which by hand |

So on the API path the human is asked for **one** thing (Step 3), not four. Announce what you did rather than asking them to verify it: "Live Preview is on, default preview environment is `development`, preview token minted, all by API. One thing left for you: the Custom Preview URL."

If no credential resolved at all, or a write failed with a **freshly refreshed** token, fall through to the full walkthrough below. **Then** (and only then) ask the user to explicitly type "done" after each step, and do NOT batch the checks.

### Step 1: Enable Live Preview at the stack level

**Skip this step if the API path already set it**: verify with `GET /v3/stacks/settings`, reading `live_preview.enabled`, and move on without asking for confirmation.

Tell the user verbatim:

> 1. Open the Contentstack web app and switch to **this stack**. Confirm by checking that the API key matches `{{stackApiKey}}` (in Settings, open Stack, then API Credentials, and read the Api Key).
> 2. Click **Settings** in the left nav.
> 3. In Settings, click **Visual Experience** (URL: `/settings/visual-experience`).
> 4. On the **General** sub-tab (the default landing), find the **Live Preview** section heading.
> 5. Check the **Enable Live Preview** checkbox.
> 6. You'll see a note below it: "As Live Preview is now locale-based, the default base URL is no longer required.". That's expected.
> 7. Click **Save** at the bottom of the page.
> 8. **Sanity check:** after Save succeeds, a new top-level link **`Visual Experience`** appears in the main stack navigation (between Content Models and Publish Queue). If you don't see it, the save didn't persist. Retry.
>
> Reply **"done"** once the checkbox is checked, Save is confirmed, and the top-nav link appears.

If the user reports the checkbox is grayed out, they lack the Settings role on the stack. Stop. Escalate to the stack owner / org admin.

### Step 2: Set the Default Preview Environment

**Skip this step if the API path already set `default-env`**: verify by read-back rather than asking.

Tell the user verbatim:

> 1. Still on the **General** sub-tab of **Visual Experience** in **Settings**, scroll to **Default Preview Environment** directly below the Enable Live Preview checkbox. (It's disabled until Step 1 is saved.)
> 2. The dropdown auto-populates from the **Environments** page in **Settings**: every environment in the stack appears as an option.
> 3. Select `{{previewEnvironmentName}}` (or whichever environment you use for previewing). **Don't pick `production`**: Live Preview reads draft content, which doesn't live in the production environment.
> 4. Click **Save**.
>
> If the dropdown is empty: in a new tab, open **Settings**, go to **Environments**, and create an environment named `{{previewEnvironmentName}}` first. Return to Visual Experience and refresh.
>
> Reply **"done"** with the env name you confirmed.

### Step 3: Set the Custom Preview URL on the Preview URL sub-tab

Tell the user verbatim:

> 1. On the **Visual Experience** page in **Settings**, click the **Preview URL** sub-tab. If it's locked with "Custom Preview URL Unavailable: You don't have permission to use a Custom Preview URL because Live Preview is disabled in the General settings," go back and re-do Step 1.
> 2. Turn the **Enable Custom Preview URL** toggle ON (helper text: "Build preview URLs that match your live website structure"). This is a separate toggle from the Enable Live Preview checkbox in Step 1.
> 3. Configure the **Base URL** section (required):
>    - **Alias**: pick a short name (e.g. `local`, `staging`, `prod`). Useful for multi-brand setups where one stack feeds multiple sites.
>    - **Pattern**: paste `{{canvasAppUrl}}` as the host pattern (e.g. `http://localhost:5173`).
>    - Use the **Insert** buttons below the Pattern field to add Contentstack's template placeholders if needed: `{{entry.title}}`, `{{taxonomy:brand}}`, `{{environment}}`, `{{locale}}`. **Use double-brace `{{ }}` syntax, not `${ }`**: Contentstack uses Handlebars-style, not JS template literals.
>    - Click **Add URL** if you want to add more aliases for additional environments.
> 4. Configure the **URL Path** section (required):
>    - One row per content type. Default path is `/{{entry.url}}`. Studio content types need prefixed rows, e.g. `/blog/{{entry.url}}`.
>    - Click **Add Path** to add per-CT overrides (e.g. blog posts at `/blog/{{entry.slug}}`, products at `/products/{{entry.sku}}`).
>    - Drag rows to reorder. Matching is top-to-bottom.
> 5. **Advanced Config** is collapsible. Leave it alone for the standard case.
> 6. Click **Save** at the bottom.
>
> Reply **"done"** with the Base URL alias name + pattern you set.

### Step 4: Generate the Preview Token on the Delivery Token

**Skip this step if the token was minted with `?create_with_preview_token=true`**: you already hold the value. Do not ask the user to create or paste one.

Tell the user verbatim:

> 1. In the left nav, open **Settings**, then **Tokens**, then **Delivery Tokens**.
> 2. Open the Delivery Token your app uses. The token must be scoped to a **Publishing Environment** that matches what you want to preview: `{{previewEnvironmentName}}` for the standard case (visible as a radio button under Publishing Environments on the token edit page).
> 3. On the token edit page, scroll past the Stack API Key and Delivery Token (read-only) fields. You'll see a button labeled **Create Preview Token** with helper text: "Live Preview relies on the Preview token. We strongly recommend using this token instead of a read-only Management token."
> 4. Click **Create Preview Token**.
> 5. After the click, the button **disappears** and a new **Preview Token (read only)** field shows up directly below the Delivery Token. The value starts with `cs` (e.g. `csxxxxxxxxxxxxxxxxxxxxxxxx`).
> 6. Copy the Preview Token value. This is what goes into your app's gitignored `.env.local` as `*_CONTENTSTACK_PREVIEW_TOKEN` (don't paste it into chat):
>    - Vite: `VITE_CONTENTSTACK_PREVIEW_TOKEN=<preview-token>`
>    - Next: `NEXT_PUBLIC_CONTENTSTACK_PREVIEW_TOKEN=<preview-token>`
>    - CRA: `REACT_APP_CONTENTSTACK_PREVIEW_TOKEN=<preview-token>`
>
> **Important:** there is **no delete / revoke button** for the Preview Token in this UI. Once you click Create Preview Token, the token exists for the lifetime of the Delivery Token. The only way to invalidate it is to delete the Delivery Token itself. So **only click it on the Delivery Token you intend to use for previewing.**
>
> Reply **"done"** when the Preview Token field is visible and you've copied the value.

### Step 5: Print the final summary

```
✅ Stack-level Visual Experience is now ready.

   Live Preview:           ENABLED (Settings → Visual Experience → General)
   Default Preview env:    <env name from Step 2>
   Custom Preview URL:
     Base URL alias:       <alias from Step 3>
     Base URL pattern:     <pattern from Step 3>
     URL Path default:     /{{entry.url}}  (plus prefixed per-CT rows)
   Preview Token:          generated on <delivery token name from Step 4>

Sanity-check signal: a top-level "Visual Experience" link should now
appear in the main stack nav.

Next:
  • Run `install-studio` (or `install-live-preview`) to wire the app side.
  • Run `verify-setup` after install to test all four layers end-to-end.
```

## Inputs needed from the user

1. `stackApiKey` (required).
2. `canvasAppUrl` (required): used in Step 3's Base URL pattern.
3. `previewEnvironmentName` (default `preview`): selected in Step 2, scopes the Delivery Token in Step 4.

## Acceptance

- [ ] **CSLP tags reach the DOM**: the SDK config sets `cslp: { appendTags: true }`, and a rendered component's root shows `data-cslp` with each bound field tagged too. Live Preview can be fully enabled and still not be editable if components drop these, see [`register-component` § The `studioAttributes` contract](register-component.md).
- [ ] User confirmed Step 1 (Enable Live Preview checked + Save clicked + top-nav `Visual Experience` link appeared)
- [ ] User confirmed Step 2 (Default Preview Environment selected, NOT production)
- [ ] User confirmed Step 3 (Enable Custom Preview URL ON, Base URL alias + pattern set, URL Path set, Save clicked)
- [ ] User confirmed Step 4 (Preview Token generated, value copied)
- [ ] Final summary printed with all captured values

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Skill skipped entirely | Most common Studio-setup failure. App installs cleanly, runtime silently broken. | Always run this skill first on a stack that has never used Live Preview |
| Enable Live Preview checkbox grayed out | User lacks Settings role on the stack | Stop. Escalate to the stack owner |
| Save clicked but top-nav `Visual Experience` link doesn't appear | The save didn't actually persist (sometimes happens on slow networks or with stale session) | Refresh the page, re-check the checkbox, click Save again |
| Default Preview Environment dropdown empty | No preview-only environment exists in the stack | Create one in Settings, then Environments, then New Environment (e.g. `preview`). Don't share with production. |
| Picked `production` as Default Preview Environment | Live Preview reads draft content, which doesn't exist in production | Pick a non-production environment (e.g. `preview`) |
| Preview URL sub-tab shows "Custom Preview URL Unavailable" | Step 1 wasn't saved | Go back to General, re-check Enable Live Preview, click Save, return to Preview URL |
| Used `${entry.uid}` or `${entry.url}` template syntax | Contentstack uses Handlebars-style `{{ }}`, not JS template literals `${ }` | Use the Insert buttons under the Pattern field, they emit the correct syntax automatically |
| No Preview Token visible on Delivery Token edit page | The token was never generated. Only the **Create Preview Token** button shows by default | Click the button. The token only exists after the click. |
| Tried to revoke / delete Preview Token after generation | There is NO revoke button in this UI | The Preview Token persists for the lifetime of the Delivery Token. To invalidate, delete the Delivery Token itself. |
| Created Preview Token on the wrong Delivery Token (e.g. one scoped to production) | The app's preview reads from this token's environment, so previewing the wrong env shows wrong content | Generate the Preview Token on the Delivery Token that's scoped to the preview environment. Each Delivery Token has its own Preview Token. |

## See also

- `install-studio`: calls this skill as **Step 0a**.
- `install-live-preview`: calls this skill first.
- `verify-setup`: Layer 0 confirms this skill was completed.
- `troubleshoot-canvas`: checks this first when canvas is blank.
