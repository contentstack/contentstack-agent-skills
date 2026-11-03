---
name: lytics
description: "Advise developers on Lytics, Contentstack's customer data platform: Lytics projects in Contentstack, installing the JavaScript tag (JStag), sending events and identities, schema fields and mappings (and legacy LQL), identity resolution, audiences and SegmentQL, content affinity and recommendations, the REST API and Segment API, consent and identity deletion, and connecting Lytics audiences to Personalize. Use when developers ask how to install or debug the Lytics tag, send custom events, map data onto profiles, build or automate audiences, read a profile, import Contentstack entries into Lytics, delete user data, or make Lytics audiences available in Personalize. For experiences, variants and the Personalize Edge SDK, use personalize."
allowed-tools: Read Grep Glob
---

# Lytics

Advise on Lytics, the customer data platform inside Contentstack: collecting events with the JavaScript tag and APIs, resolving them into unified profiles, building audiences, content affinity, managing data through the API, consent and deletion, and feeding audiences into Personalize.

## When to use

- Lytics projects, installing or debugging the JavaScript tag (JStag), sending events and identities.
- Schema fields, mappings and LQL, and identity resolution.
- Audiences, SegmentQL and the Segment API, and profile lookups.
- Importing Contentstack entries, content collections and recommendations.
- Consent, identity deletion, and connecting Lytics audiences to Personalize.

Use another skill for:

- Experiences, variants, attributes set through the Edge SDK, and edge middleware → `personalize`
- Entry variants in the CMS and how they're modeled → `cms-variants-personalization`
- Hosting the site and its tag on Launch → `launch-platform`

## Before you answer

Find out how the site is set up (Launch, tag manager or manual) and how consent is handled, the data sources (web, server, warehouse, Contentstack entries), the identity keys (email, user ID, anonymous cookie), the audience goals, and the symptoms when debugging.

## Instructions

1. Confirm the project exists and the tag is installed and sending. Get the tag verified before anything else.
2. Identify data sources and identity keys.
3. Map events to profile fields.
4. Build audiences in the UI or with SegmentQL.
5. Activate: connect Personalize, exports, recommendations.
6. Cover consent and deletion, and flag irreversible deletes.


### Projects

In Contentstack, Lytics is set up as a Lytics project. The Lytics app calls the same thing an account. Creating a project provisions the account, generates the JavaScript tag snippet and opens a default data stream. Projects replace the deprecated Data Activation Layer. From the project you install the tag, connect a CMS stack, Launch project or Personalize project, and invite collaborators. Roles are per project: organization membership alone does not grant access.

### JavaScript tag

On Launch, connecting the Launch project deploys the tag for you. Otherwise paste the snippet from **Install Lytics** on the project dashboard (also under **Data Pipeline → SDK** in Lytics) as the first element in `<head>`, or load it through a tag manager to fit your consent setup. Verify that `jstag` exists in the browser console and that the network tab shows requests to `lytics.io/c` (collection) and `lytics.io/api/personalize`.

Core calls: `jstag.send(payload)` sends key-value data to the default stream (pass a stream name to target another), `jstag.identify(payload)` is a semantic alias for sending identity, and `jstag.page()` / `jstag.pageView()` records a page view with page analysis. In single-page apps, call `jstag.page()` on route changes. The tag tracks anonymous visitors with a `_uid` cookie. Client-side integrations (GA4, Google Ad Manager, Meta, Contentstack Personalize and others) are opt-in checkboxes in the account's JavaScript tag settings.

### Identity

Profiles merge when events share an identity field value. Send a known identifier such as `email` or a user ID together with the anonymous `_uid` (for example on login) so the anonymous history joins the known profile. Identity keys have ranks that decide which wins when they conflict.

### Schema, mappings and LQL

Fields and mappings define how stream events become profile fields. Manage them in **Schema Studio** in the UI, which replaced hand-written LQL for day-to-day work. LQL (`SELECT … FROM <stream> INTO user BY <identity field>`) is still available through the API for bulk or automated changes. A stream with no mapping is collected but never reaches profiles. Changes that alter identity fields or field types can trigger a full reprocess of history; adding a field doesn't.

