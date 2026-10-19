---
name: setup-local-https-canvas
---

## When to use

Set up a locally-trusted HTTPS cert (via mkcert) for the canvas-app. NOT required for most local-dev: browsers treat `localhost` as trusted and allow Studio to iframe `http://localhost:<port>`.

Use ONLY when HTTPS-on-localhost is actually required: service workers, secure cookies, web-share/WebAuthn, strict corporate policies that block mixed content even for localhost, or production-parity smoke tests. Phrases: "I need https locally", "mixed-content block on localhost". Do NOT use for production (real HTTPS) or tunnels (Cloudflare/ngrok already ship certs).

> **Auth preflight: settle the credential before the first API call.** Resolve it OAuth-first per [`authenticate-cma`](authenticate-cma.md): `CS_OAUTH_ACCESS_TOKEN`, else the Contentstack MCP's stored session (**ask the user before reading or refreshing it**: refreshing rotates the refresh token; see that skill for where it lives). **Don't ask for a session `authtoken` up front**: it is the last rung, considered only after a freshly refreshed OAuth token has been observed to fail, and only after explaining the risk. If nothing resolves, or a refresh fails with `400 invalid_refresh_token`, hand them `! CONTENTSTACK_REGION=<code> npx @contentstack/mcp --auth` (it needs a TTY and a browser, so it cannot be run for them) and wait. `403 error_code 316` is a valid credential aimed at another org: fix the org or the `api_key`, do **not** re-authenticate.

# Set up locally-trusted HTTPS for the canvas-app

## Context: when this is actually needed

Studio is served from `https://app.contentstack.com/#!/studio`. To preview your canvas-app, Studio loads it inside an iframe.

