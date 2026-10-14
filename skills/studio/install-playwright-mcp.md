---
name: install-playwright-mcp
---

## When to use

Optionally install the Playwright MCP server so downstream skills can drive the Contentstack web app, canvas app, and Studio directly, turning manual click-through gates into one-shot automated verification.

Offer the FIRST time a user runs any setup/verification flow (`enable-visual-experience`, `install-studio`, `verify-setup`, `troubleshoot-canvas`) whose steps include "click X and confirm Y". If already installed (`claude mcp list`), skip silently. If user declines, skip for the session, never re-prompt. NOT a hard gate.

> **Mandatory auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them), and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Install Playwright MCP: optional acceleration layer

> **Recommendation, not a requirement.** Every downstream skill works without Playwright MCP via manual click-through. With it, the skill drives the web app and reports what it observed. We still ask before destructive toggles.

## Why offer this

Most Studio setup friction is tab-switching. With Playwright MCP installed:

- `enable-visual-experience` can verify the live UI state directly (is the checkbox checked? did Save persist? did the top-nav link appear?) instead of trusting "done"
- `verify-setup` Layer 2 (Live Preview iframe channel) can be tested end-to-end without the user opening DevTools
- `troubleshoot-canvas` can read the actual canvas iframe DOM instead of asking the user to describe what they see
- `enable-visual-experience` Step 1 sanity-check ("top-nav `Visual Experience` link appears") becomes an assertion, not a prompt
- Stack provisioning skills can confirm tokens were actually created via the UI (CMA can't always see Preview Tokens)

> **Confirmation policy:** any toggle that modifies stack settings (Enable Live Preview, Create Preview Token, Save buttons) goes through an explicit confirmation prompt before the MCP call fires. Playwright MCP reads the UI to confirm state, and asks before changing it.

## Task

### Step 1: Check if it's already installed

Run one of:

```bash
# claude-code CLI
claude mcp list | grep -i playwright

# In VS Code extension or Claude Desktop — check the MCP servers section of the IDE settings
```

If `playwright` (or `@playwright/mcp`) shows up, skip the rest of this skill and print: `Playwright MCP already installed — downstream skills will use it automatically.` <!-- style-lint: allow -->

### Step 2: Offer the recommendation (don't push)

Tell the user verbatim:

> I noticed Playwright MCP isn't installed. It's optional: every Studio skill works without it. But if you install it (~2 minutes), the next few setup steps go from "click here, type done" to "I clicked here, here's what I saw, ready for the next step." You stay in control: I still ask before changing any settings. Want me to install it now? <!-- style-lint: allow -->

Three valid user responses:

- **Yes / sure / install it**: proceed to Step 3.
- **No / skip / not now**: reply `Got it — I'll use the manual click-through paths for the rest of this session. You can install Playwright MCP later with this skill anytime.` Stop. Do not re-prompt this session.
- **What does it do? / tell me more**: expand on the "Why offer this at all" section above, then re-ask.

### Step 3: Install

Detect `{{ide}}` and run the right command:

**claude-code CLI:**
```bash
claude mcp add playwright npx @playwright/mcp@latest
```

**Claude Desktop / VS Code extension:**
Open the MCP config file and add:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```
Config locations:
- Claude Desktop (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`
- Claude Code VS Code extension: `.vscode/settings.json` under `claude.mcpServers` (or the extension's MCP panel)
- Cursor: `~/.cursor/mcp.json`
- Windsurf: similar, check the IDE's MCP settings panel

Restart the IDE / `claude` CLI session so the new MCP server registers.

### Step 4: Configure browser mode

Ask the user verbatim, presenting the options with their honest tradeoffs. **Recommend the dedicated profile.**

> Playwright MCP can run in two supported modes. **Pick based on how much you want MCP isolated from the rest of your browsing.**
>
> **Option A: Dedicated Chrome profile** (recommended)
>   - A second Chrome window with its own empty profile (`~/.chrome-mcp`). Contentstack is the only site logged in there, so MCP can't see anything else.
>   - **Tradeoff:** one extra login the first time. A second Chrome icon in your dock while the session is active.
>
> **Option B: Isolated headless Chromium** (strongest separation)
>   - Playwright MCP launches its own Chromium with no profile at all.
>   - **Tradeoff:** slowest first-time setup. You log in fresh inside the headless browser every session (SSO can be fiddly). Visible UI debugging is harder.
>   - Best for: CI-like flows, when you never want a visible MCP browser, when other developers run the same skill on the same machine.
>
> Which mode? (A / B)

Record the answer as `{{chromeProfileMode}}`:
- A becomes `dedicated`
- B becomes `isolated`

> **Not supported: attaching to your everyday (default) Chrome profile.** Since Chrome 136, Chrome ignores `--remote-debugging-port` on the default user data directory for **all** users, managed or not: launch succeeds, but `lsof -i :9222` shows nothing listening. It is also unsafe: a debug port on your everyday profile exposes every tab and logged-in site (email, banking, GitHub) to any local process that can reach `127.0.0.1:9222`. Never put the debug port on the everyday profile; always pair it with a dedicated `--user-data-dir`. If the user asks for this mode (`existing`), explain both reasons and offer `dedicated` instead.

For **dedicated** (`{{chromeProfileMode}}` = `dedicated`): a second Chrome window with its own empty profile, only Contentstack logged in:

- Launch a second Chrome instance with the debug port AND a dedicated `--user-data-dir`. Your normal Chrome can keep running undisturbed.

  | OS | One-liner |
  |---|---|
  | macOS | `open -na "Google Chrome" --args --remote-debugging-port=9222 --disable-features=LocalNetworkAccessChecks --user-data-dir="$HOME/.chrome-mcp"` |
  | Linux | `google-chrome --remote-debugging-port=9222 --disable-features=LocalNetworkAccessChecks --user-data-dir="$HOME/.chrome-mcp" &` |
  | Windows (PowerShell) | `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --disable-features=LocalNetworkAccessChecks --user-data-dir="$env:USERPROFILE\.chrome-mcp"` |

  > Both flags matter: `--remote-debugging-port` for MCP to attach, `--disable-features=LocalNetworkAccessChecks` for Chrome v136+ to load the Studio canvas iframe served from `localhost`. Without the second flag the canvas iframe shows up blank with `net::ERR_BLOCKED_BY_PRIVATE_NETWORK_ACCESS_CHECKS` in DevTools; it is required for any Studio canvas-iframe workflow, regardless of MCP.

- Assert the port is listening:
  ```bash
  lsof -i :9222   # macOS / Linux
  netstat -ano | findstr :9222   # Windows
  ```
  Must show Chrome bound to `127.0.0.1:9222`.

- Update the MCP config to attach:
  ```json
  "args": ["@playwright/mcp@latest", "--cdp-endpoint", "http://127.0.0.1:9222"]
  ```
  > **Use `127.0.0.1`, NOT `localhost`, in `--cdp-endpoint`.** Chrome's `--remote-debugging-port` binds **IPv4 `127.0.0.1`** only. Node/Playwright resolves `localhost` to **IPv6 `::1` first**, so `--cdp-endpoint http://localhost:9222` fails with `connect ECONNREFUSED ::1:9222` even though `lsof -i :9222` shows Chrome listening. (Changing it needs a session restart: the MCP server binds the endpoint at process start.)

- **First-time only**: the dedicated profile is empty. Step 5b prompts you to log into Contentstack once in that window. After that the profile keeps the session cookies, so subsequent sessions skip the login.

For **isolated** (`{{chromeProfileMode}}` = `isolated`):
- No extra config. Default Playwright MCP launches its own Chromium. Skip the launch one-liner and the `lsof` assertion. The session-bridge step below still applies: the isolated Chromium has no Contentstack cookies, so you'll log in once inside it.

### Step 5: Smoke test

Run a 3-line smoke test from a fresh Claude turn:

```
Browser: navigate to https://<region-app-host>   (e.g. app.contentstack.com)
Then: snapshot the page
Then: report the page title
```

Pass: Claude returns a snapshot with the Contentstack login or stacks page title.

Fail: see "Common pitfalls" below.

### Step 5b: Session bridge (verify Contentstack is reachable as a logged-in user)

This is the step that flips MCP from "installed" to "ready to auto-drive." Without it, the first downstream skill that tries to drive the UI hits the login screen and stalls.

1. **Navigate to the Contentstack editor via Playwright MCP** and take a snapshot. Use the app host for the user's region (`https://app.contentstack.com` for NA, `https://eu-app.contentstack.com` for EU, and so on). **On a custom / private data center, use the app host Contentstack supplied**; set every host explicitly. Driving the wrong host logs you into the wrong instance and every later step reads the wrong stack. Confirm the DC first via [`analyze-project-fit`](analyze-project-fit.md) § 2b: Determine the data center.

2. **Assert which page we landed on.** Branch on the snapshot:

   | Snapshot URL | State | Action |
   |---|---|---|
   | `/#!/stacks` or contains a "Stacks" heading | Logged in | Proceed to step 3. |
   | `/#!/login` or contains an SSO/login form | Not logged in | See step 2a below. |
   | Region picker / `app.contentstack.com/login/saml` / org switcher | Partly logged in | See step 2a below. |

   2a. **If not logged in**, tell the user verbatim:
   > Playwright MCP opened Contentstack but landed on the login page. **Log in once in the Chrome window MCP is using** (the one with the debug banner). I'll wait: reply `logged in` when you're on the stacks list.

   After user replies `logged in`, re-snapshot and re-assert. If still on login, stop, report failure, and do NOT mark MCP ready.

3. **Capture active org + most-recent stack.** With MCP, read the DOM:
   - Active org: on the org dashboard (`/#!/dashboard`), read `[data-test-id="cs-dashboard-org-title"]`. The switcher is under the top-right profile icon.
   - Most-recent stack: click into the stacks list, grab the **first row** (order isn't reliably recent-first; confirm it). Capture:
     - Stack display name (visible row text)
     - Stack API key (in the stack's Settings, under Stack, open API Credentials and copy the `Api Key` field. Or read it from the URL after entering: `/#!/stack/<apiKey>/...`)

4. **Write to session note** (an in-conversation memory record visible to downstream skills in this session):
   ```
   PLAYWRIGHT_MCP_READY=true
   PLAYWRIGHT_MCP_MODE={{chromeProfileMode}}
   CS_ACTIVE_ORG=<org name>
   CS_RECENT_STACK_NAME=<stack name>
   CS_RECENT_STACK_API_KEY=<blt...>
   ```
   Downstream skills check `PLAYWRIGHT_MCP_READY` before deciding whether to use auto-drive paths or fall back to manual click-through, and pre-fill the `stackApiKey` input from `CS_RECENT_STACK_API_KEY` so the user isn't asked again.

5. **Confirm the captured context with the user** verbatim:
   > MCP is bridged to your Contentstack session.
   >
   > - Active org: **<org name>**
   > - Most-recent stack: **<stack name>** (`<api key>`)
   >
   > Downstream skills will default to this stack. Reply `yes` to confirm, or paste a different stack API key.

   If user picks a different stack, overwrite `CS_RECENT_STACK_API_KEY` in the session note.

### Step 6: Tell the user what's now automated

Print:

```
✅ Playwright MCP installed and verified.

These skills will now run with reduced click-through tax:
  • enable-visual-experience  — verifies checkboxes/saves/top-nav directly
  • install-studio            — confirms Studio's "Add Canvas URL" persists
  • verify-setup              — Layer 2 + Layer 3 + Layer 4 tested end-to-end
  • troubleshoot-canvas       — reads the canvas iframe DOM directly

These still require your hands on the keyboard (CLI / file edits):
  • install-studio (npm install + env files)
  • setup-template-preview-routes (route file edits)
  • author-without-code / build-section / build-connected-template (authoring decisions)

I'll always ask before toggling any setting in the Contentstack web app —
Playwright MCP does NOT mean autonomous changes.
```

## Inputs needed from the user

1. `ide`: to pick the right config path.
2. `chromeProfileMode`: dedicated (recommended, one-time login) vs isolated (cleaner, re-login each session).

## Acceptance

- [ ] User was offered the recommendation in non-pushy framing.
- [ ] If declined: no further prompts this session.
- [ ] If accepted: Playwright MCP appears in the IDE's MCP server list.
- [ ] Smoke test (navigate + snapshot + title) returns a real result.
- [ ] Session bridge verified: MCP-driven Contentstack app snapshot lands on stacks list (not /login). If user logged in mid-flow, re-snapshot confirms success.
- [ ] Session note written with `PLAYWRIGHT_MCP_READY=true`, active org, recent stack name + API key.
- [ ] User confirmed (or overrode) the captured default stack.
- [ ] User informed which skills accelerate and which don't.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Treating this skill as a hard prerequisite | It's an accelerator. If we gate setup on it, users without admin rights to install MCP are blocked. | This is a SOFT recommendation. Decline = use manual click-through. Re-read the "This is a recommendation" header. |
| Re-prompting after the user declined | Annoying, trains the user to say no faster next time | Track decline in the session, never re-ask in the same conversation. |
| Attaching to the everyday Chrome profile | Unsupported on Chrome 136+ (the debug port never binds on the default profile), and unsafe: every tab and logged-in site is exposed to anything that can reach the port | Recommend `dedicated`. Never put the debug port on the everyday profile. |
| Claude clicks Save without asking | Violates the "verify before mutating" contract | Every state-mutating click goes through an explicit `confirm before clicking` prompt in the calling skill. Playwright MCP is for READING state and EXECUTING confirmed actions, not autonomous mutation. |
| Playwright MCP installed but not verified | Skills assume it works, then fail mid-flow with cryptic MCP errors | Always run Step 5's smoke test. If it fails, don't tell downstream skills the MCP is ready. |
| `--cdp-endpoint` set but Chrome not launched with `--remote-debugging-port=9222` | MCP server can't attach. Falls back to isolated launch silently | Confirm Chrome is running with the debug port before declaring success. `lsof -i :9222` should show Chrome listening. |
| `--cdp-endpoint http://localhost:9222` fails with `connect ECONNREFUSED ::1:9222` even though `lsof -i :9222` shows Chrome listening | Chrome binds the debug port on **IPv4 `127.0.0.1`**. Node/Playwright resolves `localhost` to **IPv6 `::1`** first and connects to the wrong address | Use `http://127.0.0.1:9222` in `--cdp-endpoint` (never `localhost`). Re-add the MCP server with the corrected endpoint and restart the session: the endpoint binds at MCP-process start. |
| Mac App Store Chrome | Sandboxed, can't use `--remote-debugging-port` reliably | Use the standalone Chrome download from google.com/chrome, not the App Store build. |
| Forgetting `--disable-features=LocalNetworkAccessChecks` on Chrome v136+ | Studio's canvas iframe (served from `localhost:<port>`) is blocked when loaded from `app.contentstack.com`. Canvas appears blank. `net::ERR_BLOCKED_BY_PRIVATE_NETWORK_ACCESS_CHECKS` in DevTools. | Add the flag to your Chrome launch one-liner. Quit the dedicated-profile Chrome and relaunch with the flag. |
| Dedicated-profile Chrome didn't actually quit before relaunch | macOS keeps Chrome's background process alive after closing the window. The new launch silently ignores `--remote-debugging-port` because the existing process owns the profile | Ask the user to fully quit that Chrome window (`Cmd+Q` on macOS); don't kill browser processes for them. Confirm `lsof -i :9222` is empty BEFORE launching, then run the one-liner. |
| Step 5b skipped because smoke test passed | Smoke test only confirms MCP can drive a browser. It doesn't confirm the browser has a Contentstack session | 5b is the gate, not 5. Don't mark `PLAYWRIGHT_MCP_READY=true` without 5b. |
| Captured stack from recently-accessed list is wrong | User most-recently opened a different stack than the one they're configuring now | Step 5b explicitly asks the user to confirm or override the captured API key. Never assume. |
| Session note lost across context compaction | Long sessions may compact older messages. The `PLAYWRIGHT_MCP_READY` flag and captured stack key can drop out | Re-run a lightweight version of Step 5b's check when a downstream skill starts (re-snapshot Contentstack, re-confirm session) rather than trusting flag indefinitely. |

## See also

- `enable-visual-experience`: biggest beneficiary, turns 6 manual steps into 6 verified observations.
- `verify-setup`: Layer 2/3/4 can be fully automated when this is installed.
- `troubleshoot-canvas`: reads canvas iframe DOM directly instead of asking user to describe.
- Reference: Playwright MCP project, `@playwright/mcp` on npm.