### Audiences

An audience is a live filter over profiles. Membership updates as profiles change, and it has no age-based expiry. Build audiences in the audience builder or in SegmentQL, for example `FILTER AND (visits > 5) FROM user`. Conditions on map fields must name a key (`conversion_ts.purchase > "now-7d"`), or the API returns 400. Turn on **Enable for Personalization** for audiences the site or Personalize needs to see. **Expires After** deletes the audience definition, not the profiles, so it is not a data-retention tool.

Automate audiences with the Segment API: `GET/POST /v2/segment`, `GET/PUT/DELETE /v2/segment/{id}`, `POST /v2/segment/{id}/reevaluate` after schema changes, and `/v2/segment/group` for groups.

### Personalize connection

Connect the Personalize project under **Settings → General → Connections** in the Lytics project. After that, Lytics audiences are available as audiences in Personalize for targeting and A/B tests, with no export job. In the browser, the tag writes audience membership to the `cs-lytics-audiences` cookie, and the Personalize Edge SDK sends it to the edge as a live attribute. The tag has to run before the edge request for the audience to apply, so first-visit targeting depends on Personalize preset attributes instead.

### Contentstack entries and recommendations

Authorize Contentstack in Lytics (**Account → Authorizations**) with the region, stack API key, delivery token and management token, then create an **Import Entries** job for the content types and taxonomies to sync. Each imported taxonomy becomes a context layer that scores profiles on that taxonomy's values. Content collections scope which documents are eligible for recommendations; the default collection includes every classified page, so create a narrower collection for production content. Lytics crawls live URLs and cannot classify localhost.

### API

Base URL `https://api.lytics.io`. Send the access token in the `Authorization` header (a query-string `access_token` also works but leaks into logs). Create tokens under **Account → Security → Access Tokens** with only the roles needed and an expiry; the token is shown once. Read a profile with `/api/entity/user/{field}/{value}`; the public personalization endpoint `/api/me/...` only returns fields on the allowlist in the account's API settings.

### Consent and deletion

Collect consent as events with a consistent event name, a `consented` value, and optional date, location and document context, mapped onto the profile so audiences can include or exclude by consent. Delete a profile with `DELETE /v2/identity/{table}/{field}/{value}`, or submit batches with `POST /v2/identity/delete` and track them with `GET /v2/identity/delete/status/{requestId}`. Deletion is permanent and does not remove data already exported to downstream tools; handle those separately.

## MCP tools

When the Contentstack MCP server is connected with the `lytics` group (authenticated with a Lytics access token), these tools act on the Lytics account:

- Inspect: `get_accounts`, `get_tables`, `get_fields`, `lytics_get_all_audiences`, `lytics_get_a_single_audience`, `get_field_information`, `get_a_user_profile`, `get_content_topics` (`lytics`)
- Change: `classify_content` (stores the classified URL in Lytics), `enrich_content` (`lytics`)

There are no tools for creating audiences, changing schema, sending events or deleting identities; use the Segment API, Schema Studio, the tag or the Identity API as described above. `get_a_user_profile` returns personal data, so only look up a profile the user names.

## Output

Lead with the step that unblocks the user. Show tag calls, payloads, SegmentQL and API requests as code with placeholders. Use short checklists for installation and debugging.

## Security

### Defaults

- Advisory by default. Use the MCP tools above only when the user asks; otherwise provide the calls and let the user run them.
- Lytics access tokens are server-side only. The tag snippet and account ID are public by design.
- Give tokens the fewest roles and an expiry.
- Respect consent: don't recommend collecting or activating data the user hasn't consented to.

### Destructive Actions

Identity deletion is permanent. Deleting a token or an audience breaks anything that depends on it. Explain the impact, name the exact profile, token or audience, and require explicit confirmation before recommending or running these calls.

### Secrets

Never echo access tokens, Contentstack management tokens or authtokens. Use placeholders and environment variables.

### Environment Variables

Use variables such as `LYTICS_API_TOKEN` and `LYTICS_ACCOUNT_ID` for server-side calls. Never hardcode tokens in client code.
