---
name: enable-visual-experience
description: "Enable Live Preview + Visual Experience at the stack level — prerequisite before any Studio / Live Preview / Visual Editor work. Without it, app installs silently fail."
allowed-tools: Read Grep Glob
---

## When to use

Enable Live Preview + Visual Experience at the stack level — prerequisite before any Studio / Live Preview / Visual Editor work. Without it, app installs silently fail.

Use as the FIRST step before `install-studio`, `install-live-preview`, `configure-studio`, or any Studio setup skill. Phrases — "enable Live Preview", "set up Visual Experience", "canvas is blank", "preview events not arriving". Also when `verify-setup` reports Layer 2 failing or `troubleshoot-canvas` finds canvas blank with no preview events. Not doable from CLI — click-through in the Contentstack web app; gates downstream skills.

# Enable Visual Experience + Live Preview at the stack level

## Why this skill exists

Studio, Live Preview, and Visual Editor share **one stack-level checkbox**: `Stack → Settings → Visual Experience → General → Live Preview → Enable Live Preview`. When unchecked, every downstream piece works *locally* and then **silently fails**:

- The preview channel doesn't exist — Preview Tokens resolve to nothing
- The Studio canvas can't fetch content via the preview environment
- Visual Editor's inline editing doesn't render
- The `Preview URL` sub-tab is locked with: *"Custom Preview URL Unavailable — You don't have permission to use a Custom Preview URL because Live Preview is disabled in the General settings."*
- The top-nav `Visual Experience` link (which appears at the route `/visual-editor` when Live Preview is on) doesn't exist

> **Side effect verified live:** enabling Live Preview + clicking Save adds a top-level **`Visual Experience`** link to the main stack navigation (between *Content Models* and *Publish Queue*). Disabling + Save removes it. This is a useful sanity-check signal — if the top-nav link is missing after Step 1, the save didn't actually persist.

> **Constraint:** Studio skills cannot toggle this checkbox via CMA — the user must do it in the Contentstack web app. This skill is purely instructional + confirmation-gated.

> **⛔ CMA boundary — DO NOT try to automate this via the API.** The endpoints look like they exist but **silently no-op**:
> - `PUT /v3/stacks { stack: { settings: { live_preview: { enable: true, … } } } }` returns **200 OK** with the new value echoed back, but a subsequent `GET /v3/stacks` shows `live_preview: {}` — the setting did NOT persist.
> - There is **no CMA endpoint** to create a Preview Token. The `Create Preview Token` button on the Delivery Token edit page is the only path.
>
> If you're an assistant that only has CMA access, you literally cannot enable Live Preview or mint a preview token on the user's behalf. **Don't waste cycles trying** — direct the user through the UI steps below and confirm each one. This is a platform boundary, not a skill gap.

## Task

Walk the user through 4 settings in order. **After each step, ask the user to explicitly type "done" (or equivalent confirmation) before proceeding to the next.** Do NOT batch the checks.

### Step 1 — Enable Live Preview at the stack level

Tell the user verbatim:

> 1. Open the Contentstack web app and switch to **this stack**. Confirm by checking that the API key matches `{{stackApiKey}}` (Settings → Stack → API Credentials → Api Key).
> 2. Click **Settings** in the left nav.
> 3. In Settings, click **Visual Experience** (URL: `/settings/visual-experience`).
> 4. On the **General** sub-tab (the default landing), find the **Live Preview** section heading.
> 5. Check the **Enable Live Preview** checkbox.
> 6. You'll see a note below it: *"As Live Preview is now locale-based, the default base URL is no longer required."* — that's expected.
> 7. Click **Save** at the bottom of the page.
> 8. **Sanity check:** after Save succeeds, a new top-level link **`Visual Experience`** appears in the main stack navigation (between Content Models and Publish Queue). If you don't see it, the save didn't persist — retry.
>
> Reply **"done"** once the checkbox is checked, Save is confirmed, and the top-nav link appears.

