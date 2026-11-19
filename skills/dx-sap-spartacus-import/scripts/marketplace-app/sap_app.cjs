#!/usr/bin/env node
/*
 * sap_app — install + configure the SAP Commerce Cloud marketplace app on a stack.
 *
 * A management token cannot install or configure marketplace apps, so this step runs on the
 * user's own Contentstack CLI session (`csdx auth:login --oauth`), through csdx's bundled
 * @contentstack/cli-utilities (the same client csdx plugins use). Nothing is stored here.
 *
 *   node sap_app.cjs status --api-key <stack>     # read-only: installation + config summary
 *   node sap_app.cjs ensure --api-key <stack>     # install + configure once if missing;
 *                                                 # an existing install is only checked
 *   node sap_app.cjs ensure --api-key <stack> --reinstall   # uninstall, install, configure once
 *
 * The configuration applied is one named multi-config (SAP_APP_CONFIG_NAME, default "hti"),
 * set as default, using a Custom URL, plus "Keys to Save" = Custom Fields: code + name
 * (keeps each product ~110 B so carousels stay under the 20 KB JSON-field limit).
 *
 * Env (see SKILL.md › Environment Variables):
 *   SAP_APP_UID              marketplace app uid (default: looked up by name)
 *   SAP_APP_NAME             default "SAP Commerce Cloud"
 *   SAP_APP_CONFIG_NAME      default "hti"
 *   SAP_APP_API_BASE_URL     SAP OCC host, no scheme      (required for ensure)
 *   SAP_APP_API_ROUTE        default "/occ/v2/"
 *   SAP_APP_BASE_SITE        e.g. "electronics", "powertools-spa" (required for ensure)
 *   SAP_APP_BACKOFFICE_URL   backoffice host or URL      (required for ensure)
 *   CS_ORG_UID               optional; otherwise read from the stack
 *
 * Prints one JSON object on stdout; exits non-zero with a readable message on failure.
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

function loadCliUtilities() {
  let csdx;
  try {
    csdx = fs.realpathSync(cp.execSync('command -v csdx', { encoding: 'utf8' }).trim());
  } catch {
    fail('csdx not found on PATH — install @contentstack/cli and run `csdx auth:login --oauth`');
  }
  const root = path.resolve(path.dirname(csdx), '..');
  return require(require.resolve('@contentstack/cli-utilities', { paths: [root] }));
}

function fail(msg, extra) {
  process.stderr.write(`[sap_app] ERROR: ${msg}\n`);
  if (extra) process.stderr.write(`${extra}\n`);
  process.exit(1);
}

function arg(name, def) {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : def;
}

function errText(e) {
  return [e?.status, e?.errorMessage || e?.error_message || e?.message].filter(Boolean).join(' ');
}

function wantedConfig() {
  const need = ['SAP_APP_API_BASE_URL', 'SAP_APP_BASE_SITE', 'SAP_APP_BACKOFFICE_URL'];
  const missing = need.filter((k) => !process.env[k]);
  if (missing.length) fail(`missing env: ${missing.join(', ')}`);
  return {
    name: process.env.SAP_APP_CONFIG_NAME || 'hti',
    apiBaseUrl: process.env.SAP_APP_API_BASE_URL.replace(/^https?:\/\//, '').replace(/\/+$/, ''),
    apiRoute: process.env.SAP_APP_API_ROUTE || '/occ/v2/',
    baseSite: process.env.SAP_APP_BASE_SITE,
    backofficeUrl: process.env.SAP_APP_BACKOFFICE_URL,
    keys: ['code', 'name'],
  };
}

/*
 * The app splits each named configuration in two, exactly as its Configuration screen saves it
 * (read from a working "hti" installation):
 *   configuration  multi_config_keys[name] = {is_custom_baseUrl, base_url, api_route, backoffice_url}
 *                  + custom_keys (Keys to Save), default/active_multi_config, is_custom_json
 *   server config  multi_config_keys[name] = {base_url, api_route, base_site_id}
 * Both merge into what is already there, so other configurations on the stack are kept.
 */
function buildConfiguration(current, w) {
  const cfg = JSON.parse(JSON.stringify(current || {}));
  cfg.multi_config_keys = {
    ...(cfg.multi_config_keys || {}),
    [w.name]: {
      is_custom_baseUrl: true,
      base_url: w.apiBaseUrl,
      api_route: w.apiRoute,
      backoffice_url: w.backofficeUrl,
    },
  };
  cfg.custom_keys = w.keys.map((k) => ({ label: k, value: k, searchLabel: k, isDisabled: true }));
  cfg.is_custom_json = true;
  cfg.keypath_options = cfg.keypath_options || [];
  cfg.default_multi_config_key = w.name;
  cfg.active_multi_config = w.name;
  return cfg;
}

function buildServerConfig(current, w) {
  const cfg = JSON.parse(JSON.stringify(current || {}));
  cfg.multi_config_keys = {
    ...(cfg.multi_config_keys || {}),
    [w.name]: { base_url: w.apiBaseUrl, api_route: w.apiRoute, base_site_id: w.baseSite },
  };
  return cfg;
}

// The public "SAP Commerce Cloud" marketplace app (same uid in every org).
const DEFAULT_SAP_APP_UID = '6388916afd520e0019bb13bc';

async function findAppUid(mp, appName) {
  if (appName === 'SAP Commerce Cloud') return DEFAULT_SAP_APP_UID;
  for (let skip = 0; skip < 500; skip += 50) {           // API caps limit at 50
    const items = (await mp.findAllApps({ limit: 50, skip })).items || [];
    const hit = items.find((a) => (a.name || '').trim() === appName);
    if (hit) return hit.uid;
    if (items.length < 50) break;
  }
  fail(`marketplace app "${appName}" not found; set SAP_APP_UID`);
}