**For plain `http://localhost:<port>` the iframe just works** in modern browsers: Chrome, Firefox, and Safari all treat `localhost` and `127.0.0.1` as "potentially trustworthy" origins per the [W3C Secure Contexts spec](https://www.w3.org/TR/secure-contexts/), so mixed-content blocking does NOT apply. **You do not need mkcert for a basic Studio canvas iframe.** Current Chrome asks once for local network access: the user must click Allow, or the canvas stays blank. HTTPS doesn't avoid this prompt.

HTTPS-on-localhost via mkcert is only needed when something else in your app requires HTTPS even at dev time:

- **Service workers**: require secure context. An HTTP localhost dev server can't register one
- **Secure cookies / SameSite=None+Secure**: set only over HTTPS, even on localhost
- **WebAuthn / WebShare / Payment Request**: gated on secure context
- **Strict corporate browser policy**: some MDM policies override the localhost exemption
- **Production-parity local testing**: to catch HTTPS-only bugs before deploy
- **Tunnel URLs (cloudflared / ngrok / lt)**: NOT localhost, so the secure-context exemption doesn't apply. The tunnel already gives you a trusted HTTPS URL, so mkcert wouldn't help anyway

If none of the above apply, **skip this skill** and use plain `http://localhost:<port>` as your Canvas URL origin / env base URL. Add mkcert later if a real need emerges.

## Task

### 1. Install mkcert (one-time per machine)

Detect the OS and use the right command:

```bash
# macOS
brew install mkcert nss
# nss is needed if you use Firefox; harmless otherwise

# Linux (Debian/Ubuntu)
sudo apt install libnss3-tools
# Then grab mkcert: https://github.com/FiloSottile/mkcert/releases (or via Homebrew on Linux)

# Windows (PowerShell, as admin)
choco install mkcert
# or: scoop install mkcert
```

Verify:

```bash
mkcert -version
```

### 2. Install the local CA into the system trust store

```bash
mkcert -install
```

This adds mkcert's root CA to:
- macOS: Keychain (System trust)
- Linux: NSS-using browsers (Chromium, Firefox). Also writes to `/etc/ssl/certs` if `update-ca-certificates` is available
- Windows: Windows Certificate Store

You may be prompted for sudo / admin once. After this, every cert mkcert generates is automatically trusted by every browser on this machine (including the Playwright-MCP-driven one, if you're using that).

### 3. Generate the cert for the canvas-app

Inside `{{projectRoot}}`:

```bash
mkdir -p certs
mkcert -cert-file certs/localhost.pem -key-file certs/localhost-key.pem localhost 127.0.0.1 ::1
```

This emits a cert valid for `localhost`, IPv4 loopback, and IPv6 loopback. The cert is locally-trusted (signed by the mkcert root CA you installed in step 2).

### 4. Wire the cert into your framework's dev server

**Vite** (`vite.config.ts` / `.js`):

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { readFileSync } from 'node:fs';

export default defineConfig({
  plugins: [react()],
  server: {
    https: {
      key:  readFileSync('certs/localhost-key.pem'),
      cert: readFileSync('certs/localhost.pem'),
    },
    port: {{devPort}},
    // Local dev only: let Studio's canvas (served from your region's
    // Contentstack app host) frame this dev server. No wildcard origins.
    headers: {
      'Content-Security-Policy': "frame-ancestors 'self' https://*.contentstack.com;",
    },
    // Only list explicit non-localhost hostnames (e.g. a tunnel); never `true`.
    // allowedHosts: ['my-tunnel.example.dev'],
  },
  preview: {
    // `vite preview` serves the production build: no permissive headers here.
    https: {
      key:  readFileSync('certs/localhost-key.pem'),
      cert: readFileSync('certs/localhost.pem'),
    },
    port: {{devPort}},
  },
});
```

> The dev-server CSP `frame-ancestors 'self' https://*.contentstack.com` header lets Studio iframe the app; it's part of this same setup, so don't split it into a separate step. Keep it on the dev server (and, in production, on the canvas route only). Don't add `Access-Control-Allow-Origin: *` or `frame-ancestors *`. If you reach the dev server through a non-localhost hostname (e.g. a tunnel) and Vite returns "host not allowed", list that hostname in `server.allowedHosts`; never set it to `true`.

**Next.js**: pass your mkcert files to `next dev` via the `--experimental-https-key` + `--experimental-https-cert` flags:

```bash
next dev \
  --experimental-https \
  --experimental-https-key ./certs/localhost-key.pem \
  --experimental-https-cert ./certs/localhost.pem
```

Bare `next dev --experimental-https` generates its OWN self-signed cert (not signed by mkcert's root CA). Studio's iframe silently blocks it. Passing the key/cert flags points Next at the trusted mkcert pair. Fallback if the flags aren't available on your Next version: a custom `server.js` booting Node's https module with the mkcert files, or a prod build (`next build && next start`) behind a reverse proxy that terminates HTTPS with the mkcert cert.

**Remix / Astro**: follow the same pattern as Vite (both expose `server.https` config).

### 5. Update `.gitignore`

The private key is sensitive, never commit it:

```
# .gitignore
certs/
```

Confirm with:

```bash
git check-ignore -v certs/localhost-key.pem
```

### 6. Verify

```bash
# Start the dev (or preview) server
npm run dev   # or pnpm dev / yarn dev / bun dev

# In another terminal — confirm HTTPS works
curl -I https://localhost:{{devPort}}/
# Expect: HTTP/2 200 (or similar). No `(self signed certificate)` warning.

# Open in a normal browser tab — expect green lock, no cert warning.
```

Then test the Studio iframe:
1. Wherever Studio asks for your canvas-app's origin (the env-level setting that holds the canvas-app's host:port, set per Contentstack environment), make sure it's now `https://localhost:{{devPort}}`. The Studio Project's Canvas URL field stays `/canvas`. Canvas URL is a separate setting and it's just a path, never an origin.
2. Open any composition. The canvas iframe should load cleanly (no blank frame, no console error).

## Inputs needed from the user

1. `projectRoot`: the canvas-app directory.
2. `devPort`: the port your dev/preview server listens on. Vite default is 5173. Next is 3000.

## Acceptance

- [ ] `mkcert -version` returns a version string.
- [ ] `mkcert -install` completed (root CA in system trust store).
- [ ] `certs/localhost.pem` + `certs/localhost-key.pem` exist in the project root.
- [ ] Framework config has `server.https` + `preview.https` pointing at the cert pair, AND the dev server sends `frame-ancestors 'self' https://*.contentstack.com` (no wildcard ACAO; `allowedHosts` only lists explicit non-localhost hostnames, never `true`).
- [ ] `.gitignore` contains `certs/`.
- [ ] `curl -I https://localhost:<port>/` returns a 200 with no untrusted-cert warning.
- [ ] Browser loads `https://localhost:<port>` with a green lock.
- [ ] Studio canvas (with the matching Canvas URL configured) shows the app inside its iframe, not a blank frame.

## Common pitfalls

| Pitfall | Why it bites | Fix |
| --- | --- | --- |
| Skipping `mkcert -install` | Cert is generated but not trusted by the browser, silent iframe block | Run `mkcert -install` first. Re-open browsers after (Firefox especially caches trust). |
| Bare `next dev --experimental-https` (no key/cert flags) | Next generates its own self-signed cert not signed by mkcert's root CA, so the Studio iframe blocks silently | Pass the mkcert pair: `next dev --experimental-https --experimental-https-key ./certs/localhost-key.pem --experimental-https-cert ./certs/localhost.pem` |
| Cert files committed to git | Private key leaked | Always add `certs/` to `.gitignore` before generating |
| Generating cert for a different hostname than the dev URL | Cert mismatch, which produces a browser warning, which blocks the iframe | `mkcert ... localhost 127.0.0.1 ::1` covers all common localhost forms. Add other names if needed |
| `allowedHosts` set but headers missing | Vite serves the page but Studio can't frame it | Set the dev-server CSP `frame-ancestors 'self' https://*.contentstack.com`. `allowedHosts` (explicit hostnames only, never `true`) solves a different layer |
| Cert expired after ~825 days | mkcert certs are short-lived for security | Regenerate the cert pair. The root CA stays trusted |
| Re-installing mkcert after a system upgrade and re-running `mkcert -install` | Old cert pair was signed by the previous mkcert root CA which is no longer trusted | Regenerate the cert pair after re-installing mkcert |
| Using Mac App Store Chrome | Sandboxed. Sometimes ignores Keychain trust for system-installed CAs | Use the standalone Chrome download from google.com/chrome |

## See also

- `setup-section-preview`: wires Studio's preview channel. This skill is its HTTPS prerequisite
- `install-playwright-mcp`: its smoke test depends on a trusted Studio canvas, which depends on this cert
- `troubleshoot-canvas`: blank-iframe symptom row maps back here