If the user reports the checkbox is greyed out → they lack the *Settings* role on the stack. Stop. Escalate to the stack owner / org admin.

### Step 2 — Set the Default Preview Environment

Tell the user verbatim:

> 1. Still on **Settings → Visual Experience → General**, scroll to **Default Preview Environment** directly below the Enable Live Preview checkbox. (It's disabled until Step 1 is saved.)
> 2. The dropdown auto-populates from **Settings → Environments** — every environment in the stack appears as an option.
> 3. Select `{{previewEnvironmentName}}` (or whichever environment you use for previewing). **Don't pick `production`** — Live Preview reads draft content, which doesn't live in the production environment.
> 4. Click **Save**.
>
> If the dropdown is empty: open a new tab → **Settings → Environments** → create an environment named `{{previewEnvironmentName}}` first. Return to Visual Experience and refresh.
>
> Reply **"done"** with the env name you confirmed.

### Step 3 — Set the Custom Preview URL on the Preview URL sub-tab

Tell the user verbatim:

> 1. On **Settings → Visual Experience**, click the **Preview URL** sub-tab. If it's locked with *"Custom Preview URL Unavailable — You don't have permission to use a Custom Preview URL because Live Preview is disabled in the General settings,"* go back and re-do Step 1.
> 2. Turn the **Enable Custom Preview URL** toggle ON (helper text: *"Build preview URLs that match your live website structure"*). This is a separate toggle from the Enable Live Preview checkbox in Step 1.
> 3. Configure the **Base URL** section (required):
>    - **Alias** — pick a short name (e.g. `local`, `staging`, `prod`). Useful for multi-brand setups where one stack feeds multiple sites.
>    - **Pattern** — paste `{{canvasAppUrl}}` as the host pattern (e.g. `http://localhost:5173`).
>    - Use the **Insert** buttons below the Pattern field to add Contentstack's template placeholders if needed: `{{entry.title}}`, `{{taxonomy:brand}}`, `{{environment}}`, `{{locale}}`. **Use double-brace `{{ }}` syntax, not `${ }`** — Contentstack uses Handlebars-style, not JS template literals.
>    - Click **Add URL** if you want to add more aliases for additional environments.
> 4. Configure the **URL Path** section (required):
>    - One row per content type. Default path is `/{{entry.url}}` — works if your entries have a `url` field.
>    - Click **Add Path** to add per-CT overrides (e.g. blog posts at `/blog/{{entry.slug}}`, products at `/products/{{entry.sku}}`).
>    - Drag rows to reorder; matching is top-to-bottom.
> 5. **Advanced Config** is collapsible — leave it alone for the standard case.
> 6. Click **Save** at the bottom.
>
> Reply **"done"** with the Base URL alias name + pattern you set.

### Step 4 — Generate the Preview Token on the Delivery Token

Tell the user verbatim:

> 1. Navigate to **Settings → Tokens → Delivery Tokens** (left nav).
> 2. Open the Delivery Token your app uses. The token must be scoped to a **Publishing Environment** that matches what you want to preview — `{{previewEnvironmentName}}` for the standard case (visible as a radio button under *Publishing Environments* on the token edit page).
> 3. On the token edit page, scroll past the *Stack API Key* and *Delivery Token* (read-only) fields. You'll see a button labelled **Create Preview Token** with helper text: *"Live Preview relies on the Preview token. We strongly recommend using this token instead of a read-only Management token."*
> 4. Click **Create Preview Token**.
> 5. After the click, the button **disappears** and a new **Preview Token (read only)** field shows up directly below the Delivery Token. The value starts with `cs` (e.g. `cs449d1c52e12fd4fea68ad6d0`).
> 6. Copy the Preview Token value — this is what goes into your app's `.env.local` as `*_PREVIEW_TOKEN`:
>    - Vite: `VITE_CS_PREVIEW_TOKEN=cs...`
>    - Next: `NEXT_PUBLIC_CS_PREVIEW_TOKEN=cs...`
>    - CRA: `REACT_APP_CS_PREVIEW_TOKEN=cs...`
>
> **Important:** there is **no delete / revoke button** for the Preview Token in this UI. Once you click *Create Preview Token*, the token exists for the lifetime of the Delivery Token. The only way to invalidate it is to delete the Delivery Token itself. So **only click it on the Delivery Token you intend to use for previewing.**
>
> Reply **"done"** when the Preview Token field is visible and you've copied the value.

### Step 5 — Print the final summary

```
✅ Stack-level Visual Experience is now ready.

   Live Preview:           ENABLED (Settings → Visual Experience → General)
   Default Preview env:    <env name from Step 2>
   Custom Preview URL:
     Base URL alias:       <alias from Step 3>
     Base URL pattern:     <pattern from Step 3>
     URL Path default:     /{{entry.url}}  (plus any per-CT overrides)
   Preview Token:          generated on <delivery token name from Step 4>

Sanity-check signal: a top-level "Visual Experience" link should now
appear in the main stack nav.

Next:
  • Run `install-studio` (or `install-live-preview`) to wire the app side.
  • Run `verify-setup` after install to test all four layers end-to-end.
```

## Inputs needed from the user

1. `stackApiKey` (required) — used to confirm correct stack.
2. `canvasAppUrl` (required) — used in Step 3's Base URL pattern.
3. `previewEnvironmentName` (default `preview`) — selected in Step 2, scopes the Delivery Token in Step 4.

## Acceptance

- [ ] User confirmed Step 1 (Enable Live Preview checked + Save clicked + top-nav `Visual Experience` link appeared)
- [ ] User confirmed Step 2 (Default Preview Environment selected — NOT production)
- [ ] User confirmed Step 3 (Enable Custom Preview URL ON, Base URL alias + pattern set, URL Path set, Save clicked)
- [ ] User confirmed Step 4 (Preview Token generated, value copied)
- [ ] Final summary printed with all captured values

## Common pitfalls

| Pitfall | Why it bites | Fix |
|---|---|---|
| Skill skipped entirely | Most common Studio-setup failure. App installs cleanly, runtime silently broken. | Always run this skill first on a stack that has never used Live Preview |
| Enable Live Preview checkbox greyed out | User lacks Settings role on the stack | Stop. Escalate to the stack owner |
| Save clicked but top-nav `Visual Experience` link doesn't appear | The save didn't actually persist (sometimes happens on slow networks or with stale session) | Refresh the page, re-check the checkbox, click Save again |
| Default Preview Environment dropdown empty | No preview-only environment exists in the stack | Create one at Settings → Environments → New Environment (e.g. `preview`). Don't share with production. |
| Picked `production` as Default Preview Environment | Live Preview reads draft content, which doesn't exist in production | Pick a non-production environment (e.g. `preview`) |
| Preview URL sub-tab shows "Custom Preview URL Unavailable" | Step 1 wasn't saved | Go back to General, re-check Enable Live Preview, click Save, return to Preview URL |
| Used `${entry.uid}` or `${entry.url}` template syntax | Contentstack uses Handlebars-style `{{ }}`, not JS template literals `${ }` | Use the Insert buttons under the Pattern field — they emit the correct syntax automatically |
| No Preview Token visible on Delivery Token edit page | The token was never generated; only the **Create Preview Token** button shows by default | Click the button. The token only exists after the click. |
| Tried to revoke / delete Preview Token after generation | There is NO revoke button in this UI | The Preview Token persists for the lifetime of the Delivery Token. To invalidate, delete the Delivery Token itself. |
| Created Preview Token on the wrong Delivery Token (e.g. one scoped to production) | The app's preview reads from this token's environment, so previewing the wrong env shows wrong content | Generate the Preview Token on the Delivery Token that's scoped to the preview environment. Each Delivery Token has its own Preview Token. |

## See also

- `install-studio` — calls this skill as **Step 0a**.
- `install-live-preview` — calls this skill first.
- `verify-setup` — Layer 0 confirms this skill was completed.
- `troubleshoot-canvas` — checks this first when canvas is blank.
