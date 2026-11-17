#!/usr/bin/env node
/*
 * csdx_auth — print the Contentstack Management API auth header of the user's csdx session,
 * as JSON on stdout, for cs_auth.py. Uses csdx's own @contentstack/cli-utilities, which
 * refreshes an expired OAuth access token first.
 *
 *   node csdx_auth.cjs            # {"authorization": "Bearer …"}  (OAuth)  or {"authtoken": "…"} (basic)
 *   node csdx_auth.cjs --refresh  # force an OAuth refresh first (after a 401)
 *
 * The value goes to the calling process only; never log it.
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

function fail(msg) {
  process.stderr.write(`[csdx_auth] ${msg}\n`);
  process.exit(1);
}

(async () => {
  let csdx;
  try {
    csdx = fs.realpathSync(cp.execSync('command -v csdx', { encoding: 'utf8' }).trim());
  } catch {
    fail('csdx not found on PATH — install @contentstack/cli, or set CS_MANAGEMENT_TOKEN');
  }
  const root = path.resolve(path.dirname(csdx), '..');
  const U = require(require.resolve('@contentstack/cli-utilities', { paths: [root] }));
  const type = U.configHandler.get('authorisationType');
  if (type === 'OAUTH') {
    if (process.argv.includes('--refresh')) await U.authHandler.compareOAuthExpiry(true);
    else await U.authHandler.compareOAuthExpiry();
    const token = U.configHandler.get('oauthAccessToken');
    if (!token) fail('csdx OAuth session has no access token — run `csdx auth:login --oauth`');
    process.stdout.write(JSON.stringify({ authorization: `Bearer ${token}` }));
  } else if (type === 'BASIC') {
    const token = U.configHandler.get('authtoken');
    if (!token) fail('csdx session has no authtoken — run `csdx auth:login --oauth`');
    process.stdout.write(JSON.stringify({ authtoken: token }));
  } else {
    fail('not logged in — run `csdx auth:login --oauth`, or set CS_MANAGEMENT_TOKEN');
  }
})().catch((e) => fail(e?.message || String(e)));