function summarize(cfg) {
  const out = {};
  for (const [k, v] of Object.entries(cfg || {})) {
    out[k] = /token|secret|password|private/i.test(k) ? '<redacted>' : v;
  }
  return out;
}

async function main() {
  const cmd = process.argv[2];
  const apiKey = arg('api-key', process.env.CS_API_KEY);
  if (!['status', 'ensure'].includes(cmd) || !apiKey) {
    fail('usage: node sap_app.cjs <status|ensure> --api-key <stack api key>');
  }
  const U = loadCliUtilities();
  const authType = U.configHandler.get('authorisationType');
  if (!authType) fail('not logged in — run `csdx auth:login --oauth` first');

  // Org of the stack: CS_ORG_UID, else read from the stack, else the org the OAuth login was
  // granted for (an OAuth session may not be allowed to read stack details).
  let org = process.env.CS_ORG_UID;
  if (!org) {
    try {
      const mgmt = await U.managementSDKClient({});
      org = (await mgmt.stack({ api_key: apiKey }).fetch()).org_uid;
    } catch (e) {
      org = authType === 'OAUTH' ? U.configHandler.get('oauthOrgUid') : undefined;
      if (!org) {
        fail(`could not read stack ${apiKey} with the csdx session (${errText(e)})`,
          authType === 'BASIC'
            ? 'Your csdx session is a basic (email/password) login; orgs with SSO reject it. Run `csdx auth:login --oauth`.'
            : 'Run `csdx auth:login --oauth` again, or set CS_ORG_UID.');
      }
    }
  }
  const mp = (await U.marketplaceSDKClient({})).marketplace(org);
  const appName = process.env.SAP_APP_NAME || 'SAP Commerce Cloud';

  const installs = (await mp.installation().fetchAll({ target_uids: apiKey })).items || [];
  let inst = installs.find((i) => (process.env.SAP_APP_UID && i.manifest?.uid === process.env.SAP_APP_UID)
    || (i.manifest?.name || '').trim() === appName);
  let appUid = process.env.SAP_APP_UID || inst?.manifest?.uid;

  if (cmd === 'status') {
    const h = inst && mp.installation(inst.uid);
    const config = h ? (await h.configuration())?.data : null;
    const server = h ? (await h.serverConfig())?.data : null;
    console.log(JSON.stringify({ org_uid: org, app_uid: appUid || null,
      installation_uid: inst?.uid || null,
      configuration: config && summarize(config), server_configuration: server && summarize(server) }, null, 1));
    return;
  }

  const wanted = wantedConfig();
  let installed = false;
  const reinstall = process.argv.includes('--reinstall');

  // Writing the configuration again on an install that already has it breaks the install on
  // the app's server: every request then fails with HTTP 414 and it never recovers. So an
  // existing install is only ever read here — never re-configured. To change or repair one,
  // --reinstall uninstalls it and configures the new install exactly once.
  if (inst && !reinstall) {
    const h = mp.installation(inst.uid);
    const cfg = (await h.configuration())?.data || {};
    const srv = (await h.serverConfig())?.data || {};
    const same = deepEqual(buildConfiguration(cfg, wanted), cfg)
      && deepEqual(buildServerConfig(srv, wanted), srv);
    if (!same) {
      fail(`the app is already installed on ${apiKey} with a different configuration`,
        'Writing it again breaks the install. Change it in the app\'s Configuration page, or re-run with --reinstall.');
    }
    console.log(JSON.stringify({ org_uid: org, app_uid: appUid, installation_uid: inst.uid,
      installed: false, configured: wanted.name, keys: wanted.keys, unchanged: true }, null, 1));
    return;
  }
  if (inst && reinstall) {
    await mp.installation(inst.uid).uninstall();
    inst = null;
  }
  if (!inst) {
    if (!appUid) appUid = await findAppUid(mp, appName);
    try {
      await mp.app(appUid).install({ targetUid: apiKey, targetType: 'stack' });
      installed = true;
    } catch (e) {
      fail(`install failed (${errText(e)})`,
        'If the app needs consent, install it once from Marketplace in the UI, then re-run.');
    }
    // The install response doesn't carry a usable installation uid; read it back.
    inst = ((await mp.installation().fetchAll({ target_uids: apiKey })).items || [])
      .find((i) => i.manifest?.uid === appUid);
    if (!inst) fail('app installed, but the installation was not found on the stack — re-run');
  }
  // Fresh install: configure it exactly once (see above).
  const handle = mp.installation(inst.uid);
  await handle.setConfiguration(buildConfiguration({}, wanted));
  await handle.setServerConfig(buildServerConfig({}, wanted));
  console.log(JSON.stringify({ org_uid: org, app_uid: appUid, installation_uid: inst.uid,
    installed, reinstalled: reinstall, configured: wanted.name, keys: wanted.keys }, null, 1));
}

function deepEqual(a, b) {
  const norm = (v) => JSON.stringify(v, (k, x) => (x && typeof x === 'object' && !Array.isArray(x)
    ? Object.fromEntries(Object.entries(x).sort(([p], [q]) => p.localeCompare(q))) : x));
  return norm(a) === norm(b);
}

if (require.main === module) {
  main().catch((e) => fail(errText(e) || String(e)));
}
module.exports = { buildConfiguration, buildServerConfig };
